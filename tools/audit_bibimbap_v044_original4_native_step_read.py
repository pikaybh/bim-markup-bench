"""v0.44 original four UPDATE/DELETE IFC4X3 source STEP XML real-tool audit.

Not a benchmark score or task solution. Baselines are the v0.43 frozen
original 45/31 source parity report, not any imaginary new matched study.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lxml import etree

from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import XmlSourceEditSession,UnsupportedArm,file_hash
from tools.bibimbap_v044_independent_original_native_source_oracle import (
    validate_original_v044_native_model_read)
from src.runtime.experimental_v44_original_native_step_readonly import PINS

ROOT=Path(__file__).resolve().parents[1]
ISSUE="https://github.com/pikaybh/bim-markup-bench/issues/203"
PARENT_SHA="711bc5804406dbd99d4f358f8fa5882c15691197"
PREVIOUS=(
    "reports/bibimbap_v043_original45_native_XML_source_read_parity_20261117.json",
    "eb05633d152b1ff15e4fdd888bb62924b31b126f6cddd05fb23e54fce3ef8dbf"
)
QUESTION_CSV_SHA="21c07f08c923cdb748255d7960535bab05e2887e4d093d64f87f76ff6d6d100b"
SOURCE_NS="{urn:bim-markup-bench:toy:v0}"


def require(ok:bool,reason:str):
    if not ok: raise ValueError(reason)


def original_45(author:Path,data:Path)->dict:
    author,data=Path(author),Path(data)
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Original published 45 author/data Git HEAD changed")
    require(file_hash(ROOT/PREVIOUS[0])==PREVIOUS[1],
            "Frozen previous v0.43 source information parity report SHA changed")
    require(file_hash(data/"prompts/all_questions.csv")==QUESTION_CSV_SHA,
            "Original public question CSV SHA changed")
    cohort=public_45(author,data)
    require(len(cohort)==45 and len({x["test_id"] for x in cohort})==45
            and Counter(x["crud"] for x in cohort)==
                {"create":15,"update":15,"delete":15}
            and Counter(x["category"] for x in cohort)==
                {"basic":15,"geometry":15,"topological":15}
            and len({x["original_ifc_sha256"] for x in cohort})==31,
            "Original public full ITT 45 / 31 distinct source IFC counts changed")
    tasks={x["test_id"]:x for x in cohort}
    for sha,(task_id,crud,question_sha,entity_count,product_count) in PINS.items():
        t=tasks.get(task_id)
        require(t is not None and t["crud"]==crud
                and t["original_ifc_sha256"]==sha
                and t["public_question_sha256"]==question_sha,
                "v0.44 original public task/source/question exact SHA preregistered pin mismatch")
        p=Path(t["original_source_ifc_relpath"])
        source=(data/"ifc"/p)
        require(not p.is_absolute() and not source.is_symlink()
                and source.resolve().is_relative_to((data/"ifc").resolve())
                and file_hash(source)==sha,
                "Source original public IFC path escaped/symlinked/bytes changed")
    previous=json.loads((ROOT/PREVIOUS[0]).read_text(encoding="utf8"))
    require(previous["original_public_ITT_task_count"]==45
            and previous["original_source_IFC_unique_sha256_count"]==31
            and previous["original45_default_XML_model_read_status_counts"]==
                {"ACTUAL_MODEL_TOOL_XML_READ_OK":36,
                 "UNSUPPORTED_BACKEND_NOT_MODEL_FAILURE":9}
            and previous["original45_research_feature_flag_XML_read_status_counts"]==
                {"ACTUAL_MODEL_TOOL_XML_READ_OK":41,
                 "UNSUPPORTED_BACKEND_NOT_MODEL_FAILURE":4},
            "Baseline frozen original45 source status altered or not comparable")
    previous_task={t["original_public_task_id"]:t
                   for t in previous["original_45_task_rows"]}
    for key in PINS.values():
        tid=key[0]
        require(previous_task[tid]["best_research_model_read_status"]==
                "UNSUPPORTED_BACKEND_NOT_MODEL_FAILURE",
                "v0.44 target was not one of four previously blocked original source reads")
    return tasks


def audit_one(t:dict,source:Path,folder:Path)->dict:
    task_id=t["test_id"]
    original_sha=t["original_ifc_sha256"]
    require(file_hash(source)==original_sha,
            "Original IFC source changed before v0.44 trial")
    with TemporaryDirectory(prefix="bmb-v044-old-default-host-") as tmp:
        try:
            XmlSourceEditSession(source,Path(tmp)/"baseline")
        except UnsupportedArm as exc:
            require(type(exc).__name__=="UnsupportedArm",
                    "Default source refused for ungrounded reason")
            baseline="UNSUPPORTED_BACKEND_NOT_MODEL_FAILURE"
            baseline_error=str(exc)[:128]
        else:
            raise ValueError("Original baseline XML source unexpectedly became readable")
    s=XmlSourceEditSession(
        source,folder,experimental_original_native_readonly_v044=True)
    require(s.native_readonly_original_task_id==task_id
            and s.slab_original_task_id is None
            and s.p3_original_task_id is None
            and s.legacy_original_task_id is None
            and s.room_original_task_id is None
            and s.complex_original_task_id is None,
            "v0.44 original source opt-in unexpectedly combined editor modes")
    require({x["name"] for x in s.tools}==
            {"read_building_xml","submit_building_xml"},
            "Actual model-facing XML source tool names changed")
    require("UNSUPPORTED" in next(x for x in s.tools
            if x["name"]=="submit_building_xml")["description"],
            "Model was not told v0.44 source editing is unsupported")
    response=s.call("read_building_xml",{})
    require(response["status"]=="ok"
            and response["xml"]==s.original_xml.decode("utf8")
            and response["native_candidate_available"] is False,
            "Actual model read did not expose all original native-source XML bytes")
    actual=response["xml"].encode("utf8")
    oracle=validate_original_v044_native_model_read(
        source,actual,task_id=task_id)
    expected_sha=sha256(actual).hexdigest()
    require(oracle["actual_read_only_model_xml_sha256"]==expected_sha,
            "Independent native original source oracle differs from model returned bytes")
    xml_before=s.current_xml
    same=s.call("submit_building_xml",{"xml_text":response["xml"]})
    require(same["status"]=="error"
            and same["error_type"]=="UnsupportedArm"
            and same["error"]==
                "V044_READ_ONLY_ORIGINAL_NATIVE_SOURCE_UPDATE_DELETE_MUTATION_UNSUPPORTED"
            and same["native_ifc_committed"] is False
            and same["original_source_unchanged"] is True
            and same["last_valid_xml_preserved"] is True,
            "Even unchanged XML must fail closed as native mutation unsupported")
    fake=s.call("submit_building_xml",{
        "xml_text":response["xml"].replace("MILLIMETER_NATIVE","METERS_FAKE",1)})
    require(fake["status"]=="error"
            and fake["error_type"]=="UnsupportedArm"
            and fake["native_ifc_committed"] is False
            and fake["last_valid_xml_preserved"] is True
            and s.output_ifc is None and s.current_xml==xml_before
            and s.submissions==2
            and not list(folder.glob("attempt_*"))
            and file_hash(source)==original_sha,
            "V044 original source could be mutated or poisoned model submission was accepted")
    require(s.call("read_building_xml",{})["xml"]==response["xml"],
            "Read-only source XML changed after rejected submissions")
    return {
        "original_public_task_id":task_id,
        "original_public_task_CRUD":t["crud"],
        "original_public_question_sha256":t["public_question_sha256"],
        "original_public_source_ifc_relpath":t["original_source_ifc_relpath"],
        "original_public_source_ifc_sha256":original_sha,
        "previous_v043_default_model_read_status":baseline,
        "previous_v043_default_model_read_reason":baseline_error,
        "new_v044_actual_model_read_status":"ACTUAL_MODEL_TOOL_XML_READ_OK_READ_ONLY_NO_WRITE",
        "new_v044_actual_model_tool_names":["read_building_xml","submit_building_xml"],
        "new_v044_actual_model_submits_attempted":2,
        "new_v044_actual_model_submits_explicitly_refused":2,
        "new_v044_native_original_update_delete_writer_available":False,
        "new_v044_native_original_candidate_produced":False,
        "new_v044_original_source_bytes_unchanged":True,
        "new_v044_immutable_read_only_XML_and_safety_gate_passed":True,
        "new_v044_source_oracle":oracle,
        "original_author_score_proven":False,
        "original_task_success_proven":False,
        "actual_matched_LLM_trial":False,
    }


def audit(author:Path,data:Path,*,progress:bool=False)->dict:
    tasks=original_45(author,data)
    rows=[]
    with TemporaryDirectory(prefix="bmb-v044-original4-native-source-") as td:
        for index,profile in enumerate(sorted(PINS.values())):
            task_id=profile[0]
            t=tasks[task_id]
            source=data/"ifc"/t["original_source_ifc_relpath"]
            row=audit_one(t,source,Path(td)/str(index))
            rows.append(row)
            if progress:
                o=row["new_v044_source_oracle"]
                print("V044_ACTUAL_SOURCE_READ_AND_INDEPENDENT_ORACLE_PASS",
                      task_id,"STEP",o[
                          "source_original_native_STEP_DATA_entities_exactly_model_visible"],
                      "native relationships",o[
                          "source_native_IfcRelationship_GUIDs_and_exact_source_endpoints_visible"],
                      "new native IFC WRITE",o[
                          "original_IFC_native_update_delete_mutation_available"],
                      flush=True)
    require(len(rows)==4
            and {r["original_public_task_id"] for r in rows}==
                {profile[0] for profile in PINS.values()},
            "All four original source SHA-pinned IFC tasks must be independently audited")
    keys=(
        "source_original_native_STEP_DATA_entities_exactly_model_visible",
        "source_native_IfcProduct_GUIDs_with_exact_class_name_and_source_step_visible",
        "source_native_IfcRelationship_GUIDs_and_exact_source_endpoints_visible",
        "source_native_IfcPropertySet_names_Guids_properties_visible",
        "source_native_IfcMaterial_names_visible",
        "source_native_IfcLocalPlacement_matrices_visible",
        "source_native_original_physical_product_world_mesh_visible",
        "source_native_original_physical_world_mesh_unavailable_explicit",
        "source_original_world_mesh_ordered_vertices_visible",
        "source_original_world_mesh_ordered_triangles_visible",
        "actual_xml_source_bytes",
    )
    totals={k:sum(r["new_v044_source_oracle"][k] for r in rows) for k in keys}
    require(totals[
                "source_original_native_STEP_DATA_entities_exactly_model_visible"]==
                119+166+579+440
            and totals[
                "source_native_IfcRelationship_GUIDs_and_exact_source_endpoints_visible"]==
                21+29+73+69
            and totals["source_native_original_physical_product_world_mesh_visible"]==
                1+4+13+12
            and totals[
                "source_native_original_physical_world_mesh_unavailable_explicit"]==0,
            "Native four-source all DATA/rel/mesh exact inventory changed")
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA
            and file_hash(ROOT/PREVIOUS[0])==PREVIOUS[1],
            "Prior report/author-data drift after v0.44 audit")
    return {
        "status":"V044_ORIGINAL_4_BLOCKED_UPD_DEL_IFC4X3_ACTUAL_XML_READ_ONLY_STEP_ALL_ENTITIES_PASS",
        "pre_registered_issue":ISSUE,
        "parent_stacked_v043_exact_head":PARENT_SHA,
        "original_author_git_head":AUTHOR_SHA,
        "original_data_git_head":DATA_SHA,
        "original_public_questions_csv_sha256":QUESTION_CSV_SHA,
        "previous_v043_frozen_full45_parity_report_sha256":PREVIOUS[1],
        "original_full_public_ITT_task_count":45,
        "original_public_CREATE_count":15,
        "original_public_UPDATE_count":15,
        "original_public_DELETE_count":15,
        "original_distinct_IFC_source_files_count":31,
        "new_four_original_previously_unsupported_source_tasks_readable_readonly":4,
        "new_four_original_previously_unsupported_source_tasks_native_editable":0,
        "previous_v043_default_XML_read_45":36,
        "previous_v043_source_pinned_research_read_45":41,
        "new_best_available_research_source_read_45":45,
        "new_best_available_research_source_read_modes_are_separate_optins":True,
        "new_best_available_research_model_read_IS_default_provider_runner":False,
        "new_four_original_Python_vs_XML_source_STEP_DATA_entity_text_full_match":True,
        "new_four_native_source_IfcProduct_IfcRelationship_IfcPropertySet_IfcMaterial_IfcLocalPlacement_and_mesh_oracle_match":True,
        "new_four_actual_model_facing_native_mutation_attempts":8,
        "new_four_native_IFC_commits":0,
        "new_original_task_specific_D0_I0_CREATE_pairs":0,
        "prior_original_task_specific_developer_D0_I0_CREATE_pairs":5,
        "full_original45_equal_source_information_parity_proven":False,
        "full_original45_equal_native_edit_authority_proven":False,
        "equal_model_token_budget_or_python_api_ergonomics_proven":False,
        "original_task_solutions_or_native_author_scores_proven":0,
        "paid_model_calls":0,
        "Docker_executions":0,
        "original_author_evaluator_calls":0,
        "real_matched_LLM_XML_vs_Python_trials":0,
        "original_public_sources_or_evaluator_modified":False,
        "research_main_or_BIXML_Xim_modified":False,
        "next_priority":"v0.45 original 4 UPDATE/DELETE task-conditioned native mutation writer oracle + remaining original-source metadata parity for already readable 27 source IFCs; no LLM trial before equal information/edit authority",
        "totals_for_exact_four_unique_original_sources":totals,
        "rows":rows,
    }


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author",type=Path,required=True)
    parser.add_argument("--data",type=Path,required=True)
    parser.add_argument("--write",type=Path)
    parser.add_argument("--progress",action="store_true")
    args=parser.parse_args()
    out=audit(args.author,args.data,progress=args.progress)
    text=(json.dumps(out,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf8")
    if args.write:
        args.write.parent.mkdir(parents=True,exist_ok=True)
        with args.write.open("xb") as f:
            f.write(text)
        print("V044_FROZEN_NATIVE_STEP_ORIGINAL4_AUDIT",args.write,
              sha256(text).hexdigest(),flush=True)
    else:
        print(json.dumps({
            "status":out["status"],
            "actual_source_reads":out["new_best_available_research_source_read_45"],
            "native_writes":out["new_four_native_IFC_commits"],
            "original_matched_LLM_trials":out["real_matched_LLM_XML_vs_Python_trials"],
        },sort_keys=True))


if __name__=="__main__":
    main()
