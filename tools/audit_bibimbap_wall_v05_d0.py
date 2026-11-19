"""Developer-owned original public BIBIMBAP Wall v0.5 controls, no LLM.

All candidate edits are predeclared from the PUBLIC question and original
source before the pinned original author grader executes. The author grader
runs ONLY on the final native IFC; score is NOT new GPT-6 model success.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import tempfile

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v4_projection import project_ifc_v4
from src.runtime.experimental_v5_wall import compile_declarative_xml_v5
from tools.oracle_bibimbap_wall_v05 import (
    verify_wall_pose_or_length,verify_wall_delete,
)
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import file_hash

NS="{urn:bim-markup-bench:toy:v0}"
CASES={
    "test_11":{"target":"22hyxvAPr65PFt9WZfHSP3","action":"rotate",
               "public_rotation_deg":90,"fixed_pivot":"first public source axis endpoint"},
    "topological_test_12":{"target":"2c8iwp2JP1ox_Asrwk4CZr","action":"shorten",
                           "public_shortening_m":1.,
                           "selection":"Only detached wall outside six explicitly named input wall IDs"},
    "test_19":{"target":"2UsXAbj6n0fwEWqdkVuHyn","action":"delete",
               "public_guid":"2UsXAbj6n0fwEWqdkVuHyn"},
}


def verify_d0(author:Path,dataset:Path)->dict:
    original_tasks={t["test_id"]:t for t in public_45(author,dataset)}
    report=[]
    for task_id,setup in CASES.items():
        row=original_tasks[task_id]
        original=dataset/"ifc"/row["original_source_ifc_relpath"]
        original_sha=file_hash(original)
        if original_sha!=row["original_ifc_sha256"]:
            raise ValueError("Original BIBIMBAP IFC source checksum mismatch")
        with tempfile.TemporaryDirectory(prefix="bibi124-wall-original-D0-") as td:
            temp=Path(td)
            src=temp/"source_metres.ifc"
            ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(original)),"METER").write(str(src))
            tree=etree.fromstring(project_ifc_v4(src).xml)
            wall=next(x for x in tree.findall(".//"+NS+"Wall")
                      if x.get("ifcGuid")==setup["target"])
            old=(float(wall.get("x1")),float(wall.get("y1")),
                 float(wall.get("x2")),float(wall.get("y2")))
            x,y,xx,yy=old
            original_length=math.hypot(xx-x,yy-y)
            action=setup["action"]
            if action=="rotate":
                wall.set("x2",str(x-(yy-y)))
                wall.set("y2",str(y+(xx-x)))
            elif action=="shorten":
                wall.set("x2",str(xx-(xx-x)/original_length))
                wall.set("y2",str(yy-(yy-y)/original_length))
            elif action=="delete":
                localid=wall.get("id")
                wall.getparent().remove(wall)
                relations=tree.find(NS+"Relations")
                for rel in list(relations):
                    if rel.get("from")==localid or rel.get("to")==localid:
                        relations.remove(rel)
            else:
                raise ValueError("Unknown predeclared public D0 task")
            destination=temp/"candidate_m.ifc"
            compiled=compile_declarative_xml_v5(
                src,etree.tostring(tree,encoding="utf8"),destination)
            if action=="rotate":
                independent=verify_wall_pose_or_length(
                    src,destination,setup["target"],operation="rotate",angle_deg=90.)
            elif action=="shorten":
                independent=verify_wall_pose_or_length(
                    src,destination,setup["target"],operation="shorten",shorten_metres=1.)
            else:
                independent=verify_wall_delete(src,destination,setup["target"])
            candidate_mm=temp/"candidate_mm.ifc"
            ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(destination)),"MILLIMETER").write(str(candidate_mm))
            grade=grade_author(author,original,candidate_mm,task_id)
            if file_hash(original)!=original_sha:
                raise ValueError("Original public data mutated during fixed D0")
            report.append({
                "task_id":task_id,
                "question_sha256":row["public_question_sha256"],
                "original_native_source_sha256":original_sha,
                "compiler_version":"experimental-wall-v0.5",
                "developer_authored_input_not_LLM_output":True,
                "public_input_selected_task":setup,
                "original_wall_axis_xy_m":old,
                "original_wall_length_m":original_length,
                "trusted_native_operation":compiled.operations[0].operation,
                "independent_native_oracle":independent,
                "original_author_score_after_compilation":grade,
                "candidate_native_mm_sha256":file_hash(candidate_mm),
                "full_45_native_parity_achieved":False,
            })
    return {
        "status":"BIBIMBAP_ORIGINAL_PUBLIC_WALL_V05_DEVELOPER_FIXED_D0_ONLY",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/124",
        "model_calls":0,
        "api_cost_usd":"0",
        "historical_luna_original_scores_unchanged":True,
        "not_a_new_model_benchmark":True,
        "original_paper_full45_feature_parity":False,
        "tasks":report,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author-repo",type=Path,required=True)
    ap.add_argument("--dataset",type=Path,required=True)
    ap.add_argument("--output-json",type=Path,required=True)
    args=ap.parse_args()
    if args.output_json.exists() or args.output_json.is_symlink():
        ap.error("Refuse overwriting original D0 evidence report")
    record=verify_d0(args.author_repo.resolve(strict=True),
                     args.dataset.resolve(strict=True))
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    with args.output_json.open("xb") as file:
        file.write((json.dumps(record,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf8"))
    print(json.dumps({
        "status":record["status"],
        "model_calls":record["model_calls"],
        "original_author_scores":{
            x["task_id"]:x["original_author_score_after_compilation"] for x in record["tasks"]},
        "report_sha256":file_hash(args.output_json),
    },sort_keys=True))


if __name__=="__main__":
    main()
