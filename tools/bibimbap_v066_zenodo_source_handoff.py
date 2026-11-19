"""Issue #247: frozen Zenodo GNI archive metadata and role-separated evidence receipt.

OFFLINE policy only: no external download, IFC/ZIP reading, task/GT access,
provider call, scorer execution, or automatic source/admission approval.
A valid receipt is still merely an UNSIGNED, UNVERIFIED claim: no trusted
independent reviewer public-key registry or actual authorization exists.
"""
from __future__ import annotations
import json
import re

RECORD_ID=19722012
VERSION_DOI="10.5281/zenodo.19722012"
CONCEPT_DOI="10.5281/zenodo.19722011"
VERSION="1.0.0"
PUBLISHED="2026-04-24"
LICENSE="cc-by-4.0"
OBSERVED="2026-11-19"
# Metadata only, directly inspected at the official Zenodo REST record.
PUBLIC_FILES=(
    ("2025_BIMfundamentals.zip",503285210,"md5:bab737c3cfb3ff0443f1cc43355b589c"),
    ("2026_BIMprojects.zip",221053555,"md5:bc4bfb90313162c68a3ec4e24a0d33cf"),
    ("class_distribution.png",195135,"md5:6e1bb235811413ad599e2e567bca56f7"),
    ("group6.png",1702879,"md5:b90d5b9bd342ac32f55f68769c02a72b"),
    ("LICENSE",341,"md5:6389478e64b473658a64093199bef598"),
    ("other_online_BIM_model_resources.csv",6839,"md5:fcb578106523ca9b283ae43a042b789d"),
    ("README.md",4288,"md5:56aa9ea145afcf63a805694eaebc3e1b"),
)
STEWARDS=(
    "source_steward","task_evaluator_steward",
    "independent_blind_reviewer","rights_reviewer","research_owner",
)
SCOPES={
    "source_steward":"source_archive_and_individual_sha_chain",
    "task_evaluator_steward":"sealed_private_task_evaluator_commitments",
    "independent_blind_reviewer":"nonexposure_and_role_isolation_attestation",
    "rights_reviewer":"per_ifc_rights_embedded_components_and_provider_terms",
    "research_owner":"future_preregistration_and_separate_consent",
}
CLAIM_FIELDS={"role","steward_pseudonym","source_ifc_sha256",
              "evidence_document_sha256","scope_revision"}
STATUS_UNVERIFIED="UNVERIFIED_EXTERNAL_ROLE_ATTESTATION_NOT_ADMITTED"
STATUS_INCOMPLETE="REQUIRED_INDEPENDENT_STEWARD_RECEIPTS_MISSING"
NO_LAUNCH="NO_MODEL_PROVIDER_OR_SCORER_LAUNCH"

class ZenodoHandoffBlocked066(ValueError):
    pass

def need(x,msg):
    if not x: raise ZenodoHandoffBlocked066(msg)

def sha_ok(s):
    return type(s) is str and bool(re.fullmatch("[0-9a-f]{64}",s))

def frozen_reduced_metadata():
    return {
        "id":RECORD_ID,"doi":VERSION_DOI,"conceptdoi":CONCEPT_DOI,
        "version":VERSION,"publication_date":PUBLISHED,"license":LICENSE,
        "files":[{"name":n,"size":s,"checksum":d} for n,s,d in PUBLIC_FILES],
    }

def metadata_snapshot(supplied):
    """Validate *metadata only*: MD5 archive != per-IFC SHA256."""
    expected=frozen_reduced_metadata()
    need(type(supplied) is dict and set(supplied)==set(expected),
         "Reduced Zenodo metadata must have only exact known fields")
    for f in ("id","doi","conceptdoi","version","publication_date","license"):
        need(type(supplied[f]) is type(expected[f]) and supplied[f]==expected[f],
             "Official version DOI, concept DOI, release date or license changed")
    files=supplied["files"]
    need(type(files) is list and len(files)==7,
         "Expected exactly seven public file metadata entries")
    actual=[]
    for item in files:
        need(type(item) is dict and set(item)=={"name","size","checksum"}
             and type(item["name"]) is str and type(item["size"]) is int
             and type(item["checksum"]) is str,
             "File name, length and MD5 fields must be explicit")
        actual.append((item["name"],item["size"],item["checksum"]))
    need(sorted(actual)==sorted(PUBLIC_FILES),
         "Unexpected Zenodo file name, MD5 checksum or byte size")
    zip_files=sorted((n,s,d) for n,s,d in actual if n.endswith(".zip"))
    need(len(zip_files)==2 and sum(x[1] for x in zip_files)==724338765
         and sum(x[1] for x in actual)==726248247,
         "Zenodo archive/source metadata size accounting changed")
    return {
        "official_zenodo_metadata_URL":"https://zenodo.org/api/records/19722012",
        "publication_date":PUBLISHED,"record_version":VERSION,
        "version_DOI":VERSION_DOI,"concept_DOI":CONCEPT_DOI,
        "previous_local_DOI_label_inversion_detected":True,
        "license_identifier":LICENSE,"public_total_files":7,
        "original_zip_archive_count":2,
        "original_zip_archive_total_bytes":724338765,
        "all_public_record_files_bytes":726248247,
        "public_file_manifest":[
            {"name":n,"bytes":s,"md5":d,"downloaded_locally":False}
            for n,s,d in sorted(actual)],
        "published_original_IFC_count_claim":224,
        "individual_IFC_names_inspected":False,
        "individual_IFC_SHA256_computed":False,
        "archive_MD5_is_NOT_individual_IFC_SHA256":True,
        "original_archive_or_individual_IFC_downloads":0,
        "public_metadata_not_verification_of_embedded_third_party_rights":True,
        "provider_transfer_retention_permission_verified":False,
        "independent_blind_samples_admitted":0,
    }

def public_receipt(claims,historical_sha):
    """Five independent role claims produce PUBLIC SHA-only evidence labels.

    Unknown fields are rejected to prevent accidental GT/IFC/ID leakage.
    A syntactically complete receipt NEVER proves reviewer identity, rights
    authority, task blindness, model training non-exposure or owner consent.
    """
    need(type(claims) is list and len(claims)<=5
         and type(historical_sha) is set and len(historical_sha)==31
         and all(sha_ok(x) for x in historical_sha),
         "Need 31 historical source SHA exclusions and at most five claims")
    roles=set()
    actors=set()
    srcs=set()
    safe=[]
    for item in claims:
        need(type(item) is dict and set(item)==CLAIM_FIELDS
             and all(type(x) is str and x.strip() == x and x for x in item.values()),
             "Only five nonempty explicit public SHA-only receipt fields allowed")
        role=item["role"]
        actor=item["steward_pseudonym"]
        sha=item["source_ifc_sha256"]
        proof=item["evidence_document_sha256"]
        need(role in STEWARDS and role not in roles,
             "Missing/doubled/invalid independent evidence role")
        need(re.fullmatch("steward-[a-z0-9-]{4,36}",actor) is not None
             and actor not in actors,
             "Role actors must be distinct pseudonyms")
        need(sha_ok(sha) and sha not in historical_sha,
             "Historical IFC SHA cannot reenter independently fresh cohort")
        need(sha_ok(proof) and item["scope_revision"]==SCOPES[role],
             "Evidence hash or role-scoped sealed document mismatched")
        roles.add(role);actors.add(actor);srcs.add(sha)
        safe.append({k:item[k] for k in sorted(CLAIM_FIELDS)})
    need(len(srcs)<=1,"Five reviewer claims must target the same IFC SHA")
    return {
        "status":STATUS_UNVERIFIED if roles==set(STEWARDS) else STATUS_INCOMPLETE,
        "source_ifc_sha256":next(iter(srcs)) if srcs else None,
        "public_metadata_only_receipts":sorted(safe,key=lambda x:x["role"]),
        "missing_roles":sorted(set(STEWARDS)-roles),
        "different_pseudonymous_role_claims":len(actors)==len(roles),
        "trusted_reviewer_signatures_verified":False,
        "rights_holder_authority_independently_verified":False,
        "third_party_IFC_components_verified":False,
        "source_developer_blind_verified":False,
        "LLM_training_nonexposure_verified":False,
        "private_task_evaluator_separation_verified":False,
        "provider_transfer_or_retention_authorized":False,
        "independent_blind_sample_admitted":False,
        "model_or_provider_run_permitted":False,
        "model_execution":NO_LAUNCH,
    }

def refuse_trial(*_args,**_kwargs):
    raise ZenodoHandoffBlocked066(
        "External signatures, legal rights and owner's separately approved "
        "model-budget/scorer protocol are required; metadata cannot launch a trial")

def canonical(data):
    return (json.dumps(data,sort_keys=True,ensure_ascii=False,
                       allow_nan=False,indent=2)+"\n").encode("utf8")
