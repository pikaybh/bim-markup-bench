#!/usr/bin/env python3
"""Independent synthetic scorer calibration + conservative G2 release gate.

No OpenAI API, no generated Python execution, no official GT IFC content.
Outputs are local, reproducible synthetic tests and metadata-only ledger.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

from src.evaluation.calibration import (
    calibrate_own_synthetic,tolerance_sensitivity
)
from src.evaluation.capability_matrix import (
    build_capability_rows,write_capability_csv
)
from src.evaluation.metric_contract import final_score

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,
                        default=Path("reports/evaluator_calibration.json"))
    parser.add_argument("--matrix",type=Path,
                        default=Path("reports/arm_capability_matrix.csv"))
    parser.add_argument("--gate",type=Path,
                        default=Path("reports/G2_readiness.json"))
    parser.add_argument("--metadata",type=Path,
                        default=Path("data/tasks.jsonl"))
    parser.add_argument("--enforce",action="store_true",
                        help="Exit 2 until external official/G2 security gates pass")
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="independent-ifc-calibration-") as temp:
        root=Path(temp)
        result=calibrate_own_synthetic(root)
        result["tolerance_sensitivity"]=tolerance_sensitivity(root)
    if not result["all_frozen_expectations_pass"]:
        print(json.dumps({"status":"FAILED_INDEPENDENT_CALIBRATION",
                          "matched":result["synthetic_cases_matching_frozen_expectations"]}))
        return 2
    matrix=build_capability_rows(args.metadata)
    result["paper_scalar_arithmetic_only"]={
        "door_perfect_mean":final_score(1.,1.,1.)["final_score"],
        "wall_length_example_mean":final_score(1.,1.,.47)["final_score"],
        "wall_thickness_example_mean":final_score(.38,.72,1.)["final_score"],
        "source":"paper-rounded-components-only-not-model-reproduction",
    }
    gates={
        "schema_version":"g2-readiness-gate-v0.1",
        "status":"BLOCKED_FOR_LIVE_MODEL_PILOT",
        "gates":{
            "G1_independent_synthetic_D0_I0_six_oracles":"YES_SYNTHETIC_ONLY",
            "G2_direct_markup_text_only_mock":"YES_OFFLINE_ONLY",
            "G2_python_baseline_preflight":"YES_CODE_NOT_EXECUTABLE",
            "G2_per_task_file_layout":"YES_SAME_USER_ONLY",
            "G2_offline_paired_schedule":"YES_EIGHT_MOCK_TRIALS",
            "G2_independent_scorer_calibration":(
                "YES_OWN_SYNTHETIC_ONLY" if result["all_frozen_expectations_pass"]
                else "NO"
            ),
            "G0_official_IFC_input_GT_324_content_audit":"NO",
            "G1_full_six_class_official_CRUD_coverage":"NO",
            "G2_official_evaluator_provenance_reproduced":"NO",
            "G2_verified_OS_network_process_secret_isolation":"NO",
            "G2_real_model_provider_billing_broker":"NO",
            "G2_independent_official_score_calibration":"NO",
            "G3_explicit_paid_run_approval":"NO",
        },
        "synthetic_calibration_cases":result["evaluated_own_synthetic_cases"],
        "synthetic_expected_checks_passed":result["synthetic_cases_matching_frozen_expectations"],
        "official_tasks_scored":0,
        "verified_official_D0_tasks":0,
        "verified_official_I0_tasks":0,
        "provider_model_calls":0,
        "OS_generated_python_execution_enabled":False,
        "paid_run_ready":False,
        "model_API_keys_required":False,
        "unmet_prerequisites":[
            "Full official 324 source/GT IFC content verification",
            "Independent official metric implementation or explicitly audited alternative",
            "Real OS/VM process, filesystem, network and secret isolation",
            "Official task-level D0/I0 matched capability and full-context auditing",
            "Durable live provider/budget/token/time enforcement and explicit approval",
        ],
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(
        json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    write_capability_csv(matrix,args.matrix)
    args.gate.parent.mkdir(parents=True,exist_ok=True)
    args.gate.write_text(
        json.dumps(gates,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps({
        "calibration_cases":result["evaluated_own_synthetic_cases"],
        "expectations_satisfied":result["synthetic_cases_matching_frozen_expectations"],
        "capability_matrix_rows":len(matrix),
        "official_tasks_scored":0,
        "model_calls":0,
        "status":gates["status"],
        "paid_run_ready":False,
    },sort_keys=True,indent=2))
    return 2 if args.enforce else 0

if __name__=="__main__":
    raise SystemExit(main())
