#!/usr/bin/env python3
"""OFFLINE declarative XML -> new IFC4X3 compile (limited Wall-only v0 slice).

Runs a trusted backend. The model authoring the XML has NO access to this
IfcOpenShell implementation, API key, hidden evaluator or ground truth.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from src.runtime.compiler import CompilerError,compile_declarative_xml

MAX_XML_BYTES=2*1024*1024

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-ifc",type=Path,required=True)
    p.add_argument("--edited-xml",type=Path,required=True)
    p.add_argument("--result-ifc",type=Path,required=True)
    a=p.parse_args()
    try:
        with a.edited_xml.open("rb") as input:
            xml=input.read(MAX_XML_BYTES+1)
        report=compile_declarative_xml(a.source_ifc,xml,a.result_ifc)
        print(json.dumps(report.as_dict(),indent=2,sort_keys=True))
        return 0
    except (CompilerError,OSError,ValueError) as exc:
        print(json.dumps({
            "status":"BLOCKED_NO_RESULT_COMMITTED",
            "error_type":type(exc).__name__,
            "reason":str(exc)[:240],
            "ifc_created":False,
        },indent=2,sort_keys=True))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
