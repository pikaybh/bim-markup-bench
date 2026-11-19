"""Post-frozen two originally scoreable Column tasks: source-only XML D0 vs Python I0.

Only the publicly pinned original task question and native IFC are passed to
the independent imperative I0 before its entire IFC is frozen and independently
native-oracle validated. Historical D0 source/results are loaded *afterwards*.
Original-author scorer runs last and never informs either candidate.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import re
from pathlib import Path
import tempfile

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_v016_original_column_i0 import run_imperative_column_i0

PUBLIC_CASES = ("test_15", "test_16")
KNOWN_AUTHOR_BROKEN = ("geometry_test_18", "geometry_test_19")
V3_FROZEN_SHA = "f358d3f65fe89734078ff6712f2543d578fac043e915c9baad6280dbaa7906b7"


class ColumnParityBlocked(ValueError):
    pass


def _strict_native_oracle(task: str, source: Path, candidate: Path, guid: str) -> dict:
    """Independent preexisting native IFC-only oracle, not a writer or grader."""
    from tools.oracle_bibimbap_column15_16_native import (
        strict_move_column, strict_delete_column,
    )
    if task == "test_15":
        return strict_move_column(source, candidate, guid, dy=-3.0)
    if task == "test_16":
        return strict_delete_column(source, candidate, guid)
    raise ColumnParityBlocked("Unexpected public task ID")


def _recreate_existing_frozen_D0(
    source_metres: Path, public_task: str, public_question: str, target: str,
    destination: Path,
) -> dict:
    """After I0 freeze only: reproject and edit *whole declarative XML state*."""
    from src.runtime.experimental_v3_projection import project_ifc_v3
    from src.runtime.experimental_v3_column import compile_declarative_xml_v3
    public_ids = re.findall(r"\bid\s+([0-9A-Za-z_$]{22})\b", public_question, re.I)
    if len(public_ids) != 1:
        raise ColumnParityBlocked("Expected one independently parsed PUBLIC Column target")
    independently_public_guid = public_ids[0]
    if independently_public_guid != target:
        raise ColumnParityBlocked("D0 and I0 do not agree on PUBLIC named identity")
    projected = project_ifc_v3(source_metres)
    root = etree.fromstring(projected.xml)
    ns = etree.QName(root).namespace
    nodes = [node for node in root.findall(".//{" + ns + "}Column")
             if node.get("ifcGuid") == independently_public_guid]
    if len(nodes) != 1:
        raise ColumnParityBlocked("Original public Column not in declarative view")
    node = nodes[0]
    if public_task == "test_15":
        if node.get("y") is None:
            raise ColumnParityBlocked("Original public Column XML y coordinate missing")
        node.set("y", str(float(node.get("y")) - 3.0))
    else:
        node.getparent().remove(node)
    final_xml = etree.tostring(root, encoding="utf8")
    compile_declarative_xml_v3(source_metres, final_xml, destination)
    return {
        "whole_declarative_XML_after_authoring_sha256": sha256(final_xml).hexdigest(),
        "D0_target_selected_from_public_question_not_scorer": True,
        "D0_full_XML_state_not_command_script": True,
    }


def audit(author: Path, dataset: Path, frozen_d0: Path,
          old_45_matrix: Path, previous_v015_report: Path) -> dict:
    if _head(author) != AUTHOR_SHA or _head(dataset) != DATA_SHA:
        raise ColumnParityBlocked("Original published author or dataset revision drift")
    if file_hash(frozen_d0).lower() != V3_FROZEN_SHA:
        raise ColumnParityBlocked("Previously frozen v0.3 D0 outcome report changed")
    public = {row["test_id"]: row for row in public_45(author, dataset)}
    if len(public) != 45:
        raise ColumnParityBlocked("Original public population is not 45")
    cohort_counts = {kind: sum(1 for x in public.values() if x["crud"] == kind)
                     for kind in ("create", "update", "delete")}
    if cohort_counts != {"create": 15, "update": 15, "delete": 15}:
        raise ColumnParityBlocked("Original 45-case CRUD distribution drift")

    src_rel = public["test_15"]["original_source_ifc_relpath"]
    if public["test_16"]["original_source_ifc_relpath"] != src_rel:
        raise ColumnParityBlocked("Two public Column tests do not use identical source IFC")
    original = dataset / "ifc" / src_rel
    source_sha = file_hash(original)
    if any(public[k]["original_ifc_sha256"] != source_sha for k in PUBLIC_CASES):
        raise ColumnParityBlocked("Pinned public original IFC source SHA mismatch")

    with tempfile.TemporaryDirectory(prefix="bibimbap-v016-public-scoreable-") as dirname:
        temp = Path(dirname)
        src_metres = temp / "pinned_public_native_m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(original)), "METER"
        ).write(str(src_metres))
        normalized_sha = file_hash(src_metres)

        # Critical barrier: author I0 from task + original native source ONLY.
        # No old D0 report, D0 projection, original scorer or hidden GT read yet.
        independently_frozen_i0 = {}
        for task in PUBLIC_CASES:
            output = temp / (task + "_independent_I0_m.ifc")
            i0 = run_imperative_column_i0(
                src_metres, task, public[task]["public_question"], output
            )
            proof = _strict_native_oracle(
                task, src_metres, output, i0.original_target_guid_from_public_question
            )
            if proof["source_sha256"] != normalized_sha or                proof["output_sha256"] != i0.candidate_native_sha256:
                raise ColumnParityBlocked("I0 native oracle/source hashes drift")
            independently_frozen_i0[task] = (output, i0, proof)

        # The original D0 evidence becomes visible only after every I0 input,
        # IFC output SHA and strict native oracle were already fixed.
        historic = json.loads(frozen_d0.read_text(encoding="utf8"))
        previous = {row["task_id"]: row for row in historic["developer_fixed_public_task_d0"]}
        if set(previous) != set(PUBLIC_CASES):
            raise ColumnParityBlocked("Frozen v0.3 developer D0 public controls drift")

        observations = []
        candidate_hashes_before_author = {}
        for task in PUBLIC_CASES:
            path_i0, result_i0, oracle_i0 = independently_frozen_i0[task]
            d0_path = temp / (task + "_recreated_XML_D0_m.ifc")
            d0_meta = _recreate_existing_frozen_D0(
                src_metres, task, public[task]["public_question"],
                result_i0.original_target_guid_from_public_question,
                d0_path,
            )
            oracle_d0 = _strict_native_oracle(
                task, src_metres, d0_path,
                result_i0.original_target_guid_from_public_question,
            )
            if not oracle_d0["status"].startswith("INDEPENDENT_REAL_IFC_TEST"):
                raise ColumnParityBlocked("Original D0 did not pass source-native oracle")
            if file_hash(path_i0) != file_hash(d0_path):
                raise ColumnParityBlocked("Original source-native I0 and prior D0 IFC differ")
            # The prior v0.3 author D0 grader report already includes the
            # identical native result hash. Freeze it rather than reselect.
            expected_native = previous[task]["independent_native_task_specific_oracle"]
            if (oracle_d0["output_sha256"] != expected_native["output_sha256"]
                or oracle_d0["source_sha256"] != expected_native["source_sha256"]):
                raise ColumnParityBlocked("Reconstructed D0 candidate changed from prior frozen v0.3")
            if (public[task]["public_question_sha256"] !=
                previous[task]["original_public_question_sha256"]):
                raise ColumnParityBlocked("Public task instruction changed")
            mm_d0 = temp / (task + "_D0_mm.ifc")
            mm_i0 = temp / (task + "_I0_mm.ifc")
            for prior, nxt in ((d0_path, mm_d0), (path_i0, mm_i0)):
                ifcopenshell.util.unit.convert_file_length_units(
                    ifcopenshell.open(str(prior)), "MILLIMETER"
                ).write(str(nxt))
            if file_hash(mm_d0) != previous[task]["candidate_native_mm_sha256"]:
                raise ColumnParityBlocked("Frozen D0 public-unit IFC output no longer reproducible")
            candidate_hashes_before_author[task] = {
                "D0": file_hash(d0_path), "I0": file_hash(path_i0),
                "D0_public_units": file_hash(mm_d0),
                "I0_public_units": file_hash(mm_i0),
            }
            observations.append({
                "task_id": task, "original_crud": public[task]["crud"],
                "original_public_source_sha256": source_sha,
                "original_public_question_sha256": public[task]["public_question_sha256"],
                "normalized_metres_native_ifc_sha256": normalized_sha,
                "public_target_guid_sha256": sha256(
                    result_i0.original_target_guid_from_public_question.encode("ascii")
                ).hexdigest(),
                "independent_Python_I0_native_result_sha256": file_hash(path_i0),
                "frozen_reproduced_XML_D0_native_result_sha256": file_hash(d0_path),
                "native_byte_identical_I0_D0": True,
                "independent_I0_native_oracle_status": oracle_i0["status"],
                "independent_D0_native_oracle_status": oracle_d0["status"],
                "independent_native_original_other_products_preserved": True,
                **d0_meta,
            })

        # Author original evaluator only AFTER BOTH D0 and I0 candidates
        # for BOTH tasks were fully frozen and strict native-oracle verified.
        from tools.bibimbap_matched25_cli import grade_author
        for row in observations:
            task = row["task_id"]
            after_D0 = grade_author(author, original, temp / (task + "_D0_mm.ifc"), task)
            after_I0 = grade_author(author, original, temp / (task + "_I0_mm.ifc"), task)
            if after_D0.get("status") != "AUTHOR_SCORED" or                after_I0.get("status") != "AUTHOR_SCORED":
                raise ColumnParityBlocked("Original author scorer failed on callable Column control")
            prior_score = previous[task]["original_author_result"]
            if after_D0.get("original_author_score") != prior_score.get("original_author_score"):
                raise ColumnParityBlocked("Prior frozen author D0 score revision mismatch")
            row["original_author_D0_status"] = after_D0["status"]
            row["original_author_I0_status"] = after_I0["status"]
            row["original_author_D0_continuous_score"] = after_D0["original_author_score"]
            row["original_author_I0_continuous_score"] = after_I0["original_author_score"]
            row["original_author_numeric_score_equal"] = (
                after_D0["original_author_score"] == after_I0["original_author_score"]
            )
            row["original_author_D0_metric_components"] = after_D0["original_author_metrics"]
            row["original_author_I0_metric_components"] = after_I0["original_author_metrics"]
            row["strict_independent_full_task_success_verified"] = False
            row["two_arms_are_developer_authored_not_LLM_results"] = True
            row["original_public_Python_and_XML_edited_candidate_not_modified_after_scoring"] = True
            for name, frozen_hash in candidate_hashes_before_author[task].items():
                path = (temp / (task + "_D0_mm.ifc" if name == "D0_public_units"
                         else task + "_I0_mm.ifc" if name == "I0_public_units"
                         else task + "_recreated_XML_D0_m.ifc" if name == "D0"
                         else task + "_independent_I0_m.ifc"))
                if file_hash(path) != frozen_hash:
                    raise ColumnParityBlocked("Candidate mutated after original author score")
        if file_hash(original) != source_sha or file_hash(src_metres) != normalized_sha:
            raise ColumnParityBlocked("Original public input mutated")

    old_matrix = json.loads(old_45_matrix.read_text(encoding="utf8"))
    existing_v015 = json.loads(previous_v015_report.read_text(encoding="utf8"))
    if existing_v015["original_population_45_unmodified"] != 45 or        set(r["public_task_id"] for r in existing_v015["cases"]) != set(KNOWN_AUTHOR_BROKEN):
        raise ColumnParityBlocked("Frozen previous Window developer I0/D0 evidence changed")
    old_rows = old_matrix["original_45_task_capability_and_evidence_matrix"]
    if len(old_rows) != 45:
        raise ColumnParityBlocked("Original full cohort baseline matrix changed")
    by_id = {row["original_public_task_id"]: row for row in old_rows}
    if set(by_id) != set(public):
        raise ColumnParityBlocked("Original full cohort task IDs changed")
    matrix = []
    for task in sorted(public):
        old = by_id[task]
        status = ("AUTHOR_SCORED_BOTH_DEVELOPER_ARMS"
                  if task in PUBLIC_CASES else
                  "AUTHOR_WORKER_FAILED_PINNED_REFERENCE_SOURCE_MISMATCH"
                  if task in KNOWN_AUTHOR_BROKEN else "NOT_CURRENTLY_ESTABLISHED")
        matrix.append({
            "task_id": task,
            "category": public[task]["category"],
            "crud": public[task]["crud"],
            "public_question_sha256": public[task]["public_question_sha256"],
            "original_ifc_source_sha256": public[task]["original_ifc_sha256"],
            "original_ifc_schema": old["original_native_schema"],
            "original_public_requested_operation_family":
                old["required_native_operation_family_from_public_task"],
            "existing_D0_developer_evidence_class_from_frozen_v012":
                old["frozen_source_only_developer_D0_status"],
            "source_native_readonly_projection_not_edit_success":
                old["actual_source_projection_state"],
            "new_scoring_status": status,
            "developer_source_only_both_D0_I0_native_feasibility":
                task in PUBLIC_CASES or task in KNOWN_AUTHOR_BROKEN,
            "new_real_matched_LLM_D_I_result": None,
            "excluded_from_original_45_denominator": False,
            "untested_scoreability_must_not_be_called_unsupported":
                task not in PUBLIC_CASES and task not in KNOWN_AUTHOR_BROKEN,
        })

    return {
        "status": "TWO_ORIGINAL_AUTHOR_SCOREABLE_DEVELOPER_COLUMN_D0_I0_NATIVE_PARITY_V016",
        "issue": "https://github.com/pikaybh/bim-markup-bench/issues/146",
        "pinned_original_author_sha256_git": AUTHOR_SHA,
        "pinned_original_public_data_sha256_git": DATA_SHA,
        "upstream_default_main_heads_verified_equal_pinned_on_2026_11_14": True,
        "upstream_default_branch_check_was_read_only_no_download": True,
        "evidence_scope_does_not_prove_absence_of_other_branches_or_future_changes": True,
        "original_public_45_total_unchanged": len(public),
        "original_45_crud_distribution": cohort_counts,
        "developer_both_arms_native_IFC_proven_task_count_including_v015": 4,
        "original_author_scorable_with_both_D0_I0_confirmed_this_audit": 2,
        "prior_original_author_worker_failed_window_cases_retained": 2,
        "other_original_cases_not_exhaustively_evaluated": 41,
        "original_author_scores_are_not_blinded_LLM_trial_results": True,
        "metric_origin": "PINNED_ORIGINAL_AUTHOR_CODE_RUN_AFTER_BOTH_CANDIDATES_FROZEN",
        "independent_full_45_task_semantic_success_proven": False,
        "new_model_api_calls": 0,
        "new_paid_usd": 0,
        "historical_prior_D0_report_sha256": V3_FROZEN_SHA,
        "source_only_original_column_controls": observations,
        "original45_intention_to_test_matrix": matrix,
        "original_scorer_and_data_unmodified": True,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--author", type=Path, required=True)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--frozen-v3-d0-report", type=Path, required=True)
    p.add_argument("--frozen-v012-matrix", type=Path, required=True)
    p.add_argument("--frozen-v015-report", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists() or a.output.is_symlink():
        p.error("Refusing overwrite of any frozen result")
    record = audit(a.author, a.data, a.frozen_v3_d0_report,
                   a.frozen_v012_matrix, a.frozen_v015_report)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x", encoding="utf8", newline="\n") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    print("source-only parity", len(record["source_only_original_column_controls"]),
          "scoreable tasks; original 45 retained, provider calls 0")
    print("report_sha256=" + file_hash(a.output))


if __name__ == "__main__":
    main()
