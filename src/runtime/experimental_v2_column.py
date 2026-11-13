"""Research-only v0.2 Column CREATE vertical slice (Issue #118).

This module is a NEW prospective compiler entrypoint, NOT a replacement of
historic v0.1 compiler or old BIBIMBAP scores. The LLM edits a *declarative*
Column state in XML; native IfcOpenShell creation stays entirely TRUSTED.

Initially supports exactly ONE added, standalone, axis-aligned rectangular
IfcColumn in an existing IFC4X3 source, on an existing zero-elevation
IfcBuildingStorey. All unsupported combinations fail closed. Otherwise
delegates unchanged v0.1 operation set to the original pinned compiler.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit
import numpy as np

from src.runtime.compiler import compile_declarative_xml,CompileReport
from src.runtime.ifc_projection import project_ifc
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document
from src.runtime.semantic_graph import graph_diff
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.ifc_mutations import Mutation
from src.runtime.transaction import stage_and_commit

class V2ColumnError(ValueError):
    pass

class ColumnV2CompileReport(CompileReport):
    """Separate prospective operation status; never label Column as Wall."""
    def as_dict(self)->dict:
        value=super().as_dict()
        value["status"]="COMMITTED_SCOPED_IFC4X3_COLUMN_CREATE_V2"
        value["scope"]="one axis-aligned rectangular standalone IfcColumn in zero-elevation original storey"
        value["compiler_version"]="experimental-column-v0.2"
        value["general_bim_edit_45_supported"]=False
        return value

def _measure(attrs:dict,name:str)->float:
    try:
        val=Decimal(attrs[name])
    except (KeyError,ValueError,ArithmeticError) as exc:
        raise V2ColumnError("Invalid Column "+name) from exc
    if not val.is_finite():
        raise V2ColumnError("Nonfinite Column "+name)
    value=float(val)
    if not math.isfinite(value) or abs(value)>10000:
        raise V2ColumnError("Column coordinate/dimension outside bounded range")
    return value

def _column_params(attrs:dict)->tuple[float,float,float,float,float,float]:
    v=tuple(_measure(attrs,k) for k in ("x","y","z","width","depth","height"))
    if any(d<=0.02 or d>50 for d in v[3:]):
        raise V2ColumnError("Column width/depth/height outside bounded positive range")
    return v

def _body_context(file:ifcopenshell.file):
    body=[x for x in file.by_type("IfcGeometricRepresentationSubContext")
          if x.ContextIdentifier=="Body" and x.TargetView=="MODEL_VIEW"]
    if len(body)!=1:
        raise V2ColumnError("Unique original native Body MODEL_VIEW context required")
    return body[0]

def _storey(file:ifcopenshell.file,guid:str):
    try:
        level=file.by_guid(guid)
    except RuntimeError as exc:
        raise V2ColumnError("Original BuildingStorey missing") from exc
    if not level.is_a("IfcBuildingStorey") or level.Elevation is None or abs(float(level.Elevation))>1e-8:
        raise V2ColumnError("v0.2 Column creation requires existing zero-elevation storey")
    return level

def _world_bbox(col:ifcopenshell.entity_instance)->tuple[tuple[float,float,float],tuple[float,float,float]]:
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        result=ifcopenshell.geom.create_shape(settings,col)
    except Exception as exc:
        raise V2ColumnError("Native IfcColumn mesh cannot be created") from exc
    verts=np.array(result.geometry.verts,dtype=float)
    if len(verts)<18 or len(verts)%3:
        raise V2ColumnError("Native Column mesh is absent")
    arr=verts.reshape((-1,3))
    if not np.isfinite(arr).all():
        raise V2ColumnError("Column mesh contains nonfinite vertices")
    return tuple(float(v) for v in arr.min(axis=0)),tuple(float(v) for v in arr.max(axis=0))

def _verify_column(file:ifcopenshell.file,guid:str,level_guid:str,
                   params:tuple[float,float,float,float,float,float])->dict:
    try:
        col=file.by_guid(guid)
    except RuntimeError as exc:
        raise V2ColumnError("Expected IfcColumn missing in result") from exc
    if not col.is_a("IfcColumn"):
        raise V2ColumnError("New GlobalId does not belong to IfcColumn")
    container=ifcopenshell.util.element.get_container(col)
    if container is None or container.GlobalId!=level_guid:
        raise V2ColumnError("Column is not contained in required native storey")
    reps=[item for rep in col.Representation.Representations for item in rep.Items
          if item.is_a("IfcExtrudedAreaSolid")]
    if len(reps)!=1:
        raise V2ColumnError("Column missing unique native extruded solid")
    solid=reps[0]
    expected=params
    if not math.isclose(float(solid.Depth),expected[5],rel_tol=0,abs_tol=1e-6):
        raise V2ColumnError("Native Column depth is not XML height")
    minimum,maximum=_world_bbox(col)
    target_min=expected[:3]
    target_max=(expected[0]+expected[3],expected[1]+expected[4],expected[2]+expected[5])
    if any(not math.isclose(actual,desired,rel_tol=0,abs_tol=1e-5)
           for actual,desired in zip((*minimum,*maximum),(*target_min,*target_max))):
        raise V2ColumnError("Actual world mesh footprint/height differs from XML Column declaration")
    return {"bbox_min_m":minimum,"bbox_max_m":maximum,"storey_guid":level_guid}

def _native_preservation(source:Path,result:Path,new_guid:str)->int:
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(result))
    if a.schema!="IFC4X3" or b.schema!="IFC4X3":
        raise V2ColumnError("Native IFC4X3 schema lost")
    old_roots={x.GlobalId:x for x in a.by_type("IfcRoot")}
    new_roots={x.GlobalId:x for x in b.by_type("IfcRoot")}
    if len(old_roots)!=len(a.by_type("IfcRoot")) or len(new_roots)!=len(b.by_type("IfcRoot")):
        raise V2ColumnError("Duplicate native GlobalId")
    if not set(old_roots) <=set(new_roots) or new_guid not in new_roots:
        raise V2ColumnError("Previously existing native root was removed")
    extra=set(new_roots)-set(old_roots)-{new_guid}
    if any(not new_roots[g].is_a("IfcRelContainedInSpatialStructure") for g in extra):
        raise V2ColumnError("Unapproved new native IFC root class")
    if len(b.by_type("IfcColumn"))!=len(a.by_type("IfcColumn"))+1:
        raise V2ColumnError("Unexpected number of native IfcColumn objects")
    unchanged=0
    for guid,obj in old_roots.items():
        new=new_roots[guid]
        if obj.is_a()!=new.is_a():
            raise V2ColumnError("Original IFC entity class mutated")
        if str(obj)==str(new):
            unchanged+=1
        elif not obj.is_a("IfcRelContainedInSpatialStructure"):
            raise V2ColumnError("Original root entity other than containment changed")
    # Check ALL pre-existing non-root entities too. New native column may
    # add STEP entities; none of the OLD unrelated geometry/entities may be
    # changed except the one existing containment relation.
    old_by_id={e.id():str(e) for e in a}
    new_by_id={e.id():str(e) for e in b}
    if not set(old_by_id).issubset(new_by_id):
        raise V2ColumnError("Original IFC STEP entity disappeared")
    changed={i for i in old_by_id if old_by_id[i]!=new_by_id[i]}
    allowed={old_roots[g].id() for g in old_roots
             if old_roots[g].is_a("IfcRelContainedInSpatialStructure")}
    if not changed <=allowed:
        raise V2ColumnError("Original noncontainment STEP entity unexpectedly changed")
    return unchanged

def compile_declarative_xml_v2(source:Path, edited_xml:bytes,
                               destination:Path)->CompileReport:
    """New v0.2 prospective compiler. Never retroactively rescored v0.1."""
    if not source.is_file() or source.is_symlink() or destination.exists():
        raise V2ColumnError("Immutable real source and unused output path required")
    projected=project_ifc(source)
    doc_before=parse_xml(projected.xml,expected_source_sha256=projected.source.source_sha256)
    doc_after=parse_xml(edited_xml,expected_source_sha256=projected.source.source_sha256)
    original=bind_document(doc_before,projection=projected)
    amended=bind_document(doc_after,projection=projected,verify_native_edges=False)
    delta=graph_diff(original.graph,amended.graph)
    node_before=original.graph.by_id()
    node_after=amended.graph.by_id()
    new_columns=[name for name in delta.added_nodes if node_after[name].kind=="Column"]
    if not new_columns:
        # Exact unchanged v0.1 semantics for previously supported operations.
        return compile_declarative_xml(source,edited_xml,destination)
    if (len(new_columns)!=1 or delta.removed_nodes or delta.changed_nodes
        or len(delta.added_nodes)!=1 or delta.removed_edges):
        raise V2ColumnError("Only isolated, single new native Column creation is supported in v0.2")
    name=new_columns[0]
    expected_added_edges=[e for e in delta.added_edges
                         if e.relation=="in_storey" and e.target==name]
    if len(delta.added_edges)!=1 or len(expected_added_edges)!=1:
        raise V2ColumnError("Unexpected semantic graph relationship addition in Column create")
    node=node_after[name]
    if node.provenance!="deterministic_new":
        raise V2ColumnError("New Column must have trusted deterministic IFC identity")
    attrs=dict(node.attributes)
    params=_column_params(attrs)
    level_node=node_after.get(attrs["level"])
    if level_node is None or level_node.kind!="Level" or level_node.provenance!="existing_source":
        raise V2ColumnError("Column creation requires existing native storey")
    model=ifcopenshell.open(str(source))
    if model.schema!="IFC4X3" or abs(ifcopenshell.util.unit.calculate_unit_scale(model)-1.0)>1e-8:
        raise V2ColumnError("Original v0.2 IFC must use metres in IFC4X3")
    storey=_storey(model,level_node.ifc_guid)
    body=_body_context(model)
    if node.ifc_guid in {o.GlobalId for o in model.by_type("IfcRoot")}:
        raise V2ColumnError("New column GlobalId collision")
    source_hash=projected.source.source_sha256

    def write(path:Path)->None:
        col=ifcopenshell.api.root.create_entity(model,ifc_class="IfcColumn",
                           name="Research-only declarative Column v0.2")
        col.GlobalId=node.ifc_guid
        x,y,z,width,depth,height=params
        profile=model.createIfcRectangleProfileDef("AREA",None,None,width,depth)
        representation=ifcopenshell.api.geometry.add_profile_representation(
            model,context=body,profile=profile,depth=height)
        ifcopenshell.api.geometry.assign_representation(
            model,product=col,representation=representation)
        matrix=np.eye(4,dtype="float64")
        matrix[:3,3]=[x+width/2,y+depth/2,z]
        ifcopenshell.api.geometry.edit_object_placement(
            model,product=col,matrix=matrix)
        ifcopenshell.api.spatial.assign_container(
            model,products=[col],relating_structure=storey)
        model.write(str(path))

    def verify(path:Path)->None:
        _verify_column(ifcopenshell.open(str(path)),node.ifc_guid,level_node.ifc_guid,params)
        _native_preservation(source,path,node.ifc_guid)
        if snapshot_source(source).source_sha256!=source_hash:
            raise V2ColumnError("Original input changed while compiling")

    stage_and_commit(destination,write,verify)
    result=snapshot_source(destination)
    untouched=_native_preservation(source,destination,node.ifc_guid)
    _verify_column(ifcopenshell.open(str(destination)),node.ifc_guid,level_node.ifc_guid,params)
    if snapshot_source(source).source_sha256!=source_hash:
        raise V2ColumnError("Original input changed after transactional commit")
    change=Mutation("CREATE_COLUMN",name,node.ifc_guid,
                    doc_after.managed_by_id()[name].span.line,
                    ("geometry","level"),"research v0.2 single axis-aligned rectangular Column")
    return ColumnV2CompileReport(source_hash,result.source_sha256,
                         projected.source.graph_fingerprint,
                         result.graph_fingerprint,
                         (change,),untouched,(),destination,True)
