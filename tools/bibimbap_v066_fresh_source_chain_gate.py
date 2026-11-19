"""Issue #247: pure metadata-only FRESH IFC review and rights intake firewall.

This code CANNOT independently certify blindness, copyright ownership,
electronic signatures, legal permission, paper-grader parity or launch an
LLM. It can reject demonstrably contaminated historical source SHAs,
validate evidence shape and produce an actionable independent review pack.
Even an internally self-asserted all-TRUE dossier remains UNAPPROVED.

Independent reviewer identity+signature, rights-holder authority, external
transfer provider/retention grant, published scorer revision and explicit
owner trial consent must be checked by people/independent trust services.
No original IFC, original author grader, external network or paid provider
access is required or performed by this file.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from hashlib import sha256
from typing import Any
import re

STATUS_HISTORICAL="HISTORICAL_SOURCE_ALREADY_AUTOMATICALLY_READ_BLOCKED"
STATUS_INCOMPLETE="NEW_SOURCE_EVIDENCE_INCOMPLETE_BLOCKED"
STATUS_EXTERNAL="COMPLETE_CLAIMS_UNVERIFIED_AWAIT_INDEPENDENT_EXTERNAL_REVIEW"
STATUS_NO_LAUNCH="NO_MODEL_OR_PROVIDER_TRIAL_AUTHORIZED"

REQUIRED_EVIDENCE_FIELDS=(
    "original_ifc_sha256",
    "source_creator_legal_identity_reference",
    "source_creation_provenance_document_sha256",
    "rights_holder_authority_document_sha256",
    "individual_ifc_license_grant_document_sha256",
    "explicit_external_model_provider_transfer_grant_sha256",
    "permitted_provider_and_retention_scope_document_sha256",
    "required_attribution_fulfilment_record_sha256",
    "independent_reviewer_identity_reference",
    "independent_blind_history_attestation_sha256",
    "independent_review_separate_trust_channel_reference",
    "source_task_definition_sha256",
    "source_scoring_contract_revision_sha256",
    "publication_to_repository_scorer_revision_crosswalk_sha256",
    "owner_trial_consent_document_sha256",
)
SHA_EVIDENCE_FIELDS=tuple(x for x in REQUIRED_EVIDENCE_FIELDS
                          if x.endswith("_sha256"))
TEXT_EVIDENCE_FIELDS=tuple(x for x in REQUIRED_EVIDENCE_FIELDS
                           if not x.endswith("_sha256"))

class SourceReview066Error(ValueError):
    pass


def require(ok, msg):
    if not ok:raise SourceReview066Error(msg)


def valid_sha(value):
    return isinstance(value,str) and bool(re.fullmatch(r"[0-9a-f]{64}",value))


def metadata_review(record: dict[str,Any] | None,
                    historical_sha_set:set[str]) -> dict:
    """Never returns admitted/cleared even for a completely filled record."""
    require(isinstance(historical_sha_set,set) and
            all(valid_sha(x) for x in historical_sha_set),
            "Pinned historical source-SHA registry must be well formed")
    require(record is None or isinstance(record,dict),
            "Metadata dossier must be a dict or explicitly absent")
    info=record or {}
    supplied_sha=info.get("original_ifc_sha256")
    require(supplied_sha is None or valid_sha(supplied_sha),
            "Original content hash requires lowercase SHA256")
    require(not (set(info)-set(REQUIRED_EVIDENCE_FIELDS)),
            "Unexpected attributes in legal/blindness intake")
    # No magic boolean approval: only verifiable document references are
    # accepted for human cross-check, and references are NOT verified here.
    for k,v in info.items():
        require(type(v) is str and v.strip() == v and v != "",
                "Only nonempty deterministic evidence-reference strings allowed")
        if k in SHA_EVIDENCE_FIELDS:
            require(valid_sha(v),f"{k}: SHA256 document reference invalid")
        else:
            require("\n" not in v and "\r" not in v
                    and len(v)<=200 and "<" not in v and ">" not in v,
                    "Evidence identity/reference not normalized")
    missing=sorted(set(REQUIRED_EVIDENCE_FIELDS)-set(info))
    seen=supplied_sha in historical_sha_set if supplied_sha else False
    if seen:
        status=STATUS_HISTORICAL
    elif missing:
        status=STATUS_INCOMPLETE
    else:
        status=STATUS_EXTERNAL
    return {
        "review_status":status,
        "source_SHA_is_in_known_historical_native_read_31":seen,
        "submitted_source_SHA256":supplied_sha,
        "all_named_document_reference_fields_present":len(missing)==0,
        "missing_evidence_fields":missing,
        "document_sha256_are_only_unverified_references":True,
        "independent_reviewer_identity_signature_cryptographically_verified":False,
        "rights_holder_authority_verified_outside_agent":False,
        "per_IFC_transfer_legal_authorization_verified_outside_agent":False,
        "official_paper_scorer_equivalence_verified":False,
        "explicit_owner_trial_consent_verified":False,
        "independent_blind_source_certified":False,
        "final_model_or_provider_launch":STATUS_NO_LAUNCH,
    }


def existing_exposure_review(historical_families):
    """Enforce actual v0.43 native-source inspection, not just task controls."""
    require(isinstance(historical_families,list) and len(historical_families)==31,
            "Frozen history must have 31 original source families")
    by_sha={}
    for row in historical_families:
        sha=row["original_source_ifc_SHA256"]
        require(valid_sha(sha) and sha not in by_sha,
                "Duplicate or invalid original historical SHA")
        require(row["v043_automated_native_IFC_product_and_representation_read"] is True
                and row["independently_certified_untouched"] is False
                and row["confirmatory_source_admission"]=="BLOCKED",
                "Historical native IFC exposure/block status changed")
        by_sha[sha]=row
    return by_sha


def summarize_historical(historical_families, rights_ledger):
    old=existing_exposure_review(historical_families)
    require(isinstance(rights_ledger,list) and len(rights_ledger)==31,
            "Source rights ledger must cover 31 SHA clusters")
    rights={x["original_source_ifc_SHA256"]:x for x in rights_ledger}
    require(len(rights)==31 and set(rights)==set(old),
            "Source rights and exposure SHA family sets differ")
    summary=[]
    for sha in sorted(old):
        h=old[sha]
        r=rights[sha]
        require(r["per_original_IFC_license_proven"] is False
                and r["external_model_provider_upload_rights_verified"] is False
                and r["external_model_provider_retention_rights_verified"] is False
                and r["source_original_IFC_creator_chain_of_title_documented"] is False
                and r["original_IFC_attribution_records_complete"] is False,
                "Historical per-IFC legal evidence unexpectedly changed")
        result=metadata_review({"original_ifc_sha256":sha},set(old))
        require(result["review_status"]==STATUS_HISTORICAL,
                "Historical developer-exposed IFC entered new blind cohort")
        summary.append({
            "source_SHA256":sha,
            "original_task_count":len(h["original_public_task_ids"]),
            "schema":h["schema"],
            "previously_original_native_IFC_programmatically_read":True,
            "documented_task_specific_developer_implemented":
                h["v065_explicit_task_specific_developer_control_evidence"],
            "historical_source_independently_blind_certified":False,
            "individual_IFC_per_file_creator_license_attribution_verified":False,
            "original_IFC_external_model_transfer_and_retention_verified":False,
            "provider_or_confirmatory_trial_status":"BLOCKED",
        })
    return summary


def forged_dossier_for_SYNTHETIC_TEST_ONLY(sha):
    """Not sufficient to certify anything. No real evidence/signatures here."""
    require(valid_sha(sha),"Only symbolic synthetic SHA allowed")
    return {field:(sha if field in SHA_EVIDENCE_FIELDS else "SYNTHETIC_UNVERIFIED")
            for field in REQUIRED_EVIDENCE_FIELDS}


def assert_no_trial_launch(*args,**kwargs):
    del args,kwargs
    raise SourceReview066Error(
        "This evidence intake is never a model/provider/scorer launch gate; "
        "independent review, authentic signatures, rights and owner consent "
        "must be verified in an entirely separate owner-authorized protocol"
    )
