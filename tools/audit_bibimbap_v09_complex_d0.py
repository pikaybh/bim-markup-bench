"""Pinned original-public BIBIMBAP complex IFC4X3 source-only developer D0.

No model inference, no paid API, no GT reference in authoring. Compile
fixed declarative XML, verify native independent oracle BEFORE running the
unchanged pinned original author evaluator on a separate mm IFC candidate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v9_projection import project_ifc_v9
from src.runtime.experimental_v9_complex_compiler import compile_declarative_xml_v9
from src.runtime.markup_normal_form import NS
from tools.oracle_bibimbap_v09_native import (
    verify_v09_rotated_slab_square,
    verify_v09_shared_columns_touch_slab,
    verify_v09_boolean_host_door,
)
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import file_hash

Q="{"+NS+"}"
CASES=("geometry_test_14","topological_test_11","topological_test_05")
PUBLIC_UPPER_SLAB="0dxtXCDSn2mfP92h$AiPMM"


def _fixed_source_only_state(tid,root):
    elements=root.find(Q+"Elements")
    if tid=="geometry_test_14":
        source_slabs=root.findall("./"+Q+"Elements/"+Q+"Slab")
        if len(source_slabs)!=1:
            raise ValueError("Original public geometry14 no longer exactly one Slab")
        slab=source_slabs[0]
        original_x=float(slab.get("width"))
        original_y=float(slab.get("depth"))
        if not original_x>original_y:
            raise ValueError("Original Slab no longer longer in native world X")
        slab.set("depth",slab.get("width"))
        return {
            "original_slab_guid":slab.get("ifcGuid"),
            "old_world_rectangle_m":(original_x,original_y),
            "new_world_square_m":(original_x,original_x),
            "original_source_only_selection":"Only original Slab; increase shorter world Y side, preserve original near-Y edge",
        }
    if tid=="topological_test_11":
        slab=next(x for x in root.findall("./"+Q+"Elements/"+Q+"Slab")
                  if x.get("ifcGuid")==PUBLIC_UPPER_SLAB)
        original_columns=root.findall("./"+Q+"Elements/"+Q+"Column")
        if len(original_columns)!=2 or any(
            abs(float(x.get("height"))-1.5)>1e-5 for x in original_columns
        ):
            raise ValueError("Original mapped-column source change; expected two 1.5m Columns")
        if not 2.<float(slab.get("z"))<3.:
            raise ValueError("Original public named upper Slab is no longer above original Columns")
        for column in original_columns:
            column.set("height","2.7")
        return {
            "original_upper_slab_guid_from_public_question":PUBLIC_UPPER_SLAB,
            "original_shared_mapped_columns":sorted(x.get("ifcGuid") for x in original_columns),
            "source_original_heights_metres":(1.5,1.5),
            "developer_new_native_height_metres":2.7,
            "original_source_only_intent":"Extend both source-typed shared mapped Columns to source upper Slab underside (within native author source floor tolerance)",
        }
    if tid=="topological_test_05":
        slabs=root.findall("./"+Q+"Elements/"+Q+"Slab")
        walls=root.findall("./"+Q+"Elements/"+Q+"Wall")
        if len(slabs)!=2 or len(walls)!=7:
            raise ValueError("Original public topological05 no longer seven Boolean Walls/two Slabs")
        ground_slab=min(slabs,key=lambda x:float(x.get("z")))
        min_slab_y=float(ground_slab.get("y"))
        # Choose source South EXTERIOR Wall: horizontal along world X,
        # on slab's minimum-Y bound, full-length away from corners. This
        # choice derives from original source geometry, not grader/GT.
        south=[
            x for x in walls
            if float(x.get("x2"))>float(x.get("x1"))+2
            and abs(float(x.get("y1"))-float(x.get("y2")))<1e-7
            and abs(float(x.get("y1"))-min_slab_y)<.21
        ]
        if len(south)!=1:
            raise ValueError("Source outer south horizontal Boolean Wall ambiguous")
        host=south[0]
        opening_id="source_only_topo05_exterior_south_opening"
        door_id="source_only_topo05_exterior_south_door"
        opener=etree.SubElement(elements,Q+"Opening",{
            "id":opening_id,
            "host":host.get("id"),
            "offset":"2.8",
            "sill":"0",
            "width":"1",
            "height":"2.1",
        })
        door=etree.SubElement(elements,Q+"Door",{
            "id":door_id,"opening":opening_id,
            "width":"1","height":"2.1",
        })
        return {
            "source_external_south_wall_guid":host.get("ifcGuid"),
            "source_external_wall_axis_m":tuple(float(host.get(k)) for k in ("x1","y1","x2","y2")),
            "public_source_ground_slab_guid":ground_slab.get("ifcGuid"),
            "new_xml_opening_id":opening_id,
            "new_xml_door_id":door_id,
            "developer_external_wall_door_m":{"offset":2.8,"width":1.,"height":2.1,"sill":0.},
            "source_only_intent":"Door cuts fully through the original exterior south Boolean Wall, remains interior of existing corner connections",
        }
    raise ValueError("Unknown or unpinned complex native D0 case")


def audit(author:Path,dataset:Path):
    public={r["test_id"]:r for r in public_45(author,dataset)}
    results=[]
    for tid in CASES:
        task=public[tid]
        raw=dataset/"ifc"/task["original_source_ifc_relpath"]
        source_sha=task["original_ifc_sha256"]
        if file_hash(raw)!=source_sha:
            raise ValueError("Original pinned author IFC source SHA drift")
        with tempfile.TemporaryDirectory(prefix="bibi132-source-only-") as temp:
            d=Path(temp)
            raw_model=ifcopenshell.open(str(raw))
            if raw_model.schema!="IFC4X3" or abs(ifcopenshell.util.unit.calculate_unit_scale(raw_model)-.001)>1e-12:
                raise ValueError("Original public source native schema/unit changed")
            source=d/"source_original_ifc4x3_m.ifc"
            ifcopenshell.util.unit.convert_file_length_units(raw_model,"METER").write(str(source))
            view=project_ifc_v9(source)
            root=etree.fromstring(view.xml)
            fixture=_fixed_source_only_state(tid,root)
            candidate=d/"candidate_native_ifc4x3_m.ifc"
            report=compile_declarative_xml_v9(
                source,etree.tostring(root,encoding="utf8"),candidate)
            if tid=="geometry_test_14":
                independent=verify_v09_rotated_slab_square(
                    source,candidate,fixture["original_slab_guid"])
            elif tid=="topological_test_11":
                independent=verify_v09_shared_columns_touch_slab(
                    source,candidate,fixture["original_shared_mapped_columns"],
                    fixture["original_upper_slab_guid_from_public_question"])
            else:
                # The complete XML was parsed and stable-ID compiled; query
                # candidate products only to identify generated GUIDs,
                # never use hidden target/reference IFC in candidate creation.
                result=ifcopenshell.open(str(candidate))
                generated_op=[x for x in result.by_type("IfcOpeningElement")]
                generated_doors=[x for x in result.by_type("IfcDoor")]
                if len(generated_op)!=1 or len(generated_doors)!=1:
                    raise ValueError("Original public file expects exactly one new Door + Opening")
                independent=verify_v09_boolean_host_door(
                    source,candidate,fixture["source_external_south_wall_guid"],
                    generated_op[0].GlobalId,generated_doors[0].GlobalId)
            original_units=d/"candidate_original_native_mm.ifc"
            ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(candidate)),"MILLIMETER").write(str(original_units))
            if ifcopenshell.open(str(original_units)).schema!="IFC4X3":
                raise ValueError("Native schema changed on original author score unit conversion")
            # Frozen source-only XML result, independent native IFC oracle
            # passed. ONLY NOW may original author grader inspect candidate.
            author_grade=grade_author(author,raw,original_units,tid)
            if file_hash(raw)!=source_sha:
                raise ValueError("Original public IFC file modified during v0.9 audit")
            results.append({
                "original_public_task":tid,
                "original_public_question_sha256":task["public_question_sha256"],
                "original_source_ifc_sha256":source_sha,
                "native_normalized_source_sha256":file_hash(source),
                "native_output_original_units_sha256":file_hash(original_units),
                "developer_fixed_source_only_xml_choice":fixture,
                "trusted_runtime_native_operation":report.operations[0].operation,
                "independent_native_ifc_oracle":independent,
                "original_author_grade_after_candidate_frozen":author_grade,
                "new_LLM_model_output":False,
                "original_real_Luna_model_score_modified":False,
            })
    return {
        "status":"ORIGINAL_IFC4X3_COMPLEX_V09_FIXED_DEVELOPER_D0_NOT_LLM",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/132",
        "original_author_revision":"667004e16bd38fd7d538bcee56191465429fd975",
        "original_dataset_revision":"f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca",
        "paid_model_calls":0,
        "paid_cost_usd":"0",
        "real_Luna_historical_45_unchanged":True,
        "native_full_45_capability_parity":False,
        "cases":results,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author-repo",required=True,type=Path)
    parser.add_argument("--dataset",required=True,type=Path)
    parser.add_argument("--output-json",required=True,type=Path)
    args=parser.parse_args()
    if args.output_json.exists() or args.output_json.is_symlink():
        parser.error("Original D0 research evidence path occupied")
    result=audit(args.author_repo.resolve(strict=True),
                 args.dataset.resolve(strict=True))
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    with args.output_json.open("xb") as f:
        f.write((json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf8"))
    print(json.dumps({
        "status":result["status"],
        "new_model_calls":0,
        "original_author_fixed_D0_scores":{
            row["original_public_task"]:
                row["original_author_grade_after_candidate_frozen"]
            for row in result["cases"]
        },
        "report_sha256":file_hash(args.output_json),
    },sort_keys=True))


if __name__=="__main__":
    main()
