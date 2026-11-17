"""Offline original-four genuine Python I-arm engineering readiness audit.

Runs 8 *trusted developer* IfcOpenShell controls directly; the sandbox worker
is NEVER run or simulated as a real LLM submission while Docker is absent.
An explicit offline test double checks the host's native post-execution gate.
"""
from __future__ import annotations
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import (
    file_hash, DockerIFCExecutor, PINNED_DOCKER_IMAGE, build_pinned_docker_command,
)
from tools.bibimbap_v051_trusted_developer_python_controls import (
    make_independent_native_python_control,
)
from tools.bibimbap_v051_independent_native_python_oracle import (
    verify_independent_native_python_v051,
)
from tools.bibimbap_v051_executed_original_native_python_session import (
    OriginalNativePythonSession051,
    inspect_original_native_python_runtime,
)
from tools.bibimbap_v048_independent_original4_semantic_oracle import (
    evaluate_original_semantic048,
)
from tools.bibimbap_v050_direct_original_state_session import DirectOriginalStateSession050


ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v051_original4_executed_python_runtime_readiness_20261118.json"
TASKS=("geometry_test_14","geometry_test_15","topological_test_11","topological_test_17")
PARENT_SHA="eb6bef852eabf12ed76b5c5df861a8e5a355a5142e5ad0d3732d646b25dfb28a"
SOURCES=[
    "tools/bibimbap_v051_executed_original_native_python_session.py",
    "tools/bibimbap_v051_independent_native_python_oracle.py",
    "tools/bibimbap_v051_trusted_developer_python_controls.py",
]


def require(ok:bool,msg:str)->None:
    if not ok:raise AssertionError(msg)


class OfflineTrustedCopyDouble051:
    """NOT a sandbox; its output cannot attest model-authored Python execution."""
    def __init__(self,fixture:Path):
        self.fixture=Path(fixture)
    def run(self,folder:Path,code:str)->dict:
        require("SAFE_OFFLINE_MOCK" in code,
                "Only deterministic offline marker accepted by test double")
        shutil.copyfile(self.fixture,folder/"current.ifc")
        # Backend text is intentionally forged to prove that the host does
        # not confuse an injected fixture with real executed model Python.
        return {"status":"ok","committed":True,
                "backend":"linux_docker_sandbox",
                "result":"OFFLINE_TEST_DOUBLE_NOT_EXECUTED",
                "stdout":"","stderr":""}


def _docker_contract() -> dict:
    # Syntactic policy is separately checked while the daemon is unavailable.
    with TemporaryDirectory(prefix="bmb-v051-cli-policy-") as scratch:
        path=Path(scratch)
        command=build_pinned_docker_command(
            PINNED_DOCKER_IMAGE,"bibi-ifc-0123456789abcdef",path)
        require(command[1]=="--host"
                and command[2]=="npipe:////./pipe/dockerDesktopLinuxEngine",
                "Model I backend may not route to a remote/context Docker daemon")
        for value in ("--network=none","--read-only","--cap-drop=ALL",
                      "--security-opt=no-new-privileges:true",
                      "--memory=768m","--pids-limit=32","--cpus=1",
                      "--user=65534:65534"):
            require(value in command,"Sandbox missing fixed security control")
        mounts=[t for t in command if t.startswith("--mount=type=bind,")]
        require(len(mounts)==2
                and any("target=/workspace" in m for m in mounts)
                and any("target=/worker.py,readonly" in m for m in mounts),
                "Cannot mount other host files, data or grading secrets")
        return {"fixed_local_Docker_host":command[2],
                "bind_mount_count":2,
                "network":"none","rootfs_read_only":True,
                "cap_drop":"ALL","user":"65534:65534",
                "memory_mebibytes":768,"cpu_count":1,
                "worker_is_readonly_mount":True,
                "image_sha256_pinned":PINNED_DOCKER_IMAGE,
                "daemon_level_live_attestation":False}


def build_report() -> dict:
    require(file_hash(ROOT/"reports"/
                      "bibimbap_v050_original4_declarative_state_diff_20261117.json")
            ==PARENT_SHA,
            "v0.50 source-native D-state frozen report changed")
    all_tasks={x["test_id"]:x for x in public_45(AUTHOR,DATA)}
    require(len(all_tasks)==45
            and len({x["original_ifc_sha256"] for x in all_tasks.values()})==31
            and Counter(x["crud"] for x in all_tasks.values())==
            {"create":15,"update":15,"delete":15},
            "Original public source/task denominator changed")
    runtime=inspect_original_native_python_runtime()
    require(runtime["status"] in ("BLOCKED_RUNTIME","RUNTIME_ADMITTED"),
            "Unknown Docker local runtime probe verdict")
    rows=[]
    pinned={}
    with TemporaryDirectory(prefix="bmb-v051-developer-only-") as work:
        workspace=Path(work)
        for n,tid in enumerate(TASKS):
            task=all_tasks[tid]
            sha=task["original_ifc_sha256"]
            source=DATA/"ifc"/task["original_source_ifc_relpath"]
            require(file_hash(source)==sha,"Original public input IFC changed")
            # Both source evidence read tools return literally identical bytes.
            xml_arm=DirectOriginalStateSession050(
                source,workspace/f"D_source_{n}")
            python_arm=OriginalNativePythonSession051(
                source,workspace/f"I_source_{n}")
            dx=xml_arm.call("read_building_xml",{})
            ix=python_arm.call("read_building_xml",{})
            require(dx["status"]==ix["status"]=="ok"
                    and dx["xml"]==ix["xml"]
                    and "execute_ifc_code" in [t["name"] for t in python_arm.tools]
                    and "submit_native_python" not in str(python_arm.tools),
                    "D/I initial source information is not bytewise identical")
            pinned[tid]={"original_source_ifc_sha256":sha,
                         "original_public_question_sha256":
                            task["public_question_sha256"],
                         "initial_D_and_I_model_source_bytewise_equal":True,
                         "initial_original_source_XML_sha256":
                            sha256(dx["xml"].encode("utf8")).hexdigest(),
                         "initial_original_source_XML_bytes":
                            len(dx["xml"].encode("utf8")),
                         "D_model_action_name":"submit_building_xml",
                         "I_model_action_name":"execute_ifc_code",
                         "same_total_tool_call_cap":25}
            for yes in (True,False):
                label="positive" if yes else "negative"
                path=workspace/f"IFC_developer_{n}_{label}.ifc"
                control=make_independent_native_python_control(
                    source,path,original_sha=sha,task_id=tid,
                    public_question=task["public_question"],positive=yes)
                oracle=verify_independent_native_python_v051(
                    source,path,source_sha=sha,task_id=tid)
                semantic=evaluate_original_semantic048(
                    source,path,original_sha=sha,task_id=tid,
                    public_question=task["public_question"])
                require(oracle["status"]==
                        "V051_INDEPENDENT_SOURCE_NATIVE_IFC_SCOPE_ORACLE_PASS"
                        and semantic["candidatePassesIndependentResearchPhysicalPredicate"]==yes,
                        "Trusted offline Python candidate verification mismatch")
                # Test post-execution host's independent IFC transaction with
                # an explicit fixture double, not model-authored Python.
                test_session=OriginalNativePythonSession051(
                    source,workspace/f"STUB_{n}_{label}",
                    executor=OfflineTrustedCopyDouble051(path),
                    allow_offline_double=True)
                result=test_session.call("execute_ifc_code",{
                    "code":"# SAFE_OFFLINE_MOCK; not executed"})
                require(result["status"]=="ok"
                        and result["offline_test_double_not_real_python"] is True
                        and result["python_execution_attested"] is False
                        and file_hash(test_session.output_ifc)==file_hash(path),
                        "Offline test double falsely claims actual Python execution")
                require(file_hash(source)==sha,
                        "Original source IFC edited during I-scoped controls")
                rows.append({
                    "task_id":tid,
                    "control":label+"_TRUSTED_PYTHON_DEVELOPER_ONLY",
                    "native_IFC_candidate_sha256":control["candidate_sha256"],
                    "independent_original_native_scope_oracle_pass":True,
                    "independent_research_semantic_predicate_pass":yes,
                    "Python_IfcOpenShell_trusted_offline_developer_code_executed":True,
                    "model_authored_Python_executed_in_container":False,
                    "offline_host_test_double_is_not_an_execution_attestation":True,
                    "original_author_benchmark_score":None,
                })
    return {
        "status": ("BLOCKED_RUNTIME_NOT_LLM_EXECUTED"
                   if runtime["status"]=="BLOCKED_RUNTIME"
                   else "RUNTIME_PRESENT_NOT_YET_LIVE_WORKER_TESTED"),
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/217",
        "frozen_base_v050_commit":"ca53e6a6d9ecd1f2dd5ee7e57a02fae580382f82",
        "frozen_v050_report_sha256":PARENT_SHA,
        "original_public_45_tasks":45,
        "original_unique_IFC_sources":31,
        "original_four_selected_exploratory_tasks":4,
        "other_41_original_public_tasks_not_attempted":41,
        "initial_model_source_XML_exact_D_I_byte_parity":True,
        "tool_names_both_read_same_evidence_but_different_edit_authority":True,
        "sandbox_cli_policy_offline_only":_docker_contract(),
        "docker_runtime_readonly_probe":runtime,
        "actual_model_python_executed_in_sandbox":0,
        "official_author_grader_invocations":0,
        "official_author_task_success_scores":None,
        "paid_model_calls":0,
        "causal_D_vs_I_accuracy_result":None,
        "real_native_developer_Python_IFC_controls":len(rows),
        "trusted_developer_research_semantic_positive":4,
        "trusted_developer_research_semantic_negative":4,
        "offline_host_contract_double_not_real_execution":True,
        "implementation_sha256":{p:file_hash(ROOT/p) for p in SOURCES},
        "records":rows,
    }


def canonical(report:dict)->bytes:
    return (json.dumps(report,ensure_ascii=False,indent=2,
                       sort_keys=True)+"\n").encode("utf8")


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write",action="store_true")
    mode.add_argument("--check",action="store_true")
    flags=parser.parse_args()
    data=canonical(build_report())
    if flags.write:
        with REPORT.open("xb") as f:f.write(data)
    else:
        require(REPORT.is_file() and REPORT.read_bytes()==data,
                "v0.51 source-native I readiness frozen report replay differs")
    print("V051_I_NATIVE_DOCKER_STATUS="+
          json.loads(data)["status"]+
          " DEVELOPER_IFC=8/8 MODEL_EXECUTIONS=0 SHA256="+
          sha256(data).hexdigest())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
