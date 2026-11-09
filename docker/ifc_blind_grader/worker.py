"""Read-only, arm-blind independent IFC scorer executable IN grader image.

This image never sees agent scripts, XML prompts, model tokens or any
untrusted executable files. Trusted task targets exist in its own
read-only metadata mount and never appear in scorer output.
Official BIM-Edit evaluator equivalence has NOT been established.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

from src.evaluation.bim_edit_scorer import (
    GraderTask,score_ifc_result,PROVENANCE,EVALUATOR_VERSION
)

_SOURCE=Path("/source/input.ifc")
_REFERENCE=Path("/ground_truth/expected.ifc")
_PREDICTION=Path("/prediction/result.ifc")
_META=Path("/metadata/task.json")


def main()->int:
    raw=json.loads(_META.read_text(encoding="utf-8"))
    if not isinstance(raw,dict) or set(raw)!={
        "task_id","operation","target_class","target_guids"
    }:
        raise ValueError("Unexpected blind grader target metadata")
    if not isinstance(raw["target_guids"],list):
        raise ValueError("Hidden target GUIDs must be a JSON list")
    task=GraderTask(raw["task_id"],raw["operation"],raw["target_class"],
                    tuple(raw["target_guids"]))
    result=score_ifc_result(
        source_ifc=_SOURCE,ground_truth_ifc=_REFERENCE,
        result_ifc=_PREDICTION,task=task)
    if (result["metric_origin"]!=PROVENANCE or
            result["scorer_version"]!=EVALUATOR_VERSION or
            result["official_bim_edit_evaluator_equivalent"] is not False or
            result["scored_official_dataset"] is not False):
        raise ValueError("Evaluator provenance unexpectedly changed")
    # Whitelisted compact fields only; never emit path, GT hash, target GUID,
    # target matching internals, source/user instructions, or raw IFC bytes.
    report={
        "task_id":task.task_id,
        "status":result["status"],
        "scorer_version":result["scorer_version"],
        "metric_origin":result["metric_origin"],
        "official_bim_edit_evaluator_equivalent":False,
        "official_tasks_scored":0,
        "geometry":result["geometry"],
        "semantics":result["semantics"],
        "topology":result["topology"],
        "final_score":result["final_score"],
        "strict_pass":result["strict_pass"],
        "failure_codes":result["failure_codes"][:8],
        "reference_or_target_metadata_in_agent_context":False,
        "paid_model_calls":0,
    }
    print(json.dumps(report,sort_keys=True,separators=(",",":")))
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (ValueError,KeyError,TypeError,RuntimeError,OSError) as exc:
        # No error tracebacks with raw task GUIDs or hidden paths.
        print("BLIND_IFC_SCORER_REFUSED",file=sys.stderr)
        raise SystemExit(2)
