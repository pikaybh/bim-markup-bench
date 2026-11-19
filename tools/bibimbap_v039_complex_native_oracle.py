"""Independent v0.39 actual restored mm IFC oracle for mapped source columns and clipped walls.

Reads original real IFC and separately reopened candidate. Does not import the
v0.39 XML compiler, author grader, hidden ground truth, or provider code.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.unit
from lxml import etree

from tools.bibimbap_v038_legacy_live_gate import _world_mesh
from tools.bibimbap_matched25_tools import file_hash

PINS={
    "geometry_test_01":"d7a0c0bda9572787b5b8e7a57b48f8157d898a9f444ac28978e9f9b9a8ff9702",
    "topological_test_05":"c0e0019d7224185d5872b80bdd3652da2bc960b819c1d8c0dd03b213b14847ca",
}
Q="{urn:bim-markup-bench:complex-native:v0.39}"


class IndependentComplexNativeError(ValueError):
    pass


def require(yes,why):
    if not yes:
        raise IndependentComplexNativeError(why)


def _native_roots(f):
    rows={x.GlobalId:x for x in f.by_type("IfcRoot")}
    require(len(rows)==len(f.by_type("IfcRoot")),"Native original GUID collision")
    return rows


def _native_edges(f):
    edges=set()
    for kind,srcfield,dstfield in (
        ("IfcRelVoidsElement","RelatingBuildingElement","RelatedOpeningElement"),
        ("IfcRelFillsElement","RelatingOpeningElement","RelatedBuildingElement"),
    ):
        for rel in f.by_type(kind):
            edges.add((kind,getattr(rel,srcfield).GlobalId,
                       getattr(rel,dstfield).GlobalId))
    for rel in f.by_type("IfcRelContainedInSpatialStructure"):
        for obj in rel.RelatedElements:
            edges.add((rel.is_a(),rel.RelatingStructure.GlobalId,obj.GlobalId))
    for rel in f.by_type("IfcRelAggregates"):
        for obj in rel.RelatedObjects:
            edges.add((rel.is_a(),rel.RelatingObject.GlobalId,obj.GlobalId))
    return edges


def _eq(a,b,tol=.00001):
    return len(a)==len(b) and all(abs(float(x)-float(y))<=tol for x,y in zip(a,b))


def verify_complex_original_restored(
        original_mm:Path,restored_mm:Path,*,task_id:str,
        submitted_xml:bytes)->dict:
    require(task_id in PINS and file_hash(original_mm)==PINS[task_id],
            "Original P1 native source SHA changed")
    require(original_mm.is_file() and restored_mm.is_file()
            and not original_mm.is_symlink() and not restored_mm.is_symlink()
            and original_mm.resolve()!=restored_mm.resolve(),
            "Native source/candidate must be distinct physical files")
    src=ifcopenshell.open(str(original_mm))
    candidate=ifcopenshell.open(str(restored_mm))
    for f in (src,candidate):
        require(f.schema=="IFC4X3" and abs(
            ifcopenshell.util.unit.calculate_unit_scale(f)-.001)<1e-12,
            "Original IFC4X3 native-millimetre schema/units changed")
    oldroots,newroots=_native_roots(src),_native_roots(candidate)
    require(set(oldroots)<=set(newroots),"Original native IFC Root missing")
    for gid,old in oldroots.items():
        now=newroots[gid]
        require(old.is_a()==now.is_a(),
                "Original native IFC Root type was changed")
        for label in ("Name","Description"):
            require(getattr(old,label,None)==getattr(now,label,None),
                    "Original native IFC Root Name/Description was altered")
    oldproducts={p.GlobalId:p for p in src.by_type("IfcProduct")}
    newproducts={p.GlobalId:p for p in candidate.by_type("IfcProduct")}
    require(set(oldproducts)<=set(newproducts),
            "Source native original IFC Product disappeared")
    added={g:x for g,x in newproducts.items() if g not in oldproducts}
    wanted={
        "geometry_test_01":Counter({"IfcSlab":1}),
        "topological_test_05":Counter({"IfcOpeningElement":1,"IfcDoor":1}),
    }[task_id]
    require(Counter(x.is_a() for x in added.values())==wanted,
            "Output did not contain exactly the permitted new native Products")
    allowed={"IfcSlab","IfcOpeningElement","IfcDoor",
             "IfcRelContainedInSpatialStructure",
             "IfcRelVoidsElement","IfcRelFillsElement"}
    require(all(x.is_a() in allowed for g,x in newroots.items()
                if g not in oldroots),
            "Unexpected new native IFC Root/relation appeared")
    oldedges=_native_edges(src)
    nowedges=_native_edges(candidate)
    require(oldedges<=nowedges,
            "Original IFC Containment/Aggregation/Void/Fill relationship changed")
    appended=nowedges-oldedges
    require(all(g in added or h in added for _,g,h in appended),
            "Unrelated original native relationship mutated")
    try:
        root=etree.fromstring(submitted_xml)
    except etree.XMLSyntaxError as exc:
        raise IndependentComplexNativeError("Submitted XML cannot be independently read") from exc
    require(root.tag==Q+"Building","Submitted XML is not P1 declarative Building state")
    elements=list(root.find(Q+"Elements"))
    host=None
    if task_id=="topological_test_05":
        voids=[e for e in appended if e[0]=="IfcRelVoidsElement"]
        require(len(voids)==1,"Original clipped Wall needs exactly one new physical void")
        host=voids[0][1]
        require(host in oldproducts and oldproducts[host].is_a()=="IfcWall",
                "Door opening not attached to an original native source Wall")
    unchanged_products=0
    unchanged_triangles=0
    for g,original in oldproducts.items():
        revised=newproducts[g]
        require(original.is_a()==revised.is_a(),
                "Original native IFC Product type changed")
        if original.Representation is None:
            require(revised.Representation is None,
                    "Original IFC Product unexpectedly gained fake geometry")
            continue
        a,b=_world_mesh(original),_world_mesh(revised)
        if g==host:
            require(any(rep.RepresentationType=="Clipping"
                        for rep in original.Representation.Representations)
                    and any(rep.RepresentationType=="Clipping"
                        for rep in revised.Representation.Representations)
                    and _eq(a[0],b[0]) and _eq(a[1],b[1])
                    and b[2]>a[2],
                    "Native clipped original host Wall was not physically opened")
        else:
            require(a[2]==b[2] and a[4]==b[4] and a[5]==b[5],
                    "Unrelated original native product mesh geometry changed")
            unchanged_products+=1
            unchanged_triangles+=a[2]
    physical={}
    for gid,entity in added.items():
        require(entity.Representation is not None,
                "New native Product physical Representation is missing")
        lo,hi,tri,*_=_world_mesh(entity)
        dims=tuple(hi[i]-lo[i] for i in range(3))
        require(tri>=12 and all(.04<dim<50. for dim in dims),
                "New native Product has degenerate restored physical shape")
        physical[entity.is_a()]={
            "min_m":tuple(round(x,6) for x in lo),
            "max_m":tuple(round(x,6) for x in hi),
            "triangles":tri}
    original_storeys={x.GlobalId:x for x in src.by_type("IfcBuildingStorey")}
    additions_contained=[e for e in appended
                         if e[0]=="IfcRelContainedInSpatialStructure"]
    if task_id=="geometry_test_01":
        require(len(elements)==1 and elements[0].tag==Q+"Slab",
                "New physical Slab is not the single declarative XML element")
        node=elements[0]
        slab=next(iter(added.values()))
        require(node.get("levelGuid") in original_storeys
                and any(e[1]==node.get("levelGuid") and e[2]==slab.GlobalId
                        for e in additions_contained),
                "New native Slab lacks original source Storey containment")
        point=tuple(float(node.get(x)) for x in ("x","y","z"))
        upper=(point[0]+float(node.get("length")),
               point[1]+float(node.get("depth")),
               point[2]+float(node.get("thickness")))
        require(_eq(physical["IfcSlab"]["min_m"],point)
                and _eq(physical["IfcSlab"]["max_m"],upper),
                "New physical Slab world shape dimensions/position not matching XML")
        require(not any(x[0] in ("IfcRelVoidsElement","IfcRelFillsElement")
                        for x in appended),
                "Unexpected Wall void or Door filling added by Slab")
    else:
        require(len(elements)==2 and elements[0].tag==Q+"Opening"
                and elements[1].tag==Q+"Door",
                "Hosted new Door must have one Opening and one Door in XML")
        op,door_spec=elements
        opening_gid=next(g for g,x in added.items()
                         if x.is_a()=="IfcOpeningElement")
        door_gid=next(g for g,x in added.items() if x.is_a()=="IfcDoor")
        fills=[e for e in appended if e[0]=="IfcRelFillsElement"]
        require(host==op.get("hostGuid")
                and fills==[("IfcRelFillsElement",opening_gid,door_gid)]
                and ("IfcRelVoidsElement",host,opening_gid) in appended
                and door_spec.get("opening")==op.get("id"),
                "Original clipped host wall and Door native fill relationship mismatch")
        actualdoor=added[door_gid]
        # The final file is restored to native MILLIMETRES; physical IfcDoor
        # OverallWidth/Height are native length values, unlike SI mesh vertices.
        require(math.isclose(actualdoor.OverallWidth*.001,
                             float(op.get("width")),abs_tol=1e-5)
                and math.isclose(actualdoor.OverallHeight*.001,
                                 float(op.get("height")),abs_tol=1e-5),
                "New physical Door overall dimensions differ from declarative XML")
        lo,hi,*_=_world_mesh(oldproducts[host])
        along_x=hi[0]-lo[0]>hi[1]-lo[1]
        tangent=0 if along_x else 1
        normal=1-tangent
        require(.15<hi[normal]-lo[normal]<.4
                and hi[tangent]-lo[tangent]>2.*(hi[normal]-lo[normal]),
                "Source original clipped wall is not safely axis aligned")
        center=(float(op.get("centerX")),float(op.get("centerY")))
        for cls,normal_width in (("IfcOpeningElement",hi[normal]-lo[normal]+.2),
                                 ("IfcDoor",.08)):
            p=physical[cls]
            low,high=p["min_m"],p["max_m"]
            require(math.isclose((low[tangent]+high[tangent])/2,
                                 center[tangent],abs_tol=1e-5)
                    and math.isclose((low[normal]+high[normal])/2,
                                     center[normal],abs_tol=1e-5)
                    and math.isclose(high[tangent]-low[tangent],
                                     float(op.get("width")),abs_tol=1e-5)
                    and math.isclose(high[normal]-low[normal],
                                     normal_width,abs_tol=1e-5)
                    and math.isclose(low[2],float(op.get("sillZ")),abs_tol=1e-5)
                    and math.isclose(high[2]-low[2],
                                     float(op.get("height")),abs_tol=1e-5),
                    "Native hosted physical Door/Opening positions differ from XML")
        require(any(x[1] in original_storeys and x[2]==door_gid
                    for x in additions_contained),
                "New Door lacks actual original Storey containment")
        require(not any(x[2]==opening_gid for x in additions_contained),
                "Opening incorrectly treated as a freestanding native product")
    require(file_hash(original_mm)==PINS[task_id],
            "Original source IFC bytes changed after physical validation")
    return {
        "original_native_schema":"IFC4X3",
        "original_native_units_to_m":.001,
        "old_original_Roots_preserved":len(oldroots),
        "old_original_Products_preserved":len(oldproducts),
        "old_native_relationship_edges_preserved":len(oldedges),
        "unchanged_original_physical_mesh_products_verified":unchanged_products,
        "unchanged_original_physical_mesh_triangles_verified":unchanged_triangles,
        "native_created_products_by_class":dict(sorted(wanted.items())),
        "native_created_physical_extents":physical,
        "physical_original_clipped_wall_void_created":host is not None,
        "source_IFC_file_unchanged":True,
        "complete_original_IFC_STEP_byte_parity_proven":False,
        "complete_original_BIM_data_visible_in_XML":False,
    }
