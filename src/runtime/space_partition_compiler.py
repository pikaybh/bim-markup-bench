"""Strict declarative state-diff to bounded native Space partition backend.

An agent edits ordinary <Wall>, <Space>, <Connects>, and <SpaceBoundary>
snapshot nodes, never a <Split> command. Only one source-proven rectangular
partition pattern may reach the trusted native compiler. All other Space
changes fail closed, and candidate output is re-projected and checked
against the *entire* edited semantic graph before atomic commit.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib

import ifcopenshell
from lxml import etree

from src.runtime.ifc_mutations import Mutation,UnsupportedIFCMutation
from src.runtime.space_partition_preflight import (
    UnsupportedSpacePartition, plan_rectangular_space_partition,
)
from src.runtime.space_partition_sandbox import sandbox_native_space_split
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.space_metadata_gate import (
    preflight_source_room_semantics,verify_native_space_metadata,
)
from src.runtime.transaction import stage_and_commit
from src.runtime.ifc_projection import project_ifc
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document


def _xml_compatible_attrs(node):
    return {k:str(v) for k,v in node.attrs().items() if k not in ("id","ifcGuid")}


def _canonical_native_graph(graph):
    """Compare identity/geometry after IFC serialization (nanometre precision).

    Local XML IDs and IFC GUID *attributes* are graph metadata, not BIM
    element state. Numeric projected coordinates are rounded to the same
    fixed 9 fractional digits as the IFC→XML projection; nonnumeric fields
    are compared exactly. This is tighter than the 1 micrometre model gate.
    """
    from decimal import Decimal, InvalidOperation
    numeric={"x","y","z","x1","y1","z1","x2","y2","z2",
             "width","depth","height","thickness","elevation",
             "offset","sill"}
    keyed={n.id:n.ifc_guid for n in graph.nodes}
    def attrs_normalized(node):
        result=[]
        for name,value in node.attributes:
            if name in ("id","ifcGuid"):
                continue
            if name in numeric:
                try:
                    value=format(Decimal(value).quantize(Decimal("0.000000001")),"f")
                    value=value.rstrip("0").rstrip(".") if "." in value else value
                    if value in ("","-0"):value="0"
                except (InvalidOperation,ValueError) as exc:
                    raise UnsupportedSpacePartition("Invalid numeric IFC geometry state") from exc
            result.append((name,value))
        return tuple(result)
    products={n.ifc_guid:(n.kind,attrs_normalized(n)) for n in graph.nodes}
    relations={(e.relation,keyed[e.source],keyed[e.target])
               for e in graph.edges}
    return products,relations


def _one_space_partition_delta(before_doc,after_doc,before,after):
    from src.runtime.semantic_graph import graph_diff
    delta=graph_diff(before.graph,after.graph)
    prior=before.graph.by_id();future=after.graph.by_id()
    changed=[name for name in delta.changed_nodes
             if prior[name].kind=="Space"]
    created_space=[name for name in delta.added_nodes
                   if future[name].kind=="Space"]
    created_walls=[name for name in delta.added_nodes
                   if future[name].kind=="Wall"]
    if len(changed)!=1 or len(created_space)!=1 or len(created_walls)!=1:
        raise UnsupportedSpacePartition(
            "Bounded Space partition requires one original Space, one new Space and one new Wall")
    if (set(delta.changed_nodes)!={changed[0]}
            or set(delta.added_nodes)!={created_space[0],created_walls[0]}
            or delta.removed_nodes or delta.removed_edges and any(
                edge.relation!="space_boundary" for edge in delta.removed_edges)
            or any(edge.relation not in ("space_boundary","connects","aggregated_in_storey","in_storey")
                   for edge in delta.added_edges)):
        raise UnsupportedSpacePartition("Space partition contains unrelated semantic graph changes")
    room=prior[changed[0]]
    new_room=future[created_space[0]]
    branch=future[created_walls[0]]
    if (room.provenance!="existing_source" or
            branch.provenance!="deterministic_new" or
            new_room.provenance!="deterministic_new"):
        raise UnsupportedSpacePartition("Space partition source/new identity provenance invalid")
    old_attrs=dict(room.attributes)
    new_attrs=dict(future[changed[0]].attributes)
    fields={k for k in old_attrs|new_attrs if old_attrs.get(k)!=new_attrs.get(k)}
    if fields!={"depth"}:
        raise UnsupportedSpacePartition("Only source Space depth may change in bounded partition")
    if len([e for e in delta.added_edges if e.relation=="connects"])!=2:
        raise UnsupportedSpacePartition("Partition must contain exactly two declarative host-wall connections")
    if (len([e for e in delta.added_edges if e.relation=="space_boundary"])<2
            or not any(e.target==created_walls[0] and e.source==created_space[0]
                       for e in delta.added_edges if e.relation=="space_boundary")
            or not any(e.target==created_walls[0] and e.source==changed[0]
                       for e in delta.added_edges if e.relation=="space_boundary")):
        raise UnsupportedSpacePartition("Partition lacks two edited declarative Wall/Space boundary states")
    return changed[0],created_space[0],created_walls[0]


def _wall_only_edit(before_doc,after_doc,wall_id:str):
    """Build Wall/Connects-only *source state*, not a mutation command."""
    original=etree.fromstring(before_doc.source_bytes)
    edited=etree.fromstring(after_doc.source_bytes)
    ns=before_doc.namespace
    orig_elements=original.find(".//{"+ns+"}Elements")
    orig_rels=original.find(".//{"+ns+"}Relations")
    edited_elements=edited.find(".//{"+ns+"}Elements")
    edited_rels=edited.find(".//{"+ns+"}Relations")
    if any(x is None for x in (orig_elements,orig_rels,edited_elements,edited_rels)):
        raise UnsupportedSpacePartition("Missing XML state graph sections")
    walls=[node for node in edited_elements if node.get("id")==wall_id
           and node.tag=="{"+ns+"}Wall"]
    if len(walls)!=1 or any(node.get("id")==wall_id for node in orig_elements):
        raise UnsupportedSpacePartition("New Wall declaration not unique")
    orig_elements.append(etree.fromstring(etree.tostring(walls[0])))
    # Connectivity is authored by XML: only two fresh Connects references
    # are copied from the *edited* document, never generated from the GT.
    current={(rel.get("from"),rel.get("to")) for rel in orig_rels
             if rel.tag=="{"+ns+"}Connects"}
    added=[rel for rel in edited_rels if rel.tag=="{"+ns+"}Connects"
           and (rel.get("from"),rel.get("to")) not in current]
    if len(added)!=2 or any(rel.get("to")!=wall_id for rel in added):
        raise UnsupportedSpacePartition("New Wall requires two directed old-host T connection declarations")
    for rel in added:
        orig_rels.append(etree.fromstring(etree.tostring(rel)))
    return etree.tostring(original,encoding="utf-8",xml_declaration=True)


def _validate_partition_xml_geometry(plan,before,after,room_id,far_id,wall_id):
    old=before.graph.by_id();new=after.graph.by_id()
    near=dict(new[room_id].attributes)
    far=dict(new[far_id].attributes)
    original=dict(old[room_id].attributes)
    wall=dict(new[wall_id].attributes)
    if any(near[k]!=original[k] for k in ("x","y","z","width","height","level")):
        raise UnsupportedSpacePartition("Near source Space changed unrelated attributes")
    if any(far[k]!=original[k] for k in ("x","z","width","height","level")):
        raise UnsupportedSpacePartition("Far Space changed unrelated attributes")
    if any(wall[k]!=original[k] for k in ("z",) if k in wall):
        raise UnsupportedSpacePartition("Wall and source Space have incompatible origins")
    for attrs,lo,hi in ((near,plan.near_box_min,plan.near_box_max),
                        (far,plan.far_box_min,plan.far_box_max)):
        for key,value in (("x",lo[0]),("y",lo[1]),("z",lo[2]),
                          ("width",hi[0]-lo[0]),("depth",hi[1]-lo[1]),("height",hi[2]-lo[2])):
            if abs(float(attrs[key])-value)>1e-7:
                raise UnsupportedSpacePartition("Edited XML Space body diverges from true native partition")


def _root_integrity_space_split(source,result,plan,actions,new_space_guid,new_boundary_guids):
    """Whitelist every old/new IfcRoot identity and its allowed edits."""
    a=ifcopenshell.open(str(source));b=ifcopenshell.open(str(result))
    prior={x.GlobalId:x for x in a.by_type("IfcRoot")}
    final={x.GlobalId:x for x in b.by_type("IfcRoot")}
    if set(prior)-set(final):
        raise UnsupportedSpacePartition("Existing native IFC Root was removed by Space split")
    created={new_space_guid,*new_boundary_guids}
    created|={op.ifc_guid for op in actions if op.operation in
              ("CREATE_WALL","ADD_WALL_CONNECTION","ADD_WALL_PATH_CONNECTION")}
    other_new=set(final)-set(prior)-created
    if any(not final[k].is_a("IfcRelContainedInSpatialStructure") for k in other_new):
        raise UnsupportedSpacePartition("Unapproved new IFC root introduced by native Space split")
    allowed_changed={plan.existing_space_id}
    allowed_changed.update(p.boundary_id for p in plan.boundary_patches
                           if p.action!="KEEP_NEAR")
    for relation in a.by_type("IfcRelAggregates"):
        if any(x.GlobalId==plan.existing_space_id for x in relation.RelatedObjects):
            allowed_changed.add(relation.GlobalId)
    for relation in a.by_type("IfcRelContainedInSpatialStructure"):
        allowed_changed.add(relation.GlobalId)
    unchanged=0
    for guid in set(prior)&set(final):
        if prior[guid].is_a()!=final[guid].is_a():
            raise UnsupportedSpacePartition("Native IFC Root class changed during partition")
        if str(prior[guid])==str(final[guid]):
            unchanged+=1
        elif guid not in allowed_changed:
            raise UnsupportedSpacePartition("Unrelated native IFC Root changed during Space split")
    return unchanged


def compile_bounded_space_state(source:Path, destination:Path,
                                before_doc,after_doc,before,after,compiler):
    from src.runtime.compiler import CompileReport,CompilerError
    import ifcopenshell.util.placement

    room_id,far_id,wall_id=_one_space_partition_delta(
        before_doc,after_doc,before,after)
    wall_xml=_wall_only_edit(before_doc,after_doc,wall_id)
    before_sha=hashlib.sha256(source.read_bytes()).hexdigest()
    if before_sha!=before_doc.source_model_sha256:
        raise UnsupportedSpacePartition("Original IFC source changed during Space preflight")
    with TemporaryDirectory(prefix="g1-xml-space-partition-") as directory:
        joined=Path(directory)/"native-joined.ifc"
        wall_result=compiler(source,wall_xml,joined)
        if [op.operation for op in wall_result.operations].count("CREATE_WALL")!=1:
            raise UnsupportedSpacePartition("Generated Wall was not compiled independently")
        if [op.operation for op in wall_result.operations].count("ADD_WALL_PATH_CONNECTION")!=2:
            raise UnsupportedSpacePartition("Two T-type Wall connections are not verified")
        original=ifcopenshell.open(str(source))
        candidate=ifcopenshell.open(str(joined))
        room_guid=before.graph.by_id()[room_id].ifc_guid
        # Existing instance identity/type/Pset/QTO must not be silently
        # duplicated or reclassified by the geometric Space split.
        preflight_source_room_semantics(original,room_guid)
        wall_guid=after.graph.by_id()[wall_id].ifc_guid
        far_guid=after.graph.by_id()[far_id].ifc_guid
        plan=plan_rectangular_space_partition(original,candidate,room_guid,wall_guid)
        _validate_partition_xml_geometry(plan,before,after,room_id,far_id,wall_id)
        split_result={}
        def writer(stage):
            nonlocal split_result
            model=ifcopenshell.open(str(joined))
            split_result=sandbox_native_space_split(
                model,plan,source_sha=before_sha,
                validated_new_space_guid=far_guid)
            if split_result["new_space_guid"]!=far_guid:
                raise UnsupportedSpacePartition("Native Space identity disagrees with declarative binder")
            model.write(str(stage))

        def validator(stage):
            if hashlib.sha256(source.read_bytes()).hexdigest()!=before_sha:
                raise UnsupportedSpacePartition("Original IFC bytes changed before Space commit")
            projected=project_ifc(stage)
            output_xml=parse_xml(projected.xml,
                expected_source_sha256=projected.source.source_sha256)
            bound=bind_document(output_xml,projection=projected)
            desired=_canonical_native_graph(after.graph)
            actual=_canonical_native_graph(bound.graph)
            if desired!=actual:
                a_nodes,a_edges=actual
                d_nodes,d_edges=desired
                raise UnsupportedSpacePartition(
                    "Native Space split result does not match whole edited XML state "
                    f"(products +{len(a_nodes.keys()-d_nodes.keys())}/"
                    f"-{len(d_nodes.keys()-a_nodes.keys())}; edges "
                    f"+{len(a_edges-d_edges)}/-{len(d_edges-a_edges)})")
            if not split_result or split_result["total_target_boundary_count"]!=13:
                raise UnsupportedSpacePartition("Native first-level Space boundaries incomplete")
            _root_integrity_space_split(
                source,stage,plan,wall_result.operations,far_guid,
                split_result["added_boundary_guids"])
            verify_native_space_metadata(original,ifcopenshell.open(str(stage)),
                                         room_guid,far_guid)

        stage_and_commit(destination,writer,validator)
        if hashlib.sha256(source.read_bytes()).hexdigest()!=before_sha:
            raise UnsupportedSpacePartition("Original IFC bytes changed after Space commit")
        output=snapshot_source(destination)
        evidence=Mutation(
            "SPLIT_SPACE",room_id,room_guid,
            after_doc.managed_by_id()[room_id].span.line,
            ("depth","new-space","space-boundary"),
            "bounded two-Space declarative state reconciliation")
        return CompileReport(
            before_sha,output.source_sha256,before.graph.fingerprint,
            after.graph.fingerprint,(*wall_result.operations,evidence),
            _root_integrity_space_split(
                source,destination,plan,wall_result.operations,far_guid,
                split_result["added_boundary_guids"]),
            (),destination,True)
