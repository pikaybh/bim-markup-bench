"""v0.64 exact original IFC2X3 Door & hosted-opening physical source-native D/I.

Original source is IFC2X3 (NOT IFC4X3) and has THREE original Walls,
no existing Door/Opening. Native project unit is MILLIMETRE, while
IfcOpenShell USE_WORLD_COORDS meshes are in METRES. One new Door and
fully-piercing hosted Opening are independent of target correctness.

The original author's PUBLIC question selects the wall nearest in +Y
from a referenced wall. This physical-public predicate is evaluator
only and NOT in the host native gate. Source-native structural validator
permits all three Wall hosts to distinguish incorrect-but-valid IFCs.

Critical IFC2X3 validity difference: OwnerHistory is REQUIRED for all
new IfcRel* Roots. IfcOpenShell API may leave it blank on add_filling
and manually created containment, so copy REFERENCE to existing original
valid Wall OwnerHistory; do not alter original ownership records.

These are narrow original-source native STEP-ID-preserving editing
affordances, not a general IFC2X3 editor or causal LLM result.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.security.agent_boundary import check_xml_bytes
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v055_production_schema_gate import _schema_error_counter
from tools.bibimbap_v060_geometry19_native import _native_entity_signature_v060
from tools.bibimbap_v063_exterior_door_native import (
    NAMESPACE,Q,BOUNDS,EPS,
    _bbox_attrs,_mesh_bounds,_volume,_near_bbox,
    _valid_guid,_original_guids,wall_orientation_v063,
    _source_structure_candidate,_complete_final_nodes,
    create_real_native_door_opening_v063,
)

TASK="geometry_test_03"
SOURCE_SHA="88f315a0ec26c1e8bd5ea84fb254cf1d30b0ef143f03bbeffcee1dd8a69a2a59"
MAX_XML=18000
MAX_COMPACT=4500
MAX_CALLS=25
STATUS="V064_ORIGINAL_IFC2X3_REAL_CSG_DOOR_OPENING_NATIVE_SCOPE_SCHEMA_PASS"


class OriginalDoorIFC2X3Native064Error(ValueError):
    pass


def need(yes:bool,reason:str):
    if not yes:
        raise OriginalDoorIFC2X3Native064Error(reason)


def parser():
    return etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,recover=False,huge_tree=False)


def source_original_ifc2x3(path:Path,*,source_sha:str):
    p=Path(path)
    need(source_sha==SOURCE_SHA and p.is_file() and not p.is_symlink()
         and file_hash(p)==SOURCE_SHA,
         "Exact original public IFC2X3 source SHA required")
    f=ifcopenshell.open(str(p))
    need(f.schema=="IFC2X3"
         and len(list(f))==164
         and len(f.by_type("IfcRoot"))==52
         and len(f.by_type("IfcWall"))==3
         and not any(f.by_type(k) for k in (
             "IfcDoor","IfcOpeningElement","IfcRelFillsElement",
             "IfcRelVoidsElement","IfcSpace"))
         and abs(ifcopenshell.util.unit.calculate_unit_scale(f)-.001)<1e-9,
         "Original IFC2X3 3-Wall source/root/count/native-unit drift")
    need(len(f.by_type("IfcRelConnectsPathElements"))==0
         and len(f.by_type("IfcSlab"))==0,
         "Original IFC2X3 source structural relation drift")
    need(file_hash(p)==source_sha,"Original source IFC changed during read")
    return f


def original_3wall_public_source_bboxes_v064(f):
    walls=sorted(f.by_type("IfcWall"),key=lambda w:w.GlobalId)
    rows=[]
    for wall in walls:
        axis,bb=wall_orientation_v063(wall)
        need(axis=="X" and abs(bb[0][0]+3.25)<.001
             and abs(bb[0][1]-3.25)<.001
             and abs(bb[2][1]-6.096)<.001,
             "Original IFC2X3 public Wall geometry source drift")
        need(wall.OwnerHistory is not None
             and len(wall.ContainedInStructure)==1
             and wall.ContainedInStructure[0].RelatingStructure.is_a("IfcBuildingStorey"),
             "Original IFC2X3 root owner or storey containment absent")
        rows.append((wall,bb))
    ymid=sorted(round((bb[1][0]+bb[1][1])/2,6) for _,bb in rows)
    need(ymid==[-.9,1.6,5.1],
         "Original distinct three-wall Y positions drifted")
    return rows


def full_original_state_v064(source:Path,*,source_sha:str)->bytes:
    f=source_original_ifc2x3(source,source_sha=source_sha)
    original_3wall_public_source_bboxes_v064(f)
    root=etree.Element(Q+"BuildingState",nsmap={None:NAMESPACE},attrib={
        "version":"0.64",
        "representation":"D_COMPLETE_XML_V064",
        "sourceOriginalIFCSha256":source_sha,
        "nativeIFCSchema":"IFC2X3",
        "nativeLengthUnit":"MILLIMETER",
        "worldMeshUnit":"METRE",
        "managedSemantics":"THREE_ORIGINAL_WALLS_PLUS_NEW_DOOR_AND_OPENING",
    })
    frozen=etree.SubElement(root,Q+"OriginalNativeIFCSource",{
        "ifcSHA256":source_sha,
        "sourceRootGUIDCount":"52",
        "originalSourceWallCount":"3",
        "originalPathConnections":"0",
    })
    products=etree.SubElement(frozen,Q+"OriginalProducts")
    for prod in sorted(f.by_type("IfcProduct"),key=lambda x:x.GlobalId):
        attrs={"ifcGuid":prod.GlobalId,
               "ifcClass":prod.is_a(),
               "name":str(prod.Name or "")}
        if prod.Representation is not None:
            attrs.update(_bbox_attrs(_mesh_bounds(prod)))
        if prod.is_a("IfcWall"):
            attrs["sourceWallAxis"]=wall_orientation_v063(prod)[0]
            attrs["originalWallPathConnectionCount"]="0"
        etree.SubElement(products,Q+"OriginalProduct",attrs)
    walls=etree.SubElement(root,Q+"ExistingWallsFinalState",{
        "boundary":"ALL_THREE_ORIGINAL_IFC2X3_WALL_GLOBALIDS"})
    for wall in sorted(f.by_type("IfcWall"),key=lambda w:w.GlobalId):
        etree.SubElement(walls,Q+"Wall",{
            "ifcGuid":wall.GlobalId,"present":"true"})
    etree.SubElement(root,Q+"FinalNewElements",{
        "boundary":"ONE_NEW_IFCDOOR_ONE_NEW_IFCOPENINGELEMENT"})
    out=etree.tostring(root,encoding="utf8",xml_declaration=True)
    need(0<len(out)<=MAX_XML,"Original full IFC2X3 source XML exceeds limit")
    return out


def managed_original_state_v064(source:Path,*,source_sha:str)->bytes:
    full=full_original_state_v064(source,source_sha=source_sha)
    original=etree.fromstring(full,parser())
    root=etree.Element(Q+"ManagedFinalState",nsmap={None:NAMESPACE},attrib={
        "version":"0.64",
        "representation":"D_MANAGED_FINAL_STATE_V064",
        "sourceOriginalIFCSha256":source_sha,
        "sourceFullBuildingStateSha256":sha256(full).hexdigest(),
        "managedBoundary":"THREE_EXISTING_WALLS_PLUS_NEW_DOOR_OPENING",
    })
    walls=etree.SubElement(root,Q+"ExistingWallsFinalState",
                           dict(original[1].attrib))
    for w in original[1]:
        etree.SubElement(walls,Q+"Wall",dict(w.attrib))
    etree.SubElement(root,Q+"FinalNewElements",dict(original[2].attrib))
    out=etree.tostring(root,encoding="utf8",xml_declaration=True)
    need(0<len(out)<=MAX_COMPACT,"Original IFC2X3 managed state too large")
    return out


def parse_full_final_v064(source:Path,xml:bytes,*,source_sha:str)->dict:
    need(isinstance(xml,bytes) and 0<len(xml)<=MAX_XML,
         "Entire bounded IFC2X3 source BuildingState XML required")
    check_xml_bytes(xml)
    original=etree.fromstring(
        full_original_state_v064(source,source_sha=source_sha),parser())
    result=etree.fromstring(xml,parser())
    need(result.tag==Q+"BuildingState"
         and dict(result.attrib)==dict(original.attrib)
         and len(result)==3
         and not (result.text or "").strip()
         and not (result.tail or "").strip(),
         "Original IFC2X3 BuildingState source/root/schema immutable")
    need(result[0].tag==Q+"OriginalNativeIFCSource"
         and etree.tostring(result[0],method="c14n")==
             etree.tostring(original[0],method="c14n"),
         "Original IFC2X3 native source products/geometry changed")
    chosen=_complete_final_nodes(
        result[1],original[1],result[2],
        source_original_ifc2x3(source,source_sha=source_sha))
    return chosen


def restore_managed_final_v064(source:Path,xml:bytes,*,source_sha:str)->tuple[bytes,dict]:
    need(isinstance(xml,bytes) and 0<len(xml)<=MAX_COMPACT,
         "Entire bounded IFC2X3 3+2 managed final-state XML required")
    check_xml_bytes(xml)
    full=full_original_state_v064(source,source_sha=source_sha)
    original=etree.fromstring(full,parser())
    doc=etree.fromstring(xml,parser())
    need(doc.tag==Q+"ManagedFinalState"
         and dict(doc.attrib)=={
            "version":"0.64",
            "representation":"D_MANAGED_FINAL_STATE_V064",
            "sourceOriginalIFCSha256":source_sha,
            "sourceFullBuildingStateSha256":sha256(full).hexdigest(),
            "managedBoundary":"THREE_EXISTING_WALLS_PLUS_NEW_DOOR_OPENING",
         }
         and len(doc)==2
         and not (doc.text or "").strip()
         and not (doc.tail or "").strip(),
         "Original IFC2X3 compact full-source SHA or 3+2 boundary changed")
    state=_complete_final_nodes(
        doc[0],original[1],doc[1],
        source_original_ifc2x3(source,source_sha=source_sha))
    for prod in doc[1]:
        etree.SubElement(original[2],prod.tag,dict(prod.attrib))
    expanded=etree.tostring(original,encoding="utf8",xml_declaration=True)
    need(parse_full_final_v064(source,expanded,source_sha=source_sha)==state,
         "Full IFC2X3 XML reconstruction differs from managed source final state")
    return expanded,state


def _state_box_tuple(box):
    return tuple((float(a),float(b)) for a,b in box)


def compile_native_ifc2x3_door_v064(source:Path,target:Path,
                                    *,source_sha:str,state:dict):
    f=source_original_ifc2x3(source,source_sha=source_sha)
    target=Path(target)
    need(not target.exists() and target.parent.is_dir()
         and not target.parent.is_symlink()
         and target.resolve()!=Path(source).resolve(),
         "Fresh separate IFC2X3 candidate required")
    need(set(state)=={
        "host_guid","opening_guid","door_guid","axis",
        "opening_bbox","door_bbox"},
        "Only complete explicit original IFC2X3 final-state product data accepted")
    guids=_original_guids(f)
    _valid_guid(state["opening_guid"],guids)
    _valid_guid(state["door_guid"],guids)
    host=f.by_guid(state["host_guid"])
    need(host is not None and host.is_a("IfcWall")
         and state["axis"]=="X",
         "Original IFC2X3 host must be one of three source Walls")
    class Box:
        def __init__(self,b):self.attrib=_bbox_attrs(b)
        def get(self,name):return self.attrib.get(name)
    _source_structure_candidate(
        f,Box(state["opening_bbox"]),Box(state["door_bbox"]),host)
    original_ids={e.id() for e in f}
    create_real_native_door_opening_v063(f,state)
    # IFC2X3 strict mandatory OwnerHistory: the pre-existing valid
    # original owner history is referenced by NEW relations missing it.
    # It is never modified, and original native STEP IDs do not change.
    source_owner=host.OwnerHistory
    need(source_owner is not None,"Original IFC2X3 source OwnerHistory missing")
    for root in f.by_type("IfcRoot"):
        if root.id() not in original_ids and root.OwnerHistory is None:
            root.OwnerHistory=source_owner
    f.write(str(target))
    need(target.is_file() and not target.is_symlink()
         and file_hash(source)==source_sha,
         "Original IFC2X3 source changed or candidate file missing")


def _new_graph_root_closure_v064(original,edited,f)->None:
    new_ids=set(edited)-set(original)
    root_classes=sorted(x.is_a() for i,x in edited.items()
                        if i in new_ids and x.is_a("IfcRoot"))
    need(root_classes==sorted((
        "IfcDoor","IfcOpeningElement","IfcRelFillsElement",
        "IfcRelVoidsElement","IfcRelContainedInSpatialStructure")),
        "Exactly 2 new products and 3 legal hosted relations are permitted")
    def linked_entities(entity):
        children=[]
        def collect(value):
            if isinstance(value,ifcopenshell.entity_instance):
                children.append(value)
            elif isinstance(value,(tuple,list)):
                for item in value:collect(item)
        for value in entity.get_info(recursive=False).values():
            collect(value)
        return children
    reached=set()
    todo=[f.by_id(i) for i in new_ids if f.by_id(i).is_a("IfcRoot")]
    while todo:
        entity=todo.pop()
        if entity.id() in reached:continue
        reached.add(entity.id())
        todo.extend(e for e in linked_entities(entity)
                    if e.id() in new_ids and e.id() not in reached)
    need(new_ids.issubset(reached),
         "Unrelated new anonymous STEP geometry, unhosted or orphaned IFC data")


def source_native_ifc2x3_scope_v064(source:Path,target:Path,
                                     *,source_sha:str)->dict:
    original=source_original_ifc2x3(source,source_sha=source_sha)
    target=Path(target)
    need(target.is_file() and not target.is_symlink()
         and target.resolve()!=Path(source).resolve(),
         "Source IFC2X3 original and candidate cannot alias")
    candidate_sha=file_hash(target)
    f=ifcopenshell.open(str(target))
    need(f.schema=="IFC2X3"
         and abs(ifcopenshell.util.unit.calculate_unit_scale(f)-.001)<1e-9
         and len(f.by_type("IfcWall"))==3
         and len(f.by_type("IfcDoor"))==1
         and len(f.by_type("IfcOpeningElement"))==1
         and len(f.by_type("IfcRelFillsElement"))==1
         and len(f.by_type("IfcRelVoidsElement"))==1
         and len(f.by_type("IfcRelConnectsPathElements"))==0,
         "Native IFC2X3 Wall/1Door/1Opening/fills/voids counts or units drift")
    old={e.id():_native_entity_signature_v060(e) for e in original}
    new={e.id():_native_entity_signature_v060(e) for e in f}
    need(set(old).issubset(new)
         and all(new[i]==record for i,record in old.items()),
         "All 164 original IFC2X3 STEP entities/Root/geometry and attributes must persist")
    _new_graph_root_closure_v064(old,{e.id():e for e in f},f)
    for elem in original.by_type("IfcRoot"):
        need(f.by_guid(elem.GlobalId) is not None,
             "Original IFC2X3 Root identity disappeared")
    newroots={x.id() for x in original.by_type("IfcRoot")}
    for root in f.by_type("IfcRoot"):
        need(root.OwnerHistory is not None,
             "IFC2X3 mandatory new-root OwnerHistory required")
    door=f.by_type("IfcDoor")[0]
    opening=f.by_type("IfcOpeningElement")[0]
    need(door.GlobalId not in _original_guids(original)
         and opening.GlobalId not in _original_guids(original)
         and door.GlobalId!=opening.GlobalId,
         "New Door/Opening IFC2X3 GUID identity collision")
    fill=f.by_type("IfcRelFillsElement")[0]
    void=f.by_type("IfcRelVoidsElement")[0]
    need(fill.RelatingOpeningElement==opening
         and fill.RelatedBuildingElement==door
         and void.RelatedOpeningElement==opening
         and void.RelatingBuildingElement.is_a("IfcWall")
         and len(opening.VoidsElements)==1
         and len(opening.HasFillings)==1
         and len(door.FillsVoids)==1,
         "Native IFC2X3 actual Door fills Opening that voids source Wall")
    host=void.RelatingBuildingElement
    original_host=original.by_guid(host.GlobalId)
    need(original_host is not None
         and original_host.is_a("IfcWall"),
         "Opening host not among original 3 IFC2X3 Walls")
    _,hb=wall_orientation_v063(original_host)
    ob=_mesh_bounds(opening)
    db=_mesh_bounds(door)
    class Box:
        def __init__(self,b):self.attrib=_bbox_attrs(b)
        def get(self,k):return self.attrib.get(k)
    _source_structure_candidate(original,Box(ob),Box(db),original_host)
    need(opening.Representation and door.Representation
         and abs(door.OverallWidth-(db[0][1]-db[0][0])*1000)<=.5
         and abs(door.OverallHeight-(db[2][1]-db[2][0])*1000)<=.5,
         "Real native IFC2X3 Door solid dimensions not coherent in native mm")
    cont=[r for r in f.by_type("IfcRelContainedInSpatialStructure")
          if door in r.RelatedElements]
    need(len(cont)==1
         and cont[0].RelatingStructure.is_a("IfcBuildingStorey")
         and cont[0].RelatingStructure.GlobalId==
             original_host.ContainedInStructure[0].RelatingStructure.GlobalId,
         "Door not contained in original host Wall existing storey")
    # The ORIGINAL host must be measured BEFORE any opening is added.
    # Measuring a mutable in-memory edited source object as a baseline
    # erroneously reports zero. Here both IFC models are independently
    # opened from the original unchanged disk SHA and committed candidate.
    source_volume=_volume(original_host)
    edited_volume=_volume(host)
    lost=source_volume-edited_volume
    expected=(ob[0][1]-ob[0][0])*(hb[1][1]-hb[1][0])*(ob[2][1]-ob[2][0])
    need(lost>.04 and abs(lost-expected)<=.003
         and _near_bbox(_mesh_bounds(original_host),_mesh_bounds(host))
         and ob[1][0]<hb[1][0]-.025
         and ob[1][1]>hb[1][1]+.025,
         "IFC2X3 actual original Wall CSG opening must pierce FULL thickness, "
         "subtract actual correct source-baseline volume and preserve original bbox")
    for prod in original.by_type("IfcProduct"):
        if prod.Representation is None or prod.GlobalId==host.GlobalId:
            continue
        other=f.by_guid(prod.GlobalId)
        need(other is not None and other.is_a()==prod.is_a()
             and _near_bbox(_mesh_bounds(prod),_mesh_bounds(other))
             and abs(_volume(prod)-_volume(other))<=.001,
             "Original non-host IFC2X3 source native Wall changed")
    source_errors=_schema_error_counter(source)
    candidate_errors=_schema_error_counter(target)
    introduced=candidate_errors-source_errors
    need(not introduced,
         "Original IFC2X3 source-vs-candidate native schema findings increased")
    need(file_hash(source)==source_sha
         and file_hash(target)==candidate_sha,
         "Native original IFC2X3 source/candidate hash changed during scope check")
    return {
        "status":STATUS,
        "original_IFC2X3_source_native_STEP_entities_unchanged":len(old),
        "original_IFC2X3_Root_count_preserved":52,
        "new_IfcDoor_count":1,
        "new_IfcOpeningElement_count":1,
        "new_Source_RelVoidsElement_count":1,
        "new_Source_RelFillsElement_count":1,
        "new_IfcDoor_original_storey_containment":True,
        "source_native_mm_and_world_mesh_metres":True,
        "new_mandatory_IFC2X3_OwnerHistory_valid":True,
        "native_original_IFC2X3_wall_full_thickness_volume_lost_m3":round(lost,6),
        "native_expected_original_wall_cut_volume_m3":round(expected,6),
        "all_other_original_source_wall_geometry_unchanged":True,
        "native_original_IFC2X3_schema_source_existing_error_count":sum(source_errors.values()),
        "native_original_IFC2X3_new_schema_errors":0,
        "native_one_door_host_source_original_guid":host.GlobalId,
        "native_opening_bbox_m":ob,
        "native_door_bbox_m":db,
        "door_world_width_m":round(db[0][1]-db[0][0],6),
        "door_world_height_m":round(db[2][1]-db[2][0],6),
        "source_SHA256_preserved":True,
        "candidate_native_IFC_SHA256":candidate_sha,
        "original_author_repository_score":None,
    }


def canonical_semantic_digest_v064(verdict:dict)->str:
    need(verdict["status"]==STATUS,"Cannot hash invalid original source IFC")
    stable={
        "source_SHA256":SOURCE_SHA,
        "host_original_wall_guid":verdict["native_one_door_host_source_original_guid"],
        "new_original_door_bbox_m":verdict["native_door_bbox_m"],
        "new_hosted_opening_bbox_m":verdict["native_opening_bbox_m"],
        "real_source_wall_volume_cut":verdict[
            "native_original_IFC2X3_wall_full_thickness_volume_lost_m3"],
        "source_step_count":verdict[
            "original_IFC2X3_source_native_STEP_entities_unchanged"],
        "source_new_schema_errors":0,
        "ownerhistory":True,
        "relation_chain":True,
    }
    return sha256(json.dumps(stable,sort_keys=True).encode("utf8")).hexdigest()
