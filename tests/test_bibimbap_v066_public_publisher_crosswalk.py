"""Offline original-code-license, EC3 task arithmetic and GNI IFC candidate tests.

No original IFC contents, author grader/GT, original benchmark execution,
new model/provided tokenization or network request is performed.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from unittest import TestCase, main, mock
import json

from tools import audit_bibimbap_v066_public_publisher_crosswalk as a
from tools import bibimbap_v066_public_publisher_crosswalk as p
from tools.bibimbap_matched25_tools import file_hash

FROZEN_SHA="381795b45366e20c27f200de90b7e611411fef95347a734e39e1784a3298eb6f"


class FrozenPublicCrosswalkReport066(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(a.REPORT.read_text("utf8"))

    def test_01_frozen_report_sha(self):
        self.assertEqual(file_hash(a.REPORT),FROZEN_SHA)

    def test_02_report_is_canonical(self):
        self.assertEqual(a.REPORT.read_bytes(),p.canonical(self.report))

    def test_03_parent_31_source_rights_report_frozen(self):
        self.assertEqual(file_hash(a.LAST_REPORT),a.PARENT_SHA)

    def test_04_source_snapshot_date_2026_11_19(self):
        self.assertEqual(self.report["public_external_metadata_observed_date"],
                         "2026-11-19")

    def test_05_no_live_network_claim_by_offline_audit(self):
        self.assertFalse(self.report["audit_execution_requeries_external_web"])
        self.assertTrue(self.report[
            "external_facts_are_pinned_observation_not_cryptographically_signed_external_attestation"])

    def test_06_pinned_head_kept(self):
        self.assertEqual(self.report["public_original_author_repository"][
            "old_local_pinned_HEAD"],p.PINNED_AUTHOR_COMMIT)

    def test_07_author_current_main_evidence(self):
        self.assertEqual(self.report["public_original_author_repository"][
            "observed_public_main_HEAD"],p.PUBLIC_MAIN_OBSERVED_COMMIT)

    def test_08_old_root_10_new_root_11(self):
        x=self.report["public_original_author_repository"]
        self.assertEqual(x["old_local_root_items"],10)
        self.assertEqual(x["new_public_main_root_items"],11)

    def test_09_only_added_license_in_git_tree(self):
        x=self.report["public_original_author_repository"]
        self.assertTrue(x["old_original_tree_root_path_ids_equal_public_main_except_LICENSE"])
        self.assertEqual(x["snapshot_crosswalk"]["only_new_public_main_root_file"],"LICENSE")

    def test_10_upstream_license_appeared_2026_11_16(self):
        x=self.report["public_original_author_repository"]
        self.assertEqual(x["observed_public_main_LICENSE_added_utc"],
                         "2026-11-16T15:11:35Z")
        self.assertEqual(x["observed_public_main_LICENSE_added_commit"],
                         p.PUBLIC_MAIN_OBSERVED_COMMIT)

    def test_11_MIT_license_public_git_blob(self):
        x=self.report["public_original_author_repository"]
        self.assertEqual(x["observed_public_main_LICENSE_text_software_terms"],"MIT")
        self.assertEqual(x["observed_public_main_LICENSE_git_blob_oid"],
                         p.PUBLIC_MAIN_MIT_LICENSE_GIT_BLOB)

    def test_12_previous_checkout_did_not_have_license(self):
        x=self.report["public_original_author_repository"]["snapshot_crosswalk"]
        self.assertTrue(x["pinned_pre_license_checkout_did_not_have_LICENSE_file"])

    def test_13_original_author_benchmark_blob_unchanged(self):
        x=self.report["public_original_author_repository"]
        self.assertEqual(x["original_benchmark_runner_blob_oid"],
                         p.PUBLIC_AUTHOR_BENCHMARK_BLOB_ID)

    def test_14_original_author_test_tree_unchanged(self):
        self.assertEqual(self.report["public_original_author_repository"][
            "original_author_test_data_tree_oid"],p.PUBLIC_AUTHOR_TEST_TREE_ID)

    def test_15_10_tracked_paths_same_oid_local_vs_public(self):
        real=a.original_git_root_object_metadata()
        self.assertEqual(real,{
            k:v for k,v in p.PUBLIC_AUTHOR_MAIN_TRACKED_ROOT_TREE.items()
            if k!="LICENSE"})

    def test_16_remote_release_count_zero_observed(self):
        x=self.report["public_original_author_repository"]
        self.assertEqual(x["github_public_releases_count_observed"],0)

    def test_17_no_paper_scorer_release_tag_claim(self):
        x=self.report["public_original_author_repository"]
        self.assertIsNone(x["official_paper_scorer_RELEASE_TAG_or_commit_link"])
        self.assertFalse(x["snapshot_crosswalk"][
            "official_paper_evaluator_execution_revision_verified"])

    def test_18_current_license_does_not_certify_ifc_asset_rights(self):
        x=self.report["public_original_author_repository"]
        self.assertFalse(x[
            "source_IFC_per_file_rights_OR_original_release_scorer_verified"])
        self.assertTrue(self.report["code_license_does_not_cover_IFC_source_asset_chain_automatically"])

    def test_19_official_EC3_doi(self):
        self.assertEqual(self.report["published_paper"]["official_doi"],
                         "10.35490/EC3.2026.271")

    def test_20_paper_100_tasks(self):
        self.assertEqual(self.report["published_paper"]["all_curated_tasks"],100)

    def test_21_paper_55_retrieval_subtasks(self):
        self.assertEqual(self.report["published_paper"][
            "derived_verified_task_count_and_reference_tool_alignment"]["original_read_subset"],55)

    def test_22_paper_45_native_edit_subtasks(self):
        self.assertEqual(self.report["published_paper"][
            "derived_verified_task_count_and_reference_tool_alignment"]["original_native_edit_CUD_subset"],45)

    def test_23_paper_CUD_15_each(self):
        p0=self.report["published_paper"][
            "derived_verified_task_count_and_reference_tool_alignment"]
        self.assertEqual([p0["original_create_subset"],
                          p0["original_update_subset"],
                          p0["original_delete_subset"]],[15,15,15])

    def test_24_paper_one_native_python_exec_tool(self):
        x=self.report["published_paper"]
        self.assertEqual(x["baseline_tool_count"],1)
        self.assertEqual(x["baseline_native_tool"],"execute_ifc_code")

    def test_25_paper_25_tool_calls_distinct_from_proposed(self):
        x=self.report["published_paper"]
        self.assertEqual(x["max_baseline_native_tool_calls_per_task"],25)
        self.assertTrue(x[
            "derived_verified_task_count_and_reference_tool_alignment"][
                "paper_25_calls_and_proposed_25_calls_NOT_equivalent"])

    def test_26_paper_author_test_reviewer_claim_not_real_cert(self):
        x=self.report["published_paper"]
        self.assertTrue(x["baseline_task_tests_reportedly_second_person_validated"])
        self.assertFalse(x[
            "derived_verified_task_count_and_reference_tool_alignment"][
                "independent_external_second_reviewer_signatures_inspected_here"])

    def test_27_paper_score_50point2_denominator_100(self):
        x=self.report["published_paper"]
        self.assertEqual(x["reported_top_model_full_100_mean_percent"],50.2)
        self.assertTrue(x["derived_verified_task_count_and_reference_tool_alignment"][
            "paper_all_100_score_is_not_edit_45_score"])

    def test_28_paper_release_snapshot_not_proven(self):
        self.assertIsNone(self.report["published_paper"][
            "exact_paper_evaluator_git_commit_or_tag_published"])
        self.assertTrue(self.report[
            "published_author_scorer_exact_execution_revision_still_not_proven"])

    def test_29_GNI_author_consent_ccby_claim(self):
        x=self.report["alternative_publicly_licensed_SOURCE_CANDIDATE_not_blind"]
        self.assertTrue(x["README_asserts_all_model_authors_consented"])
        self.assertEqual(x["public_source_license_label"],"CC-BY-4.0")

    def test_30_GNI_IFC_specific_license_and_root_license_identified(self):
        x=self.report["alternative_publicly_licensed_SOURCE_CANDIDATE_not_blind"]
        self.assertEqual(x["IFC_models_LICENSE_git_blob"],
                         p.GNI_CANDIDATE["IFC_models_LICENSE_git_blob"])
        self.assertEqual(x["root_LICENSE_git_blob"],
                         p.GNI_CANDIDATE["root_LICENSE_git_blob"])

    def test_31_GNI_repository_commit_pinned(self):
        x=self.report["alternative_publicly_licensed_SOURCE_CANDIDATE_not_blind"]
        self.assertEqual(x["public_main_commit_observed"],
                         p.GNI_CANDIDATE["public_main_commit_observed"])

    def test_32_GNI_208_plus_16_equals_224(self):
        x=self.report["alternative_publicly_licensed_SOURCE_CANDIDATE_not_blind"]
        self.assertEqual(x["declared_fundamentals_models"]+
                         x["declared_project_models"],224)

    def test_33_GNI_IFC_2x3_and_IFC4_not_IFC4X3_claim(self):
        x=self.report["alternative_publicly_licensed_SOURCE_CANDIDATE_not_blind"]
        self.assertEqual(x["model_subsets_schema_family_labels"],["IFC2X3","IFC4"])

    def test_34_GNI_DOI_version_distinct_from_citation(self):
        x=self.report["alternative_publicly_licensed_SOURCE_CANDIDATE_not_blind"]
        self.assertEqual(x["versioned_Zenodo_download_DOI"],
                         "10.5281/zenodo.19722011")
        self.assertEqual(x["citation_Zenodo_concept_DOI"],
                         "10.5281/zenodo.19722012")

    def test_35_GNI_embedded_third_party_disclaimer_retained(self):
        x=self.report["alternative_publicly_licensed_SOURCE_CANDIDATE_not_blind"]
        self.assertTrue(x["README_disclaimer_third_party_families_may_be_present"])
        self.assertFalse(x["candidate_review"][
            "third_party_embedded_family_rights_cleared"])

    def test_36_GNI_no_original_new_files_acquired(self):
        self.assertEqual(self.report["new_original_IFC_files_read_or_downloaded"],0)
        self.assertFalse(self.report[
            "alternative_publicly_licensed_SOURCE_CANDIDATE_not_blind"][
                "individual_IFC_bytes_retrieved"])

    def test_37_GNI_not_independently_blind_nor_private_tasks(self):
        x=self.report["alternative_publicly_licensed_SOURCE_CANDIDATE_not_blind"]
        self.assertFalse(x["independent_source_blind_review"])
        self.assertFalse(x["private_new_task_or_hidden_GT_prepared"])
        self.assertFalse(x["candidate_review"]["independent_hidden_task_and_blindness_certified"])

    def test_38_GNI_no_external_provider_clearance_from_license(self):
        x=self.report["alternative_publicly_licensed_SOURCE_CANDIDATE_not_blind"]
        self.assertFalse(x["provider_specific_external_original_IFC_transfer_clearance"])
        self.assertFalse(x["candidate_review"]["provider_specific_transfer_and_retention_cleared"])

    def test_39_GNI_original_individual_SHA_absent(self):
        x=self.report["alternative_publicly_licensed_SOURCE_CANDIDATE_not_blind"]
        self.assertFalse(x["individual_IFC_SHA256_known_in_this_snapshot"])

    def test_40_GNI_zero_admitted_confirmatory_sources(self):
        x=self.report["alternative_publicly_licensed_SOURCE_CANDIDATE_not_blind"]
        self.assertEqual(x["candidate_review"]["admitted_confirmatory_new_ifc_files"],0)
        self.assertEqual(self.report["new_independently_blind_IFC_samples_confirmed"],0)

    def test_41_no_model_calls_or_original_gt(self):
        self.assertEqual(self.report["new_provider_or_model_calls"],0)
        self.assertEqual(self.report["new_author_original_grader_or_GT_contents_read"],0)
        self.assertFalse(self.report["current_model_or_provider_trial_permitted"])

    def test_42_no_external_ifc_upload_or_grant(self):
        self.assertEqual(self.report["new_external_IFC_uploads"],0)
        self.assertEqual(self.report["new_provider_transfer_or_retention_authorizations"],0)

    def test_43_public_tree_missing_root_rejected(self):
        entries=dict(a.original_git_root_object_metadata())
        del entries["benchmark.py"]
        with self.assertRaises(p.PublicCrosswalk066Error):
            p.compare_pinned_and_public_main(entries)

    def test_44_public_tree_altered_original_test_data_rejected(self):
        entries=dict(a.original_git_root_object_metadata())
        entries["data"]=("tree","f"*40)
        with self.assertRaises(p.PublicCrosswalk066Error):
            p.compare_pinned_and_public_main(entries)

    def test_45_public_tree_old_license_claim_rejected(self):
        entries=dict(a.original_git_root_object_metadata())
        entries["LICENSE"]=("blob",p.PUBLIC_MAIN_MIT_LICENSE_GIT_BLOB)
        with self.assertRaises(p.PublicCrosswalk066Error):
            p.compare_pinned_and_public_main(entries)

    def test_46_paper_100_inconsistent_subset_refused(self):
        with mock.patch.dict(p.PAPER,{"all_curated_tasks":101}):
            with self.assertRaises(p.PublicCrosswalk066Error):
                p.paper_design()

    def test_47_paper_tool_budget_wrong_refused(self):
        with mock.patch.dict(p.PAPER,{
            "max_baseline_native_tool_calls_per_task":26
        }):
            with self.assertRaises(p.PublicCrosswalk066Error):
                p.paper_design()

    def test_48_GNI_claimed_third_party_cleared_refused(self):
        with mock.patch.dict(p.GNI_CANDIDATE,{
            "individual_IFC_third_party_components_cleared":True
        }):
            with self.assertRaises(p.PublicCrosswalk066Error):
                p.candidate_review()

    def test_49_GNI_claimed_provider_approved_refused(self):
        with mock.patch.dict(p.GNI_CANDIDATE,{
            "provider_specific_external_original_IFC_transfer_clearance":True
        }):
            with self.assertRaises(p.PublicCrosswalk066Error):
                p.candidate_review()

    def test_50_GNI_total_wrong_refused(self):
        with mock.patch.dict(p.GNI_CANDIDATE,{"published_total_models":225}):
            with self.assertRaises(p.PublicCrosswalk066Error):
                p.candidate_review()

    def test_51_code_does_not_include_IFC_geometry_native_or_provider(self):
        for module in (p,a):
            contents=Path(module.__file__).read_text(encoding="utf8")
            self.assertNotIn("import ifcopenshell",contents)
            self.assertNotIn("from openai import",contents)
            self.assertNotIn("requests.post(",contents)
            self.assertNotIn("import httpx",contents)

    def test_52_no_live_provider_or_network_in_audit(self):
        code=Path(a.__file__).read_text(encoding="utf8")
        self.assertNotIn("urllib.request",code)
        self.assertNotIn("subprocess.Popen",code)
        self.assertNotIn("openai",code.lower())

    def test_53_old_source_31_exposure_gate_reinspected(self):
        old=json.loads(a.LAST_REPORT.read_text(encoding="utf8"))
        self.assertEqual(old["source_family_count"],31)
        self.assertEqual(old["independently_certified_untouched_original_sources"],0)


if __name__=="__main__":
    main()
