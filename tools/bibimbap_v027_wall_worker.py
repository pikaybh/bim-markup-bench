"""v0.27 isolated trusted worker for source-pinned connected Wall cleanup.

This is NOT an LLM-facing tool or authoring language. It is the native C++
implementation detail of an opt-in, source-pinned declarative XML compiler
feature. Its raw output is NEVER sufficient evidence for publishing native
IFC: the parent coordinator must independently verify every original Root
and STEP survivor, target shape cleanup and full source XML graph before
atomic staged publication. Windows access violations kill only this worker;
the supervising process fails closed and preserves the original source.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import sys
from pathlib import Path

import ifcopenshell
import ifcopenshell.api.pset


PINNED_NORMALIZED_ORIGINAL_SHA = "16568e7c4b8b9d62567a7a199101269daa6e5b1b7535cec095b8e233ae2ef6ac"


def read_sha(path: Path)->str:
    return sha256(path.read_bytes()).hexdigest()


def _by_id(f:ifcopenshell.file,eid:int):
    try:
        return f.by_id(eid)
    except RuntimeError:
        return None


def collect_subgraph(f:ifcopenshell.file,root) -> set[int]:
    return {x.id() for x in f.traverse(root)}


def clean_unreferenced_subgraph(f:ifcopenshell.file, candidates:set[int],protected:set[int]):
    """Single-step conservative refcount sweep; no remove_deep2."""
    pending=set(candidates)-set(protected)
    removed=Counter()
    for _ in range(len(pending)+2):
        changed=False
        for eid in sorted(tuple(pending),reverse=True):
            node=_by_id(f,eid)
            if node is None:
                pending.discard(eid);continue
            if f.get_total_inverses(node)!=0:
                continue
            kind=node.is_a()
            f.remove(node)
            removed[kind]+=1
            pending.remove(eid)
            changed=True
        if not changed:break
    return dict(removed),pending


def build(source:Path,public_guid:str,destination:Path,*,reserved_empty_stage:bool=False)->dict:
    if destination.is_symlink():
        raise RuntimeError("Refuse symlink output")
    if destination.exists() and not (
        reserved_empty_stage and destination.is_file() and destination.stat().st_size==0
    ):
        raise RuntimeError("Never overwrite an existing native output")
    if read_sha(source)!=PINNED_NORMALIZED_ORIGINAL_SHA:
        raise RuntimeError("Unrecognized normalized original public IFC source SHA")
    f=ifcopenshell.open(str(source))
    if f.schema!="IFC4X3":
        raise RuntimeError("Source schema not IFC4X3")
    wall=f.by_guid(public_guid)
    if not wall.is_a("IfcWall") or wall.HasOpenings:
        raise RuntimeError("Source PUBLIC target not safely bounded Wall")
    relationships=list(f.get_inverse(wall))
    links=[r for r in relationships if r.is_a("IfcRelConnectsPathElements")]
    pset_links=[r for r in relationships if r.is_a("IfcRelDefinesByProperties")]
    if len(links)!=2 or len(pset_links)!=3 or len(relationships)!=9:
        raise RuntimeError("Native original inverse relationships not frozen")
    if len({l.GlobalId for l in links})!=2 or not all(
        l.RelatedElement==wall and l.RelatingElement.is_a("IfcWall") for l in links):
        raise RuntimeError("Original wall has unexpected path connectivity")
    for rel in pset_links:
        ps=rel.RelatingPropertyDefinition
        if tuple(rel.RelatedObjects)!=(wall,) or not ps.is_a("IfcPropertySet") or tuple(f.get_inverse(ps))!=(rel,):
            raise RuntimeError("Wall property definition is not solely owned")
    shape=wall.Representation
    placement=wall.ObjectPlacement
    if shape is None or placement is None:
        raise RuntimeError("Original native wall geometry or placement absent")
    reps=tuple(shape.Representations)
    if len(reps)!=2:
        raise RuntimeError("Original wall not exactly two representations")
    original_reps={x.id() for x in reps}
    original_shape_id=shape.id()
    original_placement_id=placement.id()
    graph_candidates=collect_subgraph(f,shape)|collect_subgraph(f,placement)
    # Protect all native roots, the original building-storey parent/other
    # placement/contexts which have external owner references.
    protected={x.id() for x in f.by_type("IfcRoot")}
    for rel in f.get_inverse(placement):
        if rel!=wall and rel.is_a("IfcObjectPlacement"):
            raise RuntimeError("Another object depends on target placement")
    layers=[layer for layer in f.by_type("IfcPresentationLayerAssignment")
            if any(rep in layer.AssignedItems for rep in reps)]
    if len(layers)!=1 or len(layers[0].AssignedItems)<=2:
        raise RuntimeError("Original representation layer not safely shared")
    layer=layers[0]
    if sum(rep in layer.AssignedItems for rep in reps)!=2:
        raise RuntimeError("Layer missing source wall representation")
    other_layer_items=[x for x in layer.AssignedItems if x.id() not in original_reps]
    if not other_layer_items:
        raise RuntimeError("Original layer would be emptied")

    before_roots={x.GlobalId:(x.is_a(),str(x)) for x in f.by_type("IfcRoot")}
    before_products={x.GlobalId:x.is_a() for x in f.by_type("IfcProduct")}
    before_step={x.id():str(x) for x in f}
    for rel in links:
        f.remove(rel)
    for rel in pset_links:
        ifcopenshell.api.pset.remove_pset(f,product=wall,pset=rel.RelatingPropertyDefinition)
    layer.AssignedItems=tuple(other_layer_items)
    f.remove(wall)
    # No deep2 call! The original wall now has no inverse owners for its
    # definition shape and its own placement. Shared parents/contexts are
    # preserved because the sweep requires zero inverse count.
    cleanup,stuck=clean_unreferenced_subgraph(f,graph_candidates,protected)
    destination.parent.mkdir(parents=True,exist_ok=True)
    f.write(str(destination))
    reread=ifcopenshell.open(str(destination))
    final_roots={x.GlobalId:(x.is_a(),str(x)) for x in reread.by_type("IfcRoot")}
    final_products={x.GlobalId:x.is_a() for x in reread.by_type("IfcProduct")}
    after_step={x.id():str(x) for x in reread}
    remaining_original_shape_ids=[i for i in original_reps if _by_id(reread,i) is not None]
    remaining_source_placement=_by_id(reread,original_placement_id) is not None
    remaining_source_product_shape=_by_id(reread,original_shape_id) is not None
    survivor_changes=[guid for guid in before_roots.keys()&final_roots.keys()
                      if before_roots[guid]!=final_roots[guid]]
    deleted_roots=Counter(before_roots[g][0] for g in before_roots.keys()-final_roots.keys())
    if final_products!={k:v for k,v in before_products.items() if k!=public_guid}:
        raise RuntimeError("Unrelated original products were changed")
    return {
      "status":"EXPERIMENTAL_CHILD_WORKER_NOT_COMMITTED",
      "candidate_sha256":read_sha(destination),
      "source_sha256_unchanged":read_sha(source)==PINNED_NORMALIZED_ORIGINAL_SHA,
      "original_product_count":len(before_products),
      "result_product_count":len(final_products),
      "other_original_product_classes_and_GUIDs_unchanged":True,
      "remaining_source_shape_representations":len(remaining_original_shape_ids),
      "remaining_source_product_definition_shape":remaining_source_product_shape,
      "remaining_source_local_placement":remaining_source_placement,
      "deleted_root_classes":dict(deleted_roots),
      "modified_surviving_root_classes":dict(Counter(final_roots[g][0] for g in survivor_changes)),
      "new_root_count":len(final_roots.keys()-before_roots.keys()),
      "new_step_count":len(after_step.keys()-before_step.keys()),
      "changed_step_count":sum(before_step[eid]!=after_step[eid] for eid in before_step.keys()&after_step.keys()),
      "remaining_geometry_candidates_with_native_inverse":len(stuck),
      "remaining_candidate_classes":dict(Counter(_by_id(reread,eid).is_a() for eid in stuck if _by_id(reread,eid) is not None)),
      "remaining_candidate_referencer_classes":dict(Counter(
          inv.is_a()
          for eid in stuck
          if _by_id(reread,eid) is not None
          for inv in reread.get_inverse(_by_id(reread,eid))
      )),
      "nonroot_cleanup_classes":cleanup,
    }


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--public-guid",default=None)
    p.add_argument("--reserved-empty-stage",action="store_true")
    p.add_argument("--output",required=True,type=Path)
    opt=p.parse_args()
    # The trusted native compiler passes the source Public GUID via stdin,
    # not an OS-visible process command-line argument.
    guid=opt.public_guid if opt.public_guid is not None else sys.stdin.readline().strip()
    if not guid or len(guid)!=22:
        p.error("Missing/invalid source-bound GUID")
    result=build(opt.source,guid,opt.output,
                 reserved_empty_stage=opt.reserved_empty_stage)
    print(json.dumps(result,sort_keys=True,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
