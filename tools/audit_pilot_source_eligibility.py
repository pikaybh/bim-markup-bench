"""G1 #16: bounded, trusted source-only feasibility audit for the FROZEN 36.

This is a preregistration *readiness* audit, NOT an LLM, editor, scorer or
official task oracle. Private target GUIDs from task metadata are inspected
only inside this trusted process and NEVER included in the report. No GT
model is opened, result IFC written, or network/model provider called.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import ifcopenshell

from src.data.bim_edit import (
    AuditError,read_tasks,repo_asset_path,verify_local_asset_bytes,validate_remote_tree,
)
from src.data.pilot_asset_audit import _files_in_root
from src.evaluation.g1_coverage import STATIC_UNSUPPORTED,CONDITIONAL
from src.runtime.geometry_ops import wall_thickness_eligibility
from src.runtime.ifc_mutations import Mutation,validate_source_mutation_eligibility
from src.runtime.ifc_projection import project_ifc
from src.runtime.topology_ops import check_window_deletion,_validate_opening_move_preflight
from src.runtime.xml_parser import parse_xml
from tools.prepare_pilot_candidate import select

ROOT=Path(__file__).resolve().parents[1]


def _conditional_source_probe(task:dict,source:Path)->tuple[str,bool|None]:
    """Read-only, restrictive source policy. Never declares a task solved."""
    cls=task["target"]["entity_type"]
    op=task["operation"]
    prompt=task["prompt"].lower()
    try:
        # Reject obviously invalid STEP bytes before creating a partial
        # native IfcOpenShell wrapper (which can emit destructor warnings).
        with source.open("rb") as stream:
            if not stream.read(96).lstrip(b" \r\n\t").startswith(b"ISO-10303-21;"):
                return "SOURCE_NATIVE_PROBE_BLOCKED",None
        model=ifcopenshell.open(str(source))
        if model.schema!="IFC4X3":
            return "IFC_SCHEMA_NOT_IFC4X3",None
        target_guids=task["target"]["guids"]
        targets=[model.by_guid(g) for g in target_guids]
        if any(x is None or x.is_a()!=cls for x in targets):
            return "TARGET_NOT_FOUND_IN_NATIVE_SOURCE",None
        if cls=="IfcWall" and op=="create":
            if "ifcrelspaceboundary" in prompt or "ifcrelconnectspathelements" in prompt:
                return "REQUIRED_NATIVE_RELATION_CREATION_NOT_IMPLEMENTED",None
            return "WALL_CREATE_SPATIAL_ORACLE_NOT_PROVEN",None
        if cls=="IfcWall" and op=="delete":
            target=targets[0]
            mutation=Mutation("DELETE_WALL","audit_only",target.GlobalId,1,(),"source preflight only")
            try:
                validate_source_mutation_eligibility(model,(mutation,))
            except Exception:
                return "WALL_DELETE_SOURCE_DEPENDENCIES_BLOCKED",None
            return "WALL_DELETE_NATIVE_PREDICATE_PASS_ORACLE_PENDING",None
        if cls=="IfcWall" and op=="update":
            if "thickness" not in prompt:
                return "WALL_UPDATE_EXACT_TASK_ORACLE_NOT_AVAILABLE",None
            try:
                wall_thickness_eligibility(model,targets[0])
            except Exception:
                return "WALL_THICKNESS_NATIVE_DEPENDENCIES_BLOCKED",None
            return "WALL_THICKNESS_NATIVE_PREDICATE_PASS_ORACLE_PENDING",None
        if cls=="IfcWindow" and op=="delete":
            try:
                check_window_deletion(model,targets[0].GlobalId)
            except Exception:
                return "WINDOW_DELETE_NATIVE_RELATIONS_BLOCKED",None
            projection=project_ifc(source)
            return ("WINDOW_DELETE_TARGET_PROJECTED_ORACLE_PENDING" if
                    targets[0].GlobalId in dict(projection.projected_global_ids)
                    else "WINDOW_DELETE_TARGET_OPAQUE_IN_XML"),True
        if cls=="IfcWindow" and op=="update":
            if "width" in prompt or "height" in prompt:
                return "WINDOW_OPENING_DIMENSION_CHANGE_UNIMPLEMENTED",None
            projection=project_ifc(source)
            mapped=dict(projection.projected_global_ids)
            if targets[0].GlobalId not in mapped:
                return "WINDOW_MOVE_TARGET_OPAQUE_IN_XML",True
            fills=list(targets[0].FillsVoids)
            if len(fills)!=1:
                return "WINDOW_MOVE_REQUIRES_ONE_FILL",True
            opening=fills[0].RelatingOpeningElement
            if opening.GlobalId not in mapped:
                return "OPENING_TARGET_OPAQUE_IN_XML",True
            parsed=parse_xml(projection.xml)
            node=next(x for x in parsed.elements if x.ifc_guid==opening.GlobalId)
            attributes=dict(node.attrs())
            # A bounded +1 metre local probe, not a complete interpretation
            # of a world-coordinate natural-language edit.
            attributes["offset"]=float(attributes["offset"])+1.0
            try:
                _validate_opening_move_preflight(
                    model,opening,attributes,model.by_type("IfcOpeningElement"))
            except Exception:
                return "OPENING_MOVE_NATIVE_FRAME_OR_DEPENDENCY_BLOCKED",True
            return "WINDOW_MOVE_VECTOR_AND_PAIRED_ORACLE_NOT_PROVEN",True
        return "SOURCE_TYPE_OPERATION_NOT_PROVEN",None
    except Exception:
        # Fail closed, no raw native error messages (can contain private IDs).
        return "SOURCE_NATIVE_PROBE_BLOCKED",None


def audit_frozen_pilot(
    *,
    task_file:Path=ROOT/"data/tasks.jsonl",
    candidate_file:Path=ROOT/"manifests/pilot_36_candidate_v0.json",
    remote_tree_file:Path=ROOT/"data/bim_edit_remote_tree.json",
    support_file:Path=ROOT/"reports/g1_324_support_matrix.json",
    cache_root:Path=ROOT/"data/ifc",
)->dict:
    tasks=read_tasks(task_file)
    candidate=json.loads(candidate_file.read_text(encoding="utf-8"))
    if candidate!=select(task_file) or len(candidate["tasks"])!=36:
        raise AuditError("Frozen fixed pilot ID/stratum integrity failed")
    tree=json.loads(remote_tree_file.read_text(encoding="utf-8"))
    validate_remote_tree(tasks,tree)
    support=json.loads(support_file.read_text(encoding="utf-8"))
    if (support.get("coverage_accounted_for")!=324
            or support.get("status")!="BLOCKED_NO_OFFICIAL_EVALUATION"):
        raise AuditError("Unexpected G1 static capability ledger version/gate")
    levels={r["task_id"]:r for r in support["tasks"]}
    if len(levels)!=324:
        raise AuditError("Duplicate or missing G1 capability IDs")
    by_id={r["task_id"]:r for r in tasks}
    remote={r["path"]:r for r in tree if r.get("type")=="file"}
    if not cache_root.is_dir() or cache_root.is_symlink():
        raise AuditError("Trusted public cache missing or linked")
    report=[]
    for item in candidate["tasks"]:
        tid=item["task_id"]
        task=by_id[tid]
        ledger=levels.get(tid)
        if ledger is None or ledger["target_class"]!=task["target"]["entity_type"]:
            raise AuditError("Static capability ledger mismatches frozen task")
        reason="STATIC_ENGINE_UNSUPPORTED"
        source_verified=False
        projection=None
        if ledger["engine_status"]==CONDITIONAL:
            rel=repo_asset_path(task["input_ifc"])
            file=_files_in_root(cache_root,rel)
            if not file.is_file():
                reason="MISSING_PINNED_INPUT_IFC"
            else:
                # Mismatch is an audit error, not an unsupported task to skip.
                verify_local_asset_bytes(file,remote[rel])
                source_verified=True
                reason,projection=_conditional_source_probe(task,file)
        elif ledger["engine_status"]!=STATIC_UNSUPPORTED:
            raise AuditError("Unknown frozen static G1 engine status")
        report.append({
            "task_id":tid,
            "operation":task["operation"],
            "category":task["category"],
            "target_class":task["target"]["entity_type"],
            "source_bytes_verified_for_conditional_probe":source_verified,
            "xml_projection_parsed_if_checked":projection,
            "reason_code":reason,
            "paired_d0_i0_task_oracle_verified":False,
            "official_task_scored":False,
        })
    counts=dict(sorted(Counter(r["reason_code"] for r in report).items()))
    if len(report)!=36 or len({r["task_id"] for r in report})!=36:
        raise AuditError("Frozen 36-task coverage incomplete")
    return {
        "status":"BLOCKED_NO_OFFICIAL_PAIRED_D0_I0_TASK_ORACLES",
        "audit_method":"trusted_read_only_source_preconditions_not_experimental_outcomes",
        "frozen_candidate_sha256":sha256(candidate_file.read_bytes()).hexdigest(),
        "task_count":36,
        "static_unsupported_count":sum(x["reason_code"]=="STATIC_ENGINE_UNSUPPORTED" for x in report),
        "source_conditionals_checked":sum(x["source_bytes_verified_for_conditional_probe"] for x in report),
        "missing_conditional_source_count":counts.get("MISSING_PINNED_INPUT_IFC",0),
        "verified_official_d0_i0_task_oracles":0,
        "official_scores_computed":0,
        "paid_model_calls":0,
        "GT_file_loaded":False,
        "model_agent_exposed_to_target_metadata":False,
        "fail_closed_reason_counts":counts,
        "tasks":report,
    }

def main()->int:
    """No-network evidence generator: exit 2 until paired oracles are proven."""
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    a=parser.parse_args()
    outcome=audit_frozen_pilot()
    if a.output_json is not None:
        path=a.output_json
        if path.exists() or path.is_symlink() or not path.parent.is_dir():
            parser.error("Refuse existing/symlink evidence path or missing parent")
        with path.open("x",encoding="utf-8",newline="\n") as stream:
            stream.write(json.dumps(outcome,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
        key:outcome[key] for key in (
            "status","task_count","static_unsupported_count",
            "source_conditionals_checked","missing_conditional_source_count",
            "verified_official_d0_i0_task_oracles",
            "official_scores_computed","paid_model_calls",
            "fail_closed_reason_counts",
        )
    },sort_keys=True,indent=2))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
