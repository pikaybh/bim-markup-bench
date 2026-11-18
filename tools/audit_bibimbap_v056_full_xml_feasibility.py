"""v0.56 ZERO-PAID real-original D snapshot output feasibility/transport replay.

Developer-authored public-source-only positive/negative controls measure the
COMPLETE XML final-state response demand. No LLM, model endpoint, token SDK,
paid provider, original author's hidden scorer or GT ever used. The streaming
interface is an explicitly DIFFERENT transport from v0.55 one-shot D and may
NOT be called equivalent without separately measuring provider billed tokens.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v055_transactional_primary_DI_sessions import (
    SchemaGuardedDirectStateSession055,SchemaGuardedLivePythonSession055,
)
from tools.bibimbap_v056_whole_state_stream import (
    WholeStateStreamDirectSession056,split_whole_final_state_utf8_v056,
    MAX_CHUNK_UTF8_BYTES,MAX_CHUNKS_PER_COMPLETE_STATE,
)
from tools.audit_bibimbap_v055_live_schema_transactions import (
    developer_XML_final,
)
from tools.bibimbap_v052_live_docker_controls import (
    developer_python_source,
)


ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v056_original4_full_XML_response_feasibility_20261118.json"
PARENT_SHA="e651a612e718281fa1ecb2741cf29216796be5df6f6d00439894e0b591b0437c"
PARENT_HEAD="6c55ffd7d6ed734b98cf9f7ecab500a7889f96b6"
TASKS=("geometry_test_14","geometry_test_15",
       "topological_test_11","topological_test_17")


def need(ok:bool,msg:str)->None:
    if not ok: raise AssertionError(msg)


def _sha(raw:bytes)->str:
    return sha256(raw).hexdigest()


def _canonical(obj:dict)->bytes:
    return (json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)
            +"\n").encode("utf8")


def build_report()->dict:
    need(file_hash(ROOT/"reports"/
        "bibimbap_v055_primary_DI_schema_guard_live_transactions_20261118.json")
        ==PARENT_SHA,"Frozen source-original v0.55 real Docker report changed")
    rows=public_45(AUTHOR,DATA)
    need(len(rows)==45
         and len({x["original_ifc_sha256"] for x in rows})==31
         and Counter(x["crud"] for x in rows)==
             {"create":15,"update":15,"delete":15},
         "Original-public 45/31 task population changed")
    tasks={x["test_id"]:x for x in rows}
    records=[]
    source_info={}
    with TemporaryDirectory(prefix="v056-NO-model-D-snapshot-") as tmp:
        root=Path(tmp)
        for idx,tid in enumerate(TASKS):
            row=tasks[tid]
            source=DATA/"ifc"/row["original_source_ifc_relpath"]
            original_sha=row["original_ifc_sha256"]
            need(file_hash(source)==original_sha,"Original IFC SHA changed")
            D=SchemaGuardedDirectStateSession055(
                source,root/f"D_initial_{idx}")
            I=SchemaGuardedLivePythonSession055(
                source,root/f"I_initial_{idx}")
            ds=D.call("read_building_xml",{})
            ips=I.call("read_building_xml",{})
            need(ds["status"]==ips["status"]=="ok"
                 and ds["xml"]==ips["xml"],
                 "Original four genuine D/I model read XML differs")
            initial=ds["xml"]
            d_tools=_canonical({"tools":D.tools})
            i_tools=_canonical({"tools":I.tools})
            streamed=WholeStateStreamDirectSession056(
                source,root/f"S_initial_{idx}")
            from_stream=streamed.call("read_building_xml",{})
            need(from_stream["xml"]==initial
                 and streamed.tools[0]==D.tools[0]
                 and streamed.tools[1]!=D.tools[1],
                 "v0.56 modified original source or silently kept old schema")
            stream_tool_bytes=len(_canonical({"tools":streamed.tools}))
            need(len(streamed.tools)==2 and
                 [x["name"] for x in streamed.tools]==
                 ["read_building_xml","submit_complete_building_xml_chunk"],
                 "Stream is not pure final-state D XML two-tool transport")
            source_info[tid]={
                "original_IFC_SHA256":original_sha,
                "original_public_question_SHA256":row["public_question_sha256"],
                "initial_source_D_I_stream_same_UTF8_bytes":True,
                "initial_full_XML_UTF8_bytes":len(initial.encode("utf8")),
                "initial_XML_SHA256":_sha(initial.encode("utf8")),
                "original_D_tool_schema_JSON_UTF8_bytes":len(d_tools),
                "original_I_tool_schema_JSON_UTF8_bytes":len(i_tools),
                "new_stream_D_tool_schema_JSON_UTF8_bytes":stream_tool_bytes,
                "model_facing_stream_schema_CHANGED_from_v055":True,
                "provider_model_actual_prompt_tokens":None,
                "provider_model_actual_completion_tokens":None,
            }
            for positive in (True,False):
                label="positive" if positive else "negative"
                edited=developer_XML_final(
                    row,source,positive=positive)
                total_bytes=len(edited.encode("utf8"))
                chunks=split_whole_final_state_utf8_v056(edited)
                need("".join(chunks).encode("utf8")==edited.encode("utf8"),
                     "Whole final XML streaming changed a byte")
                need(len(chunks)<=MAX_CHUNKS_PER_COMPLETE_STATE
                     and 1+len(chunks)<=25,
                     "Chunk transport exceeds same assigned 25 call cap")
                direct=SchemaGuardedDirectStateSession055(
                    source,root/f"D_once_{idx}_{label}")
                once=direct.call("submit_building_xml",{
                    "xml_text":edited})
                need(once["status"]=="ok" and
                     direct.output_ifc is not None,
                     "Original one-shot primary state failed")
                streamed=WholeStateStreamDirectSession056(
                    source,root/f"D_stream_{idx}_{label}")
                r=streamed.call("read_building_xml",{})
                need(r["xml"]==initial,"Different read state after chunk reset")
                for ci,piece in enumerate(chunks):
                    reply=streamed.call(
                        "submit_complete_building_xml_chunk",{
                        "sequence":ci,
                        "chunk_text":piece,
                        "final":ci==len(chunks)-1,
                    })
                    if ci<len(chunks)-1:
                        need(reply["status"]=="ok"
                             and reply["native_ifc_committed"] is False
                             and streamed.output_ifc is None
                             and streamed.current_xml==streamed.original_xml,
                             "Incomplete XML was compiled or promoted")
                need(reply["status"]=="ok"
                     and reply["native_ifc_sha256"]==
                         once["native_ifc_sha256"]
                     and streamed.current_xml==edited.encode("utf8")
                     and streamed.output_ifc is not None
                     and file_hash(streamed.output_ifc)==
                        file_hash(direct.output_ifc)
                     and streamed.calls_used==1+len(chunks),
                     "Chunk-reassembled D did not preserve full-state IFC semantics")
                python=developer_python_source(
                    tid,row["public_question"],positive=positive)
                code_b=len(python.encode("utf8"))
                tool_payload_D=len(json.dumps({
                    "xml_text":edited},ensure_ascii=False).encode("utf8"))
                tool_payload_I=len(json.dumps({
                    "code":python},ensure_ascii=False).encode("utf8"))
                # Conservative local *byte* ledger, NOT fake billed tokens.
                records.append({
                    "original_task_id":tid,
                    "source_derived_developer_fixture":label,
                    "model_generated":False,
                    "full_final_state_XML_SHA256":_sha(edited.encode("utf8")),
                    "full_final_state_XML_UTF8_bytes":total_bytes,
                    "one_shot_D_tool_argument_JSON_UTF8_bytes":tool_payload_D,
                    "independent_I_developer_Python_UTF8_bytes":code_b,
                    "I_developer_tool_argument_JSON_UTF8_bytes":tool_payload_I,
                    "D_to_I_text_utf8_byte_ratio":round(total_bytes/code_b,5),
                    "split_chunk_max_UTF8_bytes":MAX_CHUNK_UTF8_BYTES,
                    "complete_chunks_required":len(chunks),
                    "D_stream_total_calls_including_one_read":
                        streamed.calls_used,
                    "within_25_tool_calls":True,
                    "streamed_FULL_XML_reassembled_without_change":True,
                    "original_one_shot_D_IFC_SHA256":once["native_ifc_sha256"],
                    "streamed_D_IFC_SHA256":reply["native_ifc_sha256"],
                    "new_IFC_schema_error_count":0,
                    "provider_model_actual_completion_tokens":None,
                    "provider_model_actual_prompt_tokens":None,
                    "actual_provider_max_output_tokens":None,
                    "experimental_budget_equivalence_proven":False,
                })
                need(file_hash(source)==original_sha,
                     "Original source modified by developer transport audit")
        # Atomic D-state security case: reassembly rejection and recovery
        slab=tasks["geometry_test_14"]
        source=DATA/"ifc"/slab["original_source_ifc_relpath"]
        one=WholeStateStreamDirectSession056(
            source,root/"D_rejected_then_good")
        good=developer_XML_final(slab,source,positive=True)
        chunks=split_whole_final_state_utf8_v056(good)
        one.call("read_building_xml",{})
        reject=one.call("submit_complete_building_xml_chunk",{
            "sequence":1,"chunk_text":"not whole XML",
            "final":True,
        })
        need(reject["status"]=="error"
             and one.current_xml==one.original_xml
             and one.output_ifc is None
             and one.calls_used==2,
             "Out-of-order chunk wrongly accepted")
        for i,part in enumerate(chunks):
            result=one.call("submit_complete_building_xml_chunk",{
                "sequence":i,"chunk_text":part,
                "final":i==len(chunks)-1})
        need(result["status"]=="ok"
             and one.output_ifc is not None,
             "Cannot recover after malformed stream")
        before_state=one.current_xml
        before_sha=file_hash(one.output_ifc)
        # Send malformed final XML after a valid native IFC; fail atomically.
        broken=one.call("submit_complete_building_xml_chunk",{
            "sequence":0,"chunk_text":"<InvalidState/>","final":True})
        need(broken["status"]=="error"
             and one.current_xml==before_state
             and file_hash(one.output_ifc)==before_sha,
             "Invalid fully assembled XML destroyed last-good native IFC")
        # No bypass into original v0.55 one-shot tool in streaming arm.
        bypass=one.call("submit_building_xml",{"xml_text":good})
        need(bypass["status"]=="error"
             and before_sha==file_hash(one.output_ifc),
             "v0.55 one-shot tool bypassed v0.56 experimental transcript")
        security={
            "out_of_order_chunk_rejected":True,
            "recovery_with_complete_good_final_state":True,
            "bad_finished_XML_keeps_prior_native_sha":True,
            "one_shot_D_tool_blocked_from_stream_arm":True,
            "whole_final_state_reassembled_before_any_diff":True,
        }
    need(len(records)==8 and len(source_info)==4,
         "Missing real original-four final state output feasibility rows")
    return {
        "status":"V056_OFFLINE_FULL_XML_OUTPUT_FEASIBILITY_AND_STREAMING_EQUIVALENCE_PASS",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/227",
        "frozen_parent_v055_head":PARENT_HEAD,
        "prior_v055_native_D_I_report_SHA256":PARENT_SHA,
        "original_public_edit_tasks":45,
        "unique_original_source_IFCs":31,
        "engineering_selected_exploratory_original_tasks":list(TASKS),
        "other_41_original_tasks_NOT_ATTEMPTED":41,
        "primary_D_original_semantics":"WHOLE_FINAL_XML_STATE",
        "original_D_one_shot_edits_in_developer_audit":8,
        "new_stream_D_full_final_state_edits_in_developer_audit":8,
        "new_I_live_Docker_calls_this_checkpoint":0,
        "prior_I_real_Docker_evidence_retained_in_frozen_v055_report":True,
        "actual_LLM_D_I_trials":0,
        "actual_paid_model_calls":0,
        "model_snapshot_and_provider_endpoint":None,
        "model_provider_billed_input_output_tokens":None,
        "provider_max_completion_tokens":None,
        "model_data_send_approval":False,
        "data_redistribution_rights_proven":False,
        "one_shot_D_complete_final_state_output_is_large":True,
        "no_provider_specific_token_fit_or_comparability_claim":True,
        "chunk_transport_new_schema_not_identical_to_original_D":True,
        "chunking_changes_model_tool_feedback_and_call_frequency":True,
        "MAX_UTF8_BYTES_PER_MODEL_CHUNK":MAX_CHUNK_UTF8_BYTES,
        "MAX_TOTAL_MODEL_TOOL_CALLS_PER_ARM":25,
        "model_token_budget_causal_parity_not_proven":True,
        "all_8_streamed_full_final_states_exactly_same_IFC_as_one_shot":True,
        "real_native_IFC_source_unmodified":True,
        "security_rollback_controls":security,
        "initial_source_and_tool_schemas":source_info,
        "full_final_state_developer_output_records":records,
    }


def main()->int:
    cli=argparse.ArgumentParser(description=__doc__)
    group=cli.add_mutually_exclusive_group(required=True)
    group.add_argument("--write",action="store_true")
    group.add_argument("--check",action="store_true")
    args=cli.parse_args()
    out=_canonical(build_report())
    if args.write:
        with REPORT.open("xb") as f:
            f.write(out)
    else:
        need(REPORT.is_file() and REPORT.read_bytes()==out,
             "Frozen source-original full-XML streaming report changed")
    print("V056_OFFLINE_D_FULL_XML_STREAMING=PASS "
          "STATE_PAIRS=8/8 SOURCE_PARITY=4/4 "
          "MODEL_CALLS=0 PAID_CALLS=0 SHA256="+_sha(out))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
