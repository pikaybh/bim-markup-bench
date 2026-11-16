"""Independent developer-authored imperative Python/IfcOpenShell I0 test_11.

Reads ONLY the original PUBLIC IFC4X3 millimetre source and the original
PUBLIC Wall target GUID. No import from XML parser, D0 compiler, D0 writer
or original author grading. Developer-owned imperative native editing is
NOT a real LLM experiment. A source-shared RefDirection is never mutated.
"""
from __future__ import annotations

from hashlib import sha256
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.util.placement
import ifcopenshell.util.unit


class OriginalRotationI0Blocked(ValueError):
    pass


def _sha(path:Path)->str:
    return sha256(path.read_bytes()).hexdigest()


def independent_public_wall_center_rotate_i0(
    original_source:Path,target_wall_guid:str,output_path:Path,
)->dict:
    if (not original_source.is_file() or original_source.is_symlink()
            or output_path.exists() or output_path.is_symlink()):
        raise OriginalRotationI0Blocked("Refuse missing original source or output overwrite")
    source_sha=_sha(original_source)
    orig=ifcopenshell.open(str(original_source))
    if (orig.schema!="IFC4X3"
            or abs(ifcopenshell.util.unit.calculate_unit_scale(orig)-.001)>1e-12):
        raise OriginalRotationI0Blocked("Original source must be IFC4X3 millimetres")
    try: wall=orig.by_guid(target_wall_guid)
    except (RuntimeError,ValueError) as exc:
        raise OriginalRotationI0Blocked("Original PUBLIC wall target missing") from exc
    if (not wall.is_a("IfcWall") or wall.HasOpenings
            or wall.ConnectedFrom or wall.ConnectedTo or wall.ProvidesBoundaries):
        raise OriginalRotationI0Blocked("Original wall is not a simple nonhosted wall")
    native=ifcopenshell.util.unit.convert_file_length_units(orig,"METER")
    product=native.by_guid(target_wall_guid)
    local=product.ObjectPlacement
    if (local is None or not local.is_a("IfcLocalPlacement")
        or native.get_total_inverses(local)!=1):
        raise OriginalRotationI0Blocked("Native wall placement shared")
    relative=local.RelativePlacement
    point=relative.Location
    refdir=relative.RefDirection
    if (relative is None or point is None or refdir is None
        or native.get_total_inverses(point)!=1):
        raise OriginalRotationI0Blocked("Native wall direction/location missing or shared")
    local_axis=ifcopenshell.util.placement.get_local_placement(local)
    oldx,oldy=(float(local_axis[0,0]),float(local_axis[1,0]))
    if not math.isclose(math.hypot(oldx,oldy),1.,abs_tol=1e-8):
        raise OriginalRotationI0Blocked("Original native wall local X not a unit vector")
    src_axis_reps=[rep for rep in product.Representation.Representations
                   if rep.RepresentationIdentifier=="Axis"
                   and rep.RepresentationType=="Curve2D"]
    if len(src_axis_reps)!=1 or len(src_axis_reps[0].Items)!=1:
        raise OriginalRotationI0Blocked("Original native wall must have one direct axis")
    axis_item=src_axis_reps[0].Items[0]
    if not axis_item.is_a("IfcPolyline") or len(axis_item.Points)!=2:
        raise OriginalRotationI0Blocked("Original Wall native straight axis not found")
    p,q=[tuple(float(v) for v in pt.Coordinates) for pt in axis_item.Points]
    length=math.hypot(q[0]-p[0],q[1]-p[1])
    if (abs(p[0])>1e-9 or abs(p[1])>1e-9
            or abs(q[1])>1e-9 or not math.isclose(length,5.,abs_tol=1e-7)):
        raise OriginalRotationI0Blocked("Unsupported original native local wall axis")
    oldorigin=(float(local_axis[0,3]),float(local_axis[1,3]))
    center=(oldorigin[0]+oldx*length/2,oldorigin[1]+oldy*length/2)
    rotated_x=-oldy
    rotated_y=oldx
    if abs(rotated_x)<1e-12:rotated_x=0.0
    if abs(rotated_y)<1e-12:rotated_y=0.0
    new_start=(center[0]-rotated_x*length/2,
               center[1]-rotated_y*length/2)
    point.Coordinates=(new_start[0],new_start[1],float(point.Coordinates[2]))
    # Crucially: original RefDirection is an IFC entity SHARED with 13 other
    # local placements. Create a private IfcDirection and rebind the one
    # target IfcAxis2Placement3D instead of modifying that shared entity.
    private=native.create_entity("IfcDirection",
        DirectionRatios=(rotated_x,rotated_y,0.))
    relative.RefDirection=private
    with TemporaryDirectory(prefix="bmb-v028-independent-wall-i0-") as td:
        metric=Path(td)/"native_wall_rotated_metric.ifc"
        native.write(str(metric))
        restored=ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(metric)),"MILLIMETER")
        if (restored.schema!="IFC4X3"
            or abs(ifcopenshell.util.unit.calculate_unit_scale(restored)-.001)>1e-12):
            raise OriginalRotationI0Blocked("Original IFC4X3 millimetres were not restored")
        output_path.parent.mkdir(parents=True,exist_ok=True)
        restored.write(str(output_path))
    if _sha(original_source)!=source_sha:
        raise OriginalRotationI0Blocked("Source original IFC mutated")
    final=ifcopenshell.open(str(output_path))
    if final.by_guid(target_wall_guid).is_a()!="IfcWall":
        raise OriginalRotationI0Blocked("Target original Wall lost")
    return {
        "status":"INDEPENDENT_IMPERATIVE_ORIGINAL_PUBLIC_WALL_90_CENTER",
        "source_sha256":source_sha,
        "full_native_IFC_sha256":_sha(output_path),
        "original_target_wall_preserved":True,
        "native_IfcProduct_count":len(final.by_type("IfcProduct")),
        "model_calls":0,
    }
