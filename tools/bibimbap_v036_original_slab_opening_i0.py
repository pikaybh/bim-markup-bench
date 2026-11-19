"""Independent original-public BIBIMBAP test_03 Python/IfcOpenShell I0.

One nonblinded developer reference; original public IFC and question ONLY.
No XML/typed binder/compiler, author score, GT or D0 output dependency.
Geometric choices predeclared in Issue #187 BEFORE grading.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.api.feature
import ifcopenshell.api.geometry
import ifcopenshell.api.root
import ifcopenshell.geom
import ifcopenshell.util.unit
import ifcopenshell.util.shape
import numpy as np

SOURCE_SHA="9ef1235e49d5b0359c1d44fd95a7afad7755149362109ca8b875d0427dc487ca"
PUBLIC_HOST_GUID="11kJIqz$n2Jf_DfJV1SCVP"
SLAB_NATIVE_WORLD_BBOX_M=(-.2,-.175,3.8,10.2,10.2,4.1)
OPENING_WIDTH_M=5.
OPENING_DEPTH_M=5.  # horizontal Y direction in the original public slab
OPENING_TOOL_VERTICAL_DEPTH_M=.5 # through source .3m slab; NOT public 5m dimension
OPENING_CENTER_M=(5.,5.0125,3.7)
OPENING_WORLD_BBOX_M=(2.5,2.5125,3.7,7.5,7.5125,4.2)
EXPECTED_REMOVED_SLAB_VOLUME_M3=7.5


class IndependentSlabOpeningI0Blocked(ValueError):
    pass


def _hash(file:Path)->str:
    return sha256(file.read_bytes()).hexdigest()


def _require(ok:bool,why:str)->None:
    if not ok:
        raise IndependentSlabOpeningI0Blocked(why)


def create_original_test03_slab_opening_i0(original_mm:Path,new_candidate_mm:Path)->dict:
    """Persist original-native IFC4X3 mm with physical slab void, output fresh."""
    original_mm,new_candidate_mm=Path(original_mm),Path(new_candidate_mm)
    _require(original_mm.is_file() and not original_mm.is_symlink()
             and not new_candidate_mm.exists() and not new_candidate_mm.is_symlink()
             and original_mm.resolve()!=new_candidate_mm.resolve(),
             "Expected regular original IFC file and a fresh separate output")
    _require(_hash(original_mm)==SOURCE_SHA,
             "Original public native IFC source sha256 drift")
    source=ifcopenshell.open(str(original_mm))
    _require(source.schema=="IFC4X3" and
             abs(ifcopenshell.util.unit.calculate_unit_scale(source)-.001)<1e-12,
             "Original IFC4X3 millimetre schema/unit changed")
    host=source.by_guid(PUBLIC_HOST_GUID)
    _require(host.is_a("IfcSlab") and host.PredefinedType=="FLOOR"
             and not host.HasOpenings,
             "Public source object not an intact original floor IfcSlab")
    native_settings=ifcopenshell.geom.settings()
    native_settings.set(native_settings.USE_WORLD_COORDS,True)
    shape=ifcopenshell.geom.create_shape(native_settings,host)
    vertices=np.asarray(shape.geometry.verts,dtype=float).reshape(-1,3)
    actual_bbox=tuple(float(v) for v in (*vertices.min(axis=0),*vertices.max(axis=0)))
    _require(np.allclose(actual_bbox,SLAB_NATIVE_WORLD_BBOX_M,atol=1e-5,rtol=0),
             "Original named IfcSlab world mesh does not match pinned public source")
    source_volume=float(ifcopenshell.util.shape.get_volume(shape.geometry))
    _require(abs(source_volume-32.37)<1e-5,"Original source floor native geometry changed")
    model=ifcopenshell.util.unit.convert_file_length_units(source,"METER")
    rep_contexts=[x for x in model.by_type("IfcGeometricRepresentationSubContext")
                  if x.ContextIdentifier=="Body" and x.TargetView=="MODEL_VIEW"]
    _require(len(rep_contexts)==1,"Unique source original Body subcontext missing")
    original_guids={x.GlobalId for x in model.by_type("IfcRoot")}
    opening=ifcopenshell.api.root.create_entity(
        model,ifc_class="IfcOpeningElement",name="Independent I0 public slab opening")
    opening.PredefinedType="OPENING"
    profile=model.createIfcRectangleProfileDef(
        "AREA",None,None,OPENING_WIDTH_M,OPENING_DEPTH_M)
    solid=ifcopenshell.api.geometry.add_profile_representation(
        model,context=rep_contexts[0],profile=profile,
        depth=OPENING_TOOL_VERTICAL_DEPTH_M)
    ifcopenshell.api.geometry.assign_representation(
        model,product=opening,representation=solid)
    placement=np.eye(4,dtype="float64")
    placement[:3,3]=OPENING_CENTER_M
    ifcopenshell.api.geometry.edit_object_placement(
        model,product=opening,matrix=placement)
    ifcopenshell.api.feature.add_feature(
        model,feature=opening,element=model.by_guid(PUBLIC_HOST_GUID))
    _require(opening.GlobalId not in original_guids,
             "Opening GlobalId collided with original native IFC")
    result=ifcopenshell.util.unit.convert_file_length_units(
        model,"MILLIMETER")
    _require(result.schema=="IFC4X3" and
             abs(ifcopenshell.util.unit.calculate_unit_scale(result)-.001)<1e-12,
             "Restored real native IFC4X3 millimetre unit context changed")
    with TemporaryDirectory(prefix="bmb-v036-I0-") as td:
        stage=Path(td)/"I0-native-output.ifc"
        result.write(str(stage))
        persisted=ifcopenshell.open(str(stage))
        obj=persisted.by_guid(opening.GlobalId)
        _require(obj.is_a("IfcOpeningElement") and
                 len(obj.VoidsElements)==1 and
                 obj.VoidsElements[0].RelatingBuildingElement.GlobalId==PUBLIC_HOST_GUID,
                 "Written native original source IfcSlab void missing")
        _require(_hash(original_mm)==SOURCE_SHA,
                 "Original public native IFC changed during independent I0")
        new_candidate_mm.write_bytes(stage.read_bytes())
    return {
        "status":"V036_ORIGINAL_PUBLIC_TEST03_INDEPENDENT_NATIVE_I0_SLAB_VOID_COMMITTED",
        "original_source_sha256":SOURCE_SHA,
        "original_slab_host_guid":PUBLIC_HOST_GUID,
        "new_native_opening_guid":opening.GlobalId,
        "opening_horizontal_dimensions_m":[OPENING_WIDTH_M,OPENING_DEPTH_M],
        "native_void_vertical_tool_depth_m":OPENING_TOOL_VERTICAL_DEPTH_M,
        "opening_center_xyz_m":list(OPENING_CENTER_M),
        "candidate_original_mm_IFC_sha256":_hash(new_candidate_mm),
        "import_from_D0_XML_or_original_author_grader":False,
        "model_generated":False,
    }
