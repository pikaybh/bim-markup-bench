"""Prospective experimental v0.9 native IFC4X3 complex geometry compiler.

A model author edits ONLY the complete source-pinned declarative XML state.
This TRUSTED backend infers native edits; no model-facing IfcOpenShell API or
imperative Create/Move/Delete XML opcodes.

Supported narrowly: original rotated-profile Slab square reshape, exactly
two original Columns sharing one native IfcMappedItem extrusion type depth,
or one new source-BooleanClipping-Wall hosted Opening + Door pair.

Original native IFC STEP graph, unrelated geometry, spatial/connection
relations and actual source file are strictly preserved or fail closed.
"""
from __future__ import annotations

from pathlib import Path
import math
import uuid

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.api.geometry
import ifcopenshell.api.feature
import ifcopenshell.api.spatial
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.shape
import ifcopenshell.util.unit
import numpy as np

from src.runtime.compiler import CompileReport
from src.runtime.ifc_mutations import Mutation
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.transaction import stage_and_commit
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document
from src.runtime.semantic_graph import graph_diff
from src.runtime.experimental_v9_projection import (
    project_ifc_v9,_boolean_wall_attrs,ComplexV9ProjectionError,
)
from src.runtime.experimental_v7_projection import _mesh_exact_axis_box

EPS=2e-5


class ComplexV9Error(ValueError):
    pass


class ComplexV9CompileReport(CompileReport):
    def as_dict(self):
        result=super().as_dict()
        result.update({
            "status":"COMMITTED_SOURCE_IFC4X3_"+self.operations[0].operation+"_V09",
            "compiler_version":"experimental-complex-v0.9",
            "source_original_native_ifc_opaque_geometry_retained":True,
            "backend_original_45_task_full_parity":False,
            "new_provider_model_calls":0,
        })
        return result


def _numeric(a,key):
    try:
        v=float(a[key])
    except (KeyError,TypeError,ValueError,OverflowError) as exc:
        raise ComplexV9Error("Missing numeric native attribute: "+key) from exc
    if not math.isfinite(v) or abs(v)>10000:
        raise ComplexV9Error("Nonfinite/out-of-range native geometry: "+key)
    return v


def _world_geometry(product):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        shape=ifcopenshell.geom.create_shape(settings,product)
        p=np.asarray(shape.geometry.verts,dtype=float).reshape(-1,3)
        triangles=np.asarray(shape.geometry.faces,dtype=int).reshape(-1,3)
        vol=float(ifcopenshell.util.shape.get_volume(shape.geometry))
    except Exception as exc:
        raise ComplexV9Error("Native IFC physical world mesh unavailable") from exc
    if len(p)<4 or len(triangles)<4 or not np.all(np.isfinite(p)):
        raise ComplexV9Error("Invalid native geometry")
    return p,triangles,vol


def _bool_host_plan(source,f,original,added,new):
    op_id=next(n for n in added if new[n].kind=="Opening")
    door_id=next(n for n in added if new[n].kind=="Door")
    opener=new[op_id];door=new[door_id]
    op=dict(opener.attributes);da=dict(door.attributes)
    if da["opening"]!=op_id:
        raise ComplexV9Error("Exactly one Door must fill its own new Opening")
    host_id=op["host"]
    host_node=original.get(host_id)
    if host_node is None or host_node.kind!="Wall" or host_node.provenance!="existing_source":
        raise ComplexV9Error("New Opening must attach to an existing original Boolean Wall")
    host=f.by_guid(host_node.ifc_guid)
    if not host.is_a("IfcWall"):
        raise ComplexV9Error("Original IFC4X3 host must be physical IfcWall")
    if any(rel.is_a("IfcRelVoidsElement") or rel.is_a("IfcRelSpaceBoundary")
           for rel in f.get_inverse(host)):
        raise ComplexV9Error("Already voided or space-bounded Wall unsupported")
    # Independently reopen native source geometry shape & source ownership.
    frame=_boolean_wall_attrs(f,host,dict(host_node.attributes)["level"])
    if any(frame[k]!=v for k,v in dict(host_node.attributes).items()):
        raise ComplexV9Error("Original Boolean Wall declarative state not equal native mesh")
    bounds=dict(host_node.attributes)
    p1=np.array([_numeric(bounds,k) for k in ("x1","y1","z1")])
    p2=np.array([_numeric(bounds,k) for k in ("x2","y2","z2")])
    axis=p2-p1
    total=float(np.linalg.norm(axis[:2]))
    if total<.5 or abs(axis[1])>EPS or axis[0]<=0 or abs(axis[2])>EPS:
        raise ComplexV9Error("Only source world positive-X original Boolean Wall host")
    offset=_numeric(op,"offset")
    sill=_numeric(op,"sill")
    w=_numeric(op,"width")
    h=_numeric(op,"height")
    thick=_numeric(bounds,"thickness")
    if (not .5<=w<=2.5 or not 1.5<=h<=2.5 or
        not .05<=thick<=.5 or not 0<=sill<=1.
        or not .5<offset<total-w-.5
        or sill+h>_numeric(bounds,"height")-.1):
        raise ComplexV9Error("New physical hosted Door opening outside original Wall safe interior")
    if (abs(_numeric(da,"width")-w)>EPS
        or abs(_numeric(da,"height")-h)>EPS):
        raise ComplexV9Error("New IFC Door and Opening native widths/heights disagree")
    native_storey=ifcopenshell.util.element.get_container(host)
    if native_storey is None or native_storey.is_a()!="IfcBuildingStorey":
        raise ComplexV9Error("Original Boolean wall has no single native Storey")
    if any(x.is_a("IfcRelConnectsPathElements") and x.ConnectionGeometry is not None
           for x in f.get_inverse(host)):
        raise ComplexV9Error("Connected source Wall has geometry-dependent Path connection")
    # The original unclipped source wall is a complete physical box; do NOT
    # regenerate the BooleanClippingResult or drop native connections.
    low,high=_mesh_exact_axis_box(host)
    center=(p1+p2)/2.
    center[0]=p1[0]+offset+w/2
    center[2]=p1[2]+sill
    if not (low[0]+.5<center[0]-w/2 and center[0]+w/2<high[0]-.5):
        raise ComplexV9Error("Opening not within true clipped source physical host bounds")
    return {
        "op":"CREATE_BOOLEAN_CLIPPING_HOSTED_DOOR",
        "ids":(op_id,door_id),
        "guids":(opener.ifc_guid,door.ifc_guid),
        "host_guid":host.GlobalId,
        "host_wall_volume":_world_geometry(host)[2],
        "center":tuple(float(x) for x in center),
        "width":w,"height":h,"thickness":thick,"sill":sill,
        "storey_guid":native_storey.GlobalId,
        "protected original_non_target_classes":"IfcRelConnectsPathElements,IfcBooleanClippingResult",
    }


def _slab_plan(f,old,new):
    src=dict(old.attributes);dst=dict(new.attributes)
    changed={k for k in src if src[k]!=dst[k]}
    if changed!={"depth"}:
        raise ComplexV9Error("v0.9 locally rotated Slab only changes world depth dimension")
    if (abs(_numeric(dst,"depth")-_numeric(src,"width"))>EPS
        or _numeric(dst,"depth")<=_numeric(src,"depth")+.01):
        raise ComplexV9Error("Only widening shorter original Slab side to an exact square")
    slab=f.by_guid(old.ifc_guid)
    if not slab.is_a("IfcSlab"):
        raise ComplexV9Error("Original source GlobalId is not a native Slab")
    if slab.Representation is None:
        raise ComplexV9Error("Native original Slab lacks representation")
    reps=[i for r in slab.Representation.Representations for i in r.Items]
    if len(reps)!=1 or not reps[0].is_a("IfcExtrudedAreaSolid"):
        raise ComplexV9Error("Only native direct single extrusion Slab supported")
    solid=reps[0]
    profile=solid.SweptArea
    if (not profile.is_a("IfcRectangleProfileDef")
        or profile.Position is None
        or not profile.Position.is_a("IfcAxis2Placement2D")
        or solid.Position is None):
        raise ComplexV9Error("Unsupported native rotated local rectangular profile")
    point=profile.Position.Location
    if (point is None or not point.is_a("IfcCartesianPoint")
        or len(point.Coordinates)!=2
        or len(f.get_inverse(profile))!=1
        or len(f.get_inverse(profile.Position))!=1
        or len(f.get_inverse(point))!=1):
        raise ComplexV9Error("Shared or invalid original local Slab profile position")
    if (slab.ObjectPlacement is None
        or len(f.get_inverse(solid))>2):
        raise ComplexV9Error("Original Slab extrusion ownership ambiguous")
    orig_lo,orig_hi=_mesh_exact_axis_box(slab)
    old_ext=np.asarray(orig_hi)-np.asarray(orig_lo)
    if (abs(old_ext[0]-_numeric(src,"width"))>EPS
        or abs(old_ext[1]-_numeric(src,"depth"))>EPS
        or abs(old_ext[2]-_numeric(src,"thickness"))>EPS
        or not np.allclose(orig_lo,[_numeric(src,k) for k in ("x","y","z")],atol=EPS)):
        raise ComplexV9Error("Native original Slab world box does not match source XML")
    # Project the native extrusion's rectangle-local +X axis into world XY
    # using both source ObjectPlacement and solid extrusion Position.
    m=np.asarray(ifcopenshell.util.placement.get_local_placement(slab.ObjectPlacement))
    q=np.asarray(ifcopenshell.util.placement.get_axis2placement(solid.Position))
    direction=m[:3,:3]@q[:3,0]
    if not np.allclose(direction,(0,1,0),atol=1e-7):
        raise ComplexV9Error("Original Slab's local rectangle axis does not map to positive world Y")
    if not math.isclose(float(profile.XDim),old_ext[1],abs_tol=EPS):
        raise ComplexV9Error("Original world depth is not local profile XDim")
    if not math.isclose(float(profile.YDim),old_ext[0],abs_tol=EPS):
        raise ComplexV9Error("Original world width is not local profile YDim")
    delta=_numeric(dst,"depth")-_numeric(src,"depth")
    return {
        "op":"RESHAPE_LOCAL_ROTATED_SLAB_SQUARE",
        "ids":(old.id,),
        "guids":(old.ifc_guid,),
        "profile_step_id":profile.id(),
        "profile_point_step_id":point.id(),
        "profile_XDim":float(profile.XDim)+delta,
        "profile_X_center_shift":delta/2,
        "native_original_lo":tuple(orig_lo),
        "native_new_hi":tuple([orig_hi[0],orig_hi[1]+delta,orig_hi[2]]),
    }


def _mapped_column_plan(f,source_nodes,edited_nodes):
    if len(source_nodes)!=2 or len(edited_nodes)!=2:
        raise ComplexV9Error("Shared native Column update must change exactly original two Columns")
    all_columns=f.by_type("IfcColumn")
    expected={n.ifc_guid for n in source_nodes}
    if {x.GlobalId for x in all_columns}!=expected:
        raise ComplexV9Error("Unrelated original IFC Columns may share a native mapped type")
    depths=[]
    maps=[]
    solids=[]
    for node,new in zip(source_nodes,edited_nodes):
        a=dict(node.attributes);b=dict(new.attributes)
        if {k for k in a if a[k]!=b[k]}!={"height"}:
            raise ComplexV9Error("Only both original Column height values may change")
        original_height=_numeric(a,"height");target=_numeric(b,"height")
        if not 1.0<original_height<target<=10 or abs(target-original_height)>.2+1.5:
            raise ComplexV9Error("Mapped Column height change out of bounded source range")
        obj=f.by_guid(node.ifc_guid)
        if (not obj.is_a("IfcColumn") or obj.Representation is None
            or len(obj.Representation.Representations)!=1):
            raise ComplexV9Error("Unsupported original Column mapping")
        items=obj.Representation.Representations[0].Items
        if len(items)!=1 or not items[0].is_a("IfcMappedItem"):
            raise ComplexV9Error("Original shared native Column is not IfcMappedItem")
        m=items[0].MappingSource
        reps=m.MappedRepresentation.Items
        if len(reps)!=1 or not reps[0].is_a("IfcExtrudedAreaSolid"):
            raise ComplexV9Error("Original mapped geometry is not one shared extrusion")
        solids.append(reps[0])
        maps.append(m)
        depths.append((original_height,target))
        low,high=_mesh_exact_axis_box(obj)
        if abs(high[2]-low[2]-original_height)>EPS:
            raise ComplexV9Error("Native mapped source Column height differs from XML")
        if abs(low[2])>EPS:
            raise ComplexV9Error("This limited shared Column height edit requires original ground Z=0")
    if maps[0].id()!=maps[1].id() or solids[0].id()!=solids[1].id():
        raise ComplexV9Error("Original Columns do not share identical native extrusion")
    if len({x for x in depths})!=1:
        raise ComplexV9Error("All Columns sharing native type must have same old/new height")
    solid=solids[0]
    if abs(float(solid.Depth)-depths[0][0])>EPS:
        raise ComplexV9Error("Original native mapped extrusion Depth differs from original Columns")
    users={x.GlobalId for x in f.by_type("IfcColumn")
           if any(it.is_a("IfcMappedItem") and it.MappingSource.id()==maps[0].id()
                  for rep in x.Representation.Representations for it in rep.Items)}
    if users!=expected:
        raise ComplexV9Error("Original mapped extrusion shared by unexpected additional IFc Product")
    # Target must touch the original directly adjacent next upper Slab;
    # 4.8mm original author Revit floor offset tolerated, never pretend
    # the true physical slab bottom is exactly an integer metre.
    slabs=f.by_type("IfcSlab")
    above=[]
    for slab in slabs:
        low,high=_mesh_exact_axis_box(slab)
        if low[2]>depths[0][0]:
            above.append(float(low[2]))
    if not above:
        raise ComplexV9Error("No original source upper Slab to contact")
    closest=min(above)
    target_height=depths[0][1]
    if abs(target_height-closest)>.01:
        raise ComplexV9Error("Column target height does not touch upper Slab within original 1cm tolerance")
    return {
        "op":"UPDATE_SHARED_NATIVE_MAPPED_COLUMNS_HEIGHT",
        "ids":tuple(n.id for n in source_nodes),
        "guids":tuple(n.ifc_guid for n in source_nodes),
        "solid_step_id":solid.id(),
        "height_old":depths[0][0],
        "height_new":target_height,
        "upper_original_slab_bottom_world_m":closest,
        "users_of_same_mapping":tuple(sorted(users)),
    }


def _dedupe_new_roots_and_history(f,source_sha,old_root_guids,old_owner_history_ids):
    for cls in ("IfcRelFillsElement","IfcRelVoidsElement",
                "IfcRelContainedInSpatialStructure"):
        made=sorted((x for x in f.by_type(cls) if x.GlobalId not in old_root_guids),
                    key=lambda x:x.id())
        for idx,x in enumerate(made):
            guid=ifcopenshell.guid.compress(uuid.uuid5(
                uuid.NAMESPACE_URL,
                "bim-markup-bench-native-complex-v09:"+source_sha+":"+cls+":"+str(idx)
            ).hex)
            if guid in {y.GlobalId for y in f.by_type("IfcRoot")}:
                raise ComplexV9Error("New native IFC relationship GUID collision")
            x.GlobalId=guid
    histories=[x for x in f.by_type("IfcOwnerHistory")
               if x.id() not in old_owner_history_ids]
    if histories:
        native=[x for x in f.by_type("IfcOwnerHistory")
                if x.id() in old_owner_history_ids]
        if not native or any(x.CreationDate is None for x in native):
            raise ComplexV9Error("Cannot establish deterministic provenance without source OwnerHistory")
        fixed=max(int(x.CreationDate) for x in native)
        for x in histories:
            x.CreationDate=fixed
            if x.LastModifiedDate is not None:
                x.LastModifiedDate=fixed


def _new_rect(f,width,depth):
    return f.createIfcRectangleProfileDef("AREA",None,None,width,depth)


def _body_context(f):
    matches=[r for r in f.by_type("IfcGeometricRepresentationSubContext")
             if r.ContextIdentifier=="Body" and r.TargetView=="MODEL_VIEW"]
    if len(matches)!=1:
        raise ComplexV9Error("Original IFC4X3 source lacks unique native Body MODEL_VIEW")
    return matches[0]


def _make_door(f,plan,original_containment,old_root_guids,old_history_ids,source_sha):
    body=_body_context(f)
    o_id,d_id=plan["ids"]
    o_guid,d_guid=plan["guids"]
    opening=ifcopenshell.api.root.create_entity(
        f,ifc_class="IfcOpeningElement",name="Experimental source-Boolean IFC void v0.9")
    opening.GlobalId=o_guid
    w=plan["width"];h=plan["height"]
    profile=_new_rect(f,w,plan["thickness"]+.3)
    rep=ifcopenshell.api.geometry.add_profile_representation(
        f,context=body,profile=profile,depth=h)
    ifcopenshell.api.geometry.assign_representation(
        f,product=opening,representation=rep)
    m=np.eye(4);m[:3,3]=plan["center"]
    ifcopenshell.api.geometry.edit_object_placement(
        f,product=opening,matrix=m)
    host=f.by_guid(plan["host_guid"])
    ifcopenshell.api.feature.add_feature(f,feature=opening,element=host)
    door=ifcopenshell.api.root.create_entity(
        f,ifc_class="IfcDoor",name="Experimental native Boolean host Door v0.9")
    door.GlobalId=d_guid
    door.OverallWidth=w;door.OverallHeight=h
    profile=_new_rect(f,w,.08)
    rep=ifcopenshell.api.geometry.add_profile_representation(
        f,context=body,profile=profile,depth=h)
    ifcopenshell.api.geometry.assign_representation(f,product=door,representation=rep)
    ifcopenshell.api.geometry.edit_object_placement(f,product=door,matrix=m)
    ifcopenshell.api.feature.add_filling(f,opening=opening,element=door)
    ifcopenshell.api.spatial.assign_container(
        f,products=[door],relating_structure=f.by_guid(plan["storey_guid"]))
    changed=0
    for guid,members in original_containment.items():
        rel=f.by_guid(guid)
        current={x.GlobalId for x in rel.RelatedElements}
        old=set(members)
        diff=current-old
        if current not in (old,old|{d_guid}):
            raise ComplexV9Error("New native Door changed source original containment unexpectedly")
        if diff:
            changed+=1
        rel.RelatedElements=tuple(f.by_guid(x) for x in (*members,*sorted(diff)))
    if changed!=1:
        raise ComplexV9Error("New Door must extend exactly one native original Storey relation")
    _dedupe_new_roots_and_history(f,source_sha,old_root_guids,old_history_ids)


def _assert_candidate_native(source,result,plan):
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(result))
    if a.schema!="IFC4X3" or b.schema!=a.schema:
        raise ComplexV9Error("Native IFC4X3 source/candidate schema mismatch")
    oldstep={x.id():str(x) for x in a}
    newstep={x.id():str(x) for x in b}
    if not set(oldstep)<=set(newstep):
        raise ComplexV9Error("Original IFC4X3 source STEP entity was removed")
    changed={i for i in oldstep if oldstep[i]!=newstep[i]}
    oldroot={x.GlobalId:x for x in a.by_type("IfcRoot")}
    newroot={x.GlobalId:x for x in b.by_type("IfcRoot")}
    oldproducts={x.GlobalId:x for x in a.by_type("IfcProduct")}
    newproducts={x.GlobalId:x for x in b.by_type("IfcProduct")}
    if plan["op"]=="RESHAPE_LOCAL_ROTATED_SLAB_SQUARE":
        if changed!={plan["profile_step_id"],plan["profile_point_step_id"]} or set(oldstep)!=set(newstep):
            raise ComplexV9Error("Rotated Slab reshaping unexpectedly changed other source STEP objects")
        if set(oldroot)!=set(newroot):
            raise ComplexV9Error("Slab geometry edit changed original IFC Roots")
        slab=b.by_guid(plan["guids"][0])
        low,high=_mesh_exact_axis_box(slab)
        if not np.allclose(low,plan["native_original_lo"],atol=EPS):
            raise ComplexV9Error("Native Slab reshape did not preserve its lower world corner")
        if not np.allclose(high,plan["native_new_hi"],atol=EPS):
            raise ComplexV9Error("Native Slab locally rotated profile did not form exact world square")
        targets=set(plan["guids"])
    elif plan["op"]=="UPDATE_SHARED_NATIVE_MAPPED_COLUMNS_HEIGHT":
        if changed!={plan["solid_step_id"]} or set(oldstep)!=set(newstep):
            raise ComplexV9Error("Shared native Column edit modified unrelated STEP")
        if set(oldroot)!=set(newroot):
            raise ComplexV9Error("Mapped Column geometry edit changed original Roots")
        for guid in plan["guids"]:
            src=a.by_guid(guid);dst=b.by_guid(guid)
            l0,h0=_mesh_exact_axis_box(src)
            l1,h1=_mesh_exact_axis_box(dst)
            if (not np.allclose(l0,l1,atol=EPS)
                or abs(h1[2]-l1[2]-plan["height_new"])>EPS
                or not np.allclose(np.asarray(h1)[:2],np.asarray(h0)[:2],atol=EPS)):
                raise ComplexV9Error("Native shared Column world height update incorrect")
        targets=set(plan["guids"])
    else:
        allowed={r.id() for r in a.by_type("IfcRelContainedInSpatialStructure")}
        if not changed<=allowed:
            raise ComplexV9Error("New native hosted Door changed original non-containment STEP entities")
        if not set(oldroot)<=set(newroot):
            raise ComplexV9Error("New hosted Door removed original IFC Roots")
        if not set(oldproducts)|set(plan["guids"])==set(newproducts):
            raise ComplexV9Error("New hosted Door created unexpected native products")
        op=b.by_guid(plan["guids"][0]);door=b.by_guid(plan["guids"][1])
        if (not op.is_a("IfcOpeningElement") or not door.is_a("IfcDoor")
            or len(op.VoidsElements)!=1 or len(door.FillsVoids)!=1
            or op.VoidsElements[0].RelatingBuildingElement.GlobalId!=plan["host_guid"]
            or door.FillsVoids[0].RelatingOpeningElement.GlobalId!=op.GlobalId):
            raise ComplexV9Error("Actual IFC4X3 native Wall void and Door filling graph missing")
        host0=a.by_guid(plan["host_guid"]);host1=b.by_guid(plan["host_guid"])
        p0,t0,v0=_world_geometry(host0)
        p1,t1,v1=_world_geometry(host1)
        if (len(t1)<=len(t0)
            or not np.allclose(p0.min(0),p1.min(0),atol=EPS)
            or not np.allclose(p0.max(0),p1.max(0),atol=EPS)
            or not math.isclose(v0-v1,plan["width"]*plan["height"]*plan["thickness"],
                                rel_tol=0,abs_tol=2e-4)):
            raise ComplexV9Error("Original BooleanClipping Wall did not gain exactly real Door void")
        if host1.Representation.Representations[-1].RepresentationType!="Clipping":
            raise ComplexV9Error("Original native clipped host geometry was replaced")
        if ifcopenshell.util.element.get_container(door).GlobalId!=plan["storey_guid"]:
            raise ComplexV9Error("New original hosted Door not in original source Storey")
        targets={plan["host_guid"]}
    for guid,obj in oldroot.items():
        if obj.is_a()!=newroot[guid].is_a():
            raise ComplexV9Error("Original IFC Root class changed")
        if str(obj)!=str(newroot[guid]):
            if plan["op"]!="CREATE_BOOLEAN_CLIPPING_HOSTED_DOOR" or not obj.is_a("IfcRelContainedInSpatialStructure"):
                raise ComplexV9Error("Original IFC Root metadata changed unexpectedly")
            source_members={x.GlobalId for x in obj.RelatedElements}
            after_members={x.GlobalId for x in newroot[guid].RelatedElements}
            if (not source_members<=after_members
                or len(after_members-source_members)!=1
                or after_members-source_members!={plan["guids"][1]}):
                raise ComplexV9Error("Original shared Storey relation damaged")
    for guid,obj in oldproducts.items():
        if guid in targets or obj.Representation is None:
            continue
        p,t,_=_world_geometry(obj)
        pp,tt,_=_world_geometry(newproducts[guid])
        if len(t)!=len(tt) or p.shape!=pp.shape or not np.allclose(p,pp,atol=EPS,rtol=0):
            raise ComplexV9Error("Original unrelated source IFC physical world mesh altered")
    return len(oldproducts)-len(targets)


def compile_declarative_xml_v9(source:Path,edited_xml:bytes,destination:Path):
    if (not source.is_file() or source.is_symlink() or
        destination.exists() or destination.is_symlink() or
        source.resolve()==destination.resolve()):
        raise ComplexV9Error("Original native IFC required; output destination must be unused")
    proj=project_ifc_v9(source)
    source_sha=proj.source.source_sha256
    before_doc=parse_xml(proj.xml,expected_source_sha256=source_sha)
    after_doc=parse_xml(edited_xml,expected_source_sha256=source_sha)
    before=bind_document(before_doc,projection=proj)
    after=bind_document(after_doc,projection=proj,verify_native_edges=False)
    diff=graph_diff(before.graph,after.graph)
    a=before.graph.by_id();b=after.graph.by_id()
    f=ifcopenshell.open(str(source))
    if f.schema!="IFC4X3" or abs(ifcopenshell.util.unit.calculate_unit_scale(f)-1.)>1e-8:
        raise ComplexV9Error("Experimental v0.9 source must be metre-normalized native IFC4X3")
    old_roots={x.GlobalId for x in f.by_type("IfcRoot")}
    old_hist={x.id() for x in f.by_type("IfcOwnerHistory")}
    if (diff.removed_nodes or diff.removed_edges or
        (diff.added_nodes and diff.changed_nodes)):
        raise ComplexV9Error("No native source deletions or combined create/edit transactions")
    if diff.added_nodes:
        new=tuple(b[name] for name in diff.added_nodes)
        if (len(new)!=2 or {x.kind for x in new}!={"Opening","Door"}
            or len(diff.added_edges)!=2):
            raise ComplexV9Error("Only exactly one new Door+Opening hosted pair")
        plan=_bool_host_plan(source,f,a,diff.added_nodes,b)
        allowed={("host_void",plan["ids"][0]),("opening_fill",plan["ids"][1])}
        if {(edge.relation,edge.target) for edge in diff.added_edges}!=allowed:
            raise ComplexV9Error("New hosted Door must have exact source host and fill edges")
        original_containment={
            rel.GlobalId:tuple(x.GlobalId for x in rel.RelatedElements)
            for rel in f.by_type("IfcRelContainedInSpatialStructure")
        }
        if not original_containment:
            raise ComplexV9Error("No original Storey containment relation")
    elif diff.changed_nodes and not diff.added_edges:
        changed=[a[x] for x in diff.changed_nodes]
        next_nodes=[b[x] for x in diff.changed_nodes]
        if len(changed)==1 and changed[0].kind=="Slab":
            plan=_slab_plan(f,changed[0],next_nodes[0])
        elif len(changed)==2 and all(x.kind=="Column" for x in changed):
            plan=_mapped_column_plan(f,changed,next_nodes)
        else:
            raise ComplexV9Error("Only one original Slab square or all two shared Columns height updates")
    else:
        raise ComplexV9Error("Exactly one supported declarative semantic change required")
    if snapshot_source(source).source_sha256!=source_sha:
        raise ComplexV9Error("Original IFC source mutated while planning native transaction")

    def writer(path):
        if plan["op"]=="RESHAPE_LOCAL_ROTATED_SLAB_SQUARE":
            profile=f.by_id(plan["profile_step_id"])
            center=f.by_id(plan["profile_point_step_id"])
            profile.XDim=plan["profile_XDim"]
            c=list(center.Coordinates)
            c[0]+=plan["profile_X_center_shift"]
            center.Coordinates=tuple(c)
        elif plan["op"]=="UPDATE_SHARED_NATIVE_MAPPED_COLUMNS_HEIGHT":
            solid=f.by_id(plan["solid_step_id"])
            solid.Depth=plan["height_new"]
        elif plan["op"]=="CREATE_BOOLEAN_CLIPPING_HOSTED_DOOR":
            _make_door(f,plan,original_containment,old_roots,old_hist,source_sha)
        else:
            raise ComplexV9Error("Unsupported native v0.9 internal plan")
        f.write(str(path))

    def validate(path):
        if snapshot_source(source).source_sha256!=source_sha:
            raise ComplexV9Error("Original IFC mutated while writing candidate")
        _assert_candidate_native(source,path,plan)

    stage_and_commit(destination,writer,validate)
    if snapshot_source(source).source_sha256!=source_sha:
        raise ComplexV9Error("Original source IFC changed after native transaction")
    unchanged=_assert_candidate_native(source,destination,plan)
    frozen=snapshot_source(destination)
    mutation=Mutation(
        plan["op"],plan["ids"][0],plan["guids"][0],1,
        ("native_geometry","original_IFC_opaque_source") if len(plan["ids"])==1
        else ("host_void","opening_fill","native_geometry"),
        "prospective native IFC4X3 complex-only partial source operation",
    )
    return ComplexV9CompileReport(
        source_sha,frozen.source_sha256,
        proj.source.graph_fingerprint,frozen.graph_fingerprint,
        (mutation,),unchanged,(),destination,True)
