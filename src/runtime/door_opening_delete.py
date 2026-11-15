"""Strict source-state-native deletion of one existing IFC4X3 Door + Opening pair.

The model submits a complete declarative XML document with existing <Opening>
and <Door> nodes removed. No direct IFC APIs/commands are exposed to the
model. This trusted compiler backend only accepts a uniquely hosted, filled,
conservatively classified original IFC pair. It preserves the original file,
all other native products and unrelated STEP records, and fails closed on
unrecognized dependencies and non-target XML changes.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import ifcopenshell
import ifcopenshell.api.root

from src.runtime.ifc_mutations import Mutation, UnsupportedIFCMutation, by_guid_or_none
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.semantic_graph import graph_diff
from src.runtime.transaction import stage_and_commit


@dataclass(frozen=True)
class BoundedOpeningDoor:
    opening_guid: str
    door_guid: str
    host_guid: str
    deleted_root_guids: frozenset[str]
    modified_root_guids: frozenset[str]
    modified_layer_step_ids: frozenset[int]
    door_shape_step_ids: frozenset[int]


def preflight_bounded_door_opening(
    model: ifcopenshell.file, opening_guid: str, door_guid: str,
) -> BoundedOpeningDoor:
    if model.schema != "IFC4X3":
        raise UnsupportedIFCMutation("Bounded Opening/Door delete is IFC4X3-only")
    opening = by_guid_or_none(model, opening_guid)
    door = by_guid_or_none(model, door_guid)
    if (opening is None or door is None
            or not opening.is_a("IfcOpeningElement")
            or not door.is_a("IfcDoor")):
        raise UnsupportedIFCMutation("Original Opening and Door GUID/class mismatch")
    if (len(opening.HasFillings) != 1
            or opening.HasFillings[0].RelatedBuildingElement != door
            or len(door.FillsVoids) != 1
            or door.FillsVoids[0].RelatingOpeningElement != opening
            or len(opening.VoidsElements) != 1
            or not opening.VoidsElements[0].RelatingBuildingElement.is_a("IfcWall")
            or opening.ContainedInStructure):
        raise UnsupportedIFCMutation("Opening/Door/host native topology is ambiguous")
    fill = opening.HasFillings[0]
    void = opening.VoidsElements[0]
    host = void.RelatingBuildingElement
    if Counter(x.is_a() for x in model.get_inverse(opening)) != Counter({
        "IfcRelVoidsElement": 1, "IfcRelFillsElement": 1
    }):
        raise UnsupportedIFCMutation("Opening has unknown native inverse dependencies")
    expected = Counter({
        "IfcRelFillsElement": 1,
        "IfcRelDefinesByProperties": 2,
        "IfcRelDefinesByType": 1,
        "IfcRelAssociatesMaterial": 1,
        "IfcRelAssociatesClassification": 1,
        "IfcRelContainedInSpatialStructure": 1,
    })
    inverse = list(model.get_inverse(door))
    if Counter(x.is_a() for x in inverse) != expected:
        raise UnsupportedIFCMutation("Door has unrecognized native dependencies")
    owned = {opening_guid, door_guid, fill.GlobalId, void.GlobalId}
    edited = set()
    for rel in inverse:
        cls = rel.is_a()
        if cls in ("IfcRelDefinesByProperties", "IfcRelDefinesByType",
                   "IfcRelAssociatesMaterial"):
            if (not hasattr(rel, "RelatedObjects")
                    or tuple(rel.RelatedObjects) != (door,)):
                raise UnsupportedIFCMutation("Door property/type/material relation is shared")
            owned.add(rel.GlobalId)
            if cls == "IfcRelDefinesByProperties":
                definition = rel.RelatingPropertyDefinition
                if (definition is None or
                        not definition.is_a("IfcPropertySet") or
                        set(model.get_inverse(definition)) != {rel}):
                    raise UnsupportedIFCMutation("Door propertyset is not solely owned")
                owned.add(definition.GlobalId)
        elif cls == "IfcRelAssociatesClassification":
            if tuple(rel.RelatedObjects) != (door,):
                raise UnsupportedIFCMutation("Door classification membership is not unique")
            # The frozen native IfcOpenShell removal leaves the classifier
            # with an empty RelatedObjects tuple. Preserve exact I0 outcome.
            edited.add(rel.GlobalId)
        elif cls == "IfcRelContainedInSpatialStructure":
            if (door not in rel.RelatedElements
                    or len(rel.RelatedElements) <= 1
                    or not rel.RelatingStructure.is_a("IfcBuildingStorey")):
                raise UnsupportedIFCMutation("Door has unsafe storey membership")
            edited.add(rel.GlobalId)
        elif cls != "IfcRelFillsElement" or rel != fill:
            raise UnsupportedIFCMutation("Unexpected original Door inverse")
    if len(owned) != 10 or len(edited) != 2:
        raise UnsupportedIFCMutation("Native deleted/modified Root inventory incomplete")
    if door.Representation is None:
        raise UnsupportedIFCMutation("Door has no original physical representation")
    representations = {r.id() for r in door.Representation.Representations}
    if not representations:
        raise UnsupportedIFCMutation("Original Door has no shape representations")
    layers = set()
    for layer in model.by_type("IfcPresentationLayerAssignment"):
        assigned = {e.id() for e in layer.AssignedItems}
        if assigned & representations:
            if (not assigned - representations
                    or assigned & representations != representations):
                raise UnsupportedIFCMutation("Door's shared representation layer ambiguous")
            layers.add(layer.id())
    if len(layers) != 1:
        raise UnsupportedIFCMutation("Door must be on one source-proven shared layer")
    for product in model.by_type("IfcProduct"):
        if product.GlobalId in (opening_guid,door_guid):
            continue
        if (product.Representation is not None
                and any(rep.id() in representations for rep in
                        product.Representation.Representations)):
            raise UnsupportedIFCMutation("Door shape is shared with another IFC Product")
    if door.ObjectPlacement is not None:
        if any(e.is_a("IfcObjectPlacement")
               for e in model.get_inverse(door.ObjectPlacement)):
            raise UnsupportedIFCMutation("Door placement has dependent native placements")
    return BoundedOpeningDoor(
        opening_guid, door_guid, host.GlobalId,
        frozenset(owned), frozenset(edited),
        frozenset(layers), frozenset(representations),
    )


def verify_bounded_door_opening(
    source: ifcopenshell.file, result: ifcopenshell.file, plan: BoundedOpeningDoor,
) -> int:
    """Strong independent full-root plus surviving STEP mutation barrier."""
    if source.schema != result.schema or source.schema != "IFC4X3":
        raise UnsupportedIFCMutation("Original IFC schema changed")
    if preflight_bounded_door_opening(
        source, plan.opening_guid,plan.door_guid) != plan:
        raise UnsupportedIFCMutation("Door/Opening native preflight drifted")
    old = {r.GlobalId:r for r in source.by_type("IfcRoot")}
    new = {r.GlobalId:r for r in result.by_type("IfcRoot")}
    if (set(old) - set(new) != set(plan.deleted_root_guids)
            or set(new) - set(old)):
        raise UnsupportedIFCMutation("Unapproved original IFC Root added/deleted")
    original_products = {p.GlobalId:p.is_a() for p in source.by_type("IfcProduct")}
    output_products = {p.GlobalId:p.is_a() for p in result.by_type("IfcProduct")}
    expected_products = {
        g:cls for g,cls in original_products.items()
        if g not in (plan.opening_guid,plan.door_guid)
    }
    if output_products != expected_products:
        raise UnsupportedIFCMutation("Unrelated original IfcProduct identities/classes changed")
    for guid in set(old)&set(new):
        lhs = old[guid]
        rhs = new[guid]
        if lhs.is_a() != rhs.is_a():
            raise UnsupportedIFCMutation("Original surviving native Root class changed")
        if guid in plan.modified_root_guids:
            if lhs.is_a() == "IfcRelContainedInSpatialStructure":
                field = "RelatedElements"
            elif lhs.is_a() == "IfcRelAssociatesClassification":
                field = "RelatedObjects"
            else:
                raise UnsupportedIFCMutation("Unexpected mutable native relation class")
            before = {e.GlobalId for e in getattr(lhs, field)}
            after = {e.GlobalId for e in getattr(rhs, field)}
            if (before - after != {plan.door_guid}
                    or after - before
                    or len(getattr(lhs,field))-len(getattr(rhs,field))!=1):
                raise UnsupportedIFCMutation("Shared native relation membership drifted")
            for idx in range(len(lhs)):
                if lhs.attribute_name(idx) != field and str(lhs[idx]) != str(rhs[idx]):
                    raise UnsupportedIFCMutation("Shared native relation metadata drifted")
        elif str(lhs) != str(rhs):
            raise UnsupportedIFCMutation("Unrelated original IFC Root modified")
    prior_step = {item.id():str(item) for item in source}
    after_step = {item.id():str(item) for item in result}
    if set(after_step) - set(prior_step):
        raise UnsupportedIFCMutation("Unexpected native STEP entity created")
    changed_step = {
        eid for eid in set(prior_step)&set(after_step)
        if prior_step[eid] != after_step[eid]
    }
    permitted_changed = {old[k].id() for k in plan.modified_root_guids}
    permitted_changed.update(plan.modified_layer_step_ids)
    if changed_step != permitted_changed:
        raise UnsupportedIFCMutation("Unrelated original STEP entity changed")
    for layer_id in plan.modified_layer_step_ids:
        prev = source.by_id(layer_id)
        post = result.by_id(layer_id)
        if (not prev.is_a("IfcPresentationLayerAssignment")
                or not post.is_a("IfcPresentationLayerAssignment")
                or prev.Name != post.Name
                or prev.Description != post.Description
                or prev.Identifier != post.Identifier):
            raise UnsupportedIFCMutation("Native shared presentation layer metadata changed")
        orig_items={x.id() for x in prev.AssignedItems}
        new_items={x.id() for x in post.AssignedItems}
        if (orig_items-new_items != set(plan.door_shape_step_ids)
                or new_items-orig_items or not new_items):
            raise UnsupportedIFCMutation("Deleted door changed unrelated layer members")
    # The SDK can delete native non-root geometry/property descendants of the
    # two source products. Every removed non-root entity must be reachable
    # through the *original* owned IFC Root subgraph and must not be
    # referenced by another surviving unapproved entity.
    removed_ids = set(prior_step)-set(after_step)
    deleted_root_ids={old[g].id() for g in plan.deleted_root_guids}
    if not deleted_root_ids <= removed_ids:
        raise UnsupportedIFCMutation("Expected deleted native Roots still exist")
    reachable=set(deleted_root_ids)
    stack=[source.by_id(eid) for eid in deleted_root_ids]
    while stack:
        item=stack.pop()
        for child in source.traverse(item)[1:]:
            if child.is_a("IfcRoot") and child.id() not in deleted_root_ids:
                continue
            if child.id() not in reachable:
                reachable.add(child.id())
                stack.append(child)
    if not removed_ids <= reachable:
        raise UnsupportedIFCMutation("Unrelated original native STEP entity deleted")
    for eid in removed_ids:
        entity = source.by_id(eid)
        if (eid not in deleted_root_ids
                and any(inv.id() not in removed_ids|set(plan.modified_layer_step_ids)
                        for inv in source.get_inverse(entity))):
            raise UnsupportedIFCMutation(
                "Deleted native nonroot STEP entity was shared externally")
    return len(set(old)&set(new))-len(plan.modified_root_guids)


def compile_existing_door_opening_delete(
    source: Path, destination: Path, before_doc,after_doc,before,after,
):
    """Exactly two deleted declarative nodes, one source Opening and its Door."""
    from src.runtime.compiler import CompileReport

    delta=graph_diff(before.graph,after.graph)
    if (len(delta.removed_nodes)!=2 or delta.added_nodes
            or delta.changed_nodes or delta.added_edges):
        raise UnsupportedIFCMutation("Door/Opening deletion requires isolated exact XML diff")
    prior=before.graph.by_id()
    removed={k:prior[k] for k in delta.removed_nodes}
    if {x.kind for x in removed.values()} != {"Opening","Door"}:
        raise UnsupportedIFCMutation("Only existing Opening plus own Door are allowed")
    opening_id=next(k for k,v in removed.items() if v.kind=="Opening")
    door_id=next(k for k,v in removed.items() if v.kind=="Door")
    if any(x.provenance!="existing_source" for x in removed.values()):
        raise UnsupportedIFCMutation("Door/Opening XML nodes must come from original native IFC")
    old_edges={
        x for x in before.graph.edges
        if x.source in removed or x.target in removed
    }
    if (set(delta.removed_edges)!=old_edges
            or {x.relation for x in old_edges}!={"host_void","opening_fill"}
            or len(old_edges)!=2
            or next(e for e in old_edges if e.relation=="opening_fill").source!=opening_id
            or next(e for e in old_edges if e.relation=="opening_fill").target!=door_id
            or next(e for e in old_edges if e.relation=="host_void").target!=opening_id):
        raise UnsupportedIFCMutation("Door/Opening deletion lost unrelated typed XML relations")
    before_sha=snapshot_source(source).source_sha256
    if before_sha != before_doc.source_model_sha256:
        raise UnsupportedIFCMutation("Original IFC source SHA mismatch")
    native_source=ifcopenshell.open(str(source))
    plan=preflight_bounded_door_opening(
        native_source, removed[opening_id].ifc_guid,removed[door_id].ifc_guid)
    mutation=Mutation(
        "DELETE_ORIGINAL_PUBLIC_DOOR_OPENING",opening_id+"|"+door_id,
        plan.opening_guid,before_doc.managed_by_id()[opening_id].span.line,
        ("Opening","Door","source_native_relations"),
        "bounded original hosted Door+Opening ordinary XML node deletion"
    )

    def writer(stage:Path)->None:
        native=ifcopenshell.open(str(source))
        fresh=preflight_bounded_door_opening(native,plan.opening_guid,plan.door_guid)
        if fresh!=plan or snapshot_source(source).source_sha256!=before_sha:
            raise UnsupportedIFCMutation("Native original IFC or dependents changed before staged write")
        door=by_guid_or_none(native,plan.door_guid)
        opening=by_guid_or_none(native,plan.opening_guid)
        ifcopenshell.api.root.remove_product(native,product=door)
        ifcopenshell.api.root.remove_product(native,product=opening)
        native.write(str(stage))

    def validator(stage:Path)->None:
        if snapshot_source(source).source_sha256!=before_sha:
            raise UnsupportedIFCMutation("Original source IFC changed during transaction")
        verify_bounded_door_opening(
            ifcopenshell.open(str(source)),ifcopenshell.open(str(stage)),plan)
        from src.runtime.ifc_projection import project_ifc
        from src.runtime.xml_parser import parse_xml
        from src.runtime.binder import bind_document
        from src.runtime.space_partition_compiler import _canonical_native_graph
        projected=project_ifc(stage)
        final_doc=parse_xml(projected.xml,expected_source_sha256=projected.source.source_sha256)
        final_bound=bind_document(final_doc,projection=projected)
        if _canonical_native_graph(final_bound.graph)!=_canonical_native_graph(after.graph):
            raise UnsupportedIFCMutation("Native output does not match entire edited XML state")

    stage_and_commit(destination,writer,validator)
    if snapshot_source(source).source_sha256!=before_sha:
        raise UnsupportedIFCMutation("Original IFC mutated during Door/Opening commit")
    result=snapshot_source(destination)
    unaffected=verify_bounded_door_opening(
        ifcopenshell.open(str(source)),ifcopenshell.open(str(destination)),plan)
    return CompileReport(
        before_sha,result.source_sha256,
        delta.before_fingerprint,delta.after_fingerprint,
        (mutation,),unaffected,(),destination,True,
    )
