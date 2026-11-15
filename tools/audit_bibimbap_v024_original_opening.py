"""v0.24: actual original PUBLIC test_18 full IFC D0/I0 parity and scorer audit.

D0 edits two ordinary original declarative XML state elements (<Opening>,
<Window>) with source-bound GUIDs discovered only from the PUBLIC question
and original IFC. Trusted compiler performs all IFC mutations.
I0 is independently coded native IfcOpenShell and has no XML compiler.
Original author grader remains separate and unmodified.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import re

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.unit

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45, grade_author
from tools.bibimbap_matched25_tools import XmlSourceEditSession, file_hash
from tools.bibimbap_v024_original_opening_i0 import original_public_opening_window_i0

ROOT = Path(__file__).resolve().parents[1]
OLD_V023_REPORT = "reports/bibimbap_v023_original_test20_space_delete_D0_I0_native_parity_20261115.json"
OLD_V023_SHA = "9abcc4ebd21c18891bf08307624a19f6012a981455eca7db89051ae70ce86102"
OLD_V022_REPORT = "reports/bibimbap_v022_original45_task_relevant_roles_and_xml_input_20261115.json"
OLD_V022_SHA = "f606994defa7517f898e22ee6e39d5e82da6dc40288c1b38cec25c98b7cd492e"
TASK_ID = "test_18"


class OriginalOpeningParityBlocked(ValueError):
    pass


def require(value, message: str):
    if not value:
        raise OriginalOpeningParityBlocked(message)


def original_public_opening_xml_edit(
    public_instruction: str, original_xml: bytes,
) -> tuple[str, bytes]:
    """Change exactly two XML state nodes; do not add commands or external IDs."""
    from src.security.agent_boundary import check_xml_bytes

    guids = re.findall(r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",
                       public_instruction)
    require(len(guids)==1, "Original PUBLIC opening instruction target ambiguous")
    guid=guids[0]
    xml=original_xml.decode("utf8")
    opening_matches=[line for line in xml.splitlines(keepends=True)
                     if "<Opening " in line and 'ifcGuid="'+guid+'"' in line]
    require(len(opening_matches)==1, "Public target is not one existing editable Opening")
    opening_line=opening_matches[0]
    target_id=re.search(r'\bid="([^"]+)"',opening_line)
    require(target_id is not None, "Source Opening has no XML state ID")
    window_matches=[line for line in xml.splitlines(keepends=True)
                    if "<Window " in line and
                       'opening="'+target_id.group(1)+'"' in line]
    require(len(window_matches)==1,
            "Original Opening does not have exactly one projected Window filling")
    changed=xml.replace(opening_line,"",1).replace(window_matches[0],"",1).encode("utf8")
    require(changed!=original_xml and guid not in changed.decode("utf8"),
            "Public target was not deleted from editable XML state")
    check_xml_bytes(changed)
    return guid,changed


def independent_original_native_products_oracle(
    original: Path, candidate: Path, opening_guid: str,
    window_guid: str,
) -> dict:
    """Native IFC-only identity/class/geometry source oracle, no XML compiler."""
    a=ifcopenshell.open(str(original))
    b=ifcopenshell.open(str(candidate))
    require(a.schema == b.schema == "IFC4X3",
            "Original IFC schema changed in candidate")
    require(abs(ifcopenshell.util.unit.calculate_unit_scale(a)-.001)<1e-12
            and abs(ifcopenshell.util.unit.calculate_unit_scale(b)-.001)<1e-12,
            "Original mm source/output units not preserved")
    old={x.GlobalId:x.is_a() for x in a.by_type("IfcProduct")}
    new={x.GlobalId:x.is_a() for x in b.by_type("IfcProduct")}
    require(old[opening_guid]=="IfcOpeningElement"
            and old[window_guid]=="IfcWindow"
            and {k:v for k,v in old.items()
                 if k not in (opening_guid,window_guid)}==new,
            "Original surviving native IFC Product GUID/classes not identical")
    require(not any(x.GlobalId==opening_guid for x in b.by_type("IfcOpeningElement")),
            "Public Opening remains in native candidate")
    require(not any(x.GlobalId==window_guid for x in b.by_type("IfcWindow")),
            "Source Window still fills removed Opening")
    return {
        "status":"INDEPENDENT_ORIGINAL_NATIVE_PRODUCTS_PRESERVED",
        "original_IfcProducts":len(old),
        "candidate_IfcProducts":len(new),
        "exactly_one_IfcOpeningElement_and_one_IfcWindow_removed":True,
        "all_other_original_IfcProduct_GUIDs_and_classes_preserved":True,
    }


def audit_original_test18(root:Path,author:Path,data:Path)->dict:
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Original author/data frozen revisions changed")
    require(file_hash(root/OLD_V023_REPORT)==OLD_V023_SHA
            and file_hash(root/OLD_V022_REPORT)==OLD_V022_SHA,
            "Frozen prior original report checksum changed")
    tasks={row["test_id"]:row for row in public_45(author,data)}
    require(len(tasks)==45 and TASK_ID in tasks,
            "Original author public 45-task population changed")
    row=tasks[TASK_ID]
    require(row["crud"]=="delete" and row["category"]=="basic",
            "Original task18 classification drifted")
    original=data/"ifc"/row["original_source_ifc_relpath"]
    require(file_hash(original)==row["original_ifc_sha256"],
            "Actual original source IFC SHA mismatch")
    roles=json.loads((root/OLD_V022_REPORT).read_text(encoding="utf8"))
    previous={x["task_id"]:x for x in roles["all45_per_task_actual_source_role_and_admission_rows"]}
    require(len(previous)==45 and previous[TASK_ID]["public_operation_family"]==
            "DELETE_HOSTED_OPENING_AND_FILL"
            and previous[TASK_ID]["original_native_IFC_sha256"]==row["original_ifc_sha256"]
            and previous[TASK_ID]["original_public_question_sha256"]==row["public_question_sha256"],
            "Pinned parent original task18 public action/source metadata drift")
    public_guid=re.findall(r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",
                           row["public_question"])
    require(len(public_guid)==1,"Original public query changed")
    input_native=ifcopenshell.open(str(original))
    opening=input_native.by_guid(public_guid[0])
    require(opening.is_a("IfcOpeningElement") and len(opening.HasFillings)==1,
            "Original public native target not a uniquely filled opening")
    window=opening.HasFillings[0].RelatedBuildingElement
    require(window.is_a("IfcWindow"),"Original public opening is not filled with Window")
    # Strictly scientific original author scorer precondition diagnosis;
    # inspect the actual original source, never rewrite/evaluate hidden GT.
    originally_contained = ifcopenshell.util.element.get_container(opening) is not None
    original_has_void = len(opening.VoidsElements)==1
    original_sha=file_hash(original)
    with TemporaryDirectory(prefix="bmb-v024-original18-paired-") as temp:
        dest=Path(temp)
        d=XmlSourceEditSession(original,dest/"D0")
        guid,edited_xml=original_public_opening_xml_edit(
            row["public_question"],d.original_xml)
        require(guid==opening.GlobalId,"Public XML target GUID differs from original native IFC")
        outcome=d.call("submit_building_xml",{"xml_text":edited_xml.decode("utf8")})
        require(outcome.get("status")=="ok"
                and outcome.get("native_ifc_committed") is True
                and outcome.get("compile_status")==
                    "COMMITTED_SCOPED_IFC4X3_TOPOLOGY_EDIT"
                and d.output_ifc is not None and d.output_ifc.is_file(),
                "Original public D0 Opening+Window XML source did not compile to IFC")
        iout=dest/"independent_python_original_mm.ifc"
        i0=original_public_opening_window_i0(original,guid,iout)
        require(i0["status"]=="INDEPENDENT_DEVELOPER_NATIVE_OPENING_AND_WINDOW_DELETE"
                and i0["public_opening_absent"]
                and i0["original_filling_window_absent"],
                "Original public native independent I0 failed")
        dsha=file_hash(d.output_ifc);isha=file_hash(iout)
        require(dsha==isha and dsha==i0["candidate_sha256"],
                "Original public full IFC bytes differ D0/I0")
        native_d=independent_original_native_products_oracle(
            original,d.output_ifc,guid,window.GlobalId)
        native_i=independent_original_native_products_oracle(
            original,iout,guid,window.GlobalId)
        require(native_d==native_i,
                "Original native source/target IFC product identity oracle disagrees")
        grade_d=grade_author(author,original,d.output_ifc,TASK_ID)
        grade_i=grade_author(author,original,iout,TASK_ID)
        require(grade_d==grade_i
                and grade_d["status"]=="AUTHOR_SCORED"
                and grade_d["original_author_score"]==0.5
                and grade_d["original_author_metrics"]==
                    {"object_not_exists":1.0,"integrity_constraint":0.0}
                and grade_d["original_author_full_mark"] is False,
                "Original unchanged grader outcome inconsistent")
        require(file_hash(original)==original_sha,"Actual original IFC source altered")
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Original author or data revision changed after output/grading")
    return {
      "status":"ACTUAL_ORIGINAL_TEST18_D0_I0_FULL_NATIVE_IFC_BYTES_EQUAL_ORIGINAL_GRADER_HALF",
      "issue":"https://github.com/pikaybh/bim-markup-bench/issues/162",
      "original_test_id":TASK_ID,
      "original_all45_public_task_denominator":45,
      "pinned_original_author_git_sha":AUTHOR_SHA,
      "pinned_original_data_git_sha":DATA_SHA,
      "pinned_previous_v023_report_sha256":OLD_V023_SHA,
      "pinned_original45_source_roles_report_sha256":OLD_V022_SHA,
      "original_public_question_sha256":row["public_question_sha256"],
      "original_native_IFC_sha256":original_sha,
      "original_source_IFC_schema":"IFC4X3",
      "original_source_IFC_length_unit":"MILLIMETER",
      "original_XML_submission_deletes_only_existing_Opening_and_its_existing_Window":True,
      "I0_is_independent_developer_IfcOpenShell_Python":True,
      "original_D0_full_native_IFC_sha256":dsha,
      "original_I0_full_native_IFC_sha256":isha,
      "actual_full_IFC_output_bytes_equal":True,
      "independent_native_identity_oracle":native_d,
      "original_author_grader_D0":grade_d,
      "original_author_grader_I0":grade_i,
      "original_author_full_mark":False,
      "original_target_has_native_IfcRelVoidsElement":original_has_void,
      "original_target_has_no_native_get_container":not originally_contained,
      "original_author_scorer_or_input_modified":False,
      "original_public_data_source_modified":False,
      "new_actual_developer_D0_I0_native_equal_original_task_count":1,
      "historical_prior_developer_D0_I0_original_native_byte_equal":6,
      "new_cumulative_developer_D0_I0_original_native_byte_equal":7,
      "historical_prior_developer_original_author_callable_pairs":4,
      "new_cumulative_developer_original_author_callable_pairs":5,
      "original_author_missing_Window_reference_source_cases_still_unscoreable":2,
      "other_original_same_protocol_cases_not_proven":38,
      "real_model_calls":0,
      "paid_model_cost_usd":0,
      "all_original45_write_information_capability_parity_proven":False,
      "causal_representation_performance_conclusion_supported":False,
      "original_IFC2X3_IFC4_direct_XML_write_unblocked":False,
      "untrusted_model_python_execution_enabled":False,
      "original_raw_IFC_GTs_or_original_public_target_GUID_committed":False,
    }


def main()->None:
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--author",type=Path,required=True)
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():
        p.error("Refusing to overwrite frozen audit evidence")
    result=audit_original_test18(a.root,a.author,a.data)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x",encoding="utf8",newline="\n") as f:
        json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")
    print("V024_RESULT",result["status"])
    print("BOTH_NATIVE_IFC_SHA",result["original_D0_full_native_IFC_sha256"])
    print("ORIGINAL_AUTHOR_SCORE",result["original_author_grader_D0"]["original_author_score"])
    print("CUMULATIVE_DEVELOPER_EXACT",result["new_cumulative_developer_D0_I0_original_native_byte_equal"])
    print("MODEL_CALLS",result["real_model_calls"])
    print("REPORT_SHA256",sha256(a.output.read_bytes()).hexdigest())


if __name__=="__main__": main()
