"""v0.54 offline data-rights, provider-token and no-launch release guard."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools import audit_bibimbap_v054_offline_token_rights as audit
from tools import audit_bibimbap_v053_paired_prereg_gate as parent
from tools.bibimbap_matched25_tools import file_hash


REPORT_SHA="4eb66777ffeb0f38cb91e0ef1d75431f0473a11c44bd2cefd8a6f22244ff99a5"


class OriginalRightsAndTokenParity054(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(audit.REPORT.read_text(encoding="utf8"))

    def test_01_frozen_rights_token_report_SHA(self):
        self.assertEqual(file_hash(audit.REPORT),REPORT_SHA)

    def test_02_parent_D_I_candidate_manifest_sha_immutable(self):
        self.assertEqual(
            file_hash(audit.ROOT/"reports"/
                "bibimbap_v053_primary_DI_exploratory_prereg_candidate_20261118.json"),
            audit.V053_SHA)

    def test_03_new_IFC_schema_scoring_report_sha_immutable(self):
        self.assertEqual(
            file_hash(audit.ROOT/"reports"/
                "bibimbap_v054_delete_source_schema_policy_20261118.json"),
            audit.V054_GRAPH_SHA)

    def test_04_initial_same_XML_information_four_tasks(self):
        rows=self.report["per_task_source_and_tool_Utf8_bytes_NOT_actual_tokens"]
        self.assertEqual(set(rows),{
            "geometry_test_14","geometry_test_15",
            "topological_test_11","topological_test_17"})
        self.assertTrue(all(x["source_information_exact_byte_identical"]
                            for x in rows.values()))

    def test_05_actual_tool_schema_byte_counts_unequal(self):
        for row in self.report[
                "per_task_source_and_tool_Utf8_bytes_NOT_actual_tokens"].values():
            self.assertEqual(row["D_model_tool_schema_UTF8_bytes"],1324)
            self.assertEqual(row["I_model_tool_schema_UTF8_bytes"],1255)
            self.assertEqual(row["I_minus_D_tool_schema_UTF8_bytes"],-69)

    def test_06_original_source_bytes_cannot_be_called_tokens(self):
        rows=self.report["per_task_source_and_tool_Utf8_bytes_NOT_actual_tokens"]
        self.assertGreater(max(x["initial_XML_source_bytes_each_arm"]
                               for x in rows.values()),170000)
        self.assertTrue(all(x["model_provider_input_tokens_D"] is None
                            and x["model_provider_input_tokens_I"] is None
                            for x in rows.values()))
        self.assertFalse(self.report["verified_provider_token_budget_equivalence"])

    def test_07_explicit_model_and_money_approvals_missing(self):
        self.assertIsNone(self.report["verified_sampling_model_snapshot"])
        self.assertIsNone(self.report["user_approved_model_and_paid_usd_cap"])
        self.assertEqual(self.report["actual_provider_call_count"],0)

    def test_08_source_rights_undefined_and_no_license_file(self):
        self.assertFalse(self.report[
            "original_author_checkout_contains_recognized_license_file"])
        self.assertFalse(self.report[
            "huggingface_dataset_redistribution_license_verified"])
        self.assertFalse(self.report[
            "legal_transmission_or_redistribution_rights_verified"])
        self.assertTrue(self.report[
            "license_absence_does_not_establish_copyright_status"])

    def test_09_actual_author_HF_data_origin_not_an_api_token(self):
        self.assertEqual(self.report[
            "original_author_data_source_huggingface_dataset"],
            "clemenskujat/bibimbap-data")
        self.assertTrue((audit.AUTHOR/"scripts"/"download_data.py").is_file())

    def test_10_trial_admission_is_unconditional_rejection(self):
        with self.assertRaises(parent.TrialLaunchBlocked):
            parent.demand_trial_admission(None)
        with self.assertRaises(parent.TrialLaunchBlocked):
            parent.demand_trial_admission({
                k:True for k in self.report["next_approval_items"]})

    def test_11_no_provider_call_module_or_download_code(self):
        code=(audit.ROOT/"tools"/
              "audit_bibimbap_v054_offline_token_rights.py").read_text(
                  encoding="utf8")
        for token in ("import openai","import requests","import anthropic",
                      "snapshot_download(","httpx.post("):
            self.assertNotIn(token,code)

    def test_12_source_rights_change_cannot_auto_admit_trial(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)
            for name in ("README.md","download_data.py"):
                (path/name).write_text("clemenskujat/bibimbap-data",
                                       encoding="utf8")
            with patch.object(audit,"AUTHOR",path):
                with self.assertRaises(ValueError):
                    audit.build_report()

    def test_13_two_report_payloads_exclusive_creation_only(self):
        with self.assertRaises(FileExistsError):
            with audit.REPORT.open("xb") as fd:
                pass

    def test_14_no_model_original_scores_in_derived_rights_report(self):
        self.assertNotIn("correct_developer_edit",self.report)
        self.assertNotIn("author_original_GT",self.report)
        self.assertEqual(self.report["status"],
                         "BLOCKED_MODEL_AND_DATA_RELEASE_PENDING_REAL_APPROVAL")


if __name__=="__main__":
    unittest.main()
