"""v0.52 actual pinned Linux Docker Python IFC execution and security replay.

Unlike v0.51, every accepted case here is actually executed by the unchanged
attested Linux Docker Python worker, NOT by trusted Windows execution or an
offline copied-IFC double. All snippets are developer-only source-derived
controls; NO LLM/paid calls, scorer/hidden GT or original IFC mutation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import (
    PINNED_DOCKER_IMAGE, file_hash,
)
from tools.bibimbap_v052_live_original_native_python_session import (
    LiveOriginalNativePythonSession052,live_pinned_local_runtime_admission_v052,
)
from tools.bibimbap_v052_live_docker_controls import (
    TASKS,developer_python_source,deliberately_invalid_python,
)
from tools.bibimbap_v050_direct_original_state_session import (
    DirectOriginalStateSession050,
)
from tools.bibimbap_v048_independent_original4_semantic_oracle import (
    evaluate_original_semantic048,
)


ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v052_original4_live_docker_python_attestation_20261118.json"
PARENT_V051="4ad4a86c00c147523eb65d793cdcbd303a267acf19fb47d26106bb10a1be074d"
PARENT_V050="eb6bef852eabf12ed76b5c5df861a8e5a355a5142e5ad0d3732d646b25dfb28a"
SOURCE_FILES=(
    "tools/bibimbap_v052_live_docker_controls.py",
    "tools/bibimbap_v052_live_original_native_python_session.py",
)


def need(yes:bool,message:str)->None:
    if not yes:
        raise AssertionError(message)


def worker_witness(session:LiveOriginalNativePythonSession052)->dict:
    """Read only developer scratch, NOT model response or author private grader."""
    call_dirs=sorted(session.folder.glob("call_*"))
    need(call_dirs,"No actual sandbox call directory")
    response=call_dirs[-1]/"execution_result.json"
    need(response.is_file(),"No actual Docker worker execution result file")
    raw=json.loads(response.read_text(encoding="utf8"))
    need(raw.get("backend")=="linux_docker_sandbox",
         "Sandbox worker backend evidence missing")
    return {
        "status":raw.get("status"),
        "committed":raw.get("committed"),
        "backend":raw.get("backend"),
        "error_type":raw.get("error_type"),
    }


def build_report()->dict:
    need(file_hash(ROOT/"reports"/
        "bibimbap_v051_original4_executed_python_runtime_readiness_20261118.json")
        ==PARENT_V051,"Prior frozen v0.51 report changed")
    need(file_hash(ROOT/"reports"/
        "bibimbap_v050_original4_declarative_state_diff_20261117.json")
        ==PARENT_V050,"Prior frozen v0.50 report changed")
    registry={r["test_id"]:r for r in public_45(AUTHOR,DATA)}
    need(len(registry)==45 and
         len({r["original_ifc_sha256"] for r in registry.values()})==31
         and Counter(r["crud"] for r in registry.values())==
         {"create":15,"update":15,"delete":15},
         "Original published benchmark denominator changed")
    readiness=live_pinned_local_runtime_admission_v052()
    need(readiness["status"]=="RUNTIME_ADMITTED",
         "Actual pinned local Docker must be live before v0.52 evidence replay")
    docs={}
    records=[]
    with TemporaryDirectory(prefix="v052-real-pinned-docker-") as tmp:
        root=Path(tmp)
        for i,tid in enumerate(TASKS):
            r=registry[tid]
            path=DATA/"ifc"/r["original_source_ifc_relpath"]
            source_sha=r["original_ifc_sha256"]
            need(file_hash(path)==source_sha,"Original source changed")
            # Independently model-facing D/I tools must return same initial
            # source bytes. No correct target or developer patch in this read.
            d=DirectOriginalStateSession050(path,root/f"d_source_{i}")
            p=LiveOriginalNativePythonSession052(path,root/f"i_source_{i}")
            rd=d.call("read_building_xml",{})
            ri=p.call("read_building_xml",{})
            need(rd["status"]==ri["status"]=="ok"
                 and rd["xml"].encode("utf8")==ri["xml"].encode("utf8"),
                 "Real D and I initial source XML evidence unequal")
            docs[tid]={
                "original_ifc_sha256":source_sha,
                "original_public_question_sha256":r["public_question_sha256"],
                "original_source_XML_bytes":len(rd["xml"].encode("utf8")),
                "initial_model_source_XML_sha256":sha256(
                    rd["xml"].encode("utf8")).hexdigest(),
                "D_I_initial_source_exact_byte_equality":True,
                "full_original_source_IFC4X3_mm":True,
                "model_tool_calls_per_real_I_case":2,
            }
            for positive in (True,False):
                control="positive" if positive else "negative"
                session=LiveOriginalNativePythonSession052(
                    path,root/f"actual_{i}_{control}")
                source=developer_python_source(
                    tid,r["public_question"],positive=positive)
                seen=session.call("read_building_xml",{})
                need(seen["xml"]==rd["xml"],
                     "Actual I-native model read returned altered source")
                result=session.call("execute_ifc_code",{"code":source})
                need(result.get("status")=="ok"
                     and result.get("python_execution_attested") is True
                     and result.get("native_ifc_committed") is True
                     and result.get("offline_test_double_not_real_python") is False
                     and result.get("local_pinned_image_sha256")==PINNED_DOCKER_IMAGE
                     and result.get("independent_original_native_ifc_scope_oracle")=="PASS",
                     f"Actual pinned Linux worker/independent oracle failed {tid} {control} {result}")
                native=result.get("result")
                need(isinstance(native,dict)
                     and native.get("real_python_witness") is True
                     and native.get("ifcopenshell_native_schema")=="IFC4X3"
                     and native.get("linux_uid")==65534
                     and native.get("linux_gid")==65534
                     and native.get("has_pinned_readonly_worker") is True
                     and native.get("sandbox_source_clone_exists") is True,
                     "Actual pinned Linux process/worker native IFC witness invalid")
                actual=worker_witness(session)
                need(actual["status"]=="ok" and actual["committed"] is True,
                     "Model code was not really executed/committed by Linux worker")
                semantic=evaluate_original_semantic048(
                    path,session.output_ifc,
                    original_sha=source_sha,task_id=tid,
                    public_question=r["public_question"])
                need(semantic["candidatePassesIndependentResearchPhysicalPredicate"]==positive,
                     "Independent physical research semantic classification wrong")
                need(file_hash(path)==source_sha,
                     "Original user IFC mutated by real container")
                records.append({
                    "task_id":tid,
                    "control":control+"_SOURCE_DERIVED_DEVELOPER_ONLY",
                    "model_generated_code":False,
                    "actual_sandbox_python_IfcOpenShell_executed":True,
                    "linux_nonroot_uid":native["linux_uid"],
                    "python_code_sha256":sha256(source.encode("utf8")).hexdigest(),
                    "real_native_IFC_SHA256":result["native_ifc_sha256"],
                    "independent_native_source_physical_oracle_pass":True,
                    "independent_research_physical_semantic_predicate_pass":positive,
                    "actual_attested_Docker_worker":actual["backend"],
                    "actual_IFC4X3_native_mm":True,
                    "original_ifc_unchanged":True,
                    "original_author_grader_used":False,
                    "original_author_benchmark_score":None,
                })
        # Source-SHA original slab for live adversarial transaction behavior.
        slab=registry["geometry_test_14"]
        path=DATA/"ifc"/slab["original_source_ifc_relpath"]
        negatives=[]
        for n,case in enumerate((
            "without_commit","error_after_commit","unrelated_root",
            "source_noop","sandbox_witness",
        )):
            sess=LiveOriginalNativePythonSession052(
                path,root/f"security_{case}")
            code=deliberately_invalid_python(
                "geometry_test_14",slab["public_question"],case)
            r=sess.call("execute_ifc_code",{"code":code})
            evidence=worker_witness(sess)
            want_pass=case=="sandbox_witness"
            need((r["status"]=="ok")==want_pass
                 and bool(r.get("native_ifc_committed"))==want_pass
                 and bool(r.get("python_execution_attested"))==want_pass,
                 f"Actual container security case wrong result: {case} {r}")
            need(sess.output_ifc is not None if want_pass
                 else sess.output_ifc is None,
                 "Rejected IFC was unexpectedly committed")
            if case=="sandbox_witness":
                obs=r["result"]
                need(obs.get("linux_uid")==65534
                     and obs.get("rootfs_write_denied") is True
                     and obs.get("workspace_write_allowed") is True
                     and obs.get("unexpected_private_grader_mount") is False
                     and obs.get("worker_readable") is True,
                     "Live root filesystem/mount/source host isolation witness failed")
            if case=="without_commit":
                need(evidence["status"]=="ok"
                     and evidence["committed"] is False,
                     "Worker ignored model's uncommitted code")
            elif case=="error_after_commit":
                need(evidence["status"]=="error"
                     and evidence["committed"] is True,
                     "Host failed to reject actual worker error after commit()")
            elif case in ("unrelated_root","source_noop"):
                need(evidence["status"]=="ok"
                     and evidence["committed"] is True,
                     "Native independent oracle rejection not exercised")
            else:
                need(evidence["status"]=="ok"
                     and evidence["committed"] is True,
                     "Actual sandbox witness IFC was never committed")
            negatives.append({
                "case":case,
                "worker_real_linux_backend":evidence["backend"],
                "worker_status":evidence["status"],
                "worker_called_commit":evidence["committed"],
                "host_native_ifc_committed":want_pass,
                "invalid_transaction_rolled_back":not want_pass,
                "real_Docker_Python_submitted":True,
                "original_author_score":None,
            })
        # Real rollback proof: first accept actual slab edit, then reject
        # a second actual Docker executable that forges an unexpected Wall.
        sess=LiveOriginalNativePythonSession052(path,root/"security_rollback")
        good=sess.call("execute_ifc_code",{
            "code":developer_python_source(
                "geometry_test_14",slab["public_question"],positive=True)})
        need(good["status"]=="ok" and sess.output_ifc is not None,
             "Cannot prepare last-valid real container native IFC")
        digest=file_hash(sess.output_ifc)
        bad=sess.call("execute_ifc_code",{
            "code":("ifc.create_entity('IfcWall',"
                    "GlobalId=ifcopenshell.guid.new(),"
                    "Name='UNAUTHORIZED_RESEARCH_WALL')\ncommit()\n")})
        actual=worker_witness(sess)
        need(bad["status"]=="error"
             and bad["last_valid_ifc_preserved"] is True
             and file_hash(sess.output_ifc)==digest
             and actual["status"]=="ok" and actual["committed"] is True,
             "Actual Docker native root poisoning not rejected transactionally")
        negatives.append({
            "case":"accepted_then_unauthorized_wall_rollback",
            "worker_real_linux_backend":actual["backend"],
            "worker_status":actual["status"],
            "worker_called_commit":True,
            "host_native_ifc_committed":False,
            "invalid_transaction_rolled_back":True,
            "previous_live_Docker_valid_candidate_SHA256":digest,
            "real_Docker_Python_submitted":True,
            "original_author_score":None,
        })
        need(file_hash(path)==slab["original_ifc_sha256"],
             "Original native IFC input changed after real adversarial run")
    need(len(records)==8 and len(negatives)==6,
         "Expected eight real original cases and six live security probes")
    return {
        "status":"V052_LIVE_PINNED_DOCKER_PYTHON_IFC_REAL_EXECUTION_VERIFIED",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/219",
        "base_commit":"234ad85221272bbce8e226e3cf7dfe88a95b062b",
        "original_bibimbap_task_count":45,
        "original_unique_IFC_source_count":31,
        "selected_original_four_engineering_tasks_not_random_sample":True,
        "other_41_original_tasks_NOT_attempted":41,
        "source_question_and_D_I_source_parity":docs,
        "strict_local_linux_pinned_image_admission":readiness,
        "real_pinned_Linux_Docker_image_SHA256":PINNED_DOCKER_IMAGE,
        "actual_real_Docker_Python_source_native_IFC_developer_controls":8,
        "real_native_IFC_independent_scope_oracle_pass":8,
        "independent_public_source_research_semantic_positive":4,
        "independent_public_source_research_semantic_negative":4,
        "real_Docker_security_transaction_probes":len(negatives),
        "real_Docker_positive_native_IFC_security_witness":1,
        "real_Docker_rejected_security_transactions":5,
        "real_Docker_previous_valid_candidate_rollback_pass":True,
        "original_author_benchmark_score":None,
        "paid_model_inference_count":0,
        "LLM_generated_native_Python_trial_count":0,
        "causal_XML_D_vs_Python_I_model_accuracy_result":None,
        "prior_frozen_reports_unchanged":{
            "v050":PARENT_V050,"v051":PARENT_V051,
        },
        "live_experiment_source_sha256":{
            p:file_hash(ROOT/p) for p in SOURCE_FILES
        },
        "real_Docker_case_records":records,
        "security_transaction_records":negatives,
        "benchmark_hidden_GT_or_original_author_grader_access":False,
    }


def canonical(row:dict)->bytes:
    return (json.dumps(row,sort_keys=True,indent=2,
                       ensure_ascii=False)+"\n").encode("utf8")


def main()->int:
    cli=argparse.ArgumentParser(description=__doc__)
    modes=cli.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write",action="store_true")
    modes.add_argument("--check",action="store_true")
    opts=cli.parse_args()
    payload=canonical(build_report())
    if opts.write:
        with REPORT.open("xb") as f:f.write(payload)
    else:
        need(REPORT.is_file() and REPORT.read_bytes()==payload,
             "Pinned original live Docker evidence replay changed")
    digest=sha256(payload).hexdigest()
    print("V052_LIVE_DOCKER_NATIVE_IFC=PASS SOURCE_TASKS=4/45 "
          "DEVELOPER_CONTROLS=8/8 LIVE_SECURITY_PROBES=6/6 "
          "LLM_CALLS=0 REPORT_SHA256="+digest)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
