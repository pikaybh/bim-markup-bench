#!/usr/bin/env python3
"""No-network G1 deterministic coverage and paid-pilot blocker.

Generates only sanitized task metadata (no GT paths/target GUIDs/prompts).
With --enforce, exits 2 unless ALL official input/GT/evaluator/engine gates pass.
The current experimental G1 slice is always BLOCKED for full primary pilot.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from src.data.bim_edit import AuditError,read_tasks
from src.evaluation.g1_coverage import write_report,GATE_BLOCKED

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tasks",type=Path,default=Path("data/tasks.jsonl"))
    p.add_argument("--output",type=Path,default=Path("reports/g1_324_support_matrix.json"))
    p.add_argument("--enforce",action="store_true")
    options=p.parse_args()
    try:
        rows=read_tasks(options.tasks)
        result=write_report(rows,options.output)
    except (AuditError,OSError,ValueError) as exc:
        print(json.dumps({"status":"BLOCKED","message":type(exc).__name__},sort_keys=True))
        return 2
    public={key:result[key] for key in (
        "status","coverage_accounted_for","official_tasks_scored",
        "verified_official_engine_supported","static_engine_unsupported_count",
        "conditional_source_dependent_unverified_count","model_api_calls",
    )}
    public["report"]=options.output.name
    print(json.dumps(public,indent=2,sort_keys=True))
    return 2 if options.enforce and result["status"]==GATE_BLOCKED else 0

if __name__=="__main__":
    raise SystemExit(main())
