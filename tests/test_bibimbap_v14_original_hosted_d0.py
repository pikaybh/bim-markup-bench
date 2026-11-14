"""v0.14 original BIBIMBAP public geometry18/19 developer D0 source audit.

The true original author grader fails on *its own* missing original-source
GlobalIds (4/6 target roots geometry18; 1/2 geometry19) after the
developer-chosen candidate is frozen and an independent source-native IFC
oracle passes. Record UNSCORABLE, never 0, 1 or a new real model score.
No author target can enter source selection or native compiler paths.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest

import ifcopenshell
import ifcopenshell.util.unit

from tools.audit_bibimbap_v14_original_hosted_d0 import (
    audit,_source_only_selection,PUBLIC_CASES,
)
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",
                         r"D:\문서\D__1_Projects\202611"))
ROOT=Path(__file__).resolve().parents[1]
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v014_original_geometry18_19_native_hosted_window_developer_d0_20261114.json"


class V14OriginalAuthorD0SourceOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (AUTHOR.is_dir() and DATA.is_dir() and REPORT.is_file()):
            raise unittest.SkipTest("Original pinned author + public IFC dataset not present")
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))
        cls.rows={
            r["original_public_task_id"]:r
            for r in cls.report["source_original_IFC4X3_geometry_test_18_19_original_frozen_D0_cases"]
        }
        cls.public={r["test_id"]:r for r in public_45(AUTHOR,DATA)}

    def test_original_public_45_denominator_remains_45(self):
        self.assertEqual(len(self.public),45)
        self.assertEqual(self.report["original_public_45_denominator_retained"],45)
        self.assertEqual(set(self.rows),set(PUBLIC_CASES))
        self.assertEqual(self.report["original_author_revision"],AUTHOR_SHA)
        self.assertEqual(self.report["original_dataset_revision"],DATA_SHA)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)

    def test_original_public_question_and_original_ifc_identity_untouched(self):
        for tid,row in self.rows.items():
            self.assertEqual(
                row["original_public_question_sha256"],
                self.public[tid]["public_question_sha256"])
            self.assertEqual(
                row["original_public_ifc_sha256"],
                self.public[tid]["original_ifc_sha256"])
            self.assertEqual(
                file_hash(DATA/"ifc"/self.public[tid]["original_source_ifc_relpath"]),
                row["original_public_ifc_sha256"])
            self.assertEqual(row["original_native_schema"],"IFC4X3")

    def test_source_only_original_west_selection_exact_two_not_from_hidden(self):
        row=self.rows["geometry_test_18"]
        self.assertEqual(len(row[
            "developer_source_only_original_public_selected_window_guids"]),2)
        intent=row["developer_source_only_native_geometric_Window_selection"]
        self.assertEqual(intent["original_question_direction_semantics"],
                         "+X east, west is minimum original world X")
        self.assertEqual(len(intent["selected_original_native_source_west_wall_guids"]),1)
        self.assertTrue(intent["source_public_question_excludes_hidden_target"])

    def test_source_only_original_opposite_wall_selection_uses_only_named_public(self):
        row=self.rows["geometry_test_19"]
        intent=row["developer_source_only_native_geometric_Window_selection"]
        self.assertEqual(intent["public_original_named_reference_wall_guid"],
                         "1mRYVM4YfFFBRkcbz1hHbM")
        self.assertEqual(len(intent[
            "developer_original_native_opposite_host_wall_guids"]),1)
        self.assertEqual(len(intent["developer_original_opposite_wall_window_overlap_m"]),2)
        self.assertEqual(len(row[
            "developer_source_only_original_public_selected_window_guids"]),2)
        self.assertTrue(intent["source_public_question_excludes_hidden_target"])

    def test_actual_original_author_worker_is_unscoreable_not_claimed_zero(self):
        for tid,row in self.rows.items():
            with self.subTest(task=tid):
                official=row["original_author_score_AFTER_frozen_developer_D0"]
                self.assertEqual(official,{
                    "status":"AUTHOR_WORKER_FAILED",
                    "error_type":"RuntimeError",
                })
                self.assertNotIn("original_author_score",official)
                self.assertTrue(
                    row["original_author_score_influenced_candidate_generation"]
                    is False)
                self.assertFalse(row["original_hidden_author_target_used_for_selection"])
        self.assertTrue(self.report[
            "original_author_test_score_used_only_post_candidate_freeze"])

    def test_original_author_hidden_static_target_roots_missing_from_original_input(self):
        expected={
            "geometry_test_18":(6,2,4),
            "geometry_test_19":(2,1,1),
        }
        for tid,(total,present,missing) in expected.items():
            check=self.rows[tid][
                "postfreeze_original_author_source_target_missing_diagnostic"]
            self.assertEqual(check["status"],
                             "PINNED_ORIGINAL_AUTHOR_TARGET_NOT_IN_ORIGINAL_PUBLIC_IFC")
            self.assertEqual(check["original_author_static_declared_target_count"],total)
            self.assertEqual(check["original_author_targets_found_in_original_source"],present)
            self.assertEqual(check["original_author_targets_absent_from_original_source"],missing)
            self.assertEqual(check["scorer_exception_class"],"RuntimeError")
            self.assertTrue(check["original_author_target_GUID_values_excluded_from_report"])
            self.assertTrue(check["this_is_not_a_replacement_grade"])

    def test_independent_native_source_oracle_full_scene_pass_both_originals(self):
        for tid,row in self.rows.items():
            oracle=row["independent_original_native_ifc_oracle"]
            self.assertEqual(oracle["status"],
                "INDEPENDENT_ORIGINAL_NATIVE_IFC4X3_WINDOW_ONLY_DELETE_ORACLE_PASS_V014")
            self.assertEqual(len(oracle["original_requested_windows_removed"]),2)
            self.assertEqual(len(oracle["independently_expected_deleted_owned_root_guids"]),14)
            self.assertEqual(oracle["original_requested_windows_removed"],
                             row["developer_source_only_original_public_selected_window_guids"])
            self.assertTrue(oracle["original_host_wall_opening_unchanged"])
            self.assertTrue(oracle[
                "original_IfcRelVoids_and_Window_fill_semantics_preserved"])
            self.assertTrue(oracle[
                "candidate_independent_native_scene_proof_not_original_author_grade"])
            self.assertFalse(oracle["full_original45_semantic_edit_equivalence_proven"])

    def test_original_D0_experiment_is_not_a_new_real_LLM_comparison(self):
        self.assertEqual(self.report["new_paid_model_calls"],0)
        self.assertEqual(self.report["new_paid_cost_usd"],"0")
        self.assertEqual(self.report["original_Python_matched_I0_models_run"],0)
        self.assertEqual(self.report["real_matched_XML_Python_LLM_runs"],0)
        self.assertTrue(self.report["original_GPT6_Luna_real45_scores_unchanged"])
        self.assertTrue(self.report["old_D0_research_evidence_unchanged"])
        self.assertTrue(self.report["true_semantic_write_parity_45_not_proven"])

    def test_source_selection_has_no_hidden_author_input_and_is_repeatable(self):
        for tid,row in self.rows.items():
            public=self.public[tid]
            with tempfile.TemporaryDirectory() as td:
                src=Path(td)/"normalized.ifc"
                raw=DATA/"ifc"/public["original_source_ifc_relpath"]
                ifcopenshell.util.unit.convert_file_length_units(
                    ifcopenshell.open(str(raw)),"METER").write(str(src))
                guids,meta=_source_only_selection(
                    tid,public["public_question"],ifcopenshell.open(str(src)))
                self.assertEqual(list(guids),row[
                    "developer_source_only_original_public_selected_window_guids"])
                self.assertEqual(meta,row[
                    "developer_source_only_native_geometric_Window_selection"])

    def test_reject_wrong_public_semantic_phrasing_before_selection(self):
        tid="geometry_test_18"
        public=self.public[tid]
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/"normalized.ifc"
            raw=DATA/"ifc"/public["original_source_ifc_relpath"]
            ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(raw)),"METER").write(str(src))
            with self.assertRaisesRegex(ValueError,"semantics changed"):
                _source_only_selection(
                    tid,"Take out the windows in the east walls. +X is east direction.",
                    ifcopenshell.open(str(src)),
                )

    def test_complete_D0_report_is_deterministic_from_pinned_source(self):
        again=audit(AUTHOR,DATA)
        self.assertEqual(again,self.report)


if __name__=="__main__":
    unittest.main()
