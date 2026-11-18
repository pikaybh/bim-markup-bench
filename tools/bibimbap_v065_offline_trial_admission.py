"""v0.65 permanently offline trial-admission prototype, no provider code.

Scientific experiment must not launch while original IFC/author-code
chain-of-title and permission, genuine blind independent source exposure
review, published grader parity, matched token/tool/feedback/ITI and
explicit approved model snapshot/funded cap have not been established.

Even if a caller passes all-true fake fields or a matching schema, this
module refuses all original IFC provider/model trials. A future explicit
separate checkpoint with legal/model owner approval must build and
review an entirely distinct launch implementation; never toggle flags
on this class.
"""
from __future__ import annotations

import hashlib
import json


class TrialBlocked065(PermissionError):
    pass


def canonical(data):
    return (json.dumps(data,sort_keys=True,indent=2,
                       ensure_ascii=False)+"\n").encode("utf8")


def proposal_manifest(source_ledger_sha256:str)->dict:
    """Unregistered OFFLINE draft. Not a human approved pre-registration."""
    if len(source_ledger_sha256)!=64:
        raise TrialBlocked065("Immutable source-cluster ledger SHA required")
    return {
        "status":"NOT_PREREGISTERED_NOT_APPROVED_UNCONDITIONAL_NO_LAUNCH",
        "experiment":"BIBIMBAP original-source D versus I; NOT YET authorized",
        "source_cluster_ledger_sha256":source_ledger_sha256,
        "original_public_task_count":45,
        "source_family_cluster_count":31,
        "previously_developer_verified_cases":10,
        "current_true_unseen_confirmatory_source_count_certified":0,
        "independent_source_family_randomization_unit":"original_IFC_SHA256",
        "source_stratification":["IFC2X3","IFC4","IFC4X3",
                                 "CREATE","UPDATE","DELETE",
                                 "geometry","topological","basic"],
        "trial_arms_proposed":["D_COMPLETE_XML","D_MANAGED_FINAL_STATE",
                                "I_NATIVE_GENERAL_PYTHON"],
        "same_initial_source_XML_required":True,
        "tool_schema_input_output_SHA_required":True,
        "source_native_condition_and_question_equivalence_required":True,
        "source_rights_verified_for_provider_transfer":False,
        "source_rights_verified_for_retention":False,
        "pinned_author_code_license_verified":False,
        "original_paper_author_scorer_revision_parity_verified":False,
        "source_cluster_blind_exposure_auditor_approved":False,
        "source_family_test_set_immutable_registered":False,
        "data_owner_external_provider_upload_authorized":False,
        "model_provider":None,
        "model_snapshot":None,
        "approved_paid_USD_cap":None,
        "model_temperature":None,
        "model_seed":None,
        "model_max_output_tokens":None,
        "provider_actual_billable_input_tokens":None,
        "provider_actual_billable_output_tokens":None,
        "provider_total_billed_USD":None,
        "same_context_budget_output_tokens_and_feedback_not_proven":True,
        "equal_tool_power_and_affordance_not_proven":True,
        "max_total_tool_calls_per_attempt":25,
        "per_task_attempt_wall_clock_seconds":None,
        "retry_policy_registered":False,
        "feedback_policy_registered":False,
        "prompt_input_common_exact_byte_source_SHA_required":True,
        "primary_endpoint":"Original repository scorer only if provenance resolved",
        "secondary_endpoint":"Independent native IFC physical task correctness",
        "source_schema_delta_and_legal_native_edits_gate":True,
        "cluster_ITT_denominator_preserves_failures_crashes_and_timeouts":True,
        "original_author_metric_composite_bool_and_float_not_conflated":True,
        "causal_tool_intervention_validity_status":"NOT_IDENTIFIED",
        "official_paper_score_substitution_permitted":False,
        "actual_provider_model_calls":0,
        "actual_paid_calls":0,
        "actual_original_IFC_external_uploads":0,
        "launch_route_in_this_module":"NO_IMPLEMENTATION_ALWAYS_RAISES",
    }


def deny_original_model_trial(*args,**kwargs):
    raise TrialBlocked065(
        "v0.65 hard offline firewall: no original IFC/model/provider "
        "execution or transfer; an explicit new authorized, legally "
        "reviewed provider runner is required at a separate checkpoint"
    )


def deny_if_all_approvals_are_forged(*args,**kwargs):
    return deny_original_model_trial(*args,**kwargs)
