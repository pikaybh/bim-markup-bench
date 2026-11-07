"""LLM-free imperative control submission envelope with shared observations.

The model can propose solution.py text. It CANNOT execute it here: actual
untrusted code execution is blocked until OS sandbox #19 and budget runner #20.
The independently hand-authored G1 I0 oracle is a separate trusted local
test, not provided as model solution code or executed from this interface.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import time
import tempfile
from typing import Literal

from src.direct_markup.agent_runner import SourceOnlySettings,stage_source_only_workspace
from src.imperative_control.tool_policy import (
    CodeCheck,ImperativePreflightError,preflight_generated_python,
)

API_NOTES=Path(__file__).resolve().parent/"prompt_templates/ifcopenshell_reference.md"

class UnsafeExecutionBlocked(ValueError):
    pass

@dataclass(frozen=True)
class MatchedObservations:
    task_id:str
    instruction:str
    model_xml_text:str
    toy_language_spec:str
    input_ifc_sha256:str
    observation_format:str="XML_VIEW_OF_SAME_SOURCE_IFC"

    def as_dict(self):
        return {
            "task_id":self.task_id,
            "instruction":self.instruction,
            "model_xml_text":self.model_xml_text,
            "toy_language_spec":self.toy_language_spec,
            "input_ifc_sha256":self.input_ifc_sha256,
            "observation_format":self.observation_format,
        }


@dataclass(frozen=True)
class ControlConfig:
    mode:Literal["one_shot","feedback"]="one_shot"
    max_attempts:int=1
    max_wall_seconds:float=180.
    max_output_bytes:int=32_768

    def __post_init__(self):
        if self.mode not in ("one_shot","feedback"):
            raise UnsafeExecutionBlocked("Unknown control mode")
        if self.mode=="one_shot" and self.max_attempts!=1:
            raise UnsafeExecutionBlocked("Control one-shot must have exactly one attempt")
        if not 1<=self.max_attempts<=5 or not 1<=self.max_output_bytes<=64*1024:
            raise UnsafeExecutionBlocked("Invalid control arm token/attempt budget")
        if not 0<self.max_wall_seconds<=180:
            raise UnsafeExecutionBlocked("Invalid control arm wall-time limit")


@dataclass(frozen=True)
class CandidateCode:
    expected_source_sha256:str
    code:str
    success_claim:bool=True


def create_matched_observations(source_ifc:Path,task_payload:dict)->MatchedObservations:
    """Construct identical base source context to direct XML arm; no GT fields."""
    with tempfile.TemporaryDirectory(prefix="g2-matched-observations-") as temp:
        direct=stage_source_only_workspace(
            source_ifc,Path(temp)/"readonly_source",task_payload,SourceOnlySettings())
        source=direct.agent_visible_context()
        return MatchedObservations(
            source.task_id,source.instruction,source.xml_text,
            source.language_spec,
            hashlib.sha256((Path(temp)/"readonly_source"/"input.ifc").read_bytes()).hexdigest()
        )


class ImperativeControlSession:
    def __init__(self,observations:MatchedObservations,config:ControlConfig):
        self._observations=observations
        self._config=config
        self._started=time.perf_counter()
        self._attempts=0
        self._accepted_code=None
        self._trace=[]

    def model_visible_context(self)->dict:
        return {
            **self._observations.as_dict(),
            "submission_filename":"solution.py",
            "api_reference_notes":API_NOTES.read_text(encoding="utf-8"),
            "allowed_authoring_operations":["submit_python_text"],
            "allowed_execution_operations":[],
            "OS_sandbox_available":False,
        }

    def submit_code(self,candidate:CandidateCode)->dict:
        if self._accepted_code is not None:
            raise UnsafeExecutionBlocked("Control candidate already accepted")
        if self._attempts>=self._config.max_attempts:
            raise UnsafeExecutionBlocked("Control attempt budget exhausted")
        if time.perf_counter()-self._started>self._config.max_wall_seconds:
            raise UnsafeExecutionBlocked("Control wall-time budget exceeded")
        self._attempts+=1
        sha=self._observations.input_ifc_sha256
        if candidate.expected_source_sha256!=sha:
            accepted=False
            codecheck=None
            error="SOURCE_SHA_MISMATCH"
        else:
            try:
                code=candidate.code.encode("utf-8")
                if len(code)>self._config.max_output_bytes:
                    raise ImperativePreflightError("Python output exceeds paired arm limit")
                codecheck=preflight_generated_python(code)
                accepted=True
                error=None
            except (ImperativePreflightError,UnicodeError):
                codecheck=None
                accepted=False
                error="SYNTAX_OR_STATIC_POLICY_BLOCKED"
        if accepted:
            self._accepted_code=candidate.code
        self._trace.append({
            "attempt":self._attempts,
            "status":"ACCEPTED_SOURCE_ONLY_NOT_EXECUTABLE" if accepted else "REJECTED",
            "code_sha256":codecheck.source_sha256 if codecheck else None,
            "reject_reason":error,
            "api_runtime_calls":0,
            "actual_model_tokens":None,
            "source_ifc_sha256":sha,
            "elapsed_wall_ms":int((time.perf_counter()-self._started)*1000),
            "executed":False,
        })
        # Candidate is syntax-checked and stored in memory only. No untrusted
        # bytecode, subprocess or filesystem action is performed.
        return {"status":self._trace[-1]["status"],"executed":False}

    def execute_generated_solution(self):
        """Physical security gate: always denied before #19 OS sandbox."""
        raise UnsafeExecutionBlocked(
            "Generated Python execution requires isolated OS/container #19; no execution available"
        )

    def trace(self)->dict:
        return {
            "task_id":self._observations.task_id,
            "arm":"imperative_python",
            "mode":self._config.mode,
            "attempt_count":self._attempts,
            "max_attempts":self._config.max_attempts,
            "source_ifc_sha256":self._observations.input_ifc_sha256,
            "model_provider_called":False,
            "python_executed":False,
            "OS_sandbox_available":False,
            "events":list(self._trace),
        }
