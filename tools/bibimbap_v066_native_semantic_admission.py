"""v0.66 OFFLINE, source-neutral, bounded physical IFC preservation admission.

This checker is not the author task scorer and has no model-facing answers.
It does NOT require the original STEP numeric labels or exactly one native
representation strategy. It requires every original native IFC entity to
survive by a conservative, typed, multi-depth relational fingerprint (which
ignores STEP IDs), all original GUIDs/classes, existing non-host physical
shapes, a valid hosted Door+Opening wall CSG, no new schema findings and no
new root-unreachable anonymous objects.

Scope: bounded single Door+Opening on a straight represented axis-aligned
Wall in IFC2X3 / IFC4X3. Fingerprints are conservative equivalence evidence,
NOT a proof of all possible IFC semantics/graph isomorphisms.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
import math

import ifcopenshell
import ifcopenshell.entity_instance
import ifcopenshell.util.unit

from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v055_production_schema_gate import _schema_error_counter
from tools.bibimbap_v063_exterior_door_native import _mesh_bounds, _volume, _near_bbox
from tools.bibimbap_v065_source_neutral_door import horizontal_wall_axis_and_box

ROOT_CLASSES = sorted((
    "IfcDoor", "IfcOpeningElement", "IfcRelFillsElement",
    "IfcRelVoidsElement", "IfcRelContainedInSpatialStructure",
))
DEPTHS = (0, 1, 2, 4, 8, 16)
STATUS = "V066_IFC2X3_IFC4X3_BOUNDED_STEP_INDEPENDENT_NATIVE_ADMISSION_PASS"


class SemanticNative066Error(ValueError):
    pass


def need(condition, message: str):
    if not condition:
        raise SemanticNative066Error(message)


def _hash(data) -> str:
    return sha256(json.dumps(data, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf8")).hexdigest()


def _serial(value, previous):
    """Canonicalize native attribute values, never serializing STEP numbers."""
    if isinstance(value, ifcopenshell.entity_instance):
        if value.id() != 0:
            need(value.id() in previous, "dangling native IFC entity reference")
            return ["reference", previous[value.id()]]
        # Inline EXPRESS simple/defined-type entity with no STEP number.
        return ["express_inline", value.is_a(),
                [_serial(a, previous) for a in value]]
    if isinstance(value, (tuple, list)):
        return ["aggregate", [_serial(v, previous) for v in value]]
    if value is None:
        return ["missing"]
    if isinstance(value, bool):
        return ["boolean", value]
    if isinstance(value, int):
        return ["integer", value]
    if isinstance(value, float):
        need(math.isfinite(value), "non-finite IFC real attribute")
        return ["real", format(round(value, 10), ".10f")]
    if isinstance(value, str):
        return ["text_enum", value]
    raise SemanticNative066Error(
        f"Unrecognized IFC attribute primitive {type(value).__name__}"
    )


def _graph_hashes(model, rounds: int):
    """Weisfeiler-Lehman-like conservative forward-attribute refinements.

    No STEP ID, list indexes or entity creation order are in any digest.
    We validate the original's full multisets at multiple refinement depths.
    This rejects modifications to preserved property, material, geometry,
    relationship endpoints and anonymous entities in the supported cases.
    """
    instances = list(model)
    ids = [e.id() for e in instances]
    need(len(set(ids)) == len(ids) and all(i > 0 for i in ids),
         "Source IFC STEP entities must have unique positive parsing IDs")
    prev = {i: "__REFERENCE__" for i in ids}
    stages = {}
    for depth in range(rounds + 1):
        nxt = {}
        for e in instances:
            nxt[e.id()] = _hash([
                e.is_a(),
                [_serial(attribute, prev) for attribute in e],
            ])
        if depth in DEPTHS:
            stages[depth] = Counter(nxt.values())
        prev = nxt
    return stages


def _reference_entities(value):
    if isinstance(value, ifcopenshell.entity_instance):
        if value.id() != 0:
            yield value
        else:
            for v in value:
                yield from _reference_entities(v)
    elif isinstance(value, (tuple, list)):
        for v in value:
            yield from _reference_entities(v)


def _root_reachable(model):
    seen = set()
    todo = list(model.by_type("IfcRoot"))
    while todo:
        entity = todo.pop()
        if entity.id() in seen:
            continue
        seen.add(entity.id())
        for item in entity:
            todo.extend(e for e in _reference_entities(item)
                        if e.id() not in seen)
    return seen


def _roots_by_guid(model):
    roots = model.by_type("IfcRoot")
    guid = {}
    for entity in roots:
        need(entity.GlobalId not in guid, "Duplicate original/new IFC Root GUID")
        guid[entity.GlobalId] = entity
    return guid


def _same_box(a, b, epsilon=1e-5):
    return all(abs(float(a[axis][side]) - float(b[axis][side])) <= epsilon
               for axis in range(3) for side in range(2))


def post_native_semantic_gate(source: Path, source_sha: str, edited: Path) -> dict:
    source, edited = Path(source), Path(edited)
    need(source.is_file() and edited.is_file()
         and not source.is_symlink() and not edited.is_symlink()
         and source.resolve() != edited.resolve()
         and len(source_sha) == 64 and file_hash(source) == source_sha,
         "Source SHA/identity immutable; edited candidate must be separate")
    edited_sha = file_hash(edited)
    original = ifcopenshell.open(str(source))
    result = ifcopenshell.open(str(edited))
    need(original.schema in ("IFC2X3", "IFC4X3")
         and original.schema_identifier == result.schema_identifier,
         "Only matching supported IFC2X3/IFC4X3 schemas admitted")
    unit = ifcopenshell.util.unit.calculate_unit_scale(original)
    need(abs(unit - ifcopenshell.util.unit.calculate_unit_scale(result)) < 1e-12
         and unit in (1.0, 0.001),
         "Project length unit must be identical and supported")

    # Unlike v0.65, none of the source entity identities are compared by
    # arbitrary STEP number. Candidate must retain at least the original
    # MULTISET of full typed, rooted/anonymous, forward relationship subgraphs.
    original_hashes = _graph_hashes(original, max(DEPTHS))
    edited_hashes = _graph_hashes(result, max(DEPTHS))
    for depth in DEPTHS:
        missing = original_hashes[depth] - edited_hashes[depth]
        need(not missing,
             f"Existing native IFC entity/attribute/reference graph changed "
             f"(STEP-independent refinement depth {depth})")
    source_reachable = _root_reachable(original)
    result_reachable = _root_reachable(result)
    old_orphan = Counter(e.is_a() for e in original if e.id() not in source_reachable)
    new_orphan = Counter(e.is_a() for e in result if e.id() not in result_reachable)
    need(not (new_orphan - old_orphan),
         "New orphan / root-unreachable IFC native entities are forbidden")

    source_roots, candidate_roots = _roots_by_guid(original), _roots_by_guid(result)
    need(set(source_roots).issubset(candidate_roots)
         and all(candidate_roots[g].is_a() == e.is_a()
                 for g, e in source_roots.items()),
         "Original Root GUID/class identity changed")
    new_root_guids = set(candidate_roots) - set(source_roots)
    new_roots = [candidate_roots[g] for g in sorted(new_root_guids)]
    need(sorted(e.is_a() for e in new_roots) == ROOT_CLASSES,
         "Only one new Door, Opening, void, fill, and containment Roots admitted")
    for klass, new_count in [
        ("IfcWall", 0), ("IfcDoor", 1), ("IfcOpeningElement", 1),
        ("IfcRelVoidsElement", 1), ("IfcRelFillsElement", 1),
        ("IfcRelContainedInSpatialStructure", 1),
    ]:
        need(len(result.by_type(klass)) == len(original.by_type(klass)) + new_count,
             "Existing IFC class population altered or unauthorized product added")
    if original.schema == "IFC2X3":
        need(all(e.OwnerHistory is not None for e in new_roots),
             "IFC2X3 mandatory OwnerHistory missing on new IfcRoot")

    def unique(klass):
        matches = [e for e in new_roots if e.is_a(klass)]
        need(len(matches) == 1, "Missing native hosted Door/Opening chain member")
        return matches[0]
    door, opening = unique("IfcDoor"), unique("IfcOpeningElement")
    filling, void = unique("IfcRelFillsElement"), unique("IfcRelVoidsElement")
    contain = unique("IfcRelContainedInSpatialStructure")
    need(filling.RelatingOpeningElement == opening
         and filling.RelatedBuildingElement == door
         and void.RelatedOpeningElement == opening
         and void.RelatingBuildingElement.is_a("IfcWall")
         and void.RelatingBuildingElement.GlobalId in source_roots
         and contain.RelatingStructure.is_a("IfcBuildingStorey")
         and contain.RelatingStructure.GlobalId in source_roots
         and door in contain.RelatedElements,
         "Hosted native Door/Opening/void/fill/storey relations incorrect")
    host = void.RelatingBuildingElement
    source_host = original.by_guid(host.GlobalId)
    need(source_host is not None, "Wall host must be original source Wall")
    axis, wall_box = horizontal_wall_axis_and_box(source_host)
    need(door.Representation is not None and opening.Representation is not None,
         "Door and Opening must both have physical native representations")
    door_box, opening_box = _mesh_bounds(door), _mesh_bounds(opening)
    lon = 0 if axis == "X" else 1
    across = 1 - lon
    need(all(door_box[i][0] >= opening_box[i][0] - 1e-4 and
             door_box[i][1] <= opening_box[i][1] + 1e-4 for i in range(3))
         and opening_box[across][0] < wall_box[across][0] - .025
         and opening_box[across][1] > wall_box[across][1] + .025
         and opening_box[lon][0] > wall_box[lon][0] + .15
         and opening_box[lon][1] < wall_box[lon][1] - .15,
         "Native Door outside Aperture or Wall no longer fully cut")
    need(door.OverallWidth is not None and door.OverallHeight is not None
         and abs(door.OverallWidth * unit -
                 (door_box[lon][1] - door_box[lon][0])) < .001
         and abs(door.OverallHeight * unit -
                 (door_box[2][1] - door_box[2][0])) < .001,
         "Door physical dimensions disagree with source project units")
    actual_cut = _volume(source_host) - _volume(host)
    expected_cut = ((opening_box[lon][1] - opening_box[lon][0]) *
                    (wall_box[across][1] - wall_box[across][0]) *
                    (opening_box[2][1] - opening_box[2][0]))
    need(actual_cut > .05 and abs(actual_cut - expected_cut) < .003
         and _near_bbox(_mesh_bounds(source_host), _mesh_bounds(host)),
         "Native Wall CSG through aperture not physically realized")
    preserved_products = 0
    for product in original.by_type("IfcProduct"):
        candidate = result.by_guid(product.GlobalId)
        need(candidate is not None and candidate.is_a() == product.is_a(),
             "Original product GlobalId/type missing")
        if product.Representation is None:
            need(candidate.Representation is None,
                 "Original non-geometric product acquired geometry")
            continue
        if product.GlobalId == host.GlobalId:
            continue
        need(_same_box(_mesh_bounds(product), _mesh_bounds(candidate))
             and abs(_volume(product) - _volume(candidate)) < .001,
             "Untouched original product native mesh differs")
        preserved_products += 1
    original_errors = _schema_error_counter(source)
    candidate_errors = _schema_error_counter(edited)
    need(not (candidate_errors - original_errors),
         "New IfcOpenShell validator findings compared to source")
    need(file_hash(source) == source_sha and file_hash(edited) == edited_sha,
         "Source or output file changed during independent verification")
    return {
        "status": STATUS,
        "source_schema": original.schema_identifier,
        "source_SHA256": source_sha,
        "candidate_SHA256": edited_sha,
        "source_root_GUIDs_and_classes_preserved": len(source_roots),
        "source_IFC_anonymous_and_rooted_graph_counter_refinements": list(DEPTHS),
        "source_IFC_all_original_entity_graph_fingerprints_preserved": True,
        "original_STEP_numeric_ids_required": False,
        "source_unreachable_entity_type_count_not_increased": True,
        "new_Roots_exactly_allowed_five": True,
        "nonhost_native_product_geometry_preserved": preserved_products,
        "host_wall_opaque_IFC_source_global_id": host.GlobalId,
        "actual_wall_CSG_volume_removed_m3": round(actual_cut, 6),
        "expected_wall_CSG_volume_removed_m3": round(expected_cut, 6),
        "native_physical_edit_semantic_SHA256": _hash({
            "native_schema": original.schema_identifier,
            "source_SHA256": source_sha,
            "host_wall_GUID": host.GlobalId,
            "door_box_world_metres": [[round(float(a), 5), round(float(b), 5)]
                                       for a, b in door_box],
            "opening_box_world_metres": [[round(float(a), 5), round(float(b), 5)]
                                          for a, b in opening_box],
            "wall_CSG_m3": round(actual_cut, 5),
        }),
        "new_schema_findings": 0,
        "task_correctness_not_claimed": True,
        "general_edit_equivalence_not_claimed": True,
    }
