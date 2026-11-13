"""Prospective v0.7 original-public BIBIMBAP source and developer D0 audit.

The original author grader is invoked ONLY AFTER code+native IFC oracle and
NEVER used as authoring feedback. No model inference or paid API calls.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v7_projection import (
    native_source_admission_v7,project_ifc_v7,
)
from src.runtime.experimental_v7_compiler import compile_declarative_xml_v7
from tools.oracle_bibimbap_v07_source import (
    verify_v7_projected_source,verify_column_move,verify_slab_create,
)
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import file_hash

NS="{urn:bim-markup-bench:toy:v0}"
TASKS=(
    "geometry_test_01","geometry_test_03","geometry_test_04",
    "geometry_test_05","geometry_test_14","geometry_test_15",
    "topological_test_05","topological_test_11","topological_test_17",
)
MAPPED_COL_TARGET="3lOEkLxYb9$uRd50gnIDqu"
MAPPED_COL_Y_OFFSET=-.75


def audit(author:Path,dataset:Path)->dict:
    original={row["test_id"]:row for row in public_45(author,dataset)}
    reports=[]
    for tid in TASKS:
        item=original[tid]
        source=dataset/"ifc"/item["original_source_ifc_relpath"]
        if file_hash(source)!=item["original_ifc_sha256"]:
            raise ValueError("Original public IFC SHA256 changed")
        admission=native_source_admission_v7(source)
        row={
            "original_public_task_id":tid,
            "original_public_question_sha256":item["public_question_sha256"],
            "original_source_sha256":file_hash(source),
            "original_ifc_schema":admission["ifc_schema"],
            "original_readonly_admission":admission,
            "source_readonly":True,
            "legacy_schema_unconditionally_supported_for_editing":False,
            "original_45_native_edit_parity":False,
        }
        if admission["ifc_schema"]!="IFC4X3":
            row.update({
                "projection_status":"NATIVE_READONLY_ONLY",
                "original_ifc4x3_xml_view_verified":False,
                "native_operation_success":False,
                "native_operation_attempted":False,
                "original_author_score":None,
                "blocker":"Legacy original source schema cannot be relabelled as IFC4X3; IFC4 may also lack explicit storey elevation",
            })
            reports.append(row)
            continue
        with tempfile.TemporaryDirectory(prefix="bibi128-v07-real-") as temp:
            d=Path(temp)
            f=ifcopenshell.open(str(source))
            normalized=d/"source_m.ifc"
            ifcopenshell.util.unit.convert_file_length_units(f,"METER").write(str(normalized))
            view=project_ifc_v7(normalized)
            proof=verify_v7_projected_source(source,normalized,view.xml)
            row.update({
                "projection_status":"NATIVE_PARTIAL_IFC4X3_XML_VIEW_VERIFIED",
                "original_ifc4x3_xml_view_verified":True,
                "native_projection_oracle":proof,
                "projected_native_class_counts":dict(view.supported_class_counts),
                "opaque_native_class_counts":dict(view.unsupported_class_counts),
            })
            if tid in ("geometry_test_01","geometry_test_15"):
                tree=etree.fromstring(view.xml)
                if tid=="geometry_test_01":
                    columns=list(tree.findall(".//"+NS+"Column"))
                    if len(columns)!=4:
                        raise ValueError("Expected exactly four original mapped native Columns")
                    lo=[min(float(c.get(key)) for c in columns) for key in ("x","y")]
                    hi=[max(float(c.get(key))+float(c.get(dim))
                         for c in columns) for key,dim in (("x","width"),("y","depth"))]
                    top=max(float(c.get("z"))+float(c.get("height")) for c in columns)
                    if not all(abs(float(c.get("z"))+float(c.get("height"))-top)<1e-5
                               for c in columns):
                        raise ValueError("Original four upper column edges have differing height")
                    levels=tree.findall(".//"+NS+"Level")
                    ground=next(x for x in levels if abs(float(x.get("elevation")))<1e-8)
                    # Explicit developer fixture: full 3x3m span across
                    # four outer column edges, 0.2m world-Z thickness.
                    attrs={
                        "id":"original_geo01_source_full_roof_slab",
                        "level":ground.get("id"),
                        "x":str(lo[0]),"y":str(lo[1]),"z":str(top),
                        "width":str(hi[0]-lo[0]),"depth":str(hi[1]-lo[1]),
                        "thickness":"0.2",
                    }
                    etree.SubElement(tree.find(NS+"Elements"),NS+"Slab",attrs)
                    expected={"minimum":(*lo,top),
                              "maximal":(hi[0],hi[1],top+.2)}
                    fixture={
                        "developer_chosen_slab_bounds_m":expected,
                        "public_question_interpretation":"Slab atop four original Column outer top edges; 0.2m thickness",
                        "original_four_source_mapped_column_guids":sorted(x.get("ifcGuid") for x in columns),
                    }
                else:
                    nodes=tree.findall(".//"+NS+"Column")
                    if len(nodes)!=4:
                        raise ValueError("Expected original geometry15 four mapped Columns")
                    target=next(x for x in nodes if x.get("ifcGuid")==MAPPED_COL_TARGET)
                    origin=float(target.get("y"))
                    target.set("y",str(origin+MAPPED_COL_Y_OFFSET))
                    fixture={
                        "developer_selected_outlier_mapped_column_globalid":MAPPED_COL_TARGET,
                        "original_native_bottom_y_m":origin,
                        "target_native_bottom_y_m":origin+MAPPED_COL_Y_OFFSET,
                        "world_translation_m":(0.,MAPPED_COL_Y_OFFSET,0.),
                        "public_question_interpretation":"Align upper right Column y to upper left so four Column centers form a rectangle",
                    }
                candidate=d/"candidate_m.ifc"
                compiled=compile_declarative_xml_v7(
                    normalized,etree.tostring(tree,encoding="utf8"),candidate)
                if tid=="geometry_test_01":
                    native_oracle=verify_slab_create(
                        normalized,candidate,compiled.operations[0].ifc_guid,
                        minimum=expected["minimum"],maximal=expected["maximal"])
                else:
                    native_oracle=verify_column_move(
                        normalized,candidate,MAPPED_COL_TARGET,(0.,MAPPED_COL_Y_OFFSET,0.))
                original_units=d/"candidate_original_mm.ifc"
                if not abs(ifcopenshell.util.unit.calculate_unit_scale(f)-0.001)<1e-12:
                    raise ValueError("Original public input unexpected length units")
                ifcopenshell.util.unit.convert_file_length_units(
                    ifcopenshell.open(str(candidate)),"MILLIMETER").write(str(original_units))
                grade=grade_author(author,source,original_units,tid)
                row.update({
                    "native_operation_attempted":True,
                    "native_operation_success":True,
                    "developer_authored_not_a_new_LLM_model_result":True,
                    "source_public_only_fixed_fixture":fixture,
                    "native_trusted_operation":compiled.operations[0].operation,
                    "independent_native_edit_oracle":native_oracle,
                    "original_author_score":grade,
                    "native_candidate_original_units_sha256":file_hash(original_units),
                })
            else:
                row.update({
                    "native_operation_attempted":False,
                    "native_operation_success":False,
                    "developer_authored_not_a_new_LLM_model_result":True,
                    "original_author_score":None,
                    "remaining_gap":"Source projection only. No proven original task mutation or D0/I0 author grade.",
                })
        if file_hash(source)!=item["original_ifc_sha256"]:
            raise ValueError("Public original source IFC modified during audit")
        reports.append(row)
    return {
        "status":"ORIGINAL_NINE_SOURCE_COMPAT_V07_READONLY_PLUS_TWO_DEVELOPER_D0_EDITS",
        "original_source_author_sha":"667004e16bd38fd7d538bcee56191465429fd975",
        "original_source_dataset_sha":"f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca",
        "new_model_calls":0,"paid_usd":"0",
        "previous_GPT6_Luna_45_results_immutable":True,
        "native_source_read_admitted":sum(x["source_readonly"] for x in reports),
        "original_ifc4x3_source_projections_independently_verified":sum(
            x["original_ifc4x3_xml_view_verified"] for x in reports),
        "original_legacy_ifc2x3_ifc4_still_edit_blocked":sum(
            x["original_ifc_schema"]!="IFC4X3" for x in reports),
        "developer_d0_native_edits_verified":sum(
            x["native_operation_success"] for x in reports),
        "real_model_benchmark_parity_45_of_45":False,
        "tasks":reports,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author-repo",type=Path,required=True)
    ap.add_argument("--dataset",type=Path,required=True)
    ap.add_argument("--output-json",type=Path,required=True)
    args=ap.parse_args()
    if args.output_json.exists() or args.output_json.is_symlink():
        ap.error("Refuse overwriting original D0 evidence report")
    result=audit(args.author_repo.resolve(strict=True),args.dataset.resolve(strict=True))
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    with args.output_json.open("xb") as f:
        f.write((json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf8"))
    print(json.dumps({
        "status":result["status"],
        "new_model_calls":0,
        "original_legacy_edit_blocked":result["original_legacy_ifc2x3_ifc4_still_edit_blocked"],
        "original_ifc4x3_sources_xml":result["original_ifc4x3_source_projections_independently_verified"],
        "original_developer_native_edits":result["developer_d0_native_edits_verified"],
        "original_author_scores":{
            r["original_public_task_id"]:r["original_author_score"]
            for r in result["tasks"] if r["original_author_score"] is not None
        },
        "report_sha256":file_hash(args.output_json),
    },sort_keys=True))


if __name__=="__main__":
    main()
