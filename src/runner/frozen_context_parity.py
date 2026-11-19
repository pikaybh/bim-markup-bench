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

from src.data.bim_edit import read_tasks, repo_asset_path, verify_local_asset_bytes
from src.data.pilot_asset_audit import _files_in_root
from src.direct_markup.agent_runner import SourceOnlySettings, stage_source_only_workspace
from src.imperative_control.agent_runner import (
    ControlConfig, ImperativeControlSession, create_matched_observations,
)
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
