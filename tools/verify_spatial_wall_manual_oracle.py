"""G1 #14: trusted source-only spatial Wall creation *manual* D0/I0 ceiling.

This module is NOT mounted to either future LLM agent. Reads the fixed
public instruction and its verified INPUT IFC only, NEVER a GT IFC/target
annotation/official grader. Computes one conservative geometry hypothesis.
It may prove D0/I0 *execution parity*; it cannot establish benchmark success
or fairness while the referenced room remains opaque in the XML view.
"""
from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import uuid

import ifcopenshell
import ifcopenshell.geom
import numpy as np
from lxml import etree

from src.data.bim_edit import read_tasks,repo_asset_path,verify_local_asset_bytes
from src.data.pilot_asset_audit import _files_in_root
from src.runtime.compiler import compile_declarative_xml
from src.runtime.ifc_projection import project_ifc
from src.runtime.topology_ops import native_topology_inventory
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference
from tests.oracles.python.independent_ifc_checker import parity_report

ROOT=Path(__file__).resolve().parents[1]
CASE="WAL-CRE-SPA-A-003"
XML_NAMESPACE="urn:bim-markup-bench:toy:v0"
ID_NAMESPACE=uuid.UUID("9218e3de-9b55-4960-b9b0-e4dddf796ebd")
LOCAL_ID="g1_spatial_wall_oracle"


def _world_bounds(element)->tuple[np.ndarray,np.ndarray]:
    options=ifcopenshell.geom.settings()
    options.set(options.USE_WORLD_COORDS,True)
    # The native SWIG geometry depends on retaining the shape wrapper.
    shape=ifcopenshell.geom.create_shape(options,element)
    xyz=np.asarray(shape.geometry.verts,dtype=np.float64).reshape(-1,3)
    if len(xyz)<4 or not np.isfinite(xyz).all():
        raise ValueError("Nonfinite or empty native IFC geometry in prompt context")
    return xyz.min(axis=0),xyz.max(axis=0)


def _geometry_from_public_instruction(task:dict,model,projection)->dict:
    instruction=task["prompt"]
    refs=re.findall(r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",instruction)
    if len(refs)!=3 or len(set(refs))!=3:
        raise ValueError("Unsupported or ambiguous native IFC reference count")
    try:
        entities=[model.by_guid(key) for key in refs]
    except RuntimeError as exc:
        raise ValueError("Prompt references an absent native IFC entity") from exc
    if any(entity is None for entity in entities):
        raise ValueError("Prompt references an absent native IFC entity")
    first,second,room_guid=entities
    if not first.is_a("IfcWall") or not second.is_a("IfcWall") or not room_guid.is_a("IfcSpace"):
        raise ValueError("Prompt IFC reference types do not match fixed constraints")
    doors=model.by_type("IfcDoor")
    if len(doors)!=1 or not doors[0].FillsVoids:
        raise ValueError("No single native Door to resolve prompt viewpoint")
    door=doors[0]
    opening=door.FillsVoids[0].RelatingOpeningElement
    if not opening.VoidsElements or opening.VoidsElements[0].RelatingBuildingElement.GlobalId not in set(refs[:2]):
        raise ValueError("Door is not hosted by the referenced pair of walls")
    # IFC space bounds are used as a read-only cue, not silently regenerated.
    if not any(r.RelatedBuildingElement and r.RelatedBuildingElement.GlobalId in refs[:2]
               for r in room_guid.BoundedBy):
        raise ValueError("Prompt room has no physical boundary on the referenced wall")

    values=re.search(
        r"at ([0-9]+(?:\.[0-9]+)?)m in \+y direction.*?"
        r"thickness of ([0-9]+(?:\.[0-9]+)?)m.*?"
        r"height of ([0-9]+(?:\.[0-9]+)?)m",
        instruction,re.IGNORECASE|re.DOTALL)
    if values is None:
        raise ValueError("Cannot bind fixed task quantities independently of GT")
    distance,thickness,height=(Decimal(text) for text in values.groups())
    if distance<=0 or thickness<=0 or height<=0:
        raise ValueError("Invalid task dimensions")

    xbounds=sorted((_world_bounds(first),_world_bounds(second)),
                   key=lambda bounds:float(bounds[0][0]))
    left,right=xbounds
    room_min,room_max=_world_bounds(room_guid)
    door_min,door_max=_world_bounds(door)

    # Both walls are Y-aligned, form opposite Room sides and enclose its
    # interior. Validate native geometry: do NOT infer from public GT.
    small=1e-5
    if not (
        abs(float(left[1][0]-room_min[0]))<small
        and abs(float(right[0][0]-room_max[0]))<small
        and float(left[1][0])<float(right[0][0])
        and float(room_max[0])<float(door_min[0]+door_max[0])/2
        and float(room_min[1])<float(door_min[1])<float(room_max[1])
    ):
        raise ValueError("Room/wall/Door viewpoint geometry is not uniquely supported")
    if not (
        float(left[1][1]-left[0][1])>2.0 and
        float(right[1][1]-right[0][1])>2.0 and
        float(left[1][0]-left[0][0])<1.0 and
        float(right[1][0]-right[0][0])<1.0
    ):
        raise ValueError("Referenced walls are not parallel along world Y")

    # Interior looks east to this Door: its right-hand jamb is world -Y.
    # The task requires 1.3025m measured +Y *from that jamb*, rather
    # than adding to placement origin or interpreting right as world +Y.
    y=Decimal(str(float(door_min[1])))+distance
    x_start=Decimal(str(float(left[1][0])))
    x_end=Decimal(str(float(right[0][0])))
    z=Decimal(str(float(room_min[2])))
    if not (x_end>x_start and
            float(y)>=float(room_min[1])+small and
            float(y+thickness)<=float(room_max[1])-small and
            float(z+height)<=float(room_max[2])+small):
        raise ValueError("Proposed wall would not fit native room interior")
    storeys=[
        [rel.RelatingStructure for rel in obj.ContainedInStructure]
        for obj in (first,second)
    ]
    if not all(len(x)==1 and x[0].is_a("IfcBuildingStorey") for x in storeys):
        raise ValueError("Unique native storey containment not established")
    if storeys[0][0].GlobalId!=storeys[1][0].GlobalId:
        raise ValueError("Reference walls cross storeys")
    storey=storeys[0][0]
    mapped=dict(projection.projected_global_ids)
    if not all(x in mapped for x in (first.GlobalId,second.GlobalId,door.GlobalId,storey.GlobalId)):
        raise ValueError("Reference walls/Door/storey not represented in direct XML")

    return {
        "start":(x_start,y,z),
        "end":(x_end,y,z),
        "height":height,
        "thickness":thickness,
        "storey_guid":storey.GlobalId,
        "storey_local_id":mapped[storey.GlobalId],
        "prompt_room_visible_in_xml":room_guid.GlobalId in mapped,
        "door_side_identification":"WEST_OF_DOOR_LOOK_EAST_RIGHT_HAND_WORLD_MINUS_Y",
    }


def _check_existing_native_relations_preserved(
    original:dict[str,tuple], current:dict[str,tuple],
    *,new_wall_guid:str,storey_guid:str,
)->dict:
    """Only adding the new wall to its storey may modify native topology.

    A standalone physical wall does not imply correctly synthesized joins or
    space boundaries. We verify no existing reference graph is damaged, not
    that the full task's missing relationships are implemented.
    """
    if set(original)-set(current):
        raise ValueError("A native IFC relationship was deleted")
    containment_updates=0
    for rel_guid,prior in original.items():
        later=current[rel_guid]
        if prior==later:
            continue
        cls,lhs,rhs=prior
        expected=(cls,lhs,tuple(sorted(set(rhs)|{new_wall_guid})))
        if (cls!="IfcRelContainedInSpatialStructure"
                or lhs!=(storey_guid,)
                or later!=expected):
            raise ValueError("Unrelated native IFC relationship endpoints changed")
        containment_updates+=1
    for rel_guid in set(current)-set(original):
        cls,lhs,rhs=current[rel_guid]
        if (cls!="IfcRelContainedInSpatialStructure"
                or lhs!=(storey_guid,)
                or rhs!=(new_wall_guid,)):
            raise ValueError("Unexpected native IFC relationship created")
        containment_updates+=1
    if containment_updates!=1:
        raise ValueError("Expected exactly one new-wall storey containment update")
    return {"original_native_relations_preserved":True,
            "new_wall_storey_containment_updates":containment_updates}


def verify_one_spatial_wall_ceiling()->dict:
    tasks={row["task_id"]:row for row in read_tasks(ROOT/"data/tasks.jsonl")}
    fixed=json.loads((ROOT/"manifests/pilot_36_candidate_v0.json").read_text(encoding="utf-8"))
    if len(fixed["tasks"])!=36 or CASE not in {x["task_id"] for x in fixed["tasks"]}:
        raise ValueError("Spatial test case is not part of frozen 36 candidate")
    task=tasks[CASE]
    name=repo_asset_path(task["input_ifc"])
    source=_files_in_root(ROOT/"data/ifc",name)
    metadata=json.loads((ROOT/"data/bim_edit_remote_tree.json").read_text(encoding="utf-8"))
    remote={row["path"]:row for row in metadata if row.get("type")=="file"}
    verify_local_asset_bytes(source,remote[name])
    before_sha=hashlib.sha256(source.read_bytes()).hexdigest()

    model=ifcopenshell.open(str(source))
    projected=project_ifc(source)
    geometry=_geometry_from_public_instruction(task,model,projected)
    original_rels=native_topology_inventory(model)
    source_roots={obj.GlobalId for obj in model.by_type("IfcRoot")}
    xml=etree.fromstring(projected.xml)
    elements=xml.find(".//{"+XML_NAMESPACE+"}Elements")
    if elements is None or any(element.get("id")==LOCAL_ID for element in elements):
        raise ValueError("XML elements missing or frozen local ID already used")
    attrs={
        "id":LOCAL_ID,
        "level":geometry["storey_local_id"],
        "x1":str(geometry["start"][0]),
        "y1":str(geometry["start"][1]),
        "z1":str(geometry["start"][2]),
        "x2":str(geometry["end"][0]),
        "y2":str(geometry["end"][1]),
        "z2":str(geometry["end"][2]),
        "height":str(geometry["height"]),
        "thickness":str(geometry["thickness"]),
    }
    etree.SubElement(elements,"{"+XML_NAMESPACE+"}Wall",attrs)
    edited=etree.tostring(xml,encoding="utf-8",xml_declaration=True)
    guid_name=f"bim-markup-v0.1:{before_sha}:IfcWall:{LOCAL_ID}"
    new_guid=ifcopenshell.guid.compress(uuid.uuid5(ID_NAMESPACE,guid_name).hex)

    with TemporaryDirectory(prefix="g1_spatial_manual_input_only_") as temp:
        folder=Path(temp)
        d0=folder/"D0.ifc"
        i0=folder/"I0.ifc"
        direct=compile_declarative_xml(source,edited,d0)
        if [op.operation for op in direct.operations]!=["CREATE_WALL"]:
            raise ValueError("Expected only one declaratively created IFC Wall")
        manual_ifc_reference(
            source,i0,"CREATE_WALL",
            new_guid=new_guid,storey_guid=geometry["storey_guid"],
            start=tuple(float(x) for x in geometry["start"]),
            end=tuple(float(x) for x in geometry["end"]),
            height=float(geometry["height"]),
            thickness=float(geometry["thickness"]),
        )
        comparison=parity_report(d0,i0)
        if not comparison["parity"]:
            raise ValueError("Independent IFC observations differ on fixed input")
        d=ifcopenshell.open(str(d0))
        i=ifcopenshell.open(str(i0))
        if d.by_guid(new_guid) is None or i.by_guid(new_guid) is None:
            raise ValueError("Expected new native Wall GUID not created in both arms")
        if {r.GlobalId for r in d.by_type("IfcRoot")}-source_roots!={new_guid}:
            # A new storey container relationship may be added by IFC API,
            # but any such relationship must match the independent baseline.
            new_roots={r.GlobalId for r in d.by_type("IfcRoot")}-source_roots
            if not new_roots.issuperset({new_guid}) or len(new_roots)>2:
                raise ValueError("Unexpected unrelated native IFC root changes")
        dmin,dmax=_world_bounds(d.by_guid(new_guid))
        expected_min=np.array([float(geometry["start"][0]),
                               float(geometry["start"][1]),
                               float(geometry["start"][2])])
        expected_max=np.array([float(geometry["end"][0]),
                               float(geometry["end"][1]+geometry["thickness"]),
                               float(geometry["start"][2]+geometry["height"])])
        if not np.allclose(dmin,expected_min,atol=1e-6) or not np.allclose(dmax,expected_max,atol=1e-6):
            raise ValueError("Native Wall geometry does not match source-only geometric bound")
        if direct.unexpected_root_changes:
            raise ValueError("Unapproved IFC root mutation detected")
        new_wall=d.by_guid(new_guid)
        if not new_wall.ContainedInStructure or len(new_wall.ContainedInStructure)!=1:
            raise ValueError("New IFC Wall is missing storey containment")
        topology=_check_existing_native_relations_preserved(
            original_rels,native_topology_inventory(d),
            new_wall_guid=new_guid,storey_guid=geometry["storey_guid"])
        new_wall_inverses=d.get_inverse(new_wall)
        native_connects=sum(x.is_a("IfcRelConnectsElements") for x in new_wall_inverses)
        native_space_boundaries=sum(x.is_a("IfcRelSpaceBoundary") for x in new_wall_inverses)
        dsha=hashlib.sha256(d0.read_bytes()).hexdigest()
        isha=hashlib.sha256(i0.read_bytes()).hexdigest()

    if hashlib.sha256(source.read_bytes()).hexdigest()!=before_sha:
        raise ValueError("Frozen public input IFC was modified")
    return {
        "status":"BLOCKED_FULL_TASK_TOPOLOGY_ORACLE_PENDING_AFTER_MANUAL_GEOMETRY_PARITY_PASS",
        "task_id":CASE,
        "source_sha256":before_sha,
        "D0_sha256":dsha,
        "I0_sha256":isha,
        "full_file_sha_equal":dsha==isha,
        "native_IFC_parity":True,
        "new_wall_bbox_min_m":[round(float(x),6) for x in dmin],
        "new_wall_bbox_max_m":[round(float(x),6) for x in dmax],
        "new_wall_storey_containment_verified":True,
        "existing_native_relations_preserved":topology["original_native_relations_preserved"],
        "new_wall_storey_containment_updates":topology["new_wall_storey_containment_updates"],
        "new_wall_native_connects_count":native_connects,
        "new_wall_native_space_boundary_count":native_space_boundaries,
        "native_source_relation_inventory_count":len(original_rels),
        "prompt_room_visible_in_direct_markup":geometry["prompt_room_visible_in_xml"],
        "critical_room_geometry_visible_in_xml":geometry["prompt_room_visible_in_xml"],
        "all_input_information_equivalence_proven":False,
        "space_boundary_reconstruction_verified":False,
        "this_is_an_approved_full_task_oracle":False,
        "manually_resolved_public_prompt_geometry":True,
        "GT_loaded":False,
        "official_scores":0,
        "LLM_provider_calls":0,
        "new_IFC_files_committed":False,
        "fixed_task_sample_modified":False,
    }


def main()->int:
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    evidence=verify_one_spatial_wall_ceiling()
    if args.output_json:
        output=args.output_json
        if output.exists() or output.is_symlink() or not output.parent.is_dir():
            parser.error("Refuse overwrite, symlink or absent parent")
        with output.open("x",encoding="utf8",newline="\n") as f:
            f.write(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True))
    # IMPORTANT: the manual geometry pair is NOT a complete task oracle.
    # Topology semantics and information parity are still unverified.
    return 2 if not evidence["this_is_an_approved_full_task_oracle"] else 0


if __name__=="__main__":
    raise SystemExit(main())
