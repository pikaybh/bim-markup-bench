"""Source-hash-pinned offline census of ALL original public BIBIMBAP 45 edits.

A source/representation inventory is NOT a successful native XML compile.
This ledger does not run paid model inference, hidden targets, scorer
against new predictions, or candidate IFC edits. It preserves the original
45 denominator, independent of partial experimental backend capability.

The only prospective D0 per-task outcomes shown are the SEVEN developer-
authored original public v0.8/v0.9/v0.10 cases with immutable report hashes.
All other original cases are UNASSESSSED_BY_THIS_LEDGER, not assumed
to fail or pass. Previous 45 source projection gate is shown separately
as a historical snapshot, never equated to current native edit parity.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import json

import ifcopenshell
import ifcopenshell.util.unit

from tools.audit_bibimbap_v11_metric_forensics import PINNED
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head

PINNED_REPORTS={
    "v08":(
        "bibimbap_v08_legacy_ifc2x3_ifc4_d0_20261113.json",
        "1264e33403a8b7e554913a34fc79b031890fd0aee832bc6b8f2010f912a5b4e0",
    ),
    "v09":(
        "bibimbap_v09_complex_original_developer_d0_20261113.json",
        "0037c30958437364434cd81696991d5268e2ca5c284eba3bf0329c6597cc01de",
    ),
    "v010":(
        "bibimbap_v010_original_column_multi_developer_d0_20261113.json",
        "9341aa11206b2d9ae2e5c96e816287f66fb5e0bab0b02d506f65ba7e862fe938",
    ),
}


def _known_d0(root:Path)->dict:
    grades={}
    for version,(file,digest) in PINNED_REPORTS.items():
        path=root/"reports"/file
        if file_hash(path)!=digest:
            raise ValueError("Prior original developer D0 report SHA drift "+file)
        obj=json.loads(path.read_text(encoding="utf8"))
        records=(
            obj["tasks"] if version=="v08" else
            obj["cases"] if version=="v09" else [obj]
        )
        for row in records:
            task=(
                row["original_public_task_id"] if version=="v08" else
                row["original_public_task"] if version=="v09" else
                row["original_public_task_id"]
            )
            score=(
                row["original_author_grade_after_freezing_d0"] if version=="v08"
                else row["original_author_grade_after_candidate_frozen"] if version=="v09"
                else row["original_author_D0_score_after_candidate_frozen"]
            )
            original=(
                row["original_public_ifc_sha256"] if version=="v08"
                else row["original_source_ifc_sha256"] if version=="v09"
                else row["original_public_ifc_sha256"]
            )
            question=(
                row["public_question_sha256"] if version=="v08"
                else row["original_public_question_sha256"] if version=="v09"
                else row["original_public_question_sha256"]
            )
            if task in grades:
                raise ValueError("Duplicate D0 original task across v08-v010")
            if score["status"]!="AUTHOR_SCORED":
                raise ValueError("Non-source-original author D0 status")
            grades[task]={
                "experimental_backend_version":version,
                "public_original_ifc_sha256":original,
                "public_question_sha256":question,
                "original_author_fixed_developer_D0_score":score["original_author_score"],
                "original_author_fixed_developer_D0_full_mark":score["original_author_full_mark"],
                "original_author_original_metric_subscores":score["original_author_metrics"],
                "original_D0_report_sha256":digest,
            }
    if len(grades)!=7:
        raise ValueError("Expected exactly seven v0.8-v0.10 original developer D0 task slices")
    return grades


def run(root:Path,author:Path,dataset:Path)->dict:
    if _head(author)!=AUTHOR_SHA or _head(dataset)!=DATA_SHA:
        raise ValueError("Original author/dataset revisions changed")
    cohort=public_45(author,dataset)
    if len(cohort)!=45 or len({x["test_id"] for x in cohort})!=45:
        raise ValueError("Original full45 cohort is not unique/complete")
    evidence=_known_d0(root)
    if not set(evidence)<={x["test_id"] for x in cohort}:
        raise ValueError("Original developer cases outside pinned public 45 denominator")
    tasks=[]
    schema_counter=Counter()
    category=Counter()
    crud=Counter()
    prior_readonly=Counter()
    latest_d0=Counter()
    for t in sorted(cohort,key=lambda x:x["test_id"]):
        raw=dataset/"ifc"/t["original_source_ifc_relpath"]
        if file_hash(raw)!=t["original_ifc_sha256"]:
            raise ValueError("Pinned original task public IFC SHA mismatch")
        f=ifcopenshell.open(str(raw))
        schema=f.schema
        unit=ifcopenshell.util.unit.calculate_unit_scale(f)
        schema_counter[schema]+=1
        category[t["category"]]+=1
        crud[t["crud"]]+=1
        prev=t["xml_source_projection_previously_observed"]
        prior_readonly[prev]+=1
        obj_types=Counter(
            x.is_a() for x in f.by_type("IfcProduct")
        )
        supported_class_counts={
            cls:len(f.by_type(cls))
            for cls in ("IfcWall","IfcWallStandardCase","IfcSlab","IfcColumn",
                        "IfcDoor","IfcWindow","IfcSpace","IfcOpeningElement",
                        "IfcBuildingStorey")
        }
        e=evidence.get(t["test_id"])
        if e is not None:
            if (e["public_original_ifc_sha256"]!=t["original_ifc_sha256"]
                or e["public_question_sha256"]!=t["public_question_sha256"]):
                raise ValueError("Frozen developer D0 task IFC/question identity drift")
            result=(
                "EXACT_FROZEN_DEVELOPER_D0_ORIGINAL_AUTHOR_FULL_MARK"
                if e["original_author_fixed_developer_D0_full_mark"]
                else "EXACT_FROZEN_DEVELOPER_D0_ORIGINAL_AUTHOR_PARTIAL"
            )
            latest_d0[result]+=1
        else:
            result="NOT_ASSESSED_IN_V08_TO_V010_DEVELOPER_D0"
            latest_d0[result]+=1
        tasks.append({
            "original_task_id":t["test_id"],
            "original_crud":t["crud"],
            "original_category":t["category"],
            "original_public_ifc_sha256":t["original_ifc_sha256"],
            "original_public_question_sha256":t["public_question_sha256"],
            "original_native_ifc_schema":schema,
            "original_native_length_unit_scale_to_m":float(unit),
            "original_native_IFC_Root_count":len(f.by_type("IfcRoot")),
            "original_native_IFC_Product_class_counts":{
                k:v for k,v in sorted(obj_types.items())
            },
            "source_existing_BIM_element_classes_counted_with_IFC_inheritance":
                supported_class_counts,
            "historical_v01_source_projection_gate":prev,
            "historical_v01_source_projection_preflight_issue":
                t["xml_source_preflight_issue"],
            "source_original_ifc_public_data_verified":True,
            "current_v011_all45_source_native_edit_parity":
                "NOT_PROVEN",
            "v08_to_v010_fixed_developer_D0_status":result,
            "v08_to_v010_fixed_developer_D0_evidence":e,
            "real_LLM_scoring_in_this_v011_audit":None,
            "current_matched_25_feedback_run_status":"NOT_RUN",
        })
    totals=sum(latest_d0.values())
    if totals!=45:
        raise ValueError("45 population accidentally filtered in source census")
    if latest_d0["EXACT_FROZEN_DEVELOPER_D0_ORIGINAL_AUTHOR_FULL_MARK"]!=3:
        raise ValueError("Frozen v08-v010 developer full-mark count drift")
    if latest_d0["EXACT_FROZEN_DEVELOPER_D0_ORIGINAL_AUTHOR_PARTIAL"]!=4:
        raise ValueError("Frozen v08-v010 developer partial-mark count drift")
    if latest_d0["NOT_ASSESSED_IN_V08_TO_V010_DEVELOPER_D0"]!=38:
        raise ValueError("Original 45 source coverage untested count drift")
    return {
        "status":"ORIGINAL_45_PUBLIC_IFC_STATIC_CENSUS_V011_NO_45_PARITY",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/136",
        "original_author_revision":AUTHOR_SHA,
        "original_dataset_revision":DATA_SHA,
        "original_edit_task_denominator":45,
        "original_task_id_unique":True,
        "source_original_input_ifc_sha_verification":True,
        "original_native_schema_counts":dict(sorted(schema_counter.items())),
        "original_public_crud_counts":dict(sorted(crud.items())),
        "original_public_category_counts":dict(sorted(category.items())),
        "historical_v01_readonly_source_projection_counts":dict(
            sorted(prior_readonly.items())),
        "v08_to_v010_fixed_developer_D0_status_counts":dict(
            sorted(latest_d0.items())),
        "only_v08_to_v010_newest_partial_native_feature_slices_included":True,
        "v01_to_v07_other_D0_feature_slices_not_relabelled_as_absent":True,
        "native_v011_all_45_source_projection_success_claim":False,
        "native_v011_all_45_direct_XML_edit_supported_claim":False,
        "common_XML_vs_Python_backend_feature_parity_claim":False,
        "new_paid_provider_requests":0,
        "additional_API_cost_usd":"0",
        "original_real_Luna_full_45_scored_history_unchanged":True,
        "no_hidden_ground_truth_access":True,
        "original_task_ledger":tasks,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-root",type=Path,default=Path.cwd())
    parser.add_argument("--author-repo",type=Path,required=True)
    parser.add_argument("--dataset",type=Path,required=True)
    parser.add_argument("--output-json",type=Path,required=True)
    args=parser.parse_args()
    if args.output_json.exists() or args.output_json.is_symlink():
        parser.error("Cannot overwrite pre-existing original audit evidence")
    obj=run(
        args.research_root.resolve(strict=True),
        args.author_repo.resolve(strict=True),
        args.dataset.resolve(strict=True),
    )
    payload=(json.dumps(obj,indent=2,sort_keys=True,
                        ensure_ascii=False)+"\n").encode("utf8")
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    with args.output_json.open("xb") as f:
        f.write(payload)
    print(json.dumps({
        "status":obj["status"],
        "original_cohort":obj["original_edit_task_denominator"],
        "schemas":obj["original_native_schema_counts"],
        "frozen_v08_to_v010_developer_D0":obj[
            "v08_to_v010_fixed_developer_D0_status_counts"],
        "previous_readonly_projection":obj[
            "historical_v01_readonly_source_projection_counts"],
        "report_sha256":file_hash(args.output_json),
    },sort_keys=True))


if __name__=="__main__":
    main()
