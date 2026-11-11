"""Narrow *planar* IFC4X3 first-level space-boundary footprint verification.

A collection of full-height, vertical, wall-related IfcRelSpaceBoundary
surfaces can form a closed XY wall ring. This does NOT prove a closed 3D
boundary shell: floor/ceiling surfaces, surface orientation, topological
face matching and arbitrary IFC geometry remain OUT OF SCOPE.

This is a trusted runtime-only geometry validator; direct-markup agents
never see or call it. Fail closed for unfamiliar boundary surfaces.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math

import ifcopenshell
import ifcopenshell.util.placement
import numpy as np

from src.runtime.ifc_mutations import UnsupportedIFCMutation

TOL = 1e-6


@dataclass(frozen=True)
class FootprintEvidence:
    space_guid: str
    wall_boundary_guids: tuple[str, ...]
    wall_segment_signatures: tuple[tuple, ...]
    other_boundary_guids: tuple[str, ...]
    other_segment_signatures: tuple[tuple, ...]
    wall_perimeter_m: float
    enclosed_plan_area_m2: float
    wall_boundary_depth_m: float


def _source_boundary_segment(relation):
    if (not relation.is_a("IfcRelSpaceBoundary")
            or relation.Name != "1stLevel"
            or str(relation.PhysicalOrVirtualBoundary) != "PHYSICAL"
            or str(relation.InternalOrExternalBoundary) != "EXTERNAL"):
        raise UnsupportedIFCMutation("Unsupported native SpaceBoundary class/level/type")
    geom = relation.ConnectionGeometry
    if geom is None or not geom.is_a("IfcConnectionSurfaceGeometry"):
        raise UnsupportedIFCMutation("SpaceBoundary missing connection surface")
    surface = geom.SurfaceOnRelatingElement
    if (surface is None or not surface.is_a("IfcSurfaceOfLinearExtrusion")
            or geom.SurfaceOnRelatedElement is not None):
        raise UnsupportedIFCMutation("Unsupported SpaceBoundary surface mapping")
    curve = surface.SweptCurve
    if (curve is None or not curve.is_a("IfcArbitraryOpenProfileDef")
            or not curve.Curve.is_a("IfcPolyline")
            or len(curve.Curve.Points) != 2):
        raise UnsupportedIFCMutation("Boundary swept profile must be exactly one line")
    points = [np.asarray(point.Coordinates, dtype=float)
              for point in curve.Curve.Points]
    if any(len(p) not in (2,3) or not np.isfinite(p).all() for p in points):
        raise UnsupportedIFCMutation("Bad planar boundary profile coordinates")
    # The profile coordinates live in the surface's 3D Axis2Placement.
    try:
        matrix = np.asarray(
            ifcopenshell.util.placement.get_axis2placement(surface.Position),
            dtype=float)
        direction = np.asarray(surface.ExtrudedDirection.DirectionRatios,dtype=float)
        depth = float(surface.Depth)
    except Exception as exc:
        raise UnsupportedIFCMutation("Boundary surface placement invalid") from exc
    if (matrix.shape != (4,4) or len(direction)!=3
            or not np.isfinite(matrix).all() or not np.isfinite(direction).all()
            or not math.isfinite(depth) or depth<=TOL):
        raise UnsupportedIFCMutation("Degenerate boundary extrusion")
    direction /= np.linalg.norm(direction)
    if (not np.allclose(matrix[:3,:3] @ direction,(0,0,1),atol=TOL,rtol=0)
            or abs(float(np.linalg.det(matrix[:3,:3]))-1)>TOL):
        raise UnsupportedIFCMutation("Boundary extrusion is not vertical rigid transform")
    world=[]
    for p in points:
        xyz=np.array((float(p[0]),float(p[1]),float(p[2]) if len(p)==3 else 0.,1.))
        world.append((matrix @ xyz)[:3])
    left,right=world
    if (not np.allclose(left[2],right[2],atol=TOL,rtol=0)
            or np.linalg.norm(left[:2]-right[:2])<=TOL):
        raise UnsupportedIFCMutation("Boundary is not horizontal finite segment")
    return left,right,depth


def _q(point):
    p=np.asarray(point,dtype=float)
    return tuple(int(round(x/TOL)) for x in p[:2])


def _segment_signature(relation):
    a,b,h=_source_boundary_segment(relation)
    endpoint=tuple(sorted((_q(a),_q(b))))
    return (relation.GlobalId,endpoint,
            round(float(a[2])/TOL),round(h/TOL))


def _point_on_edge(p, a, b):
    p=np.asarray(p,dtype=float)
    a=np.asarray(a,dtype=float)
    b=np.asarray(b,dtype=float)
    vec=b-a
    t=float(np.dot(p-a,vec)/np.dot(vec,vec))
    cross=float(vec[0]*(p[1]-a[1])-vec[1]*(p[0]-a[0]))
    return (t>=-TOL and t<=1+TOL
            and abs(cross)<=TOL*max(1.,float(np.linalg.norm(vec))))


def _nonneighbor_intersections(a,b,c,d):
    """Proper segment crossing excluding shared endpoints in polygon ring."""
    def orient(x,y,z):
        return (y[0]-x[0])*(z[1]-x[1])-(y[1]-x[1])*(z[0]-x[0])
    t1=orient(a,b,c)
    t2=orient(a,b,d)
    t3=orient(c,d,a)
    t4=orient(c,d,b)
    return t1*t2 < -TOL*TOL and t3*t4 < -TOL*TOL


def _wall_loop(walls):
    if len(walls)<3:
        raise UnsupportedIFCMutation("Space has fewer than three Wall boundary segments")
    graph=defaultdict(set)
    segment_by_endpoints={}
    z_base=[]
    depths=[]
    points={}
    for rel in walls:
        a,b,h=_source_boundary_segment(rel)
        x,y=_q(a),_q(b)
        if x==y or frozenset((x,y)) in segment_by_endpoints:
            raise UnsupportedIFCMutation("Duplicate or degenerate Wall perimeter segment")
        segment_by_endpoints[frozenset((x,y))]=rel.GlobalId
        graph[x].add(y)
        graph[y].add(x)
        points[x]=a[:2]
        points[y]=b[:2]
        z_base.append(float(a[2]))
        depths.append(float(h))
    if (any(len(n)!=2 for n in graph.values())
            or len(graph)!=len(walls)
            or not np.allclose(z_base,z_base[0],atol=TOL,rtol=0)
            or not np.allclose(depths,depths[0],atol=TOL,rtol=0)):
        raise UnsupportedIFCMutation(
            "Space Wall-boundary footprint has open/branched/unequal-height perimeter")
    start=min(graph)
    current=start
    previous=None
    ordered=[start]
    visited_edges=set()
    while True:
        options=graph[current]-({previous} if previous is not None else set())
        if len(options)!=1 and previous is not None:
            raise UnsupportedIFCMutation("Ambiguous native Wall-boundary perimeter")
        nxt=min(options)
        edge=frozenset((current,nxt))
        if edge in visited_edges:
            raise UnsupportedIFCMutation("Native Wall-boundary loop repeats an edge")
        visited_edges.add(edge)
        if nxt==start:
            break
        ordered.append(nxt)
        previous,current=current,nxt
        if len(ordered)>len(walls):
            raise UnsupportedIFCMutation("Native Wall-boundary loop not simple")
    if len(visited_edges)!=len(walls) or len(ordered)!=len(walls):
        raise UnsupportedIFCMutation("Disconnected Wall-boundary loops")
    coords=np.array([points[p] for p in ordered],dtype=float)
    signed_area=0.5*float(
        np.dot(coords[:,0],np.roll(coords[:,1],-1))
        -np.dot(coords[:,1],np.roll(coords[:,0],-1)))
    if abs(signed_area)<=TOL:
        raise UnsupportedIFCMutation("Native Wall perimeter has no enclosed area")
    segments=[(coords[i],coords[(i+1)%len(coords)]) for i in range(len(coords))]
    for i,(a,b) in enumerate(segments):
        for j,(c,d) in enumerate(segments):
            if j<=i+1 or (i==0 and j==len(segments)-1):
                continue
            if _nonneighbor_intersections(a,b,c,d):
                raise UnsupportedIFCMutation("Self-intersecting Wall-boundary footprint")
    perimeter=sum(float(np.linalg.norm(b-a)) for a,b in segments)
    return tuple(segments),round(abs(signed_area),6),round(perimeter,6),float(depths[0])


def survey_space_wall_footprints(model) -> dict[str,FootprintEvidence]:
    """Return exact narrow 2D ring proof per existing native IfcSpace."""
    rooms=model.by_type("IfcSpace")
    if not rooms or any(not r.GlobalId for r in rooms):
        raise UnsupportedIFCMutation("No uniquely identified native IfcSpace")
    records={}
    for space in rooms:
        rels=list(space.BoundedBy)
        if (not rels or any(rel.RelatingSpace!=space for rel in rels)
                or len({x.GlobalId for x in rels})!=len(rels)):
            raise UnsupportedIFCMutation("Space native boundary inventory inconsistent")
        walls=[r for r in rels if r.RelatedBuildingElement is not None
               and r.RelatedBuildingElement.is_a("IfcWall")]
        other=[r for r in rels if r not in walls]
        edges,area,perimeter,wall_height=_wall_loop(walls)
        for rel in other:
            element=rel.RelatedBuildingElement
            if (element is None or not element.is_a() in ("IfcDoor","IfcWindow")):
                raise UnsupportedIFCMutation("Unrecognized non-wall native SpaceBoundary")
            a,b,depth=_source_boundary_segment(rel)
            if (a[2] < -TOL or a[2]+depth>wall_height+TOL
                    or not any(_point_on_edge(a[:2],c,d)
                               and _point_on_edge(b[:2],c,d)
                               for c,d in edges)):
                raise UnsupportedIFCMutation(
                    "Opening SpaceBoundary no longer overlays source Wall perimeter")
        records[space.GlobalId]=FootprintEvidence(
            space.GlobalId,
            tuple(sorted(r.GlobalId for r in walls)),
            tuple(sorted(_segment_signature(r) for r in walls)),
            tuple(sorted(r.GlobalId for r in other)),
            tuple(sorted(_segment_signature(r) for r in other)),
            perimeter,area,round(wall_height,6),
        )
    if len(records)!=len(rooms):
        raise UnsupportedIFCMutation("Duplicate native Space GlobalId in footprint")
    return records


def verify_door_delete_boundary_footprints(source, output,
                                            boundary_guid: str) -> dict:
    """Verify *2D Wall ring continuity only* and exact boundary surface delta.

    No claim about full 3D IfcRelSpaceBoundary shell closure or the official
    author-provided benchmark scorer can follow from this check.
    """
    before=survey_space_wall_footprints(source)
    after=survey_space_wall_footprints(output)
    if set(before)!=set(after):
        raise UnsupportedIFCMutation("Native Room identity changed in footprint audit")
    affected=[guid for guid,r in before.items()
              if boundary_guid in r.other_boundary_guids]
    if len(affected)!=1:
        raise UnsupportedIFCMutation("Deleted Door boundary has ambiguous Space owner")
    affected_id=affected[0]
    out=[]
    for guid in sorted(before):
        old=before[guid]
        new=after[guid]
        if (old.wall_boundary_guids!=new.wall_boundary_guids
                or old.wall_segment_signatures!=new.wall_segment_signatures
                or old.enclosed_plan_area_m2!=new.enclosed_plan_area_m2
                or old.wall_perimeter_m!=new.wall_perimeter_m
                or old.wall_boundary_depth_m!=new.wall_boundary_depth_m):
            raise UnsupportedIFCMutation("Door edit damaged existing Wall perimeter surfaces")
        removed=set(old.other_boundary_guids)-set(new.other_boundary_guids)
        added=set(new.other_boundary_guids)-set(old.other_boundary_guids)
        if (removed!=({boundary_guid} if guid==affected_id else set())
                or added):
            raise UnsupportedIFCMutation("Unapproved Door/Window boundary identity change")
        existing_segments={signature[0]:signature for signature in old.other_segment_signatures}
        new_segments={signature[0]:signature for signature in new.other_segment_signatures}
        if (set(new_segments)-set(existing_segments)
                or any(existing_segments[k]!=v for k,v in new_segments.items())):
            raise UnsupportedIFCMutation("Preserved Door/Window boundary surface geometry changed")
        out.append({
            "source_and_result_wall_segment_counts":[len(old.wall_boundary_guids),
                                                     len(new.wall_boundary_guids)],
            "source_and_result_nonwall_boundary_counts":[len(old.other_boundary_guids),
                                                       len(new.other_boundary_guids)],
            "wall_footprint_area_m2":old.enclosed_plan_area_m2,
            "wall_footprint_perimeter_m":old.wall_perimeter_m,
            "wall_boundary_vertical_height_m":old.wall_boundary_depth_m,
            "removed_door_boundary":guid==affected_id,
        })
    return {
        "status":"PASS_CLOSED_2D_WALL_PERIMETERS_3D_SHELL_NOT_VERIFIED",
        "space_count":len(out),
        "spaces":out,
        "wall_perimeter_count_closed":len(out),
        "removed_door_boundary_overlaid_wall_ring":True,
        "full_3d_space_boundary_shell_closure_proven":False,
        "floor_ceiling_boundary_reconstruction_performed":False,
        "author_provided_bim_edit_scorer_executed":False,
    }
