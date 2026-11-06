"""BIM-Edit paper scalar formulas ONLY — NOT a working IFC model scorer.

References: https://arxiv.org/html/2606.20146 (Section 3.2 & Appendix E).
This module does not compute IFC edit graphs, point clouds, OBB matching,
semantic key extraction, or graph alignments. Never label outputs as official.
"""
from __future__ import annotations
import math
from typing import Iterable

STRICT_PASS_THRESHOLD = 0.98
GEOMETRY_ALPHA = 5.0
TOPOLOGY_NODE_WEIGHT = 0.3
TOPOLOGY_EDGE_WEIGHT = 0.7

class InvalidScore(ValueError):
    pass

def unit_score(x: float, label: str) -> float:
    if isinstance(x, bool) or not isinstance(x, (float, int)):
        raise InvalidScore(label + " is not numeric")
    y = float(x)
    if not math.isfinite(y) or not (0.0 <= y <= 1.0):
        raise InvalidScore(label + " must be within [0,1] and finite")
    return y

def geometry_from_median_chamfer(cd_med: float, joint_bbox_diagonal: float) -> float:
    """Paper Eq 5 after clouds are already sampled and their CD computed."""
    if not isinstance(cd_med, (int, float)) or not math.isfinite(cd_med) or cd_med < 0:
        raise InvalidScore("Median Chamfer distance must be nonnegative and finite")
    if not isinstance(joint_bbox_diagonal, (int, float)) or not math.isfinite(joint_bbox_diagonal) or joint_bbox_diagonal <= 0:
        raise InvalidScore("Degenerate/invalid joint bounding diagonal is not specified by paper")
    return math.exp(-GEOMETRY_ALPHA * cd_med / joint_bbox_diagonal)

def semantic_score(matched_pairs: Iterable[tuple[bool, float]],
                   reference_entities: int, *,
                   deletion_removed: bool | None = None) -> float:
    """Paper Eq 3 for *already OBB-assigned* class/property pairs.

    Unmatched reference objects score 0. A delete-task bypasses matching.
    """
    if deletion_removed is not None:
        if type(deletion_removed) is not bool:
            raise InvalidScore("Deletion flag must be boolean")
        return float(deletion_removed)
    if type(reference_entities) is not int or reference_entities <= 0:
        raise InvalidScore("reference_entities must be positive")
    pairs = list(matched_pairs)
    if len(pairs) > reference_entities:
        raise InvalidScore("More matches than reference entities")
    total = 0.0
    for match, property_fraction in pairs:
        if type(match) is not bool:
            raise InvalidScore("Class match must be boolean")
        total += 0.5 * (float(match) + unit_score(property_fraction, "property score"))
    return total / reference_entities

def topology_score(node_f1: float | None, edge_f1: float | None, *,
                   reference_has_topology_change: bool,
                   prediction_has_topology_change: bool) -> float:
    """Paper Eq 4 plus special no-reference-topology-edit case."""
    if type(reference_has_topology_change) is not bool or type(prediction_has_topology_change) is not bool:
        raise InvalidScore("Topology edit flags must be booleans")
    if not reference_has_topology_change:
        return 0.0 if prediction_has_topology_change else 1.0
    if node_f1 is None or edge_f1 is None:
        raise InvalidScore("Edited-node and edited-edge F1 must both be supplied")
    return TOPOLOGY_NODE_WEIGHT * unit_score(node_f1, "node F1") + TOPOLOGY_EDGE_WEIGHT * unit_score(edge_f1, "edge F1")

def final_score(geometry: float, semantics: float, topology: float) -> dict:
    geo = unit_score(geometry, "geometry")
    sem = unit_score(semantics, "semantics")
    topo = unit_score(topology, "topology")
    return {
        "geometry": geo,
        "semantics": sem,
        "topology": topo,
        "final_score": (geo + sem + topo) / 3.0,
        "strict_pass": all(x >= STRICT_PASS_THRESHOLD for x in (geo, sem, topo)),
        "metric_origin": "paper-formula-only",
        "full_ifc_evaluator_implemented": False
    }
