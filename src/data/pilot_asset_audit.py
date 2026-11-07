"""G0 #3 conservative byte-checked pilot input/GT audit (trusted grader only).

Only pinned PUBLIC metadata and already-local IFC files are read.
No download, model provider, task execution or GT exposure to agents.
This module must not be imported by direct/imperative agent runner.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

import ifcopenshell

from src.evaluation.semantic_diff import product_fingerprint
from src.data.bim_edit import (
    AuditError,read_tasks,repo_asset_path,verify_local_asset_bytes,
    validate_remote_tree,sha256_file,MODEL_REV,TASK_REV
)
from tools.prepare_pilot_candidate import select

BENCHMARK_DIR=Path(__file__).resolve().parents[2]
CANDIDATE=BENCHMARK_DIR/"manifests/pilot_36_candidate_v0.json"


def _files_in_root(root:Path,relative:str)->Path:
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise AuditError("IFC audit root must be a real, absolute directory")
    if not re.fullmatch(r"(simple|complex)/[A-Za-z0-9_.-]+\.ifc",relative):
        raise AuditError("Disallowed model dataset path")
    path=root/relative
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise AuditError("Local asset symlink/traversal is forbidden")
    return path


def _delta(task:dict,source:Path,reference:Path)->dict:
    """Validate native target existence/edit class, NOT official metric score."""
    try:
        # Malformed IFC bytes can leave an incompletely constructed native
        # IfcOpenShell wrapper that emits destructor errors on this version.
        # Reject visibly invalid STEP files before opening the C++ parser.
        for item in (source,reference):
            with item.open("rb") as fd:
                if not fd.read(96).lstrip(b" \\n\\r\\t").startswith(b"ISO-10303-21;"):
                    return {"status":"BLOCKED_NATIVE_IFC_PARSE"}
        a=ifcopenshell.open(str(source))
        b=ifcopenshell.open(str(reference))
        if a.schema!=b.schema or a.schema not in ("IFC4","IFC4X3"):
            return {"status":"BLOCKED_IFC_SCHEMA_MISMATCH"}
        target=task["target"]["entity_type"]
        old={obj.GlobalId:obj for obj in a.by_type(target)}
        new={obj.GlobalId:obj for obj in b.by_type(target)}
        op=task["operation"]
        if op=="create":
            added=set(new)-set(old)
            passed=len(added)==1
            status="NATIVE_CREATE_ONE_ADDED_CLASS" if passed else "BLOCKED_CREATE_DELTA"
            return {"status":status,"schema":a.schema,
                    "source_target_class_count":len(old),
                    "reference_target_class_count":len(new),
                    "created_target_class_count":len(added)}
        guid=task["target"]["guids"][0]
        original=old.get(guid);expected=new.get(guid)
        if op=="delete":
            passed=original is not None and expected is None
            status="NATIVE_DELETE_TARGET_MISSING_FROM_GT" if passed else "BLOCKED_DELETE_DELTA"
        else:
            present=original is not None and expected is not None
            # A shared GUID alone does NOT prove an actual edit.
            changed=present and product_fingerprint(original)!=product_fingerprint(expected)
            passed=bool(changed)
            status=("NATIVE_UPDATE_TARGET_CHANGE_OBSERVED" if changed
                    else "BLOCKED_UPDATE_DELTA_UNPROVEN")
        return {"status":status,"schema":a.schema,
                "source_target_class_count":len(old),
                "reference_target_class_count":len(new)}
    except Exception:
        return {"status":"BLOCKED_NATIVE_IFC_PARSE"}


def audit_single_task(task:dict,tree_index:dict,root:Path)->dict:
    """Sanitized record: no prompts, target GlobalIds or GT asset paths."""
    item={
        "task_id":task["task_id"],
        "operation":task["operation"],
        "target_class":task["target"]["entity_type"],
        "input_bytes_verified":False,
        "reference_bytes_verified":False,
        "native_target_delta_verified":False,
        "status":"MISSING_LOCAL_IFC_BYTES",
    }
    source_rel=repo_asset_path(task["input_ifc"])
    reference_rel=repo_asset_path(task["ground_truth_ifc"])
    for key,relative in (("input",source_rel),("reference",reference_rel)):
        meta=tree_index.get(relative)
        if not isinstance(meta,dict) or meta.get("type")!="file":
            item["status"]="BLOCKED_MISSING_PINNED_REMOTE_FILE"
            return item
        item[key+"_expected_bytes"]=meta["size"]
    paths={}
    for key,relative in (("input",source_rel),("reference",reference_rel)):
        p=_files_in_root(root,relative)
        paths[key]=p
        if not p.exists():
            continue
        try:
            verify_local_asset_bytes(p,tree_index[relative])
        except AuditError:
            item["status"]="BLOCKED_LOCAL_ASSET_DIGEST_MISMATCH"
            return item
        item[key+"_bytes_verified"]=True
    if not (item["input_bytes_verified"] and item["reference_bytes_verified"]):
        return item
    outcome=_delta(task,paths["input"],paths["reference"])
    item["native_delta_status"]=outcome["status"]
    item["native_target_delta_verified"]=outcome["status"].startswith("NATIVE_")
    if item["native_target_delta_verified"]:
        item["status"]="VERIFIED_PINNED_BYTES_AND_CLASS_DELTA"
    else:
        item["status"]=outcome["status"]
    for name in ("schema","source_target_class_count",
                 "reference_target_class_count","created_target_class_count"):
        if name in outcome:item[name]=outcome[name]
    return item


def audit_fixed_candidate(*,task_file:Path,tree_file:Path,
                          local_root:Path,candidate_file:Path=CANDIDATE)->dict:
    records=read_tasks(task_file)
    tree=json.loads(tree_file.read_text(encoding="utf-8"))
    validate_remote_tree(records,tree)
    candidate=json.loads(candidate_file.read_text(encoding="utf-8"))
    if candidate!=select(task_file) or len(candidate["tasks"])!=36:
        raise AuditError("Frozen pilot candidate differs from pinned sampler")
    by_id={item["task_id"]:item for item in records}
    remote={x["path"]:x for x in tree if x.get("type")=="file"}
    selected=[by_id[x["task_id"]] for x in candidate["tasks"]]
    unique_assets={
        repo_asset_path(task[key]) for task in selected
        for key in ("input_ifc","ground_truth_ifc")
    }
    total_bytes=sum(remote[name]["size"] for name in unique_assets)
    results=[audit_single_task(task,remote,local_root) for task in selected]
    statuses=dict(sorted(Counter(r["status"] for r in results).items()))
    return {
        "status":"BLOCKED_FULL_PILOT_ASSET_VERIFICATION",
        "model_revision":MODEL_REV,
        "task_revision":TASK_REV,
        "candidate_sha256":sha256(candidate_file.read_bytes()).hexdigest(),
        "total_candidate_tasks":len(selected),
        "unique_referenced_assets":len(unique_assets),
        "estimated_unique_download_bytes":total_bytes,
        "locally_verified_both_input_and_GT":sum(
            r["input_bytes_verified"] and r["reference_bytes_verified"] for r in results
        ),
        "native_delta_verified_tasks":sum(r["native_target_delta_verified"] for r in results),
        "all_pilot_bytes_and_deltas_verified":all(
            r["native_target_delta_verified"] for r in results
        ),
        "official_scores_computed":0,
        "paid_model_calls":0,
        "full_324_IFC_content_audit_complete":False,
        "GT_unavailable_to_agents":True,
        "task_status_counts":statuses,
        "tasks":results,
    }
