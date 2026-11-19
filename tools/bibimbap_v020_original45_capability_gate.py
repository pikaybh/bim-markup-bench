"""v0.20 original BIBIMBAP 45-task evidence-only capability parity gate.

Reads ONLY previously frozen original task/source reports. Does NOT edit IFC,
import the XML compiler or run an author scorer, Docker, untrusted Python,
model or paid provider. Distinguishes identical *read responses* from equal
native IFC information, writable source features and true matched LLM trials.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import argparse
import json
from pathlib import Path
import re

from tools.bibimbap_v020_terminal_submission_broker import offline_terminal_noninterference_audit


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = {
    "v016": ("reports/bibimbap_v016_original45_scoreability_and_column_parity_20261114.json",
             "162ff7408429062b4e80abb3fe48bb6bb1b0c0bff51260d04d0a616d7a104ae7"),
    "v017_information": ("reports/bibimbap_v017_original45_information_parity_gate_20261114.json",
                         "c2683de1705b92ebe0ce8472c6a870b98c54c668e387ddf80c9377cdb2e88078"),
    "v017_native": ("reports/bibimbap_v017_original_topological_slab_I0_D0_author_parity_20261114.json",
                    "c6b02877a3f031c8f5435222b65db4a0fef04568119eaa750586f106d53231e8"),
    "v018": ("reports/bibimbap_v018_original45_common_read_observation_audit_20261114.json",
             "89a53c28a9c5e679fcdfb962bebe6b9bd8075e4ac0437e07ea1a0b72ea7b1b2a"),
    "v019": ("reports/bibimbap_v019_sealed_original_test15_os_and_author_20261114.json",
             "5a49f85e74398269ad5a094db9ec362fe9ed4658a89028a68b3c08452059075e"),
}
AUTHOR_SHA = "667004e16bd38fd7d538bcee56191465429fd975"
DATA_SHA = "f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca"
FROZEN_NATIVE_EQUAL = frozenset({
    "geometry_test_18", "geometry_test_19", "test_15", "test_16",
    "topological_test_15",
})
FROZEN_AUTHOR_SCORABLE = frozenset({
    "test_15", "test_16", "topological_test_15",
})
FROZEN_AUTHOR_BLOCKED = frozenset({"geometry_test_18", "geometry_test_19"})
SHA_RE = re.compile(r"[a-f0-9]{64}\Z")
TASK_RE = re.compile(r"(?:geometry_|topological_)?test_(?:0[1-5]|1[1-5]|1[6-9]|20)\Z")


class CapabilityGateBlocked(ValueError):
    pass


def _assert(condition: bool, name: str) -> None:
    if not condition:
        raise CapabilityGateBlocked(name)


def load_frozen_evidence(root: Path = ROOT) -> dict:
    """Require exact tracked frozen evidence, without rewriting ANY source."""
    results = {}
    for key, (rel, expected) in EVIDENCE.items():
        p = root / rel
        _assert(p.is_file() and not p.is_symlink(), "FROZEN_EVIDENCE_FILE_MISSING")
        raw = p.read_bytes()
        _assert(sha256(raw).hexdigest() == expected, "FROZEN_EVIDENCE_SHA256_MISMATCH")
        try:
            obj = json.loads(raw)
        except (ValueError, UnicodeDecodeError) as exc:
            raise CapabilityGateBlocked("FROZEN_EVIDENCE_INVALID_JSON") from exc
        _assert(isinstance(obj, dict), "FROZEN_EVIDENCE_MUST_BE_OBJECT")
        results[key] = obj
    return results


def _original_rows(report: dict, field: str) -> dict:
    rows = report.get(field)
    _assert(isinstance(rows, list) and len(rows) == 45,
            "FROZEN_ORIGINAL45_POPULATION_COUNT_CHANGED")
    ids = [x.get("task_id") for x in rows if isinstance(x, dict)]
    _assert(len(ids) == 45 and len(set(ids)) == 45
            and all(isinstance(x, str) and TASK_RE.fullmatch(x) for x in ids),
            "FROZEN_ORIGINAL_TASK_ID_DUPLICATE_OR_INVALID")
    return {x["task_id"]: x for x in rows}


def _pinned_origins(all_reports: dict) -> None:
    a = all_reports
    _assert(a["v016"].get("pinned_original_author_sha256_git") == AUTHOR_SHA
            and a["v016"].get("pinned_original_public_data_sha256_git") == DATA_SHA,
            "FROZEN_V016_AUTHOR_DATA_SHA_DRIFT")
    _assert(a["v017_information"].get("original_author_sha") == AUTHOR_SHA
            and a["v017_information"].get("original_public_data_sha") == DATA_SHA,
            "FROZEN_V017_AUTHOR_DATA_SHA_DRIFT")
    _assert(a["v017_native"].get("original_author_git_sha") == AUTHOR_SHA
            and a["v017_native"].get("original_data_git_sha") == DATA_SHA,
            "FROZEN_NATIVE_V017_AUTHOR_DATA_SHA_DRIFT")
    _assert(a["v018"].get("pinned_original_author_git_sha") == AUTHOR_SHA
            and a["v018"].get("pinned_original_public_data_git_sha") == DATA_SHA,
            "FROZEN_V018_AUTHOR_DATA_SHA_DRIFT")
    _assert(a["v019"].get("original_author_git_sha") == AUTHOR_SHA
            and a["v019"].get("original_public_data_git_sha") == DATA_SHA,
            "FROZEN_V019_AUTHOR_DATA_SHA_DRIFT")


def build_original45_capability_gate(reports: dict) -> dict:
    """Pure auditable derivation; never silently infer unsupported/failure."""
    _assert(set(reports) == set(EVIDENCE), "EVIDENCE_VERSION_SET_MISMATCH")
    _pinned_origins(reports)
    r16 = reports["v016"]
    r17 = reports["v017_information"]
    r17n = reports["v017_native"]
    r18 = reports["v018"]
    r19 = reports["v019"]

    from_v16 = _original_rows(r16, "original45_intention_to_test_matrix")
    from_v17 = _original_rows(r17, "all_45_task_information_parity_audit")
    from_v17n = _original_rows(r17n, "all_45_public_intention_to_test")
    from_v18 = _original_rows(r18, "all_45_public_task_read_observation_audit")
    ids = set(from_v16)
    _assert(ids == set(from_v17) == set(from_v17n) == set(from_v18),
            "FROZEN_TASK_ID_SET_MISMATCH")
    _assert(len(ids) == 45 and r16["original_public_45_total_unchanged"] == 45
            and r18["original_original45_denominator"] == 45
            and r17n["original_public_45_denominator_unchanged"] == 45,
            "ORIGINAL45_DENOMINATOR_DRIFT")
    _assert(r17n["original_native_D0_I0_both_edit_cases_total"] == 5
            and r17n["original_author_scoreable_both_dev_arms_total"] == 3
            and r17n["original_author_reference_unscoreable_cases_total"] == 2
            and r17n["original_other_untested_same_protocol_total"] == 40,
            "FROZEN_NATIVE_WRITE_OR_SCORER_TOTAL_CHANGED")
    _assert(r18.get("common_read_observation_bytes_equal_across_45_tasks") is True
            and r18.get("common_read_observation_parity_case_count") == 45,
            "COMMON_READ_PARITY_NOT_ACTUALLY_PROVEN")
    _assert(r17["strict_full_original_source_information_parity_proven_case_count"] == 0,
            "FULL_INFORMATION_PARITY_BASELINE_CHANGED")
    _assert(r17.get("original_native_has_more_products_than_safe_typed_XML_case_count") == 45,
            "TYPED_XML_OMITTED_NATIVE_PRODUCTS_CASE_COUNT_DRIFT")
    _assert(r19.get("original_case") == "test_15"
            and r19.get("Docker_kernel_security_checked_count") == 14
            and r19.get("whole_original_ifc_native_identity_and_geometry_oracle_PASS") is True
            and r19["real_sealed_candidate_has_original_native_author_score"]["original_author_score"] == 1.0
            and r19.get("real_model_generated_python_executed") is False
            and r19.get("new_real_paid_or_unpaid_LLM_calls") == 0,
            "SEALED_DEVELOPER_ONLY_ORIGINAL_WITNESS_DRIFT")
    _assert(r19["previous_actual_developer_edit_D0_I0_native_parity"] == 5
            and r19["previous_original_author_scoreable_developer_edit_pairs"] == 3
            and r19["previous_original_author_scorer_reference_errors"] == 2,
            "SEALED_WITNESS_MUST_NOT_ADD_PAIRED_TASKS")

    expected_score = {
        "AUTHOR_SCORED_BOTH_DEVELOPER_ARMS": FROZEN_AUTHOR_SCORABLE,
        "AUTHOR_WORKER_FAILED_PINNED_REFERENCE_SOURCE_MISMATCH": FROZEN_AUTHOR_BLOCKED,
    }
    actual_write = {t for t, row in from_v17n.items()
                    if row.get("developer_source_only_both_D0_I0_native_feasibility") is True}
    _assert(actual_write == FROZEN_NATIVE_EQUAL, "NATIVE_EQUAL_DEVELOPER_SET_CHANGED")
    for status, expected_set in expected_score.items():
        seen = {t for t, row in from_v17n.items()
                if row.get("new_scoring_status") == status}
        _assert(seen == expected_set, "ORIGINAL_AUTHOR_SCORER_SET_DRIFT")
    _assert(all(row.get("new_scoring_status") in {
                    "AUTHOR_SCORED_BOTH_DEVELOPER_ARMS",
                    "AUTHOR_WORKER_FAILED_PINNED_REFERENCE_SOURCE_MISMATCH",
                    "NOT_CURRENTLY_ESTABLISHED",
                } for row in from_v17n.values()),
            "UNRECOGNIZED_AUTHOR_EVIDENCE_CLASS")

    rows = []
    for task_id in sorted(ids):
        v16, v17, v17n, v18 = (
            from_v16[task_id], from_v17[task_id],
            from_v17n[task_id], from_v18[task_id],
        )
        _assert(
            v16["crud"] == v17["crud"] == v17n["crud"] == v18["crud"]
            and v16["category"] == v17["category"] == v17n["category"] == v18["category"]
            and v16["original_ifc_source_sha256"] ==
                v17["original_public_ifc_sha256"] ==
                v17n["original_ifc_source_sha256"] ==
                v18["original_source_ifc_sha256"]
            and v16["public_question_sha256"] ==
                v17["original_public_question_sha256"] ==
                v17n["public_question_sha256"] ==
                v18["public_instruction_sha256"]
            and v16["original_ifc_schema"] == v17["original_schema"] ==
                v17n["original_ifc_schema"] == v18["actual_original_IFC_schema"],
            "FOUR_VERSION_ORIGINAL_PUBLIC_TASK_PROVENANCE_MISMATCH",
        )
        _assert(v17["native_original_ifc_product_count"] ==
                v18["actual_original_IfcProduct_inventory_count"]
                and v17["native_original_products_not_in_safe_typed_XML"] > 0
                and v17["safe_typed_XML_product_count"] >= 0
                and v17["native_original_ifc_product_count"] -
                v17["safe_typed_XML_product_count"] ==
                v17["native_original_products_not_in_safe_typed_XML"],
                "ORIGINAL_NATIVE_TYPED_XML_PRODUCT_CENSUS_MISMATCH")
        _assert(v18["shared_read_only_observation_replay"] == "PASS"
                and isinstance(v18["identical_D_I_read_calls"], int)
                and 0 < v18["identical_D_I_read_calls"] <= 25
                and bool(SHA_RE.fullmatch(v18["common_public_facts_packet_sha256"]))
                and bool(SHA_RE.fullmatch(v18["identical_D_I_read_transcript_sha256"])),
                "COMMON_READ_RECEIPT_INVALID")
        _assert(v18.get("real_matched_LLM_run_count") == 0
                and v17n.get("new_real_matched_LLM_D_I_result") is None
                and v17.get("real_matched_LLM_D_vs_I_attempt") is None,
                "FROZEN_REAL_LLM_TRIAL_CONTRADICTION")
        _assert(v16.get("original_public_requested_operation_family") ==
                v17n.get("original_public_requested_operation_family"),
                "PUBLIC_OPERATION_FAMILY_CHANGED")
        score = v17n["new_scoring_status"]
        equal = task_id in FROZEN_NATIVE_EQUAL
        scored = task_id in FROZEN_AUTHOR_SCORABLE
        blocked = task_id in FROZEN_AUTHOR_BLOCKED
        rows.append({
            "task_id": task_id,
            "original_category": v16["category"],
            "original_crud": v16["crud"],
            "public_operation_family": v16["original_public_requested_operation_family"],
            "pinned_original_public_instruction_sha256": v16["public_question_sha256"],
            "pinned_original_native_ifc_sha256": v16["original_ifc_source_sha256"],
            "pinned_original_ifc_schema": v16["original_ifc_schema"],
            "original_IfcProduct_count": v17["native_original_ifc_product_count"],
            "current_safe_typed_XML_product_count": v17["safe_typed_XML_product_count"],
            "original_native_products_omitted_from_typed_XML":
                v17["native_original_products_not_in_safe_typed_XML"],
            "relevance_of_omitted_products_to_task": "NOT_ESTABLISHED",
            "original_native_full_source_information_parity": "NOT_PROVEN",
            "actual_common_public_source_read_responses": "D_AND_I_IDENTICAL_FROZEN_QUERY_REPLAY",
            "actual_equal_source_read_call_count": v18["identical_D_I_read_calls"],
            "common_read_packet_sha256": v18["common_public_facts_packet_sha256"],
            "common_read_transcript_sha256": v18["identical_D_I_read_transcript_sha256"],
            "actual_developer_native_IFC_byte_equivalence":
                "PROVEN_ON_ORIGINAL_PUBLIC_TASK" if equal else "NOT_EVALUATED",
            "actual_original_author_scoring":
                "BOTH_ARMS_SCORED" if scored else
                "PINNED_AUTHOR_REFERENCE_SOURCE_MISMATCH" if blocked else
                "NOT_EVALUATED",
            "actual_author_scoring_diagnostic_source": score,
            "full_two_arm_native_write_capability_equivalence": "NOT_PROVEN",
            "sealed_own_developer_Python_execution":
                "ORIGINAL_PUBLIC_TEST15_SCORER_AND_NATIVE_ORACLE_PASS"
                if task_id == "test_15" else "NOT_TESTED",
            "real_matched_LLM_trial": "NOT_RUN",
            "original45_intention_to_test_denominator_member": True,
            "unsupported_task_inferred_from_missing_evidence": False,
            "failed_task_inferred_from_missing_evidence": False,
        })

    counts = Counter(row["original_crud"] for row in rows)
    scored = Counter(row["actual_original_author_scoring"] for row in rows)
    edits = Counter(row["actual_developer_native_IFC_byte_equivalence"] for row in rows)
    schemas = Counter(row["pinned_original_ifc_schema"] for row in rows)
    _assert(counts == Counter({"create": 15, "update": 15, "delete": 15}),
            "ORIGINAL_CRUD_DISTRIBUTION_DRIFT")
    _assert(scored == Counter({"BOTH_ARMS_SCORED":3,
                              "PINNED_AUTHOR_REFERENCE_SOURCE_MISMATCH":2,
                              "NOT_EVALUATED":40}),
            "ORIGINAL_AUTHOR_SCORABILITY_DISTRIBUTION_DRIFT")
    _assert(edits == Counter({"PROVEN_ON_ORIGINAL_PUBLIC_TASK":5,
                             "NOT_EVALUATED":40}),
            "ORIGINAL_DEVELOPER_NATIVE_WRITE_DISTRIBUTION_DRIFT")
    _assert(schemas == Counter({"IFC4X3":42, "IFC2X3":2, "IFC4":1}),
            "ORIGINAL_TASK_SCHEMA_DISTRIBUTION_DRIFT")

    blockers = [
        "D_TYPED_XML_OMITS_NATIVE_PRODUCTS_IN_ALL_ORIGINAL45_SOURCES",
        "FULL_ORIGINAL_SOURCE_SEMANTIC_AND_TASK_RELEVANT_INFORMATION_EQUIVALENCE_NOT_VERIFIED",
        "FULL_ORIGINAL_NATIVE_WRITE_CAPABILITY_PARITY_UNVERIFIED_ALL45",
        "SOURCE_ONLY_D_I_BYTE_IDENTICAL_READ_RESPONSES_DO_NOT_CERTIFY_SAME_NATIVE_WRITE_ACCESS",
        "PYTHON_NATIVE_IFC_INSPECTION_INSIDE_SEALED_EXECUTION_NOT_MATCHED_TO_XML_EDIT_STATE",
        "REAL_MODEL_TERMINAL_BROKER_NOT_INTEGRATED_OR_ATTESTED",
        "ALL_45_AUTHOR_EVALUATOR_REFERENCE_CONSISTENCY_NOT_PROVEN",
        "NO_EXPLICIT_APPROVED_MODEL_AND_PAID_PROVIDER_BUDGET",
        "NO_REAL_BLINDED_PAIRED_LLM_TRIALS",
    ]
    return {
        "status": "ORIGINAL45_EVIDENCE_CAPABILITY_MATRIX_PASS_CAUSAL_LLM_LAUNCH_BLOCKED",
        "issue": "https://github.com/pikaybh/bim-markup-bench/issues/154",
        "pinned_original_author_git_sha": AUTHOR_SHA,
        "pinned_original_public_data_git_sha": DATA_SHA,
        "frozen_predecessor_report_sha256": {key: value[1] for key, value in EVIDENCE.items()},
        "original_denominator_45_preserved": True,
        "original_15_per_crud": dict(sorted(counts.items())),
        "original_3_categories_15_per_category": dict(sorted(
            Counter(row["original_category"] for row in rows).items())),
        "original_schema_counts": dict(sorted(schemas.items())),
        "original45_with_incomplete_typed_native_product_observation": 45,
        "original45_with_IDENTICAL_common_source_read_replay": 45,
        "original45_WITH_PROVEN_FULL_IFC_INFORMATION_PARITY": 0,
        "original45_WITH_PROVEN_FULL_NATIVE_WRITE_CAPABILITY_PARITY": 0,
        "original45_developer_both_arm_native_IFC_byte_equivalence": 5,
        "original45_author_scorable_developer_both_arm": 3,
        "original45_original_author_scorer_mismatched_reference": 2,
        "original45_same_protocol_not_yet_evaluated": 40,
        "original45_developer_sealed_Python_native_edit_with_author_score": 1,
        "new_real_matched_LLM_D_I_trials": 0,
        "new_paid_provider_calls": 0,
        "new_paid_usd": 0,
        "all_rows_metric_origin": "FROZEN_NONBLINDED_DEVELOPER_CONTROL_AND_ORIGINAL_SOURCE_QUERY_AUDIT",
        "causal_XML_vs_Python_pure_representation_performance_claim_permitted": False,
        "any_paid_or_unpaid_real_LLM_launch_permitted": False,
        "explicit_blockers": blockers,
        "offline_terminal_one_shot_noninterference": offline_terminal_noninterference_audit(),
        "evidence_does_not_establish_absence_of_other_unexamined_features": True,
        "all45_original_public_task_capability_matrix": rows,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists() or a.output.is_symlink():
        p.error("Refuse to overwrite previous frozen evidence")
    evidence = load_frozen_evidence(a.root)
    result = build_original45_capability_gate(evidence)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x", encoding="utf8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    print("V020_MATRIX",result["status"])
    print("ORIGINAL45",len(result["all45_original_public_task_capability_matrix"]))
    print("FROZEN_D0_I0_EQ",result["original45_developer_both_arm_native_IFC_byte_equivalence"],
          "AUTHOR_SCORED",result["original45_author_scorable_developer_both_arm"])
    print("REAL_LLM",result["new_real_matched_LLM_D_I_trials"],
          "LAUNCH_ALLOWED",result["any_paid_or_unpaid_real_LLM_launch_permitted"])
    print("REPORT_SHA256",sha256(a.output.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
