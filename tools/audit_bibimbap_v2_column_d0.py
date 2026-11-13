"""Zero-model-call real BIBIMBAP test_04 developer-authored Column D0.

This is NOT GPT-6 model output or 45-task success. Source/score frozen:
public question is 'Insert a column with height of 3m in (12, 8)'.
Dimensions not specified by task are predeclared as width=depth=0.3m
without consulting private grader/GT. Native IFC4X3 and author scorer
run once, with exact source/user original hashes intact.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import file_hash
from src.runtime.ifc_projection import project_ifc
from src.runtime.experimental_v2_column import compile_declarative_xml_v2,_world_bbox

FIXTURE={
    "x":"12","y":"8","z":"0",
    "width":"0.3","depth":"0.3","height":"3",
}
ISSUE="https://github.com/pikaybh/bim-markup-bench/issues/118"

def evaluate(author:Path,dataset:Path)->dict:
    task=next(x for x in public_45(author,dataset) if x["test_id"]=="test_04")
    source=dataset/"ifc"/task["original_source_ifc_relpath"]
    source_hash=file_hash(source)
    if source_hash!=task["original_ifc_sha256"]:
        raise ValueError("Original IFC source hash mismatch")
    with tempfile.TemporaryDirectory(prefix="bibimbap-v2-column-D0-") as td:
        root=Path(td)
        model=ifcopenshell.open(str(source))
        src_m=root/"frozen_source_m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(model,"METER").write(str(src_m))
        root_xml=etree.fromstring(project_ifc(src_m).xml)
        namespace=etree.QName(root_xml).namespace
        lvl=next(v for v in root_xml.find("{"+namespace+"}Levels")
                 if v.get("elevation")=="0")
        attrs={"id":"bibi118_preregistered_fixed_d0_column",
               "level":lvl.get("id"),**FIXTURE}
        etree.SubElement(root_xml.find("{"+namespace+"}Elements"),
                         "{"+namespace+"}Column",attrib=attrs)
        candidate_m=root/"candidate_m.ifc"
        native=compile_declarative_xml_v2(
            src_m,etree.tostring(root_xml,encoding="utf8"),
            candidate_m)
        result_m=ifcopenshell.open(str(candidate_m))
        actual_column=result_m.by_guid(native.operations[0].ifc_guid)
        minimum,maximum=_world_bbox(actual_column)
        result_mm=root/"candidate_mm.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            result_m,"MILLIMETER").write(str(result_mm))
        score=grade_author(author,source,result_mm,"test_04")
        if file_hash(source)!=source_hash:
            raise ValueError("Original public IFC mutated during zero-call D0")
        if score["status"]!="AUTHOR_SCORED":
            raise ValueError("Original author scorer failed in isolated process")
        return {
            "status":"REAL_BIBIMBAP_TEST04_DEVELOPER_D0_XML_COMPILER_ORIGINAL_AUTHOR_SCORED",
            "issue":ISSUE,
            "source_task_id":"test_04",
            "source_crud":"create",
            "public_question_sha256":task["public_question_sha256"],
            "original_ifc_source_sha256":source_hash,
            "developer_authored_fixture_not_model_output":True,
            "new_luna_model_requests":0,
            "api_cost_usd":"0",
            "original_historical_45_task_results_modified":False,
            "source_native_ifc_schema":model.schema,
            "candidate_compiler_version":"experimental-column-v0.2",
            "candidate_native_ifc_sha256":file_hash(result_mm),
            "native_new_ifc_entity_class":"IfcColumn",
            "native_new_ifc_guid":native.operations[0].ifc_guid,
            "native_world_bbox_min_m":list(minimum),
            "native_world_bbox_max_m":list(maximum),
            "developer_fixed_unrequested_dimensions_m":
                {"width":0.3,"depth":0.3},
            "native_commit_status":native.as_dict()["status"],
            "original_author_metric_origin":"PINNED_ORIGINAL_AUTHOR_BIBIMBAP",
            "original_author_results":score,
            "independent_full_scene_clash_oracle_pass":None,
            "45_task_backend_parity_achieved":False,
        }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author-repo",type=Path,required=True)
    ap.add_argument("--dataset",type=Path,required=True)
    ap.add_argument("--output-json",type=Path,required=True)
    args=ap.parse_args()
    if args.output_json.exists():
        ap.error("Never overwrite D0 real IFC verification report")
    result=evaluate(args.author_repo.resolve(strict=True),
                    args.dataset.resolve(strict=True))
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    with args.output_json.open("xb") as f:
        f.write((json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf8"))
    print(json.dumps({
        "status":result["status"],"model_calls":result["new_luna_model_requests"],
        "author_result":result["original_author_results"],
        "backend_parity":result["45_task_backend_parity_achieved"],
        "report_sha256":file_hash(args.output_json),
    },sort_keys=True))

if __name__=="__main__":
    main()
