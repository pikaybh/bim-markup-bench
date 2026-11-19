"""Two zero-inference developer fixed original BIBIMBAP Column D0 edits.

The only target identifiers below are exposed in PUBLIC questions, not
held-out target data. The original author grader runs only after candidate
IFC is finalized; its score is NOT language-model task success. Original
IFC data and historic Luna score stay immutable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v3_projection import project_ifc_v3
from src.runtime.experimental_v3_column import compile_declarative_xml_v3,_world_bbox
from tools.oracle_bibimbap_column15_16_native import strict_move_column,strict_delete_column
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import file_hash


PUBLIC_TASKS={
    "test_15":{
        "public_target_guid":"22hyxvAPr65PFt9WZfHSMu",
        "operation":"MOVE_COLUMN",
        "public_requested_delta_y_m":-3.,
    },
    "test_16":{
        "public_target_guid":"22hyxvAPr65PFt9WZfHS2x",
        "operation":"DELETE_COLUMN",
    },
}


def run_fixed_d0(author:Path,dataset:Path)->dict:
    tasks={x["test_id"]:x for x in public_45(author,dataset)}
    out=[]
    for task_id,fixture in PUBLIC_TASKS.items():
        task=tasks[task_id]
        if task["crud"]!=("update" if task_id=="test_15" else "delete"):
            raise ValueError("Original public question's CRUD differs from proposed D0")
        original=dataset/"ifc"/task["original_source_ifc_relpath"]
        src_sha=file_hash(original)
        if src_sha!=task["original_ifc_sha256"]:
            raise ValueError("Frozen original IFC hash mismatch")
        with tempfile.TemporaryDirectory(prefix="bibi120-column-d0-") as td:
            root=Path(td)
            src_m=root/"source_m.ifc"
            ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(original)),"METER").write(str(src_m))
            projection=project_ifc_v3(src_m)
            xml=etree.fromstring(projection.xml)
            ns=etree.QName(xml).namespace
            col=next(x for x in xml.findall(".//{"+ns+"}Column")
                     if x.attrib.get("ifcGuid")==fixture["public_target_guid"])
            model_source=ifcopenshell.open(str(src_m))
            before_bbox=_world_bbox(model_source.by_guid(fixture["public_target_guid"]))
            if fixture["operation"]=="MOVE_COLUMN":
                col.set("y",str(float(col.get("y"))+fixture["public_requested_delta_y_m"]))
            else:
                col.getparent().remove(col)
            candidate_m=root/"candidate_m.ifc"
            report=compile_declarative_xml_v3(
                src_m,etree.tostring(xml,encoding="utf8"),candidate_m)
            result_m=ifcopenshell.open(str(candidate_m))
            native_result=(None if fixture["operation"]=="DELETE_COLUMN"
                           else _world_bbox(result_m.by_guid(fixture["public_target_guid"])))
            independent_native_oracle=(
                strict_delete_column(src_m,candidate_m,fixture["public_target_guid"])
                if fixture["operation"]=="DELETE_COLUMN"
                else strict_move_column(src_m,candidate_m,fixture["public_target_guid"],dy=-3.0)
            )
            result_mm=root/"candidate_mm.ifc"
            ifcopenshell.util.unit.convert_file_length_units(
                result_m,"MILLIMETER").write(str(result_mm))
            author_score=grade_author(author,original,result_mm,task_id)
            if file_hash(original)!=src_sha:
                raise ValueError("Original IFC was modified during fixed D0 control")
            out.append({
                "task_id":task_id,
                "original_public_question_sha256":task["public_question_sha256"],
                "original_public_ifc_sha256":src_sha,
                "new_model_requests":0,
                "fixed_developer_input_not_LLM_response":True,
                "compiler_version":"experimental-column-v0.3",
                "operation":fixture["operation"],
                "original_column_guid_from_public_question":fixture["public_target_guid"],
                "before_world_bbox_m":list(map(list,before_bbox)),
                "after_world_bbox_m":(list(map(list,native_result)) if native_result else None),
                "candidate_native_mm_sha256":file_hash(result_mm),
                "original_author_result":author_score,
                "independent_native_task_specific_oracle":independent_native_oracle,
                "independent_45_task_full_success_oracle":False,
                "historical_luna_outcome_unchanged":True,
                "not_a_new_LLM_benchmark_score":True,
            })
    return {
        "status":"TWO_PUBLIC_ORIGINAL_COLUMN_D0_CONTROLS_NOT_MODEL_EVALUATIONS",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/120",
        "model_requests":0,
        "api_cost_usd":"0",
        "real_public_original_ifc_files_untouched":True,
        "compiler_full_45_task_parity":False,
        "developer_fixed_public_task_d0":out,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author-repo",required=True,type=Path)
    parser.add_argument("--dataset",required=True,type=Path)
    parser.add_argument("--output-json",required=True,type=Path)
    args=parser.parse_args()
    if args.output_json.exists() or args.output_json.is_symlink():
        parser.error("Refuse to overwrite previous original IFC D0 evidence")
    record=run_fixed_d0(args.author_repo.resolve(strict=True),args.dataset.resolve(strict=True))
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    with args.output_json.open("xb") as file:
        file.write((json.dumps(record,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf8"))
    print(json.dumps({
        "status":record["status"],
        "cost_usd":record["api_cost_usd"],
        "scores":[{"task_id":r["task_id"],"original_author_result":r["original_author_result"]}
                  for r in record["developer_fixed_public_task_d0"]],
        "sha256":file_hash(args.output_json),
    },sort_keys=True))


if __name__=="__main__":
    main()
