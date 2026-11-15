"""Independent developer-only I0 for original PUBLIC test_17 Door removal.

No declarative XML source/compiler or author grading is used in this module.
The original PUBLIC Door GUID is the only caller-supplied target; native
IfcOpenShell independently locates its single IfcOpeningElement dependency,
removes Door then Opening, and restores original source millimetres.
This is trusted developer code, not a runnable untrusted model executor.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.util.unit


class OriginalPublicDoorI0Blocked(ValueError):
    pass


def independent_original_public_door_i0(
    original_source: Path, public_door_guid: str, output_path: Path,
) -> dict:
    if (not original_source.is_file() or original_source.is_symlink()
            or output_path.exists() or output_path.is_symlink()):
        raise OriginalPublicDoorI0Blocked(
            "Original IFC source absent or output overwrite attempted")
    src_sha=sha256(original_source.read_bytes()).hexdigest()
    source=ifcopenshell.open(str(original_source))
    if (source.schema != "IFC4X3"
            or abs(ifcopenshell.util.unit.calculate_unit_scale(source)-.001)>1e-12):
        raise OriginalPublicDoorI0Blocked("Original public IFC is not IFC4X3 millimetres")
    try:
        native_door=source.by_guid(public_door_guid)
    except (RuntimeError,ValueError) as exc:
        raise OriginalPublicDoorI0Blocked("PUBLIC Door GUID missing") from exc
    if (not native_door.is_a("IfcDoor") or len(native_door.FillsVoids)!=1
            or not native_door.FillsVoids[0].RelatingOpeningElement.is_a("IfcOpeningElement")):
        raise OriginalPublicDoorI0Blocked("PUBLIC Door does not uniquely fill original native Opening")
    original_opening_guid=native_door.FillsVoids[0].RelatingOpeningElement.GlobalId

    normal=ifcopenshell.util.unit.convert_file_length_units(source,"METER")
    ifcopenshell.api.root.remove_product(
        normal, product=normal.by_guid(public_door_guid))
    ifcopenshell.api.root.remove_product(
        normal, product=normal.by_guid(original_opening_guid))
    with TemporaryDirectory(prefix="bmb-v025-independent-native-door-") as tmp:
        normal_path=Path(tmp)/"candidate_original_m.ifc"
        normal.write(str(normal_path))
        restored=ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(normal_path)),"MILLIMETER")
        if (restored.schema!="IFC4X3"
                or abs(ifcopenshell.util.unit.calculate_unit_scale(restored)-.001)>1e-12):
            raise OriginalPublicDoorI0Blocked("Independent native result schema/units drifted")
        output_path.parent.mkdir(parents=True,exist_ok=True)
        restored.write(str(output_path))
    if sha256(original_source.read_bytes()).hexdigest()!=src_sha:
        raise OriginalPublicDoorI0Blocked("Original native IFC source mutated")
    output=ifcopenshell.open(str(output_path))
    result_guids={p.GlobalId for p in output.by_type("IfcProduct")}
    return {
        "status":"INDEPENDENT_ORIGINAL_PUBLIC_NATIVE_DOOR_AND_OPENING_DELETED",
        "original_source_sha256":src_sha,
        "native_result_sha256":sha256(output_path.read_bytes()).hexdigest(),
        "original_public_door_absent":public_door_guid not in result_guids,
        "native_original_filled_opening_absent":original_opening_guid not in result_guids,
    }
