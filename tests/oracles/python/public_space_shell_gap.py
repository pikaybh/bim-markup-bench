"""Trusted source-only IfcSpace *shape mesh* vs IFC boundary-shell gap witness.

The IFC4.3 standard describes first-level boundaries of a completely
enclosed space as a closed shell. An IfcSpace product mesh can be a closed
solid while the separate IfcRelSpaceBoundary surfaces omit floor/ceiling
faces. These are distinct facts. Do not infer benchmark-author scoring.

Checks a narrowly pinned, fully rectangular IFC4X3 source; it is NOT a
generic Room/SpaceBoundary validator or any model-visible tool.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import numpy as np

from src.runtime.ifc_mutations import UnsupportedIFCMutation
from src.runtime.space_boundary_footprint import (
    _source_boundary_segment, survey_space_wall_footprints,
    verify_door_delete_boundary_footprints,
)

TOL = 1e-6
INPUT_SHA = "170d9ed9c10a31d86c3ff2207a450fd552166af21472486f11004f6e2b14defb"


class SourceSpaceShellEvidenceBlocked(ValueError):
    """Reject ambiguous source, invalid shell, or unrelated native edits."""


def _verified_sha(path:Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise SourceSpaceShellEvidenceBlocked("Missing or linked local IFC evidence")
    return sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class SpaceMesh:
    vertices: int
    triangles: int
    edges: int
    closed_oriented_manifold: bool
    floor_tris: int
    ceiling_tris: int
    floor_area_m2: float
    ceiling_area_m2: float
    signed_volume_m3: float
    bbox_height_m: float
    vertex_multiset: tuple


def _mesh(entity) -> SpaceMesh:
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    try:
        shape = ifcopenshell.geom.create_shape(settings, entity)
        pts = np.asarray(shape.geometry.verts, dtype=np.float64).reshape(-1, 3)
        tris = np.asarray(shape.geometry.faces, dtype=np.int64).reshape(-1, 3)
    except Exception as exc:
        raise SourceSpaceShellEvidenceBlocked("IfcSpace world mesh cannot be extracted") from exc
    if (len(pts) < 4 or len(tris) < 4 or not np.isfinite(pts).all()
            or np.any(tris < 0) or np.any(tris >= len(pts))):
        raise SourceSpaceShellEvidenceBlocked("IfcSpace mesh is invalid or empty")
    edge_dir = defaultdict(list)
    adjacency = defaultdict(set)
    floor_indices = []
    ceiling_indices = []
    zmin = float(pts[:, 2].min())
    zmax = float(pts[:, 2].max())
    for tid, (a, b, c) in enumerate(tris):
        a, b, c = int(a), int(b), int(c)
        if len({a, b, c}) != 3 or np.linalg.norm(np.cross(
                pts[b]-pts[a],pts[c]-pts[a])) <= TOL:
            raise SourceSpaceShellEvidenceBlocked("IfcSpace mesh has degenerate triangles")
        for u, v in ((a, b), (b, c), (c, a)):
            edge_dir[tuple(sorted((u, v)))].append((u, v, tid))
        if np.allclose(pts[[a, b, c], 2], zmin, atol=TOL, rtol=0):
            floor_indices.append(tid)
        elif np.allclose(pts[[a, b, c], 2], zmax, atol=TOL, rtol=0):
            ceiling_indices.append(tid)
    for directed in edge_dir.values():
        if (len(directed) != 2
                or directed[0][0] != directed[1][1]
                or directed[0][1] != directed[1][0]):
            raise SourceSpaceShellEvidenceBlocked("IfcSpace product mesh is not closed and oriented")
        adjacency[directed[0][2]].add(directed[1][2])
        adjacency[directed[1][2]].add(directed[0][2])
    connected = {0}
    todo = [0]
    while todo:
        current = todo.pop()
        for nxt in adjacency[current] - connected:
            connected.add(nxt)
            todo.append(nxt)
    if len(connected) != len(tris):
        raise SourceSpaceShellEvidenceBlocked("IfcSpace product mesh has disconnected shells")
    x, y, z = pts[tris[:,0]], pts[tris[:,1]], pts[tris[:,2]]
    signed_volume = float(np.einsum("ij,ij->",x,np.cross(y,z))/6.0)
    if not np.isfinite(signed_volume) or signed_volume <= TOL:
        raise SourceSpaceShellEvidenceBlocked("IfcSpace product volume is nonpositive")
    extrema = pts.max(axis=0)-pts.min(axis=0)
    if not np.isclose(signed_volume, float(np.prod(extrema)),atol=TOL,rtol=0):
        raise SourceSpaceShellEvidenceBlocked("Space is not a complete rectangular source solid")
    cap_area = float(extrema[0]*extrema[1])
    def triangle_area(indices):
        return sum(float(np.linalg.norm(np.cross(
            pts[tris[t,1]]-pts[tris[t,0]],
            pts[tris[t,2]]-pts[tris[t,0]]))/2) for t in indices)
    if (len(floor_indices)!=2 or len(ceiling_indices)!=2
            or not np.isclose(triangle_area(floor_indices),cap_area,atol=TOL,rtol=0)
            or not np.isclose(triangle_area(ceiling_indices),cap_area,atol=TOL,rtol=0)):
        raise SourceSpaceShellEvidenceBlocked("Expected rectangular solid floor/ceiling cap triangles")
    quantized = tuple(sorted(map(
        tuple, np.rint(pts/TOL).astype(np.int64))))
    return SpaceMesh(
        vertices=len(pts),triangles=len(tris),edges=len(edge_dir),
        closed_oriented_manifold=True,
        floor_tris=len(floor_indices),ceiling_tris=len(ceiling_indices),
        floor_area_m2=round(cap_area,6),ceiling_area_m2=round(cap_area,6),
        signed_volume_m3=round(signed_volume,6),
        bbox_height_m=round(float(extrema[2]),6),
        vertex_multiset=quantized,
    )


def _source_boundary_faces(room) -> tuple[int, int]:
    """Return counts of vertical and horizontal boundary RELATION surfaces.

    Geometry is read from the actual IfcConnectionSurfaceGeometry,
    rather than inferred from the closed IfcSpace product representation.
    All supported surfaces here are vertical extrusions of a horizontal
    segment. If that is no longer true, fail closed, do not classify it
    as a newly repaired horizontal boundary.
    """
    vertical = 0
    horizontal = 0
    for boundary in room.BoundedBy:
        if boundary.RelatingSpace != room:
            raise SourceSpaceShellEvidenceBlocked("Native boundary associated to wrong Room")
        try:
            a, b, depth = _source_boundary_segment(boundary)
        except (UnsupportedIFCMutation,ValueError,TypeError) as exc:
            raise SourceSpaceShellEvidenceBlocked("Unsupported nonvertical or malformed first-level boundary") from exc
        if not np.isclose(a[2],b[2],atol=TOL,rtol=0) or depth<=TOL:
            raise SourceSpaceShellEvidenceBlocked("Nonvertical native Room boundary")
        vertical += 1
    return vertical, horizontal


def _open(path:Path):
    try:
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing or linked public IFC")
        with path.open("rb") as fh:
            if not fh.read(96).lstrip(b" \r\n\t").startswith(b"ISO-10303-21;"):
                raise ValueError("Malformed STEP header")
        return ifcopenshell.open(str(path))
    except Exception as exc:
        raise SourceSpaceShellEvidenceBlocked("Invalid pinned IFC evidence") from exc


def verify_source_inherited_space_boundary_gap(source_ifc: Path,
                                                generated_ifc: Path,
                                                removed_boundary_guid:str) -> dict:
    """Verify surviving baseline shape while refusing a false 3D boundary claim.

    The native source's first-level relation shell is already incomplete.
    The current edit is only expected to preserve that baseline, never to
    synthesize floor/ceiling relations not requested in public task text.
    """
    if _verified_sha(source_ifc)!=INPUT_SHA:
        raise SourceSpaceShellEvidenceBlocked("Frozen original IFC hash changed")
    output_sha=_verified_sha(generated_ifc)
    source = _open(source_ifc)
    result = _open(generated_ifc)
    if source.schema!="IFC4X3" or result.schema!=source.schema:
        raise SourceSpaceShellEvidenceBlocked("Unexpected IFC schema")
    native_before=source.by_type("IfcRelSpaceBoundary")
    native_after=result.by_type("IfcRelSpaceBoundary")
    if (len(native_before)!=12 or len(native_after)!=11
            or any(r.is_a()!="IfcRelSpaceBoundary" or r.Name!="1stLevel"
                   for r in (*native_before,*native_after))
            or source.by_type("IfcRelSpaceBoundary1stLevel")
            or result.by_type("IfcRelSpaceBoundary1stLevel")):
        raise SourceSpaceShellEvidenceBlocked("Unrecognized concrete first-level boundary inventory")
    try:
        footprint = verify_door_delete_boundary_footprints(
            source,result,removed_boundary_guid)
        base_rings = survey_space_wall_footprints(source)
        new_rings = survey_space_wall_footprints(result)
    except UnsupportedIFCMutation as exc:
        raise SourceSpaceShellEvidenceBlocked("Planar first-level Wall rings changed") from exc
    old_spaces={s.GlobalId:s for s in source.by_type("IfcSpace")}
    new_spaces={s.GlobalId:s for s in result.by_type("IfcSpace")}
    if old_spaces.keys()!=new_spaces.keys() or len(old_spaces)!=2:
        raise SourceSpaceShellEvidenceBlocked("Source Room inventory changed")
    per_room=[]
    for guid in sorted(old_spaces):
        before,after=old_spaces[guid],new_spaces[guid]
        old_mesh,new_mesh=_mesh(before),_mesh(after)
        if old_mesh!=new_mesh:
            raise SourceSpaceShellEvidenceBlocked("Existing IfcSpace product mesh altered")
        if base_rings[guid].enclosed_plan_area_m2 != old_mesh.floor_area_m2:
            raise SourceSpaceShellEvidenceBlocked("Room product floor area not equal to Wall boundary ring")
        if not np.isclose(
                base_rings[guid].wall_boundary_depth_m,
                old_mesh.bbox_height_m,atol=TOL,rtol=0):
            raise SourceSpaceShellEvidenceBlocked("Room mesh and wall boundary height mismatch")
        v_before,h_before=_source_boundary_faces(before)
        v_after,h_after=_source_boundary_faces(after)
        if (h_before!=0 or h_after!=0
                or (v_before,v_after) not in ((6,6),(6,5))
                or v_after!=len(after.BoundedBy)):
            raise SourceSpaceShellEvidenceBlocked("Unexpected native Room boundary surface coverage")
        per_room.append({
            "plan_area_m2":old_mesh.floor_area_m2,
            "height_m":old_mesh.bbox_height_m,
            "signed_mesh_volume_m3":old_mesh.signed_volume_m3,
            "original_and_result_mesh_closed_oriented":True,
            "native_mesh_vertices":old_mesh.vertices,
            "native_mesh_triangles":old_mesh.triangles,
            "native_mesh_edges":old_mesh.edges,
            "product_floor_mesh_triangles":old_mesh.floor_tris,
            "product_ceiling_mesh_triangles":old_mesh.ceiling_tris,
            "product_floor_mesh_area_m2":old_mesh.floor_area_m2,
            "product_ceiling_mesh_area_m2":old_mesh.ceiling_area_m2,
            "original_firstlevel_relation_surfaces":[v_before,h_before],
            "result_firstlevel_relation_surfaces":[v_after,h_after],
            "explicit_floor_boundary_relation_proven":False,
            "explicit_ceiling_boundary_relation_proven":False,
            "unrepaired_horizontal_coverage_gap_m2":
                round(old_mesh.floor_area_m2+old_mesh.ceiling_area_m2,6),
        })
    if (_verified_sha(source_ifc)!=INPUT_SHA
            or _verified_sha(generated_ifc)!=output_sha):
        raise SourceSpaceShellEvidenceBlocked("Native IFC evidence mutated during inspection")
    return {
        "status":"PASS_SOURCE_PRESERVED_3D_MESH_INHERITED_FIRSTLEVEL_RELATION_SHELL_GAP",
        "source_sha256":INPUT_SHA,
        "candidate_sha256":output_sha,
        "space_count":2,
        "planar_wall_perimeter_count_closed":footprint["wall_perimeter_count_closed"],
        "original_and_output_general_boundary_concrete_classes_only":True,
        "actual_IfcRelSpaceBoundary1stLevel_subclass_records":0,
        "original_generic_firstlevel_named_boundary_count":12,
        "output_generic_firstlevel_named_boundary_count":11,
        "per_room":sorted(per_room,key=lambda x:x["plan_area_m2"]),
        "native_IfcSpace_product_meshes_closed_and_preserved":True,
        "native_IfcRelSpaceBoundary_floor_ceiling_surfaces_absent_in_source":True,
        "native_IfcRelSpaceBoundary_floor_ceiling_surfaces_absent_in_output":True,
        "baseline_relative_unmodified_3d_relation_gap":True,
        "full_3d_spatial_boundary_shell_proven":False,
        "author_provided_evaluator_scoring_requirement_verified":False,
        "official_tasks_scored":0,
        "LLM_calls":0,
    }
