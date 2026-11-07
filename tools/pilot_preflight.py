#!/usr/bin/env python3
"""Offline-only G3 pilot candidate audit. This script cannot invoke a model.

Refuses pretending the public metadata-only task sample is frozen/ready.
Does NOT read .env, API keys, provider credentials, or full GT IFC.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.prepare_pilot_candidate import select

CANDIDATE=ROOT/"manifests/pilot_36_candidate_v0.json"
CONFIG=ROOT/"configs/pilot_36_plan_v0.json"
DRAFT=ROOT/"configs/pilot_v1.draft.yaml"
PINNED=ROOT/"manifests/bim_edit_revision.json"
G2=ROOT/"reports/G2_readiness.json"


def _sha(raw:bytes)->str:
    return sha256(raw).hexdigest()


def preflight(*,metadata:Path=ROOT/"data/tasks.jsonl",
              candidate:Path=CANDIDATE,
              plan:Path=CONFIG,
              protocol:Path=DRAFT,
              pinned:Path=PINNED,
              g2:Path=G2)->dict:
    problems=[]
    evidence={}
    config=json.loads(plan.read_text())
    manifest=json.loads(candidate.read_text())
    draft=yaml.safe_load(protocol.read_text())
    revision=json.loads(pinned.read_text())
    g2_report=json.loads(g2.read_text())
    expected_sha=revision["task_jsonl_sha256"]
    artifact_sha=_sha(candidate.read_bytes())
    evidence["public_task_manifest_sha256"]=artifact_sha
    evidence["dataset_revision"]=revision["task_revision"]
    evidence["public_tasks_data_sha256"]=expected_sha
    evidence["official_source_gt_files_audited"]=bool(revision.get("content_verified"))
    evidence["official_tasks_scored"]=int(g2_report["official_tasks_scored"])
    evidence["g2_gate_status"]=g2_report["status"]
    evidence["source_metadata_pinned"]=False
    evidence["candidate_reproducible"]=False
    evidence["per_task_IFC_GT_sha_verified"]=False
    evidence["provider_model_approved"]=False
    evidence["maximum_spend_explicitly_approved"]=False
    evidence["live_model_calls_permitted"]=False
    evidence["model_api_calls_made"]=0
    evidence["api_keys_inspected"]=False

    if not metadata.exists():
        problems.append("Pinned public task metadata not cached; cannot reconstruct candidate")
    else:
        actual=_sha(metadata.read_bytes())
        if actual!=expected_sha or actual!=manifest.get("task_data_sha256"):
            problems.append("Public task metadata SHA does not match pinned revision")
        elif manifest.get("task_revision")!=revision["task_revision"]:
            problems.append("Candidate uses an unexpected task revision")
        else:
            evidence["source_metadata_pinned"]=True
            recomputed=select(metadata)
            if recomputed!=manifest:
                problems.append("Candidate task IDs/strata differ from frozen deterministic sampler")
            else:
                evidence["candidate_reproducible"]=True

    rows=manifest.get("tasks",[])
    if len(rows)!=36 or len({r.get("task_id") for r in rows})!=36:
        problems.append("Candidate does not contain 36 unique task IDs")
    groups=Counter((r.get("operation"),r.get("category"),r.get("scene")) for r in rows)
    if len(groups)!=18 or set(groups.values())!={2}:
        problems.append("Candidate does not have exactly two IDs in each of 18 strata")
    if len({r.get("entity_type") for r in rows})!=6:
        problems.append("Candidate lacks at least one of the six IFC classes")
    if any(set(r)!={"task_id","operation","category","scene","entity_type"}
           for r in rows):
        problems.append("Candidate contains unapproved fields or hidden GT details")

    required_plan={
        "model_provider":None,"model_id":None,"model_snapshot_id":None,
        "actual_provider_spend_authorized":False,"paid_calls_enabled":False,
        "maximum_total_spend_usd_explicitly_authorized":False,
        "G2_release_gate_passed":False,"official_324_IFC_GT_coverage_verified":False,
        "official_evaluator_reproduced":False,
        "study_protocol_status":"DRAFT_NOT_FROZEN",
        "max_attempts_per_task":1,"feedback_mode":"one_shot",
        "tasks":36,"repetitions":1,
    }
    if any(config.get(k)!=v for k,v in required_plan.items()):
        problems.append("Current candidate must stay draft, unapproved and nonbilling")
    for key in ("model_id","model_provider","model_snapshot_id",
                "estimated_input_usd_per_million",
                "estimated_output_usd_per_million",
                "price_quote_revision","temperature"):
        if draft.get(key) is not None:
            problems.append("Unapproved model, cost or temperature in draft: "+key)
    if (draft.get("pilot_run_allowed") is not False
        or draft.get("pilot_frozen") is not False
        or draft.get("model_calling_enabled") is not False
        or draft.get("G2_release_gate_passed") is not False
        or draft.get("maximum_total_spend_usd_explicitly_authorized") is not False):
        problems.append("Draft YAML illegally claims live run authorization")

    if config.get("arms")!=draft.get("arms") or config.get("arms")!=["direct_xml","imperative_python"]:
        problems.append("Expected paired arm identities do not match current harness")
    for config_key,draft_key in (
        ("paired_trial_seeds","repetition_seeds"),
        ("scheduler_arm_shuffle_seed","paired_arm_order_shuffle_seed"),
        ("max_attempts_per_task","max_attempts_per_arm_task"),
        ("max_input_tokens_per_attempt","max_input_tokens_per_attempt"),
        ("max_output_tokens_per_attempt","max_output_tokens_per_attempt"),
        ("max_concurrent_attempts","max_concurrent_attempts"),
        ("maximum_total_spend_usd_proposed","maximum_total_spend_usd_proposed"),
    ):
        if config.get(config_key)!=draft.get(draft_key):
            problems.append("Configuration mismatch between JSON and YAML: "+config_key)

    evidence["candidate_size"]=len(rows)
    evidence["paired_arm_slots_per_repetition"]=len(rows)*len(config.get("arms",[]))
    evidence["paired_repetition_seeds"]=config.get("paired_trial_seeds",[])
    evidence["class_counts"]=dict(sorted(Counter(r.get("entity_type") for r in rows).items()))
    evidence["strata_counts"]=dict(sorted(
        ("/".join(key),count) for key,count in groups.items()
    ))
    evidence["candidate_only"]=manifest.get("status")=="CANDIDATE_NOT_PREREGISTERED"
    if not evidence["candidate_only"]:
        problems.append("Manifest claims preregistration without official content audit")

    if revision.get("content_verified") or g2_report.get("paid_run_ready"):
        problems.append("Unexpected previously unverified gate state changed; independent review needed")

    # Scientific release dependencies: these remain blockers, not syntax errors.
    missing=[
        "NO_FULL_PINNED_OFFICIAL_INPUT_GT_SHA_AUDIT",
        "NO_PER_TASK_MATCHED_D0_I0_OFFICIAL_CAPABILITY",
        "NO_INDEPENDENT_VERIFIED_OS_SANDBOX",
        "NO_OFFICIAL_EVALUATOR_SCORE_CALIBRATION",
        "NO_REAL_PROVIDER_BILLING_BROKER",
        "NO_APPROVED_MODEL_ID_AND_PRICE_SNAPSHOT",
        "NO_EXPLICIT_SPEND_AUTHORIZATION",
        "NO_PROSPECTIVELY_FROZEN_PREREGISTRATION",
    ]
    if g2_report.get("status")!="BLOCKED_FOR_LIVE_MODEL_PILOT":
        problems.append("Unexpected G2 gate status: manual inspection required")
    outcome={
        "status":"BLOCKED_NOT_A_RUNNABLE_PREREGISTRATION",
        "candidate_integrity":"PASS" if not problems else "FAIL",
        "candidate_sha256":artifact_sha,
        "official_benchmark_tasks_scored":0,
        "paid_model_calls":0,
        "problems":problems,
        "unmet_release_requirements":missing,
        "evidence":evidence,
    }
    return outcome


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata",type=Path,default=ROOT/"data/tasks.jsonl")
    parser.add_argument("--json-out",type=Path,help="Optional new output report path")
    args=parser.parse_args()
    try:
        outcome=preflight(metadata=args.metadata)
    except (ValueError,KeyError,TypeError,OSError) as exc:
        outcome={
            "status":"BLOCKED_PREFLIGHT_ERROR",
            "candidate_integrity":"FAIL",
            "error_type":type(exc).__name__,
            "official_benchmark_tasks_scored":0,
            "paid_model_calls":0,
        }
    if args.json_out is not None:
        if args.json_out.exists() or args.json_out.is_symlink():
            raise SystemExit("Report output must not overwrite a prior record")
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(outcome,indent=2,sort_keys=True)+"\n")
    print(json.dumps(outcome,indent=2,sort_keys=True))
    # Always fail closed: this command has no authorization/scheduling branch.
    return 2


if __name__=="__main__":
    raise SystemExit(main())
