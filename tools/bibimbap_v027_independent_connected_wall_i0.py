"""Independent developer-only native Python baseline for original-public test_19.

No XML parsing, XML compiler, child-worker, source-graph planner, or scoring
imports are used. This independent imperative reference has a separate
IfcOpenShell implementation and the same native source→metres→millimetres
serialization envelope as the declarative D0. This is NOT LLM-generated code
or permission for arbitrary model Python execution.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.api.pset
import ifcopenshell.util.element
import ifcopenshell.util.unit


class NativeOriginalWallI0Blocked(ValueError):
    pass


def independent_original_connected_wall_i0(
    original_public_mm:Path,public_wall_guid:str,output_mm:Path,
) -> dict:
    if (not original_public_mm.is_file() or original_public_mm.is_symlink()
            or output_mm.exists() or output_mm.is_symlink()):
        raise NativeOriginalWallI0Blocked("Invalid public source or I0 output overwrite")
    source_hash=sha256(original_public_mm.read_bytes()).hexdigest()
    original=ifcopenshell.open(str(original_public_mm))
    if (original.schema!="IFC4X3"
            or abs(ifcopenshell.util.unit.calculate_unit_scale(original)-.001)>1e-12):
        raise NativeOriginalWallI0Blocked("Original public native IFC is not IFC4X3 millimetres")
    try:
        wall=original.by_guid(public_wall_guid)
    except (RuntimeError,ValueError) as exc:
        raise NativeOriginalWallI0Blocked("Public native Wall GUID absent") from exc
    if (not wall.is_a("IfcWall") or wall.HasOpenings
            or len([x for x in original.get_inverse(wall)
                    if x.is_a("IfcRelConnectsPathElements")])!=2):
        raise NativeOriginalWallI0Blocked("Public Wall is not the required connected source")
    metric=ifcopenshell.util.unit.convert_file_length_units(original,"METER")
    target=metric.by_guid(public_wall_guid)
    # Independently derive exclusive owned relations directly from the IFC.
    linked=[x for x in metric.get_inverse(target)
            if x.is_a("IfcRelConnectsPathElements")]
    definitions=[x for x in metric.get_inverse(target)
                 if x.is_a("IfcRelDefinesByProperties")]
    if (len(linked)!=2 or len(definitions)!=3
            or len(target.Representation.Representations)!=2):
        raise NativeOriginalWallI0Blocked("Independent original native dependency mismatch")
    for relation in linked:
        if relation.RelatedElement!=target:
            raise NativeOriginalWallI0Blocked("Source wall path role not related")
        metric.remove(relation)
    for relation in definitions:
        pset=relation.RelatingPropertyDefinition
        if (tuple(relation.RelatedObjects)!=(target,)
                or tuple(metric.get_inverse(pset))!=(relation,)):
            raise NativeOriginalWallI0Blocked("Unexpected original shared property definition")
        ifcopenshell.api.pset.remove_pset(metric,product=target,pset=pset)

    physical=list(target.Representation.Representations)
    associated=[
        layer for layer in metric.by_type("IfcPresentationLayerAssignment")
        if any(item in layer.AssignedItems for item in physical)
    ]
    if len(associated)!=1:
        raise NativeOriginalWallI0Blocked("Original source physical layer ambiguous")
    associated[0].AssignedItems=tuple(
        obj for obj in associated[0].AssignedItems if obj not in physical)
    part=target.Representation
    target.Representation=None
    ifcopenshell.util.element.remove_deep2(metric,part)
    place=target.ObjectPlacement
    target.ObjectPlacement=None
    ifcopenshell.util.element.remove_deep2(metric,place)
    metric.remove(target)

    with TemporaryDirectory(prefix="bmb-v027-independent-I0-mm-") as temp:
        native_metric=Path(temp)/"independent_m.ifc"
        metric.write(str(native_metric))
        restored=ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(native_metric)),"MILLIMETER")
        if restored.schema!="IFC4X3":
            raise NativeOriginalWallI0Blocked("I0 result lost original schema")
        output_mm.parent.mkdir(parents=True,exist_ok=True)
        restored.write(str(output_mm))

    if sha256(original_public_mm.read_bytes()).hexdigest()!=source_hash:
        raise NativeOriginalWallI0Blocked("Original input IFC modified during I0")
    result=ifcopenshell.open(str(output_mm))
    products={p.GlobalId:p.is_a() for p in result.by_type("IfcProduct")}
    return {
        "status":"INDEPENDENT_DEVELOPER_ORIGINAL_CONNECTED_WALL_I0_NATIVE_OUTPUT",
        "source_sha256":source_hash,
        "candidate_sha256":sha256(output_mm.read_bytes()).hexdigest(),
        "original_public_Wall_absent":public_wall_guid not in products,
        "remaining_original_IfcProduct_count":len(products),
    }
