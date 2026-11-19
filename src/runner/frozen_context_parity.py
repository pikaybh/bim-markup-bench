"""Issue #20: frozen-pilot *source-only* D/I observation coverage, never a live trial.

This trusted, non-agent audit reads only the public task ID, instruction and
original IFC. It never opens reference IFCs or consumes task target/evaluation
metadata; it emits no prompts, native GUIDs, IFC paths or answer artifacts.
Matching text emitted by two adapters is a necessary, not sufficient,
information-parity condition. Tool execution and token fairness are NOT proven.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from src.data.bim_edit import agent_view, read_tasks, repo_asset_path, verify_local_asset_bytes
from src.data.pilot_asset_audit import _files_in_root
from src.direct_markup.agent_runner import SourceOnlySettings, stage_source_only_workspace
from src.imperative_control.agent_runner import (
    ControlConfig, ImperativeControlSession, create_matched_observations,
)
from src.data.pilot_workspace import _frozen_inputs, pilot_staging_preflight
from src.runner.offline_context_cost_gate import component, matched_shared_components

ROOT = Path(__file__).resolve().parents[2]
TASK_SHA = "9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83"
SAMPLE_SHA = "75b4847814dbefad95340556c0b62f9cda72cac319cd82ecb23ea4933c9ab694"
SOURCE_AUDIT_SHA = "df58e40331ccc0f1da5be60219d226d9b1ae8a89cceed2a0cb6c82f68105a045"
REMOTE_TREE_SHA = "f1b150a576f3d72045819768215c34fd84602ab4f6a5f4d2f0202a0ae3a92a39"
ALLOWED_D = ("read_text", "patch_text", "rewrite_xml_text")


class FrozenContextAuditError(ValueError):
    """Fail closed on a changed study population or untrusted file."""


def _digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise FrozenContextAuditError("Required frozen public file missing or linked")
    return sha256(path.read_bytes()).hexdigest()


def _load_fixed_inputs(root: Path):
    task_file = root / "data/tasks.jsonl"
    sample_file = root / "manifests/pilot_36_candidate_v0.json"
    audit_file = root / "reports/g1_frozen_source_eligibility_20261110.json"
    if _digest(task_file) != TASK_SHA or _digest(sample_file) != SAMPLE_SHA:
        raise FrozenContextAuditError("Frozen public task records or pilot changed")
    if _digest(audit_file) != SOURCE_AUDIT_SHA:
        raise FrozenContextAuditError("Frozen prior source eligibility evidence changed")
    tree_path = root / "data/bim_edit_remote_tree.json"
    if _digest(tree_path) != REMOTE_TREE_SHA:
        raise FrozenContextAuditError("Pinned remote IFC blob/LFS metadata changed")
    rows = {row["task_id"]: row for row in read_tasks(task_file)}
    sample = json.loads(sample_file.read_text(encoding="utf8"))
    earlier = json.loads(audit_file.read_text(encoding="utf8"))
    selected = [r["task_id"] for r in sample["tasks"]]
    gates = {r["task_id"]: r for r in earlier["tasks"]}
    if (
        len(selected) != 36 or len(set(selected)) != 36
        or set(selected) != set(gates) or not set(selected) <= set(rows)
        or earlier.get("task_count") != 36
        or earlier.get("static_unsupported_count") != 23
        or earlier.get("source_conditionals_checked") != 11
        or earlier.get("missing_conditional_source_count") != 2
        or earlier.get("frozen_candidate_sha256") != SAMPLE_SHA
        or earlier.get("GT_file_loaded") is not False
        or earlier.get("official_scores_computed") != 0
    ):
        raise FrozenContextAuditError("Frozen 36 source-eligibility crosswalk diverged")
    tree = json.loads(tree_path.read_text(encoding="utf8"))
    files = {item["path"]: item for item in tree if item.get("type") == "file"}
    return rows, selected, gates, files


def _check_one_public_source(root: Path, public: dict, source: Path, digest: str) -> dict:
    """No GT or target fields; per-task temporary model-facing source views."""
    with TemporaryDirectory(prefix="g2-frozen-context-only-") as temporary:
        direct = stage_source_only_workspace(
            source, Path(temporary) / "D", public, SourceOnlySettings()
        ).agent_visible_context()
        observed = create_matched_observations(source, public)
        imperative = ImperativeControlSession(observed, ControlConfig())
        i_view = imperative.model_visible_context()
        shared = matched_shared_components(direct, observed, digest)
        notes = i_view.get("api_reference_notes")
        if (
            direct.allowed_operations != ALLOWED_D
            or not isinstance(notes, str) or not notes
            or i_view.get("OS_sandbox_available") is not False
            or i_view.get("allowed_execution_operations") != []
            or direct.instruction != public["instruction"]
            or i_view.get("instruction") != public["instruction"]
        ):
            raise FrozenContextAuditError("Authoring tool or public view contract changed")
        if _digest(source) != digest:
            raise FrozenContextAuditError("Original IFC changed during read-only audit")
        return {
            "status": "PASS_OFFLINE_SHARED_SOURCE_BYTES_ONLY",
            "source_sha256": digest,
            "shared_source_observation": shared,
            "imperative_extra_api_notes": component(notes).as_dict(),
            "provider_tokens": None,
            "native_ifc_edited": False,
            "GT_file_opened": False,
        }


def audit_frozen_source_contexts(root: Path = ROOT) -> dict:
    rows, selected, gates, files = _load_fixed_inputs(root)
    cache_root = (root / "data/ifc").resolve()
    if not cache_root.is_dir() or cache_root.is_symlink():
        raise FrozenContextAuditError("Frozen IFC source cache unavailable")
    outcomes = []
    for task_id in selected:
        gate = gates[task_id]
        if gate["reason_code"] == "STATIC_ENGINE_UNSUPPORTED":
            outcomes.append({"task_id": task_id, "status": "STATIC_UNSUPPORTED_NOT_CONTEXT_TESTED"})
            continue
        if gate["source_bytes_verified_for_conditional_probe"] is not True:
            outcomes.append({"task_id": task_id, "status": "MISSING_PINNED_SOURCE_INPUT"})
            continue

        # This explicitly projects ONLY the three public authoring inputs:
        # task ID, natural-language prompt, immutable original IFC.
        public_task = rows[task_id]
        public = {"task_id": task_id, "instruction": public_task["prompt"],
                  "input_file": "input.ifc"}
        try:
            asset = repo_asset_path(public_task["input_ifc"])
            source = _files_in_root(cache_root, asset)
            if asset not in files:
                raise FrozenContextAuditError("Pinned source omitted from remote tree")
            verify_local_asset_bytes(source, files[asset])
            digest = _digest(source)
            result = _check_one_public_source(root, public, source, digest)
            # No raw prompt, IFC path, native GUID or private benchmark fields.
            outcomes.append({"task_id": task_id, **result})
        except Exception:
            # Fail closed: do not disclose IFC-derived text, exceptions or paths.
            outcomes.append({"task_id": task_id, "status": "BLOCKED_NATIVE_SOURCE_OR_CONTEXT"})
    counts = dict(sorted(Counter(item["status"] for item in outcomes).items()))
    succeeded = counts.get("PASS_OFFLINE_SHARED_SOURCE_BYTES_ONLY", 0)
    report = {
        "version": "frozen-36-source-only-context-coverage-v0.1",
        "task_data_sha256": TASK_SHA,
        "frozen_candidate_sha256": SAMPLE_SHA,
        "tasks_total": len(selected),
        "conditional_source_verified_candidates": 11,
        "context_parity_checked": succeeded,
        "context_parity_blocked": 11 - succeeded,
        "static_engine_unsupported_not_tested": 23,
        "missing_conditional_source_inputs": 2,
        "status_counts": counts,
        "tasks": outcomes,
        "agent_target_metadata_exposed": False,
        "GT_ifc_opened": False,
        "official_benchmark_tasks_scored": 0,
        "model_calls": 0,
        "provider_tokens_measured": False,
        "imperative_code_executed": False,
        "sandbox_verified": False,
        "model_context_transport_verified": False,
        "live_pilot_authorized": False,
        "research_gate": "BLOCKED_G2_G3_NO_MODEL_TOKEN_SANDBOX_OR_OFFICIAL_SCORER",
    }
    if len(outcomes) != 36 or sum(counts.values()) != 36:
        raise FrozenContextAuditError("Incomplete fixed-pilot disposition")
    return report


def audit_current_pilot_information_and_tool_parity(root: Path = ROOT) -> dict:
    """New G3 audit of ALL 36 frozen candidate rows: 30 cached IFCs, 6 missing.

    Uses actual independently-rendered D and I source views, NOT scored trials.
    No reference/target/evaluation metadata or source IFC bytes go into report.
    Reports differences instead of asserting full parity from common XML hashes.
    """
    from src.data.bim_edit import AuditError
    from src.imperative_control.agent_runner import API_NOTES
    from src.security.agent_boundary import validate_agent_payload

    selected,audited,remote,pilot=_frozen_inputs(root)
    preflight=pilot_staging_preflight(root)
    if (len(selected)!=36 or len(audited)!=25
            or preflight["input_available_tasks"]!=30
            or preflight["blocked_input_tasks"]!=6
            or preflight["llm_launch_allowed"] is not False):
        raise FrozenContextAuditError("Expected frozen 36/25/30/6 input-denominator gate")
    # Read the exact current draft limits, but DO NOT register or approve them.
    plan=json.loads((root/"configs/pilot_36_plan_v0.json").read_text("utf8"))
    if (plan.get("status")!="DRAFT_CANDIDATE_ONLY_NOT_PREREGISTERED"
            or plan.get("study_protocol_status")!="DRAFT_NOT_FROZEN"
            or plan.get("arms")!=["direct_xml","imperative_python"]
            or plan.get("feedback_mode")!="one_shot"
            or type(plan.get("max_attempts_per_task")) is not int
            or plan["max_attempts_per_task"]!=1
            or plan.get("max_wall_seconds_per_arm_task")!=180
            or plan.get("max_input_tokens_per_attempt")!=20000
            or plan.get("max_output_tokens_per_attempt")!=6000
            or plan.get("actual_provider_spend_authorized") is not False):
        raise FrozenContextAuditError("Unexpected prospective D/I trial plan mutation")
    d_policy=SourceOnlySettings()
    i_policy=ControlConfig()
    if (d_policy.mode!=i_policy.mode
            or d_policy.max_attempts!=i_policy.max_attempts
            or d_policy.max_wall_seconds!=i_policy.max_wall_seconds
            or d_policy.max_edit_bytes!=i_policy.max_output_bytes):
        raise FrozenContextAuditError("Existing D/I attempt/seconds/UTF8 output limits diverged")
    if not API_NOTES.is_file() or API_NOTES.is_symlink():
        raise FrozenContextAuditError("Imperative reference notes changed or disappeared")
    extra_api_note=component(API_NOTES.read_text(encoding="utf8")).as_dict()
    outcomes=[]
    for tid,task in sorted(selected.items()):
        source_path=repo_asset_path(task["input_ifc"])
        audited_source=audited[source_path]
        status=preflight["task_status"][tid]
        base={
            "task_id":tid,
            "source_is_other_task_reference_path":
                audited_source.get("is_cross_task_reference_alias_in_original_324") is True,
        }
        if status!="STAGING_INPUT_AVAILABLE_NO_LAUNCH":
            outcomes.append({
                **base,"status":"BLOCKED_ORIGINAL_INPUT_MISSING_OR_INVALID",
                "shared_source_text_sha256":None,
                "total_common_text_utf8_bytes":None,
            })
            continue
        cached=root/"data/ifc"/source_path
        if cached.is_symlink() or not cached.is_file() or cached.parent.is_symlink():
            outcomes.append({**base,"status":"BLOCKED_CACHE_SYMLINK_OR_ABSENT"})
            continue
        try:
            verify_local_asset_bytes(cached,remote[source_path])
            digest=_digest(cached)
            if digest!=audited_source["byte_sha256_verified"]:
                raise FrozenContextAuditError("Actual input bytes mismatch frozen publisher proof")
            public=validate_agent_payload(agent_view(task))
            with TemporaryDirectory(prefix="g3-pilot-context-parity-") as temp:
                d=stage_source_only_workspace(
                    cached,Path(temp)/"D",public,d_policy
                ).agent_visible_context()
                i_observation=create_matched_observations(cached,public)
                i_view=ImperativeControlSession(i_observation,i_policy).model_visible_context()
                shared=matched_shared_components(d,i_observation,digest)
                if (d.allowed_operations!=ALLOWED_D
                        or i_view.get("allowed_authoring_operations")!=["submit_python_text"]
                        or i_view.get("allowed_execution_operations")!=[]
                        or i_view.get("OS_sandbox_available") is not False
                        or i_view["api_reference_notes"]!=API_NOTES.read_text("utf8")):
                    raise FrozenContextAuditError("Unexpected authoring permissions or I API docs")
                common_text=sum(entry["utf8_bytes"] for entry in shared.values())
                xml=shared["v01_source_xml"]
                if (d.task_id!=i_view["task_id"]
                        or d.instruction!=i_view["instruction"]
                        or sha256(d.xml_text.encode("utf8")).hexdigest()!=xml["sha256"]):
                    raise FrozenContextAuditError("D/I common model-visible context diverged")
                # XML is an incomplete IFC projection for many native entity classes.
                # Common XML bytes do NOT prove D can see/edit everything I can
                # inspect from the original IFC if given Python and the same input.
                outcomes.append({
                    **base,
                    "status":"COMMON_V01_SOURCE_TEXT_MATCHED_UNEQUAL_EXECUTION_AND_API_GUIDANCE",
                    "source_ifc_byte_sha256":digest,
                    "source_ifc_bytes":cached.stat().st_size,
                    "shared_source_text_sha256":xml["sha256"],
                    "shared_source_xml_utf8_bytes":xml["utf8_bytes"],
                    "shared_language_spec_utf8_bytes":shared["v01_schema_spec"]["utf8_bytes"],
                    "shared_instruction_utf8_bytes":shared["public_instruction"]["utf8_bytes"],
                    "total_common_text_utf8_bytes":common_text,
                    "I_only_extra_api_notes_utf8_bytes":extra_api_note["utf8_bytes"],
                    "D_observed_allowed_authoring_actions":list(d.allowed_operations),
                    "I_observed_allowed_authoring_actions":
                        list(i_view["allowed_authoring_operations"]),
                    "I_observed_executable_actions":list(i_view["allowed_execution_operations"]),
                    "D_native_ifc_model_completeness_verified":False,
                    "actual_rendered_provider_prompt_bytes":None,
                    "actual_provider_tokens":None,
                    "both_arms_have_identical_model_visible_documents":False,
                })
        except (AuditError,ValueError,OSError,KeyError,TypeError):
            outcomes.append({**base,"status":"BLOCKED_ACTUAL_SOURCE_OR_V01_PROJECTION"})
    counts=dict(sorted(Counter(row["status"] for row in outcomes).items()))
    audited_rows=counts.get(
        "COMMON_V01_SOURCE_TEXT_MATCHED_UNEQUAL_EXECUTION_AND_API_GUIDANCE",0
    )
    if len(outcomes)!=36 or sum(counts.values())!=36:
        raise FrozenContextAuditError("Failed complete 36-task accounting")
    tested=[row for row in outcomes if row["status"].startswith("COMMON_V01")]
    if tested:
        extra_note_sizes={r["I_only_extra_api_notes_utf8_bytes"] for r in tested}
        if extra_note_sizes!={extra_api_note["utf8_bytes"]}:
            raise FrozenContextAuditError("I-only API note bytes diverged")
    return {
        "version":"pinned-bim-edit-36-current-d-i-information-and-tool-audit-v0.1",
        "source_task_jsonl_sha256":TASK_SHA,
        "frozen_candidate_sha256":SAMPLE_SHA,
        "task_total":36,
        "distinct_original_input_paths":25,
        "cached_input_tasks":30,
        "missing_input_tasks":6,
        "actual_independent_d_and_i_source_text_matches":audited_rows,
        "cached_input_tasks_not_validated":30-audited_rows,
        "status_counts":counts,
        "same_one_shot_attempts_and_180s":True,
        "shared_max_utf8_submission_bytes":d_policy.max_edit_bytes,
        "same_max_output_provider_tokens_configured":plan["max_output_tokens_per_attempt"],
        "same_max_input_provider_tokens_configured":plan["max_input_tokens_per_attempt"],
        "fixed_draft_two_arm_protocol":plan["arms"],
        "new_three_arm_stager_labels":list(preflight["arms"]),
        "three_arm_representation_semantics_preregistered":False,
        "same_source_xml_text_for_verified_pairs":audited_rows>0,
        "I_only_extra_api_notes":extra_api_note,
        "all_model_visible_documents_identical_between_arms":False,
        "same_effective_native_IFC_query_capability_verified":False,
        "same_feedback_and_retries_in_real_runner_verified":False,
        "same_exact_provider_tokens_measured":False,
        "same_model_and_seed_verified":False,
        "actual_model_prompt_transport_verified":False,
        "independent_executable_tool_budget_fairness_verified":False,
        "all_36_original_tasks_eligible_for_live_trial":False,
        "official_benchmark_tasks_scored":0,
        "real_model_provider_called":False,
        "provider_spend_authorized":False,
        "model_launch_allowed":False,
        "gate":"BLOCKED_INFORMATION_AND_TOOL_PARITY_NOT_ESTABLISHED",
        "per_task_source_only_metadata":outcomes,
        "nonclaims":[
            "Common XML/source text equality does not prove source model semantic fidelity or native IFC capability parity",
            "I exposes extra IfcOpenShell API notes; D uses XML file edits, I uses code submission: neither is an identical tool",
            "Three-arm D_FULL/D_MANAGED/I_NATIVE staged labels are not the approved two-arm direct_xml/imperative_python protocol",
            "UTF8 byte limits and configured token ceilings are not actual tokenizer/provider input or output tokens",
            "Six tasks with unavailable original inputs remain in all fixed study denominators",
            "No GT/model-generated code/LLM/provider request or official benchmark evaluator was invoked",
        ],
    }


def main() -> int:
    """Offline current pilot context differential report; never invoke provider."""
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write-current",action="store_true",
                      help="Create a new, non-overwriting 36-task G3 audit JSON")
    mode.add_argument("--check-current",action="store_true",
                      help="Recompute current source views and compare exact stored JSON")
    args=parser.parse_args()
    payload=audit_current_pilot_information_and_tool_parity(ROOT)
    encoded=(json.dumps(payload,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf8")
    destination=ROOT/"reports/g3_bim_edit_36_task_information_and_tool_parity_20261119.json"
    if args.write_current:
        with destination.open("xb") as stream:
            stream.write(encoded)
    elif (not destination.is_file() or destination.is_symlink()
          or destination.read_bytes()!=encoded):
        raise FrozenContextAuditError("Current parity evidence missing or changed")
    print(
        "G3_OFFLINE_PILOT_CONTEXT_DIFFERENTIAL=PASS "
        f"candidate_rows={payload['task_total']} "
        f"source_view_pairs={payload['actual_independent_d_and_i_source_text_matches']} "
        f"blocked_or_unverified={payload['task_total']-payload['actual_independent_d_and_i_source_text_matches']} "
        "tool_parity_verified=false model_calls=0"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
