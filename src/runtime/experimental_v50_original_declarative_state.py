"""v0.50 research-only original four direct declarative BIM XML state editing.

The LLM-facing XML contains *final object states* only: no API, edit plan,
commands or Python. The trusted compiler derives a stable-GUID semantic diff
against a SHA-locked original IFC and lowers it to the existing v0.45 native-mm
writer INSIDE the trusted backend. An independent source/native physical IFC
oracle is mandatory at the host boundary before candidate commit.

The native IFC and XML are a deliberately PARTIAL MANAGED OVERLAY, not a
lossless IFC authoring format or the final BIXML product schema.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from pathlib import Path
from lxml import etree

import ifcopenshell
import ifcopenshell.util.placement

from src.runtime.experimental_v44_original_native_step_readonly import (
    PINS, Q, check_original_native_readonly_source,
    project_native_readonly_source_v044,
)
from src.runtime.experimental_v45_original_native_mutations import (
    compile_original_native_mutation_v045,
    project_original_native_mutations_v045,
    _body_solid,
)
from tools.bibimbap_matched25_tools import file_hash

ROOT = Path(__file__).resolve().parents[2]
XSD = ROOT / "spec" / "original_native_declarative_state_v050.xsd"
MAX_XML_BYTES = 300000
MAX_CALLS = 25
MANAGED_BOUNDARY = "EXACT_ORIGINAL_SOURCE_GUID_SUBSET"
ALLOWED_TASKS = frozenset(task for task, _, _, _, _ in PINS.values())


class DeclarativeState050Error(ValueError):
    """Untrusted whole XML state did not describe a permissible source diff."""


@dataclass(frozen=True)
class OriginalState050:
    xml: bytes
    task_id: str
    source_sha256: str


@dataclass(frozen=True)
class SemanticDiff050:
    task_id: str
    source_sha256: str
    changed_original_ids: tuple[str, ...]
    changed_state_fields: tuple[str, ...]
    # Trusted internal payload only. NEVER reveal to LLM tool output or source.
    internal_native_writer_xml: bytes


def need(condition: bool, msg: str) -> None:
    if not condition:
        raise DeclarativeState050Error(msg)


def _parser() -> etree.XMLParser:
    return etree.XMLParser(
        resolve_entities=False, load_dtd=False, no_network=True,
        recover=False, huge_tree=False, remove_comments=False,
    )


def _xsd() -> etree.XMLSchema:
    return etree.XMLSchema(etree.parse(str(XSD)))


def _num(value: float) -> str:
    v = round(float(value), 6)
    need(math.isfinite(v) and -1e5 <= v <= 1e5, "Unsafe original state number")
    return f"{v:.6f}"


def _val(text: str | None) -> float:
    try:
        need(isinstance(text, str) and 0 < len(text) <= 36,
             "Missing/bounded decimal final state value")
        n = float(text)
    except (ValueError, OverflowError, TypeError) as exc:
        raise DeclarativeState050Error("Final state requires finite literal decimal") from exc
    need(math.isfinite(n) and abs(n) <= 1e5,
         "Nonfinite or unbounded native state value")
    need(abs(n - round(n, 6)) < 1e-9,
         "Managed state accepts at most micrometre precision")
    return n


def _original_info(source: Path, source_sha: str):
    source = Path(source)
    need(source.is_file() and not source.is_symlink() and
         source_sha in PINS and file_hash(source) == source_sha,
         "v0.50 only exact four original source SHA-pinned IFCs")
    model = ifcopenshell.open(str(source))
    task = check_original_native_readonly_source(source, source_sha, model)
    return task, model


def project_original_declarative_state_v050(
    source: Path, *, source_sha: str,
) -> OriginalState050:
    task, model = _original_info(source, source_sha)
    original = project_native_readonly_source_v044(
        source, original_native_sha256=source_sha,
    )
    root_v44 = etree.fromstring(original.xml, _parser())
    need(root_v44.tag == Q + "Building" and len(root_v44) == 1 and
         root_v44[0].tag == Q + "OriginalNativeIFCSource",
         "Original source v0.44 projection unexpectedly changed")
    root = etree.Element(Q + "BuildingState", nsmap={None: "urn:bim-markup-bench:toy:v0"}, attrib={
        "version": "0.50",
        "sourceOriginalIFCSha256": source_sha,
        "nativeSchema": "IFC4X3",
        "nativeUnit": "MILLIMETER",
        "representation": "DECLARATIVE_STATE_SNAPSHOT",
        "managedSemantics": "EXPLICIT_SUBSET_ONLY",
    })
    root.append(root_v44[0])
    elements = etree.SubElement(root, Q + "ManagedElements", {
        "boundary": MANAGED_BOUNDARY,
    })
    if task == "geometry_test_14":
        slabs = model.by_type("IfcSlab")
        need(len(slabs) == 1, "Expected one native original slab")
        slab = slabs[0]
        rect = _body_solid(slab, mapped=False).SweptArea
        etree.SubElement(elements, Q + "Slab", {
            "ifcGuid": slab.GlobalId,
            "dimXM": _num(float(rect.XDim) / 1000),
            "dimYM": _num(float(rect.YDim) / 1000),
        })
    elif task == "geometry_test_15":
        columns = model.by_type("IfcColumn")
        need(len(columns) == 4, "Expected four native original columns")
        for col in sorted(columns, key=lambda x: x.GlobalId):
            _body_solid(col, mapped=True)
            need(col.ObjectPlacement is not None, "Missing native source placement")
            world = ifcopenshell.util.placement.get_local_placement(col.ObjectPlacement)
            etree.SubElement(elements, Q + "Column", {
                "ifcGuid": col.GlobalId,
                "worldXM": _num(world[0, 3] / 1000),
                "worldYM": _num(world[1, 3] / 1000),
            })
    elif task == "topological_test_11":
        columns = model.by_type("IfcColumn")
        need(len(columns) == 2, "Expected two original mapped columns")
        for col in sorted(columns, key=lambda x: x.GlobalId):
            solid = _body_solid(col, mapped=True)
            etree.SubElement(elements, Q + "Column", {
                "ifcGuid": col.GlobalId,
                "extrusionDepthM": _num(float(solid.Depth) / 1000),
            })
    elif task == "topological_test_17":
        columns = model.by_type("IfcColumn")
        need(len(columns) == 10, "Expected ten source original columns")
        for col in sorted(columns, key=lambda x: x.GlobalId):
            etree.SubElement(elements, Q + "Column", {"ifcGuid": col.GlobalId})
    else:
        raise DeclarativeState050Error("Unsupported original source task")

    raw = etree.tostring(root, encoding="utf8", xml_declaration=True, pretty_print=False)
    need(len(raw) <= MAX_XML_BYTES and _xsd().validate(root),
         "Complete declarative XML exceeds limit or fails source-state XSD")
    need(file_hash(source) == source_sha, "Original IFC changed during source projection")
    return OriginalState050(raw, task, source_sha)


def parse_original_declarative_state_diff_v050(
    source: Path, edited_xml: bytes, *, source_sha: str,
) -> SemanticDiff050:
    task, _ = _original_info(source, source_sha)
    need(isinstance(edited_xml, bytes) and 0 < len(edited_xml) <= MAX_XML_BYTES,
         "Whole replacement declarative XML bytes required")
    from src.security.agent_boundary import check_xml_bytes
    check_xml_bytes(edited_xml)
    edited = etree.fromstring(edited_xml, _parser())
    need(_xsd().validate(edited), "Invalid v0.50 declarative XML state schema")
    baseline = project_original_declarative_state_v050(
        source, source_sha=source_sha,
    )
    old = etree.fromstring(baseline.xml, _parser())
    need(edited.tag == old.tag and len(edited) == 2
         and dict(edited.attrib) == dict(old.attrib)
         and edited[0].tag == Q + "OriginalNativeIFCSource"
         and edited[1].tag == Q + "ManagedElements"
         and dict(edited[1].attrib) == dict(old[1].attrib),
         "Unmodifiable IFC identity, XML envelope or managed boundary changed")
    need(etree.tostring(edited[0], method="c14n") ==
         etree.tostring(old[0], method="c14n"),
         "Immutable original native IFC STEP/GUID/mesh/relations were modified")
    before = list(old[1])
    after = list(edited[1])
    bkeys = [(el.tag, el.get("ifcGuid")) for el in before]
    akeys = [(el.tag, el.get("ifcGuid")) for el in after]
    need(len(bkeys) == len(set(bkeys)), "Original managed identities duplicated")
    need(len(akeys) == len(set(akeys)), "Edited managed identities duplicated")
    need(set(akeys).issubset(set(bkeys)), "Created/spoofed or unmanaged IFC identity")
    need(akeys == [k for k in bkeys if k in set(akeys)],
         "Edited element identities must preserve canonical source order")
    before_by_guid = {e.get("ifcGuid"): e for e in before}
    after_by_guid = {e.get("ifcGuid"): e for e in after}
    b_guids = set(before_by_guid)
    a_guids = set(after_by_guid)
    removed = tuple(sorted(b_guids - a_guids))
    changes: list[tuple[str, dict, dict]] = []
    for guid in sorted(a_guids):
        prev = before_by_guid[guid]
        now = after_by_guid[guid]
        need(prev.tag == now.tag and set(prev.attrib) == set(now.attrib)
             and len(prev) == len(now) == 0
             and not (now.text or "").strip()
             and not (now.tail or "").strip(),
             "Source managed element shape or attributes changed")
        numeric_fields = set(prev.attrib) - {"ifcGuid"}
        parsed_prev = {field: _val(prev.get(field)) for field in numeric_fields}
        parsed_now = {field: _val(now.get(field)) for field in numeric_fields}
        if any(abs(parsed_now[k] - parsed_prev[k]) > 1e-6 for k in numeric_fields):
            changes.append((guid, parsed_prev, parsed_now))

    # Lower semantic *document-state* difference to a PRIVATE trusted writer.
    # No operation kind or target hints are ever included in model-facing XML.
    native = etree.fromstring(
        project_original_native_mutations_v045(source, source_sha=source_sha).xml,
        _parser(),
    )
    need(len(native) == 2 and native[1].tag == Q + "NativeEditPlan",
         "Trusted internal native writer changed")
    internal = native[1]
    changed_guids: tuple[str, ...]
    changed_fields: tuple[str, ...]
    if task == "geometry_test_14":
        need(not removed and len(changes) == 1 and len(before) == 1,
             "Exactly one original Slab state must change")
        guid, p, n = changes[0]
        edited_fields = tuple(k for k in ("dimXM", "dimYM")
                              if abs(n[k] - p[k]) > 1e-6)
        need(len(edited_fields) == 1, "One slab dimension state change only")
        etree.SubElement(internal, Q + "SetSlabRectangleDimensions", {
            "ifcGuid": guid,
            "newXDimM": _num(n["dimXM"]),
            "newYDimM": _num(n["dimYM"]),
        })
        changed_guids, changed_fields = (guid,), edited_fields
    elif task == "geometry_test_15":
        need(not removed and len(changes) == 1 and len(before) == 4,
             "Exactly one source Column world position may change")
        guid, _, n = changes[0]
        etree.SubElement(internal, Q + "MoveColumnPlacement", {
            "ifcGuid": guid,
            "newWorldOriginXM": _num(n["worldXM"]),
            "newWorldOriginYM": _num(n["worldYM"]),
        })
        changed_guids, changed_fields = (guid,), ("worldXM", "worldYM")
    elif task == "topological_test_11":
        need(not removed and len(changes) == 2 and len(before) == 2,
             "Both source Columns must reflect the shared mapped depth")
        values = [n["extrusionDepthM"] for _, _, n in changes]
        need(abs(values[0] - values[1]) < 1e-9,
             "Source shared geometry requires same final depth for two columns")
        etree.SubElement(internal, Q + "SetAllMappedColumnDepth", {
            "newDepthM": _num(values[0]),
        })
        changed_guids = tuple(sorted(x[0] for x in changes))
        changed_fields = ("extrusionDepthM",)
    elif task == "topological_test_17":
        need(not changes and 1 <= len(removed) <= 9 and len(before) == 10,
             "Original managed Column membership deletion only")
        delete_op = etree.SubElement(internal, Q + "DeleteColumnsByGuid")
        for guid in removed:
            etree.SubElement(delete_op, Q + "DeleteColumn", {
                "ifcGuid": guid,
            })
        changed_guids, changed_fields = removed, ("membership",)
    else:
        raise DeclarativeState050Error("Unknown managed state capability")

    # Validate the private plan through the existing v0.45 native writer.
    # No task solution/GUID guess is embedded in or returned to the model.
    internal_xml = etree.tostring(native, encoding="utf8",
                                   xml_declaration=True, pretty_print=False)
    from src.runtime.experimental_v45_original_native_mutations import (
        parse_original_native_edit_plan_v045,
    )
    parsed = parse_original_native_edit_plan_v045(
        source, internal_xml, source_sha=source_sha,
    )
    need(parsed.task_id == task and
         set(parsed.target_guids) == set(changed_guids),
         "Trusted native writer disagrees with source-state diff identity")
    need(file_hash(source) == source_sha,
         "Original IFC changed during semantic document diff")
    return SemanticDiff050(
        task, source_sha, changed_guids, changed_fields, internal_xml,
    )


def compile_original_declarative_state_v050(
    source: Path, edited_xml: bytes, destination_mm: Path,
    *, source_sha: str,
) -> SemanticDiff050:
    """Trusted source-diff compiler; host MUST independently oracle-check IFC."""
    result = parse_original_declarative_state_diff_v050(
        source, edited_xml, source_sha=source_sha,
    )
    candidate = Path(destination_mm)
    need(candidate.parent.is_dir() and not candidate.exists()
         and not candidate.is_symlink(),
         "New native candidate path required; never overwrite IFC")
    compilation = compile_original_native_mutation_v045(
        source, result.internal_native_writer_xml, candidate,
        source_sha=source_sha,
    )
    need(compilation.task_id == result.task_id and
         file_hash(source) == source_sha,
         "Trusted native compiler source identity mismatch")
    return result
