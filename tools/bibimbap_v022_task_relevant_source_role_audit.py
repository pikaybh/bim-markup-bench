"""v0.22 original-public BIBIMBAP all45 task-relevant source-role visibility.

Independently opens *actual pinned original IFC files* read-only, cross-checks
all 31 native IfcProduct GUID/class maps with the frozen independent v0.13
source/typed catalog, and binds PUBLIC instructions to exact named GUIDs and
the previously frozen PUBLIC-only required role/operation classification.

Does NOT infer complete editability, native write equivalence, semantic
task failure, model performance, or an evaluator score. "Role incomplete"
means the current editable typed XML projection omits some original products
of the public instruction's required reference class. It is not proof the
specific omitted product is necessary or the task is impossible.

No original IFC writes, source-file normalization, scorer, GT, model or Docker.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import argparse
import json
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.unit

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.audit_bibimbap_v12_real45_capability_matrix import (
    REQUIREMENTS, SOURCE_GUID_PATTERN, _type_role,
)
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash

ROOT = Path(__file__).resolve().parents[1]
FROZEN_V013 = (
    "reports/bibimbap_v013_original45_safe_native_read_catalog_20261114.json",
    "67b58b9b55d24d48ae644200e0ac9501b255ed4a346aa4add2036438cad3e9f5",
)
FROZEN_V020 = (
    "reports/bibimbap_v020_original45_capability_and_terminal_gate_20261115.json",
    "1aa218a0883186e6df1e7e7d895670fb9e012ef0229799b14881a87473f762be",
)
FROZEN_V021 = (
    "reports/bibimbap_v021_scoped_regression_and_recovery_20261115.json",
    "15a5af2cac9e2024c54fb9a79b2f46b51630ad9714e256487580090dbf0ccf11",
)


class PublicRoleAuditBlocked(ValueError):
    """Do not permit source/typed catalog/author evidence drift."""


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise PublicRoleAuditBlocked(msg)


def read_frozen_json(root: Path, frozen: tuple[str, str]) -> dict:
    rel, hash_expected = frozen
    p = root / rel
    require(p.is_file() and not p.is_symlink(), "FROZEN_REPORT_MISSING")
    require(file_hash(p) == hash_expected, "FROZEN_REPORT_SHA256_CHANGED")
    obj = json.loads(p.read_text(encoding="utf8"))
    require(isinstance(obj, dict), "FROZEN_REPORT_MUST_BE_OBJECT")
    return obj


def source_native_product_maps(public: list[dict], data: Path, frozen_v013: dict) -> dict:
    """Read each of the 31 source IFCs exactly once, no editing or output IFC."""
    existing = frozen_v013["original_native_IFC_unique_source_read_evidence"]
    require(isinstance(existing, dict) and len(existing) == 31,
            "FROZEN_ORIGINAL_31_SOURCE_CATALOG_CHANGED")
    by_sha: dict[str, dict] = {}
    for task in public:
        digest = task["original_ifc_sha256"]
        if digest in by_sha:
            continue
        orig = data / "ifc" / task["original_source_ifc_relpath"]
        require(orig.is_file() and not orig.is_symlink() and file_hash(orig) == digest,
                "ORIGINAL_PUBLIC_IFC_SHA_DRIFT")
        source = ifcopenshell.open(str(orig))
        require(source.schema in ("IFC4X3", "IFC4", "IFC2X3"),
                "ORIGINAL_PUBLIC_IFC_SCHEMA_INVALID")
        products = source.by_type("IfcProduct")
        actual = {}
        for entity in products:
            guid = getattr(entity, "GlobalId", None)
            require(isinstance(guid, str) and guid not in actual
                    and len(guid) == 22,
                    "ORIGINAL_NATIVE_IFCPRODUCT_GUID_INVALID_OR_DUPLICATED")
            actual[guid] = entity.is_a()
        require(digest in existing, "ORIGINAL_PUBLIC_NATIVE_SOURCE_CATALOG_MISSING")
        old = existing[digest]
        require(old["actual_original_source_native_read_status"] ==
                "READ_ONLY_SOURCE_AND_INDEPENDENT_NATIVE_CATALOG_ORACLE_PASS",
                "FROZEN_NATIVE_SOURCE_ORACLE_NOT_VERIFIED")
        require(actual == old["original_native_product_class_by_guid"]
                and len(actual) == old["original_native_product_count"],
                "ACTUAL_ORIGINAL_NATIVE_IFC_PRODUCT_CATALOG_DISAGREES_WITH_V013")
        typed = old["source_native_original_product_typed_XML_class_by_guid"]
        omitted = old["original_product_guids_readonly_catalog_only"]
        require(set(typed).isdisjoint(omitted) and set(typed) | set(omitted) == set(actual),
                "ORIGINAL_TYPED_AND_OPAQUE_PARTITION_INCOMPLETE")
        require({x:actual[x] for x in typed} == typed
                and {x:actual[x] for x in omitted} == omitted,
                "FROZEN_EDITABLE_TYPED_XML_ENTITY_CLASS_NOT_IN_ORIGINAL")
        scale = float(ifcopenshell.util.unit.calculate_unit_scale(source))
        require(math.isfinite(scale) and scale > 0,
                "ORIGINAL_NATIVE_IFC_LENGTH_UNIT_INVALID")
        require(source.schema == old["original_native_ifc_schema"],
                "FROZEN_SOURCE_SCHEMA_NOT_MATCHING_ORIGINAL")
        require(file_hash(orig) == digest, "ORIGINAL_SOURCE_CHANGED_DURING_READ")
        by_sha[digest] = {
            "original_ifc_schema": source.schema,
            "original_length_unit_to_m": round(scale, 12),
            "all_actual_native_source": actual,
            "frozen_typed_XML_subset": typed,
            "frozen_opaque_readonly_subset": omitted,
        }
    require(len(by_sha) == 31 and set(by_sha) == set(existing),
            "ORIGINAL_PUBLIC_31_UNIQUE_SOURCE_SET_CHANGED")
    return by_sha


def classify_original45(public: list[dict], native_sources: dict,
                        frozen_v013: dict, frozen_v020: dict,
                        frozen_v021: dict) -> dict:
    require(len(public) == 45 and len(REQUIREMENTS) == 45,
            "ORIGINAL_PUBLIC_45_OR_REQUIREMENTS_POPULATION_DRIFT")
    task_map = {x["test_id"]: x for x in public}
    require(len(task_map) == 45 and set(task_map) == set(REQUIREMENTS),
            "ORIGINAL_PUBLIC_TASK_IDS_MISSING_DUPLICATE_OR_FORGED")
    old_rows = frozen_v013["original45_task_readonly_vs_native_write_status"]
    source_map = frozen_v013["original_native_IFC_unique_source_read_evidence"]
    v20_rows = frozen_v020["all45_original_public_task_capability_matrix"]
    v013_rows = {x["original_public_task_id"]: x for x in old_rows}
    v020_rows = {x["task_id"]: x for x in v20_rows}
    require(len(old_rows) == 45 and len(v20_rows) == 45
            and len(v013_rows) == 45 and len(v020_rows) == 45
            and set(v013_rows) == set(task_map) == set(v020_rows),
            "FROZEN_TASK_MATRIX_ID_SET_CHANGED")
    require(frozen_v013.get("pinned_original_author_revision") == AUTHOR_SHA
            and frozen_v013.get("pinned_original_public_data_revision") == DATA_SHA
            and frozen_v013.get("original_public_45_denominator") == 45,
            "V013_SOURCE_COHORT_PROVENANCE_CHANGED")
    require(frozen_v020.get("pinned_original_author_git_sha") == AUTHOR_SHA
            and frozen_v020.get("pinned_original_public_data_git_sha") == DATA_SHA
            and frozen_v020.get("original45_developer_both_arm_native_IFC_byte_equivalence") == 5
            and frozen_v020.get("original45_author_scorable_developer_both_arm") == 3
            and frozen_v020.get("original45_original_author_scorer_mismatched_reference") == 2
            and frozen_v020.get("original45_same_protocol_not_yet_evaluated") == 40,
            "V020_FROZEN_SCORER_OR_DEVELOPER_EVIDENCE_DRIFT")
    require(frozen_v021.get("actual_regression_tests_run") == 162
            and frozen_v021.get("actual_regression_process_exit_code") == 0
            and frozen_v021.get("new_real_LLM_trial_calls") == 0,
            "V021_FROZEN_HOST_REPLAY_DRIFT")

    rows = []
    for task_id in sorted(task_map):
        task = task_map[task_id]
        previous, old = v013_rows[task_id], v020_rows[task_id]
        native = native_sources[task["original_ifc_sha256"]]
        all_products = native["all_actual_native_source"]
        typed = native["frozen_typed_XML_subset"]
        schema = native["original_ifc_schema"]
        scale = native["original_length_unit_to_m"]
        required_roles, operation = REQUIREMENTS[task_id]
        require(previous["original_public_IFC_sha256"] ==
                old["pinned_original_native_ifc_sha256"] ==
                task["original_ifc_sha256"]
                and previous["original_public_question_sha256"] ==
                old["pinned_original_public_instruction_sha256"] ==
                task["public_question_sha256"]
                and previous["original_native_schema"] ==
                old["pinned_original_ifc_schema"] == schema
                and previous["original_public_operation_family_required"] ==
                old["public_operation_family"] == operation,
                "ORIGINAL_PUBLIC_TASK_CROSS_VERSION_PROVENANCE_CHANGED")
        require(previous["v013_original_native_source_product_count"] ==
                old["original_IfcProduct_count"] == len(all_products)
                and previous["v013_source_safe_typed_XML_product_count"] ==
                old["current_safe_typed_XML_product_count"] == len(typed),
                "ORIGINAL_EDITABLE_TYPED_XML_COUNTS_DRIFT")
        require(previous["v013_original_required_source_roles"] == list(required_roles),
                "PUBLIC_REQUIRED_SOURCE_ROLE_LIST_DRIFT")
        public_guids = set(SOURCE_GUID_PATTERN.findall(task["public_question"]))
        frozen_public = set(previous["v013_original_public_named_reference_GUIDs"])
        require(public_guids == frozen_public,
                "ORIGINAL_PUBLIC_NAMED_GUID_INSTRUCTION_PARSE_DRIFT")
        absent_native = public_guids - set(all_products)
        absent_typed = (public_guids & set(all_products)) - set(typed)
        require(absent_native == set(previous["v013_named_public_refs_absent_original_IFC"])
                and absent_typed ==
                set(previous["v013_named_public_refs_excluded_safe_typed_XML"]),
                "ORIGINAL_PUBLIC_NAMED_GUID_NATIVE_TYPED_VISIBILITY_DRIFT")
        native_counts = Counter(_type_role(x) for x in all_products.values())
        typed_counts = Counter(_type_role(x) for x in typed.values())
        missing_roles = []
        role_summary = {}
        for role in required_roles:
            src_count = native_counts[role]
            typed_count = typed_counts[role]
            previous_role = previous["v013_original_role_readonly_vs_typed_coverage"][role]
            require(src_count == previous_role["original_native_IFC_count"]
                    and typed_count == previous_role["safe_typed_XML_existing_count"]
                    and src_count >= typed_count,
                    "ORIGINAL_TASK_ROLE_ACTUAL_IFC_TO_XML_COUNTS_DRIFT")
            role_summary[role] = {
                "actual_original_native_count": src_count,
                "existing_frozen_editable_typed_XML_count": typed_count,
                "required_role_missing_editable_IfcProducts_count":
                    src_count - typed_count,
            }
            if src_count > typed_count:
                missing_roles.append(role)
        actual_role_gate = not missing_roles and not absent_native and not absent_typed
        require(actual_role_gate == previous["v013_safe_typed_source_role_and_reference_gate"],
                "ORIGINAL_FROZEN_REQUIRED_ROLE_AND_GUID_GATE_NOT_REPRODUCED")
        schema_admissible = schema == "IFC4X3"
        length_admissible = abs(scale - .001) < 1e-12
        # Exact v0.21-current XmlSourceEditSession checks schema and mm
        # BEFORE any source conversion/authoring. This only proves input
        # admission, not successful projection or writable geometry.
        xml_input = (
            "DIRECT_XML_SESSION_REJECTS_NON_IFC4X3"
            if not schema_admissible
            else "DIRECT_XML_SESSION_REJECTS_NON_MILLIMETRE_SOURCE"
            if not length_admissible
            else "SCHEMA_AND_UNIT_ADMISSIBLE_PROJECTION_WRITE_NOT_PROVEN"
        )
        row = {
            "task_id": task_id,
            "original_category": old["original_category"],
            "original_crud": old["original_crud"],
            "public_operation_family": operation,
            "original_public_question_sha256": task["public_question_sha256"],
            "original_native_IFC_sha256": task["original_ifc_sha256"],
            "original_ifc_schema": schema,
            "actual_original_native_length_unit_to_m": scale,
            "actual_original_IfcProduct_count": len(all_products),
            "previously_oracle_verified_editable_typed_XML_product_count": len(typed),
            "native_IfcProducts_outside_editable_typed_XML": len(all_products)-len(typed),
            "explicit_public_named_guids_count": len(public_guids),
            "explicit_public_named_guids_missing_original_source": len(absent_native),
            "explicit_public_named_guids_missing_editable_XML": len(absent_typed),
            "required_public_source_roles": list(required_roles),
            "required_role_visibility_counts": role_summary,
            "required_roles_with_missing_editable_XML_objects": sorted(missing_roles),
            "all_required_roles_and_explicit_refs_present_editable_XML":
                actual_role_gate,
            "current_direct_XML_session_source_admission": xml_input,
            "actual_native_IFC_source_read_only_verified": True,
            "typed_XML_subset_from_pinned_v013_independent_oracle_not_reprojected_here": True,
            "current_D_and_I_common_fact_query_replay": "PREVIOUSLY_VERIFIED_45_45_NOT_COMPLETE_IFC_INFO",
            "previously_developer_proven_D0_I0_native_bytes_equal":
                old["actual_developer_native_IFC_byte_equivalence"] ==
                "PROVEN_ON_ORIGINAL_PUBLIC_TASK",
            "previous_original_author_scoring": old["actual_original_author_scoring"],
            "full_task_relevant_geometry_topology_metadata_equivalence": "NOT_PROVEN",
            "full_D_I_native_write_capability_equivalence": "NOT_PROVEN",
            "actual_LLM_result": "NOT_RUN",
            "no_unsupported_or_failure_inferred_from_untested_case": True,
        }
        rows.append(row)

    roles_gap = {x["task_id"] for x in rows
                 if x["required_roles_with_missing_editable_XML_objects"]}
    named_gap = {x["task_id"] for x in rows
                 if x["explicit_public_named_guids_missing_editable_XML"] > 0}
    schema_block = {x["task_id"] for x in rows
                    if x["current_direct_XML_session_source_admission"] !=
                    "SCHEMA_AND_UNIT_ADMISSIBLE_PROJECTION_WRITE_NOT_PROVEN"}
    original_crud = Counter(x["original_crud"] for x in rows)
    cats = Counter(x["original_category"] for x in rows)
    require(original_crud == Counter({"create":15,"update":15,"delete":15})
            and cats == Counter({"basic":15,"geometry":15,"topological":15}),
            "ORIGINAL_45_CRUD_OR_CATEGORY_DISTRIBUTION_CHANGED")
    require(len(roles_gap) == 9, "FROZEN_TASK_ROLE_GAP_COHORT_CHANGED")
    require(named_gap == {"topological_test_01","topological_test_20"},
            "FROZEN_PUBLIC_NAMED_EDITABLE_GUID_GAP_COHORT_CHANGED")
    require(schema_block ==
            {"geometry_test_03","geometry_test_04","geometry_test_05"},
            "FROZEN_NONIFC4X3_XML_SOURCE_ADMISSION_COHORT_CHANGED")
    require(all(x["explicit_public_named_guids_missing_original_source"] == 0
                for x in rows), "ORIGINAL_PUBLIC_GUID_SOURCE_REFERENCE_MISSING")
    require(sum(x["previously_developer_proven_D0_I0_native_bytes_equal"]
                for x in rows) == 5,
            "HISTORICAL_DEVELOPER_PAIRED_NATIVE_RESULT_COUNT_DRIFT")
    require(set(native_sources) == set(source_map) and len(native_sources) == 31,
            "ACTUAL_31_UNIQUE_SOURCE_IFC_SET_CHANGED")

    return {
        "status": "ORIGINAL45_SOURCE_ROLE_REFERENCES_AND_XML_INPUT_ADMISSION_AUDITED_WRITE_PARITY_UNPROVEN",
        "issue": "https://github.com/pikaybh/bim-markup-bench/issues/158",
        "pinned_original_author_revision": AUTHOR_SHA,
        "pinned_original_public_data_revision": DATA_SHA,
        "frozen_v013_native_source_catalog_sha256": FROZEN_V013[1],
        "frozen_v020_full45_capability_report_sha256": FROZEN_V020[1],
        "frozen_v021_selected_162_regression_report_sha256": FROZEN_V021[1],
        "original_public_task_denominator": 45,
        "original_crud_distribution": dict(sorted(original_crud.items())),
        "original_category_distribution": dict(sorted(cats.items())),
        "actual_unique_original_source_IFC_file_count": len(native_sources),
        "actual_unique_native_IfcProduct_total": sum(
            len(x["all_actual_native_source"]) for x in native_sources.values()),
        "actual_original_source_IfcProduct_catalogs_exactly_match_independent_v013": 31,
        "original45_current_safe_typed_XML_omits_some_native_products": 45,
        "original45_required_source_role_editable_XML_complete": 45-len(roles_gap),
        "original45_required_source_role_editable_XML_incomplete": len(roles_gap),
        "original_task_ids_with_incomplete_required_roles": sorted(roles_gap),
        "original45_explicit_named_public_original_product_guid_missing_native_source": 0,
        "original45_explicit_named_public_product_guids_missing_editable_XML_cases": len(named_gap),
        "original_task_ids_with_named_public_ref_omitted_from_typed_XML": sorted(named_gap),
        "original45_current_XML_input_schema_or_unit_admission_rejects": len(schema_block),
        "original_task_ids_current_XML_input_rejected": sorted(schema_block),
        "original45_input_schema_and_unit_admissible_not_proven_writable": 45-len(schema_block),
        "original45_complete_original_IFC_semantic_information_equivalence_proven": 0,
        "original45_complete_native_write_capability_equivalence_proven": 0,
        "original45_developer_native_D0_I0_byte_equivalence_previous": 5,
        "original45_original_author_scorable_both_developer_arms_previous": 3,
        "original45_pinned_original_author_scorer_missing_reference_previous": 2,
        "original45_other_same_protocol_edit_cases_not_evaluated": 40,
        "new_real_LLM_trials_or_scores": 0,
        "new_provider_paid_USD": 0,
        "new_original_public_scorer_grades_this_version": 0,
        "read_only_actual_original_IFC_no_mutation": True,
        "XML_typed_subset_derived_from_frozen_independent_native_source_catalog": True,
        "new_actual_XML_native_write_probes_in_this_version": 0,
        "explicit_guids_raw_original_catalog_and_questions_NOT_in_report": True,
        "actual_pure_representation_causal_LLM_launch_permitted": False,
        "all45_per_task_actual_source_role_and_admission_rows": rows,
    }


def audit(root: Path, author: Path, data: Path) -> dict:
    require(_head(author) == AUTHOR_SHA and _head(data) == DATA_SHA,
            "ORIGINAL_PUBLIC_GIT_REVISION_CHANGED")
    for location in (author, data):
        require(not location.is_symlink(), "ORIGINAL_PUBLIC_GIT_PATH_SYMLINK_NOT_ALLOWED")
    v013 = read_frozen_json(root, FROZEN_V013)
    v020 = read_frozen_json(root, FROZEN_V020)
    v021 = read_frozen_json(root, FROZEN_V021)
    public = public_45(author, data)
    native = source_native_product_maps(public, data, v013)
    result = classify_original45(public, native, v013, v020, v021)
    for task in public:
        orig = data / "ifc" / task["original_source_ifc_relpath"]
        require(file_hash(orig) == task["original_ifc_sha256"],
                "ORIGINAL_SOURCE_CHANGED_POST_AUDIT")
    require(_head(author) == AUTHOR_SHA and _head(data) == DATA_SHA,
            "ORIGINAL_PUBLIC_GIT_REVISION_CHANGED_POST_AUDIT")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--author", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    if a.output.is_file() or a.output.is_symlink():
        parser.error("Refuse overwrite of prior original source evidence")
    result = audit(a.root, a.author, a.data)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x", encoding="utf8", newline="\n") as f:
        json.dump(result, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    print("V022_SOURCE_ROLE_AUDIT",result["status"])
    print("ORIGINAL_TASKS",result["original_public_task_denominator"],
          "UNIQUE_ACTUAL_IFCS",result["actual_unique_original_source_IFC_file_count"])
    print("ROLE_GAP",result["original45_required_source_role_editable_XML_incomplete"],
          "NAMED_GUID_GAP",result["original45_explicit_named_public_product_guids_missing_editable_XML_cases"],
          "CURRENT_XML_SCHEMA_REJECT",result["original45_current_XML_input_schema_or_unit_admission_rejects"])
    print("NEW_LLM_CALLS",result["new_real_LLM_trials_or_scores"])
    print("REPORT_SHA256",file_hash(a.output))


if __name__ == "__main__":
    main()
