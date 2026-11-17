"""Independent original-public BIBIMBAP test_05 imperative IfcWall I0.

Predeclared BEFORE scoring from PUBLIC question only: wall starts (0,-10),
extends +X 15 metres; unspecified height 3.0m, thickness 0.2m; wall axis
at the center of thickness, bottom z=0; original L1 storey. No D0, XML,
grader, answer key or scorer imports. Developer-only native IFC control.
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
# Public input gives only the start point and 15m length.
# Remaining values are openly frozen engineering assumptions, no tuning.
SPEC = (0.0, -10.0, 0.0, 15.0, -10.0, 0.0, 3.0, 0.2)
AXIS_START_M=(0.,-10.,0.)
AXIS_END_M=(15.,-10.,0.)
EXPECTED_BODY_BBOX_M=(0.,-10.1,0.,15.,-9.9,3.)
STOREY_NAME="L1"


class IndependentWallI0Blocked(ValueError):
    pass


def _hash(path:Path)->str:
    return sha256(path.read_bytes()).hexdigest()


def create_original_test05_wall_i0(source_mm:Path,output_mm:Path)->dict:
    source_mm,output_mm=Path(source_mm),Path(output_mm)
    if (not source_mm.is_file() or source_mm.is_symlink()
            or output_mm.exists() or output_mm.is_symlink()
            or source_mm.resolve()==output_mm.resolve()):
        raise IndependentWallI0Blocked("Original native source required and output fresh")
    original_sha=_hash(source_mm)
    if original_sha!=SOURCE_SHA:
        raise IndependentWallI0Blocked("Pinned original public native source SHA changed")
    old=ifcopenshell.open(str(source_mm))
    if old.schema!="IFC4X3" or abs(ifcopenshell.util.unit.calculate_unit_scale(old)-.001)>1e-12:
        raise IndependentWallI0Blocked("Original IFC4X3 millimetre units changed")
    f=ifcopenshell.util.unit.convert_file_length_units(old,"METER")
    if abs(ifcopenshell.util.unit.calculate_unit_scale(f)-1.)>1e-12:
        raise IndependentWallI0Blocked("Native metric working model unavailable")
    levels=[s for s in f.by_type("IfcBuildingStorey")
            if s.Name==STOREY_NAME and s.Elevation is not None
            and abs(float(s.Elevation))<1e-9]
    if len(levels)!=1:
        raise IndependentWallI0Blocked("Original L1 ground storey is ambiguous")
    body=[x for x in f.by_type("IfcGeometricRepresentationSubContext")
          if x.ContextIdentifier=="Body" and x.TargetView=="MODEL_VIEW"]
    axis=[x for x in f.by_type("IfcGeometricRepresentationSubContext")
          if x.ContextIdentifier=="Axis" and x.TargetView=="GRAPH_VIEW"]
    if len(body)!=1 or len(axis)!=1:
        raise IndependentWallI0Blocked("Original unique native Body/Axis contexts missing")
    prior={s.GlobalId for s in f.by_type("IfcRoot")}
    wall=ifcopenshell.api.root.create_entity(
        f,ifc_class="IfcWall",name="Independent public I0 native wall")
    if wall.GlobalId in prior:
        raise IndependentWallI0Blocked("New physical wall native GUID collision")
    wall.PredefinedType="NOTDEFINED"
    x1,y1,z1,x2,y2,z2,height,thickness=SPEC
    # Trusted Python native IFC API but no declarative or original scorer import.
    body_rep=ifcopenshell.api.geometry.add_wall_representation(
        f,context=body[0],length=x2-x1,height=height,thickness=thickness,
        offset=-thickness/2)
    axis_rep=ifcopenshell.api.geometry.add_axis_representation(
        f,context=axis[0],axis=((0.,0.),(x2-x1,0.)))
    ifcopenshell.api.geometry.assign_representation(f,product=wall,representation=body_rep)
    ifcopenshell.api.geometry.assign_representation(f,product=wall,representation=axis_rep)
    transform=np.eye(4,dtype="float64")
    transform[:3,3]=[x1,y1,z1]
    ifcopenshell.api.geometry.edit_object_placement(f,product=wall,matrix=transform)
    ifcopenshell.api.spatial.assign_container(f,products=[wall],relating_structure=levels[0])
    mm=ifcopenshell.util.unit.convert_file_length_units(f,"MILLIMETER")
    if mm.schema!="IFC4X3" or abs(ifcopenshell.util.unit.calculate_unit_scale(mm)-.001)>1e-12:
        raise IndependentWallI0Blocked("Native millimetre output units lost")
    with TemporaryDirectory(prefix="bmb-v034-wall-I0-") as folder:
        pending=Path(folder)/"wall_native_mm.ifc"
        mm.write(str(pending))
        reopened=ifcopenshell.open(str(pending))
        if (sum(x.GlobalId==wall.GlobalId for x in reopened.by_type("IfcWall"))!=1
                or _hash(source_mm)!=original_sha):
            raise IndependentWallI0Blocked("Native physical wall missing/source drift")
        output_mm.write_bytes(pending.read_bytes())
    if _hash(source_mm)!=original_sha:
        output_mm.unlink(missing_ok=True)
        raise IndependentWallI0Blocked("Original public IFC changed")
    return {
        "status":"V034_INDEPENDENT_ORIGINAL_PUBLIC_WALL_PYTHON_IFC_I0_CREATED",
        "original_native_source_SHA256":original_sha,
        "new_native_IfcWall_GUID":wall.GlobalId,
        "original_L1_native_GUID":levels[0].GlobalId,
        "predeclared_public_axis_start_end_height_thickness_m":list(SPEC),
        "new_candidate_native_mm_ifc_SHA256":_hash(output_mm),
        "developer_authored_not_LLM":True,
        "no_XML_D0_grader_or_hidden_GT_imports":True,
    }
