"""Manually authored I0 native Door+Opening deletion on a SOURCE-only task.

This is a trusted deterministic experiment probe, not an LLM output or
official benchmark solution. No XML/compiler import or hidden GT access.
"""
from pathlib import Path

import ifcopenshell
import ifcopenshell.api.root


class IndependentDoorDeleteBlocked(ValueError):
    pass


def native_door_opening_delete(source: Path, destination: Path,
                               door_guid: str, opening_guid: str) -> None:
    if (not source.is_file() or source.is_symlink() or destination.exists()
            or destination.is_symlink() or source.resolve() == destination.resolve()):
        raise IndependentDoorDeleteBlocked("Source/output isolation failed")
    try:
        model = ifcopenshell.open(str(source))
        door = model.by_guid(door_guid)
        opening = model.by_guid(opening_guid)
    except Exception as exc:
        raise IndependentDoorDeleteBlocked("Native public Door/Opening missing") from exc
    if (not door.is_a("IfcDoor") or not opening.is_a("IfcOpeningElement")
            or len(door.FillsVoids) != 1
            or door.FillsVoids[0].RelatingOpeningElement != opening
            or len(opening.VoidsElements) != 1):
        raise IndependentDoorDeleteBlocked("Native Door/Opening relationship ambiguous")
    ifcopenshell.api.root.remove_product(model, product=door)
    ifcopenshell.api.root.remove_product(model, product=opening)
    try:
        model.by_guid(door_guid)
    except RuntimeError:
        pass
    else:
        raise IndependentDoorDeleteBlocked("Door was not removed")
    try:
        model.by_guid(opening_guid)
    except RuntimeError:
        pass
    else:
        raise IndependentDoorDeleteBlocked("Opening was not removed")
    model.write(str(destination))
