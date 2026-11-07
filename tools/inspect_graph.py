#!/usr/bin/env python3
"""Trusted offline semantic binder inspector: no IFC edits and no model calls."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from src.runtime.xml_parser import parse_xml, MarkupParseError
from src.runtime.binder import BindingError, bind_document
from src.runtime.ifc_projection import UnsupportedIFCGeometry, project_ifc

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--xml",type=Path,default=None)
    p.add_argument("--source-ifc",type=Path,default=None,
                   help="Optional immutable IFC input to validate existing GUID and relations")
    p.add_argument("--candidate",action="store_true",
                   help="Plan an edited XML graph without pretending its relations already exist in source IFC")
    a=p.parse_args()
    if not a.xml and not a.source_ifc:
        p.error("At least --xml or --source-ifc is required")
    if a.candidate and not (a.xml and a.source_ifc):
        p.error("--candidate requires both a source IFC and edited XML")
    try:
        projected=project_ifc(a.source_ifc) if a.source_ifc else None
        if a.xml:
            with a.xml.open("rb") as f:
                data=f.read(2*1024*1024+1)
        else:
            data=projected.xml
        doc=parse_xml(data,filename=a.xml.name if a.xml else "building.xml",
            expected_source_sha256=projected.source.source_sha256 if projected else None)
        evidence=bind_document(doc,projection=projected,
            verify_native_edges=not a.candidate)
    except (MarkupParseError,BindingError,UnsupportedIFCGeometry,OSError) as exc:
        print(json.dumps({"status":"BLOCKED","error_type":type(exc).__name__,
                          "message":str(exc)[:260]},indent=2))
        return 2
    report=evidence.report()
    report["status"]="TYPED_GRAPH_ONLY_NO_IFC_OUTPUT"
    report["native_relations_checked"]=not a.candidate
    report["edited_candidate_not_source_verified"]=a.candidate
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
