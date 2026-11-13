"""Independent IFC4X3 native compatibility and actual edit oracle for v0.7.

No import of projection, compiler, binder, v0.4/v0.3 mutation helpers or
original BIBIMBAP scorer. Source/result IFC native representations and
world-space mesh vertices are inspected using IfcOpenShell directly.

This is only task-scoped native geometry correctness, NOT all-45 parity.
"""
from __future__ import annotations

from collections import Counter
from itertools import product
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit
import numpy as np
from lxml import etree

from tools.bibimbap_matched25_tools import file_hash

NS="{urn:bim-markup-bench:toy:v0}"
TOL=2e-5


class IndependentV7Error(ValueError):
    pass


def _read(source,result=None):
    if not source.is_file() or source.is_symlink():
        raise IndependentV7Error("Native IFC source absent or symlink")
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(result)) if result is not None else None
    if result is not None and (
        not result.is_file() or result.is_symlink()
        or source.resolve()==result.resolve() or a.schema!=b.schema
    ):
        raise IndependentV7Error("Valid distinct original/candidate IFC and identical schema needed")
    return a,b


def _vertices(f,entity):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        shape=ifcopenshell.geom.create_shape(settings,entity)
        points=np.asarray(shape.geometry.verts,dtype=float).reshape((-1,3))
        faces=np.asarray(shape.geometry.faces,dtype=int).reshape((-1,3))
    except Exception as exc:
        raise IndependentV7Error("Native IFC world solid unavailable") from exc
    if len(points)<4 or len(faces)<4 or not np.isfinite(points).all():
        raise IndependentV7Error("Native IFC mesh incomplete")
    return points,faces


def _same_points(a,b):
    if a.shape!=b.shape:
        return False
    if np.allclose(a,b,atol=TOL,rtol=0):
        return True
    # Rigidly translated mapped representations usually preserve order,
    # but sorting complete 3D vertices also tolerates re-tessellation order.
    seq_a=a[np.lexsort((a[:,2],a[:,1],a[:,0]))]
    seq_b=b[np.lexsort((b[:,2],b[:,1],b[:,0]))]
    return bool(np.allclose(seq_a,seq_b,atol=TOL,rtol=0))


def _actual_box(f,entity):
    points,faces=_vertices(f,entity)
    if len(points)!=8 or len(faces)!=12:
        raise IndependentV7Error("Not an 8-vertex, 12-triangle native IFC prism")
    low=points.min(axis=0)
    high=points.max(axis=0)
    sizes=high-low
    if np.any(sizes<=0.01) or np.any(sizes>10000):
        raise IndependentV7Error("Degenerate native box world dimensions")
    expected=np.asarray(list(product(*zip(low,high))),dtype=float)
    hits=np.array([[np.max(np.abs(v-e))<=TOL for e in expected] for v in points])
    if not np.all(hits.sum(0)==1) or not np.all(hits.sum(1)==1):
        raise IndependentV7Error("Tilted/nonrectangular geometry misrepresented as AABB")
    count=Counter()
    areas=Counter()
    for triangle in faces:
        q=points[triangle]
        area=float(np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))/2.)
        matches=[
            (i,j) for i in range(3)
            for j,bound in ((0,low[i]),(1,high[i]))
            if np.all(abs(q[:,i]-bound)<=TOL)
        ]
        if len(matches)!=1 or area<=0:
            raise IndependentV7Error("Native box has oblique/degenerate face")
        k=matches[0]
        count[k]+=1
        areas[k]+=area
    for i in range(3):
        other=[j for j in range(3) if j!=i]
        expected_area=float(sizes[other[0]]*sizes[other[1]])
        for j in range(2):
            if count[(i,j)]!=2 or not math.isclose(
                areas[(i,j)],expected_area,rel_tol=1e-8,abs_tol=1e-5
            ):
                raise IndependentV7Error("Native box triangular faces incomplete")
    return low,high


def verify_v7_projected_source(original:Path,metre_clone:Path,xml:bytes):
    """Independent IFC native source continuity and honest XML envelope check.

    Older v0.1/v0.4 parser is NOT imported. LXML is used as a neutral
    XML reader; IFC authoritative geometry controls acceptance.
    """
    raw,_=_read(original)
    native,_=_read(metre_clone)
    if raw.schema!="IFC4X3" or native.schema!=raw.schema:
        raise IndependentV7Error("v0.7 only claims IFC4X3 native projection")
    if not math.isclose(ifcopenshell.util.unit.calculate_unit_scale(native),1.,abs_tol=1e-8):
        raise IndependentV7Error("v0.7 projected IFC clone must be in metres")
    orig_roots={x.GlobalId:x.is_a() for x in raw.by_type("IfcRoot")}
    cloned_roots={x.GlobalId:x.is_a() for x in native.by_type("IfcRoot")}
    if orig_roots!=cloned_roots:
        raise IndependentV7Error("Original native IFC Root inventory changed during metre conversion")
    root=etree.fromstring(xml)
    if (root.tag!=NS+"Building"
        or root.get("sourceModelSha256")!=file_hash(metre_clone)
        or root.get("ifcSchema")!="IFC4X3"
        or root.get("units")!="m"):
        raise IndependentV7Error("XML source hash/schema/units improperly represented")
    projected=[]
    levels=root.findall("./"+NS+"Levels/"+NS+"Level")
    native_levels={x.GlobalId:x for x in native.by_type("IfcBuildingStorey")}
    if not levels:
        raise IndependentV7Error("IFC4X3 projection has no native explicit storeys")
    ids=set()
    for level in levels:
        guid=level.get("ifcGuid")
        if guid not in native_levels or level.get("id") in ids:
            raise IndependentV7Error("XML storey missing or duplicate")
        if native_levels[guid].Elevation is None or not math.isclose(
            float(level.get("elevation")),float(native_levels[guid].Elevation),abs_tol=TOL
        ):
            raise IndependentV7Error("XML native storey elevation is fabricated")
        ids.add(level.get("id"))
    levelids={x.get("id"):x.get("ifcGuid") for x in levels}
    for node in root.findall("./"+NS+"Elements/*"):
        kind=etree.QName(node).localname
        if kind not in ("Column","Slab"):
            raise IndependentV7Error("Read-only bootstrap claims unsupported element class")
        guid=node.get("ifcGuid")
        if guid not in cloned_roots or node.get("id") in ids:
            raise IndependentV7Error("Projected native product identity invalid")
        obj=native.by_guid(guid)
        if obj.is_a()!="Ifc"+kind:
            raise IndependentV7Error("Projected IFC entity class false")
        storey=ifcopenshell.util.element.get_container(obj)
        if storey is None or levelids.get(node.get("level"))!=storey.GlobalId:
            raise IndependentV7Error("Projected native IFC storey false")
        lo,hi=_actual_box(native,obj)
        values=np.asarray([
            float(node.get("x")),float(node.get("y")),float(node.get("z"))
        ])
        ext=np.asarray([
            float(node.get("width")),float(node.get("depth")),
            float(node.get("thickness" if kind=="Slab" else "height")),
        ])
        if not np.allclose(values,lo,atol=TOL,rtol=0) or not np.allclose(
            ext,hi-lo,atol=TOL,rtol=0
        ):
            raise IndependentV7Error("Native IFC source geometry differs from XML declared bbox")
        ids.add(node.get("id"))
        projected.append(guid)
    if not projected:
        raise IndependentV7Error("No physically provable source IFC object projected")
    return {
        "status":"INDEPENDENT_V7_ORIGINAL_IFC4X3_PARTIAL_PROJECTION_VALIDATED",
        "original_schema":raw.schema,
        "original_raw_ifc_sha256":file_hash(original),
        "metre_clone_sha256":file_hash(metre_clone),
        "all_original_root_globalids_preserved":len(orig_roots),
        "verified_exact_box_elements":len(projected),
        "verified_projected_globalids":sorted(projected),
        "unprojected_source_entities_remain_native_ifc":True,
        "all45_original_d0_editing_validated":False,
    }


def _check_other_products(a,b,excluded):
    products_a={p.GlobalId:p for p in a.by_type("IfcProduct")}
    products_b={p.GlobalId:p for p in b.by_type("IfcProduct")}
    if set(products_a)-set(excluded)!=set(products_b)-set(excluded):
        raise IndependentV7Error("Original native IFC Product identity changed")
    checked=0
    for gid in set(products_a)&set(products_b)-set(excluded):
        x,y=products_a[gid],products_b[gid]
        if str(x)!=str(y):
            raise IndependentV7Error("Surviving original IFC Product metadata changed")
        if x.Representation is not None and y.Representation is not None:
            v0,f0=_vertices(a,x);v1,f1=_vertices(b,y)
            if len(f0)!=len(f1) or not _same_points(v0,v1):
                raise IndependentV7Error("Unrelated native Product world mesh changed")
            checked+=1
    return checked


def verify_column_move(source:Path,result:Path,guid:str,delta_m):
    a,b=_read(source,result)
    if a.schema!="IFC4X3":
        raise IndependentV7Error("Native Column move requires IFC4X3")
    delta=np.asarray(delta_m,dtype=float)
    if delta.shape!=(3,) or np.any(np.abs(delta)>100) or not np.isfinite(delta).all():
        raise IndependentV7Error("Invalid declared native Column translation")
    src=a.by_guid(guid);dst=b.by_guid(guid)
    if not src.is_a("IfcColumn") or not dst.is_a("IfcColumn"):
        raise IndependentV7Error("Target native IFC Column missing")
    before,faces=_vertices(a,src)
    after,faces_after=_vertices(b,dst)
    if len(faces)!=len(faces_after) or not _same_points(before+delta,after):
        raise IndependentV7Error("Full world mapped Column native mesh did not translate")
    orig_roots={x.GlobalId:str(x) for x in a.by_type("IfcRoot")}
    next_roots={x.GlobalId:str(x) for x in b.by_type("IfcRoot")}
    if orig_roots!=next_roots:
        raise IndependentV7Error("Column edit changed original IFC Root semantics")
    old={e.id():str(e) for e in a}
    new={e.id():str(e) for e in b}
    original_point=src.ObjectPlacement.RelativePlacement.Location
    after_point=dst.ObjectPlacement.RelativePlacement.Location
    if (set(old)!=set(new) or
        {i for i in old if old[i]!=new[i]}!={original_point.id()}
        or after_point.id()!=original_point.id()):
        raise IndependentV7Error("Column edit changed mapped geometry/STEP besides placement point")
    members=_check_other_products(a,b,{guid})
    return {
        "status":"INDEPENDENT_ORIGINAL_MAPPED_COLUMN_NATIVE_TRANSLATION_VALIDATED",
        "source_sha256":file_hash(source),
        "candidate_sha256":file_hash(result),
        "target_original_column_guid":guid,
        "native_world_shift_metres":delta.tolist(),
        "all_original_root_globalids_and_attrs_preserved":len(orig_roots),
        "other_original_world_mesh_products_preserved":members,
        "native_ifc_step_changed_point_only":original_point.id(),
        "all45_parity":False,
    }


def verify_slab_create(source:Path,result:Path,new_guid:str,*,minimum,maximal):
    a,b=_read(source,result)
    if a.schema!="IFC4X3":
        raise IndependentV7Error("Native Slab create requires IFC4X3")
    original_roots={x.GlobalId:x for x in a.by_type("IfcRoot")}
    new_roots={x.GlobalId:x for x in b.by_type("IfcRoot")}
    if new_guid in original_roots or new_guid not in new_roots:
        raise IndependentV7Error("New original Slab GUID invalid")
    obj=b.by_guid(new_guid)
    if not obj.is_a("IfcSlab") or len(b.by_type("IfcSlab"))!=len(a.by_type("IfcSlab"))+1:
        raise IndependentV7Error("New native IFC Slab identity/count invalid")
    lo,hi=_actual_box(b,obj)
    if not np.allclose(lo,minimum,atol=TOL) or not np.allclose(hi,maximal,atol=TOL):
        raise IndependentV7Error("New native IFC physical Slab wrong world dimensions")
    if set(original_roots)-set(new_roots):
        raise IndependentV7Error("Original IFC Root lost when adding native Slab")
    for gid,prev in original_roots.items():
        current=new_roots[gid]
        if prev.is_a()=="IfcRelContainedInSpatialStructure":
            orig={x.GlobalId for x in prev.RelatedElements}
            later={x.GlobalId for x in current.RelatedElements}
            if later not in (orig,orig|{new_guid}):
                raise IndependentV7Error("Original IFC storey containment damaged")
        elif str(prev)!=str(current):
            raise IndependentV7Error("Original IFC Root unexpectedly mutated")
    storey=ifcopenshell.util.element.get_container(obj)
    if storey is None or not storey.is_a("IfcBuildingStorey"):
        raise IndependentV7Error("Created native Slab not contained in original storey")
    rels=[r for r in b.by_type("IfcRelContainedInSpatialStructure")
          if new_guid in {x.GlobalId for x in r.RelatedElements}]
    if len(rels)!=1 or rels[0].RelatingStructure.GlobalId!=storey.GlobalId:
        raise IndependentV7Error("New native Slab has unexpected/duplicate containment")
    old_step={e.id():str(e) for e in a}
    new_step={e.id():str(e) for e in b}
    if not set(old_step)<=set(new_step):
        raise IndependentV7Error("Native Slab creation deleted old STEP entities")
    changed={i for i in old_step if old_step[i]!=new_step[i]}
    allowed={x.id() for x in a.by_type("IfcRelContainedInSpatialStructure")}
    if not changed<=allowed:
        raise IndependentV7Error("Native Slab created changes in original non-containment STEP entity")
    preserved=_check_other_products(a,b,{new_guid})
    return {
        "status":"INDEPENDENT_NATIVE_SLAB_CREATED_IN_PREVIOUSLY_OPAQUE_INPUT",
        "source_sha256":file_hash(source),
        "candidate_sha256":file_hash(result),
        "new_original_ifc_slab_guid":new_guid,
        "native_world_box_min_metres":tuple(float(x) for x in lo),
        "native_world_box_max_metres":tuple(float(x) for x in hi),
        "other_original_world_mesh_products_preserved":preserved,
        "original_globalids_preserved":len(original_roots),
        "source_original_step_noncontainment_unchanged":True,
        "all45_parity":False,
    }
