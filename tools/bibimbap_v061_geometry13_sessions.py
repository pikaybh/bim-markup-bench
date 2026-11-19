"""v0.61 actual original-source native D full, D complete-managed and Docker I.

An explicit and source-sha-pinned one-assembly absolute world-X final state
is compiled to actual native IFC4X3. Genuine general Python executes only
in an attested isolated pinned local Linux Docker worker. Both must pass
the SAME task-native source-only root/geometry/schema admission. Author
original scorer and public-question targets never enter model-facing code.
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
from tools.bibimbap_v061_geometry13_native import (
    SOURCE_SHA,TASK,MAX_XML,MAX_COMPACT,MAX_CALLS,
    Geometry13Native061Error,_source,
    full_source_final_state_v061,
    parse_complete_final_state_v061,
    restore_compact_final_state_v061,
    compile_group_move_v061,
    independent_assembly_world_scope_v061,
)


def _tool(name:str,desc:str,arg:str)->dict:
    return {
        "type":"function","name":name,"description":desc,
        "parameters":{
            "type":"object",
            "properties":{arg:{"type":"string"}},
            "required":[arg],
            "additionalProperties":False,
        },
        "strict":True,
    }


READ_TOOL=_tool(
    "read_building_xml",
    "Return the exact immutable original IFC4X3/mm source World Mesh "
    "description and all ten original Window/Opening/detail proxy positions "
    "in metres, or latest accepted complete declarative state. The exact "
    "initial read XML is common to all D/I original source arms.",
    "query",
)
FULL_TOOL=_tool(
    "submit_building_xml",
    "Submit COMPLETE v0.61 source-anchored BuildingState XML including the "
    "unchanged original native product/shape/host source subtree and ALL "
    "ten original Window, Opening and detail Proxy elements with absolute "
    "finalWorldMinXM (metres). Do not submit a command/patch/code. Exactly "
    "one native physical Window assembly with its hosted Opening and all "
    "three detail proxies may have a consistent bounded nonzero world X "
    "position change. Every other original source product stays unchanged.",
    "xml_text",
)
COMPACT_TOOL=_tool(
    "submit_managed_final_state",
    "Submit COMPLETE v0.61 managed final-state XML: source original IFC SHA, "
    "complete source BuildingState SHA and all ten original Window/Opening/"
    "Proxy GUIDs and their absolute finalWorldMinXM (metres), every GUID "
    "explicitly present. Trusted host reattaches complete immutable original "
    "source and compiles IFC only after independent scope/schema admission. "
    "No typed edit plan, implicit missing elements or Python in XML.",
    "xml_text",
)
PYTHON_TOOL=_tool(
    "execute_ifc_code",
    "Run unrestricted general Python/IfcOpenShell on an independent clone "
    "of the real original IFC4X3 inside the pinned isolated Linux Docker "
    "sandbox. Model must explicitly commit(). Correct source-native "
    "Window+host Opening+Proxy geometry and IFC schema/scope validation "
    "are independently applied before promoting any native IFC candidate.",
    "code",
)


class _Base061:
    def __init__(self,source_ifc:Path,folder:Path):
        self.source_ifc=Path(source_ifc)
        _source(self.source_ifc,source_sha=SOURCE_SHA)
        self.source_sha=SOURCE_SHA
        self.task_id=TASK
        self.folder=Path(folder)
        if self.folder.exists() or self.folder.is_symlink():
            raise Geometry13Native061Error("New original trial output folder required")
        self.folder.mkdir(parents=True)
        self.source_xml=full_source_final_state_v061(
            self.source_ifc,source_sha=SOURCE_SHA)
        self.current_xml=self.source_xml
        self.calls_used=0
        self.submissions=0
        self.output_ifc:Path|None=None

    @property
    def tools(self)->list[dict]:
        raise NotImplementedError

    def _error(self,reason:str)->dict:
        return {
            "status":"error","error_type":reason,
            "native_ifc_committed":False,
            "last_valid_ifc_preserved":True,
            "last_valid_xml_preserved":True,
            "current_xml_sha256":sha256(self.current_xml).hexdigest(),
            "original_author_score":None,
        }

    def _first(self,name:str,args:dict):
        if self.calls_used>=MAX_CALLS:
            return self._error("ToolBudgetExhausted")
        self.calls_used+=1
        if file_hash(self.source_ifc)!=SOURCE_SHA:
            return self._error("SourceIFCHashMismatch")
        if name!="read_building_xml":
            return None
        if (not isinstance(args,dict) or set(args)!={"query"}
            or not isinstance(args["query"],str)
            or args["query"] not in ("","source","building")):
            return self._error("InvalidReadSourceArguments")
        return {
            "status":"ok",
            "xml":self.current_xml.decode("utf8"),
            "current_xml_sha256":sha256(self.current_xml).hexdigest(),
            "original_source_sha256":SOURCE_SHA,
            "original_author_score":None,
        }


class _D061(_Base061):
    mode=""

    @property
    def tools(self):
        return [READ_TOOL,FULL_TOOL if self.mode=="FULL" else COMPACT_TOOL]

    def call(self,name:str,arguments:dict):
        front=self._first(name,arguments)
        if front is not None:
            return front
        valid_name=("submit_building_xml"
                    if self.mode=="FULL" else
                    "submit_managed_final_state")
        if name!=valid_name:
            return self._error("WrongDeclarativeTool")
        if (not isinstance(arguments,dict)
            or set(arguments)!={"xml_text"}
            or not isinstance(arguments["xml_text"],str)):
            return self._error("InvalidCompleteFinalStateArguments")
        try:
            xml=arguments["xml_text"].encode("utf8","strict")
            if self.mode=="FULL":
                if not 0<len(xml)<=MAX_XML:
                    return self._error("InvalidFullXMLSize")
                whole=xml
                target=parse_complete_final_state_v061(
                    self.source_ifc,whole,source_sha=SOURCE_SHA)
            else:
                if not 0<len(xml)<=MAX_COMPACT:
                    return self._error("InvalidCompleteManagedXMLSize")
                whole,target=restore_compact_final_state_v061(
                    self.source_ifc,xml,source_sha=SOURCE_SHA)
            if self.output_ifc is not None and whole==self.current_xml:
                return self._error("IdenticalStateReplayRejected")
        except Exception:
            return self._error("InvalidCompleteSourceFinalState")
        self.submissions+=1
        work=self.folder/f"attempt_{self.submissions:03d}"
        work.mkdir(exist_ok=False)
        native=work/"candidate_original_native.ifc"
        try:
            compile_group_move_v061(
                self.source_ifc,native,source_sha=SOURCE_SHA,target=target)
            verdict=independent_assembly_world_scope_v061(
                self.source_ifc,native,source_sha=SOURCE_SHA)
            if verdict["status"]!="V061_TWO_WINDOW_SOURCE_ONE_ASSEMBLY_NATIVE_MOVE_SCOPE_PASS":
                raise Geometry13Native061Error("Independent original scope refused")
            self.output_ifc=native
            self.current_xml=whole
            return {
                "status":"ok","native_ifc_committed":True,
                "native_ifc_sha256":verdict["native_candidate_file_sha256"],
                "current_xml_sha256":sha256(whole).hexdigest(),
                "representation":("D_COMPLETE_XML_V061"
                                  if self.mode=="FULL" else
                                  "D_MANAGED_FINAL_STATE_V061"),
                "complete_source_managed_element_roster":10,
                "five_original_native_products_moved_as_one_assembly":True,
                "source_world_X_shift_metres_magnitude":verdict[
                    "source_X_delta_magnitude"],
                "source_world_X_shift_direction":verdict[
                    "source_x_direction"],
                "introduced_IFC_schema_errors":0,
                "original_author_score":None,
            }
        except Exception:
            if native.exists():
                native.unlink()
            return self._error("NativeGeometryScopeOrSchemaRejected")


class DirectFullState061(_D061):
    mode="FULL"


class DirectManagedState061(_D061):
    mode="MANAGED"


class LiveDockerPython061(_Base061):
    def __init__(self,source_ifc:Path,folder:Path):
        super().__init__(source_ifc,folder)
        self.executor=DockerIFCExecutor()
        if type(self.executor) is not DockerIFCExecutor:
            raise Geometry13Native061Error("Pinned local Docker executor type required")

    @property
    def tools(self):
        return [READ_TOOL,PYTHON_TOOL]

    def call(self,name:str,arguments:dict):
        front=self._first(name,arguments)
        if front is not None:
            return front
        if name!="execute_ifc_code":
            return self._error("WrongNativePythonTool")
        if (not isinstance(arguments,dict) or set(arguments)!={"code"}
            or not isinstance(arguments["code"],str)):
            return self._error("InvalidNativePythonArguments")
        try:
            data=arguments["code"].encode("utf8","strict")
        except UnicodeEncodeError:
            return self._error("InvalidNativePythonEncoding")
        if not 0<len(data)<=MAX_CODE_BYTES:
            return self._error("InvalidNativePythonSize")
        admission=live_pinned_local_runtime_admission_v052()
        if admission["status"]!="RUNTIME_ADMITTED":
            return {
                **self._error("BLOCKED_RUNTIME"),
                "reason":admission["reason"],
                "actual_python_executed":False,
            }
        self.submissions+=1
        work=self.folder/f"call_{self.calls_used:03d}"
        work.mkdir(exist_ok=False)
        candidate=work/"current.ifc"
        shutil.copyfile(self.output_ifc or self.source_ifc,candidate)
        try:
            observed=self.executor.run(work,arguments["code"])
            if not (isinstance(observed,dict)
                    and observed.get("status")=="ok"
                    and observed.get("committed") is True
                    and observed.get("backend")=="linux_docker_sandbox"
                    and candidate.is_file() and not candidate.is_symlink()):
                raise Geometry13Native061Error("Genuine Docker commit/attestation refused")
            verdict=independent_assembly_world_scope_v061(
                self.source_ifc,candidate,source_sha=SOURCE_SHA)
            if verdict["status"]!="V061_TWO_WINDOW_SOURCE_ONE_ASSEMBLY_NATIVE_MOVE_SCOPE_PASS":
                raise Geometry13Native061Error("Independent real IFC scope refused")
            if self.output_ifc and file_hash(candidate)==file_hash(self.output_ifc):
                raise Geometry13Native061Error("No-op native replay rejected")
            self.output_ifc=candidate
            return {
                "status":"ok","native_ifc_committed":True,
                "native_ifc_sha256":verdict["native_candidate_file_sha256"],
                "real_pinned_Docker_python_executed":True,
                "python_execution_attested":True,
                "actual_linux_sandbox_backend":observed["backend"],
                "local_pinned_image_sha256":PINNED_DOCKER_IMAGE,
                "five_original_native_products_moved_as_one_assembly":True,
                "source_world_X_shift_metres_magnitude":verdict[
                    "source_X_delta_magnitude"],
                "source_world_X_shift_direction":verdict[
                    "source_x_direction"],
                "introduced_IFC_schema_errors":0,
                "original_author_score":None,
                "result":observed.get("result"),
            }
        except Exception:
            if candidate.exists():
                candidate.unlink()
            return {
                **self._error("NativeWorkerOrScopeRejected"),
                "python_execution_attested":False,
            }
