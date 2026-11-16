"""v0.27 source-pinned original IFC connected Wall native compiler.

Only a trusted compiler (outside the LLM authoring loop) may invoke this
module. Declarative authoring deletes one existing <Wall> and its two
existing <Connects> state lines; it NEVER supplies an imperative command,
a helper, Python source, or an IFC edit API.

The unstable native IfcOpenShell mutation is isolated in a supervised
subprocess. The source IFC is read-only. Native stage publication happens
ONLY after an independently re-opened, full-STEP/root/geometry and full
typed XML state verifier passes. Access violations/timeouts fail closed.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys

import ifcopenshell
import ifcopenshell.util.unit

from src.runtime.ifc_mutations import Mutation, UnsupportedIFCMutation, by_guid_or_none
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.semantic_graph import graph_diff
from src.runtime.transaction import stage_and_commit

PINNED_NORMALIZED_SOURCE_SHA="16568e7c4b8b9d62567a7a199101269daa6e5b1b7535cec095b8e233ae2ef6ac"
WORKER_TIMEOUT_SECONDS=25
OWNER_ORPHAN_TYPES=(
    "IfcShapeRepresentation","IfcProductDefinitionShape","IfcLocalPlacement",
)


@dataclass(frozen=True)
class ConnectedWallPlan:
    wall_guid:str
    source_sha256:str
    removed_native_root_guids:frozenset[str]
    changed_native_root_guids:frozenset[str]
    presentation_layer_id:int
    original_shape_rep_ids:frozenset[int]
    original_product_shape_id:int
    original_wall_placement_id:int
    source_native_root_count:int


def _orphan_counts(f:ifcopenshell.file)->dict[str,int]:
    return {kind:sum(f.get_total_inverses(obj)==0 for obj in f.by_type(kind))
            for kind in OWNER_ORPHAN_TYPES}


def _step(f:ifcopenshell.file)->dict[int,str]:
    return {x.id():str(x) for x in f}


def _entity_exists(f:ifcopenshell.file,eid:int)->bool:
    try:
        f.by_id(eid)
        return True
    except RuntimeError:
        return False


def preflight_original_connected_wall(source:Path,wall_guid:str)->ConnectedWallPlan:
    sha=snapshot_source(source).source_sha256
    if sha!=PINNED_NORMALIZED_SOURCE_SHA:
        raise UnsupportedIFCMutation("Unsupported original connected Wall IFC source checksum")
    f=ifcopenshell.open(str(source))
    if (f.schema!="IFC4X3" or
        abs(ifcopenshell.util.unit.calculate_unit_scale(f)-1.)>1e-10):
        raise UnsupportedIFCMutation("Original connected Wall source is not IFC4X3 metres")
    wall=by_guid_or_none(f,wall_guid)
    if wall is None or not wall.is_a("IfcWall") or wall.HasOpenings:
        raise UnsupportedIFCMutation("Not an existing source Wall without hosted openings")
    rels=list(f.get_inverse(wall))
    expected=Counter({
        "IfcRelConnectsPathElements":2,
        "IfcRelDefinesByProperties":3,
        "IfcRelDefinesByType":1,
        "IfcRelAssociatesMaterial":1,
        "IfcRelAssociatesClassification":1,
        "IfcRelContainedInSpatialStructure":1,
    })
    if Counter(r.is_a() for r in rels)!=expected:
        raise UnsupportedIFCMutation("Original Wall native inverse inventory not exclusive")
    links=[r for r in rels if r.is_a("IfcRelConnectsPathElements")]
    psets=[r for r in rels if r.is_a("IfcRelDefinesByProperties")]
    assoc=[r for r in rels if r not in links and r not in psets]
    if (len(links)!=2 or len({r.GlobalId for r in links})!=2
        or len({r.RelatingElement.GlobalId for r in links})!=2
        or any(r.RelatedElement!=wall or not r.RelatingElement.is_a("IfcWall")
               or r.RelatingElement==wall for r in links)):
        raise UnsupportedIFCMutation("Original Wall has unsafe path connection roles")
    owned={wall_guid}|{r.GlobalId for r in links}
    for rel in psets:
        ps=rel.RelatingPropertyDefinition
        if (tuple(rel.RelatedObjects)!=(wall,) or
            not ps.is_a("IfcPropertySet") or
            tuple(f.get_inverse(ps))!=(rel,)):
            raise UnsupportedIFCMutation("Original Wall property is not exclusively owned")
        owned|={rel.GlobalId,ps.GlobalId}
    changed=set()
    for rel in assoc:
        if rel.is_a("IfcRelContainedInSpatialStructure"):
            if (wall not in rel.RelatedElements or
                len(rel.RelatedElements)<2 or
                not rel.RelatingStructure.is_a("IfcBuildingStorey")):
                raise UnsupportedIFCMutation("Source Wall has unsafe storey ownership")
        else:
            if (not hasattr(rel,"RelatedObjects") or
                wall not in rel.RelatedObjects or
                len(rel.RelatedObjects)<2):
                raise UnsupportedIFCMutation("Source Wall shared type/material/classification unsafe")
        changed.add(rel.GlobalId)
    if len(owned)!=9 or len(changed)!=4:
        raise UnsupportedIFCMutation("Original Wall root set not source-complete")
    shape=wall.Representation
    placement=wall.ObjectPlacement
    if shape is None or placement is None:
        raise UnsupportedIFCMutation("Original Wall physical shape/placement absent")
    representations=tuple(shape.Representations)
    if len(representations)!=2 or len({rep.id() for rep in representations})!=2:
        raise UnsupportedIFCMutation("Original Wall must have two verified source representations")
    rep_ids={rep.id() for rep in representations}
    layers=[layer for layer in f.by_type("IfcPresentationLayerAssignment")
            if any(rep in layer.AssignedItems for rep in representations)]
    if (len(layers)!=1 or
        not rep_ids.issubset({x.id() for x in layers[0].AssignedItems}) or
        len(layers[0].AssignedItems)<=len(rep_ids)):
        raise UnsupportedIFCMutation("Original wall shared presentation layer unsafe")
    for product in f.by_type("IfcProduct"):
        if product==wall or product.Representation is None:
            continue
        if any(rep.id() in rep_ids for rep in product.Representation.Representations):
            raise UnsupportedIFCMutation("Source Wall shape representation shared by another Product")
    if (any(ref!=wall and ref.is_a("IfcObjectPlacement") for ref in f.get_inverse(placement))
        or any(ref!=wall and ref.is_a("IfcProduct") for ref in f.get_inverse(shape))):
        raise UnsupportedIFCMutation("Wall geometry/placement has unapproved dependent Product")
    return ConnectedWallPlan(
        wall_guid,sha,frozenset(owned),frozenset(changed),
        layers[0].id(),frozenset(rep_ids),shape.id(),placement.id(),
        len(f.by_type("IfcRoot")),
    )


def verify_original_connected_wall(
    source:Path,result:Path,plan:ConnectedWallPlan,
)->int:
    """Independent original native IFC Root+STEP, owned-shape, orphan verifier.

    This never trusts the child worker's claimed success or printed metrics.
    Exact root, survivor attributes and every surviving STEP entity must
    match, with only four specified shared relation memberships and one
    exact shared presentation-layer member change permitted.
    """
    if preflight_original_connected_wall(source,plan.wall_guid)!=plan:
        raise UnsupportedIFCMutation("Original connected Wall source/provenance changed")
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(result))
    if (a.schema!=b.schema or b.schema!="IFC4X3" or
        abs(ifcopenshell.util.unit.calculate_unit_scale(b)-1.)>1e-10):
        raise UnsupportedIFCMutation("Candidate native IFC schema or metres changed")
    old_roots={x.GlobalId:x for x in a.by_type("IfcRoot")}
    new_roots={x.GlobalId:x for x in b.by_type("IfcRoot")}
    if (set(old_roots)-set(new_roots)!=set(plan.removed_native_root_guids)
        or set(new_roots)-set(old_roots)):
        raise UnsupportedIFCMutation("Connected Wall produced unexpected added/deleted Roots")
    classes=Counter(old_roots[x].is_a() for x in plan.removed_native_root_guids)
    if classes!=Counter({
        "IfcWall":1,"IfcRelConnectsPathElements":2,
        "IfcRelDefinesByProperties":3,"IfcPropertySet":3,
    }):
        raise UnsupportedIFCMutation("Original removed Wall owned Roots are not exact")
    orig_products={x.GlobalId:x.is_a() for x in a.by_type("IfcProduct")}
    new_products={x.GlobalId:x.is_a() for x in b.by_type("IfcProduct")}
    if new_products!={k:v for k,v in orig_products.items() if k!=plan.wall_guid}:
        raise UnsupportedIFCMutation("Unrelated surviving original native Product identity/class lost")
    if len(new_roots)+len(plan.removed_native_root_guids)!=plan.source_native_root_count:
        raise UnsupportedIFCMutation("Unexpected total native Root inventory")
    expected_updated_ids=set()
    for guid in old_roots.keys()&new_roots.keys():
        old=old_roots[guid]
        cur=new_roots[guid]
        if old.is_a()!=cur.is_a():
            raise UnsupportedIFCMutation("Surviving native Root class changed")
        if guid in plan.changed_native_root_guids:
            field="RelatedElements" if old.is_a()=="IfcRelContainedInSpatialStructure" else "RelatedObjects"
            if not hasattr(old,field):
                raise UnsupportedIFCMutation("Unapproved shared Root relationship changed")
            old_guids=[x.GlobalId for x in getattr(old,field)]
            new_guids=[x.GlobalId for x in getattr(cur,field)]
            if (old_guids.count(plan.wall_guid)!=1 or
                plan.wall_guid in new_guids or
                sorted(x for x in old_guids if x!=plan.wall_guid)!=sorted(new_guids)):
                raise UnsupportedIFCMutation("Shared IFC native relation changed unrelated product membership")
            for idx in range(len(old)):
                if old.attribute_name(idx)!=field and str(old[idx])!=str(cur[idx]):
                    raise UnsupportedIFCMutation("Shared relationship native metadata modified")
            expected_updated_ids.add(old.id())
        elif str(old)!=str(cur):
            raise UnsupportedIFCMutation("Unrelated surviving original IFC Root modified")
    if len(expected_updated_ids)!=4:
        raise UnsupportedIFCMutation("Native source four shared root updates not present")
    # Every surviving STEP entity, not just products, must remain unchanged
    # except the four approved relation tuples and single layer membership.
    old_step=_step(a)
    new_step=_step(b)
    if set(new_step)-set(old_step):
        raise UnsupportedIFCMutation("Connected Wall native operation added unexpected STEP entities")
    modifications={eid for eid in old_step.keys()&new_step.keys()
                   if old_step[eid]!=new_step[eid]}
    if modifications!=expected_updated_ids|{plan.presentation_layer_id}:
        raise UnsupportedIFCMutation("Unexpected native STEP survivor mutation")
    layer_a=a.by_id(plan.presentation_layer_id)
    layer_b=b.by_id(plan.presentation_layer_id)
    if (not layer_a.is_a("IfcPresentationLayerAssignment")
        or not layer_b.is_a("IfcPresentationLayerAssignment")):
        raise UnsupportedIFCMutation("Original shared native presentation layer disappeared")
    for name in ("Name","Description","Identifier"):
        if getattr(layer_a,name)!=getattr(layer_b,name):
            raise UnsupportedIFCMutation("Original shared presentation-layer metadata changed")
    source_members={x.id() for x in layer_a.AssignedItems}
    result_members={x.id() for x in layer_b.AssignedItems}
    if (source_members-result_members!=set(plan.original_shape_rep_ids)
        or result_members-source_members or not result_members):
        raise UnsupportedIFCMutation("Shared layer member removal not limited to target Wall")
    if (_entity_exists(b,plan.original_product_shape_id)
        or _entity_exists(b,plan.original_wall_placement_id)
        or any(_entity_exists(b,eid) for eid in plan.original_shape_rep_ids)):
        raise UnsupportedIFCMutation("Deleted original Wall representation/placement is orphaned")
    # Every newly removed nonroot object must be a forward descendant of
    # the original Wall shape or placement or of one of its three owned Psets.
    original_wall=a.by_guid(plan.wall_guid)
    permitted={x.id() for x in a.traverse(original_wall)}
    for rel in a.get_inverse(original_wall):
        if rel.is_a("IfcRelDefinesByProperties"):
            permitted|={x.id() for x in a.traverse(rel.RelatingPropertyDefinition)}
    removed=set(old_step)-set(new_step)
    deleted_root_ids={old_roots[g].id() for g in plan.removed_native_root_guids}
    if (not deleted_root_ids.issubset(removed)
        or not (removed-deleted_root_ids).issubset(permitted)):
        raise UnsupportedIFCMutation("Original unrelated STEP geometry/metadata deleted")
    for kind in OWNER_ORPHAN_TYPES:
        if _orphan_counts(b)[kind]>_orphan_counts(a)[kind]:
            raise UnsupportedIFCMutation("New source IFC orphan geometry or placement retained")
    # Root/STEP strict mutation preservation implies neighboring Wall geometry,
    # materials, type, classification, path and storey unaffected.
    return len(old_roots.keys()&new_roots.keys())-len(plan.changed_native_root_guids)


def supervised_worker(
    source:Path,public_guid:str,stage:Path,*,timeout_seconds:int=WORKER_TIMEOUT_SECONDS,
)->dict:
    """Return only on clean child exit + regular nonempty native output.

    Run without shell, with an allowlisted environment and per-task timeout.
    On Windows a native C++ access violation may kill a child with status
    0xC0000005; that must not kill or corrupt the caller/normal compiler.
    """
    if (not 1<=timeout_seconds<=60 or
        not stage.is_file() or stage.is_symlink() or stage.stat().st_size!=0):
        raise UnsupportedIFCMutation("Native child output not a reserved empty staged file")
    repo=Path(__file__).resolve().parents[2]
    args=[
        sys.executable,"-m","tools.bibimbap_v027_wall_worker",
        "--source",str(source),"--output",str(stage),"--reserved-empty-stage",
    ]
    allow_env=("SYSTEMROOT","SystemRoot","WINDIR","PATH","TEMP","TMP","VIRTUAL_ENV")
    env={name:os.environ[name] for name in allow_env if name in os.environ}
    env.update(PYTHONUTF8="1",PYTHONIOENCODING="utf-8")
    try:
        process=subprocess.run(args,input=public_guid+"\n",capture_output=True,
            text=True,cwd=str(repo),env=env,timeout=timeout_seconds,
            encoding="utf8",errors="replace",shell=False)
    except subprocess.TimeoutExpired as exc:
        raise UnsupportedIFCMutation("Isolated native connected Wall worker exceeded time limit") from exc
    if process.returncode!=0:
        code=hex(process.returncode%(1<<32))
        raise UnsupportedIFCMutation(
            "Isolated native connected Wall worker failed without publishing IFC, exit "+code)
    if stage.is_symlink() or not stage.is_file() or stage.stat().st_size<1024:
        raise UnsupportedIFCMutation("Isolated native Wall worker returned no valid output file")
    try:
        receipt=json.loads(process.stdout.strip())
    except (ValueError,TypeError) as exc:
        raise UnsupportedIFCMutation("Isolated native worker receipt invalid") from exc
    if (receipt.get("status")!="EXPERIMENTAL_CHILD_WORKER_NOT_COMMITTED"
        or not receipt.get("source_sha256_unchanged")
        or receipt.get("candidate_sha256")!=snapshot_source(stage).source_sha256):
        raise UnsupportedIFCMutation("Isolated native Wall worker receipt/source hash mismatch")
    return receipt


def compile_existing_original_connected_wall(
    source:Path,destination:Path,before_doc,after_doc,before,after,
):
    from src.runtime.compiler import CompileReport
    delta=graph_diff(before.graph,after.graph)
    prior=before.graph.by_id()
    if (len(delta.removed_nodes)!=1
        or len(delta.removed_edges)!=3
        or delta.added_nodes or delta.changed_nodes or delta.added_edges):
        raise UnsupportedIFCMutation("Source Wall+two connections requires isolated exact graph diff")
    target=prior[delta.removed_nodes[0]]
    if target.kind!="Wall" or target.provenance!="existing_source":
        raise UnsupportedIFCMutation("Only one original existing connected Wall removal admitted")
    edges=tuple(delta.removed_edges)
    if Counter(edge.relation for edge in edges)!=Counter({"connects":2,"in_storey":1}):
        raise UnsupportedIFCMutation("Original Wall removal lost non-target typed relations")
    if any(edge.source!=target.id and edge.target!=target.id for edge in edges):
        raise UnsupportedIFCMutation("Connected-Wall XML edited unrelated source relationship")
    source_sha=snapshot_source(source).source_sha256
    if source_sha!=before_doc.source_model_sha256:
        raise UnsupportedIFCMutation("Edited original XML source sha mismatch")
    plan=preflight_original_connected_wall(source,target.ifc_guid)
    if plan.source_sha256!=source_sha:
        raise UnsupportedIFCMutation("Original native source identity inconsistent")

    mutation=Mutation(
        "DELETE_ORIGINAL_CONNECTED_WALL",target.id,target.ifc_guid,
        before_doc.managed_by_id()[target.id].span.line,
        ("Wall","IfcRelConnectsPathElements","original_SOURCE_IFC4X3"),
        "bounded declared Wall and two source connections; isolated native writer",
    )

    def writer(stage:Path)->None:
        if snapshot_source(source).source_sha256!=source_sha:
            raise UnsupportedIFCMutation("Original IFC input changed before worker started")
        supervised_worker(source,target.ifc_guid,stage)

    def validator(stage:Path)->None:
        if snapshot_source(source).source_sha256!=source_sha:
            raise UnsupportedIFCMutation("Original source changed during isolated worker")
        verify_original_connected_wall(source,stage,plan)
        from src.runtime.ifc_projection import project_ifc
        from src.runtime.xml_parser import parse_xml
        from src.runtime.binder import bind_document
        from src.runtime.space_partition_compiler import _canonical_native_graph
        output_projection=project_ifc(stage)
        output_doc=parse_xml(
            output_projection.xml,
            expected_source_sha256=output_projection.source.source_sha256)
        output_graph=bind_document(output_doc,projection=output_projection)
        if _canonical_native_graph(output_graph.graph)!=_canonical_native_graph(after.graph):
            raise UnsupportedIFCMutation(
                "Complete source authored XML differs from compiled native IFC")
    stage_and_commit(destination,writer,validator)
    if snapshot_source(source).source_sha256!=source_sha:
        raise UnsupportedIFCMutation("Original IFC file changed after publish")
    final=snapshot_source(destination)
    verified=verify_original_connected_wall(source,destination,plan)
    return CompileReport(
        source_sha,final.source_sha256,
        delta.before_fingerprint,delta.after_fingerprint,
        (mutation,),verified,(),destination,True,
    )
