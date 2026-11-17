"""Prospective original BIBIMBAP test04 Create control positive/negative tests.

Original author grader only after independent D0+I0 candidate/oracle validation.
All candidate files are transient. No paid model, sandbox reset or data writes.
"""
from __future__ import annotations

import ast
import copy
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.util.unit
import numpy as np

from tools import audit_bibimbap_v032_original_column_pair as audit
from tools import bibimbap_v032_original_column_i0 as i0
from tools.bibimbap_matched25_tools import file_hash

BASE = Path(os.environ.get(
    "BIBIMBAP_EXPERIMENT_BASE", r"D:\\문서\\D__1_Projects\\202611"
))
AUTHOR = BASE / "bibimbap-author-upstream"
DATA = BASE / "bibimbap-author-data"
ORIGINAL = DATA / "ifc" / "basic_tasks.ifc"
REPORT = audit.ROOT / "reports" / (
    "bibimbap_v032_original_test04_column_D0_I0_native_semantic_pair_20261117.json"
)
FROZEN_REPORT_SHA = "65cd592b83b06ac161ff420982cb2f3378e850613f4645419690e06764987b2b"


class V032OriginalPublicCreatePairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen = json.loads(REPORT.read_text(encoding="utf8"))

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="bmb-v032-test-")
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)

    def test_01_original_45_creates_preserved_no_model_call(self):
        r = self.frozen
        self.assertEqual(r["original45_intention_to_test_denominator"], 45)
        self.assertEqual(r["original_public_task_id"], "test_04")
        self.assertEqual(r["public_create_operation"], "CREATE_ABSOLUTE_COLUMN")
        self.assertEqual(r["new_paid_provider_requests"], 0)
        self.assertEqual(r["matched_real_D_I_LLM_trials"], 0)
        self.assertIsNone(r["llm_model_success_estimate"])
        self.assertFalse(r["causal_representational_performance_inference_permitted"])
        self.assertFalse(r["full_original_45_create_coverage_claimed"])

    def test_02_native_semantic_tier_not_fabricated_byte_equality(self):
        r = self.frozen
        self.assertTrue(r["developer_only_new_actual_original_create_pair"])
        self.assertFalse(r["native_full_D0_I0_bytes_equal"])
        self.assertTrue(r["native_task_specific_Column_geometry_and_original_product_preservation_equal"])
        self.assertEqual(r["prior_v031_original45_full_native_D0_I0_byte_equal_witness_count"], 11)
        self.assertEqual(r["new_cumulative_original45_full_native_byte_equal_witness_count"], 11)
        self.assertEqual(r["new_separate_semantic_only_original_public_create_pair_count"], 1)
        self.assertEqual(r["original45_full_information_equivalence_proven"], 0)
        self.assertEqual(r["original45_full_native_write_capability_equivalence_proven"], 0)

    def test_03_original_author_scores_not_model_scores(self):
        for arm in ("D0", "I0"):
            d = self.frozen["original_author_score_" + arm]
            self.assertEqual(d["status"], "AUTHOR_SCORED")
            self.assertEqual(d["original_author_score"], 1.0)
            self.assertTrue(d["original_author_full_mark"])
            self.assertEqual(d["original_author_metrics"],
                             {"object_exists": 1., "right_location": 1.,
                              "right_dimensions": 1., "integrity_constraint": 1.})

    def test_04_actual_native_source_geometry_and_roots_covered(self):
        proof = self.frozen["native_independent_oracle_both_arms"]
        self.assertEqual(proof["original_source_native_root_count"], 358)
        self.assertEqual(proof["original_source_native_product_count"], 43)
        self.assertEqual(proof["original_source_product_geometry_verified_count"], 39)
        self.assertEqual(proof["original_source_product_without_geometry_count"], 4)
        self.assertEqual(proof["new_native_column_world_bbox_m"],
                         [12., 8., 0., 12.3, 8.3, 3.])
        self.assertEqual(proof["new_native_column_swept_solid_depth_mm"], 3000.)
        self.assertTrue(proof["all_original_product_geometry_preserved"])
        self.assertTrue(proof["one_and_only_one_created_physical_IfcColumn"])

    def test_05_frozen_report_bytes_versioned_and_source_pinned(self):
        self.assertEqual(file_hash(REPORT), FROZEN_REPORT_SHA)
        self.assertEqual(self.frozen["original_source_mm_IFC_sha256"], i0.SOURCE_SHA)
        self.assertEqual(self.frozen["original_public_question_sha256"], audit.QUESTION_SHA)
        self.assertEqual(self.frozen["frozen_v031_source_gate_sha256"], audit.FROZEN_GATE[1])
        self.assertEqual(file_hash(ORIGINAL), i0.SOURCE_SHA)

    def test_06_independent_imperative_writer_does_not_import_D0_or_grader(self):
        source = Path(i0.__file__).read_text(encoding="utf8")
        tree = ast.parse(source)
        modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            elif isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
        self.assertFalse(any("experimental_v2_column" in name
                             or "ifc_projection" in name
                             or "bibimbap_matched25_cli" in name
                             or "grader" in name or "author_worker" in name
                             for name in modules))
        self.assertNotIn("grade_author(", source)
        self.assertNotIn("compile_declarative_xml", source)
        self.assertEqual(i0.SPEC_METRES, (12., 8., 0., .3, .3, 3.))

    def test_07_real_original_python_I0_native_output_and_independent_oracle(self):
        out = self.dir / "new_I0.ifc"
        before = file_hash(ORIGINAL)
        result = i0.create_independent_public_column_i0(ORIGINAL, out)
        self.assertTrue(out.is_file())
        self.assertEqual(result["candidate_native_IFC_SHA256"], file_hash(out))
        proof = audit.verified_original_native_create(
            ORIGINAL, out, known_new_column_guid=result["new_native_IfcColumn_globalid"])
        self.assertEqual(proof["original_source_native_product_count"], 43)
        self.assertEqual(proof["new_native_column_world_bbox_m"],
                         [12., 8., 0., 12.3, 8.3, 3.])
        self.assertEqual(file_hash(ORIGINAL), before)

    def test_08_independent_writer_wrong_source_hash_is_rejected(self):
        tampered = self.dir / "bad_original.ifc"
        shutil.copy2(ORIGINAL, tampered)
        with tampered.open("ab") as file:
            file.write(b" ")
        self.assertNotEqual(file_hash(tampered), i0.SOURCE_SHA)
        out = self.dir / "uncreated.ifc"
        with self.assertRaisesRegex(i0.IndependentColumnI0Error, "hash mismatch"):
            i0.create_independent_public_column_i0(tampered, out)
        self.assertFalse(out.exists())

    def test_09_independent_writer_refuses_existing_output(self):
        dest = self.dir / "already_exists.ifc"
        dest.write_bytes(b"not a candidate")
        with self.assertRaisesRegex(i0.IndependentColumnI0Error, "output fresh"):
            i0.create_independent_public_column_i0(ORIGINAL, dest)
        self.assertEqual(dest.read_bytes(), b"not a candidate")

    def test_10_no_output_if_input_itself_is_output(self):
        with self.assertRaisesRegex(i0.IndependentColumnI0Error, "output fresh"):
            i0.create_independent_public_column_i0(ORIGINAL, ORIGINAL)
        self.assertEqual(file_hash(ORIGINAL), i0.SOURCE_SHA)

    def test_11_native_oracle_rejects_untouched_input_no_creation(self):
        copy = self.dir / "unchanged.ifc"
        shutil.copy2(ORIGINAL, copy)
        with self.assertRaisesRegex(audit.OriginalColumnV032Blocked,
                                    "Native result adds non-Column product|Exactly one native IFC product"):
            audit.verified_original_native_create(ORIGINAL, copy)

    def test_12_native_oracle_rejects_forged_new_product_GUID(self):
        out = self.dir / "created.ifc"
        i0.create_independent_public_column_i0(ORIGINAL, out)
        with self.assertRaisesRegex(audit.OriginalColumnV032Blocked, "Declared independent"):
            audit.verified_original_native_create(
                ORIGINAL, out, known_new_column_guid="0" * 22)

    def test_13_native_oracle_rejects_displaced_created_column(self):
        out = self.dir / "created.ifc"
        summary = i0.create_independent_public_column_i0(ORIGINAL, out)
        model = ifcopenshell.open(str(out))
        column = model.by_guid(summary["new_native_IfcColumn_globalid"])
        mat = np.eye(4)
        mat[:3, 3] = [15., 8.15, 0.]
        # This test mutates only a temporary result, never the original IFC.
        # Existing original scene is not a scoring artifact.
        metric = ifcopenshell.util.unit.convert_file_length_units(model, "METER")
        edited = metric.by_guid(column.GlobalId)
        ifcopenshell.api.geometry.edit_object_placement(
            metric, product=edited, matrix=mat)
        ifcopenshell.util.unit.convert_file_length_units(
            metric, "MILLIMETER").write(str(out))
        with self.assertRaisesRegex(audit.OriginalColumnV032Blocked,
                                    "world coordinates"):
            audit.verified_original_native_create(ORIGINAL, out)

    def test_14_author_grade_spoof_rejected_after_real_pair(self):
        from tools import bibimbap_matched25_cli
        with patch.object(bibimbap_matched25_cli, "grade_author",
                          return_value={"status": "AUTHOR_SCORED",
                                        "original_author_score": .5,
                                        "original_author_full_mark": False,
                                        "original_author_metrics": {}}):
            with self.assertRaisesRegex(audit.OriginalColumnV032Blocked,
                                        "not full on both"):
                audit.pair_public_test04(audit.ROOT, AUTHOR, DATA)
        self.assertEqual(file_hash(ORIGINAL), i0.SOURCE_SHA)

    def test_15_any_mutated_frozen_v031_report_blocks_launch(self):
        r = self.dir / "reports"
        r.mkdir()
        target = self.dir / audit.FROZEN_GATE[0]
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(b"changed")
        with self.assertRaisesRegex(audit.OriginalColumnV032Blocked, "hash mismatch"):
            audit.pair_public_test04(self.dir, AUTHOR, DATA)

    def test_16_no_hidden_target_GUID_or_question_text_in_frozen_report(self):
        text = REPORT.read_text(encoding="utf8").lower()
        for token in ("hidden_target", "ground_truth", "original_public_question_text",
                      "author_private_target_guid", "answer_key", "model_prompt_body"):
            self.assertNotIn(token, text)
        self.assertLess(REPORT.stat().st_size, 13000)

    def test_17_new_original_case_pair_replay_task_semantic_metrics_stable(self):
        second = audit.pair_public_test04(audit.ROOT, AUTHOR, DATA)
        expected = self.frozen
        self.assertTrue(second["native_task_specific_Column_geometry_and_original_product_preservation_equal"])
        self.assertFalse(second["native_full_D0_I0_bytes_equal"])
        self.assertEqual(second["original_author_score_D0"], expected["original_author_score_D0"])
        self.assertEqual(second["original_author_score_I0"], expected["original_author_score_I0"])
        self.assertEqual(second["native_independent_oracle_both_arms"],
                         expected["native_independent_oracle_both_arms"])
        self.assertEqual(second["new_cumulative_original45_full_native_byte_equal_witness_count"], 11)
        self.assertEqual(file_hash(ORIGINAL), i0.SOURCE_SHA)


if __name__ == "__main__":
    unittest.main()
