"""Pinned original public BIBIMBAP hosted v0.6 deterministic developer D0.

No paid model use, no private solution access, and never treat as language
model success. Author scorer invoked only after native compile and oracle.
Choices are explicit fixture decisions based on public original task text
and original source IFC topology / geometry.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v4_projection import project_ifc_v4
from src.runtime.experimental_v6_hosted import compile_declarative_xml_v6
from tools.oracle_bibimbap_hosted_v06 import (
    verify_hosted_pair_delete,verify_hosted_move,_shape,
)
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import file_hash

NS="{urn:bim-markup-bench:toy:v0}"
TASKS=("test_17","test_18","geometry_test_13","geometry_test_16")
BASIC_DOOR="11kJIqz$n2Jf_DfJV1SDY7"
BASIC_OPENING="0APGbZXNKfgPNB$VQQZ0pi"
GEO13_WIDE_WINDOW="2KbOAL4v52mv2YJ6fTql5A"
GEO16_LEFT_DOOR="1g0NIEjcH1lfGqbYWRqtDg"
GEO16_RIGHT_DOOR="1g0NIEjcH1lfGqbYWRqt8M"


def _remove_pair(root,native,filling_guid,opening_guid):
    elements=root.find(NS+"Elements")
    filler=next(x for x in elements if x.get("ifcGuid")==filling_guid)
    opening=next(x for x in elements if x.get("ifcGuid")==opening_guid)
    if not (
        native.by_guid(filling_guid).FillsVoids[0].RelatingOpeningElement.GlobalId==opening_guid
    ):
        raise ValueError("Fixed developer pair is not actually hosted in source IFC")
    elements.remove(filler)
    elements.remove(opening)
    return {
        "explicit_native_filling_guid":filling_guid,
        "explicit_native_opening_guid":opening_guid,
        "native_delete_semantics":"delete filling plus exclusively-filled opening; host preserved",
    }


def _public_middle_door(native):
    doors=native.by_type("IfcDoor")
    if len(doors)!=3:
        raise ValueError("Expected exactly three original public doors in geometry_test_16")
    xcenters={}
    for door in doors:
        pts,_,_=_shape(native,door)
        xcenters[door.GlobalId]=float((pts[:,0].min()+pts[:,0].max())/2)
    left=xcenters[GEO16_LEFT_DOOR]
    right=xcenters[GEO16_RIGHT_DOOR]
    eligible=[gid for gid,cx in xcenters.items()
              if gid not in (GEO16_LEFT_DOOR,GEO16_RIGHT_DOOR)
              and min(left,right)<cx<max(left,right)]
    if len(eligible)!=1:
        raise ValueError("Public geometry question does not uniquely specify center Door")
    return eligible[0],xcenters


def fixed_d0(author:Path,dataset:Path)->dict:
    original={entry["test_id"]:entry for entry in public_45(author,dataset)}
    results=[]
    for task_id in TASKS:
        row=original[task_id]
        src=dataset/"ifc"/row["original_source_ifc_relpath"]
        src_hash=file_hash(src)
        if src_hash!=row["original_ifc_sha256"]:
            raise ValueError("Pinned BIBIMBAP source IFC SHA does not match original public packet")
        with tempfile.TemporaryDirectory(prefix="bibi126-hosted-D0-") as td:
            folder=Path(td)
            f=ifcopenshell.open(str(src))
            normalized=folder/"source_m.ifc"
            ifcopenshell.util.unit.convert_file_length_units(f,"METER").write(str(normalized))
            native=ifcopenshell.open(str(normalized))
            doc=etree.fromstring(project_ifc_v4(normalized).xml)
            if task_id=="test_17":
                filler=BASIC_DOOR
                opening=native.by_guid(filler).FillsVoids[0].RelatingOpeningElement.GlobalId
                fixture=_remove_pair(doc,native,filler,opening)
                fixture["public_task"]="Remove the public-ID Door"
                operation="delete"
            elif task_id=="test_18":
                opening=BASIC_OPENING
                native_open=native.by_guid(opening)
                fill=[rel.RelatedBuildingElement for rel in native_open.HasFillings]
                if len(fill)!=1 or not fill[0].is_a("IfcWindow"):
                    raise ValueError("Public source Opening must have exactly one original Window fill")
                filler=fill[0].GlobalId
                fixture=_remove_pair(doc,native,filler,opening)
                fixture["public_task"]="Remove the public-ID Opening"
                fixture["explicit_cascade_semantics_note"]="Also removes filled Window; this is a developer choice, not original evaluator truth"
                operation="delete"
            elif task_id=="geometry_test_16":
                filler,xcenters=_public_middle_door(native)
                opening=native.by_guid(filler).FillsVoids[0].RelatingOpeningElement.GlobalId
                fixture=_remove_pair(doc,native,filler,opening)
                fixture["public_task"]="Remove the original Door strictly between two named Door IDs"
                fixture["original_public_native_door_center_x_m"]=xcenters
                operation="delete"
            elif task_id=="geometry_test_13":
                filler=GEO13_WIDE_WINDOW
                native_window=native.by_guid(filler)
                if not native_window.is_a("IfcWindow"):
                    raise ValueError("Public wider target is not IFC Window")
                opening=native_window.FillsVoids[0].RelatingOpeningElement.GlobalId
                node=next(x for x in doc.findall(".//"+NS+"Opening")
                          if x.get("ifcGuid")==opening)
                w=next(x for x in doc.findall(".//"+NS+"Window")
                       if x.get("ifcGuid")==filler)
                if float(w.get("width"))<=1.5:
                    raise ValueError("Developer wider-than-1.50m selection changed")
                host=native.by_guid(opening).VoidsElements[0].RelatingBuildingElement
                frame=ifcopenshell.util.placement.get_local_placement(host.ObjectPlacement)
                # Public question is +3m in *global X*. This input wall's
                # original local X is exactly world +X, not inferred later
                # from private grader feedback.
                import numpy as np
                if not np.allclose(frame[:3,0],(1,0,0),atol=1e-8):
                    raise ValueError("Original source host no longer points along world positive X")
                old_offset=float(node.get("offset"))
                node.set("offset",str(old_offset+3.0))
                fixture={
                    "public_task":"Move wider-than-1.50m original Window by global +3m X",
                    "selected_original_window_guid":filler,
                    "opening_guid":opening,
                    "original_window_width_m":float(w.get("width")),
                    "world_x_offset_m":3.,
                    "original_opening_host_local_x_m":old_offset,
                    "candidate_opening_host_local_x_m":old_offset+3.,
                }
                operation="move"
            else:
                raise ValueError("Undeclared original D0 case")
            candidate=folder/"candidate_m.ifc"
            report=compile_declarative_xml_v6(
                normalized,etree.tostring(doc,encoding="utf8"),candidate)
            if operation=="move":
                independent=verify_hosted_move(
                    normalized,candidate,opening,delta_metres=3.,
                    expected_filling_guid=filler)
            else:
                independent=verify_hosted_pair_delete(
                    normalized,candidate,filler,opening)
            final_original_units=folder/"candidate_mm.ifc"
            ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(candidate)),"MILLIMETER").write(str(final_original_units))
            grade=grade_author(author,src,final_original_units,task_id)
            if file_hash(src)!=src_hash:
                raise ValueError("Original BIBIMBAP source changed in developer D0")
            results.append({
                "original_public_task_id":task_id,
                "public_question_sha256":row["public_question_sha256"],
                "original_ifc_sha256":src_hash,
                "developer_predeclared_action":fixture,
                "compiler_version":"experimental-hosted-v0.6",
                "trusted_native_operation":report.operations[0].operation,
                "independent_native_ifc_oracle":independent,
                "original_author_grade_after_d0":grade,
                "candidate_ifc_original_units_sha256":file_hash(final_original_units),
                "developer_authored_not_llm":True,
                "full_45_native_expressivity_parity":False,
            })
    return {
        "status":"PUBLIC_HOSTED_V06_DEVELOPER_FIXED_D0_ONLY",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/126",
        "original_author_dataset_revision":"f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca",
        "original_author_source_revision":"667004e16bd38fd7d538bcee56191465429fd975",
        "new_model_calls":0,"paid_cost_usd":"0",
        "historical_luna45_scores_unchanged":True,
        "this_is_NOT_a_new_LLM_benchmark_score":True,
        "native_full45_equivalent_to_ifcopenshell_python":False,
        "tasks":results,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author-repo",type=Path,required=True)
    parser.add_argument("--dataset",type=Path,required=True)
    parser.add_argument("--output-json",type=Path,required=True)
    a=parser.parse_args()
    if a.output_json.exists() or a.output_json.is_symlink():
        parser.error("Refuse overwriting pinned D0 research output")
    r=fixed_d0(a.author_repo.resolve(strict=True),a.dataset.resolve(strict=True))
    a.output_json.parent.mkdir(exist_ok=True,parents=True)
    with a.output_json.open("xb") as file:
        file.write((json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf8"))
    print(json.dumps({
        "status":r["status"],"new_model_calls":r["new_model_calls"],
        "author_scores":{x["original_public_task_id"]:x["original_author_grade_after_d0"]
                         for x in r["tasks"]},
        "report_sha256":file_hash(a.output_json),
    },sort_keys=True))


if __name__=="__main__":
    main()
