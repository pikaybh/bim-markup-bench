"""Post-frozen, source-only I0 vs existing D0 on two original BIBIMBAP cases.

Sequence matters: run truly independent imperative I0 from the public prompt
and raw IFC FIRST. Freeze and independently validate its native candidate.
Only THEN reconstruct/check the previously frozen declarative D0 and inspect
the pinned original author score/target-consistency *outside the authoring
environment*. No paid API, hidden ground truth, data downloads or target lists
in output. NOT a prospective blinded LLM study.
"""
from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import tempfile

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.util.unit
from lxml import etree

from tools.bibimbap_v015_imperative_i0 import compile_imperative_i0
from tools.oracle_bibimbap_v14_window_delete import verify_source_native_window_delete
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head

PUBLIC_TASKS = ("geometry_test_18", "geometry_test_19")


class SourceOnlyParityBlocked(ValueError):
    pass


def _frozen_d0_by_case(path: Path) -> dict:
    record = json.loads(path.read_text(encoding="utf8"))
    if record["original_public_45_denominator_retained"] != 45 or        record["real_matched_XML_Python_LLM_runs"] != 0:
        raise SourceOnlyParityBlocked("Historic D0 research population changed")
    return {
        x["original_public_task_id"]: x
        for x in record["source_original_IFC4X3_geometry_test_18_19_original_frozen_D0_cases"]
    }


def _authored_D0_reproduction(source: Path, public_task_id: str,
                               question: str, output: Path, frozen: dict):
    """Called ONLY after I0 candidate is frozen and independently validated."""
    from src.runtime.experimental_v14_native_window_delete import (
        native_full_window_state_v14, compile_native_hosted_windows_v14,
    )
    from tools.audit_bibimbap_v14_original_hosted_d0 import (
        _source_only_selection, _edited_window_state,
    )
    model = ifcopenshell.open(str(source))
    picked, _ = _source_only_selection(public_task_id, question, model)
    state = native_full_window_state_v14(source)
    edited_xml = _edited_window_state(state.xml, picked)
    if sha256(edited_xml).hexdigest() != frozen[
        "developer_XML_whole_Window_inventory_after_deleting_nodes_sha256"
    ]:
        raise SourceOnlyParityBlocked("Historic developer XML changed: do not retune")
    report = compile_native_hosted_windows_v14(source, edited_xml, output)
    if report.output_sha256 != frozen["original_native_candidate_sha256"]:
        raise SourceOnlyParityBlocked("Historic frozen D0 IFC changed")
    return tuple(sorted(picked)), report


def _postfreeze_pinned_author_discrepancy(
        author: Path, original_mm: Path, i0_mm: Path,
        task: str, selected_i0: tuple[str, ...]) -> dict:
    """Read original author static target IDs only AFTER BOTH writers finish.

    No original author target GUID values are emitted or passed to a writer,
    not even if they disagree with the independent source-derived I0.
    """
    script = author / "data" / "tests" / f"{task}.py"
    root = ast.parse(script.read_text(encoding="utf8"))
    declarations = [
        ast.literal_eval(entry.value)
        for entry in root.body if isinstance(entry, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "WINDOW_GUIDS"
                for t in entry.targets)
    ]
    if len(declarations) != 1 or not isinstance(declarations[0], list):
        raise SourceOnlyParityBlocked("Pinned original author target declaration missing")
    targets = declarations[0]
    if not targets or len(set(targets)) != len(targets):
        raise SourceOnlyParityBlocked("Original author target declaration duplicate or empty")
    old = ifcopenshell.open(str(original_mm))
    present = 0
    absent = 0
    for guid in targets:
        try:
            obj = old.by_guid(guid)
        except RuntimeError:
            absent += 1
        else:
            if not obj.is_a("IfcWindow"):
                raise SourceOnlyParityBlocked("Pinned author target class incorrect")
            present += 1
    from tools.bibimbap_matched25_cli import grade_author
    result = grade_author(author, original_mm, i0_mm, task)
    if not (result.get("status") == "AUTHOR_WORKER_FAILED"
            and result.get("error_type") == "RuntimeError" and absent > 0):
        raise SourceOnlyParityBlocked("Unexpected original author score/status drift")

    # Independently probe the *public* integrity predicates against a
    # source-derived I0 Window. Not original scorer target GUIDs.
    import sys
    if str(author) not in sys.path:
        sys.path.insert(0, str(author))
    from data.tests.delete_integrity import openings_deleted
    from data.tests.integrity_utils import non_target_elements_unchanged
    # No path to a grader or its private targets inside I0 program.
    original_window = old.by_guid(selected_i0[0])
    old_opening = original_window.FillsVoids[0].RelatingOpeningElement
    native = ifcopenshell.open(str(i0_mm))
    retained_opening = native.by_guid(old_opening.GlobalId)
    if not retained_opening.is_a("IfcOpeningElement"):
        raise SourceOnlyParityBlocked("I0 unexpectedly deleted source opening")
    retained_opening_predicate = openings_deleted(old, native, selected_i0[0])
    if retained_opening_predicate:
        raise SourceOnlyParityBlocked("Author Opening predicate changed")

    # A counterfactual scratch candidate (never substituted for D0/I0)
    # drops the Opening and checks the original non-target Root constraint.
    # This is intentionally NOT a valid scientific edit candidate.
    with tempfile.TemporaryDirectory(prefix="bibimbap-author-contradiction-") as d:
        scratch = Path(d) / "counterfactual_edited.ifc"
        ifcopenshell.api.root.remove_product(
            native, product=native.by_guid(old_opening.GlobalId)
        )
        native.write(str(scratch))
        missing_opening_fails_nontarget = not non_target_elements_unchanged(
            old, ifcopenshell.open(str(scratch)), selected_i0
        )
    if not missing_opening_fails_nontarget:
        raise SourceOnlyParityBlocked("Original non-target Root predicate behavior changed")
    return {
        "source_original_author_declared_window_targets": len(targets),
        "source_original_author_targets_present_before_edit": present,
        "source_original_author_targets_absent_before_edit": absent,
        "source_original_author_window_GUID_values_never_emitted": True,
        "original_author_worker_status": result["status"],
        "original_author_worker_exception": result["error_type"],
        "original_author_numeric_score": None,
        "retained_original_opening_fails_author_openings_deleted": True,
        "scratch_deleted_original_opening_fails_author_nontarget_preservation":
            missing_opening_fails_nontarget,
        "scratch_candidate_used_for_scoring_or_D_I_comparison": False,
        "author_evaluator_or_dataset_modified": False,
        "postfreeze_forensics_not_an_official_replacement_grade": True,
    }


def audit(author: Path, data: Path, frozen_d0_path: Path) -> dict:
    if _head(author) != AUTHOR_SHA or _head(data) != DATA_SHA:
        raise SourceOnlyParityBlocked("Original pinned author or data revision changed")
    # No author score or private test target is imported here.
    all_public = {row["test_id"]: row for row in public_45(author, data)}
    if len(all_public) != 45:
        raise SourceOnlyParityBlocked("Original 45 public task population changed")
    observed = []
    for task in PUBLIC_TASKS:
        public = all_public[task]
        original_mm = data / "ifc" / public["original_source_ifc_relpath"]
        original_sha = file_hash(original_mm)
        if original_sha != public["original_ifc_sha256"]:
            raise SourceOnlyParityBlocked("Raw public IFC not pinned")
        question = public["public_question"]
        with tempfile.TemporaryDirectory(prefix="bmb-144-source-only-i0-") as d:
            temp = Path(d)
            source = temp / "original_source_m.ifc"
            ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(original_mm)), "METER"
            ).write(str(source))
            normalized_sha = file_hash(source)
            # CRITICAL ORDER: no D0 report or writer imported before this.
            i0_path = temp / "original_public_imperative_i0.ifc"
            i0 = compile_imperative_i0(source, task, question, i0_path)
            i0_sha = file_hash(i0_path)
            if i0_sha != i0.result_sha256 or i0.source_sha256 != normalized_sha:
                raise SourceOnlyParityBlocked("Imperative source/candidate hash drift")
            i0_proof = verify_source_native_window_delete(
                source, i0_path, i0.selected_original_window_guids,
                expected_original_source_sha256=normalized_sha,
                expected_output_sha256=i0_sha,
            )
            # D0 is reconstructed ONLY after I0 is physically frozen.
            frozen = _frozen_d0_by_case(frozen_d0_path)[task]
            if frozen["original_normalized_metres_source_sha256"] != normalized_sha                or frozen["original_public_ifc_sha256"] != original_sha                or frozen["original_public_question_sha256"] != i0.public_question_sha256:
                raise SourceOnlyParityBlocked("Previously frozen D0 input not same as I0")
            d0_path = temp / "reproduced_frozen_direct_XML_D0.ifc"
            d0_guids, d0 = _authored_D0_reproduction(
                source, task, question, d0_path, frozen
            )
            d0_proof = verify_source_native_window_delete(
                source, d0_path, d0_guids,
                expected_original_source_sha256=normalized_sha,
                expected_output_sha256=d0.output_sha256,
            )
            if d0_guids != i0.selected_original_window_guids:
                raise SourceOnlyParityBlocked("Independent public task D0/I0 target selections differ")
            if (i0_proof["independently_expected_deleted_owned_root_guids"] !=
                d0_proof["independently_expected_deleted_owned_root_guids"]):
                raise SourceOnlyParityBlocked("Source native root closure differs")
            if (i0_proof["actual_world_native_product_meshes_preserved"] !=
                d0_proof["actual_world_native_product_meshes_preserved"]):
                raise SourceOnlyParityBlocked("Native world geometry preservation differs")
            # Convert both candidates back to raw public mm only for post-frozen
            # author-scoring compatibility; this does not alter original IFCs.
            i0_mm = temp / "imperative_public_mm.ifc"
            if abs(ifcopenshell.util.unit.calculate_unit_scale(
                ifcopenshell.open(str(i0_path))
            ) - 1.) > 1e-8:
                raise SourceOnlyParityBlocked("I0 candidate units changed")
            ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(i0_path)), "MILLIMETER"
            ).write(str(i0_mm))
            freeze_before_score = (file_hash(i0_path), file_hash(d0_path))
            postfreeze = _postfreeze_pinned_author_discrepancy(
                author, original_mm, i0_mm, task, i0.selected_original_window_guids
            )
            if (file_hash(i0_path), file_hash(d0_path)) != freeze_before_score:
                raise SourceOnlyParityBlocked("Candidate modified after original scorer")
            if file_hash(original_mm) != original_sha or file_hash(source) != normalized_sha:
                raise SourceOnlyParityBlocked("Original public IFC source mutated")
            observed.append({
                "public_task_id": task,
                "public_original_ifc_sha256": original_sha,
                "source_metres_ifc_sha256": normalized_sha,
                "public_task_instruction_sha256": i0.public_question_sha256,
                "ifc_schema": "IFC4X3",
                "ifcopenshell_version": ifcopenshell.version,
                "independent_i0_selection_from_original_public_source_only": True,
                "i0_before_D0_reference_access_enforced": True,
                "original_window_target_count": len(d0_guids),
                "native_target_guid_set_sha256":
                    sha256("|".join(d0_guids).encode("ascii")).hexdigest(),
                "original_native_ifc_I0_candidate_sha256": i0_sha,
                "frozen_declarative_D0_reproduced_sha256": d0.output_sha256,
                "candidate_ifc_bytes_identical_not_required":
                    (i0_sha == d0.output_sha256),
                "D0_independent_source_oracle_status": d0_proof["status"],
                "I0_independent_source_oracle_status": i0_proof["status"],
                "same_source_native_window_target_set": True,
                "same_original_source_root_deletion_closure": True,
                "same_unrelated_world_native_product_mesh_preservation": True,
                "preserved_unrelated_native_product_mesh_count":
                    i0_proof["actual_world_native_product_meshes_preserved"],
                "postfreeze_original_author_diagnostic": postfreeze,
            })
    return {
        "status": "ORIGINAL_PUBLIC_HOSTED_WINDOW_DEVELOPER_D0_I0_SOURCE_ONLY_PARITY_V015",
        "issue": "https://github.com/pikaybh/bim-markup-bench/issues/144",
        "original_author_revision": AUTHOR_SHA,
        "original_dataset_revision": DATA_SHA,
        "original_population_45_unmodified": 45,
        "fully_blinded_or_preregistered_LLM_experiment": False,
        "original_author_scored_task_successes_from_this_audit": None,
        "source_only_native_edit_not_official_task_grading": True,
        "original_native_IfcOpeningElement_retained": True,
        "native_original_Opening_delete_supported": False,
        "source_native_IfcBeam_or_IfcSpace_edit_supported": False,
        "I0_is_developer_authored_not_a_real_model_trial": True,
        "D0_is_developer_authored_not_a_real_model_trial": True,
        "original_45_case_full_both_arm_write_parity_proven": False,
        "paid_model_or_provider_calls": 0,
        "full_repository_regression_from_this_audit": None,
        "cases": observed,
    }


def main():
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument("--author", required=True, type=Path)
    arg.add_argument("--data", required=True, type=Path)
    arg.add_argument("--frozen-d0-report", required=True, type=Path)
    arg.add_argument("--output", required=True, type=Path)
    a = arg.parse_args()
    if a.output.exists() or a.output.is_symlink():
        arg.error("Will not overwrite an existing report or frozen evidence")
    result = audit(a.author, a.data, a.frozen_d0_report)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x", encoding="utf8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, ensure_ascii=False)
        stream.write("\n")
    print("v0.15 independent original I0/D0 source-only parity:", len(result["cases"]),
          "cases, 0 official scores, 0 LLM calls")
    print("report_sha256=" + file_hash(a.output))


if __name__ == "__main__":
    main()
