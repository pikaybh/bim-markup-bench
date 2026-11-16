"""v0.29 actual original PUBLIC test_14 matched native IFC D0/I0 audit.

D0: complete declarative typed XML edit changing existing Slab z ONLY.
I0: independent developer native Python/IfcOpenShell from original PUBLIC
millimetre IFC. Original unchanged author test scorer only after both actual
IFC outputs. No hidden answer use, no model-generated code, no paid calls.
All original source IFC, author/data Git, prior reports and Xim unchanged.
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

from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import XmlSourceEditSession,file_hash
from tools.bibimbap_v029_original_slab_i0 import independent_public_slab_i0
from src.runtime.original_slab_translate import (
    SOURCE_SHA,strict_slab_preflight,verify_slab_native,
)

ROOT=Path(__file__).resolve().parents[1]
TASK="test_14"
PARENT_GIT="6505cc8ffd9907d8f4fc477e8424ea4bfcfd8788"
FROZEN_V028_REPORTS={
    "reports/bibimbap_v028_original_test11_wall_center_rotate_D0_I0_native_parity_20261116.json":
        "6818e6bfa2990f8dc9ee3730ba9a7197c72d6f3131af9bae9fbda8d22fefd8cb",
    "reports/bibimbap_v028_selected_351_nondocker_regression_and_original11_native_QA_20261116.json":
        "8ad99438f24aa6e8cd34145439fdeb57aec24a59653fe4f007ab87cafd0170db",
}


class OriginalSlabAuditBlocked(ValueError):
    pass


def require(ok:bool,reason:str)->None:
    if not ok:raise OriginalSlabAuditBlocked(reason)


def whole_original_source_one_slab_z_down(question:str,xml:bytes)->tuple[str,bytes]:
    guids=re.findall(r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",question)
    require(len(guids)==1 and "slab" in question.lower()
            and "0.5" in question and "decrease" in question.lower(),
            "Original public benchmark task no longer one half-metre Slab")
    target=guids[0]
    source=xml.decode("utf8")
    selected=[line for line in source.splitlines(keepends=True)
              if "<Slab " in line and 'ifcGuid="'+target+'"' in line]
    require(len(selected)==1,"Original Slab is not present once in typed source XML")
    line=selected[0]
    match=re.search(r'\bz="([^"]+)"',line)
    require(match is not None and abs(float(match.group(1))-3.8)<1e-9,
            "Original PUBLIC source slab typed z is not frozen 3.8")
    replaced=re.sub(r'\bz="[^"]+"','z="3.3"',line,count=1)
    modified=source.replace(line,replaced,1).encode("utf8")
    require(modified!=xml and source.count("<Slab ")==modified.decode("utf8").count("<Slab ")
            and len(source.splitlines())==len(modified.decode("utf8").splitlines()),
            "Original complete declarative XML change is not one stable Slab line")
    return target,modified


def independent_native_identity_oracle(original:Path,output:Path,guid:str)->dict:
    a=ifcopenshell.open(str(original));b=ifcopenshell.open(str(output))
    require(a.schema==b.schema=="IFC4X3","Original IFC schema changed")
    roots_before={x.GlobalId:x.is_a() for x in a.by_type("IfcRoot")}
    roots_after={x.GlobalId:x.is_a() for x in b.by_type("IfcRoot")}
    require(roots_before==roots_after and a.by_guid(guid).is_a()=="IfcSlab"
            and b.by_guid(guid).is_a()=="IfcSlab",
            "Original IFC native Root/Product identity changed")
    products_before={x.GlobalId:x.is_a() for x in a.by_type("IfcProduct")}
    products_after={x.GlobalId:x.is_a() for x in b.by_type("IfcProduct")}
    require(products_before==products_after,
            "Original IFC native Product GUIDs/classes changed")
    return {
        "status":"INDEPENDENT_ORIGINAL_SOURCE_ROOT_PRODUCT_IDENTITY_PASS",
        "original_Root_count":len(roots_before),
        "original_Product_count":len(products_before),
        "every_original_IfcRoot_GUID_class_preserved":True,
        "every_original_IfcProduct_GUID_class_preserved":True,
    }


def audit_actual_original_public_test14(root:Path,author:Path,data:Path)->dict:
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Original benchmark author/data Git SHA drift")
    for relative,expected in FROZEN_V028_REPORTS.items():
        require(file_hash(root/relative)==expected,
                "Previous v0.28 original native report SHA drift")
    cases={x["test_id"]:x for x in public_45(author,data)}
    require(len(cases)==45 and TASK in cases,"Original 45-task public cohort changed")
    task=cases[TASK]
    require(task["category"]=="basic" and task["crud"]=="update",
            "Original public Slab test14 operation/category changed")
    source=data/"ifc"/task["original_source_ifc_relpath"]
    original_sha=file_hash(source)
    require(original_sha==task["original_ifc_sha256"],"Original IFC source checksum drift")
    with TemporaryDirectory(prefix="bmb-v029-real-public-slab-D0-I0-") as td:
        folder=Path(td)
        with patch.dict(os.environ,{"BMB_V029_ORIGINAL_SLAB_TRANSLATE":"1"}):
            d=XmlSourceEditSession(source,folder/"D0")
            require(file_hash(d.normalized)==SOURCE_SHA,
                    "Original IFC4X3-m normalized source SHA drift")
            guid,updated=whole_original_source_one_slab_z_down(
                task["public_question"],d.original_xml)
            plan=strict_slab_preflight(d.normalized,guid)
            receipt=d.call("submit_building_xml",{"xml_text":updated.decode("utf8")})
        require(receipt.get("status")=="ok"
                and receipt.get("native_ifc_committed") is True
                and d.output_ifc is not None and d.output_ifc.is_file(),
                "Actual original PUBLIC D0 native Slab edit did not commit")
        native_stage=d.folder/"attempt_01"/"candidate_m.ifc"
        require(native_stage.is_file(),"Native D0 temporary metric IFC stage missing")
        roots=verify_slab_native(d.normalized,native_stage,plan)
        i0_path=folder/"independent_original_native_i0_mm.ifc"
        control=independent_public_slab_i0(source,guid,i0_path)
        dsha=file_hash(d.output_ifc);isha=file_hash(i0_path)
        require(dsha==isha==control["entire_native_original_mm_IFC_sha256"],
                "Original PUBLIC D0 and independent I0 full IFC bytes differ")
        native_d=independent_native_identity_oracle(source,d.output_ifc,guid)
        native_i=independent_native_identity_oracle(source,i0_path,guid)
        require(native_d==native_i,"Original native independent IFC identities differ")
        grade_d=grade_author(author,source,d.output_ifc,TASK)
        grade_i=grade_author(author,source,i0_path,TASK)
        require(grade_d==grade_i and grade_d["status"]=="AUTHOR_SCORED"
                and grade_d["original_author_score"]==1.0
                and grade_d["original_author_full_mark"] is True
                and grade_d["original_author_metrics"]==
                    {"right_location":1.0,"right_dimensions":1.0,"integrity_constraint":1.0},
                "Original author unchanged scorer did not yield full marks for both arms")
        require(file_hash(source)==original_sha,
                "Original PUBLIC IFC source modified while testing")
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Original author/data revision changed during actual source experiment")
    return {
        "status":"V029_ORIGINAL_PUBLIC_TEST14_FLIPPED_SLAB_TYPED_XML_NATIVE_D0_I0_BYTE_IDENTICAL_AUTHOR_1_0",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/173",
        "original_public_task_id":TASK,
        "original_public45_denominator":45,
        "original_author_pinned_git_SHA":AUTHOR_SHA,
        "original_public_data_pinned_git_SHA":DATA_SHA,
        "parent_v028_git_sha":PARENT_GIT,
        "frozen_previous_v028_report_hashes":FROZEN_V028_REPORTS,
        "original_public_question_SHA256":task["public_question_sha256"],
        "original_mm_IFC_source_SHA256":original_sha,
        "normalized_original_IFC_SHA256":SOURCE_SHA,
        "actual_native_Source_IfcSlab_count":2,
        "source_flipped_Z_rectangle_presents_as_existing_typed_Slab":True,
        "original_public_author_explicit_height_wording_interpreted_as_vertical_translation":True,
        "original_complete_XML_only_target_existing_Slab_z_changed_3_8_to_3_3":True,
        "original_source_shared_56_reference_CartesianPoint_preserved":True,
        "original_native_only_private_new_IfcCartesianPoint_created":True,
        "native_all_original_Roots_and_existing_STEP_bytes_verified":True,
        "original_native_Roots_preserved_count":roots,
        "full_original_native_D0_IFC_SHA256":dsha,
        "full_original_native_I0_IFC_SHA256":isha,
        "full_native_D0_I0_IFC_bytes_identical":True,
        "independent_imperative_Python_I0_no_D0_XML_or_scorer_imports":True,
        "independent_original_native_Root_Product_identity_oracle":native_d,
        "unchanged_original_author_D0":grade_d,
        "unchanged_original_author_I0":grade_i,
        "original_author_score_1_0_both":True,
        "previous_developer_native_byte_equal_original_cases":10,
        "new_cumulative_developer_native_byte_equal_original_cases":11,
        "previous_original_author_callable_developer_pairs":8,
        "new_cumulative_original_author_callable_developer_pairs":9,
        "other_original_public_tasks_not_yet_same_protocol_paired":34,
        "trusted_read_and_write_feature_flag_default_OFF":True,
        "actual_real_LLM_calls":0,
        "new_paid_provider_USD":0,
        "all45_semantic_read_write_feedback_parity_proven":False,
        "causal_XML_vs_Python_LLM_performance_supported":False,
        "original_author_scorer_data_or_raw_original_IFC_modified":False,
        "raw_original_public_question_target_GUID_hidden_GT_or_IFC_in_report":False,
    }


def main()->None:
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--root",type=Path,default=ROOT)
    a.add_argument("--author",type=Path,required=True)
    a.add_argument("--data",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True)
    options=a.parse_args()
    if options.output.exists() or options.output.is_symlink():
        a.error("Never overwrite existing original native checkpoint reports")
    result=audit_actual_original_public_test14(
        options.root,options.author,options.data)
    options.output.parent.mkdir(parents=True,exist_ok=True)
    with options.output.open("x",encoding="utf8",newline="\n") as fp:
        json.dump(result,fp,ensure_ascii=False,sort_keys=True,indent=2)
        fp.write("\n")
    print("V029_ORIGINAL_PUBLIC14",result["status"])
    print("V029_ORIGINAL_NATIVE_D0_I0_FULL_SHA",result["full_original_native_D0_IFC_SHA256"])
    print("V029_ORIGINAL_AUTHOR_BOTH",result["unchanged_original_author_D0"]["original_author_score"])
    print("V029_CUMULATIVE_DEVELOPER_PAIRED",result["new_cumulative_developer_native_byte_equal_original_cases"])
    print("V029_REPORT_SHA256",sha256(options.output.read_bytes()).hexdigest())


if __name__=="__main__":
    main()
