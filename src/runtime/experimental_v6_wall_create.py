"""Experimental isolated v0.6 declarative IFC4X3 Wall CREATE compiler.

Only one new isolated native IfcWall from a complete XML state is admitted.
Pre-existing experimental v0.5 wall UPDATE/DELETE is UNMODIFIED. This is a
limited research-only opt-in backend, NOT equal general IFC authoring capability.
The XML does NOT express an imperative tool call. The trusted backend computes
the typed graph delta and creates IFC using the IFC API.
"""
from __future__ import annotations
from decimal import Decimal
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

from src.runtime.experimental_v4_projection import project_ifc_v4
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document
from src.runtime.semantic_graph import graph_diff
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.transaction import stage_and_commit
from src.runtime.compiler import CompileReport
from src.runtime.ifc_mutations import Mutation


class WallV6CreateError(ValueError):
    pass


def _parse_params(attrs:dict)->tuple[float,...]:
    names=("x1","y1","z1","x2","y2","z2","height","thickness")
    raw=[]
    for name in names:
        try:
            dec=Decimal(attrs[name])
        except (KeyError,ValueError,TypeError,ArithmeticError) as exc:
            raise WallV6CreateError("Missing/invalid declarative Wall field: "+name) from exc
        if not dec.is_finite():
            raise WallV6CreateError("Nonfinite declarative Wall field: "+name)
        raw.append(float(dec))
    x1,y1,z1,x2,y2,z2,h,t=raw
    length=math.hypot(x2-x1,y2-y1)
    if (any(not math.isfinite(v) or abs(v)>10000 for v in raw)
            or abs(z2-z1)>1e-8 or not 0.02<length<=100
            or not 0.1<=h<=20 or not .03<=t<=2):
        raise WallV6CreateError("Bounded single planar rectangular Wall required")
    return tuple(raw)


def _unique_context(f,identifier,view):
    items=[x for x in f.by_type("IfcGeometricRepresentationSubContext")
           if x.ContextIdentifier==identifier and x.TargetView==view]
    if len(items)!=1:
        raise WallV6CreateError("Original source requires unique "+identifier+" context")
    return items[0]


def _check_original_metre_step_preservation(source:Path,out:Path,new_guid:str)->int:
    """All original metric IFC STEP objects preserved, except containment growth."""
    original=ifcopenshell.open(str(source))
    result=ifcopenshell.open(str(out))
    if original.schema!="IFC4X3" or result.schema!="IFC4X3":
        raise WallV6CreateError("Native IFC4X3 STEP schema changed")
    a={x.id():str(x) for x in original}
    b={x.id():str(x) for x in result}
    if not set(a)<=set(b):
        raise WallV6CreateError("Original native IFC STEP entity deleted on Wall create")
    changed={k for k in a if a[k]!=b[k]}
    allowed={r.id() for r in original.by_type("IfcRelContainedInSpatialStructure")}
    if not changed<=allowed:
        raise WallV6CreateError("Unrelated native IFC STEP source was changed")
    old={x.GlobalId:x for x in original.by_type("IfcRoot")}
    new={x.GlobalId:x for x in result.by_type("IfcRoot")}
    if (not set(old)<=set(new) or len(result.by_type("IfcWall"))!=len(original.by_type("IfcWall"))+1
            or new_guid not in new or not new[new_guid].is_a("IfcWall")):
        raise WallV6CreateError("Native source root lost or new wall not present")
    extras=set(new)-set(old)-{new_guid}
    if any(not new[k].is_a("IfcRelContainedInSpatialStructure") for k in extras):
        raise WallV6CreateError("Unexpected other native IFC Root creation")
    for guid,older in old.items():
        later=new[guid]
        if (older.is_a()!=later.is_a()
                or (str(older)!=str(later) and not older.is_a("IfcRelContainedInSpatialStructure"))):
            raise WallV6CreateError("Original pre-existing IFC Root changed")
    grown=0
    for relation in original.by_type("IfcRelContainedInSpatialStructure"):
        before={x.GlobalId for x in relation.RelatedElements}
        after_rel=result.by_guid(relation.GlobalId)
        after={x.GlobalId for x in after_rel.RelatedElements}
        if before!=after:
            if after != before|{new_guid}:
                raise WallV6CreateError("An existing native containment member was changed")
            grown+=1
    if grown!=1:
        raise WallV6CreateError("New wall must extend one original native containment")
    return len(old)


def _check_physical_wall(f,guid,level_guid,params):
    wall=f.by_guid(guid)
    if not wall.is_a("IfcWall") or wall.Representation is None:
        raise WallV6CreateError("Native physical Wall missing")
    level=ifcopenshell.util.element.get_container(wall)
    if level is None or level.GlobalId!=level_guid:
        raise WallV6CreateError("Native Wall original storey containment mismatch")
    reps={x.RepresentationIdentifier:x for x in wall.Representation.Representations}
    if set(reps)!={"Axis","Body"}:
        raise WallV6CreateError("Native Wall must have one Axis and one Body")
    axis_items=list(reps["Axis"].Items)
    if len(axis_items)!=1:
        raise WallV6CreateError("Native Wall source axis line missing")
    axis_item=axis_items[0]
    if axis_item.is_a("IfcPolyline"):
        pts=[tuple(float(v) for v in point.Coordinates)
             for point in axis_item.Points]
    elif axis_item.is_a("IfcIndexedPolyCurve") and axis_item.Segments is None:
        pts=[tuple(float(v) for v in row) for row in axis_item.Points.CoordList]
    else:
        raise WallV6CreateError("Unsupported new native axis curve type")
    x1,y1,z1,x2,y2,z2,h,t=params
    length=math.hypot(x2-x1,y2-y1)
    if (len(pts)!=2 or len(pts[0])!=2 or
            not np.allclose(pts,((0.,0.),(length,0.)),atol=1e-6)):
        raise WallV6CreateError("Native Wall axis length missing/mismatch")
    placement=ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement)
    world0=placement@np.array([0.,0.,0.,1.])
    world1=placement@np.array([length,0.,0.,1.])
    if (not np.allclose(world0[:3],(x1,y1,z1),atol=1e-6)
            or not np.allclose(world1[:3],(x2,y2,z2),atol=1e-6)):
        raise WallV6CreateError("Native Wall axis world start/end differ from XML")
    solids=[item for item in reps["Body"].Items if item.is_a("IfcExtrudedAreaSolid")]
    if len(solids)!=1 or not math.isclose(float(solids[0].Depth),h,abs_tol=1e-6):
        raise WallV6CreateError("Native Wall physical height differs from XML")
    settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
    shape=ifcopenshell.geom.create_shape(settings,wall)
    verts=np.asarray(shape.geometry.verts,dtype=float)
    if len(verts)<24 or len(verts)%3 or not np.isfinite(verts).all():
        raise WallV6CreateError("New native Wall lacks physical mesh")
    xyz=verts.reshape(-1,3)
    # Local centered 0.2m thickness; +X world axis is the v0.34 public case.
    if abs(y2-y1)<1e-8:
        expected=(min(x1,x2), y1-t/2, z1, max(x1,x2), y1+t/2, z1+h)
        actual=(*xyz.min(axis=0),*xyz.max(axis=0))
        if not np.allclose(actual,expected,atol=1e-5):
            raise WallV6CreateError("New Wall world body bounds differ from XML")
    return len(verts)//3


class WallV6CreateReport(CompileReport):
    def as_dict(self):
        out=super().as_dict()
        out.update({
            "status":"COMMITTED_SCOPED_IFC4X3_CREATE_WALL_V6",
            "compiler_version":"experimental-wall-create-v0.6",
            "full_native_write_parity":False,
            "matched_model_host_enabled":False,
            "scope":"one unhosted physical Wall, no hosted openings or connections",
        })
        return out


def compile_declarative_xml_v6_wall_create(source:Path,edited_xml:bytes,
                                            destination:Path)->WallV6CreateReport:
    source,destination=Path(source),Path(destination)
    if (not source.is_file() or source.is_symlink()
            or destination.exists() or destination.is_symlink()
            or source.resolve()==destination.resolve()):
        raise WallV6CreateError("Pinned original native source and unused output required")
    projection=project_ifc_v4(source)
    pre=parse_xml(projection.xml,expected_source_sha256=projection.source.source_sha256)
    post=parse_xml(edited_xml,expected_source_sha256=projection.source.source_sha256)
    original=bind_document(pre,projection=projection)
    edited=bind_document(post,projection=projection,verify_native_edges=False)
    delta=graph_diff(original.graph,edited.graph)
    if (len(delta.added_nodes)!=1 or delta.changed_nodes or delta.removed_nodes
            or len(delta.added_edges)!=1 or delta.removed_edges):
        raise WallV6CreateError("Only exactly one new isolated Wall and its storey edge allowed")
    name=delta.added_nodes[0]
    node=edited.graph.by_id()[name]
    edge=delta.added_edges[0]
    if (node.kind!="Wall" or node.provenance!="deterministic_new"
            or edge.relation!="in_storey" or edge.target!=name):
        raise WallV6CreateError("Only a new typed Wall in original storey is supported")
    attrs=dict(node.attributes)
    params=_parse_params(attrs)
    level=edited.graph.by_id().get(attrs["level"])
    if (level is None or level.kind!="Level" or
            level.provenance!="existing_source" or edge.source!=level.id):
        raise WallV6CreateError("New Wall must use original native storey")
    f=ifcopenshell.open(str(source))
    if f.schema!="IFC4X3" or abs(ifcopenshell.util.unit.calculate_unit_scale(f)-1.)>1e-8:
        raise WallV6CreateError("Original experimental source requires IFC4X3 metres")
    storey=f.by_guid(level.ifc_guid)
    if not storey.is_a("IfcBuildingStorey") or storey.Elevation is None or abs(float(storey.Elevation))>1e-8:
        raise WallV6CreateError("Only original ground level supported for single Wall create")
    if node.ifc_guid in {x.GlobalId for x in f.by_type("IfcRoot")}:
        raise WallV6CreateError("New Wall deterministic GUID already exists")
    body=_unique_context(f,"Body","MODEL_VIEW")
    axis=_unique_context(f,"Axis","GRAPH_VIEW")
    start_hash=snapshot_source(source).source_sha256
    if start_hash!=projection.source.source_sha256:
        raise WallV6CreateError("Original native input changed since read-only projection")
    x1,y1,z1,x2,y2,z2,h,t=params
    length=math.hypot(x2-x1,y2-y1)
    cos=(x2-x1)/length;sin=(y2-y1)/length
    def writer(target:Path):
        wall=ifcopenshell.api.root.create_entity(
            f,ifc_class="IfcWall",name="Trusted whole-XML v0.6 Wall")
        wall.GlobalId=node.ifc_guid
        wall.PredefinedType="NOTDEFINED"
        rep_body=ifcopenshell.api.geometry.add_wall_representation(
            f,context=body,length=length,height=h,thickness=t,offset=-t/2)
        rep_axis=ifcopenshell.api.geometry.add_axis_representation(
            f,context=axis,axis=((0.,0.),(length,0.)))
        ifcopenshell.api.geometry.assign_representation(
            f,product=wall,representation=rep_body)
        ifcopenshell.api.geometry.assign_representation(
            f,product=wall,representation=rep_axis)
        transform=np.eye(4,dtype="float64")
        transform[:3,:3]=[[cos,-sin,0.],[sin,cos,0.],[0.,0.,1.]]
        transform[:3,3]=(x1,y1,z1)
        ifcopenshell.api.geometry.edit_object_placement(
            f,product=wall,matrix=transform)
        ifcopenshell.api.spatial.assign_container(
            f,products=[wall],relating_structure=storey)
        f.write(str(target))
    def verify(target:Path):
        candidate=ifcopenshell.open(str(target))
        _check_physical_wall(candidate,node.ifc_guid,level.ifc_guid,params)
        _check_original_metre_step_preservation(source,target,node.ifc_guid)
        if snapshot_source(source).source_sha256!=start_hash:
            raise WallV6CreateError("Original native source changed during commit")
    stage_and_commit(destination,writer,verify)
    preserved=_check_original_metre_step_preservation(source,destination,node.ifc_guid)
    _check_physical_wall(ifcopenshell.open(str(destination)),node.ifc_guid,level.ifc_guid,params)
    result=snapshot_source(destination)
    if snapshot_source(source).source_sha256!=start_hash:
        raise WallV6CreateError("Original source changed after native transaction")
    mutation=Mutation("CREATE_WALL",name,node.ifc_guid,
                      post.managed_by_id()[name].span.line,
                      ("geometry","level"),"experimental whole-declarative-XML wall v0.6")
    return WallV6CreateReport(
        start_hash,result.source_sha256,
        projection.source.graph_fingerprint,result.graph_fingerprint,
        (mutation,),preserved,(),destination,True,
    )
