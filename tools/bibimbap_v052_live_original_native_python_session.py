"""v0.52 real I-native Python Docker session, fast verified local admission.

Frozen v0.51 module/report is unchanged. Local Docker info was slower
than its old 12s preflight despite responsive Docker version/image inspect.
This module checks the SAME fixed local Linux engine and pinned image digest.
It then delegates execution to existing attesting DockerIFCExecutor.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from src.runtime.experimental_v50_original_declarative_state import MAX_CALLS
from src.runner.local_docker_transport import pinned_local_docker_argv
from tools.bibimbap_matched25_tools import (
    DockerIFCExecutor, PINNED_DOCKER_IMAGE, MAX_CODE_BYTES, file_hash,
)
from tools.bibimbap_v051_executed_original_native_python_session import (
    OriginalNativePythonSession051,
    NativePython051BoundaryError,
)
from tools.bibimbap_v051_independent_native_python_oracle import (
    verify_independent_native_python_v051,
)


def live_pinned_local_runtime_admission_v052() -> dict:
    """Read-only, fail-closed verification; no daemon launch or image pull."""
    docker=shutil.which("docker")
    if docker is None:
        return {"status":"BLOCKED_RUNTIME","reason":"LOCAL_DOCKER_CLI_MISSING"}
    try:
        os_command=pinned_local_docker_argv([
            docker,"version","--format","{{.Server.Os}}",
        ])
        probe=subprocess.run(
            os_command,capture_output=True,text=True,encoding="utf8",
            errors="replace",timeout=22,check=False,
        )
        if probe.returncode or probe.stdout.strip()!="linux":
            return {"status":"BLOCKED_RUNTIME",
                    "reason":"FIXED_LOCAL_DOCKER_LINUX_ENGINE_UNAVAILABLE"}
        image_command=pinned_local_docker_argv([
            docker,"image","inspect",PINNED_DOCKER_IMAGE,
            "--format","{{.Id}}",
        ])
        image=subprocess.run(
            image_command,capture_output=True,text=True,encoding="utf8",
            errors="replace",timeout=18,check=False,
        )
        if image.returncode or image.stdout.strip()!=PINNED_DOCKER_IMAGE:
            return {"status":"BLOCKED_RUNTIME",
                    "reason":"ORIGINAL_PINNED_IMAGE_NOT_PRESENT_LOCALLY"}
        return {
            "status":"RUNTIME_ADMITTED",
            "local_linux_engine_verified":True,
            "pinned_worker_image_id":PINNED_DOCKER_IMAGE,
            "model_python_executed_by_readonly_probe":False,
            "container_runtime_attestation_required_before_execution":True,
        }
    except (OSError,ValueError,subprocess.TimeoutExpired):
        return {"status":"BLOCKED_RUNTIME",
                "reason":"LOCAL_DOCKER_ENGINE_IMAGE_READONLY_CHECK_FAILED"}


class LiveOriginalNativePythonSession052(OriginalNativePythonSession051):
    """Strict production I-native; never admits mock executor test doubles."""

    def __init__(self,original_ifc:Path,folder:Path):
        super().__init__(original_ifc,folder,executor=None,
                         allow_offline_double=False)
        if type(self.executor) is not DockerIFCExecutor:
            raise NativePython051BoundaryError(
                "Genuine source-native Python requires exact pinned Docker executor")

    def call(self,name:str,arguments:dict)->dict:
        if name!="execute_ifc_code":
            return super().call(name,arguments)
        if self.calls_used>=MAX_CALLS:
            return {"status":"error","error_type":"ToolBudgetExhausted",
                    "max_tool_calls":MAX_CALLS,"native_ifc_committed":False}
        self.calls_used+=1
        if file_hash(self.original_ifc)!=self.source_sha:
            return {"status":"error","error_type":"OriginalSourceChanged",
                    "native_ifc_committed":False,
                    "last_valid_ifc_preserved":True}
        if (not isinstance(arguments,dict) or set(arguments)!={"code"}
            or not isinstance(arguments["code"],str)
            or not 0<len(arguments["code"].encode("utf8"))<=MAX_CODE_BYTES):
            return {"status":"error","error_type":"InvalidPythonCodeInput",
                    "native_ifc_committed":False}
        admission=live_pinned_local_runtime_admission_v052()
        if admission["status"]!="RUNTIME_ADMITTED":
            return {"status":"error","error_type":"BLOCKED_RUNTIME",
                    "reason":admission["reason"],
                    "actual_python_executed":False,
                    "native_ifc_committed":False,
                    "last_valid_ifc_preserved":True}
        path=self.folder/f"call_{self.calls_used:03d}"
        path.mkdir(exist_ok=False)
        stage=path/"current.ifc"
        shutil.copyfile(self.output_ifc or self.original_ifc,stage)
        try:
            # Existing DockerIFCExecutor attests local host/image/config, two
            # mounts, uid, no-network, no caps, rootfs and resource ceilings.
            result=self.executor.run(path,arguments["code"])
            if not (isinstance(result,dict)
                    and result.get("status")=="ok"
                    and result.get("committed") is True
                    and result.get("backend")=="linux_docker_sandbox"
                    and stage.is_file() and not stage.is_symlink()):
                raise NativePython051BoundaryError(
                    "Actual sandbox failed or had no clean explicit committed IFC")
            oracle=verify_independent_native_python_v051(
                self.original_ifc,stage,source_sha=self.source_sha,
                task_id=self.task_id)
            if not (oracle["status"]==
                    "V051_INDEPENDENT_SOURCE_NATIVE_IFC_SCOPE_ORACLE_PASS"
                    and file_hash(self.original_ifc)==self.source_sha):
                raise NativePython051BoundaryError(
                    "Independent source-native IFC scope/physical oracle failed")
            self.output_ifc=stage
            self.committed=True
            return {
                "status":"ok",
                "native_ifc_committed":True,
                "native_ifc_sha256":file_hash(stage),
                "independent_original_native_ifc_scope_oracle":"PASS",
                "original_author_benchmark_score":None,
                "python_execution_attested":True,
                "actual_linux_sandbox_backend":result["backend"],
                "local_pinned_image_sha256":PINNED_DOCKER_IMAGE,
                "offline_test_double_not_real_python":False,
                "result":result.get("result"),
                "stdout":str(result.get("stdout",""))[:3000],
                "stderr":str(result.get("stderr",""))[:1500],
            }
        except Exception as exc:
            return {
                "status":"error","error_type":type(exc).__name__,
                "native_ifc_committed":False,
                "last_valid_ifc_preserved":True,
                "python_execution_attested":False,
                "original_source_unchanged":
                    file_hash(self.original_ifc)==self.source_sha,
            }
