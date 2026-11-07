#!/usr/bin/env python3
"""Offline, non-mutating XML v0.1 validator for manually edited building.xml.

No IFC writer, OpenAI API, network or local model asset access.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.runtime.xml_parser import MarkupParseError, parse_xml

MAX_FILE_BYTES = 2 * 1024 * 1024

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Editable v0.1 declarative XML source")
    parser.add_argument("--expected-source-sha256", default=None,
                        help="Optional immutable original IFC content SHA-256")
    args = parser.parse_args()
    try:
        with args.source.open("rb") as handle:
            data = handle.read(MAX_FILE_BYTES + 1)
        doc = parse_xml(data, filename=args.source.name,
                        expected_source_sha256=args.expected_source_sha256)
    except MarkupParseError as exc:
        print(json.dumps({"status": "INVALID", "diagnostic": exc.diagnostic},
                         indent=2, sort_keys=True))
        return 2
    except OSError as exc:
        print(json.dumps({
            "status": "BLOCKED",
            "diagnostic": {
                "code": "INPUT_UNREADABLE", "severity": "ERROR",
                "message": type(exc).__name__, "file": args.source.name,
                "line": 1, "column": 1, "element_id": None
            }
        }, indent=2, sort_keys=True))
        return 2
    print(json.dumps({
        "status": "VALID_DECLARATIVE_XML_ONLY",
        "model_compiled": False,
        "output_ifc_written": False,
        "semantic_sha256": doc.semantic_sha256,
        "source_byte_sha256": doc.source_byte_sha256,
        "units": doc.units, "ifc_schema": doc.ifc_schema,
        "counts": {"levels": len(doc.levels), "elements": len(doc.elements),
                   "relations": len(doc.relations)},
    }, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
