"""Offline BIBIMBAP XML-only full-population launch gate (issue #106).

Evaluator evidence is inspected ONLY in this research audit process.
It is never forwarded to the separate public-packet entrypoint. This
tool always reports NOT_READY; it has NO model transport or paid mode.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, read_original_tasks

ROOT = Path(__file__).resolve().parents[1]
NOOP_REPORT = ROOT / "reports" / "bibimbap_original_45_noop_20261112.json"
PROJECTION_REPORT = ROOT / "reports" / "bibimbap_45_xml_projection_20261112.json"
EXPECTED_EDIT_TYPES = {"create": 15, "update": 15, "delete": 15}
WITNESS_STATUS = {
    "test_05": "DEV_AUTHORED_CREATE_XML_SCORED_NOT_LLM",
    "geometry_test_11": "DEV_AUTHORED_UPDATE_XML_SCORED_NOT_LLM",
}


class LaunchGateBlocked(ValueError):
    pass


def _json(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise LaunchGateBlocked("Required historical evidence file missing")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise LaunchGateBlocked("Invalid immutable evidence object")
    return value


def audit_launch(author: Path, dataset: Path) -> dict:
    original, pins = read_original_tasks(author, dataset)
    no_op = _json(NOOP_REPORT)
    projection = _json(PROJECTION_REPORT)
    if (pins["author_commit_sha"] != AUTHOR_SHA or
            pins["data_commit_sha"] != DATA_SHA or
            no_op.get("original_editing_tasks") != 45 or
            no_op.get("negative_control", {}).get("statuses") != {"SCORED": 45} or
            no_op.get("negative_control", {}).get("n") != 45 or
            projection.get("assessed_editing_task_count") != 45 or
            projection.get("author_commit_sha") != AUTHOR_SHA or
            projection.get("dataset_commit_sha") != DATA_SHA):
        raise LaunchGateBlocked("Pinned grader/dataset/projection evidence mismatched")
    obs = no_op["negative_control"]["observations"]
    pobs = projection["per_task"]
    if any(len(x) != 45 for x in (original, obs, pobs)):
        raise LaunchGateBlocked("Missing entries in research population")
    originals = {x["test_id"]: x for x in original}
    scores = {x["test_id"]: x for x in obs}
    projected = {x["test_id"]: x for x in pobs}
    if (len(originals) != 45 or len(scores) != 45 or len(projected) != 45 or
            set(originals) != set(scores) or set(originals) != set(projected)):
        raise LaunchGateBlocked("Score/projection IDs do not match frozen original population")
    if Counter(x["crud"] for x in original) != EXPECTED_EDIT_TYPES:
        raise LaunchGateBlocked("CRUD allocation drifted")
    if any(x.get("original_and_edited_identical") is not True or
           x.get("status") != "SCORED" or
           not 0 <= float(x.get("author_noop_score", -1)) <= 1
           for x in obs):
        raise LaunchGateBlocked("Invalid source-identical negative-control scores")
    rows = []
    for record in original:
        key = record["test_id"]
        p = projected[key]
        negative = scores[key]
        if p.get("crud") != record["crud"] or p.get("category") != record["category"]:
            raise LaunchGateBlocked("Projection metadata does not describe the same task")
        source_proj = p.get("source", {})
        if type(source_proj.get("xml_projection_passed")) is not bool:
            raise LaunchGateBlocked("Unresolved source projection evidence")
        rows.append({
            "candidate_id": key,
            "crud": record["crud"],
            "category": record["category"],
            "public_ifc_sha256": record["ifc_sha256"],
            "original_author_test_sha256_grader_only": record["test_sha256"],
            "source_projection": "PROJECTABLE" if source_proj["xml_projection_passed"] else "BLOCKED",
            "source_projection_reason": source_proj.get("reason") if not source_proj["xml_projection_passed"] else None,
            "task_specific_xml_compiler_and_oracle": WITNESS_STATUS.get(key, "NOT_PROVEN"),
            "original_author_noop_score": float(negative["author_noop_score"]),
            "original_author_score_on_future_xml": None,
            "noop_adjusted_future_score": None,
            "independent_strict_task_success": "UNVERIFIED_NOT_SCORED",
            "real_llm_trial": "NOT_RUN",
            "include_in_intention_to_test_denominator": True,
        })
    assert len(rows) == 45
    # No paid provider calls or hidden changes; the exit status is a hard block.
    blockers = [
        "NOT_PREREGISTERED: this is a 45-task candidate list, not an approved frozen live protocol",
        "NO_MODEL_AND_APPROVAL: verified model ID/parameters, price and owner USD limit absent",
        "DATA_RIGHTS_REVIEW: per-IFC external-use/redistribution scope and author test-code license unresolved",
        "STRICT_ORACLE: independent task-completion adjudication not validated for 45 tasks",
        "ENGINE_COVERAGE: source projection on 36 tasks does not establish 36 executable edits",
        "GT_ISOLATION: public packet verified for pilot only, not independently mounted for actual model inference",
        "NO_ACTUAL_LLM_BIBIMBAP_SCORES: no live prompt/code/result can be reported",
    ]
    return {
        "schema": "bibimbap-xml-only-prelaunch-gate/v0.1",
        "status": "NOT_READY",
        "research_population": "original BIBIMBAP Create/Update/Delete only",
        "protocol_freeze": "CANDIDATE_NOT_PREREGISTERED",
        "noncausal_historical_comparison_only": True,
        "pinned_author_commit": pins["author_commit_sha"],
        "pinned_dataset_commit": pins["data_commit_sha"],
        "pinned_question_csv_sha256": pins["original_csv_sha256"],
        "original_editing_population": 45,
        "excluded_original_retrieval_population": 55,
        "operation_counts": dict(sorted(Counter(x["crud"] for x in original).items())),
        "projection_only_eligible_count": sum(x["source_projection"] == "PROJECTABLE" for x in rows),
        "developer_written_scored_witness_count": len(WITNESS_STATUS),
        "actual_llm_scored_task_count": 0,
        "latest_new_billed_spend_usd": 0,
        "source_test_code_license_verified": pins["source_license_file_present"],
        "all_original_editing_tasks_intention_to_test": rows,
        "prior_noop_positive_partial_credit_count": sum(x["original_author_noop_score"] > 0 for x in rows),
        "allow_future_silent_filtering": False,
        "metric_origins": {
            "original_author_grader": "original author executable, independent of XML compiler",
            "prior_noop": "negative control only, not LLM success",
            "independent_strict_task_success": "NOT_IMPLEMENTED_FOR_FULL_POPULATION",
        },
        "live_run_blockers": blockers,
        "launch_authorized": False,
        "model_provider_contacted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author-repo", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    try:
        report = audit_launch(args.author_repo, args.dataset)
    except (LaunchGateBlocked, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "EVIDENCE_INVALID", "reason_type": type(exc).__name__}, sort_keys=True))
        return 2
    if args.output_json:
        path = args.output_json
        if path.is_symlink() or path.exists() or not path.parent.is_dir():
            parser.error("Evidence is write-once; refuse overwrite/missing folder")
        with path.open("x", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, indent=2, sort_keys=True)
            f.write("\n")
    print(json.dumps({
        "status": report["status"],
        "denominator": report["original_editing_population"],
        "projectable_only": report["projection_only_eligible_count"],
        "developer_written_witnesses": report["developer_written_scored_witness_count"],
        "real_llm_tasks": report["actual_llm_scored_task_count"],
        "blockers": len(report["live_run_blockers"]),
    }, sort_keys=True))
    return 2  # intentionally refuses live admission


if __name__ == "__main__":
    raise SystemExit(main())
