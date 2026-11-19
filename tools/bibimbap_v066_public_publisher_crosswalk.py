"""Offline PUBLIC-PUBLISHER metadata snapshot, v0.66 Issue #247.

The "observed" public GitHub/paper dataset descriptions below were read
through read-only GitHub and publisher interfaces on 2026-11-19. The cached
values are NOT live revalidated by offline checks, independent signatures,
rights grants, evaluator proofs, or data corpus snapshots.

No IFC download, hidden grader/GT, network, provider, sample creation or
model call is possible from this pure validation module.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re

EXTERNAL_OBSERVATION_DATE = "2026-11-19"
AUTHOR_REPO = "nbharathik/bibimbap"
PINNED_AUTHOR_COMMIT = "667004e16bd38fd7d538bcee56191465429fd975"
PUBLIC_MAIN_OBSERVED_COMMIT = "88ad844937de6e62eebff284ddaab479db8dc9d3"
PUBLIC_MAIN_MIT_LICENSE_GIT_BLOB = "a2e850d10ddfd0ceb4f6cad7fe1b7a7df4e0a7bb"
PUBLIC_MAIN_LICENSE_ADDED_AT_UTC = "2026-11-16T15:11:35Z"
PUBLIC_AUTHOR_RELEASES_OBSERVED = 0
PUBLIC_AUTHOR_RELEASE_TAG_MATCHING_EC3_VERIFIED = None

# GitHub REST GET /repos/nbharathik/bibimbap/git/trees/<public main commit>.
# Values explicitly observed and NOT inferred from the current local checkout.
PUBLIC_AUTHOR_MAIN_TRACKED_ROOT_TREE = {
    ".gitignore": ("blob","717995e02061772162c112e302af436da1b3a9f8"),
    "LICENSE": ("blob",PUBLIC_MAIN_MIT_LICENSE_GIT_BLOB),
    "README.md": ("blob","54fa2a389bfbeaa9cf493a301277892d109aab8b"),
    "benchmark.py": ("blob","8d1e5740b02b8b81b74987ac7dbe37c2aed55aca"),
    "configs": ("tree","c31ed9fc6098a0dce2f77b95d8be778a8f37a214"),
    "data": ("tree","ef5998c5f5817c961f2aa95634c547c5b4fea70b"),
    "docs": ("tree","922e3b25ce421c893b1af8f92318a90a40e58876"),
    "llm_agents": ("tree","d61db1d75a78cb9689bf64a7a693b46a138307f1"),
    "requirements.txt": ("blob","6b38c0203d31c8f99e8fca3dc4d49af5f24c8629"),
    "scripts": ("tree","746774b8be603ee8e5f3e614f969834e76cddf91"),
    "tests": ("tree","a4c787a7424e1d82fc74a6b168a24252a54c224f"),
}
PUBLIC_AUTHOR_TEST_TREE_ID = "bcadba5d036dbe011d9794da994ac926f8febb44"
PUBLIC_AUTHOR_BENCHMARK_BLOB_ID = "8d1e5740b02b8b81b74987ac7dbe37c2aed55aca"

PAPER = {
    "official_doi":"10.35490/EC3.2026.271",
    "official_pdf_url":"https://ec-3.org/wp-content/uploads/2026/08/EC32026_271.pdf",
    "official_publication_page":"https://ec-3.org/publication/ec32026_271/",
    "arxiv_identifier":"2611.09933",
    "all_curated_tasks":100,
    "top_category_count":5,
    "tasks_per_top_category":20,
    "first_three_categories_each_CRUD_operation_tasks":5,
    "last_two_categories_each_read_only_tasks":20,
    "reported_top_model":"Claude Opus 4.6",
    "reported_top_model_full_100_mean_percent":50.2,
    "baseline_native_tool":"execute_ifc_code",
    "baseline_tool_count":1,
    "max_baseline_native_tool_calls_per_task":25,
    "baseline_requires_python_ifcopenshell":True,
    "baseline_task_tests_reportedly_second_person_validated":True,
    "exact_paper_evaluator_git_commit_or_tag_published":None,
    "paper_revision_to_repo_execution_config_crosswalk_verified":False,
}

GNI_CANDIDATE = {
    "repo":"ZijianWang-ZW/GNI-BIM-Dataset",
    "public_main_commit_observed":"e607ada78e8ae704aea7e381e7036c792ff8eba1",
    "root_README_git_blob":"aa14b4805068d8e6ebcd607b9913c486ec603aca",
    "root_LICENSE_git_blob":"147670bb346bd87591f8e8663d70b7448fe74b4a",
    "IFC_models_LICENSE_git_blob":"e685f84a389b1e30e3740be2f034d813dea34909",
    "public_source_license_label":"CC-BY-4.0",
    "README_asserts_all_model_authors_consented":True,
    "README_disclaimer_third_party_families_may_be_present":True,
    "published_total_models":224,
    "declared_fundamentals_models":208,
    "declared_project_models":16,
    "model_subsets_schema_family_labels":["IFC2X3","IFC4"],
    "versioned_Zenodo_download_DOI":"10.5281/zenodo.19722011",
    "citation_Zenodo_concept_DOI":"10.5281/zenodo.19722012",
    "models_are_in_separate_zenodo_archive_not_in_this_git_tree":True,
    "individual_IFC_bytes_retrieved":False,
    "individual_IFC_SHA256_known_in_this_snapshot":False,
    "individual_IFC_third_party_components_cleared":False,
    "provider_specific_external_original_IFC_transfer_clearance":False,
    "independent_source_blind_review":False,
    "private_new_task_or_hidden_GT_prepared":False,
}
class PublicCrosswalk066Error(ValueError):
    pass

def require(test,why):
    if not test:raise PublicCrosswalk066Error(why)

def is_oid(o):
    return type(o) is str and bool(re.fullmatch("[0-9a-f]{40}",o))

def compare_pinned_and_public_main(pinned_root):
    """Only Git tree object ID comparison; no grader file contents."""
    require(isinstance(pinned_root,dict),"Git tree metadata dict required")
    require(set(PUBLIC_AUTHOR_MAIN_TRACKED_ROOT_TREE)-set(pinned_root)=={"LICENSE"},
            "Public main changed unexpected source tree paths")
    require("LICENSE" not in pinned_root,"Pinned commit already had LICENSE")
    require(all(type(v) in (list,tuple) and len(v)==2 and
                v[0] in ("blob","tree") and is_oid(v[1])
                for v in pinned_root.values()),
            "Invalid cached object ID or object type")
    require(pinned_root == {
            key:value for key,value in PUBLIC_AUTHOR_MAIN_TRACKED_ROOT_TREE.items()
            if key!="LICENSE"},
            "Upstream public main differs from pinned checkout beyond MIT LICENSE")
    require(PUBLIC_AUTHOR_MAIN_TRACKED_ROOT_TREE["LICENSE"]==
            ("blob",PUBLIC_MAIN_MIT_LICENSE_GIT_BLOB),
            "Public MIT LICENSE reference changed")
    require(PUBLIC_AUTHOR_MAIN_TRACKED_ROOT_TREE["benchmark.py"][1]
            ==PUBLIC_AUTHOR_BENCHMARK_BLOB_ID,
            "Benchmark runner root blob differs")
    return {
        "public_main_vs_pinned_tracked_tree_entries_identical_excluding_new_LICENSE":True,
        "published_code_and_scorer_tree_Git_OIDs_equal_at_observed_public_main":True,
        "only_new_public_main_root_file":"LICENSE",
        "public_main_MIT_license_file_present":True,
        "pinned_pre_license_checkout_did_not_have_LICENSE_file":True,
        "official_paper_evaluator_execution_revision_verified":False,
        "source_per_IFC_license_and_provider_rights_verified":False,
    }

def paper_design():
    p=PAPER
    require(p["all_curated_tasks"]==p["top_category_count"]*
            p["tasks_per_top_category"]==100,
            "Published task dimensions inconsistent")
    read=(p["first_three_categories_each_CRUD_operation_tasks"]*3+
          p["last_two_categories_each_read_only_tasks"]*2)
    create=update=delete=p["first_three_categories_each_CRUD_operation_tasks"]*3
    require((read,create,update,delete)==(55,15,15,15)
            and read+create+update+delete==100,
            "Paper category/task arithmetic changed")
    require(p["max_baseline_native_tool_calls_per_task"]==25
            and p["baseline_native_tool"]=="execute_ifc_code",
            "Published baseline tool reference changed")
    return {
        "all_100_tasks":100,
        "original_read_subset":read,
        "original_native_edit_CUD_subset":create+update+delete,
        "original_create_subset":create,
        "original_update_subset":update,
        "original_delete_subset":delete,
        "paper_all_100_score_is_not_edit_45_score":True,
        "paper_baseline_25_calls_are_execute_IFC_code_calls":True,
        "our_prospective_three_arm_25_calls_include_one_shared_read":True,
        "paper_25_calls_and_proposed_25_calls_NOT_equivalent":True,
        "paper_says_individual_task_tests_validated_by_second_person":True,
        "independent_external_second_reviewer_signatures_inspected_here":False,
        "paper_evaluator_code_snapshot_crosswalk_proven":False,
    }

def candidate_review():
    c=GNI_CANDIDATE
    require(c["published_total_models"]==
            c["declared_fundamentals_models"]+c["declared_project_models"]==224,
            "GNI 224 IFC-source license/census snapshot changed")
    require(c["public_source_license_label"]=="CC-BY-4.0"
            and c["README_asserts_all_model_authors_consented"]
            and c["README_disclaimer_third_party_families_may_be_present"]
            and all(is_oid(c[f]) for f in (
                "public_main_commit_observed","root_README_git_blob",
                "root_LICENSE_git_blob","IFC_models_LICENSE_git_blob")),
            "GNI public provenance snapshot incomplete")
    require(not c["individual_IFC_bytes_retrieved"]
            and not c["individual_IFC_SHA256_known_in_this_snapshot"]
            and not c["individual_IFC_third_party_components_cleared"]
            and not c["provider_specific_external_original_IFC_transfer_clearance"]
            and not c["independent_source_blind_review"]
            and not c["private_new_task_or_hidden_GT_prepared"],
            "Candidate wrongly promoted to actual source or rights-cleared status")
    return {
        "status":"PUBLIC_METADATA_SOURCE_CANDIDATE_ONLY_NOT_A_TRIAL",
        "published_authors_consent_and_CC_BY_4_claim_found":True,
        "file_level_consent_authority_independently_verified":False,
        "third_party_embedded_family_rights_cleared":False,
        "provider_specific_transfer_and_retention_cleared":False,
        "individual_ifc_file_hashes_observed":False,
        "independent_hidden_task_and_blindness_certified":False,
        "admitted_confirmatory_new_ifc_files":0,
        "original_source_file_downloads":0,
        "rights_or_blind_status":"NEEDS_INDEPENDENT_EXTERNAL_REVIEW",
    }

def canonical(data):
    return (json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2,
                       allow_nan=False)+"\n").encode("utf8")
