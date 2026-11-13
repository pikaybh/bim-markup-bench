"""Research-only prospective IFC4X3 Wall pose/length and dependency-aware delete.

No changes to older experimental compilers or historical model results.
LLM authors ONLY a complete declarative XML model. This trusted backend
infers a stable-ID semantic diff and materializes exactly one safe native
IfcWall edit in a new IFC clone (never the original).
"""
from __future__ import annotations

from pathlib import Path
import math

import numpy as np
import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit

from src.runtime.compiler import CompileReport
from src.runtime.ifc_mutations import Mutation
from src.runtime.ifc_projection import _body_extrusion,_wall_attrs
from src.runtime.experimental_v4_projection import project_ifc_v4
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document
from src.runtime.semantic_graph import graph_diff
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.transaction import stage_and_commit


EPS=2e-5


class WallV5Error(ValueError):
    pass


class WallV5CompileReport(CompileReport):
    def as_dict(self):
        result=super().as_dict()
        result.update({
            "status":"COMMITTED_SCOPED_IFC4X3_"+self.operations[0].operation+"_V5",
            "compiler_version":"experimental-wall-v0.5",
            "full_45_task_capability_parity":False,
            "full_hosted_wall_delete_support":False,
            "source_native_geom_passthrough":True,
        })
        return result


def _wall(f,guid):
    try:
        obj=f.by_guid(guid)
    except RuntimeError as exc:
        raise WallV5Error("Original IFC Wall GUID missing") from exc
    if not obj.is_a("IfcWall"):
        raise WallV5Error("Original IFC GlobalId is not IfcWall")
    return obj


def _wall_mesh(wall):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        mesh=ifcopenshell.geom.create_shape(settings,wall)
    except Exception as exc:
        raise WallV5Error("Native IfcWall mesh cannot be created") from exc
    points=np.asarray(mesh.geometry.verts,dtype=float)
    if not len(points) or len(points)%3 or not np.isfinite(points).all():
        raise WallV5Error("Invalid native IfcWall world mesh")
    return points.reshape(-1,3)


def _safe_wall(f,wall,*,deletion=False):
    allowed={
        "IfcRelContainedInSpatialStructure","IfcRelAssociatesMaterial",
        "IfcRelDefinesByType","IfcRelDefinesByProperties",
        "IfcRelAssociatesClassification",
    }
    if deletion:
        allowed.add("IfcRelConnectsPathElements")
    for relation in f.get_inverse(wall):
        if relation.is_a("IfcRelConnectsPathElements") and not deletion:
            raise WallV5Error("Connected Wall cannot change pose/length safely")
        if relation.is_a() not in allowed:
            raise WallV5Error("Wall has unsupported hosted/boundary/dependency "+relation.is_a())
        if relation.is_a("IfcRelDefinesByProperties"):
            members=relation.RelatedObjects
            if len(members)!=1 or members[0].GlobalId!=wall.GlobalId:
                raise WallV5Error("Wall Pset relation shared with unrelated product")
            if not relation.RelatingPropertyDefinition.is_a("IfcPropertySet"):
                raise WallV5Error("Wall has unsupported property definition")
        if relation.is_a("IfcRelConnectsPathElements"):
            if not deletion:
                raise WallV5Error("Connected Wall cannot change pose/length safely")
            # A path element connection can be removed with the Wall, but no
            # geometry-dependent ConnectionGeometry is allowed.
            if relation.ConnectionGeometry is not None:
                raise WallV5Error("Wall path connection has geometry-dependent constraint")
    if wall.ObjectPlacement is None or wall.Representation is None:
        raise WallV5Error("Wall missing original native geometry or placement")


def _unique_body(f,wall):
    solid=_body_extrusion(wall)
    rep_owners=[]
    for rep in f.get_inverse(solid):
        if rep.is_a("IfcShapeRepresentation"):
            pdefs=[x for x in f.get_inverse(rep) if x.is_a("IfcProductDefinitionShape")]
            rep_owners.extend(x for p in pdefs for x in f.get_inverse(p) if x.is_a("IfcProduct"))
    if len(rep_owners)!=1 or rep_owners[0].id()!=wall.id():
        raise WallV5Error("Native wall extrusion belongs to another/shared product")
    if len(f.get_inverse(solid.SweptArea))!=1:
        raise WallV5Error("Wall rectangle shared with another solid")
    return solid


def _axis(f,wall):
    axes=[item for rep in wall.Representation.Representations
          if rep.RepresentationType=="Curve2D" for item in rep.Items
          if item.is_a("IfcPolyline") and len(item.Points)==2]
    if len(axes)!=1:
        raise WallV5Error("Wall lacks unique native IfcPolyline axis")
    return axes[0]


def _pose(f,wall):
    placement=wall.ObjectPlacement
    if not placement.is_a("IfcLocalPlacement"):
        raise WallV5Error("Wall placement is not local")
    relative=placement.RelativePlacement
    if not relative.is_a("IfcAxis2Placement3D"):
        raise WallV5Error("Wall relative frame is not native 3D")
    if len(f.get_inverse(placement))!=1 or len(f.get_inverse(relative))!=1:
        raise WallV5Error("Wall native placement is shared")
    p=np.asarray(ifcopenshell.util.placement.get_local_placement(placement),dtype=float)
    if not np.allclose(p[:3,:3].T@p[:3,:3],np.eye(3),atol=1e-7):
        raise WallV5Error("Wall global pose is nonorthogonal")
    if not np.allclose(p[2,:3],(0,0,1),atol=1e-7):
        raise WallV5Error("Tilted Wall not a horizontal XY pose")
    return relative,p


def _source_local_start(f,wall,world_start):
    rel,world=_pose(f,wall)
    if not np.allclose(world[:3,3],world_start,atol=EPS):
        # Current slice only supports walls whose explicit Curve2D axis
        # starts at their native ObjectPlacement origin.
        raise WallV5Error("Original wall axis does not start at original local placement origin")
    return rel,world


def _bounded_xy(values):
    vals=tuple(float(x) for x in values)
    if any(not math.isfinite(x) or abs(x)>10000 for x in vals):
        raise WallV5Error("Wall coordinates nonfinite/outside 10km envelope")
    return vals


def _existing_step_preserve(source,result,allowed_updated,allowed_added):
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(result))
    if a.schema!="IFC4X3" or b.schema!=a.schema:
        raise WallV5Error("Native IFC schema changed")
    old={e.id():str(e) for e in a}
    new={e.id():str(e) for e in b}
    if not set(old)<=set(new):
        raise WallV5Error("Wall update deleted original STEP entity")
    changed={i for i in old if old[i]!=new[i]}
    if changed!=allowed_updated:
        raise WallV5Error("Original non-target native STEP entity changed: "+str(sorted(changed^allowed_updated)))
    extra={i:b.by_id(i).is_a() for i in set(new)-set(old)}
    if extra!=allowed_added:
        raise WallV5Error("Wall edit created unexpected native STEP entity")
    roots_a={x.GlobalId:x for x in a.by_type("IfcRoot")}
    roots_b={x.GlobalId:x for x in b.by_type("IfcRoot")}
    if set(roots_a)!=set(roots_b):
        raise WallV5Error("Native GlobalId/Root count changed")
    for guid in roots_a:
        if str(roots_a[guid])!=str(roots_b[guid]):
            raise WallV5Error("Original IFC Root identity or property changed")
    return len(roots_a)


def _validate_native_delete(source,result,guid):
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(result))
    old_roots={r.GlobalId:r for r in a.by_type("IfcRoot")}
    new_roots={r.GlobalId:r for r in b.by_type("IfcRoot")}
    wall=_wall(a,guid)
    _safe_wall(a,wall,deletion=True)
    if guid in new_roots or set(new_roots)-set(old_roots):
        raise WallV5Error("Target Wall survived or unrelated IFC Root added")
    old_products={e.GlobalId:e for e in a.by_type("IfcProduct")}
    new_products={e.GlobalId:e for e in b.by_type("IfcProduct")}
    if set(old_products)-{guid}!=set(new_products):
        raise WallV5Error("Wall deletion removed another native IFC Product")
    if any(str(old_products[k])!=str(new_products[k]) for k in new_products):
        raise WallV5Error("Wall deletion mutated non-target IFC Product")
    # Connection relations and only sole-owned properties can disappear.
    inverse={r.GlobalId:r for r in a.get_inverse(wall)
             if r.is_a("IfcRoot")}
    expected_removed={guid}
    allowed_changed=set()
    for rel_guid,rel in inverse.items():
        cls=rel.is_a()
        if cls=="IfcRelConnectsPathElements":
            expected_removed.add(rel_guid)
            continue
        if cls=="IfcRelDefinesByProperties":
            if len(rel.RelatedObjects)!=1 or rel.RelatedObjects[0].GlobalId!=guid:
                raise WallV5Error("Shared wall property relation deleted")
            expected_removed.add(rel_guid)
            expected_removed.add(rel.RelatingPropertyDefinition.GlobalId)
            continue
        members=(rel.RelatedElements if cls=="IfcRelContainedInSpatialStructure"
                 else rel.RelatedObjects)
        original_members={x.GlobalId for x in members}
        if guid not in original_members:
            raise WallV5Error("Wall not in actual IFC Root related-members list")
        if len(original_members)==1:
            expected_removed.add(rel_guid)
        else:
            nxt=new_roots.get(rel_guid)
            if nxt is None:
                raise WallV5Error("Shared Wall type/material/containment unexpectedly deleted")
            after_members=(nxt.RelatedElements if cls=="IfcRelContainedInSpatialStructure"
                           else nxt.RelatedObjects)
            if {x.GlobalId for x in after_members}!=original_members-{guid}:
                raise WallV5Error("Unrelated IFC relation member changed")
            allowed_changed.add(rel_guid)
    if set(old_roots)-set(new_roots)!=expected_removed:
        raise WallV5Error("Unexpected Wall native Root/property/relationship disappeared")
    for g in old_roots.keys()&new_roots.keys():
        if old_roots[g].is_a()!=new_roots[g].is_a():
            raise WallV5Error("Unrelated IFC Root class changed")
        if str(old_roots[g])!=str(new_roots[g]) and g not in allowed_changed:
            raise WallV5Error("Non-target Root changed on Wall delete")
    old={e.id():str(e) for e in a}
    new={e.id():str(e) for e in b}
    deleted=set(old)-set(new)
    changed={i for i in old.keys()&new.keys() if old[i]!=new[i]}
    added=set(new)-set(old)
    allowed_gone={
        "IfcWall","IfcRelConnectsPathElements","IfcRelDefinesByProperties",
        "IfcPropertySet","IfcRelAssociatesMaterial","IfcRelAssociatesClassification",
        "IfcRelDefinesByType","IfcRelContainedInSpatialStructure",
        "IfcAxis2Placement2D","IfcAxis2Placement3D","IfcCartesianPoint",
        "IfcLocalPlacement","IfcDirection","IfcExtrudedAreaSolid","IfcPolyline",
        "IfcRectangleProfileDef","IfcShapeRepresentation","IfcProductDefinitionShape",
        "IfcStyledItem","IfcPropertySingleValue","IfcMaterialLayerSetUsage",
        "IfcCurveSegment","IfcCartesianPointList2D",
    }
    if any(a.by_id(i).is_a() not in allowed_gone for i in deleted):
        raise WallV5Error("Wall deletion removed unexpected original STEP entity class")
    if any(not b.by_id(i).is_a("IfcOwnerHistory") for i in added):
        raise WallV5Error("Wall deletion added unexpected STEP type")
    for i in deleted:
        if any(inv.id() not in deleted and inv.id() not in changed
               for inv in a.get_inverse(a.by_id(i))):
            raise WallV5Error("Removed native geometry was still shared by another IFC element")
    allowed_step={old_roots[g].id() for g in allowed_changed}
    original_reps={r.id() for r in wall.Representation.Representations}
    for i in changed-allowed_step:
        prev=a.by_id(i);now=b.by_id(i)
        if not prev.is_a("IfcPresentationLayerAssignment") or not now.is_a("IfcPresentationLayerAssignment"):
            raise WallV5Error("Wall deletion modified unapproved nonroot STEP record")
        before_set={x.id() for x in prev.AssignedItems}
        after_set={x.id() for x in now.AssignedItems}
        if after_set-before_set or not before_set-after_set<=original_reps:
            raise WallV5Error("Unrelated native presentation layer altered")
    return len(new_products)


def compile_declarative_xml_v5(source:Path,edited_xml:bytes,destination:Path):
    if not source.is_file() or source.is_symlink() or destination.exists() or destination.is_symlink():
        raise WallV5Error("Immutable IFC source required; destination must be unused")
    proj=project_ifc_v4(source)
    pre=parse_xml(proj.xml,expected_source_sha256=proj.source.source_sha256)
    post=parse_xml(edited_xml,expected_source_sha256=proj.source.source_sha256)
    before=bind_document(pre,projection=proj)
    after=bind_document(post,projection=proj,verify_native_edges=False)
    diff=graph_diff(before.graph,after.graph)
    if diff.added_nodes or diff.added_edges or diff.changed_nodes and diff.removed_nodes:
        raise WallV5Error("v0.5 supports isolated Wall update/delete, no creates or mix")
    if len(diff.changed_nodes)+len(diff.removed_nodes)!=1:
        raise WallV5Error("Exactly one native Wall edit required")
    name=(diff.changed_nodes or diff.removed_nodes)[0]
    old=before.graph.by_id()[name]
    if old.kind!="Wall" or old.provenance!="existing_source":
        raise WallV5Error("Only existing projected native Wall in v0.5")
    f=ifcopenshell.open(str(source))
    if f.schema!="IFC4X3" or abs(ifcopenshell.util.unit.calculate_unit_scale(f)-1.)>1e-8:
        raise WallV5Error("IFC4X3 metres required")
    target=_wall(f,old.ifc_guid)
    source_hash=proj.source.source_sha256
    if snapshot_source(source).source_sha256!=source_hash:
        raise WallV5Error("Original source modified during frozen projection")
    old_attrs=dict(old.attributes)
    allowed_step=set()
    allowed_added={}
    new_coords=None
    if diff.removed_nodes:
        if diff.changed_nodes:
            raise WallV5Error("Cannot combine delete with other changes")
        expected={e for e in before.graph.edges if
                  (e.relation=="in_storey" and e.target==name) or
                  (e.relation=="connects" and (e.source==name or e.target==name))}
        if set(diff.removed_edges)!=expected or not any(
                e.relation=="in_storey" and e.target==name for e in expected):
            raise WallV5Error("Wall deletion has unexpected managed relationship changes")
        _safe_wall(f,target,deletion=True)
        op="DELETE_WALL_WITH_SAFE_RELATIONS"
    else:
        if diff.removed_edges or diff.added_edges:
            raise WallV5Error("Wall pose/length edit cannot change relations")
        updated=after.graph.by_id()[name]
        if updated.kind!="Wall" or updated.ifc_guid!=old.ifc_guid:
            raise WallV5Error("Native Wall class/identity changed")
        current=dict(updated.attributes)
        fields={k for k in current.keys()|old_attrs.keys()
                if current.get(k)!=old_attrs.get(k)}
        if not fields or fields-set(("x1","y1","x2","y2")):
            raise WallV5Error("Only planar wall endpoints can change in v0.5")
        if any(current[k]!=old_attrs[k] for k in ("z1","z2","height","thickness","level")):
            raise WallV5Error("Wall elevation/height/storey/thickness changed")
        _safe_wall(f,target,deletion=False)
        solid=_unique_body(f,target)
        pre_coords=_bounded_xy([old_attrs[k] for k in ("x1","y1","x2","y2")])
        new_coords=_bounded_xy([current[k] for k in ("x1","y1","x2","y2")])
        x1,y1,x2,y2=pre_coords
        a,b,c,d=new_coords
        oldvec=np.array((x2-x1,y2-y1),dtype=float)
        newvec=np.array((c-a,d-b),dtype=float)
        old_len=float(np.linalg.norm(oldvec))
        new_len=float(np.linalg.norm(newvec))
        if old_len<0.1 or new_len<0.1 or new_len>100:
            raise WallV5Error("Wall edit outside supported planar length")
        relative,world=_source_local_start(f,target,(x1,y1,float(old_attrs["z1"])))
        if not np.allclose(world[:2,0],oldvec/old_len,atol=EPS):
            raise WallV5Error("Original Wall axis not aligned with native local x")
        if abs(old_len-new_len)>1e-5:
            if not (np.allclose((a,b),(x1,y1),atol=EPS)
                    and np.allclose(newvec/new_len,oldvec/old_len,atol=EPS)):
                raise WallV5Error("Changing wall length only supports same start and direction")
            if not solid.SweptArea.is_a("IfcRectangleProfileDef"):
                raise WallV5Error("Only original native rectangular Wall length supported")
            axis=_axis(f,target)
            end=axis.Points[1]
            if len(f.get_inverse(end))!=1 or next(iter(f.get_inverse(end))).id()!=axis.id():
                raise WallV5Error("Wall local axis end is shared")
            if len(f.get_inverse(solid.SweptArea))!=1:
                raise WallV5Error("Native Wall rectangle profile shared")
            if not np.allclose(end.Coordinates[:2],(old_len,0.),atol=EPS):
                raise WallV5Error("Wall local axis origin/end not standard")
            if not math.isclose(float(solid.SweptArea.XDim),old_len,abs_tol=EPS):
                raise WallV5Error("Native rectangular solid length mismatch")
            op="CHANGE_WALL_LENGTH"
            allowed_step.update((end.id(),solid.SweptArea.id()))
        else:
            if np.allclose(newvec/old_len,oldvec/old_len,atol=EPS):
                op="MOVE_WALL"
            else:
                op="ROTATE_WALL"
            oldloc=relative.Location
            if len(f.get_inverse(oldloc))!=1 or next(iter(f.get_inverse(oldloc))).id()!=relative.id():
                raise WallV5Error("Wall pose shared original CartesianPoint")
            shift_xy=np.array((a-x1,b-y1),dtype=float)
            if not np.allclose(shift_xy,(0.,0.),atol=1e-8):
                allowed_step.add(oldloc.id())
            if op=="ROTATE_WALL":
                # RefDirection is shared in Revit exports. Never mutate it.
                allowed_step.add(relative.id())
    def writer(path):
        nonlocal allowed_added
        if op=="DELETE_WALL_WITH_SAFE_RELATIONS":
            _safe_wall(f,target,deletion=True)
            ifcopenshell.api.root.remove_product(f,product=target)
        elif op=="CHANGE_WALL_LENGTH":
            axis=_axis(f,target)
            axis.Points[1].Coordinates=(float(new_len),0.)
            solid.SweptArea.XDim=float(new_len)
        else:
            relative=target.ObjectPlacement.RelativePlacement
            point=relative.Location
            dx=new_coords[0]-pre_coords[0]
            dy=new_coords[1]-pre_coords[1]
            if math.hypot(dx,dy)>1e-8:
                point.Coordinates=(float(point.Coordinates[0])+dx,
                                   float(point.Coordinates[1])+dy,
                                   float(point.Coordinates[2]))
            if op=="ROTATE_WALL":
                new_direction=newvec/new_len
                ref=f.createIfcDirection((float(new_direction[0]),float(new_direction[1]),0.))
                relative.RefDirection=ref
                allowed_added[ref.id()]="IfcDirection"
        f.write(str(path))
    def validate(path):
        if snapshot_source(source).source_sha256!=source_hash:
            raise WallV5Error("Original source changed during Wall transaction")
        if op=="DELETE_WALL_WITH_SAFE_RELATIONS":
            _validate_native_delete(source,path,old.ifc_guid)
            return
        updated_model=ifcopenshell.open(str(path))
        updated_wall=_wall(updated_model,old.ifc_guid)
        # Reproject native edited wall using the original source reader.
        native_attrs=_wall_attrs(updated_wall,{
            ifcopenshell.util.element.get_container(updated_wall).GlobalId:
                old_attrs["level"],
        },1.)
        for key in ("x1","y1","z1","x2","y2","z2","height","thickness"):
            if not math.isclose(float(native_attrs[key]),float(current[key]),
                                rel_tol=0,abs_tol=2e-5):
                raise WallV5Error("Updated native IFC physical Wall axis differs from declarative XML "+key)
        _wall_mesh(updated_wall)
        before_mesh=_wall_mesh(ifcopenshell.open(str(source)).by_guid(old.ifc_guid))
        after_mesh=_wall_mesh(updated_wall)
        if len(before_mesh)!=len(after_mesh) or not np.isfinite(after_mesh).all():
            raise WallV5Error("Wall native mesh lost vertices")
        if op=="MOVE_WALL":
            shift=np.array((new_coords[0]-pre_coords[0],new_coords[1]-pre_coords[1],0.))
            if not np.allclose(
                np.sort(before_mesh+shift,axis=0),np.sort(after_mesh,axis=0),atol=EPS):
                raise WallV5Error("Native Wall world mesh did not translate")
        _existing_step_preserve(source,path,allowed_step,allowed_added)
    stage_and_commit(destination,writer,validate)
    preserved=(_validate_native_delete(source,destination,old.ifc_guid)
               if op=="DELETE_WALL_WITH_SAFE_RELATIONS"
               else _existing_step_preserve(source,destination,allowed_step,allowed_added))
    if snapshot_source(source).source_sha256!=source_hash:
        raise WallV5Error("Original source changed following trusted transaction")
    snap=snapshot_source(destination)
    line=(pre if op=="DELETE_WALL_WITH_SAFE_RELATIONS" else post).managed_by_id()[name].span.line
    change=Mutation(op,name,old.ifc_guid,line,("entity",) if diff.removed_nodes else
                    tuple(sorted(fields)),
                    "experimental v0.5 native Wall; isolated pose/length or dependency-checked removal")
    return WallV5CompileReport(source_hash,snap.source_sha256,
        proj.source.graph_fingerprint,snap.graph_fingerprint,
        (change,),preserved,(),destination,True)
