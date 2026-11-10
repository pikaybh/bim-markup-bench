"""Sandbox-only native Space split proof for a SOURCE-VERIFIED rectangular case.

Not connected to the declarative XML compiler. It exists to prove which
native IFC geometry and boundary operations can be implemented safely in a
temporary independently validated result, BEFORE extending runtime semantics.

The current source has first-level geometrically oriented IfcRelSpaceBoundary
surfaces, including pre-existing virtual and Door surfaces. This code never
silently invents a virtual element or a new 2nd-level space boundary.
"""
from __future__ import annotations

import hashlib
import math
import uuid

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import numpy as np

from src.runtime.space_partition_preflight import (
    SpacePartitionPreflight,UnsupportedSpacePartition,
    plan_rectangular_space_partition,_exact_box,_surface_polygon,TOL,
)

PARTITION_NAMESPACE=uuid.UUID("a0b90536-e3c9-45ea-a62d-e70b8dc3c8cf")


def _allocate_guid(kind:str,source_sha:str,space_guid:str,other:str)->str:
    name=f"g1-space-bounded-native-v0.1:{kind}:{source_sha}:{space_guid}:{other}"
    return ifcopenshell.guid.compress(uuid.uuid5(PARTITION_NAMESPACE,name).hex)


def _rectangular_face_geometry(f,extent_min,extent_max,normal):
    lo=np.asarray(extent_min,dtype=float);hi=np.asarray(extent_max,dtype=float)
    axis=max(range(3),key=lambda i:abs(normal[i]))
    if (len(lo)!=3 or len(hi)!=3 or
            not np.all(np.isfinite(lo)) or not np.all(np.isfinite(hi)) or
            hi[axis]-lo[axis]>TOL or
            not all(hi[i]-lo[i]>TOL for i in range(3) if i!=axis)):
        raise UnsupportedSpacePartition("Cannot create native plane from nonrectangular face")
    outward=np.asarray(normal,dtype=float)
    if abs(np.linalg.norm(outward)-1.)>TOL or abs(abs(outward[axis])-1.)>TOL:
        raise UnsupportedSpacePartition("Native SpaceBoundary outward normal unsupported")
    ref=np.array((0.,1.,0.)) if axis==0 else np.array((1.,0.,0.))
    point=f.createIfcCartesianPoint(tuple(float(x) for x in lo))
    axis_ref=f.createIfcDirection(tuple(float(x) for x in outward))
    refdir=f.createIfcDirection(tuple(float(x) for x in ref))
    frame=f.createIfcAxis2Placement3D(point,axis_ref,refdir)
    matrix=ifcopenshell.util.placement.get_axis2placement(frame)
    inverse=np.linalg.inv(matrix)
    mutable=[i for i in range(3) if i!=axis]
    def corner(a,b):
        xyz=lo.copy();xyz[mutable[0]]=a;xyz[mutable[1]]=b
        return xyz
    world=[
        corner(lo[mutable[0]],lo[mutable[1]]),
        corner(hi[mutable[0]],lo[mutable[1]]),
        corner(hi[mutable[0]],hi[mutable[1]]),
        corner(lo[mutable[0]],hi[mutable[1]]),
    ]
    n=np.cross(world[1]-world[0],world[2]-world[0])
    if np.dot(n,outward)<0:
        world.reverse()
    uv=[(inverse@np.array([*p,1.]))[:3] for p in world]
    if max(abs(float(p[2])) for p in uv)>1e-6:
        raise UnsupportedSpacePartition("Native rectangle not on intended Space-relative plane")
    curve=f.createIfcPolyline([f.createIfcCartesianPoint(tuple(float(x) for x in p[:2]))
                               for p in uv+[uv[0]]])
    plane=f.createIfcPlane(frame)
    surface=f.createIfcCurveBoundedPlane(plane,curve,[])
    return f.createIfcConnectionSurfaceGeometry(surface,None)


def _update_native_rectangular_space_body(f,space,low,high):
    """Edit exactly one unique source Space rectangular extrusion (no copy-on-share)."""
    body=space.Representation
    if not body or len(body.Representations)!=1:
        raise UnsupportedSpacePartition("Source Space has multiple/absent shape representations")
    representation=body.Representations[0]
    if len(representation.Items)!=1:
        raise UnsupportedSpacePartition("Source Space Body contains multiple shapes")
    solid=representation.Items[0]
    if not solid.is_a("IfcExtrudedAreaSolid") or not solid.SweptArea.is_a("IfcRectangleProfileDef"):
        raise UnsupportedSpacePartition("Source Space is not a unique rectangular sweep")
    if [x.id() for x in f.get_inverse(body)]!=[space.id()]:
        raise UnsupportedSpacePartition("Source Space representation is shared")
    area=solid.SweptArea
    if len(f.get_inverse(area))!=1:
        raise UnsupportedSpacePartition("Source Space profile is shared with another IFC object")
    frame=ifcopenshell.util.placement.get_axis2placement(solid.Position)
    space_frame=ifcopenshell.util.placement.get_local_placement(space.ObjectPlacement)
    global_frame=space_frame@frame
    if (not np.allclose(space_frame,np.eye(4),atol=TOL,rtol=0)
            or not np.allclose(global_frame[:3,:3],(
                (0.,1.,0.),(-1.,0.,0.),(0.,0.,1.)),atol=TOL,rtol=0)):
        raise UnsupportedSpacePartition("Native Space extruded body orientation not uniquely supported")
    mid=np.array((float((low[0]+high[0])/2),float((low[1]+high[1])/2),float(low[2])))
    # Check original geometry is exactly the swept rectangular support and
    # not a separate clipping/Boolean/singular representation.
    _,orig_high=_exact_box(space,kind="IfcSpace")
    if not math.isclose(float(solid.Depth),float(orig_high[2]-low[2]),abs_tol=TOL):
        raise UnsupportedSpacePartition("Native source Space solid depth differs from world bbox")
    area.XDim=float(high[1]-low[1])
    area.YDim=float(high[0]-low[0])
    solid.Position.Location.Coordinates=tuple(float(x) for x in mid)
    if not math.isclose(float(solid.Depth),float(high[2]-low[2]),abs_tol=TOL):
        raise UnsupportedSpacePartition("Changing Space height is not supported")
    current_min,current_max=_exact_box(space,kind="IfcSpace")
    if not np.allclose(current_min,low,atol=1e-6) or not np.allclose(current_max,high,atol=1e-6):
        raise UnsupportedSpacePartition("Native Space profile update did not produce requested body")


def sandbox_native_space_split(f,plan:SpacePartitionPreflight,*,source_sha:str):
    """Mutate IN-MEMORY candidate; caller writes only a TemporaryDirectory file.

    NOT a method callable by the markup-editing LLM or an advertised task
    compiler capability. Designed to be wrapped by an independent validator.
    """
    if not isinstance(plan,SpacePartitionPreflight) or not plan.existing_oriented_surface_reconciliation_validated:
        raise UnsupportedSpacePartition("Missing complete approved read-only Space plan")
    if f.schema!="IFC4X3" or len(source_sha)!=64:
        raise UnsupportedSpacePartition("Native source schema/hash mismatch")
    # Recompute the full immutable boundary plan from native IFC *before*
    # performing the first in-memory mutation. Never trust a stale/forged
    # geometry or boundary surface plan supplied by a caller.
    verified=plan_rectangular_space_partition(
        f,f,plan.existing_space_id,plan.new_wall_id)
    if verified!=plan:
        raise UnsupportedSpacePartition("Native Space partition plan is stale or forged")
    try:
        space=f.by_guid(plan.existing_space_id)
        wall=f.by_guid(plan.new_wall_id)
    except RuntimeError as exc:
        raise UnsupportedSpacePartition("Expected IFC Space/Wall absent") from exc
    low,high=_exact_box(space,kind="IfcSpace")
    wl,wh=_exact_box(wall,kind="IfcWall")
    if (not np.allclose(low,plan.near_box_min,atol=TOL)
            or not np.allclose(high,plan.far_box_max,atol=TOL)
            or not np.allclose(wl[1],plan.near_box_max[1],atol=TOL)
            or not np.allclose(wh[1],plan.far_box_min[1],atol=TOL)):
        raise UnsupportedSpacePartition("Candidate IFC geometry diverged since partition preflight")
    if len(space.Decomposes)!=1 or not space.Decomposes[0].RelatingObject.is_a("IfcBuildingStorey"):
        raise UnsupportedSpacePartition("Original Space has unsupported native aggregation")
    aggregate=space.Decomposes[0]
    if len(space.BoundedBy)!=len(plan.boundary_patches):
        raise UnsupportedSpacePartition("Source Space boundary inventory changed")
    known={r.GlobalId:r for r in space.BoundedBy}
    if set(known)!={p.boundary_id for p in plan.boundary_patches}:
        raise UnsupportedSpacePartition("Source IFC SpaceBoundary identities changed")
    new_guid=_allocate_guid("IfcSpace",source_sha,space.GlobalId,wall.GlobalId)
    try:
        f.by_guid(new_guid)
    except RuntimeError:
        pass
    else:
        raise UnsupportedSpacePartition("Deterministic far Space GlobalId collision")
    # Clone the rectangular SOLID before editing the source Space. Both
    # products get a distinct Shape representation and IFC placement.
    old_rep=space.Representation.Representations[0]
    original_solid=old_rep.Items[0]
    far_solid=ifcopenshell.util.element.copy_deep(f,original_solid)
    far_shape=f.createIfcShapeRepresentation(
        ContextOfItems=old_rep.ContextOfItems,
        RepresentationIdentifier=old_rep.RepresentationIdentifier,
        RepresentationType=old_rep.RepresentationType,
        Items=(far_solid,))
    far_product_shape=f.createIfcProductDefinitionShape(Representations=(far_shape,))
    parent=space.ObjectPlacement.PlacementRelTo
    far_placement=f.createIfcLocalPlacement(
        PlacementRelTo=parent,
        RelativePlacement=ifcopenshell.util.element.copy_deep(
            f,space.ObjectPlacement.RelativePlacement))
    far_space=f.createIfcSpace(
        GlobalId=new_guid,Name=str(space.Name or "Space")+" - second partition",
        CompositionType=space.CompositionType,
        ObjectPlacement=far_placement,Representation=far_product_shape)
    if far_space.GlobalId!=new_guid:
        raise UnsupportedSpacePartition("New Space GUID was not set")
    aggregate.RelatedObjects=tuple((*aggregate.RelatedObjects,far_space))
    # Source's complete body is reduced to its near (door-side) region;
    # copied far body is positioned to the distant region with identical
    # world axes, preserving the original Space identity and placement.
    _update_native_rectangular_space_body(f,space,np.asarray(plan.near_box_min),
                                          np.asarray(plan.near_box_max))
    _update_native_rectangular_space_body(f,far_space,np.asarray(plan.far_box_min),
                                          np.asarray(plan.far_box_max))

    added_boundary_ids=[]
    for patch in plan.boundary_patches:
        rel=known[patch.boundary_id]
        if patch.action=="KEEP_NEAR":
            continue
        if patch.action=="REHOME_FAR":
            rel.RelatingSpace=far_space
            continue
        if patch.action!="SPLIT_BOTH":
            raise UnsupportedSpacePartition("Unknown native SpaceBoundary reconciliation action")
        if (patch.source_related_class=="VIRTUAL" or rel.ConnectionGeometry is None or
                len(f.get_inverse(rel.ConnectionGeometry))!=1):
            raise UnsupportedSpacePartition("Cannot split shared or virtual SpaceBoundary surface")
        old_geom=rel.ConnectionGeometry
        rel.ConnectionGeometry=_rectangular_face_geometry(
            f,patch.near_extent_min,patch.near_extent_max,patch.normal)
        new_geom=_rectangular_face_geometry(
            f,patch.far_extent_min,patch.far_extent_max,patch.normal)
        rel_guid=_allocate_guid("IfcRelSpaceBoundary-SPLIT",source_sha,patch.boundary_id,new_guid)
        f.createIfcRelSpaceBoundary(
            GlobalId=rel_guid,Name=rel.Name,
            RelatingSpace=far_space,
            RelatedBuildingElement=rel.RelatedBuildingElement,
            ConnectionGeometry=new_geom,
            PhysicalOrVirtualBoundary=rel.PhysicalOrVirtualBoundary,
            InternalOrExternalBoundary=rel.InternalOrExternalBoundary)
        added_boundary_ids.append(rel_guid)
        # Drop unattached old generated source boundary geometry ONLY when it
        # no longer has an IFC inverse reference.
        if len(f.get_inverse(old_geom))!=0:
            raise UnsupportedSpacePartition("Original SpaceBoundary geometry unexpectedly shared")
        ifcopenshell.util.element.remove_deep2(f,old_geom)
    for label,face_min,face_max,normal in plan.required_new_partition_surfaces:
        boundary_guid=_allocate_guid("IfcRelSpaceBoundary-NEW",source_sha,new_guid,label)
        f.createIfcRelSpaceBoundary(
            GlobalId=boundary_guid,Name="1stLevel",
            RelatingSpace=space if label=="NEAR_PARTITION_FACE" else far_space,
            RelatedBuildingElement=wall,
            ConnectionGeometry=_rectangular_face_geometry(f,face_min,face_max,normal),
            PhysicalOrVirtualBoundary="PHYSICAL",
            InternalOrExternalBoundary="INTERNAL")
        added_boundary_ids.append(boundary_guid)
    expected=len(plan.boundary_patches)+len(plan.required_new_partition_surfaces)+sum(
        p.action=="SPLIT_BOTH" for p in plan.boundary_patches)
    actual=sum(1 for x in f.by_type("IfcRelSpaceBoundary")
               if x.RelatingSpace.GlobalId in {space.GlobalId,far_space.GlobalId})
    if actual!=expected or len(added_boundary_ids)!=expected-len(plan.boundary_patches):
        raise UnsupportedSpacePartition("Native SpaceBoundary count does not match preflight")
    return {"new_space_guid":new_guid,
            "added_boundary_guids":tuple(added_boundary_ids),
            "total_target_boundary_count":actual,
            "native_source_space_geometry_rebuilt":True,
            "source_space_id_preserved":space.GlobalId==plan.existing_space_id,
            "compiler_or_llm_interface_exposed":False}
