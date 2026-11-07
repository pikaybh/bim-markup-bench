"""Conservative, no-network metadata-only G1-08 BIM-Edit coverage ledger.

This explicitly separates native engine capability from source IFC availability
and from benchmark task correctness. ZERO tasks are scored or declared pass.
Raw prompts, target GUIDs, GT paths and evaluation annotations NEVER appear
in generated output.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
import json
import re
from pathlib import Path

from src.data.bim_edit import AuditError, read_tasks,validate_tasks,TASK_SHA256

STATIC_UNSUPPORTED="STATIC_ENGINE_UNSUPPORTED"
CONDITIONAL="SOURCE_DEPENDENT_UNVERIFIED"
GATE_BLOCKED="BLOCKED_NO_OFFICIAL_EVALUATION"


def _classify(row:dict)->tuple[str,tuple[str,...]]:
    cls=row["target"]["entity_type"]
    op=row["operation"]
    cat=row["category"]
    text=row["prompt"].lower()
    reasons=[]
    if cls in ("IfcSpace","IfcSlab","IfcColumn"):
        reasons.append(f"{cls.upper()}_CRUD_NOT_COMPILED")
    elif cls=="IfcDoor" and op in ("create","delete"):
        reasons.append("IFCDOOR_CREATE_DELETE_AND_HOST_CASCADE_UNIMPLEMENTED")
    elif cls=="IfcWindow" and op=="create":
        reasons.append("IFCWINDOW_CREATE_AND_NEW_OPENING_UNIMPLEMENTED")
    elif cls=="IfcWall" and op=="update" and any(
        term in text for term in ("length", "rotate", "move the wall", "placement")
    ):
        reasons.append("IFCWALL_LENGTH_ENDPOINT_OR_PLACEMENT_UPDATE_UNIMPLEMENTED")
    elif cls=="IfcWindow" and op=="delete" and (
        "delete the opening" in text or "space boundary" in text
    ):
        reasons.append("IFCWINDOW_OPENING_REMOVAL_OR_SPACE_BOUNDARY_CASCADE_UNIMPLEMENTED")
    elif cls=="IfcWindow" and op=="update" and (
        "new wall" in text or "change the building storey" in text
    ):
        reasons.append("IFCWINDOW_CROSS_HOST_OR_STOREY_MOVE_UNIMPLEMENTED")
    elif cls=="IfcWall" and op=="create" and (
        "bounds the spaces" in text or "separates the rooms" in text
    ):
        reasons.append("IFCWALL_NEW_SPACE_BOUNDARY_CREATION_UNIMPLEMENTED")
    elif cls=="IfcWall" and op=="delete" and (
        "voided by openings" in text or "bounding of spaces" in text
    ):
        reasons.append("IFCWALL_DEPENDENT_VOID_AND_SPACE_BOUNDARY_CASCADE_UNIMPLEMENTED")
    if reasons:
        state=STATIC_UNSUPPORTED
    else:
        state=CONDITIONAL
        reasons.append("REQUIRES_FULL_NATIVE_SOURCE_GEOMETRY_AND_REFERENCES")
    # Distinguish language/context resolution from engine geometry capability:
    # spatial/topological NL is not proof of an editable native relation.
    if cat=="spatial":
        reasons.append("SPATIAL_NATURAL_LANGUAGE_GROUNDING_NOT_ORACLE_VERIFIED")
    elif cat=="topological":
        reasons.append("TOPOLOGICAL_TASK_REFERENCE_RESOLUTION_NOT_ORACLE_VERIFIED")
    reasons.append("PINNED_OFFICIAL_INPUT_AND_GT_IFC_BYTES_NOT_VERIFIED")
    reasons.append("INDEPENDENT_OFFICIAL_BIM_EDIT_SCORER_NOT_AVAILABLE")
    return state,tuple(sorted(set(reasons)))


def generate_coverage_ledger(rows:list[dict])->dict:
    validated=validate_tasks(rows,full=True)
    details=[]
    for row in sorted(rows,key=lambda r:r["task_id"]):
        status,reasons=_classify(row)
        tags=row["tags"]
        scene=next((x for x in tags if x in ("scene:R","scene:A")),None)
        details.append({
            "task_id":row["task_id"],
            "operation":row["operation"],
            "category":row["category"],
            "target_class":row["target"]["entity_type"],
            "scene":scene,
            "engine_status":status,
            "reason_codes":list(reasons),
            "native_input_ifc_verified":False,
            "native_ground_truth_ifc_verified":False,
            "official_evaluator_run":False,
            "deterministic_official_oracle_run":False,
            "official_task_success":None,
        })
    statuses=Counter(t["engine_status"] for t in details)
    if len(details)!=324 or statuses[STATIC_UNSUPPORTED]+statuses[CONDITIONAL]!=324:
        raise AuditError("G1 ledger must account for exactly 324 tasks")
    return {
        "schema_version":"g1-08-metadata-only-v0.1",
        "public_task_record_sha256":TASK_SHA256,
        "metadata_validated_task_count":validated["record_count"],
        "strata":validated["num_strata"],
        "status":GATE_BLOCKED,
        "official_tasks_scored":0,
        "verified_official_engine_supported":0,
        "static_engine_unsupported_count":statuses[STATIC_UNSUPPORTED],
        "conditional_source_dependent_unverified_count":statuses[CONDITIONAL],
        "coverage_accounted_for":len(details),
        "official_pass_rate":None,
        "model_api_calls":0,
        "observations":{
            "G1_synthetic_manual_D0_I0_scenarios":6,
            "G1_oracle_separate_from_official_GT":True,
            "official_reference_scorer_completed":False,
            "full_324_input_and_GT_IFC_content_verified":False,
            "cross_arm_model_information_parity_completed":False,
            "full_six_class_editing_completed":False,
            "production_BIXML_or_Xim_touched":False,
        },
        "blocking_reasons":[
            "Official IFC input/GT corpus 324 task bytes not present and checked",
            "Official independent geometry/semantics/topology evaluator not yet validated",
            "Engine only supports strict wall/host/connection subset, not full six-class CRUD",
            "Matched observational context and runner safety gates G2 not yet complete",
        ],
        "tasks":details,
    }


def write_report(rows:list[dict],path:Path)->dict:
    report=generate_coverage_ledger(rows)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    return report
