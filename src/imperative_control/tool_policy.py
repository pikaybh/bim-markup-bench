"""G2 #18 preliminary AST rejector. NEVER a Python execution sandbox.

This parser can reject obvious violations and collect audit evidence. It is
not robust against Python dynamic language attack surfaces and MUST NOT be
used to execute generated code on the unrestricted Mac. Only a container/VM
OS isolation boundary (#19) can permit executing adversarial candidates.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import re

MAX_CODE_BYTES=64*1024

class ImperativePreflightError(ValueError):
    pass

BLOCKED_IMPORT_ROOTS=frozenset({
    "os","sys","subprocess","socket","pathlib","shutil","tempfile","ctypes",
    "importlib","inspect","builtins","urllib","requests","httpx","http",
    "ftplib","asyncio","multiprocessing","threading","signal","pickle",
    "marshal","pdb","code","site","zipfile","tarfile","shlex","posix",
    "platform","resource","pwd","socketserver","webbrowser",
})
ALLOWED_IMPORT_ROOTS=frozenset({"ifcopenshell","math","numpy"})
BLOCKED_CALLS=frozenset({
    "eval","exec","compile","__import__","open","input","breakpoint",
    "setattr","delattr","globals","locals","vars","dir",
})
# P1 prospective policy: allow ordinary *read-only* IFC attribute
# introspection with literal, reviewed attribute names. The function must
# appear as a direct Call and the attribute must be a static string. This
# does not approve OS execution or modify the frozen P0 trial verdict.
SAFE_IFC_REFLECTION=frozenset({"getattr","hasattr"})
IFC_REFLECTION_ATTRS=frozenset({
    "GlobalId","Name","Description","ObjectType","PredefinedType",
    "Representation","Representations","Items","ObjectPlacement",
    "Depth","Height","Width","OverallHeight","OverallWidth",
    "Material","Coordinates","HasOpenings","FillsVoids",
    "RelatingOpeningElement","RelatedBuildingElement",
    "RelatingBuildingElement","RelatedObjects","RelatedElements",
    "RelatingStructure","ContainedInStructure",
})

BLOCKED_IDENTIFIERS=frozenset({
    "__class__","__base__","__bases__","__subclasses__","__mro__",
    "__globals__","__builtins__","__dict__","__getattribute__",
    "__code__","__closure__","__reduce__","__loader__","__spec__",
})
SENSITIVE=re.compile(
    r"(OPENAI_API_KEY|sk-[A-Za-z0-9_-]{10,}|ground_truth_ifc|/grader/|"
    r"(?:\.\./)|/Users/|/etc/passwd|/proc/)",
    flags=re.IGNORECASE,
)

@dataclass(frozen=True)
class CodeCheck:
    source_sha256:str
    byte_size:int
    imported_roots:tuple[str,...]
    call_count:int
    syntax_only_pass:bool
    execution_authorized:bool=False

    def as_dict(self)->dict:
        return {
            "source_sha256":self.source_sha256,
            "byte_size":self.byte_size,
            "imported_roots":list(self.imported_roots),
            "call_count":self.call_count,
            "syntax_only_pass":self.syntax_only_pass,
            "execution_authorized":self.execution_authorized,
            "OS_sandbox_available":False,
        }


def preflight_generated_python(code:bytes)->CodeCheck:
    """Syntax/permissions read-only check. Absolutely no compile/exec/eval."""
    if type(code) is not bytes or not (0<len(code)<=MAX_CODE_BYTES):
        raise ImperativePreflightError("Python source missing or exceeds preflight cap")
    try:
        source=code.decode("utf-8")
    except UnicodeError as exc:
        raise ImperativePreflightError("Generated Python must use UTF-8") from exc
    if SENSITIVE.search(source):
        raise ImperativePreflightError("Potential secret/GT/traversal value in Python text")
    try:
        tree=ast.parse(source,filename="solution.py",mode="exec")
    except (SyntaxError,ValueError,RecursionError) as exc:
        raise ImperativePreflightError("Generated Python fails syntax preflight") from exc
    # ast.Name occurrences of getattr/hasattr are safe ONLY when they
    # themselves are the called function with a literal IFC attribute.
    allowed_reflect_names=set()
    for node in ast.walk(tree):
        if not (isinstance(node,ast.Call)
                and isinstance(node.func,ast.Name)
                and node.func.id in SAFE_IFC_REFLECTION):
            continue
        function=node.func.id
        argc=len(node.args)
        exact_arity=((function=="getattr" and argc in (2,3))
                     or (function=="hasattr" and argc==2))
        attribute=node.args[1] if argc>=2 else None
        if (not exact_arity or node.keywords
                or not isinstance(attribute,ast.Constant)
                or type(attribute.value) is not str
                or attribute.value not in IFC_REFLECTION_ATTRS):
            raise ImperativePreflightError(
                "Unsafe dynamic attribute reflection or IFC attribute")
        allowed_reflect_names.add(id(node.func))
    imports=set()
    calls=0
    for node in ast.walk(tree):
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            names=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module or ""]
            for name in names:
                root=name.split(".")[0]
                if not root or root in BLOCKED_IMPORT_ROOTS or root not in ALLOWED_IMPORT_ROOTS:
                    raise ImperativePreflightError("Unapproved Python module import")
                imports.add(root)
            if isinstance(node,ast.ImportFrom) and node.level>0:
                raise ImperativePreflightError("Relative Python imports are forbidden")
        if isinstance(node,(ast.Name,ast.Attribute)):
            identifier=node.id if isinstance(node,ast.Name) else node.attr
            allow_module_file_open=(
                isinstance(node,ast.Attribute)
                and node.attr=="open"
                and isinstance(node.value,ast.Name)
                and node.value.id=="ifcopenshell"
            )
            if identifier in SAFE_IFC_REFLECTION and (
                    not isinstance(node,ast.Name)
                    or id(node) not in allowed_reflect_names):
                raise ImperativePreflightError(
                    "Read-only IFC reflection is allowed as a literal direct call only")
            if identifier in BLOCKED_IDENTIFIERS or (
                identifier in BLOCKED_CALLS and not allow_module_file_open
            ):
                raise ImperativePreflightError("Unsafe Python identifier")
        if isinstance(node,ast.Call):
            calls+=1
        if isinstance(node,(ast.Global,ast.Nonlocal,ast.ClassDef,ast.AsyncFunctionDef,
                            ast.Await,ast.Yield,ast.YieldFrom)):
            raise ImperativePreflightError("Advanced Python execution construct is not preflighted")
    return CodeCheck(
        hashlib.sha256(code).hexdigest(),len(code),
        tuple(sorted(imports)),calls,True,False,
    )
