#!/usr/bin/env python3
"""Offline own synthetic IFC worker OS/security tests. No LLM or official GT."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from src.runner.ifc_worker import run_own_fixture
from src.runner.docker_isolation import DockerIsolationError

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-id",required=True,
                        help="The exact local SHA256 image ID built from pinned Dockerfile")
    parser.add_argument("--output-json",type=Path)
    parser.add_argument("--enforce-live",action="store_true",
                        help="Always fail until approved real generated-code worker and billing broker exist")
    opts=parser.parse_args()
    cases=("trusted-native-smoke","edit-wall","deny-attacks",
           "oversize-output","infinite-loop")
    passed={}
    try:
        for case in cases:
            result=run_own_fixture(opts.image_id,case,wall_seconds=3 if case=="infinite-loop" else 20)
            correct="BLOCKED_WALL_CLOCK_TIMEOUT" if case=="infinite-loop" else "OWN_TRUSTED_WORKER_FIXTURE_PASS"
            passed[case]=result["status"]==correct
            if not passed[case]:
                raise DockerIsolationError("Expected positive/negative worker test failed")
        data={
            "status":"CURATED_WORKER_OWN_SYNTHETIC_TESTS_PASS",
            "python":"3.12.16","ifcopenshell":"0.8.4.post1",
            "validated_own_fixture_cases":passed,
            "model_generated_code_executed":False,
            "authorized_live_worker_available":False,
            "raw_official_gt_used":False,
            "paid_model_calls":0,
            "official_tasks_scored":0,
            "G2_paid_pilot_gate":"BLOCKED",
        }
    except (DockerIsolationError,OSError,ValueError,KeyError):
        data={
            "status":"BLOCKED_WORKER_TEST_FAILED",
            "model_generated_code_executed":False,
            "paid_model_calls":0,
            "G2_paid_pilot_gate":"BLOCKED",
        }
    text=json.dumps(data,indent=2,sort_keys=True)+"\n"
    if opts.output_json:
        p=opts.output_json
        if p.is_symlink() or p.exists() or not p.parent.is_dir():
            raise SystemExit("Refuse overwrite/symlink/missing evidence directory")
        with p.open("x",encoding="utf-8") as file:
            file.write(text)
    print(text,end="")
    if data["status"]!="CURATED_WORKER_OWN_SYNTHETIC_TESTS_PASS":
        return 2
    return 2 if opts.enforce_live else 0

if __name__=="__main__":
    raise SystemExit(main())
