"""Issue #247 additional public evidence: published source code + new IFC candidate.

Read-only, OFFLINE reproducible cached GitHub/publisher facts. Read local
original author checkout Git tree OBJECT METADATA only; NO original grader
content, no source IFC content, no provider, model, network or new dataset
download. Public facts pinned in v066_public_publisher_crosswalk.py MUST
be independently re-fetched to claim live currentness after 2026-11-19.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import json
from tools import audit_bibimbap_v065_offline_generalization as base
from tools.audit_bibimbap_v066_fresh_source_scorer_provenance import (
    REPORT as LAST_REPORT,
)
from tools.bibimbap_matched25_tools import file_hash
from tools import bibimbap_v066_public_publisher_crosswalk as e

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"reports"/"bibimbap_v066_public_scorer_license_candidate_crosswalk_20261119.json"
PARENT_SHA="93f8eacd2b0767c3bda5ae3f509f90a122973064f48ed9c70c3c807321798464"
PINNED_AUTHOR_SHA=e.PINNED_AUTHOR_COMMIT

def need(test,why):
    if not test:raise AssertionError(why)


def original_git_root_object_metadata():
    """Never reads any original source blob; HEAD ls-tree roots ONLY."""
    root=Path(base.AUTHOR)
    def g(*args):
        p=subprocess.run(["git","-C",str(root),*args],
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                         text=True,encoding="utf8",errors="strict",
                         stdin=subprocess.DEVNULL,check=False,timeout=25)
        need(p.returncode==0 and not p.stderr.strip(),
             "Pinned original author Git metadata query failed")
        return p.stdout.strip()
    need(g("rev-parse","HEAD")==PINNED_AUTHOR_SHA,
         "Local author fixed HEAD unexpectedly moved")
    tree={}
    for line in g("ls-tree","HEAD").splitlines():
        lhs,path=line.split("\t",1)
        mode,object_type,oid=lhs.split(" ")
        need(mode in ("100644","040000")
             and object_type in ("blob","tree") and e.is_oid(oid)
             and path not in tree,
             "Original root Git object listing malformed")
        tree[path]=(object_type,oid)
    return tree


def build_report():
    need(file_hash(LAST_REPORT)==PARENT_SHA,
         "Frozen original 31-source rights and scorer gate changed")
    earlier=json.loads(LAST_REPORT.read_text(encoding="utf8"))
    need(earlier["source_family_count"]==31
         and earlier["source_families_previously_automatically_native_processed"]==31
         and earlier["per_IFC_external_provider_transfer_retention_grants_verified"]==0
         and earlier["independently_certified_untouched_original_sources"]==0,
         "Earlier untouched-source/rights blocker unexpectedly changed")
    old_tree=original_git_root_object_metadata()
    crosswalk=e.compare_pinned_and_public_main(old_tree)
    paper=e.paper_design()
    candidate=e.candidate_review()
    need(crosswalk["public_main_vs_pinned_tracked_tree_entries_identical_excluding_new_LICENSE"]
         and paper["original_native_edit_CUD_subset"]==45
         and candidate["admitted_confirmatory_new_ifc_files"]==0,
         "Snapshot proof or unconditional no-launch blocker failed")
    return {
        "status":"V066_PUBLISHED_MAIN_MIT_ADDED_ALL_OLDER_TRACKED_CODE_IDENTICAL_PUBLIC_CANDIDATE_ONLY_BLOCKED",
        "issue":247,
        "public_external_metadata_observed_date":e.EXTERNAL_OBSERVATION_DATE,
        "audit_execution_requeries_external_web":False,
        "external_facts_are_pinned_observation_not_cryptographically_signed_external_attestation":True,
        "public_original_author_repository":{
            "github_repo":e.AUTHOR_REPO,
            "old_local_pinned_HEAD":PINNED_AUTHOR_SHA,
            "observed_public_main_HEAD":e.PUBLIC_MAIN_OBSERVED_COMMIT,
            "observed_public_main_LICENSE_added_commit":e.PUBLIC_MAIN_OBSERVED_COMMIT,
            "observed_public_main_LICENSE_added_utc":e.PUBLIC_MAIN_LICENSE_ADDED_AT_UTC,
            "observed_public_main_LICENSE_text_software_terms":"MIT",
            "observed_public_main_LICENSE_git_blob_oid":
                e.PUBLIC_MAIN_MIT_LICENSE_GIT_BLOB,
            "old_local_root_items":len(old_tree),
            "new_public_main_root_items":len(e.PUBLIC_AUTHOR_MAIN_TRACKED_ROOT_TREE),
            "old_original_tree_root_path_ids_equal_public_main_except_LICENSE":True,
            "original_author_test_data_tree_oid":e.PUBLIC_AUTHOR_TEST_TREE_ID,
            "original_benchmark_runner_blob_oid":e.PUBLIC_AUTHOR_BENCHMARK_BLOB_ID,
            "github_public_releases_count_observed":e.PUBLIC_AUTHOR_RELEASES_OBSERVED,
            "official_paper_scorer_RELEASE_TAG_or_commit_link":
                e.PUBLIC_AUTHOR_RELEASE_TAG_MATCHING_EC3_VERIFIED,
            "source_of_main_tree_evidence":
                "https://api.github.com/repos/nbharathik/bibimbap/git/trees/"+e.PUBLIC_MAIN_OBSERVED_COMMIT,
            "source_of_MIT_license_evidence":
                "https://github.com/nbharathik/bibimbap/blob/"+e.PUBLIC_MAIN_OBSERVED_COMMIT+"/LICENSE",
            "source_of_author_LICENSE_git_history_evidence":
                "https://api.github.com/repos/nbharathik/bibimbap/commits?path=LICENSE",
            "source_of_zero_public_releases_evidence":
                "https://api.github.com/repos/nbharathik/bibimbap/releases",
            "same_old_tracked_code_as_public_MIT_licensed_snapshot":True,
            "source_IFC_per_file_rights_OR_original_release_scorer_verified":False,
            "snapshot_crosswalk":crosswalk,
        },
        "published_paper":{
            **e.PAPER,
            "derived_verified_task_count_and_reference_tool_alignment":paper,
            "paper_page_2_task_test_claim_source":"official PDF page 3 (zero-based index 2)",
            "paper_page_4_baseline_25_tool_calls_source":"official PDF page 5 (zero-based index 4)",
        },
        "alternative_publicly_licensed_SOURCE_CANDIDATE_not_blind":{
            **e.GNI_CANDIDATE,
            "source_repo_url":"https://github.com/"+e.GNI_CANDIDATE["repo"],
            "source_public_Readme_url":"https://github.com/"+
                e.GNI_CANDIDATE["repo"]+"/blob/"+e.GNI_CANDIDATE["public_main_commit_observed"]+"/README.md",
            "source_IFC_specific_License_url":"https://github.com/"+
                e.GNI_CANDIDATE["repo"]+"/blob/"+e.GNI_CANDIDATE["public_main_commit_observed"]+"/IFC-models/LICENSE",
            "candidate_review":candidate,
        },
        "prior_frozen_historical_report_SHA256":PARENT_SHA,
        "new_independently_blind_IFC_samples_confirmed":0,
        "new_original_IFC_files_read_or_downloaded":0,
        "new_author_original_grader_or_GT_contents_read":0,
        "new_provider_or_model_calls":0,
        "new_external_IFC_uploads":0,
        "new_provider_transfer_or_retention_authorizations":0,
        "public_repository_code_MIT_file_discovered":True,
        "code_license_does_not_cover_IFC_source_asset_chain_automatically":True,
        "paper_benchmark_100_task_accuracy_not_equivalent_to_45_edit_task_accuracy":True,
        "published_author_scorer_exact_execution_revision_still_not_proven":True,
        "current_model_or_provider_trial_permitted":False,
        "external_independent_review_required":True,
        "next_practical_steps":[
            "Obtain out-of-band legal review of GNI model family attribution and any third-party embedded content before acquiring any individual IFC files",
            "Have independent third-party reviewer generate genuinely private tasks and evaluator, with source/question/answer access isolation",
            "Obtain official BIBIMBAP published-score evaluator commit/tag or author attestation of exact archived execution revision and model parameters",
            "Only then seek owner-approved new protocol with exactly fixed cohort, token usage and provider transfer/retention rights before a scored model trial",
        ],
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write",action="store_true")
    group.add_argument("--check",action="store_true")
    a=parser.parse_args()
    raw=e.canonical(build_report())
    if a.write:
        with REPORT.open("xb") as f:f.write(raw)
    else:
        need(REPORT.read_bytes()==raw,
             "Snapshot code and source-candidate report did not reproduce exactly")
    print("V066_UPSTREAM_PUBLISHED_MAIN_MIT_LICENSE_"+(
        "WRITE" if a.write else "CHECK"
    )+"=PASS pinned_tracked_root=10 current_root=11 diff=MIT_LICENSE_ONLY "
      "native_edit_tasks=45 read_tasks=55 fresh_blind=0 provider_calls=0")


if __name__=="__main__":
    main()
