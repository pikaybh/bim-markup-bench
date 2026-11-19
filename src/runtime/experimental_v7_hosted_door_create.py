"""Opt-in v0.7 compiler: two new declarative XML nodes (Opening + Door).

Trusted runtime only; neither XML author nor tested LLM calls IFC APIs.
Requires exactly two new typed nodes and exactly host_void/opening_fill
graph edges. Does not modify v0.5/v0.6 Wall compilers or frozen author grader.
"""
from __future__ import annotations
from decimal import Decimal
from pathlib import Path
import math
import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.api.geometry
import ifcopenshell.api.feature
import ifcopenshell.api.spatial
import ifcopenshell.geom
import ifcopenshell.util.unit
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.shape
import numpy as np

from src.runtime.experimental_v4_projection import project_ifc_v4
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document
from src.runtime.semantic_graph import graph_diff
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.transaction import stage_and_commit

HOST_GUID="2UsXAbj6n0fwEWqdkVuHvf"
DOOR_LEAF_THICKNESS_M=.04
OPENING_DEPTH_M=.4


class ScopedDoorV07Blocked(ValueError):
    pass


def _require(ok:bool,reason:str)->None:
    if not ok:
        raise ScopedDoorV07Blocked(reason)


def _num(attrs:dict,key:str)->float:
    try:
        x=Decimal(str(attrs[key]))
    except (ValueError,TypeError,KeyError,ArithmeticError) as exc:
        raise ScopedDoorV07Blocked("Invalid declarative field "+key) from exc
    _require(x.is_finite(),"Nonfinite declarative field "+key)
    return float(x)


def _body(model):
    cs=[x for x in model.by_type("IfcGeometricRepresentationSubContext")
        if x.ContextIdentifier=="Body" and x.TargetView=="MODEL_VIEW"]
    _require(len(cs)==1,"Original Body context not unique")
    return cs[0]


def _metric_scene_step_preservation(source:Path,candidate:Path,
                                    opening_guid:str,door_guid:str)->None:
    a=ifcopenshell.open(str(source));b=ifcopenshell.open(str(candidate))
    old={x.id():str(x) for x in a};new={x.id():str(x) for x in b}
    _require(set(old)<=set(new),"Original source STEP entity removed by hosted door compiler")
    changed={i for i in old if old[i]!=new[i]}
    contain={r.id() for r in a.by_type("IfcRelContainedInSpatialStructure")}
    _require(changed<=contain,"Original unrelated metric native STEP entity changed")
    ar={x.GlobalId:x for x in a.by_type("IfcRoot")}
    br={x.GlobalId:x for x in b.by_type("IfcRoot")}
    _require(set(ar)<=set(br),"Original native IfcRoot removed")
    for guid,earlier in ar.items():
        later=br[guid]
        _require(earlier.is_a()==later.is_a() and
                 (str(earlier)==str(later) or earlier.is_a("IfcRelContainedInSpatialStructure")),
                 "Pre-existing source native Root materially changed")
    extras=set(br)-set(ar)
    _require(extras>={opening_guid,door_guid}
             and all(g in (opening_guid,door_guid)
                     or br[g].is_a() in ("IfcRelVoidsElement","IfcRelFillsElement",
                                         "IfcRelContainedInSpatialStructure")
                     for g in extras),
             "Unsupported extra Root created")


def compile_declarative_xml_v07_hosted_door_create(
    source_metric:Path,edited_full_xml:bytes,destination_metric:Path,
)->dict:
    """One original-wall-hosted Opening+Door full XML state-diff transaction."""
    source_metric,destination_metric=Path(source_metric),Path(destination_metric)
    _require(source_metric.is_file() and not source_metric.is_symlink()
             and not destination_metric.exists() and not destination_metric.is_symlink()
             and source_metric.resolve()!=destination_metric.resolve(),
             "Immutable original metre IFC and fresh output required")
    projection=project_ifc_v4(source_metric)
    pre=parse_xml(projection.xml,expected_source_sha256=projection.source.source_sha256)
    post=parse_xml(edited_full_xml,expected_source_sha256=projection.source.source_sha256)
    pre_bound=bind_document(pre,projection=projection)
    post_bound=bind_document(post,projection=projection,verify_native_edges=False)
    delta=graph_diff(pre_bound.graph,post_bound.graph)
    _require(len(delta.added_nodes)==2 and len(delta.added_edges)==2 and
             not delta.changed_nodes and not delta.removed_nodes and not delta.removed_edges,
             "Only one new opening plus one new hosted door allowed")
    new={n.id:n for n in (post_bound.graph.by_id()[key] for key in delta.added_nodes)}
    openings=[n for n in new.values() if n.kind=="Opening" and n.provenance=="deterministic_new"]
    doors=[n for n in new.values() if n.kind=="Door" and n.provenance=="deterministic_new"]
    _require(len(openings)==len(doors)==1,"Only one new Opening and one Door allowed")
    opening,door=openings[0],doors[0]
    oa,da=dict(opening.attributes),dict(door.attributes)
    host_node=post_bound.graph.by_id().get(oa.get("host"))
    _require(host_node is not None and host_node.kind=="Wall"
             and host_node.provenance=="existing_source" and
             host_node.ifc_guid==HOST_GUID,
             "Opening must host the exact original public source Wall")
    _require(da.get("opening")==opening.id,
             "Door must fill exactly the newly created opening")
    expected={( "host_void",host_node.id,opening.id),
              ( "opening_fill",opening.id,door.id)}
    actual={(e.relation,e.source,e.target) for e in delta.added_edges}
    _require(actual==expected,"Host/void/filling graph relationships differ")
    offset=_num(oa,"offset");sill=_num(oa,"sill")
    width=_num(oa,"width");height=_num(oa,"height")
    dw=_num(da,"width");dh=_num(da,"height")
    _require(0<=sill<=.5 and 0.2<=offset<=9.2
             and .2<=width<=2.5 and .2<=height<=3.5
             and math.isclose(dw,width,abs_tol=1e-8)
             and math.isclose(dh,height,abs_tol=1e-8),
             "Unsupported opening/door physical dimensions or margins")
    model=ifcopenshell.open(str(source_metric))
    _require(model.schema=="IFC4X3" and
             abs(ifcopenshell.util.unit.calculate_unit_scale(model)-1.)<1e-9,
             "Experimental native compiler requires IFC4X3 metre source")
    host=model.by_guid(HOST_GUID)
    _require(host.is_a("IfcWall"),"Specified public Wall missing")
    storey=ifcopenshell.util.element.get_container(host)
    _require(storey is not None and storey.is_a("IfcBuildingStorey")
             and storey.Name=="L1" and abs(float(storey.Elevation))<1e-8,
             "Hosted original Wall ground storey mismatched")
    body=_body(model)
    old_guids={x.GlobalId for x in model.by_type("IfcRoot")}
    _require(opening.ifc_guid not in old_guids and door.ifc_guid not in old_guids
             and opening.ifc_guid!=door.ifc_guid,
             "Original or newly assigned stable GUID collision")
    host_transform=ifcopenshell.util.placement.get_local_placement(host.ObjectPlacement)
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    baseline=ifcopenshell.geom.create_shape(settings,host)
    original_wall_volume=ifcopenshell.util.shape.get_volume(baseline.geometry)
    original_sha=snapshot_source(source_metric).source_sha256
    _require(original_sha==projection.source.source_sha256,
             "Source changed since read-only XML projection")
    def writer(path:Path)->None:
        void=ifcopenshell.api.root.create_entity(
            model,ifc_class="IfcOpeningElement",name="v0.7 trusted XML wall void")
        void.GlobalId=opening.ifc_guid
        void.PredefinedType="OPENING"
        void_profile=model.createIfcRectangleProfileDef(
            "AREA",None,None,width,OPENING_DEPTH_M)
        void_rep=ifcopenshell.api.geometry.add_profile_representation(
            model,context=body,profile=void_profile,depth=height)
        ifcopenshell.api.geometry.assign_representation(
            model,product=void,representation=void_rep)
        local=np.eye(4,dtype="float64")
        local[:3,3]=[offset,0.,sill]
        placement=host_transform@local
        ifcopenshell.api.geometry.edit_object_placement(
            model,product=void,matrix=placement)
        ifcopenshell.api.feature.add_feature(model,feature=void,element=host)
        slab=ifcopenshell.api.root.create_entity(
            model,ifc_class="IfcDoor",name="v0.7 trusted XML hosted Door")
        slab.GlobalId=door.ifc_guid
        slab.PredefinedType="DOOR"
        slab.OverallWidth=width
        slab.OverallHeight=height
        leaf_profile=model.createIfcRectangleProfileDef(
            "AREA",None,None,width,DOOR_LEAF_THICKNESS_M)
        leaf_rep=ifcopenshell.api.geometry.add_profile_representation(
            model,context=body,profile=leaf_profile,depth=height)
        ifcopenshell.api.geometry.assign_representation(
            model,product=slab,representation=leaf_rep)
        ifcopenshell.api.geometry.edit_object_placement(
            model,product=slab,matrix=placement)
        ifcopenshell.api.feature.add_filling(model,opening=void,element=slab)
        ifcopenshell.api.spatial.assign_container(
            model,products=[slab],relating_structure=storey)
        model.write(str(path))
    def validator(path:Path)->None:
        candidate=ifcopenshell.open(str(path))
        cut_wall=candidate.by_guid(HOST_GUID)
        void=candidate.by_guid(opening.ifc_guid)
        dr=candidate.by_guid(door.ifc_guid)
        _require(void.is_a("IfcOpeningElement") and dr.is_a("IfcDoor"),
                 "Compiled native Door/Opening class mismatch")
        _require(len(void.VoidsElements)==1
                 and void.VoidsElements[0].RelatingBuildingElement.GlobalId==HOST_GUID
                 and len(dr.FillsVoids)==1
                 and dr.FillsVoids[0].RelatingOpeningElement.GlobalId==opening.ifc_guid,
                 "Real void/filling IFC relationships missing")
        _require(math.isclose(float(dr.OverallHeight),height,abs_tol=1e-6)
                 and math.isclose(float(dr.OverallWidth),width,abs_tol=1e-6),
                 "Compiled native Door dimensions differ from XML")
        cut_mesh=ifcopenshell.geom.create_shape(settings,cut_wall)
        measured=original_wall_volume-ifcopenshell.util.shape.get_volume(cut_mesh.geometry)
        _require(math.isclose(measured,width*height*.2,abs_tol=1e-4),
                 "Host native wall does not have physical requested through-void")
        _metric_scene_step_preservation(
            source_metric,path,opening.ifc_guid,door.ifc_guid)
        _require(snapshot_source(source_metric).source_sha256==original_sha,
                 "Original source metric IFC changed during compiler verification")
    stage_and_commit(destination_metric,writer,validator)
    validator(destination_metric)
    return {
        "status":"SCOPED_V07_DECLARATIVE_HOSTED_DOOR_OPENING_CREATE_COMMITTED",
        "compiler_version":"experimental-hosted-door-create-v0.7",
        "original_source_sha256":original_sha,
        "created_IfcOpeningElement_guid":opening.ifc_guid,
        "created_IfcDoor_guid":door.ifc_guid,
        "public_original_host_guid":HOST_GUID,
        "typed_semantic_graph_diff_added_nodes":["Door","Opening"],
        "typed_semantic_graph_diff_added_relations":["host_void","opening_fill"],
        "complete_full_XML_submitted":True,
        "only_new_door_opening_and_void_filling_relationships":True,
        "current_matched_model_host_enabled":False,
        "original_author_scorer_called":False,
        "full_native_IFC_read_write_parity_proven":False,
    }
