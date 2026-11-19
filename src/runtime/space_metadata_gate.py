"""Source-only IFC Space type/Pset/QTO eligibility and preservation guard.

The toy XML deliberately omits the IFC SpaceType and instance property sets.
A deterministic geometric partition MUST NOT silently infer a new room's
type, room reference, number, area QTO or occupancy. This gate preserves
the source's existing semantic records and returns explicit scientific
blockers instead of fabricating attributes.

The runtime may continue a *manual geometric oracle* with an untyped new
Space; official semantic/task eligibility remains false.
"""
from __future__ import annotations

from dataclasses import dataclass

import ifcopenshell


class SpaceMetadataPolicyError(ValueError):
    """An unsafe or unexpected native Space metadata transition."""


def _by_guid(f, guid, kind):
    if not isinstance(guid,str):
        raise SpaceMetadataPolicyError("Missing expected native Space identity")
    try:
        obj=f.by_guid(guid)
    except RuntimeError as exc:
        raise SpaceMetadataPolicyError("Native IFC Space missing") from exc
    if not obj.is_a(kind):
        raise SpaceMetadataPolicyError("Native IFC product has an unexpected type")
    return obj


def _pset_signature(pset):
    if not pset.is_a("IfcPropertySet"):
        raise SpaceMetadataPolicyError(
            "Unsupported source Space quantities or nonstandard property definition")
    content=[]
    for prop in pset.HasProperties:
        if not prop.is_a("IfcPropertySingleValue"):
            raise SpaceMetadataPolicyError("Unsupported complex native Space property")
        content.append((prop.Name,prop.is_a(),
                        str(prop.NominalValue),str(prop.Unit)))
    return (pset.GlobalId,pset.Name,tuple(sorted(content)))


def _space_metadata(space):
    types=[]
    for link in space.IsTypedBy:
        typ=link.RelatingType
        if not typ.is_a("IfcSpaceType"):
            raise SpaceMetadataPolicyError("Source Space refers to another IFC type family")
        types.append((
            link.GlobalId,typ.GlobalId,typ.Name,str(typ.PredefinedType),
            tuple(sorted(member.GlobalId for member in link.RelatedObjects))))
    definitions=[]
    for link in space.IsDefinedBy:
        quantity=link.RelatingPropertyDefinition
        if quantity.is_a("IfcElementQuantity"):
            raise SpaceMetadataPolicyError(
                "Space quantity set requires explicit split-aware QTO recalculation")
        definitions.append((link.GlobalId,
                            tuple(sorted(x.GlobalId for x in link.RelatedObjects)),
                            _pset_signature(quantity)))
    associations=[]
    for rel in space.HasAssociations:
        associations.append((rel.GlobalId,rel.is_a(),tuple(sorted(
            x.GlobalId for x in rel.RelatedObjects))))
    return (tuple(sorted(types)),tuple(sorted(definitions)),
            tuple(sorted(associations)))


def _catalog(f, except_guid=None):
    return {x.GlobalId:_space_metadata(x) for x in f.by_type("IfcSpace")
            if x.GlobalId!=except_guid}


@dataclass(frozen=True)
class SpaceMetadataGate:
    source_room_type_count:int
    source_room_pset_count:int
    source_room_qto_count:int
    source_room_material_assoc_count:int
    source_instance_reference_properties:int
    other_source_space_metadata_preserved:bool
    original_room_metadata_preserved:bool
    new_room_type_count:int
    new_room_pset_count:int
    new_room_qto_count:int
    new_room_material_assoc_count:int
    unapproved_metadata_replication_rejected:bool=True
    source_no_metadata_fabrication:bool=True

    def report(self)->dict:
        blockers=[]
        if self.source_room_type_count:
            blockers.append("NEW_SPACE_TYPE_OR_FUNCTION_NOT_JUSTIFIED_BY_XML")
        if self.source_room_pset_count:
            blockers.append("NEW_SPACE_INSTANCE_PSETS_NOT_DECLARED_IN_XML")
        if self.source_instance_reference_properties:
            blockers.append("ROOM_SPECIFIC_REFERENCE_NOT_SAFE_TO_CLONE")
        blockers.extend((
            "NEW_SPACE_IDENTITY_NUMBER_POLICY_UNPROVEN",
            "LLM_SEMANTIC_INSTRUCTION_AND_OFFICIAL_SCORING_UNPROVEN",
        ))
        return {
            "status":"PASS_SOURCE_METADATA_PRESERVED_FULL_TASK_STILL_BLOCKED",
            "source_space_type_relations":self.source_room_type_count,
            "source_space_pset_relations":self.source_room_pset_count,
            "source_space_qto_relations":self.source_room_qto_count,
            "source_space_material_associations":self.source_room_material_assoc_count,
            "source_space_instance_reference_properties":
                self.source_instance_reference_properties,
            "new_space_type_relations":self.new_room_type_count,
            "new_space_pset_relations":self.new_room_pset_count,
            "new_space_qto_relations":self.new_room_qto_count,
            "new_space_material_associations":self.new_room_material_assoc_count,
            "existing_room_metadata_preserved":self.original_room_metadata_preserved,
            "other_source_space_metadata_preserved":
                self.other_source_space_metadata_preserved,
            "unapproved_metadata_replication_rejected":
                self.unapproved_metadata_replication_rejected,
            "metadata_semantically_complete":False,
            "official_task_eligible":False,
            "explicit_remaining_gates":blockers,
        }


def preflight_source_room_semantics(source_f,source_room_guid):
    """Called before native mutation: forbid unknown/geometry-dependent QTO."""
    if source_f.schema!="IFC4X3":
        raise SpaceMetadataPolicyError("Space metadata policy supports only IFC4X3")
    room=_by_guid(source_f,source_room_guid,"IfcSpace")
    types,defs,assoc=_space_metadata(room)
    if len(types)>1:
        raise SpaceMetadataPolicyError("Ambiguous multiple source Space types")
    if any(len(link[4])!=1 or source_room_guid not in link[4]
           for link in types):
        raise SpaceMetadataPolicyError(
            "Shared source SpaceType relationship requires explicit split semantics")
    if any(len(rel[1])!=1 or source_room_guid not in rel[1]
           for rel in defs):
        raise SpaceMetadataPolicyError(
            "Shared source Space Pset relationship requires explicit split semantics")
    if assoc:
        raise SpaceMetadataPolicyError(
            "Source Space material/classification association requires split policy")
    return types,defs,assoc


def verify_native_space_metadata(source_f,result_f,source_room_guid,new_space_guid):
    """Validate exact source metadata preservation and conservative new state.

    Fail on copied identity-specific Psets or type, quantity and property
    records that were not declared by the toy XML. Do not declare the new
    room semantically complete just because this native check passes.
    """
    initial=_by_guid(source_f,source_room_guid,"IfcSpace")
    kept=_by_guid(result_f,source_room_guid,"IfcSpace")
    new=_by_guid(result_f,new_space_guid,"IfcSpace")
    old_meta=preflight_source_room_semantics(source_f,source_room_guid)
    after_meta=_space_metadata(kept)
    if old_meta!=after_meta:
        raise SpaceMetadataPolicyError(
            "Existing source Space type/Pset/association relationships mutated")
    others=_catalog(source_f,except_guid=source_room_guid)
    later=_catalog(result_f,except_guid=new_space_guid)
    later.pop(source_room_guid,None)
    if others!=later:
        raise SpaceMetadataPolicyError("Unrelated native Space metadata changed")
    added_meta=_space_metadata(new)
    if any(added_meta):
        raise SpaceMetadataPolicyError(
            "New Space was assigned unsupported or cloned type/Pset/quantity associations")
    num_references=sum(
        1 for rel in initial.IsDefinedBy
        for prop in rel.RelatingPropertyDefinition.HasProperties
        if prop.Name=="Reference")
    return SpaceMetadataGate(
        len(old_meta[0]),len(old_meta[1]),0,len(old_meta[2]),
        num_references,True,True,len(added_meta[0]),len(added_meta[1]),0,
        len(added_meta[2]))
