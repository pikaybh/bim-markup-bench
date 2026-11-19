"""Independent IFC4X3-native-only v0.6 hosted move and dependent deletion oracle.

This module deliberately imports neither declarative XML, compiler, binder,
mutation helper, author grading nor hosted-door implementation. The native
source and result IFCs alone determine inventory and real physical meshes.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.shape
import ifcopenshell.util.unit
import numpy as np

from tools.bibimbap_matched25_tools import file_hash

TOL=1e-5


class IndependentHostedV6Error(ValueError):
    pass


def _read(source:Path,result:Path):
    if not source.is_file() or not result.is_file() or source.resolve()==result.resolve():
        raise IndependentHostedV6Error("Two different IFC4X3 files must exist")
    a=ifcopenshell.open(str(source));b=ifcopenshell.open(str(result))
    if a.schema!="IFC4X3" or b.schema!="IFC4X3":
        raise IndependentHostedV6Error("Source/result native IFC4X3 schema must match")
    for model in (a,b):
        if not math.isclose(ifcopenshell.util.unit.calculate_unit_scale(model),1.,abs_tol=1e-8):
            raise IndependentHostedV6Error("Native independent hosted oracle requires source metres")
    return a,b


def _shape(model,entity):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        s=ifcopenshell.geom.create_shape(settings,entity)
        pts=np.asarray(s.geometry.verts,dtype=float).reshape(-1,3)
        faces=np.asarray(s.geometry.faces,dtype=int).reshape(-1,3)
        volume=float(ifcopenshell.util.shape.get_volume(s.geometry))
    except Exception as exc:
        raise IndependentHostedV6Error("Native IFC geometry kernel failed") from exc
    if (len(pts)<4 or len(faces)<4 or not np.isfinite(pts).all()
        or not math.isfinite(volume) or volume<=0):
        raise IndependentHostedV6Error("Invalid original/result native IFC mesh")
    return pts,len(faces),volume


def _same_vertices(a,b):
    if a.shape!=b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        return False
    # Native IFC tessellation preserves triangle vertex ordering for the
    # same solid after a rigid placement edit. Prefer direct elementwise
    # tolerance: equivalent near-duplicate vertices can reorder under a
    # lexicographic float sort and cause false negatives.
    if np.allclose(a,b,atol=TOL,rtol=0):
        return True
    # A fixed-grid hash can spuriously reject equal translated meshes near
    # a half-step; the fallback compares full 3D vertices in float space.
    original=a[np.lexsort((a[:,2],a[:,1],a[:,0]))]
    result=b[np.lexsort((b[:,2],b[:,1],b[:,0]))]
    return bool(np.allclose(original,result,atol=TOL,rtol=0))


def _roots(f):
    return {x.GlobalId:x for x in f.by_type("IfcRoot")}


def _products(f):
    return {x.GlobalId:x for x in f.by_type("IfcProduct")}


def _owned_pair(f,filling_guid:str,opening_guid:str):
    roots=_roots(f)
    if filling_guid not in roots or opening_guid not in roots:
        raise IndependentHostedV6Error("Expected exact original hosted IFC GlobalIds")
    fill=roots[filling_guid];opening=roots[opening_guid]
    if (fill.is_a() not in ("IfcDoor","IfcWindow")
        or not opening.is_a("IfcOpeningElement")):
        raise IndependentHostedV6Error("Expected typed native Door/Window + Opening")
    fills=list(fill.FillsVoids);voids=list(opening.VoidsElements)
    if (len(fills)!=1 or fills[0].RelatingOpeningElement.GlobalId!=opening_guid
        or len(opening.HasFillings)!=1
        or opening.HasFillings[0].RelatedBuildingElement.GlobalId!=filling_guid
        or len(voids)!=1 or not voids[0].RelatingBuildingElement.is_a("IfcWall")):
        raise IndependentHostedV6Error("Native void/fill/host relation is not uniquely paired")
    other_inv=list(f.get_inverse(opening))
    if Counter(x.is_a() for x in other_inv)!=Counter({
        "IfcRelFillsElement":1,"IfcRelVoidsElement":1
    }):
        raise IndependentHostedV6Error("Opening has unrelated inverse dependencies")
    allowed={
        "IfcRelFillsElement","IfcRelContainedInSpatialStructure",
        "IfcRelAssociatesMaterial","IfcRelAssociatesClassification",
        "IfcRelDefinesByType","IfcRelDefinesByProperties",
    }
    inv=list(f.get_inverse(fill))
    if any(x.is_a() not in allowed for x in inv):
        raise IndependentHostedV6Error("Filling has unsupported native inverse dependencies")
    for rel in inv:
        if rel.is_a("IfcRelDefinesByProperties"):
            if len(rel.RelatedObjects)!=1 or not rel.RelatingPropertyDefinition.is_a("IfcPropertySet"):
                raise IndependentHostedV6Error("Filler property relation is not uniquely owned")
    return fill,opening,voids[0].RelatingBuildingElement


def _verify_unaffected_meshed_products(a,b,excluded):
    aa=_products(a);bb=_products(b)
    checked=0
    for gid in set(aa)&set(bb)-set(excluded):
        prev=aa[gid];new=bb[gid]
        if prev.Representation is None and new.Representation is None:
            continue
        if (prev.Representation is None)!=(new.Representation is None):
            raise IndependentHostedV6Error("Unrelated IFC Product representation changed")
        p,faces,volume=_shape(a,prev)
        q,faces2,volume2=_shape(b,new)
        if (faces!=faces2 or abs(volume-volume2)>TOL or not _same_vertices(p,q)):
            raise IndependentHostedV6Error("Unrelated native IFC product mesh or volume changed")
        checked+=1
    return checked


def verify_hosted_move(source:Path,result:Path,opening_guid:str,
                       *,delta_metres:float,expected_filling_guid:str)->dict:
    a,b=_read(source,result)
    fill,opening,host=_owned_pair(a,expected_filling_guid,opening_guid)
    post_fill,post_open,post_host=_owned_pair(b,expected_filling_guid,opening_guid)
    if host.GlobalId!=post_host.GlobalId:
        raise IndependentHostedV6Error("Hosted opening was reparented to a new Wall")
    rr=_roots(a);ss=_roots(b)
    if set(rr)!=set(ss) or any(str(rr[g])!=str(ss[g]) for g in rr):
        raise IndependentHostedV6Error("Moving hosted opening changed Root inventory/metadata")
    aa={x.id():str(x) for x in a};bb={x.id():str(x) for x in b}
    point=opening.ObjectPlacement.RelativePlacement.Location
    point_after=post_open.ObjectPlacement.RelativePlacement.Location
    if (point.id()!=point_after.id() or
        set(aa)!=set(bb) or
        {i for i in aa if aa[i]!=bb[i]}!={point.id()}):
        raise IndependentHostedV6Error("Native Opening edit unexpectedly changed STEP records")
    oldpos=np.asarray(point.Coordinates,dtype=float)
    newpos=np.asarray(point_after.Coordinates,dtype=float)
    if not np.allclose(newpos-oldpos,(delta_metres,0.,0.),atol=TOL,rtol=0):
        raise IndependentHostedV6Error("Hosted Opening did not move by exact native local X")
    if not math.isfinite(delta_metres) or not (0.001<=abs(delta_metres)<100):
        raise IndependentHostedV6Error("Independent oracle got invalid declared delta")
    host_transform=ifcopenshell.util.placement.get_local_placement(host.ObjectPlacement)
    world_dx=np.asarray(host_transform[:3,0])*float(delta_metres)
    for old,new in ((opening,post_open),(fill,post_fill)):
        original,faces,vol=_shape(a,old)
        moved,nfaces,nvol=_shape(b,new)
        # IFC mapped Door mesh may not be closed/manifold: the engine's
        # origin-dependent signed-volume estimate changes under an exact
        # rigid translation (observed ~3e-5m^3 on original basic_tasks).
        # Triangle count and the COMPLETE translated vertex cloud are the
        # independent geometric invariant, not non-watertight signed volume.
        if faces!=nfaces or not _same_vertices(original+world_dx,moved):
            raise IndependentHostedV6Error("Actual void or door/window world mesh did not move")
    a_host,faces_before,vbefore=_shape(a,host)
    b_host,faces_after,vafter=_shape(b,post_host)
    if not math.isclose(vbefore,vafter,abs_tol=TOL,rel_tol=0):
        raise IndependentHostedV6Error("Moving void changed host original Wall solid volume")
    if _same_vertices(a_host,b_host):
        raise IndependentHostedV6Error("Host Wall void remains in its old physical location")
    old_prods=_products(a);new_prods=_products(b)
    if set(old_prods)!=set(new_prods):
        raise IndependentHostedV6Error("Hosted offset moved/removed an unrelated IFC Product")
    preserved=_verify_unaffected_meshed_products(
        a,b,{opening_guid,expected_filling_guid,host.GlobalId})
    return {
        "status":"INDEPENDENT_IFC4X3_HOSTED_OPENING_WITH_FILLING_TRANSLATION_VALIDATED",
        "source_sha256":file_hash(source),"candidate_sha256":file_hash(result),
        "native_opening_guid":opening_guid,"native_filling_guid":expected_filling_guid,
        "host_wall_guid":host.GlobalId,
        "world_delta_m":tuple(float(x) for x in world_dx),
        "other_original_native_product_meshes_preserved":preserved,
        "original_root_count_preserved":len(rr),
        "source_step_changed_point_only":point.id(),
        "original_author_45_task_parity":False,
    }


def _relation_members(rel):
    return (rel.RelatedElements if rel.is_a("IfcRelContainedInSpatialStructure")
            else rel.RelatedObjects)


def verify_hosted_pair_delete(source:Path,result:Path,filling_guid:str,
                              opening_guid:str)->dict:
    a,b=_read(source,result)
    fill,opening,host=_owned_pair(a,filling_guid,opening_guid)
    old_products=_products(a);new_products=_products(b)
    if set(new_products)!=set(old_products)-{filling_guid,opening_guid}:
        raise IndependentHostedV6Error("Deletion removed/inserted unrelated original IFC Product")
    if any(str(old_products[g])!=str(new_products[g]) for g in new_products):
        raise IndependentHostedV6Error("Deletion modified unrelated original IFC Product")
    oldroots=_roots(a);newroots=_roots(b)
    if set(newroots)-set(oldroots):
        raise IndependentHostedV6Error("Native hosted pair deletion added an IFC Root")
    expect_removed={filling_guid,opening_guid}
    changed_memberships=set()
    inv={rel.GlobalId:rel for entity in (fill,opening)
         for rel in a.get_inverse(entity) if rel.is_a("IfcRoot")}
    if len(inv)!=len(set(inv)):
        raise IndependentHostedV6Error("Duplicate IFC GlobalId in hosted inverse roots")
    for guid,relation in inv.items():
        kind=relation.is_a()
        if kind in ("IfcRelFillsElement","IfcRelVoidsElement"):
            expect_removed.add(guid)
        elif kind=="IfcRelDefinesByProperties":
            expect_removed.update((guid,relation.RelatingPropertyDefinition.GlobalId))
        else:
            members={x.GlobalId for x in _relation_members(relation)}
            if filling_guid not in members:
                raise IndependentHostedV6Error("Native related-member missing from source IFC")
            if len(members)==1:
                expect_removed.add(guid)
            else:
                if guid not in newroots:
                    raise IndependentHostedV6Error("Native multi-member relation deleted")
                next_members={x.GlobalId for x in _relation_members(newroots[guid])}
                if next_members!=members-{filling_guid}:
                    raise IndependentHostedV6Error("Surviving shared IFC relation members changed")
                changed_memberships.add(guid)
    if set(oldroots)-set(newroots)!=expect_removed:
        raise IndependentHostedV6Error("Native pair deletion did not clean exact rooted dependency set")
    for gid in oldroots.keys()&newroots.keys():
        prev=oldroots[gid];new=newroots[gid]
        if prev.is_a()!=new.is_a():
            raise IndependentHostedV6Error("Surviving IFC Root changed class")
        if gid not in changed_memberships and str(prev)!=str(new):
            raise IndependentHostedV6Error("Surviving unrelated IFC Root changed attributes")
        if gid in changed_memberships:
            for i in range(len(prev)):
                attr=prev.attribute_name(i)
                if attr in ("RelatedObjects","RelatedElements"):
                    continue
                # IfcOpenShell updates shared native IfcRelDefinesByType owner
                # modification metadata; all other attrs must remain exact.
                if prev.is_a("IfcRelDefinesByType") and attr=="OwnerHistory":
                    if new.OwnerHistory is None or str(new.OwnerHistory.ChangeAction)!="MODIFIED":
                        raise IndependentHostedV6Error("Invalid native type OwnerHistory modification")
                    continue
                if str(prev[i])!=str(new[i]):
                    raise IndependentHostedV6Error("Surviving shared native relation metadata changed")
    for rel in b.by_type("IfcRelAssociatesClassification"):
        if len(rel.RelatedObjects)<1:
            raise IndependentHostedV6Error("IFC relation with no remaining classified objects")
    for rel in b.by_type("IfcRelFillsElement"):
        if rel.RelatedBuildingElement.GlobalId==filling_guid:
            raise IndependentHostedV6Error("Removed Filling left dangling IfcRelFillsElement")
    for rel in b.by_type("IfcRelVoidsElement"):
        if rel.RelatedOpeningElement.GlobalId==opening_guid:
            raise IndependentHostedV6Error("Removed Opening left dangling IfcRelVoidsElement")
    host_after=new_products.get(host.GlobalId)
    if host_after is None:
        raise IndependentHostedV6Error("Host Wall was deleted")
    _shape_a=_shape(a,host)
    _shape_b=_shape(b,host_after)
    opening_volume=_shape(a,opening)[2]
    if not math.isclose(_shape_b[2]-_shape_a[2],opening_volume,abs_tol=TOL,rel_tol=0):
        raise IndependentHostedV6Error("Host Wall void did not physically close after deletion")
    preserved=_verify_unaffected_meshed_products(a,b,{host.GlobalId,filling_guid,opening_guid})
    old_step={x.id():str(x) for x in a};new_step={x.id():str(x) for x in b}
    added=set(new_step)-set(old_step)
    if added and any(not b.by_id(i).is_a("IfcOwnerHistory") for i in added):
        raise IndependentHostedV6Error("Hosted pair deletion created unapproved native STEP objects: "+
                                        str(sorted((i,b.by_id(i).is_a()) for i in added)))
    for step_id in added:
        incoming=list(b.get_inverse(b.by_id(step_id)))
        if (not incoming or any(not x.is_a("IfcRelDefinesByType")
                                or x.GlobalId not in changed_memberships for x in incoming)):
            raise IndependentHostedV6Error("New OwnerHistory does not belong solely to a changed shared native type relation")
    dropped=set(old_step)-set(new_step)
    modified={x for x in old_step.keys()&new_step.keys() if old_step[x]!=new_step[x]}
    approved_changed={oldroots[g].id() for g in changed_memberships}
    reps={rep.id() for obj in (fill,opening)
          if obj.Representation is not None
          for rep in obj.Representation.Representations}
    for step_id in modified-approved_changed:
        prev=a.by_id(step_id);new=b.by_id(step_id)
        if (not prev.is_a("IfcPresentationLayerAssignment")
            or not new.is_a("IfcPresentationLayerAssignment")):
            raise IndependentHostedV6Error("Hosted delete changed unknown native STEP metadata")
        before={x.id() for x in prev.AssignedItems}
        after={x.id() for x in new.AssignedItems}
        if after-before or not before-after<=reps:
            raise IndependentHostedV6Error("Hosted delete changed unrelated IFC presentation layer assignment")
    for step_id in dropped:
        for owner in a.get_inverse(a.by_id(step_id)):
            if owner.id() not in dropped and owner.id() not in modified:
                raise IndependentHostedV6Error("Deleted STEP entity still owned by unrelated native IFC object")
    return {
        "status":"INDEPENDENT_IFC4X3_HOSTED_FILLING_AND_OPENING_DELETE_VALIDATED",
        "source_sha256":file_hash(source),"candidate_sha256":file_hash(result),
        "filling_guid_removed":filling_guid,"opening_guid_removed":opening_guid,
        "host_wall_guid_preserved":host.GlobalId,
        "original_other_ifc_products_preserved":len(new_products),
        "unrelated_native_product_meshes_preserved":preserved,
        "rooted_deleted_dependency_count":len(expect_removed),
        "deleted_step_objects_verified":len(dropped),
        "all_remaining_classification_relations_nonempty":True,
        "original_author_45_task_parity":False,
    }
