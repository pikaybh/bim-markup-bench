"""First matched LLM pilot PREPARATION gate (G1 #16 / G2 #19-20).

Six source-only D0/I0 real IFC native outputs are inspected by a separate
post-hoc surrogate. This is NOT an LLM trial and is NOT a scored BIM-Edit
benchmark. Every original 36 task ID remains in the fixed denominator.

No private task metadata, GT IFC, model calls, Docker start/exec, or
provider billing is used. Trial-ready is FALSE until rights, an approved
independent task-level rubric, an isolated worker, exact model/provider
envelope, and the owner's budget are independently established.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from src.evaluation.three_case_source_rubric import score_source_relative
from tools.verify_prompt_grounded_window_pair import verify_prompt_grounded_window_pair
from tools.verify_prompt_grounded_spatial_wall import verify_prompt_grounded_spatial_wall
from tools.verify_public_door_delete_gate import verify_public_door_delete_gate


ROOT=Path(__file__).resolve().parents[2]
CASES=("WIN-UPD-DIR-A-002","WAL-CRE-SPA-A-003","DOR-DEL-DIR-A-001")
EVIDENCE={
    "fixed_36":("reports/g1_frozen_36_offline_three_pair_recheck_20261111.json",
                "f96eda3fb23e549e7274105429049e99d8ee998e31548ff5b61c0bac42c4c16c"),
    "model_rights":("reports/g0_pilot_ifc_rights_20261110.json",
                    "93ccd8f716b1a9dcd48fdd9967013977e1fbbdd3453a55a62dbaea755a01539a"),
    "local_worker":("reports/g2_local_worker_live_preflight_20261111.json",
                    "a27fd255f8d499cec63b08056cfaa5802a781488b17aa67544841a0ca8e0f592"),
    "offline_budget":("reports/g2_durable_budget_dryrun_20261110.json",
                      "63bac4bacad02c66b36d90bf4c066b3bf6c7842c5ec6dfdf5e3192fc5621526e"),
    "common_context":("reports/g2_frozen_context_live_recheck_20261111.json",
                      "6e19fac000df3601e14710d2d994b693286d727419edbc7c833de12d730630c6"),
}


class FirstPilotNotReady(ValueError):
    """Evidence/source hash or the experimental release contract changed."""


def _need(ok,reason):
    if not ok:
        raise FirstPilotNotReady(reason)


def checked_evidence(root:Path=ROOT)->dict:
    data={}
    for key,(relative,expected) in EVIDENCE.items():
        path=root/relative
        _need(path.is_file() and not path.is_symlink(),
              "Prior public-readiness report missing or linked: "+key)
        raw=path.read_bytes()
        _need(sha256(raw).hexdigest()==expected,
              "Prior evidence was changed: "+key)
        try:
            data[key]=json.loads(raw)
        except (ValueError,UnicodeDecodeError) as exc:
            raise FirstPilotNotReady("Malformed prior source-only evidence: "+key) from exc
    sample=data["fixed_36"]
    _need(
        sample.get("frozen_candidates")==36
        and sample.get("posthoc_dev_native_pairs_passed_now")==3
        and sample.get("full_instruction_specific_D0_I0_task_oracles_proven")==0
        and sample.get("actual_LLM_trials")==0
        and sample.get("official_bim_edit_tasks_scored")==0
        and sample.get("paid_budget_approved") is False
        and set(sample.get("source_only_pair_task_ids",[]))==set(CASES),
        "Fixed 36 native proof was silently promoted/reclassified")
    rights=data["model_rights"]
    _need(
        rights.get("gate_status")=="BLOCKED_PER_MODEL_RIGHTS_AND_MISSING_IFC_CONTENT"
        and rights.get("individual_model_license_documents_verified")==0
        and rights.get("full_g0_release_authorized") is False,
        "Per-model IFC rights incorrectly declared cleared")
    worker=data["local_worker"]
    _need(
        worker.get("status")=="BLOCKED_LOCAL_DOCKER_ENGINE_UNAVAILABLE"
        and worker.get("true_external_task_worker_approved") is False
        and worker.get("G2_paid_or_generated_model_worker_authorized") is False
        and worker.get("actual_OS_isolation_test_executed") is False
        and worker.get("Docker_or_WSL_services_started") is False,
        "Local container worker is not independently approved")
    budget=data["offline_budget"]
    _need(
        budget.get("experiment_source")=="OFFLINE_SYNTHETIC_VALUES_ONLY"
        and budget.get("provider_prices_verified") is False
        and budget.get("real_network_or_model_calls")==0
        and budget.get("full_g2_or_g3_live_release_authorized") is False,
        "Synthetic budget was not distinguished from actual provider approval")
    context=data["common_context"]
    _need(
        context.get("tasks_total")==36
        and context.get("status_counts")=={
            "MISSING_PINNED_SOURCE_INPUT":2,
            "PASS_OFFLINE_SHARED_SOURCE_BYTES_ONLY":11,
            "STATIC_UNSUPPORTED_NOT_CONTEXT_TESTED":23}
        and context.get("provider_tokens_measured") is False
        and context.get("sandbox_verified") is False
        and context.get("live_pilot_authorized") is False,
        "Common public context checks were overstated")
    return data


def run_first_pilot_preflight(*, root:Path=ROOT,
                              runners:dict|None=None)->dict:
    """Real source-relative IFC checks on 3/36; no LLM or GT."""
    proof=checked_evidence(root)
    observed={}
    def pair(case):
        def callback(original:Path,d0:Path,i0:Path,prompt:str):
            if case in observed:
                raise FirstPilotNotReady("Source result observed twice")
            scored={
                "D0":score_source_relative(case,original,d0,prompt),
                "I0":score_source_relative(case,original,i0,prompt),
            }
            observed[case]=scored
            return {"trusted_surrogate_not_model_exposed":True}
        return callback
    def door(original:Path,candidate:Path,prompt:str):
        case=CASES[2]
        scored=score_source_relative(case,original,candidate,prompt)
        current=observed.setdefault(case,{})
        arm="D0" if not current else "I0"
        if arm in current:
            raise FirstPilotNotReady("Duplicate Door native result")
        current[arm]=scored
        return {"trusted_surrogate_not_model_exposed":True}

    chosen = runners if runners is not None else {
        CASES[0]: verify_prompt_grounded_window_pair,
        CASES[1]: verify_prompt_grounded_spatial_wall,
        CASES[2]: verify_public_door_delete_gate,
    }
    _need(set(chosen)==set(CASES), "Changed diagnostic task population")
    original_results = {}
    for case in CASES:
        if case==CASES[2]:
            original_results[case] = chosen[case](spatial_observer=door)
        else:
            original_results[case] = chosen[case](physical_observer=pair(case))
    EXPECTED = {
        CASES[0]: "PASS_PROMPT_DERIVED_SOURCE_ONLY_PAIR_OFFICIAL_TASK_STILL_UNVERIFIED",
        CASES[1]: "PASS_PROMPT_GROUNDED_WALL_TWO_JOINS_SOURCE_ONLY_FULL_ORACLE_BLOCKED",
        CASES[2]: "PASS_BOUNDED_D0_I0_NATIVE_DELETION_OFFICIAL_TASK_BLOCKED",
    }
    for case,r in original_results.items():
        _need(isinstance(r,dict) and r.get("status")==EXPECTED[case]
              and r.get("official_tasks_scored")==0,
              "Native pair runner forged official success or unsupported outcome")
        if case==CASES[0]:
            _need(r.get("LLM_calls")==0
                  and r.get("full_official_reference_IFC_task_success_proven") is False
                  and r.get("G1_G2_G3_live_release_authorized") is False,
                  "Window runner claimed unsupported LLM/official outcome")
        elif case==CASES[1]:
            _need(r.get("model_provider_calls")==0
                  and r.get("complete_task_oracle_proven") is False
                  and r.get("G1_G2_G3_experiment_unblocked") is False,
                  "Wall runner claimed unsupported LLM/official outcome")
        else:
            _need(r.get("LLM_calls")==0 and r.get("full_task_oracle_proven") is False
                  and r.get("G1_G2_G3_release_allowed") is False,
                  "Door runner claimed unsupported LLM/official outcome")
    _need(set(observed)==set(CASES)
          and all(set(row)=={"D0","I0"} for row in observed.values()),
          "All six independent native result checks not observed")
    cases=[]
    for case in CASES:
        values=observed[case]
        _need(all(r["source_relative_native_checks_pass"] is True
                  and r["metric_origin"]=="surrogate"
                  and r["full_instruction_specific_task_success_approved"] is False
                  and r["official_bim_edit_score"] is None
                  and r["candidate_origin_verified_by_grader"] is False
                  and r["grader_itself_called_model_provider"] is False
                  and r["grader_provider_calls"] == 0
                  for r in values.values()),
              "Surrogate native checks were promoted into task success")
        _need(values["D0"]["input_ifc_sha256"]==
              values["I0"]["input_ifc_sha256"],
              "Arm source IFC content not identical")
        cases.append({
            "task_id":case,
            "source_sha256":values["D0"]["input_ifc_sha256"],
            "surrogate_metric_origin":"surrogate",
            "d0_source_relative_native_pass":True,
            "i0_source_relative_native_pass":True,
            "native_postcondition":values["D0"]["source_only_criterion"],
            "unproven_full_task_condition":values["D0"]["unresolved_full_task_condition"],
            "d0_output_sha256":values["D0"]["candidate_ifc_sha256"],
            "i0_output_sha256":values["I0"]["candidate_ifc_sha256"],
            "full_task_scored":False,
        })
    return {
        "version":"FIRST_MATCHED_PILOT_SOURCE_ONLY_PRECHECK_V0.1",
        "status":"TECHNICAL_SOURCE_RELATIVE_PAIRS_PASS_REAL_LLM_PILOT_BLOCKED",
        "original_fixed_pilot_task_count":36,
        "frozen_candidate_population_modified":False,
        "posthoc_demonstration_cases":list(CASES),
        "offline_d0_i0_ifc_pairs_rerun":3,
        "offline_native_outputs_scored_by_surrogate":6,
        "surrogate_postconditions_passed":6,
        "source_relative_rubric_posthoc_not_preregistered":True,
        "full_task_instruction_oracles_approved":0,
        "official_bim_edit_scores_computed":0,
        "model_generated_attempts":0,
        "provider_or_network_calls":0,
        "real_paid_spend_usd":0,
        "source_model_rights_cleared":False,
        "approved_original_bim_edit_external_model_count":0,
        "worker_linux_engine_available":False,
        "candidate_python_isolation_verified":False,
        "model_provider_and_exact_tokenizer_selected":False,
        "provider_input_output_tokens_measured":False,
        "price_snapshot_verified":False,
        "explicit_paid_spend_authorization":False,
        "model_context_tool_feedback_parity_approved":False,
        "independent_full_task_evaluator_prospectively_approved":False,
        "real_matched_llm_trial_allowed":False,
        "expected_step_before_pilot":(
            "Prospectively review independent full-task evaluator/eligibility; "
            "clear IFC model rights; approve model, cost cap and exact token "
            "envelope; verify isolated I-arm Linux worker and D/I feedback parity."
        ),
        "linked_evidence_hashes":{
            key:value[1] for key,value in sorted(EVIDENCE.items())
        },
        "cases":cases,
    }
