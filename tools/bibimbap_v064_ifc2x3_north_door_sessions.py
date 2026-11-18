"""Original IFC2X3 three-Wall first real D/I native Door+Opening sessions.

Every arm starts with byte-identical source BuildingState XML; D_FULL
requires complete immutable source and three unchanged original Wall
GUID rows, D_MANAGED requires complete managed 3-Wall + two explicit
new product final state, I genuinely runs arbitrary native Python inside
pinned real local Linux Docker. One exact source-only IFC2X3 CSG, Root,
OwnerHistory and zero-new-schema-error gate promotes every candidate.

The original task answer/nearest-north GUID is NOT hardcoded in the host
and the original author grader is NEVER imported here.
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
from tools.bibimbap_v064_ifc2x3_north_door_native import (
    SOURCE_SHA,TASK,MAX_CALLS,MAX_XML,MAX_COMPACT,STATUS,
    OriginalDoorIFC2X3Native064Error,
    source_original_ifc2x3,full_original_state_v064,
    parse_full_final_v064,restore_managed_final_v064,
    compile_native_ifc2x3_door_v064,source_native_ifc2x3_scope_v064,
)


def tool(name,desc,key):
    return {
        "type":"function","name":name,"description":desc,
        "parameters":{"type":"object",
                      "properties":{key:{"type":"string"}},
                      "required":[key],
                      "additionalProperties":False},
        "strict":True,
    }


READ_TOOL=tool(
    "read_building_xml",
    "Read original SHA-pinned IFC2X3 three-wall building state. Original "
    "Wall GUIDs, wall global world-metre bboxes, native IFC schema and "
    "MILLIMETRE project units, and complete managed Wall roster. "
    "Initial XML bytes identical for D_FULL, D_MANAGED and Python I. "
    "D repeat reads return accepted final source state; I repeats source.",
    "query",
)
FULL_TOOL=tool(
    "submit_building_xml",
    "Submit COMPLETE declarative BuildingState XML with entire immutable "
    "original IFC2X3 source products/geometry, ALL THREE original Wall "
    "present=true final rows, ONE new Door and ONE hosted Opening with "
    "explicit new IFC GUIDs, original Wall host and fills IDs, absolute "
    "world-metre 3D bounding boxes. Opening must cut full 0.2m source "
    "Wall thickness, Door fully within it at source ground level, new "
    "Door spatially contained in original storey. Native IFC2X3 "
    "OwnerHistory mandatory. No typed operations, patch, diff, Python.",
    "xml_text",
)
MANAGED_TOOL=tool(
    "submit_managed_final_state",
    "Submit entire smaller 3-original-Wall + explicit 1-new-Door + "
    "1-new-Opening declarative FINAL physical state, pinned to original "
    "IFC2X3 source SHA and complete source BuildingState SHA. Host "
    "reattaches immutable original and validates full native IFC2X3 "
    "scope/CSG/OwnerHistory/schema before commit. No omitted original "
    "rows or typed edit command.",
    "xml_text",
)
PYTHON_TOOL=tool(
    "execute_ifc_code",
    "Execute general Python/IfcOpenShell on original native IFC2X3 source "
    "clone inside actual pinned OS-isolated local Linux Docker (nonroot, "
    "no network, read-only root, cap-drop and resource bounds). Requires "
    "commit(). The EXACT SAME full native source IFC2X3 root/geometry/"
    "CSG-cut/IfcRelVoids/IfcRelFills/OwnerHistory and schema-error-delta "
    "oracle as D_FULL/MANAGED validates it before promotion.",
    "code",
)


class _Base:
    def __init__(self,original:Path,folder:Path):
        self.source_ifc=Path(original)
        source_original_ifc2x3(self.source_ifc,source_sha=SOURCE_SHA)
        self.folder=Path(folder)
        if self.folder.exists() or self.folder.is_symlink():
            raise OriginalDoorIFC2X3Native064Error(
                "Fresh isolated original native IFC2X3 transaction directory required")
        self.folder.mkdir(parents=True)
        self.source_xml=full_original_state_v064(
            self.source_ifc,source_sha=SOURCE_SHA)
        self.current_xml=self.source_xml
        self.output_ifc:Path|None=None
        self.calls_used=0
        self.submissions=0
        self.task_id=TASK

    def _err(self,kind:str):
        return {
            "status":"error","error_type":kind,
            "native_ifc_committed":False,
            "last_good_native_IFC_preserved":True,
            "last_good_original_XML_preserved":True,
            "current_original_XML_SHA256":sha256(self.current_xml).hexdigest(),
            "original_author_score":None,
        }

    def _front(self,name,args):
        if self.calls_used>=MAX_CALLS:
            return self._err("ToolBudgetExhausted")
        self.calls_used+=1
        if file_hash(self.source_ifc)!=SOURCE_SHA:
            return self._err("OriginalIFC2X3SourceSHAChanged")
        if name!="read_building_xml":
            return None
        if (not isinstance(args,dict)
            or set(args)!={"query"}
            or not isinstance(args["query"],str)
            or args["query"] not in ("","source","building")):
            return self._err("BadOriginalReadArguments")
        return {
            "status":"ok","xml":self.current_xml.decode("utf8"),
            "source_IFC_SHA256":SOURCE_SHA,
            "current_XML_SHA256":sha256(self.current_xml).hexdigest(),
            "original_author_score":None,
        }

    @property
    def tools(self):
        raise NotImplementedError


class _D(_Base):
    mode=""

    @property
    def tools(self):
        return [READ_TOOL,FULL_TOOL if self.mode=="FULL" else MANAGED_TOOL]

    def call(self,name,args):
        front=self._front(name,args)
        if front is not None:return front
        expected=("submit_building_xml" if self.mode=="FULL"
                  else "submit_managed_final_state")
        if name!=expected:
            return self._err("WrongDeclarativeFinalStateTool")
        if not isinstance(args,dict) or set(args)!={"xml_text"} or not isinstance(args["xml_text"],str):
            return self._err("MalformedOriginalCompleteFinalStateArguments")
        try:
            submitted=args["xml_text"].encode("utf8","strict")
            if self.mode=="FULL":
                if not 0<len(submitted)<=MAX_XML:
                    return self._err("FullSourceXMLSizeExceeded")
                whole=submitted
                state=parse_full_final_v064(
                    self.source_ifc,whole,source_sha=SOURCE_SHA)
            else:
                if not 0<len(submitted)<=MAX_COMPACT:
                    return self._err("ManagedXMLSizeExceeded")
                whole,state=restore_managed_final_v064(
                    self.source_ifc,submitted,source_sha=SOURCE_SHA)
            if self.output_ifc is not None and whole==self.current_xml:
                return self._err("RepeatedIdenticalFinalStateRejected")
        except Exception:
            return self._err("InvalidCompleteOriginalIFC2X3FinalState")
        self.submissions+=1
        work=self.folder/f"attempt_{self.submissions:03d}"
        work.mkdir(exist_ok=False)
        native=work/"native_original_ifc2x3_door.ifc"
        try:
            compile_native_ifc2x3_door_v064(
                self.source_ifc,native,source_sha=SOURCE_SHA,state=state)
            verdict=source_native_ifc2x3_scope_v064(
                self.source_ifc,native,source_sha=SOURCE_SHA)
            if verdict["status"]!=STATUS:
                raise OriginalDoorIFC2X3Native064Error("Real IFC2X3 scope rejected")
            self.output_ifc=native
            self.current_xml=whole
            return {
                "status":"ok","native_ifc_committed":True,
                "representation":("D_COMPLETE_XML_V064" if self.mode=="FULL"
                                  else "D_MANAGED_FINAL_STATE_V064"),
                "current_XML_SHA256":sha256(whole).hexdigest(),
                "native_IFC2X3_SHA256":verdict["candidate_native_IFC_SHA256"],
                "all_three_source_Wall_roster_preserved":True,
                "new_Door_Opening_count":(1,1),
                "native_original_Wall_full_thickness_CSG_cut_m3":verdict[
                    "native_original_IFC2X3_wall_full_thickness_volume_lost_m3"],
                "original_source_IFC2X3_new_schema_errors":0,
                "original_author_score":None,
            }
        except Exception:
            if native.exists():native.unlink()
            return self._err("NativeIFC2X3DoorScopeOrSchemaRejected")


class DirectFullState064(_D):
    mode="FULL"


class DirectManagedState064(_D):
    mode="MANAGED"


class LiveDockerPython064(_Base):
    def __init__(self,original:Path,folder:Path):
        super().__init__(original,folder)
        self.executor=DockerIFCExecutor()
        if type(self.executor) is not DockerIFCExecutor:
            raise OriginalDoorIFC2X3Native064Error(
                "Real pinned local Linux Docker executor required")

    @property
    def tools(self):
        return [READ_TOOL,PYTHON_TOOL]

    def call(self,name,args):
        front=self._front(name,args)
        if front is not None:return front
        if name!="execute_ifc_code":
            return self._err("WrongOriginalNativePythonTool")
        if not isinstance(args,dict) or set(args)!={"code"} or not isinstance(args["code"],str):
            return self._err("InvalidNativePythonArguments")
        try:
            code=args["code"].encode("utf8","strict")
        except UnicodeEncodeError:
            return self._err("InvalidNativePythonCodeEncoding")
        if not 0<len(code)<=MAX_CODE_BYTES:
            return self._err("NativePythonCodeSizeExceeded")
        pre=live_pinned_local_runtime_admission_v052()
        if pre["status"]!="RUNTIME_ADMITTED":
            return {
                **self._err("BLOCKED_RUNTIME"),
                "reason":pre["reason"],"actual_python_executed":False,
            }
        self.submissions+=1
        work=self.folder/f"call_{self.calls_used:03d}"
        work.mkdir(exist_ok=False)
        current=work/"current.ifc"
        shutil.copyfile(self.output_ifc or self.source_ifc,current)
        try:
            real=self.executor.run(work,args["code"])
            if not (isinstance(real,dict)
                    and real.get("status")=="ok"
                    and real.get("committed") is True
                    and real.get("backend")=="linux_docker_sandbox"
                    and current.is_file() and not current.is_symlink()):
                raise OriginalDoorIFC2X3Native064Error(
                    "Actual OS-isolated native IFC2X3 Docker result not attested")
            verdict=source_native_ifc2x3_scope_v064(
                self.source_ifc,current,source_sha=SOURCE_SHA)
            if verdict["status"]!=STATUS:
                raise OriginalDoorIFC2X3Native064Error("Native source gate denied")
            if self.output_ifc is not None and file_hash(current)==file_hash(self.output_ifc):
                raise OriginalDoorIFC2X3Native064Error("Identical native replay")
            self.output_ifc=current
            return {
                "status":"ok","native_ifc_committed":True,
                "native_IFC2X3_SHA256":verdict["candidate_native_IFC_SHA256"],
                "actual_genuine_pinned_Linux_Docker_Python_executed":True,
                "python_execution_attested":True,
                "actual_linux_backend":real["backend"],
                "pinned_local_Docker_image":PINNED_DOCKER_IMAGE,
                "original_three_source_Walls_preserved":True,
                "native_original_Wall_full_thickness_CSG_cut_m3":verdict[
                    "native_original_IFC2X3_wall_full_thickness_volume_lost_m3"],
                "original_source_IFC2X3_new_schema_errors":0,
                "original_author_score":None,
                "result":real.get("result"),
            }
        except Exception:
            if current.exists():current.unlink()
            return {
                **self._err("NativeDockerWorkerOrOriginalIFC2X3ScopeRejected"),
                "python_execution_attested":False,
            }
