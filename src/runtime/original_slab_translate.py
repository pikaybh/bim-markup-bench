"""v0.29 exact-source original PUBLIC Slab vertical placement translation.

Only trusted opt-in compiler support, NEVER an LLM-facing IFC action.
The author edits complete ordinary declarative XML, changing one preexisting
Slab's z only by -0.5 m. The original IFC shared CartesianPoint is used by
56 native placements and MUST NOT be mutated. Allocate one private point,
rebind only target's exclusively owned IfcAxis2Placement3D.Location and
independently verify whole native Root/STEP and complete reprojected graph.
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
from src.runtime.ifc_projection import project_ifc

SOURCE_SHA="16568e7c4b8b9d62567a7a199101269daa6e5b1b7535cec095b8e233ae2ef6ac"
Z_DELTA=-0.5
TOL=1e-8


def require(ok:bool,msg:str)->None:
    if not ok:raise UnsupportedIFCMutation(msg)


def close(a:float,b:float,tol:float=TOL)->bool:
    return math.isclose(float(a),float(b),abs_tol=tol,rel_tol=0.)


@dataclass(frozen=True)
class SlabMovePlan:
    guid:str
    source_sha256:str
    relative_placement_id:int
    shared_point_id:int
    original_point_reference_count:int
    old_local_coords:tuple[float,...]
    native_root_count:int
    native_step_count:int


def strict_slab_preflight(source:Path,guid:str)->SlabMovePlan:
    snap=snapshot_source(source)
    require(snap.source_sha256==SOURCE_SHA,"Source original PUBLIC normalized IFC SHA differs")
    f=ifcopenshell.open(str(source))
    require(f.schema=="IFC4X3" and close(ifcopenshell.util.unit.calculate_unit_scale(f),1.),
            "Original Slab source is not IFC4X3 metres")
    slab=by_guid_or_none(f,guid)
    require(slab is not None and slab.is_a("IfcSlab")
            and slab.PredefinedType=="FLOOR",
            "Original typed target is not an existing FLOOR IfcSlab")
    refs=list(f.get_inverse(slab))
    require(Counter(x.is_a() for x in refs)==Counter({
        "IfcRelAssociatesMaterial":1,
        "IfcRelDefinesByType":1,
        "IfcRelDefinesByProperties":3,
        "IfcRelContainedInSpatialStructure":1,
    }),"Original Slab native relation inverse inventory unexpected")
    for rel in refs:
        if rel.is_a("IfcRelContainedInSpatialStructure"):
            require(slab in rel.RelatedElements and
                    rel.RelatingStructure.is_a("IfcBuildingStorey"),
                    "Original Slab storey membership changed")
        else:
            require(slab in rel.RelatedObjects,
                    "Original Slab material/type/property source association changed")
    placement=slab.ObjectPlacement
    require(placement is not None and placement.is_a("IfcLocalPlacement")
            and tuple(f.get_inverse(placement))==(slab,),
            "Slab native object placement is shared or not a local placement")
    relative=placement.RelativePlacement
    require(relative is not None and relative.is_a("IfcAxis2Placement3D")
            and tuple(f.get_inverse(relative))==(placement,)
            and relative.Axis is None and relative.RefDirection is None,
            "Source slab relative frame is not exclusively owned identity")
    original_point=relative.Location
    require(original_point is not None and original_point.is_a("IfcCartesianPoint"),
            "Original Slab native placement point missing")
    coords=tuple(float(x) for x in original_point.Coordinates)
    require(len(coords)==3 and all(close(v,0.) for v in coords),
            "Original Slab source placement not origin zero")
    inv=f.get_total_inverses(original_point)
    require(inv==56,"Original CartesianPoint is not the expected shared 56-placement source")
    # Source-specific support only for target top slab: the other slab lies at
    # different storey/elevation and must never become a silent variant.
    projection=project_ifc(source,allow_original_flipped_slab=True)
    rows=[line for line in projection.xml.decode("utf8").splitlines()
          if '<Slab ' in line and ('ifcGuid="'+guid+'"') in line]
    require(len(rows)==1 and 'z="3.8"' in rows[0]
            and 'width="10.4"' in rows[0]
            and 'depth="10.375"' in rows[0]
            and 'thickness="0.3"' in rows[0],
            "Original top slab source geometry/identity does not match original public task")
    # Profile is represented by exactly one original 300mm rectangular
    # flipped-Z native extrusion verified by the independent projector.
    product_shape=slab.Representation
    require(product_shape is not None and len(product_shape.Representations)==1
            and len(product_shape.Representations[0].Items)==1
            and product_shape.Representations[0].Items[0].is_a("IfcExtrudedAreaSolid")
            and close(product_shape.Representations[0].Items[0].Depth,.3),
            "Original physical Slab extrusion/geometry differs")
    return SlabMovePlan(
        guid,snap.source_sha256,relative.id(),original_point.id(),inv,coords,
        len(f.by_type("IfcRoot")),len(list(f)),
    )


def original_slab_xml_delta(before,after,delta)->str:
    require(len(delta.changed_nodes)==1
            and not delta.added_nodes and not delta.removed_nodes
            and not delta.added_edges and not delta.removed_edges,
            "Slab move requires exactly one original XML source node change")
    key=delta.changed_nodes[0]
    pre=before.graph.by_id()[key]
    post=after.graph.by_id()[key]
    require(pre.kind==post.kind=="Slab" and
            pre.provenance=="existing_source" and pre.ifc_guid==post.ifc_guid,
            "Only one original existing IfcSlab Z may change")
    before_attrs=dict(pre.attributes);after_attrs=dict(post.attributes)
    changed={name for name in before_attrs.keys()|after_attrs.keys()
             if before_attrs.get(name)!=after_attrs.get(name)}
    require(changed=={"z"},
            "Slab vertical move may edit only the existing typed z coordinate")
    require(close(float(before_attrs["z"]),3.8)
            and close(float(after_attrs["z"]),3.3)
            and close(float(after_attrs["z"])-float(before_attrs["z"]),Z_DELTA),
            "Original Slab requires exact −0.5 m vertical displacement")
    require(all(close(float(before_attrs[k]),v)
                for k,v in (("x",-.2),("y",-.175),("width",10.4),
                            ("depth",10.375),("thickness",.3))),
            "Original Slab typed geometry not the pinned source rectangle")
    return key


def verify_slab_native(
    source:Path,result:Path,plan:SlabMovePlan,
)->int:
    require(strict_slab_preflight(source,plan.guid)==plan,
            "Original Slab preflight changed after staging")
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(result))
    require(b.schema=="IFC4X3" and close(ifcopenshell.util.unit.calculate_unit_scale(b),1.),
            "Slab output schema or metric source units changed")
    original_roots={x.GlobalId:(x.is_a(),str(x)) for x in a.by_type("IfcRoot")}
    result_roots={x.GlobalId:(x.is_a(),str(x)) for x in b.by_type("IfcRoot")}
    require(original_roots==result_roots and len(result_roots)==plan.native_root_count,
            "Native Slab translation changed original IfcRoot classes/GUIDs/data")
    pa={x.id():str(x) for x in a};pb={x.id():str(x) for x in b}
    require(len(pa)==plan.native_step_count
            and not (pa.keys()-pb.keys())
            and len(pb.keys()-pa.keys())==1,
            "Slab translation must add one point and remove no old STEP records")
    new_id=next(iter(pb.keys()-pa.keys()))
    added=b.by_id(new_id)
    require(added.is_a("IfcCartesianPoint")
            and len(added.Coordinates)==3
            and all(close(x,y) for x,y in zip(
                added.Coordinates,(0.,0.,Z_DELTA))),
            "The only added native object is not private slab Z placement point")
    changed={i for i in pa.keys()&pb.keys() if pa[i]!=pb[i]}
    require(changed=={plan.relative_placement_id},
            "Any other existing native IFC STEP entity changed")
    rp=b.by_id(plan.relative_placement_id)
    require(rp.is_a("IfcAxis2Placement3D") and rp.Location==added
            and rp.Axis is None and rp.RefDirection is None,
            "Original source slab placement was not exclusively rebound")
    oldpoint_a=a.by_id(plan.shared_point_id)
    oldpoint_b=b.by_id(plan.shared_point_id)
    require(str(oldpoint_a)==str(oldpoint_b)
            and a.get_total_inverses(oldpoint_a)==plan.original_point_reference_count
            and b.get_total_inverses(oldpoint_b)==plan.original_point_reference_count-1,
            "Original shared source placement point was changed")
    require(tuple(b.get_inverse(added))==(rp,),
            "New slab placement point is shared or referenced elsewhere")
    wall=b.by_guid(plan.guid)
    mat=ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement)
    original_mat=ifcopenshell.util.placement.get_local_placement(
        a.by_guid(plan.guid).ObjectPlacement)
    require(all(close(mat[i,3]-original_mat[i,3],expected)
                for i,expected in enumerate((0.,0.,Z_DELTA))),
            "Original Slab target native world placement is not Z minus 0.5")
    return len(result_roots)


def compile_original_slab_down(source:Path,destination:Path,
                               before_doc,after_doc,before,after):
    from src.runtime.compiler import CompileReport
    delta=graph_diff(before.graph,after.graph)
    key=original_slab_xml_delta(before,after,delta)
    guid=before.graph.by_id()[key].ifc_guid
    require(snapshot_source(source).source_sha256==before_doc.source_model_sha256,
            "Submitted slab XML bound to different immutable IFC source")
    plan=strict_slab_preflight(source,guid)
    mutation=Mutation(
        "MOVE_ORIGINAL_SLAB_DOWN_0_5M",key,guid,
        before_doc.managed_by_id()[key].span.line,("z",),
        "single original IFC4X3 Slab -0.5m Z-only placement; shared point untouched",
    )
    def writer(stage:Path)->None:
        require(snapshot_source(source).source_sha256==plan.source_sha256,
                "Original native Slab source changed before staged writing")
        f=ifcopenshell.open(str(source))
        slab=f.by_guid(guid)
        relative=slab.ObjectPlacement.RelativePlacement
        require(relative.id()==plan.relative_placement_id
                and relative.Location.id()==plan.shared_point_id,
                "Original Slab placement references changed before edit")
        private=f.create_entity("IfcCartesianPoint",Coordinates=(0.,0.,Z_DELTA))
        relative.Location=private
        f.write(str(stage))
    def validator(stage:Path)->None:
        require(snapshot_source(source).source_sha256==plan.source_sha256,
                "Original input changed during slab validator")
        verify_slab_native(source,stage,plan)
        from src.runtime.xml_parser import parse_xml
        from src.runtime.binder import bind_document
        from src.runtime.space_partition_compiler import _canonical_native_graph
        projected=project_ifc(stage,allow_original_flipped_slab=True)
        doc=parse_xml(projected.xml,expected_source_sha256=projected.source.source_sha256)
        native=bind_document(doc,projection=projected)
        require(_canonical_native_graph(native.graph)==
                _canonical_native_graph(after.graph),
                "Full native Slab model reprojection differs from complete authored XML")
    stage_and_commit(destination,writer,validator)
    require(snapshot_source(source).source_sha256==plan.source_sha256,
            "Original Slab native IFC input changed after publishing")
    verified=verify_slab_native(source,destination,plan)
    snapshot=snapshot_source(destination)
    return CompileReport(
        plan.source_sha256,snapshot.source_sha256,
        delta.before_fingerprint,delta.after_fingerprint,
        (mutation,),verified,(),destination,True,
    )
