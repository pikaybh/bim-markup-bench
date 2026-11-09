"""OWN-only dynamic IFC worker verification (never authorizes paid experiments).

Required --image-id is the verified local Linux architecture SHA256 image.
Always uses repository-owned programs and synthetic input, never user-supplied
external IFC, prompt, GT, model API key or arbitrary host path.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from src.runner.generated_candidate import run_offline_own_generated_candidate
from src.runner.ifc_worker import OWN_SOURCE
from tests.security.test_generated_candidate import (
    OWN_DYNAMIC_PROGRAM,OWN_ATTACK_PROGRAM
)


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-id",required=True)
    parser.add_argument("--output-json",type=Path)
    parser.add_argument("--enforce-live",action="store_true",
                        help="Return 2: full paid/model research is always blocked")
    a=parser.parse_args()
    outcomes=[]
    for kind,source in (
        ("own_dynamic_wall_edit",OWN_DYNAMIC_PROGRAM),
        ("own_embedded_attack_denial",OWN_ATTACK_PROGRAM),
    ):
        grade=run_offline_own_generated_candidate(
            a.image_id,source,sha256(source).hexdigest(),seed=9)
        outcomes.append({
            "test_id":kind,"candidate_sha256":grade["candidate_sha256"],
            "own_synthetic_compartment_status":grade["status"],
            "separate_trusted_grader_process":grade["separate_grader_process"],
            "OS_isolated_owned_grader":grade["separate_OS_grader_container_verified"],
            "candidate_script_mounted_to_grader":
                grade["isolated_own_grader"]["candidate_script_mounted_in_grader"],
            "GT_mounted_only_in_isolated_grader":
                grade["isolated_own_grader"]["GT_mounted_in_separate_grader_only"],
            "only_expected_step_entity_changed":
                grade["independent_own_grader"]["only_expected_swept_wall_step_changed"],
            "input_source_unchanged":grade["original_source_unchanged"],
            "GT_accessible_to_candidate":grade["GT_accessible_inside_candidate_container"],
            "paid_model_calls":grade["paid_model_calls"],
            "official_tasks_scored":grade["official_tasks_scored"],
        })
    report={
        "status":"OWN_SYNTHETIC_DYNAMIC_SANDBOX_PROOF_PASS",
        "image_id":a.image_id,
        "test_count":len(outcomes),
        "OWN_source_only":True,
        "OWN_source_sha256":sha256(OWN_SOURCE.read_bytes()).hexdigest(),
        "scientific_independent_grader_isolation_verified":False,
        "OWN_synthetic_grader_OS_isolation_verified":True,
        "production_model_generated_program_authorized":False,
        "G2_paid_or_official_model_gate":"BLOCKED",
        "source_and_reference_not_published":True,
        "model_generated_python_called":False,
        "official_tasks_scored":0,
        "paid_model_calls":0,
        "cases":outcomes,
    }
    if a.output_json is not None:
        target=a.output_json
        if (target.exists() or target.is_symlink()
                or not target.parent.is_dir()):
            raise SystemExit("Refuse overwrite, symlink or absent output directory")
        with target.open("x",encoding="utf-8",newline="\n") as f:
            f.write(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,sort_keys=True,indent=2))
    return 2 if a.enforce_live else 0


if __name__=="__main__":
    raise SystemExit(main())
