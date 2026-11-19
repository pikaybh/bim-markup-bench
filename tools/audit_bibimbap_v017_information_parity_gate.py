"""Research v0.17 public 45-case strict D-vs-I *input information* parity gate.

Read ONLY the earlier frozen original native-source census and the new v017
paired developer audit; never invoke model, grader, source mutation, or reveal
hidden author targets. 45 original tasks remain in the denominator. "BLOCK"
means NOT scientifically ready for a strict full-original-source information
parity claim; it does not imply a task is impossible or a model score of zero.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash


class MatchedInformationGateError(ValueError):
    pass


FROZEN_V013_SHA = "67b58b9b55d24d48ae644200e0ac9501b255ed4a346aa4add2036438cad3e9f5"


def audit(author: Path, data: Path, frozen_v013: Path,
          current_v017: Path) -> dict:
    if _head(author) != AUTHOR_SHA or _head(data) != DATA_SHA:
        raise MatchedInformationGateError("Original author or public data Git SHA drift")
    if file_hash(frozen_v013).lower() != FROZEN_V013_SHA:
        raise MatchedInformationGateError("Frozen original native source inventory changed")
    source_catalog = json.loads(frozen_v013.read_text(encoding="utf8"))
    current = json.loads(current_v017.read_text(encoding="utf8"))
    public = {x["test_id"]: x for x in public_45(author, data)}
    v013 = {x["original_public_task_id"]: x for x in
            source_catalog["original45_task_readonly_vs_native_write_status"]}
    v017 = {x["task_id"]: x for x in
            current["all_45_public_intention_to_test"]}
    if (len(public) != 45 or len(v013) != 45 or len(v017) != 45
        or not (set(public) == set(v013) == set(v017))):
        raise MatchedInformationGateError("Original all-45 population drift")
    if current["original_public_45_denominator_unchanged"] != 45:
        raise MatchedInformationGateError("Prior paired auditor changed original denominator")
    items = []
    for task_id in sorted(public):
        t = public[task_id]
        old, current_row = v013[task_id], v017[task_id]
        if (old["original_public_IFC_sha256"] != t["original_ifc_sha256"] or
            old["original_public_question_sha256"] != t["public_question_sha256"] or
            current_row["original_ifc_source_sha256"] != t["original_ifc_sha256"]):
            raise MatchedInformationGateError("Original task public source or question changed")
        native_count = old["v013_original_native_source_product_count"]
        typed_count = old["v013_source_safe_typed_XML_product_count"]
        if not (isinstance(native_count, int) and isinstance(typed_count, int)
                and 0 <= typed_count <= native_count):
            raise MatchedInformationGateError("Inconsistent native source/typed view product census")
        missing = native_count - typed_count
        # Counted by independent source scan, not inferred from intended
        # edits or scorer labels. Full original product visibility is necessary,
        # not sufficient, for full IFC information equivalence.
        strict_gate = (
            "BLOCKED_CONCRETE_MISSING_NATIVE_PRODUCTS_IN_TYPED_XML"
            if missing else "NOT_PROVEN_RELATIONSHIPS_GEOMETRY_METADATA"
        )
        # Source-role visibility does NOT imply all original source objects,
        # inverse links, geometry, editing operations or model tool parity.
        role_reference_gate = bool(old["v013_safe_typed_source_role_and_reference_gate"])
        items.append({
            "task_id": task_id,
            "crud": t["crud"],
            "category": t["category"],
            "original_public_question_sha256": t["public_question_sha256"],
            "original_public_ifc_sha256": t["original_ifc_sha256"],
            "original_schema": old["original_native_schema"],
            "native_original_ifc_product_count": native_count,
            "safe_typed_XML_product_count": typed_count,
            "native_original_products_not_in_safe_typed_XML": missing,
            "required_role_and_public_reference_visibility_gate": role_reference_gate,
            "full_original_IFC_source_information_equivalence": strict_gate,
            "source_view_parity_is_not_the_same_as_native_backend_write_parity": True,
            "previous_developer_D0_I0_author_scoreability":
                current_row["new_scoring_status"],
            "full_45_population_membership": True,
            "real_matched_LLM_D_vs_I_attempt": None,
            "eligible_for_strict_full_original_information_equivalent_paid_trial": False,
        })
    blocked_count = sum(x["native_original_products_not_in_safe_typed_XML"] > 0 for x in items)
    unknown_metadata_count = len(items) - blocked_count
    grades = Counter(x["previous_developer_D0_I0_author_scoreability"] for x in items)
    if grades != Counter({
        "AUTHOR_SCORED_BOTH_DEVELOPER_ARMS": 3,
        "AUTHOR_WORKER_FAILED_PINNED_REFERENCE_SOURCE_MISMATCH": 2,
        "NOT_CURRENTLY_ESTABLISHED": 40,
    }):
        raise MatchedInformationGateError("Prior developer-source parity cases drifted")
    if blocked_count + unknown_metadata_count != 45:
        raise MatchedInformationGateError("Cohort classification lost original tasks")
    return {
        "status": "STRICT_FULL_ORIGINAL_IFC_INFORMATION_PARITY_GATE_BLOCKED",
        "issue": "https://github.com/pikaybh/bim-markup-bench/issues/148",
        "original_author_sha": AUTHOR_SHA,
        "original_public_data_sha": DATA_SHA,
        "prior_frozen_original_native_catalog_sha256": FROZEN_V013_SHA,
        "prior_v017_report_sha256": file_hash(current_v017),
        "actual_original_public_task_count": 45,
        "source_unique_original_IFC_count":
            source_catalog["original_native_unique_IFC_source_count"],
        "paired_arms": [
            {
                "arm": "D",
                "authoring_interface": "COMPLETE_DECLARATIVE_XML_TYPED_STATE",
                "source_information": "TASK_SPECIFIC_TYPED_XML_PROJECTION_OF_ORIGINAL_NATIVE_IFC",
                "native_compiler": "TRUSTED_SOURCE_IFC_CLONE_DIFF_COMPILER",
                "no_python_mutation_allowed_in_LLM": True,
            },
            {
                "arm": "I",
                "authoring_interface": "IMPERATIVE_PYTHON_IFCOPENSHELL",
                "source_information": "FULL_ORIGINAL_NATIVE_IFC_AND_PYTHON_INSPECTION",
                "native_compiler": "NATIVE_IFCOPENSHELL_DIRECT_MUTATION",
                "python_can_inspect_more_IfcProducts_than_XML_safe_typed_view": True,
            },
        ],
        "original_native_has_more_products_than_safe_typed_XML_case_count": blocked_count,
        "source_typed_view_matches_native_product_count_but_other_IFC_semantics_unproven":
            unknown_metadata_count,
        "strict_full_original_source_information_parity_proven_case_count": 0,
        "relevance_of_omitted_products_to_specific_task_NOT_proven": True,
        "absence_of_all_unnecessary_info_NOT_proven": True,
        "typed_XML_exposes_all_required_source_roles_does_not_prove_equal_source": True,
        "new_real_matched_model_inference_calls": 0,
        "new_paid_provider_calls": 0,
        "new_paid_usd": 0,
        "matched_LLM_trial_paid_execution_authorized": False,
        "research_only_explicit_no_launch_enforcement": True,
        "required_before_any_future_causal_claim": [
            "CHOOSE_AND_PREREGISTER_NATIVE_FULL_SOURCE_VS_TYPED_SOURCE_COMPARISON_AS_UNEQUAL_INFORMATION_IF_RETAINED",
            "OR_ESTABLISH_AND_MEASURE_SAME_SEMANTIC_INFORMATION_READ_FACILITY_FOR_BOTH_LLM_ARMS",
            "EXACT_SAME_PUBLIC_TASK_INPUT_AND_ORIGINAL_IFC_SOURCE_HASH_PER_TASK",
            "PREREGISTER_REPRESENTATION_EQUIVALENCE_SEPARATELY_FROM_BACKEND_CAPABILITY_EQUIVALENCE",
            "CONTROL_MODEL_SNAPSHOT_TEMPERATURE_REASONING_SEED_WHERE_SUPPORTED",
            "CONTROL_TOOL_CALL_CAP_25_TIMEOUT_RETRIES_OUTPUT_TOKEN_BUDGET_SAME_TASK_ORDER",
            "PRESERVE_UNSUPPORTED_AND_FAILED_CASES_IN_ALL45_INTENTION_TO_TEST",
            "HIDE_ORIGINAL_AUTHOR_TARGETS_AND_SCORER_CODE_UNTIL_BOTH_CANDIDATES_FROZEN",
            "PAIR_INDEPENDENT_NATIVE_IFC_ORACLE_WITH_PINNED_UNMODIFIED_AUTHOR_SCORER",
            "PREREGISTER_ORIGINAL_AUTHOR_SCORER_UNSCOREABLE_CASE_POLICY_WITHOUT_PATCHING_GT",
            "STORE_MODEL_PROVIDER_REQUEST_OUTPUT_HASHES_AND_TOKEN_COST_ACCOUNTING",
            "NEW_EXPLICIT_OWNER_PAID_EXPERIMENT_APPROVAL_REQUIRED",
        ],
        "all_45_task_information_parity_audit": items,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--author", type=Path, required=True)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--frozen-v013", type=Path, required=True)
    p.add_argument("--v017", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists() or a.output.is_symlink():
        p.error("Refusing to overwrite previous result")
    result = audit(a.author, a.data, a.frozen_v013, a.v017)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x", encoding="utf8", newline="\n") as file:
        json.dump(result, file, ensure_ascii=False, sort_keys=True, indent=2)
        file.write("\n")
    print("status:", result["status"])
    print("native product count differs for",
          result["original_native_has_more_products_than_safe_typed_XML_case_count"],
          "of 45 original tasks")
    print("report_sha256:", file_hash(a.output))


if __name__ == "__main__":
    main()
