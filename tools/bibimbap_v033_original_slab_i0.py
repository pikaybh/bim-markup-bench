"""Independently authored native original-public BIBIMBAP test_02 Slab I0.

Use only original PUBLIC IFC and task: horizontal rectangular slab 10x5m,
thickness .2m, ground face centered at (-30,0). Source-side zero-elevation
L1 is a predeclared inference, not an author-test hint. No D0/XML/compiler/
grader module is imported here. Research developer control; no model run.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.util.unit
import numpy as np

SOURCE_SHA = "9ef1235e49d5b0359c1d44fd95a7afad7755149362109ca8b875d0427dc487ca"
SPEC_METRES = (-35.0, -2.5, 0.0, 10.0, 5.0, 0.2)
EXPECTED_BBOX_METRES = (-35.0, -2.5, 0.0, -25.0, 2.5, 0.2)
STOREY_NAME = "L1"


class NativePublicSlabI0Blocked(ValueError):
    pass


def _hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def create_independent_original_test02_i0(original_mm: Path, output_mm: Path) -> dict:
    """Physically create the specified slab in a fresh original-native IFC clone."""
    original_mm, output_mm = Path(original_mm), Path(output_mm)
    if (not original_mm.is_file() or original_mm.is_symlink()
            or output_mm.exists() or output_mm.is_symlink()
            or output_mm.resolve() == original_mm.resolve()):
        raise NativePublicSlabI0Blocked("Source must be regular and output fresh")
    before = _hash(original_mm)
    if before != SOURCE_SHA:
        raise NativePublicSlabI0Blocked("Original public source IFC SHA mismatch")
    original = ifcopenshell.open(str(original_mm))
    if (original.schema != "IFC4X3" or
            abs(ifcopenshell.util.unit.calculate_unit_scale(original)-0.001)>1e-12):
        raise NativePublicSlabI0Blocked("Original IFC4X3 millimetre schema/unit drift")
    model = ifcopenshell.util.unit.convert_file_length_units(original, "METER")
    if abs(ifcopenshell.util.unit.calculate_unit_scale(model)-1.0)>1e-12:
        raise NativePublicSlabI0Blocked("Unable to normalize IFC length units")
    storeys = [s for s in model.by_type("IfcBuildingStorey")
               if s.Name==STOREY_NAME and s.Elevation is not None
               and abs(float(s.Elevation))<1e-9]
    if len(storeys)!=1:
        raise NativePublicSlabI0Blocked("Unique existing L1 ground storey absent")
    contexts=[x for x in model.by_type("IfcGeometricRepresentationSubContext")
              if x.ContextIdentifier=="Body" and x.TargetView=="MODEL_VIEW"]
    if len(contexts)!=1:
        raise NativePublicSlabI0Blocked("Unique existing native Body context absent")
    old_root={x.GlobalId for x in model.by_type("IfcRoot")}
    slab = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcSlab", name="Independent public Python I0 rectangular slab")
    if slab.GlobalId in old_root:
        raise NativePublicSlabI0Blocked("New Slab collides with existing root GlobalId")
    slab.PredefinedType = "FLOOR"
    x, y, z, width, depth, thickness = SPEC_METRES
    profile = model.createIfcRectangleProfileDef("AREA", None, None, width, depth)
    rep = ifcopenshell.api.geometry.add_profile_representation(
        model, context=contexts[0], profile=profile, depth=thickness)
    ifcopenshell.api.geometry.assign_representation(
        model, product=slab, representation=rep)
    transform = np.eye(4, dtype="float64")
    transform[:3,3]=[x+width/2,y+depth/2,z]
    ifcopenshell.api.geometry.edit_object_placement(
        model, product=slab, matrix=transform)
    ifcopenshell.api.spatial.assign_container(
        model, products=[slab], relating_structure=storeys[0])
    converted = ifcopenshell.util.unit.convert_file_length_units(model, "MILLIMETER")
    if (converted.schema!="IFC4X3" or
            abs(ifcopenshell.util.unit.calculate_unit_scale(converted)-0.001)>1e-12):
        raise NativePublicSlabI0Blocked("Output original native millimetre units lost")
    with TemporaryDirectory(prefix="bmb-v033-i0-") as td:
        stage=Path(td)/"native_original_mm.ifc"
        converted.write(str(stage))
        reopened = ifcopenshell.open(str(stage))
        if (sum(x.GlobalId==slab.GlobalId for x in reopened.by_type("IfcSlab"))!=1
                or _hash(original_mm)!=before):
            raise NativePublicSlabI0Blocked("Independent physical Slab missing or source changed")
        output_mm.write_bytes(stage.read_bytes())
    if _hash(original_mm)!=before:
        output_mm.unlink(missing_ok=True)
        raise NativePublicSlabI0Blocked("Original public IFC was changed")
    return {
        "status": "ORIGINAL_PUBLIC_TEST02_INDEPENDENT_PYTHON_NATIVE_IFCSLAB_CREATED",
        "original_source_sha256":before,
        "new_native_slab_guid":slab.GlobalId,
        "source_L1_native_guid":storeys[0].GlobalId,
        "original_public_fixed_xyz_width_depth_thickness_m":list(SPEC_METRES),
        "candidate_original_mm_ifc_sha256":_hash(output_mm),
        "original_and_output_IFC4X3_millimetres":True,
        "no_D0_XML_grader_or_hidden_GT_import":True,
        "developer_authored_not_LLM_output":True,
    }
