"""Independent developer-only imperative original IFC4X3 IfcSpace deletion.

No declarative XML parser/compiler, source edits, original scorer import or
LLM execution. The independent I0 arm uses existing native IfcOpenShell API
to remove only the public question's named IfcSpace, with identical
unit-conversion envelope to the D0 experiment. This permits *output bytes*
to be compared, not equality of model source information or reasoning tools.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.util.unit


class OriginalDeveloperI0Blocked(ValueError):
    pass


def independent_public_space_delete_i0(
    original_public_ifc: Path, public_guid: str, target_output_ifc: Path,
) -> dict:
    if (not original_public_ifc.is_file() or original_public_ifc.is_symlink()
            or target_output_ifc.exists() or target_output_ifc.is_symlink()):
        raise OriginalDeveloperI0Blocked("Original input absent or output already exists")
    original_sha = sha256(original_public_ifc.read_bytes()).hexdigest()
    original = ifcopenshell.open(str(original_public_ifc))
    if (original.schema != "IFC4X3" or
            abs(ifcopenshell.util.unit.calculate_unit_scale(original) - .001) > 1e-12):
        raise OriginalDeveloperI0Blocked("Original I0 input is not IFC4X3 millimetres")
    try:
        public_room = original.by_guid(public_guid)
    except (RuntimeError, ValueError) as exc:
        raise OriginalDeveloperI0Blocked("Public named IFC Space does not exist") from exc
    if not public_room.is_a("IfcSpace"):
        raise OriginalDeveloperI0Blocked("Public target is not an IfcSpace")

    # Unit normalization is common execution setup for I0 and D0; no XML
    # source read/semantic graph/commands/GT are invoked in this function.
    metric = ifcopenshell.util.unit.convert_file_length_units(original, "METER")
    metric_target = metric.by_guid(public_guid)
    ifcopenshell.api.root.remove_product(metric, product=metric_target)
    with TemporaryDirectory(prefix="bmb-v023-native-i0-original-") as root:
        candidate_metric = Path(root) / "imperative_candidate_m.ifc"
        metric.write(str(candidate_metric))
        millimetre = ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(candidate_metric)), "MILLIMETER")
        if (millimetre.schema != "IFC4X3" or
                abs(ifcopenshell.util.unit.calculate_unit_scale(millimetre) - .001) > 1e-12):
            raise OriginalDeveloperI0Blocked("Native I0 output schema or units drifted")
        target_output_ifc.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive refusal to overwrite old results.
        millimetre.write(str(target_output_ifc))
    if sha256(original_public_ifc.read_bytes()).hexdigest() != original_sha:
        raise OriginalDeveloperI0Blocked("Original source changed during independent I0")
    return {
        "status": "INDEPENDENT_DEVELOPER_NATIVE_IFC_SPACE_DELETION_CREATED",
        "original_source_sha256": original_sha,
        "imperative_candidate_sha256": sha256(target_output_ifc.read_bytes()).hexdigest(),
        "output_contains_target_space": any(
            x.GlobalId == public_guid
            for x in ifcopenshell.open(str(target_output_ifc)).by_type("IfcSpace")
        ),
    }
