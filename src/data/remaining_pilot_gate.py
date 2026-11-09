"""No-download G0 #3 planning gate for the fixed BIM-Edit 36-task pilot.

Reads only pinned public metadata, the frozen candidate, local byte hashes,
and the license ledger. Never downloads or opens benchmark GT IFC as a model.
Output intentionally has no IFC file names, GT paths, target IDs or prompts.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path

from src.data.bim_edit import (
    AuditError, MODEL_REV, TASK_REV,
    read_tasks, repo_asset_path, validate_remote_tree, verify_local_asset_bytes,
)
from src.data.pilot_asset_audit import _files_in_root
from tools.cache_small_pilot_ifcs import MAX_LOCAL_BATCH_BYTES
from tools.prepare_pilot_candidate import select

ROOT=Path(__file__).resolve().parents[2]


def summarize_remaining(pairs: list[tuple[str, str, str, set[str]]],
                        remote_bytes: dict[str,int],
                        missing: set[str])->dict:
    """Pure deduplicated byte accounting; pairs carry *trusted* file paths internally."""
    if len(missing-set(remote_bytes)) or any(
        type(size) is not int or size<=0 for size in remote_bytes.values()
    ):
        raise AuditError("Missing/invalid frozen remote byte metadata")
    outstanding=[]
    selected=set()
    for tid,operation,target_class,assets in pairs:
        unresolved=assets & missing
        if unresolved:
            outstanding.append({
                "task_id":tid,"operation":operation,"target_class":target_class,
                "incremental_bytes":sum(remote_bytes[n] for n in unresolved),
                "missing_asset_count":len(unresolved),
            })
            selected|=unresolved
    return {
        "remaining_tasks":outstanding,
        "remaining_task_count":len(outstanding),
        "remaining_unique_file_count":len(selected),
        "remaining_unique_bytes":sum(remote_bytes[n] for n in selected),
        "smallest_task_incremental_bytes":min(
            (row["incremental_bytes"] for row in outstanding),default=0),
        "largest_task_incremental_bytes":max(
            (row["incremental_bytes"] for row in outstanding),default=0),
    }


def build_remaining_gate(
    *, tasks_path:Path=ROOT/"data/tasks.jsonl",
    tree_path:Path=ROOT/"data/bim_edit_remote_tree.json",
    candidate_path:Path=ROOT/"manifests/pilot_36_candidate_v0.json",
    rights_path:Path=ROOT/"manifests/source_rights.json",
    cache_root:Path=ROOT/"data/ifc",
)->dict:
    records=read_tasks(tasks_path)
    tree=json.loads(tree_path.read_text(encoding="utf-8"))
    validate_remote_tree(records,tree)
    candidate=json.loads(candidate_path.read_text(encoding="utf-8"))
    if candidate!=select(tasks_path) or len(candidate["tasks"])!=36:
        raise AuditError("Frozen pilot candidate IDs/order/hash differ")
    if cache_root.is_symlink() or not cache_root.is_dir():
        raise AuditError("Trusted IFC cache root missing or linked")
    indexed={row["task_id"]:row for row in records}
    sizes={row["path"]:row["size"] for row in tree if row.get("type")=="file"}
    remote={row["path"]:row for row in tree if row.get("type")=="file"}
    pairs=[]
    all_assets=set()
    for selected in candidate["tasks"]:
        task=indexed[selected["task_id"]]
        assets={repo_asset_path(task[k]) for k in ("input_ifc","ground_truth_ifc")}
        if len(assets)!=2 or not assets.issubset(remote):
            raise AuditError("Frozen candidate source/reference assets missing/aliased")
        pairs.append((task["task_id"],task["operation"],task["target"]["entity_type"],assets))
        all_assets|=assets
    missing=set()
    for name in sorted(all_assets):
        local=_files_in_root(cache_root,name)
        if not local.exists():
            missing.add(name)
            continue
        verify_local_asset_bytes(local,remote[name])
    summary=summarize_remaining(pairs,sizes,missing)
    cached_count=len(pairs)-summary["remaining_task_count"]
    rights=json.loads(rights_path.read_text(encoding="utf-8"))
    rights_records=rights.get("records",[])
    if not isinstance(rights_records,list):
        raise AuditError("Invalid individual model rights ledger")
    cleared=set()
    for entry in rights_records:
        if not isinstance(entry,dict):
            raise AuditError("Invalid model rights entry")
        path=entry.get("source")
        if (path in all_assets and entry.get("source_revision")==MODEL_REV
            and entry.get("rights_checked") is True
            and entry.get("consent_documented") is True
            and entry.get("redistribution_permitted") is True
            and isinstance(entry.get("source_digest_sha256"),str)
            and len(entry["source_digest_sha256"])==64):
            cleared.add(path)
    return {
        "status":"BLOCKED_MISSING_MODEL_BYTES_AND_INDIVIDUAL_RIGHTS",
        "task_revision":TASK_REV,"model_revision":MODEL_REV,
        "candidate_sha256":sha256(candidate_path.read_bytes()).hexdigest(),
        "fixed_sample_size":36,
        "byte_verified_task_input_reference_pair_count":cached_count,
        "missing_pair_details":summary["remaining_tasks"],
        "missing_task_count":summary["remaining_task_count"],
        "unique_missing_asset_count":summary["remaining_unique_file_count"],
        "unique_missing_bytes":summary["remaining_unique_bytes"],
        "smallest_remaining_pair_bytes":summary["smallest_task_incremental_bytes"],
        "max_existing_bounded_batch_bytes":MAX_LOCAL_BATCH_BYTES,
        "any_remaining_pair_fits_existing_batch":any(
            row["incremental_bytes"]<=MAX_LOCAL_BATCH_BYTES
            for row in summary["remaining_tasks"]),
        "individual_asset_redistribution_clearance_count":len(cleared),
        "individual_asset_redistribution_clearance_complete":len(cleared)==len(all_assets),
        "individual_asset_rights_review_required":True,
        "download_performed":False,"approval_to_expand_batch":False,
        "official_tasks_scored":0,"paid_model_calls":0,
    }
