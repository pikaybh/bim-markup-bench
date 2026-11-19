"""v0.28 strictly bounded PUBLIC original Wall center rotation.

Trusted compiler backend, not a model-facing operation. One existing Wall's
four ordinary XML endpoints represent a +90 degree planar Z rotation about
its center. The source-original native placement's RefDirection is SHARED by
other 13 IFC placements; it must be preserved. Allocate exactly one PRIVATE
new IfcDirection, and update only this Wall's exclusive placement point and
its own IfcAxis2Placement3D.RefDirection link.

Do not enlarge this into general wall orientation, IFC4, or STEP rewriting.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.placement
import ifcopenshell.util.unit

from src.runtime.ifc_mutations import Mutation,UnsupportedIFCMutation,by_guid_or_none
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.semantic_graph import graph_diff
from src.runtime.transaction import stage_and_commit

PINNED_ORIGINAL_NORMALIZED_SHA="16568e7c4b8b9d62567a7a199101269daa6e5b1b7535cec095b8e233ae2ef6ac"
BASE_POINT=(7.5,13.9952,0.)
BASE_LOCAL_X=(-1.,0.,0.)
BASE_LENGTH=5.
TOL=1e-7


@dataclass(frozen=True)
class WallRotationPlan:
    target_guid:str
    source_sha256:str
    point_id:int
    relative_placement_id:int
    shared_direction_id:int
    wall_placement_id:int
    source_step_count:int
    source_root_count:int
    axis_local_length:float


def near(a:float,b:float,tol:float=TOL)->bool:
    return math.isclose(float(a),float(b),abs_tol=tol,rel_tol=0)


def _assert(cond:bool,msg:str)->None:
    if not cond:raise UnsupportedIFCMutation(msg)


def plan_original_wall_rotation(source:Path,guid:str)->WallRotationPlan:
    snap=snapshot_source(source)
    _assert(snap.source_sha256==PINNED_ORIGINAL_NORMALIZED_SHA,
            "Unsupported normalized original public source checksum")
    f=ifcopenshell.open(str(source))
    _assert(f.schema=="IFC4X3" and near(ifcopenshell.util.unit.calculate_unit_scale(f),1.),
            "Original source must be IFC4X3 metres")
    wall=by_guid_or_none(f,guid)
    _assert(wall is not None and wall.is_a("IfcWall")
            and not wall.HasOpenings
            and not wall.ConnectedFrom and not wall.ConnectedTo
            and not wall.ProvidesBoundaries,
            "Original Wall not uniquely isolated from openings/connections/boundaries")
    relations=list(f.get_inverse(wall))
    _assert(Counter(x.is_a() for x in relations)==Counter({
        "IfcRelDefinesByProperties":3,
        "IfcRelDefinesByType":1,
        "IfcRelAssociatesMaterial":1,
        "IfcRelAssociatesClassification":1,
        "IfcRelContainedInSpatialStructure":1,
    }),"Unrecognized original Wall non-placement inverse dependency")
    for rel in relations:
        if rel.is_a("IfcRelDefinesByProperties"):
            _assert(tuple(rel.RelatedObjects)==(wall,),
                    "Original Wall property-set is not exclusively assigned")
        elif rel.is_a("IfcRelContainedInSpatialStructure"):
            _assert(wall in rel.RelatedElements and rel.RelatingStructure.is_a("IfcBuildingStorey"),
                    "Original Wall storey assignment missing")
        else:
            _assert(wall in rel.RelatedObjects,
                    "Original Wall's shared metadata references changed")

    placement=wall.ObjectPlacement
    _assert(placement is not None and placement.is_a("IfcLocalPlacement")
            and tuple(f.get_inverse(placement))==(wall,),
            "Original Wall placement is not exclusively owned")
    rp=placement.RelativePlacement
    _assert(rp.is_a("IfcAxis2Placement3D")
            and tuple(f.get_inverse(rp))==(placement,),
            "Original Wall relative placement is shared or unsupported")
    loc=rp.Location
    direction=rp.RefDirection
    axis=rp.Axis
    _assert(loc is not None and loc.is_a("IfcCartesianPoint")
            and tuple(f.get_inverse(loc))==(rp,),
            "Original Wall placement CartesianPoint is shared or unsupported")
    _assert(direction is not None and direction.is_a("IfcDirection")
            and f.get_total_inverses(direction)>1,
            "Expected original shared source direction inventory changed")
    _assert(axis is not None and tuple(float(x) for x in axis.DirectionRatios)==(0.,0.,1.),
            "Original wall Z axis is not upright")
    _assert(len(loc.Coordinates)==3
            and all(near(x,y) for x,y in zip(loc.Coordinates,BASE_POINT))
            and tuple(float(x) for x in direction.DirectionRatios)==BASE_LOCAL_X,
            "Original public rotation Wall's geometric anchor differs")

    reps=wall.Representation.Representations
    axes=[r for r in reps if r.RepresentationIdentifier=="Axis" and r.RepresentationType=="Curve2D"]
    bodies=[r for r in reps if r.RepresentationIdentifier=="Body" and r.RepresentationType=="SweptSolid"]
    _assert(len(axes)==len(bodies)==1 and len(axes[0].Items)==1
            and axes[0].Items[0].is_a("IfcPolyline"),
            "Original public Wall lacks one exact straight native 2D axis")
    points=axes[0].Items[0].Points
    _assert(len(points)==2,"Original native 2D wall axis has wrong vertex count")
    coords=[tuple(float(v) for v in p.Coordinates) for p in points]
    _assert(coords==[(0.,0.),(5.,0.)],
            "Original wall source axis is not the expected 5m straight segment")
    _assert(near(BASE_LENGTH,coords[1][0]-coords[0][0]),
            "Native wall axis length unexpectedly changed")
    for p in f.by_type("IfcProduct"):
        if p!=wall:
            _assert(p.ObjectPlacement!=placement,
                    "Other product shares original Wall ObjectPlacement")

    return WallRotationPlan(
        guid,snap.source_sha256,loc.id(),rp.id(),direction.id(),
        placement.id(),len(list(f)),len(f.by_type("IfcRoot")),BASE_LENGTH,
    )


def _expected_four_coords(
    old:dict[str,str],
)->dict[str,float]:
    x1,y1=float(old["x1"]),float(old["y1"])
    x2,y2=float(old["x2"]),float(old["y2"])
    center=((x1+x2)/2.,(y1+y2)/2.)
    # Pure mathematical anticlockwise 90° around original midpoint.
    return {
        "x1":center[0]-(y1-center[1]),
        "y1":center[1]+(x1-center[0]),
        "x2":center[0]-(y2-center[1]),
        "y2":center[1]+(x2-center[0]),
    }


def rotation_xml_plan(before,after,delta)->tuple[str,dict[str,float]]:
    _assert(len(delta.changed_nodes)==1
            and not delta.removed_nodes and not delta.added_nodes
            and not delta.removed_edges and not delta.added_edges,
            "Expected exactly one original Wall coordinate update")
    nodeid=delta.changed_nodes[0]
    old=before.graph.by_id()[nodeid]
    new=after.graph.by_id()[nodeid]
    _assert(old.kind==new.kind=="Wall" and old.provenance=="existing_source"
            and old.ifc_guid==new.ifc_guid,
            "Only original existing Wall may rotate")
    oldattrs=dict(old.attributes)
    newattrs=dict(new.attributes)
    changed={field for field in set(oldattrs)|set(newattrs)
             if oldattrs.get(field)!=newattrs.get(field)}
    _assert(changed=={"x1","y1","x2","y2"},
            "Rotation may change only the four original Wall endpoint coordinates")
    expected=_expected_four_coords(oldattrs)
    _assert(all(near(float(newattrs[key]),expected[key]) for key in expected),
            "Original Wall XML is not an exact +90° midpoint rotation")
    _assert(all(near(float(oldattrs[key]),val) for key,val in zip(
        ("x1","y1","z1","x2","y2","z2"),(7.5,13.9952,0.,2.5,13.9952,0.))),
        "Unexpected original Wall XML geometry anchor")
    return nodeid,expected


def _step(model:ifcopenshell.file)->dict[int,str]:
    return {x.id():str(x) for x in model}


def verify_wall_rotation(
    source:Path,output:Path,plan:WallRotationPlan,
)->int:
    _assert(plan_original_wall_rotation(source,plan.target_guid)==plan,
            "Original IFC Wall rotation native preflight changed")
    before=ifcopenshell.open(str(source))
    after=ifcopenshell.open(str(output))
    _assert(before.schema==after.schema=="IFC4X3"
            and near(ifcopenshell.util.unit.calculate_unit_scale(after),1.),
            "Native Wall rotation changed IFC schema/units")
    oldroots={x.GlobalId:(x.is_a(),str(x)) for x in before.by_type("IfcRoot")}
    newroots={x.GlobalId:(x.is_a(),str(x)) for x in after.by_type("IfcRoot")}
    _assert(len(newroots)==plan.source_root_count and oldroots==newroots,
            "Any original IfcRoot GUID, class or serialized state mutated")
    oldstep=_step(before);newstep=_step(after)
    _assert(len(oldstep)==plan.source_step_count
            and not (oldstep.keys()-newstep.keys())
            and len(newstep.keys()-oldstep.keys())==1,
            "Expected exactly one added native IfcDirection and zero removed STEP")
    new_id=next(iter(newstep.keys()-oldstep.keys()))
    new_direction=after.by_id(new_id)
    _assert(new_direction.is_a("IfcDirection")
            and tuple(float(x) for x in new_direction.DirectionRatios)==(0.,-1.,0.)
            and tuple(after.get_inverse(new_direction))==(after.by_id(plan.relative_placement_id),),
            "New native Wall-exclusive IfcDirection malformed/shared")
    changed={eid for eid in oldstep.keys()&newstep.keys()
             if oldstep[eid]!=newstep[eid]}
    _assert(changed=={plan.point_id,plan.relative_placement_id},
            "Unrelated original native STEP entity was modified")
    _assert(oldstep[plan.shared_direction_id]==newstep[plan.shared_direction_id],
            "Original RefDirection shared by other IFC objects was modified")
    _assert(after.get_total_inverses(after.by_id(plan.shared_direction_id))==
            before.get_total_inverses(before.by_id(plan.shared_direction_id))-1,
            "Original shared source direction reference count changed unexpectedly")
    location=after.by_id(plan.point_id)
    rp=after.by_id(plan.relative_placement_id)
    _assert(location.is_a("IfcCartesianPoint")
            and all(near(x,y) for x,y in zip(location.Coordinates,(5.,16.4952,0.)))
            and rp.is_a("IfcAxis2Placement3D")
            and rp.Location==location and rp.RefDirection==new_direction,
            "Original Wall physical placement did not rotate about midpoint")
    output_wall=after.by_guid(plan.target_guid)
    axis=ifcopenshell.util.placement.get_local_placement(output_wall.ObjectPlacement)
    _assert(all(near(axis[i,3],v) for i,v in enumerate((5.,16.4952,0.)))
            and all(near(axis[i,0],v) for i,v in enumerate((0.,-1.,0.))),
            "Original target IFC Wall local X rotation matrix is not +90°")
    return len(oldroots)


def compile_original_wall_center_rotation(source:Path,destination:Path,
                                          before_doc,after_doc,before,after):
    from src.runtime.compiler import CompileReport
    delta=graph_diff(before.graph,after.graph)
    nodeid,expected=rotation_xml_plan(before,after,delta)
    guid=before.graph.by_id()[nodeid].ifc_guid
    _assert(snapshot_source(source).source_sha256==before_doc.source_model_sha256,
            "Original document IFC source checksum mismatch")
    plan=plan_original_wall_rotation(source,guid)
    mutation=Mutation(
        "ROTATE_ORIGINAL_WALL_PLUS_90_CENTER",nodeid,guid,
        before_doc.managed_by_id()[nodeid].span.line,
        ("x1","y1","x2","y2"),
        "original public straight wall +90deg Z about midpoint; private new direction",
    )

    def writer(stage:Path)->None:
        _assert(snapshot_source(source).source_sha256==plan.source_sha256,
                "Original source checksum changed during edit")
        f=ifcopenshell.open(str(source))
        wall=f.by_guid(guid)
        rp=wall.ObjectPlacement.RelativePlacement
        location=rp.Location
        _assert(rp.id()==plan.relative_placement_id and location.id()==plan.point_id,
                "Original native placement pointer changed in stage")
        location.Coordinates=(expected["x1"],expected["y1"],float(location.Coordinates[2]))
        newdir=f.create_entity("IfcDirection",DirectionRatios=(0.,-1.,0.))
        rp.RefDirection=newdir
        f.write(str(stage))

    def validator(stage:Path)->None:
        _assert(snapshot_source(source).source_sha256==plan.source_sha256,
                "Original source changed during validation")
        verify_wall_rotation(source,stage,plan)
        from src.runtime.ifc_projection import project_ifc
        from src.runtime.xml_parser import parse_xml
        from src.runtime.binder import bind_document
        from src.runtime.space_partition_compiler import _canonical_native_graph
        projection=project_ifc(stage)
        doc=parse_xml(projection.xml,expected_source_sha256=projection.source.source_sha256)
        rebound=bind_document(doc,projection=projection)
        _assert(_canonical_native_graph(rebound.graph)==
                _canonical_native_graph(after.graph),
                "Complete native rotated IFC graph does not match XML submitted state")
    stage_and_commit(destination,writer,validator)
    _assert(snapshot_source(source).source_sha256==plan.source_sha256,
            "Original IFC source changed after native output commit")
    verified=verify_wall_rotation(source,destination,plan)
    snapshot=snapshot_source(destination)
    return CompileReport(
        plan.source_sha256,snapshot.source_sha256,
        delta.before_fingerprint,delta.after_fingerprint,
        (mutation,),verified,(),destination,True,
    )
