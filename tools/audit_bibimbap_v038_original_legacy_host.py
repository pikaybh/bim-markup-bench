"""v0.38 actual opt-in matched XML tool interface P0 source and native write audit.

No scorer, hidden GT, model, Python agent, Docker, or source IFC mutation.
The generated complete XML states are *developer illustrative controls*, not
real LLM solutions or scientific task-success outcomes.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v8_legacy_projection import Q,parse_v8
from tools.audit_bibimbap_author import _head,AUTHOR_SHA,DATA_SHA
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import (
    XmlSourceEditSession,UnsupportedArm,file_hash,
)
from tools.bibimbap_v038_legacy_live_gate import (
    SOURCE_PROFILES,TASKS,verify_native_original_restored,
)

ROOT=Path(__file__).resolve().parents[1]
ISSUE="https://github.com/pikaybh/bim-markup-bench/issues/191"
PARENT_REPORT=(
    "reports/bibimbap_v037_original10_create_live_source_and_writer_gates_20261117.json",
    "33d99e6fb624e6a5e89dc301791c269bd5ca7d2666d8618fc67379664938501f",
)
LEGACY_REPORT=(
    "reports/bibimbap_v08_legacy_ifc2x3_ifc4_d0_20261113.json",
    "1264e33403a8b7e554913a34fc79b031890fd0aee832bc6b8f2010f912a5b4e0",
)
# Original independently published SHA pins are frozen in v0.37, not
# recomputed from a developer-authored private answer/GT.
EXPECTED_IFC_CLASSES={
    "geometry_test_03":("IFC2X3",("IfcOpeningElement","IfcDoor")),
    "geometry_test_04":("IFC2X3",("IfcSpace",)),
    "geometry_test_05":("IFC4",("IfcWall",)),
}
V08_ILLUSTRATIVE_NORTH_WALL="3YQ$1CPXD2Mh2vQ18vV$ig"


class V038EvidenceDrift(ValueError):
    pass


def require(ok:bool,reason:str)->None:
    if not ok:raise V038EvidenceDrift(reason)


def original_inputs(root:Path,author:Path,data:Path)->tuple[dict,dict]:
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Published original BIBIMBAP author/data Git revision changed")
    frozen={}
    for name,pin in (PARENT_REPORT,LEGACY_REPORT):
        f=root/name
        require(f.is_file() and not f.is_symlink() and file_hash(f)==pin,
                "Historical original evidence report SHA changed: "+name)
        frozen[name]=json.loads(f.read_text(encoding="utf8"))
    old=frozen[PARENT_REPORT[0]]
    require(old["original_public_full_ITT_45"]==45
            and old["original_public_all_CREATE_15"]==15
            and old["remaining_original_CREATE_not_yet_native_D0_I0_paired"]==10
            and old["source_schema_hard_rejections"]==3
            and old["real_matched_LLM_D_I_trials"]==0,
            "v0.37 fixed 45/15/10 P0 original evidence drifted")
    old_rows={r["task_id"]:r for r in old["rows"]}
    public=public_45(author,data)
    require(len(public)==45 and len({x["test_id"] for x in public})==45
            and Counter(x["crud"] for x in public)==
                {"create":15,"update":15,"delete":15},
            "Original published 45 task population changed")
    task_map={t["test_id"]:t for t in public}
    require(set(TASKS)==set(EXPECTED_IFC_CLASSES)
            and all(t in old_rows and t in task_map for t in TASKS),
            "Pre-frozen 3 P0 task identifiers missing")
    for tid in TASKS:
        t=task_map[tid]
        o=old_rows[tid]
        require(t["original_ifc_sha256"]==o["original_public_IFC_sha256"]
                and t["public_question_sha256"]==o["public_question_sha256"]
                and t["crud"]==o["original_crud"]=="create"
                and o["next_engineering_priority_tier"]==
                    "P0_LIVE_XML_SOURCE_SCHEMA_REJECTED"
                and o["original_ifc_schema"]==EXPECTED_IFC_CLASSES[tid][0],
                "Previously frozen original CREATE source/question/schema drift: "+tid)
        actual_profile=SOURCE_PROFILES.get(t["original_ifc_sha256"])
        require(actual_profile is not None and actual_profile[0]==tid
                and actual_profile[1]==EXPECTED_IFC_CLASSES[tid][0],
                "Exact original native IFC source SHA not allowlisted")
    return task_map,old_rows


def illustrative_legacy_xml(original_xml:bytes,task_id:str)->bytes:
    """One complete source-document addition, *not* a task answer."""
    root=etree.fromstring(original_xml)
    levels=root.findall("./"+Q+"Levels/"+Q+"Level")
    ground=next((level for level in levels
                 if abs(float(level.get("placementZ")))<1e-8),None)
    require(ground is not None,
            "Original native Legacy XML has no zero-placed source Storey")
    elems=root.find(Q+"Elements")
    require(elems is not None,"Complete XML source Elements missing")
    if task_id=="geometry_test_03":
        # Geometric example from the existing public-only v0.8 fixture;
        # not a private GT or task-score-driven choice.
        hosts=[e for e in elems if e.tag==Q+"Wall"
               and e.get("ifcGuid")==V08_ILLUSTRATIVE_NORTH_WALL]
        require(len(hosts)==1,
                "Actual source-projected host Wall class/identity changed")
        etree.SubElement(elems,Q+"Opening",{
            "id":"v038_illustrative_opening","host":hosts[0].get("id"),
            "offset":"2.75","sill":"0","width":"1","height":"2.1"})
        etree.SubElement(elems,Q+"Door",{
            "id":"v038_illustrative_door",
            "opening":"v038_illustrative_opening",
            "width":"1","height":"2.1"})
    elif task_id=="geometry_test_04":
        etree.SubElement(elems,Q+"Space",{
            "id":"v038_illustrative_space","level":ground.get("id"),
            "x":"1","y":"1","z":"0","width":"2","depth":"2","height":"2"})
    elif task_id=="geometry_test_05":
        # Deliberately 3m, NOT the original task's requested 5m.
        etree.SubElement(elems,Q+"Wall",{
            "id":"v038_illustrative_wall","level":ground.get("id"),
            "x1":"0","y1":"0","z1":"0",
            "x2":"3","y2":"0","z2":"0",
            "height":"3","thickness":"0.2"})
    else:
        raise V038EvidenceDrift("Unexpected opt-in legacy task ID")
    changed=etree.tostring(root,encoding="utf8")
    require(changed!=original_xml
            and not any(x.tag in ("Create","Update","Delete","Move","Set")
                        for x in root.iter()),
            "Legacy XML must be full declarative Building state, not commands")
    return changed


def one_actual_tool_session(
        task:dict,existing:dict,source:Path,scratch:Path)->dict:
    tid=task["test_id"]
    original_hash=file_hash(source)
    require(original_hash==task["original_ifc_sha256"]
            and not source.is_symlink() and source.is_file()
            and not scratch.exists(),
            "Actual immutable original legacy source or fresh session path invalid")
    native=ifcopenshell.open(str(source))
    schema,created=EXPECTED_IFC_CLASSES[tid]
    require(native.schema==schema
            and abs(ifcopenshell.util.unit.calculate_unit_scale(native)-.001)<1e-12,
            "Original legacy native schema or millimetres changed")

    # Prove the frozen default remains UNSUPPORTED, with a separate session.
    try:
        XmlSourceEditSession(source,scratch/"default_no_optin")
    except UnsupportedArm as exc:
        require(str(exc)=="XML source compiler only accepts IFC4X3",
                "Original live default legacy rejection unexpectedly changed")
    else:
        raise V038EvidenceDrift("Legacy original unexpectedly admitted in old default host")
    require(file_hash(source)==original_hash,
            "Default unsupported source session changed source IFC")

    actual=XmlSourceEditSession(
        source,scratch/"experimental_optin",experimental_original_legacy_v08=True)
    require(actual.legacy_original_task_id==tid
            and actual.original_native_schema==schema
            and actual.output_ifc is None and actual.submissions==0
            and set(x["name"] for x in actual.tools)==
                {"read_building_xml","submit_building_xml"},
            "Real current model-facing legacy session contract changed")
    read=actual.call("read_building_xml",{})
    require(read.get("status")=="ok"
            and read["xml"]==actual.current_xml.decode("utf8")
            and read["native_candidate_available"] is False,
            "Model-facing XML read tool not returning complete real source state")
    before=actual.current_xml
    parse_v8(before,source_sha256=file_hash(actual.normalized),
             native_schema=schema)
    created_xml=illustrative_legacy_xml(before,tid)
    submit=actual.call("submit_building_xml",{
        "xml_text":created_xml.decode("utf8")})
    require(submit.get("status")=="ok"
            and submit.get("native_ifc_committed") is True
            and submit.get("compile_status","").startswith(
                "COMMITTED_SOURCE_SCHEMA_PRESERVED_")
            and actual.output_ifc is not None
            and actual.output_ifc.is_file()
            and actual.submissions==1
            and actual.current_xml==created_xml,
            "Real model-facing illustrative native legacy CREATE not committed")
    oracle=verify_native_original_restored(
        source,actual.output_ifc,task_id=tid,expected_schema=schema)
    require(file_hash(source)==original_hash,
            "Actual original native input mutated during XML tool calls")
    reread=actual.call("read_building_xml",{})
    require(reread["xml"]==created_xml.decode("utf8")
            and reread["native_candidate_available"] is True,
            "Committed real model-facing source state not reflected in read tool")
    return {
        "task_id":tid,
        "public_original_ifc_sha256":original_hash,
        "public_original_question_sha256":task["public_question_sha256"],
        "original_native_schema":schema,
        "original_source_length_unit_to_m":.001,
        "frozen_previous_v037_blocker":
            existing["next_engineering_priority_tier"],
        "default_model_host_original_schema_admitted":False,
        "optin_model_host_source_admitted":True,
        "optin_model_host_exact_original_pinned_source_only":True,
        "model_visible_XML_schema":"legacy-0.8",
        "model_visible_complete_XML_source_sha256":sha256(before).hexdigest(),
        "model_visible_XML_source_byte_length":len(before),
        "model_visible_XML_opaque_partial_view_not_entire_IFC":True,
        "LLM_tool_names":["read_building_xml","submit_building_xml"],
        "illustrative_new_declarative_nodes":
            {"geometry_test_03":["Opening","Door"],
             "geometry_test_04":["Space"],
             "geometry_test_05":["Wall"]}[tid],
        "illustrative_new_xml_sha256":sha256(created_xml).hexdigest(),
        "illustrative_benchmark_task_answer":False,
        "real_model_facing_native_write_committed":True,
        "real_original_native_result_sha256":file_hash(actual.output_ifc),
        "real_compiler_status":submit["compile_status"],
        "native_source_restored_oracle":oracle,
        "original_author_scorer_invoked":False,
        "agent_or_paid_model_invoked":False,
        "input_native_source_unchanged":True,
        "actual_matched_LLM_trial_eligible_for_causal_claim":False,
    }


def audit(root:Path,author:Path,data:Path)->dict:
    root,author,data=Path(root),Path(author),Path(data)
    public,rows=original_inputs(root,author,data)
    results=[]
    with TemporaryDirectory(prefix="bmb-v038-original-legacy-optin-host-") as t:
        temp=Path(t)
        for i,tid in enumerate(TASKS):
            task=public[tid]
            relative=Path(task["original_source_ifc_relpath"])
            source=data/"ifc"/relative
            require(not relative.is_absolute()
                    and source.resolve().is_relative_to((data/"ifc").resolve())
                    and file_hash(source)==task["original_ifc_sha256"],
                    "Source file path traversal or actual source digest changed")
            results.append(one_actual_tool_session(
                task,rows[tid],source,temp/f"case_{i:02d}"))
    require([x["task_id"] for x in results]==list(TASKS)
            and all(x["input_native_source_unchanged"] for x in results)
            and all(x["real_model_facing_native_write_committed"] for x in results)
            and _head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "All three opt-in original source IFC native CREATE proofs failed integrity")
    return {
        "status":"V038_ORIGINAL_P0_THREE_LEGACY_XML_MODEL_HOST_OPT_IN_CREATE_PROVEN",
        "issue":ISSUE,
        "stacked_parent_v037_head":
            "030b45716d48d9f4fbc093709b0d0c973e1b13b3",
        "original_author_git_sha":AUTHOR_SHA,
        "original_public_data_git_sha":DATA_SHA,
        "frozen_prior_v008_native_controls_sha256":LEGACY_REPORT[1],
        "frozen_prior_v037_ITT_and_P0_gates_sha256":PARENT_REPORT[1],
        "default_existing_IFC4X3_model_host_changed":False,
        "original_45_ITT_denominator":45,
        "original_15_CREATE_denominator":15,
        "five_old_original_CREATE_developer_semantic_pairs":5,
        "ten_original_CREATE_still_without_task_specific_native_pair":10,
        "prior_v037_P0_actual_schema_rejected_count":3,
        "v038_P0_explicit_optin_real_XML_source_admitted_count":3,
        "v038_P0_explicit_optin_real_native_IFC_write_count":3,
        "v038_default_no_optin_original_schema_admitted_count":0,
        "task_specific_original_author_results_obtained_in_v038":0,
        "actual_original_model_scored_LLM_trials":0,
        "new_paid_provider_requests":0,
        "Docker_or_isolated_Python_LLM_trials":0,
        "original45_entire_source_visible_information_parity_proven":0,
        "original45_full_approved_native_edit_capability_parity_proven":0,
        "full_original_STEP_byte_or_entity_preservation_proven":False,
        "P1_P2_P3_other_remaining_CREATE_gates_resolved":False,
        "causal_XML_vs_imperative_model_claim_supported":False,
        "scope":"EXPLICIT_RESEARCH_OPT_IN_ONLY_EXACT_THREE_PUBLIC_IFCS_NO_LLM",
        "rows":results,
    }


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--author",type=Path,required=True)
    parser.add_argument("--data",type=Path,required=True)
    parser.add_argument("--write",type=Path)
    args=parser.parse_args()
    report=audit(args.root,args.author,args.data)
    raw=(json.dumps(report,sort_keys=True,indent=2)+"\n").encode("utf8")
    if args.write:
        args.write.parent.mkdir(parents=True,exist_ok=True)
        with args.write.open("xb") as f:
            f.write(raw)
        print("WRITTEN",args.write,sha256(raw).hexdigest())
    else:
        print(json.dumps({
            "status":report["status"],
            "p0_optin_admitted":
                report["v038_P0_explicit_optin_real_XML_source_admitted_count"],
            "p0_actual_native_writes":
                report["v038_P0_explicit_optin_real_native_IFC_write_count"],
            "real_LLM_trials":report["actual_original_model_scored_LLM_trials"],
        },sort_keys=True))


if __name__=="__main__":
    main()
