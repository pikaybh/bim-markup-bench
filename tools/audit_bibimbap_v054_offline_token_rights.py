"""v0.54 strictly offline paired token/rights, license and launch gate.

No model token counts are guessed from UTF8 byte counts. No provider, network,
license source download, Docker invocation or original GT/grader execution.
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

ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
V053_SHA="600a951bfb0733a79f09e9db43376526ceaa9e1a66cc3e800e2ca00601862524"
V054_GRAPH_SHA="27d2ef5c6d24a99303975d32e3c1622f2c241b519d554bb8fe2eb17f50c17442"
REPORT=ROOT/"reports"/"bibimbap_v054_offline_paired_token_and_source_rights_20261118.json"


def build_report()->dict:
    from_file=ROOT/"reports"/"bibimbap_v053_primary_DI_exploratory_prereg_candidate_20261118.json"
    graph=ROOT/"reports"/"bibimbap_v054_delete_source_schema_policy_20261118.json"
    if file_hash(from_file)!=V053_SHA or file_hash(graph)!=V054_GRAPH_SHA:
        raise ValueError("Frozen prior primary D/I or source policy audit changed")
    p=json.loads(from_file.read_text(encoding="utf8"))
    if not(p["status"]=="BLOCKED_PENDING_PREREG_APPROVAL_AND_MODEL_FAIRNESS"
           and p["actual_model_trial_slots_executed"]==0
           and p["max_total_model_tool_calls_per_arm_task"]==25
           and p["same_system_user_message_and_initial_source_for_both_arms"] is True):
        raise ValueError("Prior primary D/I identity or offline gate changed")
    expected_tasks={
        "geometry_test_14","geometry_test_15",
        "topological_test_11","topological_test_17",
    }
    rows=p["native_ifc_exact_source_hashes_and_task_prompt_hashes"]
    if set(rows)!=expected_tasks:
        raise ValueError("Original four task list changed")
    lengths={}
    for task,row in sorted(rows.items()):
        d,i=row["D_tool_schema_utf8_bytes"],row["I_tool_schema_utf8_bytes"]
        source=row["initial_source_XML_utf8_bytes"]
        if (d<=0 or i<=0 or source<=0 or
            not row["initial_D_I_source_xml_byte_identical"] or
            row["max_tool_calls_each_arm"]!=25 or
            row["D_tool_schema_sha256"]==row["I_tool_schema_sha256"]):
            raise ValueError("Candidate D/I source or tool schema parity violated")
        lengths[task]={
            "initial_XML_source_bytes_each_arm":source,
            "D_model_tool_schema_UTF8_bytes":d,
            "I_model_tool_schema_UTF8_bytes":i,
            "I_minus_D_tool_schema_UTF8_bytes":i-d,
            "source_information_exact_byte_identical":True,
            "model_provider_input_tokens_D":None,
            "model_provider_input_tokens_I":None,
            "actual_provider_token_parity_proven":False,
        }
    readme=AUTHOR/"README.md"
    data_readme=AUTHOR/"data"/"README.md"
    download=AUTHOR/"scripts"/"download_data.py"
    for target in (readme,data_readme,download):
        if not target.is_file() or target.is_symlink():
            raise ValueError("Original author source rights reference absent/linked")
    dl=download.read_text(encoding="utf8")
    if "clemenskujat/bibimbap-data" not in dl:
        raise ValueError("Pinned author source dataset repository changed")
    license_present=any((AUTHOR/x).is_file() for x in
                        ("LICENSE","LICENSE.md","COPYING","LICENSE.txt",
                         "LICENSE.rst"))
    if license_present:
        # New license text needs a fresh human legal review; don't silently
        # interpret its presence as an automatic transmission permission.
        raise ValueError("Observed author checkout license state changed: review")
    # This function cannot launch a model, even if all proposed approvals true.
    blocked=False
    try:
        demand_trial_admission({
            "model_snapshot":"APPROVED",
            "billed_token_budget":"APPROVED",
            "cost_limit":"APPROVED",
            "source_rights":"APPROVED",
            "data_retention":"APPROVED",
        })
    except TrialLaunchBlocked:
        blocked=True
    if not blocked:
        raise ValueError("No-launch gate bypassed unexpectedly")
    return {
        "status":"BLOCKED_MODEL_AND_DATA_RELEASE_PENDING_REAL_APPROVAL",
        "exact_original_source_user_prompt_byte_parity":True,
        "all_four_original_source_inputs_IFC4X3":True,
        "max_model_tool_calls_each_arm":25,
        "primary_arms":["D_STATE","I_NATIVE"],
        "per_task_source_and_tool_Utf8_bytes_NOT_actual_tokens":lengths,
        "tool_schema_bytes_differ_between_arms":True,
        "source_lengths_may_demand_chunking_after_prospective_budget_freeze":True,
        "provider_actual_billed_tokens":None,
        "verified_provider_token_budget_equivalence":False,
        "verified_sampling_model_snapshot":None,
        "user_approved_model_and_paid_usd_cap":None,
        "actual_provider_call_count":0,
        "original_author_code_git_repo":"https://github.com/nbharathik/bibimbap",
        "original_author_pinned_commit":"667004e16bd38fd7d538bcee56191465429fd975",
        "original_author_checkout_contains_recognized_license_file":False,
        "github_content_API_pinned_LICENSE_LICENSE_md_COPYING_observation":
            "404_NOT_FOUND_2026_11_18_MANUAL_READONLY_CHECK",
        "original_author_data_source_huggingface_dataset":
            "clemenskujat/bibimbap-data",
        "huggingface_dataset_redistribution_license_verified":False,
        "legal_transmission_or_redistribution_rights_verified":False,
        "license_absence_does_not_establish_copyright_status":True,
        "no_model_prompt_contains_evaluator_source_or_target_guid":True,
        "offline_no_paid_inference_gate_test_passed":blocked,
        "prior_v053_primary_candidate_sha256":V053_SHA,
        "prior_v054_native_schema_audit_sha256":V054_GRAPH_SHA,
        "author_publication_official_scorer_version_equivalence":None,
        "next_approval_items":[
            "source_data_owner_permission_for_provider_API_transfer",
            "actual_author_or_HuggingFace_dataset_license_reuse_terms",
            "exact_provider_and_model_snapshot",
            "real_provider_measured_billed_tokens_each_arm",
            "explicit_total_cost_cap_and_user_authorization",
            "same_transcript_feedback_and_turn_budget",
            "scoring_policy_freeze_for_schema_invalid_1.0_author_deletion",
        ],
    }


def canonical(data:dict)->bytes:
    return (json.dumps(data,sort_keys=True,ensure_ascii=False,indent=2)
            +"\n").encode("utf8")


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--write",action="store_true")
    g.add_argument("--check",action="store_true")
    opts=parser.parse_args()
    raw=canonical(build_report())
    if opts.write:
        with REPORT.open("xb") as f:
            f.write(raw)
    elif not REPORT.is_file() or REPORT.read_bytes()!=raw:
        raise ValueError("Frozen offline token/rights report is no longer identical")
    print("V054_TOKEN_RIGHTS=BLOCKED D_I_SOURCE_PARITY=4/4 "
          "TOKEN_PARITY=UNPROVEN BILLABLE_CALLS=0 SHA256="
          +sha256(raw).hexdigest())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
