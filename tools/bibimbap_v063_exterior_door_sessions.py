"""Three actual original IFC4X3 Door+Opening D/I editing sessions.

D_FULL: complete immutable original BuildingState + 7 original Wall final
roster + final Door/Opening products with world-absolute geometry/IFC
relations. D_MANAGED: complete original Wall roster and exactly two new
final products, re-attached into whole immutable source. I_NATIVE:
genuine pinned isolated Linux Docker Python on cloned original IFC4X3.
Common initial read and independent original native actual CSG cut gate.
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
from tools.bibimbap_v063_exterior_door_native import (
    SOURCE_SHA,TASK,MAX_XML,MAX_COMPACT,MAX_CALLS,
    OriginalDoorNative063Error,source_ifc,
    initial_full_source_v063,parse_full_final_v063,
    restore_managed_final_v063,
    compile_real_original_IFC_v063,
    independent_real_original_door_scope_v063,
)


def _tool(name:str,desc:str,key:str)->dict:
    return {
        "type":"function","name":name,"description":desc,
        "parameters":{"type":"object",
                      "properties":{key:{"type":"string"}},
                      "required":[key],"additionalProperties":False},
        "strict":True,
    }


READ_TOOL=_tool(
    "read_building_xml",
    "Read the SAME exact SHA-pinned original IFC4X3/mm building source "
    "including all seven original Walls and two Slabs, world bounding "
    "boxes in metres, wall axis and footprint envelope; no original "
    "IfcDoor, IfcOpeningElement, or IfcSpace. D repeat reads show last "
    "accepted complete final XML, while I repeat reads stay source.",
    "query",
)
FULL_TOOL=_tool(
    "submit_building_xml",
    "Submit the COMPLETE source-anchored original BuildingState final XML: "
    "unchanged original IFC geometry/products/envelope subtree, all "
    "SEVEN original Wall GUID final-state rows, plus exactly ONE new "
    "IfcOpeningElement and ONE new IfcDoor with new IFC GUIDs, host/"
    "fills relations and explicit absolute world-metre 3D boxes. "
    "The new Opening must pierce the chosen source Wall FULLY across "
    "its thickness. Native Door panel must lie inside Opening and be "
    "spatially contained in original source storey. No edit commands, "
    "patches or model Python disguised as XML. Public exterior-wall "
    "correctness is evaluated separately.",
    "xml_text",
)
MANAGED_TOOL=_tool(
    "submit_managed_final_state",
    "Submit COMPLETE managed final-state XML: original IFC SHA, full "
    "original source XML SHA, all SEVEN original Wall final-state rows, "
    "and explicit new Door and Opening absolute world geometry, host/"
    "filling IDs and unique IFC GUIDs. Trusted host reconstructs the "
    "ENTIRE immutable source BuildingState XML and independently checks "
    "actual original IFC4X3 CSG full-thickness Wall cut/relations/schema "
    "before commit. No partial lists, typed operation plans or Python.",
    "xml_text",
)
PYTHON_TOOL=_tool(
    "execute_ifc_code",
    "Execute general unrestricted Python/IfcOpenShell on exact original "
    "IFC4X3 native source clone inside attested OS-isolated pinned local "
    "Linux Docker (nonroot, no network, read-only root, cap-drop, bounded "
    "resources/mounts). Must commit(). Independently validate exact "
    "source-root preservation, real Wall CSG solid cut-through volume, "
    "new Door/Opening/host fills/voids geometry/relations, original "
    "storey containment and zero newly introduced schema findings.",
    "code",
)


class _Base063:
    def __init__(self,original:Path,folder:Path):
        self.source_ifc=Path(original)
        source_ifc(self.source_ifc,source_sha=SOURCE_SHA)
        self.task_id=TASK
        self.folder=Path(folder)
        if self.folder.exists() or self.folder.is_symlink():
            raise OriginalDoorNative063Error(
                "Fresh independent native original IFC output folder required")
        self.folder.mkdir(parents=True)
        self.source_xml=initial_full_source_v063(
            self.source_ifc,source_sha=SOURCE_SHA)
        self.current_xml=self.source_xml
        self.output_ifc:Path|None=None
        self.calls_used=0
        self.submissions=0

    def _error(self,reason:str)->dict:
        return {
            "status":"error","error_type":reason,
            "native_ifc_committed":False,
            "last_good_original_IFC_preserved":True,
            "last_good_original_XML_preserved":True,
            "current_xml_sha256":sha256(self.current_xml).hexdigest(),
            "original_author_score":None,
        }

    def _front(self,name:str,args:dict):
        if self.calls_used>=MAX_CALLS:
            return self._error("ToolBudgetExhausted")
        self.calls_used+=1
        if file_hash(self.source_ifc)!=SOURCE_SHA:
            return self._error("OriginalSourceIFCSHAMismatch")
        if name!="read_building_xml":
            return None
        if (not isinstance(args,dict)
            or set(args)!={"query"}
            or not isinstance(args["query"],str)
            or args["query"] not in ("","source","building")):
            return self._error("InvalidReadOriginalSourceArguments")
        return {
            "status":"ok",
            "xml":self.current_xml.decode("utf8"),
            "current_xml_sha256":sha256(self.current_xml).hexdigest(),
            "original_IFC_source_SHA256":SOURCE_SHA,
            "original_author_score":None,
        }

    @property
    def tools(self):
        raise NotImplementedError


class _D063(_Base063):
    mode=""

    @property
    def tools(self):
        return [READ_TOOL,FULL_TOOL if self.mode=="FULL" else MANAGED_TOOL]

    def call(self,name:str,arguments:dict):
        front=self._front(name,arguments)
        if front is not None:
            return front
        valid=("submit_building_xml" if self.mode=="FULL"
               else "submit_managed_final_state")
        if name!=valid:
            return self._error("WrongDeclarativeFinalStateTool")
        if (not isinstance(arguments,dict)
            or set(arguments)!={"xml_text"}
            or not isinstance(arguments["xml_text"],str)):
            return self._error("InvalidOriginalCompleteFinalStateArguments")
        try:
            raw=arguments["xml_text"].encode("utf8","strict")
            if self.mode=="FULL":
                if not 0<len(raw)<=MAX_XML:
                    return self._error("InvalidCompleteOriginalXMLSize")
                whole=raw
                target=parse_full_final_v063(
                    self.source_ifc,whole,source_sha=SOURCE_SHA)
            else:
                if not 0<len(raw)<=MAX_COMPACT:
                    return self._error("InvalidCompleteManagedXMLSize")
                whole,target=restore_managed_final_v063(
                    self.source_ifc,raw,source_sha=SOURCE_SHA)
            if self.output_ifc is not None and whole==self.current_xml:
                return self._error("ExactFinalStateReplayRejected")
        except Exception:
            return self._error("InvalidCompleteOriginalDoorOpeningFinalState")
        self.submissions+=1
        outfolder=self.folder/f"attempt_{self.submissions:03d}"
        outfolder.mkdir(exist_ok=False)
        out=outfolder/"original_native_ifc4x3_door.ifc"
        try:
            compile_real_original_IFC_v063(
                self.source_ifc,out,source_sha=SOURCE_SHA,state=target)
            grade=independent_real_original_door_scope_v063(
                self.source_ifc,out,source_sha=SOURCE_SHA)
            if grade["status"]!="V063_ORIGINAL_CSG_DOOR_OPENING_NATIVE_SCOPE_AND_SCHEMA_PASS":
                raise OriginalDoorNative063Error("Original source CSG gate blocked")
            self.output_ifc=out
            self.current_xml=whole
            return {
                "status":"ok","native_ifc_committed":True,
                "representation":("D_COMPLETE_XML_V063" if self.mode=="FULL"
                                  else "D_MANAGED_FINAL_STATE_V063"),
                "native_ifc_sha256":grade["original_IFC_actual_candidate_file_SHA256"],
                "current_xml_sha256":sha256(whole).hexdigest(),
                "full_original_7_Wall_final_state_roster":7,
                "actual_native_IfcDoor_added":1,
                "actual_native_IfcOpeningElement_added":1,
                "source_original_Wall_CSG_full_thickness_cut":True,
                "original_source_entities_preserved":grade[
                    "original_source_STEP_entities_unchanged"],
                "original_IFC4X3_schema_error_delta":0,
                "original_author_score":None,
            }
        except Exception:
            if out.exists():
                out.unlink()
            return self._error("NativeOriginalCSGDoorScopeOrSchemaRejected")


class DirectFullState063(_D063):
    mode="FULL"


class DirectManagedState063(_D063):
    mode="MANAGED"


class LiveDockerPython063(_Base063):
    def __init__(self,original:Path,folder:Path):
        super().__init__(original,folder)
        self.executor=DockerIFCExecutor()
        if type(self.executor) is not DockerIFCExecutor:
            raise OriginalDoorNative063Error("Real DockerIFCExecutor required")

    @property
    def tools(self):
        return [READ_TOOL,PYTHON_TOOL]

    def call(self,name:str,arguments:dict):
        front=self._front(name,arguments)
        if front is not None:
            return front
        if name!="execute_ifc_code":
            return self._error("WrongNativePythonTool")
        if (not isinstance(arguments,dict) or set(arguments)!={"code"}
            or not isinstance(arguments["code"],str)):
            return self._error("InvalidNativePythonCodeArgument")
        try:
            content=arguments["code"].encode("utf8","strict")
        except UnicodeEncodeError:
            return self._error("InvalidNativePythonEncoding")
        if not 0<len(content)<=MAX_CODE_BYTES:
            return self._error("InvalidNativePythonCodeSize")
        pre=live_pinned_local_runtime_admission_v052()
        if pre["status"]!="RUNTIME_ADMITTED":
            return {
                **self._error("BLOCKED_RUNTIME"),
                "reason":pre["reason"],"actual_python_executed":False,
            }
        self.submissions+=1
        work=self.folder/f"call_{self.calls_used:03d}"
        work.mkdir(exist_ok=False)
        candidate=work/"current.ifc"
        shutil.copyfile(self.output_ifc or self.source_ifc,candidate)
        try:
            result=self.executor.run(work,arguments["code"])
            if not (isinstance(result,dict)
                    and result.get("status")=="ok"
                    and result.get("committed") is True
                    and result.get("backend")=="linux_docker_sandbox"
                    and candidate.is_file() and not candidate.is_symlink()):
                raise OriginalDoorNative063Error(
                    "Real pinned Linux Docker commit not attested")
            grade=independent_real_original_door_scope_v063(
                self.source_ifc,candidate,source_sha=SOURCE_SHA)
            if grade["status"]!="V063_ORIGINAL_CSG_DOOR_OPENING_NATIVE_SCOPE_AND_SCHEMA_PASS":
                raise OriginalDoorNative063Error("Actual IFC failed CSG gate")
            if self.output_ifc is not None and file_hash(candidate)==file_hash(self.output_ifc):
                raise OriginalDoorNative063Error("Actual native no-op replay")
            self.output_ifc=candidate
            return {
                "status":"ok","native_ifc_committed":True,
                "native_ifc_sha256":grade["original_IFC_actual_candidate_file_SHA256"],
                "actual_os_isolated_pinned_Linux_Docker_Python_executed":True,
                "python_execution_attested":True,
                "actual_linux_sandbox_backend":result["backend"],
                "local_pinned_image_sha256":PINNED_DOCKER_IMAGE,
                "actual_native_IfcDoor_added":1,
                "actual_native_IfcOpeningElement_added":1,
                "actual_original_Wall_CSG_full_thickness_cut":True,
                "original_source_entities_preserved":grade[
                    "original_source_STEP_entities_unchanged"],
                "original_IFC4X3_schema_error_delta":0,
                "original_author_score":None,
                "result":result.get("result"),
            }
        except Exception:
            if candidate.exists():
                candidate.unlink()
            return {
                **self._error("NativeDockerWorkerOrCSGScopeRejected"),
                "python_execution_attested":False,
            }
