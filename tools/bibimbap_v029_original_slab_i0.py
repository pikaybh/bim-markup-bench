"""Independent original PUBLIC test_14 imperative Python/IfcOpenShell I0.

This is developer-written native imperative control, NOT XML compiler or a
real model-generated Python run. Reads the same original public millimetre
IFC4X3 and one GUID provided from the public instruction. Does not import
the declarative XML parser, projection or trusted D0 writer/validator or
original author scorer. The original 56-use point is not mutated.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.util.unit


class IndependentSlabI0Blocked(ValueError):
    pass


def _sha(source:Path)->str:
    return sha256(source.read_bytes()).hexdigest()


def independent_public_slab_i0(source:Path,public_guid:str,output:Path)->dict:
    if (not source.is_file() or source.is_symlink()
        or output.exists() or output.is_symlink()):
        raise IndependentSlabI0Blocked("Refuse absent source or existing output")
    before=_sha(source)
    f_original=ifcopenshell.open(str(source))
    if (f_original.schema!="IFC4X3"
        or abs(ifcopenshell.util.unit.calculate_unit_scale(f_original)-.001)>1e-12):
        raise IndependentSlabI0Blocked("Original source not IFC4X3 millimetres")
    try:
        slab_orig=f_original.by_guid(public_guid)
    except (RuntimeError,ValueError) as exc:
        raise IndependentSlabI0Blocked("Public source slab GUID not found") from exc
    if slab_orig.is_a()!="IfcSlab" or slab_orig.PredefinedType!="FLOOR":
        raise IndependentSlabI0Blocked("Original public target is not floor Slab")
    f=ifcopenshell.util.unit.convert_file_length_units(f_original,"METER")
    slab=f.by_guid(public_guid)
    place=slab.ObjectPlacement
    if (place is None or not place.is_a("IfcLocalPlacement")
        or f.get_total_inverses(place)!=1):
        raise IndependentSlabI0Blocked("Original Slab placement shared")
    rp=place.RelativePlacement
    if rp is None or not rp.is_a("IfcAxis2Placement3D") or f.get_total_inverses(rp)!=1:
        raise IndependentSlabI0Blocked("Original slab relative placement shared")
    original_point=rp.Location
    if (original_point is None or not original_point.is_a("IfcCartesianPoint")
        or len(original_point.Coordinates)!=3
        or any(abs(float(v))>1e-9 for v in original_point.Coordinates)
        or f.get_total_inverses(original_point)!=56):
        raise IndependentSlabI0Blocked("Original source point not the shared zero anchor")
    # Directly changing original_point.Coordinates would move many other
    # products. Independently allocate an exclusive object-position point.
    moved=f.create_entity("IfcCartesianPoint",Coordinates=(
        float(original_point.Coordinates[0]),
        float(original_point.Coordinates[1]),
        float(original_point.Coordinates[2])-.5,
    ))
    rp.Location=moved
    with TemporaryDirectory(prefix="bmb-v029-independent-original-slab-i0-") as td:
        path=Path(td)/"native_metric.ifc"
        f.write(str(path))
        final=ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(path)),"MILLIMETER")
        if (final.schema!="IFC4X3"
            or abs(ifcopenshell.util.unit.calculate_unit_scale(final)-.001)>1e-12):
            raise IndependentSlabI0Blocked("Native final output lost original units")
        output.parent.mkdir(parents=True,exist_ok=True)
        final.write(str(output))
    if _sha(source)!=before:
        raise IndependentSlabI0Blocked("Original public source IFC mutated")
    check=ifcopenshell.open(str(output))
    if (check.by_guid(public_guid).is_a()!="IfcSlab"
        or len(check.by_type("IfcProduct"))!=len(f_original.by_type("IfcProduct"))):
        raise IndependentSlabI0Blocked("Native original product count/class changed")
    return {
        "status":"INDEPENDENT_ORIGINAL_PUBLIC_TEST14_IFCSLAB_Z_MINUS_HALF_METER",
        "original_source_sha256":before,
        "entire_native_original_mm_IFC_sha256":_sha(output),
        "source_IFC4X3_and_mm_preserved":True,
        "native_original_product_count":len(check.by_type("IfcProduct")),
        "real_LLM_calls":0,
    }
