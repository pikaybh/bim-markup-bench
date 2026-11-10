"""Offline, model-free context accounting and fail-closed G3 fairness gate.

This reads the REAL existing G2 model-visible *source objects* for D/I;
there is still no provider transport/request renderer, selected tokenizer,
approved model or executable Python sandbox. It therefore measures exact
UTF-8 bytes/codepoints and fingerprints but NEVER invents token counts,
paid cost, executed LLM attempts, official accuracy or approved fairness.

A separate candidate v0.2 read-only source-semantic overlay can be audited
for both arms without changing either live v0.1 model-facing runner.
The synthetic developer-authored *answer* XML is NEVER added to the input.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from src.direct_markup.agent_runner import (
    SourceOnlySettings,stage_source_only_workspace,
)
from src.imperative_control.agent_runner import (
    ControlConfig,ImperativeControlSession,create_matched_observations,
)
from src.runtime.space_semantics_candidate import (
    project_space_semantics_candidate,verify_unedited_space_semantics_candidate,
)
from src.data.bim_edit import (
    read_tasks,repo_asset_path,verify_local_asset_bytes,
)
from src.data.pilot_asset_audit import _files_in_root


class OfflineContextGateError(ValueError):
    """Reject task/source/context mismatches without a model call."""


@dataclass(frozen=True)
class ContextComponent:
    byte_length:int
    codepoint_length:int
    sha256:str

    def as_dict(self)->dict:
        return {
            "utf8_bytes":self.byte_length,
            "unicode_codepoints":self.codepoint_length,
            "sha256":self.sha256,
            "provider_input_tokens":None,
            "billable_provider_tokens":None,
        }


def component(text:str)->ContextComponent:
    if not isinstance(text,str):
        raise OfflineContextGateError("Expected actual model-visible UTF-8 text")
    encoded=text.encode("utf8",errors="strict")
    return ContextComponent(len(encoded),len(text),sha256(encoded).hexdigest())


def matched_shared_components(direct,imperative,source_digest:str)->dict:
    """Five independently generated common observations must match."""
    pairs={
        "public_task_id":(direct.task_id,imperative.task_id),
        "public_instruction":(direct.instruction,imperative.instruction),
        "v01_source_xml":(direct.xml_text,imperative.model_xml_text),
        "v01_schema_spec":(direct.language_spec,imperative.toy_language_spec),
        "source_ifc_digest":(source_digest,imperative.input_ifc_sha256),
    }
    for field,(left,right) in pairs.items():
        if left!=right:
            raise OfflineContextGateError(
                "D/I common source observation mismatch: "+field)
    if len(source_digest)!=64 or any(c not in "0123456789abcdef"
                                     for c in source_digest):
        raise OfflineContextGateError("Invalid source IFC digest")
    return {name:component(value).as_dict() for name,(value,_) in pairs.items()}


def verify_overlay_pair(source:Path,overlay_d:bytes,overlay_i:bytes)->dict:
    """Only native SOURCE-observed v0.2 overlays permitted in audit."""
    if overlay_d!=overlay_i:
        raise OfflineContextGateError("D/I v0.2 proposed overlay bytes differ")
    try:
        src=verify_unedited_space_semantics_candidate(source,overlay_d)
    except Exception as exc:
        raise OfflineContextGateError(
            "Candidate overlay not exactly source-verified/read-only") from exc
    if not src.get("unedited_candidate_verified"):
        raise OfflineContextGateError("Candidate overlay not source-verified")
    try:
        text=overlay_d.decode("utf8",errors="strict")
    except UnicodeDecodeError as exc:
        raise OfflineContextGateError("Candidate overlay not UTF-8") from exc
    return {
        **component(text).as_dict(),
        "source_only":True,
        "candidate_model_facing_enabled":False,
        "candidate_authoring_answer_exposed":False,
    }


def _approved_model_transport_is_available(plan:dict)->bool:
    # This is deliberately NOT an adapter for an assumed model name.
    return (isinstance(plan.get("model_id"),str)
            and bool(plan["model_id"].strip())
            and isinstance(plan.get("model_provider"),str)
            and bool(plan["model_provider"].strip())
            and bool(plan.get("actual_provider_spend_authorized"))
            and bool(plan.get("paid_calls_enabled"))
            and plan.get("study_protocol_status")=="FROZEN_REGISTERED")


def _bounded_plan_readiness(plan:dict)->dict:
    if (type(plan.get("max_input_tokens_per_attempt")) is not int
            or type(plan.get("max_output_tokens_per_attempt")) is not int
            or type(plan.get("max_attempts_per_task")) is not int
            or min(plan["max_input_tokens_per_attempt"],
                   plan["max_output_tokens_per_attempt"],
                   plan["max_attempts_per_task"])<=0):
        raise OfflineContextGateError("Invalid draft experiment resource limits")
    return {
        "draft_only":plan.get("study_protocol_status")=="DRAFT_NOT_FROZEN",
        "planned_input_token_limit_per_attempt":
            plan["max_input_tokens_per_attempt"],
        "planned_output_token_limit_per_attempt":
            plan["max_output_tokens_per_attempt"],
        "planned_max_attempts_per_task":plan["max_attempts_per_task"],
        "provider_name_selected":bool(plan.get("model_provider")),
        "provider_model_selected":bool(plan.get("model_id")),
        "tokenizer_exact_for_selected_model_verified":False,
        "provider_input_tokens":None,
        "provider_output_tokens":None,
        "provider_price_revision_verified":False,
        "estimated_usd_from_measured_tokens":None,
        "live_provider_billing_authorized":_approved_model_transport_is_available(plan),
    }


def _frozen_manifest_coverage(root:Path)->dict:
    file=root/"manifests/pilot_36_candidate_v0.json"
    audit_file=root/"reports/g1_frozen_source_eligibility_20261110.json"
    plan_file=root/"configs/pilot_36_plan_v0.json"
    manifest=json.loads(file.read_text(encoding="utf8"))
    original=json.loads(audit_file.read_text(encoding="utf8"))
    plan=json.loads(plan_file.read_text(encoding="utf8"))
    digest=sha256(file.read_bytes()).hexdigest()
    if (len(manifest.get("tasks",[]))!=36
            or len({r["task_id"] for r in manifest["tasks"]})!=36
            or digest!=original.get("frozen_candidate_sha256")
            or original.get("task_count")!=36):
        raise OfflineContextGateError("Frozen candidate or source audit diverged")
    return {
        "frozen_candidate_sha256":digest,
        "frozen_candidate_size":36,
        "paired_attempts_if_all_tasks_approved":36*2,
        "source_eligibility_snapshot_status":original["status"],
        "source_eligibility_snapshot_date":"2026-11-10",
        "source_classifier_is_conservative_legacy_v01_not_latest_native":True,
        "conservative_v01_static_unsupported":original["static_unsupported_count"],
        "conservative_source_missing_conditional_inputs":
            original["missing_conditional_source_count"],
        "legacy_source_reason_counts":original["fail_closed_reason_counts"],
        "verified_current_full_36_paired_oracle_coverage":False,
        "official_benchmark_tasks_scored":0,
        "plan":_bounded_plan_readiness(plan),
    }


def evaluate_release_gate(evidence:dict)->dict:
    """An exact fair paid trial is blocked until all independently verified."""
    conditions={
        "same_public_source_text_and_sha":
            evidence["shared_source_facts_identical"],
        "candidate_overlay_equal_and_source_only":
            evidence["proposed_v02_metadata"]["source_only"],
        "model_context_transport_implemented_and_verified":False,
        "exact_selected_model_tokenizer_implemented":False,
        "per_arm_provider_token_usage_measured":False,
        "v02_ablation_preregistered_and_context_budget_approved":False,
        "live_d_and_i_tools_verified_isolated":False,
        "official_evaluator_provenance_and_score_calibrated":
            evidence["official_evaluator_verified"],
        "full_frozen_task_coverage_and_rights_verified":False,
        "model_price_snapshot_and_spend_approved":False,
        "durable_provider_budget_runtime_implemented":False,
    }
    return {
        "status":"BLOCKED_NO_ACTUAL_MODEL_TOKEN_COUNTS_OR_FAIR_G3_RUN",
        "all_prerequisites_satisfied":all(conditions.values()),
        "preconditions":conditions,
        "blocking_reason_codes":[name for name,passes in conditions.items()
                                 if not passes],
        "actual_provider_tokens":None,
        "actual_usd_cost":None,
        "official_task_scores":0,
        "model_calls":0,
    }


def audit_one_frozen_real_context(root:Path)->dict:
    # Trusted public INPUT metadata only. Hidden target and GT fields in the
    # task record are never serialized into either model-visible context.
    by_id={entry["task_id"]:entry
           for entry in read_tasks(root/"data/tasks.jsonl")}
    task=by_id["WAL-CRE-SPA-A-003"]
    tree=json.loads((root/"data/bim_edit_remote_tree.json").read_text("utf8"))
    remote={entry["path"]:entry for entry in tree
            if entry.get("type")=="file"}
    asset=repo_asset_path(task["input_ifc"])
    source=_files_in_root((root/"data/ifc").resolve(),asset)
    verify_local_asset_bytes(source,remote[asset])
    frozen_sha=sha256(source.read_bytes()).hexdigest()
    public={"task_id":task["task_id"],
            "instruction":task["prompt"],
            "input_file":"input.ifc"}
    with TemporaryDirectory(prefix="g2-source-only-cost-fairness-") as td:
        session=stage_source_only_workspace(
            source,Path(td)/"d_arm",public,SourceOnlySettings())
        d=session.agent_visible_context()
        observed=create_matched_observations(source,public)
        i=ImperativeControlSession(observed,ControlConfig())
        i_view=i.model_visible_context()
        shared=matched_shared_components(d,observed,frozen_sha)
        api_notes=i_view.get("api_reference_notes")
        if not isinstance(api_notes,str) or not api_notes:
            raise OfflineContextGateError("I0 tool/API notes are not materialized")
        if (i_view.get("OS_sandbox_available") or
                i_view.get("allowed_execution_operations")):
            raise OfflineContextGateError(
                "Unverified imperative execution is unexpectedly enabled")
        if d.allowed_operations!=("read_text","patch_text","rewrite_xml_text"):
            raise OfflineContextGateError("D0 authoring scope unexpectedly changed")
        candidate_d=project_space_semantics_candidate(source)
        candidate_i=project_space_semantics_candidate(source)
        overlay=verify_overlay_pair(source,candidate_d.xml,candidate_i.xml)
        # A developer-authored *result* XML is NOT part of the observation.
        # That would contaminate the inference experiment with answer leakage.
        if sha256(source.read_bytes()).hexdigest()!=frozen_sha:
            raise OfflineContextGateError("Original public IFC modified by audit")
        pilot=_frozen_manifest_coverage(root)
        g2=json.loads((root/"reports/G2_readiness.json").read_text("utf8"))
        blind=json.loads((root/"reports/isolated_blind_public_scorer_evidence.json").read_text("utf8"))
        rights=json.loads((root/"manifests/source_rights.json").read_text("utf8"))
        if g2.get("status")!="BLOCKED_FOR_LIVE_MODEL_PILOT":
            raise OfflineContextGateError("Unexpected G2 live execution gate")
        if blind.get("metric_origin")!="independent-reimplementation":
            raise OfflineContextGateError("Independent scorer provenance changed")
        source_rights=next((r for r in rights["records"]
                           if r["source"]=="BIM-Edit/BIM-Edit"),None)
        if not source_rights:
            raise OfflineContextGateError("No BIM-Edit per-model license ledger")
        report={
            "version":"g2-offline-context-cost-fairness-audit-v0.1",
            "task_id":task["task_id"],
            "source_sha256":frozen_sha,
            "shared_source_facts_identical":True,
            "shared_source_components":shared,
            "direct_xml_only_authoring_operations":
                list(d.allowed_operations),
            "imperative_python_only_authoring_operations":
                list(i_view["allowed_authoring_operations"]),
            "imperative_api_notes":component(api_notes).as_dict(),
            "imperative_os_sandbox_available":False,
            "imperative_python_executed":False,
            "direct_bim_api_access_available":False,
            "proposed_v02_metadata":overlay,
            "v02_experimental_authoring_answer_present_in_model_input":False,
            "v02_candidate_added_exact_utf8_bytes":overlay["utf8_bytes"],
            "v02_candidate_added_provider_tokens":None,
            "provider_tokenizer_installed":
                bool(importlib.util.find_spec("tiktoken")),
            "tokenizer_for_target_model_verified":False,
            "real_provider_token_count":None,
            "provider_price_or_billing_snapshot_freshness_verified":False,
            "frozen_pilot":pilot,
            "g2_current_status":g2["status"],
            "official_evaluator_verified":
                bool(blind.get("official_evaluator_equivalent",False)),
            "scorer_metric_origin":blind["metric_origin"],
            "source_model_rights_cleared":
                bool(source_rights.get("rights_checked")
                     and source_rights.get("redistribution_permitted")),
            "hidden_ground_truth_opened":False,
            "input_ifc_original_sha_unchanged":True,
        }
        report["release"]=evaluate_release_gate(report)
        if report["release"]["all_prerequisites_satisfied"]:
            raise OfflineContextGateError("This audit cannot authorize a model run")
        return report
