"""Strictly nonbilling G2 paired scheduler and immutable trial artifacts.

All generated text is a deterministic MOCK. There is no model/provider API,
no Python-code execution, no official evaluator and no benchmark score.
"""
from __future__ import annotations

from hashlib import sha256
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import re
import shutil
import tempfile
import time
from typing import Callable

import yaml
import jsonschema

from src.runner.agent_visibility import neutral_model_bundle
from src.runner.costs import enforce_offline_budget,make_offline_cost_record,TrialBudgetError
from src.runner.manifest import (
    ARMS, paired_schedule,persist_record,read_existing,
    verify_record_artifacts,RunManifestError,
)
from src.security.agent_boundary import validate_agent_payload

class OfflineRunError(ValueError):
    pass

CONFIG_FIELDS={
    "experiment_id","dataset_revision","provider","model_id",
    "model_temperature","provider_seed_supported","randomize_arm_order",
    "max_attempts_per_task","max_wall_seconds_per_task",
    "max_input_tokens_per_attempt","max_output_tokens_per_attempt",
    "max_concurrent_attempts","maximum_total_spend_usd","currency",
    "actual_provider_spend_authorized","required_g1_release_status",
}
REQUIRED_FIELDS=CONFIG_FIELDS
RUN_SCHEMA_PATH=Path(__file__).resolve().parents[2]/"schemas/run_record.schema.json"
OFFLINE_STATUS="MOCK_ONLY_NOT_SCORED"
NO_SCORE_FAILURES=(
    "NO_REAL_MODEL_PROVIDER_CALL",
    "UNVERIFIED_OS_ISOLATION",
    "NO_OFFICIAL_INDEPENDENT_SCORER",
)


def _sha(contents:bytes)->str:
    return sha256(contents).hexdigest()


def load_offline_configuration(path:Path)->dict:
    try:
        config=yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError,yaml.YAMLError) as exc:
        raise OfflineRunError("Cannot read frozen experiment config") from exc
    if not isinstance(config,dict) or set(config)!=REQUIRED_FIELDS:
        raise OfflineRunError("Unknown or missing experiment config fields")
    if config["provider"]!="offline" or config["model_id"]!="offline/mock-v0":
        raise OfflineRunError("Provider or model attempts a non-mock call")
    if type(config["actual_provider_spend_authorized"]) is not bool or config["actual_provider_spend_authorized"]:
        raise OfflineRunError("Paid provider execution must be disabled")
    if config["currency"]!="USD" or config["dataset_revision"]!="own-synthetic-IFC4X3":
        raise OfflineRunError("Unsupported data revision or currency")
    if config["required_g1_release_status"]!="PASS_FOR_OFFICIAL_EVALUATION":
        raise OfflineRunError("Cannot weaken official G1 evidence requirement")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,110}",config["experiment_id"]):
        raise OfflineRunError("Invalid experiment identifier")
    if type(config["model_temperature"]) not in (int,float) or config["model_temperature"]!=0:
        raise OfflineRunError("Mock temperature must be frozen at zero")
    if type(config["provider_seed_supported"]) is not bool or config["provider_seed_supported"]:
        raise OfflineRunError("Mock provider does not claim deterministic seed support")
    if type(config["randomize_arm_order"]) is not bool or not config["randomize_arm_order"]:
        raise OfflineRunError("Mock paired arm order must be preregistered randomized")
    if type(config["max_concurrent_attempts"]) is not int or config["max_concurrent_attempts"]!=1:
        raise OfflineRunError("Mock pilot is sequential until durable shared budget broker exists")
    enforce_offline_budget(
        maximum_total_spend_usd=config["maximum_total_spend_usd"],
        max_attempts=config["max_attempts_per_task"],
        max_wall_seconds=config["max_wall_seconds_per_task"],
        max_input_tokens=config["max_input_tokens_per_attempt"],
        max_output_tokens=config["max_output_tokens_per_attempt"],
        model_id=config["model_id"],
    )
    return dict(config)


def read_mock_task_list(path:Path)->list[dict]:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,ValueError) as exc:
        raise OfflineRunError("Cannot read offline task list") from exc
    if not isinstance(value,list) or not 1<=len(value)<=36:
        raise OfflineRunError("Offline task list must contain 1 to 36 task envelopes")
    records=[]
    ids=set()
    for task in value:
        item=validate_agent_payload(task)
        if not item["task_id"].startswith("OWN-"):
            raise OfflineRunError("Only own synthetic non-GT task identifiers allowed")
        if item["task_id"] in ids:
            raise OfflineRunError("Duplicate task identifier")
        ids.add(item["task_id"])
        records.append(item)
    return records


def _clean_output_root(output_root:Path)->Path:
    if not output_root.is_absolute():
        raise OfflineRunError("Output root must be explicit absolute scratch path")
    if output_root.is_symlink() or output_root.resolve()==Path("/"):
        raise OfflineRunError("Unsafe output root")
    if output_root.exists() and not output_root.is_dir():
        raise OfflineRunError("Output root must be a directory")
    return output_root


def _safe_write(path:Path,content:bytes)->str:
    if path.is_symlink():
        raise OfflineRunError("Artifact output must not be a symlink")
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    return _sha(content)


def _tokens_approximate(model_context:dict)->int:
    # This is merely a length-based budget preflight; no provider token report.
    text=json.dumps(model_context,ensure_ascii=False,sort_keys=True)
    return (len(text.encode("utf-8"))+3)//4


def _arm_details(arm:str)->tuple[str,str]:
    if arm=="direct_xml":
        return "building.xml","src/direct_markup/prompt_templates/system.md"
    if arm=="imperative_python":
        return "solution.py","src/imperative_control/prompt_templates/system.md"
    raise OfflineRunError("Unknown arm")


def _new_record(
    slot, task:dict,config:dict,view:dict,
    source_sha:str,clock:Callable[[],float],
    estimated_tokens:int, output_root:Path,
)->dict:
    started=clock()
    name,prompt_path=_arm_details(slot.arm)
    reference=(Path(__file__).resolve().parents[2]/prompt_path).read_bytes()
    base_context=json.dumps(view,sort_keys=True,ensure_ascii=False).encode("utf-8")
    input_budget=config["max_input_tokens_per_attempt"]
    max_seconds=config["max_wall_seconds_per_task"]
    if estimated_tokens>input_budget:
        status="BLOCKED_TOKEN_BUDGET"
        failures=("ESTIMATED_INPUT_TOKENS_EXCEED_CAP",)
    else:
        status=OFFLINE_STATUS
        failures=NO_SCORE_FAILURES
    simulated_response={
        "provider":"offline",
        "model_id":"offline/mock-v0",
        "is_real_llm_response":False,
        "text":"MOCK_NOT_AN_LLM_GENERATION",
        "generated_candidate":False,
        "task_id":slot.task_id,
    }
    raw=json.dumps(simulated_response,sort_keys=True,ensure_ascii=False,indent=2).encode()+b"\n"
    initial_source=view["model_xml_text"].encode() if slot.arm=="direct_xml" else b""
    artifact_root=output_root/"trials"
    artifact_root.mkdir(parents=True,exist_ok=True)
    final_dir=artifact_root/slot.run_id
    if final_dir.exists() or final_dir.is_symlink():
        raise RunManifestError("Trial artifacts already exist; do not silently overwrite")
    staging=Path(tempfile.mkdtemp(prefix="trial-staging-",dir=artifact_root))
    try:
        source_sha256=_safe_write(staging/name,initial_source)
        response_sha256=_safe_write(staging/"raw_model_response.json",raw)
        context_sha256=_safe_write(staging/"model_context.json",base_context)
        stdout_sha256=_safe_write(staging/"stdout.txt",b"")
        stderr_sha256=_safe_write(staging/"stderr.txt",b"")
        diagnostic_sha256=_safe_write(staging/"compiler_diagnostics.json",
                                      b'{"status":"NOT_INVOKED_MOCK"}\n')
        elapsed_ms=max(0,int((clock()-started)*1000))
        if elapsed_ms>max_seconds*1000:
            status="BLOCKED_WALL_TIME"
            failures=("MOCK_TIME_BUDGET_EXCEEDED",)
        notes_sha256=_safe_write(staging/"case_notes.json",json.dumps({
            "status":status,"source_file_is_a_mock":True,
            "model_called":False,"ifc_generated":False,
            "evaluation_performed":False,
        },sort_keys=True).encode()+b"\n")
        staging.rename(final_dir)
    except Exception:
        shutil.rmtree(staging,ignore_errors=True)
        raise
    cost=make_offline_cost_record(
        config["model_id"],estimated_tokens,0
    ).as_dict()
    return {
        "schema_version":"g2-offline-run-record-v0.1",
        "run_id":slot.run_id,
        "experiment_id":config["experiment_id"],
        "dataset_rev":config["dataset_revision"],
        "task_id":slot.task_id,
        "arm":slot.arm,
        "seed":slot.seed,
        "attempt_id":slot.attempt,
        "model_id":config["model_id"],
        "provider":config["provider"],
        "backend_versions":{
            "python":platform.python_version(),
            "ifcopenshell":version("ifcopenshell"),
            "runner":"g2-offline-run-record-v0.1",
        },
        "input_sha":source_sha,
        "result_sha":None,
        "status":status,
        "failures":list(failures),
        "metrics_ref":None,
        "model_input_sha256":_sha(base_context),
        "system_prompt_sha256":_sha(reference),
        "source_artifact_sha256":source_sha256,
        "raw_response_sha256":response_sha256,
        "artifact_sha256s":{
            "source":source_sha256,
            "raw_response":response_sha256,
            "model_context":context_sha256,
            "stdout":stdout_sha256,
            "stderr":stderr_sha256,
            "compiler_diagnostics":diagnostic_sha256,
            "case_notes":notes_sha256,
        },
        "artifact_refs":{
            "model_context":f"trials/{slot.run_id}/model_context.json",
            "source":f"trials/{slot.run_id}/{name}",
            "raw_response":f"trials/{slot.run_id}/raw_model_response.json",
            "stdout":f"trials/{slot.run_id}/stdout.txt",
            "stderr":f"trials/{slot.run_id}/stderr.txt",
            "compiler_diagnostics":f"trials/{slot.run_id}/compiler_diagnostics.json",
            "case_notes":f"trials/{slot.run_id}/case_notes.json",
        },
        "paired_observation_format":"XML_VIEW_OF_SAME_SOURCE_IFC",
        "cost":cost,
        "estimated_token_method":"UTF8_CONTEXT_BYTES_DIV_4_NOT_PROVIDER_REPORTED",
        "max_attempts":config["max_attempts_per_task"],
        "max_wall_seconds":max_seconds,
        "budget_policy":{
            "max_input_tokens":config["max_input_tokens_per_attempt"],
            "max_output_tokens":config["max_output_tokens_per_attempt"],
            "max_concurrent_attempts":config["max_concurrent_attempts"],
            "maximum_total_spend_usd":str(config["maximum_total_spend_usd"]),
        },
        "provider_seed_supported":config["provider_seed_supported"],
        "elapsed_wall_ms":elapsed_ms,
        "llm_calls":0,
        "python_code_executed":False,
        "trusted_compiler_executed":False,
        "independent_grader_executed":False,
        "OS_isolation_verified":False,
        "paid_pilot_authorized":False,
    }


def run_mock_schedule(
    *,
    source_ifc:Path, tasks:list[dict], config:dict,
    output_root:Path, seeds:tuple[int,...],shuffle_seed:int=0,
    arm_filter:str="both",attempt:int=0,resume:bool=False,
    clock:Callable[[],float]=time.monotonic,
)->dict:
    """Offline-only record scheduler; rejects any paid/run authorization.

    Never calls a model, executes generated Python or grades IFC.
    """
    if config.get("provider")!="offline" or config.get("model_id")!="offline/mock-v0":
        raise OfflineRunError("Only offline mock provider is permitted")
    if config.get("actual_provider_spend_authorized") is not False:
        raise OfflineRunError("Paid/real model calls disabled")
    if arm_filter not in (*ARMS,"both"):
        raise OfflineRunError("Unexpected arm selection")
    if type(attempt) is not int or attempt<0:
        raise OfflineRunError("Attempt ID must be a nonnegative integer")
    if attempt>=config["max_attempts_per_task"]:
        raise OfflineRunError("Attempt exceeds explicit per-task retry budget")
    if not seeds or any(type(x) is not int or x<0 for x in seeds):
        raise OfflineRunError("All seeded repetitions must be nonnegative integer seeds")
    _clean_output_root(output_root)
    enforce_offline_budget(
        maximum_total_spend_usd=config["maximum_total_spend_usd"],
        max_attempts=config["max_attempts_per_task"],
        max_wall_seconds=config["max_wall_seconds_per_task"],
        max_input_tokens=config["max_input_tokens_per_attempt"],
        max_output_tokens=config["max_output_tokens_per_attempt"],
        model_id=config["model_id"],
    )
    for task in tasks:
        validate_agent_payload(task)
    from src.runner.sandbox import approved_execution_status
    safe=approved_execution_status()
    if safe.generated_python_execution_allowed or safe.paid_pilot_allowed:
        raise OfflineRunError("Unexpected security gate escalation")
    view=neutral_model_bundle(source_ifc,tasks[0])
    source_sha=view["source_ifc_sha256"]
    if _sha(source_ifc.read_bytes())!=source_sha:
        raise OfflineRunError("Input source bytes mismatch projection")
    slots=paired_schedule(tasks,seeds,config["experiment_id"],source_sha,
                          attempt=attempt,shuffle_seed=shuffle_seed)
    if arm_filter!="both":
        slots=tuple(x for x in slots if x.arm==arm_filter)
    if len(slots)>144:
        raise OfflineRunError("Too many offline mock slots")
    manifest_dir=output_root/"manifests"
    existing=[x for x in slots if read_existing(manifest_dir,x.run_id) is not None]
    if existing and not resume:
        raise RunManifestError("Existing manifest(s) found; resume or choose new attempt ID")
    task_by_id={row["task_id"]:row for row in tasks}
    existing_ids=set()
    for item in existing:
        saved=read_existing(manifest_dir,item.run_id)
        jsonschema.validate(saved,json.loads(RUN_SCHEMA_PATH.read_text()))
        verify_record_artifacts(output_root,saved)
        previous_view=neutral_model_bundle(source_ifc,task_by_id[item.task_id])
        previous_context_hash=_sha(json.dumps(
            previous_view,sort_keys=True,ensure_ascii=False
        ).encode("utf-8"))
        _,system_prompt=_arm_details(item.arm)
        current_prompt_sha=_sha(
            (Path(__file__).resolve().parents[2]/system_prompt).read_bytes()
        )
        expected_policy={
            "max_input_tokens":config["max_input_tokens_per_attempt"],
            "max_output_tokens":config["max_output_tokens_per_attempt"],
            "max_concurrent_attempts":config["max_concurrent_attempts"],
            "maximum_total_spend_usd":str(config["maximum_total_spend_usd"]),
        }
        if (saved.get("model_input_sha256")!=previous_context_hash
            or saved.get("system_prompt_sha256")!=current_prompt_sha
            or saved.get("experiment_id")!=config["experiment_id"]
            or saved.get("dataset_rev")!=config["dataset_revision"]
            or saved.get("budget_policy")!=expected_policy
            or saved.get("max_attempts")!=config["max_attempts_per_task"]
            or saved.get("max_wall_seconds")!=config["max_wall_seconds_per_task"]
            or saved.get("backend_versions",{}).get("ifcopenshell")!=version("ifcopenshell")):
            raise RunManifestError("Cannot resume with changed prompt, context, runtime or budget")
        if (saved.get("task_id"),saved.get("arm"),saved.get("seed"),
            saved.get("input_sha"),saved.get("model_id"),saved.get("attempt_id"))!=(
            item.task_id,item.arm,item.seed,source_sha,config["model_id"],item.attempt
        ):
            raise RunManifestError("Cannot resume a mismatched/corrupted prior manifest")
        existing_ids.add(item.run_id)
    created=[]
    for item in slots:
        if item.run_id in existing_ids:
            continue
        row=task_by_id[item.task_id]
        scoped_view=neutral_model_bundle(source_ifc,row)
        if scoped_view["source_ifc_sha256"]!=source_sha:
            raise OfflineRunError("Source content diverged across paired arms")
        tokens=_tokens_approximate(scoped_view)
        record=_new_record(item,row,config,scoped_view,
                           source_sha,clock,tokens,output_root)
        jsonschema.validate(record,json.loads(RUN_SCHEMA_PATH.read_text()))
        persist_record(manifest_dir,record)
        created.append(record)
    all_records=[read_existing(manifest_dir,item.run_id) for item in slots]
    if any(item is None for item in all_records):
        raise RunManifestError("Missing persisted trial")
    return {
        "status":"OFFLINE_MOCK_ONLY_NO_SCORES",
        "total_slots":len(slots),
        "created":len(created),
        "skipped_unchanged":len(existing_ids),
        "planned_order":[{"task_id":x.task_id,"arm":x.arm,
                          "seed":x.seed,"run_id":x.run_id} for x in slots],
        "manifest_ids":[x["run_id"] for x in all_records],
        "statuses":{status:sum(x["status"]==status for x in all_records)
                    for status in sorted({x["status"] for x in all_records})},
        "provider_model_calls":0,
        "official_benchmark_tasks_scored":0,
        "model_context_hash_matched_per_task_seed":all(
            len({record["model_input_sha256"]
                 for record in all_records
                 if record["task_id"]==task_id and record["seed"]==seed})==1
            for task_id in {x.task_id for x in slots}
            for seed in {x.seed for x in slots}
        ),
        "paid_pilot_authorized":False,
    }
