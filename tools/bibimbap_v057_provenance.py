"""v0.57 explicitly blocked paid/third-party model experiment admission.

The original author source license is not verified, while the original
Hugging Face dataset card reports CC-BY-4.0. Underlying IFC rights,
required per-asset attribution, provider data-retention/transfer approval,
model snapshot and billed D/I token parity remain NOT approved.

No provider SDK, network execution, credentials, hidden grader or model call.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.bibimbap_matched25_tools import file_hash
from tools.audit_bibimbap_v056_offline_trial_gate import (
    REPORT as PREVIOUS_RIGHTS_REPORT,
)

NO_PROVIDER_TRIAL_STATUS="BLOCKED_NO_MODEL_PROVIDER_TRIAL"
RIGHTS_REPORT_SHA="6b8e983a80a88a06f8de9ebefaeee3c52a71231583bbfeb164c05e0c1b17137c"
ORIGINAL_HF_DATASET_SHA="f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca"
AUTHOR_CODE_SHA="667004e16bd38fd7d538bcee56191465429fd975"


class ProviderTrialBlocked057(RuntimeError):
    pass


def assert_original_source_rights_unchanged_v057()->dict:
    if file_hash(PREVIOUS_RIGHTS_REPORT)!=RIGHTS_REPORT_SHA:
        raise ProviderTrialBlocked057("Original rights and model gate report changed")
    p=json.loads(PREVIOUS_RIGHTS_REPORT.read_text(encoding="utf8"))
    hf=p["original_huggingface_dataset_readonly_public_metadata"]
    author=p["original_author_code_checkout"]
    if (p["status"]!=
            "BLOCKED_PAID_MODEL_TRIAL_AND_UNVERIFIED_BILLED_TOKEN_PARITY"
        or hf["revision_sha"]!=ORIGINAL_HF_DATASET_SHA
        or hf["cardData_license_declared"]!="cc-by-4.0"
        or hf["underlying_individual_IFC_asset_rights_proven"] is not False
        or hf["user_approved_third_party_model_API_transfer"] is not False
        or author["commit_sha256"]!=AUTHOR_CODE_SHA
        or author["code_license_terms_approved"] is not False
        or p["billable_provider_calls"]!=0):
        raise ProviderTrialBlocked057("Original rights, source, or paid gate changed")
    return {
        "status":NO_PROVIDER_TRIAL_STATUS,
        "dataset_revision":ORIGINAL_HF_DATASET_SHA,
        "dataset_card_declared_license":"cc-by-4.0",
        "original_author_code_license_verified":False,
        "underlying_individual_IFC_asset_rights_verified":False,
        "provider_transfer_and_retention_approved":False,
        "provider_exact_model_snapshot":None,
        "provider_billed_D_I_tokens":None,
        "approved_USD_cap":None,
        "model_generated_trials":0,
    }


def refuse_all_model_trials_v057(approvals:dict|None=None)->None:
    del approvals
    raise ProviderTrialBlocked057(
        "No model/provider/API launch in this original IFC compact-state "
        "feasibility checkpoint. Independent permissions, attribution, "
        "model snapshot, paid USD budget, and provider billed D/I token "
        "fairness are not prospectively approved."
    )
