"""Independent Python/IfcOpenShell imperative Space split reference.

Standalone I0 authoring: no imports from the declarative XML compiler,
topology mutator, or native Space split runtime. Uses native IFC4X3 operations,
source-only geometry and a shared preregistered deterministic GUID contract.
This *reference oracle* is a separate code path from the direct XML compiler.
"""
from __future__ import annotations

import math
from itertools import product
from pathlib import Path
import uuid

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import numpy as np

_GUID_SEED=uuid.UUID("a0b90536-e3c9-45ea-a62d-e70b8dc3c8cf")


def _guid(kind,sha,space_key,relation):
    return ifcopenshell.guid.compress(uuid.uuid5(
        _GUID_SEED,f"g1-space-bounded-native-v0.1:{kind}:{sha}:{space_key}:{relation}").hex)


def _bbox(obj):
    opts=ifcopenshell.geom.settings()
    opts.set(opts.USE_WORLD_COORDS,True)
    native=ifcopenshell.geom.create_shape(opts,obj)
    verts=np.asarray(native.geometry.verts,dtype=float).reshape(-1,3)
    if len(verts)!=8 or not np.isfinite(verts).all():
        raise ValueError("I0 only supports exact native rectangular solids")
    lower=verts.min(axis=0);upper=verts.max(axis=0)
    if not np.all(np.isfinite(upper-lower)) or np.min(upper-lower)<1e-6:
        raise ValueError("I0 native box is degenerate")
    expected=set(product(*zip(np.round(lower,7),np.round(upper,7))))
    if set(map(tuple,np.round(verts,7)))!=expected:
        raise ValueError("I0 native body is not an axis-aligned cuboid")
    return lower,upper


def _world_surface(space,relation):
    geom=relation.ConnectionGeometry
    if not geom or not geom.is_a("IfcConnectionSurfaceGeometry"):
        raise ValueError("I0 source has missing boundary surface")
    face=geom.SurfaceOnRelatingElement
    space_frame=ifcopenshell.util.placement.get_local_placement(space.ObjectPlacement)
    if face.is_a("IfcSurfaceOfLinearExtrusion"):
        curve=face.SweptCurve.Curve
        if not curve.is_a("IfcPolyline") or len(curve.Points)!=2:
            raise ValueError("I0 unrecognized swept source boundary")
        transform=space_frame@ifcopenshell.util.placement.get_axis2placement(face.Position)
        first,second=[
            (transform@np.array((*p.Coordinates,0.,1.)))[:3]
            for p in curve.Points]
        vector=transform[:3,:3]@(
            np.array(face.ExtrudedDirection.DirectionRatios,dtype=float)*float(face.Depth))
        corners=np.array((first,second,second+vector,first+vector))
    elif face.is_a("IfcCurveBoundedPlane"):
        outline=list(face.OuterBoundary.Points)
        if len(outline)!=5:
            raise ValueError("I0 unrecognized bounded source boundary")
        transform=space_frame@ifcopenshell.util.placement.get_axis2placement(face.BasisSurface.Position)
        corners=np.array([(transform@np.array((*p.Coordinates,0.,1.)))[:3]
                          for p in outline[:4]])
    else:
        raise ValueError("I0 unrecognized native surface family")
    normal=np.cross(corners[1]-corners[0],corners[3]-corners[0])
    if np.linalg.norm(normal)<1e-9:
        raise ValueError("I0 degenerate source boundary")
    normal=normal/np.linalg.norm(normal)
    return corners.min(axis=0),corners.max(axis=0),normal


def _oriented_plane(model,lo,hi,normal):
    diff=hi-lo;axis=int(np.argmax(np.abs(normal)))
    other=[i for i in range(3) if i!=axis]
    if abs(diff[axis])>1e-6 or not all(diff[i]>1e-6 for i in other):
        raise ValueError("I0 intended face is not rectangular")
    ref=(np.array([0.,1.,0.]) if axis==0 else np.array([1.,0.,0.]))
    z=normal.copy();z/=np.linalg.norm(z)
    x=ref-np.dot(ref,z)*z
    x/=np.linalg.norm(x)
    y=np.cross(z,x)
    basis=np.stack((x,y,z),axis=1)
    frame=model.createIfcAxis2Placement3D(
        model.createIfcCartesianPoint(tuple(float(k) for k in lo)),
        model.createIfcDirection(tuple(float(k) for k in z)),
        model.createIfcDirection(tuple(float(k) for k in x)))
    world=[lo.copy() for _ in range(4)]
    for index,(a,b) in enumerate(((0,0),(1,0),(1,1),(0,1))):
        world[index][other[0]]=hi[other[0]] if a else lo[other[0]]
        world[index][other[1]]=hi[other[1]] if b else lo[other[1]]
    if np.dot(np.cross(world[1]-world[0],world[2]-world[0]),z)<0:
        world.reverse()
    local=[basis.T@(p-lo) for p in world]
    poly=model.createIfcPolyline([
        model.createIfcCartesianPoint((float(v[0]),float(v[1])))
        for v in (*local,local[0])])
    return model.createIfcConnectionSurfaceGeometry(
        model.createIfcCurveBoundedPlane(model.createIfcPlane(frame),poly,[]),None)


def _set_box(model,space,lo,hi):
    reps=space.Representation.Representations
    if len(reps)!=1 or len(reps[0].Items)!=1:
        raise ValueError("I0 requires one rectangular source Space solid")
    solid=reps[0].Items[0]
    if not solid.is_a("IfcExtrudedAreaSolid") or not solid.SweptArea.is_a("IfcRectangleProfileDef"):
        raise ValueError("I0 source Space is not a swept rectangular profile")
    placement=ifcopenshell.util.placement.get_local_placement(space.ObjectPlacement)
    body=placement@ifcopenshell.util.placement.get_axis2placement(solid.Position)
    axes=np.argmax(np.abs(body[:3,:3]),axis=0)
    if set(axes)!={0,1,2} or not np.allclose(
        np.abs(body[:3,:3]),np.eye(3)[:,axes],atol=1e-7):
        raise ValueError("I0 source body has unsupported rotated coordinate frame")
    ext=hi-lo
    solid.SweptArea.XDim=float(ext[axes[0]])
    solid.SweptArea.YDim=float(ext[axes[1]])
    solid.Depth=float(ext[axes[2]])
    center=(lo+hi)/2
    center[axes[2]]=lo[axes[2]]
    point=np.linalg.inv(placement)@np.array([*center,1.])
    solid.Position.Location.Coordinates=tuple(float(x) for x in point[:3])
    found_lo,found_hi=_bbox(space)
    if not np.allclose(found_lo,lo,atol=1e-6) or not np.allclose(found_hi,hi,atol=1e-6):
        raise ValueError("I0 native Space sweep did not produce intended world cuboid")


def author_independent_space_partition(joined_ifc:Path,out:Path,*,source_sha:str,
                                       source_space_guid:str,new_wall_guid:str,
                                       new_space_guid:str):
    """Author I0 Space repartition, from independently verified source geometry."""
    model=ifcopenshell.open(str(joined_ifc))
    space=model.by_guid(source_space_guid)
    new_wall=model.by_guid(new_wall_guid)
    original_min,original_max=_bbox(space)
    wall_min,wall_max=_bbox(new_wall)
    tol=1e-6
    if (not np.allclose(original_min[[0,2]],wall_min[[0,2]],atol=tol)
            or not np.allclose(original_max[[0,2]],wall_max[[0,2]],atol=tol)
            or not original_min[1]+tol<wall_min[1]<wall_max[1]<original_max[1]-tol):
        raise ValueError("I0 wall does not partition exactly one source room")
    near_max=original_max.copy();near_max[1]=wall_min[1]
    far_min=original_min.copy();far_min[1]=wall_max[1]
    start_volume=np.prod(original_max-original_min)
    resulting_volume=(np.prod(near_max-original_min)+np.prod(original_max-far_min)
                      +np.prod(wall_max-wall_min))
    if not math.isclose(float(start_volume),float(resulting_volume),abs_tol=1e-6):
        raise ValueError("I0 native Space volume is not conserved")
    for other in model.by_type("IfcSpace"):
        if other.GlobalId==source_space_guid:
            continue
        low,high=_bbox(other)
        if float(np.prod(np.maximum(np.minimum(high,wall_max)-
                                    np.maximum(low,wall_min),0)))>tol:
            raise ValueError("I0 new partition Wall overlaps another native Space")
    known=list(space.BoundedBy)
    if len(known)!=7:
        raise ValueError("I0 reference requires all seven first-level source boundaries")
    if len(space.Decomposes)!=1:
        raise ValueError("I0 source Space needs unique building-storey aggregation")
    old_solid=space.Representation.Representations[0].Items[0]
    clone=ifcopenshell.util.element.copy_deep(model,old_solid)
    original_shape=space.Representation.Representations[0]
    rep=model.createIfcShapeRepresentation(
        ContextOfItems=original_shape.ContextOfItems,
        RepresentationIdentifier=original_shape.RepresentationIdentifier,
        RepresentationType=original_shape.RepresentationType,Items=(clone,))
    shape=model.createIfcProductDefinitionShape(Representations=(rep,))
    original_placement=space.ObjectPlacement
    new_placement=model.createIfcLocalPlacement(
        PlacementRelTo=original_placement.PlacementRelTo,
        RelativePlacement=ifcopenshell.util.element.copy_deep(
            model,original_placement.RelativePlacement))
    far=model.createIfcSpace(
        GlobalId=new_space_guid,
        Name=str(space.Name or "Space")+" - second partition",
        CompositionType=space.CompositionType,
        ObjectPlacement=new_placement,Representation=shape)
    aggregate=space.Decomposes[0]
    aggregate.RelatedObjects=tuple((*aggregate.RelatedObjects,far))
    _set_box(model,space,original_min,near_max)
    _set_box(model,far,far_min,original_max)
    for boundary in known:
        lo,hi,n=_world_surface(space,boundary)
        face_axis=int(np.argmin(hi-lo))
        if abs(n[face_axis])<1.-1e-6:
            raise ValueError("I0 source Space boundary orientation is oblique")
        near_lo=np.maximum(lo,original_min);near_hi=np.minimum(hi,near_max)
        far_lo=np.maximum(lo,far_min);far_hi=np.minimum(hi,original_max)
        def visible(a,b):
            return (np.all(b>=a-tol) and
                    all(b[k]-a[k]>tol for k in range(3) if k!=face_axis))
        near_ok=visible(near_lo,near_hi)
        far_ok=visible(far_lo,far_hi)
        if not near_ok and not far_ok:
            raise ValueError("I0 source boundary lost during partition")
        if near_ok and far_ok:
            if boundary.RelatedBuildingElement is None:
                raise ValueError("I0 cannot duplicate virtual IFC boundary")
            old_geom=boundary.ConnectionGeometry
            boundary.ConnectionGeometry=_oriented_plane(model,near_lo,near_hi,n)
            if model.get_inverse(old_geom):
                raise ValueError("I0 original boundary geometry unexpectedly shared")
            ifcopenshell.util.element.remove_deep2(model,old_geom)
            new_rel_id=_guid("IfcRelSpaceBoundary-SPLIT",source_sha,boundary.GlobalId,new_space_guid)
            model.createIfcRelSpaceBoundary(
                GlobalId=new_rel_id,Name=boundary.Name,RelatingSpace=far,
                RelatedBuildingElement=boundary.RelatedBuildingElement,
                ConnectionGeometry=_oriented_plane(model,far_lo,far_hi,n),
                PhysicalOrVirtualBoundary=boundary.PhysicalOrVirtualBoundary,
                InternalOrExternalBoundary=boundary.InternalOrExternalBoundary)
        elif far_ok:
            boundary.RelatingSpace=far
    for label,y,normal,room in (
        ("NEAR_PARTITION_FACE",wall_min[1],np.array([0.,1.,0.]),space),
        ("FAR_PARTITION_FACE",wall_max[1],np.array([0.,-1.,0.]),far)):
        face_min=np.array([original_min[0],y,original_min[2]])
        face_max=np.array([original_max[0],y,original_max[2]])
        model.createIfcRelSpaceBoundary(
            GlobalId=_guid("IfcRelSpaceBoundary-NEW",source_sha,new_space_guid,label),
            Name="1stLevel",RelatingSpace=room,RelatedBuildingElement=new_wall,
            ConnectionGeometry=_oriented_plane(model,face_min,face_max,normal),
            PhysicalOrVirtualBoundary="PHYSICAL",InternalOrExternalBoundary="INTERNAL")
    if not (len(space.BoundedBy)==7 and len(far.BoundedBy)==6):
        raise ValueError("I0 independent source boundary partition counts changed")
    model.write(str(out))
    return new_space_guid
