"""v0.62 original IFC4X3 Wall source-native full D, managed D, Docker I.

All three model-facing reads share byte-identical source original XML.
FULL and compact D submit original eight-wall COMPLETE final physical lengths
(not typed ops/patches), compile trusted source-bound native geometry.
I executes arbitrary IfcOpenShell Python in genuine isolated pinned local
Linux Docker; independent whole IFC native scope/schema gates all three.

This source-specific validator is narrow: only one original unconnected
SweptSolid Wall is editable, which is an explicit limitation for D/I parity.
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
from tools.bibimbap_v062_topology12_native import (
    SOURCE_SHA,TASK,MAX_XML,MAX_COMPACT,MAX_CALLS,
    Topology12Native062Error,_source,
    full_source_state_v062,parse_full_final_state_v062,
    restore_compact_final_state_v062,
    compile_wall_shortening_v062,
    independent_wall_native_scope_v062,
)


def _tool(name:str,description:str,arg:str)->dict:
    return {
        "type":"function",
        "name":name,
        "description":description,
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
    "Return original native IFC4X3/mm immutable source Wall/Slab/Column/Space "
    "products, original world-metre physical bbox, Wall Axis curve length, "
    "body shape class and connected path relationships. All model arms "
    "read the same initial original complete source BuildingState XML, "
    "or the last accepted declarative state for D.",
    "query",
)
FULL_TOOL=_tool(
    "submit_building_xml",
    "Submit the COMPLETE v0.62 BuildingState final-state XML: unchanged "
    "source IFC SHA/native schema/world mesh/product/relationship subtree "
    "and ALL EIGHT source Wall GUIDs with their absolute finalAxisLengthM. "
    "Only the source-native unconnected SweptSolid Wall length may decrease; "
    "other source walls cannot be edited by this strict source-specific "
    "compiler. Never submit edit opcodes, typed plans, patches or Python.",
    "xml_text",
)
COMPACT_TOOL=_tool(
    "submit_managed_final_state",
    "Submit COMPLETE v0.62 ManagedFinalState all-eight source Wall "
    "original GUIDs and absolute finalAxisLengthM (metres), anchored "
    "to immutable original native IFC and full source XML SHA256. "
    "No command, patch, implicit/missing row or code. The trusted source "
    "only host reattaches full immutable source and independently checks "
    "native IFC physical geometry and schema before any commit.",
    "xml_text",
)
PYTHON_TOOL=_tool(
    "execute_ifc_code",
    "Execute unrestricted native Python/IfcOpenShell on source IFC4X3 "
    "inside pinned nonroot/net-none/read-only/caps-drop isolated Linux "
    "Docker. Must explicitly call commit(). Independent source-native "
    "IFC scope/schema checker admits only shortening of original isolated "
    "SweptSolid Wall axis and body physical profile, with all non-target "
    "STEP/geometry/connection records preserved.",
    "code",
)


class _Base062:
    def __init__(self,source_ifc:Path,folder:Path):
        self.source_ifc=Path(source_ifc)
        _source(self.source_ifc,source_sha=SOURCE_SHA)
        self.source_sha=SOURCE_SHA
        self.task_id=TASK
        self.folder=Path(folder)
        if self.folder.exists() or self.folder.is_symlink():
            raise Topology12Native062Error("Fresh original IFC output folder required")
        self.folder.mkdir(parents=True)
        self.source_xml=full_source_state_v062(
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
            "status":"error",
            "error_type":reason,
            "native_ifc_committed":False,
            "last_valid_ifc_preserved":True,
            "last_valid_xml_preserved":True,
            "current_xml_sha256":sha256(self.current_xml).hexdigest(),
            "original_author_score":None,
        }

    def _front(self,name:str,args:dict):
        if self.calls_used>=MAX_CALLS:
            return self._error("ToolBudgetExhausted")
        self.calls_used+=1
        if file_hash(self.source_ifc)!=SOURCE_SHA:
            return self._error("OriginalSourceIFCHashMismatch")
        if name!="read_building_xml":
            return None
        if (not isinstance(args,dict)
            or set(args)!={"query"}
            or not isinstance(args["query"],str)
            or args["query"] not in ("","source","building")):
            return self._error("InvalidOriginalSourceReadArguments")
        return {
            "status":"ok",
            "xml":self.current_xml.decode("utf8"),
            "current_xml_sha256":sha256(self.current_xml).hexdigest(),
            "original_source_sha256":SOURCE_SHA,
            "original_author_score":None,
        }


class _D062(_Base062):
    mode=""

    @property
    def tools(self)->list[dict]:
        return [READ_TOOL,FULL_TOOL if self.mode=="FULL" else COMPACT_TOOL]

    def call(self,name:str,arguments:dict)->dict:
        front=self._front(name,arguments)
        if front is not None:
            return front
        valid=("submit_building_xml"
               if self.mode=="FULL" else "submit_managed_final_state")
        if name!=valid:
            return self._error("WrongDeclarativeFinalStateTool")
        if (not isinstance(arguments,dict)
            or set(arguments)!={"xml_text"}
            or not isinstance(arguments["xml_text"],str)):
            return self._error("InvalidCompleteFinalStateArguments")
        try:
            xml=arguments["xml_text"].encode("utf8","strict")
            if self.mode=="FULL":
                if not 0<len(xml)<=MAX_XML:
                    return self._error("InvalidCompleteOriginalXMLSize")
                whole=xml
                target=parse_full_final_state_v062(
                    self.source_ifc,whole,source_sha=SOURCE_SHA)
            else:
                if not 0<len(xml)<=MAX_COMPACT:
                    return self._error("InvalidManagedStateXMLSize")
                whole,target=restore_compact_final_state_v062(
                    self.source_ifc,xml,source_sha=SOURCE_SHA)
            if self.output_ifc is not None and whole==self.current_xml:
                return self._error("ExactFinalStateReplayRejected")
        except Exception:
            return self._error("InvalidCompleteOriginalWallFinalState")
        self.submissions+=1
        work=self.folder/f"attempt_{self.submissions:03d}"
        work.mkdir(exist_ok=False)
        candidate=work/"candidate_original_wall.ifc"
        try:
            compile_wall_shortening_v062(
                self.source_ifc,candidate,source_sha=SOURCE_SHA,target=target)
            verdict=independent_wall_native_scope_v062(
                self.source_ifc,candidate,source_sha=SOURCE_SHA)
            if verdict["status"]!="V062_ORIGINAL_ONE_UNCONNECTED_WALL_SHORTENED_NATIVE_SCOPE_SCHEMA_PASS":
                raise Topology12Native062Error("Independent native gate rejected")
            self.output_ifc=candidate
            self.current_xml=whole
            return {
                "status":"ok",
                "native_ifc_committed":True,
                "native_ifc_sha256":verdict["candidate_native_IFC_file_SHA256"],
                "current_xml_sha256":sha256(whole).hexdigest(),
                "representation":("D_COMPLETE_XML_V062"
                                  if self.mode=="FULL" else
                                  "D_MANAGED_FINAL_STATE_V062"),
                "complete_source_IfWall_roster":8,
                "actual_native_original_wall_shortening_m":verdict[
                    "actual_native_shortening_m"],
                "original_wall_world_center_preserved":True,
                "off_target_native_entity_and_connections_preserved":True,
                "introduced_original_IFC_schema_errors":0,
                "original_author_score":None,
            }
        except Exception:
            if candidate.exists():
                candidate.unlink()
            return self._error("NativeWallGeometryOrSchemaRejected")


class DirectFullState062(_D062):
    mode="FULL"


class DirectManagedState062(_D062):
    mode="MANAGED"


class LiveDockerPython062(_Base062):
    def __init__(self,source_ifc:Path,folder:Path):
        super().__init__(source_ifc,folder)
        self.executor=DockerIFCExecutor()
        if type(self.executor) is not DockerIFCExecutor:
            raise Topology12Native062Error("Pinned local genuine Docker executor required")

    @property
    def tools(self):
        return [READ_TOOL,PYTHON_TOOL]

    def call(self,name:str,arguments:dict)->dict:
        front=self._front(name,arguments)
        if front is not None:
            return front
        if name!="execute_ifc_code":
            return self._error("WrongNativePythonTool")
        if (not isinstance(arguments,dict)
            or set(arguments)!={"code"}
            or not isinstance(arguments["code"],str)):
            return self._error("InvalidNativePythonArguments")
        try:
            code=arguments["code"].encode("utf8","strict")
        except UnicodeEncodeError:
            return self._error("InvalidNativePythonEncoding")
        if not 0<len(code)<=MAX_CODE_BYTES:
            return self._error("InvalidNativePythonSize")
        preflight=live_pinned_local_runtime_admission_v052()
        if preflight["status"]!="RUNTIME_ADMITTED":
            return {
                **self._error("BLOCKED_RUNTIME"),
                "reason":preflight["reason"],
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
                raise Topology12Native062Error("Genuine Docker worker execution not attested")
            verdict=independent_wall_native_scope_v062(
                self.source_ifc,candidate,source_sha=SOURCE_SHA)
            if verdict["status"]!="V062_ORIGINAL_ONE_UNCONNECTED_WALL_SHORTENED_NATIVE_SCOPE_SCHEMA_PASS":
                raise Topology12Native062Error("Original wall source scope/schema rejected")
            if self.output_ifc is not None and file_hash(candidate)==file_hash(self.output_ifc):
                raise Topology12Native062Error("Native exact no-op rejected")
            self.output_ifc=candidate
            return {
                "status":"ok",
                "native_ifc_committed":True,
                "native_ifc_sha256":verdict["candidate_native_IFC_file_SHA256"],
                "real_pinned_Docker_python_executed":True,
                "python_execution_attested":True,
                "actual_linux_sandbox_backend":observed["backend"],
                "local_pinned_image_sha256":PINNED_DOCKER_IMAGE,
                "actual_native_original_wall_shortening_m":verdict[
                    "actual_native_shortening_m"],
                "off_target_native_entity_and_connections_preserved":True,
                "introduced_original_IFC_schema_errors":0,
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
