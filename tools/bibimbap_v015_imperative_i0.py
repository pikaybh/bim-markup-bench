"""Independent imperative developer I0 for two *public* hosted Window tasks.

The authoring path sees only the public natural-language task and the original
IFC4X3 source. It NEVER imports D0's XML writer/projector, frozen D0 evidence,
the original author scorer or target GUIDs. This is a nonblinded, locally
authored source-only Python/IfcOpenShell comparison, NOT an LLM result.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import os
import re
import tempfile

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

SUPPORTED = frozenset({"geometry_test_18", "geometry_test_19"})
TARGETS = re.compile(r'GlobalId\s*=\s*"([0-9A-Za-z_$]{22})"')
EPS = 1e-5
REL_MEMBERS = {
    "IfcRelDefinesByType": "RelatedObjects",
    "IfcRelAssociatesClassification": "RelatedObjects",
    "IfcRelContainedInSpatialStructure": "RelatedElements",
}
SOURCE_INVERSE = Counter({
    "IfcRelFillsElement": 1,
    "IfcRelDefinesByProperties": 2,
    "IfcRelAssociatesMaterial": 1,
    "IfcRelAssociatesClassification": 1,
    "IfcRelDefinesByType": 1,
    "IfcRelContainedInSpatialStructure": 1,
})


class ImperativeI0Blocked(ValueError):
    pass


@dataclass(frozen=True)
class ImperativeI0Evidence:
    source_sha256: str
    result_sha256: str
    public_task_id: str
    public_question_sha256: str
    selected_original_window_guids: tuple[str, ...]
    original_source_schema: str
    original_source_window_count: int
    original_file_unchanged: bool
    backend: str = "Python/IfcOpenShell imperative root.remove_product"
    developer_fixed_not_model_trial: bool = True


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _axis(wall) -> tuple[np.ndarray, np.ndarray]:
    """Read original native IFC Curve2D (world) without authoring XML."""
    if wall is None or not wall.is_a("IfcWall") or wall.Representation is None:
        raise ImperativeI0Blocked("Native IFC host Wall has no physical source axis")
    curves = [
        item for rep in wall.Representation.Representations
        if rep.RepresentationType == "Curve2D"
        for item in rep.Items
        if item.is_a("IfcPolyline") and len(item.Points) == 2
    ]
    if len(curves) != 1:
        raise ImperativeI0Blocked("Expected one real source native Wall axis")
    matrix = np.asarray(
        ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement),
        dtype=float,
    )
    xy = [np.asarray((*map(float, point.Coordinates), 0., 1.), dtype=float)
          for point in curves[0].Points]
    if any(vec.shape != (4,) for vec in xy):
        raise ImperativeI0Blocked("Native Curve2D malformed")
    start = (matrix @ xy[0])[:3]
    end = (matrix @ xy[1])[:3]
    if not np.all(np.isfinite([start, end])) or np.linalg.norm(end - start) < 0.5:
        raise ImperativeI0Blocked("Native Wall axis degenerate")
    return start, end


def _window_inventory(model) -> list[dict]:
    rows = []
    for window in model.by_type("IfcWindow"):
        fills = list(window.FillsVoids)
        if len(fills) != 1 or fills[0].RelatedBuildingElement != window:
            raise ImperativeI0Blocked("Original Window has ambiguous fill")
        opening = fills[0].RelatingOpeningElement
        if opening is None or not opening.is_a("IfcOpeningElement"):
            raise ImperativeI0Blocked("Original Window's Opening missing")
        voids = list(opening.VoidsElements)
        if len(voids) != 1 or len(opening.HasFillings) != 1:
            raise ImperativeI0Blocked("Original source Window/Opening host not unique")
        wall = voids[0].RelatingBuildingElement
        a, b = _axis(wall)
        direction = (b - a) / np.linalg.norm(b - a)
        midpoint = (a + b) / 2
        matrix = np.asarray(
            ifcopenshell.util.placement.get_local_placement(opening.ObjectPlacement),
            dtype=float,
        )
        origin = matrix[:3, 3]
        width = float(window.OverallWidth or 0.)
        if width <= 0 or width > np.linalg.norm(b - a) + 1:
            raise ImperativeI0Blocked("Original native Window width unsupported")
        rows.append({
            "guid": window.GlobalId, "host": wall.GlobalId,
            "a": a, "b": b, "center": midpoint, "dir": direction,
            "origin": origin, "width": width,
        })
    return sorted(rows, key=lambda row: row["guid"])


def select_original_windows(task_id: str, public_question: str, model) -> tuple[str, ...]:
    """Self-contained imperative-public-task interpretation (no D0 imports)."""
    if task_id not in SUPPORTED:
        raise ImperativeI0Blocked("Only the two frozen original public tasks allowed")
    rows = _window_inventory(model)
    if task_id == "geometry_test_18":
        if ("west" not in public_question.lower()
                or "+X is east" not in public_question
                or "+Y is north" not in public_question):
            raise ImperativeI0Blocked("Public west-wall task text drift")
        # Geographic west in the publicly defined IFC world frame is min X.
        hosts = {}
        for row in rows:
            direction = row["dir"]
            if abs(direction[0]) < EPS and abs(abs(direction[1]) - 1.) < EPS:
                hosts[row["host"]] = row["center"][0]
        if not hosts:
            raise ImperativeI0Blocked("No north/south-oriented source host Wall")
        xwest = min(hosts.values())
        near_west = {k for k, x in hosts.items() if abs(x - xwest) < EPS}
        chosen = tuple(sorted(row["guid"] for row in rows if row["host"] in near_west))
        if len(chosen) != 2 or len(near_west) != 1:
            raise ImperativeI0Blocked("Public source west hosted Windows ambiguous")
        return chosen

    identifiers = TARGETS.findall(public_question)
    if len(identifiers) != 1 or "opposite" not in public_question.lower():
        raise ImperativeI0Blocked("Public source opposite-wall task drift")
    try:
        reference = model.by_guid(identifiers[0])
    except RuntimeError as exc:
        raise ImperativeI0Blocked("Publicly named reference Wall missing") from exc
    a, b = _axis(reference)
    delta = b - a
    length = np.linalg.norm(delta)
    direction = delta / length
    midpoint = (a + b) / 2
    transverse = np.array([-direction[1], direction[0], 0.])
    selected = []
    for row in rows:
        if abs(abs(np.dot(row["dir"], direction)) - 1.) > EPS:
            continue
        if abs(np.dot(row["center"] - midpoint, transverse)) <= 1.:
            continue
        left = float(np.dot(row["origin"] - a, direction))
        right = float(np.dot(row["origin"] + row["dir"] * row["width"] - a, direction))
        overlap = max(0., min(max(left, right), length) - max(min(left, right), 0.))
        if overlap + EPS >= row["width"] / 2.:
            selected.append(row)
    if len(selected) != 2 or len({row["host"] for row in selected}) != 1:
        raise ImperativeI0Blocked("Native opposite Wall Window source selection ambiguous")
    return tuple(sorted(row["guid"] for row in selected))


def _safe_source_relationships(model, guids: tuple[str, ...]):
    """Self-contained original IFC preflight, no D0 or evaluator dependency."""
    previous = {}
    selected = set(guids)
    for guid in guids:
        window = model.by_guid(guid)
        if not window.is_a("IfcWindow"):
            raise ImperativeI0Blocked("Selected IFC entity not an original Window")
        inverses = list(model.get_inverse(window))
        if Counter(rel.is_a() for rel in inverses) != SOURCE_INVERSE:
            raise ImperativeI0Blocked("Unsupported original source Window inverse graph")
        for rel in inverses:
            typ = rel.is_a()
            if typ in REL_MEMBERS:
                member_attr = REL_MEMBERS[typ]
                members = tuple(x.GlobalId for x in getattr(rel, member_attr))
                if guid not in members:
                    raise ImperativeI0Blocked("Original native shared relation lacks target")
                previous[rel.GlobalId] = (
                    typ, member_attr, members,
                    rel.OwnerHistory.id() if rel.OwnerHistory else None,
                )
            elif typ == "IfcRelDefinesByProperties":
                if len(rel.RelatedObjects) != 1 or rel.RelatedObjects[0] != window:
                    raise ImperativeI0Blocked("Unsafe original shared PropertySet")
                prop = rel.RelatingPropertyDefinition
                if not prop.is_a("IfcPropertySet") or set(model.get_inverse(prop)) != {rel}:
                    raise ImperativeI0Blocked("Original source property ownership ambiguous")
            elif typ == "IfcRelAssociatesMaterial":
                if len(rel.RelatedObjects) != 1 or rel.RelatedObjects[0] != window:
                    raise ImperativeI0Blocked("Unsafe shared native material association")
            elif typ != "IfcRelFillsElement":
                raise ImperativeI0Blocked("Unexpected source IFC inverse relation")
    for _, _, members, _ in previous.values():
        if not set(members) - selected:
            raise ImperativeI0Blocked("Cannot empty original shared source relation")
    return previous


def compile_imperative_i0(source: Path, public_task_id: str,
                          public_question: str, destination: Path) -> ImperativeI0Evidence:
    """Actually execute Python/IfcOpenShell IFC edits on a fresh file model."""
    if not source.is_file() or source.is_symlink() or destination.exists()        or destination.is_symlink() or source.resolve() == destination.resolve()        or not destination.parent.is_dir():
        raise ImperativeI0Blocked("Immutable source, distinct unused output path required")
    source_sha = _sha(source)
    model = ifcopenshell.open(str(source))
    if model.schema != "IFC4X3" or abs(
        ifcopenshell.util.unit.calculate_unit_scale(model) - 1.0
    ) > 1e-8:
        raise ImperativeI0Blocked("Source IFC4X3 must be normalized to metres")
    count = len(model.by_type("IfcWindow"))
    guids = select_original_windows(public_task_id, public_question, model)
    original_relations = _safe_source_relationships(model, guids)
    original_step_ids = {item.id() for item in model}
    for guid in guids:
        ifcopenshell.api.root.remove_product(model, product=model.by_guid(guid))
    # The public standard IFC API may touch OwnerHistory and reorder shared
    # membership. Reconstruct only already existing original source members.
    generated_histories = {}
    for rel_guid, (typ, attr, members, history_id) in original_relations.items():
        relation = model.by_guid(rel_guid)
        if relation.is_a() != typ:
            raise ImperativeI0Blocked("Source shared relationship class changed")
        desired = tuple(model.by_guid(g) for g in members if g not in guids)
        actual = getattr(relation, attr)
        if set(x.GlobalId for x in actual) != set(x.GlobalId for x in desired):
            raise ImperativeI0Blocked("Native API altered unexpected shared members")
        setattr(relation, attr, desired)
        history = relation.OwnerHistory
        current_id = history.id() if history else None
        if current_id != history_id:
            relation.OwnerHistory = model.by_id(history_id) if history_id else None
            if history is not None:
                generated_histories[current_id] = history
    for h in generated_histories.values():
        if model.get_inverse(h):
            raise ImperativeI0Blocked("Unexpected shared generated OwnerHistory")
        model.remove(h)
    if {item.id() for item in model} - original_step_ids:
        raise ImperativeI0Blocked("New unexpected IFC STEP entity after I0")
    if _sha(source) != source_sha:
        raise ImperativeI0Blocked("Original IFC mutated during I0")
    with tempfile.TemporaryDirectory(prefix=".i0-original-window-", dir=destination.parent) as d:
        staging = Path(d) / "imperative_i0.ifc"
        model.write(str(staging))
        if _sha(source) != source_sha or destination.exists():
            raise ImperativeI0Blocked("Original IFC/destination changed before I0 commit")
        os.rename(staging, destination)
    result_sha = _sha(destination)
    if _sha(source) != source_sha:
        raise ImperativeI0Blocked("Original IFC mutated after I0 commit")
    return ImperativeI0Evidence(
        source_sha, result_sha, public_task_id,
        sha256(public_question.encode("utf8")).hexdigest(),
        guids, model.schema, count, True,
    )
