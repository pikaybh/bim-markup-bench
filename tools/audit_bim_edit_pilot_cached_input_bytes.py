"""Offline hash-check *already cached* public BIM-Edit pilot INPUT IFC bytes.

G0 integrity evidence only. Never opens GT, scorer, prompt or native IFC model,
never downloads data, and never certifies independent buildings or rights.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re

from src.data.bim_edit import AuditError, verify_local_asset_bytes
from tools.audit_bim_edit_pilot_input_clusters import (
    PilotMetadataError, TASK_SHA256, _load_json_bytes, _path_only, run_lineage_review
)

SOURCE_PATH_REPORT = "reports/bim_edit_pilot_source_path_independence_20261119.json"
SOURCE_PATH_REPORT_SHA256 = "6511d1f3783b9f031bd80060ce3e751730839683a9f2a7cc1ce2bd9f95ca9d01"
REVIEW_QUEUE = "reports/bim_edit_pilot_lineage_review_queue_20261119.json"
REVIEW_QUEUE_SHA256 = "35273b3951882ceae197912ee66b85404f82ef14af050425902c7c0197924216"
RIGHTS_LEDGER = "manifests/source_rights.json"
RIGHTS_LEDGER_SHA256 = "43f85c4ebf17184bfaea3fa749b565337e34f4fd397ec1b9536a8f242b2add06"
MAX_SINGLE_IFC_BYTES = 50_000_000
MAX_TOTAL_IFC_BYTES = 100_000_000
INPUT_RE = re.compile(r"(simple|complex)/[A-Za-z0-9_.-]+[.]ifc\Z")


class CachedInputIdentityBlocked(ValueError):
    """Unverified or altered cached input, rights or frozen cohort evidence."""


def _pinned_json(root: Path, relative: str, expected_sha256: str):
    file = root / relative
    if file.is_symlink() or not file.is_file():
        raise CachedInputIdentityBlocked(f"Missing/linked pinned evidence: {relative}")
    raw = file.read_bytes()
    if sha256(raw).hexdigest() != expected_sha256:
        raise CachedInputIdentityBlocked(f"Frozen evidence SHA256 drift: {relative}")
    return _load_json_bytes(raw)


def _sha256_stream(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_one_cached_input(
    asset_root: Path, relative: str, publisher_entry: dict
) -> dict:
    """Validate source-only bytes against original remote Git/LFS object metadata.

    Testable using a self-authored tiny byte fixture with an independently
    computed Git blob OID/LFS SHA, never requiring original IFC extraction.
    """
    if not isinstance(relative, str) or not INPUT_RE.fullmatch(relative):
        raise CachedInputIdentityBlocked("Only pinned source *input* paths allowed")
    if not asset_root.is_absolute() or asset_root.is_symlink() or not asset_root.is_dir():
        raise CachedInputIdentityBlocked("Invalid sandbox asset root")
    path = asset_root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(asset_root.resolve()):
        raise CachedInputIdentityBlocked("Symlink or escaped IFC input path forbidden")
    if not path.exists():
        return {
            "status": "MISSING_LOCAL_PINNED_INPUT",
            "byte_sha256_verified": None,
            "verification_method": None,
        }
    if not path.is_file():
        raise CachedInputIdentityBlocked("Existing input source is not a file")
    size = path.stat().st_size
    if type(publisher_entry.get("size")) is not int or publisher_entry["size"] <= 0:
        raise CachedInputIdentityBlocked("Invalid pinned publisher byte count")
    if size != publisher_entry["size"]:
        raise CachedInputIdentityBlocked("Cached original IFC size disagrees with pinned publisher metadata")
    if size > MAX_SINGLE_IFC_BYTES:
        return {
            "status": "BLOCKED_PRESENT_EXCEEDS_PREAPPROVED_HASH_LIMIT",
            "byte_sha256_verified": None,
            "verification_method": None,
        }

    before = path.stat()
    try:
        verified = verify_local_asset_bytes(path, publisher_entry)
    except (AuditError, OSError, ValueError) as exc:
        raise CachedInputIdentityBlocked("Local IFC content did not match publisher Git/LFS object") from exc
    digest = _sha256_stream(path)
    after = path.stat()
    if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        raise CachedInputIdentityBlocked("Cached source changed during verification")
    is_lfs = verified["content_sha256_verified"] is True
    if is_lfs and publisher_entry["lfs"]["oid"] != digest:
        raise CachedInputIdentityBlocked("LFS SHA256 pointer mismatch after second read")
    return {
        "status": "PUBLISHER_OBJECT_AND_LOCAL_SHA256_VERIFIED",
        "byte_sha256_verified": digest,
        "verification_method": "publisher_lfs_sha256_and_local_sha256" if is_lfs
            else "publisher_git_blob_sha1_and_local_sha256",
    }


def _cross_task_reference_aliases(root: Path, groups: list[dict]) -> dict:
    """Inspect ONLY task-record path strings; NEVER dereference a GT file.

    A benchmark input for task A may be the reference file for task B, so
    blanket statements that no reference-labelled BYTES were hashed would
    be wrong. Make this cross-task overlap explicit before any trial.
    """
    task_bytes = (root / "data/tasks.jsonl").read_bytes()
    if sha256(task_bytes).hexdigest() != TASK_SHA256:
        raise CachedInputIdentityBlocked("Pinned public task JSONL changed during alias audit")
    tasks = [_load_json_bytes(line) for line in task_bytes.splitlines() if line.strip()]
    if len(tasks) != 324:
        raise CachedInputIdentityBlocked("Expected pinned full 324 public task records")
    by_id = {row["task_id"]: row for row in tasks}
    if len(by_id) != len(tasks):
        raise CachedInputIdentityBlocked("Duplicate task identity in pinned public corpus")
    pilot_ids = [tid for group in groups for tid in group["public_task_ids"]]
    if len(pilot_ids) != 36 or len(set(pilot_ids)) != 36:
        raise CachedInputIdentityBlocked("Pilot task-to-input mapping has changed")
    pilot_tasks = []
    for group in groups:
        for tid in group["public_task_ids"]:
            row = by_id.get(tid)
            if row is None or _path_only(row["input_ifc"]) != group["public_input_path"]:
                raise CachedInputIdentityBlocked("Task source path no longer matches original cohort")
            pilot_tasks.append(row)
    all_reference_paths = {_path_only(row["ground_truth_ifc"]) for row in tasks}
    pilot_reference_paths = {_path_only(row["ground_truth_ifc"]) for row in pilot_tasks}
    overlapping_any = {
        group["public_input_path"] for group in groups
        if group["public_input_path"] in all_reference_paths
    }
    overlapping_pilot = {
        group["public_input_path"] for group in groups
        if group["public_input_path"] in pilot_reference_paths
    }
    return {
        "source_paths_also_reference_paths_for_other_tasks_full324": len(overlapping_any),
        "pilot_task_rows_using_cross_task_reference_paths_full324": sum(
            _path_only(task["input_ifc"]) in overlapping_any for task in pilot_tasks
        ),
        "source_paths_also_reference_paths_for_pilot_tasks": len(overlapping_pilot),
        "pilot_task_rows_using_reference_paths_of_other_pilot_tasks": sum(
            _path_only(task["input_ifc"]) in overlapping_pilot for task in pilot_tasks
        ),
        "same_task_source_equals_reference_path": sum(
            _path_only(task["input_ifc"]) == _path_only(task["ground_truth_ifc"])
            for task in pilot_tasks
        ),
        "overlap_source_paths": overlapping_any,
    }


def run_cached_input_audit(root: Path) -> dict:
    """Only paths referenced by the EXISTING frozen 36-task input list."""
    root = root.resolve()
    earlier = _pinned_json(root, SOURCE_PATH_REPORT, SOURCE_PATH_REPORT_SHA256)
    review = _pinned_json(root, REVIEW_QUEUE, REVIEW_QUEUE_SHA256)
    rights = _pinned_json(root, RIGHTS_LEDGER, RIGHTS_LEDGER_SHA256)
    if earlier.get("status") != "METADATA_ONLY_NOT_INDEPENDENT_SOURCE_FAMILIES_OR_SCORER_VALIDATION":
        raise CachedInputIdentityBlocked("Source-path provenance unexpectedly promoted")
    if review.get("verdict") != "EXTERNAL_REVIEW_QUEUE_ONLY_ALL_DATA_RIGHTS_AND_SOURCE_LINEAGE_BLOCKED":
        raise CachedInputIdentityBlocked("Review queue provenance unexpectedly promoted")
    if review != run_lineage_review(root):
        raise CachedInputIdentityBlocked("Source-lineage metadata replay differed from frozen review report")
    rights_rows = [x for x in rights["records"] if x.get("source") == "BIM-Edit/BIM-Edit"]
    if len(rights_rows) != 1 or rights_rows[0]["rights_checked"] is not False:
        raise CachedInputIdentityBlocked("Unauthorized rights promotion")
    if rights_rows[0]["redistribution_permitted"] is not False:
        raise CachedInputIdentityBlocked("Unauthorized external IFC transfer promoted")
    groups = earlier["groups"]
    if len(groups) != 25 or len({row["public_input_path"] for row in groups}) != 25:
        raise CachedInputIdentityBlocked("Expected exactly original 25 source paths")

    remote_bytes = (root / "data/bim_edit_remote_tree.json").read_bytes()
    if sha256(remote_bytes).hexdigest() != review["pinned_input_sha256"]["public_remote_tree"]:
        raise CachedInputIdentityBlocked("Pinned remote IFC tree metadata changed")
    remote_tree = _load_json_bytes(remote_bytes)
    remote = {row["path"]: row for row in remote_tree if row.get("type") == "file"}

    asset_root = (root / "data/ifc").absolute()
    cross_alias = _cross_task_reference_aliases(root, groups)
    rows = []
    verified_total_bytes = 0
    digest_paths: dict[str, list[str]] = defaultdict(list)
    for g in sorted(groups, key=lambda x: x["public_input_path"]):
        path = g["public_input_path"]
        if path not in remote:
            raise CachedInputIdentityBlocked("Source input missing in pinned publisher metadata")
        if remote[path].get("size") != g["remote_file_size_metadata_bytes"]:
            raise CachedInputIdentityBlocked("Source input publisher size drift")
        result = verify_one_cached_input(asset_root, path, remote[path])
        if result["byte_sha256_verified"] is not None:
            digest_paths[result["byte_sha256_verified"]].append(path)
            verified_total_bytes += g["remote_file_size_metadata_bytes"]
        rows.append({
            "public_input_path": path,
            "public_task_ids": g["public_task_ids"],
            "task_count": g["task_count"],
            "expected_source_bytes": g["remote_file_size_metadata_bytes"],
            **result,
            "verified_underlying_building_lineage": None,
            "per_file_legal_provider_transfer_approved": False,
            "is_cross_task_reference_alias_in_original_324": (
                path in cross_alias["overlap_source_paths"]
            ),
        })

    if verified_total_bytes > MAX_TOTAL_IFC_BYTES:
        raise CachedInputIdentityBlocked("Unexpected aggregate local hash cost, needs separate review")
    statuses = {s: sum(row["status"] == s for row in rows) for s in sorted({r["status"] for r in rows})}
    complete = [r for r in rows if r["status"] == "PUBLISHER_OBJECT_AND_LOCAL_SHA256_VERIFIED"]
    verified_tasks = sum(r["task_count"] for r in complete)
    if sum(r["task_count"] for r in rows) != 36:
        raise CachedInputIdentityBlocked("Frozen 36 pilot task coverage drift")
    return {
        "status": "PARTIAL_LOCAL_INPUT_BYTE_IDENTITY_VERIFIED_NOT_SCIENTIFIC_LAUNCH",
        "scope": "ALREADY_CACHED_EXACT_INPUT_IFC_BYTES_ONLY_NO_GT_NATIVE_PARSE",
        "pinned_task_sha256": earlier["task_jsonl_sha256"],
        "pinned_model_revision": earlier["model_revision"],
        "pinned_evidence_sha256": {
            "source_path_report": SOURCE_PATH_REPORT_SHA256,
            "lineage_review_queue": REVIEW_QUEUE_SHA256,
            "existing_source_rights": RIGHTS_LEDGER_SHA256,
            "remote_file_metadata": sha256(remote_bytes).hexdigest(),
        },
        "original_pilot_tasks": 36,
        "distinct_pilot_source_paths": 25,
        "verified_local_input_files": len(complete),
        "verified_local_distinct_byte_sha256": len(digest_paths),
        "verified_pilot_tasks_with_local_input": verified_tasks,
        "pilot_tasks_without_verified_local_input": 36 - verified_tasks,
        "missing_local_source_paths": sum(r["status"] == "MISSING_LOCAL_PINNED_INPUT" for r in rows),
        "local_source_hash_bytes_read_for_sha256": verified_total_bytes,
        "remote_reported_missing_source_bytes": sum(
            r["expected_source_bytes"] for r in rows
            if r["status"] == "MISSING_LOCAL_PINNED_INPUT"
        ),
        "verification_method_counts": {
            m: sum(row["verification_method"] == m for row in complete)
            for m in ("publisher_git_blob_sha1_and_local_sha256", "publisher_lfs_sha256_and_local_sha256")
        },
        "exact_duplicate_byte_sha256_groups": [
            {"verified_byte_sha256": digest, "source_input_paths": sorted(paths)}
            for digest, paths in sorted(digest_paths.items()) if len(paths) > 1
        ],
        "status_counts": statuses,
        "independent_underlying_building_lineages_verified": 0,
        "rights_cleared_for_external_provider": 0,
        "actual_model_calls": 0,
        "approved_paid_model_calls": 0,
        "model_launch_allowed": False,
        "cross_task_reference_alias_audit": {
            name: value for name, value in cross_alias.items()
            if name != "overlap_source_paths"
        },
        "verified_cached_inputs_that_are_reference_paths_for_some_other_task": sum(
            r["status"] == "PUBLISHER_OBJECT_AND_LOCAL_SHA256_VERIFIED"
            and r["is_cross_task_reference_alias_in_original_324"] for r in rows
        ),
        "original_task_reference_file_role_read": False,
        "source_IFC_geometry_native_parsed": False,
        "rows": rows,
        "nonclaims": [
            "20 different original source SHA256 digests prove different file BYTES, not independent building/project lineage",
            "The frozen full 36 task sample and all 6 unavailable tasks remain in the denominator",
            "Hashing public input bytes may also hash an asset used as another task's reference; task-to-file role isolation is required",
            "Original task reference files were never dereferenced in their reference role; no reference scores/geometry were inspected",
            "Native input/GT geometry and author scorer were not inspected in this SHA-only audit",
            "Dataset-level CC BY 4.0 does not establish original per-file rights or provider retention consent",
            "No official publication-backed scorer, true unseen holdout, preregistration or model-launch approval",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write == args.check:
        parser.error("Exactly one of --write or --check required")
    root = Path(__file__).resolve().parents[1]
    report = run_cached_input_audit(root)
    data = (json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    output = root / "reports/bim_edit_pilot_existing_cached_input_SHA256_20261119.json"
    if args.write:
        with output.open("xb") as out:
            out.write(data)
    elif not output.is_file() or output.read_bytes() != data:
        raise CachedInputIdentityBlocked("Frozen cached-input SHA report missing or changed")
    print(
        f"BIM_EDIT_EXISTING_INPUT_BYTE_HASH=PASS"
        f" files={report['verified_local_input_files']}/{report['distinct_pilot_source_paths']}"
        f" pilot_tasks={report['verified_pilot_tasks_with_local_input']}/36"
        f" unique_sha256={report['verified_local_distinct_byte_sha256']}"
        " native_geometry_and_scorer_read=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
