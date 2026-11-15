"""Reproducible actual original PUBLIC test_17 Door+Opening D0/I0 native audit.

D0 authoring is a *single complete edited declarative XML document* with two
existing source elements removed. I0 is independent developer-authored Python
using IfcOpenShell. Original grader is called only after both outputs exist.
No actual LLM inference, model code execution, original grader modification,
dataset edit, or performance inference occurs.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.unit

from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import XmlSourceEditSession,file_hash
from tools.bibimbap_v025_original_door_i0 import independent_original_public_door_i0

ROOT=Path(__file__).resolve().parents[1]
TASK_ID="test_17"
ORIGINAL_PUBLIC_NORMALIZED_IFC_SHA="16568e7c4b8b9d62567a7a199101269daa6e5b1b7535cec095b8e233ae2ef6ac"
OLDER_REPORT_HASHES={
    "reports/bibimbap_v022_original45_task_relevant_roles_and_xml_input_20261115.json":
        "f606994defa7517f898e22ee6e39d5e82da6dc40288c1b38cec25c98b7cd492e",
    "reports/bibimbap_v023_original_test20_space_delete_D0_I0_native_parity_20261115.json":
        "9abcc4ebd21c18891bf08307624a19f6012a981455eca7db89051ae70ce86102",
    "reports/bibimbap_v024_original_test18_opening_window_D0_I0_20261115.json":
        "a31e74dacdece9924304de6c74c5d9e8769497a8ad68287779ddd4a37bac6a67",
}


class OriginalPublicDoorAuditBlocked(ValueError):
    pass


def _require(ok,reason:str)->None:
    if not ok:
        raise OriginalPublicDoorAuditBlocked(reason)


def actual_public_door_declarative_source(
    instruction:str,source_xml:bytes,
)->tuple[str,bytes]:
    """Use exactly one public Door GUID; remove exactly two original state lines."""
    from src.security.agent_boundary import check_xml_bytes
    guids=re.findall(r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",instruction)
    _require(len(guids)==1,"Original PUBLIC question requires one unambiguous Door GUID")
    guid=guids[0]
    xml=source_xml.decode("utf8")
    door_lines=[s for s in xml.splitlines(keepends=True)
                if "<Door " in s and 'ifcGuid="'+guid+'"' in s]
    _require(len(door_lines)==1,"Original PUBLIC Door absent from editable declarative source")
    door_line=door_lines[0]
    opening_ref=re.search(r'\bopening="([^"]+)"',door_line)
    _require(opening_ref is not None,"Original Door has no uniquely referenced Opening")
    opening_lines=[s for s in xml.splitlines(keepends=True)
                   if "<Opening " in s and 'id="'+opening_ref.group(1)+'"' in s]
    _require(len(opening_lines)==1,"Original Door's Opening not exactly one XML state node")
    changed=xml.replace(door_line,"",1).replace(opening_lines[0],"",1).encode("utf8")
    check_xml_bytes(changed)
    _require(changed!=source_xml and guid not in changed.decode("utf8")
             and len(source_xml.decode("utf8").splitlines())-
                     len(changed.decode("utf8").splitlines())==2,
             "Original public pair XML edit not isolated")
    return guid,changed


def independent_native_products_oracle(
    original:Path,candidate:Path,public_guid:str,opening_guid:str,
)->dict:
    a=ifcopenshell.open(str(original))
    b=ifcopenshell.open(str(candidate))
    _require(a.schema==b.schema=="IFC4X3"
             and abs(ifcopenshell.util.unit.calculate_unit_scale(a)-.001)<1e-12
             and abs(ifcopenshell.util.unit.calculate_unit_scale(b)-.001)<1e-12,
             "Original native IFC4X3 millimetre source/output not retained")
    orig={x.GlobalId:x.is_a() for x in a.by_type("IfcProduct")}
    final={x.GlobalId:x.is_a() for x in b.by_type("IfcProduct")}
    _require(orig[public_guid]=="IfcDoor"
             and orig[opening_guid]=="IfcOpeningElement"
             and {k:v for k,v in orig.items()
                  if k not in (public_guid,opening_guid)}==final,
             "Independent original product identity/class preservation failed")
    return {
        "status":"NATIVE_ORIGINAL_DOOR_AND_OPENING_ONLY_PRODUCTS_REMOVED",
        "original_IfcProduct_count":len(orig),
        "result_IfcProduct_count":len(final),
        "only_two_original_products_removed":True,
        "every_other_original_native_IfcProduct_class_and_GUID_preserved":True,
    }


def audit_original_public_test17(root:Path,author:Path,data:Path)->dict:
    _require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
             "Original pinned author/public data Git revision drift")
    for rel,sha in OLDER_REPORT_HASHES.items():
        _require(file_hash(root/rel)==sha,"Frozen previous original result changed")
    public={task["test_id"]:task for task in public_45(author,data)}
    _require(len(public)==45 and TASK_ID in public,"Original public45 cohort drift")
    row=public[TASK_ID]
    _require(row["crud"]=="delete" and row["category"]=="basic",
             "Original test17 operation family changed")
    original=data/"ifc"/row["original_source_ifc_relpath"]
    sha=file_hash(original)
    _require(sha==row["original_ifc_sha256"],"Original native IFC checksum changed")
    f=ifcopenshell.open(str(original))
    guids=re.findall(r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",
                     row["public_question"])
    _require(len(guids)==1,"Original PUBLIC Door target ambiguously specified")
    original_door=f.by_guid(guids[0])
    _require(original_door.is_a("IfcDoor") and len(original_door.FillsVoids)==1
             and original_door.FillsVoids[0].RelatingOpeningElement.is_a("IfcOpeningElement"),
             "Original PUBLIC Door has no exact native Opening dependency")
    opguid=original_door.FillsVoids[0].RelatingOpeningElement.GlobalId
    originally_contained=ifcopenshell.util.element.get_container(original_door) is not None
    with TemporaryDirectory(prefix="bmb-v025-original17-two-armed-") as td:
        folder=Path(td)
        d=XmlSourceEditSession(original,folder/"D0")
        _require(file_hash(d.normalized)==ORIGINAL_PUBLIC_NORMALIZED_IFC_SHA,
                 "Normalized original native source SHA differed from frozen public input")
        public_guid,updated=actual_public_door_declarative_source(
            row["public_question"],d.original_xml)
        _require(public_guid==original_door.GlobalId,
                 "PUBLIC Door GUID differs from native original")
        response=d.call("submit_building_xml",{"xml_text":updated.decode("utf8")})
        _require(response.get("status")=="ok"
                 and response.get("native_ifc_committed") is True
                 and response.get("compile_status")==
                     "COMMITTED_SCOPED_IFC4X3_TOPOLOGY_EDIT"
                 and d.output_ifc is not None and d.output_ifc.is_file(),
                 "Original PUBLIC Door+Opening D0 actual native IFC commit failed")
        i0path=folder/"independent_I0_native_original_mm.ifc"
        i0=independent_original_public_door_i0(original,public_guid,i0path)
        _require(i0["status"]==
                     "INDEPENDENT_ORIGINAL_PUBLIC_NATIVE_DOOR_AND_OPENING_DELETED"
                 and i0["original_public_door_absent"]
                 and i0["native_original_filled_opening_absent"],
                 "Actual independent native I0 did not remove exact public Door pair")
        dsha=file_hash(d.output_ifc);isha=file_hash(i0path)
        _require(dsha==isha and isha==i0["native_result_sha256"],
                 "Original PUBLIC paired D0/I0 full output IFC bytes not identical")
        native_d=independent_native_products_oracle(
            original,d.output_ifc,public_guid,opguid)
        native_i=independent_native_products_oracle(
            original,i0path,public_guid,opguid)
        _require(native_d==native_i,"Independent native product source oracle inconsistent")
        score_d=grade_author(author,original,d.output_ifc,TASK_ID)
        score_i=grade_author(author,original,i0path,TASK_ID)
        _require(score_d==score_i
                 and score_d["status"]=="AUTHOR_SCORED"
                 and score_d["original_author_score"]==0.5
                 and score_d["original_author_metrics"]==
                     {"integrity_constraint":0.0,"object_not_exists":1.0}
                 and not score_d["original_author_full_mark"],
                 "Original unchanged author score differs from pinned expectation")
        _require(file_hash(original)==sha,"Original public IFC source was modified")
    _require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
             "Original benchmark author/data revision changed after runs")
    return {
        "status":"ORIGINAL_PUBLIC_TEST17_D0_I0_FULL_NATIVE_IFC_BYTES_IDENTICAL_ORIGINAL_AUTHOR_HALF",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/164",
        "original_public_45_task_denominator":45,
        "original_task_id":TASK_ID,
        "original_author_pinned_git_sha":AUTHOR_SHA,
        "original_public_data_pinned_git_sha":DATA_SHA,
        "original_public_question_sha256":row["public_question_sha256"],
        "original_IFC4X3_mm_source_sha256":sha,
        "normalized_original_public_native_IFC_sha256":ORIGINAL_PUBLIC_NORMALIZED_IFC_SHA,
        "prior_frozen_reports_sha256":OLDER_REPORT_HASHES,
        "declarative_XML_edit_is_exactly_one_original_Door_and_Opening_state_removal":True,
        "independent_developer_I0_uses_native_IfcOpenShell_without_XML_compiler":True,
        "D0_actual_native_output_IFC_sha256":dsha,
        "I0_actual_native_output_IFC_sha256":isha,
        "full_original_native_output_IFC_bytes_equal":True,
        "independent_original_native_product_oracle":native_d,
        "unchanged_original_author_D0":score_d,
        "unchanged_original_author_I0":score_i,
        "original_public_Door_native_spatial_container_exists":originally_contained,
        "original_author_score_full_mark_achieved":False,
        "prior_frozen_developer_original_native_D0_I0_identical_cases":7,
        "new_cumulative_developer_original_native_D0_I0_identical_cases":8,
        "prior_frozen_original_author_callable_developer_pairs":5,
        "new_cumulative_original_author_callable_developer_pairs":6,
        "other_original_public_same_protocol_cases_unverified":37,
        "prior_original_author_missing_Window_source_cases":2,
        "real_LLM_model_calls":0,
        "paid_provider_USD":0,
        "full_original_45_write_information_tool_or_feedback_parity_proven":False,
        "original_IFC2X3_or_IFC4_XML_editing_supported":False,
        "developer_output_parity_proves_causal_XML_model_performance":False,
        "original_author_or_source_IFC_modified":False,
        "raw_original_public_named_GUID_or_hidden_original_targets_in_report":False,
    }


def main()->None:
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--root",type=Path,default=ROOT)
    a.add_argument("--author",type=Path,required=True)
    a.add_argument("--data",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True)
    args=a.parse_args()
    if args.output.exists() or args.output.is_symlink():
        a.error("Refuse to overwrite prior original benchmark evidence")
    result=audit_original_public_test17(args.root,args.author,args.data)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf8",newline="\n") as fh:
        json.dump(result,fh,sort_keys=True,ensure_ascii=False,indent=2)
        fh.write("\n")
    print("V025_ORIGINAL17_STATUS",result["status"])
    print("V025_FULL_D0_I0_IFC_SHA256",result["D0_actual_native_output_IFC_sha256"])
    print("V025_ORIGINAL_AUTHOR_SCORE_BOTH",result["unchanged_original_author_D0"]["original_author_score"])
    print("V025_DEVELOPER_DISTINCT_BYTE_MATCH_COUNT",result["new_cumulative_developer_original_native_D0_I0_identical_cases"])
    print("V025_NEW_REAL_MODEL_CALLS",result["real_LLM_model_calls"])
    print("V025_AUDIT_REPORT_SHA256",sha256(args.output.read_bytes()).hexdigest())


if __name__=="__main__":
    main()
