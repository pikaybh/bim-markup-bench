"""v0.15 independent public-IFC Python I0 versus frozen XML D0 safety gates.

Developer-only and source-only. Original scorer target values never flow into
I0 generation, full IFC scene oracle remains external to both code writers.
"""
from __future__ import annotations

import ast
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest

import ifcopenshell
import ifcopenshell.util.unit

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v015_imperative_i0 import (
    ImperativeI0Blocked, compile_imperative_i0, select_original_windows,
)
from tools.audit_bibimbap_v015_original_i0_d0 import audit
from tools.oracle_bibimbap_v14_window_delete import verify_source_native_window_delete


BASE = Path(os.environ.get(
    "BIBIMBAP_EXPERIMENT_BASE", r"D:\문서\D__1_Projects\202611"
))
HERE = Path(__file__).resolve().parents[1]
AUTHOR = BASE / "bibimbap-author-upstream"
DATA = BASE / "bibimbap-author-data"
REPORT = HERE / "reports" / "bibimbap_v015_original_hosted_window_i0_d0_parity_20261114.json"
FROZEN = HERE / "reports" / "bibimbap_v014_original_geometry18_19_native_hosted_window_developer_d0_20261114.json"
CASES = ("geometry_test_18", "geometry_test_19")


class IndependentOriginalI0D0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not all(x.exists() for x in (AUTHOR, DATA, REPORT, FROZEN)):
            raise unittest.SkipTest("Pinned original public dataset or v0.15 report not mounted")
        cls.report = json.loads(REPORT.read_text(encoding="utf8"))
        cls.frozen = json.loads(FROZEN.read_text(encoding="utf8"))
        cls.public = {x["test_id"]: x for x in public_45(AUTHOR, DATA)}
        cls._temp = tempfile.TemporaryDirectory(prefix="bmb-144-tests-")
        cls.root = Path(cls._temp.name)
        cls.cases = {}
        for task in CASES:
            original = DATA / "ifc" / cls.public[task]["original_source_ifc_relpath"]
            normalized = cls.root / (task + "_metres.ifc")
            ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(original)), "METER"
            ).write(str(normalized))
            out = cls.root / (task + "_i0.ifc")
            candidate = compile_imperative_i0(
                normalized, task, cls.public[task]["public_question"], out
            )
            cls.cases[task] = {
                "normalized": normalized, "original": original,
                "output": out, "i0": candidate,
                "proof": verify_source_native_window_delete(
                    normalized, out, candidate.selected_original_window_guids,
                    expected_original_source_sha256=file_hash(normalized),
                    expected_output_sha256=file_hash(out),
                ),
            }

    @classmethod
    def tearDownClass(cls):
        cls._temp.cleanup()

    def test_native_original_source_schema_and_source_nonmutation(self):
        self.assertEqual(_head(AUTHOR), AUTHOR_SHA)
        self.assertEqual(_head(DATA), DATA_SHA)
        for task, row in self.cases.items():
            with self.subTest(task=task):
                self.assertEqual(file_hash(row["original"]),
                                 self.public[task]["original_ifc_sha256"])
                self.assertEqual(file_hash(row["normalized"]), row["i0"].source_sha256)
                self.assertTrue(row["i0"].original_file_unchanged)
                self.assertEqual(row["i0"].original_source_schema, "IFC4X3")

    def test_i0_native_output_independently_proven_both_real_sources(self):
        for task, row in self.cases.items():
            with self.subTest(task=task):
                self.assertEqual(
                    row["proof"]["status"],
                    "INDEPENDENT_ORIGINAL_NATIVE_IFC4X3_WINDOW_ONLY_DELETE_ORACLE_PASS_V014",
                )
                self.assertEqual(len(row["i0"].selected_original_window_guids), 2)
                self.assertTrue(row["proof"]["original_host_wall_opening_unchanged"])

    def test_d0_i0_native_original_evidence_and_hash_match(self):
        self.assertEqual(len(self.report["cases"]), 2)
        frozen = {r["original_public_task_id"]: r for r in
                  self.frozen["source_original_IFC4X3_geometry_test_18_19_original_frozen_D0_cases"]}
        observed = {r["public_task_id"]: r for r in self.report["cases"]}
        self.assertEqual(set(observed), set(CASES))
        for task in CASES:
            with self.subTest(task=task):
                row = self.cases[task]
                exp = observed[task]
                self.assertEqual(exp["original_native_ifc_I0_candidate_sha256"],
                                 row["i0"].result_sha256)
                self.assertEqual(exp["frozen_declarative_D0_reproduced_sha256"],
                                 frozen[task]["original_native_candidate_sha256"])
                self.assertEqual(row["i0"].result_sha256,
                                 frozen[task]["original_native_candidate_sha256"])
                self.assertEqual(
                    exp["native_target_guid_set_sha256"],
                    sha256("|".join(row["i0"].selected_original_window_guids).encode("ascii")).hexdigest(),
                )
                self.assertTrue(exp["same_original_source_root_deletion_closure"])
                self.assertTrue(exp["same_unrelated_world_native_product_mesh_preservation"])
                self.assertTrue(exp["candidate_ifc_bytes_identical_not_required"])

    def test_original_author_worker_and_missing_source_targets_never_scored(self):
        observed = {r["public_task_id"]: r for r in self.report["cases"]}
        self.assertEqual(self.report["original_population_45_unmodified"], 45)
        self.assertFalse(self.report["fully_blinded_or_preregistered_LLM_experiment"])
        self.assertEqual(self.report["paid_model_or_provider_calls"], 0)
        self.assertIsNone(self.report["original_author_scored_task_successes_from_this_audit"])
        for task, missing in (("geometry_test_18", 4), ("geometry_test_19", 1)):
            with self.subTest(task=task):
                x = observed[task]["postfreeze_original_author_diagnostic"]
                self.assertEqual(x["source_original_author_targets_absent_before_edit"], missing)
                self.assertEqual(x["original_author_worker_status"], "AUTHOR_WORKER_FAILED")
                self.assertIsNone(x["original_author_numeric_score"])
                self.assertTrue(x["source_original_author_window_GUID_values_never_emitted"])
                self.assertTrue(x["retained_original_opening_fails_author_openings_deleted"])
                self.assertTrue(
                    x["scratch_deleted_original_opening_fails_author_nontarget_preservation"])

    def test_i0_authoring_code_is_separate_from_D0_scorer_or_hidden_GT(self):
        # Static import-graph safeguard: I0 implementation must not depend
        # on D0 runtime, frozen candidate or original grader modules.
        from tools import bibimbap_v015_imperative_i0
        tree = ast.parse(Path(bibimbap_v015_imperative_i0.__file__).read_text(encoding="utf8"))
        deps = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                deps.append(node.module or "")
            if isinstance(node, ast.Import):
                deps.extend(alias.name for alias in node.names)
        self.assertFalse(any(
            name == "tools" or name.startswith(("tools.", "src.", "data."))
            for name in deps
        ))
        self.assertNotIn("original_author_score", bibimbap_v015_imperative_i0.__dict__)

    def test_invalid_task_and_public_semantic_drift_rejected(self):
        row = self.cases["geometry_test_18"]
        model = ifcopenshell.open(str(row["normalized"]))
        question = self.public["geometry_test_18"]["public_question"]
        with self.assertRaises(ImperativeI0Blocked):
            select_original_windows("geometry_test_20", question, model)
        with self.assertRaises(ImperativeI0Blocked):
            select_original_windows("geometry_test_18", question.replace("+X is east", "+X is west"), model)
        task19 = self.cases["geometry_test_19"]
        with self.assertRaises(ImperativeI0Blocked):
            select_original_windows("geometry_test_19", "delete windows opposite to GUID UNKNOWN", ifcopenshell.open(str(task19["normalized"])))

    def test_immutable_destination_and_raw_millimetre_source_fail_closed(self):
        row = self.cases["geometry_test_18"]
        path = row["output"]
        prior = file_hash(path)
        source_sha = file_hash(row["normalized"])
        with self.assertRaises(ImperativeI0Blocked):
            compile_imperative_i0(row["normalized"], "geometry_test_18",
                                  self.public["geometry_test_18"]["public_question"], path)
        self.assertEqual(file_hash(path), prior)
        self.assertEqual(file_hash(row["normalized"]), source_sha)
        with self.assertRaises(ImperativeI0Blocked):
            compile_imperative_i0(row["original"], "geometry_test_18",
                                  self.public["geometry_test_18"]["public_question"],
                                  self.root / "must_not_exist.ifc")
        self.assertFalse((self.root / "must_not_exist.ifc").exists())

    def test_source_only_reaudit_report_byte_stable_and_no_original_change(self):
        public_shas = {case: file_hash(self.cases[case]["original"]) for case in CASES}
        another = audit(AUTHOR, DATA, FROZEN)
        self.assertEqual(another, self.report)
        self.assertEqual(public_shas,
                         {case: file_hash(self.cases[case]["original"]) for case in CASES})
        self.assertEqual(_head(AUTHOR), AUTHOR_SHA)
        self.assertEqual(_head(DATA), DATA_SHA)


if __name__ == "__main__":
    unittest.main()
