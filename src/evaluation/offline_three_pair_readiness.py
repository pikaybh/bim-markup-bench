"""G1 #16 — 36-candidate OFFLINE three-pair executable readiness audit.

This does not call an LLM, score official BIM-Edit outputs, read hidden
ground truths or license-protected IFC references. It re-executes exactly
three independent, developer-authored D0/XML vs I0/Python source-only
demonstrations, while accounting for the ENTIRE original frozen 36 task
denominator and its historical 30/6 asset availability.

Historical STATIC_UNSUPPORTED stays historical: one Door capability was
developed later, after examining this frozen source, and is counted in a
SEPARATE *post-hoc engineering* column, not retroactively approved.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Callable, Any

from src.data.bim_edit import AuditError
from src.evaluation.frozen_pilot_readiness import (
    load_pinned_evidence,
)
from tools.verify_prompt_grounded_window_pair import verify_prompt_grounded_window_pair
from tools.verify_prompt_grounded_spatial_wall import verify_prompt_grounded_spatial_wall
from tools.verify_public_door_delete_gate import verify_public_door_delete_gate

ROOT = Path(__file__).resolve().parents[2]

# SHA of preexisting, read-only evidence. These exact files remain unchanged.
EXTRA_PINS = {
    "rights": (
        "reports/g0_pilot_ifc_rights_20261110.json",
        "93ccd8f716b1a9dcd48fdd9967013977e1fbbdd3453a55a62dbaea755a01539a",
    ),
    "readiness": (
        "reports/g1_frozen_pilot_readiness_20261110.json",
        "42db4d9594926b086c9780e0abcd0e8f40ba228b044c6140714c442d28548cc0",
    ),
    "context": (
        "reports/g2_frozen_context_parity_20261110.json",
        "6e19fac000df3601e14710d2d994b693286d727419edbc7c833de12d730630c6",
    ),
    "scorer_origin": (
        "reports/g0_official_scorer_origin_review_20261111.json",
        "5964631a47162528abbb059f1164cae600050cba2d5eccf69f3cd2fe6034d921",
    ),
}
CASES = (
    "WIN-UPD-DIR-A-002",
    "WAL-CRE-SPA-A-003",
    "DOR-DEL-DIR-A-001",
)
EXPECTED_STATUS = {
    CASES[0]: "PASS_PROMPT_DERIVED_SOURCE_ONLY_PAIR_OFFICIAL_TASK_STILL_UNVERIFIED",
    CASES[1]: "PASS_PROMPT_GROUNDED_WALL_TWO_JOINS_SOURCE_ONLY_FULL_ORACLE_BLOCKED",
    CASES[2]: "PASS_BOUNDED_D0_I0_NATIVE_DELETION_OFFICIAL_TASK_BLOCKED",
}
METHOD = {
    CASES[0]: "PUBLIC_INSTRUCTION_DERIVED_WINDOW_OPENING_MOVE",
    CASES[1]: "PUBLIC_INSTRUCTION_DERIVED_WALL_CREATION_AND_TWO_NATIVE_JOINS",
    CASES[2]: "PUBLIC_INSTRUCTION_DERIVED_DOOR_OPENING_CASCADE_DELETE",
}
PINNED_TASK_SHA = "75b4847814dbefad95340556c0b62f9cda72cac319cd82ecb23ea4933c9ab694"
EXPECTED_REASONS = {"STATIC_ENGINE_UNSUPPORTED": 23, "MISSING_PINNED_INPUT_IFC": 2}
EXPECTED_ORIGINAL_30 = 30


class OfflinePairReadinessBlocked(AuditError):
    """Invalid pinned proof or an attempted promotion to benchmark result."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise OfflinePairReadinessBlocked("G1 source-only pair readiness: " + reason)


def _load_snapshot(root: Path, rel: str, digest: str) -> dict:
    path = root / rel
    _require(path.is_file() and not path.is_symlink(),
             "source evidence missing, linked or nonfile")
    data = path.read_bytes()
    _require(sha256(data).hexdigest() == digest, "frozen evidence SHA changed: " + rel)
    try:
        obj = json.loads(data)
    except (ValueError, UnicodeDecodeError) as exc:
        raise OfflinePairReadinessBlocked("Malformed frozen JSON: " + rel) from exc
    _require(isinstance(obj, dict), "evidence document must be a JSON object")
    return obj


def _load_evidence(root: Path) -> dict:
    pinned = load_pinned_evidence(root=root)  # nine older source/asset/manual/scorer/budget pins
    additional = {
        name: _load_snapshot(root, *pair) for name, pair in EXTRA_PINS.items()
    }
    return {**pinned, **additional}


def _index(rows: Any, expected: int, kind: str) -> dict[str, dict]:
    _require(isinstance(rows, list) and len(rows) == expected,
             kind + ": unexpected task count")
    if not all(isinstance(v, dict) and isinstance(v.get("task_id"), str)
               and v["task_id"] for v in rows):
        raise OfflinePairReadinessBlocked(kind + ": missing task identifiers")
    output = {r["task_id"]: r for r in rows}
    _require(len(output) == expected, kind + ": duplicate task IDs")
    return output


def _assert_same_frozen_task_population(records: dict) -> tuple[dict, dict, dict]:
    pilot = records["candidate"]
    readiness = records["readiness"]
    rights = records["rights"]
    context = records["context"]
    scorer = records["scorer_origin"]
    _require(pilot.get("status") == "CANDIDATE_NOT_PREREGISTERED"
             and pilot.get("sample_size") == 36
             and pilot.get("runs_per_repetition") == 72
             and pilot.get("gate_status") == {
                 "G0": "NOT_PASSED", "G1": "NOT_PASSED",
                 "G2": "NOT_PASSED", "BUDGET": "NOT_APPROVED"
             }, "candidate sample has been promoted or changed")
    tasks = _index(pilot.get("tasks"), 36, "candidate")
    past = _index(readiness.get("tasks"), 36, "historical readiness")
    assets = _index(rights.get("tasks"), 36, "historical rights")
    observed = _index(context.get("tasks"), 36, "G2 observation context")
    _require(set(tasks) == set(past) == set(assets) == set(observed),
             "sample IDs differ across evidence releases")
    _require(set(CASES).issubset(tasks), "at least one demonstration not in the original 36")
    _require((readiness.get("task_count"),readiness.get("static_engine_unsupported_count"),
              readiness.get("historical_verified_input_and_reference_deltas_count"))
             == (36,23,30), "old source readiness class totals changed")
    _require(rights.get("status_counts") == {
        "BLOCKED_PAIRED_INPUT_REFERENCE_CONTENT_MISSING":6,
        "VERIFIED_PINNED_BYTES_RIGHTS_UNRESOLVED":30,
    } and rights.get("individual_model_license_documents_verified") == 0
             and rights.get("full_g0_release_authorized") is False,
             "original data model-level rights are not cleared")
    _require(context.get("context_parity_checked") == 11
             and context.get("context_parity_blocked") == 0
             and context.get("static_engine_unsupported_not_tested") == 23
             and context.get("missing_conditional_source_inputs") == 2
             and context.get("live_pilot_authorized") is False
             and context.get("model_context_transport_verified") is False,
             "historical local observation/transport evidence changed")
    _require(scorer.get("official_tasks_scored") == 0
             and scorer.get("author_original_evaluator_cli_entrypoint_verified") is False
             and scorer.get("G0_G1_G2_G3_release_allowed") is False,
             "original scorer origin has been promoted without new verification")
    for item in tasks.values():
        task_id = item["task_id"]
        prev, legal = past[task_id], assets[task_id]
        _require(prev["operation"] == item["operation"]
                 and prev["category"] == item["category"]
                 and prev["scene"] == item["scene"]
                 and prev["target_class"] == item["entity_type"],
                 "task stratum or entity type changed")
        _require((prev["previous_pinned_input_and_reference_delta_evidence"] is True)
                 == (legal["status"] ==
                     "VERIFIED_PINNED_BYTES_RIGHTS_UNRESOLVED"),
                 "input/reference bytes crosswalk inconsistent")
        _require(prev["task_oracle_fully_proven"] is False
                 and prev["official_benchmark_task_scored"] is False,
                 "historical task score forged")
    _require(sum(x["status"]=="VERIFIED_PINNED_BYTES_RIGHTS_UNRESOLVED"
                 for x in assets.values()) == EXPECTED_ORIGINAL_30,
             "historical 30 verified task pair files mismatch")
    _require(sum(r["source_or_engine_reason"]=="STATIC_ENGINE_UNSUPPORTED"
                 for r in past.values())==23,
             "original 23 unsupported reason codes changed")
    _require(all(assets[case]["status"]=="VERIFIED_PINNED_BYTES_RIGHTS_UNRESOLVED"
                 for case in CASES),
             "one of the three public native test sources was historically missing")
    return tasks, past, assets


def _assert_live_demo(case: str, report: dict) -> dict:
    _require(isinstance(report, dict)
             and report.get("status") == EXPECTED_STATUS[case],
             "source-only harness failed or unsupported case: " + case)
    _require(report.get("official_tasks_scored") == 0,
             "official score was silently computed")
    if case == CASES[0]:
        _require(
            report.get("task_id") == case
            and report.get("source_only_deterministic_instruction_pair_demonstrated") is True
            and report.get("independent_native_D0_I0_observation_parity") is True
            and report.get("window_and_opening_native_world_move_matches_instruction") is True
            and report.get("IFC_full_file_d0_i0_equal") is True
            and report.get("common_model_facing_observation_byte_identical") is True
            and report.get("all_existing_relationships_preserved") is True
            and report.get("full_official_reference_IFC_task_success_proven") is False
            and report.get("model_facing_tool_and_feedback_parity_approved") is False
            and report.get("LLM_calls") == 0
            and report.get("G1_G2_G3_live_release_authorized") is False,
            "Window edited source native IFCs not independently comparable")
        return {
            "source_only_native_pair_pass": True,
            "native_postcondition": "WINDOW_OPENING_WORLD_MOVE_AND_RELATIONS_PRESERVED",
            "native_subclaim": {"source_only_exact_pair_file_parity": True},
            "full_public_task_oracle": False,
        }
    if case == CASES[1]:
        _require(
            report.get("frozen_task_id") == case
            and report.get("prompt_right_side_door_world_y_offset_verified") is True
            and report.get("native_path_joins_to_prompt_walls") == 2
            and report.get("native_d0_i0_ifc_six_category_parity") is True
            and report.get("common_model_source_components_byte_identical") is True
            and report.get("existing_space_boundaries_unmodified") is True
            and report.get("complete_task_oracle_proven") is False
            and report.get("room_split_if_required_by_official_target_proven") is False
            and report.get("model_generated_output_used") is False
            and report.get("model_provider_calls") == 0
            and report.get("G1_G2_G3_experiment_unblocked") is False,
            "Spatial Wall source parity or room-split caveat missing")
        return {
            "source_only_native_pair_pass": True,
            "native_postcondition": "WALL_CREATED_AT_PUBLIC_OFFSET_AND_TWO_JOINS",
            "native_subclaim": {"native_wall_join_count":2},
            "full_public_task_oracle": False,
        }
    if case == CASES[2]:
        _require(
            report.get("frozen_task_id") == case
            and report.get("D0_trusted_compiler_scoped_deletion_committed") is True
            and report.get("D0_I0_both_native_success_proven") is True
            and report.get("D0_I0_common_dependency_counts_match") is True
            and report.get("native_IfcRoot_deleted") == 10
            and report.get("native_unrelated_world_meshes_preserved") == 13
            and report.get("source_Opening_direct_storey_assignment_does_not_exist") is True
            and report.get("unmentioned_space_boundary_cleanup_is_declared_native_policy") is True
            and report.get("full_task_oracle_proven") is False
            and report.get("LLM_calls") == 0
            and report.get("G1_G2_G3_release_allowed") is False,
            "Door cascade source dependencies do not match bounded native evidence")
        return {
            "source_only_native_pair_pass": True,
            "native_postcondition": "DOOR_OPENING_CASCADE_AND_UNRELATED_MESHES_PRESERVED",
            "native_subclaim": {
                "deleted_ifc_roots": 10,
                "unrelated_world_meshes_preserved": 13,
                "space_boundary_policy_not_officially_resolved": True,
            },
            "full_public_task_oracle": False,
        }
    raise OfflinePairReadinessBlocked("Case not predeclared")


RUNNERS: dict[str,Callable[[],dict]] = {
    CASES[0]: verify_prompt_grounded_window_pair,
    CASES[1]: verify_prompt_grounded_spatial_wall,
    CASES[2]: verify_public_door_delete_gate,
}


def run_offline_three_pair_recheck(*, root:Path=ROOT,
                                   runners:dict[str,Callable[[],dict]]|None=None) -> dict:
    """Run three public-source deterministic pairs; retain all other 33 IDs."""
    records=_load_evidence(root)
    tasks, baseline, rights = _assert_same_frozen_task_population(records)
    chosen=RUNNERS if runners is None else runners
    _require(set(chosen)==set(CASES), "caller changed fixed subset")
    demos={}
    for case in CASES:
        observed=chosen[case]()
        demos[case]=_assert_live_demo(case,observed)
    rows=[]
    for item in records["candidate"]["tasks"]:
        task_id=item["task_id"]
        prev=baseline[task_id]
        rights_record=rights[task_id]
        demo=demos.get(task_id)
        rows.append({
            "task_id":task_id,
            "operation":item["operation"],
            "category":item["category"],
            "scene":item["scene"],
            "target_class":item["entity_type"],
            "historical_g1_disposition_unchanged":prev["readiness_disposition"],
            "historical_reason_code_unchanged":prev["source_or_engine_reason"],
            "pinned_source_and_reference_bytes_historically_checked":(
                rights_record["status"]=="VERIFIED_PINNED_BYTES_RIGHTS_UNRESOLVED"),
            "per_model_permission_independently_cleared":False,
            "source_only_pair_rerun_now":demo is not None,
            "posthoc_engineering_proof_not_scored":demo is not None,
            "native_verification_method":METHOD.get(task_id),
            "native_postcondition":demo["native_postcondition"] if demo else None,
            "native_subclaim":demo["native_subclaim"] if demo else None,
            "full_instruction_specific_oracle_approved":False,
            "official_score_computed":False,
            "live_LLM_trial_authorized":False,
        })
    _require(len(rows)==36 and len({r["task_id"] for r in rows})==36,
             "Pilot population changed")
    _require(sum(r["source_only_pair_rerun_now"] for r in rows)==3,
             "Native pair count differs from actual live executions")
    _require(sum(r["pinned_source_and_reference_bytes_historically_checked"]
                 for r in rows)==30, "Source/reference evidence count changed")
    _require(sum(r["historical_reason_code_unchanged"]=="STATIC_ENGINE_UNSUPPORTED"
                 for r in rows)==23,
             "Historical unsupported statuses were retrospectively changed")

    return {
        "version":"G1_FROZEN_36_THREE_POSTHOC_SOURCE_ONLY_PAIRS_RECHECK_V0_1",
        "status":"PASS_THREE_OFFLINE_NATIVE_PAIRS_LLM_AND_OFFICIAL_BENCHMARK_BLOCKED",
        "scope":"three_developer_authored_source_only_native_pairs_not_LLM",
        "fixed_candidate_sha256":PINNED_TASK_SHA,
        "frozen_candidates":36,
        "frozen_source_reference_pairs_historically_verified":30,
        "frozen_source_reference_pairs_missing":6,
        "unique_external_ifc_asset_rights_individually_cleared":0,
        "frozen_static_unsupported_legacy_classifications_unchanged":23,
        "historical_conditional_source_lookups":11,
        "historical_common_source_text_parity_verified":11,
        "posthoc_dev_native_pairs_executed_now":3,
        "posthoc_dev_native_pairs_passed_now":3,
        "source_only_pair_task_ids":list(CASES),
        "historical_pilot_task_scope_retroactively_changed":False,
        "full_instruction_specific_D0_I0_task_oracles_proven":0,
        "actual_model_generated_XML_or_Python_used":False,
        "actual_LLM_trials":0,
        "official_bim_edit_scorer_executed":False,
        "official_bim_edit_tasks_scored":0,
        "GT_or_target_fields_exposed_to_model":False,
        "ground_truth_IFC_opened_in_this_run":False,
        "reference_IFC_read_by_this_orchestrator":False,
        "linux_worker_admission_verified":False,
        "official_author_scorer_CLI_verified":False,
        "model_provider_token_usage_measured":False,
        "paid_budget_approved":False,
        "G0_G1_G2_G3_live_experiment_release_allowed":False,
        "frozen_external_evidence_sha256":{
            key:digest for key,(_,digest) in sorted(EXTRA_PINS.items())
        },
        "tested_operations":["update","create","delete"],
        "tested_instruction_categories":["direct","spatial"],
        "all_other_33_tasks_not_rerun_not_silently_dropped":True,
        "tasks":rows,
    }
