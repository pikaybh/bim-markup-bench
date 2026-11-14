"""Original BIBIMBAP topological_test_15 native imperative Python I0.

Independent source+PUBLIC-question-only writer. No project runtime, XML,
prior D0 candidate, author scorer, author target, or evaluator imports.
This is NOT model-generated output or full BIM task equivalence.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import math
import os
import re
import tempfile

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np


class OriginalTopologicalSlabI0Blocked(ValueError):
    pass


@dataclass(frozen=True)
class TopologicalSlabI0Result:
    public_question_sha256: str
    original_normalized_source_sha256: str
    native_candidate_sha256: str
    upper_public_guid: str
    lower_public_guid: str
    native_world_z_delta_m: float
    original_source_byte_identical: bool
    native_copy_on_write_point: bool
    upper_lower_original_xy_overlap_m2: float


_QUESTION = re.compile(
    r"^Change the position of the slab with id ([0-9A-Za-z_$]{22}) "
    r"that it lays on the slab with the id ([0-9A-Za-z_$]{22})\.$"
)


def parse_public_topological_slab_question(question: str) -> tuple[str, str]:
    matched = _QUESTION.fullmatch(question.strip())
    if matched is None or matched[1] == matched[2]:
        raise OriginalTopologicalSlabI0Blocked(
            "Original public Slab-on-Slab task has unexpected semantics"
        )
    return matched[1], matched[2]


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _world_bounds(slab) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    try:
        shape = ifcopenshell.geom.create_shape(settings, slab)
    except Exception as exc:
        raise OriginalTopologicalSlabI0Blocked("Public source slab has no physical IFC world mesh") from exc
    v = shape.geometry.verts
    if not v or len(v) < 24 or len(v) % 3:
        raise OriginalTopologicalSlabI0Blocked("Public source slab world mesh incomplete")
    points = [v[i:i + 3] for i in range(0, len(v), 3)]
    if not np.all(np.isfinite(points)):
        raise OriginalTopologicalSlabI0Blocked("Nonfinite native world geometry")
    return (
        tuple(float(min(p[j] for p in points)) for j in range(3)),
        tuple(float(max(p[j] for p in points)) for j in range(3)),
    )


def run_original_topological_slab_i0(
    normalized_source: Path, public_question: str, output: Path
) -> TopologicalSlabI0Result:
    upper_guid, lower_guid = parse_public_topological_slab_question(public_question)
    if (
        not normalized_source.is_file()
        or normalized_source.is_symlink()
        or output.exists()
        or output.is_symlink()
        or normalized_source.resolve() == output.resolve()
        or not output.parent.is_dir()
    ):
        raise OriginalTopologicalSlabI0Blocked("Original source must be read-only, output unique")
    before_sha = _sha(normalized_source)
    model = ifcopenshell.open(str(normalized_source))
    if model.schema != "IFC4X3" or not math.isclose(
        ifcopenshell.util.unit.calculate_unit_scale(model), 1.0, abs_tol=1e-8
    ):
        raise OriginalTopologicalSlabI0Blocked("Original native IFC4X3 must be normalized to metres")
    try:
        upper = model.by_guid(upper_guid)
        lower = model.by_guid(lower_guid)
    except RuntimeError as exc:
        raise OriginalTopologicalSlabI0Blocked("Public original source Slab identity missing") from exc
    if not (upper.is_a("IfcSlab") and lower.is_a("IfcSlab")):
        raise OriginalTopologicalSlabI0Blocked("Public source targets must be native IfcSlab")
    up_min, up_max = _world_bounds(upper)
    low_min, low_max = _world_bounds(lower)
    width_overlap = min(up_max[0], low_max[0]) - max(up_min[0], low_min[0])
    depth_overlap = min(up_max[1], low_max[1]) - max(up_min[1], low_min[1])
    if width_overlap <= 1e-6 or depth_overlap <= 1e-6:
        raise OriginalTopologicalSlabI0Blocked("Requested vertical positioning lacks real XY contact")
    dz = float(low_max[2] - up_min[2])
    if not math.isfinite(dz) or abs(dz) > 100:
        raise OriginalTopologicalSlabI0Blocked("Original physical Z contact delta unsafe")
    if abs(dz) < 1e-8:
        raise OriginalTopologicalSlabI0Blocked("Source is already resting on lower slab")
    placement = upper.ObjectPlacement
    if placement is None or not placement.is_a("IfcLocalPlacement"):
        raise OriginalTopologicalSlabI0Blocked("Original Slab native local placement absent")
    relative = placement.RelativePlacement
    if relative is None or not relative.is_a("IfcAxis2Placement3D"):
        raise OriginalTopologicalSlabI0Blocked("Source Slab lacks 3D native placement axis")
    point = relative.Location
    if point is None or not point.is_a("IfcCartesianPoint") or len(point.Coordinates) != 3:
        raise OriginalTopologicalSlabI0Blocked("Source Slab has no safe 3D placement")
    if (len(model.get_inverse(placement)) != 1
        or next(iter(model.get_inverse(placement))).id() != upper.id()
        or len(model.get_inverse(relative)) != 1
        or next(iter(model.get_inverse(relative))).id() != placement.id()):
        raise OriginalTopologicalSlabI0Blocked("Source Slab local placement belongs to another object")
    parent = placement.PlacementRelTo
    if parent is None:
        rotation = np.eye(3)
    else:
        rotation = np.asarray(
            ifcopenshell.util.placement.get_local_placement(parent), dtype=float
        )[:3, :3]
    if (not np.all(np.isfinite(rotation)) or
        not np.allclose(rotation.T @ rotation, np.eye(3), rtol=0, atol=1e-7)):
        raise OriginalTopologicalSlabI0Blocked("Source Slab parent reference is not rigid")
    local = rotation.T @ np.array([0., 0., dz])
    previous = tuple(float(value) for value in point.Coordinates)
    if not np.all(np.isfinite(previous)):
        raise OriginalTopologicalSlabI0Blocked("Nonfinite source native placement coordinates")
    changed = tuple(previous[i] + float(local[i]) for i in range(3))
    if any(not math.isfinite(n) or abs(n) > 1e4 for n in changed):
        raise OriginalTopologicalSlabI0Blocked("New native Slab placement out of bounds")
    point_owners = model.get_inverse(point)
    owned = len(point_owners) == 1 and point_owners[0].id() == relative.id()
    if not any(ref.id() == relative.id() for ref in point_owners):
        raise OriginalTopologicalSlabI0Blocked("Original native point ownership inconsistent")
    if owned:
        point.Coordinates = changed
    else:
        # Original IFC4X3 has a shared origin point (#3); do not move it.
        # A real independent native imperative IfcOpenShell edit must COW.
        new_point = model.createIfcCartesianPoint(changed)
        relative.Location = new_point
    if _sha(normalized_source) != before_sha:
        raise OriginalTopologicalSlabI0Blocked("Original public native source mutated")
    with tempfile.TemporaryDirectory(prefix="bmb-v017-native-slab-i0-", dir=output.parent) as td:
        stage = Path(td) / "candidate_native.ifc"
        model.write(str(stage))
        if output.exists() or _sha(normalized_source) != before_sha:
            raise OriginalTopologicalSlabI0Blocked("Source or destination changed before commit")
        os.rename(stage, output)
    if _sha(normalized_source) != before_sha:
        raise OriginalTopologicalSlabI0Blocked("Original public source mutated after writing")
    return TopologicalSlabI0Result(
        public_question_sha256=sha256(public_question.encode("utf8")).hexdigest(),
        original_normalized_source_sha256=before_sha,
        native_candidate_sha256=_sha(output),
        upper_public_guid=upper_guid,
        lower_public_guid=lower_guid,
        native_world_z_delta_m=dz,
        original_source_byte_identical=True,
        native_copy_on_write_point=not owned,
        upper_lower_original_xy_overlap_m2=width_overlap * depth_overlap,
    )
