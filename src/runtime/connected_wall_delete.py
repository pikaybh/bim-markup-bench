"""v0.27 bounded original IFC4X3 connected Wall deletion via supervised worker.

The direct-markup arm changes ONLY a complete declarative Building XML state
(one existing Wall and its two existing Connects removed). This trusted
runtime component executes native IFC code strictly AFTER XML graph diff
binding. No model-generated Python, special Delete command, arbitrary IFC
mutator, or unsupervised native worker is exposed.

Safety gates:
- Exactly the pinned original-public normalized IFC4X3 source SHA.
- Exact native original Wall, two directed path connections, own three Psets,
  shared storey/type/material/classification members and owned physical shape.
- Hard wall-only graph delta with two exact connects and derived storey edge.
- Fixed native one-shot child process, deadline and crash exit fail-closed.
- Independent parent full original Root / STEP / orphan / layer preservation
  and whole native IFC reprojected XML graph verification.
- Exclusive atomic transaction, source SHA cannot drift.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import ifcopenshell

from src.runtime.ifc_mutations import (
    Mutation, UnsupportedIFCMutation, by_guid_or_none,
)
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.semantic_graph import graph_diff
from src.runtime.transaction import stage_and_commit

PINNED_NORMALIZED_ORIGINAL_IFC_SHA = (
    "16568e7c4b8b9d62567a7a199101269daa6e5b1b7535cec095b8e233ae2ef6ac"
)
CHILD_TIMEOUT_SECONDS = 25
CHILD_MODULE = "tools.bibimbap_v027_wall_native_worker"
CHILD_RESULT_PREFIX = "V027_WORKER_JSON "
SHARED_KINDS = {
    "IfcRelContainedInSpatialStructure": "RelatedElements",
    "IfcRelDefinesByType": "RelatedObjects",
    "IfcRelAssociatesMaterial": "RelatedObjects",
    "IfcRelAssociatesClassification": "RelatedObjects",
}
OWNED_IFC_ROOT_KINDS = Counter({
    "IfcWall": 1, "IfcRelConnectsPathElements": 2,
    "IfcRelDefinesByProperties": 3, "IfcPropertySet": 3,
})
SOURCE_INVERSE_KINDS = Counter({
    "IfcRelConnectsPathElements": 2,
    "IfcRelDefinesByProperties": 3,
    "IfcRelDefinesByType": 1,
    "IfcRelAssociatesMaterial": 1,
    "IfcRelAssociatesClassification": 1,
    "IfcRelContainedInSpatialStructure": 1,
})
ORPHAN_TYPES = (
    "IfcShapeRepresentation", "IfcProductDefinitionShape", "IfcLocalPlacement",
    "IfcExtrudedAreaSolid", "IfcGeometricCurveSet",
)


@dataclass(frozen=True)
class ConnectedWallPlan:
    wall_guid: str
    neighbor_wall_guids: frozenset[str]
    deleted_root_guids: frozenset[str]
    modified_root_guids: frozenset[str]
    representation_ids: frozenset[int]
    product_shape_id: int
    placement_id: int
    shared_layer_id: int


def _model_orphans(m: ifcopenshell.file) -> dict[str,int]:
    return {
        typ: sum(m.get_total_inverses(x)==0 for x in m.by_type(typ))
        for typ in ORPHAN_TYPES
    }


def preflight_original_connected_wall(
    m: ifcopenshell.file, wall_guid: str,
) -> ConnectedWallPlan:
    if m.schema!="IFC4X3":
        raise UnsupportedIFCMutation("Original connected Wall authoring requires IFC4X3")
    wall=by_guid_or_none(m,wall_guid)
    if wall is None or not wall.is_a("IfcWall") or wall.HasOpenings:
        raise UnsupportedIFCMutation("Original target must be an unhosted existing Wall")
    incoming=list(m.get_inverse(wall))
    if Counter(x.is_a() for x in incoming)!=SOURCE_INVERSE_KINDS:
        raise UnsupportedIFCMutation("Unexpected original Wall inverse dependency inventory")
    if (wall.Representation is None or wall.ObjectPlacement is None
            or len(wall.Representation.Representations)!=2
            or set(x.RepresentationType for x in wall.Representation.Representations)
               != {"SweptSolid","Curve2D"}):
        raise UnsupportedIFCMutation("Original Wall physical shape / placement changed")
    if set(m.get_inverse(wall.Representation))!={wall}:
        raise UnsupportedIFCMutation("Target ProductDefinitionShape is shared")
    if set(m.get_inverse(wall.ObjectPlacement))!={wall}:
        raise UnsupportedIFCMutation("Target placement shared with another IFC object")
    reps=list(wall.Representation.Representations)
    rep_ids={x.id() for x in reps}
    for rep in reps:
        if len([x for x in m.get_inverse(rep)
                if x.is_a("IfcProductDefinitionShape")])!=1:
            raise UnsupportedIFCMutation("Original Wall shape representation is shared")
    layers=[x for x in m.by_type("IfcPresentationLayerAssignment")
            if any(rep in x.AssignedItems for rep in reps)]
    if (len(layers)!=1 or not rep_ids<=set(x.id() for x in layers[0].AssignedItems)
            or len(layers[0].AssignedItems)<=len(reps)):
        raise UnsupportedIFCMutation("Original Wall presentation layer/shared objects unsafe")
    owned={wall_guid}
    edited=set()
    neighbors=set()
    path_relations=0
    owned_psets=0
    for rel in incoming:
        if rel.is_a("IfcRelConnectsPathElements"):
            if (rel.RelatedElement!=wall or
                    not rel.RelatingElement.is_a("IfcWall") or
                    rel.RelatingElement.GlobalId==wall_guid):
                raise UnsupportedIFCMutation("Original connected Wall path direction wrong")
            neighbors.add(rel.RelatingElement.GlobalId)
            owned.add(rel.GlobalId)
            path_relations+=1
        elif rel.is_a("IfcRelDefinesByProperties"):
            pset=rel.RelatingPropertyDefinition
            if (tuple(rel.RelatedObjects)!=(wall,)
                    or not pset.is_a("IfcPropertySet")
                    or set(m.get_inverse(pset))!={rel}):
                raise UnsupportedIFCMutation("Original Wall propertyset is shared")
            owned.add(rel.GlobalId)
            owned.add(pset.GlobalId)
            owned_psets+=1
        else:
            field=SHARED_KINDS.get(rel.is_a())
            if not field:
                raise UnsupportedIFCMutation("Unknown original Wall native inverse")
            linked=getattr(rel,field)
            if (wall not in linked or len(linked)<2
                    or len({x.GlobalId for x in linked})!=len(linked)):
                raise UnsupportedIFCMutation("Original Wall shared relation membership ambiguous")
            if (rel.is_a("IfcRelContainedInSpatialStructure") and
                    not rel.RelatingStructure.is_a("IfcBuildingStorey")):
                raise UnsupportedIFCMutation("Original Wall containment is not a Storey")
            edited.add(rel.GlobalId)
    if (len(neighbors)!=2 or path_relations!=2 or owned_psets!=3
            or len(owned)!=9 or len(edited)!=4):
        raise UnsupportedIFCMutation("Original Wall native connected/metadata count mismatch")
    if any(v!=0 for v in _model_orphans(m).values()):
        raise UnsupportedIFCMutation("Original source contains unexpected native shape orphans")
    return ConnectedWallPlan(
        wall_guid=wall_guid,
        neighbor_wall_guids=frozenset(neighbors),
        deleted_root_guids=frozenset(owned),
        modified_root_guids=frozenset(edited),
        representation_ids=frozenset(rep_ids),
        product_shape_id=wall.Representation.id(),
        placement_id=wall.ObjectPlacement.id(),
        shared_layer_id=layers[0].id(),
    )


def verify_original_connected_wall(
    original: ifcopenshell.file, result: ifcopenshell.file,
    plan: ConnectedWallPlan,
) -> int:
    if original.schema!=result.schema or original.schema!="IFC4X3":
        raise UnsupportedIFCMutation("Original IFC4X3 source schema drift")
    if preflight_original_connected_wall(original,plan.wall_guid)!=plan:
        raise UnsupportedIFCMutation("Original Wall preflight plan drift")
    old={x.GlobalId:x for x in original.by_type("IfcRoot")}
    new={x.GlobalId:x for x in result.by_type("IfcRoot")}
    if (set(old)-set(new)!=set(plan.deleted_root_guids)
            or set(new)-set(old)):
        raise UnsupportedIFCMutation("Native IFC Root identities added or unapproved deleted")
    if Counter(old[g].is_a() for g in plan.deleted_root_guids)!=OWNED_IFC_ROOT_KINDS:
        raise UnsupportedIFCMutation("Original deleted IFC Root class inventory unexpected")
    before_products={x.GlobalId:x.is_a() for x in original.by_type("IfcProduct")}
    after_products={x.GlobalId:x.is_a() for x in result.by_type("IfcProduct")}
    if after_products!={g:c for g,c in before_products.items()
                       if g!=plan.wall_guid}:
        raise UnsupportedIFCMutation("Unrelated original native IfcProduct changed")
    changes=set()
    for gid in set(old)&set(new):
        first,second=old[gid],new[gid]
        if first.is_a()!=second.is_a():
            raise UnsupportedIFCMutation("Surviving native IFC Root class drift")
        if gid in plan.modified_root_guids:
            field=SHARED_KINDS.get(first.is_a())
            if not field:
                raise UnsupportedIFCMutation("Unapproved mutable IFC Root class")
            before=getattr(first,field)
            after=getattr(second,field)
            if (len(before)-len(after)!=1 or
                    {x.GlobalId for x in before}-{x.GlobalId for x in after}
                    !={plan.wall_guid} or
                    {x.GlobalId for x in after}-{x.GlobalId for x in before}):
                raise UnsupportedIFCMutation("Shared original relationship member changed unexpectedly")
            for idx in range(len(first)):
                if first.attribute_name(idx)!=field and str(first[idx])!=str(second[idx]):
                    raise UnsupportedIFCMutation("Shared original IFC metadata mutated")
            if str(first)==str(second):
                raise UnsupportedIFCMutation("Expected shared relation membership not updated")
            changes.add(gid)
        elif str(first)!=str(second):
            raise UnsupportedIFCMutation("Original surviving IFC Root unexpectedly modified")
    if changes!=set(plan.modified_root_guids):
        raise UnsupportedIFCMutation("Native membership updates incomplete")
    original_step={x.id():str(x) for x in original}
    candidate_step={x.id():str(x) for x in result}
    if set(candidate_step)-set(original_step):
        raise UnsupportedIFCMutation("Unexpected new IFC STEP entities")
    removed=set(original_step)-set(candidate_step)
    required={old[k].id() for k in plan.deleted_root_guids}
    required|={plan.product_shape_id,plan.placement_id}
    required|=set(plan.representation_ids)
    if not required<=removed:
        raise UnsupportedIFCMutation("Deleted Wall shape/placement/relations still present")
    # Native SDK can delete owned descendants but not shared references.
    reachable=set()
    for root in [original.by_guid(plan.wall_guid)] + [
        original.by_guid(g) for g in plan.deleted_root_guids if g!=plan.wall_guid
    ]:
        reachable.update(x.id() for x in original.traverse(root))
    if not removed<=reachable:
        raise UnsupportedIFCMutation("Unrelated original nonroot STEP item deleted")
    changed={i for i in set(original_step)&set(candidate_step)
             if original_step[i]!=candidate_step[i]}
    four={old[guid].id() for guid in plan.modified_root_guids}
    expected=four|{plan.shared_layer_id}
    if changed!=expected:
        raise UnsupportedIFCMutation("Other existing original native STEP entity mutated")
    old_layer=original.by_id(plan.shared_layer_id)
    new_layer=result.by_id(plan.shared_layer_id)
    if (not old_layer.is_a("IfcPresentationLayerAssignment")
            or not new_layer.is_a("IfcPresentationLayerAssignment")
            or old_layer.Name!=new_layer.Name
            or old_layer.Description!=new_layer.Description
            or old_layer.Identifier!=new_layer.Identifier):
        raise UnsupportedIFCMutation("Original presentation layer metadata changed")
    prev={x.id() for x in old_layer.AssignedItems}
    cur={x.id() for x in new_layer.AssignedItems}
    if (prev-cur!=set(plan.representation_ids) or cur-prev or not cur):
        raise UnsupportedIFCMutation("Surviving layer members modified")
    if _model_orphans(result)!=_model_orphans(original):
        raise UnsupportedIFCMutation("Original native IFC contains new orphan shape/placement")
    for neighbor in plan.neighbor_wall_guids:
        w=result.by_guid(neighbor)
        if not w.is_a("IfcWall"):
            raise UnsupportedIFCMutation("Neighbor Wall changed class")
        if any(x.RelatedElement.GlobalId==plan.wall_guid
               or x.RelatingElement.GlobalId==plan.wall_guid
               for x in result.get_inverse(w)
               if x.is_a("IfcRelConnectsPathElements")):
            raise UnsupportedIFCMutation("Dangling original Wall connection remains")
    return len(set(old)&set(new))-len(plan.modified_root_guids)


def supervised_native_child(
    source:Path,staged:Path,guid:str,source_sha:str,
    *, timeout_seconds:int=CHILD_TIMEOUT_SECONDS,
    child_module:str=CHILD_MODULE,
) -> dict:
    """Launch exactly one source-bounded child. A crash cannot kill parent.

    This wrapper only creates temporary candidate files; staged output itself
    belongs to the caller's exclusive transaction. Success here is *not*
    enough for publication: independent full IFC validator follows.
    """
    if (source_sha!=PINNED_NORMALIZED_ORIGINAL_IFC_SHA
            or snapshot_source(source).source_sha256!=source_sha):
        raise UnsupportedIFCMutation("Nonoriginal pinned IFC source to native child")
    child=staged.with_name(staged.stem+".child.ifc")
    if child.exists() or child.is_symlink():
        raise UnsupportedIFCMutation("Unsafe child IFC candidate already exists")
    args=[
        sys.executable, "-m", child_module,
        "--source",str(source),
        "--source-sha",source_sha,
        "--public-guid",guid,
        "--destination",str(child),
    ]
    env=os.environ.copy()
    env.update(PYTHONUTF8="1",PYTHONIOENCODING="utf8",PYTHONNOUSERSITE="1")
    try:
        try:
            result=subprocess.run(
                args,cwd=str(Path(__file__).resolve().parents[2]),
                env=env,capture_output=True,timeout=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            raise UnsupportedIFCMutation("Native child exceeded bounded deadline") from exc
        if result.returncode!=0:
            raise UnsupportedIFCMutation(
                "Native child crash/error rejected (return code "
                +str(result.returncode)+")")
        output=result.stdout.decode("utf8","replace")
        messages=[line[len(CHILD_RESULT_PREFIX):]
                  for line in output.splitlines()
                  if line.startswith(CHILD_RESULT_PREFIX)]
        if len(messages)!=1:
            raise UnsupportedIFCMutation("Native child output receipt absent/ambiguous")
        try:
            receipt=json.loads(messages[0])
        except (ValueError,TypeError) as exc:
            raise UnsupportedIFCMutation("Invalid native child receipt") from exc
        if (not child.is_file() or child.is_symlink()
                or receipt.get("source_sha256")!=source_sha
                or receipt.get("mode")!="fixed_source_bound_deep_cleanup"
                or not receipt.get("original_Wall_absent")
                or receipt.get("product_count")!=42
                or any(receipt.get(key)!=0 for key in (
                    "orphan_rep_count","orphan_pds_count","orphan_place_count"
                )) or
                sha256(child.read_bytes()).hexdigest()!=receipt.get("result_sha256")):
            raise UnsupportedIFCMutation("Native child receipt/file/orphan sanity gate failed")
        if snapshot_source(source).source_sha256!=source_sha:
            raise UnsupportedIFCMutation("Original IFC changed during native worker")
        # Parent owns the mkstemp staged file and is allowed to replace only it.
        os.replace(child,staged)
        return receipt
    finally:
        if child.exists():
            child.unlink()


def compile_original_connected_wall(
    source:Path,destination:Path,before_doc,after_doc,before,after,
):
    """Compile only one source Wall + exactly its two existing Connects."""
    from src.runtime.compiler import CompileReport

    delta=graph_diff(before.graph,after.graph)
    old=before.graph.by_id()
    if (len(delta.removed_nodes)!=1 or
            delta.added_nodes or delta.changed_nodes or delta.added_edges):
        raise UnsupportedIFCMutation("Original connected Wall needs isolated XML state deletion")
    wall_id=delta.removed_nodes[0]
    wall=old[wall_id]
    if wall.kind!="Wall" or wall.provenance!="existing_source":
        raise UnsupportedIFCMutation("Native original connected Wall source required")
    removed={
        edge for edge in before.graph.edges
        if edge.source==wall_id or edge.target==wall_id
    }
    if (set(delta.removed_edges)!=removed
            or Counter(x.relation for x in removed)!=Counter(
                {"connects":2,"in_storey":1})
            or any(x.target!=wall_id for x in removed)):
        raise UnsupportedIFCMutation("Original Wall lost unrelated XML native relationship")
    sha=snapshot_source(source).source_sha256
    if sha!=PINNED_NORMALIZED_ORIGINAL_IFC_SHA or sha!=before_doc.source_model_sha256:
        raise UnsupportedIFCMutation("Original source must match independent normalized SHA")
    native=ifcopenshell.open(str(source))
    plan=preflight_original_connected_wall(native,wall.ifc_guid)
    old_connects={e.source for e in removed if e.relation=="connects"}
    native_neighbors={old[x].ifc_guid for x in old_connects}
    if native_neighbors!=set(plan.neighbor_wall_guids):
        raise UnsupportedIFCMutation("Declared original neighbor links mismatch native source")
    mutation=Mutation(
        "DELETE_ORIGINAL_PUBLIC_CONNECTED_WALL",wall_id,wall.ifc_guid,
        before_doc.managed_by_id()[wall_id].span.line,
        ("Wall","two_original_connections","owned_native_geometry"),
        "bounded original-source full XML connected Wall state deletion"
    )
    def writer(stage:Path):
        if snapshot_source(source).source_sha256!=sha:
            raise UnsupportedIFCMutation("Original normalized IFC changed before worker")
        supervised_native_child(source,stage,plan.wall_guid,sha)
    def validator(stage:Path):
        if snapshot_source(source).source_sha256!=sha:
            raise UnsupportedIFCMutation("Original IFC mutated during child transaction")
        verify_original_connected_wall(
            ifcopenshell.open(str(source)),ifcopenshell.open(str(stage)),plan)
        from src.runtime.ifc_projection import project_ifc
        from src.runtime.xml_parser import parse_xml
        from src.runtime.binder import bind_document
        from src.runtime.space_partition_compiler import _canonical_native_graph
        projected=project_ifc(stage)
        parsed=parse_xml(projected.xml,
                         expected_source_sha256=projected.source.source_sha256)
        bound=bind_document(parsed,projection=projected)
        if _canonical_native_graph(bound.graph)!=_canonical_native_graph(after.graph):
            raise UnsupportedIFCMutation("Native IFC full XML state differs from declaration")
    stage_and_commit(destination,writer,validator)
    if snapshot_source(source).source_sha256!=sha:
        raise UnsupportedIFCMutation("Original native IFC changed during transaction")
    output=snapshot_source(destination)
    untouched=verify_original_connected_wall(
        ifcopenshell.open(str(source)),ifcopenshell.open(str(destination)),plan)
    return CompileReport(
        sha,output.source_sha256,delta.before_fingerprint,delta.after_fingerprint,
        (mutation,),untouched,(),destination,True,
    )
