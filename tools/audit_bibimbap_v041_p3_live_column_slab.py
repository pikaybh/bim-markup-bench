"""v0.41 original-public P3 real whole-XML model host Column/Slab writer audit.

Offline, source-only, real native IFC read/write/reopen. Not original-task
answer, original-author grading, hidden GT or real paired LLM trial.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from tools.audit_bibimbap_author import _head,AUTHOR_SHA,DATA_SHA
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import XmlSourceEditSession,file_hash
from tools.bibimbap_v041_p3_native_oracle import verify_p3_original_native_add

ROOT=Path(__file__).resolve().parents[1]
Q="{urn:bim-markup-bench:toy:v0}"
ISSUE="https://github.com/pikaybh/bim-markup-bench/issues/197"
PINS={
  "geometry_test_02":{
    "original_sha":"58833e0bdf80e2207b8c221fc8195e5411f9f94e0d7f1cb39633b3c447eb4767",
    "question_sha":"bd7465f6f246b8662c62cb2830292ace4cee09e3a5f53a34d79bf9cc5a27d9e2",
    "created_kind":"Column","source_native_walls":4,"source_opaque_native_slabs":0,
    "source_native_roots":68,"source_native_products":8,
  },
  "topological_test_02":{
    "original_sha":"8f1d9e885603f8680cb79f2a373fa36b4ecd52634ac920f2ec53c60ac465ad72",
    "question_sha":"8d9053bf43826d2354f8053fb9e23b147c13e496c3cdb79b063443e237f297ff",
    "created_kind":"Column","source_native_walls":4,"source_opaque_native_slabs":2,
    "source_native_roots":89,"source_native_products":10,
  },
  "topological_test_04":{
    "original_sha":"29cd44b72639ba9573aa1698a4efab4adcfbc5461c19dd85259e6a9505d303e5",
    "question_sha":"c587dae1444490eb2be2e92ea2359039e5099b87690828dfd4cbe81c7cf46fba",
    "created_kind":"Slab","source_native_walls":7,"source_opaque_native_slabs":1,
    "source_native_roots":108,"source_native_products":12,
  },
}
TARGETS=tuple(PINS)
V037=("reports/bibimbap_v037_original10_create_live_source_and_writer_gates_20261117.json",
      "33d99e6fb624e6a5e89dc301791c269bd5ca7d2666d8618fc67379664938501f")
V040=("reports/bibimbap_v040_original_p2_room_native_mm_exact_20261117.json",
      "8f5a9d8df436e52139a09c6fd78a961d71684303eb8499d8d61513adca305f3e")


def require(ok,why):
    if not ok:raise ValueError(why)


def input_cohort(root:Path,author:Path,data:Path)->dict:
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "P3 pristine original author/data Git HEAD SHA changed")
    for path,pin in (V037,V040):
        previous=root/path
        require(previous.is_file() and file_hash(previous)==pin,
                "Previous frozen original benchmark report SHA changed: "+path)
    pop=public_45(author,data)
    require(len(pop)==45 and len({x["test_id"] for x in pop})==45
            and Counter(x["crud"] for x in pop)==
                {"create":15,"update":15,"delete":15},
            "Full original public benchmark 45 and 15/15/15 ITT population changed")
    indexed={t["test_id"]:t for t in pop}
    require(set(TARGETS)<=set(indexed),"P3 three target original public tasks missing")
    for taskid,pin in PINS.items():
        task=indexed[taskid]
        require(task["crud"]=="create"
                and task["public_question_sha256"]==pin["question_sha"]
                and task["original_ifc_sha256"]==pin["original_sha"]
                and task["xml_source_projection_previously_observed"]=="PROJECTABLE",
                "P3 original task question, source or public CREATE cohort pre-registration altered")
    return indexed


def illustrative_non_answer_xml(source_xml:bytes,*,kind:str)->bytes:
    original=etree.fromstring(source_xml)
    levels=original.findall("./"+Q+"Levels/"+Q+"Level")
    ground=next((x for x in levels
                 if abs(float(x.get("elevation")))<.00000001),None)
    require(ground is not None and ground.get("ifcGuid"),
            "No source native zero-elevation Storey in whole declarative XML")
    elements=original.find(Q+"Elements")
    require(elements is not None
            and not any(x.get("id")=="v041_illustrative_not_original_task_answer"
                        for x in elements),
            "P3 deterministic source append local ID collision")
    attrs={
        "id":"v041_illustrative_not_original_task_answer",
        "level":ground.get("id"),
        "x":"8","y":"0","z":"0",
    }
    attrs.update(
        {"width":"0.4","depth":"0.3","height":"2.5"}
        if kind=="Column" else
        {"width":"1.2","depth":"1.5","thickness":"0.2"})
    etree.SubElement(elements,Q+kind,attrs)
    return etree.tostring(original,encoding="utf8")


def inspect_one(task:dict,pin:dict,source:Path,folder:Path)->dict:
    taskid=task["test_id"]
    original_sha=file_hash(source)
    require(original_sha==pin["original_sha"]
            and source.is_file() and not source.is_symlink()
            and not folder.exists(),
            "P3 original public IFC source SHA / isolated session path not pinned")
    f=ifcopenshell.open(str(source))
    require(f.schema=="IFC4X3" and abs(
            ifcopenshell.util.unit.calculate_unit_scale(f)-.001)<1e-12
            and len(f.by_type("IfcRoot"))==pin["source_native_roots"]
            and len(f.by_type("IfcProduct"))==pin["source_native_products"]
            and len(f.by_type("IfcWall"))==pin["source_native_walls"]
            and len(f.by_type("IfcSlab"))==pin["source_opaque_native_slabs"],
            "P3 original public native source IFC4X3/mm inventory changed")
    source_slabs={x.GlobalId for x in f.by_type("IfcSlab")}
    default=XmlSourceEditSession(source,folder/"old_default")
    require(default.p3_original_task_id is None and default.output_ifc is None,
            "P3 opt-in unexpectedly enabled in default existing XML host")
    default_doc=etree.fromstring(default.current_xml)
    default_guids={x.get("ifcGuid") for x in default_doc.find(Q+"Elements")}
    require(len(default_doc.find(Q+"Elements"))==pin["source_native_walls"]
            and all(x.tag==Q+"Wall" for x in default_doc.find(Q+"Elements"))
            and not source_slabs & default_guids,
            "P3 default current model-facing XML existing Walls/opaque Slabs changed")

    session=XmlSourceEditSession(
        source,folder/"p3_explicit_optin",experimental_original_p3_v041=True)
    require(session.p3_original_task_id==taskid
            and session.room_original_task_id is None
            and session.complex_original_task_id is None
            and session.legacy_original_task_id is None
            and {x["name"] for x in session.tools}==
                {"read_building_xml","submit_building_xml"},
            "P3 actual model tools changed or research flags accidentally combined")
    read=session.call("read_building_xml",{})
    require(read["status"]=="ok"
            and read["native_candidate_available"] is False
            and read["xml"]==session.current_xml.decode("utf8"),
            "P3 real model read must expose full original source XML")
    original_xml=session.current_xml
    require(original_xml==default.current_xml,
            "P3 must not inflate original current XML source with task-answer hints")
    edited=illustrative_non_answer_xml(
        original_xml,kind=pin["created_kind"])
    result=session.call("submit_building_xml",{
        "xml_text":edited.decode("utf8")})
    require(result["status"]=="ok"
            and result.get("native_ifc_committed") is True
            and result.get("compile_status")==
                "COMMITTED_ORIGINAL_IFC4X3_P3_SINGLE_COLUMN_SLAB_NATIVE_XML_V041"
            and session.output_ifc is not None
            and session.output_ifc.is_file()
            and session.submissions==1
            and session.current_xml==edited,
            "P3 actual full-declarative XML Column/Slab writer did not produce native IFC")
    oracle=verify_p3_original_native_add(
        source,session.output_ifc,task_id=taskid,
        submitted_xml=edited)
    require(oracle["original_native_opaque_Slab_count_preserved"]==
                pin["source_opaque_native_slabs"]
            and oracle["all_original_opaque_native_Slab_physical_shapes_preserved"]==
                pin["source_opaque_native_slabs"],
            "P3 original source opaque IFC Slab physically lost")
    after=session.call("read_building_xml",{})
    require(after["status"]=="ok"
            and after["native_candidate_available"] is True
            and after["xml"]==edited.decode("utf8")
            and file_hash(source)==original_sha,
            "P3 successful model tool write/re-read or original immutable source changed")
    return {
        "task_id":taskid,
        "original_public_question":task["public_question"],
        "original_public_question_sha256":task["public_question_sha256"],
        "original_native_source_ifc_relpath":task["original_source_ifc_relpath"],
        "original_native_source_IFC_sha256":original_sha,
        "original_native_schema":"IFC4X3",
        "original_native_unit_to_m":.001,
        "new_declared_XML_element_kind":pin["created_kind"],
        "original_native_IfcWalls":pin["source_native_walls"],
        "original_native_IfcSlabs":pin["source_opaque_native_slabs"],
        "original_XML_original_Walls_visible":pin["source_native_walls"],
        "original_XML_original_Slabs_visible":0,
        "original_native_opaque_Slabs_omitted_from_model_view":
            pin["source_opaque_native_slabs"],
        "original_native_Storeys":2,
        "model_facing_tools":["read_building_xml","submit_building_xml"],
        "default_read_XML_sha256":sha256(default.current_xml).hexdigest(),
        "experimental_read_XML_sha256":sha256(original_xml).hexdigest(),
        "default_and_optin_model_visible_input_equal":True,
        "candidate_declarative_XML_sha256":sha256(edited).hexdigest(),
        "actual_illustrative_native_IFC_created":True,
        "submitted_new_geometry_is_original_task_answer":False,
        "source_native_IfcSpaceBoundary_invented":False,
        "independent_original_native_millimetre_IFC_oracle":oracle,
        "original_IFC_source_bytes_unchanged":True,
        "original_author_grader_invoked":False,
        "matched_LLMS_XML_Python_trials":0,
    }


def audit(root:Path,author:Path,data:Path)->dict:
    cohort=input_cohort(root,author,data)
    rows=[]
    with TemporaryDirectory(prefix="bmb-v041-three-original-native-creates-") as d:
        for index,tid in enumerate(TARGETS):
            task=cohort[tid]
            rel=Path(task["original_source_ifc_relpath"])
            source=data/"ifc"/rel
            require(not rel.is_absolute()
                    and source.resolve().is_relative_to(
                        (data/"ifc").resolve()),
                    "P3 original source relative path escaped public IFC directory")
            rows.append(inspect_one(
                task,PINS[tid],source,Path(d)/("case_"+str(index))))
    require(len(rows)==3 and all(row["original_IFC_source_bytes_unchanged"]
            for row in rows) and _head(author)==AUTHOR_SHA
            and _head(data)==DATA_SHA,
            "P3 original author source/data changed during actual IFC writer audit")
    return {
        "status":"V041_ORIGINAL_P3_THREE_REAL_XML_MODEL_FACING_COLUMN_SLAB_NATIVE_WRITERS_VERIFIED",
        "issue":ISSUE,
        "stacked_parent_v040_commit":"95371fd3c7b1d1cbbcfd09a77569c4e815a1c0bd",
        "original_author_git_sha":AUTHOR_SHA,
        "original_data_git_sha":DATA_SHA,
        "original_frozen_v037_report_sha256":V037[1],
        "original_frozen_v040_report_sha256":V040[1],
        "original45_public_ITT_denominator":45,
        "original15_CREATE_denominator":15,
        "previous_original_task_specific_developer_D0_I0_semantic_pairs":5,
        "original_CREATE_without_task_specific_D0_I0_semantic_pair":10,
        "v041_original_P3_model_facing_Column_creation_triggers":2,
        "v041_original_P3_model_facing_Slab_creation_triggers":1,
        "v041_original_public_P3_real_native_create_writers":3,
        "v041_previous_existing_opaque_IfcSlabs_preserved":3,
        "v041_previous_existing_opaque_IfcSlabs_now_visible_in_XML":0,
        "v041_original_P3_readable_source_information_parity_with_Python_arm":False,
        "v041_original_P3_full_native_mutation_parity_with_Python_arm":False,
        "v041_original_public_P3_author_task_solutions_confirmed":0,
        "actual_real_matched_LLM_XML_Python_trials":0,
        "complete_original45_matched_model_read_parity_proven":0,
        "complete_original45_matched_native_write_parity_proven":0,
        "original_author_evaluator_invocations":0,
        "Docker_executions":0,
        "new_paid_provider_requests":0,
        "research_main_modified":False,
        "Xim_product_repo_modified":False,
        "original_author_or_public_data_modified":False,
        "default_XSD_or_existing_default_host_behavior_changed":False,
        "full_original_IFC_STEP_byte_equivalence_proven":False,
        "causal_XML_vs_Python_LLM_effect_established":False,
        "next_priority":"P3 remaining original source facts, especially opaque existing Slabs, then full equal-read/equal-write D/I parity gates before real matched LLM runs",
        "rows":rows,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--author",type=Path,required=True)
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--write",type=Path)
    args=p.parse_args()
    result=audit(args.root,args.author,args.data)
    raw=(json.dumps(result,sort_keys=True,indent=2)+"\n").encode("utf8")
    if args.write:
        args.write.parent.mkdir(parents=True,exist_ok=True)
        with args.write.open("xb") as writer: writer.write(raw)
        print("V041_FROZEN_REPORT",args.write,"sha256",sha256(raw).hexdigest())
    else:
        print(json.dumps({
            "status":result["status"],
            "real_native_writers":result["v041_original_public_P3_real_native_create_writers"],
            "original_opaque_IfcSlabs_preserved":result["v041_previous_existing_opaque_IfcSlabs_preserved"],
            "actual_matched_LLM_trials":result["actual_real_matched_LLM_XML_Python_trials"],
        },sort_keys=True))


if __name__=="__main__":
    main()
