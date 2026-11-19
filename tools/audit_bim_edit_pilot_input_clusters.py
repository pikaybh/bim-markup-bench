"""Pinned, public-metadata-only BIM-Edit input-IFC pilot-dependence audit.

No IFC, reference IFC, prompt, target GUID, evaluator, network, provider or model
file is opened. An exact input repository *path* is a conservative grouping
key, NOT a verified source IFC SHA or independent real-building family.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re

TASK_SHA256 = "9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83"
TASK_REVISION = "2dc6462bfab145ddf81b43e9954322855b8443dc"
MODEL_REVISION = "0ae510bd21865def4e2c6145c1244f01a1e3bcb9"
ARM_NAMES = ("D_FULL", "D_MANAGED", "I_NATIVE")


class PilotMetadataError(ValueError):
    """Fail closed on source/pilot metadata drift or incomplete remote inventory."""


def _path_only(value: str) -> str:
    if not isinstance(value, str) or "\\" in value or "\x00" in value:
        raise PilotMetadataError("Invalid public input IFC repo path")
    parts = PurePosixPath(value).parts
    if ".." in parts or (parts[0:2] != ("data", "realistic") and parts[0:2] != ("data", "artificial")):
        raise PilotMetadataError("Non-canonical BIM-Edit input path")
    if len(parts) != 3 or not parts[2].endswith(".ifc"):
        raise PilotMetadataError("Unexpected BIM-Edit source path format")
    return ("complex/" if parts[1] == "realistic" else "simple/") + parts[2]


def _load_json_bytes(data: bytes):
    def no_duplicates(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise PilotMetadataError("Duplicate JSON property")
            obj[key] = value
        return obj
    def no_nan(value):
        raise PilotMetadataError("Non-standard JSON numeric constant")
    return json.loads(data, object_pairs_hook=no_duplicates, parse_constant=no_nan)


def build_pilot_source_path_audit(
    tasks_bytes: bytes,
    pilot: dict,
    remote_tree: list[dict],
    revision: dict,
    earlier_remote_audit: dict,
) -> dict:
    if sha256(tasks_bytes).hexdigest() != TASK_SHA256:
        raise PilotMetadataError("Pinned task file SHA256 mismatch: do not silently change cohort")
    if revision.get("task_revision") != TASK_REVISION or revision.get("model_revision") != MODEL_REVISION:
        raise PilotMetadataError("Public source repository version changed")
    if earlier_remote_audit.get("task_jsonl_sha256") != TASK_SHA256:
        raise PilotMetadataError("Earlier remote task provenance changed")
    if pilot.get("status") != "CANDIDATE_NOT_PREREGISTERED":
        raise PilotMetadataError("Unverified pilot cannot be promoted to preregistration")
    if pilot.get("task_revision") != TASK_REVISION or pilot.get("task_data_sha256") != TASK_SHA256:
        raise PilotMetadataError("Pilot source hash/revision mismatch")
    if pilot.get("sample_size") != 36:
        raise PilotMetadataError("Pilot sample size changed")
    tasks = [_load_json_bytes(line) for line in tasks_bytes.splitlines() if line.strip()]
    if len(tasks) != 324:
        raise PilotMetadataError("Not the pinned 324 task corpus")
    by_id: dict[str, dict] = {}
    path_by_task: dict[str, str] = {}
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get("task_id"), str):
            raise PilotMetadataError("Malformed public task")
        task_id = task["task_id"]
        if task_id in by_id:
            raise PilotMetadataError("Duplicate public task ID")
        by_id[task_id] = task
        path_by_task[task_id] = _path_only(task.get("input_ifc"))
    raw_pilot = pilot.get("tasks")
    if not isinstance(raw_pilot, list) or len(raw_pilot) != 36:
        raise PilotMetadataError("Pilot cohort missing or size changed")
    pilot_ids = []
    strata: Counter = Counter()
    for raw in raw_pilot:
        if not isinstance(raw, dict) or set(raw) != {"task_id", "operation", "category", "scene", "entity_type"}:
            raise PilotMetadataError("Pilot public fields changed unexpectedly")
        ident = raw["task_id"]
        if ident not in by_id or ident in pilot_ids:
            raise PilotMetadataError("Pilot task duplicated or outside pinned corpus")
        row = by_id[ident]
        scene = next((tag for tag in row["tags"] if tag in ("scene:A", "scene:R")), None)
        expected = (row["operation"], row["category"], scene, row["target"]["entity_type"])
        actual = (raw["operation"], raw["category"], raw["scene"], raw["entity_type"])
        if expected != actual:
            raise PilotMetadataError("Frozen pilot task strata/class metadata mismatch")
        pilot_ids.append(ident)
        strata[actual[:3]] += 1
    if len(strata) != 18 or set(strata.values()) != {2}:
        raise PilotMetadataError("Original stratified 36 pilot changed")

    files = {}
    if not isinstance(remote_tree, list):
        raise PilotMetadataError("Remote metadata tree not a list")
    for entry in remote_tree:
        if not isinstance(entry, dict) or entry.get("type") != "file":
            continue
        path = entry.get("path")
        if not isinstance(path, str) or path in files:
            raise PilotMetadataError("Malformed or duplicate remote file entry")
        files[path] = entry
    if len(files) != 154:
        raise PilotMetadataError("Pinned remote file metadata inventory changed")
    grouped = defaultdict(list)
    for ident in pilot_ids:
        path = path_by_task[ident]
        if path not in files:
            raise PilotMetadataError("Pinned input source missing from remote inventory")
        meta = files[path]
        if type(meta.get("size")) is not int or meta["size"] <= 0:
            raise PilotMetadataError("Invalid remote IFC size metadata")
        grouped[path].append(ident)

    # ALL task input paths should exist; this says nothing about IFC bytes/rights.
    if any(path not in files for path in path_by_task.values()):
        raise PilotMetadataError("Entire 324 task input mapping is not covered")
    groups = []
    for path, ids in sorted(grouped.items()):
        meta = files[path]
        # Never substitute a Git OID or a SHA of its path for IFC content SHA256.
        lfs = meta.get("lfs")
        exposed_content_sha = (
            lfs.get("oid")
            if isinstance(lfs, dict) and re.fullmatch("[0-9a-f]{64}", str(lfs.get("oid", "")))
            else None
        )
        groups.append({
            "public_input_path": path,
            "path_group_key_sha256": sha256(path.encode("utf-8")).hexdigest(),
            "task_count": len(ids),
            "public_task_ids": sorted(ids),
            "remote_file_size_metadata_bytes": meta["size"],
            "remote_lfs_sha256_pointer_unverified": exposed_content_sha,
            "content_hash_verified_from_downloaded_ifc": False,
        })
    group_sizes = Counter(len(g["public_task_ids"]) for g in groups)
    return {
        "status": "METADATA_ONLY_NOT_INDEPENDENT_SOURCE_FAMILIES_OR_SCORER_VALIDATION",
        "task_revision": TASK_REVISION,
        "model_revision": MODEL_REVISION,
        "task_jsonl_sha256": TASK_SHA256,
        "pilot_status_unchanged": pilot["status"],
        "all_task_rows": len(tasks),
        "all_unique_exact_input_paths": len(set(path_by_task.values())),
        "pilot_task_rows": len(pilot_ids),
        "pilot_unique_exact_input_paths": len(groups),
        "pilot_repeated_input_task_rows": sum(g["task_count"] - 1 for g in groups),
        "largest_single_input_path_task_count": max(g["task_count"] for g in groups),
        "group_multiplicity_distribution": {str(key): group_sizes[key] for key in sorted(group_sizes)},
        "remote_total_metadata_bytes_of_distinct_pilot_inputs": sum(g["remote_file_size_metadata_bytes"] for g in groups),
        "groups": groups,
        "nonclaims": [
            "Equal input IFC repo paths imply shared input asset metadata but different paths may still be the same original building",
            "25 path groups is an upper bound on independently distinct pilot source families, not certified 25 independent source SHA clusters",
            "Git object IDs, path hashes, and unverified LFS pointer digests are NOT independently computed local IFC SHA256",
            "No IFC bytes, GT IFCs, target GUIDs, original scorer, model run, licensed-data acceptance, or independent blind certification",
            "Original pilot cohort unchanged; no release, provider, owner, data-rights or preregistration approval",
        ],
    }


def run_audit(root: Path) -> dict:
    tasks = (root / "data/tasks.jsonl").read_bytes()
    pilot_bytes = (root / "manifests/pilot_36_candidate_v0.json").read_bytes()
    tree_bytes = (root / "data/bim_edit_remote_tree.json").read_bytes()
    revision_bytes = (root / "manifests/bim_edit_revision.json").read_bytes()
    older_bytes = (root / "data/bim_edit_remote_audit.json").read_bytes()
    report = build_pilot_source_path_audit(
        tasks, _load_json_bytes(pilot_bytes), _load_json_bytes(tree_bytes),
        _load_json_bytes(revision_bytes), _load_json_bytes(older_bytes)
    )
    report["input_metadata_sha256"] = {
        "pilot_manifest": sha256(pilot_bytes).hexdigest(),
        "remote_tree": sha256(tree_bytes).hexdigest(),
        "revision_manifest": sha256(revision_bytes).hexdigest(),
        "older_remote_audit": sha256(older_bytes).hexdigest(),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.check == args.write:
        parser.error("Exactly one of --check or --write is required")
    root = Path(__file__).resolve().parents[1]
    report = run_audit(root)
    raw = (json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    output = root / "reports/bim_edit_pilot_source_path_independence_20261119.json"
    if args.write:
        with output.open("xb") as f:
            f.write(raw)
    elif not output.exists() or output.read_bytes() != raw:
        raise PilotMetadataError("Missing/mismatched frozen metadata-only report")
    print(
        f"BIM_EDIT_METADATA_PATH_AUDIT=PASS pilot_tasks={report['pilot_task_rows']} "
        f"unique_input_paths={report['pilot_unique_exact_input_paths']} "
        f"largest_reuse={report['largest_single_input_path_task_count']} "
        "original_IFC_bytes_read=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
