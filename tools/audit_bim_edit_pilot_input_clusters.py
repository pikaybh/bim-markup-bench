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


def _potential_family_label(path: str) -> str:
    """A filename-prefix *review clue*, NEVER a certified source/building identity."""
    match = re.fullmatch(r"(simple/task[0-9]{3})-(?:create|delete|update)-[^/]+[.]ifc", path)
    if match:
        return match.group(1)
    match = re.fullmatch(r"(complex/[0-9a-f]{12})-(?:create|delete|update|input|gt)[^/]*[.]ifc", path)
    if match:
        return match.group(1)
    return path


def build_lineage_review_queue(
    report: dict, remote_tree: list[dict], rights_ledger: dict
) -> dict:
    """Produce PUBLIC-METADATA-only questions for a future *external* source steward.

    No IFC bytes are read, no per-file approvals synthesized and no verified
    source_ifc_sha256 derived from Git/LFS/path identifiers.
    """
    if report.get("status") != "METADATA_ONLY_NOT_INDEPENDENT_SOURCE_FAMILIES_OR_SCORER_VALIDATION":
        raise PilotMetadataError("Not an approved pinned source-path audit input")
    groups = report.get("groups")
    if not isinstance(groups, list) or len(groups) != 25:
        raise PilotMetadataError("Fixed pilot exact input-path groups changed")
    rights = rights_ledger.get("records", [])
    source_rights = [r for r in rights if r.get("source") == "BIM-Edit/BIM-Edit"]
    if len(source_rights) != 1:
        raise PilotMetadataError("No unambiguous original asset rights source record")
    source = source_rights[0]
    if source.get("rights_checked") is not False or source.get("redistribution_permitted") is not False or source.get("consent_documented") is not False:
        raise PilotMetadataError("Existing frozen unverified rights contract changed: require new review version")
    if source.get("source_revision") != MODEL_REVISION:
        raise PilotMetadataError("Original asset-rights revision changed")
    paths = [g["public_input_path"] for g in groups]
    if len(set(paths)) != len(paths):
        raise PilotMetadataError("Duplicate exact input-path group")
    remote_files = {row.get("path"): row for row in remote_tree if row.get("type") == "file"}
    if len(remote_files) != 154:
        raise PilotMetadataError("Remote file inventory not the original pinned 154-file tree")
    by_label = defaultdict(list)
    pointers = []
    git_oids = []
    for g in groups:
        path = g["public_input_path"]
        remote = remote_files.get(path)
        if remote is None or remote.get("size") != g.get("remote_file_size_metadata_bytes"):
            raise PilotMetadataError("Unpinned remote source size/path")
        oid = remote.get("oid")
        if not isinstance(oid, str) or not re.fullmatch(r"[0-9a-f]{40}", oid):
            raise PilotMetadataError("Invalid public Git object identifier")
        git_oids.append(oid)
        lfs = remote.get("lfs")
        pointer = None
        if lfs is not None:
            if not isinstance(lfs, dict) or not re.fullmatch(
                r"[0-9a-f]{64}", str(lfs.get("oid", ""))
            ):
                raise PilotMetadataError("Malformed LFS SHA256 pointer")
            pointer = lfs["oid"]
            if pointer != g.get("remote_lfs_sha256_pointer_unverified"):
                raise PilotMetadataError("LFS pointer differs from previous frozen source-path report")
            pointers.append(pointer)
        elif g.get("remote_lfs_sha256_pointer_unverified") is not None:
            raise PilotMetadataError("Unrecognized LFS pointer disappeared")
        by_label[_potential_family_label(path)].append(path)
    if len(set(git_oids)) != len(git_oids):
        raise PilotMetadataError("Distinct input paths share a Git object ID: require fresh dedicated audit")
    if len(set(pointers)) != len(pointers):
        raise PilotMetadataError("Distinct input paths share a claimed LFS content SHA: review before continuing")

    candidate_pairs = []
    for label, paths_of_label in sorted(by_label.items()):
        if len(paths_of_label) > 1:
            candidate_pairs.append({
                "filename_stem_clue": label,
                "public_input_paths_needing_independent_lineage_review": sorted(paths_of_label),
                "interpretation": "UNVERIFIED_FILENAME_HEURISTIC_NOT_CONFIRMED_COMMON_SOURCE",
            })
    review_queue = sorted(
        ({
            "public_input_path": g["public_input_path"],
            "public_task_ids": g["public_task_ids"],
            "task_count": g["task_count"],
            "remote_metadata_size_bytes": g["remote_file_size_metadata_bytes"],
            "public_git_oid_sha1_unverified_for_ifc_content": remote_files[g["public_input_path"]]["oid"],
            "lfs_sha256_pointer_not_byte_verified": g["remote_lfs_sha256_pointer_unverified"],
            "potential_filename_family_label_not_certified": _potential_family_label(g["public_input_path"]),
            "verified_original_ifc_sha256": None,
            "verified_original_building_lineage": None,
            "per_file_rights_verified": False,
            "explicit_provider_transfer_retention_approved": False,
            "recommended_review_priority": (
                "cross_path_stem_match"
                if len(by_label[_potential_family_label(g["public_input_path"])]) > 1
                else "reused_exact_input_path"
                if g["task_count"] > 1
                else "single_pilot_task"
            ),
        } for g in groups),
        key=lambda g: (
            {"cross_path_stem_match": 0, "reused_exact_input_path": 1, "single_pilot_task": 2}[g["recommended_review_priority"]],
            -g["task_count"],
            g["public_input_path"],
        ),
    )
    return {
        "verdict": "EXTERNAL_REVIEW_QUEUE_ONLY_ALL_DATA_RIGHTS_AND_SOURCE_LINEAGE_BLOCKED",
        "pinned_36_pilot_task_count": report["pilot_task_rows"],
        "exact_input_paths": len(groups),
        "public_git_sha1_oid_count": len(git_oids),
        "distinct_public_git_sha1_oids": len(set(git_oids)),
        "unverified_lfs_sha256_pointer_count": len(pointers),
        "distinct_unverified_lfs_sha256_pointers": len(set(pointers)),
        "filenames_suggesting_cross_path_lineage_review": candidate_pairs,
        "filename_clue_group_count_not_independent_sources": len(by_label),
        "source_ifc_content_sha256_independently_verified": 0,
        "source_building_lineages_independently_verified": 0,
        "per_original_ifc_rights_verified": 0,
        "trial_launch_authorized": False,
        "external_steward_questions": [
            "Are two different IFC paths variants of the same underlying building or project?",
            "Which verified original IFC content SHA256 matches each public pinned file?",
            "Who can verify creator consent, embedded third-party content and per-file attribution?",
            "Is a named provider permitted to receive and retain/delete the specific IFC under its stated terms?",
            "Can a separately access-controlled reviewer seal source lineage and hidden reference scoring without developer exposure?",
        ],
        "review_queue": review_queue,
        "nonclaims": [
            "Git SHA1 OIDs are publisher source-tree metadata, not hashes checked against local IFC bytes",
            "Only 6 LFS SHA256 pointers in this pilot, and none were verified against downloaded bytes",
            "A filename stem is not proof of source lineage: 23 clue-groups are NOT 23 independent buildings",
            "No unseen source/blind cohort, dataset rights, official scorer release or external provider authorization certified",
            "No original IFC, reference IFC, private grader, task prompt or target GUID opened by this review",
        ],
    }


def run_lineage_review(root: Path) -> dict:
    original = run_audit(root)
    remote_bytes = (root / "data/bim_edit_remote_tree.json").read_bytes()
    rights_bytes = (root / "manifests/source_rights.json").read_bytes()
    report = build_lineage_review_queue(
        original, _load_json_bytes(remote_bytes), _load_json_bytes(rights_bytes)
    )
    report["pinned_input_sha256"] = {
        "original_source_path_report": sha256(
            (root / "reports/bim_edit_pilot_source_path_independence_20261119.json").read_bytes()
        ).hexdigest(),
        "public_remote_tree": sha256(remote_bytes).hexdigest(),
        "existing_rights_ledger": sha256(rights_bytes).hexdigest(),
    }
    if report["pinned_input_sha256"]["original_source_path_report"] != (
        "6511d1f3783b9f031bd80060ce3e751730839683a9f2a7cc1ce2bd9f95ca9d01"
    ):
        raise PilotMetadataError("Frozen prior report hash changed")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--write-review", action="store_true")
    parser.add_argument("--check-review", action="store_true")
    args = parser.parse_args()
    if sum((args.check, args.write, args.write_review, args.check_review)) != 1:
        parser.error("Exactly one of --check, --write, --check-review, --write-review is required")
    root = Path(__file__).resolve().parents[1]
    if args.check_review or args.write_review:
        report = run_lineage_review(root)
        raw = (json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        output = root / "reports/bim_edit_pilot_lineage_review_queue_20261119.json"
        if args.write_review:
            with output.open("xb") as f:
                f.write(raw)
        elif not output.exists() or output.read_bytes() != raw:
            raise PilotMetadataError("Missing/mismatched immutable external-review queue")
        print(
            f"BIM_EDIT_LINEAGE_REVIEW=PASS exact_paths={report['exact_input_paths']} "
            f"filename_clue_groups={report['filename_clue_group_count_not_independent_sources']} "
            "rights_verified=0 original_IFC_bytes_read=0"
        )
        return 0
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
