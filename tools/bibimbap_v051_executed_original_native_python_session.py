"""Genuine I-native original four via PINNED Linux Docker executed Python.

No source editing API, D typed plan, model GT or original benchmark scorer.
Offline injected doubles test the host only and never count as Python execution.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

from src.runtime.experimental_v44_original_native_step_readonly import PINS
from src.runtime.experimental_v50_original_declarative_state import (
    project_original_declarative_state_v050, MAX_CALLS,
)
from src.runtime.experimental_v45_original_native_mutations import check_source
from src.runner.local_docker_transport import pinned_local_docker_argv
from tools.bibimbap_matched25_tools import (
    DockerIFCExecutor, PINNED_DOCKER_IMAGE, MAX_CODE_BYTES, file_hash,
)
from tools.bibimbap_v051_independent_native_python_oracle import (
    verify_independent_native_python_v051,
)


class NativePython051BoundaryError(ValueError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise NativePython051BoundaryError(message)


def inspect_original_native_python_runtime() -> dict:
    """Read-only Docker local Linux image admission. No daemon lifecycle action."""
    docker = shutil.which("docker")
    if not docker:
        return {"status": "BLOCKED_RUNTIME",
                "reason": "LOCAL_DOCKER_CLI_MISSING",
                "actual_python_executed": False}
    try:
        info = pinned_local_docker_argv([
            docker, "info", "--format", "{{json .}}",
        ])
        p = subprocess.run(info, capture_output=True, text=True,
                           encoding="utf8", errors="replace",
                           timeout=12, check=False)
        if p.returncode != 0:
            return {"status": "BLOCKED_RUNTIME",
                    "reason": "LOCAL_DOCKER_LINUX_DAEMON_NOT_AVAILABLE",
                    "actual_python_executed": False}
        server = json.loads(p.stdout)
        if server.get("OSType") != "linux":
            return {"status": "BLOCKED_RUNTIME",
                    "reason": "REQUIRES_LINUX_DOCKER_ENGINE",
                    "actual_python_executed": False}
        inspect = pinned_local_docker_argv([
            docker, "image", "inspect", PINNED_DOCKER_IMAGE,
            "--format", "{{.Id}}",
        ])
        q = subprocess.run(inspect, capture_output=True, text=True,
                           encoding="utf8", errors="replace",
                           timeout=12, check=False)
        if q.returncode != 0 or q.stdout.strip() != PINNED_DOCKER_IMAGE:
            return {"status": "BLOCKED_RUNTIME",
                    "reason": "EXACT_PINNED_LOCAL_IFCOPENSHELL_IMAGE_UNAVAILABLE",
                    "actual_python_executed": False}
        return {"status": "RUNTIME_ADMITTED", "linux_engine": True,
                "exact_pinned_docker_image": PINNED_DOCKER_IMAGE,
                "actual_python_executed": False,
                "requires_per_candidate_independent_ifc_oracle": True}
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        return {"status": "BLOCKED_RUNTIME",
                "reason": "DOCKER_RUNTIME_ATTESTATION_FAILED",
                "actual_python_executed": False}


class OriginalNativePythonSession051:
    """25-call I-native host. Explicit doubles cannot attest real Python."""

    def __init__(self, original_ifc: Path, folder: Path, *,
                 executor: DockerIFCExecutor | None = None,
                 allow_offline_double: bool = False) -> None:
        self.original_ifc = Path(original_ifc)
        self.folder = Path(folder)
        require(self.original_ifc.is_file() and not self.original_ifc.is_symlink()
                and self.folder.parent.is_dir()
                and not self.folder.parent.is_symlink()
                and not self.folder.exists() and not self.folder.is_symlink(),
                "Source and isolated I-native scratch folder must be safe/new")
        self.source_sha = file_hash(self.original_ifc)
        require(self.source_sha in PINS,
                "Only four SHA-pinned original public IFC input files supported")
        self.task_id = check_source(self.original_ifc, self.source_sha)
        self.original_source_xml = project_original_declarative_state_v050(
            self.original_ifc, source_sha=self.source_sha,
        ).xml
        self.is_offline_double = bool(allow_offline_double)
        if executor is None:
            self.executor = DockerIFCExecutor()
            require(not allow_offline_double,
                    "Offline admission needs an explicit injected test executor")
        else:
            require(allow_offline_double or type(executor) is DockerIFCExecutor,
                    "Production requires actual pinned DockerIFCExecutor")
            self.executor = executor
        self.calls_used = 0
        self.output_ifc: Path | None = None
        self.committed = False
        self.folder.mkdir(exist_ok=False)

    @property
    def tools(self) -> list[dict]:
        return [
            {"type": "function", "name": "read_building_xml",
             "description": (
                 "Read the same exact original native IFC4X3 source evidence "
                 "and initial final-state manifest returned to the declarative "
                 "arm: original STEP, GUID, geometry, materials, relationships "
                 "and placements. Read-only for this Python IFC authoring arm."),
             "parameters": {"type": "object", "properties": {},
                            "additionalProperties": False}, "strict": True},
            {"type": "function", "name": "execute_ifc_code",
             "description": (
                 "Execute actual Python/IfcOpenShell on an isolated original "
                 "native IFC4X3 millimetre model in a pinned local Linux "
                 "no-network sandbox. Globals: ifc, ifcopenshell, api, util, "
                 "element_util, guid, result and commit(). Call commit() "
                 "to propose native changes. Independent native-source "
                 "preservation oracle accepts or rejects the changed IFC. "
                 "No original author scorer or ground truth is accessible."),
             "parameters": {
                 "type": "object",
                 "properties": {"code": {"type": "string"}},
                 "required": ["code"], "additionalProperties": False},
             "strict": True},
        ]

    def call(self, name: str, arguments: dict) -> dict:
        if self.calls_used >= MAX_CALLS:
            return {"status": "error", "error_type": "ToolBudgetExhausted",
                    "max_tool_calls": MAX_CALLS, "native_ifc_committed": False}
        self.calls_used += 1
        if file_hash(self.original_ifc) != self.source_sha:
            return {"status": "error", "error_type": "OriginalSourceChanged",
                    "native_ifc_committed": False, "last_valid_ifc_preserved": True}
        if name == "read_building_xml":
            if arguments != {}:
                return {"status": "error", "error_type": "InvalidReadArguments"}
            return {"status": "ok",
                    "xml": self.original_source_xml.decode("utf8"),
                    "source_xml_sha256": sha256(self.original_source_xml).hexdigest(),
                    "current_native_sha256": (
                        file_hash(self.output_ifc) if self.output_ifc is not None
                        else self.source_sha),
                    "native_candidate_available": self.output_ifc is not None}
        if name != "execute_ifc_code":
            return {"status": "error", "error_type": "UnknownINativeTool",
                    "native_ifc_committed": False}
        if (not isinstance(arguments, dict) or set(arguments) != {"code"}
            or not isinstance(arguments["code"], str)
            or not 0 < len(arguments["code"].encode("utf8")) <= MAX_CODE_BYTES):
            return {"status": "error", "error_type": "InvalidPythonCodeInput",
                    "native_ifc_committed": False}
        if not self.is_offline_double:
            admission = inspect_original_native_python_runtime()
            if admission["status"] != "RUNTIME_ADMITTED":
                return {"status": "error", "error_type": "BLOCKED_RUNTIME",
                        "reason": admission["reason"],
                        "actual_python_executed": False,
                        "native_ifc_committed": False,
                        "last_valid_ifc_preserved": True}
        attempt = self.folder / f"call_{self.calls_used:03d}"
        attempt.mkdir(exist_ok=False)
        stage = attempt / "current.ifc"
        shutil.copyfile(self.output_ifc or self.original_ifc, stage)
        try:
            executed = self.executor.run(attempt, arguments["code"])
            # Reject errors even if worker called commit() just before raising.
            require(isinstance(executed, dict)
                    and executed.get("status") == "ok"
                    and executed.get("committed") is True
                    and stage.is_file() and not stage.is_symlink(),
                    "Uncommitted or failed Python model execution never persists")
            if not self.is_offline_double:
                require(executed.get("backend") == "linux_docker_sandbox",
                        "Trusted worker sandbox backend not attested")
            oracle = verify_independent_native_python_v051(
                self.original_ifc, stage, source_sha=self.source_sha,
                task_id=self.task_id)
            require(oracle["status"] ==
                    "V051_INDEPENDENT_SOURCE_NATIVE_IFC_SCOPE_ORACLE_PASS"
                    and file_hash(self.original_ifc) == self.source_sha,
                    "Source native candidate preservation oracle rejected edit")
            self.output_ifc = stage
            self.committed = True
            return {"status": "ok", "native_ifc_committed": True,
                    "native_ifc_sha256": file_hash(stage),
                    "independent_original_native_ifc_scope_oracle": "PASS",
                    "original_author_benchmark_score": None,
                    "python_execution_attested": not self.is_offline_double,
                    "offline_test_double_not_real_python": self.is_offline_double,
                    "result": executed.get("result"),
                    "stdout": str(executed.get("stdout",""))[:3000],
                    "stderr": str(executed.get("stderr",""))[:1500]}
        except Exception as exc:
            return {"status": "error", "error_type": type(exc).__name__,
                    "native_ifc_committed": False,
                    "last_valid_ifc_preserved": True,
                    "python_execution_attested": False,
                    "original_source_unchanged":
                        file_hash(self.original_ifc) == self.source_sha}
