"""G1 #16: independent IFC-only, GT-free frozen spatial-Wall postconditions.

This is a developer-authored *source-only* witness, not the BIM-Edit official
evaluator or an assertion that Space creation is required by the public text.
It consumes only published instruction, immutable source IFC and candidate IFC.
It does not import either authoring arm, their geometry helper or scorer.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import re

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.shape
import ifcopenshell.util.unit
import numpy as np

INPUT_SHA = "e90e635629a85cf1942163db0f647a49edc6d24631ba72ec79a0381c9145a0de"
PROMPT_SHA = "31a00588498f68ef6791a133b033cc3da442749d5a237e76f0f5817cf095d14d"
IFC_MESH_TOL = 1e-6
TASK_PATTERN = re.compile(
    r"create a wall that spans orthogonally between the wall with the ID "
    r"(?P<first>[A-Za-z0-9_$]{22}) and (?P<second>[A-Za-z0-9_$]{22}) "
    r"and begins at (?P<offset>[0-9]+(?:\.[0-9]+)?)m in \+y direction "
    r"from the right side of the door looking from inside of the room "
    r"with the ID (?P<room>[A-Za-z0-9_$]{22})\. "
    r"It must have a thickness of (?P<thickness>[0-9]+(?:\.[0-9]+)?)m "
    r"and a height of (?P<height>[0-9]+(?:\.[0-9]+)?)m\.",
    re.ASCII,
)


class PublicWallSpaceBlocked(ValueError):
    """Invalid native source/physical edit/claimed IFC semantic evidence."""


def _sha(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise PublicWallSpaceBlocked("Missing or linked real IFC evidence")
    return sha256(path.read_bytes()).hexdigest()


def _parse_instruction(instruction: str) -> dict:
    if not isinstance(instruction, str) or len(instruction) > 640:
        raise PublicWallSpaceBlocked("Absent or oversized public Wall instruction")
    if sha256(instruction.encode("utf8")).hexdigest() != PROMPT_SHA:
        raise PublicWallSpaceBlocked("Public frozen instruction digest changed")
    match = TASK_PATTERN.fullmatch(instruction)
    if not match:
        raise PublicWallSpaceBlocked("Unrecognized or extended published Wall task")
    first, second, room = (match[x] for x in ("first", "second", "room"))
    if len({first, second, room}) != 3:
        raise PublicWallSpaceBlocked("Public source identifiers ambiguous")
    offset, thickness, height = map(
        float, (match["offset"], match["thickness"], match["height"]))
    if (offset, thickness, height) != (1.3025, 0.175, 2.8):
        raise PublicWallSpaceBlocked("Public frozen Wall dimensions changed")
    return {
        "first": first, "second": second, "room": room,
        "offset": offset, "thickness": thickness, "height": height,
    }


def _by_guid(model, guid: str, expected_class: str):
    try:
        entity = model.by_guid(guid)
    except RuntimeError as exc:
        raise PublicWallSpaceBlocked("Unresolvable public IFC object") from exc
    if entity is None or not entity.is_a(expected_class):
        raise PublicWallSpaceBlocked("Missing or wrong native public object class")
    return entity


def _mesh(entity):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    try:
        shape = ifcopenshell.geom.create_shape(settings, entity)
        coords = np.asarray(shape.geometry.verts, dtype=np.float64).reshape(-1, 3)
        triangles = len(shape.geometry.faces) // 3
        volume = float(ifcopenshell.util.shape.get_volume(shape.geometry))
    except Exception as exc:
        raise PublicWallSpaceBlocked("Unsupported native IFC product geometry") from exc
    if (len(coords) < 4 or triangles < 4 or not np.isfinite(coords).all()
            or not np.isfinite(volume) or volume <= 0):
        raise PublicWallSpaceBlocked("Invalid IFC mesh or physical measure")
    return coords, triangles, volume


def _vertices(points) -> Counter:
    return Counter(map(tuple, np.rint(points / IFC_MESH_TOL).astype(np.int64)))


def _native_products(model):
    by_guid = {}
    for item in model.by_type("IfcProduct"):
        if item.Representation is not None:
            if item.GlobalId in by_guid:
                raise PublicWallSpaceBlocked("Duplicate represented product identity")
            by_guid[item.GlobalId] = _mesh(item)
    return by_guid


def _same_geometry(before, after) -> bool:
    return (
        before[1] == after[1]
        and abs(before[2] - after[2]) <= IFC_MESH_TOL
        and _vertices(before[0]) == _vertices(after[0])
    )


def _bbox(physical):
    return physical[0].min(axis=0), physical[0].max(axis=0)


def _relation_index(model):
    relations = {}
    for relation in model.by_type("IfcRelationship"):
        if relation.GlobalId in relations:
            raise PublicWallSpaceBlocked("Duplicate native relation identity")
        relations[relation.GlobalId] = relation
    return relations


def _compare_relationships(before, after, new_wall_guid, storey_guid) -> tuple[int, int]:
    old, new = _relation_index(before), _relation_index(after)
    if not set(old).issubset(new):
        raise PublicWallSpaceBlocked("Original native IFC relation deleted")
    original_containment_edits = 0
    for guid, source_rel in old.items():
        output_rel = new[guid]
        if source_rel.is_a() != output_rel.is_a():
            raise PublicWallSpaceBlocked("Existing native relationship class changed")
        if str(source_rel) == str(output_rel):
            continue
        if not source_rel.is_a("IfcRelContainedInSpatialStructure"):
            raise PublicWallSpaceBlocked("Unrelated original native relation changed")
        old_members = {x.GlobalId for x in source_rel.RelatedElements}
        new_members = {x.GlobalId for x in output_rel.RelatedElements}
        if (source_rel.RelatingStructure.GlobalId != storey_guid
                or output_rel.RelatingStructure.GlobalId != storey_guid
                or new_members != old_members | {new_wall_guid}
                or any(getattr(source_rel, x, None) != getattr(output_rel, x, None)
                       for x in ("Name", "Description"))):
            raise PublicWallSpaceBlocked("Unexpected source containment mutation")
        original_containment_edits += 1
    if original_containment_edits > 1:
        raise PublicWallSpaceBlocked("New Wall attached to multiple source containers")

    paths, new_containment = [], []
    for guid in set(new) - set(old):
        rel = new[guid]
        if rel.is_a("IfcRelConnectsPathElements"):
            paths.append(rel)
        elif rel.is_a("IfcRelContainedInSpatialStructure"):
            new_containment.append(rel)
        else:
            raise PublicWallSpaceBlocked("Unexpected new native IFC relationship")
    if len(paths) != 2 or original_containment_edits + len(new_containment) != 1:
        raise PublicWallSpaceBlocked("Missing/extra physical joins or storey containment")
    for relation in new_containment:
        if (relation.RelatingStructure.GlobalId != storey_guid
                or [obj.GlobalId for obj in relation.RelatedElements] != [new_wall_guid]):
            raise PublicWallSpaceBlocked("Incorrect new storey containment")
    return len(paths), len(new_containment)


def audit_public_wall_space_semantics(source_ifc: Path,
                                      candidate_ifc: Path,
                                      public_instruction: str) -> dict:
    """Inspect native IFC and explicitly *not* certify any unknown Space split."""
    spec = _parse_instruction(public_instruction)
    if _sha(source_ifc) != INPUT_SHA:
        raise PublicWallSpaceBlocked("Frozen public source IFC hash changed")
    candidate_sha = _sha(candidate_ifc)
    for path in (source_ifc, candidate_ifc):
        with path.open("rb") as stream:
            if not stream.read(96).lstrip(b" \r\n\t").startswith(b"ISO-10303-21;"):
                raise PublicWallSpaceBlocked("Not a valid STEP IFC source")
    try:
        before = ifcopenshell.open(str(source_ifc))
        after = ifcopenshell.open(str(candidate_ifc))
    except Exception as exc:
        raise PublicWallSpaceBlocked("Cannot parse original/candidate IFC") from exc
    if before.schema != "IFC4X3" or after.schema != before.schema:
        raise PublicWallSpaceBlocked("Unexpected source/output IFC schema")
    if (not np.isclose(ifcopenshell.util.unit.calculate_unit_scale(before), 1.0)
            or not np.isclose(ifcopenshell.util.unit.calculate_unit_scale(after), 1.0)):
        raise PublicWallSpaceBlocked("Native IFC world length unit is not metres")

    first = _by_guid(before, spec["first"], "IfcWall")
    second = _by_guid(before, spec["second"], "IfcWall")
    room = _by_guid(before, spec["room"], "IfcSpace")
    doors = before.by_type("IfcDoor")
    if len(doors) != 1 or len(room.Decomposes) != 1:
        raise PublicWallSpaceBlocked("Public source room/storey/door ambiguous")
    storey = room.Decomposes[0].RelatingObject
    if not storey.is_a("IfcBuildingStorey"):
        raise PublicWallSpaceBlocked("Source room storey parent is invalid")
    if (len(first.ContainedInStructure) != 1
            or len(second.ContainedInStructure) != 1
            or first.ContainedInStructure[0].RelatingStructure != storey
            or second.ContainedInStructure[0].RelatingStructure != storey):
        raise PublicWallSpaceBlocked("Public bounding Wall storeys differ")

    old_roots = {r.GlobalId: r for r in before.by_type("IfcRoot")}
    new_roots = {r.GlobalId: r for r in after.by_type("IfcRoot")}
    if not set(old_roots).issubset(new_roots):
        raise PublicWallSpaceBlocked("Existing source root removed")
    for guid, source_root in old_roots.items():
        output_root = new_roots[guid]
        if source_root.is_a() != output_root.is_a():
            raise PublicWallSpaceBlocked("Existing root changed IFC class")
        for field in ("Name", "Description", "ObjectType", "Tag"):
            if (hasattr(source_root, field)
                    and getattr(source_root, field, None)
                    != getattr(output_root, field, None)):
                raise PublicWallSpaceBlocked("Original IFC root metadata changed")

    new_roots_delta = [item for guid, item in new_roots.items()
                       if guid not in old_roots]
    created_walls = [r for r in new_roots_delta if r.is_a("IfcWall")]
    if len(created_walls) != 1:
        raise PublicWallSpaceBlocked("Expected exactly one new native IfcWall")
    created = created_walls[0]
    added_paths, added_containers = _compare_relationships(
        before, after, created.GlobalId, storey.GlobalId)
    if len(new_roots_delta) != 1 + added_paths + added_containers:
        raise PublicWallSpaceBlocked("Unexpected extra IFC roots or relationships")
    if (len(created.ContainedInStructure) != 1
            or created.ContainedInStructure[0].RelatingStructure.GlobalId != storey.GlobalId):
        raise PublicWallSpaceBlocked("New physical Wall not contained by source storey")

    newly_joined = [
        rel for rel in after.by_type("IfcRelConnectsPathElements")
        if rel.GlobalId not in _relation_index(before)
    ]
    expected_relations = {
        (spec["first"], "ATPATH", "ATSTART"),
        (spec["second"], "ATPATH", "ATEND"),
    }
    observed_relations = {
        (rel.RelatingElement.GlobalId, str(rel.RelatingConnectionType),
         str(rel.RelatedConnectionType))
        for rel in newly_joined
        if rel.RelatedElement.GlobalId == created.GlobalId
    }
    if len(newly_joined) != 2 or observed_relations != expected_relations:
        raise PublicWallSpaceBlocked("Unexpected physical native Wall join endpoints")
    if any(rel.ConnectionGeometry is not None for rel in newly_joined):
        raise PublicWallSpaceBlocked("Unverified extra junction geometry in native edit")

    source_products = _native_products(before)
    output_products = _native_products(after)
    if (set(output_products) - set(source_products) != {created.GlobalId}
            or not set(source_products).issubset(output_products)):
        raise PublicWallSpaceBlocked("Existing represented product lost/added")
    for guid, physical in source_products.items():
        if not _same_geometry(physical, output_products[guid]):
            raise PublicWallSpaceBlocked("Original IFC physical product mesh changed")

    room_box = _bbox(source_products[room.GlobalId])
    first_box = _bbox(source_products[first.GlobalId])
    second_box = _bbox(source_products[second.GlobalId])
    door_box = _bbox(source_products[doors[0].GlobalId])
    wall_box = _bbox(output_products[created.GlobalId])
    room_min, room_max = room_box
    new_min, new_max = wall_box
    expected_y = door_box[0][1] + spec["offset"]
    expected_min = np.array((room_min[0], expected_y, room_min[2]))
    expected_max = np.array((room_max[0], expected_y + spec["thickness"],
                             room_min[2] + spec["height"]))
    if (not np.allclose(new_min, expected_min, rtol=0, atol=IFC_MESH_TOL)
            or not np.allclose(new_max, expected_max,
                               rtol=0, atol=IFC_MESH_TOL)
            or not np.isclose(first_box[1][0], new_min[0], atol=IFC_MESH_TOL)
            or not np.isclose(second_box[0][0], new_max[0], atol=IFC_MESH_TOL)
            or not np.isclose(room_max[2] - room_min[2],
                              spec["height"], atol=IFC_MESH_TOL)
            or not room_min[1] < new_min[1] < new_max[1] < room_max[1]):
        raise PublicWallSpaceBlocked("Source-only native Wall geometry violates published constraint")

    expected_wall_volume = (
        (room_max[0] - room_min[0]) * spec["thickness"] * spec["height"]
    )
    if abs(output_products[created.GlobalId][2] - expected_wall_volume) > IFC_MESH_TOL:
        raise PublicWallSpaceBlocked("Native Wall solid physical volume incorrect")

    source_spaces = {s.GlobalId for s in before.by_type("IfcSpace")}
    out_spaces = {s.GlobalId for s in after.by_type("IfcSpace")}
    source_boundaries = {
        rel.GlobalId: str(rel) for rel in before.by_type("IfcRelSpaceBoundary")
    }
    new_boundaries = {
        rel.GlobalId: str(rel) for rel in after.by_type("IfcRelSpaceBoundary")
    }
    if source_spaces != out_spaces or source_boundaries != new_boundaries:
        raise PublicWallSpaceBlocked("Unexpected new Space or altered native Space boundary")

    intersection = np.maximum(
        0.0, np.minimum(room_max, new_max) - np.maximum(room_min, new_min))
    overlap = float(np.prod(intersection))
    if abs(overlap - expected_wall_volume) > IFC_MESH_TOL:
        raise PublicWallSpaceBlocked("New Wall not crossing entire source room")
    if _sha(source_ifc) != INPUT_SHA or _sha(candidate_ifc) != candidate_sha:
        raise PublicWallSpaceBlocked("Source/result IFC changed during read-only audit")
    return {
        "status": "PASS_SOURCE_ONLY_PHYSICAL_WALL_JOINS_ROOM_SEMANTIC_SPLIT_UNPROVEN",
        "frozen_source_sha256": INPUT_SHA,
        "produced_ifc_sha256": candidate_sha,
        "public_instruction_sha256": PROMPT_SHA,
        "native_source_products_preserved": len(source_products),
        "new_native_wall_count": 1,
        "new_native_path_joins": 2,
        "new_wall_storey_containment_correct": True,
        "source_room_and_wall_full_cross_section": True,
        "source_room_wall_overlap_volume_m3": round(overlap, 6),
        "source_room_ifc_space_geometry_unchanged": True,
        "source_ifc_space_count_before_and_after": [
            len(source_spaces), len(out_spaces)],
        "source_ifc_space_boundary_count_before_and_after": [
            len(source_boundaries), len(new_boundaries)],
        "new_ifc_space_created": False,
        "new_room_identity_type_name_or_pset_entailed_by_public_instruction": False,
        "geometry_implies_new_ifc_space_semantics": False,
        "complete_official_task_oracle_proven": False,
        "official_bim_edit_evaluator_executed": False,
        "official_tasks_scored": 0,
        "llm_calls": 0,
        "G1_G2_G3_unblocked": False,
    }
