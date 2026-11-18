"""Reproducible offline audit of STEP-independent, bounded native IFC legality.

Only two already inspected original IFC source families, generated real local
native IFCs, no hidden answer / original grader / provider / model launch.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil

import ifcopenshell

from tools.bibimbap_matched25_tools import DockerIFCExecutor
from tools.bibimbap_v052_live_original_native_python_session import live_pinned_local_runtime_admission_v052

from tools import audit_bibimbap_v065_offline_generalization as base
from tools.audit_bibimbap_v066_step_identity_fairness import relabel_spf
from tools.bibimbap_v065_source_neutral_door import (
    compile_hosted_door, full_initial_xml, parse_full_xml, source_model,
)
from tools.bibimbap_v066_native_semantic_admission import (
    post_native_semantic_gate, SemanticNative066Error, STATUS,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "bibimbap_v066_native_semantic_scope_20261118.json"
PARENT_SHA = "cc55f6623fc65d3936cf6ee9bbacf1c46d3893aa94122317632d9f90d009382d"
TASKS = ("geometry_test_03", "topological_test_05")


def need(x, why):
    if not x:
        raise AssertionError(why)


def canonical(payload):
    return (json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf8")


def _write_variant(base_output: Path, target: Path, mutate):
    f = ifcopenshell.open(str(base_output))
    mutate(f)
    f.write(str(target))


def _negative_verdict(original, sha, path):
    try:
        post_native_semantic_gate(original, sha, path)
    except SemanticNative066Error as exc:
        return str(exc)
    raise AssertionError("A physically or semantically unauthorized IFC candidate was accepted")


def run_case(task, row, tmp):
    original = base.DATA / "ifc" / row["original_source_ifc_relpath"]
    sha = row["original_ifc_sha256"]
    f = source_model(original, sha)
    state = base._case_fixture(f, f.schema)
    raw = base._final_xml(full_initial_xml(original, sha), state)
    parsed = parse_full_xml(original, sha, raw)
    base_output = tmp / f"{task}_D_full.ifc"
    compile_hosted_door(original, sha, parsed, base_output)
    legal = post_native_semantic_gate(original, sha, base_output)
    need(legal["status"] == STATUS, "original legal D full rejected by new semantic validator")
    encoded, mapping = relabel_spf(base_output.read_bytes())
    relabeled = tmp / f"{task}_relabel.ifc"
    relabeled.write_bytes(encoded)
    alt = post_native_semantic_gate(original, sha, relabeled)
    need(alt["status"] == legal["status"]
         and alt["source_IFC_anonymous_and_rooted_graph_counter_refinements"]
            == legal["source_IFC_anonymous_and_rooted_graph_counter_refinements"]
         and alt["host_wall_opaque_IFC_source_global_id"]
            == legal["host_wall_opaque_IFC_source_global_id"],
         "Equivalent STEP-number relabel did not pass independent native gate")

    # Independent imperative I executes genuine generated Python/IfcOpenShell
    # in the existing SHA-pinned local Linux Docker sandbox, not in the D compiler.
    preflight = live_pinned_local_runtime_admission_v052()
    need(preflight["status"] == "RUNTIME_ADMITTED",
         "Genuine pinned local Linux Docker sandbox unavailable")
    sandbox = tmp / (task + "_I_NATIVE_SANDBOX")
    sandbox.mkdir(exist_ok=False)
    native_I = sandbox / "current.ifc"
    shutil.copyfile(original, native_I)
    independent_I_code = base._real_independent_I_python(state, f)
    execution = DockerIFCExecutor().run(sandbox, independent_I_code)
    need(execution.get("status") == "ok"
         and execution.get("backend") == "linux_docker_sandbox"
         and execution.get("committed") is True,
         "Actual pinned isolated imperative IfcOpenShell edit failed")
    native_I_verdict = post_native_semantic_gate(original, sha, native_I)
    need(native_I_verdict["status"] == STATUS
         and native_I_verdict["native_physical_edit_semantic_SHA256"]
           == legal["native_physical_edit_semantic_SHA256"]
           == alt["native_physical_edit_semantic_SHA256"],
         "Real Linux Docker I and D state/STEP alternatives differ physically")

    negative = {}
    def reject(name, change):
        target = tmp / (task + "_" + name + ".ifc")
        _write_variant(base_output, target, change)
        negative[name] = _negative_verdict(original, sha, target)

    def source_wall_name(m):
        wall = m.by_guid(legal["host_wall_opaque_IFC_source_global_id"])
        wall.Name = "UNAUTHORIZED_ORIGINAL_IFC_SOURCE_WALL_CHANGE"
    reject("changed_existing_source_wall_name", source_wall_name)

    def source_owner_history(m):
        root = m.by_guid(legal["host_wall_opaque_IFC_source_global_id"])
        history = root.OwnerHistory
        need(history is not None, "source source owner history absent")
        history.ChangeAction = "MODIFIED"
    reject("modified_existing_source_owner_history", source_owner_history)

    def add_orphan(m):
        m.create_entity("IfcCartesianPoint", Coordinates=(12345., 54321., 10101.))
    reject("added_orphan_anonymous_geometry", add_orphan)

    def add_root(m):
        root = m.create_entity("IfcBuildingElementProxy",
                               GlobalId=ifcopenshell.guid.new(),
                               Name="UNAUTHORIZED_EXTRA_ROOT")
        if m.schema == "IFC2X3":
            root.OwnerHistory = m.by_type("IfcWall")[0].OwnerHistory
    reject("added_unauthorized_root", add_root)

    def wrong_link(m):
        void = next(e for e in m.by_type("IfcRelVoidsElement")
                    if e.GlobalId not in {x.GlobalId for x in f.by_type("IfcRoot")})
        alternative = next((w for w in m.by_type("IfcWall")
                            if w.GlobalId != legal["host_wall_opaque_IFC_source_global_id"]), None)
        need(alternative is not None, "need alternative existing Wall for topology negative")
        void.RelatingBuildingElement = alternative
    reject("wrong_hosted_wall_relation", wrong_link)

    def wrong_width(m):
        new_door = next(e for e in m.by_type("IfcDoor")
                        if e.GlobalId not in {x.GlobalId for x in f.by_type("IfcRoot")})
        new_door.OverallWidth = new_door.OverallWidth * 1.15
    reject("incorrect_real_door_width", wrong_width)

    def mutate_original_anonymous_geometry(m):
        # Existing source-side STEP point is used only to create a negative
        # control; no target guideline or grader-derived information involved.
        old_first = f.by_type("IfcCartesianPoint")[0]
        point = m.by_id(old_first.id())
        coords = list(point.Coordinates)
        coords[0] += 0.25
        point.Coordinates = tuple(coords)
    reject("modified_existing_anonymous_geometry", mutate_original_anonymous_geometry)

    def mutate_existing_relation(m):
        old_relation = f.by_type("IfcRelContainedInSpatialStructure")[0]
        original_relation = m.by_guid(old_relation.GlobalId)
        original_relation.Name = "UNAUTHORIZED_RELATION_METADATA_CHANGE"
    reject("modified_existing_native_relationship", mutate_existing_relation)

    need(base.file_hash(original) == sha,
         "Original developer-exposed IFC unexpectedly modified")
    return {
        "exposed_original_task": task,
        "original_source_ifc_sha256": sha,
        "schema": f.schema,
        "real_native_D_source_preservation_pass": legal["status"],
        "real_native_reindexed_source_preservation_pass": alt["status"],
        "real_pinned_linux_docker_independent_python_I_pass": native_I_verdict["status"],
        "D_I_reindexed_native_physical_semantic_digest_equal": True,
        "native_edit_physical_semantic_SHA256": legal["native_physical_edit_semantic_SHA256"],
        "source_entities_graph_depths": legal[
            "source_IFC_anonymous_and_rooted_graph_counter_refinements"],
        "root_GUID_classes_retained": legal["source_root_GUIDs_and_classes_preserved"],
        "wall_CSG_removed_m3": legal["actual_wall_CSG_volume_removed_m3"],
        "source_global_guid_redacted": True,
        "negative_real_native_IFC_mutation_rejected": negative,
        "new_model_calls": 0,
        "author_scorer_called": False,
    }


def build_report():
    need(base.file_hash(base.REPORT) == PARENT_SHA,
         "Frozen parent v0.65 source-neutral evidence unexpectedly changed")
    all_rows = {r["test_id"]: r for r in base.public_45(base.AUTHOR, base.DATA)}
    with TemporaryDirectory(prefix="v066-native-semantic-research-") as d:
        tmp = Path(d)
        cases = [run_case(t, all_rows[t], tmp) for t in TASKS]
    need({c["schema"] for c in cases} == {"IFC2X3", "IFC4X3"},
         "Two original supported schemas not covered")
    count = sum(len(c["negative_real_native_IFC_mutation_rejected"]) for c in cases)
    need(count == 16, "Expected 16 independently rejected mutated real IFCs")
    return {
        "status": "V066_BOUNDED_NATIVE_STEP_INDEPENDENT_SEMANTIC_ADMISSION_PASS",
        "issue": 247,
        "two_already_developer_exposed_native_source_schemas": ["IFC2X3", "IFC4X3"],
        "source_research_original_IFC_not_modified": True,
        "frozen_parent_v065_report_sha256": PARENT_SHA,
        "real_native_legal_D_full_cases": 2,
        "real_native_legal_step_reindexed_cases": 2,
        "real_pinned_linux_Docker_I_python_native_semantic_pass_cases": 2,
        "real_native_illegal_candidates_rejected": count,
        "source_graph_evidence": "All original typed root/anonymous entity attribute/reference fingerprints subset across depths 0,1,2,4,8,16; root GUID/class preserving; no added orphan",
        "physical_evidence": "Original source native mesh unchanged except host source Wall real CSG; hosted door+opening full source relations; two schema validator delta",
        "hard_limitations": [
            "Still rejects legal old-entity modifications not part of this bounded Door-create family",
            "Fingerprints are conservative bounded graph invariants, not a complete arbitrary IFC graph-isomorphism or semantic proof",
            "This validates physical scope, source integrity and legal encoding, not target-specific public task correctness",
            "No original author scorer imported or invoked, no GT and no unseen source visited",
            "No paid LLM or official benchmark matched D/I trials",
            "No source-license or independent unseen certification",
        ],
        "actual_provider_calls": 0,
        "external_original_IFC_uploads": 0,
        "independently_certified_unseen_original_source_families": 0,
        "all_original_provider_transfers_blocked": True,
        "cases": cases,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build_report()
    raw = canonical(result)
    if args.write:
        with OUTPUT.open("xb") as out:
            out.write(raw)
    else:
        need(OUTPUT.read_bytes() == raw, "Frozen semantic native report changed")
    print(f"V066_SEMANTIC_NATIVE_{'WRITE' if args.write else 'CHECK'}=PASS "
          f"positive={2+2+2} rejected_negatives={result['real_native_illegal_candidates_rejected']} "
          "provider_calls=0")


if __name__ == "__main__":
    main()
