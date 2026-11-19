"""v0.16 real original PUBLIC Column controls: source-only developer D0/I0.

Do NOT change original author scorer, hidden GT, prior D0 frozen artifacts or
score metrics. This is not a new LLM trial and not all-45 task edit parity.
"""
from __future__ import annotations

import ast
from hashlib import sha256
import json
from pathlib import Path
import os
import tempfile
import unittest

import ifcopenshell
import ifcopenshell.util.unit

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v016_original_column_i0 import (
    run_imperative_column_i0, ColumnI0Blocked, _parse_public_instruction,
)
from tools.audit_bibimbap_v016_scoreable_column import (
    audit, PUBLIC_CASES, V3_FROZEN_SHA,
)
from tools.oracle_bibimbap_column15_16_native import (
    strict_move_column, strict_delete_column,
)

BASE = Path(os.environ.get(
    "BIBIMBAP_EXPERIMENT_BASE", r"D:\문서\D__1_Projects\202611"
))
HERE = Path(__file__).resolve().parents[1]
AUTHOR = BASE / "bibimbap-author-upstream"
DATA = BASE / "bibimbap-author-data"
FROZEN = HERE / "reports" / "bibimbap_v3_column_d0_test15_test16_20261113.json"
MATRIX = HERE / "reports" / "bibimbap_v012_actual_original45_native_read_and_D0I0_matrix_20261114.json"
PREV = HERE / "reports" / "bibimbap_v015_original_hosted_window_i0_d0_parity_20261114.json"
CURRENT = HERE / "reports" / "bibimbap_v016_original45_scoreability_and_column_parity_20261114.json"


class V016SourceOnlyAuthorScoreableColumnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not all(p.is_file() for p in (FROZEN, MATRIX, PREV, CURRENT)):
            raise unittest.SkipTest("Missing versioned source-only research evidence")
        if not (AUTHOR.is_dir() and DATA.is_dir()):
            raise unittest.SkipTest("Pinned original author/data source checkout absent")
        cls.report = json.loads(CURRENT.read_text(encoding="utf8"))
        cls.public = {row["test_id"]: row for row in public_45(AUTHOR, DATA)}
        cls.temp = tempfile.TemporaryDirectory(prefix="bmb-v016-regression-")
        cls.tmp = Path(cls.temp.name)
        original = DATA / "ifc" / "basic_tasks.ifc"
        cls.original_sha = file_hash(original)
        cls.source = cls.tmp / "same_public_original_m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(original)), "METER"
        ).write(str(cls.source))
        cls.i0_results = {}
        for case in PUBLIC_CASES:
            dest = cls.tmp / (case + "_new_imperative.ifc")
            result = run_imperative_column_i0(
                cls.source, case, cls.public[case]["public_question"], dest
            )
            proof = (strict_move_column(
                cls.source, dest, result.original_target_guid_from_public_question, dy=-3.0)
                if case == "test_15"
                else strict_delete_column(
                    cls.source, dest, result.original_target_guid_from_public_question)
            )
            cls.i0_results[case] = (dest, result, proof)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_public_population_counts_and_unchanged_data_revision(self):
        self.assertEqual(_head(AUTHOR), AUTHOR_SHA)
        self.assertEqual(_head(DATA), DATA_SHA)
        self.assertEqual(self.report["original_public_45_total_unchanged"], 45)
        self.assertEqual(self.report["original_45_crud_distribution"],
                         {"create":15, "update":15, "delete":15})
        self.assertEqual(self.report["new_model_api_calls"], 0)
        self.assertEqual(self.report["new_paid_usd"], 0)
        self.assertEqual(len(self.report["original45_intention_to_test_matrix"]),45)
        self.assertTrue(all(not row["excluded_from_original_45_denominator"]
                            for row in self.report["original45_intention_to_test_matrix"]))
        self.assertEqual(file_hash(FROZEN), V3_FROZEN_SHA)
        self.assertEqual(file_hash(DATA / "ifc" / "basic_tasks.ifc"), self.original_sha)

    def test_true_public_Column_native_I0_edit_verified_without_xml_compiler(self):
        rows = {row["task_id"]:row for row in self.report["source_only_original_column_controls"]}
        for case in PUBLIC_CASES:
            with self.subTest(case=case):
                output, result, proof = self.i0_results[case]
                self.assertEqual(result.candidate_native_sha256,file_hash(output))
                self.assertEqual(result.candidate_native_sha256,
                                 rows[case]["independent_Python_I0_native_result_sha256"])
                self.assertEqual(result.candidate_native_sha256,
                                 rows[case]["frozen_reproduced_XML_D0_native_result_sha256"])
                self.assertEqual(proof["status"],rows[case]["independent_I0_native_oracle_status"])
                self.assertTrue(rows[case]["native_byte_identical_I0_D0"])
                self.assertTrue(result.original_source_unchanged)
        self.assertEqual(file_hash(DATA / "ifc" / "basic_tasks.ifc"), self.original_sha)

    def test_original_author_callable_both_without_full_task_success_claim(self):
        scores = {"test_15": 1.0, "test_16": 0.5}
        rows = {row["task_id"]:row for row in self.report["source_only_original_column_controls"]}
        self.assertEqual(set(rows), set(PUBLIC_CASES))
        for case in PUBLIC_CASES:
            with self.subTest(case=case):
                r = rows[case]
                self.assertEqual(r["original_author_D0_status"],"AUTHOR_SCORED")
                self.assertEqual(r["original_author_I0_status"],"AUTHOR_SCORED")
                self.assertEqual(r["original_author_D0_continuous_score"],scores[case])
                self.assertEqual(r["original_author_I0_continuous_score"],scores[case])
                self.assertTrue(r["original_author_numeric_score_equal"])
                self.assertFalse(r["strict_independent_full_task_success_verified"])
        self.assertEqual(rows["test_16"]["original_author_D0_metric_components"]["integrity_constraint"],0.0)
        self.assertEqual(rows["test_16"]["original_author_D0_metric_components"]["object_not_exists"],1.0)
        self.assertTrue(self.report["original_author_scores_are_not_blinded_LLM_trial_results"])

    def test_cohort_45_no_failure_imputation_or_subset_metric_inflation(self):
        from collections import Counter
        counts = Counter(row["new_scoring_status"]
                         for row in self.report["original45_intention_to_test_matrix"])
        self.assertEqual(counts, {
            "AUTHOR_SCORED_BOTH_DEVELOPER_ARMS":2,
            "AUTHOR_WORKER_FAILED_PINNED_REFERENCE_SOURCE_MISMATCH":2,
            "NOT_CURRENTLY_ESTABLISHED":41,
        })
        self.assertEqual(self.report["other_original_cases_not_exhaustively_evaluated"],41)
        self.assertEqual(self.report["original_author_scorable_with_both_D0_I0_confirmed_this_audit"],2)
        self.assertEqual(self.report["developer_both_arms_native_IFC_proven_task_count_including_v015"],4)
        self.assertFalse(self.report["independent_full_45_task_semantic_success_proven"])
        self.assertTrue(all(row["new_real_matched_LLM_D_I_result"] is None
                            for row in self.report["original45_intention_to_test_matrix"]))

    def test_i0_writer_python_imports_no_D0_scorer_or_hidden_targets(self):
        from tools import bibimbap_v016_original_column_i0
        code = Path(bibimbap_v016_original_column_i0.__file__).read_text(encoding="utf8")
        tree=ast.parse(code)
        modules=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                modules.append(node.module or "")
            if isinstance(node,ast.Import):
                modules.extend(alias.name for alias in node.names)
        self.assertFalse(any(x=="src" or x.startswith(("src.","tools.","data."))
                             for x in modules))
        self.assertNotIn("original_author_score", bibimbap_v016_original_column_i0.__dict__)

    def test_wrong_task_and_changed_public_target_or_direction_fails_closed(self):
        q15=self.public["test_15"]["public_question"]
        q16=self.public["test_16"]["public_question"]
        with self.assertRaises(ColumnI0Blocked):
            _parse_public_instruction("test_17",q15)
        with self.assertRaises(ColumnI0Blocked):
            _parse_public_instruction("test_15",q15.replace("by -3 meters","by +3 meters"))
        with self.assertRaises(ColumnI0Blocked):
            _parse_public_instruction("test_16",q16.replace("Delete the column","Move the column"))
        with self.assertRaises(ColumnI0Blocked):
            _parse_public_instruction("test_15","Move a random Column")

    def test_immutable_existing_output_and_wrong_unit_rejected(self):
        for case in PUBLIC_CASES:
            with self.subTest(case=case):
                output,_,_=self.i0_results[case]
                digest=file_hash(output)
                with self.assertRaises(ColumnI0Blocked):
                    run_imperative_column_i0(self.source,case,
                            self.public[case]["public_question"],output)
                self.assertEqual(file_hash(output),digest)
        orig=DATA/"ifc"/"basic_tasks.ifc"
        destination=self.tmp/"wrong_unit_output.ifc"
        with self.assertRaises(ColumnI0Blocked):
            run_imperative_column_i0(orig,"test_15",
                self.public["test_15"]["public_question"],destination)
        self.assertFalse(destination.exists())

    def test_source_only_reaudit_exact_json_reproducibility(self):
        fresh=audit(AUTHOR,DATA,FROZEN,MATRIX,PREV)
        self.assertEqual(fresh,self.report)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)


if __name__=="__main__":
    unittest.main()
