"""Immutable per-attempt JSON record and deterministic paired-arm scheduling."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import re


TASK_ID_RE=re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,110}$")
ARMS=("direct_xml","imperative_python")

class RunManifestError(ValueError):
    pass

@dataclass(frozen=True)
class TrialSlot:
    task_id:str
    arm:str
    seed:int
    attempt:int
    run_id:str


def make_run_id(experiment_id:str,task_id:str,arm:str,
                seed:int,attempt:int,input_sha256:str)->str:
    if not TASK_ID_RE.fullmatch(task_id) or not TASK_ID_RE.fullmatch(experiment_id):
        raise RunManifestError("Invalid task/experiment identifier")
    if arm not in ARMS or type(seed) is not int or seed<0 or type(attempt) is not int or attempt<0:
        raise RunManifestError("Invalid arm, seed or attempt")
    if not re.fullmatch(r"[0-9a-f]{64}",input_sha256):
        raise RunManifestError("Input IFC SHA-256 invalid")
    content=f"g2-manifest-v0:{experiment_id}:{task_id}:{arm}:{seed}:{attempt}:{input_sha256}"
    return "r-"+hashlib.sha256(content.encode()).hexdigest()[:32]


def paired_schedule(tasks:list[dict],seeds:tuple[int,...],
                    experiment_id:str,input_sha256:str,attempt:int=0,
                    shuffle_seed:int=0)->tuple[TrialSlot,...]:
    if not tasks or not seeds:
        raise RunManifestError("Empty mock task/seed set")
    sorted_tasks=sorted(tasks,key=lambda r:r["task_id"])
    if len({t["task_id"] for t in sorted_tasks})!=len(sorted_tasks):
        raise RunManifestError("Duplicate task ID in mock scheduler")
    slots=[]
    for task in sorted_tasks:
        for seed in sorted(set(seeds)):
            arms=list(ARMS)
            # Randomized arm order with deterministic seeded draw; the
            # shuffled run order is fixed per task/seed/experiment.
            source=f"{shuffle_seed}:{experiment_id}:{task['task_id']}:{seed}"
            rand_seed=int(hashlib.sha256(source.encode()).hexdigest()[:16],16)
            random.Random(rand_seed).shuffle(arms)
            for arm in arms:
                slots.append(TrialSlot(
                    task_id=task["task_id"],arm=arm,seed=seed,
                    attempt=attempt,
                    run_id=make_run_id(experiment_id,task["task_id"],
                                       arm,seed,attempt,input_sha256),
                ))
    return tuple(slots)


def persist_record(root:Path,record:dict)->Path:
    if root.is_symlink():
        raise RunManifestError("Manifest root must not be a symlink")
    root.mkdir(parents=True,exist_ok=True)
    run_id=record["run_id"]
    if not re.fullmatch(r"r-[a-f0-9]{32}",run_id):
        raise RunManifestError("Invalid run ID in record")
    location=root/(run_id+".json")
    # Exclusive creation is atomic. No retry overwrites prior data.
    try:
        with location.open("x",encoding="utf-8") as stream:
            json.dump(record,stream,indent=2,sort_keys=True)
            stream.write("\n")
            stream.flush()
    except FileExistsError as exc:
        raise RunManifestError("Duplicate trial already persisted") from exc
    return location


def read_existing(root:Path,run_id:str)->dict|None:
    target=root/(run_id+".json")
    if target.is_symlink():
        raise RunManifestError("Recorded manifest must not be a symlink")
    if not target.exists():
        return None
    if target.is_symlink() or not target.is_file():
        raise RunManifestError("Recorded run is not a regular file")
    data=json.loads(target.read_text(encoding="utf-8"))
    if data.get("run_id")!=run_id:
        raise RunManifestError("Recorded run ID mismatch")
    return data


def verify_record_artifacts(output_root:Path,record:dict)->None:
    """Verify all immutable artifacts on resume/report; never trust references.

    This is an offline integrity test, not a secure operating-system boundary.
    """
    refs=record.get("artifact_refs")
    hashes=record.get("artifact_sha256s")
    if not isinstance(refs,dict) or not isinstance(hashes,dict) or set(refs)!=set(hashes):
        raise RunManifestError("Incomplete recorded artifact hash inventory")
    if output_root.is_symlink() or not output_root.is_dir():
        raise RunManifestError("Unsafe output root")
    for key,path in refs.items():
        if not isinstance(path,str) or not path.startswith("trials/"+record["run_id"]+"/"):
            raise RunManifestError("Artifact ref escaped trial directory")
        file=output_root/path
        if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(output_root.resolve()):
            raise RunManifestError("Recorded artifact is missing or escaped")
        observed=hashlib.sha256(file.read_bytes()).hexdigest()
        if observed!=hashes[key]:
            raise RunManifestError("Immutable artifact hash mismatch")
    if hashes["source"]!=record["source_artifact_sha256"]:
        raise RunManifestError("Source artifact digest and manifest disagree")
    if hashes["raw_response"]!=record["raw_response_sha256"]:
        raise RunManifestError("Raw model response digest and manifest disagree")
    if hashes["model_context"]!=record["model_input_sha256"]:
        raise RunManifestError("Model input digest and manifest disagree")


# Proposed G3 three-arm contract: isolated from the released two-arm ARMS API.
# Candidate slots are NEVER accepted by make_run_id, workers, or paid providers.
THREE_ARM_DRAFT=("D_FULL","D_MANAGED","I_NATIVE")
THREE_ARM_PROPOSAL_PATH="configs/pilot_36_three_arm_candidate_v0.json"
THREE_ARM_ORIGINAL_PLAN_SHA="dfc1b27ff933a73834c18d16b16e1ff822a729e801d70e26d4d4dd28efdf77a1"
THREE_ARM_PILOT_SHA="75b4847814dbefad95340556c0b62f9cda72cac319cd82ecb23ea4933c9ab694"
THREE_ARM_G3_SHA="c78650e8e30f50029237e927ae6006e18a92e9872416e9e75c03290db22abad8"


class ThreeArmDraftBlocked(RunManifestError):
    """No provider calls, model-generated program, scoring or arm approval."""


def _pinned_proposal_evidence(root:Path,relative:str,digest:str)->dict:
    path=root/relative
    if path.is_symlink() or not path.is_file():
        raise ThreeArmDraftBlocked("Frozen source missing or symlinked")
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=digest:
        raise ThreeArmDraftBlocked("Frozen source content changed")
    return json.loads(raw)


def validate_three_arm_candidate(root:Path,proposal:dict)->dict:
    """Fail closed on scientific treatment gaps, original frozen sample, or budgets."""
    from src.data.pilot_workspace import _frozen_inputs,pilot_staging_preflight,ARMS as STAGE_ARMS
    from src.direct_markup.agent_runner import SourceOnlySettings, LANGUAGE_SPEC
    from src.imperative_control.agent_runner import ControlConfig, API_NOTES
    old=_pinned_proposal_evidence(root,"configs/pilot_36_plan_v0.json",THREE_ARM_ORIGINAL_PLAN_SHA)
    pilot=_pinned_proposal_evidence(root,"manifests/pilot_36_candidate_v0.json",THREE_ARM_PILOT_SHA)
    g3=_pinned_proposal_evidence(
        root,"reports/g3_bim_edit_36_task_information_and_tool_parity_20261119.json",THREE_ARM_G3_SHA
    )
    selected,audited,_,_=_frozen_inputs(root)
    preflight=pilot_staging_preflight(root)
    if (old["arms"]!=list(ARMS) or old["study_protocol_status"]!="DRAFT_NOT_FROZEN"
            or old["paid_calls_enabled"] is not False
            or len(pilot["tasks"])!=36
            or set(selected)!={r["task_id"] for r in pilot["tasks"]}
            or preflight["input_available_tasks"]!=30
            or preflight["blocked_input_tasks"]!=6
            or preflight["llm_launch_allowed"] is not False
            or g3["actual_independent_d_and_i_source_text_matches"]!=30
            or g3["same_exact_provider_tokens_measured"] is not False):
        raise ThreeArmDraftBlocked("Frozen original study or G3 evidence diverged")
    # Compare actual MODEL-VISIBLE text bytes, never host CRLF file-byte counts.
    # A changed XML language spec or imperative API note invalidates this draft.
    for path,expected_size,expected_hash in (
        (LANGUAGE_SPEC,7383,"05703e0ba035ccddfe942593dbe6e4c2355d989fd86ec97b6ad70985c53a284e"),
        (API_NOTES,1113,"cb6f952ee2b3e6e1f69836e99c3681dbdaf4071bcfb045843778c35f53a26901"),
    ):
        if path.is_symlink() or not path.is_file():
            raise ThreeArmDraftBlocked("Arm documentation missing or symlinked")
        observed=path.read_text(encoding="utf8").encode("utf8")
        if len(observed)!=expected_size or hashlib.sha256(observed).hexdigest()!=expected_hash:
            raise ThreeArmDraftBlocked("Actual model-visible language/API documentation changed")
    if g3["I_only_extra_api_notes"]["sha256"]!="cb6f952ee2b3e6e1f69836e99c3681dbdaf4071bcfb045843778c35f53a26901":
        raise ThreeArmDraftBlocked("G3 imperative-only API note evidence mismatch")
    if not isinstance(proposal,dict) or set(proposal)!={
        "status","proposal_id","original_two_arm_plan_sha256",
        "original_36_task_pilot_sha256","original_g3_source_differential_sha256",
        "arms","arm_contracts","shared_limits","randomized_order","provider","execution"
    }:
        raise ThreeArmDraftBlocked("Unexpected proposed three-arm contract fields")
    if (proposal["status"]!="DRAFT_3ARM_NOT_PREREGISTERED"
            or proposal["proposal_id"]!="bim-edit-36-three-arm-candidate-v0"
            or proposal["original_two_arm_plan_sha256"]!=THREE_ARM_ORIGINAL_PLAN_SHA
            or proposal["original_36_task_pilot_sha256"]!=THREE_ARM_PILOT_SHA
            or proposal["original_g3_source_differential_sha256"]!=THREE_ARM_G3_SHA
            or proposal["arms"]!=list(THREE_ARM_DRAFT)
            or proposal["arms"]!=list(STAGE_ARMS)):
        raise ThreeArmDraftBlocked("Different arms, revisions or registration claims")
    expect={
        "D_FULL":("XML_FILE_EDIT","SHARED_XML_LANGUAGE_SPEC_ONLY",
                  "FULL_DECLARATIVE_NOT_IMPLEMENTED"),
        "D_MANAGED":("XML_FILE_EDIT","SHARED_XML_LANGUAGE_SPEC_ONLY",
                      "MANAGED_AND_FULL_CONTRAST_NOT_VERIFIED"),
        "I_NATIVE":("PYTHON_TEXT_SUBMISSION",
                    "SHARED_XML_SPEC_PLUS_I_ONLY_1113_BYTE_IFCOPENSHELL_REFERENCE",
                    "ORIGINAL_TASK_PYTHON_RUNNER_NOT_ENABLED"),
    }
    if not isinstance(proposal["arm_contracts"],dict) or set(proposal["arm_contracts"])!=set(expect):
        raise ThreeArmDraftBlocked("Three complete, distinct contracts required")
    for arm,(mode,notes,missing) in expect.items():
        if proposal["arm_contracts"][arm]!={
            "input_view":"CURRENT_G2_V01_XML_SOURCE_PROJECTION",
            "authoring":mode,"api_guidance":notes,"native_capability":missing,
            "tool_status":"NOT_APPROVED_FOR_BENCHMARK"
        }:
            raise ThreeArmDraftBlocked("Arm capability was falsely promoted")
    limits={
        "max_attempts_per_task_arm":1,"max_wall_seconds_per_task_arm":180,
        "max_submission_utf8_bytes":32768,"max_model_input_tokens_per_attempt":20000,
        "max_model_output_tokens_per_attempt":6000,"max_model_authored_submissions":1,
        "feedback_rounds":0,"max_concurrent_model_calls":1
    }
    if proposal["shared_limits"]!=limits:
        raise ThreeArmDraftBlocked("Missing or asymmetric resource/feedback ceiling")
    if (limits["max_attempts_per_task_arm"]!=old["max_attempts_per_task"]
            or limits["max_wall_seconds_per_task_arm"]!=old["max_wall_seconds_per_arm_task"]
            or limits["max_model_input_tokens_per_attempt"]!=old["max_input_tokens_per_attempt"]
            or limits["max_model_output_tokens_per_attempt"]!=old["max_output_tokens_per_attempt"]):
        raise ThreeArmDraftBlocked("Proposed ceilings disagree with old draft")
    d,i=SourceOnlySettings(),ControlConfig()
    if (d.mode!="one_shot" or i.mode!="one_shot"
            or d.max_attempts!=i.max_attempts or d.max_attempts!=1
            or d.max_wall_seconds!=i.max_wall_seconds or d.max_wall_seconds!=180
            or d.max_edit_bytes!=i.max_output_bytes or d.max_edit_bytes!=32768):
        raise ThreeArmDraftBlocked("Actual D/I existing adapter policy differs")
    if proposal["randomized_order"]!={
        "seed":1234,"allocation":"BALANCED_6_PERMUTATIONS_REPEATED_6_TIMES",
        "full_sample_includes_blocked":True
    }:
        raise ThreeArmDraftBlocked("Arm order or missing task accounting changed")
    if proposal["provider"]!={
        "provider_id":None,"model_snapshot_id":None,
        "verified_exact_tokenizer_revision":None,"provider_usage_receipts":False,
        "verified_price_revision":None,"external_IFC_transfer_approved":False,
        "maximum_total_spend_usd_authorized":False,"paid_calls_enabled":False
    } or proposal["execution"]!={
        "dataset_original_tasks":36,"available_source_rows":30,
        "missing_input_rows":6,"original_GT_opened":False,
        "model_generated_code_enabled":False,"experiment_registered":False,
        "scientific_release_enabled":False
    }:
        raise ThreeArmDraftBlocked("Unverified model/rights/scoring/billing was elevated")
    return {"selected":selected,"audited":audited,"preflight":preflight}


def validate_synthetic_one_shot_trace(arm:str,events:list[dict])->dict:
    """Pure simulated tool event, NEVER an actual model usage receipt."""
    if arm not in THREE_ARM_DRAFT or type(events) is not list or len(events)!=1:
        raise ThreeArmDraftBlocked("Three-arm one-shot permits precisely one submission")
    item=events[0]
    expected="submit_python_text" if arm=="I_NATIVE" else "edit_xml"
    if (type(item) is not dict or set(item)!={"action","payload_bytes","feedback_round"}
            or item["action"]!=expected
            or type(item["payload_bytes"]) is not int
            or not 1<=item["payload_bytes"]<=32768
            or type(item["feedback_round"]) is not int or item["feedback_round"]!=0):
        raise ThreeArmDraftBlocked("Tool action, output bytes or forbidden feedback mismatch")
    return {"arm":arm,"status":"SYNTHETIC_TRACE_POLICY_PASS",
            "provider_calls":0,"actual_provider_tokens":None,
            "real_tool_runtime_verified":False}


def three_arm_candidate_schedule(root:Path,proposal:dict)->dict:
    """Deterministic balanced 36x3 offline plan; ZERO TrialSlot objects are runnable."""
    from itertools import permutations
    from src.data.bim_edit import repo_asset_path
    proof=validate_three_arm_candidate(root,proposal)
    selected,audited,preflight=(proof[k] for k in ("selected","audited","preflight"))
    task_ids=sorted(selected)
    random.Random(1234).shuffle(task_ids)
    balanced=list(sorted(permutations(THREE_ARM_DRAFT)))
    rows=[]
    for index,tid in enumerate(task_ids):
        record=audited[repo_asset_path(selected[tid]["input_ifc"])]
        available=preflight["task_status"][tid]=="STAGING_INPUT_AVAILABLE_NO_LAUNCH"
        digest=record.get("byte_sha256_verified") if available else None
        if available and (not isinstance(digest,str)
                          or re.fullmatch(r"[0-9a-f]{64}",digest) is None):
            raise ThreeArmDraftBlocked("Available source missing byte-level identity")
        for position,arm in enumerate(balanced[index%6]):
            slot_id="candidate-"+hashlib.sha256(
                f"three-arm-unregistered-v0:{tid}:{arm}:11:0:{digest or 'MISSING'}".encode()
            ).hexdigest()[:24]
            rows.append({
                "task_id":tid,"arm":arm,"order_position":position,
                "source_sha256":digest,
                "status":("SOURCE_AVAILABLE_STUDY_BLOCKED"
                          if available else "ORIGINAL_INPUT_ABSENT_BLOCKED"),
                "candidate_slot_id":slot_id,"trial_launch_allowed":False,
            })
    by_position={
        arm:[sum(item["arm"]==arm and item["order_position"]==pos for item in rows)
             for pos in range(3)]
        for arm in THREE_ARM_DRAFT
    }
    if (len(rows)!=108 or len({r["candidate_slot_id"] for r in rows})!=108
            or sum(r["source_sha256"] is not None for r in rows)!=90
            or sum(r["source_sha256"] is None for r in rows)!=18
            or any(positions!=[12,12,12] for positions in by_position.values())):
        raise ThreeArmDraftBlocked("Paired 108-slot counterbalanced denominator violated")
    for tid in selected:
        subset=[r for r in rows if r["task_id"]==tid]
        if len(subset)!=3 or len({r["source_sha256"] for r in subset})!=1:
            raise ThreeArmDraftBlocked("Within-task arm content identity violated")
    mock=[
        validate_synthetic_one_shot_trace(arm,[{
            "action":"submit_python_text" if arm=="I_NATIVE" else "edit_xml",
            "payload_bytes":128,"feedback_round":0
        }])
        for arm in THREE_ARM_DRAFT
    ]
    return {
        "status":"DRAFT_3ARM_SCHEDULE_ONLY_NOT_PREREGISTERED",
        "original_pilot_sha256":THREE_ARM_PILOT_SHA,
        "old_two_arm_plan_sha256":THREE_ARM_ORIGINAL_PLAN_SHA,
        "g3_observed_information_sha256":THREE_ARM_G3_SHA,
        "original_task_denominator":36,
        "source_available_task_rows":30,"source_missing_task_rows":6,
        "candidate_slots_all":108,"source_available_nonrunnable_slots":90,
        "missing_source_blocked_slots":18,"runnable_slots":0,
        "arm_order_by_position":by_position,
        "all_within_task_source_hashes_equal":True,
        "synthetic_tool_events":mock,
        "shared_input_token_ceiling_planned":20000,
        "shared_output_token_ceiling_planned":6000,
        "one_shot_feedback_rounds":0,"max_utf8_submission_bytes":32768,
        "actual_provider_input_tokens":None,"actual_provider_output_tokens":None,
        "verified_model_tokenizer":False,"provider_usage_receipt_verified":False,
        "D_full_native_coverage_verified":False,
        "D_full_vs_managed_treatment_difference_verified":False,
        "actual_live_tool_feedback_parity_verified":False,
        "live_provider_calls":0,"official_tasks_scored":0,
        "approved_for_preregistration":False,"model_launch_allowed":False,
        "release_gate":"BLOCKED_UNVERIFIED_THREE_ARM_TREATMENTS_TOKENIZER_RIGHTS_SCORER",
        "candidate_slots":rows,
    }



def validate_synthetic_token_ceiling(*,input_tokens:int,output_tokens:int)->dict:
    """Only laboratory-supplied fake counts, NOT model/provider token receipts."""
    if (type(input_tokens) is not int or type(output_tokens) is not int
            or not 1<=input_tokens<=20000 or not 0<=output_tokens<=6000):
        raise ThreeArmDraftBlocked("Mock provider-token envelope violates draft ceilings")
    return {"status":"SYNTHETIC_TOKEN_CEILING_ONLY","mock_input_tokens":input_tokens,
            "mock_output_tokens":output_tokens,"real_provider_usage_receipt":None,
            "true_provider_token_count_verified":False,"provider_calls":0}


def _candidate_three_arm_cli()->int:
    import argparse
    parser=argparse.ArgumentParser(
        description="Offline, unfrozen 108-slot planning only; NO model/IFC trial"
    )
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write-three-arm-draft",action="store_true")
    mode.add_argument("--check-three-arm-draft",action="store_true")
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    plan_file=root/THREE_ARM_PROPOSAL_PATH
    if plan_file.is_symlink() or not plan_file.is_file():
        raise ThreeArmDraftBlocked("Proposed study contract unavailable or symlinked")
    plan=json.loads(plan_file.read_text(encoding="utf8"))
    report=three_arm_candidate_schedule(root,plan)
    canonical=(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf8")
    destination=root/"reports/g3_three_arm_108_slot_candidate_schedule_20261120.json"
    if args.write_three_arm_draft:
        with destination.open("xb") as stream:
            stream.write(canonical)
    elif (destination.is_symlink() or not destination.is_file()
          or destination.read_bytes()!=canonical):
        raise ThreeArmDraftBlocked("Actual proposed schedule not equal to fixed report")
    print(
        "G3_THREE_ARM_CANDIDATE=PASS "
        "tasks=36 planned_slots=108 available_not_authorized=90 "
        "missing_blocked=18 actual_provider_tokens=none "
        "live_model_launch=false preregistered=false"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(_candidate_three_arm_cli())
