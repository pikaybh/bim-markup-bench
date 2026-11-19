"""Offline Zenodo metadata/IFC-steward handoff audit, Issue #247.

Reproduce PUBLIC 2026-11-19 metadata and checksum snapshot without HTTP,
original source IFC, ZIP download, private GT, author grader, provider or
model execution. A synthetic all-claims handoff is intentionally BLOCKED.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from tools import bibimbap_v066_zenodo_source_handoff as z
from tools import audit_bibimbap_v066_public_publisher_crosswalk as p
from tools import audit_bibimbap_v066_fresh_source_scorer_provenance as prior
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v057_provenance import (
    refuse_all_model_trials_v057,ProviderTrialBlocked057,
)

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"reports"/"bibimbap_v066_zenodo_archive_steward_handoff_20261119.json"
PUBLIC_SHA="381795b45366e20c27f200de90b7e611411fef95347a734e39e1784a3298eb6f"
RIGHTS_SHA="93f8eacd2b0767c3bda5ae3f509f90a122973064f48ed9c70c3c807321798464"

def need(ok,reason):
    if not ok:raise AssertionError(reason)


def historical_31():
    old=json.loads(prior.REPORT.read_text("utf8"))
    need(old["source_family_count"]==31 and
         old["independently_certified_untouched_original_sources"]==0,
         "Historical original IFC cohort and exposure gate drifted")
    shas={x["source_SHA256"] for x in
          old["per_source_original_SHA_legal_and_exposure_matrix"]}
    need(len(shas)==31,"Historical sha registry duplicates")
    return shas


def build_report():
    need(file_hash(p.REPORT)==PUBLIC_SHA
         and file_hash(prior.REPORT)==RIGHTS_SHA,
         "Previously frozen public archive/copyright reports changed")
    previous=json.loads(p.REPORT.read_text("utf8"))
    candidate=previous["alternative_publicly_licensed_SOURCE_CANDIDATE_not_blind"]
    need(candidate["published_total_models"]==224
         and candidate["individual_IFC_SHA256_known_in_this_snapshot"] is False
         and candidate["provider_specific_external_original_IFC_transfer_clearance"] is False,
         "Previous GNI metadata/readiness status changed")
    history=historical_31()
    metadata=z.metadata_snapshot(z.frozen_reduced_metadata())
    need(metadata["version_DOI"]=="10.5281/zenodo.19722012"
         and metadata["concept_DOI"]=="10.5281/zenodo.19722011"
         and metadata["original_zip_archive_total_bytes"]==724338765,
         "Zenodo first-party DOI/ZIP metadata observation changed")
    symbolic="f"*64
    need(symbolic not in history,"Symbolic source SHA collided with prior real original")
    fake_claims=[]
    for role in z.STEWARDS:
        fake_claims.append({
            "role":role,
            "steward_pseudonym":"steward-"+role.replace("_","-"),
            "source_ifc_sha256":symbolic,
            "evidence_document_sha256":
                hashlib.sha256(("UNTRUSTED_SIMULATION_ONLY:"+role).encode()).hexdigest(),
            "scope_revision":z.SCOPES[role],
        })
    all_claims=z.public_receipt(fake_claims,history)
    empty=z.public_receipt([],history)
    need(all_claims["status"]==z.STATUS_UNVERIFIED
         and not all_claims["independent_blind_sample_admitted"]
         and not all_claims["model_or_provider_run_permitted"]
         and empty["status"]==z.STATUS_INCOMPLETE
         and len(empty["missing_roles"])==5,
         "Synthetic 5-party or empty handoff incorrectly admitted")
    for illegal in (symbolic,next(iter(history))):
        claims=[dict(fake_claims[0],source_ifc_sha256=illegal)]
        if illegal in history:
            try:z.public_receipt(claims,history)
            except z.ZenodoHandoffBlocked066:pass
            else:raise AssertionError("Previously exposed source bypassed SHA gate")
    try:z.refuse_trial(fake_claims,owner_claim=True)
    except z.ZenodoHandoffBlocked066:pass
    else:raise AssertionError("Public handoff launched an experiment")
    try:refuse_all_model_trials_v057({"license":"cc-by-4.0",
                                      "provider_approved":True})
    except ProviderTrialBlocked057:pass
    else:raise AssertionError("Existing unconditional no-provider gate defeated")
    return {
        "status":"V066_ZENODO_OFFICIAL_ARCHIVE_METADATA_DOI_CORRECTED_WITH_ALL_EXTERNAL_GATE_BLOCKERS",
        "issue":247,
        "public_metadata_observed_date":z.OBSERVED,
        "rights_report_SHA256":RIGHTS_SHA,
        "prior_public_version_license_report_SHA256":PUBLIC_SHA,
        "official_zenodo_record_metadata_only":metadata,
        "doi_role_correction":{
            "old_document_inverted_roles":True,
            "old_document_unchanged_under_prior_frozen_SHA":True,
            "correct_record_version_DOI":z.VERSION_DOI,
            "correct_record_concept_DOI":z.CONCEPT_DOI,
            "source_of_correction":"https://zenodo.org/api/records/19722012",
        },
        "candidate_IFC_archives_previously_unknown_exact_sizes_now_measured":2,
        "archive_download_and_storage_authorization_needed":True,
        "source_file_legal_and_safety_limits":{
            "GNI_creator_consent_AND_ccby_claims_are_public":True,
            "third_party_embedded_family_rights_and_attribution_verified":False,
            "individual_IFC_SHA256_and_source_lineage_verified":False,
            "external_provider_specific_transfer_retention_authorization":False,
            "independent_developer_blindness_proven":False,
            "LLM_training_nonexposure_proven":False,
            "new_independently_blind_source_count":0,
        },
        "external_steward_required_roles":list(z.STEWARDS),
        "external_steward_roles_required_before_verifiable_review":len(z.STEWARDS),
        "synthetic_all_role_claims_still_status":all_claims["status"],
        "synthetic_all_role_claims_represent_real_signatures":False,
        "empty_claims_missing_roles":empty["missing_roles"],
        "real_external_signatures_received":0,
        "trust_anchor_registry_for_external_signatures_configured":False,
        "untrusted_receipt_document_SHA_does_not_prove_signer_rights":True,
        "prospective_source_SHA_in_new_receipt_certified_as_actual":False,
        "individual_IFC_files_opened":0,
        "IFC_zip_archive_files_downloaded":0,
        "private_task_or_reference_evaluator_files_opened":0,
        "original_author_grader_or_GT_files_opened":0,
        "provider_or_model_calls":0,
        "paid_trials_or_external_IFC_uploads":0,
        "paper_scorer_git_release_crosswalk_completed":False,
        "new_owner_approval_to_launch":False,
        "provider_launch_status":z.NO_LAUNCH,
        "next_external_preconditions":[
            "Source steward obtains a specific IFC only after source licensing and 724MB archive acquisition/storage authorization, records its own SHA256",
            "Rights steward checks the IFC-specific original author consent, attribution, embedded third-party objects and provider transfer/retention terms",
            "Independent reviewer certifies source/task/evaluator independence with authenticated real identity, separate keys and out-of-band protected evidence",
            "Separate evaluator steward creates private new tasks/GT and independently validated scoring rubric without revealing answers to model-facing project",
            "Research owner verifies authenticated evidence, exact published-scorer revision, cohort/model/tokens/paid cap, then separately authorizes a new research protocol",
        ],
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    gr=ap.add_mutually_exclusive_group(required=True)
    gr.add_argument("--write",action="store_true")
    gr.add_argument("--check",action="store_true")
    args=ap.parse_args()
    raw=z.canonical(build_report())
    if args.write:
        with REPORT.open("xb") as f:f.write(raw)
    else:
        need(REPORT.read_bytes()==raw,"Zenodo source metadata/rights report not reproducible")
    print("V066_ZENODO_RIGHTS_SOURCE_HANDOFF_"+("WRITE" if args.write else "CHECK")
          +"=PASS file_records=7 archive_count=2 archive_bytes=724338765"
          " old_IFC_shas_blocked=31 blind=0 model_calls=0")


if __name__=="__main__":
    main()
