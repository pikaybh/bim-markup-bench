"""Pinned original BIBIMBAP IFC2X3/IFC4 legacy v0.8 native D0 audit.

ONLY original public questions & original IFC support source-only developer
choices. Independent native oracle runs first; original pinned author grader
runs *after* the candidate IFC is frozen. No GT/hidden solution is viewed or
used for source edits; no paid LLM calls, no historical model-score updates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v8_legacy_projection import project_legacy_v8,Q
from src.runtime.experimental_v8_legacy_compiler import compile_declarative_xml_v8
from tools.oracle_bibimbap_v08_native import (
    verify_ifc4_wall,verify_ifc2x3_space,verify_ifc2x3_hosted_door,
)
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import file_hash

CASES=("geometry_test_03","geometry_test_04","geometry_test_05")
SOUTH_WALL="3YQ$1CPXD2Mh2vQ18vV$hw"
NORTH_WALL="3YQ$1CPXD2Mh2vQ18vV$ig"


def _fixture(task_id,f,root):
    ground=next(x for x in root.findall("./"+Q+"Levels/"+Q+"Level")
                if abs(float(x.get("placementZ")))<1e-8)
    elements=root.find(Q+"Elements")
    if task_id=="geometry_test_05":
        assert f.schema=="IFC4" and ground.get("elevationState")=="MISSING"
        new=etree.SubElement(elements,Q+"Wall",{
            "id":"original_public_geometry05_wall",
            "level":ground.get("id"),
            "x1":"10","y1":"5","z1":"0",
            "x2":"15","y2":"5","z2":"0",
            "height":"3","thickness":"0.2",
        })
        return {
            "new_ids":(new.get("id"),),
            "public_instruction":"Create 5m Wall from world plan (10,5) towards (1,0)",
            "developer_added_wall_height_m":3.,
            "developer_added_wall_thickness_m":.2,
            "missing_native_storey_elevation_not_fabricated":True,
        }
    if task_id=="geometry_test_04":
        assert f.schema=="IFC2X3"
        col=f.by_guid("3A5GfH23DBvBYpavCfWh4z")
        assert col.is_a("IfcColumn")
        new=etree.SubElement(elements,Q+"Space",{
            "id":"original_public_geometry04_left_room",
            "level":ground.get("id"),
            "x":"0.2","y":"0.2","z":"0",
            "width":"6.1","depth":"6.5","height":"2.8",
        })
        return {
            "new_ids":(new.get("id"),),
            "public_instruction":"Insert an IFC Space strictly left of named original Column",
            "named_original_reference_column_guid":col.GlobalId,
            "developer_room_bottom_left_m":(.2,.2,0),
            "developer_room_dimensions_m":(6.1,6.5,2.8),
            "author_score_will_be_reported_separately":True,
        }
    assert task_id=="geometry_test_03" and f.schema=="IFC2X3"
    walls=root.findall("./"+Q+"Elements/"+Q+"Wall")
    south=next(x for x in walls if x.get("ifcGuid")==SOUTH_WALL)
    assert f.by_guid(NORTH_WALL).is_a("IfcWallStandardCase")
    nearest_north=sorted(
        (float(x.get("y1")),x) for x in walls
        if float(x.get("y1"))>float(south.get("y1"))
    )[0][1]
    if nearest_north.get("ifcGuid")!=NORTH_WALL:
        raise ValueError("Public source original nearest northern Wall changed")
    opening_id="original_public_geometry03_new_opening"
    door_id="original_public_geometry03_new_door"
    # Source-only selected 1m door near world x=0, positive-X original Wall
    # from x=-3.25 to +3.25. Native Opening offset from x=-3.25 is
    # 2.75m to the left edge (-0.5) of the rectangular 1m opening.
    opening=etree.SubElement(elements,Q+"Opening",{
        "id":opening_id,"host":nearest_north.get("id"),
        "offset":"2.75","sill":"0","width":"1","height":"2.1",
    })
    door=etree.SubElement(elements,Q+"Door",{
        "id":door_id,"opening":opening_id,
        "width":"1","height":"2.1",
    })
    return {
        "new_ids":(opening.get("id"),door.get("id")),
        "original_named_south_wall_guid":SOUTH_WALL,
        "developer_selected_nearest_north_original_wall_guid":NORTH_WALL,
        "door_world_center_m":(0.,1.6,1.05),
        "opening_dimensions_m":(1.,.4,2.1),
        "door_dimensions_m":(1.,.08,2.1),
        "public_instruction":"Add a Door to source Wall north of explicitly named original south Wall",
    }


def audit(author:Path,dataset:Path):
    tasks={row["test_id"]:row for row in public_45(author,dataset)}
    records=[]
    for tid in CASES:
        item=tasks[tid]
        original=dataset/"ifc"/item["original_source_ifc_relpath"]
        expected_sha=item["original_ifc_sha256"]
        if file_hash(original)!=expected_sha:
            raise ValueError("Pinned original public IFC bytes changed")
        with tempfile.TemporaryDirectory(prefix="bibi130-native-schema-") as temp:
            folder=Path(temp)
            f=ifcopenshell.open(str(original))
            original_schema=f.schema
            if original_schema not in ("IFC2X3","IFC4"):
                raise ValueError("Unexpected original author source schema")
            normalized=folder/"source_original_schema_metres.ifc"
            if abs(ifcopenshell.util.unit.calculate_unit_scale(f)-.001)>1e-12:
                raise ValueError("Original public source must be native millimetres")
            ifcopenshell.util.unit.convert_file_length_units(
                f,"METER").write(str(normalized))
            native=ifcopenshell.open(str(normalized))
            if native.schema!=original_schema:
                raise ValueError("Original IFC schema changed during metre normalization")
            project=project_legacy_v8(normalized)
            root=etree.fromstring(project.xml)
            fixture=_fixture(tid,native,root)
            result=folder/"candidate_original_schema_metres.ifc"
            compiled=compile_declarative_xml_v8(
                normalized,etree.tostring(root,encoding="utf8"),result)
            if tid=="geometry_test_05":
                oracle=verify_ifc4_wall(
                    normalized,result,compiled.operations[0].ifc_guid)
            elif tid=="geometry_test_04":
                from src.runtime.experimental_v8_legacy_compiler import _det_guid
                gid=_det_guid(project.source_sha256,fixture["new_ids"][0])
                oracle=verify_ifc2x3_space(normalized,result,gid)
            else:
                from src.runtime.experimental_v8_legacy_compiler import _det_guid
                op_guid=_det_guid(project.source_sha256,fixture["new_ids"][0])
                door_guid=_det_guid(project.source_sha256,fixture["new_ids"][1])
                oracle=verify_ifc2x3_hosted_door(
                    normalized,result,op_guid,door_guid)
            original_unit_candidate=folder/"candidate_native_mm.ifc"
            ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(result)),"MILLIMETER").write(
                    str(original_unit_candidate))
            if ifcopenshell.open(str(original_unit_candidate)).schema!=original_schema:
                raise ValueError("Native result original schema changed before original author scoring")
            # Original author grader only runs after source-only fixed XML was
            # compiled and independent oracle passed; never feeds authoring.
            grade=grade_author(author,original,original_unit_candidate,tid)
            if file_hash(original)!=expected_sha:
                raise ValueError("Immutable original public input IFC source modified")
            records.append({
                "original_public_task_id":tid,
                "original_native_schema":original_schema,
                "original_public_ifc_sha256":expected_sha,
                "public_question_sha256":item["public_question_sha256"],
                "source_m_normalized_sha256":file_hash(normalized),
                "source_only_fixed_developer_fixture":fixture,
                "new_edited_xml_generated_by_model":False,
                "trusted_native_schema_preserving_operation":compiled.operations[0].operation,
                "independent_native_ifc_oracle":oracle,
                "original_author_grade_after_freezing_d0":grade,
                "candidate_original_m_units_sha256":file_hash(result),
                "candidate_original_mm_units_sha256":file_hash(original_unit_candidate),
                "full_45_runtime_parity_not_proven":True,
            })
    return {
        "status":"EXPERIMENTAL_LEGACY_V08_NATIVE_SOURCE_PRESERVING_DEVELOPER_D0_ONLY",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/130",
        "source_original_dataset_revision":"f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca",
        "original_author_scoring_revision":"667004e16bd38fd7d538bcee56191465429fd975",
        "new_paid_provider_calls":0,
        "additional_paid_usd":"0",
        "real_GPT6_Luna_historical_score_unchanged":True,
        "all_original_IFC_schema_preserved":True,
        "runtime_all_45_original_tasks_native_edit_equivalent":False,
        "developer_fixed_D0_not_a_model_benchmark":True,
        "tasks":records,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author-repo",required=True,type=Path)
    parser.add_argument("--dataset",required=True,type=Path)
    parser.add_argument("--output-json",required=True,type=Path)
    args=parser.parse_args()
    if args.output_json.exists() or args.output_json.is_symlink():
        parser.error("Never overwrite earlier original source/score evidence")
    result=audit(args.author_repo.resolve(strict=True),
                 args.dataset.resolve(strict=True))
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    with args.output_json.open("xb") as h:
        h.write((json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf8"))
    print(json.dumps({
        "status":result["status"],
        "new_paid_model_calls":0,
        "developer_d0_original_author_scores":{
            x["original_public_task_id"]:x["original_author_grade_after_freezing_d0"]
            for x in result["tasks"]
        },
        "report_sha256":file_hash(args.output_json),
    },sort_keys=True))


if __name__=="__main__":
    main()
