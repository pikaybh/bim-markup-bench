#!/usr/bin/env python3
"""Read-only verified IFC4X3 -> experimental XML source generator.

All generated XML and backend-only audit files stay local / untracked by default.
Never downloads an IFC corpus or invokes OpenAI.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from src.runtime.ifc_projection import UnsupportedIFCGeometry, project_ifc
from src.runtime.xml_parser import parse_xml, MarkupParseError
from src.runtime.ifc_snapshot import SourceIntegrityError, passthrough_noop

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("--xml-out",type=Path,default=Path("data/projections/building.xml"))
    parser.add_argument("--strict",action="store_true",
                        help="Fail if any editable type or supported relation cannot be projected")
    parser.add_argument("--noop-copy",type=Path,default=None,
                        help="Optional independent IFC output; accepts only a validated, unchanged XML state")
    args=parser.parse_args()
    try:
        result=project_ifc(args.source,strict_on_opaque=args.strict)
        if args.xml_out.exists() or args.xml_out.is_symlink():
            raise SourceIntegrityError("Refuse to overwrite an existing XML output")
        args.xml_out.parent.mkdir(parents=True,exist_ok=True)
        with args.xml_out.open("xb") as output:
            output.write(result.xml)
        report=result.report()
        if args.noop_copy is not None:
            initial=parse_xml(result.xml,expected_source_sha256=result.source.source_sha256)
            copied=passthrough_noop(result.source,initial,initial,args.noop_copy)
            report["noop_ifc_output_sha256"]=copied.source_sha256
            report["noop_graph_equal"]=copied.graph_fingerprint==result.source.graph_fingerprint
        print(json.dumps(report,indent=2,sort_keys=True))
        print("STATUS: PROJECTION_ONLY, NONEDITABLE CLASSES REMAIN OPAQUE; NO IFC MUTATION SUPPORTED")
        return 0
    except (UnsupportedIFCGeometry,SourceIntegrityError,MarkupParseError,OSError,ValueError) as exc:
        print(json.dumps({"status":"BLOCKED","reason":str(exc)[:260],
                          "source":args.source.name},indent=2))
        return 2

if __name__=="__main__":
    sys.exit(main())
