"""Offline G0 #4 provenance gap audit: never computes official benchmark scores.

Only compares the documented paper formula contract with the current
independent scorer's implementation evidence. No benchmark IFC is opened,
no GT/prompt is loaded, no remote requests or model provider are used.
"""
from __future__ import annotations

from hashlib import sha256
import inspect

from src.evaluation.bim_edit_scorer import (
    PROVENANCE, EVALUATOR_VERSION, STRICT_THRESHOLD,
    _candidate_target, _constrained_scores,
)
from src.evaluation.geometry_metrics import GeometrySettings
from src.evaluation.metric_contract import final_score, STRICT_PASS_THRESHOLD
from src.evaluation.topology_metrics import compare_topology

_PAPER_EXAMPLES = (
    ("H1_perfect", 1.0, 1.0, 1.0),
    ("H2_partial_topology", 1.0, 1.0, 0.47),
    ("H3_partial_geometry_semantics", 0.38, 0.72, 1.0),
    ("H4_failure", 0.0, 0.0, 0.0),
)


def audit_scorer_gap(*, geometry_settings:GeometrySettings|None=None) -> dict:
    config=geometry_settings or GeometrySettings()
    scorer_code=inspect.getsource(_candidate_target)
    topology_code=inspect.getsource(compare_topology)
    strict_code=inspect.getsource(_constrained_scores)
    evidence={
        "create_match_by_nearest_center": "candidates.sort(" in scorer_code,
        "explicit_hungarian_match_absent_in_candidate_target":
            "linear_sum_assignment" not in scorer_code and "hungarian" not in scorer_code.lower(),
        "topology_uses_guid_based_set_deltas": (
            "native_relation_edges" in topology_code
            and "delta(" in topology_code
            and "set_f1(" in topology_code
        ),
        "strict_pass_additional_collateral_veto":
            "collateral[\"collateral_clean\"]" in strict_code,
        "paper_and_independent_threshold_equal": STRICT_THRESHOLD==STRICT_PASS_THRESHOLD,
    }
    code_hashes={
        "candidate_target_sha256":sha256(scorer_code.encode("utf-8")).hexdigest(),
        "topology_comparison_sha256":sha256(topology_code.encode("utf-8")).hexdigest(),
        "strict_pass_sha256":sha256(strict_code.encode("utf-8")).hexdigest(),
    }
    examples=[]
    for label,geo,sem,topo in _PAPER_EXAMPLES:
        result=final_score(geo,sem,topo)
        examples.append({
            "paper_example":label,
            "rounded_axis_inputs":[geo,sem,topo],
            "scalar_mean":result["final_score"],
            "scalar_strict_pass":result["strict_pass"],
            "source":"paper_reported_rounded_component_scores",
            "raw_ifc_recomputed":False,
        })
    return {
        "status":("BLOCKED_OFFICIAL_SCORER_UNVERIFIED"
                  if all(evidence.values()) else "BLOCKED_REAUDIT_CODE_SIGNATURE_CHANGED"),
        "metric_origin":PROVENANCE,
        "evaluator_version":EVALUATOR_VERSION,
        "official_evaluator_source_commit_verified":False,
        "official_metric_numerical_equivalence":False,
        "official_tasks_scored":0,
        "paid_model_calls":0,
        "paper_sampling_per_object_upper_bound":4096,
        "independent_default_sample_count":config.sample_count,
        "sampling_schedule_equivalence_verified":False,
        "OBB_IoU_Hungarian_equivalence_verified":False,
        "greedy_topology_node_alignment_equivalence_verified":False,
        "same_strict_threshold":STRICT_THRESHOLD==STRICT_PASS_THRESHOLD,
        "paper_examples_scalar_only":examples,
        "current_code_evidence":evidence,
        "code_sha256":code_hashes,
        "next_required_evidence":[
            "author_owned_evaluator_source_revision_license_and_entrypoint",
            "identical_IFC_prediction_output_regraded_in_both_evaluators",
            "sample_allocation_and_rng_parity",
            "OBB_Hungarian_matching_and_topology_alignment_parity",
            "official_task_GT_and_individual_asset_rights",
        ],
    }
