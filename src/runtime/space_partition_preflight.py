"""G1 #15: SOURCE-ONLY first-level IfcSpace boundary partition preflight.

This module does NOT mutate IFC, fabricate physical surfaces, choose an
official GT policy, or grant task-success eligibility.  It verifies whether
a rectangular existing IFC4X3 IfcSpace and real created partition Wall admit
a *complete* oriented rectangular-face reconciliation schedule.

All surfaces are read in the source Space's local coordinates, transformed
to world space, and classified with strict topology and area guards.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from itertools import product

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import numpy as np


TOL=1e-6


class UnsupportedSpacePartition(ValueError):
    """The IFC source cannot yet be partitioned without semantic invention."""


@dataclass(frozen=True)
class BoundaryPatch:
    boundary_id: str
    action: str  # KEEP_NEAR, REHOME_FAR, SPLIT_BOTH
    source_related_class: str
    plane_axis: str
    normal: tuple[float,float,float]
    original_extent_min: tuple[float,float,float]
    original_extent_max: tuple[float,float,float]
    near_extent_min: tuple[float,float,float] | None
    near_extent_max: tuple[float,float,float] | None
    far_extent_min: tuple[float,float,float] | None
    far_extent_max: tuple[float,float,float] | None


@dataclass(frozen=True)
class SpacePartitionPreflight:
    existing_space_id: str
    new_wall_id: str
    near_box_min: tuple[float,float,float]
    near_box_max: tuple[float,float,float]
    far_box_min: tuple[float,float,float]
    far_box_max: tuple[float,float,float]
    original_volume_m3: float
    near_volume_m3: float
    far_volume_m3: float
    intervening_wall_volume_m3: float
    boundary_patches: tuple[BoundaryPatch,...]
    required_new_partition_surfaces: tuple[tuple[str,tuple[float,float,float],tuple[float,float,float],tuple[float,float,float]],...]
    existing_oriented_surface_reconciliation_validated: bool
    native_ifc_writes_performed: bool=False
    new_ifc_space_boundaries_committed: bool=False

    def audit(self)->dict:
        from collections import Counter
        actions=Counter(p.action for p in self.boundary_patches)
        return {
            "status":"PASS_READ_ONLY_BOUNDARY_RECONCILIATION_PLAN_NOT_AN_IFC_EDIT",
            "original_boundary_count":len(self.boundary_patches),
            "keep_near_count":actions["KEEP_NEAR"],
            "rehome_far_count":actions["REHOME_FAR"],
            "split_both_count":actions["SPLIT_BOTH"],
            "required_new_partition_boundary_count":len(self.required_new_partition_surfaces),
            "expected_total_boundary_count_after_split":len(self.boundary_patches)+actions["SPLIT_BOTH"]+len(self.required_new_partition_surfaces),
            "original_room_volume_m3":round(self.original_volume_m3,6),
            "near_room_volume_m3":round(self.near_volume_m3,6),
            "far_room_volume_m3":round(self.far_volume_m3,6),
            "partition_wall_volume_m3":round(self.intervening_wall_volume_m3,6),
            "near_room_bbox_min":list(self.near_box_min),
            "near_room_bbox_max":list(self.near_box_max),
            "far_room_bbox_min":list(self.far_box_min),
            "far_room_bbox_max":list(self.far_box_max),
            "existing_oriented_surface_reconciliation_validated":
                self.existing_oriented_surface_reconciliation_validated,
            "native_ifc_writes_performed":self.native_ifc_writes_performed,
            "new_ifc_space_boundaries_committed":self.new_ifc_space_boundaries_committed,
            "official_task_succeeded":False,
        }


def _as_tuple(arr):
    return tuple(round(float(x),8) for x in arr)


def _exact_box(obj, *,kind:str):
    if not obj or not obj.is_a(kind):
        raise UnsupportedSpacePartition("Missing typed native IFC Space or Wall")
    try:
        opts=ifcopenshell.geom.settings()
        opts.set(opts.USE_WORLD_COORDS,True)
        shape=ifcopenshell.geom.create_shape(opts,obj)
        verts=np.asarray(shape.geometry.verts,dtype=np.float64).reshape((-1,3))
        faces=np.asarray(shape.geometry.faces,dtype=np.int64).reshape((-1,3))
    except Exception as exc:
        raise UnsupportedSpacePartition("Native IFC product mesh unavailable") from exc
    if (len(verts)!=8 or len(faces)!=12 or not np.isfinite(verts).all()
            or np.min(faces)<0 or np.max(faces)>=len(verts)):
        raise UnsupportedSpacePartition("Partition requires exact 8-vertex 12-triangle native cuboid")
    low=verts.min(0);high=verts.max(0);dims=high-low
    if np.any(dims<1e-5) or np.any(dims>10000):
        raise UnsupportedSpacePartition("Nonpositive or excessive IFC cuboid extents")
    corners=np.array(list(product(*zip(low,high))))
    if any(not np.any(np.linalg.norm(verts-c,axis=1)<TOL) for c in corners):
        raise UnsupportedSpacePartition("Rotated/skewed IFC product is not a world cuboid")
    faces_found={(axis,side):0 for axis in range(3) for side in (0,1)}
    areas={key:0. for key in faces_found}
    vertex_sets={key:set() for key in faces_found}
    for face in verts[faces]:
        v1,v2=face[1]-face[0],face[2]-face[0]
        area=float(np.linalg.norm(np.cross(v1,v2)))/2
        if area<TOL or not math.isfinite(area):
            raise UnsupportedSpacePartition("Degenerate IFC cuboid triangle")
        matches=[(axis,side) for axis in range(3)
                 for side,bound in ((0,low[axis]),(1,high[axis]))
                 if np.max(np.abs(face[:,axis]-bound))<TOL]
        if len(matches)!=1:
            raise UnsupportedSpacePartition("Oblique IFC body surface")
        key=matches[0]
        faces_found[key]+=1;areas[key]+=area
        vertex_sets[key].update(tuple(np.round(x,7)) for x in face)
    for (axis,side),count in faces_found.items():
        other=[i for i in range(3) if i!=axis]
        if (count!=2 or len(vertex_sets[(axis,side)])!=4
                or abs(areas[(axis,side)]-dims[other[0]]*dims[other[1]])>1e-5):
            raise UnsupportedSpacePartition("Incomplete IFC cuboid face")
    return low,high


def _surface_polygon(space,relation):
    if relation.ConnectionGeometry is None or not relation.ConnectionGeometry.is_a("IfcConnectionSurfaceGeometry"):
        raise UnsupportedSpacePartition("Existing SpaceBoundary has no supported oriented surface")
    surf=relation.ConnectionGeometry.SurfaceOnRelatingElement
    if not surf:
        raise UnsupportedSpacePartition("Space boundary lacks relating Space surface")
    transform=ifcopenshell.util.placement.get_local_placement(space.ObjectPlacement)
    if surf.is_a("IfcSurfaceOfLinearExtrusion"):
        profile=surf.SweptCurve
        if not profile.is_a("IfcArbitraryOpenProfileDef") or not profile.Curve.is_a("IfcPolyline"):
            raise UnsupportedSpacePartition("Space boundary swept profile type unsupported")
        pts=list(profile.Curve.Points)
        if len(pts)!=2 or any(len(p.Coordinates)!=2 for p in pts):
            raise UnsupportedSpacePartition("Space boundary extrusion must use a two-point base line")
        transform=transform@ifcopenshell.util.placement.get_axis2placement(surf.Position)
        origin=np.array([(transform@np.array((*p.Coordinates,0.,1.)))[:3] for p in pts])
        direction=np.asarray(surf.ExtrudedDirection.DirectionRatios,dtype=float)
        if np.linalg.norm(direction)<TOL or not math.isfinite(float(surf.Depth)) or float(surf.Depth)<TOL:
            raise UnsupportedSpacePartition("Boundary sweep direction/depth unsupported")
        ext=transform[:3,:3]@(direction/np.linalg.norm(direction)*float(surf.Depth))
        corners=np.array((origin[0],origin[1],origin[1]+ext,origin[0]+ext))
    elif surf.is_a("IfcCurveBoundedPlane"):
        if not surf.BasisSurface.is_a("IfcPlane") or not surf.OuterBoundary.is_a("IfcPolyline"):
            raise UnsupportedSpacePartition("Unsupported native planar boundary surface")
        transform=transform@ifcopenshell.util.placement.get_axis2placement(surf.BasisSurface.Position)
        boundary=list(surf.OuterBoundary.Points)
        coords=[p.Coordinates for p in boundary]
        if len(coords)!=5 or coords[0]!=coords[-1] or any(len(p)!=2 for p in coords):
            raise UnsupportedSpacePartition("Boundary plane must have closed rectangular polyline")
        corners=np.array([(transform@np.array((*p,0.,1.)))[:3] for p in coords[:4]])
    else:
        raise UnsupportedSpacePartition("Unsupported native oriented space boundary shape")
    if not np.isfinite(corners).all() or len(corners)!=4:
        raise UnsupportedSpacePartition("SpaceBoundary contains nonfinite/degenerate geometry")
    # The cyclic four corners have a single planar constant coordinate,
    # a complete rectangle, and a deterministic outward orientation.
    low=corners.min(axis=0);high=corners.max(axis=0)
    flat=[i for i in range(3) if high[i]-low[i]<TOL]
    if len(flat)!=1:
        raise UnsupportedSpacePartition("SpaceBoundary is not a world-axis rectangular plane")
    axis=flat[0]
    other=[i for i in range(3) if i!=axis]
    if any(high[k]-low[k]<TOL for k in other):
        raise UnsupportedSpacePartition("SpaceBoundary has zero planar area")
    expected=np.array(list(product(*zip(low[other],high[other]))))
    if any(not np.any(np.linalg.norm(corners[:,other]-p,axis=1)<TOL) for p in expected):
        raise UnsupportedSpacePartition("SpaceBoundary is not a complete plane rectangle")
    normal=np.cross(corners[1]-corners[0],corners[3]-corners[0])
    magnitude=np.linalg.norm(normal)
    if magnitude<TOL:
        raise UnsupportedSpacePartition("SpaceBoundary has degenerate surface normal")
    normal/=magnitude
    if abs(abs(normal[axis])-1.)>1e-6:
        raise UnsupportedSpacePartition("SpaceBoundary normal not aligned with its plane")
    return low,high,axis,normal


def plan_rectangular_space_partition(original_f,generated_f,space_guid:str,
                                     new_wall_guid:str)->SpacePartitionPreflight:
    """Read-only bounded 1st-level Space/Wall partition, fail before IFC writes.

    The right-hand Wall is full room width/height and creates a nonzero gap
    in Y. The original Space is treated as **near** the existing y-min edge,
    while any new far Space identity is UNASSIGNED pending explicit XML.
    """
    if original_f.schema!="IFC4X3" or generated_f.schema!="IFC4X3":
        raise UnsupportedSpacePartition("Only pinned metre-unit IFC4X3 supported")
    try:
        space=original_f.by_guid(space_guid)
        wall=generated_f.by_guid(new_wall_guid)
    except RuntimeError as exc:
        raise UnsupportedSpacePartition("Space or partition Wall identity absent") from exc
    near,far=_exact_box(space,kind="IfcSpace")
    wl,wh=_exact_box(wall,kind="IfcWall")
    if (not np.allclose(wl[[0,2]],near[[0,2]],atol=TOL,rtol=0)
            or not np.allclose(wh[[0,2]],far[[0,2]],atol=TOL,rtol=0)
            or not (near[1]+TOL<wl[1]<wh[1]<far[1]-TOL)):
        raise UnsupportedSpacePartition("Wall must form full-width/full-height interior Y partition")
    original_volume=float(np.prod(far-near))
    near_high=np.array((far[0],wl[1],far[2]),dtype=float)
    far_low=np.array((near[0],wh[1],near[2]),dtype=float)
    near_vol=float(np.prod(near_high-near))
    far_vol=float(np.prod(far-far_low))
    wall_vol=float(np.prod(wh-wl))
    if not math.isclose(original_volume,near_vol+far_vol+wall_vol,abs_tol=1e-5,rel_tol=1e-8):
        raise UnsupportedSpacePartition("New Wall/Space partition volume not conserved")
    # This is a one-space split; reject intersections with any OTHER existing Space.
    for entity in original_f.by_type("IfcSpace"):
        if entity.GlobalId==space_guid:continue
        ol,oh=_exact_box(entity,kind="IfcSpace")
        overlap=np.maximum(np.minimum(oh,wh)-np.maximum(ol,wl),0)
        if float(np.prod(overlap))>TOL:
            raise UnsupportedSpacePartition("Partition Wall interferes with another original IfcSpace")
    if len(space.BoundedBy)<6:
        raise UnsupportedSpacePartition("Source Space has incomplete boundary declarations")
    patches=[]
    face_coverage=set()
    for rel in space.BoundedBy:
        if rel.is_a()!="IfcRelSpaceBoundary" or rel.Name!="1stLevel":
            raise UnsupportedSpacePartition("Only first-level oriented source SpaceBoundary supported")
        low,high,axis,normal=_surface_polygon(space,rel)
        fixed=[i for i in range(3) if i!=axis]
        expected_inward=(-1. if abs(low[axis]-near[axis])<=TOL
                         else 1. if abs(low[axis]-far[axis])<=TOL else None)
        if expected_inward is None or abs(normal[axis]-expected_inward)>1e-6:
            raise UnsupportedSpacePartition("Native boundary is not outward-oriented on Space surface")
        if (np.any(low<near-TOL) or np.any(high>far+TOL)):
            raise UnsupportedSpacePartition("SpaceBoundary surface extends outside source Space cuboid")
        source_type=rel.RelatedBuildingElement.is_a() if rel.RelatedBuildingElement else "VIRTUAL"
        if source_type=="VIRTUAL":
            # Preserve a historical virtual/unlinked relation, but do not
            # fabricate a new virtual element when splitting the space.
            if str(rel.PhysicalOrVirtualBoundary)!="VIRTUAL":
                raise UnsupportedSpacePartition("Missing physical SpaceBoundary building element")
        elif str(rel.PhysicalOrVirtualBoundary)!="PHYSICAL":
            raise UnsupportedSpacePartition("Unsupported inconsistent virtual/physical boundary")
        nlo=np.maximum(low,near);nhi=np.minimum(high,near_high)
        flo=np.maximum(low,far_low);fhi=np.minimum(high,far)
        def visible(a,b):
            # A plane outside a region cannot count merely because its
            # two in-plane dimensions are nonzero.
            return (np.all(b>=a-TOL) and
                    all(b[i]-a[i]>TOL for i in range(3) if i!=axis))
        near_valid=visible(nlo,nhi)
        far_valid=visible(flo,fhi)
        # Compare true areas, not merely bounding overlap of a door/window.
        area=float(np.prod([(high[i]-low[i]) for i in range(3) if i!=axis]))
        sum_areas=0.
        if near_valid: sum_areas+=float(np.prod([(nhi[i]-nlo[i]) for i in range(3) if i!=axis]))
        if far_valid: sum_areas+=float(np.prod([(fhi[i]-flo[i]) for i in range(3) if i!=axis]))
        # Source planar surfaces on the cut-through x/z side have their
        # mid-strip occluded by the new Wall; all remaining visible area must
        # equal original minus that geometric occlusion.
        occlusion=0.
        if axis!=1 and high[1]>wl[1]+TOL and low[1]<wh[1]-TOL:
            occlusion=float(min(high[1],wh[1])-max(low[1],wl[1]))
            other_axis=next(i for i in range(3) if i not in (axis,1))
            occlusion*=float(high[other_axis]-low[other_axis])
        if not math.isclose(sum_areas+occlusion,area,abs_tol=1e-5,rel_tol=1e-8):
            raise UnsupportedSpacePartition("Boundary surface partition/occlusion area mismatch")
        if not near_valid and not far_valid:
            raise UnsupportedSpacePartition("Source boundary disappeared under partition")
        action=("SPLIT_BOTH" if near_valid and far_valid else
                "KEEP_NEAR" if near_valid else "REHOME_FAR")
        if source_type=="VIRTUAL" and action=="SPLIT_BOTH":
            raise UnsupportedSpacePartition("Shared virtual boundary needs explicit virtual element")
        plane=f"xyz"[axis]
        if (abs(low[axis]-near[axis])<TOL or abs(low[axis]-far[axis])<TOL):
            face_coverage.add((axis,round(float(low[axis]),6)))
        patches.append(BoundaryPatch(
            rel.GlobalId,action,source_type,plane,_as_tuple(normal),
            _as_tuple(low),_as_tuple(high),
            _as_tuple(nlo) if near_valid else None,
            _as_tuple(nhi) if near_valid else None,
            _as_tuple(flo) if far_valid else None,
            _as_tuple(fhi) if far_valid else None))
    for axis in range(3):
        for value in (near[axis],far[axis]):
            if (axis,round(float(value),6)) not in face_coverage:
                raise UnsupportedSpacePartition("Original Space perimeter face has no declared boundary")
    bottom=(np.array((near[0],wl[1],near[2])),np.array((far[0],wl[1],far[2])))
    top=(np.array((near[0],wh[1],near[2])),np.array((far[0],wh[1],far[2])))
    surfaces=(
        ("NEAR_PARTITION_FACE",_as_tuple(bottom[0]),_as_tuple(bottom[1]),(0.,1.,0.)),
        ("FAR_PARTITION_FACE",_as_tuple(top[0]),_as_tuple(top[1]),(0.,-1.,0.)),
    )
    return SpacePartitionPreflight(
        space_guid,new_wall_guid,_as_tuple(near),_as_tuple(near_high),
        _as_tuple(far_low),_as_tuple(far),
        *[round(x,8) for x in (original_volume,near_vol,far_vol,wall_vol)],
        tuple(sorted(patches,key=lambda p:p.boundary_id)),
        surfaces,True)
