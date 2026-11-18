"""v0.56 zero-LLM launch admission and verified public dataset-card evidence.

Snapshot of a read-only public HF Hub dataset metadata response taken
2026-11-18, NOT a claim that individual IFC original authors granted the
dataset uploader rights. This offline executable rechecks frozen evidence
and unconditionally refuses provider trials even if caller passes true flags.
No credentials, network, model provider, GT/scorer or paid API imported.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from tools.bibimbap_matched25_tools import file_hash
from tools.audit_bibimbap_v053_paired_prereg_gate import (
    TrialLaunchBlocked,demand_trial_admission,
)
from tools.audit_bibimbap_v056_full_xml_feasibility import (
    REPORT as FEASIBILITY_REPORT,TASKS,
)


ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
REPORT=ROOT/"reports"/"bibimbap_v056_offline_trial_rights_and_output_budget_gate_20261118.json"
PARENT_D_FEASIBILITY_SHA="09b2435f402fd333cdb048681313b05a180fe751bc641b9a8a774b77d7620849"
HF_DATASET_ID="clemenskujat/bibimbap-data"
HF_DATASET_SHA="f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca"
HF_CARD_DECLARED_LICENSE="cc-by-4.0"
AUTHOR_GIT_COMMIT="667004e16bd38fd7d538bcee56191465429fd975"


class OfflineTrialBlocked056(TrialLaunchBlocked):
    pass


def enforce_no_paid_or_unapproved_trial_v056(_approvals:dict|None=None)->None:
    """Admission is intentionally not implemented, including all-true dicts."""
    raise OfflineTrialBlocked056(
        "v0.56 is an OFFLINE D-state feasibility and rights research gate. "
        "Provider/model snapshot, billed token parity, monetary cost ceiling, "
        "per-IFC attribution/underlying rights and user data/API transfer "
        "approval require a future independently reviewed checkpoint."
    )


def canonical(data:dict)->bytes:
    return (json.dumps(data,sort_keys=True,indent=2,ensure_ascii=False)
            +"\n").encode("utf8")


def build_report()->dict:
    if file_hash(FEASIBILITY_REPORT)!=PARENT_D_FEASIBILITY_SHA:
        raise ValueError("Frozen v0.56 real D XML output audit was altered")
    parent=json.loads(FEASIBILITY_REPORT.read_text(encoding="utf8"))
    if (parent["status"]!=
            "V056_OFFLINE_FULL_XML_OUTPUT_FEASIBILITY_AND_STREAMING_EQUIVALENCE_PASS"
        or parent["actual_LLM_D_I_trials"]!=0
        or parent["actual_paid_model_calls"]!=0
        or len(parent["full_final_state_developer_output_records"])!=8):
        raise ValueError("Frozen v0.56 D-state output/LLM boundary changed")
    if (not (AUTHOR/"README.md").is_file()
        or any((AUTHOR/file).exists()
               for file in ("LICENSE","LICENSE.md","LICENSE.txt",
                            "LICENSE.rst","COPYING"))):
        raise ValueError("Original author checkout license state changed")
    from subprocess import run
    checked=run(["git","-C",str(AUTHOR),"rev-parse","HEAD"],
                capture_output=True,text=True,encoding="utf8",
                timeout=12,check=True).stdout.strip()
    if checked!=AUTHOR_GIT_COMMIT:
        raise ValueError("Original author checkout HEAD changed")

    arrays={}
    for task in TASKS:
        matched=[
            x for x in parent["full_final_state_developer_output_records"]
            if x["original_task_id"]==task
        ]
        if len(matched)!=2 or not all(
                x["streamed_FULL_XML_reassembled_without_change"]
                and x["within_25_tool_calls"] for x in matched):
            raise ValueError("D-state final XML response feasibility missing")
        info=parent["initial_source_and_tool_schemas"][task]
        arrays[task]={
            "initial_full_XML_source_bytes":info["initial_full_XML_UTF8_bytes"],
            "developer_final_D_XML_min_utf8_bytes":min(
                x["full_final_state_XML_UTF8_bytes"] for x in matched),
            "developer_final_D_XML_max_utf8_bytes":max(
                x["full_final_state_XML_UTF8_bytes"] for x in matched),
            "developer_I_Python_min_utf8_bytes":min(
                x["independent_I_developer_Python_UTF8_bytes"] for x in matched),
            "developer_I_Python_max_utf8_bytes":max(
                x["independent_I_developer_Python_UTF8_bytes"] for x in matched),
            "D_stream_chunk_count_min":min(
                x["complete_chunks_required"] for x in matched),
            "D_stream_chunk_count_max":max(
                x["complete_chunks_required"] for x in matched),
            "D_max_required_calls_including_source_read":max(
                x["D_stream_total_calls_including_one_read"] for x in matched),
            "v055_one_shot_D_tool_schema_json_bytes":
                info["original_D_tool_schema_JSON_UTF8_bytes"],
            "v055_I_tool_schema_json_bytes":
                info["original_I_tool_schema_JSON_UTF8_bytes"],
            "v056_D_stream_tool_schema_json_bytes":
                info["new_stream_D_tool_schema_JSON_UTF8_bytes"],
            "actual_provider_billed_D_completion_tokens":None,
            "actual_provider_billed_I_completion_tokens":None,
            "actual_provider_billed_prompt_tokens":None,
            "byte_ratio_is_NOT_token_ratio":True,
        }
    # No inference SDK/tokenizer exists in pinned research venv, and a model
    # snapshot has never been selected; do not smuggle one into the report.
    denied=False
    try:
        demand_trial_admission({"user_approved":True,"paid_budget":True})
    except TrialLaunchBlocked:
        denied=True
    if not denied:
        raise ValueError("v0.53 unconditional provider gate unexpectedly bypassed")
    try:
        enforce_no_paid_or_unapproved_trial_v056({
            "all_conditions":True,"source_transfer":True,
            "provider_billed_tokens":True,"cost_cap":True,
        })
    except OfflineTrialBlocked056:
        denied2=True
    else:
        denied2=False
    if not denied2:
        raise ValueError("v0.56 unconditional provider gate unexpectedly bypassed")
    return {
        "status":"BLOCKED_PAID_MODEL_TRIAL_AND_UNVERIFIED_BILLED_TOKEN_PARITY",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/227",
        "original_public_45_task_population":45,
        "unique_original_public_IFC_sha_sources":31,
        "exploratory_original_4_tasks":list(TASKS),
        "other_41_original_edit_tasks_not_run":41,
        "original_author_code_checkout":{
            "url":"https://github.com/nbharathik/bibimbap",
            "commit_sha256":AUTHOR_GIT_COMMIT,
            "license_file_in_pinned_checkout":False,
            "code_license_terms_approved":False,
        },
        "original_huggingface_dataset_readonly_public_metadata":{
            "api_url":"https://huggingface.co/api/datasets/"+HF_DATASET_ID,
            "dataset_card_url":"https://huggingface.co/datasets/"+HF_DATASET_ID,
            "observed_on_date":"2026-11-18",
            "id":HF_DATASET_ID,
            "revision_sha":HF_DATASET_SHA,
            "private":False,
            "gated":False,
            "cardData_license_declared":HF_CARD_DECLARED_LICENSE,
            "tag_license_declared":HF_CARD_DECLARED_LICENSE,
            "api_read_only_metadata_fetched":True,
            "dataset_files_downloaded_during_metadata_check":False,
            "underlying_individual_IFC_asset_rights_proven":False,
            "attribution_and_provenance_require_separate_review":True,
            "user_approved_third_party_model_API_transfer":False,
        },
        "important_license_distinction":
            "Dataset-card declares CC-BY-4.0; this does not independently prove "
            "uploader owns every underlying IFC element, code has same license "
            "or user has authorized model-provider upload/data retention.",
        "full_XML_output_budget_observations_UTF8_NOT_TOKENS":arrays,
        "provider_model_snapshot":None,
        "provider_model_endpoint":None,
        "provider_model_real_tokenizer_available_or_selected":False,
        "provider_actual_billed_token_parity":None,
        "provider_max_output_tokens":None,
        "provider_max_context_tokens":None,
        "temperature_seed_top_p_and_retries":None,
        "time_budget_each_arm":None,
        "tool_error_feedback_equivalence":False,
        "approved_money_cap_USD":None,
        "approved_original_IFC_to_model_transfer":False,
        "study_ITT_success_policy_frozen":False,
        "model_generated_task_results_count":0,
        "billable_provider_calls":0,
        "provider_network_clients_or_credentials_used":False,
        "author_grader_data_separated_from_model":True,
        "v055_paid_launch_gate_fail_closed":denied,
        "v056_paid_launch_gate_fail_closed":denied2,
        "streaming_D_must_NOT_be_claimed_matched_tool_affordance_to_I":True,
        "source_canonical_D_state_XML_semantics_unchanged":True,
        "prior_v056_D_feasibility_report_SHA256":PARENT_D_FEASIBILITY_SHA,
    }


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write",action="store_true")
    group.add_argument("--check",action="store_true")
    args=parser.parse_args()
    raw=canonical(build_report())
    if args.write:
        with REPORT.open("xb") as target:
            target.write(raw)
    elif not REPORT.is_file() or REPORT.read_bytes()!=raw:
        raise ValueError("Frozen v0.56 data rights/budget gate report changed")
    print("V056_OFFLINE_MODEL_LAUNCH=BLOCKED HF_CARD_LICENSE=cc-by-4.0 "
          "PROVIDER_BILLED_TOKENS=NULL ACTUAL_MODEL_CALLS=0 "
          "SHA256="+sha256(raw).hexdigest())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
