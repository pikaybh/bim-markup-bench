"""v0.54 independent schema-gaming rejection, original-source fidelity tests."""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell

from tools import audit_bibimbap_v054_delete_schema_policy as audit
from tools import audit_bibimbap_v053_paired_prereg_gate as gate
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_v051_independent_native_python_oracle import (
    verify_independent_native_python_v051,
)

REPORT_HASH="27d2ef5c6d24a99303975d32e3c1622f2c241b519d554bb8fe2eb17f50c17442"


class AuthorDeleteSchemaPolicy054(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(audit.REPORT.read_text(encoding="utf8"))
        cls.task={r["test_id"]:r for r in
                  public_45(audit.AUTHOR,audit.DATA)}[audit.TASK_ID]
        cls.source=audit.DATA/"ifc"/cls.task["original_source_ifc_relpath"]

    def test_01_frozen_v054_report_SHA256(self):
        self.assertEqual(file_hash(audit.REPORT),REPORT_HASH)

    def test_02_original_source_SHA_pinned(self):
        self.assertEqual(file_hash(self.source),
                         self.report["source_original_IFC_sha256"])

    def test_03_original_public_question_sha_pinned(self):
        self.assertEqual(self.task["public_question_sha256"],
                         self.report["original_public_question_sha256"])

    def test_04_old_frozen_v053_author_report_unchanged(self):
        self.assertEqual(file_hash(audit.ROOT/"reports"/
           "bibimbap_v053_author_origin_four_original_score_20261118.json"),
           audit.V053_AUTHOR_SHA)

    def test_05_old_frozen_v053_prereg_unchanged(self):
        self.assertEqual(file_hash(audit.ROOT/"reports"/
           "bibimbap_v053_primary_DI_exploratory_prereg_candidate_20261118.json"),
           audit.V053_PREREG_SHA)

    def test_06_original_population_pinned_45_31(self):
        tasks=public_45(audit.AUTHOR,audit.DATA)
        self.assertEqual(len(tasks),45)
        self.assertEqual(len({r["original_ifc_sha256"] for r in tasks}),31)
        self.assertEqual(Counter(r["crud"] for r in tasks),
                         {"create":15,"update":15,"delete":15})

    def test_07_source_schema_IFC4X3_and_inherited_existing_error(self):
        self.assertEqual(ifcopenshell.open(str(self.source)).schema,"IFC4X3")
        self.assertEqual(
            self.report["source_existing_schema_error_count"],1)
        self.assertTrue(self.report[
            "SCHEMA_BASELINE_EXISTING_ISSUE_NOT_ATTRIBUTABLE_TO_CANDIDATE"])

    def test_08_graph_exclusive_15_properties_and_5_types(self):
        rel=self.report["source_relationship_ownership_counts_no_GUIDs"]
        self.assertEqual(rel["IfcRelDefinesByProperties"][
            "relations_exclusively_related_to_deleted_columns"],15)
        self.assertEqual(rel["IfcRelDefinesByType"][
            "relations_exclusively_related_to_deleted_columns"],5)
        self.assertEqual(rel["IfcRelContainedInSpatialStructure"][
            "relations_with_surviving_shared_objects"],1)

    def test_09_source_graph_author_private_target_count_not_guids(self):
        self.assertEqual(
            self.report["original_author_deleted_target_count_not_ids"],5)
        self.assertEqual(len(audit.original_author_targets_evaluator_only()),5)
        self.assertNotIn("target_column_guids",
                         audit.REPORT.read_text(encoding="utf8"))

    def test_10_raw_edit_original_author_metrics_fool_test(self):
        raw=self.report["candidate_evidence"][
            "RAW_REMOVE_INVALID_NEGATIVE_CONTROL"]
        self.assertEqual(raw["original_author_repository_metric"][
            "author_repo_score"],1)
        self.assertTrue(raw["original_author_repository_metric"][
            "boolean_metrics"]["object_not_exists"])
        self.assertTrue(raw["original_author_repository_metric"][
            "boolean_metrics"]["integrity_constraint"])

    def test_11_direct_raw_delete_native_output_has_25_NEW_schema_errors(self):
        raw=self.report["candidate_evidence"][
            "RAW_REMOVE_INVALID_NEGATIVE_CONTROL"]["real_IFC_schema_delta"]
        self.assertEqual(raw["source_existing_schema_error_count"],1)
        self.assertEqual(raw["candidate_schema_error_count"],26)
        self.assertEqual(raw["introduced_schema_error_count"],25)
        self.assertEqual(raw["status"],"REJECT_NEW_IFC_SCHEMA_ERRORS")

    def test_12_raw_delete_introduced_20_bad_rel_and_5_bad_shapes(self):
        breakdown=self.report["candidate_evidence"][
            "RAW_REMOVE_INVALID_NEGATIVE_CONTROL"][
                "real_IFC_schema_delta"]["introduced_schema_error_by_attribute"]
        self.assertEqual(breakdown.get("RelatedObjects"),20)
        self.assertEqual(sum(breakdown.values()),25)
        self.assertEqual(len(breakdown),2)

    def test_13_native_scope_old_oracle_missed_invalid_schema(self):
        raw=self.report["candidate_evidence"][
            "RAW_REMOVE_INVALID_NEGATIVE_CONTROL"]
        self.assertEqual(raw["source_native_physical_oracle"],
            "V051_INDEPENDENT_SOURCE_NATIVE_IFC_SCOPE_ORACLE_PASS")
        self.assertTrue(raw["research_physical_task_predicate"])
        self.assertFalse(raw["augmented_strict_native_admission"])

    def test_14_valid_D_and_I_source_native_admitted(self):
        for mode in ("D_STATE","I_NATIVE_API"):
            row=self.report["candidate_evidence"][mode]
            self.assertEqual(row["real_IFC_schema_delta"]["status"],
                             "PASS_NO_NEW_IFC_SCHEMA_ERRORS")
            self.assertEqual(
                row["real_IFC_schema_delta"]["introduced_schema_error_count"],0)
            self.assertTrue(row["augmented_strict_native_admission"])

    def test_15_valid_D_and_I_author_scores_identical_but_half(self):
        for mode in ("D_STATE","I_NATIVE_API"):
            row=self.report["candidate_evidence"][mode]
            metrics=row["original_author_repository_metric"]
            self.assertTrue(metrics["boolean_metrics"]["object_not_exists"])
            self.assertFalse(metrics["boolean_metrics"]["integrity_constraint"])
            self.assertEqual(metrics["author_repo_score"],0.5)

    def test_16_no_causal_effect_claim_or_paper_score(self):
        self.assertIsNone(self.report["published_paper_score"])
        self.assertFalse(
            self.report["original_author_score_promoted_to_published_paper_OFFICIAL"])
        self.assertEqual(self.report["LLM_trials"],0)
        self.assertEqual(self.report["billable_provider_calls"],0)

    def test_17_original_source_unmodified_across_three_candidates(self):
        self.assertFalse(self.report["original_IFC_changed"])
        self.assertTrue(all(
            row["real_IFC_schema_delta"]["original_input_hash_unchanged"]
            for row in self.report["candidate_evidence"].values()))

    def test_18_schema_multiset_subtraction_preserves_preexisting_errors(self):
        with TemporaryDirectory(prefix="v054-schema-source-") as tmp:
            same=Path(tmp)/"identical.ifc"
            same.write_bytes(self.source.read_bytes())
            gate=audit.native_ifc_schema_delta_v054(
                self.source,same,expected_source_sha=self.task[
                    "original_ifc_sha256"])
            self.assertEqual(gate["status"],"PASS_NO_NEW_IFC_SCHEMA_ERRORS")
            self.assertEqual(gate["introduced_schema_error_count"],0)
            self.assertEqual(gate["source_existing_schema_error_count"],1)

    def test_19_schema_wrong_source_sha_fails_closed(self):
        with self.assertRaises(audit.SchemaValidationBoundaryError):
            audit.native_ifc_schema_delta_v054(
                self.source,self.source,expected_source_sha="0"*64)

    def test_20_missing_candidate_file_fails_closed(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaises(audit.SchemaValidationBoundaryError):
                audit.native_ifc_schema_delta_v054(
                    self.source,Path(tmp)/"missing.ifc",
                    expected_source_sha=self.task["original_ifc_sha256"])

    def test_21_symlinked_candidate_rejected_when_supported(self):
        with TemporaryDirectory() as tmp:
            link=Path(tmp)/"symlink.ifc"
            try: link.symlink_to(self.source)
            except (OSError,NotImplementedError):
                self.skipTest("Windows symlink not allowed for this user")
            with self.assertRaises(audit.SchemaValidationBoundaryError):
                audit.native_ifc_schema_delta_v054(
                    self.source,link,
                    expected_source_sha=self.task["original_ifc_sha256"])

    def test_22_actual_raw_invalid_guard_inside_new_gate(self):
        with TemporaryDirectory(prefix="v054-raw-negative-") as tmp:
            path=Path(tmp)/"untrusted_raw.ifc"
            f=ifcopenshell.open(str(self.source))
            for guid in sorted(audit.original_author_targets_evaluator_only()):
                f.remove(f.by_guid(guid))
            f.write(str(path))
            result=audit.strict_native_scope_plus_schema_v054(
                self.source,path,source_sha=self.task[
                    "original_ifc_sha256"],task_id=audit.TASK_ID)
            self.assertFalse(result["admitted"])
            self.assertEqual(result["native_scope_status"],
                             "NOT_SUFFICIENT_NEW_SCHEMA_ERRORS")
            self.assertEqual(result["introduced_schema_error_count"],25)

    def test_23_no_explicit_original_author_GTs_in_report(self):
        text=audit.REPORT.read_text(encoding="utf8")
        self.assertNotIn("target_column_guids",text)
        self.assertNotIn("positive_developer_source_edit",text)
        self.assertNotIn("developer_control_to_declarative_state",text)
        self.assertNotIn("Source target GUIDs",text)

    def test_24_existing_primary_D_I_not_falsely_promoted_to_model_trials(self):
        p=json.loads((audit.ROOT/"reports"/
          "bibimbap_v053_primary_DI_exploratory_prereg_candidate_20261118.json")
          .read_text(encoding="utf8"))
        self.assertEqual(p["actual_model_trial_slots_executed"],0)
        self.assertFalse(p["model_token_parity_proven"])
        self.assertFalse(p["user_approved_paid_experiment"])

    def test_25_prospective_gate_still_refuses_all_approved_dict(self):
        with self.assertRaises(gate.TrialLaunchBlocked):
            gate.demand_trial_admission({
                "provider":True,"token_budget":True,"data_rights":True,
                "user_paid_budget":True,"privacy":True,
            })

    def test_26_source_code_does_not_send_provider_models_or_write_ifcs_to_repo(self):
        source=(audit.ROOT/"tools"/
                "audit_bibimbap_v054_delete_schema_policy.py").read_text(
                    encoding="utf8")
        self.assertNotIn("import openai",source)
        self.assertNotIn("import anthropic",source)
        self.assertNotIn("requests.post",source)
        self.assertIn("TemporaryDirectory",source)

    def test_27_frozen_report_has_exclusive_create_mode(self):
        with self.assertRaises(FileExistsError):
            with audit.REPORT.open("xb") as fd:
                pass

    def test_28_source_and_report_not_symlinks(self):
        self.assertFalse(self.source.is_symlink())
        self.assertFalse(audit.REPORT.is_symlink())


if __name__=="__main__":
    unittest.main()
