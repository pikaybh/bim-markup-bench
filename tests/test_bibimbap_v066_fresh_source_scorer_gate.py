"""v0.66 pure blocked independent-source/rights/scorer provenance tests."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import unittest

from tools import bibimbap_v066_fresh_source_chain_gate as g
from tools import audit_bibimbap_v066_fresh_source_scorer_provenance as a
from tools.bibimbap_matched25_tools import file_hash

REPORT_SHA="93f8eacd2b0767c3bda5ae3f509f90a122973064f48ed9c70c3c807321798464"


class FrozenExternalGateReport066(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj=json.loads(a.REPORT.read_text(encoding="utf8"))
        cls.rows=cls.obj["per_source_original_SHA_legal_and_exposure_matrix"]
        cls.old={r["source_SHA256"] for r in cls.rows}
        cls.synthetic="f"*64

    def test_01_frozen_current_report_sha(self):
        self.assertEqual(file_hash(a.REPORT),REPORT_SHA)

    def test_02_report_canonical_bytes(self):
        self.assertEqual(a.REPORT.read_bytes(),a.canonical(self.obj))

    def test_03_prior_historical_report_unchanged(self):
        self.assertEqual(file_hash(a.EXPOSURE),a.HISTORICAL_SHA)

    def test_04_prior_v065_rights_and_scorer_report_unchanged(self):
        self.assertEqual(file_hash(a.baseline.REPORT),a.V065_SHA)

    def test_05_original_31_sha_nonduplicate(self):
        self.assertEqual(len(self.old),len(self.rows))
        self.assertEqual(len(self.rows),31)

    def test_06_all_original_31_automatically_native_read(self):
        self.assertEqual(self.obj[
            "source_families_previously_automatically_native_processed"],31)
        self.assertTrue(all(row["previously_original_native_IFC_programmatically_read"]
                            for row in self.rows))

    def test_07_original_10_task_specific_exposed(self):
        self.assertEqual(sum(row["documented_task_specific_developer_implemented"]
                             for row in self.rows),10)

    def test_08_original_21_not_cleared(self):
        self.assertEqual(self.obj[
            "source_families_without_independent_task_specific_clearance"],21)

    def test_09_all_original_31_blocked(self):
        self.assertTrue(all(row["provider_or_confirmatory_trial_status"]=="BLOCKED"
                            for row in self.rows))
        self.assertEqual(self.obj["all_31_historical_source_review_status"],
                         g.STATUS_HISTORICAL)

    def test_10_all_original_31_license_not_proven(self):
        self.assertTrue(all(
            not row["individual_IFC_per_file_creator_license_attribution_verified"]
            for row in self.rows))

    def test_11_all_original_31_provider_transfer_not_approved(self):
        self.assertTrue(all(
            not row["original_IFC_external_model_transfer_and_retention_verified"]
            for row in self.rows))

    def test_12_no_independent_certified_blind(self):
        self.assertEqual(self.obj["independently_certified_untouched_original_sources"],0)
        self.assertEqual(self.obj["new_prospective_independently_acquired_sources"],0)

    def test_13_no_external_reviewer_signatures(self):
        self.assertEqual(self.obj["independent_external_reviewer_signatures_verified"],0)
        self.assertFalse(self.obj["future_external_reviewer_and_legal_trust_anchors_configured"])

    def test_14_15_required_evidence_fields(self):
        self.assertEqual(len(self.obj["new_fresh_source_evidence_required_fields"]),15)
        self.assertEqual(set(self.obj["new_fresh_source_evidence_required_fields"]),
                         set(g.REQUIRED_EVIDENCE_FIELDS))

    def test_15_original_author_commit_exact(self):
        self.assertEqual(self.obj["original_author_Git_metadata_only"][
            "pinned_author_git_HEAD_commit_SHA"],a.AUTHOR_SHA)

    def test_16_original_author_test_tree_exact(self):
        self.assertEqual(self.obj["original_author_Git_metadata_only"][
            "tracked_author_test_directory_tree_oid_no_content_read"],a.TEST_TREE)

    def test_17_original_author_benchmark_entry_blob_exact(self):
        self.assertEqual(self.obj["original_author_Git_metadata_only"][
            "tracked_author_benchmark_entry_blob_oid_no_content_read"],a.BENCHMARK_BLOB)

    def test_18_original_author_test_tracked_paths_metadata_only(self):
        self.assertEqual(self.obj["original_author_Git_metadata_only"][
            "tracked_paths_in_author_data_tests"],108)
        self.assertFalse(self.obj["original_author_Git_metadata_only"][
            "author_scorer_files_or_private_GT_content_read"])

    def test_19_no_claim_of_paper_scorer_sha(self):
        self.assertIsNone(self.obj["paper_provenance"][
            "original_repository_published_paper_scorer_SHA_crosswalk"])
        self.assertFalse(self.obj["paper_provenance"][
            "paper_scorer_equals_pinned_author_repo_verified"])

    def test_20_published_paper_denominator_not_local(self):
        self.assertEqual(self.obj["paper_provenance"]["published_paper_total_CRUD_tasks"],100)
        self.assertEqual(self.obj["paper_provenance"][
            "locally_pinned_original_edit_subset_tasks"],45)
        self.assertFalse(self.obj["paper_provenance"][
            "official_paper_score_comparable_to_45_original_edits"])

    def test_21_all_four_scorer_discrepancy_records_preserved(self):
        tasks={x["task"] for x in self.obj[
            "previously_documented_pinned_author_scorer_discrepancies"]}
        self.assertEqual(tasks,{
            "topological_test_05","geometry_test_19",
            "topological_test_17","geometry_test_03"})

    def test_22_31_authorship_license_provider_rights_unverified(self):
        self.assertEqual(self.obj["per_IFC_owner_license_attribution_verified"],0)
        self.assertEqual(self.obj["per_IFC_external_provider_transfer_retention_grants_verified"],0)

    def test_23_no_ifc_source_open_or_author_grader_read(self):
        self.assertEqual(self.obj["original_source_IFC_content_bytes_read"],0)
        self.assertEqual(self.obj["original_author_grader_or_private_GT_content_bytes_read"],0)

    def test_24_no_model_launch_or_file_upload(self):
        self.assertEqual(self.obj["model_provider_calls"],0)
        self.assertEqual(self.obj["external_original_IFC_uploads"],0)
        self.assertFalse(self.obj["any_provider_trial_permitted"])

    def test_25_forged_all_claims_not_certified(self):
        self.assertEqual(self.obj["all_unverified_synthetic_claims_still_status"],
                         g.STATUS_EXTERNAL)
        self.assertFalse(self.obj["all_claimed_sha_reference_documents_trusted_as_signature"])


class ActualIntakePolicy066(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d=json.loads(a.REPORT.read_text("utf8"))
        cls.old={x["source_SHA256"] for x in
                 d["per_source_original_SHA_legal_and_exposure_matrix"]}
        cls.new="f"*64

    def test_26_original_SHA_rejected_even_claimed_all_docs(self):
        for sha in self.old:
            doc=g.forged_dossier_for_SYNTHETIC_TEST_ONLY(sha)
            verdict=g.metadata_review(doc,self.old)
            self.assertEqual(verdict["review_status"],g.STATUS_HISTORICAL)
            self.assertFalse(verdict["independent_blind_source_certified"])

    def test_27_new_source_sha_only_still_incomplete(self):
        verdict=g.metadata_review({"original_ifc_sha256":self.new},self.old)
        self.assertEqual(verdict["review_status"],g.STATUS_INCOMPLETE)
        self.assertFalse(verdict["all_named_document_reference_fields_present"])

    def test_28_missing_original_sha_source_cannot_be_approved(self):
        verdict=g.metadata_review({},self.old)
        self.assertEqual(verdict["review_status"],g.STATUS_INCOMPLETE)
        self.assertIsNone(verdict["submitted_source_SHA256"])

    def test_29_forged_complete_new_source_does_not_certify(self):
        dossier=g.forged_dossier_for_SYNTHETIC_TEST_ONLY(self.new)
        verdict=g.metadata_review(dossier,self.old)
        self.assertEqual(verdict["review_status"],g.STATUS_EXTERNAL)
        self.assertTrue(verdict["all_named_document_reference_fields_present"])
        self.assertFalse(verdict["independent_blind_source_certified"])
        self.assertFalse(verdict["independent_reviewer_identity_signature_cryptographically_verified"])

    def test_30_false_permission_boolean_injection_refused(self):
        d=g.forged_dossier_for_SYNTHETIC_TEST_ONLY(self.new)
        d["provider_transfer_rights_approved"]=True
        with self.assertRaises(g.SourceReview066Error):
            g.metadata_review(d,self.old)

    def test_31_unknown_extra_attribute_refused(self):
        d=g.forged_dossier_for_SYNTHETIC_TEST_ONLY(self.new)
        d["author_private_expected_answer"]="SECRET"
        with self.assertRaises(g.SourceReview066Error):
            g.metadata_review(d,self.old)

    def test_32_non_lowercase_sha_refused(self):
        with self.assertRaises(g.SourceReview066Error):
            g.metadata_review({"original_ifc_sha256":"F"*64},self.old)

    def test_33_short_source_sha_refused(self):
        with self.assertRaises(g.SourceReview066Error):
            g.metadata_review({"original_ifc_sha256":"f"*63},self.old)

    def test_34_rights_doc_non_hash_refused(self):
        d=g.forged_dossier_for_SYNTHETIC_TEST_ONLY(self.new)
        d["rights_holder_authority_document_sha256"]="author says yes"
        with self.assertRaises(g.SourceReview066Error):
            g.metadata_review(d,self.old)

    def test_35_missing_provider_retention_ref_remains_blocked(self):
        d=g.forged_dossier_for_SYNTHETIC_TEST_ONLY(self.new)
        del d["permitted_provider_and_retention_scope_document_sha256"]
        verdict=g.metadata_review(d,self.old)
        self.assertIn("permitted_provider_and_retention_scope_document_sha256",
                      verdict["missing_evidence_fields"])
        self.assertEqual(verdict["review_status"],g.STATUS_INCOMPLETE)

    def test_36_missing_paper_scorer_crosswalk_remains_blocked(self):
        d=g.forged_dossier_for_SYNTHETIC_TEST_ONLY(self.new)
        del d["publication_to_repository_scorer_revision_crosswalk_sha256"]
        verdict=g.metadata_review(d,self.old)
        self.assertEqual(verdict["review_status"],g.STATUS_INCOMPLETE)

    def test_37_missing_owner_consent_remains_blocked(self):
        d=g.forged_dossier_for_SYNTHETIC_TEST_ONLY(self.new)
        del d["owner_trial_consent_document_sha256"]
        self.assertEqual(g.metadata_review(d,self.old)["review_status"],
                         g.STATUS_INCOMPLETE)

    def test_38_independent_reviewer_same_text_cannot_certify(self):
        d=g.forged_dossier_for_SYNTHETIC_TEST_ONLY(self.new)
        d["independent_reviewer_identity_reference"]="SYNTHETIC_UNVERIFIED"
        self.assertFalse(g.metadata_review(d,self.old)[
            "independent_reviewer_identity_signature_cryptographically_verified"])

    def test_39_html_or_newline_in_identity_refused(self):
        for bogus in ("person\ninjected","<script>",""):
            d=g.forged_dossier_for_SYNTHETIC_TEST_ONLY(self.new)
            d["independent_reviewer_identity_reference"]=bogus
            with self.assertRaises(g.SourceReview066Error):
                g.metadata_review(d,self.old)

    def test_40_trailing_space_identity_refused(self):
        d=g.forged_dossier_for_SYNTHETIC_TEST_ONLY(self.new)
        d["independent_reviewer_identity_reference"]="person "
        with self.assertRaises(g.SourceReview066Error):
            g.metadata_review(d,self.old)

    def test_41_bad_historical_registry_refused(self):
        with self.assertRaises(g.SourceReview066Error):
            g.metadata_review(None,{"WRONG HASH"})

    def test_42_missing_historical_registry_refused(self):
        with self.assertRaises(g.SourceReview066Error):
            g.metadata_review(None,[])

    def test_43_non_dict_dossier_refused(self):
        with self.assertRaises(g.SourceReview066Error):
            g.metadata_review([self.new],self.old)

    def test_44_source_metadata_only_not_execution_authorization(self):
        d=g.forged_dossier_for_SYNTHETIC_TEST_ONLY(self.new)
        verdict=g.metadata_review(d,self.old)
        self.assertEqual(verdict["final_model_or_provider_launch"],g.STATUS_NO_LAUNCH)

    def test_45_all_launch_methods_unconditionally_blocked(self):
        for args in ((),(self.new,),({"consent":True},)):
            with self.assertRaises(g.SourceReview066Error):
                g.assert_no_trial_launch(*args)

    def test_46_source_sha_cannot_express_hidden_answer_or_an_operation(self):
        code=Path(g.__file__).read_text("utf8")
        self.assertNotIn("def execute_ifc",code)
        self.assertNotIn("def call_provider(",code)
        self.assertNotIn("import ifcopenshell",code)
        self.assertNotIn("from openai import",code)

    def test_47_historical_ledger_never_updates_to_certified(self):
        hist=json.loads(a.EXPOSURE.read_text("utf8"))["families"]
        rights=json.loads(a.baseline.REPORT.read_text("utf8"))[
            "original_source_per_file_rights_ledger"]
        old=g.summarize_historical(hist,rights)
        self.assertEqual(len(old),31)
        self.assertTrue(all(not r["historical_source_independently_blind_certified"]
                            for r in old))

    def test_48_negative_missing_historical_row_blocks(self):
        hist=json.loads(a.EXPOSURE.read_text("utf8"))["families"]
        with self.assertRaises(g.SourceReview066Error):
            g.existing_exposure_review(hist[:-1])

    def test_49_altered_prior_census_does_not_silently_pass(self):
        hist=[dict(x) for x in json.loads(a.EXPOSURE.read_text("utf8"))["families"]]
        hist[0]["v043_automated_native_IFC_product_and_representation_read"]=False
        with self.assertRaises(g.SourceReview066Error):
            g.existing_exposure_review(hist)

    def test_50_duplicate_historical_sha_not_accepted(self):
        hist=[dict(x) for x in json.loads(a.EXPOSURE.read_text("utf8"))["families"]]
        hist[0]["original_source_ifc_SHA256"]=hist[1]["original_source_ifc_SHA256"]
        with self.assertRaises(g.SourceReview066Error):
            g.existing_exposure_review(hist)

    def test_51_raw_original_author_git_metadata_only(self):
        d=a.git_metadata(a.baseline.AUTHOR)
        self.assertEqual(d["pinned_author_git_HEAD_commit_SHA"],a.AUTHOR_SHA)
        self.assertEqual(d["tracked_author_test_directory_tree_oid_no_content_read"],
                         a.TEST_TREE)
        self.assertFalse(d["author_scorer_files_or_private_GT_content_read"])


if __name__=="__main__":
    unittest.main()
