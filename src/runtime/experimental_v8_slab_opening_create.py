"""Opt-in v0.8 slab-hosted Opening full-declarative-state compiler.

Never a model command surface. A trusted runtime outside the direct-markup
agent observes one new typed <Opening> hosted by a real source IfcSlab.
Old wall-only schema/binder behavior is retained by default; versioned
v0.8 XSD and binder override must be explicitly opted into here.
"""
from __future__ import annotations

from decimal import Decimal,InvalidOperation
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.api.feature
import ifcopenshell.api.geometry
import ifcopenshell.api.root
import ifcopenshell.geom
import ifcopenshell.util.shape
import ifcopenshell.util.unit
import numpy as np

from src.runtime.experimental_v4_projection import project_ifc_v4
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document
from src.runtime.semantic_graph import graph_diff
from src.runtime.transaction import stage_and_commit
from src.runtime.ifc_snapshot import snapshot_source

PUBLIC_ORIGINAL_SLAB_GUID="11kJIqz$n2Jf_DfJV1SCVP"
# This is a through-cut construction parameter, not one of the original
# horizontal 5m × 5m user-requested dimensions.
TRUSTED_VERTICAL_CUT_DEPTH_M=.5
TRUSTED_VERTICAL_MARGIN_BELOW_M=.1


class V08NativeSlabOpeningBlocked(ValueError):
    pass


def _require(condition:bool,description:str)->None:
    if not condition:
        raise V08NativeSlabOpeningBlocked(description)


def _number(a:dict,key:str)->float:
    try:
        dec=Decimal(str(a[key]))
    except (KeyError,TypeError,InvalidOperation) as exc:
        raise V08NativeSlabOpeningBlocked("Invalid numeric XML field "+key) from exc
    _require(dec.is_finite(),"Nonfinite XML slab opening field "+key)
    return float(dec)


def _original_ifc_step_and_root_preservation(original:Path,out:Path,
                                              opening_guid:str)->None:
    a=ifcopenshell.open(str(original))
    b=ifcopenshell.open(str(out))
    old={x.id():str(x) for x in a}
    now={x.id():str(x) for x in b}
    _require(set(old)<=set(now)
             and all(old[i]==now[i] for i in old),
             "Original metric native IFC STEP entities changed/removed")
    original_roots={x.GlobalId:x for x in a.by_type("IfcRoot")}
    current_roots={x.GlobalId:x for x in b.by_type("IfcRoot")}
    _require(set(original_roots)<=set(current_roots),
             "Original frozen native IFC Roots lost")
    extras=set(current_roots)-set(original_roots)
    _require(len(extras)==2 and opening_guid in extras and
             {current_roots[g].is_a() for g in extras}==
             {"IfcOpeningElement","IfcRelVoidsElement"},
             "Exactly one native Opening and its void relation may be added")
    for g,original_entity in original_roots.items():
        current=current_roots[g]
        _require(current.is_a()==original_entity.is_a()
                 and current.Name==original_entity.Name
                 and current.Description==original_entity.Description,
                 "Existing source IFC Root class/name/description changed")


def compile_declarative_xml_v08_slab_opening_create(
        source_metric:Path,full_edited_XML:bytes,out_metric:Path)->dict:
    source_metric,out_metric=Path(source_metric),Path(out_metric)
    _require(source_metric.is_file() and not source_metric.is_symlink()
             and not out_metric.exists() and not out_metric.is_symlink()
             and source_metric.resolve()!=out_metric.resolve(),
             "Original metric IFC and fresh output must be separate regular files")
    projection=project_ifc_v4(source_metric)
    original=parse_xml(projection.xml,
                       expected_source_sha256=projection.source.source_sha256)
    # The *only* opt-in path; default parser still uses Wall-only frozen schema.
    revised=parse_xml(full_edited_XML,
                      expected_source_sha256=projection.source.source_sha256,
                      schema_variant="slab_opening_v08")
    old=bind_document(original,projection=projection)
    new=bind_document(revised,projection=projection,
                      verify_native_edges=False,
                      allow_slab_opening_hosts=True)
    delta=graph_diff(old.graph,new.graph)
    _require(len(delta.added_nodes)==1 and len(delta.added_edges)==1
             and not delta.changed_nodes and not delta.removed_nodes
             and not delta.removed_edges,
             "Only one new slab-hosted Opening state diff allowed")
    node=new.graph.by_id()[delta.added_nodes[0]]
    edge=delta.added_edges[0]
    _require(node.kind=="Opening" and node.provenance=="deterministic_new"
             and edge.relation=="host_void" and edge.target==node.id,
             "New object must be an actual slab-hosted Opening/host_void graph pair")
    attrs=dict(node.attributes)
    host=new.graph.by_id().get(attrs.get("host"))
    _require(host is not None and host.id==edge.source
             and host.kind=="Slab" and host.provenance=="existing_source"
             and host.ifc_guid==PUBLIC_ORIGINAL_SLAB_GUID,
             "Slab Opening may only host the original public source IfcSlab")
    offset=_number(attrs,"offset")
    y_displacement=_number(attrs,"sill")
    xspan=_number(attrs,"width")
    yspan=_number(attrs,"height")
    _require(0<=offset<=20 and 0<=y_displacement<=20
             and 0.01<xspan<=10 and 0.01<yspan<=10,
             "Unsafe slab opening parameter range")
    model=ifcopenshell.open(str(source_metric))
    _require(model.schema=="IFC4X3" and
             abs(ifcopenshell.util.unit.calculate_unit_scale(model)-1.)<1e-9,
             "Only original IFC4X3 metre-converted trusted source supported")
    slab=model.by_guid(PUBLIC_ORIGINAL_SLAB_GUID)
    _require(slab.is_a("IfcSlab") and slab.PredefinedType=="FLOOR"
             and not slab.HasOpenings,
             "Original public IfcSlab altered, wrong type, or already opened")
    context=[r for r in model.by_type("IfcGeometricRepresentationSubContext")
             if r.ContextIdentifier=="Body" and r.TargetView=="MODEL_VIEW"]
    _require(len(context)==1,"Original native IFC Body MODEL_VIEW context missing")
    original_guids={r.GlobalId for r in model.by_type("IfcRoot")}
    _require(node.ifc_guid not in original_guids,
             "New stable Opening GUID collides with native source")
    s=ifcopenshell.geom.settings()
    s.set(s.USE_WORLD_COORDS,True)
    original_shape=ifcopenshell.geom.create_shape(s,slab)
    before=float(ifcopenshell.util.shape.get_volume(original_shape.geometry))
    slab_verts=np.asarray(original_shape.geometry.verts,dtype=float).reshape(-1,3)
    lower=slab_verts.min(axis=0)
    upper=slab_verts.max(axis=0)
    _require(np.allclose(upper-lower,[10.4,10.375,.3],atol=1e-5,rtol=0)
             and abs(before-32.37)<1e-5,
             "Original source Slab actual physical slab extent differs")
    slaba=dict(host.attributes)
    _require(np.allclose(
                 [float(slaba[c]) for c in ("x","y","z","width","depth","thickness")],
                 [*lower[:3],*(upper-lower)],atol=1e-5,rtol=0),
             "Projected slab XML bounding geometry not native source mesh")
    center=(float(lower[0])+offset+xspan/2,
            float(lower[1])+y_displacement+yspan/2,
            float(lower[2])-TRUSTED_VERTICAL_MARGIN_BELOW_M)
    _require(center[0]-xspan/2>lower[0]+1e-6 and
             center[0]+xspan/2<upper[0]-1e-6 and
             center[1]-yspan/2>lower[1]+1e-6 and
             center[1]+yspan/2<upper[1]-1e-6,
             "New physical slab Opening must be internal to original footprint")
    _require(TRUSTED_VERTICAL_CUT_DEPTH_M>
             float(upper[2]-lower[2])+TRUSTED_VERTICAL_MARGIN_BELOW_M,
             "Physical vertical void must traverse original slab")
    old_digest=snapshot_source(source_metric).source_sha256
    _require(old_digest==projection.source.source_sha256,
             "Original source edited between full XML projection and trusted compilation")
    def writer(stage:Path)->None:
        opening=ifcopenshell.api.root.create_entity(
            model,ifc_class="IfcOpeningElement",name="v0.8 full XML Slab Opening")
        opening.GlobalId=node.ifc_guid
        opening.PredefinedType="OPENING"
        profile=model.createIfcRectangleProfileDef(
            "AREA",None,None,xspan,yspan)
        rep=ifcopenshell.api.geometry.add_profile_representation(
            model,context=context[0],profile=profile,depth=TRUSTED_VERTICAL_CUT_DEPTH_M)
        ifcopenshell.api.geometry.assign_representation(
            model,product=opening,representation=rep)
        transform=np.eye(4,dtype=float)
        transform[:3,3]=center
        ifcopenshell.api.geometry.edit_object_placement(
            model,product=opening,matrix=transform)
        ifcopenshell.api.feature.add_feature(
            model,feature=opening,element=slab)
        model.write(str(stage))
    def validator(stage:Path)->None:
        persisted=ifcopenshell.open(str(stage))
        opening=persisted.by_guid(node.ifc_guid)
        hosted=persisted.by_guid(PUBLIC_ORIGINAL_SLAB_GUID)
        _require(opening.is_a("IfcOpeningElement") and
                 len(opening.VoidsElements)==1 and
                 opening.VoidsElements[0].RelatingBuildingElement.GlobalId==
                 PUBLIC_ORIGINAL_SLAB_GUID and
                 len(hosted.HasOpenings)==1,
                 "Committed native Slab/Opening void relation absent")
        actual=ifcopenshell.geom.create_shape(s,hosted)
        removed=before-float(ifcopenshell.util.shape.get_volume(actual.geometry))
        expected=xspan*yspan*float(upper[2]-lower[2])
        _require(math.isclose(removed,expected,abs_tol=1e-5,rel_tol=0),
                 "Physical original Slab volume not cut by requested planar Opening")
        opening_shape=ifcopenshell.geom.create_shape(s,opening)
        verts=np.asarray(opening_shape.geometry.verts,dtype=float).reshape(-1,3)
        low,high=verts.min(axis=0),verts.max(axis=0)
        _require(np.allclose(
                     (*low,*high),(
                         center[0]-xspan/2,center[1]-yspan/2,center[2],
                         center[0]+xspan/2,center[1]+yspan/2,
                         center[2]+TRUSTED_VERTICAL_CUT_DEPTH_M),
                     atol=1e-5,rtol=0),
                 "Native opening world geometry does not match declarative footprint")
        _original_ifc_step_and_root_preservation(source_metric,stage,node.ifc_guid)
        _require(snapshot_source(source_metric).source_sha256==old_digest,
                 "Immutable source IFC bytes changed during trusted D0 compiler")
    stage_and_commit(out_metric,writer,validator)
    validator(out_metric)
    return {
        "status":"V08_SCOPED_FULL_XML_SLAB_OPENING_COMMITTED",
        "native_compiler_version":"experimental-slab-hosted-opening-v0.8",
        "schema_variant":"slab_opening_v08",
        "previous_default_wall_only_schema_and_binder_retained":True,
        "source_metric_sha256":old_digest,
        "public_host_native_IfcSlab_GUID":PUBLIC_ORIGINAL_SLAB_GUID,
        "created_IfcOpeningElement_GUID":node.ifc_guid,
        "whole_XML_state_semantic_added_nodes":["Opening"],
        "whole_XML_state_semantic_added_edges":["host_void"],
        "whole_XML_node_host_kind":"Slab",
        "native_opening_horizontal_XY_dimensions_m":[xspan,yspan],
        "native_opening_footprint_min_offset_from_slab_m":[offset,y_displacement],
        "trusted_native_vertical_through_cut_depth_m":TRUSTED_VERTICAL_CUT_DEPTH_M,
        "matched_model_host_enabled":False,
        "original_author_scorer_invoked":False,
        "full_source_information_parity_proven":False,
    }
