"""Fail-closed OFFLINE staging of one already-cached, pinned BIM-Edit pilot INPUT.

This only creates an isolated *file surface*, not an OS/container sandbox.
Never launches a model, compiler, Python task code or evaluator. Never touches
a task's ground-truth path, other benchmark inputs, or private grader files.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import argparse
import tempfile
import os
from pathlib import Path
import re

from src.data.bim_edit import (
    TASK_SHA256, TASK_REV, MODEL_REV, AuditError,
    agent_view, read_tasks, repo_asset_path, verify_local_asset_bytes,
)
from src.security.agent_boundary import validate_agent_payload
from tools.audit_bim_edit_pilot_cached_input_bytes import (
    CachedInputIdentityBlocked, _pinned_json, MAX_SINGLE_IFC_BYTES,
)

PILOT_PATH = "manifests/pilot_36_candidate_v0.json"
PILOT_SHA256 = "75b4847814dbefad95340556c0b62f9cda72cac319cd82ecb23ea4933c9ab694"
HASH_REPORT = "reports/bim_edit_pilot_existing_cached_input_SHA256_20261119.json"
HASH_REPORT_SHA256 = "99669d6ae1e006ad9d93039cc42c1ed5d7b460e73982399972285e37cf3dbd10"
PUBLIC_TREE = "data/bim_edit_remote_tree.json"
PUBLIC_TREE_SHA256 = "f1b150a576f3d72045819768215c34fd84602ab4f6a5f4d2f0202a0ae3a92a39"
ARMS = ("D_FULL", "D_MANAGED", "I_NATIVE")
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{1,80}\Z")


class PilotStageBlocked(ValueError):
    """No silent sample change, original-byte change, unsafe input, or launch."""


@dataclass(frozen=True)
class OfflineStage:
    task_id: str
    arm: str
    workspace: Path
    source_byte_sha256: str
    bytes_copied: int
    agent_payload: dict
    model_launch_allowed: bool = False
    os_sandbox_established: bool = False


def _frozen_inputs(root: Path) -> tuple[dict, dict, dict, dict]:
    if not root.is_dir() or root.is_symlink():
        raise PilotStageBlocked("Invalid repository root")
    try:
        pilot = _pinned_json(root, PILOT_PATH, PILOT_SHA256)
        report = _pinned_json(root, HASH_REPORT, HASH_REPORT_SHA256)
        tree = _pinned_json(root, PUBLIC_TREE, PUBLIC_TREE_SHA256)
        tasks = read_tasks(root / "data/tasks.jsonl")
    except (CachedInputIdentityBlocked, AuditError, ValueError, OSError) as exc:
        raise PilotStageBlocked("Frozen pilot provenance was not satisfied") from exc
    if (pilot.get("status") != "CANDIDATE_NOT_PREREGISTERED"
            or pilot.get("sample_size") != 36
            or pilot.get("task_revision") != TASK_REV
            or pilot.get("task_data_sha256") != TASK_SHA256
            or report.get("status") != "PARTIAL_LOCAL_INPUT_BYTE_IDENTITY_VERIFIED_NOT_SCIENTIFIC_LAUNCH"
            or report.get("pinned_task_sha256") != TASK_SHA256
            or report.get("pinned_model_revision") != MODEL_REV
            or report.get("model_launch_allowed") is not False
            or report.get("original_pilot_tasks") != 36
            or len(report.get("rows", [])) != 25):
        raise PilotStageBlocked("Invalid/unregistered frozen pilot or corrupted input audit")
    by_id = {r["task_id"]: r for r in tasks}
    if len(by_id) != 324:
        raise PilotStageBlocked("Missing/duplicate original task records")
    selection = pilot.get("tasks")
    if not isinstance(selection, list) or len(selection) != 36:
        raise PilotStageBlocked("Invalid fixed pilot sample")
    selected = {}
    for row in selection:
        tid = row.get("task_id")
        if tid not in by_id or tid in selected or not SAFE_ID.fullmatch(tid):
            raise PilotStageBlocked("Invalid/duplicated fixed pilot ID")
        task = by_id[tid]
        expected = {k: task[k] for k in ("operation", "category")}
        if any(row.get(k) != v for k, v in expected.items()):
            raise PilotStageBlocked("Tampered fixed pilot strata")
        selected[tid] = task
    audited = {}
    for entry in report["rows"]:
        path = entry.get("public_input_path")
        if path in audited or not isinstance(path, str):
            raise PilotStageBlocked("Duplicated original input asset mapping")
        audited[path] = entry
    if (sum(r.get("task_count", 0) for r in audited.values()) != 36
            or set(selected) != {tid for entry in audited.values() for tid in entry["public_task_ids"]}):
        raise PilotStageBlocked("36/25 original input mapping changed")
    for tid, task in selected.items():
        path = repo_asset_path(task["input_ifc"])
        if path not in audited or tid not in audited[path]["public_task_ids"]:
            raise PilotStageBlocked("Task source mismatched frozen original input audit")
    publisher_files = {r["path"]: r for r in tree if r.get("type") == "file"}
    if len(publisher_files) != 154:
        raise PilotStageBlocked("Original publisher tree changed")
    return selected, audited, publisher_files, pilot


def pilot_staging_preflight(root: Path) -> dict:
    """List *all* 36 task statuses; never quietly select the 30 available."""
    selected, audited, _, _ = _frozen_inputs(root)
    statuses = {}
    for task_id, row in sorted(selected.items()):
        asset = audited[repo_asset_path(row["input_ifc"])]
        try:
            validate_agent_payload(agent_view(row))
        except (AuditError, ValueError, TypeError):
            statuses[task_id] = "BLOCKED_UNSAFE_AGENT_PAYLOAD"
            continue
        statuses[task_id] = (
            "STAGING_INPUT_AVAILABLE_NO_LAUNCH"
            if asset["status"] == "PUBLISHER_OBJECT_AND_LOCAL_SHA256_VERIFIED"
            else "BLOCKED_ORIGINAL_INPUT_ABSENT"
        )
    available = sum(s == "STAGING_INPUT_AVAILABLE_NO_LAUNCH" for s in statuses.values())
    return {
        "status": "OFFLINE_INPUT_PREPARATION_ONLY_NOT_TRIAL_READY",
        "original_tasks": 36,
        "input_available_tasks": available,
        "blocked_input_tasks": 36 - available,
        "arms": list(ARMS),
        "pilot_candidate_not_preregistered": True,
        "source_rights_verified_for_external_provider": False,
        "os_level_agent_isolation_verified": False,
        "llm_launch_allowed": False,
        "task_status": statuses,
    }


def _check_scratch_root(root: Path, scratch: Path) -> Path:
    if not scratch.is_absolute() or not scratch.is_dir() or scratch.is_symlink():
        raise PilotStageBlocked("Scratch must be a real, already-existing absolute directory")
    real = scratch.resolve(strict=True)
    repo = root.resolve(strict=True)
    if real == repo or real.is_relative_to(repo) or repo.is_relative_to(real):
        raise PilotStageBlocked("Scratch must be neither inside the repo nor an ancestor of it")
    # Prevent task contents from landing in a symlinked scratch parent.
    current = scratch
    while current != current.parent:
        if current.is_symlink():
            raise PilotStageBlocked("Scratch path includes a symlink")
        current = current.parent
    return real


def stage_verified_pilot_input(root: Path, scratch: Path, task_id: str, arm: str) -> OfflineStage:
    """Copy only a *preverified* original IFC input and a sanitized instruction.

    The caller must mount ONLY the returned workspace as the agent's
    filesystem inside a separately secured process/container. No API
    calls or filesystem/process isolation are provided here.
    """
    if arm not in ARMS or not isinstance(task_id, str) or not SAFE_ID.fullmatch(task_id):
        raise PilotStageBlocked("Invalid original task or experimental arm")
    selected, audited, publisher_files, _ = _frozen_inputs(root)
    if task_id not in selected:
        raise PilotStageBlocked("Requested task is not in the unmodified 36-task pilot")
    task = selected[task_id]
    path = repo_asset_path(task["input_ifc"])
    record = audited[path]
    if record.get("status") != "PUBLISHER_OBJECT_AND_LOCAL_SHA256_VERIFIED":
        raise PilotStageBlocked("Original pinned IFC input missing or unverified; never reduce ITT sample")
    expected_sha = record.get("byte_sha256_verified")
    if not isinstance(expected_sha, str) or not re.fullmatch("[0-9a-f]{64}", expected_sha):
        raise PilotStageBlocked("Invalid actual original source content SHA256")
    if (root / "data").is_symlink() or (root / "data/ifc").is_symlink():
        raise PilotStageBlocked("Source dataset root may not be symlinked elsewhere")
    asset_root = (root / "data/ifc").resolve(strict=True)
    if not asset_root.is_relative_to(root.resolve(strict=True)):
        raise PilotStageBlocked("Source dataset root escaped original repository")
    source = asset_root / path
    if (source.is_symlink() or source.parent.is_symlink()
            or not source.is_file() or not source.resolve(strict=True).is_relative_to(asset_root)):
        raise PilotStageBlocked("Source is a symlink, inaccessible or outside original asset root")
    if (source.stat().st_size > MAX_SINGLE_IFC_BYTES
            or source.stat().st_size != record.get("expected_source_bytes")):
        raise PilotStageBlocked("Source exceeds original pinned size or staging budget")
    try:
        identity = verify_local_asset_bytes(source, publisher_files[path])
    except (AuditError, OSError, ValueError) as exc:
        raise PilotStageBlocked("Source no longer matches its publisher object") from exc
    if not (identity.get("git_blob_sha1_verified") or identity.get("content_sha256_verified")):
        raise PilotStageBlocked("Publisher content identity was not proven")

    try:
        payload = validate_agent_payload(agent_view(task))
    except (AuditError, ValueError, TypeError) as exc:
        raise PilotStageBlocked("Unsafe agent-facing task payload") from exc
    scratch = _check_scratch_root(root, scratch)
    stage = scratch / (task_id + "--" + arm)
    if stage.is_symlink() or stage.exists():
        raise PilotStageBlocked("Never reuse or overwrite an existing task-arm workspace")
    try:
        stage.mkdir(mode=0o700)
    except (FileExistsError, OSError) as exc:
        raise PilotStageBlocked("Cannot create a fresh exclusive task-arm workspace") from exc
    try:
        destination = stage / "input.ifc"
        copied = 0
        digest = sha256()
        with source.open("rb") as src, destination.open("xb") as dst:
            for chunk in iter(lambda: src.read(1024 * 1024), b""):
                copied += len(chunk)
                if copied > MAX_SINGLE_IFC_BYTES:
                    raise PilotStageBlocked("Input unexpectedly grew during staging")
                digest.update(chunk)
                dst.write(chunk)
            dst.flush()
            os.fsync(dst.fileno())
        if digest.hexdigest() != expected_sha or copied != record["expected_source_bytes"]:
            raise PilotStageBlocked("Source identity changed between audit and staging")
        destination.chmod(0o444)
        with (stage / "task.json").open("x", encoding="utf-8", newline="\n") as out:
            json.dump(payload, out, sort_keys=True, ensure_ascii=False)
            out.write("\n")
        if {p.name for p in stage.iterdir()} != {"input.ifc", "task.json"}:
            raise PilotStageBlocked("Unexpected file in the staged task workspace")
        if sha256(destination.read_bytes()).hexdigest() != expected_sha:
            raise PilotStageBlocked("Staged original input was corrupted")
    except Exception:
        for path_out in (stage / "task.json", stage / "input.ifc"):
            if path_out.is_file() and not path_out.is_symlink():
                path_out.chmod(0o600)
                path_out.unlink()
        try:
            stage.rmdir()
        except OSError:
            pass
        raise
    return OfflineStage(
        task_id=task_id, arm=arm, workspace=stage,
        source_byte_sha256=expected_sha, bytes_copied=copied, agent_payload=payload,
    )


def main() -> int:
    """Repeatable offline source-surface diagnostic, NEVER a trial runner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify 36 task statuses; do not copy IFC")
    parser.add_argument(
        "--smoke-stage", action="store_true",
        help="Stage one already-cached input for all 3 arms in disposable local temp; no model",
    )
    args = parser.parse_args()
    if args.check == args.smoke_stage:
        parser.error("Choose exactly one of --check or --smoke-stage")
    root = Path(__file__).resolve().parents[2]
    result = pilot_staging_preflight(root)
    if args.smoke_stage:
        sample = next(
            (tid for tid, status in result["task_status"].items()
             if status == "STAGING_INPUT_AVAILABLE_NO_LAUNCH"), None
        )
        if sample is None:
            raise PilotStageBlocked("No locally verified source for bounded staging smoke test")
        with tempfile.TemporaryDirectory(prefix="bim-pilot-input-only-") as temp:
            records = [
                stage_verified_pilot_input(root, Path(temp), sample, arm)
                for arm in ARMS
            ]
            if (len({x.source_byte_sha256 for x in records}) != 1
                    or len({json.dumps(x.agent_payload, sort_keys=True) for x in records}) != 1
                    or any(
                        {f.name for f in x.workspace.iterdir()} != {"input.ifc", "task.json"}
                        for x in records
                    )):
                raise PilotStageBlocked("Staged arms leaked or mismatched their original input surface")
        print(
            "BIM_EDIT_OFFLINE_STAGE=PASS paired_arms=3 "
            "identical_pinned_input_and_prompt=true "
            "workspace_files=input.ifc,task.json "
            "temp_cleaned=true model_calls=0 os_sandbox_proven=false"
        )
    else:
        print(
            "BIM_EDIT_PILOT_STAGING_PREFLIGHT=PASS "
            f"original_tasks={result['original_tasks']} "
            f"input_available={result['input_available_tasks']} "
            f"blocked={result['blocked_input_tasks']} "
            "model_launch_allowed=false"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
