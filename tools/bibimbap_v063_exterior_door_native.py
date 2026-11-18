"""v0.63 source-original IFC4X3 complete declarative Door + Opening final state.

All source facts derive from the exact immutable original IFC, native
project length MILLIMETRES, geometry world mesh METRES. Three arms share
the same independent geometry/relationship/original-entity/schema gate.

Structural native gate permits a geometrically valid *internal* Door as
a negative control; independent PUBLIC exterior/indoor-outdoor semantics
remain separate, evaluator-only, NOT a hidden author scorer or host hint.
Only two explicit NEW final-state products (Door + hosted Opening), plus
complete explicit unchanged roster of all seven original source Walls.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path
import re

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.api.geometry
import ifcopenshell.api.feature
import ifcopenshell.geom
import ifcopenshell.util.shape
import ifcopenshell.util.unit
import numpy as np
from lxml import etree

from src.security.agent_boundary import check_xml_bytes
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v055_production_schema_gate import production_native_schema_delta_v055
from tools.bibimbap_v060_geometry19_native import _native_entity_signature_v060
from tools.bibimbap_v061_geometry13_native import _mesh_bounds

SOURCE_SHA="c0e0019d7224185d5872b80bdd3652da2bc960b819c1d8c0dd03b213b14847ca"
TASK="topological_test_05"
NAMESPACE="urn:bim-markup-bench:toy:v0"
Q="{"+NAMESPACE+"}"
MAX_XML=21000
MAX_COMPACT=6000
MAX_CALLS=25
EPS=2e-4
BOUNDS=("minXM","maxXM","minYM","maxYM","minZM","maxZM")


class OriginalDoorNative063Error(ValueError):
    pass


def need(condition:bool,message:str):
    if not condition:
        raise OriginalDoorNative063Error(message)


def parser():
    return etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,recover=False,huge_tree=False)


def source_ifc(path:Path,*,source_sha:str):
    p=Path(path)
    need(p.is_file() and not p.is_symlink() and
         source_sha==SOURCE_SHA and file_hash(p)==SOURCE_SHA,
         "Exact SHA-pinned unmodified original public IFC input required")
    model=ifcopenshell.open(str(p))
    need(model.schema=="IFC4X3" and len(model.by_type("IfcWall"))==7
         and len(model.by_type("IfcSlab"))==2
         and len(model.by_type("IfcRelConnectsPathElements"))==9
         and all(len(model.by_type(k))==0 for k in (
             "IfcDoor","IfcOpeningElement","IfcRelVoidsElement",
             "IfcRelFillsElement","IfcSpace","IfcWindow"))
         and abs(ifcopenshell.util.unit.calculate_unit_scale(model)-.001)<1e-9,
         "Original IFC4X3 Door CREATE source counts/units drifted")
    need(file_hash(p)==source_sha,"Original source changed during native read")
    return model


def _volume(product)->float:
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    shape=ifcopenshell.geom.create_shape(settings,product)
    value=float(ifcopenshell.util.shape.get_volume(shape.geometry))
    need(math.isfinite(value) and value>0,"Real native source shape is empty")
    return value


def wall_orientation_v063(wall):
    b=_mesh_bounds(wall)
    width=b[0][1]-b[0][0]
    depth=b[1][1]-b[1][0]
    need(wall.is_a("IfcWall")
         and abs(min(width,depth)-.2)<.03
         and max(width,depth)>1.2,
         "Original source Wall axis/thickness geometry not supported")
    return ("X" if width>depth else "Y"),b


def source_envelope_v063(model):
    walls=model.by_type("IfcWall")
    bounds=[_mesh_bounds(w) for w in walls]
    env=(min(b[0][0] for b in bounds),max(b[0][1] for b in bounds),
         min(b[1][0] for b in bounds),max(b[1][1] for b in bounds))
    need(abs(env[0])<.01 and abs(env[1]-7.7)<.01
         and abs(env[2])<.01 and abs(env[3]-8.1)<.01,
         "Original source world outer-envelope geometry drifted")
    return env


def _number(v)->str:
    n=float(v)
    need(math.isfinite(n) and abs(n)<=1e4,
         "Unbounded source-world absolute geometry")
    return f"{n:.6f}"


def _bbox_attrs(b):
    return {
        "minXM":_number(b[0][0]),"maxXM":_number(b[0][1]),
        "minYM":_number(b[1][0]),"maxYM":_number(b[1][1]),
        "minZM":_number(b[2][0]),"maxZM":_number(b[2][1]),
    }


def _original_guids(model):
    return {root.GlobalId for root in model.by_type("IfcRoot")}


def initial_full_source_v063(path:Path,*,source_sha:str)->bytes:
    original=source_ifc(path,source_sha=source_sha)
    env=source_envelope_v063(original)
    root=etree.Element(Q+"BuildingState",nsmap={None:NAMESPACE},attrib={
        "version":"0.63",
        "representation":"D_COMPLETE_XML_V063",
        "sourceOriginalIFCSha256":source_sha,
        "originalIFCSchema":"IFC4X3",
        "nativeLengthUnit":"MILLIMETER",
        "worldMeshUnit":"METRE",
        "managedSemantics":"ALL_SEVEN_EXISTING_WALLS_PLUS_NEW_DOOR_AND_OPENING",
    })
    frozen=etree.SubElement(root,Q+"OriginalNativeIFCSource",{
        "ifcSHA256":source_sha,
        "sourceRootGUIDCount":str(len(original.by_type("IfcRoot"))),
        "originalSourceWallCount":"7",
        "originalPathConnections":"9",
    })
    etree.SubElement(frozen,Q+"OriginalWallFootprintEnvelope",{
        k:_number(v) for k,v in zip(
            ("minXM","maxXM","minYM","maxYM"),env)
    })
    products=etree.SubElement(frozen,Q+"OriginalProducts")
    for prod in sorted(original.by_type("IfcProduct"),key=lambda x:x.GlobalId):
        attrs={"ifcGuid":prod.GlobalId,"ifcClass":prod.is_a(),
               "name":str(prod.Name or "")}
        if prod.Representation is not None:
            attrs.update(_bbox_attrs(_mesh_bounds(prod)))
        if prod.is_a("IfcWall"):
            axis,b=wall_orientation_v063(prod)
            attrs["sourceWallAxis"]=axis
            attrs["originalWallPathConnectionCount"]=str(sum(
                x.is_a("IfcRelConnectsPathElements")
                for x in original.get_inverse(prod)))
        etree.SubElement(products,Q+"OriginalProduct",attrs)
    walls=etree.SubElement(root,Q+"ExistingWallsFinalState",{
        "boundary":"ALL_SEVEN_ORIGINAL_WALL_GLOBALIDS",
    })
    for wall in sorted(original.by_type("IfcWall"),key=lambda w:w.GlobalId):
        etree.SubElement(walls,Q+"Wall",{
            "ifcGuid":wall.GlobalId,"present":"true"})
    etree.SubElement(root,Q+"FinalNewElements",{
        "boundary":"ONE_NEW_IFCDOOR_ONE_NEW_IFCOPENINGELEMENT",
    })
    out=etree.tostring(root,encoding="utf8",xml_declaration=True)
    need(0<len(out)<=MAX_XML,"Original full source XML unbounded")
    return out


def initial_compact_source_v063(path:Path,*,source_sha:str)->bytes:
    initial=initial_full_source_v063(path,source_sha=source_sha)
    doc=etree.fromstring(initial,parser())
    root=etree.Element(Q+"ManagedFinalState",nsmap={None:NAMESPACE},attrib={
        "version":"0.63",
        "representation":"D_MANAGED_FINAL_STATE_V063",
        "sourceOriginalIFCSha256":source_sha,
        "sourceFullBuildingStateSha256":sha256(initial).hexdigest(),
        "managedBoundary":"SEVEN_EXISTING_WALLS_PLUS_NEW_DOOR_OPENING",
    })
    walls=etree.SubElement(root,Q+"ExistingWallsFinalState",
                           dict(doc[1].attrib))
    for wall in doc[1]:
        etree.SubElement(walls,Q+"Wall",dict(wall.attrib))
    etree.SubElement(root,Q+"FinalNewElements",dict(doc[2].attrib))
    out=etree.tostring(root,encoding="utf8",xml_declaration=True)
    need(0<len(out)<=MAX_COMPACT,"Original compact source XML unbounded")
    return out


def _parse_bbox(node):
    need(set(node.attrib).issuperset(BOUNDS),"Complete absolute bbox required")
    b=[]
    for lo,hi in (("minXM","maxXM"),("minYM","maxYM"),("minZM","maxZM")):
        for key in (lo,hi):
            raw=node.get(key)
            try:
                value=float(raw)
            except (TypeError,ValueError):
                raise OriginalDoorNative063Error("Invalid absolute world coordinate") from None
            need(math.isfinite(value) and -100<=value<=100
                 and raw==f"{value:.6f}",
                 "Only source-world bounded canonical 6-decimal coordinates")
        b.append((float(node.get(lo)),float(node.get(hi))))
    need(all(hi-lo>.00001 for lo,hi in b),
         "Original complete final geometry bbox must have positive dimensions")
    return tuple(b)


def _valid_guid(guid:str,used:set[str]):
    need(isinstance(guid,str) and len(guid)==22
         and re.fullmatch(r"[0-9A-Za-z_$]{22}",guid) is not None
         and guid not in used and guid!="0"*22,
         "New original final-state GUID missing/duplicate/invalid")
    try:
        uncompressed=ifcopenshell.guid.expand(guid)
        need(len(uncompressed)==32,"IFC source new GUID not valid")
    except Exception:
        raise OriginalDoorNative063Error("Invalid compressed IFC GUID") from None
    used.add(guid)


def _source_structure_candidate(model,opening,door,host):
    need(host is not None and host.is_a("IfcWall"),
         "Original Wall reference does not exist")
    axis,wb=wall_orientation_v063(host)
    ob=_parse_bbox(opening)
    db=_parse_bbox(door)
    # New door panel must be INSIDE its host opening in all world axes.
    for k in range(3):
        need(db[k][0]>=ob[k][0]-EPS and db[k][1]<=ob[k][1]+EPS,
             "Native Door panel must lie inside hosted Opening geometry")
    longitudinal=0 if axis=="X" else 1
    transverse=1-longitudinal
    doorwidth=db[longitudinal][1]-db[longitudinal][0]
    openwidth=ob[longitudinal][1]-ob[longitudinal][0]
    doorheight=db[2][1]-db[2][0]
    openheight=ob[2][1]-ob[2][0]
    door_thickness=db[transverse][1]-db[transverse][0]
    opening_thickness=ob[transverse][1]-ob[transverse][0]
    need(.35<=doorwidth<=1.6 and 1.0<=doorheight<=2.6
         and .025<=door_thickness<=.10
         and doorwidth+.01<=openwidth<=doorwidth+.3
         and doorheight+.01<=openheight<=doorheight+.3
         and opening_thickness>=.25 and opening_thickness<=.6,
         "Unsupported Door/Opening geometric final-world dimensional envelope")
    need(ob[transverse][0]<wb[transverse][0]-.025
         and ob[transverse][1]>wb[transverse][1]+.025,
         "Source-wall external AND internal thickness faces must both be cut")
    need(ob[longitudinal][0]>wb[longitudinal][0]+.25
         and ob[longitudinal][1]<wb[longitudinal][1]-.25,
         "Door opening must lie within original host span away from wall joints")
    need(abs(ob[2][0]-wb[2][0])<=.01
         and ob[2][1]<wb[2][1]-.2,
         "New Door opening must start from existing finished floor and below Wall top")
    return axis,wb,ob,db


def _complete_final_nodes(original_walls,source_walls,final_new,model):
    need(original_walls.tag==source_walls.tag==Q+"ExistingWallsFinalState"
         and dict(original_walls.attrib)==dict(source_walls.attrib)
         and etree.tostring(original_walls,method="c14n")==
             etree.tostring(source_walls,method="c14n"),
         "Original complete seven-Wall source final-state roster changed")
    need(final_new.tag==Q+"FinalNewElements"
         and dict(final_new.attrib)=={
             "boundary":"ONE_NEW_IFCDOOR_ONE_NEW_IFCOPENINGELEMENT"}
         and len(final_new)==2
         and not (final_new.text or "").strip()
         and not (final_new.tail or "").strip(),
         "Exactly two explicit complete new original-source final products required")
    opening,door=list(final_new)
    need(opening.tag==Q+"Opening" and door.tag==Q+"Door"
         and not len(opening) and not len(door)
         and not (opening.text or "").strip()
         and not (door.text or "").strip()
         and not (opening.tail or "").strip()
         and not (door.tail or "").strip()
         and set(opening.attrib)==set(BOUNDS)|{
             "ifcGuid","hostOriginalWallGuid"}
         and set(door.attrib)==set(BOUNDS)|{
             "ifcGuid","fillsOpeningGuid"},
         "New source IFC products must be explicit final geometry and relation")
    used=_original_guids(model)
    _valid_guid(opening.get("ifcGuid"),used)
    _valid_guid(door.get("ifcGuid"),used)
    need(door.get("fillsOpeningGuid")==opening.get("ifcGuid"),
         "New Door must explicitly fill new original source Opening")
    host=model.by_guid(opening.get("hostOriginalWallGuid"))
    axis,wb,ob,db=_source_structure_candidate(model,opening,door,host)
    return {
        "host_guid":host.GlobalId,
        "opening_guid":opening.get("ifcGuid"),
        "door_guid":door.get("ifcGuid"),
        "axis":axis,
        "opening_bbox":ob,
        "door_bbox":db,
    }


def parse_full_final_v063(source:Path,final_xml:bytes,
                          *,source_sha:str)->dict:
    need(isinstance(final_xml,bytes) and 0<len(final_xml)<=MAX_XML,
         "Bounded whole original BuildingState XML required")
    check_xml_bytes(final_xml)
    reference=etree.fromstring(
        initial_full_source_v063(source,source_sha=source_sha),parser())
    doc=etree.fromstring(final_xml,parser())
    need(doc.tag==Q+"BuildingState"
         and dict(doc.attrib)==dict(reference.attrib)
         and len(doc)==3
         and not (doc.text or "").strip()
         and not (doc.tail or "").strip(),
         "Source IFC/building root immutable")
    need(doc[0].tag==Q+"OriginalNativeIFCSource"
         and etree.tostring(doc[0],method="c14n")==
             etree.tostring(reference[0],method="c14n"),
         "Entire source native IFC geometry/products/topology must be immutable")
    return _complete_final_nodes(
        doc[1],reference[1],doc[2],source_ifc(source,source_sha=source_sha))


def restore_managed_final_v063(source:Path,compact_xml:bytes,
                               *,source_sha:str)->tuple[bytes,dict]:
    need(isinstance(compact_xml,bytes) and 0<len(compact_xml)<=MAX_COMPACT,
         "Bounded complete original seven-Wall compact final XML required")
    check_xml_bytes(compact_xml)
    original=initial_full_source_v063(source,source_sha=source_sha)
    reference=etree.fromstring(original,parser())
    doc=etree.fromstring(compact_xml,parser())
    need(doc.tag==Q+"ManagedFinalState"
         and dict(doc.attrib)=={
             "version":"0.63",
             "representation":"D_MANAGED_FINAL_STATE_V063",
             "sourceOriginalIFCSha256":source_sha,
             "sourceFullBuildingStateSha256":sha256(original).hexdigest(),
             "managedBoundary":"SEVEN_EXISTING_WALLS_PLUS_NEW_DOOR_OPENING",
         }
         and len(doc)==2
         and not (doc.text or "").strip()
         and not (doc.tail or "").strip(),
         "Original compact full-source SHA or complete 7+2 boundary tampered")
    model=source_ifc(source,source_sha=source_sha)
    chosen=_complete_final_nodes(
        doc[0],reference[1],doc[1],model)
    for src in doc[1]:
        etree.SubElement(reference[2],src.tag,dict(src.attrib))
    whole=etree.tostring(reference,encoding="utf8",xml_declaration=True)
    need(parse_full_final_v063(
        source,whole,source_sha=source_sha)==chosen,
        "Source-bound full declarative reconstruction disagreed")
    return whole,chosen


def _matrix_from_world_bbox(axis,bbox):
    mat=np.eye(4)
    if axis=="X":
        mat[:3,3]=[bbox[0][0],bbox[1][0],bbox[2][0]]
    else:
        mat[:3,0]=[0,1,0]
        mat[:3,1]=[-1,0,0]
        mat[:3,3]=[bbox[0][1],bbox[1][0],bbox[2][0]]
    return mat


def create_real_native_door_opening_v063(model,state:dict):
    host=model.by_guid(state["host_guid"])
    axis,wb=wall_orientation_v063(host)
    need(axis==state["axis"],"Original Wall source orientation drift")
    context=[c for c in model.by_type("IfcGeometricRepresentationSubContext")
             if c.ContextIdentifier=="Body" and c.TargetView=="MODEL_VIEW"]
    need(len(context)==1,"Exact original IFC4X3 Body context required")
    body=context[0]
    ob=state["opening_bbox"]
    db=state["door_bbox"]
    longitudinal=0 if axis=="X" else 1
    transverse=1-longitudinal
    opening=ifcopenshell.api.root.create_entity(
        model,ifc_class="IfcOpeningElement",name="New Door Clear Opening")
    opening.GlobalId=state["opening_guid"]
    r=ifcopenshell.api.geometry.add_wall_representation(
        model,context=body,length=ob[longitudinal][1]-ob[longitudinal][0],
        height=ob[2][1]-ob[2][0],
        thickness=ob[transverse][1]-ob[transverse][0])
    ifcopenshell.api.geometry.assign_representation(
        model,product=opening,representation=r)
    ifcopenshell.api.geometry.edit_object_placement(
        model,product=opening,matrix=_matrix_from_world_bbox(axis,ob))
    ifcopenshell.api.feature.add_feature(
        model,feature=opening,element=host)
    door=ifcopenshell.api.root.create_entity(
        model,ifc_class="IfcDoor",name="New Building Entrance Door")
    door.GlobalId=state["door_guid"]
    door.OverallWidth=round(
        (db[longitudinal][1]-db[longitudinal][0])*1000.,6)
    door.OverallHeight=round((db[2][1]-db[2][0])*1000.,6)
    r=ifcopenshell.api.geometry.add_wall_representation(
        model,context=body,
        length=db[longitudinal][1]-db[longitudinal][0],
        height=db[2][1]-db[2][0],
        thickness=db[transverse][1]-db[transverse][0])
    ifcopenshell.api.geometry.assign_representation(
        model,product=door,representation=r)
    ifcopenshell.api.geometry.edit_object_placement(
        model,product=door,matrix=_matrix_from_world_bbox(axis,db))
    ifcopenshell.api.feature.add_filling(
        model,opening=opening,element=door)
    # Product is part of the ORIGINAL existing storey, without modifying
    # any original source IfcRelContainedInSpatialStructure attribute.
    storey=[r.RelatingStructure for r in host.ContainedInStructure]
    need(len(storey)==1 and storey[0].is_a("IfcBuildingStorey"),
         "New IFC Door original spatial parent is unambiguous")
    model.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=ifcopenshell.guid.new(),
        RelatedElements=(door,),RelatingStructure=storey[0])
    return opening,door


def compile_real_original_IFC_v063(source:Path,out:Path,
                                    *,source_sha:str,state:dict)->None:
    model=source_ifc(source,source_sha=source_sha)
    destination=Path(out)
    need(not destination.exists() and destination.parent.is_dir()
         and not destination.parent.is_symlink()
         and destination.resolve()!=Path(source).resolve(),
         "Fresh separate native IFC output required")
    # Independently check the complete final state again in source context,
    # even if caller supplied a fabricated dict rather than XML.
    need(set(state)=={
        "host_guid","opening_guid","door_guid","axis",
        "opening_bbox","door_bbox"},
        "Only validated original complete final state is compilable")
    used=_original_guids(model)
    for product_kind in ("door_guid","opening_guid"):
        _valid_guid(state[product_kind],used)
    host=model.by_guid(state["host_guid"])
    need(host is not None and host.is_a("IfcWall")
         and wall_orientation_v063(host)[0]==state["axis"],
         "Original native host source Wall not present")
    class Box:
        def __init__(self,b):self.attrib=_bbox_attrs(b)
        def get(self,key):return self.attrib.get(key)
    _source_structure_candidate(
        model,Box(state["opening_bbox"]),Box(state["door_bbox"]),host)
    create_real_native_door_opening_v063(model,state)
    model.write(str(destination))
    need(destination.is_file() and not destination.is_symlink()
         and file_hash(source)==source_sha,
         "Native IFC Door+Opening output or source preservation failed")


def _near_bbox(actual,expect):
    return all(abs(actual[i][j]-expect[i][j])<=EPS
               for i in range(3) for j in range(2))


def independent_real_original_door_scope_v063(
    source:Path,candidate:Path,*,source_sha:str,
)->dict:
    """Source-only native & actual CSG cut check; no public target answer.

    Admits any original Wall (interior or exterior) if the new Door and
    hosted Opening geometrically span and void it with a genuine CSG cut.
    All original STEP entities and other original mesh geometry unchanged.
    The public exterior/outside classification is *separate* evaluator.
    """
    before=source_ifc(source,source_sha=source_sha)
    dest=Path(candidate)
    need(dest.is_file() and not dest.is_symlink()
         and dest.resolve()!=Path(source).resolve(),
         "Original and native candidate must be distinct")
    dest_sha=file_hash(dest)
    final=ifcopenshell.open(str(dest))
    need(final.schema=="IFC4X3"
         and abs(ifcopenshell.util.unit.calculate_unit_scale(final)-.001)<1e-9,
         "Native IFC schema/project units changed")
    need(len(final.by_type("IfcWall"))==7
         and len(final.by_type("IfcSlab"))==2
         and len(final.by_type("IfcRelConnectsPathElements"))==9
         and len(final.by_type("IfcDoor"))==1
         and len(final.by_type("IfcOpeningElement"))==1
         and len(final.by_type("IfcRelVoidsElement"))==1
         and len(final.by_type("IfcRelFillsElement"))==1,
         "Exactly one new hosted native Door+Opening relationship required")
    original={e.id():_native_entity_signature_v060(e) for e in before}
    edited={e.id():_native_entity_signature_v060(e) for e in final}
    need(set(original).issubset(edited)
         and all(edited[i]==signature for i,signature in original.items()),
         "All original IFC native STEP entities/Root/geometry/relationships must "
         "remain IDENTICAL; only added hosted Opening+Door permitted")
    # Independent exact-new-entity graph closure: prevent a fake IFC that
    # adds unrelated Roots, orphaned arbitrary STEP objects or extra
    # malicious product/geometry, even when it also contains a valid door.
    new_ids=set(edited)-set(original)
    newly_added={i:final.by_id(i) for i in new_ids}
    roots=[e for e in newly_added.values() if e.is_a("IfcRoot")]
    classes=sorted(e.is_a() for e in roots)
    need(classes==sorted((
        "IfcDoor","IfcOpeningElement","IfcRelVoidsElement",
        "IfcRelFillsElement","IfcRelContainedInSpatialStructure")),
        "Native source may introduce exactly 2 products + 3 legal hosted "
        "IFC relationships and NO other rooted IFC objects")
    def linked_entities(entity):
        children=[]
        def collect(value):
            if isinstance(value,ifcopenshell.entity_instance):
                children.append(value)
            elif isinstance(value,(tuple,list)):
                for item in value:
                    collect(item)
        for value in entity.get_info(recursive=False).values():
            collect(value)
        return children
    reached=set()
    pending=list(roots)
    while pending:
        item=pending.pop()
        if item.id() in reached:
            continue
        reached.add(item.id())
        pending.extend(x for x in linked_entities(item)
                       if x.id() in new_ids and x.id() not in reached)
    need(new_ids.issubset(reached),
         "Native candidate introduced extra unreferenced non-Root "
         "IFC entities unrelated to new hosted Door/Opening/relations")
    original_guids=_original_guids(before)
    for r in before.by_type("IfcRoot"):
        need(final.by_guid(r.GlobalId) is not None,
             "Original IFC Root identity disappeared")
    door=final.by_type("IfcDoor")[0]
    opening=final.by_type("IfcOpeningElement")[0]
    need(door.GlobalId not in original_guids
         and opening.GlobalId not in original_guids
         and door.GlobalId!=opening.GlobalId,
         "New IFC Door/Opening identities must be new unique Roots")
    fills=final.by_type("IfcRelFillsElement")[0]
    void=final.by_type("IfcRelVoidsElement")[0]
    need(fills.RelatedBuildingElement==door
         and fills.RelatingOpeningElement==opening
         and void.RelatedOpeningElement==opening
         and void.RelatingBuildingElement.is_a("IfcWall")
         and void.RelatingBuildingElement.GlobalId in original_guids
         and len(door.FillsVoids)==1
         and len(opening.VoidsElements)==1
         and len(opening.HasFillings)==1,
         "Original Door/Opening/Wall fills and voids chain incorrect")
    host=void.RelatingBuildingElement
    axis,wb=wall_orientation_v063(before.by_guid(host.GlobalId))
    opening_box=_mesh_bounds(opening)
    door_box=_mesh_bounds(door)
    # Geometry-derived source native full thickness cut, not just a fake
    # rel chain or an arbitrary mesh placed on the surface of a wall.
    class Box:
        def __init__(self,b):self.attrib=_bbox_attrs(b)
        def get(self,key):return self.attrib.get(key)
    _source_structure_candidate(
        before,Box(opening_box),Box(door_box),
        before.by_guid(host.GlobalId))
    need(door.Representation is not None
         and opening.Representation is not None
         and abs(door.OverallWidth-(
             door_box[0][1]-door_box[0][0] if axis=="X" else
             door_box[1][1]-door_box[1][0])*1000)<=.5
         and abs(door.OverallHeight-(
             door_box[2][1]-door_box[2][0])*1000)<=.5,
         "New Door has no real solid or native mm dimensions inconsistent")
    new_relations=[x for x in final.by_type("IfcRelContainedInSpatialStructure")
                   if door in x.RelatedElements]
    need(len(new_relations)==1
         and new_relations[0].RelatingStructure.is_a("IfcBuildingStorey")
         and door in new_relations[0].RelatedElements,
         "New native Door must be contained in original storey")
    old_host=before.by_guid(host.GlobalId)
    # Compare both models freshly opened: source wall native geometry
    # really loses exactly the solid 3D intersection of full opening
    # with wall thickness. Merely adding IfcRelVoids without actual
    # piercing, or deleting pieces of other Wall, cannot pass.
    initial_host_vol=_volume(old_host)
    edited_host_vol=_volume(host)
    transverse=1 if axis=="X" else 0
    long=1-transverse
    expected=(
        (opening_box[long][1]-opening_box[long][0])
        *(wb[transverse][1]-wb[transverse][0])
        *(opening_box[2][1]-opening_box[2][0])
    )
    observed=initial_host_vol-edited_host_vol
    need(observed>.05
         and abs(observed-expected)<=.003
         and _near_bbox(_mesh_bounds(old_host),_mesh_bounds(host)),
         "Actual source Wall CSG mesh must contain FULL-THICKNESS opening "
         "volume cut, not merely source geometric bounding box/rel chain")
    for product in before.by_type("IfcProduct"):
        if product.Representation is None or product.GlobalId==host.GlobalId:
            continue
        other=final.by_guid(product.GlobalId)
        need(other is not None and other.is_a()==product.is_a()
             and _near_bbox(_mesh_bounds(product),_mesh_bounds(other))
             and abs(_volume(product)-_volume(other))<=.001,
             "Original OTHER product 3D geometry/volume changed")
    # Geometric layout, native root preservation, source-cut and schema
    # validation are separate from AUTHOR's weak exterior-location check.
    delta=production_native_schema_delta_v055(
        source,dest,source_sha=source_sha)
    need(delta["status"]=="PASS_NO_NEW_SCHEMA_FINDINGS"
         and delta["introduced_schema_error_count"]==0,
         "Original native IFC4X3 schema introduced validation findings")
    need(file_hash(source)==source_sha and file_hash(dest)==dest_sha,
         "Original/source or candidate bytes changed while validating")
    return {
        "status":"V063_ORIGINAL_CSG_DOOR_OPENING_NATIVE_SCOPE_AND_SCHEMA_PASS",
        "new_source_IfcDoor":1,
        "new_source_IfcOpeningElement":1,
        "real_fills_voids_host_wall_chain":True,
        "new_door_original_storey_containment":True,
        "original_source_STEP_entities_unchanged":len(original),
        "original_source_Wall_count":7,
        "original_source_PathJoins_unchanged":9,
        "native_real_wall_full_thickness_boolean_volume_removed_m3":
            round(observed,6),
        "native_expected_source_Wall_intersection_volume_m3":
            round(expected,6),
        "native_source_geometry_other_products_unchanged":True,
        "original_IFC4X3_schema_errors_introduced":0,
        "original_source_SHA256_preserved":True,
        "host_wall_source_original_GUID":host.GlobalId,
        "opening_world_bbox":opening_box,
        "door_world_bbox":door_box,
        "door_world_width_m":round(
            door_box[long][1]-door_box[long][0],6),
        "door_world_height_m":round(
            door_box[2][1]-door_box[2][0],6),
        "original_IFC_actual_candidate_file_SHA256":dest_sha,
        "author_original_repository_score":None,
    }


def source_public_exterior_pass_v063(source:Path,candidate:Path,
                                    *,source_sha:str)->dict:
    """Independent PUBLIC physically exterior predicate, evaluator-only.

    Not part of model host/native structure gate, and NOT the author's
    repository grader. Source outer 2D bbox envelope identifies boundary
    walls; candidate hosted opening must pierce BOTH inside/outside faces.
    The source has NO IfcSpace; inside/outside are planar envelope proxies.
    """
    before=source_ifc(source,source_sha=source_sha)
    model=ifcopenshell.open(str(candidate))
    host=model.by_type("IfcRelVoidsElement")[0].RelatingBuildingElement
    source_wall=before.by_guid(host.GlobalId)
    axis,box=wall_orientation_v063(source_wall)
    env=source_envelope_v063(before)
    if axis=="X":
        at_external=(abs(box[1][0]-env[2])<=.005 or
                     abs(box[1][1]-env[3])<=.005)
    else:
        at_external=(abs(box[0][0]-env[0])<=.005 or
                     abs(box[0][1]-env[1])<=.005)
    native=independent_real_original_door_scope_v063(
        source,candidate,source_sha=source_sha)
    doorwidth=native["door_world_width_m"]
    doorheight=native["door_world_height_m"]
    appropriate=.6<=doorwidth<=1.5 and 1.5<=doorheight<=3.
    return {
        "status":"PUBLIC_SOURCE_OUTER_BOUNDARY_DOOR_PHYSICAL_PREDICATE",
        "door_wall_is_outer_envelope_boundary":bool(at_external),
        "new_door_reasonable_dimensions":bool(appropriate),
        "native_original_wall_fully_pierced":True,
        "physically_outside_connection_proxy_pass":
            bool(at_external and appropriate),
        "original_source_has_explicit_IfcSpace":False,
        "outside_true_topological_room_graph_verified":False,
        "author_repository_scorer_equivalence":False,
    }


def semantic_digest_after_native_oracle_v063(report:dict)->str:
    """Stable meaningful native SEMANTIC digest only after oracle PASS.

    New IFC Root GUIDs/STEP numbering/OwnerHistory vary between genuine
    valid D and independent Docker I. Normalize them ONLY after full
    source-root/schema/cut/geometry acceptance. Never assert native
    raw byte SHA identical.
    """
    need(report["status"]==
         "V063_ORIGINAL_CSG_DOOR_OPENING_NATIVE_SCOPE_AND_SCHEMA_PASS",
         "Cannot hash unverified original native IFC candidate")
    stable={
        "original_source_sha":SOURCE_SHA,
        "host_original_guid":report["host_wall_source_original_GUID"],
        "opening_world_bbox":report["opening_world_bbox"],
        "door_world_bbox":report["door_world_bbox"],
        "volume_removed":report[
            "native_real_wall_full_thickness_boolean_volume_removed_m3"],
        "other_original_entity_count":report[
            "original_source_STEP_entities_unchanged"],
        "original_ifc_schema_new_errors":report[
            "original_IFC4X3_schema_errors_introduced"],
        "filling_host_storey":report["new_door_original_storey_containment"],
    }
    return sha256(json.dumps(stable,sort_keys=True).encode("utf8")).hexdigest()
