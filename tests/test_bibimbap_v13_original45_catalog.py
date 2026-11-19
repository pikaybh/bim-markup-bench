"""v0.13 full original BIBIMBAP 45 native read-only catalog audit tests."""
from __future__ import annotations

from collections import Counter
import csv
import json
import os
from pathlib import Path
import tempfile
import unittest

from tools.audit_bibimbap_v13_original45_read_catalog import (
    run,PREVIOUS_V12_SHA,PREVIOUS_V12
)
from tools.audit_bibimbap_v12_real45_capability_matrix import REQUIREMENTS
from tools.audit_bibimbap_v13_source_worker import inspect
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",
                         r"D:\문서\D__1_Projects\202611"))
ROOT=Path(__file__).resolve().parents[1]
DATA=BASE/"bibimbap-author-data"
AUTHOR=BASE/"bibimbap-author-upstream"
JSON=ROOT/"reports"/"bibimbap_v013_original45_safe_native_read_catalog_20261114.json"
CSV=ROOT/"reports"/"bibimbap_v013_original45_safe_native_read_catalog_20261114.csv"


class V13OriginalFull45ReadOnlyCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (DATA.is_dir() and AUTHOR.is_dir() and
                JSON.is_file() and CSV.is_file()):
            raise unittest.SkipTest("Pinned original public IFC and v0.13 report absent")
        cls.result=json.loads(JSON.read_text(encoding="utf8"))
        cls.rows={
            x["original_public_task_id"]:x
            for x in cls.result["original45_task_readonly_vs_native_write_status"]
        }
        cls.public={x["test_id"]:x for x in public_45(AUTHOR,DATA)}

    def test_exact_original_population_45_and_unique_31_sources(self):
        self.assertEqual(self.result["original_public_45_denominator"],45)
        self.assertEqual(len(self.rows),45)
        self.assertEqual(set(self.rows),set(self.public))
        self.assertEqual(set(self.rows),set(REQUIREMENTS))
        self.assertEqual(self.result["original_native_unique_IFC_source_count"],31)
        self.assertEqual(len(self.result["original_native_IFC_unique_source_read_evidence"]),31)
        self.assertTrue(self.result["all_45_original_tasks_preserved_in_denominator"])

    def test_genuine_source_independent_native_ifc_oracle_45_of_45(self):
        self.assertEqual(self.result[
            "actual_v013_native_source_read_oracle_status_counts"],{
                "READ_ONLY_SOURCE_AND_INDEPENDENT_NATIVE_CATALOG_ORACLE_PASS":45,
            })
        self.assertEqual(self.result[
            "actual_v013_native_unique_source_read_status_counts"],{
                "READ_ONLY_SOURCE_AND_INDEPENDENT_NATIVE_CATALOG_ORACLE_PASS":31,
            })
        for row in self.rows.values():
            self.assertEqual(row["v013_original_source_independent_read_status"],
                "READ_ONLY_SOURCE_AND_INDEPENDENT_NATIVE_CATALOG_ORACLE_PASS")
            self.assertEqual(row["v013_independent_native_catalog_oracle"],
                "INDEPENDENT_NATIVE_IFC_READONLY_CATALOG_ORACLE_PASS_V013")

    def test_v013_safe_typed_support_vs_native_readonly_coverage_not_confused(self):
        self.assertEqual(self.result[
            "actual_v013_safe_typed_XML_source_role_gate_count"],36)
        self.assertEqual(self.result[
            "actual_v013_source_readonly_catalog_roles_and_ref_gate_count"],45)
        self.assertEqual(sum(
            row["v013_safe_typed_source_role_and_reference_gate"]
            for row in self.rows.values()),36)
        self.assertEqual(sum(
            row["v013_readonly_native_catalog_source_role_and_reference_gate"]
            for row in self.rows.values()),45)
        self.assertTrue(self.result["native_read_catalog_is_NOT_an_editable_ifc_source"])
        self.assertTrue(self.result["full_original45_IFC_semantic_write_parity_not_proven"])

    def test_exact_two_old_source_failure_cases_now_readonly_pass_but_not_edit(self):
        v12blocked={t for t,row in self.rows.items() if
                    row["v012_historical_actual_typed_XML_read_status"]=="FAIL_CLOSED"}
        self.assertEqual(v12blocked,{"geometry_test_18","geometry_test_19"})
        self.assertEqual(set(self.rows["geometry_test_18"][
            "v013_original_native_hosted_openings_readonly_demoted"]),{
                "07NAHYposfcUjqlUhBJbQM"
            })
        self.assertEqual(len(self.rows["geometry_test_19"][
            "v013_original_native_hosted_openings_readonly_demoted"]),3)
        for task in v12blocked:
            row=self.rows[task]
            self.assertFalse(row["v013_safe_typed_source_role_and_reference_gate"])
            self.assertTrue(row["v013_readonly_native_catalog_source_role_and_reference_gate"])
            self.assertFalse(row["v013_demoted_native_opening_fill_edit_support"])

    def test_native_four_original_openings_and_four_fills_demoted_only(self):
        self.assertEqual(self.result[
            "native_original_openings_readonly_demoted_count_across_unique_sources"],4)
        self.assertEqual(self.result[
            "native_original_fills_readonly_demoted_count_across_unique_sources"],4)
        others=[
            r for r in self.rows.values()
            if r["original_public_task_id"] not in
            ("geometry_test_18","geometry_test_19")
        ]
        self.assertTrue(all(
            not x["v013_original_native_hosted_openings_readonly_demoted"]
            and not x["v013_original_linked_fills_readonly_demoted"]
            for x in others
        ))

    def test_original_public_input_hashes_and_operation_family_unchanged(self):
        for task,row in self.rows.items():
            self.assertEqual(row["original_public_IFC_sha256"],
                             self.public[task]["original_ifc_sha256"])
            self.assertEqual(row["original_public_question_sha256"],
                             self.public[task]["public_question_sha256"])
            self.assertEqual(row["original_public_operation_family_required"],
                             REQUIREMENTS[task][1])
            self.assertFalse(row["excluded_from_original_45_denominator"])

    def test_legacy_native_schemas_are_not_relabelled_as_ifc4x3(self):
        self.assertEqual(Counter(
            row["original_native_schema"] for row in self.rows.values()),{
                "IFC4X3":42,"IFC2X3":2,"IFC4":1,
            })
        for tid in ("geometry_test_03","geometry_test_04","geometry_test_05"):
            r=self.rows[tid]
            self.assertTrue(r["v013_readonly_native_catalog_source_role_and_reference_gate"])
            self.assertEqual(r["v013_original_source_independent_read_status"],
                "READ_ONLY_SOURCE_AND_INDEPENDENT_NATIVE_CATALOG_ORACLE_PASS")

    def test_original_four_beams_and_opaque_spaces_remain_source_owned(self):
        beam=self.rows["topological_test_14"]
        self.assertEqual(beam["v013_original_role_readonly_vs_typed_coverage"]["Beam"],{
            "original_native_IFC_count":4,
            "safe_typed_XML_existing_count":0,
            "native_source_readonly_catalog_count":4,
            "all_original_native_role_in_safe_typed_XML":False,
        })
        self.assertTrue(beam[
            "v013_readonly_native_catalog_source_role_and_reference_gate"])
        self.assertFalse(beam["v013_safe_typed_source_role_and_reference_gate"])
        for task in ("topological_test_01","topological_test_03",
                     "topological_test_18","topological_test_20"):
            r=self.rows[task]
            self.assertTrue(r["v013_readonly_native_catalog_source_role_and_reference_gate"])
            self.assertFalse(r["v013_safe_typed_source_role_and_reference_gate"])

    def test_nine_frozen_D0_reports_keep_full11_partial11_unassessed23(self):
        self.assertEqual(self.result["frozen_v012_historical_D0_counts_unchanged"],{
            "FROZEN_DEVELOPER_D0_ORIGINAL_AUTHOR_FULL_MARK":11,
            "FROZEN_DEVELOPER_D0_ORIGINAL_AUTHOR_PARTIAL":11,
            "NO_V02_TO_V010_FROZEN_DEVELOPER_D0":23,
        })
        self.assertEqual(self.result["frozen_prior_v012_report_sha256"],
                         PREVIOUS_V12_SHA)
        self.assertEqual(file_hash(ROOT/"reports"/PREVIOUS_V12),
                         PREVIOUS_V12_SHA)
        for r in self.rows.values():
            prior=r["historical_original_task_developer_D0_evidence"]
            if prior is not None:
                self.assertTrue(prior[
                    "original_author_score_does_not_prove_strict_task_success"])

    def test_no_new_python_I0_or_model_score_or_hidden_ground_truth(self):
        self.assertEqual(self.result["matched_Python_I0_original_task_runs"],0)
        self.assertEqual(self.result["matched_real_XML_vs_Python_LLM_runs"],0)
        self.assertEqual(self.result["new_paid_provider_calls"],0)
        self.assertEqual(self.result["additional_paid_usd"],"0")
        self.assertTrue(self.result["real_Luna_historical_original45_scores_unchanged"])
        self.assertTrue(self.result["no_original_BIBIMBAP_scorer_or_hidden_GT_called"])
        for row in self.rows.values():
            self.assertEqual(row["matching_original_Python_I0_source_task_result"],
                             "NOT_RUN_NO_EVIDENCE")
            self.assertEqual(row["matching_original_XML_LLM_source_task_result"],
                             "NOT_RUN")
            self.assertEqual(row["original_task_native_XML_semantic_write_equivalence"],
                             "NOT_PROVEN")
            self.assertFalse(row["v013_readonly_catalog_can_compile_native_ifc_edits"])

    def test_original_native_relationships_are_independently_verified_for_all_31(self):
        reports=self.result["original_native_IFC_unique_source_read_evidence"]
        for sha,proof in reports.items():
            self.assertEqual(proof["original_public_ifc_sha256"],sha)
            self.assertTrue(proof[
                "original_readonly_catalog_contains_all_source_product_guids"])
            self.assertEqual(proof[
                "native_readonly_source_catalog_read_permission"],
                "READ_ONLY_NO_COMPILER_AUTHORITY")
            self.assertTrue(proof[
                "no_new_IFC_native_product_writes_or_LLM_invocations"])
            self.assertGreater(proof[
                "original_IFC_explicit_relation_edges_independently_checked"],0)

    def test_csv_has_45_rows_and_does_not_fabricate_python_I0(self):
        with CSV.open("r",encoding="utf8",newline="") as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),45)
        self.assertEqual(set(x["task"] for x in rows),set(self.rows))
        self.assertEqual({x["matched_Python_I0"] for x in rows},{"NOT_RUN"})
        self.assertEqual({x["actual_native_XML_edit_parity"] for x in rows},
                         {"NOT_PROVEN"})

    def test_current_readonly_catalog_complete_must_not_claim_full45_edit(self):
        self.assertTrue(self.result["native_source_original_ifc_mesh_geometry_unmodified"])
        self.assertTrue(self.result["native_IfcRelVoids_IfcRelFills_original_source_links_unmodified"])
        self.assertFalse(any(
            x["original_task_native_XML_vs_Python_feature_parity"]=="PROVEN"
            for x in self.rows.values()
        ))

    def test_real_worker_invalid_original_source_hash_fails_closed(self):
        raw=DATA/"ifc"/"basic_tasks.ifc"
        with self.assertRaisesRegex(ValueError,"SOURCE_HASH"):
            inspect(raw,"0"*64)

    def test_every_prior_v012_actual_failure_kept_as_history(self):
        historical={
            r["original_public_task_id"]:r["v012_historical_typed_XML_read_failure"]
            for r in self.rows.values()
            if r["v012_historical_actual_typed_XML_read_status"]=="FAIL_CLOSED"
        }
        self.assertEqual(historical,{
            "geometry_test_18":"HOSTED_OPENING_OUTSIDE_SOURCE_WALL_XML_BINDER_EXTENT",
            "geometry_test_19":"HOSTED_OPENING_OUTSIDE_SOURCE_WALL_XML_BINDER_EXTENT",
        })


if __name__=="__main__":
    unittest.main()
