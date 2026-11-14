"""Independent original PUBLIC Column tasks test_15/test_16 Python I0.

This is a bounded, non-LLM developer-written imperative IfcOpenShell control.
Only original public task text and original IFC4X3 source may drive targeting.
Do not import the declarative D0 projector/compiler, historic D0 report,
original author scorer or hidden ground truth into this file.
"""
from __future__ import annotations

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


PUBLIC_GUID = re.compile(r"\bid\s+([0-9A-Za-z_$]{22})\b", re.I)


class ColumnI0Blocked(ValueError):
    pass


@dataclass(frozen=True)
class ColumnI0Result:
    task_id: str
    original_public_question_sha256: str
    source_sha256: str
    candidate_native_sha256: str
    original_target_guid_from_public_question: str
    operation: str
    original_source_unchanged: bool


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _parse_public_instruction(task: str, question: str):
    identifiers = PUBLIC_GUID.findall(question)
    if len(identifiers) != 1:
        raise ColumnI0Blocked("Expected exactly one original PUBLIC Column GlobalId")
    if task == "test_15":
        if not (question.startswith("Move the column with id ")
                and "by -3 meters in the direction of y" in question):
            raise ColumnI0Blocked("Original public Column move semantics drift")
        return "MOVE_COLUMN_Y_MINUS_3M", identifiers[0]
    if task == "test_16":
        if not question.startswith("Delete the column with the id "):
            raise ColumnI0Blocked("Original public Column deletion semantics drift")
        return "DELETE_COLUMN", identifiers[0]
    raise ColumnI0Blocked("Original public task not in frozen Column parity slice")


def _move_original_column(source, column):
    placement = column.ObjectPlacement
    if placement is None or not placement.is_a("IfcLocalPlacement"):
        raise ColumnI0Blocked("Original Column has no safe local placement")
    frame = placement.RelativePlacement
    if frame is None or not frame.is_a("IfcAxis2Placement3D"):
        raise ColumnI0Blocked("Original Column native axis placement is unsupported")
    point = frame.Location
    if point is None or not point.is_a("IfcCartesianPoint"):
        raise ColumnI0Blocked("Original source point coordinates absent")
    if (len(source.get_inverse(point)) != 1
        or len(source.get_inverse(frame)) != 1
        or any(x.id() != column.id() for x in source.get_inverse(placement))):
        raise ColumnI0Blocked("Original Column placement is shared")
    if placement.PlacementRelTo is not None:
        parent = np.asarray(
            ifcopenshell.util.placement.get_local_placement(placement.PlacementRelTo),
            dtype=float,
        )
        if not np.allclose(parent[:3, :3], np.eye(3), rtol=0, atol=1e-8):
            raise ColumnI0Blocked("Original Column parent frame is not world-parallel")
    coords = tuple(float(x) for x in point.Coordinates)
    if len(coords) != 3 or not np.all(np.isfinite(coords)):
        raise ColumnI0Blocked("Original CartesianPoint not a finite 3D position")
    point.Coordinates = (coords[0], coords[1] - 3.0, coords[2])


def _delete_original_column(source, column):
    permitted = {
        "IfcRelContainedInSpatialStructure",
        "IfcRelDefinesByType",
        "IfcRelDefinesByProperties",
    }
    inverse = list(source.get_inverse(column))
    if not inverse or {rel.is_a() for rel in inverse} - permitted:
        raise ColumnI0Blocked("Original Column has unknown native dependent relationship")
    for relation in inverse:
        members = (relation.RelatedElements if relation.is_a("IfcRelContainedInSpatialStructure")
                   else relation.RelatedObjects)
        if column not in members:
            raise ColumnI0Blocked("Original Column missing from native relation")
        if relation.is_a("IfcRelDefinesByProperties"):
            if len(members) != 1:
                raise ColumnI0Blocked("Original source PropertySet relation is shared")
            prop = relation.RelatingPropertyDefinition
            if not prop.is_a("IfcPropertySet") or len(source.get_inverse(prop)) != 1:
                raise ColumnI0Blocked("Original source PropertySet is shared")
    ifcopenshell.api.root.remove_product(source, product=column)


def run_imperative_column_i0(source: Path, task_id: str,
                             public_question: str, destination: Path) -> ColumnI0Result:
    """Source-only I0. Candidate validation is deliberately external to I0."""
    if (not source.is_file() or source.is_symlink()
            or destination.exists() or destination.is_symlink()
            or source.resolve() == destination.resolve()
            or not destination.parent.is_dir()):
        raise ColumnI0Blocked("Distinct immutable original source and unused output required")
    operation, guid = _parse_public_instruction(task_id, public_question)
    source_sha = _sha(source)
    f = ifcopenshell.open(str(source))
    if f.schema != "IFC4X3" or abs(ifcopenshell.util.unit.calculate_unit_scale(f) - 1) > 1e-8:
        raise ColumnI0Blocked("Requires real original IFC4X3 source normalized to metres")
    try:
        col = f.by_guid(guid)
    except RuntimeError as exc:
        raise ColumnI0Blocked("Publicly named native Column absent") from exc
    if not col.is_a("IfcColumn"):
        raise ColumnI0Blocked("Public named IFC entity is not a Column")

    if operation == "MOVE_COLUMN_Y_MINUS_3M":
        _move_original_column(f, col)
    else:
        _delete_original_column(f, col)

    if _sha(source) != source_sha:
        raise ColumnI0Blocked("Input native IFC unexpectedly mutated")
    with tempfile.TemporaryDirectory(prefix="bmb-v016-i0-", dir=destination.parent) as dirname:
        tmp = Path(dirname) / "new_original_column_i0.ifc"
        f.write(str(tmp))
        if destination.exists() or _sha(source) != source_sha:
            raise ColumnI0Blocked("Original source/output changed before commit")
        os.rename(tmp, destination)
    if _sha(source) != source_sha:
        raise ColumnI0Blocked("Original source changed after candidate write")
    return ColumnI0Result(
        task_id=task_id, original_public_question_sha256=sha256(
            public_question.encode("utf8")
        ).hexdigest(), source_sha256=source_sha,
        candidate_native_sha256=_sha(destination),
        original_target_guid_from_public_question=guid,
        operation=operation, original_source_unchanged=True,
    )
