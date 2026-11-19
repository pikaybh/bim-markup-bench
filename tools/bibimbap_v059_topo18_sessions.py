"""v0.59 first six-holdout task genuine D complete/compact and Docker I sessions.

All three read EXACT same source-only native XML. D emits COMPLETE final
original three-room state, either full native source-anchored XML or compact
full managed roster. Both restore full state and compile an actual IFC in a
trusted host, then run the very same source-only native oracle as the
genuinely Docker-executed arbitrary Python/IfcOpenShell I arm.

Distinct versioned protocol and honest limited original-task eligibility.
No author scorer, private target, GT, fake executed code, paid model/client.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import shutil

from tools.bibimbap_matched25_tools import (
    DockerIFCExecutor,PINNED_DOCKER_IMAGE,MAX_CODE_BYTES,file_hash,
)
from tools.bibimbap_v052_live_original_native_python_session import (
    live_pinned_local_runtime_admission_v052,
)
from tools.bibimbap_v059_topo18_native import (
    SOURCE_SHA,TASK,MAX_XML,MAX_COMPACT,MAX_CALLS,
    Topo18Native059Error,
    _source,
    source_full_state_v059,
    parse_full_final_state_v059,
    restore_compact_final_state_v059,
    compile_space_deletion_v059,
    native_space_delete_scope_v059,
)


def _tool(name:str,description:str,parameter:str)->dict:
    return {
        "type":"function",
        "name":name,
        "description":description,
        "parameters":{
            "type":"object",
            "properties":{parameter:{"type":"string"}},
            "required":[parameter],
            "additionalProperties":False,
        },
        "strict":True,
    }


READ_TOOL=_tool(
    "read_building_xml",
    "Read original immutable public-source native IFC4X3 geometry/GlobalIds "
    "and the last accepted full declarative state. This is the same exact "
    "source read tool in all v0.59 experimental D/I representations.",
    "query",
)
FULL_TOOL=_tool(
    "submit_building_xml",
    "Submit the COMPLETE final BuildingState XML v0.59, including exactly "
    "unchanged OriginalNativeIFCSource and exactly 3 original IfcSpace "
    "managed membership rows with present true/false; no edit script, "
    "commands, partial patches, target labels or Python. The host restores "
    "and commits only after independent native/IFC schema admission.",
    "xml_text",
)
COMPACT_TOOL=_tool(
    "submit_managed_final_state",
    "Submit COMPLETE v0.59 ManagedFinalState XML containing the source hash, "
    "original BuildingState hash and ALL three original IfcSpace GUIDs with "
    "explicit final present true/false. No partial patch, named commands, "
    "Python code or inferred missing objects. Source subtree is reattached "
    "only by the trusted compiler and independently validated.",
    "xml_text",
)
PYTHON_TOOL=_tool(
    "execute_ifc_code",
    "Execute general Python/IfcOpenShell source against a cloned original "
    "IFC4X3 in a pinned non-root no-network Linux Docker worker. The model "
    "must call commit() explicitly. Host will accept only a native IFC "
    "which independently matches original source scope and schema policy. "
    "No GT, author scorer or reference solutions are visible.",
    "code",
)


class _Base059:
    def __init__(self,source_ifc:Path,folder:Path):
        self.original_ifc=Path(source_ifc)
        _source(self.original_ifc,SOURCE_SHA)
        self.source_sha=SOURCE_SHA
        self.task_id=TASK
        self.folder=Path(folder)
        if self.folder.exists() or self.folder.is_symlink():
            raise Topo18Native059Error("Fresh research trial folder required")
        self.folder.mkdir(parents=True)
        self.source_xml=source_full_state_v059(
            self.original_ifc,source_sha=self.source_sha)
        self.current_xml=self.source_xml
        self.calls_used=0
        self.submissions=0
        self.output_ifc:Path|None=None

    @property
    def tools(self)->list[dict]:
        raise NotImplementedError

    def _answer_error(self,kind:str)->dict:
        return {
            "status":"error","error_type":kind,
            "native_ifc_committed":False,
            "last_valid_ifc_preserved":True,
            "last_valid_xml_preserved":True,
            "current_xml_sha256":sha256(self.current_xml).hexdigest(),
        }

    def _read(self,arguments:dict)->dict:
        if not isinstance(arguments,dict) or set(arguments)!={"query"}:
            return self._answer_error("InvalidSourceReadArgument")
        if (not isinstance(arguments["query"],str)
            or arguments["query"] not in ("","source","building")):
            return self._answer_error("InvalidSourceReadArgument")
        if file_hash(self.original_ifc)!=self.source_sha:
            return self._answer_error("OriginalSourceChanged")
        return {
            "status":"ok","xml":self.current_xml.decode("utf8"),
            "current_xml_sha256":sha256(self.current_xml).hexdigest(),
            "original_source_sha256":self.source_sha,
            "original_author_score":None,
        }

    def _front(self,name:str,arguments:dict)->dict|None:
        if self.calls_used>=MAX_CALLS:
            return self._answer_error("ToolBudgetExhausted")
        self.calls_used+=1
        if name=="read_building_xml":
            return self._read(arguments)
        if file_hash(self.original_ifc)!=self.source_sha:
            return self._answer_error("OriginalSourceChanged")
        return None


class _Declarative059(_Base059):
    mode:str=""

    def __init__(self,source_ifc:Path,folder:Path):
        super().__init__(source_ifc,folder)
        if self.mode not in ("FULL","MANAGED"):
            raise Topo18Native059Error("Invalid D representation")

    @property
    def tools(self)->list[dict]:
        return [READ_TOOL,FULL_TOOL if self.mode=="FULL" else COMPACT_TOOL]

    def call(self,name:str,arguments:dict)->dict:
        front=self._front(name,arguments)
        if front is not None:
            return front
        expected="submit_building_xml" if self.mode=="FULL" else "submit_managed_final_state"
        if name!=expected:
            return self._answer_error("WrongDRepresentationTool")
        if (not isinstance(arguments,dict) or set(arguments)!={"xml_text"}
            or not isinstance(arguments["xml_text"],str)):
            return self._answer_error("InvalidCompleteFinalStateArguments")
        try:
            payload=arguments["xml_text"].encode("utf8","strict")
            if self.mode=="MANAGED":
                if not 0<len(payload)<=MAX_COMPACT:
                    return self._answer_error("InvalidCompactFinalStateLength")
                full,guid=restore_compact_final_state_v059(
                    self.original_ifc,payload,source_sha=self.source_sha)
            else:
                if not 0<len(payload)<=MAX_XML:
                    return self._answer_error("InvalidFullFinalStateLength")
                full=payload
                guid=parse_full_final_state_v059(
                    self.original_ifc,full,source_sha=self.source_sha)
            if self.output_ifc is not None and full==self.current_xml:
                return self._answer_error("ExactFinalStateReplayRejected")
        except Exception:
            return self._answer_error("InvalidCompleteFinalState")
        self.submissions+=1
        attempt=self.folder/f"attempt_{self.submissions:03d}"
        attempt.mkdir(exist_ok=False)
        candidate=attempt/"candidate_original_native.ifc"
        try:
            compile_space_deletion_v059(
                self.original_ifc,candidate,
                source_sha=self.source_sha,absent_guid=guid)
            inspected=native_space_delete_scope_v059(
                self.original_ifc,candidate,source_sha=self.source_sha)
            if inspected["status"]!="V059_SOURCE_ONLY_ORIGINAL_SPACE_NATIVE_SCOPE_AND_SCHEMA_PASS":
                raise Topo18Native059Error("Source-native scope validation rejected")
            self.output_ifc=candidate
            self.current_xml=full
            return {
                "status":"ok","native_ifc_committed":True,
                "native_ifc_sha256":inspected["candidate_sha256"],
                "current_xml_sha256":sha256(full).hexdigest(),
                "representation":("D_COMPLETE_XML_V059" if self.mode=="FULL"
                                  else "D_MANAGED_FINAL_STATE_V059"),
                "complete_original_three_room_roster":True,
                "introduced_schema_errors":0,
                "independent_original_native_ifc_scope_oracle":"PASS",
                "source_entire_ifc_unchanged":True,
                "original_author_score":None,
            }
        except Exception:
            if candidate.exists():
                candidate.unlink()
            return self._answer_error("NativeScopeOrSchemaRejected")


class DirectFullState059(_Declarative059):
    mode="FULL"


class DirectManagedFinalState059(_Declarative059):
    mode="MANAGED"


class LiveDockerPython059(_Base059):
    def __init__(self,source_ifc:Path,folder:Path):
        super().__init__(source_ifc,folder)
        self.executor=DockerIFCExecutor()
        if type(self.executor) is not DockerIFCExecutor:
            raise Topo18Native059Error("Only exact pinned Docker executor allowed")

    @property
    def tools(self)->list[dict]:
        return [READ_TOOL,PYTHON_TOOL]

    def call(self,name:str,arguments:dict)->dict:
        front=self._front(name,arguments)
        if front is not None:
            return front
        if name!="execute_ifc_code":
            return self._answer_error("WrongIRepresentationTool")
        if (not isinstance(arguments,dict) or set(arguments)!={"code"}
            or not isinstance(arguments["code"],str)):
            return self._answer_error("InvalidPythonArguments")
        try:
            code=arguments["code"].encode("utf8","strict")
        except UnicodeEncodeError:
            return self._answer_error("InvalidPythonEncoding")
        if not 0<len(code)<=MAX_CODE_BYTES:
            return self._answer_error("InvalidPythonCodeLength")
        admission=live_pinned_local_runtime_admission_v052()
        if admission["status"]!="RUNTIME_ADMITTED":
            return {
                **self._answer_error("BLOCKED_RUNTIME"),
                "reason":admission["reason"],
                "actual_python_executed":False,
            }
        self.submissions+=1
        attempt=self.folder/f"call_{self.calls_used:03d}"
        attempt.mkdir(exist_ok=False)
        candidate=attempt/"current.ifc"
        shutil.copyfile(self.output_ifc or self.original_ifc,candidate)
        try:
            executed=self.executor.run(attempt,arguments["code"])
            if not (isinstance(executed,dict)
                    and executed.get("status")=="ok"
                    and executed.get("committed") is True
                    and executed.get("backend")=="linux_docker_sandbox"
                    and candidate.is_file() and not candidate.is_symlink()):
                raise Topo18Native059Error("Real Docker commit/attestation refused")
            native=native_space_delete_scope_v059(
                self.original_ifc,candidate,source_sha=self.source_sha)
            if native["status"]!="V059_SOURCE_ONLY_ORIGINAL_SPACE_NATIVE_SCOPE_AND_SCHEMA_PASS":
                raise Topo18Native059Error("Native scope refused")
            if self.output_ifc is not None and file_hash(candidate)==file_hash(self.output_ifc):
                raise Topo18Native059Error("Previous identical native state replay")
            self.output_ifc=candidate
            return {
                "status":"ok","native_ifc_committed":True,
                "native_ifc_sha256":native["candidate_sha256"],
                "python_execution_attested":True,
                "actual_linux_sandbox_backend":executed["backend"],
                "local_pinned_image_sha256":PINNED_DOCKER_IMAGE,
                "independent_original_native_ifc_scope_oracle":"PASS",
                "introduced_schema_errors":0,
                "original_author_score":None,
                "result":executed.get("result"),
            }
        except Exception:
            if candidate.exists():
                candidate.unlink()
            return {
                **self._answer_error("NativeWorkerOrScopeRejected"),
                "python_execution_attested":False,
            }
