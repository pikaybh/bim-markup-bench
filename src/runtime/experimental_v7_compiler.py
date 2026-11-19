"""Prospective research-only v0.7 single-operation compiler for formerly blocked input IFC4X3.

The source XML is a *complete declarative state*, not a command list.
The trusted backend infers exactly one semantic change against the exact
source-pinned v0.7 partial projection. Original IFC4X3 opaque geometry
and legacy IFC2X3/IFC4 sources are NEVER rebuilt/relabelled.

Supported native edits: one mapped Column rigid XYZ translation, or one
new direct rectangular Slab on a zero-elevation original storey.
"""
from __future__ import annotations

from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.util.element
import ifcopenshell.util.unit
import numpy as np

from src.runtime.compiler import CompileReport
from src.runtime.ifc_mutations import Mutation
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document
from src.runtime.semantic_graph import graph_diff
from src.runtime.transaction import stage_and_commit
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.experimental_v7_projection import project_ifc_v7
from src.runtime.experimental_v4_slab import (
    _params,_verify_mesh,_native_add_preservation,
)
from src.runtime.experimental_v2_column import _body_context
from src.runtime.experimental_v3_column import (
    _resolve,_placement_point,_unchanged_after_update,
)


class V7CompileError(ValueError):
    pass


class V7CompileReport(CompileReport):
    def as_dict(self):
        out=super().as_dict()
        out.update({
            "status":"COMMITTED_SCOPED_IFC4X3_"+self.operations[0].operation+"_V7",
            "compiler_version":"experimental-source-compat-v0.7",
            "full_45_task_equivalence_with_Python_IFC":False,
            "legacy_IFC2X3_IFC4_native_edit_supported":False,
            "original_ifc_opaque_geometry_rebuilt":False,
            "experimental_isolated_single_edit":True,
        })
        return out


def compile_declarative_xml_v7(source:Path,edited_xml:bytes,destination:Path):
    if (not source.is_file() or source.is_symlink() or destination.exists()
        or destination.is_symlink()):
        raise V7CompileError("Source IFC must exist; candidate output must be unused")
    p=project_ifc_v7(source)
    before_doc=parse_xml(p.xml,expected_source_sha256=p.source.source_sha256)
    after_doc=parse_xml(edited_xml,expected_source_sha256=p.source.source_sha256)
    before=bind_document(before_doc,projection=p)
    after=bind_document(after_doc,projection=p,verify_native_edges=False)
    diff=graph_diff(before.graph,after.graph)
    old=before.graph.by_id()
    new=after.graph.by_id()
    f=ifcopenshell.open(str(source))
    if f.schema!="IFC4X3" or abs(ifcopenshell.util.unit.calculate_unit_scale(f)-1.)>1e-8:
        raise V7CompileError("Only a metre-normalized IFC4X3 original source is editable")
    source_sha=p.source.source_sha256
    if snapshot_source(source).source_sha256!=source_sha:
        raise V7CompileError("Original IFC bytes changed while freezing projection")
    if (diff.removed_nodes or diff.removed_edges or diff.changed_nodes and diff.added_nodes
        or len(diff.added_nodes)+len(diff.changed_nodes)!=1):
        raise V7CompileError("Only exactly one existing Column MOVE or one Slab CREATE")
    changed_fields=()
    if diff.changed_nodes:
        localid=diff.changed_nodes[0]
        if diff.added_edges or diff.removed_edges:
            raise V7CompileError("Mapped Column move cannot change relations")
        original=old[localid]
        target=new[localid]
        if (original.kind!="Column" or original.provenance!="existing_source"
            or target.kind!=original.kind or target.ifc_guid!=original.ifc_guid):
            raise V7CompileError("Only one pre-existing native mapped Column may move")
        a=dict(original.attributes)
        b=dict(target.attributes)
        changed_fields=tuple(sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)))
        if not changed_fields or not set(changed_fields)<={"x","y","z"}:
            raise V7CompileError("Only native Column x/y/z can change")
        old_xyz=np.array([float(a[key]) for key in ("x","y","z")],dtype=float)
        new_xyz=np.array([float(b[key]) for key in ("x","y","z")],dtype=float)
        delta_xyz=new_xyz-old_xyz
        if not np.all(np.isfinite(delta_xyz)) or np.any(np.abs(delta_xyz)>100):
            raise V7CompileError("Column move outside bounded original native displacement")
        column=_resolve(f,original.ifc_guid)
        if not any(x.is_a("IfcMappedItem") for rep in column.Representation.Representations for x in rep.Items):
            raise V7CompileError("v0.7 Column move restricted to original mapped IFC geometry")
        point=_placement_point(f,column)
        source_ref=point.id()
        guid=original.ifc_guid
        op="MOVE_ORIGINAL_MAPPED_COLUMN"
        level=None
        slab_params=None
    else:
        localid=diff.added_nodes[0]
        node=new[localid]
        if node.kind!="Slab" or node.provenance!="deterministic_new":
            raise V7CompileError("Only deterministic newly authored Slab is creatable")
        if (set(diff.added_edges)!={e for e in diff.added_edges if e.relation=="in_storey" and e.target==localid}
            or len(diff.added_edges)!=1):
            raise V7CompileError("New Slab must have precisely one original source storey reference")
        level=new[dict(node.attributes)["level"]]
        if level.kind!="Level" or level.provenance!="existing_source":
            raise V7CompileError("New Slab must use existing native IFC BuildingStorey")
        storey=f.by_guid(level.ifc_guid)
        if (not storey.is_a("IfcBuildingStorey") or storey.Elevation is None
            or abs(float(storey.Elevation))>1e-8):
            raise V7CompileError("New Slab limited to original zero-elevation storey")
        slab_params=_params(dict(node.attributes))
        guid=node.ifc_guid
        if guid in {x.GlobalId for x in f.by_type("IfcRoot")}:
            raise V7CompileError("Deterministic Slab GUID collides with original IFC")
        body=_body_context(f)
        # IfcOpenShell spatial.assign_container may reorder the IFC SET
        # of pre-existing contained products non-deterministically. Preserve
        # each source relation's original sequence and append ONLY the new
        # Slab, so repeated identical source/state yields byte-stable IFC.
        source_containment_order={
            rel.GlobalId:tuple(x.GlobalId for x in rel.RelatedElements)
            for rel in f.by_type("IfcRelContainedInSpatialStructure")
        }
        # This prospective RESEARCH artifact uses source-anchored
        # provenance timestamps for new IfcOwnerHistory records so identical
        # source+XML pairs produce identical IFC evidence bytes across runs.
        # It is NOT an actual wall-clock creation date. Original existing
        # OwnerHistory records (and their dates) remain completely untouched.
        old_histories=f.by_type("IfcOwnerHistory")
        if not old_histories or any(h.CreationDate is None for h in old_histories):
            raise V7CompileError("Cannot pin deterministic experimental OwnerHistory without native source epoch")
        fixed_source_epoch=max(int(h.CreationDate) for h in old_histories)
        original_history_ids={h.id() for h in old_histories}
        op="CREATE_SLAB_FROM_BOOTSTRAP"
        changed_fields=("geometry","level")
        source_ref=None

    def writer(path):
        if op=="MOVE_ORIGINAL_MAPPED_COLUMN":
            # Preserve shared IfcMappedItem/type geometry byte-for-byte.
            point.Coordinates=tuple(float(point.Coordinates[i])+float(delta_xyz[i]) for i in range(3))
        elif op=="CREATE_SLAB_FROM_BOOTSTRAP":
            x,y,z,width,depth,thickness=slab_params
            slab=ifcopenshell.api.root.create_entity(
                f,ifc_class="IfcSlab",name="Research declarative Slab v0.7")
            slab.GlobalId=guid
            slab.PredefinedType="FLOOR"
            prof=f.createIfcRectangleProfileDef("AREA",None,None,width,depth)
            rep=ifcopenshell.api.geometry.add_profile_representation(
                f,context=body,profile=prof,depth=thickness)
            ifcopenshell.api.geometry.assign_representation(f,product=slab,representation=rep)
            placement=np.eye(4,dtype=float)
            placement[:3,3]=[x+width/2,y+depth/2,z]
            ifcopenshell.api.geometry.edit_object_placement(f,product=slab,matrix=placement)
            ifcopenshell.api.spatial.assign_container(f,products=[slab],relating_structure=storey)
            changed_containment=0
            for relation_guid,ordered_source_guids in source_containment_order.items():
                relation=f.by_guid(relation_guid)
                native_members={x.GlobalId for x in relation.RelatedElements}
                source_members=set(ordered_source_guids)
                if native_members==source_members|{guid}:
                    changed_containment+=1
                    fixed_guids=(*ordered_source_guids,guid)
                elif native_members==source_members:
                    fixed_guids=ordered_source_guids
                else:
                    raise V7CompileError("Native Slab create corrupted original containment members")
                relation.RelatedElements=tuple(f.by_guid(g) for g in fixed_guids)
            if changed_containment!=1:
                raise V7CompileError("New Slab must extend exactly one original storey relation")
            for owner_history in f.by_type("IfcOwnerHistory"):
                if owner_history.id() in original_history_ids:
                    continue
                owner_history.CreationDate=fixed_source_epoch
                if owner_history.LastModifiedDate is not None:
                    owner_history.LastModifiedDate=fixed_source_epoch
        else:
            raise V7CompileError("Unrecognized v0.7 native edit")
        f.write(str(path))

    def validate(path):
        if snapshot_source(source).source_sha256!=source_sha:
            raise V7CompileError("Original source changed during candidate")
        if op=="MOVE_ORIGINAL_MAPPED_COLUMN":
            _unchanged_after_update(source,path,guid,source_ref)
            # Physical native mesh validation belongs to independent oracle
            # and is NOT asserted from copied XML bounds alone.
            from src.runtime.experimental_v2_column import _world_bbox
            old_model=ifcopenshell.open(str(source))
            new_model=ifcopenshell.open(str(path))
            x0,y0=_world_bbox(old_model.by_guid(guid))
            x1,y1=_world_bbox(new_model.by_guid(guid))
            if not np.allclose(np.asarray(x1)-x0,delta_xyz,atol=1e-5):
                raise V7CompileError("New native mapped Column world mesh bounds not translated")
            if not np.allclose(np.asarray(y1)-y0,delta_xyz,atol=1e-5):
                raise V7CompileError("New native mapped Column world max bounds not translated")
        else:
            result=ifcopenshell.open(str(path))
            _verify_mesh(result,guid,slab_params)
            containing=ifcopenshell.util.element.get_container(result.by_guid(guid))
            if containing is None or containing.GlobalId!=level.ifc_guid:
                raise V7CompileError("New Slab not contained in intended original storey")
            _native_add_preservation(source,path,guid)

    stage_and_commit(destination,writer,validate)
    if snapshot_source(source).source_sha256!=source_sha:
        raise V7CompileError("Original source modified after validated output")
    dest=snapshot_source(destination)
    if op=="MOVE_ORIGINAL_MAPPED_COLUMN":
        unchanged=_unchanged_after_update(source,destination,guid,source_ref)
    else:
        unchanged=_native_add_preservation(source,destination,guid)
    line=after_doc.managed_by_id()[localid].span.line
    mutation=Mutation(op,localid,guid,line,changed_fields,
        "experimental v0.7 formerly unprojectable IFC4X3 input; source preserving")
    return V7CompileReport(
        source_sha,dest.source_sha256,
        p.source.graph_fingerprint,dest.graph_fingerprint,
        (mutation,),unchanged,(),destination,True)
