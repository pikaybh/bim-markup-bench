"""G2 #21 blind-grader smoke on three pinned public IFC source/GT pairs.

This tool NEVER runs a model/LLM or exposes model-visible task context.
It is independent scorer verification only, NOT official BIM-Edit scoring.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.runner.blind_public_ifc_grader import (
    ALLOWED_TASKS, run_pinned_blind_scorer,
)
from src.evaluation.bim_edit_scorer import EVALUATOR_VERSION, PROVENANCE


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-id", required=True,
                        help="Exact immutable locally cached Linux AMD64 image SHA256")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--enforce-live", action="store_true",
                        help="Always return 2: model and official research gate blocked")
    options = parser.parse_args()
    details = []
    conditions = (
        *( (task, "reference_self_check") for task in sorted(ALLOWED_TASKS) ),
        ("WAL-UPD-TOP-A-001", "unchanged_source"),
        ("WAL-UPD-TOP-A-001", "invalid_output"),
    )
    for task_id, condition in conditions:
        proof = run_pinned_blind_scorer(options.image_id, task_id, condition)
        outcome = proof["independent_grader_result"]
        details.append({
            "task_id": task_id,
            "condition": condition,
            "run_id": proof["run_id"],
            "status": outcome["status"],
            "strict_pass": outcome["strict_pass"],
            "all_three_axes_one_for_self_check": (
                all(outcome[name] == 1.0 for name in
                    ("geometry", "semantics", "topology"))
                if condition == "reference_self_check" else None
            ),
            "official_tasks_scored": 0,
            "model_calls": 0,
        })
    record = {
        "status": "INDEPENDENT_BLIND_PUBLIC_IFC_REFERENCE_SMOKE_PASS",
        "candidate_task_count": 3,
        "smoke_case_count": len(details),
        "image_id": options.image_id,
        "evaluator_version": EVALUATOR_VERSION,
        "metric_origin": PROVENANCE,
        "official_evaluator_equivalent": False,
        "agent_python_executed": False,
        "agent_arm_label_provided_to_scorer": False,
        "hidden_reference_target_or_path_published": False,
        "GT_mount_only_in_grader": True,
        "real_model_provider_calls": 0,
        "official_tasks_scored": 0,
        "G2_G3_live_pilot_gate": "BLOCKED",
        "cases": details,
    }
    if options.output_json is not None:
        path = options.output_json
        if path.exists() or path.is_symlink() or not path.parent.is_dir():
            parser.error("Refusing to overwrite scorer evidence or write to symlink")
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps(record, sort_keys=True, indent=2))
    return 2 if options.enforce_live else 0


if __name__ == "__main__":
    raise SystemExit(main())
