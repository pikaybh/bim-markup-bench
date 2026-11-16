"""Read-only, pinned original-45 BIBIMBAP developer-evidence reconciliation (v0.30).

This is a prospective report derived from existing frozen reports, NOT a new
LLM experiment, a full IFC information/write parity proof, or an official score.
No original question, hidden target, GlobalId or source IFC bytes are loaded.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/pikaybh/bim-markup-bench/issues/175"
PARENT = "952d17d6c2596108e368d071eb6552c52e7c05bd"
BASE = (
    "bibimbap_v020_original45_capability_and_terminal_gate_20261115.json",
    "1aa218a0883186e6df1e7e7d895670fb9e012ef0229799b14881a87473f762be",
)
ROLES = (
    "bibimbap_v022_original45_task_relevant_roles_and_xml_input_20261115.json",
    "f606994defa7517f898e22ee6e39d5e82da6dc40288c1b38cec25c98b7cd492e",
)
# (report file, immutable file hash, public task, native-bytes-equal field,
#  previous/current native counts, previous/current author-callable counts,
#  original author D0/I0 score fields)
NEW_CASES = (
    ("bibimbap_v023_original_test20_space_delete_D0_I0_native_parity_20261115.json",
     "9abcc4ebd21c18891bf08307624a19f6012a981455eca7db89051ae70ce86102",
     "test_20", "actual_full_IFC_output_bytes_identical",
     "prior_frozen_developer_D0_I0_byte_equal_original_cases",
     "post_v023_distinct_developer_D0_I0_byte_equal_original_cases",
     "prior_frozen_both_original_author_callable_cases",
     "post_v023_distinct_developer_both_original_author_callable_cases",
     "pinned_original_author_D0_score", "pinned_original_author_I0_score"),
    ("bibimbap_v024_original_test18_opening_window_D0_I0_20261115.json",
     "a31e74dacdece9924304de6c74c5d9e8769497a8ad68287779ddd4a37bac6a67",
     "test_18", "actual_full_IFC_output_bytes_equal",
     "historical_prior_developer_D0_I0_original_native_byte_equal",
     "new_cumulative_developer_D0_I0_original_native_byte_equal",
     "historical_prior_developer_original_author_callable_pairs",
     "new_cumulative_developer_original_author_callable_pairs",
     "original_author_grader_D0", "original_author_grader_I0"),
    ("bibimbap_v025_original_test17_door_opening_D0_I0_20261115.json",
     "4ea264519d011288acf6d059fc15b3ca49aa7d4d21315ccb5cbebe5bb17f3f4a",
     "test_17", "full_original_native_output_IFC_bytes_equal",
     "prior_frozen_developer_original_native_D0_I0_identical_cases",
     "new_cumulative_developer_original_native_D0_I0_identical_cases",
     "prior_frozen_original_author_callable_developer_pairs",
     "new_cumulative_original_author_callable_developer_pairs",
     "unchanged_original_author_D0", "unchanged_original_author_I0"),
    ("bibimbap_v027_original_test19_connected_wall_D0_I0_native_parity_20261116.json",
     "9cee40c6cd75f5f5fc3c35f1d8ee5b0580681e38820da6178f39c413c71d63b4",
     "test_19", "original_D0_I0_full_IFC_bytes_equal",
     "prior_frozen_developer_original_native_D0_I0_byte_equal",
     "new_cumulative_developer_original_native_D0_I0_byte_equal",
     "prior_frozen_original_author_callable_developer_pairs",
     "new_cumulative_original_author_callable_developer_pairs",
     "unchanged_original_author_D0", "unchanged_original_author_I0"),
    ("bibimbap_v028_original_test11_wall_center_rotate_D0_I0_native_parity_20261116.json",
     "6818e6bfa2990f8dc9ee3730ba9a7197c72d6f3131af9bae9fbda8d22fefd8cb",
     "test_11", "full_native_IFC_D0_I0_bytes_equal",
     "prior_developer_original_native_byte_equal_D0_I0_tasks",
     "new_cumulative_developer_original_native_byte_equal_D0_I0_tasks",
     "prior_original_author_callable_developer_pairs",
     "new_cumulative_original_author_callable_developer_pairs",
     "unchanged_original_author_D0", "unchanged_original_author_I0"),
    ("bibimbap_v029_original_test14_flipped_slab_D0_I0_native_parity_20261116.json",
     "338f763b691390b7186c51ecdaaa914ce18a9c8ab8586fa000542a7d63f8b748",
     "test_14", "full_native_D0_I0_IFC_bytes_identical",
     "previous_developer_native_byte_equal_original_cases",
     "new_cumulative_developer_native_byte_equal_original_cases",
     "previous_original_author_callable_developer_pairs",
     "new_cumulative_original_author_callable_developer_pairs",
     "unchanged_original_author_D0", "unchanged_original_author_I0"),
)


class EvidenceError(ValueError):
    pass


def require(value: bool, message: str) -> None:
    if not value:
        raise EvidenceError(message)


def load_pinned(root: Path, name: str, expected_hash: str) -> dict:
    require(Path(name).name == name, "Invalid report filename")
    path = root / "reports" / name
    require(path.is_file() and not path.is_symlink(), f"Missing or linked report: {name}")
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == expected_hash, f"Frozen report hash mismatch: {name}")
    try:
        obj = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise EvidenceError(f"Invalid JSON: {name}") from exc
    require(type(obj) is dict, f"Unexpected report type: {name}")
    return obj


def reconciled_report(root: Path = ROOT) -> dict:
    root = Path(root)
    base = load_pinned(root, *BASE)
    roles = load_pinned(root, *ROLES)
    original = base["all45_original_public_task_capability_matrix"]
    require(type(original) is list and len(original) == 45, "Frozen 45-case denominator drift")
    by_id = {x["task_id"]: x for x in original}
    require(len(by_id) == 45, "Duplicate original task ID")
    require(Counter(x["original_crud"] for x in original)
            == {"create": 15, "update": 15, "delete": 15},
            "Original CRUD distribution drift")
    require(Counter(x["original_category"] for x in original)
            == {"basic": 15, "geometry": 15, "topological": 15},
            "Original task-category distribution drift")
    require(base["original45_developer_both_arm_native_IFC_byte_equivalence"] == 5
            and base["original45_author_scorable_developer_both_arm"] == 3
            and base["original45_original_author_scorer_mismatched_reference"] == 2,
            "Frozen historical developer baseline drift")
    require(base["original45_WITH_PROVEN_FULL_IFC_INFORMATION_PARITY"] == 0
            and base["original45_WITH_PROVEN_FULL_NATIVE_WRITE_CAPABILITY_PARITY"] == 0
            and base["new_real_matched_LLM_D_I_trials"] == 0,
            "Frozen experiment causal gate drift")
    require(roles["original_public_task_denominator"] == 45
            and roles["original45_complete_original_IFC_semantic_information_equivalence_proven"] == 0
            and roles["original45_complete_native_write_capability_equivalence_proven"] == 0
            and roles["new_real_LLM_trials_or_scores"] == 0,
            "Frozen original45 source capability gate drift")
    role_rows = roles["all45_per_task_actual_source_role_and_admission_rows"]
    require(type(role_rows) is list and len(role_rows) == 45
            and {x["task_id"] for x in role_rows} == set(by_id),
            "Original45 source-role row integrity drift")
    proven = {
        task: x for task, x in by_id.items()
        if x["actual_developer_native_IFC_byte_equivalence"]
        == "PROVEN_ON_ORIGINAL_PUBLIC_TASK"
    }
    scored = {
        task for task, x in proven.items()
        if x["actual_original_author_scoring"] == "BOTH_ARMS_SCORED"
    }
    mismatched = {
        task for task, x in proven.items()
        if x["actual_original_author_scoring"]
        == "PINNED_AUTHOR_REFERENCE_SOURCE_MISMATCH"
    }
    require(len(proven) == 5 and len(scored) == 3 and len(mismatched) == 2,
            "Historical original-author classification drift")
    for task, x in by_id.items():
        if task not in proven:
            require(x["actual_developer_native_IFC_byte_equivalence"] == "NOT_EVALUATED"
                    and x["actual_original_author_scoring"] == "NOT_EVALUATED",
                    f"Unexpected historical task evidence: {task}")
    proof_files = {task: BASE[0] for task in proven}
    individual_scores = {}
    new_ids = set()
    current_native = len(proven)
    current_author = len(scored)
    for (name, file_sha, task, equality_field, prev_native, next_native,
         prev_author, next_author, score_d, score_i) in NEW_CASES:
        require(task in by_id and task not in proven and task not in new_ids,
                f"Unknown, duplicated, or historically proven new case: {task}")
        new_ids.add(task)
        snapshot = load_pinned(root, name, file_sha)
        require(snapshot.get(equality_field) is True,
                f"No native D0/I0 IFC byte equality evidence: {task}")
        require(snapshot.get(prev_native) == current_native
                and snapshot.get(next_native) == current_native + 1,
                f"Historical developer count chain mismatch: {task}")
        require(snapshot.get(prev_author) == current_author
                and snapshot.get(next_author) == current_author + 1,
                f"Author-callable count chain mismatch: {task}")
        public_question_hash = snapshot.get(
            "original_public_question_SHA256",
            snapshot.get("original_public_question_sha256"))
        require(public_question_hash == by_id[task]["pinned_original_public_instruction_sha256"],
                f"Original public instruction SHA mismatch: {task}")
        require(by_id[task]["pinned_original_native_ifc_sha256"]
                == "9ef1235e49d5b0359c1d44fd95a7afad7755149362109ca8b875d0427dc487ca",
                f"Actual original source IFC SHA mismatch: {task}")
        d, i = snapshot.get(score_d), snapshot.get(score_i)
        require(isinstance(d, dict) and isinstance(i, dict)
                and d.get("status") == i.get("status") == "AUTHOR_SCORED"
                and type(d.get("original_author_score")) in (int, float)
                and d["original_author_score"] == i.get("original_author_score")
                and 0.0 <= d["original_author_score"] <= 1.0,
                f"Original author score pair not established: {task}")
        require(snapshot.get("paid_provider_USD", snapshot.get("paid_model_cost_usd",
                snapshot.get("new_paid_provider_USD", 0))) in (0, "0", None),
                f"Unexpected new provider spend in developer evidence: {task}")
        proof_files[task] = name
        individual_scores[task] = d["original_author_score"]
        current_native += 1
        current_author += 1

    require(current_native == 11 and current_author == 9
            and len(new_ids) == 6 and len(set(proof_files)) == 11,
            "Cumulative developer counts do not reconcile")
    result_rows = []
    for task, row in sorted(by_id.items()):
        native = task in proof_files
        status = ("AUTHOR_REFERENCE_SOURCE_MISMATCH"
                  if task in mismatched else
                  "AUTHOR_SCORED_DEVELOPER_CONTROL"
                  if task in scored or task in new_ids else
                  "NOT_EVALUATED_UNDETERMINED")
        result_rows.append({
            "task_id": task,
            "original_category": row["original_category"],
            "original_crud": row["original_crud"],
            "developer_native_D0_I0_bytes_equal_proven": native,
            "developer_author_scorer_status": status,
            "developer_author_score_each_arm": individual_scores.get(task),
            "frozen_evidence_report": proof_files.get(task),
            "actual_matched_D_I_LLM_result": "NOT_RUN",
            "source_information_parity": "NOT_PROVEN",
            "full_native_write_capability_parity": "NOT_PROVEN",
        })
    require(sum(x["developer_native_D0_I0_bytes_equal_proven"] for x in result_rows) == 11,
            "45-row developer control count mismatch")
    return {
        "status": "V030_ORIGINAL45_FROZEN_DEVELOPER_EVIDENCE_RECONCILED_CAUSAL_GATE_BLOCKED",
        "issue": ISSUE,
        "parent_draft_pr": "https://github.com/pikaybh/bim-markup-bench/pull/174",
        "source_parent_git_commit": PARENT,
        "scope": "PROSPECTIVE_READ_ONLY_SECONDARY_EVIDENCE_SYNTHESIS",
        "evidence_origin": "PINNED_HISTORICAL_NONBLINDED_DEVELOPER_REPORTS_NOT_NEW_LLM_EVALUATION",
        "frozen_inputs_sha256": {BASE[0]: BASE[1], ROLES[0]: ROLES[1],
                                  **{x[0]: x[1] for x in NEW_CASES}},
        "original45_ITT_denominator": 45,
        "original45_developer_native_D0_I0_full_ifc_byte_equal": 11,
        "original45_original_author_callable_developer_pairs": 9,
        "original45_historical_author_reference_source_mismatch": 2,
        "original45_not_yet_developer_native_D0_I0_byte_equal_proven": 34,
        "original45_full_IFC_information_parity_proven": 0,
        "original45_full_native_write_capability_parity_proven": 0,
        "original45_latest_protocol_actual_matched_LLM_trials": 0,
        "causal_representation_only_XML_vs_Python_performance_claim_permitted": False,
        "missing_developer_evidence_is_not_a_task_failure_or_unsupported_proof": True,
        "new_paid_inference_or_new_IFC_experiment_in_v030": False,
        "independently_reexecuted_prior_six_developer_controls_in_v030": False,
        "rows": result_rows,
    }


def encoded_report(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n").encode("utf8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", type=Path, help="Compare an existing v0.30 report without modifying it")
    parser.add_argument("--write", type=Path, help="Create report once; refuse overwrite")
    args = parser.parse_args()
    out = encoded_report(reconciled_report(args.root))
    if args.check:
        require(args.check.read_bytes() == out, "Frozen v0.30 output drift")
        print(f"CHECK_OK sha256={sha256(out).hexdigest()}")
    elif args.write:
        require(not args.write.exists() and not args.write.is_symlink(), "Refuse report overwrite")
        args.write.parent.mkdir(parents=True, exist_ok=True)
        with args.write.open("xb") as f:
            f.write(out)
        print(f"WRITE_OK sha256={sha256(out).hexdigest()}")
    else:
        print(f"DRYRUN_OK sha256={sha256(out).hexdigest()}")


if __name__ == "__main__":
    main()
