"""Read-only, author-grader-free native IFC checks for PUBLIC BIBIMBAP test_05.

The public instruction requires one new 15 m wall beginning at (0,-10);
its direction is NOT constrained. This checks only the requested geometry
and root identity; collision nonregression and full unrelated-geometry
preservation remain *unverified*. Not a complete strict benchmark scorer.

This checker is separate from the XML compiler and original author test.
No author test code, target GUIDs, XML source or evaluator metadata is read.
"""
from __future__ import annotations

from hashlib import sha256
from math import isfinite
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.shape
import ifcopenshell.util.unit
import numpy as np

EXPECTED_LENGTH_M = 15.0
START_XY_M = (0.0, -10.0)
MAX_LENGTH_ERROR_M = 0.05
MAX_START_ERROR_M = 0.5
EXPECTED_MM_SCALE = 0.001
MAX_GEOMETRY_VERTICES = 2000


class NativeCoreError(ValueError):
    pass


def _hash(path: Path) -> str:
    with path.open("rb") as f:
        return sha256(f.read()).hexdigest()


def _root_classes(model) -> dict[str, str]:
    roots = list(model.by_type("IfcRoot"))
    pairs = {o.GlobalId: o.is_a() for o in roots}
    if len(pairs) != len(roots):
        raise NativeCoreError("Duplicate/missing IfcRoot GUID identity")
    return pairs


def _geometry_core(wall) -> tuple[float, float]:
    settings = ifcopenshell.geom.settings()
    shape = ifcopenshell.geom.create_shape(settings, wall)
    verts = np.asarray(
        ifcopenshell.util.shape.get_shape_vertices(shape, shape.geometry),
        dtype=np.float64,
    )
    if verts.ndim != 2 or verts.shape[1] != 3 or not 2 <= len(verts) <= MAX_GEOMETRY_VERTICES:
        raise NativeCoreError("Invalid native IFC wall shape vertices")
    xy = verts[:, :2]
    if not np.isfinite(xy).all():
        raise NativeCoreError("Nonfinite native IFC world coordinates")
    # IFC geometry outputs use world-space SI metres (default
    # IfcOpenShell geometry settings); never interpret raw STEP mm numbers
    # as lengths or trust an XML endpoint after compilation.
    difference = xy[:, None, :] - xy[None, :, :]
    span = float(np.sqrt(np.sum(difference * difference, axis=2)).max())
    start = np.asarray(START_XY_M, dtype=np.float64)
    nearest_start = float(np.sqrt(np.sum((xy - start) ** 2, axis=1)).min())
    if not isfinite(span) or not isfinite(nearest_start):
        raise NativeCoreError("Nonfinite physical span or start")
    return span, nearest_start


def evaluate_public_test05_core(original_ifc: Path, predicted_ifc: Path) -> dict:
    original_ifc = Path(original_ifc).resolve(strict=True)
    predicted_ifc = Path(predicted_ifc).resolve(strict=True)
    if original_ifc == predicted_ifc or not original_ifc.is_file() or not predicted_ifc.is_file():
        raise NativeCoreError("Two independent IFC paths required")
    before_source = _hash(original_ifc)
    before_result = _hash(predicted_ifc)
    original = ifcopenshell.open(str(original_ifc))
    edited = ifcopenshell.open(str(predicted_ifc))
    scale_a = float(ifcopenshell.util.unit.calculate_unit_scale(original))
    scale_b = float(ifcopenshell.util.unit.calculate_unit_scale(edited))
    if original.schema != edited.schema or original.schema != "IFC4X3" or not (
            abs(scale_a - EXPECTED_MM_SCALE) < 1e-10 and
            abs(scale_b - EXPECTED_MM_SCALE) < 1e-10):
        raise NativeCoreError("Original/edited IFC schema or original mm units mismatch")
    prior_roots = _root_classes(original)
    new_roots = _root_classes(edited)
    identity_preserved = all(new_roots.get(k) == v for k, v in prior_roots.items())
    old_walls = {wall.GlobalId for wall in original.by_type("IfcWall")}
    added_walls = [wall for wall in edited.by_type("IfcWall")
                   if wall.GlobalId not in old_walls]
    exactly_one_new_wall = len(added_walls) == 1
    observed_length_m = None
    nearest_start_m = None
    dimensions_ok = False
    start_ok = False
    if exactly_one_new_wall:
        observed_length_m, nearest_start_m = _geometry_core(added_walls[0])
        dimensions_ok = abs(observed_length_m - EXPECTED_LENGTH_M) <= MAX_LENGTH_ERROR_M
        start_ok = nearest_start_m <= MAX_START_ERROR_M
    result = {
        "status": "IFC_NATIVE_PUBLIC_TASK_CORE_ONLY",
        "source_original_sha256": before_source,
        "predicted_result_sha256": before_result,
        "unit_scale_to_m": scale_b,
        "existing_root_class_identity_preserved": identity_preserved,
        "added_ifcwall_count": len(added_walls),
        "exactly_one_new_wall": exactly_one_new_wall,
        "native_max_horizontal_vertex_span_m": observed_length_m,
        "native_nearest_start_vertex_m": nearest_start_m,
        "public_length_pass": dimensions_ok,
        "public_start_pass": start_ok,
        "public_task_core_success": bool(
            exactly_one_new_wall and identity_preserved and dimensions_ok and start_ok),
        "clash_nonregression_verified": False,
        "untouched_geometry_identical_verified": False,
        "full_independent_strict_task_success": None,
        "author_grader_consulted": False,
        "llm_calls": 0,
    }
    if _hash(original_ifc) != before_source or _hash(predicted_ifc) != before_result:
        raise NativeCoreError("Unexpected mutation while reading native IFCs")
    return result
