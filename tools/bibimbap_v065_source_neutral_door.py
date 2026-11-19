"""v0.65 LOCAL source-neutral native hosted-Door feasibility prototype.

Same source-independent declarative grammar and post-edit native CSG gate
for two exposed IFC2X3 and IFC4X3 source models. No task ID, author
scorer, target GUID, fixed wall counts, source filename, or answers in
this module. This is an offline experimental scope check only, NOT
permission to launch trials, NOT a universal IFC compiler.

The "whole" and "managed" modes carry complete original Wall rosters and
an absolute 1-Door+1-Opening final physical state. Limited family:
axis-aligned planar IFC Walls with represented solids, hosted opening
and one door in same original storey. No unrelated authoring styles or
replacements/deletions. No geometric target success predicate here.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import math

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.api.geometry
import ifcopenshell.api.feature
import ifcopenshell.geom
import ifcopenshell.util.unit
from lxml import etree
import numpy as np

from src.security.agent_boundary import check_xml_bytes
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v055_production_schema_gate import _schema_error_counter
from tools.bibimbap_v060_geometry19_native import _native_entity_signature_v060
from tools.bibimbap_v063_exterior_door_native import (
    _mesh_bounds,_volume,_bbox_attrs,_valid_guid,_near_bbox,
)

NS="urn:bim-markup-bench:source-neutral:v065"
Q="{"+NS+"}"
MAX_XML_BYTES=200000
MAX_MANAGED_BYTES=90000
BBOX_KEYS=("minXM","maxXM","minYM","maxYM","minZM","maxZM")
ROOT_CLASSES=sorted((
    "IfcDoor","IfcOpeningElement","IfcRelFillsElement",
    "IfcRelVoidsElement","IfcRelContainedInSpatialStructure",
))
STATUS="V065_SOURCE_NEUTRAL_TWO_SCHEMA_NATIVE_HOSTED_DOOR_SCOPE_PASS"


class NeutralDoor065Error(ValueError):
    pass


def require(test,reason):
    if not test:raise NeutralDoor065Error(reason)


def xml_parser():
    return etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,huge_tree=False,recover=False)


def source_model(source:Path,sha:str):
    src=Path(source)
    require(len(sha)==64 and src.is_file() and not src.is_symlink()
            and file_hash(src)==sha,
            "SHA-bound original source native IFC missing/changed")
    model=ifcopenshell.open(str(src))
    require(model.schema in ("IFC2X3","IFC4X3"),
            "Source-neutral prototype only supports IFC2X3 and IFC4X3")
    scale=ifcopenshell.util.unit.calculate_unit_scale(model)
    require(scale in (1.,.001),
            "Unsupported native LENGTHUNIT, source world conversion blocked")
    require(len(model.by_type("IfcWall"))>=1
            and len(model.by_type("IfcBuildingStorey"))>=1,
            "Source must contain represented Walls and existing storey")
    return model


def _source_products(model):
    return sorted(model.by_type("IfcProduct"),key=lambda x:x.GlobalId)


def _box_attrs(box):
    flat=(box[0][0],box[0][1],box[1][0],box[1][1],
          box[2][0],box[2][1])
    return {key:f"{float(value):.6f}" for key,value in zip(BBOX_KEYS,flat)}


def _absolute_box(element):
    require(set(element.attrib).issuperset(BBOX_KEYS),
            "Explicit final object world 3D box required")
    coords=[]
    for key in BBOX_KEYS:
        raw=element.get(key)
        try:v=float(raw)
        except (TypeError,ValueError):
            raise NeutralDoor065Error("Invalid world 3D coordinate") from None
        require(math.isfinite(v) and abs(v)<=1000
                and raw==f"{v:.6f}",
                "Canonical finite six-decimal world metre coordinate required")
        coords.append(v)
    box=((coords[0],coords[1]),(coords[2],coords[3]),
         (coords[4],coords[5]))
    require(all(b-a>1e-5 for a,b in box),
            "Nonempty final geometry")
    return box


def horizontal_wall_axis_and_box(wall):
    require(wall.is_a("IfcWall") and wall.Representation is not None,
            "A real represented native IFC Wall is required")
    box=_mesh_bounds(wall)
    x=box[0][1]-box[0][0]
    y=box[1][1]-box[1][0]
    axis="X" if x>=y else "Y"
    span=max(x,y)
    thick=min(x,y)
    require(.05<=thick<=1. and span>=thick*2.5,
            "Axis-aligned source Wall planar thickness/span unsupported")
    return axis,box


def _wall_roster(model):
    return sorted(w.GlobalId for w in model.by_type("IfcWall"))


def full_initial_xml(source:Path,sha:str)->bytes:
    model=source_model(source,sha)
    root=etree.Element(Q+"BuildingState",nsmap={None:NS},attrib={
        "version":"0.65",
        "representation":"FULL_FINAL_SOURCE_NEUTRAL_HOSTED_DOOR",
        "sourceIFCSha256":sha,
        "schema":model.schema,
        "nativeLengthUnitSI":f"{ifcopenshell.util.unit.calculate_unit_scale(model):.6f}",
        "worldMeshLengthUnit":"metre",
        "supportedEditFamily":"ONE_HOSTED_IFCDOOR_AND_ONE_OPENING",
    })
    immutable=etree.SubElement(root,Q+"ImmutableNativeSource",{
        "sha256":sha,
        "sourceRootCount":str(len(model.by_type("IfcRoot"))),
        "sourceWallCount":str(len(model.by_type("IfcWall"))),
    })
    products=etree.SubElement(immutable,Q+"OriginalProducts")
    for p in _source_products(model):
        attrs={"guid":p.GlobalId,"ifcClass":p.is_a(),
               "name":str(p.Name or "")}
        if p.Representation:
            attrs.update(_box_attrs(_mesh_bounds(p)))
        if p.is_a("IfcWall"):
            attrs["sourceAxis"]=horizontal_wall_axis_and_box(p)[0]
        etree.SubElement(products,Q+"Product",attrs)
    walls=etree.SubElement(root,Q+"FinalExistingWalls",{
        "complete":"all-original-walls"})
    for guid in _wall_roster(model):
        etree.SubElement(walls,Q+"Wall",{
            "guid":guid,"present":"true"})
    etree.SubElement(root,Q+"FinalNewProducts",{
        "boundary":"EXACTLY_ONE_DOOR_ONE_OPENING"})
    buf=etree.tostring(root,encoding="utf8",xml_declaration=True)
    require(0<len(buf)<=MAX_XML_BYTES,"Original building XML too large")
    return buf


def managed_initial_xml(source:Path,sha:str)->bytes:
    full=full_initial_xml(source,sha)
    original=etree.fromstring(full,xml_parser())
    root=etree.Element(Q+"ManagedFinalState",nsmap={None:NS},attrib={
        "version":"0.65","representation":"MANAGED_FINAL_SOURCE_NEUTRAL_HOSTED_DOOR",
        "sourceIFCSha256":sha,
        "sourceFullBuildingStateSha256":sha256(full).hexdigest(),
    })
    walls=etree.SubElement(root,Q+"FinalExistingWalls",dict(original[1].attrib))
    for wall in original[1]:
        etree.SubElement(walls,Q+"Wall",dict(wall.attrib))
    etree.SubElement(root,Q+"FinalNewProducts",dict(original[2].attrib))
    buf=etree.tostring(root,encoding="utf8",xml_declaration=True)
    require(0<len(buf)<=MAX_MANAGED_BYTES,"Managed XML too large")
    return buf


def _final_products(model,walls,new):
    require(walls.tag==Q+"FinalExistingWalls"
            and dict(walls.attrib)=={"complete":"all-original-walls"}
            and [x.tag for x in walls]==[Q+"Wall"]*len(_wall_roster(model))
            and [(x.get("guid"),x.get("present")) for x in walls]
                ==[(g,"true") for g in _wall_roster(model)]
            and all(set(x.attrib)=={"guid","present"} and len(x)==0
                    for x in walls)
            and not (walls.text or "").strip(),
            "Every original source Wall must appear in complete final roster")
    require(new.tag==Q+"FinalNewProducts"
            and dict(new.attrib)=={"boundary":"EXACTLY_ONE_DOOR_ONE_OPENING"}
            and len(new)==2
            and not (new.text or "").strip()
            and not (new.tail or "").strip(),
            "One fully declared new Opening plus Door required")
    opening,door=list(new)
    require(opening.tag==Q+"Opening"
            and door.tag==Q+"Door"
            and set(opening.attrib)==set(BBOX_KEYS)|{"guid","hostOriginalWallGuid"}
            and set(door.attrib)==set(BBOX_KEYS)|{"guid","fillsOpeningGuid"}
            and not len(opening) and not len(door)
            and not (opening.text or "").strip()
            and not (door.text or "").strip(),
            "Complete original IFC final Door/Opening geometry and refs required")
    used={root.GlobalId for root in model.by_type("IfcRoot")}
    _valid_guid(opening.get("guid"),used)
    _valid_guid(door.get("guid"),used)
    require(door.get("fillsOpeningGuid")==opening.get("guid"),
            "Explicit complete Door->Opening fill required")
    host=model.by_guid(opening.get("hostOriginalWallGuid"))
    require(host is not None and host.is_a("IfcWall"),
            "Source-existing host Wall GUID not found")
    axis,box=horizontal_wall_axis_and_box(host)
    ob=_absolute_box(opening)
    db=_absolute_box(door)
    k=0 if axis=="X" else 1
    t=1-k
    for n in range(3):
        require(db[n][0]>=ob[n][0]-1e-4
                and db[n][1]<=ob[n][1]+1e-4,
                "Door must be contained inside its hosted Opening solid")
    width=db[k][1]-db[k][0]
    height=db[2][1]-db[2][0]
    thickness=db[t][1]-db[t][0]
    ow=ob[k][1]-ob[k][0]
    oh=ob[2][1]-ob[2][0]
    require(.3<=width<=2. and 1.<=height<=3.5
            and .015<=thickness<=.15
            and width<ow<=width+.5
            and height<oh<=height+.5,
            "Bounded new Door world solid geometry family unsupported")
    require(ob[t][0]<box[t][0]-.025
            and ob[t][1]>box[t][1]+.025
            and ob[k][0]>box[k][0]+.15
            and ob[k][1]<box[k][1]-.15,
            "Opening must pass BOTH faces, within original host span away from joins")
    require(abs(ob[2][0]-box[2][0])<=.01
            and ob[2][1]<box[2][1]-.1,
            "Opening must start at original Wall ground Z and below wall top")
    containers=[r.RelatingStructure for r in host.ContainedInStructure]
    require(len(containers)==1 and containers[0].is_a("IfcBuildingStorey"),
            "One preexisting native storey required for new Door")
    return {
        "host":host.GlobalId,
        "opening_guid":opening.get("guid"),
        "door_guid":door.get("guid"),
        "axis":axis,
        "opening_box":ob,
        "door_box":db,
    }


def parse_full_xml(source:Path,sha:str,xml:bytes):
    require(isinstance(xml,bytes) and 0<len(xml)<=MAX_XML_BYTES,
            "Bounded complete source XML required")
    check_xml_bytes(xml)
    original=etree.fromstring(full_initial_xml(source,sha),xml_parser())
    final=etree.fromstring(xml,xml_parser())
    require(final.tag==original.tag
            and dict(final.attrib)==dict(original.attrib)
            and len(final)==3
            and etree.tostring(final[0],method="c14n")
                ==etree.tostring(original[0],method="c14n")
            and not (final.text or "").strip(),
            "Entire native IFC source geometry/identity/metadata immutable")
    return _final_products(source_model(source,sha),final[1],final[2])


def expand_managed_xml(source:Path,sha:str,xml:bytes):
    require(isinstance(xml,bytes) and 0<len(xml)<=MAX_MANAGED_BYTES,
            "Bounded managed original complete final XML required")
    check_xml_bytes(xml)
    full=full_initial_xml(source,sha)
    ref=etree.fromstring(full,xml_parser())
    managed=etree.fromstring(xml,xml_parser())
    require(managed.tag==Q+"ManagedFinalState"
            and dict(managed.attrib)=={
                "version":"0.65",
                "representation":"MANAGED_FINAL_SOURCE_NEUTRAL_HOSTED_DOOR",
                "sourceIFCSha256":sha,
                "sourceFullBuildingStateSha256":sha256(full).hexdigest(),
            }
            and len(managed)==2
            and not (managed.text or "").strip(),
            "Complete managed original building SHA/roster changed")
    state=_final_products(source_model(source,sha),managed[0],managed[1])
    for prod in managed[1]:
        etree.SubElement(ref[2],prod.tag,dict(prod.attrib))
    whole=etree.tostring(ref,encoding="utf8",xml_declaration=True)
    require(parse_full_xml(source,sha,whole)==state,
            "Source-neutral original full and managed semantic state diverged")
    return whole,state


def _world_transform(axis,box):
    x=np.eye(4)
    if axis=="X":
        x[:3,3]=[box[0][0],box[1][0],box[2][0]]
    else:
        x[:3,0]=[0,1,0]
        x[:3,1]=[-1,0,0]
        x[:3,3]=[box[0][1],box[1][0],box[2][0]]
    return x


def compile_hosted_door(source:Path,sha:str,state:dict,target:Path):
    f=source_model(source,sha)
    target=Path(target)
    require(target.parent.is_dir() and not target.parent.is_symlink()
            and not target.exists() and not target.is_symlink()
            and target.resolve()!=Path(source).resolve(),
            "Fresh separate original IFC output path required")
    # Reconstruct a canonical complete final state from validated data,
    # not a permissive direct-call dict bypassing the XML admission.
    original=etree.fromstring(full_initial_xml(source,sha),xml_parser())
    new=original[2]
    for kind,guid,refkey,refvalue,box in (
        ("Opening",state["opening_guid"],"hostOriginalWallGuid",
         state["host"],state["opening_box"]),
        ("Door",state["door_guid"],"fillsOpeningGuid",
         state["opening_guid"],state["door_box"]),
    ):
        etree.SubElement(new,Q+kind,{"guid":guid,refkey:refvalue,
                                    **_box_attrs(box)})
    validated=parse_full_xml(
        source,sha,etree.tostring(original,encoding="utf8",xml_declaration=True))
    require(validated==state,"Source-bound complete final native IFC state invalid")
    host=f.by_guid(state["host"])
    original_ids={e.id() for e in f}
    axis=state["axis"]
    op=state["opening_box"]
    db=state["door_box"]
    long=0 if axis=="X" else 1
    cross=1-long
    body=[r for r in f.by_type("IfcGeometricRepresentationSubContext")
          if r.ContextIdentifier=="Body" and r.TargetView=="MODEL_VIEW"]
    require(len(body)==1,"One original source Model/Body representation context")
    opening=ifcopenshell.api.root.create_entity(
        f,ifc_class="IfcOpeningElement",name="Source-neutral Door Opening")
    opening.GlobalId=state["opening_guid"]
    openingrep=ifcopenshell.api.geometry.add_wall_representation(
        f,context=body[0],length=op[long][1]-op[long][0],
        height=op[2][1]-op[2][0],
        thickness=op[cross][1]-op[cross][0])
    ifcopenshell.api.geometry.assign_representation(
        f,product=opening,representation=openingrep)
    ifcopenshell.api.geometry.edit_object_placement(
        f,product=opening,matrix=_world_transform(axis,op))
    void=ifcopenshell.api.feature.add_feature(
        f,feature=opening,element=host)
    door=ifcopenshell.api.root.create_entity(
        f,ifc_class="IfcDoor",name="Source-neutral Door")
    door.GlobalId=state["door_guid"]
    units=ifcopenshell.util.unit.calculate_unit_scale(f)
    door.OverallWidth=round((db[long][1]-db[long][0])/units,6)
    door.OverallHeight=round((db[2][1]-db[2][0])/units,6)
    doorrep=ifcopenshell.api.geometry.add_wall_representation(
        f,context=body[0],length=db[long][1]-db[long][0],
        height=db[2][1]-db[2][0],
        thickness=db[cross][1]-db[cross][0])
    ifcopenshell.api.geometry.assign_representation(
        f,product=door,representation=doorrep)
    ifcopenshell.api.geometry.edit_object_placement(
        f,product=door,matrix=_world_transform(axis,db))
    fill=ifcopenshell.api.feature.add_filling(
        f,opening=opening,element=door)
    originalstorey=host.ContainedInStructure[0].RelatingStructure
    contained=f.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=ifcopenshell.guid.new(),
        RelatedElements=(door,),RelatingStructure=originalstorey)
    if f.schema=="IFC2X3":
        require(host.OwnerHistory is not None,
                "Required source IFC2X3 OwnerHistory missing")
        for root in f.by_type("IfcRoot"):
            if root.id() not in original_ids and root.OwnerHistory is None:
                root.OwnerHistory=host.OwnerHistory
    f.write(str(target))
    require(target.is_file() and file_hash(source)==sha,
            "Original source changed or candidate missing")


def post_native_ifc_gate(source:Path,sha:str,candidate:Path):
    original=source_model(source,sha)
    candidate=Path(candidate)
    require(candidate.is_file() and not candidate.is_symlink()
            and candidate.resolve()!=Path(source).resolve(),
            "Original source and edited IFC must be distinct")
    candidate_sha=file_hash(candidate)
    edited=ifcopenshell.open(str(candidate))
    require(edited.schema==original.schema
            and abs(ifcopenshell.util.unit.calculate_unit_scale(edited)
                    -ifcopenshell.util.unit.calculate_unit_scale(original))<1e-9,
            "Source native schema and mm/m LENGTHUNIT unchanged")
    for k in ("IfcWall","IfcDoor","IfcOpeningElement","IfcRelFillsElement",
              "IfcRelVoidsElement"):
        oldcount=len(original.by_type(k))
        need=1 if k in (
            "IfcDoor","IfcOpeningElement","IfcRelFillsElement",
            "IfcRelVoidsElement") else 0
        require(len(edited.by_type(k))==oldcount+need,
                "Only one hosted Door/Opening added, original objects kept")
    old={e.id():_native_entity_signature_v060(e) for e in original}
    new={e.id():_native_entity_signature_v060(e) for e in edited}
    require(set(old).issubset(new)
            and all(new[i]==v for i,v in old.items()),
            "ALL ORIGINAL native STEP IDs, geometry and attributes must remain")
    new_ids=set(new)-set(old)
    added={i:edited.by_id(i) for i in new_ids}
    roots=[x for x in added.values() if x.is_a("IfcRoot")]
    require(sorted(x.is_a() for x in roots)==ROOT_CLASSES,
            "Exactly new Door, Opening, fills, voids and one containment allowed")
    def links(entity):
        found=[]
        def inspect(v):
            if isinstance(v,ifcopenshell.entity_instance):
                found.append(v)
            elif isinstance(v,(tuple,list)):
                for item in v:inspect(item)
        for v in entity.get_info(recursive=False).values():inspect(v)
        return found
    seen=set()
    todo=list(roots)
    while todo:
        entity=todo.pop()
        if entity.id() in seen:continue
        seen.add(entity.id())
        todo.extend(n for n in links(entity)
                    if n.id() in new_ids and n.id() not in seen)
    require(new_ids<=seen,
            "New unreferenced anonymous IFC geometry/STEP data must not be added")
    old_root_guids={x.GlobalId for x in original.by_type("IfcRoot")}
    for x in original.by_type("IfcRoot"):
        require(edited.by_guid(x.GlobalId) is not None,
                "Original IFC Root GUID lost")
    for x in roots:
        require(x.GlobalId not in old_root_guids,
                "New Root GUID collides with original IFC")
        if edited.schema=="IFC2X3":
            require(x.OwnerHistory is not None,
                    "IFC2X3 nonoptional new-root OwnerHistory absent")
    door=next(x for x in roots if x.is_a("IfcDoor"))
    opening=next(x for x in roots if x.is_a("IfcOpeningElement"))
    filling=next(x for x in roots if x.is_a("IfcRelFillsElement"))
    void=next(x for x in roots if x.is_a("IfcRelVoidsElement"))
    contain=next(x for x in roots if x.is_a("IfcRelContainedInSpatialStructure"))
    require(filling.RelatingOpeningElement==opening
            and filling.RelatedBuildingElement==door
            and void.RelatedOpeningElement==opening
            and void.RelatingBuildingElement.is_a("IfcWall")
            and void.RelatingBuildingElement.GlobalId in old_root_guids
            and contain.RelatingStructure.is_a("IfcBuildingStorey")
            and door in contain.RelatedElements,
            "Native Door/Opening/host/storey relations not connected")
    host=void.RelatingBuildingElement
    original_host=original.by_guid(host.GlobalId)
    axis,wall_box=horizontal_wall_axis_and_box(original_host)
    ob=_mesh_bounds(opening)
    db=_mesh_bounds(door)
    require(door.Representation is not None
            and opening.Representation is not None,
            "Native solids must actually be represented")
    lon=0 if axis=="X" else 1
    t=1-lon
    require(all(db[i][0]>=ob[i][0]-1e-4
                and db[i][1]<=ob[i][1]+1e-4 for i in range(3))
            and ob[t][0]<wall_box[t][0]-.025
            and ob[t][1]>wall_box[t][1]+.025
            and ob[lon][0]>wall_box[lon][0]+.15
            and ob[lon][1]<wall_box[lon][1]-.15,
            "Actual source native Door must fill through-thickness Wall aperture")
    units=ifcopenshell.util.unit.calculate_unit_scale(original)
    require(abs(door.OverallWidth*units-(db[lon][1]-db[lon][0]))<.001
            and abs(door.OverallHeight*units-(db[2][1]-db[2][0]))<.001,
            "IFC2X3/IFC4X3 native units must agree with actual metres")
    old_volume=_volume(original_host)
    new_volume=_volume(host)
    actual=old_volume-new_volume
    expected=(ob[lon][1]-ob[lon][0]) * (
        wall_box[t][1]-wall_box[t][0]) * (ob[2][1]-ob[2][0])
    require(actual>.05 and abs(actual-expected)<.003
            and _near_bbox(_mesh_bounds(original_host),_mesh_bounds(host)),
            "True native original->edited Wall full-thickness CSG volume mismatch")
    for x in original.by_type("IfcProduct"):
        if x.Representation is None or x.GlobalId==host.GlobalId:
            continue
        y=edited.by_guid(x.GlobalId)
        require(y is not None and y.is_a()==x.is_a()
                and _near_bbox(_mesh_bounds(x),_mesh_bounds(y))
                and abs(_volume(x)-_volume(y))<.001,
                "Original other IFC product geometry changed")
    findings_initial=_schema_error_counter(source)
    findings_result=_schema_error_counter(candidate)
    require(not (findings_result-findings_initial),
            "New native IFC2X3/IFC4X3 validator schema errors detected")
    require(file_hash(source)==sha and file_hash(candidate)==candidate_sha,
            "Original IFC or result changed during independent post-native gate")
    return {
        "status":STATUS,
        "original_ifc_schema":original.schema,
        "original_ifc_sha256":sha,
        "original_ifc_source_step_entities_unchanged":len(old),
        "original_ifc_wall_count":len(original.by_type("IfcWall")),
        "original_root_guid_count_preserved":len(old_root_guids),
        "new_ifc_roots_exact_5":True,
        "new_door_original_storey":True,
        "actual_wall_csg_volume_removed_m3":round(actual,6),
        "expected_wall_volume_removed_m3":round(expected,6),
        "new_ifc_validator_errors":0,
        "host_original_wall_guid":host.GlobalId,
        "opening_bbox_m":ob,
        "door_bbox_m":db,
        "candidate_native_ifc_sha256":candidate_sha,
        "source_only_scope_no_task_correctness":True,
    }


def semantic_digest(verdict):
    require(verdict["status"]==STATUS,"No digest of unvalidated output")
    normalized={
        "schema":verdict["original_ifc_schema"],
        "source_sha":verdict["original_ifc_sha256"],
        "root_count":verdict["original_root_guid_count_preserved"],
        "host":verdict["host_original_wall_guid"],
        "opening_box":verdict["opening_bbox_m"],
        "door_box":verdict["door_bbox_m"],
        "cut":verdict["actual_wall_csg_volume_removed_m3"],
        "new_schema_errors":verdict["new_ifc_validator_errors"],
    }
    return sha256(json.dumps(normalized,sort_keys=True).encode("utf8")).hexdigest()
