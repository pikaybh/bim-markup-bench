"""Independent IFC4X3 native-only Wall pose/length/delete D0 oracle.

No import of XML compiler/projection, semantic binder, planner or original
author grader. Strict on unchanged IFC Roots/products, native STEP entity
inventory and geometric world-mesh positions. Not a building-wide clash or
100% of original BIBIMBAP tasks oracle.
"""
from __future__ import annotations

from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

from tools.bibimbap_matched25_tools import file_hash

EPS=3e-5


class NativeWallV5OracleError(ValueError):
    pass


def _models(source:Path,candidate:Path):
    if not source.is_file() or not candidate.is_file() or source.resolve()==candidate.resolve():
        raise NativeWallV5OracleError("Distinct source/output IFC files required")
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(candidate))
    if a.schema!="IFC4X3" or b.schema!=a.schema:
        raise NativeWallV5OracleError("Independent native IFC schema mismatch")
    for f in (a,b):
        if abs(ifcopenshell.util.unit.calculate_unit_scale(f)-1.0)>1e-8:
            raise NativeWallV5OracleError("Native wall oracle requires metres")
    return a,b


def _coords(wall):
    transform=np.asarray(ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement),
                         dtype=float)
    axes=[x for rep in wall.Representation.Representations
          if rep.RepresentationType=="Curve2D" for x in rep.Items
          if x.is_a("IfcPolyline") and len(x.Points)==2]
    if len(axes)!=1:
        raise NativeWallV5OracleError("Wall native Curve2D axis is not unique")
    out=[]
    for item in axes[0].Points:
        x,y=(float(c) for c in item.Coordinates[:2])
        p=transform@np.array((x,y,0.,1.),dtype=float)
        out.append(tuple(float(v) for v in p[:3]))
    return tuple(out)


def _mesh(wall):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        shape=ifcopenshell.geom.create_shape(settings,wall)
    except Exception as exc:
        raise NativeWallV5OracleError("Independent IFC geometry kernel failed") from exc
    v=np.asarray(shape.geometry.verts,dtype=float)
    if not len(v) or len(v)%3 or not np.isfinite(v).all():
        raise NativeWallV5OracleError("Original or new native wall mesh invalid")
    return v.reshape((-1,3))


def _near(a,b):
    return np.allclose(a,b,atol=EPS,rtol=0)


def _mesh_set_equal(a,b):
    if a.shape!=b.shape:
        return False
    # Round world coordinates at submillimeter tolerance then compare
    # all complete 3D corners, rather than column-wise sort which could
    # combine unrelated vertices.
    aa=sorted(tuple(float(round(v,5)) for v in pt) for pt in a)
    bb=sorted(tuple(float(round(v,5)) for v in pt) for pt in b)
    return all(_near(x,y) for x,y in zip(aa,bb))


def _products_preserved(a,b,removed_guid=None,edited_guid=None):
    old={x.GlobalId:x for x in a.by_type("IfcProduct")}
    new={x.GlobalId:x for x in b.by_type("IfcProduct")}
    expected=set(old)-({removed_guid} if removed_guid else set())
    if set(new)!=expected:
        raise NativeWallV5OracleError("Unrelated native IFC Product identity disappeared")
    if any(str(old[k])!=str(new[k]) for k in new):
        raise NativeWallV5OracleError("Unrelated IFC Product STEP attributes changed")
    walls_a={x.GlobalId:x for x in a.by_type("IfcWall")}
    walls_b={x.GlobalId:x for x in b.by_type("IfcWall")}
    if set(walls_b)!=set(walls_a)-({removed_guid} if removed_guid else set()):
        raise NativeWallV5OracleError("Other native IfcWall identities changed")
    for key in walls_b:
        if key not in (removed_guid,edited_guid) and not _mesh_set_equal(_mesh(walls_a[key]),_mesh(walls_b[key])):
            raise NativeWallV5OracleError("Non-target physical wall mesh changed")
    return len(new),len(walls_b)


def _target_coords(a,b,guid):
    try:
        wa=a.by_guid(guid);wb=b.by_guid(guid)
    except RuntimeError as exc:
        raise NativeWallV5OracleError("Target original Wall disappeared unexpectedly") from exc
    if not wa.is_a("IfcWall") or not wb.is_a("IfcWall"):
        raise NativeWallV5OracleError("Original target not an IFC Wall")
    return wa,wb,_coords(wa),_coords(wb)


def verify_wall_pose_or_length(source,candidate,guid,*,operation,angle_deg=None,
                               rotation_pivot_xyz=None,shift_xyz=None,
                               shorten_metres=None):
    a,b=_models(source,candidate)
    if set(x.GlobalId for x in a.by_type("IfcRoot"))!=set(x.GlobalId for x in b.by_type("IfcRoot")):
        raise NativeWallV5OracleError("Wall update native Root identity changed")
    orig_roots={x.GlobalId:str(x) for x in a.by_type("IfcRoot")}
    if any(orig_roots[x.GlobalId]!=str(x) for x in b.by_type("IfcRoot")):
        raise NativeWallV5OracleError("Native Root attributes changed")
    wa,wb,old,new=_target_coords(a,b,guid)
    before_start=np.asarray(old[0]);before_end=np.asarray(old[1])
    after_start=np.asarray(new[0]);after_end=np.asarray(new[1])
    orig_len=float(np.linalg.norm(before_end-before_start))
    after_len=float(np.linalg.norm(after_end-after_start))
    bm=_mesh(wa);am=_mesh(wb)

    if operation=="move":
        if shift_xyz is None:
            raise NativeWallV5OracleError("No declared native translation vector")
        shift=np.asarray(shift_xyz,dtype=float)
        if not (_near(after_start-before_start,shift)
                and _near(after_end-before_end,shift)
                and _mesh_set_equal(bm+shift,am)):
            raise NativeWallV5OracleError("Physical Wall mesh/axis not fully translated")
    elif operation=="rotate":
        if angle_deg is None:
            raise NativeWallV5OracleError("No declared physical rotation angle")
        ang=math.radians(float(angle_deg))
        cs=math.cos(ang);sn=math.sin(ang)
        rotation=np.array(((cs,-sn,0.),(sn,cs,0.),(0.,0.,1.)))
        # A geometry test explicitly declares the pivot. The fixed D0
        # chooses first endpoint. Additional tests may choose the midpoint
        # without changing the earlier predeclared author-grade fixture.
        pivot=(before_start if rotation_pivot_xyz is None
               else np.asarray(rotation_pivot_xyz,dtype=float))
        expected_start=pivot+rotation@(before_start-pivot)
        expected_end=pivot+rotation@(before_end-pivot)
        if not (_near(after_start,expected_start) and _near(after_end,expected_end)
                and _mesh_set_equal((bm-pivot)@rotation.T+pivot,am)):
            raise NativeWallV5OracleError("Wall native mesh not rotated about declared pivot")
    elif operation=="shorten":
        if shorten_metres is None or shorten_metres<=0:
            raise NativeWallV5OracleError("No positive predeclared shortening length")
        if not (_near(after_start,before_start)
                and abs(after_len-(orig_len-shorten_metres))<EPS
                and _near((after_end-after_start)/after_len,
                          (before_end-before_start)/orig_len)):
            raise NativeWallV5OracleError("Native wall local line was not shortened at fixed start")
        original_profile=next(z.SweptArea for rep in wa.Representation.Representations
                              for z in rep.Items if z.is_a("IfcExtrudedAreaSolid"))
        after_profile=next(z.SweptArea for rep in wb.Representation.Representations
                           for z in rep.Items if z.is_a("IfcExtrudedAreaSolid"))
        if not (original_profile.is_a("IfcRectangleProfileDef")
                and after_profile.is_a("IfcRectangleProfileDef")
                and abs(float(after_profile.XDim)-float(original_profile.XDim)
                        +shorten_metres)<EPS):
            raise NativeWallV5OracleError("Physical swept rectangle was not shortened")
    else:
        raise NativeWallV5OracleError("Unknown prospective wall operation")

    old_step={x.id():str(x) for x in a}
    new_step={x.id():str(x) for x in b}
    if set(old_step)-set(new_step):
        raise NativeWallV5OracleError("Wall edit deleted unrelated original STEP entity")
    changed={id for id in old_step if old_step[id]!=new_step[id]}
    approved_classes={
        "IfcCartesianPoint","IfcAxis2Placement3D","IfcRectangleProfileDef",
    }
    extra=set(new_step)-set(old_step)
    if (not changed or any(a.by_id(i).is_a() not in approved_classes for i in changed)
        or any(not b.by_id(i).is_a("IfcDirection") for i in extra)):
        raise NativeWallV5OracleError("Unexpected original IFC native STEP geometry mutation")
    if operation=="shorten" and not (
        {a.by_id(i).is_a() for i in changed}==
        {"IfcCartesianPoint","IfcRectangleProfileDef"} and not extra):
        raise NativeWallV5OracleError("Wall shorten changed non-length original STEP entities")
    products,unaffected=_products_preserved(a,b,removed_guid=None,edited_guid=guid)
    return {
        "status":"INDEPENDENT_NATIVE_WALL_"+operation.upper()+"_IFC_VALIDATED",
        "changed_original_step_types":sorted(a.by_id(i).is_a() for i in changed),
        "native_original_step_change_count":len(changed),
        "native_copy_on_write_direction_entities":len(extra),
        "original_root_inventory_unchanged":len(orig_roots),
        "other_original_wall_meshes_unchanged":unaffected-1,
        "other_original_ifc_products_preserved":products-1,
        "original_wall_axis_before_m":old,
        "actual_wall_axis_after_m":new,
        "source_sha256":file_hash(source),
        "candidate_sha256":file_hash(candidate),
        "all_45_task_oracle_coverage":False,
    }


def verify_wall_delete(source,candidate,guid):
    a,b=_models(source,candidate)
    old_roots={x.GlobalId:x for x in a.by_type("IfcRoot")}
    new_roots={x.GlobalId:x for x in b.by_type("IfcRoot")}
    if guid not in old_roots or not old_roots[guid].is_a("IfcWall") or guid in new_roots:
        raise NativeWallV5OracleError("Target Wall not removed from native IFC")
    if set(new_roots)-set(old_roots):
        raise NativeWallV5OracleError("New unexpected IFC Root after Wall delete")
    original=old_roots[guid]
    related={
        x.GlobalId:x for x in a.get_inverse(original) if x.is_a("IfcRoot")
    }
    if len(related)!=len(a.get_inverse(original)):
        raise NativeWallV5OracleError("Original Wall has unsupported relationship dependency")
    expected_removed={guid}
    mutable_relation=set()
    for key,rel in related.items():
        cls=rel.is_a()
        if cls=="IfcRelConnectsPathElements":
            if rel.ConnectionGeometry is not None:
                raise NativeWallV5OracleError("Wall connected with shape-dependent native relation")
            expected_removed.add(key)
        elif cls=="IfcRelDefinesByProperties":
            if len(rel.RelatedObjects)!=1:
                raise NativeWallV5OracleError("Wall delete modified shared IFC Pset")
            expected_removed.add(key)
            expected_removed.add(rel.RelatingPropertyDefinition.GlobalId)
        else:
            members=(rel.RelatedElements if cls=="IfcRelContainedInSpatialStructure"
                     else rel.RelatedObjects)
            prev={x.GlobalId for x in members}
            if guid not in prev:
                raise NativeWallV5OracleError("Wall missing native connection membership")
            if len(prev)==1:
                expected_removed.add(key)
            else:
                nxt=new_roots.get(key)
                if nxt is None:
                    raise NativeWallV5OracleError("Shared IFC relation removed unexpectedly")
                now=(nxt.RelatedElements if cls=="IfcRelContainedInSpatialStructure"
                     else nxt.RelatedObjects)
                if {x.GlobalId for x in now}!=prev-{guid}:
                    raise NativeWallV5OracleError("Other IFC relation members changed")
                mutable_relation.add(key)
    if set(old_roots)-set(new_roots)!=expected_removed:
        raise NativeWallV5OracleError("Deleted unrelated IFC Root or left target relations")
    for key in old_roots.keys()&new_roots.keys():
        if old_roots[key].is_a()!=new_roots[key].is_a():
            raise NativeWallV5OracleError("Surviving IFC Root changed class")
        if str(old_roots[key])!=str(new_roots[key]) and key not in mutable_relation:
            raise NativeWallV5OracleError("Non-target original IFC Root changed")
    products,remaining_walls=_products_preserved(a,b,removed_guid=guid)
    if any(r.RelatingElement.GlobalId==guid or r.RelatedElement.GlobalId==guid
           for r in b.by_type("IfcRelConnectsPathElements")):
        raise NativeWallV5OracleError("Dangling wall path connection after deletion")
    return {
        "status":"INDEPENDENT_NATIVE_WALL_SAFE_RELATION_DELETE_VALIDATED",
        "deleted_wall_guid":guid,
        "other_original_wall_meshes_unchanged":remaining_walls,
        "other_original_ifc_products_preserved":products,
        "removed_only_target_owned_and_connection_roots":len(expected_removed),
        "source_sha256":file_hash(source),
        "candidate_sha256":file_hash(candidate),
        "hosted_opening_and_filling_delete_supported":False,
        "all_45_task_oracle_coverage":False,
    }
