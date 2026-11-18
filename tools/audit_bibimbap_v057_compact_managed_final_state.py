"""v0.57 offline complete ManagedElements final-state evidence.

Actual source-original native IFCs, separately compiled through v0.55
FULL state and new D_MANAGED_FINAL_STATE; all original author test code
called only from this trusted evaluator-only audit, NEVER from model tools.
This is not a model-generated result, not official published-paper grading,
not an experiment on the 41 other original edit tasks and not a license.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import importlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from lxml import etree

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v052_live_docker_controls import (
    developer_python_source,
)
from tools.audit_bibimbap_v055_live_schema_transactions import (
    developer_XML_final,row_registry,
)
from tools.bibimbap_v055_transactional_primary_DI_sessions import (
    SchemaGuardedDirectStateSession055,
    SchemaGuardedLivePythonSession055,
)
from tools.bibimbap_v057_managed_final_state_session import (
    ManagedFinalStateDirectSession057,
)
from tools.bibimbap_v057_provenance import (
    NO_PROVIDER_TRIAL_STATUS,assert_original_source_rights_unchanged_v057,
)
from tools.bibimbap_v048_independent_original4_semantic_oracle import (
    evaluate_original_semantic048,
)
from src.runtime.experimental_v57_compact_managed_state import (
    project_managed_final_state_v057,
    compact_from_complete_declarative_state_v057,
    restore_complete_declarative_state_v057,
)
from tools.audit_bibimbap_v056_full_xml_feasibility import TASKS

ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v057_compact_managed_final_state_original4_20261118.json"
PARENT_SHA="09b2435f402fd333cdb048681313b05a180fe751bc641b9a8a774b77d7620849"
RIGHTS_SHA="6b8e983a80a88a06f8de9ebefaeee3c52a71231583bbfeb164c05e0c1b17137c"
V055_SHA="e651a612e718281fa1ecb2741cf29216796be5df6f6d00439894e0b591b0437c"
V053_AUTHOR_SHA="40742725e59f7b0909f2d1ff061a7d68bcfcf1f35da829c3d15d0624928366e4"
PARENT_HEAD="f9f18eb83d300e5ae2b0f0112f3de8b500fc992a"
AUTHOR_COMMIT="667004e16bd38fd7d538bcee56191465429fd975"


def need(condition:bool,msg:str)->None:
    if not condition:
        raise AssertionError(msg)


def _sha(raw:bytes)->str:
    return sha256(raw).hexdigest()


def _canonical(data:dict)->bytes:
    return (json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)
            +"\n").encode("utf8")


def _original_author_scorer_evaluator_only(
    task:str,source_ifc:Path,candidate_ifc:Path
)->dict:
    # Distinct evaluator-side namespace only; user/provider tools have
    # no import from here and this result is never given as tool feedback.
    sys.path.insert(0,str(AUTHOR))
    try:
        module=importlib.import_module(f"data.tests.{task}")
        need(Path(module.__file__).resolve()==
             (AUTHOR/"data"/"tests"/f"{task}.py").resolve(),
             "Original author module was shadowed")
        raw=module.execute_test(
            str(source_ifc),str(candidate_ifc),None)
        need(isinstance(raw,dict) and len(raw)>0
             and all(type(v) is bool for v in raw.values()),
             "Original author test did not return Boolean result")
        return {
            "author_repository_boolean_metric_values":dict(sorted(raw.items())),
            "author_repository_mean_boolean_score":round(
                sum(raw.values())/len(raw),6),
            "published_paper_official_score":None,
        }
    finally:
        sys.path.remove(str(AUTHOR))


def build_report()->dict:
    hashes={
        "prior_v056_full_XML_native":(
          ROOT/"reports"/"bibimbap_v056_original4_full_XML_response_feasibility_20261118.json",PARENT_SHA),
        "prior_v056_source_rights":(
          ROOT/"reports"/"bibimbap_v056_offline_trial_rights_and_output_budget_gate_20261118.json",RIGHTS_SHA),
        "prior_v055_pinned_Docker":(
          ROOT/"reports"/"bibimbap_v055_primary_DI_schema_guard_live_transactions_20261118.json",V055_SHA),
        "prior_v053_author_repo":(
          ROOT/"reports"/"bibimbap_v053_author_origin_four_original_score_20261118.json",V053_AUTHOR_SHA),
    }
    for label,(path,digest) in hashes.items():
        need(file_hash(path)==digest,label+" immutable report changed")
    need(NO_PROVIDER_TRIAL_STATUS=="BLOCKED_NO_MODEL_PROVIDER_TRIAL"
         and assert_original_source_rights_unchanged_v057()["status"]==
             NO_PROVIDER_TRIAL_STATUS,
         "Original rights and paid model launch gate changed")
    rows=row_registry()
    need(len(rows)==45 and len({
        x["original_ifc_sha256"] for x in rows.values()})==31
        and Counter(x["crud"] for x in rows.values())==
            {"create":15,"update":15,"delete":15},
        "Original 45/31 public edit denominator changed")
    metadata={}
    controls=[]
    with TemporaryDirectory(prefix="v057-original-IFC-compact-no-provider-") as tmp:
        scratch=Path(tmp)
        for ix,task in enumerate(TASKS):
            row=rows[task]
            source=DATA/"ifc"/row["original_source_ifc_relpath"]
            source_sha=row["original_ifc_sha256"]
            need(file_hash(source)==source_sha,
                 "Original BIBIMBAP source IFC changed")
            baseline=project_managed_final_state_v057(
                source,source_sha=source_sha)
            d_src=SchemaGuardedDirectStateSession055(
                source,scratch/f"D_source_{ix}")
            c_src=ManagedFinalStateDirectSession057(
                source,scratch/f"C_source_{ix}")
            i_src=SchemaGuardedLivePythonSession055(
                source,scratch/f"I_source_{ix}")
            D=d_src.call("read_building_xml",{})
            C=c_src.call("read_building_xml",{})
            I=i_src.call("read_building_xml",{})
            need(D["status"]==C["status"]==I["status"]=="ok"
                 and D["xml"]==C["xml"]==I["xml"]
                 and D["current_xml_sha256"]==
                     C["current_xml_sha256"],
                 "New D variant changed model-visible input XML information")
            d_schema=_canonical({"tools":d_src.tools})
            i_schema=_canonical({"tools":i_src.tools})
            c_schema=_canonical({"tools":c_src.tools})
            need(c_src.tools[0]==d_src.tools[0]
                 and [x["name"] for x in c_src.tools]==[
                     "read_building_xml","submit_managed_final_state"]
                 and c_src.tools[1]!=d_src.tools[1],
                 "Explicitly new D variant must declare changed tool schema")
            metadata[task]={
                "original_public_IFC_SHA256":source_sha,
                "original_public_question_SHA256":row["public_question_sha256"],
                "original_D_I_compact_initial_source_xml_byte_equal":True,
                "original_model_source_XML_UTF8_bytes":len(D["xml"].encode()),
                "original_model_source_XML_SHA256":_sha(D["xml"].encode()),
                "original_managed_complete_state_UTF8_bytes":len(baseline),
                "original_compact_state_SHA256":_sha(baseline),
                "complete_managed_original_roster_count":
                    len(etree.fromstring(baseline)),
                "v055_D_full_tool_schema_JSON_bytes":len(d_schema),
                "v055_I_native_tool_schema_JSON_bytes":len(i_schema),
                "v057_NEW_managed_D_tool_schema_JSON_bytes":len(c_schema),
                "tool_schema_changed_NOT_causal_parity":True,
                "model_provider_billed_input_tokens":None,
                "model_provider_billed_output_tokens":None,
            }
            for positive in (True,False):
                fixture="positive" if positive else "negative"
                full=developer_XML_final(
                    row,source,positive=positive)
                full_bytes=full.encode("utf8")
                compact=compact_from_complete_declarative_state_v057(
                    source,full_bytes,source_sha=source_sha)
                restored=restore_complete_declarative_state_v057(
                    source,compact,source_sha=source_sha)
                need(restored==full_bytes,
                     "Source-anchored compact complete state must restore exact full bytes")
                full_session=SchemaGuardedDirectStateSession055(
                    source,scratch/f"full_{ix}_{fixture}")
                compact_session=ManagedFinalStateDirectSession057(
                    source,scratch/f"managed_{ix}_{fixture}")
                full_result=full_session.call(
                    "submit_building_xml",{"xml_text":full})
                compact_result=compact_session.call(
                    "submit_managed_final_state",
                    {"xml_text":compact.decode("utf8")})
                need(full_result["status"]==compact_result["status"]=="ok"
                     and full_result["native_ifc_sha256"]==
                         compact_result["native_ifc_sha256"]
                     and full_session.current_xml==
                         compact_session.current_xml==full_bytes
                     and compact_session.calls_used==1
                     and compact_result[
                         "independent_original_schema_delta_oracle"]=="PASS"
                     and compact_result["introduced_schema_error_count"]==0
                     and compact_result["original_author_benchmark_score"] is None,
                     "Real native IFC new compact vs original full-state mismatch")
                physically=evaluate_original_semantic048(
                    source,compact_session.output_ifc,
                    original_sha=source_sha,task_id=task,
                    public_question=row["public_question"])
                need(physically[
                    "candidatePassesIndependentResearchPhysicalPredicate"]==positive,
                    "Original research physical predicate unexpected")
                grade_full=_original_author_scorer_evaluator_only(
                    task,source,full_session.output_ifc)
                grade_compact=_original_author_scorer_evaluator_only(
                    task,source,compact_session.output_ifc)
                need(grade_full==grade_compact,
                     "Original author grader disagreed between IFC-identical edits")
                i_python=developer_python_source(
                    task,row["public_question"],positive=positive)
                controls.append({
                    "original_task_id":task,
                    "fixture":fixture+"_DEVELOPER_ONLY",
                    "actual_LLM_generated":False,
                    "new_D_variant":"D_MANAGED_FINAL_STATE",
                    "full_final_XML_UTF8_bytes":len(full_bytes),
                    "compact_complete_final_XML_UTF8_bytes":len(compact),
                    "I_native_developer_Python_UTF8_bytes":len(i_python.encode()),
                    "D_full_to_compact_output_byte_ratio":round(
                        len(full_bytes)/len(compact),5),
                    "compact_to_I_python_byte_ratio":round(
                        len(compact)/len(i_python.encode()),5),
                    "all_original_managed_objects_explicitly_declared":True,
                    "compact_state_SHA256":_sha(compact),
                    "restored_full_state_SHA256":_sha(restored),
                    "whole_D_IFC_SHA256":full_result["native_ifc_sha256"],
                    "compact_D_IFC_SHA256":compact_result["native_ifc_sha256"],
                    "physical_source_research_predicate":positive,
                    "new_ifc_schema_findings":0,
                    "author_repository_evaluator_only":grade_compact,
                    "actual_published_paper_official_score":None,
                    "model_provider_billed_tokens":None,
                })
                need(file_hash(source)==source_sha,
                     "Original input IFC modified by controlled native editing")
    need(len(controls)==8 and len(metadata)==4,
         "Compact original-source developer-control trial count changed")
    need(all(x["whole_D_IFC_SHA256"]==
             x["compact_D_IFC_SHA256"] for x in controls),
         "Final native files differ")
    return {
        "status":"V057_COMPACT_DECLARATIVE_FINAL_STATE_NATIVE_FIDELITY_PASS",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/229",
        "frozen_parent_v056_head":PARENT_HEAD,
        "primary_new_arm_identity":"D_MANAGED_FINAL_STATE",
        "prior_arm_identities_unchanged":[
            "D_COMPLETE_XML","D_COMPLETE_XML_STREAMED","I_NATIVE"],
        "new_arm_is_NOT_same_representation_as_prior_full_XML":True,
        "semantic_state_all_managed_original_records_explicit":True,
        "original_source_read_identical_in_D_and_I_and_new_variant":True,
        "original_public_45_edit_task_population":45,
        "original_distinct_IFC_sources":31,
        "exploratory_source_native_engineered_tasks":list(TASKS),
        "other_original_41_tasks_NOT_attempted":41,
        "source_code_and_original_IFC_and_prior_reports_immutable":True,
        "actual_native_original_IFC_one_shot_D_controls":8,
        "actual_native_original_IFC_managed_D_controls":8,
        "actual_author_repository_evaluator_scores_verified_8_pairs":True,
        "original_author_score_never_returned_in_model_tool":True,
        "original_author_repository_metrics_are_not_paper_official":True,
        "actual_original_paper_official_score":None,
        "actual_LLM_generated_trial_count":0,
        "paid_model_calls":0,
        "model_token_parity_or_accuracy_inference_not_proven":True,
        "provider_model_snapshot":None,
        "provider_actual_billed_prompt_completion_tokens":None,
        "approved_USD_budget":None,
        "provider_data_transfer_or_dataset_individual_asset_rights_verified":False,
        "dataset_card_declared_cc_by_4_0_not_blanket_legal_approval":True,
        "original_model_source_anchors":metadata,
        "developer_only_complete_final_state_controls":controls,
        "frozen_parent_reports_sha256":{
            k:digest for k,(_path,digest) in hashes.items()
        },
    }


def main()->int:
    cli=argparse.ArgumentParser(description=__doc__)
    group=cli.add_mutually_exclusive_group(required=True)
    group.add_argument("--write",action="store_true")
    group.add_argument("--check",action="store_true")
    options=cli.parse_args()
    data=_canonical(build_report())
    if options.write:
        with REPORT.open("xb") as f:
            f.write(data)
    else:
        need(REPORT.is_file() and REPORT.read_bytes()==data,
             "Source-original compact/native author-score replay differs")
    print("V057_COMPACT_STATE_NATIVE=PASS REAL_ORIGINAL_IFC_PAIRS=8/8 "
          "AUTHOR_EVALUATOR_PAIRS=8/8 LLM=0 BILLABLE=0 SHA256="+_sha(data))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
