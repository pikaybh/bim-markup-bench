"""Original public BIBIMBAP test_01 native Python/IfcOpenShell I0 control.

Read ONLY the original public IFC and public task. Predeclared engineering
interpretation: 2m height x 1m width, zero sill, center of specified host
wall's real native axis, 0.04m physical door leaf, 0.4m deep full through-void.
Do not import XML, D0, graders, private GT or earlier native candidates.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import ifcopenshell
import ifcopenshell.api.feature
import ifcopenshell.api.geometry
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

SOURCE_SHA="9ef1235e49d5b0359c1d44fd95a7afad7755149362109ca8b875d0427dc487ca"
HOST_GUID="2UsXAbj6n0fwEWqdkVuHvf"
DOOR_WIDTH_M=1.0
DOOR_HEIGHT_M=2.0
SILL_M=0.0
DOOR_LEAF_THICKNESS_M=0.04
OPENING_THROUGH_WALL_DEPTH_M=0.4
# Original wall's 10.2m horizontal axis -> centre, fixed before scoring.
OFFSET_FROM_HOST_AXIS_START_M=5.1

class OriginalPublicDoorI0Blocked(ValueError):
    pass

def _sha(file:Path)->str:
    return sha256(file.read_bytes()).hexdigest()

def _context(file,identifier,view):
    cs=[x for x in file.by_type("IfcGeometricRepresentationSubContext")
        if x.ContextIdentifier==identifier and x.TargetView==view]
    if len(cs)!=1:
        raise OriginalPublicDoorI0Blocked("Unique original Body MODEL_VIEW context missing")
    return cs[0]

def create_original_public_test01_door_i0(source_mm:Path,dest_mm:Path)->dict:
    source_mm,dest_mm=Path(source_mm),Path(dest_mm)
    if (not source_mm.is_file() or source_mm.is_symlink()
            or dest_mm.exists() or dest_mm.is_symlink()
            or source_mm.resolve()==dest_mm.resolve()):
        raise OriginalPublicDoorI0Blocked("Source must be existing regular and output fresh")
    source_sha=_sha(source_mm)
    if source_sha!=SOURCE_SHA:
        raise OriginalPublicDoorI0Blocked("Original public IFC source SHA mismatch")
    orig=ifcopenshell.open(str(source_mm))
    if orig.schema!="IFC4X3" or abs(ifcopenshell.util.unit.calculate_unit_scale(orig)-0.001)>1e-12:
        raise OriginalPublicDoorI0Blocked("Original IFC4X3 millimetres drift")
    model=ifcopenshell.util.unit.convert_file_length_units(orig,"METER")
    host=model.by_guid(HOST_GUID)
    if not host.is_a("IfcWall"):
        raise OriginalPublicDoorI0Blocked("Public host GlobalId is not IfcWall")
    level=ifcopenshell.util.element.get_container(host)
    if (level is None or not level.is_a("IfcBuildingStorey")
            or level.Name!="L1" or level.Elevation is None
            or abs(float(level.Elevation))>1e-8):
        raise OriginalPublicDoorI0Blocked("Specified original host not in L1 ground storey")
    # Derive actual host axis length from original native IFC, not prior D0.
    axes=[rep for rep in host.Representation.Representations
          if rep.RepresentationIdentifier=="Axis"]
    if len(axes)!=1 or len(axes[0].Items)!=1:
        raise OriginalPublicDoorI0Blocked("Host needs exactly one native Axis line")
    axis=axes[0].Items[0]
    if axis.is_a("IfcPolyline"):
        coords=[x.Coordinates for x in axis.Points]
    elif axis.is_a("IfcIndexedPolyCurve") and axis.Segments is None:
        coords=axis.Points.CoordList
    else:
        raise OriginalPublicDoorI0Blocked("Unsupported native host axis geometry")
    if (len(coords)!=2 or len(coords[0])<2 or len(coords[1])<2
            or not np.allclose(coords[0][:2],(0.,0.),atol=1e-5)
            or not np.allclose(coords[1][:2],(10.2,0.),atol=1e-4)):
        raise OriginalPublicDoorI0Blocked("Source host original 10.2m axis differs")
    body=_context(model,"Body","MODEL_VIEW")
    original_roots={x.GlobalId for x in model.by_type("IfcRoot")}
    opening=ifcopenshell.api.root.create_entity(
        model,ifc_class="IfcOpeningElement",name="Native public wall void I0")
    opening.PredefinedType="OPENING"
    # Opening is vertically extruded; XY profile spans wall-axis width
    # and penetrates completely through original 0.2m thick host.
    profile=model.createIfcRectangleProfileDef(
        "AREA",None,None,DOOR_WIDTH_M,OPENING_THROUGH_WALL_DEPTH_M)
    rep=ifcopenshell.api.geometry.add_profile_representation(
        model,context=body,profile=profile,depth=DOOR_HEIGHT_M)
    ifcopenshell.api.geometry.assign_representation(
        model,product=opening,representation=rep)
    host_world=ifcopenshell.util.placement.get_local_placement(host.ObjectPlacement)
    rel=np.eye(4,dtype="float64")
    rel[:3,3]=[OFFSET_FROM_HOST_AXIS_START_M,SILL_M*0.,SILL_M]
    placement=host_world@rel
    ifcopenshell.api.geometry.edit_object_placement(
        model,product=opening,matrix=placement)
    ifcopenshell.api.feature.add_feature(model,feature=opening,element=host)
    door=ifcopenshell.api.root.create_entity(
        model,ifc_class="IfcDoor",name="Native public hosted Door I0")
    door.PredefinedType="DOOR"
    door.OverallWidth=DOOR_WIDTH_M
    door.OverallHeight=DOOR_HEIGHT_M
    # Door leaf is a physically present solid, substantially thinner than
    # the void and centered in the wall plane.
    leaf=model.createIfcRectangleProfileDef(
        "AREA",None,None,DOOR_WIDTH_M,DOOR_LEAF_THICKNESS_M)
    leafrep=ifcopenshell.api.geometry.add_profile_representation(
        model,context=body,profile=leaf,depth=DOOR_HEIGHT_M)
    ifcopenshell.api.geometry.assign_representation(
        model,product=door,representation=leafrep)
    ifcopenshell.api.geometry.edit_object_placement(
        model,product=door,matrix=placement)
    ifcopenshell.api.feature.add_filling(
        model,opening=opening,element=door)
    ifcopenshell.api.spatial.assign_container(
        model,products=[door],relating_structure=level)
    if any(x.GlobalId in original_roots for x in (opening,door)):
        raise OriginalPublicDoorI0Blocked("New native GUID collided with original")
    restored=ifcopenshell.util.unit.convert_file_length_units(model,"MILLIMETER")
    if restored.schema!="IFC4X3" or abs(
            ifcopenshell.util.unit.calculate_unit_scale(restored)-0.001)>1e-12:
        raise OriginalPublicDoorI0Blocked("Output original-native mm context lost")
    with TemporaryDirectory(prefix="bmb-v035-I0-original-") as td:
        stage=Path(td)/"native_door_mm.ifc"
        restored.write(str(stage))
        checked=ifcopenshell.open(str(stage))
        if (not checked.by_guid(opening.GlobalId).is_a("IfcOpeningElement")
                or not checked.by_guid(door.GlobalId).is_a("IfcDoor")
                or _sha(source_mm)!=source_sha):
            raise OriginalPublicDoorI0Blocked("Physical native Door/Opening missing or source changed")
        dest_mm.write_bytes(stage.read_bytes())
    if _sha(source_mm)!=source_sha:
        dest_mm.unlink(missing_ok=True)
        raise OriginalPublicDoorI0Blocked("Source mutated during independent native I0")
    return {
        "status":"ORIGINAL_TEST01_HOSTED_DOOR_NATIVE_I0_CREATED",
        "source_sha256":source_sha,
        "host_guid":HOST_GUID,
        "opening_guid":opening.GlobalId,
        "door_guid":door.GlobalId,
        "predeclared_door_height_m":DOOR_HEIGHT_M,
        "predeclared_door_width_m":DOOR_WIDTH_M,
        "predeclared_sill_m":SILL_M,
        "predeclared_midwall_axis_offset_m":OFFSET_FROM_HOST_AXIS_START_M,
        "candidate_mm_ifc_sha256":_sha(dest_mm),
        "model_generated":False,
        "imports_from_XML_compiler_or_original_grader":False,
    }
