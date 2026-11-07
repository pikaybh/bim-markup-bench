"""Grader-only synthetic scorer calibration / expected failure fixtures.

No generated Python, model API, official IFC GT or authoring XML is used.
All resulting IFC files live only in a caller-provided ephemeral scratch dir.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Callable

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.api.pset
import ifcopenshell.util.unit

from src.evaluation.bim_edit_scorer import GraderTask,score_ifc_result
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"tests/fixtures/synthetic/input.ifc"
WALL_GT=ROOT/"tests/fixtures/synthetic/expected_wall_height.ifc"
CATALOG=ROOT/"tests/evaluation/fixtures/calibration_expectations_v0.json"
WALL_GUID="2L_lrSH5fHAgIRV7tit5Pp"
WINDOW_GUID="0OpF3nUSXM4A74oRaddWtv"
FIRST_NEW_WALL="1UXHdOzirKMwnUzfD_y3ME"
SECOND_NEW_WALL="0atSxzNVbS9gi82DTpTUq9"


def _write_variant(source:Path,path:Path,change:Callable)->Path:
    if path.exists():
        raise ValueError("Calibration output must not overwrite a prior IFC")
    model=ifcopenshell.open(str(source))
    change(model)
    model.write(str(path))
    return path


def _wall_point(model):
    return model.by_guid(WALL_GUID).ObjectPlacement.RelativePlacement.Location


def _shift_wall(model,dx:float):
    p=_wall_point(model)
    x,y,z=tuple(float(x) for x in p.Coordinates)
    p.Coordinates=(x+dx,y,z)


def _rotate_wall(model,degrees:float):
    direction=model.by_guid(WALL_GUID).ObjectPlacement.RelativePlacement.RefDirection
    angle=math.radians(degrees)
    direction.DirectionRatios=(float(math.cos(angle)),float(math.sin(angle)),0.)


def _add_pset(model):
    wall=model.by_guid(WALL_GUID)
    pset=ifcopenshell.api.pset.add_pset(
        model,product=wall,name="Pset_WallCommon"
    )
    ifcopenshell.api.pset.edit_pset(
        model,pset=pset,
        properties={"FireRating":"REI 180","Reference":"Own synthetic fixture"}
    )


def _retype(model):
    ifcopenshell.api.root.reassign_class(
        model,product=model.by_guid(WALL_GUID),ifc_class="IfcSlab"
    )


def _remove_rel(model,name):
    relations=model.by_type(name)
    if not relations:
        raise ValueError("Calibration source lacks required native relation")
    model.remove(relations[0])


def _remove_door(model):
    door=model.by_type("IfcDoor")[0]
    ifcopenshell.api.root.remove_product(model,product=door)


def _change_column(model):
    column=model.by_type("IfcColumn")[0]
    point=column.ObjectPlacement.RelativePlacement.Location
    x,y,z=tuple(float(v) for v in point.Coordinates)
    point.Coordinates=(x+2.,y,z)


def _change_wall_guid(model):
    model.by_guid(WALL_GUID).GlobalId=FIRST_NEW_WALL


def _change_unit(model):
    length=[u for u in model.by_type("IfcSIUnit")
            if u.UnitType=="LENGTHUNIT"]
    if len(length)!=1:
        raise ValueError("One native SI length unit is required")
    length[0].Prefix="MILLI"


def build_calibration_artifacts(root:Path)->dict:
    """Create known IFC alternatives; do not return grader GT through model."""
    if root.exists() and any(root.iterdir()):
        raise ValueError("Calibration fixture directory must start empty")
    root.mkdir(parents=True,exist_ok=True)
    source_model=ifcopenshell.open(str(SRC))
    storey=source_model.by_type("IfcBuildingStorey")[0].GlobalId
    files={"wall_gt":WALL_GT,"source_unchanged":SRC}
    recipes={
        "wall_translate":(WALL_GT,lambda m:_shift_wall(m,1.0)),
        "wall_rotate":(WALL_GT,lambda m:_rotate_wall(m,45.)),
        "wall_retype":(WALL_GT,_retype),
        "remove_void":(WALL_GT,lambda m:_remove_rel(m,"IfcRelVoidsElement")),
        "remove_space_boundary":(WALL_GT,
                                 lambda m:_remove_rel(m,"IfcRelSpaceBoundary")),
        "delete_door":(WALL_GT,_remove_door),
        "change_column_only":(SRC,_change_column),
        "change_wall_guid":(WALL_GT,_change_wall_guid),
        "change_length_units":(WALL_GT,_change_unit),
    }
    for label,(input_path,change) in recipes.items():
        files[label]=_write_variant(input_path,root/(label+".ifc"),change)
    files["wall_pset_gt"]=_write_variant(
        WALL_GT,root/"reference_wall_with_pset.ifc",_add_pset)
    files["invalid_ifc"]=root/"invalid_candidate.ifc"
    files["invalid_ifc"].write_bytes(b"not IFC content")
    files["create_gt"]=root/"created_wall_gt.ifc"
    manual_ifc_reference(SRC,files["create_gt"],"CREATE_WALL",
                         new_guid=FIRST_NEW_WALL,storey_guid=storey)
    files["create_different_guid"]=root/"created_wall_prediction.ifc"
    manual_ifc_reference(SRC,files["create_different_guid"],"CREATE_WALL",
                         new_guid=SECOND_NEW_WALL,storey_guid=storey)
    files["delete_window"]=root/"window_deleted_gt.ifc"
    manual_ifc_reference(SRC,files["delete_window"],"DELETE_WINDOW",
                         target_guid=WINDOW_GUID)
    return files


def _grading_task(task_key:str)->GraderTask:
    options={
        "wall_update":GraderTask(
            "OWN-CAL-WALL-UPDATE","update","IfcWall",(WALL_GUID,)
        ),
        "wall_pset":GraderTask(
            "OWN-CAL-WALL-PSET","update","IfcWall",(WALL_GUID,)
        ),
        "wall_create":GraderTask(
            "OWN-CAL-WALL-CREATE","create","IfcWall",()
        ),
        "window_delete":GraderTask(
            "OWN-CAL-WINDOW-DELETE","delete","IfcWindow",(WINDOW_GUID,)
        ),
    }
    if task_key not in options:
        raise ValueError("Unexpected frozen calibration task")
    return options[task_key]


def calibrate_own_synthetic(root:Path)->dict:
    """Verify all predeclared predicates, not merely a model score >=0.98."""
    catalog=json.loads(CATALOG.read_text(encoding="utf-8"))
    files=build_calibration_artifacts(root)
    results=[]
    for case in catalog["cases"]:
        reference={
            "wall_update":files["wall_gt"],
            "wall_pset":files["wall_pset_gt"],
            "wall_create":files["create_gt"],
            "window_delete":files["delete_window"],
        }[case["task"]]
        prediction=files[case["condition"]]
        task=_grading_task(case["task"])
        value=score_ifc_result(
            source_ifc=SRC,ground_truth_ifc=reference,
            result_ifc=prediction,task=task)
        axes={name:value[name] for name in ("geometry","semantics","topology")}
        expected_axes=set(case["expected_failed_axes"])
        if value["status"]=="INDEPENDENT_IFC_SCORED":
            failed_axes={name for name,v in axes.items() if v is not None and v<.98}
        elif value["status"]=="INVALID_OUTPUT_IFC":
            failed_axes=set(axes)
        else:
            # A blocked case must not invent numeric axis values.
            if any(score is not None for score in axes.values()):
                raise AssertionError("Reference/units block produced fake numeric score")
            failed_axes=set()
        checks={
            "expected_status":value["status"]==case["status"],
            "expected_strict":value["strict_pass"]==case["strict_pass"],
            "expected_failed_axes_included":expected_axes<=failed_axes,
            "collateral_expected":(
                not case.get("requires_collateral",False) or (
                    value.get("collateral_detail") is not None and
                    value["collateral_detail"]["collateral_changed_count"]>=1
                )
            ),
            "independent_provenance":
                value["metric_origin"]=="independent-reimplementation",
            "not_official":value["official_bim_edit_evaluator_equivalent"] is False,
            "no_model_calls":value["model_provider_calls"]==0,
        }
        result={
            "case_id":case["id"],"task":case["task"],
            "condition":case["condition"],
            "status":value["status"],
            "geometry":value["geometry"],"semantics":value["semantics"],
            "topology":value["topology"],
            "strict_pass":value["strict_pass"],
            "failure_codes":value["failure_codes"],
            "checks":checks,
            "all_expected_properties_pass":all(checks.values()),
        }
        results.append(result)
    passing=sum(int(r["all_expected_properties_pass"]) for r in results)
    return {
        "version":catalog["version"],
        "metric_origin":"independent-reimplementation",
        "official_paper_score_reproduced":False,
        "official_dataset_cases_scored":0,
        "evaluated_own_synthetic_cases":len(results),
        "synthetic_cases_matching_frozen_expectations":passing,
        "synthetic_detection_ratio":passing/len(results),
        "all_frozen_expectations_pass":passing==len(results),
        "model_provider_calls":0,
        "cases":results,
    }


def tolerance_sensitivity(root:Path)->dict:
    """Evaluate geometric sensitivity, never fit tuning parameters to outputs."""
    if not root.is_dir():
        raise ValueError("Calibration sensitivity root must exist")
    task=_grading_task("wall_update")
    distances=(0.,1e-7,1e-4,1e-2,.1,.5,1.)
    translations=[]
    for idx,d in enumerate(distances):
        prediction=_write_variant(
            WALL_GT,root/("translation_sensitivity_"+str(idx)+".ifc"),
            lambda model,dx=d:_shift_wall(model,dx)
        )
        score=score_ifc_result(
            source_ifc=SRC,ground_truth_ifc=WALL_GT,
            result_ifc=prediction,task=task)
        translations.append({
            "translation_m":d,"geometry":score["geometry"],
            "strict_pass":score["strict_pass"],
        })
    rotation_degrees=(0.,15.,45.,90.)
    rotations=[]
    for idx,angle in enumerate(rotation_degrees):
        prediction=_write_variant(
            WALL_GT,root/("rotation_sensitivity_"+str(idx)+".ifc"),
            lambda model,a=angle:_rotate_wall(model,a)
        )
        score=score_ifc_result(
            source_ifc=SRC,ground_truth_ifc=WALL_GT,
            result_ifc=prediction,task=task)
        rotations.append({
            "rotation_degrees":angle,"geometry":score["geometry"],
            "strict_pass":score["strict_pass"],
        })
    return {
        "metric_version":"independent-ifc-surface-cd-v0.1",
        "reported_world_units":"m",
        "input_source_IFC_unit":"METRE",
        "sample_points":384,
        "sampling_seed":2607,
        "translation":translations,
        "rotation":rotations,
        "official_calibration_available":False,
    }
