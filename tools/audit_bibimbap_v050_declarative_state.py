"""Developer-only offline original-public 4-case D-state native IFC evidence.

This file imports v0.48 developer POSITIVE/NEGATIVE source-derived controls.
NEVER expose it, its values, its candidate IFC, or this report to an LLM.
The actual model-facing v0.50 session imports NONE of these fixtures.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lxml import etree

from src.runtime.experimental_v44_original_native_step_readonly import Q, PINS
from src.runtime.experimental_v45_original_native_mutations import (
    project_original_native_mutations_v045,
)
from tools.audit_bibimbap_v045_original4_native_mutations import make_illustrative_plan
from tools.audit_bibimbap_v048_original4_semantic_controls import (
    positive_developer_source_edit,
)
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash, XmlSourceEditSession
from tools.bibimbap_v050_direct_original_state_session import DirectOriginalStateSession050
from tools.bibimbap_v048_independent_original4_semantic_oracle import (
    evaluate_original_semantic048,
)
from src.runtime.experimental_v50_original_declarative_state import (
    project_original_declarative_state_v050, parse_original_declarative_state_diff_v050,
)
from tools.bibimbap_v045_independent_native_mutation_oracle import (
    verify_original_native_mutation_v045,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(r"D:\문서\D__1_Projects\202611")
AUTHOR = BASE / "bibimbap-author-upstream"
DATA = BASE / "bibimbap-author-data"
TASK_IDS = ("geometry_test_14", "geometry_test_15",
            "topological_test_11", "topological_test_17")
FROZEN_PRIOR = {
    "v045": ("bibimbap_v045_original4_native_IFC_typed_writers_20261117.json",
             "7d7518f6c65242f7f00066beeb0229fbb6e42e44d5e841243666ac375105c4b3"),
    "v048": ("bibimbap_v048_original4_semantic_positive_negative_native_controls_20261117.json",
             "ca5f365198bff4f92b14031690b30338d3000adfd70b39c2be4471c9a32d7e08"),
    "v049": ("bibimbap_v049_causal_arm_admission_20261117.json",
             "14a3dd1bd2a00c4fbd7efdafca88c89d00b7c4d247152782d53055b494d54478"),
}
REPORT = ROOT / "reports" / "bibimbap_v050_original4_declarative_state_diff_20261117.json"
SOURCE_MODULE = ROOT / "src" / "runtime" / "experimental_v50_original_declarative_state.py"
HOST_MODULE = ROOT / "tools" / "bibimbap_v050_direct_original_state_session.py"
XSD = ROOT / "spec" / "original_native_declarative_state_v050.xsd"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def developer_control_to_declarative_state(
    original_state_xml: bytes, private_control_typed_xml: bytes,
) -> bytes:
    """Convert fixture's native numbers into FINAL state for testing only.

    This conversion is NOT in the D-arm model tool, compiler or prompts.
    """
    doc = etree.fromstring(original_state_xml)
    command_doc = etree.fromstring(private_control_typed_xml)
    require(doc.tag == Q + "BuildingState"
            and len(doc) == 2 and doc[1].tag == Q + "ManagedElements",
            "Developer-only state fixture XML changed")
    require(command_doc[-1].tag == Q + "NativeEditPlan"
            and len(command_doc[-1]) == 1,
            "Unexpected developer source-only positive/negative control")
    operation = command_doc[-1][0]
    name = operation.tag.removeprefix(Q)
    elements = doc[1]
    by_guid = {x.get("ifcGuid"): x for x in elements}
    if name == "SetSlabRectangleDimensions":
        guid = operation.get("ifcGuid")
        require(guid in by_guid and by_guid[guid].tag == Q + "Slab",
                "Developer slab control missing original state target")
        by_guid[guid].set("dimXM", operation.get("newXDimM"))
        by_guid[guid].set("dimYM", operation.get("newYDimM"))
    elif name == "MoveColumnPlacement":
        guid = operation.get("ifcGuid")
        require(guid in by_guid and by_guid[guid].tag == Q + "Column",
                "Developer Column move missing original state target")
        by_guid[guid].set("worldXM", operation.get("newWorldOriginXM"))
        by_guid[guid].set("worldYM", operation.get("newWorldOriginYM"))
    elif name == "SetAllMappedColumnDepth":
        require(len(by_guid) == 2, "Shared depth fixture requires two Columns")
        for col in elements:
            col.set("extrusionDepthM", operation.get("newDepthM"))
    elif name == "DeleteColumnsByGuid":
        remove = [x.get("ifcGuid") for x in operation]
        require(len(remove) == len(set(remove)) and
                all(g in by_guid for g in remove), "Developer delete fixture invalid")
        for item in list(elements):
            if item.get("ifcGuid") in remove:
                elements.remove(item)
    else:
        raise AssertionError("Unexpected developer control kind")
    result = etree.tostring(doc, xml_declaration=True, encoding="utf8")
    # The model-facing result contains only a final state; never the fixture opcode.
    require(b"NativeEditPlan" not in result
            and b"<Set" not in result and b"<DeleteColumn" not in result,
            "Typed command leaked into D declarative model source")
    return result


def build_report(author: Path = AUTHOR, data: Path = DATA) -> dict:
    for version, (filename, expected) in FROZEN_PRIOR.items():
        require(file_hash(ROOT / "reports" / filename) == expected,
                f"Prior frozen {version} report was modified")
    tasks = {task["test_id"]: task for task in public_45(author, data)}
    require(len(tasks) == 45 and
            Counter(t["crud"] for t in tasks.values()) ==
            {"create": 15, "update": 15, "delete": 15} and
            len({t["original_ifc_sha256"] for t in tasks.values()}) == 31,
            "Original public task source population changed")
    provenance = {}
    records = []
    with TemporaryDirectory(prefix="bmb-v050-developer-only-") as work:
        base = Path(work)
        for idx, task_id in enumerate(TASK_IDS):
            row = tasks[task_id]
            source = data / "ifc" / row["original_source_ifc_relpath"]
            original_sha = row["original_ifc_sha256"]
            require(original_sha in PINS and PINS[original_sha][0] == task_id
                    and PINS[original_sha][2] == row["public_question_sha256"]
                    and file_hash(source) == original_sha,
                    "Original question/IFC source SHA or identity differs")
            snap = project_original_declarative_state_v050(
                source, source_sha=original_sha,
            )
            internal_original = project_original_native_mutations_v045(
                source, source_sha=original_sha,
            ).xml
            require(b"NativeEditPlan" not in snap.xml and
                    b"<Set" not in snap.xml and
                    b"<DeleteColumn" not in snap.xml,
                    "D-state source contains a typed editing command")
            provenance[task_id] = {
                "original_source_sha256": original_sha,
                "public_question_sha256": row["public_question_sha256"],
                "original_crud": row["crud"],
                "model_readonly_original_native_ifc_plus_managed_state_sha256":
                    sha256(snap.xml).hexdigest(),
                "model_original_declarative_XML_bytes": len(snap.xml),
                "scoped_original_managed_element_count":
                    len(etree.fromstring(snap.xml)[1]),
            }
            for control in ("positive", "negative"):
                private_control = (
                    positive_developer_source_edit(
                        internal_original, source, task_id, row["public_question"],
                    ) if control == "positive" else
                    make_illustrative_plan(internal_original, task_id, source)
                )
                edited = developer_control_to_declarative_state(
                    snap.xml, private_control,
                )
                before = file_hash(source)
                diff = parse_original_declarative_state_diff_v050(
                    source, edited, source_sha=original_sha,
                )
                direct = DirectOriginalStateSession050(
                    source, base / f"direct_{idx}_{control}",
                )
                require(len(direct.tools) == 2 and
                        "NativeEditPlan" not in str(direct.tools)
                        and "ifcopenshell" not in str(direct.tools).lower(),
                        "Model tool surface leaked internal command or Python API")
                observed = direct.call("read_building_xml", {})
                require(observed["status"] == "ok"
                        and observed["xml"].encode("utf8") == snap.xml,
                        "Model actually read the exact initial whole XML state")
                result = direct.call("submit_building_xml", {
                    "xml_text": edited.decode("utf8"),
                })
                require(result["status"] == "ok" and
                        result["independent_original_native_ifc_physical_oracle"] == "PASS"
                        and direct.output_ifc is not None,
                        f"Actual D source state edit failed: {task_id} {control} {result}")
                old_typed = XmlSourceEditSession(
                    source, base / f"typed_{idx}_{control}",
                    experimental_original_native_mutations_v045=True,
                )
                baseline_typed_read = old_typed.call("read_building_xml", {})
                require(baseline_typed_read["status"] == "ok"
                        and baseline_typed_read["xml"].encode("utf8") == internal_original,
                        "Original typed baseline unexpectedly changed")
                result_typed = old_typed.call("submit_building_xml", {
                    "xml_text": private_control.decode("utf8"),
                })
                require(result_typed["status"] == "ok" and
                        old_typed.output_ifc is not None,
                        "Prior trusted native write control was not successfully executed")
                require(file_hash(direct.output_ifc) == file_hash(old_typed.output_ifc),
                        "New real native D-state differs bytewise from prior trusted native edit")
                semantic = evaluate_original_semantic048(
                    source, direct.output_ifc,
                    original_sha=original_sha, task_id=task_id,
                    public_question=row["public_question"],
                )
                native_oracle = verify_original_native_mutation_v045(
                    source, direct.output_ifc,
                    submitted_xml=diff.internal_native_writer_xml,
                    source_sha=original_sha,
                    task_id=task_id,
                )
                sem_pass = semantic["candidatePassesIndependentResearchPhysicalPredicate"]
                require(sem_pass == (control == "positive"),
                        "Independent original public source geometric research predicate changed")
                require(native_oracle["status"] ==
                        "V045_INDEPENDENT_ORIGINAL_IFC_NATIVE_MUTATION_ORACLE_PASS",
                        "Independent original/native physical source preservation oracle failed")
                require(file_hash(source) == before,
                        "Original input IFC mutated during new D-state developer evidence")
                # Deliberately exclude developer target GUIDs, values, private
                # typed plans and positive candidate XML from immutable report.
                records.append({
                    "task_id": task_id,
                    "control": control + "_DEVELOPER_ONLY_NOT_MODEL_RESULT",
                    "declarative_state_XML_bytes": len(edited),
                    "declarative_state_sha256": sha256(edited).hexdigest(),
                    "real_D_state_native_IFC_sha256": file_hash(direct.output_ifc),
                    "real_legacy_typed_native_IFC_sha256": file_hash(old_typed.output_ifc),
                    "native_ifc_actual_bytes_equal": True,
                    "independent_original_native_physical_oracle_pass": True,
                    "independent_research_physical_semantic_predicate_pass": sem_pass,
                    "no_author_scoring_or_GT": True,
                    "original_input_IFC_unmodified": True,
                    "D_model_facing_read_calls": 1,
                    "D_model_facing_submit_calls": 1,
                })
    return {
        "status": "V050_SOURCE_NATIVE_DECLARATIVE_STATE_DIFF_FOUR_ORIGINAL_DEVELOPER_CONTROLS_PASS",
        "issue": "https://github.com/pikaybh/bim-markup-bench/issues/215",
        "parent_v049_commit_sha": "58226ef089d55e9ed630cd3e3152b5c1048a90db",
        "original_45_tasks": 45,
        "original_31_unique_source_IFCs": 31,
        "original_CUD_counts": {"CREATE": 15, "UPDATE": 15, "DELETE": 15},
        "selected_four_tasks_NOT_a_preregistered_random_sample": True,
        "other_41_tasks_NOT_attempted": 41,
        "source_and_question_exact_sha256_per_task": provenance,
        "model_facing_XML_contains_final_object_state_not_opcode": True,
        "strict_state_diff_original_GUID_identity": True,
        "original_IFC_source_opaque_unmanaged_pass_through": True,
        "real_native_original_mm_IFC_generated": len(records),
        "real_D_state_vs_typed_legacy_native_candidate_byte_equal": len(records),
        "positive_developer_research_physical_semantic_controls": 4,
        "negative_developer_research_physical_semantic_controls": 4,
        "original_author_benchmark_scores": None,
        "matched_D_state_vs_unrestricted_Python_IFC_model_trials": 0,
        "causal_D_state_vs_I_native_result": None,
        "all_new_D_state_actions_predefined_to_four_native_original_task_scopes": True,
        "independent_oracle": "V045_original_IFC_native_physical_preservation_plus_V048_research_semantics",
        "frozen_parent_report_sha256": {
            v: sha for v, (_, sha) in sorted(FROZEN_PRIOR.items())
        },
        "implementation_sha256": {
            "compiler": file_hash(SOURCE_MODULE),
            "host_session": file_hash(HOST_MODULE),
            "declarative_xsd": file_hash(XSD),
        },
        "records": records,
        "no_paid_model_API_Docker_or_original_author_grader_calls": True,
    }


def canonical(report: dict) -> bytes:
    return (json.dumps(report, ensure_ascii=False, sort_keys=True,
                       indent=2) + "\n").encode("utf8")


def main() -> int:
    arg = argparse.ArgumentParser(description=__doc__)
    modes = arg.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--check", action="store_true")
    opts = arg.parse_args()
    data = canonical(build_report())
    if opts.write:
        with REPORT.open("xb") as f:
            f.write(data)
    else:
        require(REPORT.is_file() and REPORT.read_bytes() == data,
                "Frozen v0.50 report no longer matches exact real native IFC replay")
    print(f"V050_NATIVE_DECLARATIVE_STATE_D0=PASS SOURCE_TASKS=4/45 "
          f"REAL_CANDIDATE_CONTROLS=8 SHA256={sha256(data).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
