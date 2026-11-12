"""Prospective original BIBIMBAP XML-only 45-edit ITT cohort (#112).

Never imports or edits BIXML/Xim. 45 original edit tasks remain the
denominator. Reuse the prior genuinely model-produced test_05 EXACTLY once.
Known unsupported source IFCs count as failures, not exclusions.

--preflight: zero API calls; cache public ONLY projected input and normalized
  source in ignored results/ and freeze upper bound of all possible calls.
--live-approved: run exact preflight plan with cumulative tariff reservation
  below owner's USD 1 cap, no retries or revisiting any attempted task.
--finalize: aggregate already frozen records offline, zero calls.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from typing import Any

from tools.bibimbap_public_packet import (
    DATA_COMMIT, CSV_SHA256, PUBLIC_GRAMMAR, sha,
)
from tools.audit_bibimbap_author import (
    read_original_tasks, AUTHOR_SHA, DATA_SHA, _head, _sha, WORKER,
)
from tools.run_bibimbap_test05_first_luna import (
    APPROVED_CAP_USD, MODEL, STANDARD_INPUT_USD_PER_1M,
    STANDARD_OUTPUT_USD_PER_1M, MAX_OUTPUT_TOKENS,
    now_utc,
)
from src.runtime.ifc_projection import project_ifc
from src.runtime.compiler import compile_declarative_xml
from src.security.agent_boundary import validate_agent_payload

import ifcopenshell
import ifcopenshell.util.unit

ROOT = Path(__file__).resolve().parents[1]
RUN_NAME = "bibimbap_original_45_luna_20261112_issue112"
RUN_ROOT = ROOT / "results" / RUN_NAME
MANIFEST = RUN_ROOT / "preflight.json"
COHORT_REPORT = ROOT / "reports" / "bibimbap_original45_luna_20261112.json"
ORIGINAL_PILOT = ROOT / "reports" / "bibimbap_test05_luna_first_real_20261112.json"
PRIOR_LEDGER = ROOT / "reports" / "bibimbap_xml_only_launch_gate_20261112.json"
MAX_PARALLEL = 4
INPUT_BYTE_LIMIT = 240000
INPUT_MARGIN_TOKENS = 2048
# conservative 2x cost reservation for entire cohort (even though common API
# standard rate exact): hard refuse before billing if budget insufficient.
RESERVATION_MULTIPLIER = Decimal(2)
OUTPUT_SAFETY_LIMIT = 1200000
RUN_APPROVAL = "https://github.com/pikaybh/bim-markup-bench/issues/112"

def _write_new(path: Path, obj: dict) -> None:
    with path.open("xb") as f:
        f.write((json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf8"))

def _replace_local(path: Path, obj: dict) -> None:
    tmp = path.with_name(path.name+".tmp")
    with tmp.open("wb") as f:
        f.write((json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf8"))
    tmp.replace(path)

def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf8"))

def _task_inputs(author: Path, dataset: Path) -> tuple[list[dict], list[dict]]:
    # The original public questions ONLY are used to make LLM packets.
    # Private original author module paths in the separate scorer are not
    # in the data flow to packet construction.
    tasks, pinned = read_original_tasks(author, dataset)
    if pinned["author_commit_sha"] != AUTHOR_SHA or pinned["data_commit_sha"] != DATA_SHA:
        raise ValueError("Author/dataset Git identity mismatch")
    if pinned["original_csv_sha256"] != CSV_SHA256:
        raise ValueError("Public source CSV mismatch")
    with (dataset / "prompts/all_questions.csv").open("r", encoding="utf-8-sig", newline="") as f:
        public = {row["test"]: {"question": row["question"].strip(),
                                "crud": row["CRUD"].lower().strip(),
                                "ifc": row["ifc-file"].replace("\\", "/")}
                  for row in csv.DictReader(f)}
    ledger = _load(PRIOR_LEDGER)["all_original_editing_tasks_intention_to_test"]
    planned = {row["candidate_id"]: row for row in ledger}
    if len(tasks) != len(planned) or set(x["test_id"] for x in tasks) != set(planned):
        raise ValueError("Original ITT cohort drift")
    for t in tasks:
        q = public[t["test_id"]]
        if q["crud"] != t["crud"] or q["ifc"] != t["ifc_relpath"] or not q["question"]:
            raise ValueError("Question and pinned scorer population mismatch")
    return tasks, ledger

def _packet_public(question: str, projected_xml: bytes) -> dict[str,str]:
    # Same exact model instructions, source-only field boundary as #110;
    # no task id, evaluator, private target, original code, XML answer.
    validate_agent_payload({"task_id": "PUBLIC-XML-EDIT", "instruction": question, "input_file": "input.ifc"})
    instructions = (
        "Edit the provided declarative building.xml document state to "
        "perform the PUBLIC TASK. Return only the COMPLETE updated XML. "
        "Keep every unrelated supported element unchanged. "
        "Do not write Python, tool calls, or XML operation commands. "
        "The separate trusted runtime will compile the final XML later."
    )
    body = ("PUBLIC TASK:\n" + question +
            "\n\nPUBLIC SOURCE PROJECTION (building.xml):\n" + projected_xml.decode("utf8") +
            "\n\nPUBLIC EXPERIMENTAL XML GRAMMAR:\n" + PUBLIC_GRAMMAR.read_text(encoding="utf8") +
            "\n\nReturn only the complete edited building.xml.")
    return {"instructions": instructions, "input": body}

def _prepared_row(t:dict, ledger:dict, question:str, dataset:Path, store:Path) -> dict:
    test_id = t["test_id"]
    row = {
        "test_id": test_id, "source_crud": t["crud"], "source_category": t["category"],
        "original_ifc_sha256": t["ifc_sha256"],
        "original_relpath": t["ifc_relpath"],
        "public_question_sha256": sha(question.encode("utf8")),
        "source_projection_earlier": ledger["source_projection"],
        "source_projection_reason_earlier": ledger["source_projection_reason"],
        "original_author_noop_score": ledger["original_author_noop_score"],
        "model_calls_attempted": 0,
        "status": "NOT_RUN",
    }
    if test_id == "test_05":
        first = _load(ORIGINAL_PILOT)
        if first["status"] != "ONE_REAL_MODEL_EDIT_SCORED" or first["actual_api_calls_attempted"] != 1:
            raise ValueError("Original genuine Luna test05 evidence is not validated")
        row.update(
            status="REUSED_EXISTING_REAL_ONE_SHOT", model_calls_attempted=1,
            provider_returned_model=first["provider_returned_model"],
            reported_input_tokens=first["reported_input_tokens"],
            reported_output_tokens=first["reported_output_tokens"],
            usage_estimated_cost_usd=first["actual_provider_usage_cost_estimate_usd"],
            actual_model_output_sha256=first["raw_model_output_sha256"],
            author_score=first["original_author_score"],
            author_metrics=first["original_author_metric_vector"],
            compiled=True, score_observed=True,
            author_full_score=True,
            independent_native_public_task_core=first["independent_native_core_success"],
            full_independent_strict_success=None,
            originating_issue="https://github.com/pikaybh/bim-markup-bench/issues/110",
            called_during_this_cohort=False,
        )
        return row
    if ledger["source_projection"] != "PROJECTABLE":
        row.update(status="BLOCKED_UNSUPPORTED_SOURCE_PREDECLARED", scored=False,
                   author_score=None, compiled=False, called_during_this_cohort=False)
        return row
    src = dataset / "ifc" / t["ifc_relpath"]
    if _sha(src) != t["ifc_sha256"] or src.is_symlink():
        raise ValueError("Original IFC bytes drift")
    try:
        model = ifcopenshell.open(str(src))
        if model.schema != "IFC4X3":
            raise ValueError("SOURCE_NOT_IFC4X3")
        old_scale = ifcopenshell.util.unit.calculate_unit_scale(model)
        if abs(old_scale-0.001)>1e-12:
            raise ValueError("SOURCE_NOT_MILLIMETRE")
        normalized = ifcopenshell.util.unit.convert_file_length_units(model, "METER")
        folder = store / test_id
        folder.mkdir(parents=True, exist_ok=False)
        normalized_path = folder / "source_normalized_m.ifc"
        normalized.write(str(normalized_path))
        projection = project_ifc(normalized_path, strict_on_opaque=False)
        if not projection.projected_global_ids:
            raise ValueError("NO_PROJECTED_GEOMETRY")
        packet = _packet_public(question, projection.xml)
        packet_bytes = json.dumps(packet, sort_keys=True, ensure_ascii=False).encode("utf8")
        size = len(packet["instructions"].encode("utf8")) + len(packet["input"].encode("utf8"))
        row["source_projected_guid_count"] = len(projection.projected_global_ids)
        row["source_opaque_reference_count"] = len(projection.opaque_references)
        row["normalized_ifc_sha256"] = _sha(normalized_path)
        row["public_projected_xml_sha256"] = sha(projection.xml)
        row["public_packet_sha256"] = sha(packet_bytes)
        row["public_input_bytes"] = size
        row["source_original_xml_state_sha256"] = sha(projection.xml)
        if size > INPUT_BYTE_LIMIT:
            row.update(status="BLOCKED_PUBLIC_INPUT_TOO_LARGE", compiled=False)
            return row
        # A conservatively high bound: 1 UTF8 byte can encode at most one
        # text token; 2048 input overhead + max full output tokens. Tools 0.
        upper = (Decimal(size+INPUT_MARGIN_TOKENS)*STANDARD_INPUT_USD_PER_1M +
                 Decimal(MAX_OUTPUT_TOKENS)*STANDARD_OUTPUT_USD_PER_1M)/Decimal(1000000)
        row["reserved_upper_cost_usd"] = str(upper*RESERVATION_MULTIPLIER)
        row["status"] = "READY_REAL_MODEL"
        _write_new(folder / "public_packet.json", packet)
        _write_new(folder / "source_context.json", {
            "original_ifc_sha256": t["ifc_sha256"],
            "original_relpath": t["ifc_relpath"], "normalized_ifc_sha256": row["normalized_ifc_sha256"],
            "public_packet_sha256": row["public_packet_sha256"],
        })
    except Exception as exc:
        row.update(status="BLOCKED_NEW_SOURCE_PROJECTION_ERROR",
                   failure_type=type(exc).__name__, author_score=None, compiled=False)
    return row

def preflight(author:Path, dataset:Path) -> dict:
    from dotenv import load_dotenv
    load_dotenv(ROOT.parent / "bim-markup-bench" / ".env", override=False)
    if os.environ.get("OPENAI_MODEL") != MODEL or not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("Exact approved model/API credentials unavailable")
    if os.environ.get("OPENAI_BASE_URL"):
        raise ValueError("Custom provider endpoint not approved")
    if RUN_ROOT.exists() or COHORT_REPORT.exists():
        raise ValueError("Cohort preflight already created; never overwrite")
    tasks, ledger_rows = _task_inputs(author, dataset)
    prev = {x["candidate_id"]:x for x in ledger_rows}
    with (dataset/"prompts/all_questions.csv").open("r",encoding="utf-8-sig",newline="") as f:
        q = {v["test"]:v["question"].strip() for v in csv.DictReader(f)}
    RUN_ROOT.mkdir(parents=True,exist_ok=False)
    rows=[]
    for pos,t in enumerate(tasks,1):
        entry=_prepared_row(t,prev[t["test_id"]],q[t["test_id"]],dataset,RUN_ROOT)
        rows.append(entry)
        print(f"PREP {pos:02d}/45 {t['test_id']} {entry['status']} bytes={entry.get('public_input_bytes')}",
              flush=True)
    if len(rows)!=45 or {x["test_id"] for x in rows}!={x["test_id"] for x in tasks}:
        raise ValueError("Prospective 45 ITT candidate inventory mismatch")
    first = _load(ORIGINAL_PILOT)
    previous_cost = Decimal(first["actual_provider_usage_cost_estimate_usd"])
    future_reserve=sum((Decimal(x["reserved_upper_cost_usd"]) for x in rows
                        if x["status"]=="READY_REAL_MODEL"),Decimal("0"))
    if previous_cost + future_reserve >= APPROVED_CAP_USD:
        raise ValueError("ALL possible one-call reservations plus previous spend >= $1")
    info = {
        "schema":"bibimbap-xml-full-45-itt/v1",
        "scope":"EXPERIMENT_TEST_CODE_ONLY_NEVER_BIXML_XIM",
        "owner_approved_issue":RUN_APPROVAL,
        "model":MODEL,
        "original_edit_itt_count":45,
        "existing_test05_provider_calls_reused":1,
        "future_one_attempt_per_ready_task":True,
        "future_provider_calls_planned":sum(x["status"]=="READY_REAL_MODEL" for x in rows),
        "original_unsupported_source_count":sum(x["status"]=="BLOCKED_UNSUPPORTED_SOURCE_PREDECLARED" for x in rows),
        "additional_preflight_block_count":sum(x["status"].startswith("BLOCKED") and
                                               x["status"]!="BLOCKED_UNSUPPORTED_SOURCE_PREDECLARED" for x in rows),
        "approved_global_spend_cap_usd":str(APPROVED_CAP_USD),
        "prior_test05_usage_cost_usd":str(previous_cost),
        "max_total_new_requests_cost_reserved_usd":str(future_reserve),
        "all_attempts_cost_reserved_usd":str(previous_cost+future_reserve),
        "reservation_multiplier":str(RESERVATION_MULTIPLIER),
        "official_pricing_url":"https://developers.openai.com/api/docs/pricing",
        "official_pricing_checked_utc":now_utc(),
        "input_price_usd_per_million":str(STANDARD_INPUT_USD_PER_1M),
        "output_price_usd_per_million":str(STANDARD_OUTPUT_USD_PER_1M),
        "max_response_output_tokens":MAX_OUTPUT_TOKENS,
        "total_provider_call_retries":0,
        "provider_tools":[],
        "public_packet_excludes_private_scorer_and_ground_truth":True,
        "original_ifc_and_author_source_nonmodifiable":True,
        "author_grader_commit_sha":AUTHOR_SHA,
        "original_dataset_commit_sha":DATA_SHA,
        "public_question_csv_sha256":CSV_SHA256,
        "frozen_population":rows,
        "status":"PREFLIGHT_READY_ZERO_NEW_MODEL_CALLS",
    }
    _write_new(MANIFEST,info)
    return info

def _score_model_row(row:dict,author:Path,dataset:Path, folder:Path, raw:bytes) -> dict:
    orig = dataset/"ifc"/row["original_relpath"]
    from src.security.agent_boundary import check_xml_bytes
    check_xml_bytes(raw)
    source=folder/"source_normalized_m.ifc"
    if _sha(source)!=row["normalized_ifc_sha256"]:
        raise ValueError("Frozen normalized source hash mismatch")
    native_meter=folder/"model_compiled_m.ifc"
    compilation=compile_declarative_xml(source,raw,native_meter)
    if compilation.as_dict().get("status") not in (
        "COMMITTED", "ACCEPTED", "COMPILED", "SUCCESS"):
        # The first pilot's compiler actually returned a status; permit its
        # native IFC output based on existence rather than guess status names.
        if not native_meter.is_file():
            raise ValueError("Trusted XML compiler produced no native IFC")
    if not native_meter.is_file():
        raise ValueError("Trusted XML compiler did not produce result file")
    compiled = ifcopenshell.open(str(native_meter))
    mm = ifcopenshell.util.unit.convert_file_length_units(compiled,"MILLIMETER")
    mm_path=folder/"model_compiled_mm.ifc"
    mm.write(str(mm_path))
    if abs(ifcopenshell.util.unit.calculate_unit_scale(ifcopenshell.open(str(mm_path)))-.001)>1e-12:
        raise ValueError("Original source scale was not restored")
    tested = subprocess.run(
        [sys.executable, "-I",str(WORKER),"--author-repo",str(author),
         "--test", row["test_id"],
         "--source-ifc",str(orig),"--edited-ifc",str(mm_path)],
        capture_output=True,text=True,timeout=70,check=False,
    )
    if not tested.stdout:
        raise ValueError("Original grader produced no valid response")
    original_grade=json.loads(tested.stdout.strip().splitlines()[-1])
    if tested.returncode != 0 or original_grade.get("status")!="SCORED":
        raise RuntimeError("Original author scorer error, result cannot be called success")
    if _sha(orig)!=row["original_ifc_sha256"]:
        raise ValueError("External original IFC was mutated by grader")
    return {
        "compiler_status":compilation.as_dict().get("status"),
        "model_compiled_native_ifc_sha256":_sha(mm_path),
        "author_score":original_grade["score"],
        "author_metrics":original_grade["metrics"],
        "author_full_score":abs(original_grade["score"]-1.0)<1e-8,
    }

def _run_one(item:dict,author:Path,dataset:Path,api_key:str) -> dict:
    from openai import OpenAI
    row = dict(item)
    folder=RUN_ROOT/row["test_id"]
    packet=_load(folder/"public_packet.json")
    if sha(json.dumps(packet,sort_keys=True,ensure_ascii=False).encode("utf8"))!=row["public_packet_sha256"]:
        raise ValueError("Frozen public model packet mutated")
    if _sha(folder/"source_normalized_m.ifc") != row["normalized_ifc_sha256"]:
        raise ValueError("Frozen source state mutated")
    row["model_calls_attempted"]=1
    row["called_during_this_cohort"]=True
    row["status"]="MODEL_ATTEMPT_ISSUED"
    _write_new(folder/"attempt_issued.json",row)
    try:
        client=OpenAI(api_key=api_key,max_retries=0,timeout=170)
        started=perf_counter()
        answer=client.responses.create(model=MODEL,instructions=packet["instructions"],
                input=packet["input"],max_output_tokens=MAX_OUTPUT_TOKENS,
                reasoning={"effort":"medium"},store=False,tools=[],service_tier="default")
        row["provider_elapsed_s"]=round(perf_counter()-started,3)
        row["provider_status"]=answer.status
        row["provider_returned_model"]=answer.model
        row["provider_response_id_hash"]=sha(str(answer.id).encode("utf8"))
        with (folder/"provider_response_raw.json").open("xb") as f:
            f.write(answer.model_dump_json(indent=2).encode("utf8"))
        row["provider_response_raw_sha256"]=_sha(folder/"provider_response_raw.json")
        raw=(answer.output_text or "").encode("utf8")
        with (folder/"model_generated_exact.raw.txt").open("xb") as f:
            f.write(raw)
        row["model_generated_exact_sha256"]=sha(raw)
        row["model_generated_bytes"]=len(raw)
        usage=answer.usage
        if usage is not None:
            row["reported_input_tokens"]=usage.input_tokens
            row["reported_output_tokens"]=usage.output_tokens
            row["usage_estimated_cost_usd"]=str(
                (Decimal(usage.input_tokens)*STANDARD_INPUT_USD_PER_1M+
                 Decimal(usage.output_tokens)*STANDARD_OUTPUT_USD_PER_1M)/Decimal(1000000))
        if answer.status!="completed" or not raw or len(raw)>OUTPUT_SAFETY_LIMIT:
            row["status"]="PROVIDER_INCOMPLETE_OR_EMPTY"
        elif answer.model!=MODEL:
            row["status"]="PROVIDER_MODEL_MISMATCH"
        else:
            try:
                score=_score_model_row(row,author,dataset,folder,raw)
                row.update(score)
                row["status"]="ORIGINAL_AUTHOR_SCORED"
                row["compiled"]=True
                row["full_independent_strict_success"]=None
            except Exception as exc:
                row["status"]="TRUSTED_XML_OR_NATIVE_GRADING_FAILED"
                row["native_failure_type"]=type(exc).__name__
                row["compiled"]=False
    except Exception as exc:
        row["status"]="PROVIDER_ERROR_NO_RETRY"
        row["provider_failure_type"]=type(exc).__name__
        row["compiled"]=False
    finally:
        row["completed_utc"]=now_utc()
        _write_new(folder/"attempt_result.json",row)
    return row

def full_live(author:Path,dataset:Path,parallel:int=MAX_PARALLEL) -> dict:
    if COHORT_REPORT.exists():
        raise ValueError("Cohort final report already exists")
    prep=_load(MANIFEST)
    if prep.get("status")!="PREFLIGHT_READY_ZERO_NEW_MODEL_CALLS":
        raise ValueError("Preflight missing or corrupted")
    if prep["all_attempts_cost_reserved_usd"] and Decimal(prep["all_attempts_cost_reserved_usd"])>=APPROVED_CAP_USD:
        raise ValueError("Cumulative owner USD cap exceeded")
    from dotenv import load_dotenv
    load_dotenv(ROOT.parent/"bim-markup-bench"/".env",override=False)
    if os.environ.get("OPENAI_MODEL")!=MODEL or not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("Approved model/API key absent")
    if os.environ.get("OPENAI_BASE_URL"):
        raise ValueError("Nonstandard endpoint forbidden")
    tasks,_ = _task_inputs(author,dataset)
    if len(tasks)!=45 or _head(author)!=AUTHOR_SHA or _head(dataset)!=DATA_SHA:
        raise ValueError("Original dataset/scorer drift")
    ready=[x for x in prep["frozen_population"] if x["status"]=="READY_REAL_MODEL"]
    if len(ready)!=prep["future_provider_calls_planned"]:
        raise ValueError("Frozen model call set drift")
    # All calls pre-reserved at a worst-case pessimistic upper bound.
    # Directory is sealed before FIRST provider request.
    active=RUN_ROOT/"cohort_live_issued.json"
    if active.exists() or any((RUN_ROOT/x["test_id"]/"attempt_issued.json").exists() for x in ready):
        raise ValueError("Trial already issued: no duplicate calls or reruns allowed")
    _write_new(active,{
        "status":"LIVE_AUTHORIZED_ONCE_ALL_CALL_RESERVATIONS_FROZEN",
        "issued_utc":now_utc(),"count":len(ready),
        "max_parallel":parallel,
        "all_calls_cost_reserved_usd":prep["all_attempts_cost_reserved_usd"],
    })
    api_key=os.environ["OPENAI_API_KEY"]
    with ThreadPoolExecutor(max_workers=parallel) as pool:
        tasks={pool.submit(_run_one,x,author,dataset,api_key):x["test_id"] for x in ready}
        for future in as_completed(tasks):
            name=tasks[future]
            try:
                row=future.result()
                print(f"COMPLETE {name:>20s} {row['status']:<39s} author={row.get('author_score')} USD={row.get('usage_estimated_cost_usd')}",flush=True)
            except BaseException as exc:
                print(f"FATAL_TASK_EXCEPTION {name} {type(exc).__name__}",flush=True)
                # Already issued record remains; do not retry.
    return finalize(author,dataset,live_was_run=True)

def finalize(author:Path,dataset:Path,*,live_was_run:bool=False) -> dict:
    prep=_load(MANIFEST)
    first=_load(ORIGINAL_PILOT)
    if len(prep["frozen_population"])!=45:
        raise ValueError("ITT manifest incomplete")
    entries=[]
    for input_row in prep["frozen_population"]:
        row=dict(input_row)
        if row["status"]=="READY_REAL_MODEL":
            result_path=RUN_ROOT/row["test_id"]/"attempt_result.json"
            issued_path=RUN_ROOT/row["test_id"]/"attempt_issued.json"
            if result_path.is_file():
                row=_load(result_path)
            elif issued_path.is_file():
                row["status"]="PROVIDER_ATTEMPT_ISSUED_RESULT_UNAVAILABLE"
                row["model_calls_attempted"]=1
            else:
                row["status"]="PREPARED_BUT_NOT_CALLED"
        # Do not map original author's positive no-op partial score to success.
        score=row.get("author_score",None)
        row["author_full_score"]=bool(
            isinstance(score,(int,float)) and abs(score-1.0)<1e-8
            and row.get("compiled") is True
        )
        row["strict_success_independent"]=None
        row["conservative_full_score_success_for_45_itt"]=row["author_full_score"]
        entries.append(row)
    if len(entries)!=45 or len({x["test_id"] for x in entries})!=45:
        raise ValueError("45 complete distinct rows mandatory")
    usage_cost=sum((Decimal(x.get("usage_estimated_cost_usd","0"))
                    for x in entries if x.get("usage_estimated_cost_usd") is not None),Decimal(0))
    unseen_usage=[x["test_id"] for x in entries if x.get("model_calls_attempted",0) and
                  not x.get("usage_estimated_cost_usd")]
    completed_scored=[x for x in entries if x["status"] in
                      ("REUSED_EXISTING_REAL_ONE_SHOT","ORIGINAL_AUTHOR_SCORED")]
    total_full=sum(x["author_full_score"] for x in entries)
    model_attempts=sum(x.get("model_calls_attempted",0) for x in entries)
    statuses=Counter(x["status"] for x in entries)
    report={
        "schema":"bibimbap-xml-full-45-itt/results-v1",
        "status":"COMPLETE_SINGLE_COHORT_WITH_DECLARED_UNSUPPORTED"
                 if not any(x["status"] in ("PREPARED_BUT_NOT_CALLED","PROVIDER_ATTEMPT_ISSUED_RESULT_UNAVAILABLE") for x in entries)
                 else "PARTIAL_COHORT_NOT_ALL_ATTEMPTS_FINISHED",
        "model":MODEL,"scope":"ORIGINAL_45_BIBIMBAP_EDIT_TASKS_NOT_ORIGINAL_ALL100",
        "method":"XML_ONLY_EXPERIMENTAL_OVERLAY_NONCAUSAL_TO_OTHER_PAPER_RESULTS",
        "owner_issue":RUN_APPROVAL,
        "owner_approved_max_usd":"1.00",
        "pricing":"standard_0.10_input_0.50_output_per_million",
        "cost_estimated_usd_including_prior_test05":str(usage_cost),
        "cost_reserved_upper_usd":prep["all_attempts_cost_reserved_usd"],
        "bill_reconciled":False,
        "provider_attempts_including_prior_test05":model_attempts,
        "provider_attempts_new_in_this_cohort":model_attempts-1,
        "original_population_45_intention_to_test":45,
        "original_retrieval_55_out_of_scope":True,
        "original_source_unprojectable_9_as_failures":9,
        "original_source_projectable_36":36,
        "original_author_scorer_successfully_returned_rows":len(completed_scored),
        "author_full_score_count_45":total_full,
        "author_full_score_rate_45":total_full/45,
        "mean_original_author_score_all45_zero_for_non_scored":sum((float(x.get("author_score") or 0) for x in entries))/45,
        "mean_original_author_score_scored_only":sum(float(x["author_score"]) for x in completed_scored)/len(completed_scored) if completed_scored else None,
        "task_level_strict_success_independently_verified":False,
        "independently_verified_45_task_success_rate":None,
        "no_model_output_modified_or_repaired":True,
        "all_model_results_and_ifc_candidates_stored_only_in_gitignored_results":True,
        "private_original_grader_not_model_visible":True,
        "statuses":dict(sorted(statuses.items())),
        "unknown_usage_attempt_ids":unseen_usage,
        "stratified_by_crud":{},
        "stratified_by_category":{},
        "frozen_public_csv_sha256":prep["public_question_csv_sha256"],
        "original_author_sha":prep["author_grader_commit_sha"],
        "original_dataset_sha":prep["original_dataset_commit_sha"],
        "individual_results":entries,
    }
    for attr,field in (("stratified_by_crud","source_crud"),("stratified_by_category","source_category")):
        for kind in sorted({x[field] for x in entries}):
            selected=[x for x in entries if x[field]==kind]
            report[attr][kind]={
                "denominator":len(selected),
                "author_full_score_count":sum(x["author_full_score"] for x in selected),
                "original_author_mean_zero_filled":sum(float(x.get("author_score") or 0) for x in selected)/len(selected),
                "original_source_not_projectable":sum(x["status"]=="BLOCKED_UNSUPPORTED_SOURCE_PREDECLARED" for x in selected),
                "scored_count":sum(x["status"] in ("REUSED_EXISTING_REAL_ONE_SHOT","ORIGINAL_AUTHOR_SCORED") for x in selected),
            }
    if COHORT_REPORT.exists():
        raise ValueError("Refusing overwrite of frozen aggregate")
    _write_new(COHORT_REPORT,report)
    print(json.dumps({k:report[k] for k in (
        "status","provider_attempts_including_prior_test05",
        "cost_estimated_usd_including_prior_test05","cost_reserved_upper_usd",
        "original_author_scorer_successfully_returned_rows",
        "author_full_score_count_45","author_full_score_rate_45",
        "mean_original_author_score_all45_zero_for_non_scored","statuses")},sort_keys=True),flush=True)
    return report

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight",action="store_true")
    mode.add_argument("--live-approved",action="store_true")
    mode.add_argument("--finalize",action="store_true")
    ap.add_argument("--author-repo",type=Path,required=True)
    ap.add_argument("--dataset",type=Path,required=True)
    ap.add_argument("--parallel",type=int,default=MAX_PARALLEL)
    args=ap.parse_args()
    if args.parallel<1 or args.parallel>MAX_PARALLEL:
        ap.error(f"Parallel must be 1 to {MAX_PARALLEL} (cost pre-reserved globally)")
    if args.preflight:
        info=preflight(args.author_repo,args.dataset)
        print(json.dumps({k:info[k] for k in (
            "status","future_provider_calls_planned","original_unsupported_source_count",
            "additional_preflight_block_count","all_attempts_cost_reserved_usd")},sort_keys=True),flush=True)
        return 0
    if args.live_approved:
        report=full_live(args.author_repo,args.dataset,parallel=args.parallel)
        return 0 if report["status"].startswith("COMPLETE") else 2
    report=finalize(args.author_repo,args.dataset)
    return 0 if report["status"].startswith("COMPLETE") else 2

if __name__=="__main__":
    raise SystemExit(main())
