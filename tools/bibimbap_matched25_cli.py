"""Offline preflight and opt-in (paid) paired BIBIMBAP 25-tool research runner.

Usage (zero cost):
 python -m tools.bibimbap_matched25_cli --preflight --author-repo ... --dataset ...
 python -m tools.bibimbap_matched25_cli --smoke --author-repo ... --dataset ...

Paid execution is NEVER started without a new, explicit owner approval file
with the issue, model, max_calls, max_output, price cap and timestamp.
No new paid experiment was authorized by Issue #114 implementation request.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime,timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from tools.audit_bibimbap_author import (
    AUTHOR_SHA,DATA_SHA,WORKER,read_original_tasks,_head,_sha,
)
from tools.bibimbap_matched25_agent import (
    MODEL, MAX_TOOL_CALLS,MAX_OUTPUT_TOKENS, PairProtocol,
    DurableBudget,ProviderBudgetError,run_agent,OfflineFakeClient,_FunctionCall,
)
from tools.bibimbap_matched25_tools import (
    ROOT, XmlSourceEditSession,PythonIfcCodeSession,
    DockerIFCExecutor,UnsupportedArm,file_hash,PINNED_DOCKER_IMAGE,
)

PROTOCOL_SHA_CONSTANTS={
    "name":"bibimbap-paired-25-tool-xml-vs-python-v1",
    "model":MODEL,"max_tool_calls_per_arm_per_task":MAX_TOOL_CALLS,
    "max_provider_output_tokens":MAX_OUTPUT_TOKENS,
    "reasoning_effort":"medium","service_tier":"default",
    "max_retries":0,"provider_storage":False,
    "samples_per_task":1,"original_editing_task_count":45,
}
PRIOR=ROOT/"reports"/"bibimbap_xml_only_launch_gate_20261112.json"
TEMPLATE=ROOT/"configs"/"bibimbap_matched25_approval.example.json"

def _save_unique(path:Path, obj:object)->None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"Refusing overwrite: {path.name}")
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("xb") as f:
        f.write((json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2,default=repr)+"\n").encode("utf8"))

def public_45(author:Path,dataset:Path)->list[dict]:
    tasks, pinned=read_original_tasks(author,dataset)
    if len(tasks)!=45 or pinned["author_commit_sha"]!=AUTHOR_SHA or pinned["data_commit_sha"]!=DATA_SHA:
        raise ValueError("Original 45 public edit population or Git provenance drift")
    with (dataset/"prompts/all_questions.csv").open("r",encoding="utf-8-sig",newline="") as f:
        questions={row["test"]:row for row in csv.DictReader(f)}
    frozen=json.loads(PRIOR.read_text(encoding="utf8"))["all_original_editing_tasks_intention_to_test"]
    previous={row["candidate_id"]:row for row in frozen}
    if len(previous)!=45 or {x["test_id"] for x in tasks}!=set(previous):
        raise ValueError("Original cohort gate drift")
    result=[]
    for t in tasks:
        q=questions[t["test_id"]]
        if (q["ifc-file"].replace("\\","/")!=t["ifc_relpath"]
            or q["CRUD"].lower().strip()!=t["crud"]):
            raise ValueError("Original public question/source relation drift")
        src=dataset/"ifc"/t["ifc_relpath"]
        if src.is_symlink() or _sha(src)!=t["ifc_sha256"]:
            raise ValueError("Original source IFC hash changed")
        result.append({
            "test_id":t["test_id"],"crud":t["crud"],"category":t["category"],
            "original_source_ifc_relpath":t["ifc_relpath"],
            "original_ifc_sha256":t["ifc_sha256"],
            "public_question_sha256":sha256(q["question"].strip().encode("utf8")).hexdigest(),
            "public_question":q["question"].strip(), # private local only, never Git public preflight
            "xml_source_projection_previously_observed":previous[t["test_id"]]["source_projection"],
            "xml_source_preflight_issue":previous[t["test_id"]]["source_projection_reason"],
            "original_noop_score_prior":previous[t["test_id"]]["original_author_noop_score"],
        })
    return result

def public_safe_entry(entry:dict)->dict:
    # No original task question full text or grader code in committed report.
    return {k:v for k,v in entry.items() if k!="public_question"}

def offline_preflight(author:Path,dataset:Path)->dict:
    plan=public_45(author,dataset)
    return {
        "status":"PROTOCOL_PREPARED_NO_MODEL_REQUESTS",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/114",
        "model_calls":0,"usd_paid":"0",
        "model":MODEL,
        "protocol":PROTOCOL_SHA_CONSTANTS,
        "original_author_sha":AUTHOR_SHA,
        "original_data_sha":DATA_SHA,
        "official_reference_url":"https://ec-3.org/wp-content/uploads/2026/08/EC32026_271.pdf",
        "official_author_source":"https://github.com/nbharathik/bibimbap",
        "paper_author_tool":"execute_ifc_code",
        "paper_tool_input":"Python snippet; preloaded ifc and API variables",
        "paper_tool_max_calls_per_task":25,
        "xml_source_tool_names":["read_building_xml","submit_building_xml"],
        "xml_llm_python_mutator_access":False,
        "imperative_worker":"Linux Docker non-root no-network no-new-privileges, pinned image SHA",
        "worker_image_sha":PINNED_DOCKER_IMAGE,
        "paper_equivalent_full_ifc_backend_coverage":False,
        "reason_not_full_equivalence":"Research toy XML compiler lacks elements/relationships/IFC2X3/IFC4 and geometric coverage; Python original source full access",
        "original_45_edit_task_denominator":45,
        "xml_previously_projectable_inputs":sum(x["xml_source_projection_previously_observed"]=="PROJECTABLE" for x in plan),
        "xml_previously_unsupported_inputs":sum(x["xml_source_projection_previously_observed"]!="PROJECTABLE" for x in plan),
        "same_model_and_max_tool_slots":True,
        "same_native_author_grader_post_run":True,
        "same_public_question_and_original_ifc":True,
        "actual_matched_model_runs":0,
        "new_paid_inference_requires_separate_owner_budget":True,
        "original_tasks":[public_safe_entry(x) for x in plan],
    }

def grade_author(author:Path, original:Path, candidate:Path, task_id:str)->dict:
    if _head(author)!=AUTHOR_SHA:
        raise ValueError("Author code has changed")
    if candidate.resolve()==original.resolve():
        raise ValueError("Scorer must receive a separately cloned source and result file")
    scored=subprocess.run(
        [sys.executable,"-I",str(WORKER),"--author-repo",str(author),
         "--test",task_id,"--source-ifc",str(original),
         "--edited-ifc",str(candidate)],
        capture_output=True,text=True,timeout=90,check=False,
    )
    try:
        obj=json.loads(scored.stdout.splitlines()[-1])
    except (ValueError,IndexError):
        return {"status":"AUTHOR_WORKER_NO_RESULT","exit":scored.returncode}
    if scored.returncode or obj.get("status")!="SCORED":
        return {"status":"AUTHOR_WORKER_FAILED",
                "error_type":obj.get("type","UNKNOWN")}
    return {"status":"AUTHOR_SCORED","original_author_score":obj["score"],
            "original_author_metrics":obj["metrics"],
            "original_author_full_mark":abs(obj["score"]-1)<1e-9}

def _sanitized_task_results(task:dict,arms:dict)->dict:
    return {
        "task_id":task["test_id"],"crud":task["crud"],
        "category":task["category"],
        "original_ifc_sha256":task["original_ifc_sha256"],
        "public_question_sha256":task["public_question_sha256"],
        "arms":arms,
    }

def paired_summary(pairs:list[dict],*,selected_count:int)->dict:
    """Original-author continuous-score comparison on exact paired cases.

    Unscored or unsupported cases are ZERO, not excluded. Strict independent
    task pass rates stay null until independently attested; paper model
    baselines use different models/settings and are NOT causal controls.
    """
    if selected_count<1 or selected_count>45 or len(pairs)>selected_count:
        raise ValueError("Invalid paired denominator")
    if len({p["task_id"] for p in pairs})!=len(pairs):
        raise ValueError("Duplicate benchmark task in paired outcome")
    full_cohort=(selected_count==45 and len(pairs)==45)
    out={
        "paired_tasks_recorded":len(pairs),"planned_tasks":selected_count,
        "original_45_task_population":45,
        "full_45_intention_to_test_complete":full_cohort,
        "incomplete_result_not_a_full_45_score":not full_cohort,
        "independent_strict_binary_success_rates":None,
        "metric_origin":"PINNED_ORIGINAL_BIBIMBAP_AUTHOR_WORKER",
        "paired_common_task_count":len(pairs),
        "arms":{},"paired_mean_delta_xml_minus_python":None,
        "category_breakdown":{},"crud_breakdown":{},
    }
    def observed(p,arm):
        a=p["arms"].get(arm,{})
        score=a.get("original_author_result") or {}
        value=score.get("original_author_score")
        if (score.get("status")=="AUTHOR_SCORED"
            and isinstance(value,(int,float)) and 0<=value<=1.0):
            return float(value)
        return 0.0
    def rates(group:list[dict],arm:str):
        n=len(group)
        scores=[observed(p,arm) for p in group]
        attempted=sum(p["arms"].get(arm,{}).get("model_requests",0)>0 for p in group)
        scoreable=sum((p["arms"].get(arm,{}).get("original_author_result") or {}).get("status")
                      =="AUTHOR_SCORED" for p in group)
        return {
            "denominator":n,"model_attempted_task_count":attempted,
            "original_author_scored_task_count":scoreable,
            "author_mean_zero_filled":sum(scores)/n if n else None,
            "original_author_full_marks_count":sum(abs(s-1)<1e-9 for s in scores),
            "original_author_full_mark_rate":sum(abs(s-1)<1e-9 for s in scores)/n if n else None,
            "full_independent_strict_task_success_rate":None,
            "explicit_unsupported_backend_task_count":sum(
                p["arms"].get(arm,{}).get("status")=="UNSUPPORTED_BACKEND_NOT_MODEL_FAILURE"
                for p in group),
        }
    for arm in ("XML","PYTHON"):
        out["arms"][arm]=rates(pairs,arm)
    if pairs:
        out["paired_mean_delta_xml_minus_python"]=sum(
            observed(p,"XML")-observed(p,"PYTHON") for p in pairs)/len(pairs)
    for attr,key in (("category_breakdown","category"),("crud_breakdown","crud")):
        for value in sorted({p[key] for p in pairs}):
            subset=[p for p in pairs if p[key]==value]
            out[attr][value]={a:rates(subset,a) for a in ("XML","PYTHON")}
    return out

def run_one_pair(client:object,task:dict,author:Path,dataset:Path,
                 folder:Path,budget:DurableBudget|None=None)->dict:
    """Run both matched arms against unique original IFC clones.

    No original author grader code/source or hidden reference is inside the
    LLM-visible tools or model messages. The grader runs after both arms.
    """
    if folder.exists() or folder.is_symlink():
        raise ValueError("Paired task folder must be fresh")
    folder.mkdir(parents=True)
    original=dataset/"ifc"/task["original_source_ifc_relpath"]
    if file_hash(original)!=task["original_ifc_sha256"]:
        raise ValueError("Original IFC drift")
    out={}
    protocol=PairProtocol()
    for arm in ("XML","PYTHON"):
        arm_folder=folder/arm.lower()
        source_hash=file_hash(original)
        try:
            if arm=="XML":
                session=XmlSourceEditSession(original,arm_folder)
            else:
                session=PythonIfcCodeSession(original,arm_folder,DockerIFCExecutor())
        except UnsupportedArm as exc:
            out[arm]={"status":"UNSUPPORTED_BACKEND_NOT_MODEL_FAILURE",
                       "reason_type":type(exc).__name__,"tool_calls":0,
                       "author_original_score":None,
                       "parity_limitation":True}
            continue
        except Exception as exc:
            out[arm]={"status":"BACKEND_SETUP_ERROR",
                       "reason_type":type(exc).__name__,
                       "tool_calls":0,"author_original_score":None}
            continue
        try:
            report=run_agent(client,session,arm=arm,public_question=task["public_question"],
                             protocol=protocol,budget=budget,
                             record_file=arm_folder/"provider_and_tool_transcript_local.json")
            status=report["status"]
        except ProviderBudgetError:
            report={"status":"NOT_ATTEMPTED_BUDGET_EXHAUSTED","model_requests":0,
                    "tool_calls":0}
            status=report["status"]
        except Exception as exc:
            report={"status":"AGENT_LOOP_ERROR",
                    "error_type":type(exc).__name__,"model_requests":0,
                    "tool_calls":0}
            status=report["status"]
        # The paper baseline scores the final copy, even if no commit(); the
        # unchanged file may earn partial scores under author Update metrics.
        final=arm_folder/"final_for_author.ifc"
        if session.output_ifc and session.output_ifc.is_file():
            shutil.copy2(session.output_ifc,final)
        else:
            shutil.copy2(original,final)
        score=grade_author(author,original,final,task["test_id"])
        out[arm]={
            "status":status,
            "model_requests":report.get("model_requests",0),
            "tool_calls":report.get("tool_calls",0),
            "reported_input_tokens":report.get("input_tokens",0),
            "reported_output_tokens":report.get("output_tokens",0),
            "original_author_result":score,
            "final_native_ifc_sha256":file_hash(final),
            "changed_from_original_ifc_bytes":file_hash(final)!=source_hash,
            "full_independent_strict_task_success":None,
            "tool_trace_sha256":report.get("raw_transcript_sha256"),
        }
        if file_hash(original)!=source_hash:
            raise ValueError("Original source IFC mutated during experiment")
    answer=_sanitized_task_results(task,out)
    _save_unique(folder/"pair_summary.json",answer)
    return answer

def smoke(author:Path,dataset:Path)->dict:
    """Deterministic OFFLINE integration with real XML compiler and Docker.

    No provider/API. Original IFC stays external and unchanged.
    """
    original=next(x for x in public_45(author,dataset) if x["test_id"]=="test_05")
    source=dataset/"ifc"/original["original_source_ifc_relpath"]
    digest=file_hash(source)
    from lxml import etree
    with tempfile.TemporaryDirectory(prefix="bibimbap-matched25-offline-") as tmp:
        root=Path(tmp)
        xml=XmlSourceEditSession(source,root/"xml")
        observed=xml.call("read_building_xml",{})
        if observed["status"]!="ok":
            raise AssertionError("XML source read failed")
        invalid=xml.call("submit_building_xml",{"xml_text":"<Building><broken>"})
        if invalid["status"]!="error" or xml.output_ifc is not None:
            raise AssertionError("Invalid XML must not commit")
        old=etree.fromstring(xml.original_xml)
        namespace=etree.QName(old).namespace
        levels=old.find("{"+namespace+"}Levels")
        elements=old.find("{"+namespace+"}Elements")
        ground=next((x for x in levels if x.get("elevation")=="0"),None)
        if ground is None or elements is None:
            raise AssertionError("Public original wall Level absent")
        etree.SubElement(elements,"{"+namespace+"}Wall",attrib={
            "id":"matched25_offline_control_wall","level":ground.get("id"),
            "x1":"0","y1":"-10","z1":"0","x2":"15","y2":"-10",
            "z2":"0","height":"3","thickness":"0.2"})
        # Trusted offline local fixture: NOT a paid LLM output or benchmark result.
        valid=xml.call("submit_building_xml",{"xml_text":etree.tostring(
            old,encoding="unicode",xml_declaration=False)})
        if valid["status"]!="ok":
            raise AssertionError("Valid fixed XML fixture did not compile: "+str(valid))
        oldhash=file_hash(xml.output_ifc)
        invalid_again=xml.call("submit_building_xml",{"xml_text":"<WrongRoot/>"})
        if invalid_again["status"]!="error" or file_hash(xml.output_ifc)!=oldhash:
            raise AssertionError("Invalid submission changed last valid compiled IFC")
        py=PythonIfcCodeSession(source,root/"python",DockerIFCExecutor())
        query=py.call("execute_ifc_code",{"code":"result=len(ifc.by_type('IfcWall'))"})
        if query.get("status")!="ok" or not isinstance(query.get("result"),int):
            raise AssertionError("Original-style Docker IFC read failed: "+str(query))
        oldpy=file_hash(py.current)
        edit=py.call("execute_ifc_code",{"code":"p=ifc.by_type('IfcWall')[0];p.Name='TestOnlyNoProductionCommit';commit();result='saved'"})
        if edit.get("status")!="ok" or not edit.get("committed") or file_hash(py.current)==oldpy:
            raise AssertionError("Sandbox commit did not persist across calls: "+str(edit))
        repeat=py.call("execute_ifc_code",{"code":"result=ifc.by_type('IfcWall')[0].Name"})
        if repeat.get("status")!="ok" or repeat.get("result")!="TestOnlyNoProductionCommit":
            raise AssertionError("Sandbox second call did not observe saved IFC")
        # Exercise repeated tool calls through the agent state machine, with
        # a FAKE provider (not OpenAI; no billing) and real XML tools.
        fake_xml=XmlSourceEditSession(source,root/"fake_xml")
        fake=OfflineFakeClient([
            [_FunctionCall("read_building_xml","{}","offline_call_1")],
            [_FunctionCall("submit_building_xml",json.dumps({"xml_text":"<bad"}),"offline_call_2")],
            [_FunctionCall("read_building_xml","{}","offline_call_3")],
            [],
        ])
        result=run_agent(fake,fake_xml,arm="XML",
                         public_question=original["public_question"],
                         protocol=PairProtocol(),budget=None,
                         record_file=root/"fake_xml"/"offline_transcript.json")
        if result["tool_calls"]!=3 or result["model_requests"]!=4 or result["status"]!="MODEL_FINAL_MESSAGE":
            raise AssertionError("Multi-turn tool feedback loop failed")
        if file_hash(source)!=digest:
            raise AssertionError("Real original task's IFC was modified")
        return {
            "status":"MATCHED25_OFFLINE_DOCKER_XML_TOOL_LOOP_PASS",
            "offline_provider_model_calls":0,
            "offline_api_charges_usd":"0",
            "control_source_original_hash_unchanged":True,
            "real_native_xml_positive_control":True,
            "real_native_xml_invalid_then_recovery":True,
            "original_python_ifc_query_and_commit_in_docker":True,
            "original_python_ifc_commit_visible_next_call":True,
            "simulated_agent_tool_calls":result["tool_calls"],
            "simulated_agent_provider_messages":result["model_requests"],
            "max_tools_both_arms":MAX_TOOL_CALLS,
            "linux_image":PINNED_DOCKER_IMAGE,
        }

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight",action="store_true")
    mode.add_argument("--smoke",action="store_true")
    mode.add_argument("--run-approved",action="store_true")
    parser.add_argument("--author-repo",required=True,type=Path)
    parser.add_argument("--dataset",required=True,type=Path)
    parser.add_argument("--output-json",type=Path)
    parser.add_argument("--approval",type=Path)
    parser.add_argument("--task-id",action="append")
    parser.add_argument("--run-dir",type=Path)
    args=parser.parse_args()
    author=args.author_repo.resolve(strict=True)
    dataset=args.dataset.resolve(strict=True)
    if args.preflight:
        result=offline_preflight(author,dataset)
    elif args.smoke:
        result=smoke(author,dataset)
    else:
        if args.approval is None or args.run_dir is None:
            parser.error("Paid pairing requires independent owner approval file and unused run directory")
        # Only the user can provide a newly approved config. Do NOT infer
        # approval from earlier $1 budget (which is already exhausted).
        cfg=json.loads(args.approval.read_text(encoding="utf8"))
        if not isinstance(cfg,dict) or cfg.get("approved") is not True:
            parser.error("Owner has not provided the new paid budget")
        if args.run_dir.exists() or args.run_dir.is_symlink():
            parser.error("Paid run directory already issued, never replay")
        tasks=public_45(author,dataset)
        if args.task_id:
            chosen=set(args.task_id)
            if len(chosen)!=len(args.task_id):
                parser.error("Duplicate task IDs refused")
            tasks=[t for t in tasks if t["test_id"] in chosen]
            if len(tasks)!=len(chosen):
                parser.error("Unknown original task ID")
        args.run_dir.mkdir(parents=True)
        budget=DurableBudget(args.run_dir/"budget_ledger.json",str(cfg.get("cap_usd")),
                             approval=cfg)
        from dotenv import load_dotenv
        load_dotenv(ROOT.parent/"bim-markup-bench"/".env",override=False)
        import os
        if os.environ.get("OPENAI_MODEL")!=MODEL or not os.environ.get("OPENAI_API_KEY"):
            raise ProviderBudgetError("Exact user model/API key missing")
        if os.environ.get("OPENAI_BASE_URL"):
            raise ProviderBudgetError("Custom API endpoint prohibited")
        from openai import OpenAI
        client=OpenAI(timeout=140,max_retries=0)
        all_results=[]
        for item in tasks:
            if budget.data["status"]=="BUDGET_EXHAUSTED":
                break
            all_results.append(run_one_pair(client,item,author,dataset,
                                            args.run_dir/item["test_id"],budget))
        result={
            "status":"PAIRED_RUN_FINISHED" if len(all_results)==len(tasks)
               else "BUDGET_OR_RUNTIME_PARTIAL_RUN",
            "model":MODEL,"original_45_itt_denominator":45,
            "selected_task_count":len(tasks),"finished_pairs":len(all_results),
            "budget":budget.data,
            "paired_metrics":paired_summary(all_results,selected_count=len(tasks)),
            "pairs":all_results,
            "publication_restriction":"Local research only, no private source/GT or raw model code in Git",
            "full_independent_strict_task_success_rate":None,
            "paper_equivalent_full_backend_coverage":False,
        }
        _save_unique(args.run_dir/"cohort_local_only.json",result)
    # Only metadata/repro info, never model-generated code, is printed.
    summary={
        "status":result.get("status"),
        "model_calls":result.get("model_calls",None),
        "usd_paid":result.get("usd_paid",None),
        "original_45_edit_task_denominator":result.get("original_45_edit_task_denominator",45),
        "xml_previously_projectable_inputs":result.get("xml_previously_projectable_inputs",None),
        "xml_previously_unsupported_inputs":result.get("xml_previously_unsupported_inputs",None),
        "simulated_agent_tool_calls":result.get("simulated_agent_tool_calls",None),
        "finished_pairs":result.get("finished_pairs",None),
    }
    if args.output_json:
        _save_unique(args.output_json,result)
    print(json.dumps(summary,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
