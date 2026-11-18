"""v0.55 REAL pinned-Docker I-native + direct-state D transactional admission audit.

All native edits are independently developer-authored using public original
question/source only. No LLM or provider calls; this is NOT the 45-task
benchmark, not the original author grader, and not a D-vs-I causal outcome.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import (
    DockerIFCExecutor,PINNED_DOCKER_IMAGE,file_hash,
)
from src.runtime.experimental_v45_original_native_mutations import (
    project_original_native_mutations_v045,
)
from src.runtime.experimental_v50_original_declarative_state import (
    project_original_declarative_state_v050,
)
from tools.audit_bibimbap_v048_original4_semantic_controls import (
    positive_developer_source_edit,
)
from tools.audit_bibimbap_v045_original4_native_mutations import (
    make_illustrative_plan,
)
from tools.audit_bibimbap_v050_declarative_state import (
    developer_control_to_declarative_state,
)
from tools.bibimbap_v052_live_docker_controls import (
    TASKS,developer_python_source,deliberately_invalid_python,
    question_named_slab_guid,
)
from tools.bibimbap_v055_transactional_primary_DI_sessions import (
    SchemaGuardedDirectStateSession055,
    SchemaGuardedLivePythonSession055,
)
from tools.bibimbap_v055_production_schema_gate import (
    NativeSourceSchema055Error,production_native_schema_delta_v055,
)
from tools.bibimbap_v048_independent_original4_semantic_oracle import (
    evaluate_original_semantic048,
)
from tools.bibimbap_v052_live_original_native_python_session import (
    live_pinned_local_runtime_admission_v052,
)


ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v055_primary_DI_schema_guard_live_transactions_20261118.json"
PARENT_V054_SCHEMA_SHA="27d2ef5c6d24a99303975d32e3c1622f2c241b519d554bb8fe2eb17f50c17442"
PARENT_V054_RIGHTS_SHA="4eb66777ffeb0f38cb91e0ef1d75431f0473a11c44bd2cefd8a6f22244ff99a5"
PINNED_PARENT="6a6e2a7c361934021177dfde6269af8e89aee609"


def need(ok:bool,message:str)->None:
    if not ok:
        raise AssertionError(message)


def row_registry()->dict:
    rows=public_45(AUTHOR,DATA)
    need(len(rows)==45 and Counter(x["crud"] for x in rows)==
         {"create":15,"update":15,"delete":15} and
         len({x["original_ifc_sha256"] for x in rows})==31,
         "Original benchmark population changed")
    return {x["test_id"]:x for x in rows}


def developer_XML_final(row:dict,source:Path,*,positive:bool)->str:
    source_sha=row["original_ifc_sha256"]
    original_state=project_original_declarative_state_v050(
        source,source_sha=source_sha).xml
    typed_internal=project_original_native_mutations_v045(
        source,source_sha=source_sha).xml
    if positive:
        developer_only_plan=positive_developer_source_edit(
            typed_internal,source,row["test_id"],row["public_question"])
    else:
        developer_only_plan=make_illustrative_plan(
            typed_internal,row["test_id"],source)
    state=developer_control_to_declarative_state(
        original_state,developer_only_plan)
    return state.decode("utf8")


def raw_public_source_column_delete(row:dict)->str:
    """Transform independent PUBLIC-SOURCE-DERIVED code, not author GUIDs."""
    valid=developer_python_source(row["test_id"],
                                  row["public_question"],positive=True)
    old='api.run("root.remove_product",ifc,product=ifc.by_guid(guid))'
    need(valid.count(old)==1,"Original developer fixture delete semantics changed")
    return valid.replace(old,"ifc.remove(ifc.by_guid(guid))")


def raw_last_surviving_column_delete(row:dict,*,safe:bool)->str:
    """Derive remaining column from original public question plus live IFC.

    After a safe first edit removes four unrelated columns, exactly one
    remains unrelated to original named lower slab. Never insert target GUID.
    """
    slab=question_named_slab_guid(row["public_question"])
    edit=('api.run("root.remove_product",ifc,product=remaining[0])'
          if safe else 'ifc.remove(remaining[0])')
    return (
        "slab=ifc.by_guid("+repr(slab)+")\n"
        "assert slab is not None and slab.is_a('IfcSlab')\n"
        "containment={}\n"
        "for rel in ifc.by_type('IfcRelContainedInSpatialStructure'):\n"
        "    for entity in rel.RelatedElements:\n"
        "        if entity.is_a('IfcColumn') or entity.is_a('IfcSlab'):\n"
        "            containment[entity.GlobalId]=rel.RelatingStructure.GlobalId\n"
        "remaining=[c for c in ifc.by_type('IfcColumn') if "
        "containment.get(c.GlobalId)!=containment[slab.GlobalId]]\n"
        "assert len(remaining)==1\n"
        +edit+"\n"
        "import os\n"
        "result={'actual_docker_last_column_edit':True, 'linux_uid':os.getuid(), 'ifc_schema':ifc.schema}\n"
        "commit()\n"
    )


def worker_result(session:SchemaGuardedLivePythonSession055)->dict:
    dirs=sorted(session.folder.glob("call_*"))
    need(bool(dirs),"Actual worker never generated a call directory")
    p=dirs[-1]/"execution_result.json"
    need(p.is_file(),"Attested Docker worker result not found")
    result=json.loads(p.read_text(encoding="utf8"))
    need(result.get("backend")=="linux_docker_sandbox",
         "Actual Docker worker was not attested")
    return {
        "backend":result["backend"],
        "status":result.get("status"),
        "committed":result.get("committed"),
    }


def valid_commit_result(result:dict,*,I:bool)->None:
    need(result.get("status")=="ok"
         and result.get("native_ifc_committed") is True
         and result.get("independent_original_schema_delta_oracle")=="PASS"
         and result.get("introduced_schema_error_count")==0
         and result.get("original_author_benchmark_score") is None,
         "Actual versioned native IFC transaction not admitted correctly")
    if I:
        need(result.get("python_execution_attested") is True
             and result.get("offline_test_double_not_real_python") is False
             and result.get("actual_linux_sandbox_backend")==
                    "linux_docker_sandbox"
             and result.get("local_pinned_image_sha256")==PINNED_DOCKER_IMAGE
             and isinstance(result.get("result"),dict)
             and result["result"].get("linux_uid")==65534,
             "Real source-native I arm did not run in correct pinned Linux sandbox")


def build_report()->dict:
    need(file_hash(ROOT/"reports"/
        "bibimbap_v054_delete_source_schema_policy_20261118.json")
        ==PARENT_V054_SCHEMA_SHA,"Frozen v0.54 schema report changed")
    need(file_hash(ROOT/"reports"/
        "bibimbap_v054_offline_paired_token_and_source_rights_20261118.json")
        ==PARENT_V054_RIGHTS_SHA,"Frozen v0.54 rights report changed")
    admission=live_pinned_local_runtime_admission_v052()
    need(admission.get("status")=="RUNTIME_ADMITTED"
         and admission["pinned_worker_image_id"]==PINNED_DOCKER_IMAGE,
         "No live EXACT pinned local Linux Docker runtime")
    tasks=row_registry()
    observations={}
    paired=[]
    with TemporaryDirectory(prefix="v055-genuine-DI-schema-transaction-") as scratch:
        base=Path(scratch)
        for idx,tid in enumerate(TASKS):
            row=tasks[tid]
            source=DATA/"ifc"/row["original_source_ifc_relpath"]
            sha=row["original_ifc_sha256"]
            need(file_hash(source)==sha,"Original IFC task source hash changed")
            d_for_parity=SchemaGuardedDirectStateSession055(
                source,base/f"source_D_{idx}")
            i_for_parity=SchemaGuardedLivePythonSession055(
                source,base/f"source_I_{idx}")
            a=d_for_parity.call("read_building_xml",{})
            b=i_for_parity.call("read_building_xml",{})
            need(a["status"]==b["status"]=="ok"
                 and a["xml"]==b["xml"]
                 and d_for_parity.tools[0]["name"]==
                     i_for_parity.tools[0]["name"]=="read_building_xml"
                 and [x["name"] for x in d_for_parity.tools]==
                     ["read_building_xml","submit_building_xml"]
                 and [x["name"] for x in i_for_parity.tools]==
                     ["read_building_xml","execute_ifc_code"],
                 "Primary genuine model-facing source/tool parity changed")
            observations[tid]={
                "original_public_IFC_SHA256":sha,
                "public_question_SHA256":row["public_question_sha256"],
                "initial_D_I_source_XML_byte_identical":True,
                "initial_source_XML_SHA256":sha256(
                    a["xml"].encode("utf8")).hexdigest(),
                "each_arm_total_model_tool_calls_budget":25,
            }
            for positive in (True,False):
                control="positive" if positive else "negative"
                d=SchemaGuardedDirectStateSession055(
                    source,base/f"D_{idx}_{control}")
                state=developer_XML_final(row,source,positive=positive)
                d_response=d.call("submit_building_xml",{"xml_text":state})
                valid_commit_result(d_response,I=False)
                i=SchemaGuardedLivePythonSession055(
                    source,base/f"I_{idx}_{control}")
                code=developer_python_source(
                    tid,row["public_question"],positive=positive)
                i_response=i.call("execute_ifc_code",{"code":code})
                valid_commit_result(i_response,I=True)
                evidence=worker_result(i)
                need(evidence["status"]=="ok"
                     and evidence["committed"] is True,
                     "Actual Docker backend did not commit developer edit")
                for arm,session,response in (
                    ("D_STATE",d,d_response),
                    ("I_NATIVE_DOCKER",i,i_response),
                ):
                    actual=production_native_schema_delta_v055(
                        source,session.output_ifc,source_sha=sha)
                    need(actual["status"]=="PASS_NO_NEW_SCHEMA_FINDINGS"
                         and actual["introduced_schema_error_count"]==0,
                         "Accepted model session somehow has new source schema issues")
                    semantic=evaluate_original_semantic048(
                        source,session.output_ifc,original_sha=sha,
                        task_id=tid,public_question=row["public_question"])
                    need(semantic[
                        "candidatePassesIndependentResearchPhysicalPredicate"]==positive,
                         "Independent physical task predicate disagreed with control")
                    need(file_hash(source)==sha,
                         "Actual original input IFC changed")
                    paired.append({
                        "task_id":tid,
                        "arm":arm,
                        "control":control+"_DEVELOPER_PUBLIC_SOURCE",
                        "model_generated":False,
                        "real_IFC4X3_SHA256":response["native_ifc_sha256"],
                        "physical_research_predicate":positive,
                        "v055_original_source_native_scope_and_schema":"PASS",
                        "source_inherited_schema_errors":
                            actual["source_schema_error_count"],
                        "newly_introduced_schema_errors":0,
                        "actual_Python_run_in_pinned_Linux_Docker":
                            arm=="I_NATIVE_DOCKER",
                        "original_author_score":None,
                    })
        # Forged 1.0 author score case: true Docker worker executes source-
        # derived raw file.remove with NO grader private target IDs.
        deletion=tasks["topological_test_17"]
        source=DATA/"ifc"/deletion["original_source_ifc_relpath"]
        source_sha=deletion["original_ifc_sha256"]
        raw=raw_public_source_column_delete(deletion)
        rejected=SchemaGuardedLivePythonSession055(
            source,base/"I_raw_initial_delete")
        prior_source=file_hash(source)
        attempt=rejected.call("execute_ifc_code",{"code":raw})
        worker=worker_result(rejected)
        need(attempt["status"]=="error"
             and attempt["error_type"]=="NativeSchemaOrScopeRejected"
             and attempt["native_ifc_committed"] is False
             and rejected.output_ifc is None
             and worker["status"]=="ok" and worker["committed"] is True
             and file_hash(source)==prior_source
             and not (rejected.folder/"call_001"/"current.ifc").exists(),
             "Real Docker raw five-Column schema-invalid edit was promoted")
        # Independent active worker output proves exactly +25 schema errors,
        # not solely a frozen earlier Windows raw candidate observation.
        raw_run=base/"real_raw_worker"
        raw_run.mkdir(exist_ok=False)
        shutil.copyfile(source,raw_run/"current.ifc")
        direct_worker=DockerIFCExecutor().run(raw_run,raw)
        need(direct_worker["backend"]=="linux_docker_sandbox"
             and direct_worker["status"]=="ok"
             and direct_worker["committed"] is True,
             "No actual pinned Docker worker executed raw-delete control")
        delta=production_native_schema_delta_v055(
            source,raw_run/"current.ifc",source_sha=source_sha)
        need(delta["introduced_schema_error_count"]==25
             and delta["source_schema_error_count"]==1
             and delta["candidate_schema_error_count"]==26,
             "Actual live container raw-delete IFC schema error pattern changed")
        # Rollback on latest valid native IFC and then successful recovery.
        sequential=SchemaGuardedLivePythonSession055(
            source,base/"I_rollback_recovery")
        good=sequential.call("execute_ifc_code",{
            "code":developer_python_source(
                "topological_test_17",deletion["public_question"],
                positive=False)})
        valid_commit_result(good,I=True)
        last_good_sha=file_hash(sequential.output_ifc)
        bad=sequential.call("execute_ifc_code",{
            "code":raw_last_surviving_column_delete(deletion,safe=False)})
        bad_worker=worker_result(sequential)
        need(bad["status"]=="error"
             and bad["error_type"]=="NativeSchemaOrScopeRejected"
             and not bad["native_ifc_committed"]
             and bad_worker["status"]=="ok"
             and bad_worker["committed"] is True
             and last_good_sha==file_hash(sequential.output_ifc)
             and not (sequential.folder/"call_002"/"current.ifc").exists(),
             "Last valid native IFC changed after invalid real Docker commit")
        recovery=sequential.call("execute_ifc_code",{
            "code":raw_last_surviving_column_delete(deletion,safe=True)})
        valid_commit_result(recovery,I=True)
        need(file_hash(sequential.output_ifc)!=last_good_sha
             and file_hash(source)==source_sha,
             "Cannot recover after rejected Docker edit")
        # D-state: ensure malformed model XML cannot overwrite a valid IFC.
        slab=tasks["geometry_test_14"]
        slab_source=DATA/"ifc"/slab["original_source_ifc_relpath"]
        d=SchemaGuardedDirectStateSession055(
            slab_source,base/"D_valid_then_invalid")
        good_D=d.call("submit_building_xml",{
            "xml_text":developer_XML_final(slab,slab_source,positive=True)})
        valid_commit_result(good_D,I=False)
        state_sha=sha256(d.current_xml).hexdigest()
        ifc_sha=file_hash(d.output_ifc)
        invalid_D=d.call("submit_building_xml",{
            "xml_text":"<not-a-declarative-state/>"})
        need(invalid_D["status"]=="error"
             and invalid_D["native_ifc_committed"] is False
             and invalid_D["last_valid_ifc_preserved"] is True
             and sha256(d.current_xml).hexdigest()==state_sha
             and file_hash(d.output_ifc)==ifc_sha,
             "D-state malformed XML overwrote previous valid native state")
        # New validator rejection guard must run BEFORE D commit. Force
        # local test-only error, never modify actual input or native file.
        probe=SchemaGuardedDirectStateSession055(
            slab_source,base/"D_injected_guard_rejection")
        with patch(
            "tools.bibimbap_v055_transactional_primary_DI_sessions.validate_production_native_commit_v055",
            side_effect=NativeSourceSchema055Error("NativeSchemaDeltaRejected")):
            forced=probe.call("submit_building_xml",{
                "xml_text":developer_XML_final(slab,slab_source,positive=True)})
        need(forced["status"]=="error"
             and forced["error_type"]=="NativeSchemaOrScopeRejected"
             and probe.output_ifc is None
             and not (probe.folder/"attempt_001"/
                       "candidate_original_native_mm.ifc").exists(),
             "Model-facing direct XML state bypassed new schema guard")
        # Source/engine startup is a strict fail-closed non-execution path.
        refused=SchemaGuardedLivePythonSession055(
            slab_source,base/"I_blocked_no_execution")
        with patch(
            "tools.bibimbap_v055_transactional_primary_DI_sessions.live_pinned_local_runtime_admission_v052",
            return_value={"status":"BLOCKED_RUNTIME",
                          "reason":"SOURCE_PINNED_LOCAL_DOCKER_UNAVAILABLE"}):
            gate=refused.call("execute_ifc_code",{"code":"commit()"})
        need(gate["error_type"]=="BLOCKED_RUNTIME"
             and refused.output_ifc is None
             and list(refused.folder.iterdir())==[],
             "Genuine I-native created candidate before sandbox admission")
        # Failure-after-commit is a REAL Linux worker failure.
        failure=SchemaGuardedLivePythonSession055(
            slab_source,base/"I_error_after_commit")
        error=failure.call("execute_ifc_code",{
            "code":deliberately_invalid_python(
                "geometry_test_14",slab["public_question"],
                "error_after_commit")})
        worker_fail=worker_result(failure)
        need(error["status"]=="error"
             and error["native_ifc_committed"] is False
             and failure.output_ifc is None
             and worker_fail["status"]=="error"
             and worker_fail["committed"] is True,
             "Actual worker failure after commit was not rejected")
        need(file_hash(source)==source_sha
             and file_hash(slab_source)==slab["original_ifc_sha256"],
             "Original public source modified during adversarial controls")
        safeguards={
            "raw_5_columns_real_Docker_worker_status":worker["status"],
            "raw_5_columns_worker_committed":worker["committed"],
            "raw_5_columns_host_committed":False,
            "raw_5_columns_schema_new_findings_from_separate_real_Docker_output":
                delta["introduced_schema_error_count"],
            "original_source_schema_preexisting_findings":
                delta["source_schema_error_count"],
            "new_schema_guard_response_type":attempt["error_type"],
            "last_good_4_column_Docker_IFC_SHA256":last_good_sha,
            "invalid_5th_column_real_worker_executed_and_committed":
                bad_worker["status"]=="ok" and bad_worker["committed"] is True,
            "invalid_5th_column_previous_last_good_preserved":True,
            "subsequent_safe_5th_column_native_recovery":True,
            "D_state_after_valid_malformed_XML_rolled_back":True,
            "D_state_validator_enforced_before_commit":True,
            "I_native_missing_Docker_engine_refuses_before_execution":True,
            "I_native_real_worker_exception_after_commit_rejected":True,
            "worker_exact_pinned_image_sha256":PINNED_DOCKER_IMAGE,
        }
    need(len(paired)==16 and len(observations)==4,
         "Missing exact paired developer original-four scope")
    return {
        "status":"V055_REAL_PRIMARY_D_I_SCHEMA_GUARDED_TRANSACTIONS_PASS",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/225",
        "exact_parent_v054_commit":PINNED_PARENT,
        "original_45_public_tasks":45,
        "original_distinct_IFC_sources":31,
        "original_four_engineered_nonrandom_exploratory_tasks":list(TASKS),
        "other_41_original_tasks_NOT_attempted":41,
        "actual_paired_model_generated_Python_XML_trials":0,
        "paid_provider_model_calls":0,
        "original_author_paper_score":None,
        "license_and_provider_transfer_rights_approved":False,
        "provider_billed_input_output_token_parity_proven":False,
        "original_source_XML_info_parity":observations,
        "developer_control_native_candidates_D_I":len(paired),
        "accepted_native_D_controls":8,
        "accepted_true_Docker_I_controls":8,
        "all_accepted_candidates_no_new_IFC4X3_schema_errors":True,
        "no_initial_source_IFC_mutated":True,
        "actual_pinned_Docker_runtime_readonly_probe":admission,
        "real_Docker_adversarial_commit_and_atomic_rollback":safeguards,
        "new_validator_is_not_full_IFC_EXPRESS_WHERE_semantic_completeness":True,
        "old_v054_frozen_schema_report_SHA256":PARENT_V054_SCHEMA_SHA,
        "old_v054_frozen_rights_report_SHA256":PARENT_V054_RIGHTS_SHA,
        "native_developer_case_records":paired,
    }


def canonical(data:dict)->bytes:
    return (json.dumps(data,sort_keys=True,indent=2,ensure_ascii=False)
            +"\n").encode("utf8")


def main()->int:
    cli=argparse.ArgumentParser(description=__doc__)
    g=cli.add_mutually_exclusive_group(required=True)
    g.add_argument("--write",action="store_true")
    g.add_argument("--check",action="store_true")
    opts=cli.parse_args()
    report=canonical(build_report())
    if opts.write:
        with REPORT.open("xb") as fd:
            fd.write(report)
    else:
        need(REPORT.is_file() and REPORT.read_bytes()==report,
             "Actual original source/native D/I live Docker replay changed")
    print("V055_PRIMARY_D_I_SCHEMA_COMMIT=PASS "
          "DEVELOPER_REAL_IFC=16/16 REAL_PINNED_I=8/8 "
          "NEW_SCHEMA_FINDINGS=0 RAW_DOCKER_25=REJECT "
          "ROLLBACK=PASS MODEL_TRIALS=0 SHA256="
          +sha256(report).hexdigest())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
