"""Offline BIBIMBAP test_05 orientation sensitivity probe, not model evaluation.

Compare author scoring of developer-authored declarative walls starting at
(0,-10), with the same 15 m true centerline and different headings. Probe
a 10 m wall as a negative control. Upstream author evaluator is untouched.
"""
from __future__ import annotations

import argparse
import json
from math import cos, radians, sin
from pathlib import Path

from tools.audit_bibimbap_author import read_original_tasks
from tools.verify_bibimbap_xml_author import run_witness


def endpoint(angle: float, length: float) -> tuple[float, float]:
    x = length * cos(radians(angle))
    y = -10.0 + length * sin(radians(angle))
    # Decimal XML grammar does not allow float scientific notation for 90 deg ~0.
    return (0.0 if abs(x) < 1e-9 else x,
            0.0 if abs(y) < 1e-9 else y)


CASES = (
    ("axis_x_15m", 0.0, 15.0),
    ("diagonal_30_15m", 30.0, 15.0),
    ("diagonal_45_15m", 45.0, 15.0),
    ("axis_y_15m", 90.0, 15.0),
    ("invalid_short_10m", 0.0, 10.0),
)


def audit(author: Path, data: Path) -> dict:
    tasks, pins = read_original_tasks(author, data)
    test = next(x for x in tasks if x["test_id"] == "test_05")
    results = []
    for label, degrees, length in CASES:
        entry = {
            "case": label,
            "heading_degrees": degrees,
            "source_declared_length_m": length,
            "correct_by_public_length_and_start": abs(length - 15.0) <= 0.05,
            "development_control_not_llm": True,
        }
        try:
            result = run_witness(author, data, end_xy=endpoint(degrees, length))
            response = result["observations"]["xml_wall_created"]["scorer"]
            entry.update({
                "compile_status": result["compile_status"],
                "scorer_status": response.get("status"),
                "author_score": response.get("score"),
                "author_metric_vector": response.get("metrics"),
                "original_source_unchanged": result["input_source_hash_unmodified"],
                "guids_removed": result["root_inventory"]["lost_guids"],
                "measured_declared_centerline_m": result["developer_wall_horizontal_length_m"],
                "independent_native_task_core": result["native_public_task_core"],
                "independent_native_noop_core": result["native_public_task_noop_negative_control"],
            })
        except Exception as exc:
            entry.update({
                "scorer_status": "BLOCKED",
                "error_type": type(exc).__name__,
                "reason": str(exc)[:250],
            })
        results.append(entry)
    first = results[0]
    dimension = [
        x for x in results
        if x["correct_by_public_length_and_start"]
        and x.get("scorer_status") == "SCORED"
    ]
    return {
        "schema": "bibimbap-test05-orientation-validity/v0.2",
        "issue": 108,
        "test_id": "test_05",
        "public_task": "Add a wall with a length of 15m beginning in (0, -10).",
        "author_sha256": pins["author_commit_sha"],
        "dataset_sha256": pins["data_commit_sha"],
        "original_scorer_source_sha256": test["test_sha256"],
        "original_ifc_sha256": test["ifc_sha256"],
        "method": "developer-authored declarative XML, trusted compiler, unmodified author scorer",
        "llm_calls": 0,
        "paid_api_cost": 0,
        "author_scorer_modified": False,
        "original_full_benchmark_score_reproduced": False,
        "independent_full_strict_task_success_implemented": False,
        "independent_native_valid_core_count": sum(
            x.get("independent_native_task_core", {}).get("public_task_core_success") is True
            for x in results if x["correct_by_public_length_and_start"]
        ),
        "independent_native_invalid_core_rejected": (
            results[-1].get("independent_native_task_core", {}).get("public_task_core_success") is False
        ),
        "independent_native_noop_rejected_all": all(
            x.get("independent_native_noop_core", {}).get("public_task_core_success") is False
            for x in results if x.get("scorer_status") == "SCORED"
        ),
        "results": results,
        "all_variants_scored": len([x for x in results if x.get("scorer_status") == "SCORED"]) == len(CASES),
        "valid_heading_dimension_pass_count": sum(
            float((x.get("author_metric_vector") or {}).get("right_dimensions", 0)) >= 0.5 for x in dimension
        ),
        "valid_heading_dimension_tested_count": len(dimension),
        "same_score_across_valid_headings": (
            len({x["author_score"] for x in dimension}) == 1
            if len(dimension) == 4 else None
        ),
        "negative_short_wall_dimensions_rejected": (
            float((results[-1].get("author_metric_vector") or {}).get("right_dimensions", 1)) < 0.5
        ),
        "warning": "Author continuous score differs from independent public-task geometry core. Clash/non-target shape invariance and full strict success are NOT verified; no LLM outputs.",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--author-repo", type=Path, required=True)
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--output-json", type=Path)
    args = p.parse_args()
    report = audit(args.author_repo, args.dataset)
    if args.output_json:
        path = args.output_json
        if path.exists() or path.is_symlink() or not path.parent.is_dir():
            p.error("Evidence path exists, symlink or parent missing")
        with path.open("x", encoding="utf8", newline="\n") as f:
            json.dump(report, f, indent=2, sort_keys=True)
            f.write("\n")
    print(json.dumps({
        "case_count": len(report["results"]),
        "all_scored": report["all_variants_scored"],
        "dimension_pass_count": report["valid_heading_dimension_pass_count"],
        "dimension_tested_count": report["valid_heading_dimension_tested_count"],
        "scores_invariant": report["same_score_across_valid_headings"],
        "negative_rejected": report["negative_short_wall_dimensions_rejected"],
        "cases": [{"case": x["case"], "score": x.get("author_score"),
                   "dimensions": (x.get("author_metric_vector") or {}).get("right_dimensions"),
                   "status": x.get("scorer_status")} for x in report["results"]],
        "llm_calls": 0,
    }))
    return 0 if report["all_variants_scored"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
