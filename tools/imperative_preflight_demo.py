#!/usr/bin/env python3
"""Demonstrate Python solution.py text submission without running the code.

No model API calls. No untrusted Python execution. No IFC result creation.
Only trusted, reviewed G1 manual oracles are executable for parity tests.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from src.imperative_control.agent_runner import (
    CandidateCode,ControlConfig,ImperativeControlSession,
    create_matched_observations
)

SAMPLE_SOURCE="""import ifcopenshell
model = ifcopenshell.open("input.ifc")
wall = model.by_type("IfcWall")[0]
# A full code generation control must run only inside future #19 sandbox.
model.write("result.ifc")
"""

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-ifc",type=Path,
       default=Path("tests/fixtures/synthetic/input.ifc"))
    p=parser.parse_args()
    source=create_matched_observations(p.source_ifc,{
        "task_id":"OWN-G2-IMPERATIVE-PREFLIGHT-001",
        "instruction":"Change the North Wall height from 3m to 3.3m",
        "input_file":"input.ifc"
    })
    agent=ImperativeControlSession(source,ControlConfig())
    result=agent.submit_code(CandidateCode(source.input_ifc_sha256,SAMPLE_SOURCE))
    print(json.dumps({
        "status":result["status"],
        "source_ifc_sha256":source.input_ifc_sha256,
        "matched_source_observation_format":source.observation_format,
        "generated_python_executed":False,
        "IFC_result_created":False,
        "model_provider_calls":0,
        "requires_OS_sandbox_issue_19":True,
        "trace":agent.trace(),
    },indent=2,sort_keys=True))
    return 0 if result["status"]=="ACCEPTED_SOURCE_ONLY_NOT_EXECUTABLE" else 2

if __name__=="__main__":
    raise SystemExit(main())
