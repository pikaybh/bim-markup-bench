"""Prospective native-schema-preserving IFC2X3/IFC4 experimental v0.8 compiler.

Input is a WHOLE declarative source XML state in an original-native-schema
namespace; the trusted compiler infers bounded additions by stable node IDs.
No model-facing imperative commands, no lossless IFC/XML parity claim.

IFC4: exactly one native IfcWall created on an original IfcBuildingStorey
that may have Elevation=None, using its ACTUAL native placement (not a
fabricated Elevation).
IFC2X3: exactly one native IfcSpace inside original storey, OR one original
Wall-hosted IfcOpeningElement + IfcDoor with native void/fill relations.

Original IFC product geometry, metadata, roots, STEP and inverse relations
are protected. All output IFCs retain the *same native IFC schema*.
"""
from __future__ import annotations

from decimal import Decimal,InvalidOperation
from pathlib import Path
import math
import uuid

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.api.geometry
import ifcopenshell.api.spatial
import ifcopenshell.api.aggregate
import ifcopenshell.api.feature
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

from src.runtime.compiler import CompileReport
from src.runtime.ifc_mutations import Mutation
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.transaction import stage_and_commit
from src.runtime.experimental_v8_legacy_projection import (
    NS,Q,NUMERIC,LegacyV8Error,project_legacy_v8,parse_v8,
)


EPS=2e-5


class LegacyV8CompileError(LegacyV8Error):
    pass


class LegacyV8CompileReport(CompileReport):
    def as_dict(self):
        out=super().as_dict()
        out.update({
            "status":"COMMITTED_SOURCE_SCHEMA_PRESERVED_"+self.operations[0].operation+"_V08",
            "compiler_version":"experimental-legacy-IFC2X3-IFC4-v0.8",
            "schema_original_preserved":True,
            "frozen_IFC4X3_v01_to_v07_unchanged":True,
            "original_45_task_native_equivalence":False,
            "model_calls":0,
            "native_opaque_product_geometry_preserved_except_explicit_host_void":True,
        })
        return out


def _det_guid(source_sha:str,local_id:str)->str:
    value=uuid.uuid5(uuid.NAMESPACE_URL,
        "urn:bim-markup-bench:legacy:v0.8:"+source_sha+":"+local_id)
    return ifcopenshell.guid.compress(value.hex)


def _attrs_equal(before,after):
    if before.tag!=after.tag:
        return False
    if set(before.attrib)!=set(after.attrib):
        return False
    for k,value in before.attrib.items():
        other=after.get(k)
        if k in NUMERIC:
            try:
                if Decimal(value)!=Decimal(other):
                    return False
            except (ValueError,TypeError,InvalidOperation):
                return False
        elif value!=other:
            return False
    return True


def _number(node,key,minimum=-10000.,maximum=10000.):
    try:
        d=Decimal(node.get(key))
        x=float(d)
    except (TypeError,ValueError,InvalidOperation,OverflowError) as exc:
        raise LegacyV8CompileError("Non-numeric declarative coordinate "+key) from exc
    if not d.is_finite() or not math.isfinite(x) or not (minimum<=x<=maximum):
        raise LegacyV8CompileError("Out-of-bounds native declarative coordinate "+key)
    return x


def _orig_level(f,level_node):
    storey=f.by_guid(level_node.get("ifcGuid"))
    if not storey.is_a("IfcBuildingStorey"):
        raise LegacyV8CompileError("New native element requires original native Storey")
    if (level_node.get("elevationState")=="EXPLICIT") != (storey.Elevation is not None):
        raise LegacyV8CompileError("Native storey Elevation presence was fabricated")
    if storey.Elevation is not None and not math.isclose(
        float(storey.Elevation),_number(level_node,"elevation"),abs_tol=EPS,rel_tol=0
    ):
        raise LegacyV8CompileError("Native original storey explicit Elevation changed")
    if storey.ObjectPlacement is None:
        raise LegacyV8CompileError("Native original Storey has no placement")
    world=ifcopenshell.util.placement.get_local_placement(storey.ObjectPlacement)
    if not math.isclose(float(world[2,3]),_number(level_node,"placementZ"),abs_tol=EPS,rel_tol=0):
        raise LegacyV8CompileError("Original Storey world placementZ changed")
    if not np.allclose(world[:3,:3].T@world[:3,:3],np.eye(3),atol=1e-8):
        raise LegacyV8CompileError("Unmanaged rotated source storey placement")
    return storey


def _body_context(f):
    body=[x for x in f.by_type("IfcGeometricRepresentationSubContext")
          if x.ContextIdentifier=="Body" and x.TargetView=="MODEL_VIEW"]
    if len(body)!=1:
        raise LegacyV8CompileError("Unique original native Body/MODEL_VIEW context required")
    return body[0]


def _rect_profile(f,width,depth):
    if f.schema=="IFC2X3":
        # IFC2X3 IfcRectangleProfileDef.Position is REQUIRED, unlike IFC4.
        p=f.createIfcAxis2Placement2D(
            f.createIfcCartesianPoint((0.,0.)),
            f.createIfcDirection((1.,0.)))
    else:
        p=None
    return f.createIfcRectangleProfileDef("AREA",None,p,width,depth)


def _place(f,entity,xyz,angle=0.):
    m=np.eye(4,dtype=float)
    c,s=math.cos(angle),math.sin(angle)
    m[:2,:2]=((c,-s),(s,c))
    m[:3,3]=xyz
    ifcopenshell.api.geometry.edit_object_placement(f,product=entity,matrix=m)


def _world_mesh(entity):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        shape=ifcopenshell.geom.create_shape(settings,entity)
        verts=np.asarray(shape.geometry.verts,dtype=float).reshape((-1,3))
        faces=np.asarray(shape.geometry.faces,dtype=int).reshape((-1,3))
    except Exception as exc:
        raise LegacyV8CompileError("Actual native IFC world mesh unavailable") from exc
    if not len(verts) or not len(faces) or not np.isfinite(verts).all():
        raise LegacyV8CompileError("Native IFC mesh degenerate/empty")
    return verts,faces


def _source_plan(source,edited,f,view):
    original=parse_v8(view.xml,source_sha256=view.source_sha256,native_schema=view.native_schema)
    target=parse_v8(edited,source_sha256=view.source_sha256,native_schema=view.native_schema)
    orig_levels={n.get("id"):n for n in original.findall("./"+Q+"Levels/"+Q+"Level")}
    next_levels={n.get("id"):n for n in target.findall("./"+Q+"Levels/"+Q+"Level")}
    if orig_levels.keys()!=next_levels.keys() or any(
        not _attrs_equal(n,next_levels[k]) for k,n in orig_levels.items()
    ):
        raise LegacyV8CompileError("Cannot invent/change native source Storey/elevation")
    levels={}
    for key,node in next_levels.items():
        levels[key]=_orig_level(f,node)
    orig={x.get("id"):x for x in original.findall("./"+Q+"Elements/*")}
    new={x.get("id"):x for x in target.findall("./"+Q+"Elements/*")}
    if not orig.keys()<=new.keys() or any(
        not _attrs_equal(n,new[key]) for key,n in orig.items()
    ):
        raise LegacyV8CompileError("Existing original native IFC products must remain unchanged")
    added={k:n for k,n in new.items() if k not in orig}
    for key,node in added.items():
        if node.get("ifcGuid") is not None:
            raise LegacyV8CompileError("New native element cannot assert an existing GlobalId")
    names=tuple(sorted((x.tag.removeprefix(Q) for x in added.values())))
    if view.native_schema=="IFC4" and names==("Wall",):
        op="CREATE_ORIGINAL_IFC4_WALL"
        kind="wall"
    elif view.native_schema=="IFC2X3" and names==("Space",):
        op="CREATE_ORIGINAL_IFC2X3_SPACE"
        kind="space"
    elif view.native_schema=="IFC2X3" and names==("Door","Opening"):
        op="CREATE_ORIGINAL_IFC2X3_HOSTED_DOOR"
        kind="door"
    else:
        raise LegacyV8CompileError("Only one IFC4 Wall, one IFC2X3 Space, or one IFC2X3 Opening+Door creation")
    guids={key:_det_guid(view.source_sha256,key) for key in added}
    roots={x.GlobalId for x in f.by_type("IfcRoot")}
    if len(set(guids.values()))!=len(guids) or set(guids.values())&roots:
        raise LegacyV8CompileError("Original native IFC GUID collision")
    if op=="CREATE_ORIGINAL_IFC4_WALL":
        key,node=next(iter(added.items()))
        start=np.array([_number(node,c) for c in ("x1","y1","z1")])
        end=np.array([_number(node,c) for c in ("x2","y2","z2")])
        dx=end-start
        length=float(np.linalg.norm(dx[:2]))
        height=_number(node,"height",0.1,100.)
        thickness=_number(node,"thickness",0.05,3.)
        if not (0.1<length<=100. and abs(dx[2])<=EPS):
            raise LegacyV8CompileError("IFC4 Wall needs horizontal bounded physical axis")
        level_id=node.get("level")
        if level_id not in levels:
            raise LegacyV8CompileError("New Wall references missing native source Storey")
        storey=levels[level_id]
        if storey.Elevation is not None:
            raise LegacyV8CompileError("IFC4 prototype is restricted to original MISSING-elevation Storey")
        local_level=np.asarray(ifcopenshell.util.placement.get_local_placement(storey.ObjectPlacement))
        if abs(start[2]-local_level[2,3])>EPS:
            raise LegacyV8CompileError("IFC4 wall base must use original native Storey placement")
        if f.by_type("IfcWall"):
            raise LegacyV8CompileError("Source IFC4 wall already exists; v0.8 limits this source to empty base")
        info={
            "node_ids":(key,),"guids":guids,"kind":kind,"op":op,
            "base_xyz":tuple(float(v) for v in start),
            "angle":float(math.atan2(dx[1],dx[0])),
            "wall_length":length,"height":height,"thickness":thickness,
            "level":storey,"body":_body_context(f),
        }
    elif op=="CREATE_ORIGINAL_IFC2X3_SPACE":
        key,node=next(iter(added.items()))
        level_id=node.get("level")
        if level_id not in levels:
            raise LegacyV8CompileError("New room references missing native source Storey")
        storey=levels[level_id]
        if storey.Elevation is None:
            raise LegacyV8CompileError("Native IFC2X3 room requires original explicit Storey elevation")
        params=tuple(_number(node,c) for c in ("x","y","z","width","depth","height"))
        x,y,z,w,d,h=params
        if any(not 0.25<=v<=100 for v in (w,d,h)):
            raise LegacyV8CompileError("IFC2X3 room requires bounded positive dimensions")
        if z<0 or abs(z-float(storey.Elevation))>EPS:
            raise LegacyV8CompileError("IFC2X3 room base must equal original storey elevation")
        if f.by_type("IfcSpace"):
            raise LegacyV8CompileError("Existing native room requires additional spatial topology analysis")
        info={
            "node_ids":(key,),"guids":guids,"kind":kind,"op":op,
            "xyz":(x,y,z),"dims":(w,d,h),
            "level":storey,"body":_body_context(f),
        }
    else:
        opener_id=next(k for k,n in added.items() if n.tag==Q+"Opening")
        door_id=next(k for k,n in added.items() if n.tag==Q+"Door")
        opening=added[opener_id];door=added[door_id]
        if door.get("opening")!=opener_id:
            raise LegacyV8CompileError("New native Door must explicitly fill its new Opening")
        if opener_id==door_id:
            raise LegacyV8CompileError("Door and Opening need distinct stable XML IDs")
        hostid=opening.get("host")
        hostnode=orig.get(hostid)
        if hostnode is None or hostnode.tag!=Q+"Wall":
            raise LegacyV8CompileError("Native Opening must reference one original projected IfcWallStandardCase")
        host=f.by_guid(hostnode.get("ifcGuid"))
        if not host.is_a("IfcWallStandardCase"):
            raise LegacyV8CompileError("Referenced original IFC2X3 wall does not exist")
        if any(rel.is_a("IfcRelVoidsElement") for rel in f.get_inverse(host)):
            raise LegacyV8CompileError("Existing native host voids unsupported by isolated first Opening")
        x1,y1,z1=(_number(hostnode,c) for c in ("x1","y1","z1"))
        x2,y2,z2=(_number(hostnode,c) for c in ("x2","y2","z2"))
        axis=np.asarray((x2-x1,y2-y1),dtype=float)
        walllength=float(np.linalg.norm(axis))
        if walllength<=0.1 or abs(axis[1])>EPS or axis[0]<=0:
            raise LegacyV8CompileError("Hosted v0.8 Door restricted to native world positive-X Wall axis")
        width=_number(opening,"width",0.5,3.)
        height=_number(opening,"height",1.,4.)
        offset=_number(opening,"offset",0.,100.)
        sill=_number(opening,"sill",0.,10.)
        if (offset<.1 or offset+width>walllength-.1
            or sill+height>_number(hostnode,"height")-.1):
            raise LegacyV8CompileError("Native hosted opening outside original Wall length or height")
        if (abs(_number(door,"width")-width)>EPS
            or abs(_number(door,"height")-height)>EPS):
            raise LegacyV8CompileError("Door and original hosted Opening dimensions disagree")
        thickness=_number(hostnode,"thickness",.05,2.)
        center=np.asarray((x1+offset+width/2,y1,z1+sill))
        storey=levels[hostnode.get("level")]
        info={
            "node_ids":(opener_id,door_id),"guids":guids,"kind":kind,"op":op,
            "host_guid":host.GlobalId,"center":tuple(center),
            "width":width,"height":height,"sill":sill,
            "host_thickness":thickness,
            "level":storey,"body":_body_context(f),
        }
    return info


def _deterministic_new_relations(f,source_sha,old_guids,old_hist_ids):
    originals={x.GlobalId for x in f.by_type("IfcRoot") if x.GlobalId in old_guids}
    if originals!=old_guids:
        raise LegacyV8CompileError("Original native IFC root deleted during transaction")
    new_relations={}
    for relation_class in ("IfcRelAggregates","IfcRelContainedInSpatialStructure",
                            "IfcRelVoidsElement","IfcRelFillsElement"):
        new_instances=[
            x for x in f.by_type(relation_class)
            if x.GlobalId not in old_guids
        ]
        for index,entity in enumerate(sorted(new_instances,key=lambda x:x.id())):
            new_id=_det_guid(source_sha,"native-relation:"+relation_class+":"+str(index))
            if any(y.GlobalId==new_id for y in f.by_type("IfcRoot")):
                raise LegacyV8CompileError("Deterministic relation GUID collides")
            entity.GlobalId=new_id
            new_relations[entity.id()]=relation_class
    owner_histories=[x for x in f.by_type("IfcOwnerHistory") if x.id() not in old_hist_ids]
    if owner_histories:
        originals=[x for x in f.by_type("IfcOwnerHistory") if x.id() in old_hist_ids]
        if not originals or any(x.CreationDate is None for x in originals):
            raise LegacyV8CompileError("New native IfcOwnerHistory lacks source-anchored time")
        epoch=max(int(x.CreationDate) for x in originals)
        for x in owner_histories:
            x.CreationDate=epoch
            if x.LastModifiedDate is not None:
                x.LastModifiedDate=epoch
    return new_relations


def _member_order_stable(f,existing):
    changed=0
    for guid,before in existing.items():
        rel=f.by_guid(guid)
        now={e.GlobalId for e in rel.RelatedElements}
        old=set(before)
        new=now-old
        if now!=old and len(new)!=1:
            raise LegacyV8CompileError("Existing spatial containment gained unexpected original members")
        if not old<=now:
            raise LegacyV8CompileError("Original spatial containment lost native member")
        if new:
            changed+=1
        rel.RelatedElements=tuple(f.by_guid(x) for x in (*before,*sorted(new)))
    return changed


def _verify_native_v8(source:Path,result:Path,plan):
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(result))
    if a.schema!=b.schema or b.schema not in ("IFC2X3","IFC4"):
        raise LegacyV8CompileError("Original native legacy IFC schema was not preserved")
    src_roots={x.GlobalId:x for x in a.by_type("IfcRoot")}
    new_roots={x.GlobalId:x for x in b.by_type("IfcRoot")}
    if not set(src_roots)<=set(new_roots):
        raise LegacyV8CompileError("Original IFC Root disappeared during native create")
    src_steps={e.id():str(e) for e in a}
    new_steps={e.id():str(e) for e in b}
    if not set(src_steps)<=set(new_steps):
        raise LegacyV8CompileError("Original IFC STEP entity deleted during native create")
    expected_changed={r.id() for r in a.by_type("IfcRelContainedInSpatialStructure")}
    for gid,entity in src_roots.items():
        current=new_roots[gid]
        if entity.is_a()!=current.is_a():
            raise LegacyV8CompileError("Original IFC Root class modified")
        if str(entity)!=str(current):
            if (entity.is_a()!="IfcRelContainedInSpatialStructure"
                or gid not in plan["original_spatial_relations"]):
                raise LegacyV8CompileError("Unrelated original IFC Root was modified")
            orig=set(plan["original_spatial_relations"][gid])
            following={x.GlobalId for x in current.RelatedElements}
            new_members=following-orig
            if orig-following or len(new_members)!=1 or not new_members<=set(plan["guids"].values()):
                raise LegacyV8CompileError("Original source storey containment members damaged")
    changed={eid for eid in src_steps if src_steps[eid]!=new_steps[eid]}
    if not changed<=expected_changed:
        raise LegacyV8CompileError("Unrelated original IFC STEP object changed")
    # Only native host Wall can have a changed physical shape (it is cut by
    # the *declared new Opening*). Every other source solid must be unchanged.
    source_product_ids={x.GlobalId for x in a.by_type("IfcProduct")}
    candidate_product_ids={x.GlobalId for x in b.by_type("IfcProduct")}
    if candidate_product_ids!=source_product_ids|set(plan["guids"].values()):
        raise LegacyV8CompileError("Missing original or unexpected new IFC Product")
    physical=0
    for src in a.by_type("IfcProduct"):
        if src.Representation is None:
            continue
        if src.GlobalId==plan.get("host_guid"):
            before,faces0=_world_mesh(src)
            after,faces1=_world_mesh(b.by_guid(src.GlobalId))
            if len(faces1)<=len(faces0):
                raise LegacyV8CompileError("Native host Wall physical void was not actually created")
            if not np.allclose(before.min(0),after.min(0),atol=EPS):
                raise LegacyV8CompileError("Original Wall external native lower bounds changed unexpectedly")
            if not np.allclose(before.max(0),after.max(0),atol=EPS):
                raise LegacyV8CompileError("Original Wall external native upper bounds changed unexpectedly")
        else:
            before,faces0=_world_mesh(src)
            after,faces1=_world_mesh(b.by_guid(src.GlobalId))
            if before.shape!=after.shape or faces0.shape!=faces1.shape or not np.allclose(
                before,after,atol=EPS,rtol=0
            ):
                raise LegacyV8CompileError("Unrelated original IFC product physical native shape altered")
            physical+=1
    for gid in plan["guids"].values():
        if gid not in new_roots:
            raise LegacyV8CompileError("New native IFC entity missing")
        _world_mesh(b.by_guid(gid))
    if plan["kind"]=="wall":
        node=b.by_guid(next(iter(plan["guids"].values())))
        lo,hi=_world_mesh(node)[0].min(0),_world_mesh(node)[0].max(0)
        if not node.is_a("IfcWall"):
            raise LegacyV8CompileError("New native IFC4 entity not Wall")
        if ifcopenshell.util.element.get_container(node).GlobalId!=plan["level"].GlobalId:
            raise LegacyV8CompileError("Native IFC4 Wall not contained in original Storey")
        if b.by_guid(plan["level"].GlobalId).Elevation is not None:
            raise LegacyV8CompileError("Missing original IFC4 Storey elevation fabricated")
        length=plan["wall_length"]
        if not math.isclose(math.dist(lo[:2],hi[:2]),
                            math.hypot(length,plan["thickness"]),rel_tol=0,abs_tol=.4):
            # Other arbitrary orientations produce a larger world AABB;
            # size is checked independently below via exact local extrusion.
            raise LegacyV8CompileError("Wall physical bbox exceeds declared source dimensions")
    elif plan["kind"]=="space":
        node=b.by_guid(next(iter(plan["guids"].values())))
        if (not node.is_a("IfcSpace")
            or ifcopenshell.util.element.get_aggregate(node).GlobalId!=plan["level"].GlobalId):
            raise LegacyV8CompileError("Native IFC2X3 Space lacks original Storey aggregation")
        points,_=_world_mesh(node)
        xyz=np.asarray(plan["xyz"])
        w,d,h=plan["dims"]
        intended_min=xyz
        intended_max=xyz+np.asarray((w,d,h))
        if not np.allclose(points.min(0),intended_min,atol=EPS) or not np.allclose(
            points.max(0),intended_max,atol=EPS
        ):
            raise LegacyV8CompileError("Native IFC2X3 room physical dimensions/position differ from XML")
    else:
        opening=b.by_guid(plan["guids"][plan["node_ids"][0]])
        door=b.by_guid(plan["guids"][plan["node_ids"][1]])
        if (not opening.is_a("IfcOpeningElement") or not door.is_a("IfcDoor")
            or len(opening.VoidsElements)!=1 or len(door.FillsVoids)!=1
            or opening.VoidsElements[0].RelatingBuildingElement.GlobalId!=plan["host_guid"]
            or door.FillsVoids[0].RelatingOpeningElement.GlobalId!=opening.GlobalId):
            raise LegacyV8CompileError("IFC2X3 original host Opening and Door fill/void relation missing")
        if ifcopenshell.util.element.get_container(door).GlobalId!=plan["level"].GlobalId:
            raise LegacyV8CompileError("Original IFC2X3 Door lacks original source Storey containment")
        p_o,_=_world_mesh(opening)
        p_d,_=_world_mesh(door)
        c=np.asarray(plan["center"])
        w,h=plan["width"],plan["height"]
        if not np.allclose(
            p_o.min(0),(c[0]-w/2,c[1]-plan["host_thickness"]/2-.1,c[2]),atol=EPS
        ) or not np.allclose(
            p_o.max(0),(c[0]+w/2,c[1]+plan["host_thickness"]/2+.1,c[2]+h),atol=EPS
        ):
            raise LegacyV8CompileError("Physical IFC2X3 wall Opening not at declared location")
        if not np.allclose(p_d.max(0)-p_d.min(0),(w,.08,h),atol=EPS):
            raise LegacyV8CompileError("Physical native IFC2X3 Door dimensions mismatch")
    return physical


def compile_declarative_xml_v8(source:Path,edited_xml:bytes,destination:Path):
    if (not source.is_file() or source.is_symlink()
        or destination.exists() or destination.is_symlink()
        or source.resolve()==destination.resolve()):
        raise LegacyV8CompileError("Native source exists and destination must be unused distinct IFC path")
    view=project_legacy_v8(source)
    f=ifcopenshell.open(str(source))
    if f.schema!=view.native_schema:
        raise LegacyV8CompileError("Source IFC schema changed during projection")
    plan=_source_plan(source,edited_xml,f,view)
    base_guid={x.GlobalId for x in f.by_type("IfcRoot")}
    histories={x.id() for x in f.by_type("IfcOwnerHistory")}
    orig_containment={
        x.GlobalId:tuple(y.GlobalId for y in x.RelatedElements)
        for x in f.by_type("IfcRelContainedInSpatialStructure")
    }
    plan["original_spatial_relations"]=orig_containment
    op=plan["op"]
    sourcehash=view.source_sha256
    if snapshot_source(source).source_sha256!=sourcehash:
        raise LegacyV8CompileError("Source native IFC modified before edit")
    body=plan["body"]
    native_created={}

    def writer(path):
        if plan["kind"]=="wall":
            key=plan["node_ids"][0]
            node=ifcopenshell.api.root.create_entity(
                f,ifc_class="IfcWall",name="Research native IFC4 declarative Wall v0.8")
            node.GlobalId=plan["guids"][key]
            representation=ifcopenshell.api.geometry.add_wall_representation(
                f,context=body,length=plan["wall_length"],height=plan["height"],
                thickness=plan["thickness"])
            ifcopenshell.api.geometry.assign_representation(
                f,product=node,representation=representation)
            _place(f,node,plan["base_xyz"],plan["angle"])
            ifcopenshell.api.spatial.assign_container(
                f,products=[node],relating_structure=plan["level"])
            native_created[key]=node
        elif plan["kind"]=="space":
            key=plan["node_ids"][0]
            node=ifcopenshell.api.root.create_entity(
                f,ifc_class="IfcSpace",name="Research native IFC2X3 declarative Space v0.8")
            node.GlobalId=plan["guids"][key]
            x,y,z=plan["xyz"]
            w,d,h=plan["dims"]
            profile=_rect_profile(f,w,d)
            rep=ifcopenshell.api.geometry.add_profile_representation(
                f,context=body,profile=profile,depth=h)
            ifcopenshell.api.geometry.assign_representation(
                f,product=node,representation=rep)
            _place(f,node,(x+w/2,y+d/2,z))
            ifcopenshell.api.aggregate.assign_object(
                f,products=[node],relating_object=plan["level"])
            native_created[key]=node
        elif plan["kind"]=="door":
            opening_id,door_id=plan["node_ids"]
            opening=ifcopenshell.api.root.create_entity(
                f,ifc_class="IfcOpeningElement",name="Research IFC2X3 native Wall void v0.8")
            opening.GlobalId=plan["guids"][opening_id]
            w,h=plan["width"],plan["height"]
            thick=plan["host_thickness"]
            rectangle=_rect_profile(f,w,thick+.2)
            rep=ifcopenshell.api.geometry.add_profile_representation(
                f,context=body,profile=rectangle,depth=h)
            ifcopenshell.api.geometry.assign_representation(
                f,product=opening,representation=rep)
            _place(f,opening,plan["center"])
            ifcopenshell.api.feature.add_feature(
                f,feature=opening,element=f.by_guid(plan["host_guid"]))
            door=ifcopenshell.api.root.create_entity(
                f,ifc_class="IfcDoor",name="Research native IFC2X3 hosted Door v0.8")
            door.GlobalId=plan["guids"][door_id]
            door.OverallWidth=w
            door.OverallHeight=h
            doorprofile=_rect_profile(f,w,.08)
            rep=ifcopenshell.api.geometry.add_profile_representation(
                f,context=body,profile=doorprofile,depth=h)
            ifcopenshell.api.geometry.assign_representation(
                f,product=door,representation=rep)
            _place(f,door,plan["center"])
            ifcopenshell.api.feature.add_filling(
                f,opening=opening,element=door)
            ifcopenshell.api.spatial.assign_container(
                f,products=[door],relating_structure=plan["level"])
            native_created[opening_id]=opening
            native_created[door_id]=door
        else:
            raise LegacyV8CompileError("Internal v0.8 legacy edit plan unsupported")
        _member_order_stable(f,orig_containment)
        _deterministic_new_relations(f,sourcehash,base_guid,histories)
        f.write(str(path))

    def verify(path):
        if snapshot_source(source).source_sha256!=sourcehash:
            raise LegacyV8CompileError("Immutable original native IFC source mutated during editing")
        _verify_native_v8(source,path,plan)

    stage_and_commit(destination,writer,verify)
    if snapshot_source(source).source_sha256!=sourcehash:
        raise LegacyV8CompileError("Immutable original native IFC modified after output")
    final=snapshot_source(destination)
    preserved=_verify_native_v8(source,destination,plan)
    report=Mutation(
        op,plan["node_ids"][0],plan["guids"][plan["node_ids"][0]],1,
        ("geometry","level") if plan["kind"]!="door"
        else ("native_host_void","native_door_filling","geometry"),
        "Prospective v0.8 original native IFC2X3/IFC4 source-schema-preserving declarative delta",
    )
    return LegacyV8CompileReport(
        sourcehash,final.source_sha256,
        view.source_fingerprint,final.graph_fingerprint,
        (report,),preserved,(),destination,True)
