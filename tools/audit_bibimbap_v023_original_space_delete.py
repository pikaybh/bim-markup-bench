"""v0.23 real original public test_20 D0/I0 native-IFC byte-parity audit.

D0: remove the *existing* public room's ordinary <Space> tag from a
complete projected declarative building.xml document; trusted external
compiler validates the whole state diff before changing IFC.
I0: independent developer code uses IfcOpenShell on a native input IFC.
Both run only on an original-public pinned IFC copy/in memory; compare
exact resulting IFC bytes and independent original author scorer unchanged.
No provider/LLM, hidden grader-target list or Git main modifications.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
from ifcopenshell.util.unit import calculate_unit_scale

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45, grade_author
from tools.bibimbap_matched25_tools import XmlSourceEditSession, file_hash
from tools.bibimbap_v023_original_space_i0 import independent_public_space_delete_i0

ROOT = Path(__file__).resolve().parents[1]
PARENT_V022_PATH = "reports/bibimbap_v022_original45_task_relevant_roles_and_xml_input_20261115.json"
PARENT_V022_SHA = "f606994defa7517f898e22ee6e39d5e82da6dc40288c1b38cec25c98b7cd492e"
TASK_ID = "test_20"


class OriginalSpaceParityBlocked(ValueError):
    pass


def _require(ok: bool, reason: str) -> None:
    if not ok:
        raise OriginalSpaceParityBlocked(reason)


def public_original_space_target_and_declarative_source(
    public_question: str, projected_xml: bytes,
) -> tuple[str, bytes]:
    import re
    from src.security.agent_boundary import check_xml_bytes

    guids = re.findall(r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",
                       public_question)
    _require(len(guids) == 1 and len(set(guids)) == 1,
             "Original PUBLIC instruction requires one unambiguous room GUID")
    guid = guids[0]
    xml = projected_xml.decode("utf8")
    matches = [line for line in xml.splitlines(keepends=True)
               if "<Space " in line and 'ifcGuid="' + guid + '"' in line]
    _require(len(matches) == 1 and matches[0].strip().endswith("/>"),
             "Public target Space not uniquely represented as existing declarative state")
    # The result is complete *ordinary declarative XML* source: one existing
    # state element removed. No imperative <Delete> or command fields.
    updated = xml.replace(matches[0], "", 1).encode("utf8")
    check_xml_bytes(updated)
    _require(updated != projected_xml and guid not in updated.decode("utf8"),
             "Declarative edited source still includes the public room")
    return guid, updated


def independent_original_native_identity_oracle(
    source_ifc: Path, candidate_ifc: Path, deleted_public_guid: str,
) -> dict:
    """Does NOT use compiler preflight or original author grader."""
    source = ifcopenshell.open(str(source_ifc))
    candidate = ifcopenshell.open(str(candidate_ifc))
    if (source.schema != candidate.schema or source.schema != "IFC4X3"
            or abs(calculate_unit_scale(source)-.001)>1e-12
            or abs(calculate_unit_scale(candidate)-.001)>1e-12):
        raise OriginalSpaceParityBlocked("Original native schema/units changed")
    original = {x.GlobalId:x.is_a() for x in source.by_type("IfcProduct")}
    final = {x.GlobalId:x.is_a() for x in candidate.by_type("IfcProduct")}
    _require(deleted_public_guid in original
             and original[deleted_public_guid] == "IfcSpace"
             and deleted_public_guid not in final,
             "Native output did not delete the targeted original public IfcSpace")
    _require({g:k for g,k in original.items() if g!=deleted_public_guid} == final,
             "Original unrelated IfcProduct identities/classes changed")
    other_spaces = {x.GlobalId for x in source.by_type("IfcSpace")} - {deleted_public_guid}
    _require(other_spaces == {x.GlobalId for x in candidate.by_type("IfcSpace")},
             "Original other native Rooms, including opaque XML rooms, did not survive")
    _require(all(x.GlobalId not in other_spaces for x in candidate.by_type("IfcWall")),
             "Unrelated original room reclassified as Wall")
    return {
        "status": "INDEPENDENT_ORIGINAL_NATIVE_PUBLIC_ROOM_IDENTITY_PASS",
        "source_product_count": len(original),
        "candidate_product_count": len(final),
        "removed_original_room_count": 1,
        "remaining_original_rooms_unchanged": len(other_spaces),
        "all_other_original_IfcProduct_classes_and_GUIDs_unchanged": True,
    }


def audit_original20(
    root: Path, author: Path, data: Path,
) -> dict:
    _require(_head(author) == AUTHOR_SHA and _head(data) == DATA_SHA,
             "Original public author/data Git revision mismatch")
    parent_path = root / PARENT_V022_PATH
    _require(parent_path.is_file() and not parent_path.is_symlink()
             and file_hash(parent_path) == PARENT_V022_SHA,
             "Frozen parent source/role report SHA changed")
    parent = json.loads(parent_path.read_text(encoding="utf8"))
    originals = {x["test_id"]:x for x in public_45(author,data)}
    _require(len(originals) == 45 and TASK_ID in originals,
             "Original 45-task public cohort drift")
    case = originals[TASK_ID]
    _require(case["crud"] == "delete" and case["category"] == "basic",
             "Original task20 category/CRUD changed")
    previous = {x["task_id"]:x for x in parent[
        "all45_per_task_actual_source_role_and_admission_rows"]}
    _require(len(previous) == 45 and set(originals)==set(previous),
             "Original public all45 benchmark population or parent changed")
    row = previous[TASK_ID]
    _require(row["public_operation_family"] == "DELETE_NAMED_ROOM"
             and row["required_roles_with_missing_editable_XML_objects"] == ["Space"]
             and row["current_direct_XML_session_source_admission"] ==
                 "SCHEMA_AND_UNIT_ADMISSIBLE_PROJECTION_WRITE_NOT_PROVEN"
             and row["original_native_IFC_sha256"] == case["original_ifc_sha256"]
             and row["original_public_question_sha256"] == case["public_question_sha256"],
             "Frozen original task20 source roles/input or public hashes changed")
    original_source = data / "ifc" / case["original_source_ifc_relpath"]
    source_sha = file_hash(original_source)
    _require(source_sha == case["original_ifc_sha256"], "Original native IFC source SHA drift")
    with TemporaryDirectory(prefix="bmb-v023-original-public20-") as temp:
        folder = Path(temp)
        declarative = XmlSourceEditSession(original_source, folder/"D0")
        target_guid, changed_xml = public_original_space_target_and_declarative_source(
            case["public_question"], declarative.original_xml)
        result = declarative.call("submit_building_xml",{"xml_text":changed_xml.decode("utf8")})
        _require(result.get("status") == "ok"
                 and result.get("native_ifc_committed") is True
                 and declarative.output_ifc is not None
                 and declarative.output_ifc.is_file(),
                 "Original public XML declaration did not commit native IFC")
        _require(result.get("compile_status") ==
                 "COMMITTED_SCOPED_IFC4X3_TOPOLOGY_EDIT",
                 "Unexpected native XML compiler operation status")
        native_i_path = folder / "native_independent_I0_mm.ifc"
        i_result = independent_public_space_delete_i0(
            original_source,target_guid,native_i_path)
        _require(i_result["status"] ==
                 "INDEPENDENT_DEVELOPER_NATIVE_IFC_SPACE_DELETION_CREATED"
                 and not i_result["output_contains_target_space"],
                 "Developer Python native I0 failed to delete original Space")
        d_sha=file_hash(declarative.output_ifc)
        i_sha=file_hash(native_i_path)
        _require(d_sha == i_sha,
                 "D0/I0 original native output IFC bytes differ")
        native_d=independent_original_native_identity_oracle(
            original_source,declarative.output_ifc,target_guid)
        native_i=independent_original_native_identity_oracle(
            original_source,native_i_path,target_guid)
        _require(native_d == native_i,
                 "Independent native original source identity oracle disagrees")
        score_d=grade_author(author,original_source,declarative.output_ifc,TASK_ID)
        score_i=grade_author(author,original_source,native_i_path,TASK_ID)
        _require(score_d == score_i
                 and score_d["status"] == "AUTHOR_SCORED"
                 and score_d["original_author_score"] == .5
                 and score_d["original_author_metrics"] ==
                    {"integrity_constraint":0.0,"object_not_exists":1.0}
                 and score_d["original_author_full_mark"] is False,
                 "Unmodified original author grader differs or unexpectedly changed")
        _require(file_hash(original_source) == source_sha,
                 "Original IFC was modified by D0/I0 native experiments")
    _require(_head(author) == AUTHOR_SHA and _head(data) == DATA_SHA,
             "Original author/data revisions changed after experiment")
    return {
        "status": "ACTUAL_ORIGINAL_TEST20_D0_I0_DEVELOPER_NATIVE_IFC_BYTES_EQUAL_AUTHOR_HALF_SCORE",
        "issue": "https://github.com/pikaybh/bim-markup-bench/issues/160",
        "pinned_original_author_git_sha": AUTHOR_SHA,
        "pinned_original_public_data_git_sha": DATA_SHA,
        "pinned_parent_v022_report_sha256": PARENT_V022_SHA,
        "original_all45_intention_to_test_denominator":45,
        "original_task_id":TASK_ID,
        "original_public_question_sha256":case["public_question_sha256"],
        "original_native_source_IFC_sha256":source_sha,
        "source_IFC_schema":"IFC4X3",
        "original_source_native_IFC_length_units":"MILLIMETER",
        "original_task_required_role_current_XML_omission":"Space",
        "declarative_D0_edit_is_single_existing_Space_node_removed":True,
        "imperative_I0_uses_independent_IfcOpenShell_native_root_remove_product":True,
        "D0_original_native_output_sha256":d_sha,
        "I0_original_native_output_sha256":i_sha,
        "actual_full_IFC_output_bytes_identical":True,
        "native_original_source_independent_product_identity_oracle":native_d,
        "pinned_original_author_D0_score":score_d,
        "pinned_original_author_I0_score":score_i,
        "actual_new_developer_D0_I0_pair_original_task_count":1,
        "prior_frozen_developer_D0_I0_byte_equal_original_cases":5,
        "post_v023_distinct_developer_D0_I0_byte_equal_original_cases":6,
        "prior_frozen_both_original_author_callable_cases":3,
        "post_v023_distinct_developer_both_original_author_callable_cases":4,
        "pinned_original_author_reference_missing_cases_unchanged":2,
        "other_original_public_same_protocol_edit_cases_unverified":39,
        "existing_pinned_v020_v021_v022_reports_updated":False,
        "original_author_scorer_source_modified":False,
        "native_model_original_IFC_source_modified":False,
        "new_full_original45_native_information_or_write_parity_proven":False,
        "original_author_full_mark_achieved":False,
        "original_author_integrity_constraint_result":0.0,
        "new_real_paired_LLM_model_calls":0,
        "paid_provider_USD":0,
        "new_full_original45_developer_causal_representation_study_claim":False,
        "new_actual_XML_IFC2X3_or_IFC4_write_support":False,
        "other_original_IFC_Source_Space_deletion_universally_supported":False,
        "raw_target_GUID_original_IFC_or_public_question_text_in_report":False,
    }


def main() -> None:
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--author", type=Path, required=True)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():
        p.error("Refuse to overwrite frozen original experiment evidence")
    result=audit_original20(a.root,a.author,a.data)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x",encoding="utf8",newline="\n") as out:
        json.dump(result,out,ensure_ascii=False,sort_keys=True,indent=2)
        out.write("\n")
    print("V023_ORIGINAL20",result["status"])
    print("D0_I0_SHA",result["D0_original_native_output_sha256"])
    print("PAIRED_DEVELOPER",result["post_v023_distinct_developer_D0_I0_byte_equal_original_cases"],
          "BOTH_AUTHOR_SCORED",result["post_v023_distinct_developer_both_original_author_callable_cases"])
    print("ORIGINAL_AUTHOR_SCORE",result["pinned_original_author_D0_score"]["original_author_score"])
    print("REAL_MODEL_CALLS",result["new_real_paired_LLM_model_calls"],
          "REPORT_SHA256",sha256(a.output.read_bytes()).hexdigest())


if __name__=="__main__":
    main()
