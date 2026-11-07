#!/usr/bin/env python3
"""Own synthetic IFC-only evaluator demo. Never an official BIM-Edit score."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import ifcopenshell
import jsonschema

from src.evaluation.bim_edit_scorer import GraderTask,score_ifc_result

ROOT=Path(__file__).resolve().parents[1]
SYNTHETIC=ROOT/"tests/fixtures/synthetic"
SOURCE=SYNTHETIC/"input.ifc"
GT=SYNTHETIC/"expected_wall_height.ifc"
SCHEMA=ROOT/"schemas/score_result.schema.json"

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prediction",type=Path,default=GT)
    parser.add_argument("--output-json",type=Path)
    opts=parser.parse_args()
    guid=ifcopenshell.open(str(SOURCE)).by_type("IfcWall")[0].GlobalId
    task=GraderTask("OWN-SYNTHETIC-WALL-HEIGHT-001","update",
                    "IfcWall",(guid,))
    result=score_ifc_result(
        source_ifc=SOURCE,ground_truth_ifc=GT,
        result_ifc=opts.prediction,task=task)
    jsonschema.validate(result,json.loads(SCHEMA.read_text()))
    text=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if opts.output_json is not None:
        if opts.output_json.is_symlink() or opts.output_json.exists():
            raise SystemExit("Refusing to overwrite preexisting scorer record")
        with opts.output_json.open("x",encoding="utf-8") as f:
            f.write(text)
    print(text,end="")
    return 0 if result["status"]=="INDEPENDENT_IFC_SCORED" else 2

if __name__=="__main__":
    raise SystemExit(main())
