"""Independent, strictly scoped native IFC oracle for BIBIMBAP geometry_test_11.

Public task: decrease height of ALL walls on the SECOND storey by 0.5m.
This is a D0/independent IFC structural+mesh oracle, NOT the original author
grader and NOT a full 45-task validation suite. Native m input/output ONLY.

Independence: does not use the XML parser, compiler, mutation planner,
BIBIMBAP private original grader, or ground truth. Compares every serialized
STEP entity and every target wall's actual mesh bounding-box world Z span.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import json
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit

from tools.bibimbap_matched25_tools import file_hash

TARGET_METRES=0.5
EPS=0.0005

class OracleFailure(ValueError):
    pass

def check_close(value:float, expected:float,reason:str)->None:
    if not math.isclose(value,expected,rel_tol=0,abs_tol=EPS):
        raise OracleFailure(reason+f" (got {value:.8f}; expected {expected:.8f})")

def storey2(file:ifcopenshell.file):
    levels=file.by_type("IfcBuildingStorey")
    if len(levels)<2:
        raise OracleFailure("Input has fewer than two IFC building storeys")
    levels.sort(key=lambda obj:float(obj.Elevation if obj.Elevation is not None else -1e20))
    elevations=[float(x.Elevation) for x in levels]
    if any(not math.isfinite(x) for x in elevations) or len(elevations)!=len(set(elevations)):
        raise OracleFailure("Storeys have ambiguous/null/duplicate elevations")
    return levels[1]

def wall_solid(wall:ifcopenshell.entity_instance):
    if not wall.is_a("IfcWall"):
        raise OracleFailure("Nonwall passed to geometric verifier")
    rep=wall.Representation
    if rep is None:
        raise OracleFailure("Wall has no real IFC representation")
    solids=[item for r in rep.Representations for item in r.Items
            if item.is_a("IfcExtrudedAreaSolid")]
    if len(solids)!=1:
        raise OracleFailure("Wall body must have exactly one directly extruded solid")
    solid=solids[0]
    direction=tuple(float(x) for x in solid.ExtrudedDirection.DirectionRatios)
    if any(abs(a-b)>1e-8 for a,b in zip(direction,(0,0,1))):
        raise OracleFailure("Wall extrusion not in positive local height direction")
    return solid

def world_z_bbox(wall:ifcopenshell.entity_instance)->tuple[float,float]:
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        shape=ifcopenshell.geom.create_shape(settings,wall)
    except Exception as exc:
        raise OracleFailure("Native IFC wall mesh could not be created") from exc
    verts=shape.geometry.verts
    if len(verts)<18 or len(verts)%3:
        raise OracleFailure("Wall native mesh is absent/degenerate")
    z=verts[2::3]
    return min(z),max(z)

def independent_oracle(source:Path,candidate:Path,*,verify_mesh:bool=True)->dict:
    if not (source.is_file() and candidate.is_file()) or source.resolve()==candidate.resolve():
        raise OracleFailure("Source/result must be separate existing IFC files")
    before=ifcopenshell.open(str(source))
    after=ifcopenshell.open(str(candidate))
    if before.schema!="IFC4X3" or after.schema!=before.schema:
        raise OracleFailure("Both files must be real IFC4X3")
    before_scale=ifcopenshell.util.unit.calculate_unit_scale(before)
    after_scale=ifcopenshell.util.unit.calculate_unit_scale(after)
    check_close(before_scale,1.0,"Source units must be metres")
    check_close(after_scale,1.0,"Output units must be metres")

    target_storey=storey2(before)
    if storey2(after).GlobalId!=target_storey.GlobalId:
        raise OracleFailure("Second-storey GlobalId/elevation changed")
    old_walls=before.by_type("IfcWall")
    new_walls=after.by_type("IfcWall")
    old_by_guid={x.GlobalId:x for x in old_walls}
    new_by_guid={x.GlobalId:x for x in new_walls}
    if len(old_by_guid)!=len(old_walls) or set(old_by_guid)!=set(new_by_guid):
        raise OracleFailure("Wall identity inventory changed")
    target=[]
    for guid,w in old_by_guid.items():
        c=ifcopenshell.util.element.get_container(w)
        if c is not None and c.GlobalId==target_storey.GlobalId:
            target.append(guid)
    if not target:
        raise OracleFailure("No Wall objects in the second storey")
    if len(target)>=len(old_walls):
        raise OracleFailure("No non-target wall to audit for preservation")

    expected_step_changes=set()
    geom=[]
    for guid in sorted(target):
        old=old_by_guid[guid]
        new=new_by_guid[guid]
        oldsolid=wall_solid(old)
        newsolid=wall_solid(new)
        if oldsolid.id()!=newsolid.id():
            raise OracleFailure("Wall extrusion STEP ID changed")
        delta=float(oldsolid.Depth)-float(newsolid.Depth)
        check_close(delta,TARGET_METRES,"Wrong second-storey wall height reduction")
        if float(newsolid.Depth)<=0:
            raise OracleFailure("Negative/zero wall height")
        expected_step_changes.add(oldsolid.id())
        if verify_mesh:
            old_bbox=world_z_bbox(old)
            new_bbox=world_z_bbox(new)
            check_close(old_bbox[0],new_bbox[0],"Wall bottom moved during height-only edit")
            check_close(old_bbox[1]-new_bbox[1],TARGET_METRES,
                        "Native wall mesh top did not decrease by 0.5m")
            geom.append({"wall_guid":guid,"before_z_span_m":list(old_bbox),
                         "after_z_span_m":list(new_bbox),
                         "verified_top_drop_m":old_bbox[1]-new_bbox[1]})

    # Complete STEP-level non-target preservation, including unrepresented
    # IFC building objects, relations, properties and all other geometry.
    old_step={e.id():str(e) for e in before}
    new_step={e.id():str(e) for e in after}
    if set(old_step)!=set(new_step):
        raise OracleFailure("IFC STEP entity inventory added/deleted non-target objects")
    actual_changed={eid for eid in old_step if old_step[eid]!=new_step[eid]}
    if actual_changed!=expected_step_changes:
        raise OracleFailure(
            "Unexpected native STEP entity delta: "
            +str({"unexpected":sorted(actual_changed-expected_step_changes),
                  "missing":sorted(expected_step_changes-actual_changed)})
        )
    for eid in actual_changed:
        if not before.by_id(eid).is_a("IfcExtrudedAreaSolid") or not after.by_id(eid).is_a("IfcExtrudedAreaSolid"):
            raise OracleFailure("Non-extrusion entity modified")
    return {
        "status":"INDEPENDENT_IFC_NATIVE_6_WALL_HEIGHT_EDIT_VALIDATED",
        "metric_origin":"INDEPENDENT_TASK_SPECIFIC_IFC_STEP_AND_WORLD_MESH_ORACLE",
        "task_id":"geometry_test_11",
        "source_sha256":file_hash(source),
        "candidate_sha256":file_hash(candidate),
        "verified_second_storey_height_decrease_m":TARGET_METRES,
        "verified_modified_second_storey_walls":len(target),
        "verified_unchanged_non_target_walls":len(old_walls)-len(target),
        "step_entity_inventory_unchanged":True,
        "exact_step_changed_entity_count":len(actual_changed),
        "only_target_extrusions_modified":True,
        "native_world_mesh_each_target_verified":verify_mesh,
        "native_world_mesh_geometry_evidence":geom,
        "full_collision_and_building_topology_independently_verified":False,
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",required=True,type=Path)
    parser.add_argument("--candidate",required=True,type=Path)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    result=independent_oracle(args.source,args.candidate)
    if args.output_json:
        if args.output_json.exists():
            parser.error("Refuse to overwrite verification evidence")
        args.output_json.parent.mkdir(parents=True,exist_ok=True)
        with args.output_json.open("xb") as f:
            f.write((json.dumps(result,indent=2,sort_keys=True)+"\n").encode("utf8"))
    print(json.dumps({key:result[key] for key in (
        "status","verified_modified_second_storey_walls",
        "verified_unchanged_non_target_walls",
        "exact_step_changed_entity_count",
        "native_world_mesh_each_target_verified",
        "full_collision_and_building_topology_independently_verified",
    )},sort_keys=True))

if __name__=="__main__":
    main()
