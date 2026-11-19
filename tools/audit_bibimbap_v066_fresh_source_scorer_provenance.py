"""Issue #247: original IFC exposure, legal rights, author Git object metadata.

OFFLINE ONLY. Opens previously frozen JSON research reports and queries
original author Git tree/blob object IDs; never reads original IFC bytes,
original author grader content, GT, external data, or any provider API.
No independent certification or right is manufactured from metadata.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
from tools import audit_bibimbap_v065_offline_generalization as baseline
from tools.audit_bibimbap_v066_historical_exposure import OUTPUT as EXPOSURE
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v057_provenance import (
    assert_original_source_rights_unchanged_v057,
    refuse_all_model_trials_v057, ProviderTrialBlocked057,
)
from tools import bibimbap_v066_fresh_source_chain_gate as gate

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"reports"/"bibimbap_v066_fresh_blind_rights_scorer_chain_20261119.json"
HISTORICAL_SHA="ad4474b04b601986bcad7c2710b2461ff77ac231f3d76278d779b21431d68427"
V065_SHA="cc55f6623fc65d3936cf6ee9bbacf1c46d3893aa94122317632d9f90d009382d"
AUTHOR_SHA="667004e16bd38fd7d538bcee56191465429fd975"
TEST_TREE="bcadba5d036dbe011d9794da994ac926f8febb44"
BENCHMARK_BLOB="8d1e5740b02b8b81b74987ac7dbe37c2aed55aca"


def need(test,why):
    if not test:raise AssertionError(why)


def canonical(x):
    return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,
                       allow_nan=False)+"\n").encode("utf8")


def git_metadata(author:Path):
    """Queries only Git metadata: original grader CONTENT is never opened."""
    author=Path(author)
    need(author.is_dir(),"Original author pinned repository missing")
    def git(*args):
        p=subprocess.run(["git","-C",str(author),*args],
                         capture_output=True,text=True,encoding="utf8",
                         check=False,timeout=45,stdin=subprocess.DEVNULL)
        need(p.returncode==0 and not p.stderr.strip(),
             "Local author Git metadata query failed")
        return p.stdout.strip()
    head=git("rev-parse","HEAD")
    need(head==AUTHOR_SHA,"Local author HEAD no longer pinned")
    tree=git("ls-tree","HEAD","data/tests")
    need(tree==f"040000 tree {TEST_TREE}\tdata/tests",
         "Original author data/tests Git tree ID drift")
    benchmark=git("ls-tree","HEAD","benchmark.py")
    need(benchmark==f"100644 blob {BENCHMARK_BLOB}\tbenchmark.py",
         "Original author benchmark.py Git blob ID drift")
    names=git("ls-tree","-r","--name-only","HEAD","data/tests")
    tracked=names.splitlines()
    need(len(tracked)==108
         and all(p.startswith("data/tests/") for p in tracked),
         "Original author tracked tests path count drift")
    top=git("ls-tree","--name-only","HEAD").splitlines()
    license_names=sorted(set(top)&{
        "LICENSE","LICENSE.md","LICENSE.txt","LICENCE","LICENCE.md",
        "COPYING","COPYING.md","COPYING.txt","LICENSE.rst"})
    need(not license_names,
         "Recognized top-level license status differs from frozen provenance")
    tags=git("tag","--points-at",AUTHOR_SHA)
    return {
        "original_source_repository_url":"https://github.com/nbharathik/bibimbap",
        "pinned_author_git_HEAD_commit_SHA":head,
        "tracked_author_test_directory_tree_oid_no_content_read":TEST_TREE,
        "tracked_author_benchmark_entry_blob_oid_no_content_read":BENCHMARK_BLOB,
        "tracked_paths_in_author_data_tests":len(tracked),
        "recognized_top_level_license_filenames":license_names,
        "tags_pointing_at_pinned_author_commit":tags.splitlines() if tags else [],
        "paper_official_scorer_release_SHA_or_tag_verified":False,
        "author_scorer_files_or_private_GT_content_read":False,
        "interpretation_limit":"A Git object ID proves a local checkout identity only; it does not prove published paper grader equivalence or licensing",
    }


def build_report():
    need(file_hash(EXPOSURE)==HISTORICAL_SHA
         and file_hash(baseline.REPORT)==V065_SHA,
         "Historical frozen input report changed")
    exposure=json.loads(EXPOSURE.read_text("utf8"))
    v065=json.loads(baseline.REPORT.read_text("utf8"))
    need(exposure["original_source_SHA_families"]==31
         and exposure["previously_automatically_native_IFC_examined_families_v043"]==31
         and exposure["documented_task_specific_developer_exposed_families"]==10
         and exposure["independently_certified_blind_families"]==0,
         "Original exposure baseline changed")
    registry=gate.summarize_historical(
        exposure["families"],v065["original_source_per_file_rights_ledger"])
    need(len(registry)==31
         and sum(x["documented_task_specific_developer_implemented"]
                 for x in registry)==10,
         "31 source exposure and rights accounting drifted")
    old_sha={x["source_SHA256"] for x in registry}
    symbolic="f"*64
    need(symbolic not in old_sha,"Symbolic synthetic SHA collides with real source")
    synthetic=gate.forged_dossier_for_SYNTHETIC_TEST_ONLY(symbolic)
    claimed=gate.metadata_review(synthetic,old_sha)
    need(claimed["review_status"]==gate.STATUS_EXTERNAL
         and not claimed["independent_blind_source_certified"]
         and not claimed["per_IFC_transfer_legal_authorization_verified_outside_agent"],
         "All-claimed unverified documents bypassed trust gate")
    need(all(gate.metadata_review(
                {"original_ifc_sha256":sha},old_sha)["review_status"]
             ==gate.STATUS_HISTORICAL for sha in old_sha),
         "Previously inspected IFC admitted as untouched")
    missing=gate.metadata_review({"original_ifc_sha256":symbolic},old_sha)
    need(len(missing["missing_evidence_fields"])==
         len(gate.REQUIRED_EVIDENCE_FIELDS)-1,
         "Future-new-source evidence checklist changed")
    try:gate.assert_no_trial_launch(synthetic,owner_approval=True)
    except gate.SourceReview066Error:pass
    else:raise AssertionError("Metadata evidence could trigger a model trial")
    try:refuse_all_model_trials_v057({
        "all_rights_approved":True,
        "paper_scorer_matched":True,
        "provider":"unverified",
    })
    except ProviderTrialBlocked057:pass
    else:raise AssertionError("Unconditional original provider trial gate defeated")
    rights=assert_original_source_rights_unchanged_v057()
    need(rights["status"]=="BLOCKED_NO_MODEL_PROVIDER_TRIAL",
         "Original IFC provider rights trial gate changed")
    scorer=git_metadata(baseline.AUTHOR)
    anomalies=v065["source_author_scorer_known_discrepancies"]
    need({a["task"] for a in anomalies}=={
        "topological_test_05","geometry_test_19",
        "topological_test_17","geometry_test_03"}
        and all(a["published_official_scorer_equivalence"] is False
                for a in anomalies),
         "Pinned author scorer discrepancy/provenance record changed")
    return {
        "status":"V066_HISTORY_AND_AUTHOR_GIT_METADATA_PROVENANCE_PASS_CONFIRMATORY_BLOCKED",
        "issue":247,
        "method":"Only SHA-pinned previous research JSON metadata + local original author Git tree/blob metadata; no original grader or IFC bytes read",
        "historical_exposure_report_SHA256":HISTORICAL_SHA,
        "original_v065_report_SHA256":V065_SHA,
        "source_family_count":31,
        "source_families_previously_automatically_native_processed":31,
        "source_families_documented_task_specific_developer_exposure":10,
        "source_families_without_independent_task_specific_clearance":21,
        "independently_certified_untouched_original_sources":0,
        "new_prospective_independently_acquired_sources":0,
        "independent_external_reviewer_signatures_verified":0,
        "original_source_IFC_content_bytes_read":0,
        "original_author_grader_or_private_GT_content_bytes_read":0,
        "model_provider_calls":0,
        "external_original_IFC_uploads":0,
        "per_IFC_owner_license_attribution_verified":0,
        "per_IFC_external_provider_transfer_retention_grants_verified":0,
        "original_author_Git_metadata_only":scorer,
        "previously_documented_pinned_author_scorer_discrepancies":anomalies,
        "paper_provenance":{
            "official_EC3_paper":"https://ec-3.org/publication/ec32026_271/",
            "doi":"10.35490/EC3.2026.271",
            "published_paper_total_CRUD_tasks":100,
            "paper_reported_best_baseline_percent":50.2,
            "locally_pinned_original_edit_subset_tasks":45,
            "original_repository_published_paper_scorer_SHA_crosswalk":None,
            "author_repo_test_semantics_unchanged_PROVEN_by_Git_object_OID":True,
            "paper_scorer_equals_pinned_author_repo_verified":False,
            "official_paper_score_comparable_to_45_original_edits":False,
            "author_repo_code_license_verified":False,
        },
        "all_31_historical_source_review_status":gate.STATUS_HISTORICAL,
        "per_source_original_SHA_legal_and_exposure_matrix":registry,
        "new_fresh_source_evidence_required_fields":list(gate.REQUIRED_EVIDENCE_FIELDS),
        "new_fresh_source_missing_example_fields":missing["missing_evidence_fields"],
        "all_unverified_synthetic_claims_still_status":claimed["review_status"],
        "all_claimed_sha_reference_documents_trusted_as_signature":False,
        "future_external_reviewer_and_legal_trust_anchors_configured":False,
        "confirmatory_cohort_preapproved":False,
        "any_provider_trial_permitted":False,
        "external_owner_consent_verified":False,
        "remaining_external_steps":[
            "New truly unseen source with independently authenticated source lineage and reviewer attestation",
            "Source-level legal owner authority, attribution, license, named provider and retention/transfer permission",
            "Verified out-of-band independent reviewer signatures and approved trust anchors",
            "EC3 official evaluator release SHA and author pinned commit semantic crosswalk",
            "Owner authorization, frozen independent cohort/model/seed/tokens/pricing before any new trials",
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--write",action="store_true")
    g.add_argument("--check",action="store_true")
    a=p.parse_args()
    blob=canonical(build_report())
    if a.write:
        with REPORT.open("xb") as f:f.write(blob)
    else:
        need(REPORT.read_bytes()==blob,
             "Frozen source-exposure/rights/scorer metadata evidence not reproducible")
    print("V066_FRESH_RIGHTS_SCORER_"+("WRITE" if a.write else "CHECK")+
          "=PASS source_shas=31 native_exposed=31 blind_certified=0 "
          "rights_verified=0 grader_reads=0 model_calls=0")


if __name__=="__main__":
    main()
