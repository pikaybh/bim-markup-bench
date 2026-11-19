"""G1 #16: 36-task pilot readiness *reconciliation*, not new scoring.

Cross-checks a fresh read-only source preflight with immutable, previously
reviewed G1 metadata/asset/manual proof reports. No result/GT IFC opens in
this module, no model instructions or private target GUIDs leave the trusted
process, and no D0/I0 trial is launched. Strong manual parity evidence must
NEVER be silently promoted to a complete official task oracle.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from src.data.bim_edit import AuditError
from src.evaluation.g1_coverage import STATIC_UNSUPPORTED,CONDITIONAL


ROOT=Path(__file__).resolve().parents[2]
FROZEN_FILES={
    "candidate":("manifests/pilot_36_candidate_v0.json",
                 "75b4847814dbefad95340556c0b62f9cda72cac319cd82ecb23ea4933c9ab694"),
    "g1_324":("reports/g1_324_support_matrix.json",
              "c5999a6fad50cb90efdac2c2c702164c3d29983bd0fbe3b56e3b3cbd435b43ca"),
    "g1_36":("reports/g1_frozen_source_eligibility_20261110.json",
             "df58e40331ccc0f1da5be60219d226d9b1ae8a89cceed2a0cb6c82f68105a045"),
    "assets":("reports/pilot_asset_audit_partial.json",
              "4657c8a2f4937b5ecc83305ae72fcb0138455af2c40129b8a3cc11dfcb72f927"),
    "manual_window":("reports/manual_real_window_oracle_20261109.json",
                     "b6a27d91f71d68e5edc4d51164a3a15cef9985cc85a9abd4fa4d3616df727063"),
    "manual_wall":("reports/manual_full_declarative_space_pair_20261110.json",
                   "6b6d232d01ef4b5181eba384ef8231596c29a120ccdedef004e2bd54e3f6e402"),
    "manual_wall_v02":("reports/manual_explicit_space_semantics_v02_pair_20261110.json",
                       "740f6078ec46727a444c9e24c6f722f6e467492943278a8efe9b474a8dec4f41"),
    "official":("reports/g0_official_bim_edit_public_release_20261110.json",
                "f7232a0217617b54c97c8ae7f8efd965e2e7a8b051a04490ea05c1af87ad3e48"),
    "budget":("reports/g2_durable_budget_dryrun_20261110.json",
              "63bac4bacad02c66b36d90bf4c066b3bf6c7842c5ec6dfdf5e3192fc5621526e"),
}
EXPECTED_CANDIDATE_STATUS="CANDIDATE_NOT_PREREGISTERED"
EXPECTED_G1_STATUS="BLOCKED_NO_OFFICIAL_PAIRED_D0_I0_TASK_ORACLES"
EXPECTED_STATIC_STATUS="BLOCKED_NO_OFFICIAL_EVALUATION"
EXPECTED_ASSET_STATUS="BLOCKED_FULL_PILOT_ASSET_VERIFICATION"
EXPECTED_ASSET_LABELS={"MISSING_LOCAL_IFC_BYTES",
                       "VERIFIED_PINNED_BYTES_AND_CLASS_DELTA"}
EXPECTED_MANUAL_IDS={"WIN-UPD-DIR-A-002","WAL-CRE-SPA-A-003"}


def _require(ok:bool,message:str)->None:
    if not ok:
        raise AuditError("Pilot readiness evidence mismatch: "+message)


def load_pinned_evidence(*,root:Path=ROOT)->dict:
    """Reject edited manifests/reports before classifying any task."""
    if root.is_symlink() or not root.is_dir():
        raise AuditError("Trusted repository root missing/linked")
    data={}
    for key,(relative,expected) in FROZEN_FILES.items():
        path=root/relative
        if not path.is_file() or path.is_symlink():
            raise AuditError("Pinned research source missing or symlinked: "+key)
        raw=path.read_bytes()
        if sha256(raw).hexdigest()!=expected:
            raise AuditError("Pinned research report/manifest digest mismatch: "+key)
        try:
            obj=json.loads(raw.decode("utf8"))
        except (ValueError,UnicodeDecodeError) as exc:
            raise AuditError("Pinned research source is not JSON: "+key) from exc
        if not isinstance(obj,dict):
            raise AuditError("Pinned research source is not a record: "+key)
        data[key]=obj
    return data


def _indexed(rows:Any,expected:int,kind:str)->dict:
    _require(isinstance(rows,list) and len(rows)==expected,
             kind+" row count mismatch")
    ids=[]
    for row in rows:
        _require(isinstance(row,dict)
                 and isinstance(row.get("task_id"),str)
                 and row["task_id"],kind+" invalid task ID")
        ids.append(row["task_id"])
    _require(len(set(ids))==expected,kind+" duplicated task ID")
    return {r["task_id"]:r for r in rows}


def _manual_source_only_evidence(evidence:dict)->dict:
    """Two real-source demonstrations, neither a full benchmark oracle."""
    win=evidence["manual_window"]
    wall=evidence["manual_wall"]
    wall02=evidence["manual_wall_v02"]
    _require(win.get("task_id")=="WIN-UPD-DIR-A-002"
             and win.get("status")==
             "PASS_ONE_TRUSTED_MANUAL_REAL_SOURCE_ORACLE_NOT_AN_LLM_EXPERIMENT"
             and win.get("paired_independent_ifc_observation_parity") is True
             and win.get("shared_pinned_input") is True
             and win.get("source_bytes_unchanged") is True
             and win.get("model_interpreted_instruction") is False
             and win.get("ground_truth_ifc_opened") is False
             and win.get("official_evaluator_executed") is False
             and win.get("official_tasks_scored")==0
             and win.get("paid_model_calls")==0,
             "untrustworthy manually selected window source-only parity")
    _require(wall.get("frozen_task_id")=="WAL-CRE-SPA-A-003"
             and wall.get("status")==
             "PASS_ONE_TRUSTED_PAIRED_DECLARATIVE_SPACE_ORACLE_NOT_OFFICIAL_BIM_EDIT"
             and wall.get("same_pinned_public_source") is True
             and wall.get("native_independent_ifc_parity") is True
             and wall.get("input_information_equivalence_proven") is False
             and wall.get("model_interpreted_natural_language") is False
             and wall.get("ground_truth_loaded") is False
             and wall.get("official_evaluator_executed") is False
             and wall.get("official_tasks_scored")==0
             and wall.get("LLM_provider_calls")==0,
             "untrustworthy wall D0/I0 source-only demonstration")
    _require(wall02.get("status")==
             "PASS_EXPERIMENTAL_D0_I0_NATIVE_TYPED_SPACE_PARITY_NOT_OFFICIAL"
             and wall02.get("native_independent_six_category_parity") is True
             and wall02.get("native_all_space_type_pset_qto_relation_parity") is True
             and wall02.get("full_native_space_semantics_proven") is False
             and wall02.get("new_room_metadata_in_benchmark_instruction_proven") is False
             and wall02.get("model_facing_v02_promoted") is False
             and wall02.get("model_context_budget_approved") is False
             and wall02.get("ground_truth_loaded") is False
             and wall02.get("official_evaluator_called") is False
             and wall02.get("official_tasks_scored")==0
             and wall02.get("model_calls")==0,
             "untrustworthy experimental v0.2 space semantics provenance")
    for doc,expected_sha in (
        (win,"c533767f850a7ba01b73caf4467fae7cc886807a72a900d65cd480e7b877bcc9"),
        (wall,"e90e635629a85cf1942163db0f647a49edc6d24631ba72ec79a0381c9145a0de"),
        (wall02,"e90e635629a85cf1942163db0f647a49edc6d24631ba72ec79a0381c9145a0de"),
    ):
        key="original_input_sha256" if doc is not wall02 else "source_sha256"
        _require(doc.get(key)==expected_sha,
                 "manual source IFC hash does not match pinned real source")
    return {
        "WIN-UPD-DIR-A-002":"MANUAL_VECTOR_SELECTED_SOURCE_ONLY_PARITY_NOT_FULL_TASK",
        "WAL-CRE-SPA-A-003":"EXPERIMENTAL_V02_SPACE_NATIVE_PARITY_NOT_MODEL_FACING",
    }


def reconcile_pilot_evidence(
    evidence:dict,live_source:dict,*,worker_observation:dict,
    official_scorer:dict,budget:dict
)->dict:
    """Pure status reconciliation; no IFC/GT files loaded or model called."""
    candidate=evidence["candidate"]
    g1=evidence["g1_324"]
    baseline=evidence["g1_36"]
    assets=evidence["assets"]
    _require(candidate.get("status")==EXPECTED_CANDIDATE_STATUS
             and candidate.get("sample_size")==36
             and candidate.get("task_revision")==
             "2dc6462bfab145ddf81b43e9954322855b8443dc"
             and candidate.get("task_data_sha256")==
             "9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83"
             and candidate.get("gate_status")=={
                 "G0":"NOT_PASSED","G1":"NOT_PASSED",
                 "G2":"NOT_PASSED","BUDGET":"NOT_APPROVED"},
             "frozen candidate sample not in known unapproved state")
    _require(g1.get("status")==EXPECTED_STATIC_STATUS
             and g1.get("coverage_accounted_for")==324
             and g1.get("static_engine_unsupported_count")==246
             and g1.get("conditional_source_dependent_unverified_count")==78
             and g1.get("official_tasks_scored")==0
             and g1.get("model_api_calls")==0,
             "324 metadata-only static support report inconsistent")
    _require(baseline.get("status")==EXPECTED_G1_STATUS
             and baseline.get("task_count")==36
             and baseline.get("official_scores_computed")==0
             and baseline.get("paid_model_calls")==0
             and baseline.get("GT_file_loaded") is False,
             "frozen source-only baseline promoted to official score")
    _require(live_source==baseline,
             "live source-only audit drifted from pinned November 10 report")
    _require(assets.get("status")==EXPECTED_ASSET_STATUS
             and assets.get("total_candidate_tasks")==36
             and assets.get("candidate_sha256")==FROZEN_FILES["candidate"][1]
             and assets.get("task_revision")==candidate["task_revision"]
             and assets.get("all_pilot_bytes_and_deltas_verified") is False
             and assets.get("GT_unavailable_to_agents") is True
             and assets.get("official_scores_computed")==0
             and assets.get("paid_model_calls")==0,
             "pinned IFC asset audit missing/overclaimed")
    _require(isinstance(worker_observation,dict)
             and worker_observation.get("real_candidate_execution_authorized") is False
             and worker_observation.get("paid_model_run_authorized") is False
             and worker_observation.get("worker_os_isolation_currently_verified") is False,
             "Docker worker grant/OS isolation unexpected")
    _require(official_scorer.get("official_executable_scorer_available_to_this_project") is False
             and official_scorer.get("official_scorer_numerically_equivalent_to_local") is False
             and official_scorer.get("official_tasks_scored_by_this_project")==0,
             "official scorer grant unexpected")
    _require(budget.get("full_g2_or_g3_live_release_authorized") is False
             and budget.get("real_network_or_model_calls")==0
             and budget.get("official_benchmark_tasks_scored")==0,
             "paid model or budget release unexpected")

    ci=_indexed(candidate["tasks"],36,"candidate")
    si=_indexed(g1["tasks"],324,"static")
    bi=_indexed(baseline["tasks"],36,"source")
    ai=_indexed(assets["tasks"],36,"asset")
    _require(set(ci)==set(bi)==set(ai)
             and set(ci).issubset(si),"public task IDs do not align")
    _require(assets.get("task_status_counts")=={
        "MISSING_LOCAL_IFC_BYTES":6,
        "VERIFIED_PINNED_BYTES_AND_CLASS_DELTA":30
    },"historic asset counts drifted")
    manual=_manual_source_only_evidence(evidence)
    _require(set(manual)==EXPECTED_MANUAL_IDS
             and set(manual).issubset(ci),"manual evidence task IDs not in candidate")

    rows=[]
    for entry in candidate["tasks"]:
        task_id=entry["task_id"]
        stat=si[task_id]
        src=bi[task_id]
        asset=ai[task_id]
        cls=entry["entity_type"]
        _require(stat["operation"]==src["operation"]==asset["operation"]==entry["operation"]
                 and stat["category"]==src["category"]==entry["category"]
                 and stat["scene"]==entry["scene"]
                 and stat["target_class"]==src["target_class"]==asset["target_class"]==cls,
                 "task metadata cross-ledger mismatch")
        expected=STATIC_UNSUPPORTED if src["reason_code"]=="STATIC_ENGINE_UNSUPPORTED" else CONDITIONAL
        _require(stat["engine_status"]==expected,
                 "G1 static and source-only classification inconsistent")
        kind=asset["status"]
        _require(kind in EXPECTED_ASSET_LABELS
                 and (kind!="VERIFIED_PINNED_BYTES_AND_CLASS_DELTA" or (
                     asset.get("input_bytes_verified") is True
                     and asset.get("reference_bytes_verified") is True
                     and asset.get("native_target_delta_verified") is True)),
                 "unsupported asset verification claim")
        _require((src["source_bytes_verified_for_conditional_probe"] is True)
                 ==(src["reason_code"] not in {
                     "STATIC_ENGINE_UNSUPPORTED","MISSING_PINNED_INPUT_IFC"}),
                 "native source probe accounting inconsistent")
        manual_code=manual.get(task_id)
        if manual_code:
            _require(src["source_bytes_verified_for_conditional_probe"] is True
                     and kind=="VERIFIED_PINNED_BYTES_AND_CLASS_DELTA",
                     "manual proof appears on unverified/missing source assets")
        reason=src["reason_code"]
        if reason=="STATIC_ENGINE_UNSUPPORTED":
            disposition="STATIC_ENGINE_UNSUPPORTED"
        elif reason=="MISSING_PINNED_INPUT_IFC":
            disposition="INPUT_IFC_NOT_CACHED"
        elif manual_code is not None:
            disposition="MANUAL_SOURCE_ONLY_EVIDENCE_WITH_GATES"
        else:
            disposition="SOURCE_DEPENDENCY_OR_ORACLE_BLOCKED"
        rows.append({
            "task_id":task_id,
            "operation":entry["operation"],
            "category":entry["category"],
            "scene":entry["scene"],
            "target_class":cls,
            "native_source_probe_completed":src["source_bytes_verified_for_conditional_probe"],
            "previous_pinned_input_and_reference_delta_evidence":
                kind=="VERIFIED_PINNED_BYTES_AND_CLASS_DELTA",
            "historical_asset_audit_not_revalidated_this_turn":True,
            "source_or_engine_reason":reason,
            "manual_evidence_code":manual_code,
            "readiness_disposition":disposition,
            "task_oracle_fully_proven":False,
            "same_information_D0_I0_model_facing_approved":False,
            "official_benchmark_task_scored":False,
        })
    _require(len(rows)==36 and len({r["task_id"] for r in rows})==36,
             "36-task public sample coverage incomplete")
    reason_counts=dict(sorted(Counter(r["source_or_engine_reason"] for r in rows).items()))
    _require(reason_counts==baseline["fail_closed_reason_counts"],
             "source-only reason code totals differ from pinned report")
    _require(sum(r["native_source_probe_completed"] is True for r in rows)==11,
             "11 source-native probes no longer accounted for")
    _require(sum(r["previous_pinned_input_and_reference_delta_evidence"]
                 for r in rows)==30,"historic 30 verified IFC pairs not accounted for")
    _require(sum(r["readiness_disposition"]=="STATIC_ENGINE_UNSUPPORTED"
                 for r in rows)==23,"frozen static support count changed")

    return {
        "status":"BLOCKED_FROZEN_36_NO_COMPLETE_TASK_ORACLES_OR_LIVE_SCORER",
        "method":"trusted_read_only_live_source_plus_sha_pinned_historic_evidence",
        "task_count":36,
        "static_metadata_task_count":324,
        "not_preregistered":True,
        "static_engine_unsupported_count":23,
        "conditional_source_task_count":13,
        "currently_cached_conditional_input_probed_count":11,
        "missing_conditional_input_count":2,
        "historical_verified_input_and_reference_deltas_count":30,
        "historical_unavailable_source_or_GT_asset_count":6,
        "historical_asset_evidence_reverified_now":False,
        "distinct_manual_source_only_pair_task_count":len(manual),
        "manual_source_only_evidence_not_task_oracle":True,
        "full_instruction_specific_paired_D0_I0_task_oracles_proven":0,
        "model_facing_observational_context_parity_full_task_proven":0,
        "official_task_scores":0,
        "real_model_provider_calls":0,
        "model_provider_price_and_token_usage_approved":False,
        "official_scorer_available":False,
        "docker_current_own_worker_admission":worker_observation.get("status"),
        "actual_linux_kernel_isolation_verified_now":False,
        "paid_or_official_pilot_approved":False,
        "reason_counts":reason_counts,
        "disposition_counts":dict(sorted(Counter(
            r["readiness_disposition"] for r in rows).items())),
        "op_counts":dict(sorted(Counter(r["operation"] for r in rows).items())),
        "category_counts":dict(sorted(Counter(r["category"] for r in rows).items())),
        "scene_counts":dict(sorted(Counter(r["scene"] for r in rows).items())),
        "target_class_counts":dict(sorted(Counter(r["target_class"] for r in rows).items())),
        "trusted_manual_proof_filenames_not_exposed_to_model":True,
        "ground_truth_IFC_opened_by_this_reconciler":False,
        "task_prompts_or_target_guids_in_report":False,
        "frozen_source_document_sha256":{
            name:digest for name,(_,digest) in sorted(FROZEN_FILES.items())
        },
        "tasks":rows,
    }
