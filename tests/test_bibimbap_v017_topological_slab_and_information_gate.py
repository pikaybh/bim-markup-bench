"""v0.17 original IFC topological Slab I0 and 45-case information parity.

Only pinned publicly available author/source data, no paid model inference.
Historical D0 and author grades are read only after an independently frozen
native imperative result; no original source/scorer/GT is ever modified.
"""
from __future__ import annotations

import ast
from collections import Counter
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
from tools.bibimbap_v017_independent_slab_on_slab_i0 import (
    run_original_topological_slab_i0,
    OriginalTopologicalSlabI0Blocked,
    parse_public_topological_slab_question,
)
from tools.oracle_bibimbap_slab_v04 import (
    verify_update, IndependentSlabOracleError,
)
from tools.audit_bibimbap_v017_topological_slab import (
    audit as audit_slab, FROZEN_V04_SHA,
)
from tools.audit_bibimbap_v017_information_parity_gate import (
    audit as audit_gate, MatchedInformationGateError, FROZEN_V013_SHA,
)

BASE = Path(os.getenv("BIBIMBAP_EXPERIMENT_BASE", r"D:\문서\D__1_Projects\202611"))
HERE = Path(__file__).resolve().parents[1]
AUTHOR = BASE / "bibimbap-author-upstream"
DATA = BASE / "bibimbap-author-data"
FROZEN_D0 = HERE / "reports" / "bibimbap_v04_slab_developer_d0_20261113.json"
FROZEN_V013 = HERE / "reports" / "bibimbap_v013_original45_safe_native_read_catalog_20261114.json"
PRIOR_V016 = HERE / "reports" / "bibimbap_v016_original45_scoreability_and_column_parity_20261114.json"
OUT_SLAB = HERE / "reports" / "bibimbap_v017_original_topological_slab_I0_D0_author_parity_20261114.json"
OUT_GATE = HERE / "reports" / "bibimbap_v017_original45_information_parity_gate_20261114.json"
SHA_SLAB = "c6b02877a3f031c8f5435222b65db4a0fef04568119eaa750586f106d53231e8"
SHA_GATE = "c2683de1705b92ebe0ce8472c6a870b98c54c668e387ddf80c9377cdb2e88078"
TASK = "topological_test_15"


class OriginalTopologicalSlabAndFairnessGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        required = (FROZEN_D0, FROZEN_V013, PRIOR_V016, OUT_SLAB, OUT_GATE)
        if not all(p.is_file() for p in required):
            raise unittest.SkipTest("Missing pinned original public source-only evidence")
        if not AUTHOR.is_dir() or not DATA.is_dir():
            raise unittest.SkipTest("Pinned original author/source checkouts unavailable")
        cls.public = {t["test_id"]: t for t in public_45(AUTHOR, DATA)}
        cls.task = cls.public[TASK]
        cls.original = DATA / "ifc" / cls.task["original_source_ifc_relpath"]
        cls.original_sha = file_hash(cls.original)
        cls.tmp = tempfile.TemporaryDirectory(prefix="bmb-v017-proof-")
        root = Path(cls.tmp.name)
        cls.normalized = root / "original_public_source_m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(cls.original)), "METER"
        ).write(str(cls.normalized))
        cls.out = root / "imperative_candidate.ifc"
        cls.actual = run_original_topological_slab_i0(
            cls.normalized, cls.task["public_question"], cls.out
        )
        cls.native_oracle = verify_update(
            cls.normalized, cls.out, cls.actual.upper_public_guid,
            kind="move", delta=(0., 0., cls.actual.native_world_z_delta_m),
        )
        cls.slab_report = json.loads(OUT_SLAB.read_text(encoding="utf8"))
        cls.gate_report = json.loads(OUT_GATE.read_text(encoding="utf8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_original_public_task_pins_source_and_real_move(self):
        self.assertEqual(_head(AUTHOR), AUTHOR_SHA)
        self.assertEqual(_head(DATA), DATA_SHA)
        self.assertEqual(len(self.public), 45)
        self.assertEqual(self.original_sha, self.task["original_ifc_sha256"])
        self.assertEqual(file_hash(FROZEN_D0), FROZEN_V04_SHA)
        self.assertEqual(file_hash(FROZEN_V013), FROZEN_V013_SHA)
        self.assertEqual(file_hash(OUT_SLAB), SHA_SLAB)
        self.assertEqual(file_hash(OUT_GATE), SHA_GATE)
        self.assertEqual(file_hash(self.original), self.original_sha)
        self.assertEqual(self.slab_report["original_source_ifc_sha256"], self.original_sha)

    def test_strict_native_ifc_only_oracle_and_developer_candidate_same_as_D0(self):
        self.assertTrue(self.actual.original_source_byte_identical)
        self.assertTrue(self.actual.native_copy_on_write_point)
        self.assertAlmostEqual(self.actual.native_world_z_delta_m, -0.05, places=8)
        self.assertAlmostEqual(self.actual.upper_lower_original_xy_overlap_m2,1.0,places=6)
        self.assertEqual(
            self.native_oracle["status"], "INDEPENDENT_NATIVE_SLAB_MOVE_PHYSICAL_IFC_VALIDATED")
        self.assertEqual(file_hash(self.out), self.native_oracle["output_sha256"])
        self.assertEqual(
            file_hash(self.out),
            self.slab_report["frozen_rebuilt_XML_D0_candidate_native_sha256"],
        )
        self.assertTrue(self.slab_report["identical_complete_native_IFC_D0_vs_I0"])
        self.assertTrue(self.slab_report["original_public_units_candidate_sha256_same"])
        self.assertEqual(file_hash(self.original), self.original_sha)

    def test_original_author_metrics_and_no_prohibited_claims(self):
        self.assertEqual(
            self.slab_report["original_author_scorer_I0"]["status"], "AUTHOR_SCORED"
        )
        self.assertEqual(
            self.slab_report["original_author_scorer_D0"]["status"], "AUTHOR_SCORED"
        )
        self.assertEqual(
            self.slab_report["original_author_scorer_I0"]["original_author_score"],1.0)
        self.assertEqual(
            self.slab_report["original_author_scorer_D0"]["original_author_score"],1.0)
        self.assertTrue(
            self.slab_report["author_result_not_independent_full_task_success"])
        self.assertTrue(
            self.slab_report["independently_selected_public_task_previously_D0_scored_nonblinded"])
        self.assertTrue(
            self.slab_report["original_test14_height_semantics_ambiguity"][
                "public_text_semantics_not_independently_disambiguated"])
        self.assertEqual(self.slab_report["new_matched_LLM_model_trials"],0)
        self.assertEqual(self.slab_report["new_paid_provider_calls"],0)
        self.assertFalse(self.slab_report["full_45_native_write_parity_proven"])

    def test_original_all45_counts_and_unverified40_still_unscored(self):
        self.assertEqual(
            self.slab_report["original_45_create_update_delete_counts"],
            {"create":15,"update":15,"delete":15})
        self.assertEqual(
            len(self.slab_report["all_45_public_intention_to_test"]),45)
        self.assertEqual(
            set(x["task_id"] for x in self.slab_report["all_45_public_intention_to_test"]),
            set(self.public))
        self.assertEqual(
            Counter(x["new_scoring_status"] for x in
                    self.slab_report["all_45_public_intention_to_test"]),
            Counter({
                "AUTHOR_SCORED_BOTH_DEVELOPER_ARMS":3,
                "AUTHOR_WORKER_FAILED_PINNED_REFERENCE_SOURCE_MISMATCH":2,
                "NOT_CURRENTLY_ESTABLISHED":40,
            }),
        )
        self.assertTrue(
            all(not x["excluded_from_original_45_denominator"]
                for x in self.slab_report["all_45_public_intention_to_test"]))

    def test_information_parity_typed_missing_native_all_45(self):
        self.assertEqual(self.gate_report["actual_original_public_task_count"],45)
        self.assertEqual(self.gate_report["source_unique_original_IFC_count"],31)
        self.assertEqual(
            self.gate_report[
                "original_native_has_more_products_than_safe_typed_XML_case_count"],45
        )
        self.assertEqual(
            self.gate_report["strict_full_original_source_information_parity_proven_case_count"],0
        )
        self.assertEqual(
            len(self.gate_report["all_45_task_information_parity_audit"]),45
        )
        for row in self.gate_report["all_45_task_information_parity_audit"]:
            with self.subTest(task=row["task_id"]):
                self.assertGreater(
                    row["native_original_ifc_product_count"],
                    row["safe_typed_XML_product_count"],
                )
                self.assertEqual(
                    row["native_original_products_not_in_safe_typed_XML"],
                    row["native_original_ifc_product_count"] -
                    row["safe_typed_XML_product_count"],
                )
                self.assertFalse(
                    row["eligible_for_strict_full_original_information_equivalent_paid_trial"])
                self.assertIsNone(row["real_matched_LLM_D_vs_I_attempt"])

    def test_strict_trial_not_auto_authorized(self):
        self.assertEqual(
            self.gate_report["status"],
            "STRICT_FULL_ORIGINAL_IFC_INFORMATION_PARITY_GATE_BLOCKED"
        )
        self.assertFalse(self.gate_report["matched_LLM_trial_paid_execution_authorized"])
        self.assertTrue(self.gate_report["research_only_explicit_no_launch_enforcement"])
        self.assertEqual(self.gate_report["new_real_matched_model_inference_calls"],0)
        self.assertEqual(self.gate_report["new_paid_usd"],0)
        self.assertTrue(self.gate_report["relevance_of_omitted_products_to_specific_task_NOT_proven"])
        self.assertTrue(self.gate_report["absence_of_all_unnecessary_info_NOT_proven"])

    def test_public_question_validation_and_no_source_writes_for_invalid_prompt(self):
        question=self.task["public_question"]
        upper, lower=parse_public_topological_slab_question(question)
        self.assertNotEqual(upper,lower)
        with self.assertRaises(OriginalTopologicalSlabI0Blocked):
            parse_public_topological_slab_question(question.replace("lays on","floats above"))
        with self.assertRaises(OriginalTopologicalSlabI0Blocked):
            parse_public_topological_slab_question(
                question.replace(lower,upper))
        with self.assertRaises(OriginalTopologicalSlabI0Blocked):
            run_original_topological_slab_i0(
                self.normalized, question, self.out
            )
        with self.assertRaises(OriginalTopologicalSlabI0Blocked):
            run_original_topological_slab_i0(
                self.original, question, Path(self.tmp.name)/"unit_mismatch.ifc"
            )
        self.assertEqual(file_hash(self.original), self.original_sha)

    def test_native_oracle_detects_wrong_target_delta(self):
        clone=Path(self.tmp.name)/"wrong_vertical_position.ifc"
        f=ifcopenshell.open(str(self.out))
        p=f.by_guid(self.actual.upper_public_guid).ObjectPlacement.RelativePlacement.Location
        before=tuple(p.Coordinates)
        p.Coordinates=(before[0],before[1],before[2]+0.25)
        f.write(str(clone))
        with self.assertRaises(IndependentSlabOracleError):
            verify_update(
                self.normalized,clone,self.actual.upper_public_guid,
                kind="move",delta=(0.,0.,self.actual.native_world_z_delta_m)
            )

    def test_i0_only_public_source_ifc_and_standard_library_imports(self):
        from tools import bibimbap_v017_independent_slab_on_slab_i0
        source=Path(bibimbap_v017_independent_slab_on_slab_i0.__file__).read_text(encoding="utf8")
        tree=ast.parse(source)
        imported=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                imported.append(node.module or "")
            if isinstance(node,ast.Import):
                imported.extend(alias.name for alias in node.names)
        self.assertFalse(any(x=="tools" or x.startswith(("tools.","src."))
                             for x in imported))
        self.assertNotIn("grade_author",source)
        self.assertNotIn("compile_declarative_xml",source)
        self.assertNotIn("original_author_scorer",source)

    def test_gate_tampered_v013_frozen_hash_fails_closed(self):
        corrupted=Path(self.tmp.name)/"tampered_native_census.json"
        corrupted.write_text(FROZEN_V013.read_text(encoding="utf8")+"\n", encoding="utf8")
        with self.assertRaises(MatchedInformationGateError):
            audit_gate(AUTHOR,DATA,corrupted,OUT_SLAB)

    def test_complete_information_gate_repeat_reproduces_json(self):
        self.assertEqual(
            audit_gate(AUTHOR,DATA,FROZEN_V013,OUT_SLAB),
            self.gate_report,
        )

    def test_original_topological_audit_repeat_reproduces_json(self):
        self.assertEqual(
            audit_slab(AUTHOR,DATA,FROZEN_D0,PRIOR_V016),
            self.slab_report,
        )
        self.assertEqual(file_hash(self.original),self.original_sha)


if __name__ == "__main__":
    unittest.main()
