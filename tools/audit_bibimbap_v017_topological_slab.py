"""v0.17: original public Slab-on-Slab source-only independent I0 vs frozen XML D0.

Audit ordering: (1) original public 45 + native source pin; (2) independent
imperative I0 and outside IFC-only oracle, candidate frozen; (3) old
declarative D0 reconstructed and native-oracle frozen; (4) author scorer
runs last for both candidates; (5) original all-45 denominator retained.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import tempfile

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v017_independent_slab_on_slab_i0 import (
    run_original_topological_slab_i0,
)

TASK = "topological_test_15"
FROZEN_V04_SHA = "98166dc3a6c606996a5f9bd43e3b0b26fb2852fb61e1c64ea1154aaefc630fec"
FROZEN_V016_SHA = "162ff7408429062b4e80abb3fe48bb6bb1b0c0bff51260d04d0a616d7a104ae7"
XML_NS = "{urn:bim-markup-bench:toy:v0}"


class SlabParityBlocked(ValueError):
    pass


def _rebuild_frozen_D0(
    normalized_source: Path, public_question: str, upper_guid: str,
    lower_guid: str, input_only_z_delta: float, candidate: Path,
) -> dict:
    # This method is not called until the independent I0 output is frozen.
    from src.runtime.experimental_v4_projection import project_ifc_v4, _slab_mesh_bbox
    from src.runtime.experimental_v4_slab import compile_declarative_xml_v4

    ids = re.fullmatch(
        r"Change the position of the slab with id ([0-9A-Za-z_$]{22}) "
        r"that it lays on the slab with the id ([0-9A-Za-z_$]{22})\.",
        public_question,
    )
    if ids is None or ids.groups() != (upper_guid, lower_guid):
        raise SlabParityBlocked("Independent public question identity parsing mismatch")
    native = ifcopenshell.open(str(normalized_source))
    upper = native.by_guid(ids[1])
    lower = native.by_guid(ids[2])
    upper_min, _ = _slab_mesh_bbox(upper)
    _, lower_max = _slab_mesh_bbox(lower)
    delta_from_original_D0_inputs = float(lower_max[2] - upper_min[2])
    if abs(delta_from_original_D0_inputs - input_only_z_delta) > 1e-8:
        raise SlabParityBlocked("Historical D0 and independently derived native contact differ")

    original_whole_xml = project_ifc_v4(normalized_source)
    tree = etree.fromstring(original_whole_xml.xml)
    nodes = [
        node for node in tree.find(XML_NS + "Elements").findall(XML_NS + "Slab")
        if node.get("ifcGuid") == ids[1]
    ]
    if len(nodes) != 1 or nodes[0].get("z") is None:
        raise SlabParityBlocked("Public upper Slab not uniquely represented in full XML state")
    nodes[0].set("z", str(float(nodes[0].get("z")) + delta_from_original_D0_inputs))
    updated_full_xml = etree.tostring(tree, encoding="utf8")
    compiled = compile_declarative_xml_v4(normalized_source, updated_full_xml, candidate)
    if not compiled.operations or compiled.operations[0].operation != "MOVE_SLAB":
        raise SlabParityBlocked("Frozen XML D0 did not perform native Slab move")
    return {
        "whole_declarative_XML_after_edit_sha256": sha256(updated_full_xml).hexdigest(),
        "original_public_question_only_target": True,
        "D0_trusted_native_compiler_unmodified": True,
        "D0_original_source_mesh_delta_m": delta_from_original_D0_inputs,
    }


def audit(
    author: Path, data: Path, frozen_v04: Path, frozen_v016: Path
) -> dict:
    if _head(author) != AUTHOR_SHA or _head(data) != DATA_SHA:
        raise SlabParityBlocked("Pinned original author/data Git provenance drift")
    tasks = {t["test_id"]: t for t in public_45(author, data)}
    if len(tasks) != 45 or TASK not in tasks:
        raise SlabParityBlocked("Original 45-task public cohort changed")
    counts = {k: sum(1 for t in tasks.values() if t["crud"] == k)
              for k in ("create", "update", "delete")}
    if counts != {"create": 15, "update": 15, "delete": 15}:
        raise SlabParityBlocked("Original 15/15/15 cohort distribution changed")
    public = tasks[TASK]
    original = data / "ifc" / public["original_source_ifc_relpath"]
    source_sha = file_hash(original)
    if source_sha != public["original_ifc_sha256"]:
        raise SlabParityBlocked("Original public source IFC changed")

    with tempfile.TemporaryDirectory(prefix="bibimbap-v017-slab-equal-source-") as tmp:
        root = Path(tmp)
        normalized = root / "original_native_m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(original)), "METER"
        ).write(str(normalized))
        normalized_sha = file_hash(normalized)

        # First and only original-source/public-question imperative authoring:
        # no author grading, D0 XML compiler, D0 report or GT read.
        out_i0 = root / "imperative_native_i0_m.ifc"
        i0 = run_original_topological_slab_i0(
            normalized, public["public_question"], out_i0
        )
        from tools.oracle_bibimbap_slab_v04 import verify_update
        native_i0 = verify_update(
            normalized, out_i0, i0.upper_public_guid, kind="move",
            delta=(0., 0., i0.native_world_z_delta_m),
        )
        if native_i0["output_sha256"] != i0.native_candidate_sha256:
            raise SlabParityBlocked("Independent I0 IFC-only oracle disagreeing with frozen SHA")
        if native_i0["source_sha256"] != normalized_sha:
            raise SlabParityBlocked("I0 changed original native source")

        # Only after I0 is independently frozen, open historical D0 report.
        if file_hash(frozen_v04) != FROZEN_V04_SHA:
            raise SlabParityBlocked("Frozen XML D0 v0.4 evidence changed")
        historic = json.loads(frozen_v04.read_text(encoding="utf8"))
        prev_cases = [
            x for x in historic["tasks"] if x["original_public_task_id"] == TASK
        ]
        if len(prev_cases) != 1:
            raise SlabParityBlocked("No unambiguous prior original task D0 evidence")
        old = prev_cases[0]
        if (old["public_question_sha256"] != public["public_question_sha256"] or
            old["original_source_ifc_sha256"] != source_sha or
            old["developer_fixture"]["operation"] != "MOVE_SLAB"):
            raise SlabParityBlocked("Public task/frozen original D0 record drift")
        d0 = root / "reconstructed_complete_XML_D0_m.ifc"
        d0_meta = _rebuild_frozen_D0(
            normalized, public["public_question"], i0.upper_public_guid,
            i0.lower_public_guid, i0.native_world_z_delta_m, d0,
        )
        native_d0 = verify_update(
            normalized, d0, i0.upper_public_guid, kind="move",
            delta=(0., 0., i0.native_world_z_delta_m),
        )
        historic_native = old["independent_native_slab_oracle"]
        if (native_d0["output_sha256"] != historic_native["output_sha256"]
            or native_d0["source_sha256"] != historic_native["source_sha256"]
            or file_hash(d0) != file_hash(out_i0)):
            raise SlabParityBlocked("Independent I0 or reconstructed D0 did not match prior frozen entire native IFC")
        mm_i0 = root / "imperative_i0_mm.ifc"
        mm_d0 = root / "declarative_D0_mm.ifc"
        for src, dest in ((out_i0, mm_i0), (d0, mm_d0)):
            if ifcopenshell.util.unit.calculate_unit_scale(ifcopenshell.open(str(src))) != 1:
                raise SlabParityBlocked("Native source metre unit changed")
            ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(src)), "MILLIMETER"
            ).write(str(dest))
        if file_hash(mm_d0) != old["candidate_native_mm_sha256"]:
            raise SlabParityBlocked("Original prior XML D0 public-unit IFC result changed")
        frozen_hashes = {
            "I0_source_native": file_hash(out_i0),
            "D0_source_native": file_hash(d0),
            "I0_original_public_units": file_hash(mm_i0),
            "D0_original_public_units": file_hash(mm_d0),
        }

        # The author scorer is invoked only AFTER BOTH complete native IFC
        # candidates have been frozen and independently validated.
        from tools.bibimbap_matched25_cli import grade_author
        scorer_d0 = grade_author(author, original, mm_d0, TASK)
        scorer_i0 = grade_author(author, original, mm_i0, TASK)
        previous_scorer = old["original_author_grade_after_compilation"]
        if scorer_d0.get("status") != "AUTHOR_SCORED" or scorer_i0.get("status") != "AUTHOR_SCORED":
            raise SlabParityBlocked("Official author scorer did not return result for paired original task")
        if scorer_d0 != previous_scorer or scorer_d0 != scorer_i0:
            raise SlabParityBlocked("Prior original author D0 metric changed or independent I0 produced different author metric")
        if any(file_hash(path) != frozen_hashes[key] for key, path in {
            "I0_source_native": out_i0,
            "D0_source_native": d0,
            "I0_original_public_units": mm_i0,
            "D0_original_public_units": mm_d0,
        }.items()):
            raise SlabParityBlocked("Native candidate changed after grading")
        if file_hash(original) != source_sha or file_hash(normalized) != normalized_sha:
            raise SlabParityBlocked("Pinned source IFC changed after paired audit")

    # Prior 45-case matrix is kept in every output, not narrowed to 1.
    if file_hash(frozen_v016) != FROZEN_V016_SHA:
        raise SlabParityBlocked("Previously frozen 45-case v0.16 matrix changed")
    previous = json.loads(frozen_v016.read_text(encoding="utf8"))
    if previous["original_public_45_total_unchanged"] != 45:
        raise SlabParityBlocked("v0.16 original 45 cohort drift")
    previous_rows = previous["original45_intention_to_test_matrix"]
    if len(previous_rows) != 45 or {x["task_id"] for x in previous_rows} != set(tasks):
        raise SlabParityBlocked("Original all-45 intention-to-test matrix drift")
    matrix = []
    for row in previous_rows:
        cur = dict(row)
        if cur["task_id"] == TASK:
            if cur["new_scoring_status"] != "NOT_CURRENTLY_ESTABLISHED":
                raise SlabParityBlocked("Public task previously classified before independent verification")
            cur["new_scoring_status"] = "AUTHOR_SCORED_BOTH_DEVELOPER_ARMS"
            cur["developer_source_only_both_D0_I0_native_feasibility"] = True
            cur["independent_native_original_public_slab_on_slab_contact"] = True
            cur["untested_scoreability_must_not_be_called_unsupported"] = False
        matrix.append(cur)
    summary = {label: sum(1 for r in matrix if r["new_scoring_status"] == label)
               for label in (
                   "AUTHOR_SCORED_BOTH_DEVELOPER_ARMS",
                   "AUTHOR_WORKER_FAILED_PINNED_REFERENCE_SOURCE_MISMATCH",
                   "NOT_CURRENTLY_ESTABLISHED",
               )}
    if summary != {
        "AUTHOR_SCORED_BOTH_DEVELOPER_ARMS": 3,
        "AUTHOR_WORKER_FAILED_PINNED_REFERENCE_SOURCE_MISMATCH": 2,
        "NOT_CURRENTLY_ESTABLISHED": 40,
    }:
        raise SlabParityBlocked("Original 45-case result classification inconsistent")
    return {
        "status": "ORIGINAL_PUBLIC_TOPOLOGICAL_SLAB_DEVELOPER_D0_I0_NATIVE_AND_AUTHOR_PARITY_PASS",
        "issue": "https://github.com/pikaybh/bim-markup-bench/issues/148",
        "original_author_git_sha": AUTHOR_SHA,
        "original_data_git_sha": DATA_SHA,
        "original_public_task_id": TASK,
        "original_source_ifc_sha256": source_sha,
        "original_public_question_sha256": public["public_question_sha256"],
        "native_normalized_source_sha256": normalized_sha,
        "independent_imperative_I0_candidate_native_sha256": frozen_hashes["I0_source_native"],
        "frozen_rebuilt_XML_D0_candidate_native_sha256": frozen_hashes["D0_source_native"],
        "identical_complete_native_IFC_D0_vs_I0": True,
        "original_public_units_candidate_sha256_same": (
            frozen_hashes["I0_original_public_units"] ==
            frozen_hashes["D0_original_public_units"]
        ),
        "independent_native_ifc_only_oracle_I0": native_i0["status"],
        "independent_native_ifc_only_oracle_D0": native_d0["status"],
        "native_upper_slab_z_delta_m_from_original_public_IFC": i0.native_world_z_delta_m,
        "native_source_shared_point_copy_on_write": i0.native_copy_on_write_point,
        "actual_source_xy_contact_area_m2": i0.upper_lower_original_xy_overlap_m2,
        "original_author_scorer_I0": scorer_i0,
        "original_author_scorer_D0": scorer_d0,
        "author_result_not_independent_full_task_success": True,
        "prior_historical_frozen_D0_report_sha256": FROZEN_V04_SHA,
        "prior_historical_frozen_v016_report_sha256": FROZEN_V016_SHA,
        "original_public_45_denominator_unchanged": 45,
        "original_45_create_update_delete_counts": counts,
        "original_author_scoreable_both_dev_arms_total": 3,
        "original_author_reference_unscoreable_cases_total": 2,
        "original_other_untested_same_protocol_total": 40,
        "original_native_D0_I0_both_edit_cases_total": 5,
        "original_45_scoreability_summary": summary,
        "all_45_public_intention_to_test": matrix,
        "original_test14_height_semantics_ambiguity": {
            "prior_D0_grade": "AUTHOR_SCORED_1_POINT",
            "historical_D0_interprets_height_as": "ELEVATION_TRANSLATION_NOT_THICKNESS",
            "public_text_semantics_not_independently_disambiguated": True,
            "excluded_from_new_v017_native_pair_scoreable_increment": True,
        },
        "new_matched_LLM_model_trials": 0,
        "new_paid_provider_calls": 0,
        "new_paid_USD": 0,
        "real_model_causal_XML_vs_Python_evidence": False,
        "full_45_native_write_parity_proven": False,
        "original_source_and_author_evaluator_mutated": False,
        "independently_selected_public_task_previously_D0_scored_nonblinded": True,
        **d0_meta,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--author", type=Path, required=True)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--prior-v04-d0-report", type=Path, required=True)
    p.add_argument("--prior-v016-report", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or args.output.is_symlink():
        p.error("Refusing overwrite of previous evidence")
    report = audit(args.author, args.data, args.prior_v04_d0_report, args.prior_v016_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf8", newline="\n") as out:
        json.dump(report, out, indent=2, sort_keys=True, ensure_ascii=False)
        out.write("\n")
    print("v017_slab_parity", report["status"],
          "author_score_D0", report["original_author_scorer_D0"]["original_author_score"],
          "author_score_I0", report["original_author_scorer_I0"]["original_author_score"])
    print("report_sha256", file_hash(args.output))


if __name__ == "__main__":
    main()
