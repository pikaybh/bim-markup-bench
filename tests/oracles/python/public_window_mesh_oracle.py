"""Trusted, GT-free native IFC postcondition check for one frozen public Window task.

The check reads only the published natural-language instruction, immutable
original IFC, and a generated IFC candidate. It is deliberately independent
of the D0 XML compiler, I0 authoring recipe and the official benchmark grader.

This is a task-scoped deterministic oracle preflight, NOT a general scorer:
raw STEP row preservation is a strong fixture condition, not an assertion
that every semantically valid IFC representation must have identical rows.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import re

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.shape
import ifcopenshell.util.unit
import numpy as np


PUBLIC_MOVE = re.compile(
    r"Move the window with ID (?P<window>[A-Za-z0-9_$]{22}) "
    r"by (?P<distance>[0-9]+(?:\.[0-9]+)?)m in positive "
    r"(?P<axis>[xyz]) direction\. "
    r"Also move the opening (?P<opening>[A-Za-z0-9_$]{22}) "
    r"the same and preserve all relationships\.",
    re.ASCII,
)
TOL = 1e-6
EXPECTED_WORLD_MOVE = (0.0, 1.0, 0.0)


class PublicWindowMeshBlocked(ValueError):
    """Bail out on unmatched original/candidate BIM native evidence."""


def _sha(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise PublicWindowMeshBlocked("Missing or linked native IFC input")
    return sha256(path.read_bytes()).hexdigest()


def _public_guids(instruction: str) -> tuple[str, str]:
    if not isinstance(instruction, str) or len(instruction) > 512:
        raise PublicWindowMeshBlocked("Missing or oversized public task")
    m = PUBLIC_MOVE.fullmatch(instruction)
    if not m or m["axis"] != "y" or float(m["distance"]) != 1.0:
        raise PublicWindowMeshBlocked("Unsupported or ambiguous public Window task")
    if m["window"] == m["opening"]:
        raise PublicWindowMeshBlocked("Window and Opening must differ")
    return m["window"], m["opening"]


def _by_guid_class(model, guid: str, ifc_class: str):
    try:
        ent = model.by_guid(guid)
    except RuntimeError as exc:
        raise PublicWindowMeshBlocked("Public referenced IFC object missing") from exc
    if ent is None or not ent.is_a(ifc_class):
        raise PublicWindowMeshBlocked("Public referenced IFC object missing or wrong class")
    return ent


def _host_guid(model, window_guid: str, opening_guid: str) -> str:
    w = _by_guid_class(model, window_guid, "IfcWindow")
    opening = _by_guid_class(model, opening_guid, "IfcOpeningElement")
    fills = list(w.FillsVoids)
    voids = list(opening.VoidsElements)
    if (len(fills) != 1 or len(voids) != 1
        or fills[0].RelatingOpeningElement != opening
        or not voids[0].RelatingBuildingElement.is_a("IfcWall")
        or len(opening.HasFillings) != 1
        or opening.HasFillings[0].RelatedBuildingElement != w):
        raise PublicWindowMeshBlocked("Native Window/Opening/host graph invalid")
    return voids[0].RelatingBuildingElement.GlobalId


def _verts_and_metrics(entity) -> tuple[np.ndarray, int, float]:
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    try:
        shape = ifcopenshell.geom.create_shape(settings, entity)
        points = np.asarray(shape.geometry.verts, dtype=np.float64).reshape(-1, 3)
        triangles = len(shape.geometry.faces) // 3
        volume = float(ifcopenshell.util.shape.get_volume(shape.geometry))
    except Exception as exc:
        raise PublicWindowMeshBlocked("IFC shape unavailable for strict mesh check") from exc
    if (len(points) < 4 or triangles < 4 or not np.isfinite(points).all()
            or not np.isfinite(volume) or volume <= 0):
        raise PublicWindowMeshBlocked("Degenerate or non-finite native IFC shape")
    return points, triangles, volume


def _vertices(points: np.ndarray) -> Counter:
    if not np.isfinite(points).all():
        raise PublicWindowMeshBlocked("Nonfinite world-coordinate geometry")
    return Counter(map(tuple, np.rint(points / TOL).astype(np.int64)))


def _shapes(model):
    out = {}
    for product in model.by_type("IfcProduct"):
        if product.Representation is not None:
            if product.GlobalId in out:
                raise PublicWindowMeshBlocked("Duplicate native IFC product ID")
            out[product.GlobalId] = _verts_and_metrics(product)
    return out


def _same_mesh(a, b) -> bool:
    return (
        a[1] == b[1]
        and abs(a[2] - b[2]) <= TOL
        and _vertices(a[0]) == _vertices(b[0])
    )


def _translated(source, target, translation) -> bool:
    return (
        source[1] == target[1]
        and abs(source[2] - target[2]) <= TOL
        and _vertices(source[0] + np.asarray(translation)) == _vertices(target[0])
    )


def _relation_rows(model) -> dict[str, str]:
    return {root.GlobalId: str(root) for root in model.by_type("IfcRelationship")}


def audit_window_public_mesh(source_ifc: Path, result_ifc: Path,
                             public_instruction: str) -> dict:
    """Check both movable meshes plus regenerated host void and all other meshes.

    Never consumes task target/evaluation fields or accesses ground-truth IFC.
    A valid output is one strict source-bounded *deterministic* reference,
    not a claim that any alternative valid IFC serialization is incorrect.
    """
    original_sha = _sha(source_ifc)
    result_sha = _sha(result_ifc)
    window_guid, opening_guid = _public_guids(public_instruction)
    # Avoid constructing a partial native IFC wrapper from obviously invalid
    # STEP bytes (IfcOpenShell destructor can otherwise emit spurious warnings).
    for path in (source_ifc, result_ifc):
        with path.open("rb") as fh:
            if not fh.read(96).lstrip(b" \r\n\t").startswith(b"ISO-10303-21;"):
                raise PublicWindowMeshBlocked("Invalid IFC STEP header")
    try:
        source = ifcopenshell.open(str(source_ifc))
        result = ifcopenshell.open(str(result_ifc))
    except Exception as exc:
        raise PublicWindowMeshBlocked("IFC source/candidate cannot be opened") from exc
    if source.schema != "IFC4X3" or result.schema != source.schema:
        raise PublicWindowMeshBlocked("Expected matching pinned IFC4X3 input/output")
    if not np.isclose(ifcopenshell.util.unit.calculate_unit_scale(source),
                      1.0, atol=0, rtol=0):
        raise PublicWindowMeshBlocked("Source IFC not in expected world-metre units")
    if not np.isclose(ifcopenshell.util.unit.calculate_unit_scale(result),
                      1.0, atol=0, rtol=0):
        raise PublicWindowMeshBlocked("Output IFC length unit unexpectedly changed")

    host = _host_guid(source, window_guid, opening_guid)
    if _host_guid(result, window_guid, opening_guid) != host:
        raise PublicWindowMeshBlocked("Window/Opening host relationship changed")
    roots_before = {root.GlobalId: root.is_a() for root in source.by_type("IfcRoot")}
    roots_after = {root.GlobalId: root.is_a() for root in result.by_type("IfcRoot")}
    if roots_before != roots_after or _relation_rows(source) != _relation_rows(result):
        raise PublicWindowMeshBlocked("Native IFC root/relationship inventory changed")

    native_before = {entity.id(): str(entity) for entity in source}
    native_after = {entity.id(): str(entity) for entity in result}
    point = _by_guid_class(source, opening_guid, "IfcOpeningElement")
    changed_point_id = point.ObjectPlacement.RelativePlacement.Location.id()
    if (set(native_before) != set(native_after)
        or [i for i in sorted(native_before) if native_before[i] != native_after[i]]
           != [changed_point_id]
        or not source.by_id(changed_point_id).is_a("IfcCartesianPoint")):
        raise PublicWindowMeshBlocked("Unrequested native STEP entities modified")

    original_shapes, candidate_shapes = _shapes(source), _shapes(result)
    if original_shapes.keys() != candidate_shapes.keys():
        raise PublicWindowMeshBlocked("Represented IFC products added or removed")
    if any(guid not in original_shapes for guid in (window_guid, opening_guid, host)):
        raise PublicWindowMeshBlocked("Public Window/Opening/host physical shape missing")

    for guid in (window_guid, opening_guid):
        if not _translated(original_shapes[guid], candidate_shapes[guid],
                           EXPECTED_WORLD_MOVE):
            raise PublicWindowMeshBlocked("Window/Opening world mesh displacement invalid")
    unaffected = 0
    for guid in original_shapes.keys() - {window_guid, opening_guid, host}:
        if not _same_mesh(original_shapes[guid], candidate_shapes[guid]):
            raise PublicWindowMeshBlocked("Unrelated IFC product world geometry changed")
        unaffected += 1

    # Original host wall mesh must lose *exactly* the old opening's eight
    # world-space rim vertices and gain those translated by +Y=1 m.
    # Every other wall vertex, including other existing opening rims, stays.
    before_host = original_shapes[host]
    after_host = candidate_shapes[host]
    opening_rim = _vertices(original_shapes[opening_guid][0])
    shifted_rim = _vertices(original_shapes[opening_guid][0]
                            + np.asarray(EXPECTED_WORLD_MOVE))
    host_vertices = _vertices(before_host[0])
    if any(host_vertices[key] < count for key, count in opening_rim.items()):
        raise PublicWindowMeshBlocked("Original opening not realized in host wall")
    expected_wall = host_vertices.copy()
    expected_wall.subtract(opening_rim)
    if any(v < 0 for v in expected_wall.values()):
        raise PublicWindowMeshBlocked("Host opening rim multiplicity invalid")
    expected_wall += shifted_rim
    if (_vertices(after_host[0]) != expected_wall
        or before_host[1] != after_host[1]
        or abs(before_host[2] - after_host[2]) > TOL
        or not np.allclose(
            np.array([before_host[0].min(axis=0), before_host[0].max(axis=0)]),
            np.array([after_host[0].min(axis=0), after_host[0].max(axis=0)]),
            rtol=0, atol=TOL,
        )):
        raise PublicWindowMeshBlocked("Host wall void was not physically relocated")

    if _sha(source_ifc) != original_sha or _sha(result_ifc) != result_sha:
        raise PublicWindowMeshBlocked("Native IFC bytes changed while checking")
    return {
        "status": "PASS_STRICT_PUBLIC_SOURCE_NATIVE_MESH_POSTCONDITIONS",
        "original_ifc_sha256": original_sha,
        "candidate_ifc_sha256": result_sha,
        "public_instruction_sha256":
            sha256(public_instruction.encode("utf8")).hexdigest(),
        "represented_products_checked": len(original_shapes),
        "unaffected_product_world_meshes_preserved": unaffected,
        "window_and_opening_exact_world_mesh_shift": True,
        "host_void_rim_replaced_by_translated_rim": True,
        "host_outer_world_bounds_volume_and_triangle_count_preserved": True,
        "native_roots_relations_and_other_step_rows_preserved": True,
        "reference_ground_truth_opened": False,
        "independent_of_d_and_i_authoring_logic": True,
        "official_bim_edit_evaluator_executed": False,
        "official_tasks_scored": 0,
        "llm_calls": 0,
        "complete_official_task_oracle_proven": False,
        "G1_G2_G3_unblocked": False,
    }
