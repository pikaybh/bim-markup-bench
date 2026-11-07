"""Three-compartment per-task file staging; fail-closed OS execution gate.

THIS IS NOT A VERIFIED SANDBOX. Until #19 independent container validation,
no method accepts, runs, executes, evals or shells untrusted Python. The host
may create staged immutable input copies but agent code cannot run here.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import uuid

from src.runner.agent_visibility import neutral_model_bundle,validate_minimal_agent_bundle
from src.runtime.ifc_projection import project_ifc

SAFE_ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,110}$")

class SandboxNotReady(RuntimeError):
    pass

class TaskStagingError(ValueError):
    pass

@dataclass(frozen=True)
class IsolationStatus:
    source_hash_verified:bool
    three_compartments_staged:bool
    independent_grader_mount:bool
    network_isolated_at_os_level:bool
    process_execution_isolated_at_os_level:bool
    secret_environment_unavailable_to_agent:bool
    generated_python_execution_allowed:bool
    paid_pilot_allowed:bool

    def as_dict(self)->dict:
        return {key:getattr(self,key) for key in self.__dataclass_fields__}

@dataclass(frozen=True)
class TaskCompartments:
    run_id:str
    task_id:str
    arm:str
    seed:int
    source_sha256:str
    root:Path
    agent_workspace:Path
    trusted_compiler:Path
    grader:Path

    def manifest(self)->dict:
        # Path/seed metadata is trusted-controller ONLY, never returned
        # through neutral_model_bundle to a model or a plugin.
        return {
            "run_id":self.run_id,
            "task_id":self.task_id,
            "arm":self.arm,
            "seed":self.seed,
            "source_ifc_sha256":self.source_sha256,
            "compartments":{
                "agent":"agent_workspace",
                "compiler":"trusted_compiler",
                "grader":"grader",
            },
            "agent_allowed_files":[
                "building.xml","language_spec.md","input.ifc"
            ] if self.arm=="direct_xml" else [
                "building.xml","language_spec.md","input.ifc","solution.py"
            ],
            "agent_mount_security":"UNVERIFIED_NO_OS_SANDBOX",
            "GT_visible_to_agent":False,
            "generated_python_executable":False,
        }


def _hash(file:Path)->str:
    h=hashlib.sha256()
    with file.open("rb") as handle:
        for blob in iter(lambda:handle.read(1024*1024),b""):
            h.update(blob)
    return h.hexdigest()


def canonical_run_id(task_id:str,arm:str,seed:int,source_sha:str)->str:
    if not SAFE_ID.fullmatch(task_id):
        raise TaskStagingError("Task id has invalid filesystem characters")
    if arm not in ("direct_xml","imperative_python"):
        raise TaskStagingError("Unexpected experiment arm")
    if not isinstance(seed,int) or isinstance(seed,bool) or not 0<=seed<=2**31-1:
        raise TaskStagingError("Invalid deterministic random seed")
    if not re.fullmatch("[0-9a-f]{64}",source_sha):
        raise TaskStagingError("Invalid original IFC hash")
    digest=hashlib.sha256(
        f"g2-v0:{task_id}:{arm}:{seed}:{source_sha}".encode()
    ).hexdigest()[:24]
    return f"{arm}-{digest}"


def _assert_clean_stage_root(root:Path):
    if root.is_symlink():
        raise TaskStagingError("Task output root cannot be a symlink")
    if root.exists() and any(root.iterdir()):
        raise TaskStagingError("Refuse to reuse a nonempty task root")
    # Parent trust is a caller prerequisite, never accept / or shared
    # system roots as an unsafe place for writable agent inputs.
    if not root.is_absolute() or root==Path("/"):
        raise TaskStagingError("Task root must be an explicit absolute path")
    if root.parent.is_symlink():
        raise TaskStagingError("Task root parent must not be a symlink")


def stage_task(
    source_ifc:Path,
    destination_root:Path,
    task_payload:dict,
    arm:str,
    seed:int,
)->tuple[TaskCompartments,dict]:
    """Only trusted-controller invocation stages paths, not model tools."""
    if source_ifc.is_symlink() or not source_ifc.is_file():
        raise TaskStagingError("Immutable source IFC must be a real regular file")
    model_visible=neutral_model_bundle(source_ifc,task_payload)
    source_sha=model_visible["source_ifc_sha256"]
    run_id=canonical_run_id(model_visible["task_id"],arm,seed,source_sha)
    root=destination_root/run_id
    _assert_clean_stage_root(root)
    root.mkdir(parents=True,mode=0o700,exist_ok=False)
    paths={
        "agent":root/"agent_workspace",
        "compiler":root/"trusted_compiler",
        "grader":root/"grader",
    }
    try:
        for path in paths.values():path.mkdir(mode=0o700)
        for label in ("agent","compiler"):
            target=paths[label]/"input.ifc"
            with source_ifc.open("rb") as original,target.open("xb") as output:
                shutil.copyfileobj(original,output,length=1024*1024)
            if _hash(target)!=source_sha:
                raise TaskStagingError("Input IFC changed during compartment staging")
            target.chmod(0o444)
        (paths["agent"]/"building.xml").write_text(
            model_visible["model_xml_text"],encoding="utf-8"
        )
        from src.direct_markup.agent_runner import LANGUAGE_SPEC
        spec=paths["agent"]/"language_spec.md"
        spec.write_bytes(LANGUAGE_SPEC.read_bytes())
        spec.chmod(0o444)
        if arm=="imperative_python":
            (paths["agent"]/"solution.py").write_bytes(b"")
        record=TaskCompartments(
            run_id=run_id,task_id=model_visible["task_id"],arm=arm,
            seed=seed,source_sha256=source_sha,
            root=root,agent_workspace=paths["agent"],
            trusted_compiler=paths["compiler"],grader=paths["grader"],
        )
        (paths["compiler"]/"trusted_manifest.json").write_text(
            json.dumps(record.manifest(),sort_keys=True)+"\n"
        )
        return record,model_visible
    except Exception:
        # Do not follow symlinks during failed stage cleanup. Pre-existing task
        # roots are refused upfront, so every entry here is ours.
        shutil.rmtree(root)
        raise


def verify_compartment_files(record:TaskCompartments)->dict:
    allowed={
        "agent_workspace":{
            "building.xml","language_spec.md","input.ifc",
            *({"solution.py"} if record.arm=="imperative_python" else set())
        },
        "trusted_compiler":{"input.ifc","trusted_manifest.json"},
        "grader":set(),
    }
    for name,expected in allowed.items():
        directory=record.root/name
        if directory.is_symlink() or not directory.is_dir():
            raise TaskStagingError("Compartment boundary is not a real directory")
        actual=set(os.listdir(directory))
        if actual!=expected:
            raise TaskStagingError("Undeclared file inserted in task compartment")
        for filename in actual:
            p=directory/filename
            if p.is_symlink() or not p.is_file():
                raise TaskStagingError("Sandbox contains symlink/special file")
    agent_ifc=record.agent_workspace/"input.ifc"
    compiler_ifc=record.trusted_compiler/"input.ifc"
    for file in (agent_ifc,compiler_ifc):
        if _hash(file)!=record.source_sha256:
            raise TaskStagingError("Staged original IFC hash mismatch")
        if stat.S_IMODE(file.stat().st_mode)&0o222:
            raise TaskStagingError("Staged source IFC has writable permissions")
    return {
        "status":"FILE_LAYOUT_VERIFIED_ONLY",
        "source_sha256":record.source_sha256,
        "declared_files_verified":True,
        "actual_OS_sandbox_passed":False,
        "secret_process_env_exposed":None,
        "untrusted_code_execution_allowed":False,
        "official_paid_pilot_allowed":False,
    }


def approved_execution_status()->IsolationStatus:
    return IsolationStatus(
        source_hash_verified=False,three_compartments_staged=False,
        independent_grader_mount=False,network_isolated_at_os_level=False,
        process_execution_isolated_at_os_level=False,
        secret_environment_unavailable_to_agent=False,
        generated_python_execution_allowed=False,paid_pilot_allowed=False,
    )


def execute_untrusted_candidate(*args,**kwargs):
    """ALWAYS denied until independent OS sandbox verification and approval."""
    raise SandboxNotReady(
        "Container/VM isolation has not been independently verified. "
        "Python execution/paid model trials remain blocked."
    )
