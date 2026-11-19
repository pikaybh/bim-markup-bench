"""Independent native IFC2X3/IFC4 original-source oracle for v0.8.

No import of the v0.8 projection, compiler, XML binder, planner, mutation
API, original BIBIMBAP grader or hidden GT. All evidence derives from
native IFC STEP, original product mesh and original/public instructions.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.shape
import numpy as np


TOL=2e-5
SOUTH_REFERENCE_WALL="3YQ$1CPXD2Mh2vQ18vV$hw"
NORTH_TARGET_WALL="3YQ$1CPXD2Mh2vQ18vV$ig"
ORIGINAL_GEO04_COLUMN="3A5GfH23DBvBYpavCfWh4z"


class IndependentLegacyV8Error(ValueError):
    pass


def _hash(path):
    h=sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def _mesh(f,product):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        shape=ifcopenshell.geom.create_shape(settings,product)
        points=np.asarray(shape.geometry.verts,dtype=float).reshape((-1,3))
        faces=np.asarray(shape.geometry.faces,dtype=int).reshape((-1,3))
        volume=float(ifcopenshell.util.shape.get_volume(shape.geometry))
    except Exception as exc:
        raise IndependentLegacyV8Error("Independent original native IFC geometry absent") from exc
    if len(points)<4 or len(faces)<4 or not np.isfinite(points).all():
        raise IndependentLegacyV8Error("Original or resulting IFC native product mesh invalid")
    return points,faces,volume


def _original_products_preserved(original,candidate,excluded):
    base={x.GlobalId:x for x in original.by_type("IfcProduct")}
    final={x.GlobalId:x for x in candidate.by_type("IfcProduct")}
    if not set(base)<=set(final):
        raise IndependentLegacyV8Error("Original IFC product/root deleted from output")
    physically=0
    for gid,p in base.items():
        q=final[gid]
        if p.is_a()!=q.is_a() or str(p)!=str(q):
            raise IndependentLegacyV8Error("Unrelated original IFC product metadata modified")
        if gid in excluded or p.Representation is None:
            continue
        a,fa,_=_mesh(original,p)
        b,fb,_=_mesh(candidate,q)
        if len(fa)!=len(fb) or a.shape!=b.shape or not np.allclose(
            a,b,rtol=0,atol=TOL
        ):
            raise IndependentLegacyV8Error("Unrelated original IFC native world geometry changed")
        physically+=1
    return physically


def _step_and_roots(original,candidate,created_guids):
    a={x.GlobalId:x for x in original.by_type("IfcRoot")}
    b={x.GlobalId:x for x in candidate.by_type("IfcRoot")}
    if not set(a)<=set(b):
        raise IndependentLegacyV8Error("Original native schema Root GlobalIds not all preserved")
    new=set(b)-set(a)
    if not set(created_guids)<=new:
        raise IndependentLegacyV8Error("Expected original named native candidate not newly added")
    original_step={x.id():str(x) for x in original}
    new_step={x.id():str(x) for x in candidate}
    if not set(original_step)<=set(new_step):
        raise IndependentLegacyV8Error("Original source native STEP entity deleted")
    allowed={x.id() for x in original.by_type("IfcRelContainedInSpatialStructure")}
    changed={k for k in original_step if original_step[k]!=new_step[k]}
    if not changed<=allowed:
        raise IndependentLegacyV8Error("Original source non-containment native STEP changed")
    changed_memberships=0
    for guid,obj in a.items():
        cur=b[guid]
        if obj.is_a()!=cur.is_a():
            raise IndependentLegacyV8Error("Original IFC Root schema type mutated")
        if str(obj)!=str(cur):
            if not obj.is_a("IfcRelContainedInSpatialStructure"):
                raise IndependentLegacyV8Error("Unrelated original IFC Root mutated")
            before={x.GlobalId for x in obj.RelatedElements}
            after={x.GlobalId for x in cur.RelatedElements}
            if not before<=after or len(after-before)!=1 or not (after-before)<=set(created_guids):
                raise IndependentLegacyV8Error("Original native storey containment damaged")
            changed_memberships+=1
    return {
        "source_root_guids_preserved":len(a),
        "source_original_step_entities_preserved":len(original_step),
        "source_noncontainment_step_changes":0,
        "source_containment_relations_growing_by_one":changed_memberships,
        "new_native_root_guids":len(new),
    }


def _first_read(source,candidate,expected_schema):
    if (not source.is_file() or not candidate.is_file()
        or source.is_symlink() or candidate.is_symlink()
        or source.resolve()==candidate.resolve()):
        raise IndependentLegacyV8Error("Independent native IFC source/candidate path is invalid")
    s=ifcopenshell.open(str(source))
    t=ifcopenshell.open(str(candidate))
    if s.schema!=expected_schema or t.schema!=expected_schema:
        raise IndependentLegacyV8Error("Original native IFC schema changed")
    return s,t


def verify_ifc4_wall(source:Path,candidate:Path,new_wall_guid:str):
    a,b=_first_read(source,candidate,"IFC4")
    if new_wall_guid in {x.GlobalId for x in a.by_type("IfcRoot")}:
        raise IndependentLegacyV8Error("Reported new Wall GUID existed in original IFC")
    wall=b.by_guid(new_wall_guid)
    if not wall.is_a("IfcWall"):
        raise IndependentLegacyV8Error("Native original IFC4 Wall class invalid")
    if len(b.by_type("IfcWall"))!=len(a.by_type("IfcWall"))+1:
        raise IndependentLegacyV8Error("Exactly one native IFC4 Wall must be new")
    storey=b.by_type("IfcBuildingStorey")
    if len(storey)!=1 or storey[0].Elevation is not None:
        raise IndependentLegacyV8Error("Missing IFC4 source Storey Elevation was fabricated")
    assigned=ifcopenshell.util.element.get_container(wall)
    if assigned is None or assigned.GlobalId!=storey[0].GlobalId:
        raise IndependentLegacyV8Error("New native Wall not under original missing-elevation Storey")
    verts,faces,_=_mesh(b,wall)
    if (len(verts)!=8 or len(faces)!=12
        or not np.allclose(verts.min(0),(10,5,0),rtol=0,atol=TOL)
        or not np.allclose(verts.max(0),(15,5.2,3),rtol=0,atol=TOL)):
        raise IndependentLegacyV8Error("Native IFC4 Wall not original public 5m +X at (10,5)")
    preserved=_original_products_preserved(a,b,set())
    inventory=_step_and_roots(a,b,{new_wall_guid})
    if inventory["source_containment_relations_growing_by_one"]!=0:
        raise IndependentLegacyV8Error("Empty original IFC4 storey had unexpected original containment")
    return {
        "status":"INDEPENDENT_NATIVE_ORIGINAL_IFC4_PUBLIC_WALL_CREATE_PASS",
        "source_sha256":_hash(source),
        "candidate_sha256":_hash(candidate),
        "new_wall_guid":new_wall_guid,
        "native_mesh_bbox_min_m":[10,5,0],
        "native_mesh_bbox_max_m":[15,5.2,3],
        "original_storey_elevation_remains_missing":True,
        "all_original_products_world_mesh_preserved":preserved,
        **inventory,
        "full_45_parity":False,
    }


def verify_ifc2x3_space(source:Path,candidate:Path,new_space_guid:str,
                        minimum=(.2,.2,0),maximum=(6.3,6.7,2.8)):
    a,b=_first_read(source,candidate,"IFC2X3")
    sp=b.by_guid(new_space_guid)
    if (not sp.is_a("IfcSpace") or
        len(b.by_type("IfcSpace"))!=len(a.by_type("IfcSpace"))+1):
        raise IndependentLegacyV8Error("Native IFC2X3 Space class/unique count incorrect")
    storey=ifcopenshell.util.element.get_aggregate(sp)
    if storey is None or not storey.is_a("IfcBuildingStorey"):
        raise IndependentLegacyV8Error("Native spatial IfcSpace not aggregated under original source Storey")
    if storey.GlobalId not in {s.GlobalId for s in a.by_type("IfcBuildingStorey")}:
        raise IndependentLegacyV8Error("IFC2X3 Space references invented Storey")
    col=a.by_guid(ORIGINAL_GEO04_COLUMN)
    colmesh,_,_=_mesh(a,col)
    points,faces,_=_mesh(b,sp)
    if (len(points)!=8 or len(faces)!=12
        or not np.allclose(points.min(0),minimum,atol=TOL,rtol=0)
        or not np.allclose(points.max(0),maximum,atol=TOL,rtol=0)):
        raise IndependentLegacyV8Error("Native original IFC2X3 Space geometry differs from developer XML")
    if float(points.max(0)[0])>=float(colmesh.min(0)[0])-TOL:
        raise IndependentLegacyV8Error("New IFC2X3 Space is not strictly left of original public Column")
    preserved=_original_products_preserved(a,b,set())
    inventory=_step_and_roots(a,b,{new_space_guid})
    if inventory["source_containment_relations_growing_by_one"]!=0:
        raise IndependentLegacyV8Error("Space should aggregate, not alter original wall containment")
    return {
        "status":"INDEPENDENT_NATIVE_ORIGINAL_IFC2X3_SPACE_CREATE_PASS",
        "source_sha256":_hash(source),
        "candidate_sha256":_hash(candidate),
        "new_space_guid":new_space_guid,
        "native_mesh_min_m":list(minimum),
        "native_mesh_max_m":list(maximum),
        "original_reference_column_guid":ORIGINAL_GEO04_COLUMN,
        "spatial_aggregated_under_source_storey_guid":storey.GlobalId,
        "all_original_products_world_mesh_preserved":preserved,
        **inventory,
        "full_45_parity":False,
    }


def verify_ifc2x3_hosted_door(source:Path,candidate:Path,
                              new_opening_guid:str,new_door_guid:str):
    a,b=_first_read(source,candidate,"IFC2X3")
    opening=b.by_guid(new_opening_guid)
    door=b.by_guid(new_door_guid)
    if (not opening.is_a("IfcOpeningElement") or not door.is_a("IfcDoor")
        or len(b.by_type("IfcDoor"))!=len(a.by_type("IfcDoor"))+1
        or len(b.by_type("IfcOpeningElement"))!=len(a.by_type("IfcOpeningElement"))+1):
        raise IndependentLegacyV8Error("New IFC2X3 Opening and Door missing or duplicated")
    if (len(opening.VoidsElements)!=1 or len(door.FillsVoids)!=1
        or opening.VoidsElements[0].RelatingBuildingElement.GlobalId!=NORTH_TARGET_WALL
        or door.FillsVoids[0].RelatingOpeningElement.GlobalId!=new_opening_guid):
        raise IndependentLegacyV8Error("Original source Wall void + Door filling relationships invalid")
    north=b.by_guid(NORTH_TARGET_WALL)
    south=a.by_guid(SOUTH_REFERENCE_WALL)
    p_north_before,faces0,volume0=_mesh(a,a.by_guid(NORTH_TARGET_WALL))
    p_south,_,_=_mesh(a,south)
    p_after,faces1,volume1=_mesh(b,north)
    if not (p_north_before.min(0)[1]>p_south.min(0)[1]
            and p_north_before.min(0)[1]>p_south.max(0)[1]):
        raise IndependentLegacyV8Error("Door target Wall is not north of original named Wall")
    if (len(faces1)<=len(faces0) or
        not np.allclose(p_after.min(0),p_north_before.min(0),atol=TOL)
        or not np.allclose(p_after.max(0),p_north_before.max(0),atol=TOL)):
        raise IndependentLegacyV8Error("Actual original IFC Wall does not contain physical cut")
    cut=volume0-volume1
    if not math.isclose(cut,1.*.2*2.1,abs_tol=2e-4,rel_tol=1e-4):
        raise IndependentLegacyV8Error("Original IFC Wall solid volume has wrong physical Door void")
    open_points,open_faces,_=_mesh(b,opening)
    door_points,door_faces,_=_mesh(b,door)
    if (len(open_points)!=8 or len(open_faces)!=12
        or not np.allclose(open_points.min(0),(-.5,1.4,0),atol=TOL)
        or not np.allclose(open_points.max(0),(.5,1.8,2.1),atol=TOL)
        or not np.allclose(door_points.min(0),(-.5,1.56,0),atol=TOL)
        or not np.allclose(door_points.max(0),(.5,1.64,2.1),atol=TOL)):
        raise IndependentLegacyV8Error("Native IFC Door or actual Opening is not at developer declared location")
    container=ifcopenshell.util.element.get_container(door)
    if (container is None or container.GlobalId not in
        {x.GlobalId for x in a.by_type("IfcBuildingStorey")}):
        raise IndependentLegacyV8Error("Native IFC2X3 Door not contained in original Storey")
    preserved=_original_products_preserved(a,b,{NORTH_TARGET_WALL})
    inventory=_step_and_roots(a,b,{new_opening_guid,new_door_guid})
    if inventory["source_containment_relations_growing_by_one"]!=1:
        raise IndependentLegacyV8Error("New IFC2X3 Door did not extend exactly one original spatial containment")
    return {
        "status":"INDEPENDENT_NATIVE_ORIGINAL_IFC2X3_HOSTED_DOOR_CREATE_PASS",
        "source_sha256":_hash(source),
        "candidate_sha256":_hash(candidate),
        "new_opening_guid":new_opening_guid,
        "new_door_guid":new_door_guid,
        "original_named_south_wall_guid":SOUTH_REFERENCE_WALL,
        "actual_void_host_north_wall_guid":NORTH_TARGET_WALL,
        "host_wall_physical_void_volume_cubic_m":cut,
        "original_south_wall_unchanged":True,
        "all_other_original_product_world_mesh_preserved":preserved,
        **inventory,
        "full_45_parity":False,
    }
