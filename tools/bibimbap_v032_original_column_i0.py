"""Independent imperative original-source IfcColumn Create I0 for BIBIMBAP test_04.

This module MUST NOT import declarative XML, binder, D0 compiler, or author
grader. Public question: Column at (12m,8m), height 3m. Unspecified width and
depth fixed prospectively at 0.3m; source L1 storey at elevation zero.
Research-only deterministic DEVELOPER control, not model-generated code.
"""
from __future__ import annotations

from pathlib import Path

import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.util.unit
import numpy as np

SOURCE_SHA = "9ef1235e49d5b0359c1d44fd95a7afad7755149362109ca8b875d0427dc487ca"
SPEC_METRES = (12.0, 8.0, 0.0, 0.3, 0.3, 3.0)
L1_NAME = "L1"


class IndependentColumnI0Error(ValueError):
    pass


def _hash(path: Path) -> str:
    from hashlib import sha256
    return sha256(path.read_bytes()).hexdigest()


def create_independent_public_column_i0(original_mm: Path, result_mm: Path) -> dict:
    """Native IFC editing solely from the original IFC file and fixed public spec."""
    original_mm = Path(original_mm)
    result_mm = Path(result_mm)
    if (not original_mm.is_file() or original_mm.is_symlink()
            or result_mm.exists() or result_mm.resolve() == original_mm.resolve()):
        raise IndependentColumnI0Error("Original source must be immutable and output fresh")
    source_hash = _hash(original_mm)
    if source_hash != SOURCE_SHA:
        raise IndependentColumnI0Error("Pinned original public IFC hash mismatch")
    raw = ifcopenshell.open(str(original_mm))
    if (raw.schema != "IFC4X3"
            or abs(ifcopenshell.util.unit.calculate_unit_scale(raw) - .001) > 1e-12):
        raise IndependentColumnI0Error("Pinned original native IFC schema/unit mismatch")
    metric = ifcopenshell.util.unit.convert_file_length_units(raw, "METER")
    if abs(ifcopenshell.util.unit.calculate_unit_scale(metric) - 1.0) > 1e-12:
        raise IndependentColumnI0Error("Metric working IFC units not established")
    storeys = [s for s in metric.by_type("IfcBuildingStorey")
               if s.Name == L1_NAME and s.Elevation is not None
               and abs(float(s.Elevation)) < 1e-9]
    if len(storeys) != 1:
        raise IndependentColumnI0Error("Original L1 zero-elevation storey ambiguous")
    bodies = [r for r in metric.by_type("IfcGeometricRepresentationSubContext")
              if r.ContextIdentifier == "Body" and r.TargetView == "MODEL_VIEW"]
    if len(bodies) != 1:
        raise IndependentColumnI0Error("Original Body MODEL_VIEW context ambiguous")
    old_root_guids = {e.GlobalId for e in metric.by_type("IfcRoot")}
    x, y, z, width, depth, height = SPEC_METRES
    column = ifcopenshell.api.root.create_entity(
        metric, ifc_class="IfcColumn", name="Independent original-public Python I0 Column")
    if column.GlobalId in old_root_guids:
        raise IndependentColumnI0Error("Native root GUID collision")
    profile = metric.createIfcRectangleProfileDef("AREA", None, None, width, depth)
    shape = ifcopenshell.api.geometry.add_profile_representation(
        metric, context=bodies[0], profile=profile, depth=height)
    ifcopenshell.api.geometry.assign_representation(
        metric, product=column, representation=shape)
    transform = np.eye(4, dtype="float64")
    transform[0, 3], transform[1, 3], transform[2, 3] = (
        x + width / 2, y + depth / 2, z)
    ifcopenshell.api.geometry.edit_object_placement(
        metric, product=column, matrix=transform)
    ifcopenshell.api.spatial.assign_container(
        metric, products=[column], relating_structure=storeys[0])
    native_mm = ifcopenshell.util.unit.convert_file_length_units(metric, "MILLIMETER")
    if (native_mm.schema != "IFC4X3"
            or abs(ifcopenshell.util.unit.calculate_unit_scale(native_mm) - .001) > 1e-12):
        raise IndependentColumnI0Error("Native original millimetre IFC conversion failed")
    from tempfile import TemporaryDirectory
    with TemporaryDirectory(prefix="bmb-v032-i0-") as td:
        staging = Path(td) / "candidate_mm.ifc"
        native_mm.write(str(staging))
        if _hash(original_mm) != source_hash:
            raise IndependentColumnI0Error("Original public source changed during I0")
        # Reopen the complete STEP output before copying it to final unique output.
        materialized = ifcopenshell.open(str(staging))
        if not any(e.GlobalId == column.GlobalId for e in materialized.by_type("IfcColumn")):
            raise IndependentColumnI0Error("Created IfcColumn missing from saved native IFC")
        result_mm.write_bytes(staging.read_bytes())
    if _hash(original_mm) != source_hash:
        result_mm.unlink(missing_ok=True)
        raise IndependentColumnI0Error("Original source altered during independent I0")
    return {
        "status": "INDEPENDENT_PYTHON_IFCOPENSHELL_ORIGINAL_TEST04_NATIVE_CREATE",
        "native_original_source_sha256": source_hash,
        "new_native_IfcColumn_globalid": column.GlobalId,
        "original_existing_storey_globalid": storeys[0].GlobalId,
        "predeclared_fixed_x_y_z_width_depth_height_m": list(SPEC_METRES),
        "candidate_native_IFC_SHA256": _hash(result_mm),
        "source_schema": "IFC4X3",
        "source_and_output_length_units": "MILLIMETER",
        "ground_truth_or_grader_access_in_imperative_writer": False,
        "declarative_XML_or_D0_compiler_imported": False,
        "developer_authored_not_model_generated": True,
    }
