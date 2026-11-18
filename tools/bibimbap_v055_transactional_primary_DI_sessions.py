"""v0.55 genuine primary D-state and I-native native-IFC transactional sessions.

Additive versioned protection: old v0.50/v0.52 implementations and reports are
not altered. Calls preserve their exact two model-facing tool descriptions,
initial read XML and 25-total-tool-call budget. The candidate is not
promoted until BOTH source-native oracle and IFC4X3 schema-delta pass.

The v0.55 schema gate is production-only and contains ZERO author scorer/GT,
developer source edit controls, model-provider connection or paid calls.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import shutil

from src.runtime.experimental_v50_original_declarative_state import (
    MAX_CALLS,MAX_XML_BYTES,compile_original_declarative_state_v050,
)
from tools.bibimbap_v050_direct_original_state_session import (
    DirectOriginalStateSession050,
)
from tools.bibimbap_v052_live_original_native_python_session import (
    LiveOriginalNativePythonSession052,
    live_pinned_local_runtime_admission_v052,
)
from tools.bibimbap_matched25_tools import (
    DockerIFCExecutor, PINNED_DOCKER_IMAGE, MAX_CODE_BYTES,file_hash,
)
from tools.bibimbap_v045_independent_native_mutation_oracle import (
    verify_original_native_mutation_v045,
)
from tools.bibimbap_v055_production_schema_gate import (
    NativeSourceSchema055Error,validate_production_native_commit_v055,
)


class SchemaGuardedDirectStateSession055(DirectOriginalStateSession050):
    """Real final-state-XML D-arm, original source/IFC4X3 schema commit gate."""

    def call(self,name:str,arguments:dict)->dict:
        if name!="submit_building_xml":
            return super().call(name,arguments)
        if self.calls_used>=MAX_CALLS:
            return {
                "status":"error","error_type":"ToolBudgetExhausted",
                "max_tool_calls":MAX_CALLS,"native_ifc_committed":False,
            }
        self.calls_used+=1
        if file_hash(self.original_ifc)!=self.source_sha:
            return {
                "status":"error","error_type":"OriginalSourceChanged",
                "native_ifc_committed":False,"last_valid_xml_preserved":True,
            }
        if (not isinstance(arguments,dict) or set(arguments)!={"xml_text"}
            or not isinstance(arguments["xml_text"],str)):
            return {
                "status":"error","error_type":"InvalidWriteArguments",
                "native_ifc_committed":False,"last_valid_xml_preserved":True,
            }
        payload=arguments["xml_text"].encode("utf8")
        if not 0<len(payload)<=MAX_XML_BYTES:
            return {
                "status":"error","error_type":"InvalidXMLSize",
                "native_ifc_committed":False,"last_valid_xml_preserved":True,
            }
        self.submissions+=1
        attempt=self.folder/f"attempt_{self.submissions:03d}"
        attempt.mkdir(exist_ok=False)
        (attempt/"submitted_state.xml").write_bytes(payload)
        candidate=attempt/"candidate_original_native_mm.ifc"
        try:
            compiled=compile_original_declarative_state_v050(
                self.original_ifc,payload,candidate,source_sha=self.source_sha)
            # Preserve original v0.50 source-physical writer validation too:
            prior=verify_original_native_mutation_v045(
                self.original_ifc,candidate,
                submitted_xml=compiled.internal_native_writer_xml,
                source_sha=self.source_sha,task_id=self.task_id)
            if prior["status"]!="V045_INDEPENDENT_ORIGINAL_IFC_NATIVE_MUTATION_ORACLE_PASS":
                raise NativeSourceSchema055Error("PriorSourceNativeOracleRejected")
            admission=validate_production_native_commit_v055(
                self.original_ifc,candidate,source_sha=self.source_sha,
                task_id=self.task_id)
            if admission["status"]!="V055_SOURCE_SCHEMA_AND_NATIVE_SCOPE_ADMITTED":
                raise NativeSourceSchema055Error("NativeAdmissionRejected")
            digest=admission["candidate_sha256"]
            # Atomic host last-valid XML and native IFC promotion.
            self.output_ifc=candidate
            self.current_xml=payload
            return {
                "status":"ok","native_ifc_committed":True,
                "native_ifc_sha256":digest,
                "current_xml_sha256":sha256(payload).hexdigest(),
                "independent_original_native_ifc_physical_oracle":"PASS",
                "independent_original_schema_delta_oracle":"PASS",
                "introduced_schema_error_count":0,
                "original_author_benchmark_score":None,
                "last_valid_state_committed":True,
            }
        except Exception as exc:
            if candidate.exists():
                candidate.unlink()
            return {
                "status":"error",
                "error_type":(
                    "NativeSchemaOrScopeRejected"
                    if isinstance(exc,NativeSourceSchema055Error)
                    else "InvalidStateOrCompileRejected"),
                "native_ifc_committed":False,
                "last_valid_xml_preserved":True,
                "last_valid_ifc_preserved":True,
                "current_xml_sha256":sha256(self.current_xml).hexdigest(),
                "original_source_unchanged":
                    file_hash(self.original_ifc)==self.source_sha,
            }


class SchemaGuardedLivePythonSession055(LiveOriginalNativePythonSession052):
    """Real pinned Linux Docker Python I-arm, native source/schema commit gate.

    Deliberately no offline injected executors: the worker MUST be genuine
    DockerIFCExecutor and return the exact pinned local backend attestation.
    """

    def __init__(self,original_ifc:Path,folder:Path):
        super().__init__(original_ifc,folder)
        if type(self.executor) is not DockerIFCExecutor or self.is_offline_double:
            raise NativeSourceSchema055Error("Only genuine pinned Docker executor")

    def call(self,name:str,arguments:dict)->dict:
        if name!="execute_ifc_code":
            return super().call(name,arguments)
        if self.calls_used>=MAX_CALLS:
            return {
                "status":"error","error_type":"ToolBudgetExhausted",
                "max_tool_calls":MAX_CALLS,"native_ifc_committed":False,
            }
        self.calls_used+=1
        if file_hash(self.original_ifc)!=self.source_sha:
            return {
                "status":"error","error_type":"OriginalSourceChanged",
                "native_ifc_committed":False,"last_valid_ifc_preserved":True,
            }
        if (not isinstance(arguments,dict) or set(arguments)!={"code"}
            or not isinstance(arguments["code"],str)
            or not 0<len(arguments["code"].encode("utf8"))<=MAX_CODE_BYTES):
            return {
                "status":"error","error_type":"InvalidPythonCodeInput",
                "native_ifc_committed":False,
            }
        admission=live_pinned_local_runtime_admission_v052()
        if admission["status"]!="RUNTIME_ADMITTED":
            return {
                "status":"error","error_type":"BLOCKED_RUNTIME",
                "reason":admission["reason"],
                "actual_python_executed":False,
                "native_ifc_committed":False,
                "last_valid_ifc_preserved":True,
            }
        attempt=self.folder/f"call_{self.calls_used:03d}"
        attempt.mkdir(exist_ok=False)
        candidate=attempt/"current.ifc"
        shutil.copyfile(self.output_ifc or self.original_ifc,candidate)
        try:
            executed=self.executor.run(attempt,arguments["code"])
            if not (
                isinstance(executed,dict)
                and executed.get("status")=="ok"
                and executed.get("committed") is True
                and executed.get("backend")=="linux_docker_sandbox"
                and candidate.is_file() and not candidate.is_symlink()
            ):
                raise RuntimeError("DockerWorkerCommitNotAttested")
            # Both checks run on the actual worker-produced IFC, BEFORE
            # making it the last-good source for any subsequent model call.
            native=validate_production_native_commit_v055(
                self.original_ifc,candidate,source_sha=self.source_sha,
                task_id=self.task_id)
            if native["status"]!="V055_SOURCE_SCHEMA_AND_NATIVE_SCOPE_ADMITTED":
                raise NativeSourceSchema055Error("NativeAdmissionRejected")
            self.output_ifc=candidate
            self.committed=True
            return {
                "status":"ok",
                "native_ifc_committed":True,
                "native_ifc_sha256":native["candidate_sha256"],
                "independent_original_native_ifc_scope_oracle":"PASS",
                "independent_original_schema_delta_oracle":"PASS",
                "introduced_schema_error_count":0,
                "original_author_benchmark_score":None,
                "python_execution_attested":True,
                "offline_test_double_not_real_python":False,
                "actual_linux_sandbox_backend":executed["backend"],
                "local_pinned_image_sha256":PINNED_DOCKER_IMAGE,
                "result":executed.get("result"),
                "stdout":str(executed.get("stdout",""))[:3000],
                "stderr":str(executed.get("stderr",""))[:1500],
            }
        except Exception as exc:
            if candidate.exists():
                candidate.unlink()
            return {
                "status":"error",
                "error_type":(
                    "NativeSchemaOrScopeRejected"
                    if isinstance(exc,NativeSourceSchema055Error)
                    else "NativeWorkerOrValidationRejected"),
                "native_ifc_committed":False,
                "last_valid_ifc_preserved":True,
                "python_execution_attested":False,
                "original_source_unchanged":
                    file_hash(self.original_ifc)==self.source_sha,
            }
