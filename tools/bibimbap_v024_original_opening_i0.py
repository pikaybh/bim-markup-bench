"""Independent developer I0 for original PUBLIC IfcOpeningElement + IfcWindow.

No declarative XML compiler or scorer imports. The script uses only the public
original native IFC, resolves exactly one filled source opening, and removes
the filling window then its opening via trusted IfcOpenShell API. This is NOT
LLM-generated code and not the unrestricted model-code execution arm.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.util.unit


class IndependentOpeningI0Blocked(ValueError):
    pass


def original_public_opening_window_i0(
    original: Path, public_opening_guid: str, output: Path,
) -> dict:
    if not original.is_file() or original.is_symlink():
        raise IndependentOpeningI0Blocked("Original public IFC unavailable")
    if output.exists() or output.is_symlink():
        raise IndependentOpeningI0Blocked("I0 result overwrite refused")
    before_sha=sha256(original.read_bytes()).hexdigest()
    source=ifcopenshell.open(str(original))
    if (source.schema!="IFC4X3" or
            abs(ifcopenshell.util.unit.calculate_unit_scale(source)-.001)>1e-12):
        raise IndependentOpeningI0Blocked("I0 original input is not IFC4X3 millimetres")
    try:
        target=source.by_guid(public_opening_guid)
    except RuntimeError as exc:
        raise IndependentOpeningI0Blocked("Public target Opening GUID absent") from exc
    if not target.is_a("IfcOpeningElement") or len(target.HasFillings)!=1:
        raise IndependentOpeningI0Blocked("Public target is not a uniquely filled Opening")
    fill=target.HasFillings[0].RelatedBuildingElement
    if not fill.is_a("IfcWindow"):
        raise IndependentOpeningI0Blocked("Public original Opening filling is not a Window")
    native=ifcopenshell.util.unit.convert_file_length_units(source,"METER")
    opening=native.by_guid(public_opening_guid)
    window=native.by_guid(fill.GlobalId)
    ifcopenshell.api.root.remove_product(native,product=window)
    ifcopenshell.api.root.remove_product(native,product=opening)
    with TemporaryDirectory(prefix="bmb-v024-original-opening-i0-") as temp:
        mid=Path(temp)/"native_m.ifc"
        native.write(str(mid))
        mm=ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(mid)),"MILLIMETER")
        if (mm.schema!="IFC4X3" or
                abs(ifcopenshell.util.unit.calculate_unit_scale(mm)-.001)>1e-12):
            raise IndependentOpeningI0Blocked("Native I0 output lost original schema/units")
        output.parent.mkdir(parents=True,exist_ok=True)
        mm.write(str(output))
    if sha256(original.read_bytes()).hexdigest()!=before_sha:
        raise IndependentOpeningI0Blocked("Original native IFC source altered")
    result=ifcopenshell.open(str(output))
    return {
        "status": "INDEPENDENT_DEVELOPER_NATIVE_OPENING_AND_WINDOW_DELETE",
        "original_source_sha256": before_sha,
        "candidate_sha256": sha256(output.read_bytes()).hexdigest(),
        "public_opening_absent": not any(
            x.GlobalId==public_opening_guid for x in result.by_type("IfcOpeningElement")
        ),
        "original_filling_window_absent": not any(
            x.GlobalId==fill.GlobalId for x in result.by_type("IfcWindow")
        ),
    }
