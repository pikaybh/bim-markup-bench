"""Typed, immutable v0.1 declarative state and source-map records.

This is NOT the full IFC semantic/geometry graph. Source bytes are retained
verbatim so diagnostics and later source-preserving patches remain possible.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

Scalar = str | Decimal

@dataclass(frozen=True)
class SourceSpan:
    file: str
    line: int
    column: int
    start_byte: int
    start_tag_end_byte: int

    def as_dict(self) -> dict:
        return {
            "file": self.file, "line": self.line, "column": self.column,
            "start_byte": self.start_byte, "start_tag_end_byte": self.start_tag_end_byte
        }

@dataclass(frozen=True)
class ElementNode:
    kind: str
    id: str | None
    ifc_guid: str | None
    raw_attributes: tuple[tuple[str, str], ...]
    typed_attributes: tuple[tuple[str, Scalar], ...]
    span: SourceSpan
    role: Literal["element", "relation", "level"]

    def attrs(self) -> dict[str, Scalar]:
        return dict(self.typed_attributes)

    def semantic_key(self) -> tuple:
        # Source position, whitespace and input attribute order are not semantic.
        return self.kind, self.id, tuple(sorted(self.typed_attributes))

    def relation_key(self) -> tuple:
        if self.role != "relation":
            raise ValueError("Only relationship nodes have relation keys")
        return self.kind, tuple(sorted(self.typed_attributes))

@dataclass(frozen=True)
class BuildingDocument:
    source_filename: str
    source_bytes: bytes
    source_byte_sha256: str
    semantic_sha256: str
    source_model_sha256: str
    namespace: str
    units: str
    ifc_schema: str
    levels: tuple[ElementNode, ...]
    elements: tuple[ElementNode, ...]
    relations: tuple[ElementNode, ...]
    root_span: SourceSpan

    def all_nodes(self) -> tuple[ElementNode, ...]:
        return (*self.levels, *self.elements, *self.relations)

    def managed_by_id(self) -> dict[str, ElementNode]:
        # Full semantic binder may later have opaque references to IFC source.
        return {x.id: x for x in (*self.levels, *self.elements) if x.id is not None}

@dataclass(frozen=True)
class ChangeSet:
    created: tuple[str, ...]
    modified: tuple[str, ...]
    deleted: tuple[str, ...]
    relations_added: tuple[tuple, ...]
    relations_removed: tuple[tuple, ...]
    input_source_sha256: str
    old_semantic_sha256: str
    new_semantic_sha256: str
    effect: str

    def as_dict(self) -> dict:
        return {
            "created": list(self.created), "modified": list(self.modified),
            "deleted": list(self.deleted),
            "relations_added": [list(x) for x in self.relations_added],
            "relations_removed": [list(x) for x in self.relations_removed],
            "input_source_sha256": self.input_source_sha256,
            "old_semantic_sha256": self.old_semantic_sha256,
            "new_semantic_sha256": self.new_semantic_sha256,
            "effect": self.effect,
            "ifc_mutated": False,
        }


def semantic_diff(previous: BuildingDocument, edited: BuildingDocument) -> ChangeSet:
    """Pure XML state diff. No IFC IO or geometry mutation occurs."""
    if previous.source_model_sha256 != edited.source_model_sha256:
        raise ValueError("Source IFC hash changed between XML snapshots")
    if previous.ifc_schema != edited.ifc_schema or previous.namespace != edited.namespace:
        raise ValueError("Model schema or XML namespace changed")
    old=previous.managed_by_id()
    new=edited.managed_by_id()
    common=old.keys() & new.keys()
    for name in common:
        if old[name].kind != new[name].kind:
            raise ValueError("Element kind changed at stable ID: "+name)
        if old[name].ifc_guid and old[name].ifc_guid != new[name].ifc_guid:
            raise ValueError("Existing IFC GlobalId was modified at stable ID: "+name)
    r_old=set(x.relation_key() for x in previous.relations)
    r_new=set(x.relation_key() for x in edited.relations)
    created=tuple(sorted(new.keys()-old.keys()))
    modified=tuple(sorted(name for name in common if old[name].semantic_key()!=new[name].semantic_key()))
    deleted=tuple(sorted(old.keys()-new.keys()))
    r_added=tuple(sorted(r_new-r_old))
    r_removed=tuple(sorted(r_old-r_new))
    effect="NO_OP" if not any((created,modified,deleted,r_added,r_removed)) else "DECLARATIVE_STATE_DIFF"
    return ChangeSet(created,modified,deleted,r_added,r_removed,
                     previous.source_model_sha256,previous.semantic_sha256,
                     edited.semantic_sha256,effect)
