"""Scoped IFC4X3 Door+Opening deletion for a native dependent pair.

TRUSTED runtime only. The direct-markup model edits declarative XML nodes
and never receives these IFC mutation routines. This is a conservative
source-only dependency policy, not a general Door/Room delete primitive.

Prospective policy: a native IfcRelSpaceBoundary whose RelatedBuildingElement
is the removed Door MUST be deleted to prevent a dangling relationship. The
remaining Room geometry and its unrelated boundaries are preserved, NOT
reconstructed. An official BIM-Edit success is NOT implied.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.geom
import ifcopenshell.util.shape
import numpy as np

from src.runtime.ifc_mutations import UnsupportedIFCMutation, by_guid_or_none

_REQUIRED_DOOR_INVERSES = Counter({
    "IfcRelFillsElement": 1,
    "IfcRelVoidsElement": 0,
    "IfcRelSpaceBoundary": 1,
    "IfcRelContainedInSpatialStructure": 1,
    "IfcRelAssociatesMaterial": 1,
    "IfcRelAssociatesClassification": 1,
    "IfcRelDefinesByProperties": 2,
    "IfcRelDefinesByType": 1,
})
_REQUIRED_OPENING_INVERSES = Counter({
    "IfcRelFillsElement": 1, "IfcRelVoidsElement": 1,
})
_TOL = 1e-6


@dataclass(frozen=True)
class ScopedDoorDelete:
    door_guid: str
    opening_guid: str
    host_guid: str
    storey_guid: str
    removed_roots: tuple[str, ...]
    affected_shared_roots: tuple[str, ...]
    boundary_guid: str
    host_volume_before: float
    opening_volume_before: float


def _geometry(entity) -> tuple[np.ndarray, int, float]:
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    try:
        shape = ifcopenshell.geom.create_shape(settings, entity)
        verts = np.asarray(shape.geometry.verts, dtype=float).reshape(-1, 3)
        nfaces = len(shape.geometry.faces)//3
        volume = float(ifcopenshell.util.shape.get_volume(shape.geometry))
    except Exception as exc:
        raise UnsupportedIFCMutation("Cannot inspect native Door delete geometry") from exc
    if (len(verts) < 4 or nfaces < 4 or not np.isfinite(verts).all()
            or not math.isfinite(volume) or volume <= 0):
        raise UnsupportedIFCMutation("Native Door-delete geometry invalid")
    return verts, nfaces, volume


def _source_pair(model, door_guid: str, opening_guid: str):
    door = by_guid_or_none(model, door_guid)
    opening = by_guid_or_none(model, opening_guid)
    if (door is None or opening is None
            or not door.is_a("IfcDoor")
            or not opening.is_a("IfcOpeningElement")):
        raise UnsupportedIFCMutation("Door+Opening delete requires exact native typed pair")
    fills = list(door.FillsVoids)
    voids = list(opening.VoidsElements)
    if (len(fills) != 1 or fills[0].RelatingOpeningElement != opening
            or len(opening.HasFillings) != 1
            or opening.HasFillings[0].RelatedBuildingElement != door
            or len(voids) != 1 or not voids[0].RelatingBuildingElement.is_a("IfcWall")
            or len(opening.ContainedInStructure) != 0):
        raise UnsupportedIFCMutation("Door/Opening/Wall relationship or opening storey ambiguous")
    return door, opening, fills[0], voids[0].RelatingBuildingElement, voids[0]


def preflight_door_opening_deletion(model, door_guid: str,
                                    opening_guid: str) -> ScopedDoorDelete:
    """Accept only exact native inverse dependencies and shared membership."""
    door, opening, fill, host, void = _source_pair(
        model, door_guid, opening_guid)
    inv_door = list(model.get_inverse(door))
    inv_opening = list(model.get_inverse(opening))
    if (Counter(r.is_a() for r in inv_door) !=
            +_REQUIRED_DOOR_INVERSES
            or Counter(r.is_a() for r in inv_opening) !=
            _REQUIRED_OPENING_INVERSES):
        raise UnsupportedIFCMutation("Door+Opening has unsupported native inverse dependencies")
    boundary = list(door.ProvidesBoundaries)[0]
    containment = list(door.ContainedInStructure)[0]
    storey = containment.RelatingStructure
    if (not storey.is_a("IfcBuildingStorey")
            or boundary.RelatedBuildingElement != door
            or boundary.RelatingSpace is None
            or not boundary.RelatingSpace.is_a("IfcSpace")
            or len(door.ProvidesBoundaries) != 1
            or len(door.ContainedInStructure) != 1):
        raise UnsupportedIFCMutation("Door boundary/storey dependency is not uniquely scoped")

    root_deleted = [door, opening, fill, void, boundary]
    shared = [containment]
    for rel in inv_door:
        if rel.is_a("IfcRelAssociatesMaterial"):
            if tuple(rel.RelatedObjects) != (door,):
                raise UnsupportedIFCMutation("Door material assignment is shared")
            root_deleted.append(rel)
        elif rel.is_a("IfcRelDefinesByProperties"):
            if tuple(rel.RelatedObjects) != (door,):
                raise UnsupportedIFCMutation("Door property assignment is shared")
            ps = rel.RelatingPropertyDefinition
            if (ps is None or not ps.is_a("IfcPropertySet")
                    or set(model.get_inverse(ps)) != {rel}):
                raise UnsupportedIFCMutation("Door property set ownership is ambiguous")
            root_deleted.extend([rel, ps])
        elif rel.is_a("IfcRelDefinesByType"):
            if door not in rel.RelatedObjects or len(rel.RelatedObjects) < 2:
                raise UnsupportedIFCMutation("Door type relation is not safely shared")
            shared.append(rel)
        elif rel.is_a("IfcRelAssociatesClassification"):
            if door not in rel.RelatedObjects or len(rel.RelatedObjects) < 2:
                raise UnsupportedIFCMutation("Door classification is not safely shared")
            shared.append(rel)
    if (len(root_deleted) != 10 or len(shared) != 3
            or len({r.GlobalId for r in root_deleted}) != len(root_deleted)
            or len({r.GlobalId for r in shared}) != len(shared)):
        raise UnsupportedIFCMutation("Door delete dependent roots are not uniquely classified")
    return ScopedDoorDelete(
        door_guid, opening_guid, host.GlobalId, storey.GlobalId,
        tuple(sorted(x.GlobalId for x in root_deleted)),
        tuple(sorted(x.GlobalId for x in shared)),
        boundary.GlobalId,
        _geometry(host)[2], _geometry(opening)[2],
    )


def remove_scoped_door_opening(model, pair: ScopedDoorDelete) -> None:
    """Native mutation is confined to a preflighted clone in the compiler."""
    fresh = preflight_door_opening_deletion(model, pair.door_guid, pair.opening_guid)
    if fresh != pair:
        raise UnsupportedIFCMutation("Native dependency inventory changed after preflight")
    door, opening, _, _, _ = _source_pair(model, pair.door_guid, pair.opening_guid)
    ifcopenshell.api.root.remove_product(model, product=door)
    ifcopenshell.api.root.remove_product(model, product=opening)
    if (by_guid_or_none(model, pair.door_guid) is not None
            or by_guid_or_none(model, pair.opening_guid) is not None):
        raise UnsupportedIFCMutation("Native Door/Opening deletion incomplete")


def _membership(root, attr: str) -> set[str]:
    return {x.GlobalId for x in getattr(root, attr)}


def _nonmembership_equal(left, right, attr: str) -> bool:
    if left.is_a() != right.is_a():
        return False
    for index in range(len(left)):
        name = left.attribute_name(index)
        if name == attr:
            continue
        if left.is_a("IfcRelDefinesByType") and name == "OwnerHistory":
            # Native IfcOpenShell API updates only the type relation's
            # OwnerHistory.ChangeAction and LastModifiedDate.
            prior, post = left.OwnerHistory, right.OwnerHistory
            if (prior is None or post is None
                    or str(post.ChangeAction) != "MODIFIED"
                    or post.CreationDate != prior.CreationDate
                    or str(post.OwningUser) != str(prior.OwningUser)
                    or str(post.OwningApplication) != str(prior.OwningApplication)
                    or post.LastModifiedDate is None):
                return False
            continue
        if str(left[index]) != str(right[index]):
            return False
    return True


def _same_mesh(a, b) -> bool:
    va, fa, vola = _geometry(a)
    vb, fb, volb = _geometry(b)
    quantize = lambda xyz: Counter(map(
        tuple, np.rint(xyz/_TOL).astype(np.int64)))
    return (fa == fb and abs(vola - volb) <= _TOL
            and quantize(va) == quantize(vb))


def verify_scoped_door_delete_output(before, after,
                                     pair: ScopedDoorDelete) -> int:
    """Validate exact native relation cleanup and full physical preservation."""
    if before.schema != "IFC4X3" or after.schema != before.schema:
        raise UnsupportedIFCMutation("Native IFC4X3 schema changed")
    if preflight_door_opening_deletion(before,pair.door_guid,pair.opening_guid) != pair:
        raise UnsupportedIFCMutation("Preflight source native IFC changed")
    roots_before = {r.GlobalId:r for r in before.by_type("IfcRoot")}
    roots_after = {r.GlobalId:r for r in after.by_type("IfcRoot")}
    if (set(roots_before)-set(roots_after) != set(pair.removed_roots)
            or set(roots_after)-set(roots_before)):
        raise UnsupportedIFCMutation("Door-delete native root set differs from approved dependencies")
    for key, entity in roots_before.items():
        if key not in roots_after:
            continue
        output = roots_after[key]
        if entity.is_a() != output.is_a():
            raise UnsupportedIFCMutation("Surviving root class changed during native deletion")
        if key in pair.affected_shared_roots:
            relclass=entity.is_a()
            attr = (
                "RelatedElements" if relclass=="IfcRelContainedInSpatialStructure"
                else "RelatedObjects" if relclass in (
                    "IfcRelAssociatesClassification","IfcRelDefinesByType")
                else None
            )
            if (attr is None or not _nonmembership_equal(entity, output, attr)
                    or _membership(entity,attr)-_membership(output,attr)
                    != {pair.door_guid}
                    or _membership(output,attr)-_membership(entity,attr)):
                raise UnsupportedIFCMutation("Shared source membership or native metadata corrupted")
        elif str(entity) != str(output):
            raise UnsupportedIFCMutation("Unrelated native IFC root modified")
    if (by_guid_or_none(after,pair.host_guid) is None
            or by_guid_or_none(after,pair.storey_guid) is None
            or by_guid_or_none(after,pair.boundary_guid) is not None):
        raise UnsupportedIFCMutation("Host/storey/boundary deletion postcondition failed")

    original_products = {
        p.GlobalId:p for p in before.by_type("IfcProduct") if p.Representation is not None
    }
    changed_products = {
        p.GlobalId:p for p in after.by_type("IfcProduct") if p.Representation is not None
    }
    if (set(original_products)-set(changed_products) !=
            {pair.door_guid,pair.opening_guid}
            or set(changed_products)-set(original_products)):
        raise UnsupportedIFCMutation("Unexpected native product removed or created")
    preserved=0
    for guid in set(original_products)&set(changed_products):
        if guid == pair.host_guid:
            continue
        if not _same_mesh(original_products[guid],changed_products[guid]):
            raise UnsupportedIFCMutation("Unrelated IFC world mesh was altered")
        preserved += 1
    host_after = changed_products.get(pair.host_guid)
    if host_after is None:
        raise UnsupportedIFCMutation("Original host Wall lost its physical mesh")
    new_volume = _geometry(host_after)[2]
    if not math.isclose(new_volume-pair.host_volume_before,
                        pair.opening_volume_before, rel_tol=0,abs_tol=_TOL):
        raise UnsupportedIFCMutation("Deleted Opening did not close host Wall void")
    if (len(after.by_type("IfcSpace")) != len(before.by_type("IfcSpace"))
            or len(before.by_type("IfcRelSpaceBoundary")) -
               len(after.by_type("IfcRelSpaceBoundary")) != 1):
        raise UnsupportedIFCMutation("Unapproved Space or boundary topology mutation")
    return preserved
