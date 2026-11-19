"""Prospective offline original45 D/I prerequisite and developer-proof overlap audit.

All inputs are already frozen historical JSON. No real IFC, questions, hidden
answers, evaluator, model provider, Docker runtime or subprocess is accessed.
Necessary source-role/schema checks are NOT sufficient causal model eligibility.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from tools import audit_bibimbap_v030_reconcile as v030

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/pikaybh/bim-markup-bench/issues/177"
PARENT_COMMIT = "2f8ba78c6fc329ff2dc577a68c7b568b9f63f1c0"
BASE = v030.BASE
ROLES = v030.ROLES
RECONCILED = (
    "bibimbap_v030_original45_evidence_reconciliation_20261116.json",
    "4e14cce8dd0ee0c961d9b632345c559df7551c16fee073a89b7bc12df8a2b509",
)
ADMITTED = "SCHEMA_AND_UNIT_ADMISSIBLE_PROJECTION_WRITE_NOT_PROVEN"
REJECTED = "DIRECT_XML_SESSION_REJECTS_NON_IFC4X3"
TIERS = (
    "P0_XML_SOURCE_SCHEMA_REJECTION",
    "P1_NAMED_PUBLIC_SOURCE_PRODUCT_OMITTED",
    "P2_REQUIRED_SOURCE_ROLE_OMITTED",
    "P3_NONBLINDED_DEVELOPER_WITNESS_REVIEW",
    "P4_NO_DEVELOPER_NATIVE_PAIR_PROVEN",
)
EvidenceError = v030.EvidenceError


def require(value: bool, message: str) -> None:
    if not value:
        raise EvidenceError(message)


def unique_rows(value: object, field: str) -> dict:
    require(type(value) is list and len(value) == 45, f"{field}: expected 45 rows")
    ids = [r.get("task_id") for r in value if type(r) is dict]
    require(len(ids) == 45 and len(set(ids)) == 45 and all(
        type(x) is str and x for x in ids
    ), f"{field}: missing/duplicate or invalid task IDs")
    return {r["task_id"]: r for r in value}


def eligibility_report(root: Path = ROOT) -> dict:
    root = Path(root)
    # Load all historical v0.30 report ancestors and independently reproduce
    # the previous frozen reconciliation before trusting a single row.
    freshly_reconciled = v030.reconciled_report(root)
    reconstructed = v030.encoded_report(freshly_reconciled)
    frozen = v030.load_pinned(root, *RECONCILED)
    require(reconstructed == v030.encoded_report(frozen),
            "v0.30 frozen reconciliation differs from independent replay")
    base = v030.load_pinned(root, *BASE)
    roles = v030.load_pinned(root, *ROLES)
    b = unique_rows(base["all45_original_public_task_capability_matrix"], "v0.20")
    r = unique_rows(roles["all45_per_task_actual_source_role_and_admission_rows"], "v0.22")
    p = unique_rows(frozen["rows"], "v0.30")
    require(set(b) == set(r) == set(p), "Original 45 task membership drift")
    require(frozen["original45_ITT_denominator"] == 45
            and frozen["original45_full_IFC_information_parity_proven"] == 0
            and frozen["original45_full_native_write_capability_parity_proven"] == 0
            and frozen["original45_latest_protocol_actual_matched_LLM_trials"] == 0
            and frozen["causal_representation_only_XML_vs_Python_performance_claim_permitted"] is False,
            "v0.30 causal safety gate drift")
    require(roles["original45_current_XML_input_schema_or_unit_admission_rejects"] == 3
            and roles["original45_required_source_role_editable_XML_incomplete"] == 9
            and roles["original45_explicit_named_public_product_guids_missing_editable_XML_cases"] == 2
            and roles["original45_complete_original_IFC_semantic_information_equivalence_proven"] == 0
            and roles["original45_complete_native_write_capability_equivalence_proven"] == 0
            and roles["new_real_LLM_trials_or_scores"] == 0,
            "v0.22 source audit causal counts drift")
    require(base["original45_with_IDENTICAL_common_source_read_replay"] == 45
            and base["original45_WITH_PROVEN_FULL_IFC_INFORMATION_PARITY"] == 0
            and base["original45_WITH_PROVEN_FULL_NATIVE_WRITE_CAPABILITY_PARITY"] == 0
            and base["new_real_matched_LLM_D_I_trials"] == 0,
            "v0.20 common read or causal gate drift")

    output = []
    for task in sorted(b):
        bb, rr, pp = b[task], r[task], p[task]
        require(rr["original_category"] == bb["original_category"] == pp["original_category"]
                and rr["original_crud"] == bb["original_crud"] == pp["original_crud"],
                f"Category or CRUD drift: {task}")
        require(rr["original_native_IFC_sha256"] == bb["pinned_original_native_ifc_sha256"]
                and rr["original_public_question_sha256"] == bb["pinned_original_public_instruction_sha256"],
                f"Public IFC/question provenance drift: {task}")
        require(rr["original_ifc_schema"] == bb["pinned_original_ifc_schema"]
                and rr["public_operation_family"] == bb["public_operation_family"],
                f"Original IFC schema or operation drift: {task}")
        require(rr["actual_original_IfcProduct_count"] == bb["original_IfcProduct_count"]
                and rr["native_IfcProducts_outside_editable_typed_XML"]
                == bb["original_native_products_omitted_from_typed_XML"]
                and rr["previously_oracle_verified_editable_typed_XML_product_count"]
                == bb["current_safe_typed_XML_product_count"],
                f"Native/typed product count drift: {task}")
        require(rr["actual_native_IFC_source_read_only_verified"] is True
                and rr["explicit_public_named_guids_missing_original_source"] == 0
                and rr["full_D_I_native_write_capability_equivalence"] == "NOT_PROVEN"
                and rr["full_task_relevant_geometry_topology_metadata_equivalence"] == "NOT_PROVEN"
                and rr["actual_LLM_result"] == "NOT_RUN"
                and rr["no_unsupported_or_failure_inferred_from_untested_case"] is True,
                f"Unverified source/parity or model-result claim: {task}")
        require(pp["source_information_parity"] == "NOT_PROVEN"
                and pp["full_native_write_capability_parity"] == "NOT_PROVEN"
                and pp["actual_matched_D_I_LLM_result"] == "NOT_RUN",
                f"Unsound native/LLM status promotion: {task}")
        missing_roles = rr["required_roles_with_missing_editable_XML_objects"]
        required = rr["required_public_source_roles"]
        counts = rr["required_role_visibility_counts"]
        require(type(required) is list and all(type(z) is str for z in required)
                and type(missing_roles) is list and set(missing_roles).issubset(set(required))
                and len(missing_roles) == len(set(missing_roles))
                and type(counts) is dict and set(counts) == set(required),
                f"Malformed original required-role inventory: {task}")
        for role in required:
            c = counts[role]
            require(all(type(c.get(k)) is int and c[k] >= 0 for k in (
                "actual_original_native_count",
                "existing_frozen_editable_typed_XML_count",
                "required_role_missing_editable_IfcProducts_count"
            )) and c["actual_original_native_count"]
                == c["existing_frozen_editable_typed_XML_count"]
                + c["required_role_missing_editable_IfcProducts_count"],
                f"Required native role accounting drift: {task}:{role}")
            require((role in missing_roles)
                    == (c["required_role_missing_editable_IfcProducts_count"] > 0),
                    f"Missing required role label drift: {task}:{role}")
        named = rr["explicit_public_named_guids_missing_editable_XML"]
        require(type(named) is int and 0 <= named <= rr["explicit_public_named_guids_count"],
                f"Malformed named public GUID counts: {task}")
        require(rr["all_required_roles_and_explicit_refs_present_editable_XML"]
                is (not missing_roles and named == 0),
                f"Role/ref necessary-check drift: {task}")
        admitted = rr["current_direct_XML_session_source_admission"] == ADMITTED
        require(rr["current_direct_XML_session_source_admission"] in (ADMITTED, REJECTED)
                and admitted == (rr["original_ifc_schema"] == "IFC4X3"),
                f"Original IFC schema/typed XML admission mismatch: {task}")
        witnessed = pp["developer_native_D0_I0_bytes_equal_proven"]
        require(type(witnessed) is bool
                and (pp["developer_author_scorer_status"] in (
                    "AUTHOR_SCORED_DEVELOPER_CONTROL",
                    "AUTHOR_REFERENCE_SOURCE_MISMATCH")
                    if witnessed else
                    pp["developer_author_scorer_status"] == "NOT_EVALUATED_UNDETERMINED"),
                f"Developer/scorer evidence drift: {task}")
        if not admitted:
            tier = TIERS[0]
        elif named:
            tier = TIERS[1]
        elif missing_roles:
            tier = TIERS[2]
        elif witnessed:
            tier = TIERS[3]
        else:
            tier = TIERS[4]
        output.append({
            "task_id": task,
            "original_category": bb["original_category"],
            "original_crud": bb["original_crud"],
            "original_ifc_schema": rr["original_ifc_schema"],
            "public_edit_operation_family": rr["public_operation_family"],
            "required_public_source_roles_missing_editable_XML": sorted(missing_roles),
            "named_public_source_products_missing_editable_XML_count": named,
            "XML_schema_and_unit_admission_necessary_check": "PASS_NOT_WRITE_PROOF" if admitted else "REJECTS_INPUT",
            "developer_original_native_D0_I0_byte_equal_witness": witnessed,
            "original_author_grader_developer_witness_status": pp["developer_author_scorer_status"],
            "audit_priority_tier": tier,
            "task_relevant_complete_read_information_parity_proven": False,
            "task_relevant_native_write_capability_parity_proven": False,
            "eligible_for_matched_causal_LLM_trial": False,
            "actual_matched_LLM_outcome": "NOT_RUN",
            "missing_witness_may_be_counted_as_failure": False,
        })

    tally = Counter(x["audit_priority_tier"] for x in output)
    crud_witness = Counter(x["original_crud"] for x in output
                           if x["developer_original_native_D0_I0_byte_equal_witness"])
    gap_witness = [
        x["task_id"] for x in output
        if x["developer_original_native_D0_I0_byte_equal_witness"]
        and x["required_public_source_roles_missing_editable_XML"]
    ]
    simple_pass = sum(x["audit_priority_tier"] in TIERS[3:] for x in output)
    require(len(output) == 45 and simple_pass == 33
            and tally == {TIERS[0]: 3, TIERS[1]: 2, TIERS[2]: 7,
                          TIERS[3]: 8, TIERS[4]: 25}
            and len(gap_witness) == 3
            and set(gap_witness) == {"geometry_test_18", "geometry_test_19", "test_20"}
            and crud_witness == {"update": 4, "delete": 7},
            "Prospective v0.31 overlap classification/count invariant drift")
    require(Counter(x["original_crud"] for x in output)
            == {"create": 15, "update": 15, "delete": 15}
            and Counter(x["original_category"] for x in output)
            == {"basic": 15, "geometry": 15, "topological": 15},
            "Original 45 population drift")
    require(sum(x["developer_original_native_D0_I0_byte_equal_witness"]
                for x in output) == 11, "Developer evidence denominator drift")
    return {
        "status": "V031_ORIGINAL45_NECESSARY_GAPS_AND_NONBLINDED_WITNESSES_RECONCILED_NO_LLM_LAUNCH",
        "issue": ISSUE,
        "parent_commit": PARENT_COMMIT,
        "origin": "OFFLINE_FROZEN_REPORT_INTERSECTION_NOT_NEW_NATIVE_REEXECUTION_OR_CAUSAL_ESTIMATE",
        "frozen_inputs_sha256": {
            BASE[0]: BASE[1], ROLES[0]: ROLES[1], RECONCILED[0]: RECONCILED[1],
            **{x[0]: x[1] for x in v030.NEW_CASES},
        },
        "original_intention_to_test_task_count": 45,
        "coarse_necessary_source_role_ref_and_schema_checks_passed_not_sufficient": simple_pass,
        "full_task_relevant_source_information_equivalence_proven": 0,
        "full_task_relevant_native_edit_capability_equivalence_proven": 0,
        "matched_LLM_trial_eligible_tasks": 0,
        "matched_D_I_LLM_trials_executed": 0,
        "declarative_XML_task_specific_schema_rejections": tally[TIERS[0]],
        "named_public_source_object_absence_tasks": tally[TIERS[1]],
        "missing_required_editable_source_role_other_tasks": tally[TIERS[2]],
        "developer_witnesses_after_necessary_checks": tally[TIERS[3]],
        "necessary_checks_passed_without_developer_witness": tally[TIERS[4]],
        "original45_any_required_role_gap_total": 9,
        "original45_developer_native_equal_witnesses": 11,
        "original45_developer_witnesses_despite_required_role_gap": len(gap_witness),
        "original45_developer_witness_and_role_gap_task_ids": sorted(gap_witness),
        "original45_create_task_developer_native_equal_witnesses": crud_witness.get("create", 0),
        "original45_update_task_developer_native_equal_witnesses": crud_witness["update"],
        "original45_delete_task_developer_native_equal_witnesses": crud_witness["delete"],
        "original45_author_callable_developer_witnesses": 9,
        "original45_original_author_reference_source_mismatch_witnesses": 2,
        "prioritization_is_diagnostic_not_score_or_success_based": True,
        "nonblinded_developer_witnesses_are_not_randomized_LLM_outcomes": True,
        "all_45_including_unproven_or_unsupported_must_remain_in_ITT": True,
        "new_paid_model_calls_or_original_IFC_modifications": 0,
        "ordered_offline_audit_queue": [
            {"tier": tier, "task_ids": [x["task_id"] for x in output
                                       if x["audit_priority_tier"] == tier]}
            for tier in TIERS
        ],
        "rows": output,
    }


def encoded_report(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)
            + "\n").encode("utf8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", type=Path, help="Compare previously frozen output only")
    parser.add_argument("--write", type=Path, help="Write new report exclusively, no overwrite")
    args = parser.parse_args()
    require(not (args.check and args.write), "Choose at most one output action")
    data = encoded_report(eligibility_report(args.root))
    if args.check:
        require(args.check.is_file() and not args.check.is_symlink()
                and args.check.read_bytes() == data,
                "Published report differs from deterministic recomputation")
        print("EXACT_MATCH " + sha256(data).hexdigest())
    elif args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        with args.write.open("xb") as file:
            file.write(data)
        print("WRITTEN " + str(args.write) + " " + sha256(data).hexdigest())
    else:
        print("SHA256 " + sha256(data).hexdigest())
        print("45 original tasks, 33 necessary checks pass, 0 causal-ready")
        print("queue tiers: " + str(Counter(x["audit_priority_tier"]
                                              for x in eligibility_report(args.root)["rows"])))


if __name__ == "__main__":
    main()
