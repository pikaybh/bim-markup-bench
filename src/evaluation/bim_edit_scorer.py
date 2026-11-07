"""Independent, IFC-native, grader-only synthetic BIM editing evaluator.

This is NOT the BIM-Edit official implementation. It follows the paper's
three-axis intent, but target pairing, surface sampling, property selection,
collateral penalty and graph empty-set rules are independent choices.

No XML, authoring CommandBus, generated Python, model provider or runtime
compiler API is ever accessed. The grader is deliberately blinded to arms.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from pathlib import Path
import re
from typing import Literal

import ifcopenshell
import ifcopenshell.util.unit
import numpy as np

from src.evaluation.geometry_metrics import (
    GeometrySettings,compare_surface_geometry,
    geometry_bbox_center,UnsupportedGeometry
)
from src.evaluation.semantic_diff import (
    product_by_guid,compare_target_semantics,collateral_change_audit
)
from src.evaluation.topology_metrics import compare_topology

SUPPORTED_CLASSES=frozenset({
    "IfcWall","IfcSlab","IfcSpace","IfcDoor","IfcWindow",
    "IfcColumn","IfcOpeningElement",
})
PROVENANCE="independent-reimplementation"
EVALUATOR_VERSION="independent-ifc-three-axis-v0.1"
STRICT_THRESHOLD=.98


@dataclass(frozen=True)
class GraderTask:
    task_id:str
    operation:Literal["create","update","delete"]
    target_class:str
    target_guids:tuple[str,...]

    def __post_init__(self):
        if not isinstance(self.task_id,str) or not self.task_id:
            raise ValueError("Invalid independent grader task")
        if self.operation not in ("create","update","delete"):
            raise ValueError("Unknown IFC task operation")
        if self.target_class not in SUPPORTED_CLASSES:
            raise ValueError("Unknown IFC target class")
        if type(self.target_guids) is not tuple or any(
            not isinstance(guid,str) or not re.fullmatch(r"[0-9A-Za-z_$]{22}",guid)
            for guid in self.target_guids
        ):
            raise ValueError("Grader-only targets must be a tuple of 22-character IFC GUIDs")
        if self.operation=="create" and self.target_guids:
            raise ValueError("Create task cannot contain a prior target GUID")
        if self.operation in ("update","delete") and len(self.target_guids)!=1:
            raise ValueError("Update/delete must have exactly one grader-only target GUID")


def _hash(path:Path)->str:
    h=sha256()
    with path.open("rb") as f:
        for buf in iter(lambda:f.read(1024*1024),b""):
            h.update(buf)
    return h.hexdigest()


def _base(task:GraderTask,source_sha:str|None,gt_sha:str|None,
          output_sha:str|None)->dict:
    return {
        "scorer_version":EVALUATOR_VERSION,
        "metric_origin":PROVENANCE,
        "official_bim_edit_evaluator_equivalent":False,
        "task_id":task.task_id,
        "operation":task.operation,
        "target_class":task.target_class,
        "source_ifc_sha256":source_sha,
        "ground_truth_ifc_sha256":gt_sha,
        "result_ifc_sha256":output_sha,
        "status":"BLOCKED_NOT_EVALUATED",
        "geometry":None,
        "semantics":None,
        "topology":None,
        "final_score":None,
        "strict_pass":False,
        "strict_threshold_per_axis":STRICT_THRESHOLD,
        "geometry_detail":None,
        "semantics_detail":None,
        "topology_detail":None,
        "collateral_detail":None,
        "target_matching_method":"UNRESOLVED",
        "confidence":"NOT_EVALUATED",
        "failure_codes":[],
        "model_provider_calls":0,
        "source_or_gt_mutated":False,
        "scored_official_dataset":False,
    }


def _abort(record:dict,status:str,code:str,
           *,invalid_candidate:bool=False)->dict:
    record["status"]=status
    record["failure_codes"]=[code]
    record["confidence"]="LOW"
    if invalid_candidate:
        record.update({
            "geometry":0.0,"semantics":0.0,"topology":0.0,
            "final_score":0.0,"strict_pass":False,
        })
    return record


def _validated_native_model(path:Path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Native IFC file missing/linked")
    # Fast STEP signature check first; avoid constructing a half-parsed native
    # IfcOpenShell wrapper for plainly invalid bytes on this pinned kernel.
    with path.open("rb") as fp:
        header=fp.read(96).lstrip(b" \r\n\t")
    if not header.startswith(b"ISO-10303-21;"):
        raise ValueError("Input does not begin with an IFC STEP-21 header")
    model=ifcopenshell.open(str(path))
    if model is None or not model.by_type("IfcProject"):
        raise ValueError("Native IFC project missing")
    if model.schema!="IFC4X3":
        raise ValueError("Current scorer requires IFC4X3")
    return model


def _one_expected_target(task:GraderTask,source,reference):
    source_objs=product_by_guid(source)
    ref_objs=product_by_guid(reference)
    if task.operation=="create":
        added=[x for guid,x in ref_objs.items()
               if guid not in source_objs and x.is_a()==task.target_class]
        if len(added)!=1:
            raise ValueError("Reference does not have exactly one new target of specified class")
        return added[0]
    guid=task.target_guids[0]
    source_target=source_objs.get(guid)
    if not source_target or source_target.is_a()!=task.target_class:
        raise ValueError("Grader-only target GUID/class not found in original model")
    gt_target=ref_objs.get(guid)
    if task.operation=="delete":
        if gt_target is not None:
            raise ValueError("Reference delete target remains in GT")
        return source_target
    if gt_target is None or gt_target.is_a()!=task.target_class:
        raise ValueError("Reference update target GUID/class unsupported")
    return gt_target


def _candidate_target(task:GraderTask,source,reference,output,gt_target):
    source_objs=product_by_guid(source)
    actual=product_by_guid(output)
    if task.operation!="create":
        target=actual.get(task.target_guids[0])
        return target,"SAME_SOURCE_GLOBAL_ID" if target else "TARGET_NOT_FOUND"
    gt_guid=gt_target.GlobalId
    if gt_guid in actual and gt_guid not in source_objs:
        return actual[gt_guid],"NEW_MATCHED_GLOBAL_ID"
    new=[x for guid,x in actual.items() if guid not in source_objs]
    if not new:
        return None,"NO_NEW_NATIVE_PRODUCT"
    try:
        expected_center=geometry_bbox_center(gt_target)
    except UnsupportedGeometry:
        return None,"UNSUPPORTED_TARGET_GEOMETRY"
    candidates=[]
    for item in new:
        try:
            center=geometry_bbox_center(item)
        except UnsupportedGeometry:
            continue
        candidates.append((float(np.linalg.norm(center-expected_center)),
                           item.GlobalId,item))
    if not candidates:
        return None,"NO_GEOMETRICALLY_OBSERVABLE_NEW_PRODUCT"
    candidates.sort(key=lambda pair:(pair[0],pair[1]))
    if len(candidates)>1 and abs(candidates[0][0]-candidates[1][0])<1e-6:
        return None,"AMBIGUOUS_NEW_TARGET_GEOMETRY"
    return candidates[0][2],"NEAREST_NEW_WORLD_GEOMETRY"


def _constrained_scores(geometry:float,semantics:float,
                        topology:float,collateral:dict,
                        failures:list[str])->dict:
    axes=(geometry,semantics,topology)
    if any(not math.isfinite(x) or x<0 or x>1 for x in axes):
        raise ValueError("Native IFC scoring produced invalid numeric component")
    strict=(all(score>=STRICT_THRESHOLD for score in axes)
            and collateral["collateral_clean"] and not failures)
    return {
        "geometry":geometry,"semantics":semantics,"topology":topology,
        "final_score":sum(axes)/3.,
        "strict_pass":strict,
    }


def score_ifc_result(
    *,
    source_ifc:Path,ground_truth_ifc:Path,result_ifc:Path,
    task:GraderTask,
    settings:GeometrySettings=GeometrySettings(),
)->dict:
    """Read-only, arm-blind, grader-only IFC triple comparison.

    A valid output may receive partial independent scores. Input/GT parse,
    target metadata, or unrepresented reference geometry failures instead
    return BLOCKED with null metrics, never a fake official score.
    """
    paths=(source_ifc,ground_truth_ifc,result_ifc)
    digests=[]
    for p in paths:
        try:
            digests.append(_hash(p) if p.is_file() and not p.is_symlink() else None)
        except OSError:
            digests.append(None)
    result=_base(task,*digests)
    try:
        source=_validated_native_model(source_ifc)
        gt=_validated_native_model(ground_truth_ifc)
    except Exception:
        return _abort(result,"BLOCKED_REFERENCE_IFC_INVALID",
                      "INPUT_OR_GT_NATIVE_IFC_INVALID")
    try:
        output=_validated_native_model(result_ifc)
    except Exception:
        return _abort(result,"INVALID_OUTPUT_IFC",
                      "PREDICTION_NOT_VALID_IFC4X3",invalid_candidate=True)

    # Unannounced IFC project-length unit changes are not a valid BIM edit
    # within this independent scorer's frozen source-project convention.
    try:
        scales=tuple(float(ifcopenshell.util.unit.calculate_unit_scale(model))
                     for model in (source,gt,output))
        if any(not math.isfinite(scale) or scale<=0 for scale in scales):
            raise ValueError("Nonfinite IFC project unit scale")
    except Exception:
        return _abort(result,"BLOCKED_IFC_UNIT_MISMATCH",
                      "UNSUPPORTED_IFC_LENGTH_UNIT_CONVENTION")
    if not math.isclose(scales[0],scales[1],abs_tol=1e-12,rel_tol=0.) or not math.isclose(
        scales[0],scales[2],abs_tol=1e-12,rel_tol=0.
    ):
        return _abort(result,"BLOCKED_IFC_UNIT_MISMATCH",
                      "PREDICTION_OR_REFERENCE_LENGTH_UNIT_CHANGED")

    try:
        target=_one_expected_target(task,source,gt)
        prediction,method=_candidate_target(task,source,gt,output,target)
    except (ValueError,UnsupportedGeometry):
        return _abort(result,"BLOCKED_UNSUPPORTED_REFERENCE_TASK",
                      "TARGET_NOT_UNIQUELY_DEFINED_OR_SUPPORTED")
    result["target_matching_method"]=method

    # Detect unsupported source geometry before matching candidates.
    if task.operation!="delete":
        try:
            from src.evaluation.geometry_metrics import triangle_mesh
            triangle_mesh(target)
        except UnsupportedGeometry:
            return _abort(result,"BLOCKED_REFERENCE_GEOMETRY_UNAVAILABLE",
                          "REFERENCE_TARGET_MESH_MISSING")

    failures=[]
    if task.operation=="delete":
        geometry=1.0 if prediction is None else 0.0
        semantics=geometry
        geo_detail={
            "score":geometry,
            "geometry_metric":"delete_source_global_id_absence_independent_v0.1",
            "mesh_sampling_used":False,
        }
        sem_detail={
            "score":semantics,
            "class_match":prediction is None,
            "properties_fraction":1.0 if prediction is None else 0.0,
            "matched_property_count":0,"reference_property_count":0,
        }
    else:
        sem_detail=compare_target_semantics(target,prediction)
        semantics=sem_detail["score"]
        if prediction is None:
            geometry=0.0
            geo_detail={
                "score":0.0,
                "geometry_metric":settings.metric_version,
                "mesh_sampling_used":False,
            }
            failures.append("TARGET_NOT_FOUND")
        else:
            try:
                geo_detail=compare_surface_geometry(target,prediction,settings)
                geometry=geo_detail["score"]
            except UnsupportedGeometry:
                geometry=0.0
                geo_detail={
                    "score":0.0,
                    "geometry_metric":settings.metric_version,
                    "mesh_sampling_used":False,
                }
                failures.append("OUTPUT_GEOMETRY_MISSING_OR_INVALID")
    aliases={}
    if task.operation=="create" and prediction is not None:
        if prediction.GlobalId!=target.GlobalId:
            aliases[prediction.GlobalId]=target.GlobalId
    topo_detail=compare_topology(source,gt,output,output_guid_aliases=aliases)
    topology=topo_detail["score"]
    collateral=collateral_change_audit(
        source,gt,output,
        reference_target_guid=target.GlobalId,
        prediction_target_guid=prediction.GlobalId if prediction else None,
    )
    if not collateral["collateral_clean"]:
        failures.append("UNEXPECTED_COLLATERAL_IFC_OBJECT_MUTATION")
        # Explicitly discourage perfect scores with collateral edits.
        semantics*=.5
    if geometry<STRICT_THRESHOLD:
        failures.append("TARGET_GEOMETRY_DIFFERENCE")
    if semantics<STRICT_THRESHOLD:
        failures.append("TARGET_SEMANTICS_DIFFERENCE")
    if topology<STRICT_THRESHOLD:
        failures.append("IFC_TOPOLOGY_DIFFERENCE")

    result.update(_constrained_scores(geometry,semantics,topology,collateral,failures))
    result.update({
        "status":"INDEPENDENT_IFC_SCORED",
        "geometry_detail":geo_detail,
        "semantics_detail":sem_detail,
        "topology_detail":topo_detail,
        "collateral_detail":collateral,
        "confidence":"BOUNDED_SYNTHETIC_IFC_ONLY",
        "failure_codes":sorted(set(failures)),
    })
    after=[]
    for p in paths:
        try:after.append(_hash(p))
        except OSError:after.append(None)
    if after!=digests:
        result["source_or_gt_mutated"]=True
        return _abort(result,"DATA_MUTATED_DURING_SCORING",
                      "IFC_INPUT_OR_RESULT_CONTENT_CHANGED")
    return result
