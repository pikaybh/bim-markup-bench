"""v0.47 matched source XML versus AST-RESTRICTED Python-call research pilot.

No model Python code is executed. One whitelisted function CALL with literal
arguments is parsed and translated to the exact v0.45 original native edit XML.
Both arms share identical source XML and SAME native-mm writer and independent
physical IFC oracle. NOT an unrestricted Python or IfcOpenShell comparison.
"""
from __future__ import annotations

import ast
from hashlib import sha256
import math
from pathlib import Path
import re
from typing import Any
from lxml import etree

from src.runtime.experimental_v45_original_native_mutations import (
    check_source, project_original_native_mutations_v045,
    compile_original_native_mutation_v045, TASK_OPERATIONS, Q)
from tools.bibimbap_matched25_tools import (
    file_hash, _no_overwrite, UnsupportedArm, SecurityGate, MAX_CODE_BYTES,
    XmlSourceEditSession)
from tools.bibimbap_v045_independent_native_mutation_oracle import (
    verify_original_native_mutation_v045)

PY_TOOL_READ="read_source_python"
PY_TOOL_WRITE="submit_native_python"
FUNCTION_BY_TASK={
    "geometry_test_14":"set_slab_rectangle_dimensions",
    "geometry_test_15":"move_column_placement",
    "topological_test_11":"set_all_mapped_column_depth",
    "topological_test_17":"delete_columns_by_guid",
}
ARGS={
    "set_slab_rectangle_dimensions":("ifc_guid","new_x_dim_m","new_y_dim_m"),
    "move_column_placement":("ifc_guid","new_world_origin_x_m","new_world_origin_y_m"),
    "set_all_mapped_column_depth":("new_depth_m",),
    "delete_columns_by_guid":("ifc_guids",),
}
NUMBER_ARGS={
    "new_x_dim_m","new_y_dim_m","new_world_origin_x_m",
    "new_world_origin_y_m","new_depth_m",
}
IDENTIFIER_PATTERN=re.compile(r"^[0-9A-Za-z_$]{22}$")


class RestrictedNativePython047Error(ValueError):
    pass


def require(cond:bool,msg:str)->None:
    if not cond:
        raise RestrictedNativePython047Error(msg)


def _number(node:ast.AST)->float:
    """Only direct literal numeric source tokens; NO expression evaluation."""
    if isinstance(node,ast.Constant) and type(node.value) in (float,int):
        v=node.value
    elif (isinstance(node,ast.UnaryOp)
          and isinstance(node.op,(ast.UAdd,ast.USub))
          and isinstance(node.operand,ast.Constant)
          and type(node.operand.value) in (float,int)):
        v=node.operand.value if isinstance(node.op,ast.UAdd) else -node.operand.value
    else:
        raise RestrictedNativePython047Error(
            "Only direct finite numeric Python literals, not arithmetic/names/calls")
    try:
        result=float(v)
    except (OverflowError,ValueError,TypeError) as exc:
        raise RestrictedNativePython047Error("Number cannot be represented") from exc
    require(math.isfinite(result),"Nonfinite numeric literal not permitted")
    return result


def _guid(node:ast.AST)->str:
    require(isinstance(node,ast.Constant)
            and isinstance(node.value,str)
            and IDENTIFIER_PATTERN.fullmatch(node.value) is not None,
            "Only literal original native 22-character IFC GUID allowed")
    return node.value


def _guid_list(node:ast.AST)->list[str]:
    require(isinstance(node,(ast.List,ast.Tuple))
            and 1<=len(node.elts)<=9,
            "Explicit deletion accepts only 1..9 GUID string literals")
    result=[_guid(n) for n in node.elts]
    require(len(set(result))==len(result),"Duplicate source Column deletion GUID")
    return result


def parse_single_restricted_python_call(code:str,*,task_id:str)->dict[str,Any]:
    """A single typed AST call; NEVER compile/exec/eval submitted source."""
    require(isinstance(code,str) and 0<len(code.encode("utf8"))<=MAX_CODE_BYTES
            and "\x00" not in code and not code.startswith("\ufeff"),
            "Bounded UTF8 Python edit call required")
    require(task_id in FUNCTION_BY_TASK,"Unknown original public task")
    try:
        tree=ast.parse(code,mode="exec")
    except (SyntaxError,ValueError,TypeError) as exc:
        raise RestrictedNativePython047Error(
            "Malformed restricted Python typed edit call") from exc
    require(len(tree.body)==1 and isinstance(tree.body[0],ast.Expr)
            and isinstance(tree.body[0].value,ast.Call),
            "One expression-statement function call ONLY")
    call=tree.body[0].value
    expected=FUNCTION_BY_TASK[task_id]
    require(isinstance(call.func,ast.Name)
            and call.func.id==expected
            and not call.args
            and len(call.keywords)==len(ARGS[expected]),
            "Only original task's matched native typed function and exact kwargs")
    names=[kw.arg for kw in call.keywords]
    require(all(isinstance(k,str) for k in names)
            and len(set(names))==len(names)
            and set(names)==set(ARGS[expected]),
            "Missing/duplicate/extra Python keyword or dynamic **kwargs")
    out={}
    for kw in call.keywords:
        if kw.arg in NUMBER_ARGS:
            out[kw.arg]=_number(kw.value)
        elif kw.arg=="ifc_guid":
            out[kw.arg]=_guid(kw.value)
        elif kw.arg=="ifc_guids":
            out[kw.arg]=_guid_list(kw.value)
        else:
            raise RestrictedNativePython047Error("Not a permitted native keyword")
    return out


def typed_python_to_exact_original_xml(
        source:Path,source_sha:str,code:str)->bytes:
    """Build the SAME source-immutable v0.45 XML plan, not a new writer."""
    source=Path(source)
    task_id=check_source(source,source_sha)
    values=parse_single_restricted_python_call(code,task_id=task_id)
    original=project_original_native_mutations_v045(
        source,source_sha=source_sha).xml
    root=etree.fromstring(original,etree.XMLParser(
        no_network=True,load_dtd=False,resolve_entities=False,recover=False))
    require(root.tag==Q+"Building" and len(root)==2
            and root[1].tag==Q+"NativeEditPlan" and not len(root[1]),
            "Original source immutable v0.45 baseline changed")
    plan=root[1]
    kind=TASK_OPERATIONS[task_id]
    if kind=="SetSlabRectangleDimensions":
        etree.SubElement(plan,Q+kind,{
            "ifcGuid":values["ifc_guid"],
            "newXDimM":repr(values["new_x_dim_m"]),
            "newYDimM":repr(values["new_y_dim_m"]),
        })
    elif kind=="MoveColumnPlacement":
        etree.SubElement(plan,Q+kind,{
            "ifcGuid":values["ifc_guid"],
            "newWorldOriginXM":repr(values["new_world_origin_x_m"]),
            "newWorldOriginYM":repr(values["new_world_origin_y_m"]),
        })
    elif kind=="SetAllMappedColumnDepth":
        etree.SubElement(plan,Q+kind,{"newDepthM":repr(values["new_depth_m"])})
    elif kind=="DeleteColumnsByGuid":
        children=etree.SubElement(plan,Q+kind)
        for guid in values["ifc_guids"]:
            etree.SubElement(children,Q+"DeleteColumn",{"ifcGuid":guid})
    else:
        raise RestrictedNativePython047Error("No matched original typed operation")
    result=etree.tostring(root,encoding="utf8",
                          xml_declaration=True,pretty_print=False)
    require(0<len(result)<=300000,
            "Native edit XML larger than paired model source ceiling")
    require(file_hash(source)==source_sha,"Original source IFC changed in translation")
    return result


def exact_model_facing_python_source(source_xml:bytes)->str:
    """Original v0.45 XML embedded as lossless Python string literal only."""
    require(isinstance(source_xml,bytes) and len(source_xml)<=300000,
            "Original paired model XML must be bounded")
    decoded=source_xml.decode("utf8","strict")
    view="ORIGINAL_SOURCE_XML = "+repr(decoded)+"\n"
    require(len(view.encode("utf8"))<=300000,
            "Python literal source wrapping over original context size limit")
    decoded_back=ast.literal_eval(view.split(" = ",1)[1].strip())
    require(decoded_back.encode("utf8")==source_xml,
            "Python literal does not preserve the same source XML evidence")
    return view


class RestrictedOriginalPythonSession047:
    """Model-facing SAFE Python-call syntax with original XML evidence.

    The code is AST data, never executed in Python; native edit is the EXACT
    v0.45 XML trusted compiler, independently physically checked thereafter.
    """

    def __init__(self,original_ifc:Path,folder:Path,*,max_calls:int=25):
        original_ifc=Path(original_ifc)
        folder=Path(folder)
        if not original_ifc.is_file() or original_ifc.is_symlink():
            raise ValueError("Original native source IFC file not available")
        if folder.exists():
            raise ValueError("Python research destination already exists")
        if max_calls!=25:
            raise UnsupportedArm("Frozen pilot uses exactly 25 tool calls")
        self.original_ifc=original_ifc.resolve(strict=True)
        self.source_sha=file_hash(self.original_ifc)
        try:
            self.task_id=check_source(self.original_ifc,self.source_sha)
            source=project_original_native_mutations_v045(
                self.original_ifc,source_sha=self.source_sha)
            self.source_xml=source.xml
            self.source_python=exact_model_facing_python_source(source.xml)
        except Exception as exc:
            raise UnsupportedArm(
                f"Four-original-SHA source unavailable: {type(exc).__name__}") from exc
        folder.mkdir(parents=True)
        self.folder=folder
        self.output_ifc:Path|None=None
        self.current_python_code:str|None=None
        self.current_xml=self.source_xml
        self.submissions=0
        self.calls=0
        self.call_budget=max_calls

    @property
    def tools(self)->list[dict]:
        signature={
            "geometry_test_14":"set_slab_rectangle_dimensions(ifc_guid='...', new_x_dim_m=..., new_y_dim_m=...)",
            "geometry_test_15":"move_column_placement(ifc_guid='...', new_world_origin_x_m=..., new_world_origin_y_m=...)",
            "topological_test_11":"set_all_mapped_column_depth(new_depth_m=...)",
            "topological_test_17":"delete_columns_by_guid(ifc_guids=['...', ...])",
        }[self.task_id]
        return [
            {
                "type":"function",
                "name":PY_TOOL_READ,
                "description":"Read Python literal ORIGINAL_SOURCE_XML preserving EXACT SAME v0.45 original IFC4X3/mm source evidence and empty native edit plan as matched XML arm; no extra IFC facts, code runtime, answer or evaluator.",
                "parameters":{"type":"object","properties":{},
                              "additionalProperties":False},"strict":True,
            },
            {
                "type":"function",
                "name":PY_TOOL_WRITE,
                "description":(
                    "Send one AST-restricted Python typed native edit call. "
                    f"Required function signature: {signature}. Not arbitrary Python "
                    "code execution/IfcOpenShell. Same v0.45 original source-native "
                    "writer and independent physical IFC oracle as the XML arm."
                ),
                "parameters":{"type":"object","properties":{
                    "python_code":{"type":"string","description":
                        "Exactly one Python call with literal typed keyword arguments"}},
                    "required":["python_code"],"additionalProperties":False},
                "strict":True,
            },
        ]

    def call(self,name:str,arguments:dict)->dict:
        if self.calls>=self.call_budget:
            return {"status":"error","error_type":"ToolBudgetExceeded",
                    "error":"Original pilot 25 tool-call limit reached",
                    "native_ifc_committed":False}
        self.calls+=1
        if file_hash(self.original_ifc)!=self.source_sha:
            return {"status":"error","error_type":"OriginalSourceSHAChanged",
                    "error":"Immutable original IFC SHA does not match",
                    "native_ifc_committed":False}
        if name==PY_TOOL_READ:
            if arguments:
                return {"status":"error","error_type":"InvalidReadArgs",
                        "error":"Read source takes no arguments"}
            return {
                "status":"ok","source_python":self.source_python,
                "original_source_xml_sha256":sha256(self.source_xml).hexdigest(),
                "native_candidate_available":self.output_ifc is not None,
                "native_edit_authority":"SAME_FOUR_TYPED_ORIGINAL_OPERATIONS_AS_V045_XML",
            }
        if name!=PY_TOOL_WRITE:
            return {"status":"error","error_type":"UnknownTool",
                    "error":"Only two research pilot tools exist"}
        if set(arguments)!={"python_code"} or not isinstance(arguments["python_code"],str):
            return {"status":"error","error_type":"InvalidSubmitArgs",
                    "error":"One Python typed edit string required"}
        code=arguments["python_code"]
        self.submissions+=1
        attempt_dir=self.folder/f"attempt_{self.submissions:02d}"
        attempt_dir.mkdir()
        candidate=attempt_dir/"candidate_original_native_mm.ifc"
        try:
            require(0<len(code.encode("utf8"))<=MAX_CODE_BYTES,
                    "Python edit program exceeds original code size bound")
            _no_overwrite(attempt_dir/"submitted_exact.py",code.encode("utf8"))
            xml=typed_python_to_exact_original_xml(
                self.original_ifc,self.source_sha,code)
            _no_overwrite(attempt_dir/"translated_exact_source.xml",xml)
            compilation=compile_original_native_mutation_v045(
                self.original_ifc,xml,candidate,source_sha=self.source_sha)
            oracle=verify_original_native_mutation_v045(
                self.original_ifc,candidate,submitted_xml=xml,
                source_sha=self.source_sha,task_id=self.task_id)
            if file_hash(self.original_ifc)!=self.source_sha:
                raise SecurityGate("Original published IFC source changed")
            self.output_ifc=candidate
            self.current_python_code=code
            self.current_xml=xml
            return {
                "status":"ok","native_ifc_committed":True,
                "native_ifc_sha256":file_hash(candidate),
                "translated_exact_xml_sha256":sha256(xml).hexdigest(),
                "native_compile_status":compilation.as_dict()["status"],
                "independent_original_native_oracle_status":oracle["status"],
                "source_original_ifc_unchanged":True,
                "original_benchmark_semantic_success_proven":False,
                "model_can_retry":True,
            }
        except Exception as exc:
            if candidate.exists():
                candidate.unlink()
            return {
                "status":"error","error_type":type(exc).__name__,
                "error":str(exc)[:900],"native_ifc_committed":False,
                "last_valid_IFC_and_source_preserved":True,
                "original_native_source_unchanged":
                    file_hash(self.original_ifc)==self.source_sha,
                "current_source_xml_sha256":sha256(self.current_xml).hexdigest(),
            }


class MatchedOriginalXmlSession047:
    """Same exact v0.45 trusted XML arm, explicit shared pilot 25-call cap."""

    def __init__(self,original_ifc:Path,folder:Path,*,max_calls:int=25):
        if max_calls!=25:
            raise UnsupportedArm("Original pilot both arms require 25 calls")
        self.base=XmlSourceEditSession(
            original_ifc,folder,
            experimental_original_native_mutations_v045=True)
        self.original_xml=self.base.original_xml
        self.original_ifc=self.base.original_ifc
        self.source_sha=self.base.source_sha
        self.task_id=self.base.native_mutation_original_task_id
        self.folder=self.base.folder
        self.calls=0
        self.call_budget=max_calls

    @property
    def tools(self)->list[dict]:
        return self.base.tools

    @property
    def output_ifc(self)->Path|None:
        return self.base.output_ifc

    @property
    def current_xml(self)->bytes:
        return self.base.current_xml

    def call(self,name:str,arguments:dict)->dict:
        if self.calls>=self.call_budget:
            return {"status":"error","error_type":"ToolBudgetExceeded",
                    "error":"Original pilot 25 tool-call limit reached",
                    "native_ifc_committed":False}
        self.calls+=1
        if file_hash(self.original_ifc)!=self.source_sha:
            return {"status":"error","error_type":"OriginalSourceSHAChanged",
                    "error":"Original public source IFC bytes no longer match",
                    "native_ifc_committed":False}
        return self.base.call(name,arguments)
