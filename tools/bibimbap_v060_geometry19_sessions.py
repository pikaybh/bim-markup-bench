"""v0.60 exact-source original native geometry19 genuine D and Docker I sessions.

Both D arms submit complete 7-original-Window GUID final-state declarations,
not XML operation scripts or partial patches; I runs arbitrary Python in
the pinned local OS-isolated Linux Docker/IfcOpenShell environment. The
same independent original native all-entity scope and IFC4X3 schema delta
checker is required before any candidate is promoted. No scorer/GT or
third-party provider import permitted.
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
from tools.bibimbap_v060_geometry19_native import (
    SOURCE_SHA,TASK,MAX_XML_BYTES,MAX_COMPACT_BYTES,MAX_CALLS,
    Geometry19Native060Error,_source,
    source_full_state_v060,parse_full_final_state_v060,
    restore_compact_final_state_v060,
    compile_two_window_removal_v060,
    independent_two_window_native_scope_v060,
)


def tool(name:str,description:str,parameter:str)->dict:
    return {
        "type":"function","name":name,
        "description":description,
        "parameters":{
            "type":"object",
            "properties":{parameter:{"type":"string"}},
            "required":[parameter],"additionalProperties":False,
        },
        "strict":True,
    }


READ_TOOL=tool(
    "read_building_xml",
    "Read original source-native IFC4X3/mm wall/window/opening "
    "geometry and associations. Return original source-anchored full XML "
    "or the latest accepted declarative XML state. Identical initial "
    "read across D complete, D managed and genuine Docker I-native.",
    "query",
)
FULL_TOOL=tool(
    "submit_building_xml",
    "Submit COMPLETE v0.60 BuildingState final XML, retaining exact "
    "immutable original Products/geometry/window-host-opening links and "
    "all seven original IfcWindow rows with present true/false. Exactly "
    "two original windows should be absent in final state. No commands, "
    "patches or missing-window inference. Native IFC admits only after "
    "independent original-source and schema validation.",
    "xml_text",
)
MANAGED_TOOL=tool(
    "submit_managed_final_state",
    "Submit COMPLETE v0.60 ManagedFinalState containing original source "
    "IFC hash, full source XML hash and all seven original Window GUIDs "
    "with present true/false. Trusted source-only host restores immutable "
    "source subtree and compiles actual native IFC after independent "
    "scope/schema verification; not a typed edit plan.",
    "xml_text",
)
PYTHON_TOOL=tool(
    "execute_ifc_code",
    "Run genuine unrestricted Python/IfcOpenShell code on cloned original "
    "IFC4X3 inside the pinned local nonroot, no-network Linux Docker "
    "sandbox. Explicit commit() required. An independent original "
    "native geometry/relationship/schema gate must pass before promotion.",
    "code",
)


class _Base060:
    def __init__(self,original_ifc:Path,folder:Path):
        self.original_ifc=Path(original_ifc)
        _source(self.original_ifc,source_sha=SOURCE_SHA)
        self.source_sha=SOURCE_SHA
        self.task_id=TASK
        self.folder=Path(folder)
        if self.folder.exists() or self.folder.is_symlink():
            raise Geometry19Native060Error("Fresh output folder required")
        self.folder.mkdir(parents=True)
        self.source_xml=source_full_state_v060(
            self.original_ifc,source_sha=SOURCE_SHA)
        self.current_xml=self.source_xml
        self.calls_used=0
        self.submissions=0
        self.output_ifc:Path|None=None

    @property
    def tools(self)->list[dict]:
        raise NotImplementedError

    def _error(self,error_type:str)->dict:
        return {
            "status":"error","error_type":error_type,
            "native_ifc_committed":False,
            "last_valid_ifc_preserved":True,
            "last_valid_xml_preserved":True,
            "current_xml_sha256":sha256(self.current_xml).hexdigest(),
        }

    def _front(self,name:str,arguments:dict)->dict|None:
        if self.calls_used>=MAX_CALLS:
            return self._error("ToolBudgetExhausted")
        self.calls_used+=1
        if file_hash(self.original_ifc)!=SOURCE_SHA:
            return self._error("OriginalSourceChanged")
        if name!="read_building_xml":
            return None
        if (not isinstance(arguments,dict)
            or set(arguments)!={"query"}
            or not isinstance(arguments["query"],str)
            or arguments["query"] not in ("","source","building")):
            return self._error("InvalidSourceReadArguments")
        return {
            "status":"ok",
            "xml":self.current_xml.decode("utf8"),
            "current_xml_sha256":sha256(self.current_xml).hexdigest(),
            "original_source_sha256":SOURCE_SHA,
            "original_author_score":None,
        }


class _D060(_Base060):
    mode=""

    @property
    def tools(self)->list[dict]:
        return [READ_TOOL,FULL_TOOL if self.mode=="FULL" else MANAGED_TOOL]

    def call(self,name:str,arguments:dict)->dict:
        front=self._front(name,arguments)
        if front is not None:
            return front
        expected="submit_building_xml" if self.mode=="FULL" else "submit_managed_final_state"
        if name!=expected:
            return self._error("WrongDeclarativeFinalStateTool")
        if (not isinstance(arguments,dict) or set(arguments)!={"xml_text"}
            or not isinstance(arguments["xml_text"],str)):
            return self._error("InvalidCompleteFinalStateArguments")
        try:
            payload=arguments["xml_text"].encode("utf8","strict")
            if self.mode=="FULL":
                if not 0<len(payload)<=MAX_XML_BYTES:
                    return self._error("InvalidCompleteXMLSize")
                full=payload
                absent=parse_full_final_state_v060(
                    self.original_ifc,full,source_sha=SOURCE_SHA)
            else:
                if not 0<len(payload)<=MAX_COMPACT_BYTES:
                    return self._error("InvalidManagedFinalStateSize")
                full,absent=restore_compact_final_state_v060(
                    self.original_ifc,payload,source_sha=SOURCE_SHA)
            if self.output_ifc is not None and full==self.current_xml:
                return self._error("IdenticalFinalStateReplayRejected")
        except Exception:
            return self._error("InvalidCompleteFinalState")
        self.submissions+=1
        folder=self.folder/f"attempt_{self.submissions:03d}"
        folder.mkdir(exist_ok=False)
        candidate=folder/"candidate_original_native.ifc"
        try:
            compile_two_window_removal_v060(
                self.original_ifc,candidate,
                source_sha=SOURCE_SHA,absent_guids=absent)
            native=independent_two_window_native_scope_v060(
                self.original_ifc,candidate,source_sha=SOURCE_SHA)
            if native["status"]!="V060_SOURCE_NATIVE_TWO_WINDOWS_OPENINGS_SCOPE_AND_SCHEMA_PASS":
                raise Geometry19Native060Error("Independent native gate refused")
            self.output_ifc=candidate
            self.current_xml=full
            return {
                "status":"ok","native_ifc_committed":True,
                "native_ifc_sha256":native["candidate_sha256"],
                "current_xml_sha256":sha256(full).hexdigest(),
                "representation":("D_COMPLETE_XML_V060"
                                  if self.mode=="FULL" else
                                  "D_MANAGED_FINAL_STATE_V060"),
                "complete_original_window_roster":7,
                "removed_native_windows":2,
                "removed_linked_native_openings":2,
                "independent_original_native_ifc_scope_oracle":"PASS",
                "introduced_schema_error_count":0,
                "original_author_score":None,
            }
        except Exception:
            if candidate.exists():
                candidate.unlink()
            return self._error("NativeScopeOrSchemaRejected")


class DirectFullState060(_D060):
    mode="FULL"


class DirectManagedState060(_D060):
    mode="MANAGED"


class LiveDockerPython060(_Base060):
    def __init__(self,original_ifc:Path,folder:Path):
        super().__init__(original_ifc,folder)
        self.executor=DockerIFCExecutor()
        if type(self.executor) is not DockerIFCExecutor:
            raise Geometry19Native060Error("Only genuine DockerIFCExecutor")

    @property
    def tools(self)->list[dict]:
        return [READ_TOOL,PYTHON_TOOL]

    def call(self,name:str,arguments:dict)->dict:
        front=self._front(name,arguments)
        if front is not None:
            return front
        if name!="execute_ifc_code":
            return self._error("WrongNativePythonTool")
        if (not isinstance(arguments,dict) or set(arguments)!={"code"}
            or not isinstance(arguments["code"],str)):
            return self._error("InvalidNativePythonArguments")
        try:
            code=arguments["code"].encode("utf8","strict")
        except UnicodeEncodeError:
            return self._error("InvalidNativePythonEncoding")
        if not 0<len(code)<=MAX_CODE_BYTES:
            return self._error("InvalidNativePythonCodeSize")
        preflight=live_pinned_local_runtime_admission_v052()
        if preflight["status"]!="RUNTIME_ADMITTED":
            return {
                **self._error("BLOCKED_RUNTIME"),
                "reason":preflight["reason"],
                "actual_python_executed":False,
            }
        self.submissions+=1
        folder=self.folder/f"call_{self.calls_used:03d}"
        folder.mkdir(exist_ok=False)
        candidate=folder/"current.ifc"
        shutil.copyfile(self.output_ifc or self.original_ifc,candidate)
        try:
            result=self.executor.run(folder,arguments["code"])
            if not (isinstance(result,dict)
                    and result.get("status")=="ok"
                    and result.get("committed") is True
                    and result.get("backend")=="linux_docker_sandbox"
                    and candidate.is_file() and not candidate.is_symlink()):
                raise Geometry19Native060Error("Docker native execution not attested")
            native=independent_two_window_native_scope_v060(
                self.original_ifc,candidate,source_sha=SOURCE_SHA)
            if native["status"]!="V060_SOURCE_NATIVE_TWO_WINDOWS_OPENINGS_SCOPE_AND_SCHEMA_PASS":
                raise Geometry19Native060Error("Native scope/schema refused")
            if self.output_ifc is not None and file_hash(candidate)==file_hash(self.output_ifc):
                raise Geometry19Native060Error("No-op after prior commit")
            self.output_ifc=candidate
            return {
                "status":"ok","native_ifc_committed":True,
                "native_ifc_sha256":native["candidate_sha256"],
                "removed_native_windows":2,
                "removed_linked_native_openings":2,
                "independent_original_native_ifc_scope_oracle":"PASS",
                "introduced_schema_error_count":0,
                "python_execution_attested":True,
                "actual_linux_sandbox_backend":result["backend"],
                "local_pinned_image_sha256":PINNED_DOCKER_IMAGE,
                "original_author_score":None,
                "result":result.get("result"),
            }
        except Exception:
            if candidate.exists():
                candidate.unlink()
            return {
                **self._error("NativeWorkerOrScopeRejected"),
                "python_execution_attested":False,
            }
