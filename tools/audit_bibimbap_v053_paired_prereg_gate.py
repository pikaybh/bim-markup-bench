"""v0.53 OFFLINE paired D-state/I-native prospectively frozen *candidate* manifest.

Provides reproducible source/question/tool-schema/prompt/order evidence without
ever importing evaluator target values, developer solutions, model provider,
payment backend or executing model-authored code. Even an all-true approval
object cannot launch a paid trial through this no-launch-only module.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v050_direct_original_state_session import DirectOriginalStateSession050
from tools.bibimbap_v052_live_original_native_python_session import LiveOriginalNativePythonSession052

ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v053_primary_DI_exploratory_prereg_candidate_20261118.json"
AUTHOR_REPORT=ROOT/"reports"/"bibimbap_v053_author_origin_four_original_score_20261118.json"
V052_HASH="83aaebf382ddad136ee55ff4e3b54559e6630b64587c4665f447bb12baffcc31"
TASKS=("geometry_test_14","geometry_test_15","topological_test_11","topological_test_17")
ARMS=("D_STATE","I_NATIVE")
RANDOMIZATION_SEED="BIBIMBAP-v053-exploratory-original4-paired-order-20261118"
COMMON_SYSTEM=(
    "You are a BIM editing research agent. Apply only the requested public "
    "building edit. Preserve original identities and all unrelated building "
    "information. Use only the tools made available in this arm. "
    "Do not request or infer private evaluator answers or grading outcomes."
)
COMMON_USER_PREFIX="Original BIM edit instruction:\n"
CALL_BUDGET=25


class TrialLaunchBlocked(RuntimeError):
    pass


def need(condition: bool,reason:str)->None:
    if not condition:
        raise ValueError(reason)


def _canonical(data:dict)->bytes:
    return (json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)
            +"\n").encode("utf8")


def _hash(text:str)->str:
    return sha256(text.encode("utf8")).hexdigest()


def _future_pair_order(task:str)->list[str]:
    # Randomization seed was selected for experimental order BEFORE model
    # outputs; task IDs are the four engineering-selected exploratory cases.
    digest=sha256((RANDOMIZATION_SEED+"|"+task).encode("utf8")).digest()
    return list(ARMS if digest[0]%2==0 else reversed(ARMS))


def demand_trial_admission(approvals:dict|None=None)->None:
    """Unconditional no-network, no-paid-launch firewall, including all TRUE."""
    del approvals
    raise TrialLaunchBlocked(
        "v0.53 is OFFLINE-ONLY: exact provider snapshot, billable budget, "
        "data-use rights, scoring equivalence, prompt/token parity and user "
        "approval have not been proven. There is no provider execution path."
    )


def prospective_envelope(task_row:dict,arm:str,source_xml:str,
                         tool_schemas:list[dict])->dict:
    """Read-only model message candidate; no developer/evaluator import."""
    need(arm in ARMS,"Only genuine D-state or executed I-native arm supported")
    need(isinstance(source_xml,str) and source_xml.startswith("<?xml"),
         "Expected original XML source state, never a developer control")
    need(isinstance(tool_schemas,list) and len(tool_schemas)==2,
         "Exactly two distinct model-facing tools per primary arm")
    return {
        "arm":arm,
        "task_id":task_row["test_id"],
        "system_message":COMMON_SYSTEM,
        "user_message":COMMON_USER_PREFIX+task_row["public_question"],
        "initial_read_source_xml":source_xml,
        "model_tools":tool_schemas,
        "max_total_tool_calls":CALL_BUDGET,
        "model_output_from_provider":None,
        "no_model_inference_executed":True,
    }


def build_manifest()->dict:
    need(file_hash(ROOT/"reports"/
        "bibimbap_v052_original4_live_docker_python_attestation_20261118.json")
        ==V052_HASH,"Prior live pinned Docker experiment report changed")
    need(AUTHOR_REPORT.is_file() and not AUTHOR_REPORT.is_symlink(),
         "Original-author evaluator-side source audit not yet frozen")
    grader_hash=file_hash(AUTHOR_REPORT)
    grader=json.loads(AUTHOR_REPORT.read_text(encoding="utf8"))
    need(grader["status"]==
         "V053_AUTHOR_CODE_REPLAY_SUCCEEDED_LLM_LAUNCH_BLOCKED"
         and grader["author_origin_task_evaluations_on_developer_native_IFCs"]==16
         and grader["actual_LLM_trials"]==0
         and grader["official_published_paper_score"] is None,
         "Author evaluator-side provenance/GT barrier not properly declared")
    tasks={r["test_id"]:r for r in public_45(AUTHOR,DATA)}
    need(len(tasks)==45 and
         Counter(row["crud"] for row in tasks.values())==
         {"create":15,"update":15,"delete":15}
         and len({row["original_ifc_sha256"]
                  for row in tasks.values()})==31,
         "Original benchmark denominator changed")
    entries={}
    with TemporaryDirectory(prefix="v053-candidate-NO-INFERENCE-") as tmp:
        scratch=Path(tmp)
        for i,task_id in enumerate(TASKS):
            r=tasks[task_id]
            src=DATA/"ifc"/r["original_source_ifc_relpath"]
            need(file_hash(src)==r["original_ifc_sha256"],
                 "Immutable original public IFC source changed")
            direct=DirectOriginalStateSession050(
                src,scratch/f"D_READ_{i}")
            python=LiveOriginalNativePythonSession052(
                src,scratch/f"I_READ_{i}")
            a=direct.call("read_building_xml",{})
            b=python.call("read_building_xml",{})
            need(a["status"]==b["status"]=="ok"
                 and a["xml"]==b["xml"],
                 "D-state and I-native initial source XML bytes differ")
            need(direct.calls_used==python.calls_used==1,
                 "Source read tool call accounting differs")
            need(len(direct.tools)==len(python.tools)==2
                 and [tool["name"] for tool in direct.tools]==
                 ["read_building_xml","submit_building_xml"]
                 and [tool["name"] for tool in python.tools]==
                 ["read_building_xml","execute_ifc_code"],
                 "Primary arm identity or tool authorization changed")
            source=a["xml"]
            env_D=prospective_envelope(r,"D_STATE",source,direct.tools)
            env_I=prospective_envelope(r,"I_NATIVE",source,python.tools)
            need(env_D["system_message"]==env_I["system_message"]
                 and env_D["user_message"]==env_I["user_message"]
                 and env_D["initial_read_source_xml"]==
                     env_I["initial_read_source_xml"],
                 "Common user/system/source model-facing messages differ")
            schema_D=_canonical({"tools":direct.tools})
            schema_I=_canonical({"tools":python.tools})
            need(schema_D != schema_I,
                 "D XML state and I executed Python tools unexpectedly identical")
            entries[task_id]={
                "original_source_ifc_sha256":r["original_ifc_sha256"],
                "original_public_question_sha256":r["public_question_sha256"],
                "original_crud":r["crud"],
                "user_prompt_sha256":_hash(env_D["user_message"]),
                "common_system_prompt_sha256":_hash(COMMON_SYSTEM),
                "initial_D_I_source_xml_byte_identical":True,
                "initial_D_I_source_xml_sha256":_hash(source),
                "initial_source_XML_utf8_bytes":len(source.encode("utf8")),
                "D_tool_schema_sha256":sha256(schema_D).hexdigest(),
                "I_tool_schema_sha256":sha256(schema_I).hexdigest(),
                "D_tool_schema_utf8_bytes":len(schema_D),
                "I_tool_schema_utf8_bytes":len(schema_I),
                "tool_schema_unequal_and_token_budgets_NOT_yet_proven":True,
                "max_tool_calls_each_arm":CALL_BUDGET,
                "assignment_order_preregister_candidate":
                    _future_pair_order(task_id),
                "same_original_IFC_for_each_arm":True,
                "raw_provider_input_tokens_each_arm":None,
                "raw_provider_output_tokens_each_arm":None,
                "paid_provider_model_calls":0,
                "model_success_D":None,
                "model_success_I":None,
                "author_repository_task_metric_from_model":None,
            }
    return {
        "status":"BLOCKED_PENDING_PREREG_APPROVAL_AND_MODEL_FAIRNESS",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/221",
        "frozen_v052_commit":
            "a0ef25fad9e86c32661344a45cee0c15a47b675a",
        "cohort":"ORIGINAL_PUBLIC_BIBIMBAP_FOUR_ENGINEERING_SELECTED_EXPLORATORY",
        "not_a_formally_preregistered_or_random_original_cohort":True,
        "full_original_public_population":45,
        "original_unique_IFC_inputs":31,
        "exploratory_pre_model_trial_cases":4,
        "full_population_unattempted_tasks":41,
        "primary_arms":list(ARMS),
        "auxiliary_restricted_T_XML_or_T_Python_in_primary_study":False,
        "pair_randomization_algorithm":
            "SHA256(seed UTF8 + '|' + task_id UTF8) first byte parity",
        "pair_randomization_seed":RANDOMIZATION_SEED,
        "candidate_trial_slots":8,
        "actual_model_trial_slots_executed":0,
        "same_system_user_message_and_initial_source_for_both_arms":True,
        "max_total_model_tool_calls_per_arm_task":CALL_BUDGET,
        "author_repository_task_tests_replayed_on_developer_controls":True,
        "author_repository_eval_report_sha256":grader_hash,
        "original_author_publication_score_equivalence_verified":False,
        "original_author_paper_scores":None,
        "strict_author_test_all_metrics_pass_per_task":
            "DESCRIPTIVE exploratory candidate only; retain per-metric fractional score",
        "scoring_layers":[
            "independent_v051_original_native_IFC_source_preservation_oracle",
            "independent_v048_public_source_research_physical_predicate",
            "original_author_checkout_execute_test_boolean_metrics",
            "official_published_paper_score_UNVERIFIED",
        ],
        "ITT_denominator_when_authorized":4,
        "intended_paired_estimand":"mean(D_success - I_success) on all four assigned original tasks",
        "inferential_status":"DESCRIPTIVE_ONLY_NOT_CONFIRMATORY",
        "original_model_source_cluster_count":4,
        "provider_exact_model_snapshot":None,
        "provider_api_endpoint":None,
        "provider_billed_usage_tokens":None,
        "provider_pricing_quote":None,
        "max_approved_usd_budget":None,
        "user_approved_paid_experiment":False,
        "provider_data_rights_and_retention_approved":False,
        "model_token_parity_proven":False,
        "model_response_and_tool_error_feedback_parity_proven":False,
        "decoding_temperature_seed_max_output_tokens":None,
        "actual_request_retry_and_error_counting_strategy":None,
        "max_wall_time_per_arm_task_seconds":None,
        "source_rights_for_republication_verified":False,
        "native_ifc_exact_source_hashes_and_task_prompt_hashes":{
            k:entries[k] for k in TASKS
        },
        "no_provider_or_author_published_grader_execution_path":True,
        "caller_approval_does_not_override_offline_gate":True,
        "prior_v052_frozen_report_sha256":V052_HASH,
    }


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write",action="store_true")
    group.add_argument("--check",action="store_true")
    args=parser.parse_args()
    content=_canonical(build_manifest())
    if args.write:
        with REPORT.open("xb") as fd:
            fd.write(content)
    else:
        need(REPORT.is_file() and REPORT.read_bytes()==content,
             "Original primary-D/I prospective manifest changed")
    print("V053_PRIMARY_D_I_CANDIDATE_GATE=BLOCKED "
          "SOURCE_PARITY=4/4 ACTUAL_LLM_CALLS=0 "
          "SHA256="+sha256(content).hexdigest())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
