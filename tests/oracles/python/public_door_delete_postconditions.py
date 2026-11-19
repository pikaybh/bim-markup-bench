"""Source-only IFC deletion audit; independent of D0 and manual I0 authoring.

No GT, target record, official scorer or treatment compiler is loaded.
A native deletion with a modified space boundary cannot be promoted to
an official success on the basis of this limited independent witness.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import re

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.shape
import numpy as np


INPUT_SHA = "170d9ed9c10a31d86c3ff2207a450fd552166af21472486f11004f6e2b14defb"
PUBLIC_SHA = "8dc59cbf741dbbf626843eebd91972197fa9ff0b9cbea251d6b9a8d8cd0a752a"
# Literal public text from the pinned task record, never a private grader field.
PUBLIC_RE = re.compile(
    r"Delete the door with ID (?P<door>[A-Za-z0-9_$]{22})\. "
    r"Also delete the opening (?P<opening>[A-Za-z0-9_$]{22}), "
    r"the relationship between door and opening, the voids relationship "
    r"between the opening and the wall (?P<wall>[A-Za-z0-9_$]{22}), "
    r"and the assignment of door and opening to storey "
    r"(?P<storey>[A-Za-z0-9_$]{22})\.",
    re.ASCII,
)
MAX_PROMPT_LEN = 640
EXPECTED_REMOVED_CLASSES = {
    "IfcDoor": 1,
    "IfcOpeningElement": 1,
    "IfcRelFillsElement": 1,
    "IfcRelVoidsElement": 1,
    "IfcRelSpaceBoundary": 1,
    "IfcRelAssociatesMaterial": 1,
    "IfcRelDefinesByProperties": 2,
    "IfcPropertySet": 2,
}
EXPECTED_CHANGED_RELATIONS = {
    "IfcRelDefinesByType": "RelatedObjects",
    "IfcRelAssociatesClassification": "RelatedObjects",
    "IfcRelContainedInSpatialStructure": "RelatedElements",
}
TOLERANCE = 1e-6


class PublicDoorDeleteBlocked(ValueError):
    pass


def _sha(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise PublicDoorDeleteBlocked("Missing/linked native IFC")
    return sha256(path.read_bytes()).hexdigest()


def published_guids(prompt: str) -> dict:
    if not isinstance(prompt, str) or len(prompt) > MAX_PROMPT_LEN:
        raise PublicDoorDeleteBlocked("Missing/oversized public instruction")
    if sha256(prompt.encode("utf8")).hexdigest() != PUBLIC_SHA:
        raise PublicDoorDeleteBlocked("Frozen public instruction digest changed")
    match = PUBLIC_RE.fullmatch(prompt)
    if match is None:
        raise PublicDoorDeleteBlocked("Unsupported public Door deletion grammar")
    guids = match.groupdict()
    if len(set(guids.values())) != 4:
        raise PublicDoorDeleteBlocked("Public GUIDs are not distinct")
    return guids


def _entity(model, guid: str, kind: str):
    try:
        value = model.by_guid(guid)
    except RuntimeError as exc:
        raise PublicDoorDeleteBlocked("Public GUID not found in native source") from exc
    if value is None or not value.is_a(kind):
        raise PublicDoorDeleteBlocked("Wrong public IFC entity class")
    return value


def _source_relations(source, guids) -> dict:
    door = _entity(source, guids["door"], "IfcDoor")
    opening = _entity(source, guids["opening"], "IfcOpeningElement")
    wall = _entity(source, guids["wall"], "IfcWall")
    storey = _entity(source, guids["storey"], "IfcBuildingStorey")
    if (len(door.FillsVoids) != 1
            or door.FillsVoids[0].RelatingOpeningElement != opening
            or len(opening.HasFillings) != 1
            or opening.HasFillings[0].RelatedBuildingElement != door
            or len(opening.VoidsElements) != 1
            or opening.VoidsElements[0].RelatingBuildingElement != wall
            or len(door.ContainedInStructure) != 1
            or door.ContainedInStructure[0].RelatingStructure != storey
            or len(opening.ContainedInStructure) != 0):
        raise PublicDoorDeleteBlocked("Frozen public Door relations do not match source")
    if len(door.ProvidesBoundaries) != 1:
        raise PublicDoorDeleteBlocked("Expected one unmentioned native Door SpaceBoundary")
    if any(x.RelatingSpace is None for x in door.ProvidesBoundaries):
        raise PublicDoorDeleteBlocked("Native Space boundary has invalid endpoint")
    # Native I0 root.remove_product is allowed to cascade these exact
    # dependencies, but absence of an explicit policy for the SpaceBoundary
    # and absent source Opening->Storey relation prevents full task approval.
    return {
        "public_door": door,
        "public_opening": opening,
        "public_host": wall,
        "public_storey": storey,
        "unmentioned_space_boundary": door.ProvidesBoundaries[0],
        "fill_relation": door.FillsVoids[0],
        "void_relation": opening.VoidsElements[0],
    }


def _shape(entity):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    try:
        shape = ifcopenshell.geom.create_shape(settings, entity)
        pts = np.asarray(shape.geometry.verts, dtype=float).reshape(-1, 3)
        vol = float(ifcopenshell.util.shape.get_volume(shape.geometry))
        faces = len(shape.geometry.faces) // 3
    except Exception as exc:
        raise PublicDoorDeleteBlocked("Cannot inspect native product geometry") from exc
    if len(pts) < 4 or faces < 4 or not np.isfinite(pts).all() or not np.isfinite(vol):
        raise PublicDoorDeleteBlocked("Nonfinite/invalid native product mesh")
    return pts, vol, faces


def _mesh_equal(left, right) -> bool:
    xyz_left, vol_left, faces_left = left
    xyz_right, vol_right, faces_right = right
    norm = lambda a: Counter(map(tuple, np.rint(a / TOLERANCE).astype(np.int64)))
    return (
        faces_left == faces_right and abs(vol_left - vol_right) <= TOLERANCE
        and norm(xyz_left) == norm(xyz_right)
    )


def _attribute_unchanged_except_membership(a, b, member_attr: str) -> bool:
    if a.is_a() != b.is_a() or a.GlobalId != b.GlobalId:
        return False
    for index in range(len(a)):
        field = a.attribute_name(index)
        if field == member_attr:
            continue
        if field == "OwnerHistory" and str(a[index]) != str(b[index]):
            # The native IfcOpenShell root API updates the shared type
            # relation's OwnerHistory after removing one of its members.
            # This metadata delta is distinct from product/space edits.
            old_history = a.OwnerHistory
            new_history = b.OwnerHistory
            if (a.is_a() != "IfcRelDefinesByType"
                    or old_history is None or new_history is None
                    or str(new_history.ChangeAction) != "MODIFIED"
                    or new_history.CreationDate != old_history.CreationDate
                    or str(new_history.OwningUser) != str(old_history.OwningUser)
                    or str(new_history.OwningApplication) != str(old_history.OwningApplication)
                    or new_history.LastModifiedDate is None):
                return False
            continue
        if str(a[index]) != str(b[index]):
            return False
    return True


def check_native_i0_result(source_ifc: Path, output_ifc: Path,
                           public_prompt: str) -> dict:
    original_sha = _sha(source_ifc)
    if original_sha != INPUT_SHA:
        raise PublicDoorDeleteBlocked("Original fixed IFC content hash changed")
    output_sha = _sha(output_ifc)
    guids = published_guids(public_prompt)
    for path in (source_ifc, output_ifc):
        with path.open("rb") as handle:
            if not handle.read(96).lstrip(b" \r\n\t").startswith(b"ISO-10303-21;"):
                raise PublicDoorDeleteBlocked("Not a STEP IFC file")
    try:
        before = ifcopenshell.open(str(source_ifc))
        after = ifcopenshell.open(str(output_ifc))
    except Exception as exc:
        raise PublicDoorDeleteBlocked("Cannot reopen IFC deletion evidence") from exc
    if before.schema != "IFC4X3" or after.schema != before.schema:
        raise PublicDoorDeleteBlocked("IFC schema unexpectedly changed")
    source_rel = _source_relations(before, guids)
    a = {obj.GlobalId: obj for obj in before.by_type("IfcRoot")}
    b = {obj.GlobalId: obj for obj in after.by_type("IfcRoot")}
    if set(b) - set(a):
        raise PublicDoorDeleteBlocked("I0 deletion added new native roots")
    gone = {k: a[k] for k in set(a) - set(b)}
    if dict(Counter(x.is_a() for x in gone.values())) != EXPECTED_REMOVED_CLASSES:
        raise PublicDoorDeleteBlocked("Native root deletion differs from observed dependencies")
    for mandatory in (guids["door"], guids["opening"],
                      source_rel["unmentioned_space_boundary"].GlobalId,
                      source_rel["fill_relation"].GlobalId,
                      source_rel["void_relation"].GlobalId):
        if mandatory not in gone:
            raise PublicDoorDeleteBlocked("Required dependent relation or element survived")

    changed = {}
    for guid in set(a) & set(b):
        if a[guid].is_a() != b[guid].is_a():
            raise PublicDoorDeleteBlocked("Preserved native root changed class")
        if str(a[guid]) != str(b[guid]):
            name = a[guid].is_a()
            member = EXPECTED_CHANGED_RELATIONS.get(name)
            if member is None or name in changed:
                raise PublicDoorDeleteBlocked("Unexpected modification of surviving IFC roots")
            if not _attribute_unchanged_except_membership(a[guid], b[guid], member):
                raise PublicDoorDeleteBlocked("Unrelated relationship attributes mutated")
            old_members = {x.GlobalId for x in getattr(a[guid], member)}
            new_members = {x.GlobalId for x in getattr(b[guid], member)}
            if old_members - new_members != {guids["door"]} or new_members - old_members:
                raise PublicDoorDeleteBlocked("Surviving shared relationship was not safely reduced")
            changed[name] = True
    if set(changed) != set(EXPECTED_CHANGED_RELATIONS):
        raise PublicDoorDeleteBlocked("Door not removed from all shared relations")

    if (len(before.by_type("IfcSpace")) != len(after.by_type("IfcSpace"))
            or len(before.by_type("IfcRelSpaceBoundary")) -
            len(after.by_type("IfcRelSpaceBoundary")) != 1
            or len(after.by_guid(guids["wall"]).HasOpenings) !=
            len(before.by_guid(guids["wall"]).HasOpenings) - 1):
        raise PublicDoorDeleteBlocked("Native Space/Wall dependency counts inconsistent")

    old_products = {
        x.GlobalId: x for x in before.by_type("IfcProduct") if x.Representation is not None
    }
    new_products = {
        x.GlobalId: x for x in after.by_type("IfcProduct") if x.Representation is not None
    }
    if set(old_products) - set(new_products) != {guids["door"], guids["opening"]}:
        raise PublicDoorDeleteBlocked("Native product deletion set is wrong")
    if set(new_products) - set(old_products):
        raise PublicDoorDeleteBlocked("Unexpected new native represented product")
    preserved = 0
    for guid in set(old_products) & set(new_products):
        if guid == guids["wall"]:
            continue  # host wall void is expected to change world geometry
        if not _mesh_equal(_shape(old_products[guid]), _shape(new_products[guid])):
            raise PublicDoorDeleteBlocked("Unrelated world-meshed IFC product changed")
        preserved += 1

    host_volume_before = _shape(before.by_guid(guids["wall"]))[1]
    host_volume_after = _shape(after.by_guid(guids["wall"]))[1]
    opening_volume = _shape(source_rel["public_opening"])[1]
    if (opening_volume <= TOLERANCE
            or abs((host_volume_after - host_volume_before) - opening_volume)
            > TOLERANCE):
        raise PublicDoorDeleteBlocked("Host wall void not closed by removing Opening")

    if _sha(source_ifc) != original_sha or _sha(output_ifc) != output_sha:
        raise PublicDoorDeleteBlocked("IFC changed during read-only output validation")
    return {
        "status": "I0_NATIVE_DEPENDENT_DELETION_VERIFIED_OFFICIAL_TASK_BLOCKED",
        "source_ifc_sha256": original_sha,
        "i0_ifc_sha256": output_sha,
        "native_IfcRoot_deleted": len(gone),
        "native_IfcRoot_removed_class_counts": dict(sorted(EXPECTED_REMOVED_CLASSES.items())),
        "surviving_shared_relations_updated": len(changed),
        "shared_type_relation_owner_history_automatically_modified": True,
        "native_original_IfcSpace_count": len(before.by_type("IfcSpace")),
        "native_IfcRelSpaceBoundary_deleted": 1,
        "original_Opening_direct_storey_assignments": 0,
        "native_unrelated_world_meshes_preserved": preserved,
        "host_wall_opening_void_closed": True,
        "host_wall_mesh_volume_gain_m3": round(host_volume_after - host_volume_before, 6),
        "unmentioned_space_boundary_policy_resolved": False,
        "explicit_opening_storey_assignment_existed": False,
        "official_task_oracle_proven": False,
        "official_tasks_scored": 0,
        "provider_model_calls": 0,
    }
