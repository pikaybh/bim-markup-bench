"""Strict single existing IfcSpace removal from declarative XML source state.

This is a deliberately bounded experimental IFC4X3 native writer, NOT a
general IfcSpace/room mutation API. It is reachable only from the trusted
declarative compiler after all authored <Building> XML source has been
parsed, provenance-bound and semantically diffed. The authoring agent cannot
call IFC APIs directly and never submits imperative <Delete> instructions.

No original IFC is mutated; all writes use an exclusive staged transaction.
"""
from __future__ import annotations

from pathlib import Path

import ifcopenshell
import ifcopenshell.api.root

from src.runtime.ifc_mutations import Mutation, UnsupportedIFCMutation, by_guid_or_none
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.semantic_graph import graph_diff
from src.runtime.transaction import stage_and_commit


def _guard_original_space(f: ifcopenshell.file, guid: str) -> tuple:
    room = by_guid_or_none(f, guid)
    if room is None or not room.is_a("IfcSpace"):
        raise UnsupportedIFCMutation("Source Space is absent or has a different class")
    if room.ObjectPlacement is not None:
        # A child placement could otherwise silently move another object when
        # the room's placement is removed by IfcOpenShell.
        children = [x for x in f.get_inverse(room.ObjectPlacement)
                    if x.is_a("IfcObjectPlacement")]
        if children:
            raise UnsupportedIFCMutation("Space placement has externally dependent placements")
    allowed_deletions = {guid}
    allowed_aggregate_updates = set()
    inverse = list(f.get_inverse(room))
    if not inverse:
        raise UnsupportedIFCMutation("Space has no verified native spatial structure")
    found_aggregate = False
    for rel in inverse:
        if rel.is_a("IfcRelAggregates"):
            if (room not in rel.RelatedObjects
                or not rel.RelatingObject.is_a("IfcSpatialStructureElement")
                or not rel.RelatingObject.is_a("IfcBuildingStorey")
                or len(rel.RelatedObjects) < 2):
                raise UnsupportedIFCMutation("Space aggregation is not safely bounded")
            found_aggregate = True
            allowed_aggregate_updates.add(rel.GlobalId)
        elif rel.is_a("IfcRelDefinesByType"):
            if len(rel.RelatedObjects) != 1 or rel.RelatedObjects[0] != room:
                raise UnsupportedIFCMutation("Space has shared type-definition relationship")
            allowed_deletions.add(rel.GlobalId)
        elif rel.is_a("IfcRelDefinesByProperties"):
            if len(rel.RelatedObjects) != 1 or rel.RelatedObjects[0] != room:
                raise UnsupportedIFCMutation("Space has shared property-set relationship")
            definition = rel.RelatingPropertyDefinition
            if (not definition.is_a("IfcPropertySet")
                    and not definition.is_a("IfcElementQuantity")):
                raise UnsupportedIFCMutation("Space property definition is unsupported")
            refs = f.get_inverse(definition)
            if len(refs) != 1 or rel not in refs:
                raise UnsupportedIFCMutation("Space property definition is shared")
            allowed_deletions.add(rel.GlobalId)
            allowed_deletions.add(definition.GlobalId)
        else:
            # Especially reject IfcRelSpaceBoundary, associations,
            # constraints, assignments, containment, and custom links.
            raise UnsupportedIFCMutation(
                "Space has unsupported native dependencies: " + rel.is_a()
            )
    if not found_aggregate:
        raise UnsupportedIFCMutation("Space is missing a safe storey aggregation")
    if len(allowed_aggregate_updates) != 1:
        raise UnsupportedIFCMutation("Space belongs to multiple native aggregations")
    return (room, frozenset(allowed_deletions),
            frozenset(allowed_aggregate_updates))


def verify_bounded_space_deletion(
    before: ifcopenshell.file, after: ifcopenshell.file,
    target_guid: str, allowed_deleted: frozenset[str],
    allowed_modified: frozenset[str],
) -> int:
    """Independent original native identity and full surviving STEP oracle."""
    original_roots = {x.GlobalId: x for x in before.by_type("IfcRoot")}
    output_roots = {x.GlobalId: x for x in after.by_type("IfcRoot")}
    old_guids = set(original_roots)
    new_guids = set(output_roots)
    removed = old_guids - new_guids
    added = new_guids - old_guids
    if (removed != set(allowed_deleted) or added
            or any(k not in original_roots for k in allowed_modified)):
        raise UnsupportedIFCMutation("Space deletion changed unauthorized IFC Root identities")
    if by_guid_or_none(after, target_guid) is not None:
        raise UnsupportedIFCMutation("Deleted Space remains in native IFC")
    old_products = {x.GlobalId: x for x in before.by_type("IfcProduct")}
    new_products = {x.GlobalId: x for x in after.by_type("IfcProduct")}
    if (set(old_products) - set(new_products) != {target_guid}
            or set(new_products) - set(old_products)):
        raise UnsupportedIFCMutation("Space deletion modified unrelated native products")
    for guid, old in original_roots.items():
        if guid not in output_roots:
            continue
        new = output_roots[guid]
        if old.is_a() != new.is_a():
            raise UnsupportedIFCMutation("Space deletion reclassified existing IFC Root")
        if guid in allowed_modified:
            if (not old.is_a("IfcRelAggregates")
                    or not new.is_a("IfcRelAggregates")
                    or old.RelatingObject.GlobalId != new.RelatingObject.GlobalId
                    or {x.GlobalId for x in old.RelatedObjects}
                       - {x.GlobalId for x in new.RelatedObjects} != {target_guid}
                    or len(old.RelatedObjects) - len(new.RelatedObjects) != 1):
                raise UnsupportedIFCMutation("Space aggregation changed beyond one room")
            continue
        if str(old) != str(new):
            raise UnsupportedIFCMutation(
                "Space removal mutated an unrelated IFC Root: " + old.is_a()
            )
    # Independent *complete* STEP entity check: no original surviving entity
    # may change except the one Aggregates relationship and the owned
    # target/metadata entity subgraph which is deleted.
    old_step = {x.id(): str(x) for x in before}
    new_step = {x.id(): str(x) for x in after}
    if set(new_step) - set(old_step):
        raise UnsupportedIFCMutation("Space deletion unexpectedly creates IFC STEP entities")
    modified_step = {eid for eid in old_step.keys() & new_step.keys()
                     if old_step[eid] != new_step[eid]}
    permitted_step = {original_roots[g].id() for g in allowed_modified}
    # A presentation layer can list multiple shape representations. Deleting
    # this room removes ONLY its own shape from that layer; the same layer
    # and all unrelated room/wall representations MUST survive unchanged.
    original_space = before.by_guid(target_guid)
    owned_representations = {
        shape.id() for shape in
        (original_space.Representation.Representations
         if original_space.Representation else ())
    }
    for old_layer in before.by_type("IfcPresentationLayerAssignment"):
        if not any(item.id() in owned_representations
                   for item in old_layer.AssignedItems):
            continue
        try:
            new_layer = after.by_id(old_layer.id())
        except RuntimeError as exc:
            raise UnsupportedIFCMutation(
                "Space deletion removed a shared presentation layer"
            ) from exc
        if (not new_layer.is_a("IfcPresentationLayerAssignment")
                or old_layer.Name != new_layer.Name
                or old_layer.Description != new_layer.Description
                or old_layer.Identifier != new_layer.Identifier):
            raise UnsupportedIFCMutation(
                "Space deletion modified presentation layer metadata"
            )
        was = {x.id() for x in old_layer.AssignedItems}
        now = {x.id() for x in new_layer.AssignedItems}
        if (not now or now - was or not was - now
                or not (was - now) <= owned_representations):
            raise UnsupportedIFCMutation(
                "Space deletion modified unrelated presentation layer members"
            )
        permitted_step.add(old_layer.id())
    if modified_step != permitted_step:
        raise UnsupportedIFCMutation("Space deletion modified non-target IFC STEP entities")
    if before.schema != after.schema or before.schema != "IFC4X3":
        raise UnsupportedIFCMutation("Original IFC schema changed during Space removal")
    return len(old_guids & new_guids) - len(allowed_modified)


def compile_existing_space_deletion(source: Path, destination: Path,
                                    before_doc, after_doc, before, after):
    """Execute only one legal declarative Space node removal, fail closed."""
    from src.runtime.compiler import CompileReport, CompilerError

    delta = graph_diff(before.graph, after.graph)
    if (len(delta.removed_nodes) != 1 or delta.added_nodes
            or delta.changed_nodes or delta.added_edges):
        raise UnsupportedIFCMutation("Only one existing declarative Space removal is supported")
    node_id = delta.removed_nodes[0]
    old = before.graph.by_id()
    node = old[node_id]
    if node.kind != "Space" or node.provenance != "existing_source":
        raise UnsupportedIFCMutation("Removal is not an existing native IfcSpace")
    expected_edges = {
        edge for edge in before.graph.edges
        if edge.source == node_id or edge.target == node_id
    }
    if (set(delta.removed_edges) != expected_edges
            or any(edge.relation != "aggregated_in_storey"
                   or edge.target != node_id for edge in delta.removed_edges)
            or len(delta.removed_edges) != 1):
        raise UnsupportedIFCMutation("Space removal changes unsupported declarative relations")
    original = ifcopenshell.open(str(source))
    if original.schema != "IFC4X3":
        raise UnsupportedIFCMutation("Only IFC4X3 direct XML source admitted")
    orig_sha = snapshot_source(source).source_sha256
    if orig_sha != before_doc.source_model_sha256:
        raise UnsupportedIFCMutation("Original source SHA does not match declarative XML")
    _, allow_deleted, allow_modified = _guard_original_space(original, node.ifc_guid)
    op = Mutation("DELETE_SPACE", node_id, node.ifc_guid,
                  before_doc.managed_by_id()[node_id].span.line,
                  ("entity", "level"), "bounded existing native Space and individually owned metadata")

    def writer(stage: Path) -> None:
        current = ifcopenshell.open(str(source))
        room, expected_deleted, expected_modified = _guard_original_space(
            current, node.ifc_guid
        )
        if expected_deleted != allow_deleted or expected_modified != allow_modified:
            raise UnsupportedIFCMutation("Space native dependencies drifted before writing")
        ifcopenshell.api.root.remove_product(current, product=room)
        current.write(str(stage))

    def validator(stage: Path) -> None:
        if snapshot_source(source).source_sha256 != orig_sha:
            raise UnsupportedIFCMutation("Original source IFC modified before commit")
        now = ifcopenshell.open(str(stage))
        verify_bounded_space_deletion(
            ifcopenshell.open(str(source)), now,
            node.ifc_guid, allow_deleted, allow_modified,
        )
        # Reprojection is a separate check that requires the entire *typed*
        # native result to match the edited XML intent; opaque source
        # products remain present and cannot be silently dropped.
        from src.runtime.ifc_projection import project_ifc
        from src.runtime.xml_parser import parse_xml
        from src.runtime.binder import bind_document
        from src.runtime.space_partition_compiler import _canonical_native_graph
        projected = project_ifc(stage)
        result_doc = parse_xml(
            projected.xml, expected_source_sha256=projected.source.source_sha256
        )
        result_bound = bind_document(result_doc, projection=projected)
        if (_canonical_native_graph(result_bound.graph) !=
                _canonical_native_graph(after.graph)):
            raise UnsupportedIFCMutation("Native output graph disagrees with full edited XML")

    stage_and_commit(destination, writer, validator)
    if snapshot_source(source).source_sha256 != orig_sha:
        raise UnsupportedIFCMutation("Original source IFC modified during commit")
    result = snapshot_source(destination)
    unchanged = verify_bounded_space_deletion(
        ifcopenshell.open(str(source)), ifcopenshell.open(str(destination)),
        node.ifc_guid, allow_deleted, allow_modified,
    )
    return CompileReport(orig_sha, result.source_sha256,
                         delta.before_fingerprint, delta.after_fingerprint,
                         (op,), unchanged, (), destination, True)
