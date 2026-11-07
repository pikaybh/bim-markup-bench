"""Experimental declarative-source -> IFC4X3 wall-only transactional compiler.

The LLM edits XML source; ALL IfcOpenShell mutation logic runs in this trusted
separate backend. Unimplemented geometry/class/relationship combinations fail
closed without creating an output file.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import math

import ifcopenshell

from src.runtime.xml_parser import MarkupParseError,parse_xml
from src.runtime.ast import semantic_diff
from src.runtime.binder import BindingError,bind_document
from src.runtime.ifc_projection import project_ifc
from src.runtime.ifc_snapshot import IFCSnapshot,SourceIntegrityError,passthrough_noop,snapshot_source
from src.runtime.ifc_mutations import (
    Mutation,UnsupportedIFCMutation,plan_wall_mutations,
    create_standalone_wall,delete_standalone_wall,
    mutate_wall_height,validate_source_mutation_eligibility,by_guid_or_none,
)
from src.runtime.transaction import TransactionError,stage_and_commit


class CompilerError(ValueError):
    pass

@dataclass(frozen=True)
class CompileReport:
    source_sha256: str
    result_sha256: str
    source_graph_fingerprint: str
    result_graph_fingerprint: str
    operations: tuple[Mutation,...]
    untouched_root_objects_verified: int
    unexpected_root_changes: tuple[str,...]
    output_file: Path
    write_committed: bool

    def as_dict(self) -> dict:
        return {
            "status":"COMMITTED_SCOPED_IFC4X3_WALL_EDIT",
            "scope":"Simple straight Wall create/delete and swept-solid height update only",
            "source_sha256":self.source_sha256,
            "result_sha256":self.result_sha256,
            "source_graph_fingerprint":self.source_graph_fingerprint,
            "result_graph_fingerprint":self.result_graph_fingerprint,
            "operations":[op.as_dict() for op in self.operations],
            "untouched_root_objects_verified":self.untouched_root_objects_verified,
            "unexpected_root_changes":list(self.unexpected_root_changes),
            "output_file":self.output_file.name,
            "write_committed":self.write_committed,
            "general_bim_edit_324_supported":False,
        }


def _root_unchanged_integrity(source_path:Path,result_path:Path,
                              actions:tuple[Mutation,...]) -> int:
    """Fail for unexpected changes to IFC root entities and their IDs."""
    a=ifcopenshell.open(str(source_path))
    b=ifcopenshell.open(str(result_path))
    previous={x.GlobalId:x for x in a.by_type("IfcRoot")}
    current={x.GlobalId:x for x in b.by_type("IfcRoot")}
    created={x.ifc_guid for x in actions if x.operation=="CREATE_WALL"}
    deleted={x.ifc_guid for x in actions if x.operation=="DELETE_WALL"}
    if not deleted <= previous.keys():
        raise CompilerError("Unexpected deleted native IFC entity")
    if not created <= current.keys():
        raise CompilerError("Expected created Wall is missing from IFC result")
    extra_old=set(previous)-set(current)-deleted
    extra_new=set(current)-set(previous)-created
    # IfcOpenShell may add/remove only a required containment relationship
    # when a storey previously had none, never an unrelated element.
    changes_containment=any(x.operation in ("CREATE_WALL","DELETE_WALL") for x in actions)
    if extra_old or extra_new:
        if not changes_containment:
            raise CompilerError("IFC relationship inventory changed during height-only update")
        if any(not previous[g].is_a("IfcRelContainedInSpatialStructure") for g in extra_old):
            raise CompilerError("Unapproved original IFC GlobalIds were deleted")
        if any(not current[g].is_a("IfcRelContainedInSpatialStructure") for g in extra_new):
            raise CompilerError("Unapproved new IFC GlobalIds were created")
    untouched=0
    for guid in sorted(set(previous)&set(current)):
        before=previous[guid]
        after=current[guid]
        if before.is_a()!=after.is_a():
            raise CompilerError("IFC class changed for existing GlobalId")
        if str(before)==str(after):
            untouched+=1
            continue
        if before.is_a("IfcRelContainedInSpatialStructure") and any(
            x.operation in ("CREATE_WALL","DELETE_WALL") for x in actions
        ):
            continue
        raise CompilerError("Unexpected modified IFC root entity: "+before.is_a())
    return untouched


def _verify_only_approved_swept_solid_changed(source_path:Path,result_path:Path,
                                             actions:tuple[Mutation,...]) -> None:
    """For height-only edits, check *every* original STEP entity, not just IFC roots.

    Creation/deletion can legitimately add/remove spatial containment and
    geometry subgraphs, so those require a separate fuller change auditor.
    """
    if not actions or any(a.operation!="UPDATE_WALL_HEIGHT" for a in actions):
        return
    from src.runtime.ifc_projection import _body_extrusion
    before=ifcopenshell.open(str(source_path))
    after=ifcopenshell.open(str(result_path))
    allowed=set()
    for op in actions:
        w=before.by_guid(op.ifc_guid)
        allowed.add(_body_extrusion(w).id())
    old={x.id():str(x) for x in before}
    new={x.id():str(x) for x in after}
    if old.keys()!=new.keys():
        raise CompilerError("Height-only change added/deleted IFC entities")
    actual={k for k in old if old[k]!=new[k]}
    if actual!=allowed:
        raise CompilerError("Unexpected IFC entity mutation in height-only update")


def _validate_typed_result(result:Path,source:IFCSnapshot,
                           operations:tuple[Mutation,...],
                           amended_graph) -> None:
    actual=snapshot_source(result)
    if actual.ifc_schema!="IFC4X3":
        raise CompilerError("IFC4X3 schema lost in output")
    if actual.source_sha256==source.source_sha256 and operations:
        raise CompilerError("Expected change but output IFC byte hash is unchanged")
    file=ifcopenshell.open(str(result))
    expected_guid=set(node.ifc_guid for node in amended_graph.nodes)
    for op in operations:
        existing=by_guid_or_none(file,op.ifc_guid)
        if op.operation=="DELETE_WALL":
            if existing is not None:
                raise CompilerError("Deleted native Wall still exists")
        else:
            if existing is None or existing.is_a()!="IfcWall":
                raise CompilerError("Created/updated native IFC Wall missing")
            if op.operation=="UPDATE_WALL_HEIGHT":
                # Physically check changed extrusion, not merely the STEP file header.
                from src.runtime.ifc_projection import _body_extrusion
                depth=float(_body_extrusion(existing).Depth)
                new=amended_graph.by_id()[op.xml_id]
                exp=float(dict(new.attributes)["height"])
                if not math.isclose(depth,exp,abs_tol=1e-6):
                    raise CompilerError("IFC height does not match edited declarative XML")
    _root_unchanged_integrity(source.source_file,result,operations)
    _verify_only_approved_swept_solid_changed(source.source_file,result,operations)


def compile_declarative_xml(source: Path, edited_xml: bytes,
                            destination: Path) -> CompileReport:
    """Apply a preflighted narrow compiler slice and commit a NEW IFC result.

    Never modifies source. Invalid/unsupported edits return an error without
    creating destination. Do not call with LLM-generated Python.
    """
    try:
        projected=project_ifc(source)
        before_doc=parse_xml(projected.xml,
            expected_source_sha256=projected.source.source_sha256)
        after_doc=parse_xml(edited_xml,
            expected_source_sha256=projected.source.source_sha256)
        before=bind_document(before_doc,projection=projected)
        # Intentional graph edits may differ from native *input* relations.
        after=bind_document(after_doc,projection=projected,verify_native_edges=False)
        plan=plan_wall_mutations(before_doc,after_doc,before,after)
        if not plan:
            original=passthrough_noop(projected.source,before_doc,after_doc,destination)
            return CompileReport(
                projected.source.source_sha256,original.source_sha256,
                projected.source.graph_fingerprint,original.graph_fingerprint,
                (),len(projected.source.global_ids),(),destination,True)
        model=ifcopenshell.open(str(source))
        validate_source_mutation_eligibility(model,plan)
        if snapshot_source(source).source_sha256!=projected.source.source_sha256:
            raise CompilerError("Source IFC changed during compiler preflight")
        old=before.graph.by_id()
        new=after.graph.by_id()
        # Preflight all new Wall dimensions and level references, and all
        # existing wall geometry, before beginning any in-memory mutation.
        for op in plan:
            if op.operation=="CREATE_WALL":
                attrs=dict(new[op.xml_id].attributes)
                level=new.get(attrs["level"])
                if level is None or level.kind!="Level" or level.provenance!="existing_source":
                    raise CompilerError("New Wall requires an existing native storey")
            elif op.operation=="UPDATE_WALL_HEIGHT":
                if by_guid_or_none(model,op.ifc_guid) is None:
                    raise CompilerError("Update wall missing from native original")
        def writer(stage:Path):
            # Cloning is only inside this in-memory file handle.
            for op in plan:
                if op.operation=="UPDATE_WALL_HEIGHT":
                    mutate_wall_height(model,by_guid_or_none(model,op.ifc_guid),
                                       __import__("decimal").Decimal(dict(new[op.xml_id].attributes)["height"]))
                elif op.operation=="CREATE_WALL":
                    attrs=dict(new[op.xml_id].attributes)
                    storey=new[attrs["level"]]
                    create_standalone_wall(model,attrs,op.ifc_guid,storey.ifc_guid)
                elif op.operation=="DELETE_WALL":
                    delete_standalone_wall(model,op.ifc_guid)
                else:
                    raise UnsupportedIFCMutation("Unimplemented compiler operation")
            model.write(str(stage))

        def validator(stage:Path):
            if snapshot_source(source).source_sha256!=projected.source.source_sha256:
                raise CompilerError("Source IFC changed before transaction commit")
            _validate_typed_result(stage,projected.source,plan,after.graph)

        stage_and_commit(destination,writer,validator)
        output=snapshot_source(destination)
        untouched=_root_unchanged_integrity(source,destination,plan)
        if snapshot_source(source).source_sha256!=projected.source.source_sha256:
            raise CompilerError("Original IFC changed during result commit")
        return CompileReport(
            projected.source.source_sha256,output.source_sha256,
            projected.source.graph_fingerprint,output.graph_fingerprint,
            plan,untouched,(),destination,True)
    except (MarkupParseError,BindingError,SourceIntegrityError,
            UnsupportedIFCMutation,TransactionError,CompilerError) as exc:
        raise CompilerError(type(exc).__name__+": "+str(exc)[:220]) from exc
