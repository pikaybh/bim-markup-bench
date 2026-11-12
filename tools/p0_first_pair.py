"""P0 #97: first *real* LLM A/B on owned IFC only.

Default prepare mode has ZERO model calls or charges. Live mode requires an
explicit owner-approved config and the OpenAI API key. The same LLM is called
once for D XML and once for I Python; results are independently checked.
Never pass original BIM-Edit/GT or run model-generated Python on Windows.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
import uuid

from src.direct_markup.agent_runner import (
    SourceOnlySettings, SourceFileEdit, TrustedCompilationController,
    stage_source_only_workspace,
)
from src.imperative_control.agent_runner import (
    ControlConfig, CandidateCode, ImperativeControlSession,
    create_matched_observations,
)
from src.runner.own_result_grader import evaluate as grade_own_ifc
from src.runner.generated_candidate import run_offline_own_generated_candidate
from src.runner.worker_admission import EXPECTED_OWN_SOURCE_SHA256

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tests/fixtures/synthetic/input.ifc"
TASK_ID="OWN-P0-FIRST-REAL-LLM-001"
INSTRUCTION=("Change only North Wall height from 3.0 m to 3.3 m. "
    "Do not modify any other IFC object, identity, relationship or geometry.")
IMAGE_ID="sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee"
OUTPUT_TOKENS=3500

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def public()->dict:
    return {"task_id":TASK_ID,"instruction":INSTRUCTION,"input_file":"input.ifc"}

def packets()->dict:
    if (not SOURCE.is_file() or SOURCE.is_symlink() or
        sha(SOURCE.read_bytes())!=EXPECTED_OWN_SOURCE_SHA256):
        raise ValueError("Own synthetic IFC absent/changed")
    with TemporaryDirectory(prefix="p0-packets-") as tmp:
        d=stage_source_only_workspace(
            SOURCE,Path(tmp)/"D",public(),SourceOnlySettings()
        ).agent_visible_context()
        i=create_matched_observations(SOURCE,public())
        if (d.xml_text!=i.model_xml_text or
            d.language_spec!=i.toy_language_spec or
            i.input_ifc_sha256!=EXPECTED_OWN_SOURCE_SHA256):
            raise ValueError("D/I common observation mismatch")
        notes=ImperativeControlSession(i,ControlConfig()).model_visible_context()["api_reference_notes"]
    common=("PUBLIC TASK:\n"+INSTRUCTION+
        "\n\nSAME ORIGINAL IFC XML VIEW:\n"+d.xml_text+
        "\n\nSHARED XML LANGUAGE SPECIFICATION:\n"+d.language_spec)
    system=("Solve the public BIM edit task using only the supplied IFC "
        "source observation. Keep all unrelated elements intact. "
        "Output exactly one source file, without explanation or fences.")
    result={
        "D_XML":{
            "instructions":system+
                " Declarative condition: edit the actual XML document state. "
                "Return the full updated building.xml. No Python or command lists.",
            "input":common+"\n\nReturn complete updated XML.",
        },
        "I_PYTHON":{
            "instructions":system+
                " Imperative condition: write Python/IfcOpenShell script. "
                "Read /input/input.ifc and write /output/result.ifc. "
                "No shell, network, additional files or XML modifications.",
            "input":common+"\n\nImperative-only IFC API reference:\n"+
                notes+"\n\nReturn complete solution.py text.",
        },
    }
    if any(len((p["instructions"]+p["input"]).encode("utf8"))>40000
           for p in result.values()):
        raise ValueError("Prompt over P0 bound")
    return result

def manifest()->dict:
    prompts=packets()
    return {
        "status":"PREPARED_ZERO_LLM_CALLS",
        "task_id":TASK_ID,"original_ifc_sha256":EXPECTED_OWN_SOURCE_SHA256,
        "owned_fixture":True,"official_bim_edit_task":False,
        "experiment_kind":"exploratory_owned_synthetic",
        "same_public_instruction":True,"same_model_and_attempt_budget":True,
        "provider_calls":0,"paid_spend_usd":"0",
        "prompts":prompts,
        "common_public_task_sha256":sha(INSTRUCTION.encode("utf8")),
        "common_original_xml_sha256":sha(
            create_matched_observations(SOURCE,public()).model_xml_text.encode("utf8")),
    }

def approved_budget(cfg:dict, prompts:dict)->None:
    keys={"approved","issue","model","input_rate_per_million_usd",
          "output_rate_per_million_usd","cap_usd","price_reference",
          "price_checked_utc","max_output_tokens"}
    if not isinstance(cfg,dict) or set(cfg)!=keys:
        raise ValueError("Explicit approved P0 model/budget schema required")
    if (cfg["approved"] is not True or
        cfg["issue"]!="https://github.com/pikaybh/bim-markup-bench/issues/97" or
        cfg["price_reference"]!="https://developers.openai.com/api/docs/pricing" or
        cfg["max_output_tokens"]!=OUTPUT_TOKENS or
        type(cfg["model"]) is not str or
        not re.fullmatch(r"[A-Za-z0-9_.-]{3,90}",cfg["model"]) or
        cfg["model"]=="CHOOSE_APPROVED_OPENAI_API_MODEL" or
        type(cfg["price_checked_utc"]) is not str or
        not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",
                         cfg["price_checked_utc"])):
        raise ValueError("P0 model/budget approval not established")
    # Exact Decimal rates must be manually verified and authorized, not
    # inferred from any example. One attempt/arm, never retry provider calls.
    try:
        if any(type(cfg[key]) is not str for key in (
                "input_rate_per_million_usd","output_rate_per_million_usd","cap_usd")):
            raise ValueError("Exact decimal rate/cap strings required")
        r_in=Decimal(cfg["input_rate_per_million_usd"])
        r_out=Decimal(cfg["output_rate_per_million_usd"])
        cap=Decimal(cfg["cap_usd"])
    except Exception as exc:
        raise ValueError("Malformed approved pricing") from exc
    if not all(x.is_finite() and x>0 for x in (r_in,r_out,cap)) or cap>10:
        raise ValueError("Unapproved spending bound")
    # Conservative byte-based input budget: NOT measured tokens.
    reserved=sum(
        (Decimal(len((p["instructions"]+p["input"]).encode("utf8"))+2048)
         *r_in+Decimal(OUTPUT_TOKENS)*r_out)/Decimal(1000000)
        for p in prompts.values())
    if reserved>cap:
        raise ValueError("Two model requests exceed approved maximum cap")

def _d_output(text:str,folder:Path)->dict:
    s=stage_source_only_workspace(
        SOURCE,folder/"D_workspace",public(),SourceOnlySettings())
    v=s.agent_visible_context()
    accepted=s.attempt(SourceFileEdit(
        "building.xml",v.xml_byte_sha256,"whole_file_rewrite","",text,False))
    if accepted["status"]!="ACCEPTED_VALID_XML":
        raise ValueError("D model did not output accepted XML")
    out=folder/"D_result.ifc"
    c=TrustedCompilationController.compile_accepted(s,SOURCE,out)
    grade=grade_own_ifc(SOURCE,out)
    if grade["status"]!="OWN_WALL_EDIT_VERIFIED":
        raise ValueError("D native result incorrect")
    return {"passed":True,"result_sha256":sha(out.read_bytes()),
            "native_change_ops":[x.operation for x in c.operations]}

def _i_output(text:str,folder:Path)->dict:
    o=create_matched_observations(SOURCE,public())
    s=ImperativeControlSession(o,ControlConfig())
    accepted=s.submit_code(CandidateCode(o.input_ifc_sha256,text,False))
    if accepted["status"]!="ACCEPTED_SOURCE_ONLY_NOT_EXECUTABLE":
        raise ValueError("I model output rejected by AST preflight")
    raw=text.encode("utf8")
    grade=run_offline_own_generated_candidate(
        IMAGE_ID,raw,sha(raw),wall_seconds=15,seed=97,
        export_verified_own_ifc=folder/"I_result.ifc")
    if grade["status"]!="OWN_SYNTHETIC_DYNAMIC_CANDIDATE_VERIFIED":
        raise ValueError("I sandbox/native result incorrect")
    verified=folder/"I_result.ifc"
    if not verified.is_file() or sha(verified.read_bytes())!=grade["output_sha256"]:
        raise ValueError("Isolated OWN IFC export missing or hash mismatch")
    return {"passed":True,"result_sha256":grade["output_sha256"],
            "saved_file":"I_result.ifc","Linux_worker_isolated":True}

def _call_model(client,p:dict,model:str):
    return client.responses.create(
        model=model,instructions=p["instructions"],input=p["input"],
        max_output_tokens=OUTPUT_TOKENS,store=False,tools=[],
    )

def run(cfg:dict,folder:Path,*,client=None)->dict:
    p=packets()
    approved_budget(cfg,p)
    if client is None:
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("No API key; paid requests not permitted")
        from openai import OpenAI
        client=OpenAI(timeout=90,max_retries=0)
    if folder.exists() or folder.is_symlink():
        raise ValueError("Run destination must be new")
    folder.mkdir(parents=True,mode=0o700)
    report={
        "scope":"OWN_SYNTHETIC_NOT_OFFICIAL",
        "status":"PARTIAL_OR_FAILED","model":cfg["model"],
        "original_ifc_sha256":EXPECTED_OWN_SOURCE_SHA256,
        "provider_bill_reconciliation":"PENDING",
        "approved_cap_usd":cfg["cap_usd"],
        "arms":{},"actual_model_calls_attempted":0,
    }
    for arm in ("D_XML","I_PYTHON"):
        attempt={"model_output_available":False,"native_success":False}
        report["arms"][arm]=attempt
        try:
            t0=perf_counter()
            attempt["provider_request_attempted"]=True
            report["actual_model_calls_attempted"]+=1
            answer=_call_model(client,p[arm],cfg["model"])
            attempt["response_seconds"]=round(perf_counter()-t0,3)
            if answer.status!="completed":
                raise ValueError("Provider response incomplete")
            source=answer.output_text
            if (not isinstance(source,str) or
                not 0<len(source.encode("utf8"))<=32768 or
                source.lstrip().startswith(chr(96)*3)):
                raise ValueError("Model did not provide raw source")
            attempt["model_output_available"]=True
            name="D_model_generated.xml" if arm=="D_XML" else "I_model_generated.py"
            # Preserve the provider's source text byte-for-byte on Windows.
            # Path.write_text() with newline=None would silently turn LF into CRLF.
            with (folder/name).open("x",encoding="utf8",newline="\n") as saved:
                saved.write(source)
            attempt["source_file"]=name
            attempt["source_sha256"]=sha(source.encode("utf8"))
            if getattr(answer,"usage",None) is None:
                raise ValueError("Provider did not return usage for cost accounting")
            input_used=answer.usage.input_tokens
            output_used=answer.usage.output_tokens
            if (type(input_used) is not int or type(output_used) is not int
                    or input_used<0 or output_used<0):
                raise ValueError("Invalid reported provider token counts")
            attempt["reported_input_tokens"]=input_used
            attempt["reported_output_tokens"]=output_used
            attempt["usage_estimated_cost_usd"]=str(
                (Decimal(input_used)*Decimal(cfg["input_rate_per_million_usd"])
                 +Decimal(output_used)*Decimal(cfg["output_rate_per_million_usd"]))
                /Decimal(1000000))
            attempt["native"]=(_d_output(source,folder)
                               if arm=="D_XML" else _i_output(source,folder))
            attempt["native_success"]=True
        except Exception as exc:
            # No exception string: it may contain API identifiers or secrets.
            attempt["error_type"]=type(exc).__name__
            attempt["native_success"]=False
        finally:
            (folder/"results.json").write_text(
                json.dumps(report,indent=2,sort_keys=True)+"\n",
                encoding="utf8")
    report["status"]="FIRST_REAL_LLM_PAIR_ATTEMPTED"
    report["two_native_successes"]=all(
        report["arms"][a]["native_success"] for a in ("D_XML","I_PYTHON"))
    (folder/"results.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return report

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--prepare",action="store_true")
    ap.add_argument("--run-approved",action="store_true")
    ap.add_argument("--approval-file",type=Path)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    if args.prepare==args.run_approved:
        ap.error("Specify exactly one of --prepare or --run-approved")
    if args.prepare:
        info=manifest()
        if args.out:
            if args.out.exists() or args.out.is_symlink():
                ap.error("No overwrite")
            with args.out.open("x",encoding="utf8",newline="\n") as dest:
                dest.write(json.dumps(info,indent=2,sort_keys=True)+"\n")
        print(json.dumps({k:info[k] for k in (
            "status","task_id","original_ifc_sha256","provider_calls",
            "paid_spend_usd")},sort_keys=True))
        return 0
    if args.approval_file is None or args.out is None:
        ap.error("Live run requires --approval-file and new --out dir")
    cfg=json.loads(args.approval_file.read_text(encoding="utf8"))
    info=run(cfg,args.out)
    print(json.dumps({k:info[k] for k in (
        "status","model","two_native_successes","actual_model_calls_attempted")},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
