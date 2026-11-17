"""v0.47 exact original 4-source XML vs restricted typed Python paired audit.

The exact original source IFC, public question and task IDs are unchanged. Each
arm is a real model-facing session independently reading the same immutable
v0.45 source XML, with a frozen 25-call limit, EXACT same four task-conditioned
native edits, trusted v0.45 compiler and independent v0.45 original-IFC oracle.

Four DEVELOPER illustrative edits are intentionally NOT solutions to any
original benchmark question. NO LLM/provider, scorer/hidden GT, unrestricted
Python/IfcOpenShell eval, external grader, Docker or benchmark model trials.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lxml import etree

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.audit_bibimbap_v045_original4_native_mutations import (
    make_illustrative_plan)
from tools.bibimbap_v047_restricted_python_native_session import (
    MatchedOriginalXmlSession047,
    RestrictedOriginalPythonSession047,
    typed_python_to_exact_original_xml,
    parse_single_restricted_python_call,
    FUNCTION_BY_TASK,
)
from tools.bibimbap_v045_independent_native_mutation_oracle import (
    verify_original_native_mutation_v045)
from src.runtime.experimental_v45_original_native_mutations import (
    TASK_OPERATIONS,parse_original_native_edit_plan_v045)
from src.runtime.experimental_v44_original_native_step_readonly import (
    PINS,project_native_readonly_source_v044)

ROOT=Path(__file__).resolve().parents[1]
ISSUE="https://github.com/pikaybh/bim-markup-bench/issues/209"
FROZEN_V046_SHA="beab50998c1f2f984342cf784fe910adc384752a16b8f0eed40623421c38509f"
FROZEN_V045_SHA="7d7518f6c65242f7f00066beeb0229fbb6e42e44d5e841243666ac375105c4b3"
PARENT_HEAD="e9697c07f005517545b6b3cdb45a066528cd9c6d"
TASKS=("geometry_test_14","geometry_test_15","topological_test_11",
       "topological_test_17")


def need(cond,msg):
    if not cond:
        raise AssertionError(msg)


def illustrative_python_from_original_xml(tid:str,completed:bytes)->str:
    """Serialize developer NON-SOLUTION edit to exact bounded Python call."""
    root=etree.fromstring(completed)
    need(root[-1].tag.endswith("NativeEditPlan") and len(root[-1])==1,
         "Developer illustrative original native edit plan changed")
    op=root[-1][0]
    need(op.tag.endswith(TASK_OPERATIONS[tid]),
         "Illustrative original public edit kind mismatched")
    if tid=="geometry_test_14":
        # Illustration lengthens one side by just 0.4m; not a square.
        a,b=float(op.get("newXDimM")),float(op.get("newYDimM"))
        need(abs(a-b)>1e-6,
             "Illustration must not solve original square-request task")
        return (f"set_slab_rectangle_dimensions(ifc_guid={op.get('ifcGuid')!r},"
                f"new_x_dim_m={a!r},new_y_dim_m={b!r})")
    if tid=="geometry_test_15":
        return (f"move_column_placement(ifc_guid={op.get('ifcGuid')!r},"
                f"new_world_origin_x_m={float(op.get('newWorldOriginXM'))!r},"
                f"new_world_origin_y_m={float(op.get('newWorldOriginYM'))!r})")
    if tid=="topological_test_11":
        return f"set_all_mapped_column_depth(new_depth_m={float(op.get('newDepthM'))!r})"
    if tid=="topological_test_17":
        return "delete_columns_by_guid(ifc_guids="+repr(
            [v.get("ifcGuid") for v in op])+")"
    raise AssertionError("Not original four native typed benchmark source")


def audit_paired_original_task(src:Path,task:dict,folder:Path)->dict:
    tid=task["test_id"]
    source_sha=task["original_ifc_sha256"]
    need(file_hash(src)==source_sha and tid in TASKS,
         "Original public native source SHA or pilot task changed")
    xml_arm=MatchedOriginalXmlSession047(src,folder/"xml")
    py_arm=RestrictedOriginalPythonSession047(src,folder/"python")
    need(xml_arm.task_id==py_arm.task_id==tid
         and xml_arm.call_budget==py_arm.call_budget==25
         and len(xml_arm.tools)==len(py_arm.tools)==2
         and xml_arm.original_xml==py_arm.source_xml,
         "Pilot source / task / tool count / frozen call budget mismatch")
    xml_response=xml_arm.call("read_building_xml",{})
    py_response=py_arm.call("read_source_python",{})
    need(xml_response["status"]=="ok"
         and py_response["status"]=="ok"
         and xml_response["xml"].encode("utf8")==xml_arm.original_xml
         and py_response["original_source_xml_sha256"]==
             xml_response["current_xml_sha256"],
         "Actual model source read calls have different original evidence SHA")
    rendered=py_response["source_python"]
    head,separator,representation=rendered.partition(" = ")
    need(head=="ORIGINAL_SOURCE_XML" and separator==" = "
         and ast.literal_eval(representation.strip()).encode("utf8")==
         xml_response["xml"].encode("utf8"),
         "Python literal original source not losslessly equivalent to XML arm")
    v44=project_native_readonly_source_v044(
        src,original_native_sha256=source_sha)
    xml_original=etree.fromstring(xml_arm.original_xml)
    v44_original=etree.fromstring(v44.xml)
    need(etree.tostring(xml_original[0],method="c14n")==
         etree.tostring(v44_original[0],method="c14n"),
         "Cross-arm original immutable native/mm STEP/relations/geometry changed")
    # One developer non-solution edit, with model-facing original task controls.
    xml_submission=make_illustrative_plan(xml_arm.original_xml,tid,src)
    py_code=illustrative_python_from_original_xml(tid,xml_submission)
    need(parse_single_restricted_python_call(py_code,task_id=tid),
         "Python command not one exact source-task bounded AST call")
    py_submission=typed_python_to_exact_original_xml(
        src,source_sha,py_code)
    left=parse_original_native_edit_plan_v045(
        src,xml_submission,source_sha=source_sha)
    right=parse_original_native_edit_plan_v045(
        src,py_submission,source_sha=source_sha)
    need(left==right and left.task_id==tid
         and left.kind==TASK_OPERATIONS[tid],
         "Source-native operation, target GUIDs, numeric arguments differ")
    xml_edited=xml_arm.call("submit_building_xml",{
        "xml_text":xml_submission.decode("utf8")})
    py_edited=py_arm.call("submit_native_python",{"python_code":py_code})
    need(xml_edited["status"]==py_edited["status"]=="ok"
         and xml_edited["native_ifc_committed"]
         and py_edited["native_ifc_committed"]
         and xml_edited["independent_native_oracle_status"]==
              py_edited["independent_original_native_oracle_status"]==
              "V045_INDEPENDENT_ORIGINAL_IFC_NATIVE_MUTATION_ORACLE_PASS",
         "Two actual original task native model tool edit writes/oracles failed")
    need(xml_arm.output_ifc.is_file() and py_arm.output_ifc.is_file()
         and xml_edited["native_ifc_sha256"]==
             py_edited["native_ifc_sha256"]==
             file_hash(xml_arm.output_ifc)==file_hash(py_arm.output_ifc),
         "Actual native source physical IFC candidates differ in BYTES")
    xml_oracle=verify_original_native_mutation_v045(
        src,xml_arm.output_ifc,submitted_xml=xml_submission,
        source_sha=source_sha,task_id=tid)
    py_oracle=verify_original_native_mutation_v045(
        src,py_arm.output_ifc,submitted_xml=py_submission,
        source_sha=source_sha,task_id=tid)
    need(xml_oracle["status"]==py_oracle["status"]
         and xml_oracle["exact_target_original_physical_products_actually_changed"]==
             py_oracle["exact_target_original_physical_products_actually_changed"]
         and xml_oracle["non_target_original_physical_products_unchanged"]==
             py_oracle["non_target_original_physical_products_unchanged"],
         "External independent original native physical pair oracle mismatch")
    original_candidate_sha=file_hash(xml_arm.output_ifc)
    # Second deliberately invalid action, same two tools and last-valid rollback.
    bad_xml=xml_submission.decode("utf8").replace(
        "NativeEditPlan","ForgedEditPlan",1)
    rejected_xml=xml_arm.call("submit_building_xml",{"xml_text":bad_xml})
    rejected_py=py_arm.call("submit_native_python",{
        "python_code":"import os\nos.system('do_not_execute')"})
    need(rejected_xml["status"]==rejected_py["status"]=="error"
         and not rejected_xml["native_ifc_committed"]
         and not rejected_py["native_ifc_committed"]
         and rejected_xml["last_valid_xml_preserved"]
         and rejected_py["last_valid_IFC_and_source_preserved"]
         and file_hash(xml_arm.output_ifc)==file_hash(py_arm.output_ifc)==
             original_candidate_sha
         and xml_arm.current_xml==xml_submission
         and py_arm.current_xml==py_submission
         and py_arm.current_python_code==py_code
         and file_hash(src)==source_sha,
         "Original source, previous valid native IFC or source modified on error")
    need(xml_arm.calls==py_arm.calls==3
         and xml_arm.base.submissions==py_arm.submissions==2,
         "Unequal actual model tool call counts in paired session")
    return {
        "original_public_task_id":tid,
        "original_public_question_sha256":task["public_question_sha256"],
        "original_public_source_ifc_sha256":source_sha,
        "original_task_CRUD":task["crud"],
        "original_source_native_schema":"IFC4X3",
        "original_source_native_length_unit":"millimetres",
        "same_original_source_XML_bytes_shown_to_both_models":len(xml_arm.original_xml),
        "source_XML_read_SHA_identical_both_arms":sha256(xml_arm.original_xml).hexdigest(),
        "python_literal_source_view_bytes":len(rendered.encode("utf8")),
        "source_python_literal_roundtrip_exact_original_XML":True,
        "original_native_immutable_STEP_and_source_metadata_both_arms_equal":True,
        "same_original_public_question_on_both_arms":True,
        "same_whitelisted_native_task_edit_kind":left.kind,
        "same_original_native_target_GUIDs":list(left.target_guids),
        "same_original_native_numerical_arguments":list(left.args),
        "python_AST_disallowed_all_arbitrary_execution":True,
        "actual_model_tool_read_calls_per_arm":1,
        "actual_model_tool_native_success_calls_per_arm":1,
        "actual_model_tool_rejected_calls_per_arm":1,
        "total_model_tool_call_budget_per_arm":25,
        "actual_native_IFC_edited_and_written_XML":True,
        "actual_native_IFC_edited_and_written_Python":True,
        "actual_two_independently_written_IFC_bytes_SHA256_IDENTICAL":True,
        "original_native_IFC_both_arm_sha256":original_candidate_sha,
        "both_arms_independent_native_oracle_PASS":True,
        "native_physical_targets_changed":xml_oracle[
            "exact_target_original_physical_products_actually_changed"],
        "original_non_target_physical_objects_preserved":xml_oracle[
            "non_target_original_physical_products_unchanged"],
        "native_IFC_valid_candidate_preserved_after_both_rejected_resubmissions":True,
        "original_public_IFC_source_byte_hash_unchanged":True,
        "developer_generated_illustrative_candidate_NOT_original_task_solution":True,
        "original_task_semantic_success_or_score_proven":False,
        "original_author_evaluator_invoked":False,
        "paid_LLM_model_trial":False,
    }


def audit(author:Path,data:Path,*,progress:bool=False)->dict:
    author=Path(author);data=Path(data)
    need(file_hash(ROOT/"reports"/
         "bibimbap_v046_original27_all_native_IFC_paged_source_catalog_20261117.json")==
         FROZEN_V046_SHA
         and file_hash(ROOT/"reports"/
         "bibimbap_v045_original4_native_IFC_typed_writers_20261117.json")==
         FROZEN_V045_SHA,
         "Prior v0.45/v0.46 original frozen reports drift")
    originals=public_45(author,data)
    byid={x["test_id"]:x for x in originals}
    need(len(originals)==45
         and len({x["original_ifc_sha256"] for x in originals})==31
         and Counter(x["crud"] for x in originals)==
             {"create":15,"update":15,"delete":15},
         "Original publicly published benchmark population changed")
    original_pins={pin[0]:(sha,pin[2]) for sha,pin in PINS.items()}
    need(set(original_pins)==set(TASKS),
         "Original fixed four source tasks not same 45 benchmark tasks")
    for tid,(sha,question_sha) in original_pins.items():
        need(byid[tid]["original_ifc_sha256"]==sha
             and byid[tid]["public_question_sha256"]==question_sha
             and byid[tid]["crud"] in ("update","delete"),
             "Original publication public task question or source SHA changed")
    rows=[]
    with TemporaryDirectory(prefix="bmb-v047-original4-restricted-matched-") as tmp:
        for i,tid in enumerate(TASKS):
            item=byid[tid]
            source=data/"ifc"/item["original_source_ifc_relpath"]
            row=audit_paired_original_task(source,item,Path(tmp)/str(i))
            rows.append(row)
            if progress:
                print("V047_RESTRICTED_SOURCE_AND_NATIVE_WRITER_PAIRED_PASS",
                      tid,"OP",row["same_whitelisted_native_task_edit_kind"],
                      "IFC_BYTES_IDENTICAL",
                      row["actual_two_independently_written_IFC_bytes_SHA256_IDENTICAL"],
                      "QUESTION_SCORED",False,flush=True)
    need(len(rows)==4
         and {r["original_public_task_id"] for r in rows}==set(TASKS)
         and all(r["actual_two_independently_written_IFC_bytes_SHA256_IDENTICAL"]
                 and r["both_arms_independent_native_oracle_PASS"] for r in rows),
         "Not four exact source-locked native matched pairs")
    need(file_hash(ROOT/"reports"/
         "bibimbap_v046_original27_all_native_IFC_paged_source_catalog_20261117.json")==
         FROZEN_V046_SHA,
         "Prior original v0.46 published audit modified by experiment")
    return {
        "status":"V047_FOUR_ORIGINAL_SOURCE_MATCHED_RESTRICTED_XML_PYTHON_NATIVE_IFC_BYTE_EQUAL_PASS",
        "issue":ISSUE,
        "exact_frozen_v046_parent_SHA":PARENT_HEAD,
        "frozen_v046_report_SHA256":FROZEN_V046_SHA,
        "frozen_v045_report_SHA256":FROZEN_V045_SHA,
        "original_public_ITT_count":45,
        "original_public_CREATE_count":15,
        "original_public_UPDATE_count":15,
        "original_public_DELETE_count":15,
        "original_public_unique_IFC_source_SHA_count":31,
        "selected_original_task_count":4,
        "other_original_tasks_NOT_in_matched_restricted_pilot":41,
        "selected_original_UPDATE_count":3,
        "selected_original_DELETE_count":1,
        "selected_original_CREATE_count":0,
        "identical_original_source_information_and_immutable_native_STEP_both_arms":True,
        "identical_native_task_edit_authority_four_sources":True,
        "same_trusted_IFC4X3_mm_native_IFC_writer_and_independent_oracle":True,
        "two_actual_independent_original_native_IFC_candidate_files_per_task":True,
        "native_IFC_files_byte_identical_for_each_original_four_paired_task":True,
        "actual_matched_source_and_native_output_pilot_pairs":4,
        "total_actual_tool_calls_XML":12,
        "total_actual_tool_calls_Python":12,
        "max_tool_call_budget_each_arm_each_task":25,
        "python_arm_restricted_AST_only_no_arbitrary_Python_execution":True,
        "no_original_question_correct_answer_hardcoded":True,
        "new_actual_original_full_task_semantic_solutions_proven":0,
        "real_original_task_author_evaluator_invocations":0,
        "paid_provider_calls":0,
        "Docker_executions":0,
        "real_paid_XML_vs_Python_model_trials":0,
        "default_original_benchmark_Python_IfcOpenShell_unrestricted_tool_equivalent":False,
        "original_45_equal_native_write_authority_proven":False,
        "same_models_context_tokens_or_tool_ergonomics_proven":False,
        "original_CREATE_developer_task_specific_D0_I0_pairs":5,
        "original_author_question_IFC_datasets_unchanged":True,
        "research_main_and_Xim_untouched":True,
        "next_priority":"v0.48 prospective fixed-subset original semantic evaluators and restricted-vs-unrestricted arm separation; token budget preregistration, fair LLM trials only then",
        "original_four_paired_rows":rows,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--author",type=Path,required=True)
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--write",type=Path)
    p.add_argument("--progress",action="store_true")
    args=p.parse_args()
    report=audit(args.author,args.data,progress=args.progress)
    raw=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
    if args.write:
        args.write.parent.mkdir(parents=True,exist_ok=True)
        with args.write.open("xb") as out:out.write(raw)
        print("V047_FROZEN_MATCHED_RESTRICTED_ORIGINAL4_REPORT",
              args.write,sha256(raw).hexdigest(),flush=True)
    else:
        print(json.dumps({
            "status":report["status"],
            "identical_source_AND_IFC_byte_pairs":4,
            "original_solved_tasks":0,
            "real_LLM_trials":0,
        },sort_keys=True))


if __name__=="__main__":
    main()
