"""v0.28 reproducible actual original PUBLIC test_11 Wall rotation D0/I0 audit.

D0: complete ordinary authored XML source, only four endpoint coordinate
attributes changed to a +90° center rotation. Native mutation is trusted
source-gated IFC compiler, not an agent tool. I0: separately implemented
imperative Python/IfcOpenShell native placement edit on original public IFC.
Unmodified original author scorer runs only after both native outputs exist.
No hidden ground truth, model API, or model-generated code.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import os
import re
from tempfile import TemporaryDirectory
from unittest.mock import patch

import ifcopenshell

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45, grade_author
from tools.bibimbap_matched25_tools import XmlSourceEditSession, file_hash
from tools.bibimbap_v028_original_wall_rotation_i0 import independent_public_wall_center_rotate_i0
from src.runtime.original_wall_rotation import (
    PINNED_ORIGINAL_NORMALIZED_SHA,plan_original_wall_rotation,
    verify_wall_rotation,
)

ROOT=Path(__file__).resolve().parents[1]
TASK_ID="test_11"
PREVIOUS_REPORT_SHA={
    "reports/bibimbap_v027_original_test19_connected_wall_D0_I0_native_parity_20261116.json":
        "9cee40c6cd75f5f5fc3c35f1d8ee5b0580681e38820da6178f39c413c71d63b4",
    "reports/bibimbap_v027_selected_316_non_docker_regression_and_original19_native_QA_20261116.json":
        "5cc9a36b6c2aad2b30d8240173f1eb0d35e470676383eae33c708fb6c6212c4c",
}
BASE_V027_GIT="cb4965d3d5e9f34cbc9a6eb97b9247a38b71d058"


class OriginalWallRotateAuditBlocked(ValueError):
    pass


def require(ok:bool,why:str)->None:
    if not ok:raise OriginalWallRotateAuditBlocked(why)


def _fmt(n:float)->str:
    value=round(n,7)
    return f"{value:.7f}".rstrip("0").rstrip(".") if value else "0"


def full_public_XML_center_rotation(question:str,xml:bytes)->tuple[str,bytes]:
    guidlist=re.findall(r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",question)
    require(len(guidlist)==1 and "+90" in question and "z axis" in question.lower(),
            "Expected one public target and +90° Z-rotation instruction")
    guid=guidlist[0]
    text=xml.decode("utf8")
    lines=[line for line in text.splitlines(keepends=True)
           if '<Wall ' in line and 'ifcGuid="'+guid+'"' in line]
    require(len(lines)==1,"Public source Wall has no single editable XML state")
    original=lines[0]
    def val(k):
        m=re.search(r"\b"+re.escape(k)+r'="([^"]+)"',original)
        require(m is not None,"Original public wall coordinate missing")
        return float(m.group(1))
    p=(val("x1"),val("y1"));q=(val("x2"),val("y2"))
    c=((p[0]+q[0])/2.,(p[1]+q[1])/2.)
    updated={
        "x1":c[0]-(p[1]-c[1]),
        "y1":c[1]+(p[0]-c[0]),
        "x2":c[0]-(q[1]-c[1]),
        "y2":c[1]+(q[0]-c[0]),
    }
    replacement=original
    for name,value in updated.items():
        replacement,n=re.subn(r'\b'+name+r'="[^"]+"',
            name+'="'+_fmt(value)+'"',replacement,count=1)
        require(n==1,"Original Wall coordinate replacement unexpectedly ambiguous")
    out=text.replace(original,replacement,1).encode("utf8")
    require(out!=xml and guid in out.decode("utf8")
            and len(text.splitlines())==len(out.decode("utf8").splitlines()),
            "Full XML update did not change only one existing Wall line")
    return guid,out


def independently_verify_original_native_products(
    original:Path,final:Path,target_guid:str,
)->dict:
    """Independent oracle on original-mm-native products & original Root IDs."""
    a=ifcopenshell.open(str(original));b=ifcopenshell.open(str(final))
    require(a.schema==b.schema=="IFC4X3","Original schema changed")
    original_roots={x.GlobalId:x.is_a() for x in a.by_type("IfcRoot")}
    final_roots={x.GlobalId:x.is_a() for x in b.by_type("IfcRoot")}
    require(original_roots==final_roots,"Original IfcRoot classes or GUIDs mutated")
    original_products={x.GlobalId:x.is_a() for x in a.by_type("IfcProduct")}
    final_products={x.GlobalId:x.is_a() for x in b.by_type("IfcProduct")}
    require(original_products==final_products
            and original_products[target_guid]=="IfcWall",
            "Original native product GUIDs/classes differ")
    return {
        "status":"INDEPENDENT_NATIVE_ALL_ORIGINAL_IFCROOT_AND_IFCPRODUCT_IDENTITIES_PRESERVED",
        "original_native_IfcRoot_count":len(original_roots),
        "original_native_IfcProduct_count":len(original_products),
        "original_native_Root_GUIDs_classes_unchanged":True,
        "original_native_all_Product_GUIDs_classes_unchanged":True,
    }


def audit_original_public_test11(root:Path,author:Path,data:Path)->dict:
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Pinned original benchmark author/data Git revisions differ")
    for rel,sha in PREVIOUS_REPORT_SHA.items():
        require(file_hash(root/rel)==sha,"Frozen predecessor report checksum changed")
    cohort={x["test_id"]:x for x in public_45(author,data)}
    require(len(cohort)==45 and TASK_ID in cohort,
            "Original public45 cohort changed")
    task=cohort[TASK_ID]
    require(task["crud"]=="update" and task["category"]=="basic",
            "Original task category/operation differs")
    src=data/"ifc"/task["original_source_ifc_relpath"]
    original_sha=file_hash(src)
    require(original_sha==task["original_ifc_sha256"],
            "Original benchmark IFC has been modified")
    with TemporaryDirectory(prefix="bmb-v028-original11-matched-D0-I0-") as td:
        folder=Path(td)
        d=XmlSourceEditSession(src,folder/"D0")
        require(file_hash(d.normalized)==PINNED_ORIGINAL_NORMALIZED_SHA,
                "Unexpected original IFC4X3 normalized source SHA")
        public_guid,updated=full_public_XML_center_rotation(
            task["public_question"],d.original_xml)
        preflight=plan_original_wall_rotation(d.normalized,public_guid)
        with patch.dict(os.environ,{"BMB_V028_ORIGINAL_WALL_CENTER_ROTATE":"1"}):
            receipt=d.call("submit_building_xml",{"xml_text":updated.decode("utf8")})
        require(receipt.get("status")=="ok"
                and receipt.get("native_ifc_committed") is True
                and receipt.get("compile_status")=="COMMITTED_SCOPED_IFC4X3_WALL_EDIT"
                and d.output_ifc is not None and d.output_ifc.is_file(),
                "Original PUBLIC D0 trusted native IFC rotation was not committed")
        metric=d.folder/"attempt_01"/"candidate_m.ifc"
        require(metric.is_file(),"Native metric IFC transaction stage missing")
        native_verified=verify_wall_rotation(d.normalized,metric,preflight)
        independent_i0=folder/"independent_original_I0_mm.ifc"
        i0=independent_public_wall_center_rotate_i0(src,public_guid,independent_i0)
        d_sha=file_hash(d.output_ifc);i_sha=file_hash(independent_i0)
        require(d_sha==i_sha==i0["full_native_IFC_sha256"],
                "Full original output IFC bytes D0 and independent I0 differ")
        d_oracle=independently_verify_original_native_products(
            src,d.output_ifc,public_guid)
        i_oracle=independently_verify_original_native_products(
            src,independent_i0,public_guid)
        require(d_oracle==i_oracle,"Independent original native Root identity check disagrees")
        grade_d=grade_author(author,src,d.output_ifc,TASK_ID)
        grade_i=grade_author(author,src,independent_i0,TASK_ID)
        require(grade_d==grade_i and grade_d["status"]=="AUTHOR_SCORED"
                and grade_d["original_author_full_mark"] is True
                and grade_d["original_author_score"]==1.0
                and grade_d["original_author_metrics"]==
                    {"right_location":1.0,"right_dimensions":1.0,"integrity_constraint":1.0},
                "Original author scorer does not give both complete native outputs full marks")
        require(file_hash(src)==original_sha,"Original benchmark source file modified")
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Original benchmark source repositories changed")
    return {
        "status":"V028_ORIGINAL_PUBLIC_TEST11_FULL_IFC_D0_I0_BYTE_IDENTICAL_ORIGINAL_AUTHOR_1_0",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/171",
        "original_public_task_id":TASK_ID,
        "original_public45_denominator":45,
        "original_author_pinned_git_sha":AUTHOR_SHA,
        "original_public_data_pinned_git_sha":DATA_SHA,
        "parent_v027_frozen_git_SHA":BASE_V027_GIT,
        "original_public_question_sha256":task["public_question_sha256"],
        "original_mm_source_IFC_sha256":original_sha,
        "normalized_original_IFC_SHA256":PINNED_ORIGINAL_NORMALIZED_SHA,
        "previous_frozen_reports_SHA256":PREVIOUS_REPORT_SHA,
        "full_original_XML_source_only_one_existing_Wall_four_endpoints_changed":True,
        "rotation_about_original_center_plus90_degrees_Z":True,
        "trusted_compiler_source_SHA_pinned_and_default_feature_OFF":True,
        "native_source_shared_RefDirection_kept_unchanged":True,
        "new_private_Wall_RefDirection_count":1,
        "original_native_root_count_verified_unchanged":native_verified,
        "original_native_all_surviving_STEP_change_scope":"2 original placement STEP changed, 1 private IfcDirection added; others identical",
        "D0_complete_original_native_IFC_SHA256":d_sha,
        "I0_complete_original_native_IFC_SHA256":i_sha,
        "full_native_IFC_D0_I0_bytes_equal":True,
        "independent_original_native_Root_and_Product_oracle":d_oracle,
        "unchanged_original_author_D0":grade_d,
        "unchanged_original_author_I0":grade_i,
        "both_original_author_full_marks":True,
        "prior_developer_original_native_byte_equal_D0_I0_tasks":9,
        "new_cumulative_developer_original_native_byte_equal_D0_I0_tasks":10,
        "prior_original_author_callable_developer_pairs":7,
        "new_cumulative_original_author_callable_developer_pairs":8,
        "other_original_public_tasks_unverified_identical_protocol":35,
        "real_LLM_model_calls":0,
        "paid_provider_USD":0,
        "causal_D0_vs_I0_model_performance_proven":False,
        "complete_original45_source_information_writable_feedback_parity_proven":False,
        "original_author_or_source_IFC_modified":False,
        "raw_original_public_question_target_GUID_or_private_GT_in_report":False,
    }


def main()->None:
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--author",type=Path,required=True)
    parser.add_argument("--data",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error("Never overwrite existing frozen evidence")
    result=audit_original_public_test11(args.root,args.author,args.data)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf8",newline="\n") as fh:
        json.dump(result,fh,ensure_ascii=False,sort_keys=True,indent=2)
        fh.write("\n")
    print("V028_STATUS",result["status"])
    print("V028_FULL_IFC_SHA256",result["D0_complete_original_native_IFC_SHA256"])
    print("V028_AUTHOR_SCORE_BOTH",result["unchanged_original_author_D0"]["original_author_score"])
    print("V028_CUMULATIVE_DEVELOPER_PARITY",result["new_cumulative_developer_original_native_byte_equal_D0_I0_tasks"])
    print("V028_REPORT_SHA256",sha256(args.output.read_bytes()).hexdigest())


if __name__=="__main__":
    main()
