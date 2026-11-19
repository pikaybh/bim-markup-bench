"""Offline negative/positive historical exposure integrity tests for Issue #247.

NO unseen IFC, original author scorer, provider, external network or GT opens.
All test inputs are four already SHA-frozen, committed research reports.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import unittest

from tools import audit_bibimbap_v066_historical_exposure as a


class HistoricalExposureV066Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = a.load_pinned_reports()
        cls.report = a.build_report(cls.inputs)

    def test_01_report_is_canonical_and_reproducible(self):
        self.assertEqual(a.OUTPUT.read_bytes(), a.canonical(self.report))

    def test_02_input_report_sha256_pinned(self):
        self.assertEqual(self.report["input_report_SHA256"],
                         {k: v[1] for k, v in a.INPUTS.items()})

    def test_03_original_task_population_grouped_by_source_not_task(self):
        self.assertEqual(len(self.report["families"]), 31)
        self.assertEqual(sum(f["task_rows_sharing_family"] for f in self.report["families"]), 45)
        self.assertEqual(sorted(f["task_rows_sharing_family"] for f in self.report["families"])[-1], 15)

    def test_04_all_native_IFC_inputs_previously_processed_not_blind_proof(self):
        self.assertEqual(self.report["previously_automatically_native_IFC_examined_families_v043"], 31)
        self.assertEqual(self.report["previously_paged_native_IFC_examined_families_v046"], 27)
        self.assertEqual(sum(f["v043_automated_native_IFC_product_and_representation_read"]
                             for f in self.report["families"]), 31)

    def test_05_developer_specific_and_candidate_are_distinguished(self):
        self.assertEqual(self.report["documented_task_specific_developer_exposed_families"], 10)
        self.assertEqual(self.report["not_independently_audited_for_task_specific_human_inspection"], 21)
        self.assertEqual(sum(f["human_task_specific_inspection_status"] == "DOCUMENTED_BY_V065"
                             for f in self.report["families"]), 10)

    def test_06_no_certificate_fabricated_from_metadata_and_history(self):
        self.assertEqual(self.report["independently_certified_blind_families"], 0)
        self.assertTrue(all(not f["independently_certified_untouched"]
                            for f in self.report["families"]))
        self.assertTrue(all(f["confirmatory_source_admission"] == "BLOCKED"
                            for f in self.report["families"]))

    def test_07_historical_model_attempts_not_confused_with_current_trial(self):
        self.assertEqual(self.report["historical_XML_only_model_calls_20261112"], 36)
        self.assertEqual(self.report["historical_XML_only_original_author_scored_tasks"], 15)
        self.assertEqual(self.report["historical_XML_only_author_full_score_tasks"], 3)
        self.assertIsNone(self.report["historical_XML_only_independent_strict_success_rate"])
        self.assertEqual(self.report["historical_XML_only_Python_matched_control_trials"], 0)
        self.assertEqual(self.report["new_provider_calls_during_this_v066_audit"], 0)

    def test_08_historical_source_aggregation_by_task(self):
        self.assertEqual(sum(f["historical_20261112_XML_only_provider_calls"]
                             for f in self.report["families"]), 36)
        self.assertEqual(sum(f["historical_20261112_XML_only_author_scored_tasks"]
                             for f in self.report["families"]), 15)

    def test_09_external_source_transfer_still_blocked(self):
        self.assertEqual(self.report["original_per_source_IFC_rights_verified_count"], 0)
        self.assertTrue(all(f["external_original_IFC_transfer_rights"] == "UNVERIFIED_BLOCKED"
                            for f in self.report["families"]))

    def test_10_report_contains_only_approved_metadata_keys(self):
        accepted = {
            "original_source_ifc_SHA256", "original_public_task_ids", "schema",
            "task_rows_sharing_family",
            "v043_automated_native_IFC_product_and_representation_read",
            "v046_automated_native_paged_STEP_geometry_read",
            "v065_explicit_task_specific_developer_control_evidence",
            "v065_no_explicit_task_specific_control_evidence",
            "historical_20261112_XML_only_provider_calls",
            "historical_20261112_XML_only_author_scored_tasks",
            "historical_model_facing_XML_was_not_full_native_IFC",
            "human_task_specific_inspection_status", "independently_certified_untouched",
            "confirmatory_source_admission", "external_original_IFC_transfer_rights",
        }
        self.assertTrue(all(set(f) == accepted for f in self.report["families"]))
        self.assertNotIn("target", a.canonical(self.report).decode().lower())
        self.assertNotIn("ground_truth", a.canonical(self.report).decode().lower())

    def test_11_mutated_native_source_family_is_rejected(self):
        tampered = deepcopy(self.inputs)
        tampered["v043"]["original_31_unique_native_source_rows"][0][
            "native_original_ifc_file_sha256"] = "0" * 64
        with self.assertRaises(a.ExposureEvidenceError):
            a.build_report(tampered)

    def test_12_mutated_prior_model_task_source_mapping_is_rejected(self):
        tampered = deepcopy(self.inputs)
        tampered["luna45"]["individual_results"][0]["original_ifc_sha256"] = "0" * 64
        with self.assertRaises(a.ExposureEvidenceError):
            a.build_report(tampered)

    def test_13_duplicate_historical_task_is_rejected(self):
        tampered = deepcopy(self.inputs)
        first = tampered["luna45"]["individual_results"][0]["test_id"]
        tampered["luna45"]["individual_results"][1]["test_id"] = first
        with self.assertRaises(a.ExposureEvidenceError):
            a.build_report(tampered)

    def test_14_forged_blind_certification_is_rejected(self):
        tampered = deepcopy(self.inputs)
        tampered["v065"]["original_source_per_file_rights_ledger"][0][
            "unseen_source_confirmed_by_independent_fresh_auditor"] = True
        with self.assertRaises(a.ExposureEvidenceError):
            a.build_report(tampered)

    def test_15_forged_rights_to_externalize_is_rejected(self):
        tampered = deepcopy(self.inputs)
        tampered["v065"]["original_source_per_file_rights_ledger"][0][
            "source_external_provider_trial"] = "ALLOWED"
        with self.assertRaises(a.ExposureEvidenceError):
            a.build_report(tampered)

    def test_16_wrong_author_score_count_is_rejected(self):
        tampered = deepcopy(self.inputs)
        tampered["luna45"]["individual_results"][0]["author_full_score"] = True
        with self.assertRaises(a.ExposureEvidenceError):
            a.build_report(tampered)

    def test_17_output_sha_is_fixed_after_freeze(self):
        expected = "ad4474b04b601986bcad7c2710b2461ff77ac231f3d76278d779b21431d68427"
        self.assertEqual(sha256(a.OUTPUT.read_bytes()).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()
