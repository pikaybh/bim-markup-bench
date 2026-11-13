"""Frozen candidate v0.11 forensic evidence tests — original author not edited.

These tests run the same four source-only D0 candidates to establish exact
candidate SHA continuity, then inspect only public author metric helpers
after candidate and original-native oracle are frozen. No hidden GT or model
calls. Previous D0 outcome and original 45 denominator remain immutable.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from tools.audit_bibimbap_v11_metric_forensics import (
    PINNED,_prior,run,
)
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",
                         r"D:\문서\D__1_Projects\202611"))
ROOT=Path(__file__).resolve().parents[1]
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"


class FrozenD0MetricForensicsV11(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not AUTHOR.exists() or not DATA.exists():
            raise unittest.SkipTest("Original pinned author and dataset must be mounted")
        cls.findings=run(ROOT,AUTHOR,DATA)
        cls.cases={
            row["original_public_task_id"]:row
            for row in cls.findings["cases"]
        }

    def test_original_four_frozen_previous_D0_artifacts_are_unmodified(self):
        for key,declared in PINNED.items():
            with self.subTest(task=key):
                filename=ROOT/"reports"/declared["prior_report"]
                self.assertEqual(file_hash(filename),
                                 declared["prior_report_sha256"])
                expected,grade=_prior(ROOT,key)
                self.assertTrue(grade["status"]=="AUTHOR_SCORED")
                self.assertFalse(grade["original_author_full_mark"])
                self.assertEqual(self.cases[key]["original_public_ifc_sha256"],
                                 expected["original"])

    def test_all_previous_original_source_native_candidate_ifc_hashes_unchanged(self):
        self.assertEqual(set(self.cases),set(PINNED))
        for task,row in self.cases.items():
            expected,grade=_prior(ROOT,task)
            with self.subTest(task=task):
                self.assertEqual(row["recreated_native_candidate_sha256"],
                                 expected["native"])
                self.assertEqual(row["recreated_original_units_candidate_sha256"],
                                 expected["mm"])
                self.assertTrue(row["candidate_exactly_byte_identical_to_prior_frozen_D0"])
                self.assertTrue(row["hidden_grader_reference_ifc_not_loaded"])
                self.assertTrue(row["developer_candidate_not_rewritten_to_improve_score"])

    def test_ifc2x3_space_original_author_missing_direct_containment(self):
        evidence=self.cases["geometry_test_04"][
            "public_author_component_forensics"]
        checks=evidence["evaluated_public_subchecks"]
        self.assertEqual(checks,{
            "original_author_check_spatial_containment":0.,
            "original_author_check_clash_integrity":True,
            "original_author_check_all_prior_root_guids_preserved":1.,
        })
        native=evidence["native_evidence"]
        self.assertTrue(native["original_source_storey_aggregate_relation_used"])
        self.assertEqual(native["new_space_ifc_class"],"IfcSpace")
        self.assertEqual(native["new_IfcSpace_direct_containment_relations"],0)
        self.assertAlmostEqual(sum(checks.values())/3,2/3)

    def test_original_slab_scoring_location_requires_center_preservation(self):
        evidence=self.cases["geometry_test_14"][
            "public_author_component_forensics"]
        checks=evidence["evaluated_public_subchecks"]
        self.assertFalse(checks["original_author_slab_location_center_pass"])
        self.assertTrue(checks["original_author_integrity"]["integrity_constraint"])
        self.assertAlmostEqual(
            evidence["native_evidence"]["frozen_candidate_center_shift_original_units"][1],
            .75,places=5)
        self.assertTrue(
            evidence["native_evidence"]["original_lower_world_Y_remains_fixed"])
        self.assertEqual(checks["original_author_center_coordinate_tolerance_original_units"],.05)

    def test_original_typed_mapped_column_height_introduced_three_author_clashes(self):
        evidence=self.cases["topological_test_11"][
            "public_author_component_forensics"]
        checks=evidence["evaluated_public_subchecks"]
        self.assertTrue(
            checks["original_author_check_integrity"]["non_target_elements_unchanged"])
        self.assertFalse(
            checks["original_author_check_integrity"]["no_new_clashes"])
        self.assertEqual(checks["original_author_new_clash_pair_count"],3)
        self.assertEqual(checks["original_author_clash_pairs_before"],1)
        self.assertEqual(checks["original_author_clash_pairs_after"],4)
        pair_ids=[set(pair) for pair in checks["original_author_new_clash_pairs"]]
        self.assertEqual(sum(
            "0dxtXCDSn2mfP92h$AiPMM" in pair for pair in pair_ids
        ),2)

    def test_original_delete_all_target_relation_subchecks_pass_but_root_guard_fails(self):
        evidence=self.cases["topological_test_17"][
            "public_author_component_forensics"]
        checks=evidence["evaluated_public_subchecks"]
        self.assertTrue(checks[
            "original_author_all_target_delete_relation_checks_pass"])
        self.assertFalse(checks["original_author_non_target_elements_unchanged"])
        self.assertEqual(len(checks[
            "original_author_public_four_subchecks_by_source_column"]),5)
        self.assertTrue(all(all(check.values()) for check in checks[
            "original_author_public_four_subchecks_by_source_column"].values()))
        native=evidence["native_evidence"]
        self.assertEqual(native[
            "removed_original_root_objects_excluding_removed_Column_GUIDs"],35)
        self.assertEqual(native[
            "original_roots_considered_non_target_but_deleted_with_owned_Column"],{
                "IfcPropertySet":15,
                "IfcRelDefinesByProperties":15,
                "IfcRelDefinesByType":5,
            })

    def test_four_exact_prior_original_author_grades_not_rewritten(self):
        self.assertEqual({
            task:case["frozen_original_author_score"]["original_author_score"]
            for task,case in self.cases.items()
        },{
            "geometry_test_04":.916675,
            "geometry_test_14":2/3,
            "topological_test_11":2/3,
            "topological_test_17":.5,
        })
        self.assertTrue(self.findings["historical_real_model_45_scores_untouched"])
        self.assertEqual(self.findings["new_paid_model_calls"],0)
        self.assertEqual(self.findings["original_45_task_population"],45)
        self.assertFalse(self.findings["native_all_45_task_parity_not_proven"] is False)

    def test_source_only_diagnostic_no_hidden_reference_or_scorer_modification(self):
        self.assertTrue(self.findings["no_hidden_reference_or_target_used_for_candidate"])
        self.assertFalse(self.findings["frozen_original_grader_edited"])
        self.assertFalse(self.findings["native_all_45_task_parity_not_proven"] is False)
        for item in self.cases.values():
            self.assertTrue(item["original_author_test_source_not_changed"])
            self.assertIn("PASS",item["independent_native_ifc_oracle_status"])
            self.assertIn("cause_class",item["public_author_component_forensics"])

    def test_evidence_generation_is_deterministic_without_mutating_input(self):
        # Identical original IFC and exact source-only fixtures produce
        # identical complete scored-component diagnostic evidence JSON.
        repeated=run(ROOT,AUTHOR,DATA)
        self.assertEqual(
            json.dumps(repeated,sort_keys=True),
            json.dumps(self.findings,sort_keys=True),
        )

    def test_reject_invalid_case_selector_and_corrupted_prior_D0_report(self):
        with self.assertRaisesRegex(ValueError,"Unknown frozen"):
            run(ROOT,AUTHOR,DATA,only=["not_original_bibimbap_task"])
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/"reports").mkdir()
            name=PINNED["topological_test_17"]["prior_report"]
            (root/"reports"/name).write_bytes(b"tampered D0 evidence")
            with self.assertRaisesRegex(ValueError,"Frozen D0"):
                _prior(root,"topological_test_17")


if __name__=="__main__":
    unittest.main()
