"""Trusted helper launched ONLY within a restricted Linux Docker container.

This worker is never run on Windows/macOS by the paired-arm harness.
Its single writable mount contains only an expendable original-IFC clone.
Only explicit commit() persists mutations, matching the official BIBIMBAP
execute_ifc_code tool semantics. This file is mounted read-only.
"""
from __future__ import annotations
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import traceback

WORKSPACE=Path("/workspace")
IFC_PATH=WORKSPACE/"current.ifc"
PAYLOAD=WORKSPACE/"submitted_code.json"
RESULT=WORKSPACE/"execution_result.json"

def _jsonable(value):
    try:
        json.dumps(value,allow_nan=False)
        return value
    except (TypeError,ValueError,OverflowError):
        return repr(value)[:3000]

def main():
    import ifcopenshell
    import ifcopenshell.api as api
    import ifcopenshell.util as util
    import ifcopenshell.util.element as element_util
    import ifcopenshell.guid as guid

    request=json.loads(PAYLOAD.read_text(encoding="utf8"))
    code=request["code"]
    if not isinstance(code,str) or not (0<len(code.encode("utf8"))<=64000):
        raise ValueError("Invalid Python submission")
    if not IFC_PATH.is_file():
        raise ValueError("No stage IFC clone")
    f=ifcopenshell.open(str(IFC_PATH))
    committed=[False]
    def commit(path=None):
        if path is not None and str(path) not in (str(IFC_PATH), "/workspace/current.ifc"):
            raise ValueError("commit() only accepts active isolated IFC file")
        f.write(str(IFC_PATH))
        committed[0]=True
        return str(IFC_PATH)

    env={"__builtins__":__builtins__,"ifc":f,"ifcopenshell":ifcopenshell,
         "api":api,"util":util,"element_util":element_util,
         "guid":guid,"commit":commit,"ifc_file_path":str(IFC_PATH)}
    output=io.StringIO();errors=io.StringIO()
    record={"status":"ok","committed":False,"result":None,
            "stdout":"","stderr":"","backend":"linux_docker_sandbox"}
    try:
        with redirect_stdout(output), redirect_stderr(errors):
            exec(compile(code, "<model-submitted-code>", "exec"),env,env)
        record["result"]=_jsonable(env.get("result"))
    except Exception as exc:
        record["status"]="error"
        record["error_type"]=type(exc).__name__
        record["error"]=str(exc)[:3000]
        record["traceback"]=traceback.format_exc(limit=3)[-2500:]
    finally:
        record["committed"]=committed[0]
        record["stdout"]=output.getvalue()[:6000]
        record["stderr"]=errors.getvalue()[:3000]
    RESULT.write_text(json.dumps(record,ensure_ascii=False,default=repr)+"\n",encoding="utf8")
    print(json.dumps({"status":record["status"],"committed":record["committed"]}))

if __name__=="__main__":
    main()
