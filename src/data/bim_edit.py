"""BIM-Edit task metadata audit: no IFC corpus downloads or paid services.

The full task record contains grader-only fields. Never pass it to the LLM.
Only agent_view() output may cross the agent boundary.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.request import urlopen

TASK_REV = "2dc6462bfab145ddf81b43e9954322855b8443dc"
TASK_SHA256 = "9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83"
MODEL_REV = "0ae510bd21865def4e2c6145c1244f01a1e3bcb9"
TASK_URL = "https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks/resolve/" + TASK_REV + "/tasks.jsonl"
MODEL_TREE_URL = "https://huggingface.co/api/datasets/BIM-Edit/BIM-Edit/tree/" + MODEL_REV + "?recursive=true"
MODEL_REPO_URL = "https://huggingface.co/api/datasets/BIM-Edit/BIM-Edit"
PREFIX_MAP = {"data/realistic": "complex", "data/artificial": "simple"}
TYPES = {"IfcWall": 72, "IfcSlab": 72, "IfcSpace": 72, "IfcDoor": 36, "IfcWindow": 36, "IfcColumn": 36}
GROUPS = {"create": 108, "update": 108, "delete": 108}
CATEGORIES = {"direct": 108, "spatial": 108, "topological": 108}
SCENES = {"scene:A": 162, "scene:R": 162}
GUID_RE = re.compile(r"^[0-9A-Za-z_$]{22}$")
PATH_RE = re.compile(r"^data/(realistic|artificial)/([A-Za-z0-9_.-]+\.ifc)$")

class AuditError(ValueError):
    pass

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_tasks(path: Path, *, check_revision: bool = True) -> list[dict]:
    if check_revision and sha256_file(path) != TASK_SHA256:
        raise AuditError("Pinned public task records SHA-256 mismatch")
    rows = []
    with path.open(encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise AuditError(f"Task at line {n} must be an object")
                rows.append(row)
            except json.JSONDecodeError as exc:
                raise AuditError(f"Malformed JSON line {n}") from exc
    return rows

def repo_asset_path(task_path: str) -> str:
    match = PATH_RE.fullmatch(task_path)
    if not match or task_path.lower().endswith(".ifc.ifc"):
        raise AuditError("Unsupported/suspicious task IFC path")
    category, name = match.groups()
    return PREFIX_MAP["data/" + category] + "/" + name

def validate_tasks(rows: list[dict], *, full: bool = True) -> dict:
    seen = set()
    operations = Counter()
    categories = Counter()
    scenes = Counter()
    types = Counter()
    cells = Counter()
    referenced = set()
    for i, row in enumerate(rows):
        required = {"task_id", "operation", "category", "input_ifc", "ground_truth_ifc",
                    "prompt", "target", "evaluation", "tags"}
        if not required.issubset(row):
            raise AuditError(f"Missing fields on record {i}: {sorted(required - set(row))}")
        tid = row["task_id"]
        if not isinstance(tid, str) or not tid or tid in seen:
            raise AuditError("Missing/duplicate task_id")
        seen.add(tid)
        op = row["operation"]
        cat = row["category"]
        if op not in GROUPS or cat not in CATEGORIES:
            raise AuditError("Unknown operation or category")
        if not isinstance(row["prompt"], str) or not row["prompt"].strip():
            raise AuditError("Missing natural-language instruction")
        if not isinstance(row["evaluation"], dict) or not isinstance(row["tags"], list):
            raise AuditError("Invalid evaluation/tags record")
        tags = [s for s in row["tags"] if s in SCENES]
        if len(tags) != 1:
            raise AuditError("Missing/ambiguous scene tag")
        target = row["target"]
        if not isinstance(target, dict) or target.get("entity_type") not in TYPES:
            raise AuditError("Unknown target class")
        gids = target.get("guids")
        if not isinstance(gids, list) or len(gids) != (0 if op == "create" else 1):
            raise AuditError("Invalid target GUID count for operation")
        if any(not isinstance(g, str) or not GUID_RE.fullmatch(g) for g in gids):
            raise AuditError("Invalid 22-character IFC GlobalId")
        for key in ("input_ifc", "ground_truth_ifc"):
            referenced.add(repo_asset_path(row[key]))
        operations[op] += 1
        categories[cat] += 1
        scenes[tags[0]] += 1
        types[target["entity_type"]] += 1
        cells[(op, cat, tags[0])] += 1
    if full:
        if len(rows) != 324 or dict(operations) != GROUPS or dict(categories) != CATEGORIES:
            raise AuditError("324-task operation/category count mismatch")
        if dict(scenes) != SCENES or dict(types) != TYPES or len(cells) != 18 or set(cells.values()) != {18}:
            raise AuditError("Scene/type/18-strata balance mismatch")
    return {
        "record_count": len(rows),
        "unique_task_ids": len(seen),
        "operations": dict(sorted(operations.items())),
        "categories": dict(sorted(categories.items())),
        "scenes": dict(sorted(scenes.items())),
        "types": dict(sorted(types.items())),
        "num_strata": len(cells),
        "unique_referenced_ifc_assets": len(referenced),
        "remote_asset_paths": sorted(referenced),
    }

def agent_view(row: dict) -> dict:
    """The ONLY allowed LLM-facing metadata projection.

    The model-specific input file should be mounted as input.ifc inside its
    isolated sandbox, with no raw benchmark path or grader-only target data.
    """
    if not isinstance(row.get("prompt"), str):
        raise AuditError("Missing prompt for agent")
    return {"task_id": row["task_id"], "instruction": row["prompt"], "input_file": "input.ifc"}

def validate_remote_tree(records: list[dict], tree: list[dict]) -> dict:
    expected = set(validate_tasks(records, full=True)["remote_asset_paths"])
    available = {entry["path"]: entry for entry in tree if entry.get("type") == "file"}
    missing = sorted(expected - available.keys())
    total_ifcs = [entry for path, entry in available.items() if path.lower().endswith(".ifc")]
    total_size = sum(entry.get("size", 0) or 0 for entry in available.values())
    lfs = sum(bool(entry.get("lfs", {}).get("oid")) for entry in total_ifcs)
    absent_digest = [entry["path"] for entry in total_ifcs if not entry.get("lfs", {}).get("oid") and not entry.get("oid")]
    if missing:
        raise AuditError(f"Missing {len(missing)} task-referenced IFC files in pinned remote tree: {missing[:3]}")
    if absent_digest:
        raise AuditError("Asset metadata lacks Git SHA-1 or LFS SHA-256 pointers")
    if not all(isinstance(available[p].get("size"), int) and available[p]["size"] > 0 for p in expected):
        raise AuditError("Missing/suspicious file size in referenced remote asset")
    return {
        "source": "Hugging Face pinned repository tree metadata ONLY",
        "remote_file_metadata_present": True,
        "actual_bytes_downloaded_or_verified": False,
        "target_guids_in_actual_input_gt_checked": False,
        "task_paths_matched": len(expected),
        "task_paths_missing": len(missing),
        "remote_total_ifc_files": len(total_ifcs),
        "remote_total_file_count": len(available),
        "remote_total_file_bytes": total_size,
        "remote_ifc_with_lfs_sha256_pointer": lfs,
        "remote_ifc_with_only_git_object_id": len(total_ifcs) - lfs,
        "full_validation": "BLOCKED_PENDING_IFC_ASSET_DOWNLOAD_AND_CONTENT_VERIFICATION"
    }


def verify_local_asset_bytes(local_path: Path, tree_entry: dict) -> dict:
    """Compare actual local IFC bytes against pinned Hugging Face LFS SHA-256 or Git blob SHA-1.

    This has NO network side effects. A remote pointer alone never counts as verification.
    """
    if not local_path.is_file():
        raise AuditError("IFC asset bytes missing at required local path")
    size = local_path.stat().st_size
    if size != tree_entry.get("size"):
        raise AuditError("IFC asset size mismatch")
    lfs_sha256 = tree_entry.get("lfs", {}).get("oid")
    if lfs_sha256:
        observed = sha256_file(local_path)
        if observed != lfs_sha256:
            raise AuditError("IFC LFS SHA256 content mismatch")
        return {"content_sha256_verified": True, "git_blob_sha1_verified": False, "size": size}
    git_oid = tree_entry.get("oid")
    if not isinstance(git_oid, str) or not re.fullmatch(r"[0-9a-f]{40}", git_oid):
        raise AuditError("Missing Git blob SHA1 for non-LFS IFC asset")
    h = hashlib.sha1()
    h.update(("blob " + str(size) + "\0").encode("ascii"))
    with local_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    if h.hexdigest() != git_oid:
        raise AuditError("IFC Git blob SHA1 content mismatch")
    return {"content_sha256_verified": False, "git_blob_sha1_verified": True, "size": size}


def verify_local_assets(rows: list[dict], tree: list[dict], root: Path) -> dict:
    """Fail unless every pinned task-referenced input/GT IFC byte object exists and matches."""
    expected = validate_tasks(rows, full=True)["remote_asset_paths"]
    remote = {r["path"]: r for r in tree if r.get("type") == "file"}
    verified = []
    for name in expected:
        if name not in remote:
            raise AuditError("Pinned remote metadata missing a referenced IFC asset")
        actual = root / name
        if not actual.resolve().is_relative_to(root.resolve()):
            raise AuditError("Local IFC asset escaped the sandbox root")
        verified.append(verify_local_asset_bytes(actual, remote[name]))
    return {
        "verified_actual_ifc_files": len(verified),
        "verified_lfs_sha256": sum(int(x["content_sha256_verified"]) for x in verified),
        "verified_git_blob_sha1": sum(int(x["git_blob_sha1_verified"]) for x in verified),
    }

def fetch_json(url: str) -> Any:
    with urlopen(url, timeout=40) as response:
        return json.load(response)

def metadata_audit(*, task_path: Path, output_path: Path, allow_network: bool) -> dict:
    if not task_path.exists():
        if not allow_network:
            raise AuditError("Pinned 180KB public tasks metadata absent; use --fetch-metadata-only")
        task_path.parent.mkdir(parents=True, exist_ok=True)
        # Download only small public JSONL, never model IFC/GT.
        with urlopen(TASK_URL, timeout=40) as f, task_path.open("wb") as target:
            while True:
                buf = f.read(65536)
                if not buf:
                    break
                target.write(buf)
                if target.tell() > 300000:
                    raise AuditError("Task metadata unexpectedly large; abort")
    rows = read_tasks(task_path)
    task_result = validate_tasks(rows)
    if not allow_network:
        raise AuditError("Remote file tree metadata not provided: use --fetch-metadata-only")
    dataset_meta = fetch_json(MODEL_REPO_URL)
    if dataset_meta.get("sha") != MODEL_REV:
        raise AuditError("Model dataset moving ref differs from pinned SHA")
    tree = fetch_json(MODEL_TREE_URL)
    (task_path.parent / "bim_edit_remote_tree.json").write_text(json.dumps(tree), encoding="utf-8")
    remote_result = validate_remote_tree(rows, tree)
    out = {
        "status": "REMOTE_METADATA_VERIFIED_ONLY_NOT_IFC_CONTENT",
        "task_repository_revision": TASK_REV,
        "task_jsonl_sha256": TASK_SHA256,
        "model_repository_revision": MODEL_REV,
        "model_repository_license_tag": dataset_meta.get("cardData", {}).get("license"),
        "task_counts": {k: v for k, v in task_result.items() if k != "remote_asset_paths"},
        "remote": remote_result,
        "licensing": "Dataset card advertises CC-BY-4.0; individual model provenance/redistribution audit pending",
        "blockers": ["No local IFC corpus (4.31GB remote repository)", "GT versus input content and target GUID validation not performed", "No independent artifact digest recomputation", "No evaluation task oracle completed"],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out
