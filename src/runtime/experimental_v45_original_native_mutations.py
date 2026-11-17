"""v0.45 original 4-task research-only typed XML -> ORIGINAL native-mm IFC.

No original question answers hardcoded and no author grading. The entire
original v0.44 source reference remains immutable. This writer is limited to:
 - positive new dimensions of a single original IfcSlab rectangle profile;
 - absolute original-native world XY position of one original mapped column;
 - the shared mapped IfcColumn extrusion depth for ALL source columns;
 - explicit original column GUID deletion set using IfcOpenShell API.
An independent oracle (not imported here) must validate every candidate before
the host commits it.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from pathlib import Path
from lxml import etree

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.placement
import numpy as np

from src.runtime.experimental_v44_original_native_step_readonly import (
    PINS as ORIGINAL_PINS, Q, check_original_native_readonly_source,
    project_native_readonly_source_v044)
from tools.bibimbap_matched25_tools import file_hash

ROOT=Path(__file__).resolve().parents[2]
XSD=ROOT/"spec"/"original_native_typed_mutations_v045.xsd"
AUTHORING_MODE="SINGLE_TYPED_PLAN_NATIVE_MUTATION"
EDIT_AUTHORITY="SELECTIVE_NATIVE_MUTATION_SUBJECT_TO_INDEPENDENT_ORACLE"
TASK_OPERATIONS={
    "geometry_test_14":"SetSlabRectangleDimensions",
    "geometry_test_15":"MoveColumnPlacement",
    "topological_test_11":"SetAllMappedColumnDepth",
    "topological_test_17":"DeleteColumnsByGuid",
}
MAX_XML_BYTES=300000


class OriginalNativeMutation045Error(ValueError):
    pass


@dataclass(frozen=True)
class OriginalNativeView045:
    xml:bytes
    source_sha:str
    task_id:str
    native_schema:str


@dataclass(frozen=True)
class TypedEdit045:
    task_id:str
    kind:str
    target_guids:tuple[str,...]
    args:tuple[float,...]


@dataclass(frozen=True)
class NativeMutation045Result:
    task_id:str
    kind:str
    changed_guid_count:int
    candidate_original_native_mm_sha256:str

    def as_dict(self):
        return {"status":"ACTUAL_ORIGINAL_NATIVE_MM_IFC_WRITTEN_UNTRUSTED_UNTIL_ORACLE",
                "task_id":self.task_id,"operation_kind":self.kind,
                "target_guid_count":self.changed_guid_count}


def need(ok:bool,msg:str):
    if not ok:raise OriginalNativeMutation045Error(msg)


def schema()->etree.XMLSchema:
    return etree.XMLSchema(etree.parse(str(XSD)))


def check_source(source:Path,sha:str,model=None)->str:
    source=Path(source)
    need(source.is_file() and not source.is_symlink()
         and sha in ORIGINAL_PINS and file_hash(source)==sha,
         "V045 requires exact one of four original published IFC4X3/mm SHA256 sources")
    opened=model if model is not None else ifcopenshell.open(str(source))
    return check_original_native_readonly_source(source,sha,opened)


def project_original_native_mutations_v045(source:Path,*,source_sha:str)->OriginalNativeView045:
    task_id=check_source(source,source_sha)
    source_v44=project_native_readonly_source_v044(
        source,original_native_sha256=source_sha)
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True)
    root=etree.fromstring(source_v44.xml,parser)
    need(root.tag==Q+"Building" and len(root)==1,
         "Original v0.44 complete source node structurally changed")
    root.set("version","0.45")
    root.set("nativeMutationPermission",EDIT_AUTHORITY)
    etree.SubElement(root,Q+"NativeEditPlan",{
        "planVersion":"0.45",
        "sourceOriginalIFCSha256":source_sha,
        "editAuthority":AUTHORING_MODE,
    })
    data=etree.tostring(root,encoding="utf8",xml_declaration=True,
                        pretty_print=False)
    need(len(data)<=MAX_XML_BYTES and schema().validate(root),
         "Original v0.45 typed XML exceeded limit or invalid XSD")
    need(file_hash(source)==source_sha,
         "Original public source changed during v0.45 XML reader")
    return OriginalNativeView045(data,source_sha,task_id,source_v44.native_schema)


def _float(s:str,*,min_value:float,max_value:float)->float:
    try:
        value=float(s)
    except Exception as exc:
        raise OriginalNativeMutation045Error("Finite numeric typed edit value required") from exc
    need(math.isfinite(value) and min_value<=value<=max_value,
         "Finite positive or bounded typed value required")
    # reject submicrometre changes that could be rounded away
    need(abs(value-round(value,6))<1e-9,
         "V045 original native mutation requires up-to-1-micrometre precision")
    return value


def _body_solid(product,*,mapped:bool):
    need(product.Representation is not None,
         "Original target has no native IFC physical representation")
    reps=[r for r in product.Representation.Representations
          if r.RepresentationIdentifier=="Body"]
    need(len(reps)==1 and len(reps[0].Items)==1,
         "Ambiguous multi-item original body geometry cannot be edited")
    item=reps[0].Items[0]
    if mapped:
        need(item.is_a("IfcMappedItem") and item.MappingSource is not None,
             "Original target body is not mapped source geometry")
        source=item.MappingSource.MappedRepresentation
        need(len(source.Items)==1,
             "Original source map contains multiple native solid items")
        solid=source.Items[0]
    else:
        solid=item
    need(solid.is_a("IfcExtrudedAreaSolid")
         and solid.SweptArea.is_a("IfcRectangleProfileDef")
         and solid.Depth>0,
         "V045 supports only original native rectangular extrusion solid")
    return solid


def _validate_shared_column_solid(model,columns):
    need(len(columns)==2,
         "Original shared mapped column depth path must have exactly two native columns")
    solids=[_body_solid(p,mapped=True) for p in columns]
    need(solids[0].id()==solids[1].id(),
         "Original column mapped extrusion must be same shared native source")
    return solids[0]


def parse_original_native_edit_plan_v045(
        original_source:Path,edited_xml:bytes,*,source_sha:str)->TypedEdit045:
    task_id=check_source(original_source,source_sha)
    need(isinstance(edited_xml,bytes) and 0<len(edited_xml)<=MAX_XML_BYTES,
         "Complete original source XML required with bounded byte size")
    from src.security.agent_boundary import check_xml_bytes
    check_xml_bytes(edited_xml)
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,recover=False,huge_tree=False)
    root=etree.fromstring(edited_xml,parser)
    need(schema().validate(root),"V045 original source XML violates strict typed XSD")
    baseline=project_original_native_mutations_v045(
        original_source,source_sha=source_sha)
    expected=etree.fromstring(baseline.xml,parser)
    need(root.tag==Q+"Building" and len(root)==2
         and [x.tag for x in root]==[Q+"OriginalNativeIFCSource",Q+"NativeEditPlan"]
         and dict(root.attrib)==dict(expected.attrib),
         "Original native source root, schema, units, version, SHA or edit authority spoofed")
    need(etree.tostring(root[0],method="c14n")==
         etree.tostring(expected[0],method="c14n"),
         "Original native source STEP/GUID/metadata/world meshes are IMMUTABLE")
    plan=root[1]
    need(dict(plan.attrib)==dict(expected[1].attrib)
         and len(plan)==1,
         "One source-pinned typed native editing operation required")
    op=plan[0]
    kind=op.tag.removeprefix(Q)
    need(kind==TASK_OPERATIONS[task_id],
         "Operation kind incompatible with original public source native CRUD task")
    f=ifcopenshell.open(str(original_source))
    if kind=="SetSlabRectangleDimensions":
        need(len(op)==0 and set(op.attrib)==
             {"ifcGuid","newXDimM","newYDimM"},
             "Only one native IfcSlab source rectangle dimensional command")
        slabs=f.by_type("IfcSlab")
        need(len(slabs)==1 and op.get("ifcGuid")==slabs[0].GlobalId,
             "Must reference actual native original IfcSlab GUID")
        solid=_body_solid(slabs[0],mapped=False)
        x=_float(op.get("newXDimM"),min_value=.1,max_value=25.)
        y=_float(op.get("newYDimM"),min_value=.1,max_value=25.)
        old=(float(solid.SweptArea.XDim)/1000,
             float(solid.SweptArea.YDim)/1000)
        changed=[abs(new-prev)>1e-6 for new,prev in zip((x,y),old)]
        need(sum(changed)==1 and (x>old[0]+1e-6 or y>old[1]+1e-6),
             "Original Slab edit must strictly INCREASE exactly one native rectangle dimension")
        return TypedEdit045(task_id,kind,(slabs[0].GlobalId,),(x,y))
    if kind=="MoveColumnPlacement":
        need(len(op)==0 and set(op.attrib)==
             {"ifcGuid","newWorldOriginXM","newWorldOriginYM"},
             "Original column move accepts only original GUID and absolute XY")
        guid=op.get("ifcGuid")
        cols={c.GlobalId:c for c in f.by_type("IfcColumn")}
        need(len(cols)==4 and guid in cols,
             "Column GUID must exist in exactly four original source columns")
        c=cols[guid]
        need(c.ObjectPlacement is not None
             and c.ObjectPlacement.is_a("IfcLocalPlacement"),
             "Only actual original native source LocalPlacement can be moved")
        _body_solid(c,mapped=True)
        point=c.ObjectPlacement.RelativePlacement.Location
        need(len(point.Coordinates)==3 and f.get_total_inverses(point)==1,
             "Original column coordinate is not an isolated editable CartesianPoint")
        x=_float(op.get("newWorldOriginXM"),min_value=-40,max_value=40)
        y=_float(op.get("newWorldOriginYM"),min_value=-40,max_value=40)
        world=ifcopenshell.util.placement.get_local_placement(c.ObjectPlacement)
        before=(world[0,3]/1000,world[1,3]/1000)
        need(abs(x-before[0])+abs(y-before[1])>1e-6,
             "Original column absolute placement did not change")
        return TypedEdit045(task_id,kind,(guid,),(x,y))
    if kind=="SetAllMappedColumnDepth":
        need(len(op)==0 and set(op.attrib)=={"newDepthM"},
             "Only one exact shared mapped original native column depth value allowed")
        cols=f.by_type("IfcColumn")
        solid=_validate_shared_column_solid(f,cols)
        new_depth=_float(op.get("newDepthM"),min_value=.2,max_value=10.)
        need(abs(float(solid.Depth)/1000-new_depth)>1e-6,
             "Original native shared mapped column depth was unchanged")
        return TypedEdit045(task_id,kind,
                            tuple(sorted(c.GlobalId for c in cols)),(new_depth,))
    if kind=="DeleteColumnsByGuid":
        need(set(op.attrib)==set() and 1<=len(op)<=9,
             "Delete only 1..9 original source Column GUIDs")
        targets=[]
        cols={c.GlobalId:c for c in f.by_type("IfcColumn")}
        need(len(cols)==10,"Original native source must contain exactly 10 Columns")
        for child in op:
            need(child.tag==Q+"DeleteColumn" and len(child)==0
                 and set(child.attrib)=={"ifcGuid"},
                 "Unexpected non-column deletion or extra attributes")
            g=child.get("ifcGuid")
            need(g in cols and g not in targets,
                 "Unknown, duplicate or non-column native source deletion target")
            targets.append(g)
        return TypedEdit045(task_id,kind,tuple(targets),())
    raise OriginalNativeMutation045Error("Unsupported native edit kind")


def compile_original_native_mutation_v045(
        source:Path,submitted_xml:bytes,destination_mm:Path,*,source_sha:str,
        )->NativeMutation045Result:
    """Native writer only. The HOST must run independent physical oracle."""
    source=Path(source)
    destination_mm=Path(destination_mm)
    need(destination_mm.parent.is_dir() and not destination_mm.exists()
         and not destination_mm.is_symlink(),
         "V045 native candidate destination must be fresh directory/file")
    edit=parse_original_native_edit_plan_v045(
        source,submitted_xml,source_sha=source_sha)
    model=ifcopenshell.open(str(source))
    task_id=check_source(source,source_sha,model)
    if edit.kind=="SetSlabRectangleDimensions":
        target=model.by_guid(edit.target_guids[0])
        solid=_body_solid(target,mapped=False)
        solid.SweptArea.XDim=round(edit.args[0]*1000,6)
        solid.SweptArea.YDim=round(edit.args[1]*1000,6)
    elif edit.kind=="MoveColumnPlacement":
        target=model.by_guid(edit.target_guids[0])
        place=target.ObjectPlacement
        p=place.RelativePlacement.Location
        orig=tuple(float(v) for v in p.Coordinates)
        world=ifcopenshell.util.placement.get_local_placement(place)
        parent=place.PlacementRelTo
        pm=(ifcopenshell.util.placement.get_local_placement(parent)
            if parent is not None else np.eye(4))
        target_world=np.array([edit.args[0]*1000,
                               edit.args[1]*1000,world[2,3],1.])
        local=np.linalg.inv(pm)@target_world
        need(np.isfinite(local).all() and
             all(abs(float(local[i]))<1e7 for i in range(3)),
             "Original world position not representable in source parent frame")
        p.Coordinates=tuple(round(float(local[i]),6) for i in range(3))
    elif edit.kind=="SetAllMappedColumnDepth":
        cols=model.by_type("IfcColumn")
        solid=_validate_shared_column_solid(model,cols)
        solid.Depth=round(edit.args[0]*1000,6)
    elif edit.kind=="DeleteColumnsByGuid":
        for guid in edit.target_guids:
            product=model.by_guid(guid)
            need(product is not None and product.is_a("IfcColumn"),
                 "Delete target no longer valid original native Column")
            ifcopenshell.api.run("root.remove_product",model,product=product)
    else:
        raise OriginalNativeMutation045Error("Unknown/forbidden original mutation plan")
    need(file_hash(source)==source_sha,
         "Original source IFC changed while preparing native mutation")
    model.write(str(destination_mm))
    need(destination_mm.is_file()
         and destination_mm.stat().st_size>100
         and file_hash(source)==source_sha,
         "Original source-native IFC writer failed or modified its original input")
    return NativeMutation045Result(
        task_id,edit.kind,len(edit.target_guids),file_hash(destination_mm))
