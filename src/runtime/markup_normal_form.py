"""V0 XML semantic fingerprint for source-state comparisons.

This is a small independent helper, NOT the full typed parser, binder,
IFC compiler or source-preserving editor. The LLM still edits XML only.
"""
from __future__ import annotations
import hashlib
from xml.etree import ElementTree as ET

from src.security.agent_boundary import check_xml_bytes

COLLECTIONS = {"Levels", "Elements", "Relations"}
NS = "urn:bim-markup-bench:toy:v0"

def local(tag: str) -> str:
    return tag.rsplit("}",1)[-1]

def canonical_semantic_xml(source: bytes) -> bytes:
    check_xml_bytes(source)
    root=ET.fromstring(source)
    if root.tag != "{"+NS+"}Building":
        raise ValueError("Unexpected XML namespace or root element")
    for collection in root:
        if local(collection.tag) in COLLECTIONS:
            collection[:] = sorted(
                collection,
                key=lambda el: (local(el.tag),el.attrib.get("id",""),
                                tuple(sorted(el.attrib.items()))),
            )
    out = ET.canonicalize(
        ET.tostring(root,encoding="unicode"),
        with_comments=False,strip_text=True,
    )
    return out.encode("utf-8")

def semantic_digest(source: bytes) -> str:
    return hashlib.sha256(canonical_semantic_xml(source)).hexdigest()
