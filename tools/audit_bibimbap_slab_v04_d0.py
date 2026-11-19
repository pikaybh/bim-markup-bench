"""Fixed developer D0 on public BIBIMBAP Slab tasks, NO model calls.

Choices are preregistered in this source fixture before author grading:
- test_02: 10x5m, thickness 0.2m, footprint x -35..-25 and y -2.5..2.5
  so plan center (-30,0), base z=0 ground storey;
- test_14: L2 Slab public GUID translated -0.5m in global z. 'height'
  is interpreted as elevation, NOT a negative physical thickness;
- topological_test_15: upper slab z moved so its bottom world Z touches
  lower slab's top world Z, preserving its original XY location.
Scorer is run only AFTER compiling the developer-owned output IFC, never
inside the model loop; scores do not change original GPT-6 evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v4_projection import project_ifc_v4,_slab_mesh_bbox
from src.runtime.experimental_v4_slab import compile_declarative_xml_v4
from tools.oracle_bibimbap_slab_v04 import verify_create,verify_update
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import file_hash

NS="{urn:bim-markup-bench:toy:v0}"
TASKS=("test_02","test_14","topological_test_15")
HIGH_SLAB="11kJIqz$n2Jf_DfJV1SCVP"
ABOVE_SLAB="0CJwXarnHAeA7eFXxxI_is"
BELOW_SLAB="0CJwXarnHAeA7eFXxxI_hO"


def fixed_d0(author:Path,dataset:Path):
    task_index={x["test_id"]:x for x in public_45(author,dataset)}
    outcomes=[]
    for task_id in TASKS:
        task=task_index[task_id]
        source=dataset/"ifc"/task["original_source_ifc_relpath"]
        checksum=file_hash(source)
        if checksum!=task["original_ifc_sha256"]:
            raise ValueError("Original public BIBIMBAP slab IFC hash mismatch")
        with tempfile.TemporaryDirectory(prefix="bibi122-slab-native-D0-") as td:
            d=Path(td)
            original=ifcopenshell.open(str(source))
            normalized=d/"source_normalized_m.ifc"
            ifcopenshell.util.unit.convert_file_length_units(
                original,"METER").write(str(normalized))
            projected=project_ifc_v4(normalized)
            tree=etree.fromstring(projected.xml)
            elements=tree.find(NS+"Elements")
            levels=tree.find(NS+"Levels")
            initial_native=ifcopenshell.open(str(normalized))
            if task_id=="test_02":
                ground=next(x for x in levels if float(x.get("elevation"))==0)
                etree.SubElement(elements,NS+"Slab",attrib={
                    "id":"d0_predeclared_public_rectangle",
                    "level":ground.get("id"),
                    "x":"-35","y":"-2.5","z":"0",
                    "width":"10","depth":"5","thickness":"0.2",
                })
                state={"operation":"CREATE_SLAB",
                       "fixed_plan_bbox_min_m":[-35.,-2.5,0.],
                       "fixed_plan_bbox_max_m":[-25.,2.5,0.2]}
            elif task_id=="test_14":
                col=next(x for x in elements.findall(NS+"Slab")
                         if x.get("ifcGuid")==HIGH_SLAB)
                col.set("z",str(float(col.get("z"))-0.5))
                state={"operation":"MOVE_SLAB",
                       "public_slab_guid":HIGH_SLAB,
                       "developer_interpretation":"lower world-Z elevation by 0.5m",
                       "fixed_global_z_change_m":-0.5}
            else:
                upper=initial_native.by_guid(ABOVE_SLAB)
                lower=initial_native.by_guid(BELOW_SLAB)
                umin,umax=_slab_mesh_bbox(upper)
                lmin,lmax=_slab_mesh_bbox(lower)
                delta_z=float(lmax[2]-umin[2])
                col=next(x for x in elements.findall(NS+"Slab")
                         if x.get("ifcGuid")==ABOVE_SLAB)
                col.set("z",str(float(col.get("z"))+delta_z))
                state={"operation":"MOVE_SLAB",
                       "public_upper_slab_guid":ABOVE_SLAB,
                       "public_lower_slab_guid":BELOW_SLAB,
                       "developer_rule":"bottom of upper touches top of lower; XY untouched",
                       "computed_input_only_z_delta_m":delta_z}
            candidate_m=d/"candidate_m.ifc"
            compiled=compile_declarative_xml_v4(
                normalized,etree.tostring(tree,encoding="utf8"),candidate_m)
            if task_id=="test_02":
                independent=verify_create(
                    normalized,candidate_m,compiled.operations[0].ifc_guid,
                    bounds_min=(-35.,-2.5,0.),bounds_max=(-25.,2.5,0.2))
            elif task_id=="test_14":
                independent=verify_update(
                    normalized,candidate_m,HIGH_SLAB,
                    kind="move",delta=(0.,0.,-0.5))
            else:
                independent=verify_update(
                    normalized,candidate_m,ABOVE_SLAB,
                    kind="move",delta=(0.,0.,delta_z))
            candidate_mm=d/"candidate_mm.ifc"
            ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(candidate_m)),"MILLIMETER").write(str(candidate_mm))
            grade=grade_author(author,source,candidate_mm,task_id)
            if file_hash(source)!=checksum:
                raise ValueError("Original BIBIMBAP IFC was modified in a D0 task")
            outcomes.append({
                "original_public_task_id":task_id,
                "public_question_sha256":task["public_question_sha256"],
                "original_source_ifc_sha256":checksum,
                "compiler":"experimental-slab-v0.4",
                "developer_fixed_input_not_model":True,
                "model_requests":0,
                "old_luna_45_outcome_unchanged":True,
                "developer_fixture":state,
                "native_compiler_operation":compiled.operations[0].operation,
                "candidate_native_mm_sha256":file_hash(candidate_mm),
                "original_author_grade_after_compilation":grade,
                "independent_native_slab_oracle":independent,
                "full_45_native_backend_parity":False,
                "full_independent_clash_oracle":None,
            })
    return {
        "status":"BIBIMBAP_PUBLIC_SLAB_EXPERIMENTAL_V04_DEVELOPER_D0_ONLY",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/122",
        "model_requests":0,
        "api_cost_usd":"0",
        "not_a_new_model_benchmark_result":True,
        "full_original_45_native_backend_parity":False,
        "tasks":outcomes,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--author-repo",type=Path,required=True)
    p.add_argument("--dataset",type=Path,required=True)
    p.add_argument("--output-json",type=Path,required=True)
    a=p.parse_args()
    if a.output_json.exists() or a.output_json.is_symlink():
        p.error("Refuse overwriting prior original fixed D0 results")
    output=fixed_d0(a.author_repo.resolve(strict=True),a.dataset.resolve(strict=True))
    a.output_json.parent.mkdir(parents=True,exist_ok=True)
    with a.output_json.open("xb") as file:
        file.write((json.dumps(output,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf8"))
    print(json.dumps({
        "status":output["status"],"model_calls":output["model_requests"],
        "author_scores":{x["original_public_task_id"]:
                         x["original_author_grade_after_compilation"] for x in output["tasks"]},
        "report_sha256":file_hash(a.output_json),
    },sort_keys=True))


if __name__=="__main__":
    main()
