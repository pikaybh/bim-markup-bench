"""v0.11 original 45-task immutable source census, not a 45-task edit claim."""
from __future__ import annotations

import os
from pathlib import Path
import unittest

from tools.audit_bibimbap_v11_full45_ledger import (
    run,_known_d0,PINNED_REPORTS,
)
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get(
    "BIBIMBAP_EXPERIMENT_BASE",r"D:\문서\D__1_Projects\202611"))
ROOT=Path(__file__).resolve().parents[1]
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"


class V11OriginalFull45Ledger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not AUTHOR.is_dir() or not DATA.is_dir():
            raise unittest.SkipTest("Original pinned public author and dataset unavailable")
        cls.report=run(ROOT,AUTHOR,DATA)
        cls.rows={
            r["original_task_id"]:r
            for r in cls.report["original_task_ledger"]
        }

    def test_exact_original_forty_five_cohort_with_no_duplicate_ids(self):
        self.assertEqual(self.report["original_edit_task_denominator"],45)
        self.assertEqual(len(self.rows),45)
        self.assertEqual(len(self.report["original_task_ledger"]),45)
        self.assertTrue(self.report["original_task_id_unique"])

    def test_original_native_schema_population_counts_all_real_source_ifcs(self):
        self.assertEqual(self.report["original_native_schema_counts"],{
            "IFC2X3":2,"IFC4":1,"IFC4X3":42,
        })
        for row in self.rows.values():
            self.assertEqual(len(row["original_public_ifc_sha256"]),64)
            self.assertEqual(len(row["original_public_question_sha256"]),64)
            self.assertTrue(row["source_original_ifc_public_data_verified"])

    def test_original_initial_source_projection_gate_preserved_as_historical(self):
        self.assertEqual(self.report[
            "historical_v01_readonly_source_projection_counts"],{
                "BLOCKED":9,"PROJECTABLE":36,
            })
        self.assertFalse(
            self.report["native_v011_all_45_source_projection_success_claim"])
        self.assertFalse(
            self.report["native_v011_all_45_direct_XML_edit_supported_claim"])
        self.assertFalse(
            self.report["common_XML_vs_Python_backend_feature_parity_claim"])

    def test_seven_v08_to_v010_fixed_developer_scores_are_not_real_llm_scores(self):
        counts=self.report["v08_to_v010_fixed_developer_D0_status_counts"]
        self.assertEqual(counts,{
            "EXACT_FROZEN_DEVELOPER_D0_ORIGINAL_AUTHOR_FULL_MARK":3,
            "EXACT_FROZEN_DEVELOPER_D0_ORIGINAL_AUTHOR_PARTIAL":4,
            "NOT_ASSESSED_IN_V08_TO_V010_DEVELOPER_D0":38,
        })
        self.assertTrue(self.report["only_v08_to_v010_newest_partial_native_feature_slices_included"])
        self.assertTrue(self.report["v01_to_v07_other_D0_feature_slices_not_relabelled_as_absent"])
        self.assertTrue(self.report["original_real_Luna_full_45_scored_history_unchanged"])
        self.assertEqual(self.report["new_paid_provider_requests"],0)
        self.assertEqual(self.report["additional_API_cost_usd"],"0")

    def test_seven_frozen_developer_D0_task_scores_and_original_schemas(self):
        scores={
            task:row["v08_to_v010_fixed_developer_D0_evidence"][
                "original_author_fixed_developer_D0_score"]
            for task,row in self.rows.items()
            if row["v08_to_v010_fixed_developer_D0_evidence"] is not None
        }
        self.assertEqual(scores,{
            "geometry_test_03":1.0,
            "geometry_test_04":.916675,
            "geometry_test_05":1.0,
            "geometry_test_14":2/3,
            "topological_test_05":1.0,
            "topological_test_11":2/3,
            "topological_test_17":.5,
        })
        self.assertEqual(self.rows["geometry_test_03"]["original_native_ifc_schema"],"IFC2X3")
        self.assertEqual(self.rows["geometry_test_04"]["original_native_ifc_schema"],"IFC2X3")
        self.assertEqual(self.rows["geometry_test_05"]["original_native_ifc_schema"],"IFC4")
        for tid in ("geometry_test_14","topological_test_05",
                    "topological_test_11","topological_test_17"):
            self.assertEqual(self.rows[tid]["original_native_ifc_schema"],"IFC4X3")

    def test_all_prior_v08_v09_v010_author_reports_immutably_hashed(self):
        records=_known_d0(ROOT)
        self.assertEqual(len(records),7)
        for version,(filename,expected_sha) in PINNED_REPORTS.items():
            with self.subTest(version=version):
                self.assertEqual(file_hash(ROOT/"reports"/filename),expected_sha)

    def test_every_unassessed_original_task_explicitly_marked_unassessed_not_failed(self):
        untouched=[
            row for row in self.rows.values()
            if row["v08_to_v010_fixed_developer_D0_evidence"] is None
        ]
        self.assertEqual(len(untouched),38)
        self.assertTrue(all(
            row["v08_to_v010_fixed_developer_D0_status"]
            =="NOT_ASSESSED_IN_V08_TO_V010_DEVELOPER_D0"
            for row in untouched
        ))
        self.assertTrue(all(
            row["current_v011_all45_source_native_edit_parity"]=="NOT_PROVEN"
            and row["real_LLM_scoring_in_this_v011_audit"] is None
            and row["current_matched_25_feedback_run_status"]=="NOT_RUN"
            for row in self.rows.values()
        ))

    def test_original_source_census_rerun_is_byte_stable_and_complete(self):
        again=run(ROOT,AUTHOR,DATA)
        self.assertEqual(again,self.report)


if __name__=="__main__":
    unittest.main()
