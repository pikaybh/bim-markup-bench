"""Fixed crash-isolated trusted native IFC4X3 connected Wall writer.

This is the trusted compiler's one-shot CHILD PROCESS, never a model-facing
Python execution tool. Its source bytes must match the independently pinned
original-public IFC4X3 normalized source SHA; command line is internal only.
There is exactly one fixed cleanup order. The parent has additional IFC
Root/STEP, orphan, typed-document and exclusive transaction gates, so this
worker's zero exit code alone is not permission to publish the result.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.api.pset
import ifcopenshell.util.element

def emit(name,detail=None):
    print("V027_WORKER_EVENT",name,detail if detail is not None else "",flush=True)

def run(source:Path,destination:Path,source_sha:str,guid:str):
    if not source.is_file() or source.is_symlink():
        raise ValueError("Source absent or symlink")
    if destination.exists() or destination.is_symlink():
        raise ValueError("Destination exists, refuse overwrite")
    if source_sha!="16568e7c4b8b9d62567a7a199101269daa6e5b1b7535cec095b8e233ae2ef6ac":
        raise ValueError("Non-original normalized source SHA is forbidden")
    if sha256(source.read_bytes()).hexdigest()!=source_sha:
        raise ValueError("Source checksum mismatch")
    m=ifcopenshell.open(str(source))
    if m.schema!="IFC4X3":raise ValueError("Source is not original IFC4X3")
    wall=m.by_guid(guid)
    if not wall.is_a("IfcWall") or wall.HasOpenings:
        raise ValueError("Original source target not a safe Wall")
    inv=list(m.get_inverse(wall))
    if Counter(x.is_a() for x in inv)!=Counter({
        "IfcRelConnectsPathElements":2,
        "IfcRelDefinesByProperties":3,
        "IfcRelDefinesByType":1,
        "IfcRelAssociatesMaterial":1,
        "IfcRelAssociatesClassification":1,
        "IfcRelContainedInSpatialStructure":1}):
        raise ValueError("Unexpected original connected Wall inverse")
    paths=[x for x in inv if x.is_a("IfcRelConnectsPathElements")]
    own_psets=[x for x in inv if x.is_a("IfcRelDefinesByProperties")]
    reps=list(wall.Representation.Representations)
    if len(reps)!=2 or not wall.ObjectPlacement:raise ValueError("Missing source wall shape/placement")
    for r in paths:
        if (r.RelatedElement!=wall or
            not r.RelatingElement.is_a("IfcWall")):raise ValueError("Wrong path role")
    for r in own_psets:
        if (tuple(r.RelatedObjects)!=(wall,)
            or not r.RelatingPropertyDefinition.is_a("IfcPropertySet")
            or tuple(m.get_inverse(r.RelatingPropertyDefinition))!=(r,)):
            raise ValueError("Shared pset risk")
    pds=wall.Representation
    placement=wall.ObjectPlacement
    rep_ids={x.id() for x in reps}
    layers=[x for x in m.by_type("IfcPresentationLayerAssignment")
            if any(rep in x.AssignedItems for rep in reps)]
    if len(layers)!=1:raise ValueError("Expected exactly one shared presentation layer")
    layer=layers[0]
    if len(layer.AssignedItems)<=len(reps):raise ValueError("No surviving layer items")
    for r in paths:m.remove(r)
    emit("TWO_PATH_ROOTS_REMOVED")
    for r in own_psets:
        ifcopenshell.api.pset.remove_pset(m,product=wall,pset=r.RelatingPropertyDefinition)
    emit("THREE_OWNED_PSETS_REMOVED")
    # This single, source-verified order is deliberately fixed.
    # Earlier SDK root.remove_product and arbitrary cleanup order caused
    # a process-level Windows native access violation. This worker is
    # supervised and can never publish its candidate without parent gates.
    layer.AssignedItems=tuple(e for e in layer.AssignedItems if e.id() not in rep_ids)
    emit("WALL_REPS_REMOVED_FROM_SHARED_LAYER")
    wall.Representation=None
    emit("PRODUCT_SHAPE_DETACHED")
    ifcopenshell.util.element.remove_deep2(m,pds)
    emit("PRODUCT_SHAPE_AND_UNSHARED_GEOMETRY_PURGED")
    wall.ObjectPlacement=None
    ifcopenshell.util.element.remove_deep2(m,placement)
    emit("TARGET_PLACEMENT_PURGED")
    m.remove(wall)
    emit("SOURCE_WALL_ROOT_REMOVED")
    destination.parent.mkdir(parents=True,exist_ok=True)
    emit("PREPARE_WRITE")
    m.write(str(destination))
    emit("WRITE_DONE")
    fresh=ifcopenshell.open(str(destination))
    emit("REOPEN_OK",len(fresh.by_type("IfcProduct")))
    if source_sha!="16568e7c4b8b9d62567a7a199101269daa6e5b1b7535cec095b8e233ae2ef6ac":
        raise ValueError("Non-original normalized source SHA is forbidden")
    if sha256(source.read_bytes()).hexdigest()!=source_sha:
        raise ValueError("Source mutated by worker")
    print("V027_WORKER_JSON",json.dumps({
        "mode":"fixed_source_bound_deep_cleanup",
        "source_sha256":source_sha,
        "result_sha256":sha256(destination.read_bytes()).hexdigest(),
        "original_Wall_absent":not any(x.GlobalId==guid for x in fresh.by_type("IfcWall")),
        "product_count":len(fresh.by_type("IfcProduct")),
        "orphan_rep_count":sum(fresh.get_total_inverses(x)==0
                               for x in fresh.by_type("IfcShapeRepresentation")),
        "orphan_pds_count":sum(fresh.get_total_inverses(x)==0
                               for x in fresh.by_type("IfcProductDefinitionShape")),
        "orphan_place_count":sum(fresh.get_total_inverses(x)==0
                               for x in fresh.by_type("IfcLocalPlacement")),
    },sort_keys=True),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--destination",type=Path,required=True)
    parser.add_argument("--source-sha",required=True)
    parser.add_argument("--public-guid",required=True)
    args=parser.parse_args()
    try:
        run(args.source,args.destination,args.source_sha,args.public_guid)
    except Exception as exc:
        emit("PYTHON_EXCEPTION",type(exc).__name__+":"+str(exc)[:160])
        raise
