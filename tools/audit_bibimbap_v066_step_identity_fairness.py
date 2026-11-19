"""v0.66 bounded native IFC fairness counterexample: STEP identity is not meaning.

ONLY two already developer-exposed original IFCs, no unseen source, original
author grader or model-provider call. A bijective relabeling of IFC STEP IDs
changes no other byte of the SPF payload: its exact inverse recovers the
original byte-for-byte. Native open, IFC schema and physical meshes are checked.
The pre-existing v0.65 strict gate wrongly rejects this serialisation-equivalent
IFC because it binds source entities to their old numeric STEP IDs.

This does NOT yet license arbitrary restructuring, extra Roots or modification
of original Psets/relations; no live causal D/I evaluation is attempted.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.util.unit

from tools import audit_bibimbap_v065_offline_generalization as a065
from tools.bibimbap_v065_source_neutral_door import (
    full_initial_xml,
    parse_full_xml,
    compile_hosted_door,
    post_native_ifc_gate,
    source_model,
    NeutralDoor065Error,
    _mesh_bounds,
    _volume,
    _schema_error_counter,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "bibimbap_v066_step_number_false_rejection_20261118.json"
SOURCE_TASKS = ("geometry_test_03", "topological_test_05")
PARENT065_SHA = "cc55f6623fc65d3936cf6ee9bbacf1c46d3893aa94122317632d9f90d009382d"


class RelabelError(ValueError):
    pass


def need(p: bool, reason: str) -> None:
    if not p:
        raise RelabelError(reason)


def canonical(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf8")


def scan_spf(raw: bytes, mapping: dict[int, int] | None = None):
    """Return remapped SPF bytes, defined IDs and reference IDs.

    Lexically treats quoted STEP literals (including doubled quotes) and
    /* comments */ as opaque bytes. Only external #decimal tokens change.
    Reject unclosed strings/comments and duplicate/unbound entity references.
    No IFC content/geometry serialization or inferred model semantics.
    """
    need(raw.startswith(b"ISO-10303-21;"),
         "Expected a complete STEP Physical File, not an arbitrary fragment")
    out = bytearray()
    definitions = []
    references = []
    i = 0
    quote = False
    comment = False
    while i < len(raw):
        c = raw[i]
        next_byte = raw[i + 1] if i + 1 < len(raw) else None
        if comment:
            if c == 42 and next_byte == 47:  # */
                out.extend(raw[i:i+2])
                i += 2
                comment = False
            else:
                out.append(c)
                i += 1
            continue
        if quote:
            if c == 39 and next_byte == 39:  # '' escaped STEP quote
                out.extend(raw[i:i+2])
                i += 2
            else:
                out.append(c)
                i += 1
                if c == 39:
                    quote = False
            continue
        if c == 47 and next_byte == 42:  # /*
            out.extend(raw[i:i+2])
            i += 2
            comment = True
            continue
        if c == 39:  # '
            out.append(c)
            quote = True
            i += 1
            continue
        if c == 35 and next_byte is not None and 48 <= next_byte <= 57:
            j = i + 1
            while j < len(raw) and 48 <= raw[j] <= 57:
                j += 1
            val = int(raw[i+1:j])
            references.append(val)
            k = j
            while k < len(raw) and raw[k] in b" \t\r\n":
                k += 1
            if k < len(raw) and raw[k] == 61:  # '=' means entity label
                definitions.append(val)
            target = val if mapping is None else mapping.get(val)
            need(target is not None, "Unexpected unmapped SPF numeric reference")
            out.extend(b"#" + str(target).encode("ascii"))
            i = j
            continue
        out.append(c)
        i += 1
    need(not comment and not quote, "Malformed STEP literal/comment")
    need(len(definitions) > 0 and len(definitions) == len(set(definitions)),
         "No unique STEP entity labels")
    need(set(references) == set(definitions),
         "Unexpected undefined or unreferenced STEP numeric IDs")
    if mapping is not None:
        need(set(mapping) == set(definitions)
             and len(set(mapping.values())) == len(mapping)
             and all(int(v) > 0 for v in mapping.values()),
             "STEP ID remapping must be bijective and cover all entities")
    return bytes(out), sorted(definitions), references


def relabel_spf(raw: bytes):
    _, ids, _ = scan_spf(raw)
    mapping = dict(zip(ids, reversed(ids)))
    need(any(x != y for x, y in mapping.items()), "No nontrivial STEP relabeling")
    relabeled, _, _ = scan_spf(raw, mapping)
    inverse = {v: k for k, v in mapping.items()}
    recovered, _, _ = scan_spf(relabeled, inverse)
    need(recovered == raw, "Inverse label remapping did not restore every byte")
    return relabeled, mapping


def native_equivalence(original: Path, alternative: Path, mapping: dict[int, int]):
    """Independent bounded validation of re-labeled, otherwise SAME SPF bytes."""
    old_bytes = original.read_bytes()
    new_bytes = alternative.read_bytes()
    recovered, _, _ = scan_spf(new_bytes, {v: k for k, v in mapping.items()})
    need(recovered == old_bytes,
         "Native IFC differs from accepted result beyond bijective STEP labels")
    old = ifcopenshell.open(str(original))
    new = ifcopenshell.open(str(alternative))
    need(old.schema_identifier == new.schema_identifier,
         "IFC native schema version drift")
    old_entities = list(old)
    new_entities = list(new)
    need(len(old_entities) == len(new_entities) == len(mapping),
         "Native IFC entity population drift")
    old_roots = {r.GlobalId: (r.is_a(), r.id()) for r in old.by_type("IfcRoot")}
    new_roots = {r.GlobalId: (r.is_a(), r.id()) for r in new.by_type("IfcRoot")}
    need({g: v[0] for g, v in old_roots.items()}
         == {g: v[0] for g, v in new_roots.items()},
         "IFC Root GUID/type population changed")
    ids_changed = sum(old_roots[g][1] != new_roots[g][1] for g in old_roots)
    need(ids_changed > 0, "Expected at least one changed STEP ID")
    need(abs(ifcopenshell.util.unit.calculate_unit_scale(old) -
             ifcopenshell.util.unit.calculate_unit_scale(new)) < 1e-12,
         "Native IFC units drifted")
    products = old.by_type("IfcProduct")
    checked = 0
    for p in products:
        q = new.by_guid(p.GlobalId)
        need(q is not None and q.is_a() == p.is_a(), "Native IFC product type drift")
        if p.Representation is None:
            need(q.Representation is None, "Native non-geometric product became geometric")
            continue
        a, b = _mesh_bounds(p), _mesh_bounds(q)
        need(all(abs(float(a[j][k])-float(b[j][k])) < 1e-6
                 for j in range(3) for k in range(2)),
             "Native world geometry bounding box changed")
        need(abs(_volume(p)-_volume(q)) < 1e-6,
             "Native world shape volume changed")
        checked += 1
    need(_schema_error_counter(original) == _schema_error_counter(alternative),
         "Native IFC schema errors changed on identical semantic content")
    return {
        "native_schema_identifier": old.schema_identifier,
        "native_total_ifc_entities": len(old_entities),
        "native_root_guids_and_classes_preserved": len(old_roots),
        "native_root_STEP_IDs_reassigned": ids_changed,
        "native_geometry_products_physically_equal": checked,
        "source_semantic_payload_inverse_byte_identical": True,
        "native_IFC_schema_error_delta": 0,
        "original_result_and_alternative_ROOT_semantics_equal": True,
    }


def build_report() -> dict:
    need(a065.file_hash(a065.REPORT) == PARENT065_SHA,
         "Parent source-neutral audit SHA changed")
    tasks = {r["test_id"]: r for r in a065.public_45(a065.AUTHOR, a065.DATA)}
    result = []
    for task in SOURCE_TASKS:
        row = tasks[task]
        src = a065.DATA / "ifc" / row["original_source_ifc_relpath"]
        source_sha = row["original_ifc_sha256"]
        f = source_model(src, source_sha)
        st = a065._case_fixture(f, f.schema)
        initial = full_initial_xml(src, source_sha)
        final = a065._final_xml(initial, st)
        state = parse_full_xml(src, source_sha, final)
        with TemporaryDirectory(prefix="v066-step-number-evidence-") as tmp:
            baseline = Path(tmp)/"source_native_D_full.ifc"
            alternative = Path(tmp)/"semantic_same_relabelled.ifc"
            compile_hosted_door(src, source_sha, state, baseline)
            verdict = post_native_ifc_gate(src, source_sha, baseline)
            modified, mapping = relabel_spf(baseline.read_bytes())
            alternative.write_bytes(modified)
            comparable = native_equivalence(baseline, alternative, mapping)
            try:
                post_native_ifc_gate(src, source_sha, alternative)
            except NeutralDoor065Error as exc:
                strict_rejection = str(exc)
            else:
                raise RelabelError("Original strict gate must reject re-labeled source")
            need("ALL ORIGINAL native STEP IDs" in strict_rejection,
                 "Expected strict STEP-number-only rejection, not a legality failure")
            need(a065.file_hash(src) == source_sha, "Original source changed in audit")
            result.append({
                "already_developer_exposed_original_task": task,
                "original_source_sha256": source_sha,
                "v065_strict_original_D_full_gate_passed": True,
                "same_native_IFC_after_one_to_one_STEP_ID_only_relabel": comparable,
                "v065_strict_gate_rejects_legal_reencoding": True,
                "v065_rejection_reason": strict_rejection,
                "native_original_wall_CSG_cut_m3": verdict[
                    "actual_wall_csg_volume_removed_m3"],
                "input_source_IFC_preserved_by_sha": True,
            })
    return {
        "status": "V066_NATIVE_IFC_STEP_NUMBERS_NOT_SEMANTIC_IDENTITY_COUNTEREXAMPLE_PASS",
        "issue": 247,
        "parent_v065_frozen_report_sha256": PARENT065_SHA,
        "source_cohort": "Only two already developer-exposed original IFC source files; NO unseen IFC",
        "real_native_alternative_encoding_cases": len(result),
        "alternative_IFC_natively_reopened": True,
        "alternative_IFC_full_original_SPF_semantic_payload_invertibly_same": True,
        "alternative_IFC_geometry_same": True,
        "two_IFC_schemas": ["IFC2X3", "IFC4X3"],
        "strict_gate_false_rejections_due_to_STEP_number_only": len(result),
        "no_original_author_scorer_or_GT_read": True,
        "no_model_paid_calls_or_provider_upload": True,
        "independent_validator_scope": "Bytewise inversion plus native GUID/class/count, mesh bbox/volume and schema-error equality; not arbitrary edit equivalence",
        "not_yet_proven": [
            "Arbitrary Python IFC native edits that use different legal geometry representations",
            "Semantically equivalent non-STEP-identity preservation of existing material/placement/relations",
            "Native edit source-neutral move or delete parity",
            "Full task-specific author-grader correctness",
            "LLM D-vs-I fairness or superiority",
        ],
        "cases": result,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build_report()
    raw = canonical(report)
    if args.write:
        with OUTPUT.open("xb") as o:
            o.write(raw)
    else:
        need(OUTPUT.read_bytes() == raw, "v0.66 native source regression drift")
    print(f"V066_STEP_FAIRNESS_{'WRITE' if args.write else 'CHECK'}=PASS "
          f"real_native_reencodings={len(report['cases'])} "
          f"strict_false_rejects={report['strict_gate_false_rejections_due_to_STEP_number_only']} "
          "LLM_calls=0")


if __name__ == "__main__":
    main()
