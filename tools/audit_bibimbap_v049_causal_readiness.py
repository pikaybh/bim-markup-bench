"""Offline causal-validity admission gate for BIBIMBAP v0.49.

This module cannot run an LLM, a grader, or an IFC editor. It only checks
immutable prior evidence and preserves the distinction between interfaces.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SOURCE_REPORTS = {
    "v045": (
        "bibimbap_v045_original4_native_IFC_typed_writers_20261117.json",
        "7d7518f6c65242f7f00066beeb0229fbb6e42e44d5e841243666ac375105c4b3",
    ),
    "v046": (
        "bibimbap_v046_original27_all_native_IFC_paged_source_catalog_20261117.json",
        "beab50998c1f2f984342cf784fe910adc384752a16b8f0eed40623421c38509f",
    ),
    "v047": (
        "bibimbap_v047_original4_restricted_XML_Python_native_matched_20261117.json",
        "cf1d37bf84fe744921989affc8b524e296c4d3b38731601513fd1b9fa95a44aa",
    ),
    "v048": (
        "bibimbap_v048_original4_semantic_positive_negative_native_controls_20261117.json",
        "ca5f365198bff4f92b14031690b30338d3000adfd70b39c2be4471c9a32d7e08",
    ),
}
FOUR_TASKS = (
    "geometry_test_14",
    "geometry_test_15",
    "topological_test_11",
    "topological_test_17",
)
HEX_SHA = re.compile(r"[0-9a-f]{64}\Z")
REPORT_NAME = "bibimbap_v049_causal_arm_admission_20261117.json"
PRIMARY_D = "D_STATE_DECLARATIVE"
PRIMARY_I = "I_NATIVE_IFCOPENSHELL"
AUX_XML = "T_XML_TYPED"
AUX_PYTHON = "T_PYTHON_RESTRICTED_AST"


class EvidenceError(RuntimeError):
    """Frozen evidence did not satisfy the declared provenance contract."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise EvidenceError(reason)


def _raw_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_evidence(root: Path) -> tuple[dict, dict]:
    evidence: dict[str, dict] = {}
    for version, (filename, expected_hash) in SOURCE_REPORTS.items():
        path = root / "reports" / filename
        _require(path.is_file(), f"Missing prior frozen evidence: {filename}")
        _require(_raw_hash(path) == expected_hash, f"Frozen SHA mismatch: {filename}")
        evidence[version] = json.loads(path.read_text(encoding="utf-8"))
    return evidence, {v: digest for v, (_, digest) in SOURCE_REPORTS.items()}


def _source_rows(report47: dict, report48: dict) -> list[dict]:
    _require(report47["original_public_ITT_count"] == 45, "Original 45-task denominator changed")
    _require(report47["original_public_unique_IFC_source_SHA_count"] == 31, "Original 31 IFC denominator changed")
    _require(
        [report47[f"original_public_{k}_count"] for k in ("CREATE", "UPDATE", "DELETE")] == [15, 15, 15],
        "Original CRUD distribution changed",
    )
    _require(report47["selected_original_task_count"] == 4, "Restricted pilot denominator changed")
    _require(report47["other_original_tasks_NOT_in_matched_restricted_pilot"] == 41, "Other tasks denominator changed")
    _require(report47["max_tool_call_budget_each_arm_each_task"] == 25, "Restricted pilot tool budget changed")
    _require(report47["default_original_benchmark_Python_IfcOpenShell_unrestricted_tool_equivalent"] is False, "Restricted Python misreported as native")
    _require(report47["python_arm_restricted_AST_only_no_arbitrary_Python_execution"] is True, "Restricted AST semantics changed")
    _require(report47["identical_original_source_information_and_immutable_native_STEP_both_arms"] is True, "Source equality evidence missing")
    _require(report47["same_models_context_tokens_or_tool_ergonomics_proven"] is False, "Unproven token equivalence was promoted")
    _require(report47["original_45_equal_native_write_authority_proven"] is False, "Unproven full coverage was promoted")
    _require(report47["real_paid_XML_vs_Python_model_trials"] == 0, "Unexpected provider trials in frozen pilot")
    _require(report47["real_original_task_author_evaluator_invocations"] == 0, "Unexpected author grader calls")
    _require(report48["original_public_task_count"] == 45, "v048 changed task population")
    _require(report48["original_public_unique_native_IFC_source_count"] == 31, "v048 changed original IFC population")
    _require(report48["author_original_evaluator_equivalence_proven"] is False, "Independent oracle misreported as author evaluator")
    _require(report48["actual_real_LLM_model_trials"] == 0, "v048 is not an LLM run")
    _require(report48["original_author_evaluator_invocations"] == 0, "v048 author evaluator should not run")
    _require(report48["original_author_benchmark_task_score_claimed"] is False, "Developer semantic control misreported as benchmark result")
    _require(report48["real_independent_native_IFC_candidate_count"] == 16, "Native control candidate count mismatch")
    _require(report48["real_native_IFC_XML_and_Python_pair_count"] == 8, "Native control pair count mismatch")
    _require(report48["developer_example_oracle_decision_is_NOT_author_public_benchmark_score"] is True, "Developer control attribution lost")
    _require(report48["real_v048_research_physical_semantic_positive_pass"] == 4, "Research positive controls unverified")
    _require(report48["real_v048_research_physical_semantic_negative_rejected"] == 4, "Research negative controls unverified")

    rows = report47["original_four_paired_rows"]
    _require(len(rows) == 4, "Four original source/question pair records required")
    _require(set(report48["selected_original_four_tasks"]) == set(FOUR_TASKS), "v048 selected task identities changed")
    _require(set(r["original_public_task_id"] for r in rows) == set(FOUR_TASKS), "v047 original task identities changed")
    pins: list[dict] = []
    for row in sorted(rows, key=lambda r: r["original_public_task_id"]):
        for f in ("original_public_question_sha256", "original_public_source_ifc_sha256"):
            _require(isinstance(row[f], str) and bool(HEX_SHA.fullmatch(row[f])), f"Invalid source/question pin: {f}")
        _require(isinstance(row["same_original_source_XML_bytes_shown_to_both_models"], int) and row["same_original_source_XML_bytes_shown_to_both_models"] > 0, "Two-arm source fact evidence size missing")
        _require(bool(HEX_SHA.fullmatch(row["source_XML_read_SHA_identical_both_arms"])), "Two-arm XML source equality digest missing")
        _require(row["source_python_literal_roundtrip_exact_original_XML"] is True, "Python source literal is not byte-exact")
        _require(row["developer_generated_illustrative_candidate_NOT_original_task_solution"] is True, "Unblinded solution claim")
        _require(row["original_task_semantic_success_or_score_proven"] is False, "Developer candidate misreported as benchmark task success")
        _require(row["paid_LLM_model_trial"] is False, "Unexpected model run in developer record")
        _require(row["original_author_evaluator_invoked"] is False, "Author grader accessed during development")
        _require(row["both_arms_independent_native_oracle_PASS"] is True, "Independent IFC physical source oracle missing")
        _require(row["actual_two_independently_written_IFC_bytes_SHA256_IDENTICAL"] is True, "Native candidate output parity missing")
        _require(row["total_model_tool_call_budget_per_arm"] == 25, "Per-task restricted call budget changed")
        pins.append({
            "task_id": row["original_public_task_id"],
            "public_question_sha256": row["original_public_question_sha256"],
            "original_source_ifc_sha256": row["original_public_source_ifc_sha256"],
            "original_task_operation": row["original_task_CRUD"],
        })
    return pins


def classify_claim(xml_surface: str, python_surface: str) -> str:
    """No typed operation may be passed off as the primary D/I contrast."""
    if xml_surface == PRIMARY_D and python_surface == PRIMARY_I:
        return "PRIMARY_CAUSAL_CONTRAST_CONCEPT"
    if xml_surface == AUX_XML and python_surface == AUX_PYTHON:
        return "AUXILIARY_RESTRICTED_TYPED_CONTRAST_ONLY"
    raise EvidenceError("Unregistered or mismatched arm identities: refuse causal interpretation")


def demand_trial_admission(
    causal_arm: str, *,
    authorized_paid_budget: bool = False,
    approved_model_and_tokenizer: bool = False,
    verified_original_author_evaluator: bool = False,
    verified_unrestricted_python_sandbox: bool = False,
    verified_declarative_state_writer: bool = False,
) -> None:
    """Fail closed; no user-controlled flag can replace missing actual evidence."""
    _require(causal_arm == "PRIMARY_CAUSAL_CONTRAST_CONCEPT", "Auxiliary typed interface cannot launch as D/I causal trial")
    _require(verified_declarative_state_writer, "Original-native D-state writer unverified")
    _require(verified_unrestricted_python_sandbox, "I-native Python/IfcOpenShell sandbox unverified")
    _require(verified_original_author_evaluator, "Original evaluator equivalence not proven")
    _require(approved_model_and_tokenizer, "Model tokenizer/budget controls not independently pinned")
    _require(authorized_paid_budget, "Paid API budget approval not established")
    # This tool NEVER launches a model even when all flags are set.
    raise EvidenceError("Offline v0.49 gate is non-executing; model launch requires a separately approved runner")


def build_report(root: Path) -> dict:
    evidence, hashes = _read_evidence(root)
    _require(evidence["v045"]["new_v045_paid_provider_calls"] == 0, "v045 provider budget evidence changed")
    _require(evidence["v046"]["paid_provider_calls"] == 0, "v046 provider budget evidence changed")
    _require(evidence["v048"]["paid_provider_calls"] == 0, "v048 did not preserve the zero-provider gate")
    _require("XML is what the LLM edits, as a declarative document state." in (root / "AGENTS.md").read_text(encoding="utf-8"), "AGENTS.md D-state invariant missing")
    _require("Operations are inferred solely from before/after declarative document states" in (root / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8"), "Architecture snapshot-diff invariant missing")
    pins = _source_rows(evidence["v047"], evidence["v048"])
    return {
        "status": "BLOCKED_CAUSAL_PRIMARY_AND_PAID_TRIAL",
        "issue": "https://github.com/pikaybh/bim-markup-bench/issues/213",
        "stacked_parent_sha": "0da87ff4275582f98b5c4b8381cdb38a03178a40",
        "original_public_population": {"tasks": 45, "unique_source_ifcs": 31, "create": 15, "update": 15, "delete": 15},
        "exploratory_post_selected_four_original_tasks": pins,
        "other_original_tasks_outside_pilot": 41,
        "prior_frozen_report_sha256": hashes,
        "surface_identity": {
            PRIMARY_D: "Direct XML declarative document state; stable-ID before/after semantic diff; NOT proven source-native for original four",
            PRIMARY_I: "Executed sandboxed Python/IfcOpenShell against immutable original IFC; NOT verified matched to original four",
            AUX_XML: "Original source XML plus typed NativeEditPlan; bounded command interface; NOT the direct declarative D arm",
            AUX_PYTHON: "AST-validated single typed function; NO Python execution or general IfcOpenShell; NOT I arm",
        },
        "auxiliary_restricted_surface_evidence": {
            "estimand": classify_claim(AUX_XML, AUX_PYTHON),
            "developer_control_native_ifc_pairs_byte_equal": 8,
            "research_defined_positive_physical_controls": 4,
            "research_defined_negative_physical_controls": 4,
            "original_author_scores": None,
            "matched_paid_llm_trials": 0,
            "causal_D_state_vs_I_native_result": None,
        },
        "primary_estimand": {
            "arms": [PRIMARY_D, PRIMARY_I],
            "eligible_to_claim_causal_result": False,
            "task_denominator_for_confirmatory_original_benchmark": 45,
            "four_selected_tasks_are_exploratory_not_confirmatory": True,
            "causal_result": None,
            "token_count_by_model": None,
            "paid_usd_cost": None,
            "author_benchmark_score": None,
        },
        "launch_gate": {
            "approved_model_and_tokenizer": False,
            "source_info_consumption_and_prompt_token_equalized": False,
            "verified_original_native_declarative_state_diff_writer": False,
            "verified_isolated_unrestricted_python_ifcopenshell": False,
            "author_evaluator_provenance_or_calibration_approved": False,
            "paid_provider_budget_authorized_for_next_trial": False,
            "ground_truth_barrier_prospectively_audited_for_next_run": False,
            "model_launch_allowed": False,
        },
        "no_external_actions": {
            "paid_model_calls": 0,
            "original_author_grader_calls": 0,
            "docker_jobs": 0,
            "original_ifc_mutations": 0,
            "changed_previous_reports": 0,
            "new_experiment_score_claims": 0,
        },
    }


def canonical_bytes(report: dict) -> bytes:
    return (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Exclusively create frozen report once; never overwrite")
    mode.add_argument("--check", action="store_true", help="Read-only reproduce frozen report, compare exact bytes")
    args = parser.parse_args()
    report = build_report(args.root)
    result = canonical_bytes(report)
    path = args.root / "reports" / REPORT_NAME
    if args.write:
        with path.open("xb") as f:
            f.write(result)
    else:
        _require(path.exists() and path.read_bytes() == result, "v0.49 report differs from current evidence")
    print(f"V049_GATE=BLOCKED_PAID_AND_CAUSAL REPORT_SHA256={hashlib.sha256(result).hexdigest()} SOURCE_TASKS=4/45")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
