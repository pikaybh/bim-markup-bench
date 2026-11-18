"""v0.57 NEW explicit D_MANAGED_FINAL_STATE complete declarative final state.

The source is an immutable original SHA-pinned IFC4X3/mm model. The model's
compact XML must declare EVERY original managed object, in canonical order,
with its final numeric attributes and explicit present flag. Missing records
are NOT guessed/inferred from the source: no partial patch, NativeEditPlan,
typed operation, imperative editing, author grader or private solution.

The trusted host alone restores the original immutable STEP/GUID/mesh/relations
subtree and reconstructs the old v0.50 WHOLE final-state XML, then delegates
the actual IFC compilation and commit to v0.55's independent IFC oracles.

This variant is NOT the same representation/tool interface as v0.55 D-full or
v0.56 D-stream, and no prospective model study is authorized by this module.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from lxml import etree

from src.runtime.experimental_v44_original_native_step_readonly import Q
from src.runtime.experimental_v50_original_declarative_state import (
    project_original_declarative_state_v050,
    parse_original_declarative_state_diff_v050,
)
from src.security.agent_boundary import check_xml_bytes
from tools.bibimbap_matched25_tools import file_hash


ROOT=Path(__file__).resolve().parents[2]
XSD=ROOT/"spec"/"original_native_managed_final_state_v057.xsd"
MAX_MANAGED_STATE_UTF8_BYTES=8192
MAX_MANAGED_RECORDS=10
REPRESENTATION="D_MANAGED_FINAL_STATE"
MANAGED_BOUNDARY="EXACT_ORIGINAL_SOURCE_GUID_SUBSET"


class ManagedFinalState057Error(ValueError):
    """Failed all-original-managed-roster final-state declaration."""


def _need(condition:bool,reason:str)->None:
    if not condition:
        raise ManagedFinalState057Error(reason)


def _parser()->etree.XMLParser:
    return etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,recover=False,huge_tree=False,
                           remove_comments=False)


def _schema()->etree.XMLSchema:
    return etree.XMLSchema(etree.parse(str(XSD),_parser()))


def _source(source:Path,source_sha:str)->etree._Element:
    original=Path(source)
    _need(original.is_file() and not original.is_symlink()
          and file_hash(original)==source_sha,"Untrusted source IFC identity")
    projected=project_original_declarative_state_v050(
        original,source_sha=source_sha).xml
    node=etree.fromstring(projected,_parser())
    _need(node.tag==Q+"BuildingState" and len(node)==2
          and node[0].tag==Q+"OriginalNativeIFCSource"
          and node[1].tag==Q+"ManagedElements",
          "Original source-state projection changed")
    return node


def _build(original:etree._Element,source_sha:str)->etree._Element:
    root=etree.Element(Q+"ManagedFinalState",
       nsmap={None:"urn:bim-markup-bench:toy:v0"},
       attrib={
        "version":"0.57",
        "representation":REPRESENTATION,
        "sourceOriginalIFCSha256":source_sha,
        "sourceBuildingStateSha256":sha256(
            etree.tostring(original,encoding="utf8",
                           xml_declaration=True,pretty_print=False)
        ).hexdigest(),
        "managedBoundary":MANAGED_BOUNDARY,
    })
    for element in original[1]:
        attributes={"ifcGuid":element.get("ifcGuid"),
                    "present":"true"}
        for key,value in element.attrib.items():
            if key!="ifcGuid":
                attributes[key]=value
        etree.SubElement(root,element.tag,attributes)
    _need(_schema().validate(root),"Invalid source-derived complete final-state grammar")
    return root


def project_managed_final_state_v057(
    source_ifc:Path,*,source_sha:str,
)->bytes:
    """Deterministic ORIGINAL unedited complete managed-state projection."""
    original=_source(Path(source_ifc),source_sha)
    root=_build(original,source_sha)
    data=etree.tostring(root,encoding="utf8",
                        xml_declaration=True,pretty_print=False)
    _need(0<len(data)<=MAX_MANAGED_STATE_UTF8_BYTES,
          "Source managed-state exceeds compact bound")
    return data


def compact_from_complete_declarative_state_v057(
    source_ifc:Path,completed_state:bytes,*,source_sha:str,
)->bytes:
    """Developer-only comparison helper: no GT, used outside model tools.

    First uses the existing v0.50 ORIGINAL full-state parser to confirm
    this edited complete XML is physically admissible. Then *purely* renders
    final-state attributes/presence without leaking edit operations.
    """
    parse_original_declarative_state_diff_v050(
        source_ifc,completed_state,source_sha=source_sha)
    original=_source(Path(source_ifc),source_sha)
    final=etree.fromstring(completed_state,_parser())
    compact=_build(original,source_sha)
    final_by_guid={e.get("ifcGuid"):e for e in final[1]}
    for managed in compact:
        guid=managed.get("ifcGuid")
        if guid not in final_by_guid:
            managed.set("present","false")
        else:
            final_record=final_by_guid[guid]
            _need(managed.tag==final_record.tag,
                  "Managed final identity/tag corrupted")
            for key,value in final_record.attrib.items():
                _need(key in managed.attrib,"Managed final attribute changed")
                managed.set(key,value)
    data=etree.tostring(compact,encoding="utf8",
                        xml_declaration=True,pretty_print=False)
    _need(0<len(data)<=MAX_MANAGED_STATE_UTF8_BYTES
          and _schema().validate(compact),
          "Invalid compact final state derived from accepted full state")
    return data


def restore_complete_declarative_state_v057(
    source_ifc:Path,compact_xml:bytes,*,source_sha:str,
)->bytes:
    """Untrusted compact *complete* final state -> trusted full document.

    This performs no IFC mutation and accepts no commands. Validation
    includes original roster EXACT order, exact tag/numeric attributes,
    original IFC+state SHA anchors, explicit presence on every row and
    absence of DTD/XXE/hidden extra source fields.
    """
    _need(isinstance(compact_xml,bytes)
          and 0<len(compact_xml)<=MAX_MANAGED_STATE_UTF8_BYTES,
          "Full compact original managed-state UTF-8 bytes required")
    check_xml_bytes(compact_xml)
    candidate=etree.fromstring(compact_xml,_parser())
    _need(_schema().validate(candidate),
          "Invalid compact complete final-state XML grammar")
    original=_source(Path(source_ifc),source_sha)
    initial=etree.tostring(original,encoding="utf8",
                           xml_declaration=True,pretty_print=False)
    expected={
        "version":"0.57",
        "representation":REPRESENTATION,
        "sourceOriginalIFCSha256":source_sha,
        "sourceBuildingStateSha256":sha256(initial).hexdigest(),
        "managedBoundary":MANAGED_BOUNDARY,
    }
    _need(candidate.tag==Q+"ManagedFinalState"
          and dict(candidate.attrib)==expected
          and not (candidate.text or "").strip()
          and not (candidate.tail or "").strip(),
          "Original-source anchors or compact outer state changed")
    source_records=list(original[1])
    candidate_records=list(candidate)
    _need(1<=len(source_records)<=MAX_MANAGED_RECORDS
          and len(candidate_records)==len(source_records),
          "Every original managed identity must appear exactly once")
    restored=etree.fromstring(initial,_parser())
    final_container=restored[1]
    # Must not hide a roster omission by accepting only present=true rows.
    for old,new in zip(source_records,candidate_records):
        keys_old={(key,value) for key,value in old.attrib.items() if key!="ifcGuid"}
        _need(old.tag==new.tag
              and new.get("ifcGuid")==old.get("ifcGuid")
              and set(new.attrib)==set(old.attrib)|{"present"}
              and new.get("present") in {"true","false"}
              and len(new)==0
              and not (new.text or "").strip()
              and not (new.tail or "").strip(),
              "Original managed roster/order/fields/presence invalid")
        _need(set(old.attrib)==set(new.attrib)-{"present"},
              "Final managed-state attributes incomplete or extended")
        # Complete numeric final values MUST be supplied for even absent
        # objects so no numeric defaults are hallucinated or backfilled.
        if new.get("present")=="false":
            # In original v0.50, only whole-column presence deletion is
            # supported; disallow declaring absent slabs or arbitrary task
            # membership mutations.
            _need(old.tag==Q+"Column"
                  and not keys_old,
                  "Unsupported non-column or numeric managed deletion")
            final_container.remove(next(
                x for x in final_container
                if x.get("ifcGuid")==old.get("ifcGuid")))
        else:
            old_target=next(
                x for x in final_container
                if x.get("ifcGuid")==old.get("ifcGuid"))
            for k in old.attrib:
                old_target.set(k,new.get(k))
    restored_xml=etree.tostring(restored,encoding="utf8",
                                xml_declaration=True,pretty_print=False)
    # THIS is critical: the independent existing v0.50 full-state diff
    # parser re-validates physical admissibility, source subset, original
    # subtree canonical equality and trusted private v0.45 writer contract.
    parse_original_declarative_state_diff_v050(
        source_ifc,restored_xml,source_sha=source_sha)
    _need(file_hash(source_ifc)==source_sha,
          "Original source IFC changed during compact state restoration")
    return restored_xml
