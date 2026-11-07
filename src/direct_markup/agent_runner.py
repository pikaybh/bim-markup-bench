"""Source-only XML file editing harness, with NO real LLM or IFC mutation tool.

G2 #17 bounded offline slice. The model interface consists of plain text
visible XML/spec/instruction and a textual file edit. A separate *trusted*
controller later compiles accepted source into IFC; it is not agent-callable.

This is NOT an OS sandbox, provider transport or paid-run authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from typing import Literal

from src.runtime.ifc_projection import project_ifc
from src.runtime.xml_parser import MarkupParseError,parse_xml
from src.security.agent_boundary import (
    FileAccessPolicy,SecurityBoundaryError,validate_agent_payload,
)

LANGUAGE_SPEC=Path(__file__).resolve().parents[2]/"spec/toy_markup_v0.md"
MAX_PATCH_BYTES=2*1024*1024
PREVIEW_DIFF_BYTES=32_000

class FileEditBlocked(ValueError):
    pass

@dataclass(frozen=True)
class SourceOnlySettings:
    mode:Literal["one_shot","feedback"]="one_shot"
    max_attempts:int=1
    max_xml_bytes:int=2*1024*1024
    max_edit_bytes:int=32_768
    max_wall_seconds:float=180.0
    context_mode:Literal["xml_projection"]="xml_projection"

    def __post_init__(self):
        if self.mode not in ("one_shot","feedback"):
            raise FileEditBlocked("Unknown experimental feedback policy")
        if self.context_mode!="xml_projection":
            raise FileEditBlocked("Context surface must be frozen before running paired arms")
        if self.mode=="one_shot" and self.max_attempts!=1:
            raise FileEditBlocked("One-shot policy must have exactly one attempt")
        if not (1<=self.max_attempts<=5):
            raise FileEditBlocked("Maximum attempts must be 1–5")
        if not (1024<=self.max_xml_bytes<=2*1024*1024):
            raise FileEditBlocked("XML limit exceeds pinned parser ceiling")
        if not (1<=self.max_edit_bytes<=MAX_PATCH_BYTES):
            raise FileEditBlocked("File edit byte budget outside bounds")
        if not (0<self.max_wall_seconds<=180):
            raise FileEditBlocked("Task wall-time budget outside safe bounds")

@dataclass(frozen=True)
class AgentVisibleSource:
    task_id:str
    instruction:str
    filename:str
    xml_text:str
    language_spec:str
    xml_byte_sha256:str
    allowed_operations:tuple[str,...]=("read_text","patch_text","rewrite_xml_text")

    def exposed(self)->dict:
        return {
            "task_id":self.task_id,
            "instruction":self.instruction,
            "filename":self.filename,
            "xml_text":self.xml_text,
            "language_spec":self.language_spec,
            "xml_byte_sha256":self.xml_byte_sha256,
            "allowed_operations":list(self.allowed_operations),
        }

@dataclass(frozen=True)
class SourceFileEdit:
    filename:str
    expected_sha256:str
    mode:Literal["surgical_patch","whole_file_rewrite"]
    old_text:str
    new_text:str
    agent_declared_success:bool=True


def _sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def stage_source_only_workspace(source_ifc:Path,workdir:Path,task_payload:dict,
                                settings:SourceOnlySettings)->"SourceOnlySession":
    # The full task/GT dataset record must NOT enter this boundary.
    view=validate_agent_payload(task_payload)
    if workdir.is_symlink() or workdir.exists() and any(workdir.iterdir()):
        raise FileEditBlocked("Task workspace must be a new empty directory")
    workdir.mkdir(parents=True,exist_ok=True)
    try:
        projection=project_ifc(source_ifc)
        # The original IFC remains visible ONLY as a read-only runtime asset,
        # never a writable tool target or copied into the LLM text prompt.
        staged_ifc=workdir/"input.ifc"
        with source_ifc.open("rb") as src, staged_ifc.open("xb") as dst:
            shutil.copyfileobj(src,dst,1024*1024)
        if _sha(staged_ifc.read_bytes())!=projection.source.source_sha256:
            raise FileEditBlocked("Input IFC content changed while staging task")
        staged_ifc.chmod(0o444)
        xml=workdir/"building.xml"
        xml.write_bytes(projection.xml)
        spec=workdir/"language_spec.md"
        spec.write_bytes(LANGUAGE_SPEC.read_bytes())
        spec.chmod(0o444)
        policy=FileAccessPolicy(workdir)
        policy.check("read","building.xml")
        policy.check("edit_xml","building.xml")
        return SourceOnlySession(
            workdir,view,projection.source.source_sha256,settings,policy
        )
    except Exception:
        for filename in ("building.xml","language_spec.md","input.ifc"):
            p=workdir/filename
            if p.exists() and not p.is_symlink():
                p.chmod(0o600)
                p.unlink()
        raise


class SourceOnlySession:
    def __init__(self,workdir:Path,view:dict,source_sha:str,
                 settings:SourceOnlySettings,policy:FileAccessPolicy):
        self._workdir=workdir
        self._view=view
        self._source_sha=source_sha
        self._settings=settings
        self._policy=policy
        self._created=time.perf_counter()
        self._attempts=0
        self._events=[]
        self._accepted=False

    def agent_visible_context(self)->AgentVisibleSource:
        file=self._policy.check("read","building.xml")
        spec=self._policy.check("read","language_spec.md")
        self._events.append({
            "attempt":self._attempts,
            "status":"READ",
            "operation":"read_text",
            "filename":"building.xml",
            "before_sha256":_sha(file.read_bytes()),
            "after_sha256":None,
            "unified_diff":"",
            "agent_declared_success":False,
            "agent_tools_used":["read_text"],
            "agent_BIM_API_calls":0,
            "real_model_provider_called":False,
            "actual_model_tokens":None,
            "elapsed_wall_ms":int((time.perf_counter()-self._created)*1000),
        })
        return AgentVisibleSource(
            task_id=self._view["task_id"],
            instruction=self._view["instruction"],
            filename="building.xml",
            xml_text=file.read_text(encoding="utf-8"),
            language_spec=spec.read_text(encoding="utf-8"),
            xml_byte_sha256=_sha(file.read_bytes()),
        )

    def attempt(self,edit:SourceFileEdit)->dict:
        if self._accepted:
            raise FileEditBlocked("Final accepted source cannot be patched again in this attempt")
        if self._attempts>=self._settings.max_attempts:
            raise FileEditBlocked("Predeclared maximum attempts exceeded")
        if time.perf_counter()-self._created>self._settings.max_wall_seconds:
            raise FileEditBlocked("Predeclared wall-time budget exceeded")
        self._attempts+=1
        try:
            current=self._policy.check("edit_xml",edit.filename)
            if edit.mode not in ("surgical_patch","whole_file_rewrite"):
                raise FileEditBlocked("Only file text patch or rewrite is permitted")
            before=current.read_bytes()
            if _sha(before)!=edit.expected_sha256:
                raise FileEditBlocked("Stale XML version: expected byte SHA-256 mismatch")
            if not isinstance(edit.new_text,str) or not isinstance(edit.old_text,str):
                raise FileEditBlocked("Only UTF-8 text edits are supported")
            if len(edit.new_text.encode("utf-8"))>self._settings.max_edit_bytes:
                raise FileEditBlocked("File edit exceeds predeclared byte budget")
            source=before.decode("utf-8")
            if edit.mode=="surgical_patch":
                if not edit.old_text or source.count(edit.old_text)!=1:
                    raise FileEditBlocked("Surgical patch must match exactly one original text span")
                candidate=source.replace(edit.old_text,edit.new_text,1)
            else:
                if edit.old_text:
                    raise FileEditBlocked("Whole-file rewrite must have empty old_text")
                candidate=edit.new_text
            encoded=candidate.encode("utf-8")
            if encoded==before:
                raise FileEditBlocked("Unchanged XML does not constitute a successful file edit")
            if len(encoded)>self._settings.max_xml_bytes:
                raise FileEditBlocked("Candidate source exceeds parser byte ceiling")
            # Preflight XML/XSD and immutable IFC binding, before touching file.
            parse_xml(encoded,filename="building.xml",
                      expected_source_sha256=self._source_sha)
            fd,temp_name=tempfile.mkstemp(prefix=".xml-candidate-",suffix=".tmp",dir=self._workdir)
            try:
                with os.fdopen(fd,"wb") as output:
                    output.write(encoded)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temp_name,current)
            finally:
                if Path(temp_name).exists():
                    Path(temp_name).unlink()
            old_lines=source.splitlines(keepends=True)
            new_lines=candidate.splitlines(keepends=True)
            diff="".join(difflib.unified_diff(
                old_lines,new_lines,fromfile="a/building.xml",tofile="b/building.xml",
            ))
            event={
                "attempt":self._attempts,
                "status":"ACCEPTED_VALID_XML",
                "operation":"edit_xml_text",
                "filename":"building.xml",
                "before_sha256":_sha(before),
                "after_sha256":_sha(encoded),
                "unified_diff":diff[:PREVIEW_DIFF_BYTES],
                "agent_declared_success":bool(edit.agent_declared_success),
                "agent_tools_used":["edit_xml_text"],
                "agent_BIM_API_calls":0,
                "real_model_provider_called":False,
                "actual_model_tokens":None,
                "elapsed_wall_ms":int((time.perf_counter()-self._created)*1000),
            }
            self._events.append(event)
            self._accepted=True
            return {"status":"ACCEPTED_VALID_XML","attempt":self._attempts,
                    "source_sha256":_sha(encoded),"diagnostic":None}
        except (FileEditBlocked,SecurityBoundaryError,MarkupParseError,
                ValueError,UnicodeError) as exc:
            diagnostic=(exc.diagnostic if isinstance(exc,MarkupParseError)
                        else {"code":"FILE_EDIT_POLICY_BLOCKED","severity":"ERROR",
                              "file":"building.xml","line":1,"column":1,
                              "message":type(exc).__name__})
            try:
                current_digest=_sha(self._policy.check("read","building.xml").read_bytes())
            except (SecurityBoundaryError,OSError):
                current_digest=None
            self._events.append({
                "attempt":self._attempts,
                "status":"REJECTED",
                "operation":"edit_xml_text",
                "filename":"building.xml",
                "before_sha256":current_digest,
                "after_sha256":None,
                "unified_diff":"",
                "agent_declared_success":False,
                "agent_tools_used":[],
                "agent_BIM_API_calls":0,
                "real_model_provider_called":False,
                "actual_model_tokens":None,
                "elapsed_wall_ms":int((time.perf_counter()-self._created)*1000),
            })
            return {
                "status":"REJECTED","attempt":self._attempts,
                "diagnostic":diagnostic if self._settings.mode=="feedback" else None,
            }

    def reject_tool_call(self,tool_name:str,filename:str="")->None:
        """Check the tiny file-tool allowlist; audit every denied operation.

        The adapter offers NO executable code, subprocess or BIM authoring
        tools. Physical process/network isolation remains G2 #19.
        """
        name=tool_name.lower().strip()
        allowed={"read_text","patch_text","rewrite_xml_text"}
        try:
            if name not in allowed:
                raise FileEditBlocked("Nonfile authoring tool request is forbidden")
            self._policy.check("read" if name=="read_text" else "edit_xml",
                               filename)
        except (FileEditBlocked,SecurityBoundaryError) as exc:
            self._events.append({
                "attempt":self._attempts,
                "status":"REJECTED_TOOL",
                "operation":"tool_denied",
                "filename":"building.xml",
                "before_sha256":None,"after_sha256":None,"unified_diff":"",
                "agent_declared_success":False,
                "agent_tools_used":[],
                "agent_BIM_API_calls":0,
                "real_model_provider_called":False,
                "actual_model_tokens":None,
                "elapsed_wall_ms":int((time.perf_counter()-self._created)*1000),
            })
            raise FileEditBlocked("Forbidden file/tool action") from exc

    def accepted_xml(self)->bytes:
        if not self._accepted:
            raise FileEditBlocked("Trusted compiler cannot consume an unaccepted XML state")
        return self._policy.check("read","building.xml").read_bytes()

    def trace(self)->dict:
        return {
            "task_id":self._view["task_id"],
            "mode":self._settings.mode,
            "context_mode":self._settings.context_mode,
            "attempt_count":self._attempts,
            "maximum_attempts":self._settings.max_attempts,
            "max_wall_seconds":self._settings.max_wall_seconds,
            "accepted_valid_xml":self._accepted,
            "source_ifc_sha256":self._source_sha,
            "events":list(self._events),
            "tool_access_boundary":"FILE_TEXT_ONLY_NOT_OS_SANDBOX",
            "trusted_compiler_visible_to_agent":False,
            "real_model_provider_called":False,
        }


class TrustedCompilationController:
    """Not part of the model interface. Requires trusted owner invocation."""

    @staticmethod
    def compile_accepted(session:SourceOnlySession,source_ifc:Path,destination:Path):
        from src.runtime.compiler import compile_declarative_xml
        # This call is NEVER exposed to AgentVisibleSource or FileEditSession.
        if hashlib.sha256(source_ifc.read_bytes()).hexdigest()!=session._source_sha:
            raise FileEditBlocked("Trusted controller source IFC digest mismatch")
        return compile_declarative_xml(source_ifc,session.accepted_xml(),destination)
