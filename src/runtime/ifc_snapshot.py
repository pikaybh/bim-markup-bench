"""Immutable IFC backing model manifest and lossless NO-EDIT passthrough.

This does not compile XML edits. Only verified semantic no-ops are allowed;
all real IFC mutation remains a separate gated feature (#12/#13).
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
import tempfile

import ifcopenshell

from src.runtime.ast import BuildingDocument, semantic_diff
from src.runtime.xml_parser import parse_xml

class SourceIntegrityError(ValueError):
    pass

@dataclass(frozen=True)
class IFCSnapshot:
    source_sha256: str
    ifc_schema: str
    file_size: int
    entity_count: int
    graph_fingerprint: str
    global_ids: tuple[tuple[str,str], ...]
    named_relation_memberships: tuple[tuple[str,tuple[str,...]], ...]
    entity_class_counts: tuple[tuple[str,int], ...]
    source_file: Path

    def manifest(self) -> dict:
        # Backend-only structural record, not a model-visible prompt.
        return {
            "source_sha256":self.source_sha256,"ifc_schema":self.ifc_schema,
            "file_size":self.file_size, "entity_count":self.entity_count,
            "graph_fingerprint":self.graph_fingerprint,
            "ifc_root_objects":len(self.global_ids),
            "relation_edges":len(self.named_relation_memberships),
            "entity_class_counts":dict(self.entity_class_counts),
            "property_set_count":dict(self.entity_class_counts).get("IfcPropertySet",0),
            "material_count":dict(self.entity_class_counts).get("IfcMaterial",0),
        }


def _sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda:source.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_source(path: Path) -> IFCSnapshot:
    """Read-only open: exact bytes, full STEP entity fingerprint and GUID graph."""
    if not path.is_file() or path.is_symlink():
        raise SourceIntegrityError("IFC input must be an existing regular, non-symlinked file")
    before=_sha256(path)
    try:
        f=ifcopenshell.open(str(path))
    except Exception as exc:
        raise SourceIntegrityError("IFC source failed to parse as a valid IFC file") from exc

    root_by_guid={}
    relation_memberships=[]
    type_counts={}
    lines=[]
    for entity in f:
        type_counts[entity.is_a()] = type_counts.get(entity.is_a(),0)+1
        # A full typed-entity STEP fingerprint detects changes in root and
        # non-root representations, Psets, placements, materials and relations.
        lines.append((entity.id(),str(entity)))
        if entity.is_a("IfcRoot"):
            guid=entity.GlobalId
            if guid in root_by_guid:
                raise SourceIntegrityError("Duplicate IFC GlobalIds in input")
            root_by_guid[guid]=entity.is_a()
        if entity.is_a("IfcRelationship"):
            # Extract typed relation endpoints, not inverse relations.
            guids=[]
            for item in entity:
                if isinstance(item,ifcopenshell.entity_instance) and item.is_a("IfcRoot"):
                    guids.append(item.GlobalId)
                elif isinstance(item,tuple):
                    guids.extend(x.GlobalId for x in item
                                 if isinstance(x,ifcopenshell.entity_instance)
                                 and x.is_a("IfcRoot"))
            relation_memberships.append((entity.GlobalId,tuple(sorted(set(guids)))))
    stable_lines="\n".join(t for _,t in sorted(lines)).encode("utf-8")
    graph_hash=hashlib.sha256(stable_lines).hexdigest()
    after=_sha256(path)
    if before!=after:
        raise SourceIntegrityError("Input IFC changed during read-only snapshot")
    return IFCSnapshot(
        source_sha256=before,ifc_schema=f.schema,file_size=path.stat().st_size,
        entity_count=len(lines),graph_fingerprint=graph_hash,
        global_ids=tuple(sorted(root_by_guid.items())),
        named_relation_memberships=tuple(sorted(relation_memberships)),
        entity_class_counts=tuple(sorted(type_counts.items())),
        source_file=path.resolve(),
    )


def passthrough_noop(source: IFCSnapshot, initial: BuildingDocument,
                     edited: BuildingDocument, destination: Path) -> IFCSnapshot:
    """Only an XML semantic no-op can produce a byte-identical IFC copy.

    Not a runtime compiler. No mutation code is reachable through this path.
    """
    if source.source_sha256 != initial.source_model_sha256:
        raise SourceIntegrityError("Projection is not bound to original IFC bytes")
    if edited.source_model_sha256 != source.source_sha256:
        raise SourceIntegrityError("Edited XML changed immutable IFC reference")
    if semantic_diff(initial,edited).effect != "NO_OP":
        raise SourceIntegrityError("Edited IFC compilation unavailable; refuse non-noop change")
    if destination.exists() or destination.is_symlink():
        raise SourceIntegrityError("Refuse to overwrite an existing destination")
    if destination.resolve() == source.source_file.resolve():
        raise SourceIntegrityError("Never overwrite immutable source IFC")
    if _sha256(source.source_file) != source.source_sha256:
        raise SourceIntegrityError("Source IFC bytes changed since projection")
    destination.parent.mkdir(parents=True,exist_ok=True)
    fd,tmpname=tempfile.mkstemp(prefix=".ifc-stage-",suffix=".ifc",dir=destination.parent)
    os.close(fd)
    tmp=Path(tmpname)
    try:
        with source.source_file.open("rb") as inp, tmp.open("wb") as out:
            shutil.copyfileobj(inp,out,length=1024*1024)
            out.flush()
            os.fsync(out.fileno())
        if _sha256(tmp)!=source.source_sha256:
            raise SourceIntegrityError("Staged pass-through bytes differ from immutable IFC")
        staged_snapshot=snapshot_source(tmp)
        if staged_snapshot.graph_fingerprint!=source.graph_fingerprint:
            raise SourceIntegrityError("Staged IFC graph differs")
        if staged_snapshot.global_ids!=source.global_ids:
            raise SourceIntegrityError("Unchanged IFC object identities differ")
        if staged_snapshot.named_relation_memberships!=source.named_relation_memberships:
            raise SourceIntegrityError("Unchanged IFC relations differ")
        # Atomic exclusive destination creation: never clobber a concurrent
        # output, even if it appeared after the initial existence test.
        try:
            os.link(tmp, destination, follow_symlinks=False)
        except FileExistsError as exc:
            raise SourceIntegrityError("Destination appeared while staging IFC") from exc
        return snapshot_source(destination)
    finally:
        if tmp.exists():
            tmp.unlink()
