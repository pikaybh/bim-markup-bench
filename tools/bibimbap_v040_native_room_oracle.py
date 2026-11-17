"""Independent P2 native-mm oracle: original IfcSpaces and true room relationships.

This module does NOT import v0.40 XML source projector/compiler or the
original published grader. It reopens actual original and newly saved IFCs
and verifies old native room meshes, aggregate-to-storey relations, other
source products, and one illustrative new physical Wall. Zero explicit
IfcRelSpaceBoundary records may never be fabricated.
"""
from __future__ import annotations

from collections import Counter
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.unit
from lxml import etree

from tools.bibimbap_v038_legacy_live_gate import _world_mesh
from tools.bibimbap_matched25_tools import file_hash

PINS={
    "topological_test_01":
        "2cb6cc753784c13fcd1f6f037b97431294cc3c91db9bcc75213ba61b8e3a18ac",
    "topological_test_03":
        "1035e999dd8579b7d2c33950498eea1f50bd9ff81e1816bdf4b9893901969466",
}
Q="{urn:bim-markup-bench:toy:v0}"


class IndependentRoomNativeError(ValueError):
    pass


def require(condition,why):
    if not condition:
        raise IndependentRoomNativeError(why)


def _root_map(model):
    roots={e.GlobalId:e for e in model.by_type("IfcRoot")}
    require(len(roots)==len(model.by_type("IfcRoot")),
            "Original/native candidate IFC Root GUID collision")
    return roots


def _edges(model):
    evidence=set()
    for typ,a,b in (
        ("IfcRelVoidsElement","RelatingBuildingElement","RelatedOpeningElement"),
        ("IfcRelFillsElement","RelatingOpeningElement","RelatedBuildingElement")):
        for rel in model.by_type(typ):
            evidence.add((typ,getattr(rel,a).GlobalId,getattr(rel,b).GlobalId))
    for rel in model.by_type("IfcRelAggregates"):
        for child in rel.RelatedObjects:
            evidence.add(("IfcRelAggregates",rel.RelatingObject.GlobalId,child.GlobalId))
    for rel in model.by_type("IfcRelContainedInSpatialStructure"):
        for child in rel.RelatedElements:
            evidence.add(("IfcRelContainedInSpatialStructure",
                          rel.RelatingStructure.GlobalId,child.GlobalId))
    for rel in model.by_type("IfcRelSpaceBoundary"):
        if rel.RelatingSpace and rel.RelatedBuildingElement:
            evidence.add((rel.is_a(),
                          rel.RelatingSpace.GlobalId,
                          rel.RelatedBuildingElement.GlobalId))
    return evidence


def _near(a,b,eps=.00001):
    return all(abs(float(x)-float(y))<=eps for x,y in zip(a,b))


def verify_p2_native_wall_create(original_mm:Path,final_mm:Path, *,
                                 task_id:str,submitted_xml:bytes)->dict:
    require(task_id in PINS and file_hash(original_mm)==PINS[task_id],
            "Original P2 public native IFC SHA mismatch")
    require(original_mm.is_file() and final_mm.is_file()
            and not original_mm.is_symlink() and not final_mm.is_symlink()
            and original_mm.resolve()!=final_mm.resolve(),
            "Actual original native IFC and candidate must be separate files")
    old=ifcopenshell.open(str(original_mm))
    result=ifcopenshell.open(str(final_mm))
    for f in (old,result):
        require(f.schema=="IFC4X3" and
                abs(ifcopenshell.util.unit.calculate_unit_scale(f)-.001)<1e-12,
                "Original P2 native IFC4X3/mm schema and units must be preserved")
    roots0,roots1=_root_map(old),_root_map(result)
    require(set(roots0)<=set(roots1),"Original native Root GUID disappeared")
    for gid,entity in roots0.items():
        now=roots1[gid]
        require(entity.is_a()==now.is_a(),
                "Existing original IFC Root class mutated")
        for attr in ("Name","Description"):
            require(getattr(entity,attr,None)==getattr(now,attr,None),
                    "Existing original IFC Root Name/Description changed")
    originals={e.GlobalId:e for e in old.by_type("IfcProduct")}
    after={e.GlobalId:e for e in result.by_type("IfcProduct")}
    require(set(originals)<=set(after),
            "Original native IfcProduct removed from output")
    added={gid:e for gid,e in after.items() if gid not in originals}
    require(Counter(e.is_a() for e in added.values())==Counter({"IfcWall":1}),
            "Exactly one real native IfcWall must be newly created")
    newwall=next(iter(added.values()))
    extra_roots={gid:r for gid,r in roots1.items() if gid not in roots0}
    require(all(r.is_a() in ("IfcWall","IfcRelContainedInSpatialStructure")
                for r in extra_roots.values()),
            "Unapproved new original-native IfcRoot appeared")
    edges0,edges1=_edges(old),_edges(result)
    require(edges0<=edges1,"Original Space/Storey/Wall explicit IFC relationship changed")
    additions=edges1-edges0
    require(all((kind=="IfcRelContainedInSpatialStructure" and dst==newwall.GlobalId)
                for kind,src,dst in additions),
            "Original native source gained an invented SpaceBoundary or unrelated relationship")
    require(len(old.by_type("IfcRelSpaceBoundary"))==0
            and len(result.by_type("IfcRelSpaceBoundary"))==0,
            "Neither source has real space boundaries; IFC must not invent any")
    rooms0=old.by_type("IfcSpace")
    rooms1=result.by_type("IfcSpace")
    want_count=1 if task_id=="topological_test_01" else 2
    require(len(rooms0)==len(rooms1)==want_count,
            "Original source native IfcSpace count did not survive")
    expected_meshes={
        "topological_test_01":(12,),
        "topological_test_03":(20,20),
    }[task_id]
    require(tuple(sorted(_world_mesh(x)[2] for x in rooms0))==
            tuple(sorted(expected_meshes)),
            "Published original native Room physical mesh triangle count drifted")
    for space in rooms0:
        new=result.by_guid(space.GlobalId)
        require(new is not None and new.is_a("IfcSpace"),
                "Original native room GUID lost")
        agg0=ifcopenshell.util.element.get_aggregate(space)
        agg1=ifcopenshell.util.element.get_aggregate(new)
        require(agg0 is not None and agg1 is not None
                and agg0.is_a("IfcBuildingStorey")
                and agg0.GlobalId==agg1.GlobalId,
                "Source native Room aggregate-to-Storey relationship changed")
        require(len(space.BoundedBy)==len(new.BoundedBy)==0,
                "Nonexistent original Room boundary falsely fabricated")
    checked=0
    checked_triangles=0
    for gid,source in originals.items():
        revised=after[gid]
        require(source.is_a()==revised.is_a(),
                "Original native product type changed")
        if source.Representation is None:
            require(revised.Representation is None,
                    "Original non-geometric product now has invented geometry")
            continue
        left,right=_world_mesh(source),_world_mesh(revised)
        require(left[2]==right[2]
                and left[4]==right[4] and left[5]==right[5],
                "Unrelated original IFC world mesh geometry or physical planar faces changed")
        checked+=1
        checked_triangles+=left[2]
    require(newwall.Representation is not None,
            "New native Wall has no physical representation")
    lo,hi,n,*_=_world_mesh(newwall)
    require(n>=12 and all(.05<hi[i]-lo[i]<50. for i in range(3)),
            "New native Wall world body is not physically valid")
    try:
        root=etree.fromstring(submitted_xml)
    except etree.XMLSyntaxError as exc:
        raise IndependentRoomNativeError("Submitted P2 source XML cannot be parsed") from exc
    require(root.tag==Q+"Building", "No full P2 declarative Building XML supplied")
    refs=root.findall("./"+Q+"OriginalNativeRoomEvidence")
    require(len(refs)==1, "Submitted P2 source is missing read-only original room evidence")
    elements=root.find(Q+"Elements")
    new_walls=[x for x in elements if x.tag==Q+"Wall" and not x.get("ifcGuid")]
    require(len(new_walls)==1 and new_walls[0].get("id"),
            "One and only one new declarative Wall must match native write")
    xml=new_walls[0]
    a=(float(xml.get("x1")),float(xml.get("y1")))
    b=(float(xml.get("x2")),float(xml.get("y2")))
    h=float(xml.get("height"))
    thickness=float(xml.get("thickness"))
    za=float(xml.get("z1"))
    zb=float(xml.get("z2"))
    require(abs(za-zb)<1e-8,"New illustrative native Wall requires straight planar Axis")
    dx,dy=b[0]-a[0],b[1]-a[1]
    run=math.hypot(dx,dy)
    require(run>.1 and math.isfinite(run),"New Wall native length invalid")
    normal=(-dy/run,dx/run)
    # The default v0.1 native Wall compiler extrudes a source line segment
    # along its left-hand normal from 0 to thickness, not +/- thickness/2.
    # This is independently checked from the ACTUAL restored native mesh.
    corners=[(p[0]+j*normal[0]*thickness,
              p[1]+j*normal[1]*thickness)
             for p in (a,b) for j in (0,1)]
    expected_min=(min(p[0] for p in corners),
                  min(p[1] for p in corners),za)
    expected_max=(max(p[0] for p in corners),
                  max(p[1] for p in corners),za+h)
    require(_near(lo,expected_min) and _near(hi,expected_max),
            "New native Wall actual physical world geometry differs from declarative XML")
    xmllevel=next((x for x in root.findall("./"+Q+"Levels/"+Q+"Level")
                   if x.get("id")==xml.get("level")),None)
    require(xmllevel is not None and xmllevel.get("ifcGuid") in {
        x.GlobalId for x in old.by_type("IfcBuildingStorey")},
        "Declarative new Wall does not reference an original native Storey")
    require(any(kind=="IfcRelContainedInSpatialStructure"
                and relating==xmllevel.get("ifcGuid")
                and related==newwall.GlobalId
                for kind,relating,related in additions),
            "Native Wall not placed in declared real original Storey")
    require(file_hash(original_mm)==PINS[task_id],
            "Original published source IFC changed during physical oracle")
    return {
        "status":"INDEPENDENT_ORIGINAL_IFC4X3_ROOM_AND_WALL_NATIVE_PRESERVATION_PASS",
        "original_native_schema_and_mm_preserved":True,
        "original_Root_guids_and_classes_names_preserved":len(roots0),
        "original_native_IfcProducts_preserved":len(originals),
        "source_native_IfcSpaces_preserved":len(rooms0),
        "all_original_native_Space_meshes_and_Storey_aggregates_unchanged":True,
        "original_explicit_IfcRelSpaceBoundary_count":0,
        "output_explicit_IfcRelSpaceBoundary_count":0,
        "original_explicit_topology_edges_preserved":len(edges0),
        "original_world_mesh_products_preserved":checked,
        "original_world_mesh_triangles_preserved":checked_triangles,
        "one_new_original_native_IfcWall_saved":True,
        "new_wall_world_bounds_m":{
            "min":tuple(round(float(x),6) for x in lo),
            "max":tuple(round(float(x),6) for x in hi),
            "triangles":n,
        },
        "full_original_STEP_entity_byte_parity_proven":False,
        "original_room_adjacency_inferred_or_fabricated":False,
        "original_source_IFC_mutated":False,
    }
