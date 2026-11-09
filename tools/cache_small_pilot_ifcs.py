"""Bounded public pinned IFC cache for the trusted, OFFLINE GT auditor.

Only a fixed subset of the 36 prospectively selected task IDs can be
downloaded. The default is planning only: network access requires --apply
and --limit-bytes. Bytes stay in gitignored local scratch. No API keys,
model calls, arbitrary paths, benchmark scoring or agent-facing GT access.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import urllib.request

from src.data.bim_edit import (
    AuditError, MODEL_REV, read_tasks, repo_asset_path,
    validate_remote_tree, verify_local_asset_bytes
)
from src.data.pilot_asset_audit import _files_in_root
from tools.prepare_pilot_candidate import select

ROOT=Path(__file__).resolve().parents[1]
MAX_LOCAL_BATCH_BYTES=50_000_000


def bounded_plan(records:list[dict],candidate:dict,tree:list[dict],
                 root:Path,budget:int)->dict:
    if not isinstance(budget,int) or not 0<=budget<=MAX_LOCAL_BATCH_BYTES:
        raise AuditError("Batch budget must be between zero and 50MB")
    indexed={row["task_id"]:row for row in records}
    remote={row["path"]:row for row in tree if row.get("type")=="file"}
    missing_by_task={}
    present=set()
    for row in candidate["tasks"]:
        task=indexed[row["task_id"]]
        assets={repo_asset_path(task[k]) for k in ("input_ifc","ground_truth_ifc")}
        for name in assets:
            if name not in remote:
                raise AuditError("Missing pinned remote asset metadata")
            path=_files_in_root(root,name)
            if path.exists():
                verify_local_asset_bytes(path,remote[name])
                present.add(name)
        missing_by_task[task["task_id"]]=assets-present
    pending={tid:files for tid,files in missing_by_task.items() if files}
    chosen=[]
    downloads=set()
    spent=0
    while pending:
        options=sorted(
            (sum(remote[a]["size"] for a in files-downloads),
             tid) for tid,files in pending.items()
        )
        eligible=next(((amount,tid) for amount,tid in options
                      if spent+amount<=budget),None)
        if eligible is None:
            break
        amount,tid=eligible
        downloads.update(pending.pop(tid))
        spent+=amount
        chosen.append(tid)
    if spent!=sum(remote[name]["size"] for name in downloads):
        raise AuditError("Internal budget/deduplication accounting error")
    return {
        "status":"PLAN_ONLY_NOT_A_BENCHMARK_RUN",
        "fixed_task_ids":chosen,
        "planned_download_bytes":spent,
        "planned_download_file_count":len(downloads),
        "unique_missing_assets":sorted(downloads),
        "max_budget_bytes":budget,
    }


def fetch_verified(plan:dict,remote:list[dict],root:Path,
                   *,timeout_seconds:int=40)->dict:
    if not 2<=timeout_seconds<=90:
        raise AuditError("Unsafe download timeout")
    index={x["path"]:x for x in remote if x.get("type")=="file"}
    names=plan.get("unique_missing_assets")
    cap=plan.get("planned_download_bytes")
    if not isinstance(names,list) or not all(isinstance(n,str) for n in names):
        raise AuditError("Frozen plan asset list required")
    if len(names)!=len(set(names)) or any(n not in index for n in names):
        raise AuditError("Duplicate or unpinned plan asset")
    if not isinstance(cap,int) or not 0<=cap<=MAX_LOCAL_BATCH_BYTES:
        raise AuditError("Invalid frozen download byte budget")
    if sum(index[n]["size"] for n in names)!=cap:
        raise AuditError("Frozen budget and pinned asset bytes disagree")
    downloaded=0
    new_files=0
    for name in plan["unique_missing_assets"]:
        if name not in index:
            raise AuditError("Unpinned file in approved plan")
        entry=index[name]
        destination=_files_in_root(root,name)
        destination.parent.mkdir(parents=True,exist_ok=True)
        if destination.exists():
            verify_local_asset_bytes(destination,entry)
            continue
        temp=destination.with_name(".bim-pinned-"+secrets.token_hex(12)+".part")
        try:
            req=urllib.request.Request(
                "https://huggingface.co/datasets/BIM-Edit/BIM-Edit/resolve/"
                +MODEL_REV+"/"+name,
                headers={"User-Agent":"bim-markup-bench-pinned-audit"}
            )
            with urllib.request.urlopen(req,timeout=timeout_seconds) as response:
                with temp.open("xb") as f:
                    written=0
                    for data in iter(lambda:response.read(256*1024),b""):
                        written+=len(data)
                        if written>entry["size"]:
                            raise AuditError("Remote file exceeds pinned byte count")
                        f.write(data)
                    f.flush()
                    os.fsync(f.fileno())
            verify_local_asset_bytes(temp,entry)
            # Exclusive hardlink preserves an already-downloaded file in a
            # concurrent caller; never overwrite any existing task/GT bytes.
            try:
                os.link(temp,destination)
                downloaded+=temp.stat().st_size
                new_files+=1
            except FileExistsError:
                verify_local_asset_bytes(destination,entry)
        finally:
            temp.unlink(missing_ok=True)
    if downloaded>plan["planned_download_bytes"]:
        raise AuditError("Downloaded more than frozen preflight budget")
    return {
        "status":"PUBLIC_BYTES_CACHED_AND_HASH_VERIFIED",
        "downloaded_files":new_files,
        "downloaded_bytes":downloaded,
        "paid_model_calls":0,
        "official_tasks_scored":0,
        "GT_exposed_to_agent":False,
    }


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit-bytes",type=int,required=True)
    parser.add_argument("--apply",action="store_true",
                        help="Explicitly download hashed public model assets")
    opts=parser.parse_args()
    task_file=ROOT/"data/tasks.jsonl"
    records=read_tasks(task_file)
    tree=json.loads((ROOT/"data/bim_edit_remote_tree.json").read_text())
    validate_remote_tree(records,tree)
    candidate_file=ROOT/"manifests/pilot_36_candidate_v0.json"
    candidate=json.loads(candidate_file.read_text())
    if candidate!=select(task_file):
        raise AuditError("Fixed pilot candidate metadata mismatch")
    cache=ROOT/"data/ifc"
    if cache.is_symlink() or not cache.is_dir():
        raise AuditError("IFC cache path missing or symlinked")
    plan=bounded_plan(records,candidate,tree,cache,opts.limit_bytes)
    sanitized={
        "status":plan["status"],
        "fixed_task_ids":plan["fixed_task_ids"],
        "planned_download_bytes":plan["planned_download_bytes"],
        "planned_download_file_count":plan["planned_download_file_count"],
        "max_budget_bytes":opts.limit_bytes,
        "apply_requested":opts.apply,
        "paid_model_calls":0,
        "official_tasks_scored":0,
    }
    if opts.apply:
        sanitized["actual"]=fetch_verified(plan,tree,cache)
        sanitized["status"]="PUBLIC_ASSET_CACHE_APPLIED_NOT_AN_EXPERIMENT"
    print(json.dumps(sanitized,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
