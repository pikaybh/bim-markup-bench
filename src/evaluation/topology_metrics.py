"""Independent native IFC relationship edit signatures and delta F1.

Every signature is extracted from the actual IFC graph. We deliberately
do not interpret XML, Python authoring scripts, model tools or prompts.
"""
from __future__ import annotations

from collections.abc import Mapping
import ifcopenshell

from src.evaluation.semantic_diff import product_by_guid


RELATION_DEFS=(
    ("IfcRelContainedInSpatialStructure","RelatingStructure","RelatedElements"),
    ("IfcRelAggregates","RelatingObject","RelatedObjects"),
    ("IfcRelVoidsElement","RelatingBuildingElement","RelatedOpeningElement"),
    ("IfcRelFillsElement","RelatingOpeningElement","RelatedBuildingElement"),
    ("IfcRelSpaceBoundary","RelatingSpace","RelatedBuildingElement"),
    ("IfcRelConnectsElements","RelatingElement","RelatedElement"),
)


def _groups(x):
    if x is None:
        return ()
    return x if isinstance(x,tuple) else (x,)


def native_relation_edges(model:ifcopenshell.file,
                          aliases:Mapping[str,str]|None=None)->frozenset:
    aliases=aliases or {}
    edges=set()
    for cls,from_key,to_key in RELATION_DEFS:
        for rel in model.by_type(cls):
            lhs=_groups(getattr(rel,from_key))
            rhs=_groups(getattr(rel,to_key))
            metadata=()
            if cls=="IfcRelSpaceBoundary":
                metadata=(str(getattr(rel,"PhysicalOrVirtualBoundary",None)),
                          str(getattr(rel,"InternalOrExternalBoundary",None)))
            for parent in lhs:
                for child in rhs:
                    if parent is None or child is None:
                        continue
                    if not (parent.is_a("IfcRoot") and child.is_a("IfcRoot")):
                        continue
                    pguid=aliases.get(parent.GlobalId,parent.GlobalId)
                    cguid=aliases.get(child.GlobalId,child.GlobalId)
                    edges.add((cls,pguid,cguid,*metadata))
    return frozenset(edges)


def native_object_nodes(model:ifcopenshell.file,
                        aliases:Mapping[str,str]|None=None)->frozenset:
    aliases=aliases or {}
    return frozenset(
        (aliases.get(x.GlobalId,x.GlobalId),x.is_a())
        for x in product_by_guid(model).values()
    )


def delta(source:frozenset,edited:frozenset)->frozenset:
    return frozenset({("removed",*row) for row in source-edited}|
                     {("added",*row) for row in edited-source})


def set_f1(expected:frozenset,actual:frozenset)->float:
    if not expected and not actual:
        return 1.
    if not expected or not actual:
        return 0.
    tp=len(expected&actual)
    return 2.*tp/(len(expected)+len(actual))


def compare_topology(source:ifcopenshell.file,ground_truth:ifcopenshell.file,
                     output:ifcopenshell.file,
                     *,output_guid_aliases:Mapping[str,str]|None=None)->dict:
    original_edges=native_relation_edges(source)
    gt_edges=native_relation_edges(ground_truth)
    actual_edges=native_relation_edges(output,output_guid_aliases)
    ref_edge_edits=delta(original_edges,gt_edges)
    pred_edge_edits=delta(original_edges,actual_edges)
    original_nodes=native_object_nodes(source)
    gt_nodes=native_object_nodes(ground_truth)
    actual_nodes=native_object_nodes(output,output_guid_aliases)
    ref_node_edits=delta(original_nodes,gt_nodes)
    pred_node_edits=delta(original_nodes,actual_nodes)
    if not ref_node_edits and not ref_edge_edits:
        status=1. if not pred_node_edits and not pred_edge_edits else 0.
        return {
            "score":status,
            "reference_nodes_edited":0,
            "reference_edges_edited":0,
            "predicted_nodes_edited":len(pred_node_edits),
            "predicted_edges_edited":len(pred_edge_edits),
            "node_f1":1. if not pred_node_edits else 0.,
            "edge_f1":1. if not pred_edge_edits else 0.,
            "topology_change_expected":False,
            "topology_change_predicted":bool(pred_node_edits or pred_edge_edits),
        }
    node_f1=set_f1(ref_node_edits,pred_node_edits)
    edge_f1=set_f1(ref_edge_edits,pred_edge_edits)
    return {
        "score":float(.3*node_f1+.7*edge_f1),
        "reference_nodes_edited":len(ref_node_edits),
        "reference_edges_edited":len(ref_edge_edits),
        "predicted_nodes_edited":len(pred_node_edits),
        "predicted_edges_edited":len(pred_edge_edits),
        "node_f1":node_f1,
        "edge_f1":edge_f1,
        "topology_change_expected":True,
        "topology_change_predicted":bool(pred_node_edits or pred_edge_edits),
    }
