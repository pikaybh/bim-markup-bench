"""Read-only BIM-Edit XML-only launch audit. Does not call LLMs or graders.

Uses exactly pinned public task records and preexisting audits. No model inputs,
instructions, target GUIDs, ground-truth paths, or IFC bytes enter the report.
The audit is deliberately non-scoring and always fails closed at the live gate.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUTS = {
    "revision": "manifests/bim_edit_revision.json",
    "candidate": "manifests/pilot_36_candidate_v0.json",
    "support": "reports/g1_324_support_matrix.json",
    "readiness": "reports/g1_frozen_pilot_readiness_20261110.json",
    "rights": "reports/g0_pilot_ifc_rights_20261110.json",
    "scorer": "reports/g0_official_scorer_origin_review_20261111.json",
    "published": "reports/g2_published_per_task_audit_20261110.json",
    "offline": "reports/g1_frozen_36_offline_three_pair_recheck_20261111.json",
}
SAFE_TASK_FIELDS = ("task_id", "operation", "category", "scene", "target_class")


class ReadinessEvidenceError(ValueError):
    """Fail closed for stale, corrupt, missing or inconsistent evidence."""


def _load_json(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise ReadinessEvidenceError(f"Missing or linked evidence: {path.name}")
    try:
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ReadinessEvidenceError(f"Invalid evidence: {path.name}") from exc
    if not isinstance(obj, dict):
        raise ReadinessEvidenceError(f"Object evidence required: {path.name}")
    return obj


def _indexed_tasks(records: list[dict], label: str, count: int) -> dict[str, dict]:
    if not isinstance(records, list) or len(records) != count:
        raise ReadinessEvidenceError(f"{label}: expected {count} task rows")
    result = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("task_id"), str):
            raise ReadinessEvidenceError(f"{label}: malformed task row")
        key = record["task_id"]
        if not key or key in result:
            raise ReadinessEvidenceError(f"{label}: invalid/duplicate task ID")
        result[key] = record
    return result


def audit_xml_only(
    *, evidence_root: Path = ROOT, task_jsonl: Path | None = None,
) -> dict:
    root = Path(evidence_root)
    if task_jsonl is None:
        task_jsonl = root / "data/tasks.jsonl"
    task_jsonl = Path(task_jsonl)
    if not task_jsonl.is_file() or task_jsonl.is_symlink():
        raise ReadinessEvidenceError("Pinned public task metadata file missing or linked")

    evidence_paths = {name: root / path for name, path in INPUTS.items()}
    files = {name: _load_json(path) for name, path in evidence_paths.items()}
    revisions, candidate = files["revision"], files["candidate"]
    support, readiness = files["support"], files["readiness"]
    rights, scorer, published, offline = (
        files["rights"], files["scorer"], files["published"], files["offline"]
    )

    original_bytes = task_jsonl.read_bytes()
    digest = sha256(original_bytes).hexdigest()
    pinned = revisions.get("task_jsonl_sha256")
    if (digest != pinned or pinned != candidate.get("task_data_sha256")
            or pinned != support.get("public_task_record_sha256")):
        raise ReadinessEvidenceError("Pinned 324 task metadata SHA-256 mismatch")

    try:
        public_rows = [json.loads(line) for line in original_bytes.decode("utf-8-sig").splitlines()
                       if line.strip()]
    except (ValueError, UnicodeError) as exc:
        raise ReadinessEvidenceError("Invalid public task JSONL") from exc
    public_tasks = _indexed_tasks(public_rows, "public", 324)
    support_tasks = _indexed_tasks(support.get("tasks"), "support", 324)
    candidate_tasks = _indexed_tasks(candidate.get("tasks"), "candidate", 36)
    readiness_tasks = _indexed_tasks(readiness.get("tasks"), "readiness", 36)
    rights_tasks = _indexed_tasks(rights.get("tasks"), "rights", 36)

    if (set(public_tasks) != set(support_tasks)
            or set(candidate_tasks) != set(readiness_tasks)
            or set(candidate_tasks) != set(rights_tasks)
            or not set(candidate_tasks).issubset(public_tasks)):
        raise ReadinessEvidenceError("Task identity drift between pinned manifests and audits")
    if candidate.get("task_revision") != revisions.get("task_revision"):
        raise ReadinessEvidenceError("Pinned task revision differs")
    if candidate.get("status") != "CANDIDATE_NOT_PREREGISTERED":
        raise ReadinessEvidenceError("Candidate preregistration status changed: independent review required")
    for task_id, record in candidate_tasks.items():
        ref = readiness_tasks[task_id]
        support_ref = support_tasks[task_id]
        for attr, other_attr in (
            ("operation", "operation"), ("category", "category"),
            ("scene", "scene"), ("entity_type", "target_class"),
        ):
            if record.get(attr) != ref.get(other_attr) or record.get(attr) != support_ref.get(other_attr):
                raise ReadinessEvidenceError(f"Task metadata mismatch: {task_id}:{attr}")

    status_counts = dict(sorted(Counter(
        record.get("readiness_disposition") for record in readiness_tasks.values()
    ).items()))
    if (status_counts != readiness.get("disposition_counts")
            or sum(status_counts.values()) != 36):
        raise ReadinessEvidenceError("Frozen candidate disposition count drift")
    global_support = dict(sorted(Counter(
        task.get("engine_status") for task in support_tasks.values()
    ).items()))
    if (global_support.get("STATIC_ENGINE_UNSUPPORTED") != support.get("static_engine_unsupported_count")
            or sum(global_support.values()) != 324):
        raise ReadinessEvidenceError("324 support coverage drift")

    required_blockers = {
        "official_author_scorer": not scorer.get("author_original_evaluator_callable_on_arbitrary_prediction", False),
        "author_score_parity": not scorer.get("author_original_evaluator_scored_output_reproduced", False),
        "per_model_redistribution_rights": not rights.get("model_redistribution_rights_cleared", False),
        "full_task_oracles": readiness.get("full_instruction_specific_paired_D0_I0_task_oracles_proven", -1) != 36,
        "pilot_registered": candidate.get("status") != "PREREGISTERED",
    }
    # In a new single-arm study an XML-specific oracle is necessary, not
    # merely a historical matched D0/I0 demonstration.
    if offline.get("full_instruction_specific_D0_I0_task_oracles_proven", -1) != 0:
        raise ReadinessEvidenceError("Historical oracle evidence changed; re-audit")
    if published.get("official_executable_scorer_verified", False):
        raise ReadinessEvidenceError("Official scorer provenance changed; re-audit")
    if not all(required_blockers.values()):
        raise ReadinessEvidenceError("Previously blocked gate changed; require prospective gate review")

    safe_tasks = []
    for task_id in sorted(candidate_tasks):
        task = readiness_tasks[task_id]
        safe_tasks.append({
            key: task[key] for key in SAFE_TASK_FIELDS
        } | {
            "source_readiness": task["readiness_disposition"],
            "full_task_oracle_proven": bool(task["task_oracle_fully_proven"]),
            "official_score": None,
            "xml_llm_trial_performed": False,
        })
    if any(item["full_task_oracle_proven"] for item in safe_tasks):
        raise ReadinessEvidenceError("Unexpected full-task oracle; require prospective review")

    return {
        "schema": "xml-only-bim-edit-readiness/v0.1",
        "status": "BLOCKED_NOT_REGISTERED_OR_SCORABLE",
        "purpose": "Offline readiness and provenance only; not model performance",
        "primary_condition": "direct_xml_only",
        "comparison_design": "historical_external_baselines_descriptive_only",
        "can_claim_causal_xml_vs_api_or_python": False,
        "model_calls_in_this_audit": 0,
        "official_bim_edit_tasks_scored_in_this_audit": 0,
        "pinned_metadata_sha256": digest,
        "pinned_task_revision": revisions["task_revision"],
        "pinned_model_revision": revisions["model_revision"],
        "existing_candidate_size": 36,
        "candidate_preregistered": False,
        "prospective_itt_denominator_if_registered": 36,
        "published_population_size": 324,
        "published_population_support_dispositions": global_support,
        "candidate_readiness_dispositions": status_counts,
        "historical_verified_source_and_reference_pairs": sum(rights.get("status_counts", {}).values()) - rights.get("status_counts", {}).get(
                "BLOCKED_PAIRED_INPUT_REFERENCE_CONTENT_MISSING", 0),
        "historical_source_only_offline_pairs_not_full_task_scores": offline.get(
            "posthoc_dev_native_pairs_passed_now", 0),
        "author_published_models_audited": published.get("verified_published_models", 0),
        "published_baseline_rows_missing": published.get("total_missing_published_task_rows"),
        "official_scorer_code_verified": False,
        "independent_scorer_is_official": False,
        "individual_model_rights_verified": rights.get("individual_model_license_documents_verified", 0),
        "launch_blockers": sorted(key for key, value in required_blockers.items() if value),
        "comparison_constraints": [
            "Cannot directly rank independently scored XML against paper official scores without parity",
            "Cannot infer effect of XML authoring from models/harnesses with different budgets",
            "Do not select supported-only subset after observing outcomes",
            "Original paper baseline scores remain citations, not scores computed by this runner",
        ],
        "task_rows_no_prompt_or_ground_truth": safe_tasks,
        "input_evidence_sha256": {
            name: sha256(path.read_bytes()).hexdigest()
            for name, path in evidence_paths.items()
        },
    }
