"""Original public BIBIMBAP geometry_test_18/19 source-native Window D0.

NONBLINDED DEVELOPER-FIXED D0 ONLY. Original PUBLIC natural-language prompt
and actual original IFC Wall/Opening native geometry determine exact Window
selection; original author hidden target GUID list, scorer, private reference
IFC and previous score must NEVER be consulted until the *entire* developer-
authored complete declarative Window XML, source-normalized IFC candidate,
candidate SHA and independent true native IFC oracle are fixed.

Original author scorer is invoked only *after* physical IFC candidate is
frozen. Scores are diagnostic, not model success or causal XML-vs-Python
parity. If the score is low, do not reselect/develop after seeing score.
"""
from __future__ import annotations

from pathlib import Path
from hashlib import sha256
import argparse
import ast
import json
import math
import re
import tempfile

import ifcopenshell
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np
from lxml import etree

from src.runtime.experimental_v14_native_window_delete import (
    NS,native_full_window_state_v14,compile_native_hosted_windows_v14
)
from tools.oracle_bibimbap_v14_window_delete import (
    verify_source_native_window_delete,
)
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head

Q="{"+NS+"}"
PUBLIC_CASES=("geometry_test_18","geometry_test_19")
GUID_RE=re.compile(r'GlobalId\s*=\s*"([A-Za-z0-9_$]{22})"')
TOL=1e-5


def _wall_axis_native(wall):
    reps=wall.Representation.Representations if wall.Representation else []
    axes=[
        el for rep in reps if rep.RepresentationType=="Curve2D"
        for el in rep.Items if el.is_a("IfcPolyline") and len(el.Points)==2
    ]
    if len(axes)!=1:
        raise ValueError("Source original geometry does not have exactly one native line Wall axis")
    transform=np.asarray(
        ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement),
        dtype=float,
    )
    ends=[]
    for pt in axes[0].Points:
        if len(pt.Coordinates)!=2:
            raise ValueError("Original native Wall axis points not 2D")
        ends.append((transform@np.asarray(
            (float(pt.Coordinates[0]),float(pt.Coordinates[1]),0.,1.)
        ))[:3])
    p0,p1=np.asarray(ends)
    delta=p1-p0
    length=float(np.linalg.norm(delta))
    if length<=.5 or abs(delta[2])>TOL:
        raise ValueError("Original native Wall axis not horizontal/finite/usable")
    u=delta/length
    if not np.isfinite(u).all():
        raise ValueError("Original native Wall direction nonfinite")
    return p0,p1,u,length


def _source_filled_window_rows(model):
    result=[]
    ifc_windows=model.by_type("IfcWindow")
    for window in ifc_windows:
        fills=list(window.FillsVoids)
        if len(fills)!=1 or fills[0].RelatedBuildingElement!=window:
            raise ValueError("Original public source Window doesn't have unique original fill relation")
        opening=fills[0].RelatingOpeningElement
        voids=list(opening.VoidsElements)
        if len(voids)!=1 or voids[0].RelatedOpeningElement!=opening:
            raise ValueError("Original public Opening has ambiguous native host relation")
        wall=voids[0].RelatingBuildingElement
        p0,p1,u,length=_wall_axis_native(wall)
        native_open_position=np.asarray(
            ifcopenshell.util.placement.get_local_placement(
                opening.ObjectPlacement),dtype=float
        )[:3,3]
        width=float(window.OverallWidth)
        if width<=0 or width>length+1 or not np.isfinite(width):
            raise ValueError("Original public Window has unsupported native source opening width")
        result.append({
            "window_guid":window.GlobalId,
            "opening_guid":opening.GlobalId,
            "host_guid":wall.GlobalId,
            "axis_start_world_m":p0,
            "axis_end_world_m":p1,
            "axis_unit_world":u,
            "axis_length_m":length,
            "host_center_world_m":(p0+p1)/2,
            "opening_origin_world_m":native_open_position,
            "opening_width_from_source_IfcWindow_OverallWidth_m":width,
        })
    return sorted(result,key=lambda x:x["window_guid"])


def _source_only_selection(task:str,public_question:str,model):
    """Select by source Wall +X west or source opposite-wall overlap ONLY."""
    rows=_source_filled_window_rows(model)
    if task=="geometry_test_18":
        if not ("west" in public_question.lower() and
                "+X is east" in public_question):
            raise ValueError("Original public west Window task semantics changed")
        # Westmost ORIGINAL host Wall(s) with a N/S-directed native line.
        # West/East is world X, not local Revit screen orientation.
        westward_hosts={
            r["host_guid"]:r for r in rows
            if abs(r["axis_unit_world"][0])<TOL
            and abs(abs(r["axis_unit_world"][1])-1)<TOL
        }
        if not westward_hosts:
            raise ValueError("No source north/south oriented original west host Wall")
        min_x=min(float(r["host_center_world_m"][0])
                  for r in westward_hosts.values())
        west_guid={
            guid for guid,r in westward_hosts.items()
            if abs(float(r["host_center_world_m"][0])-min_x)<TOL
        }
        chosen=[
            r for r in rows if r["host_guid"] in west_guid
        ]
        if len(chosen)!=2 or len(west_guid)!=1:
            raise ValueError("Native source west-wall window selection is ambiguous")
        return tuple(r["window_guid"] for r in chosen),{
            "original_question_direction_semantics":
                "+X east, west is minimum original world X",
            "native_selection_only":"Original westmost north/south oriented Window host Wall",
            "selected_original_native_source_west_wall_guids":sorted(west_guid),
            "original_native_source_west_wall_center_x_m":round(min_x,6),
            "source_public_question_excludes_hidden_target":True,
            "developer_fixed_source_native_Window_Guids":
                [r["window_guid"] for r in chosen],
        }
    if task=="geometry_test_19":
        match=GUID_RE.findall(public_question)
        if len(match)!=1 or "opposite" not in public_question.lower():
            raise ValueError("Original public opposite wall reference ambiguously changed")
        ref_guid=match[0]
        try:
            ref=model.by_guid(ref_guid)
        except RuntimeError as exc:
            raise ValueError("Public original named Wall is missing source") from exc
        if not ref.is_a("IfcWall"):
            raise ValueError("Original named public reference is not an IfcWall")
        p0,p1,d,L=_wall_axis_native(ref)
        normal=np.array([-d[1],d[0],0.])
        midpoint=(p0+p1)/2
        candidates=[]
        for r in rows:
            u=r["axis_unit_world"]
            if abs(abs(float(np.dot(u,d)))-1)>TOL:
                continue  # Only parallel source native host Walls.
            wall_mid=r["host_center_world_m"]
            across=abs(float(np.dot(wall_mid-midpoint,normal)))
            if across<=1.:
                continue  # Coplanar or same wall is not "opposite".
            # Actual original Window native opening starts at its source
            # IfcLocalPlacement, follows the original hosting Wall axis,
            # and spans original native OverallWidth. No hidden GT IDs.
            o0=r["opening_origin_world_m"]
            o1=o0+u*r["opening_width_from_source_IfcWindow_OverallWidth_m"]
            a=float(np.dot(o0-p0,d))
            b=float(np.dot(o1-p0,d))
            lo,hi=sorted((a,b))
            overlap=max(0.,min(hi,L)-max(lo,0.))
            if overlap+TOL>=r["opening_width_from_source_IfcWindow_OverallWidth_m"]*.5:
                candidates.append({
                    "row":r,"normal_distance_m":across,
                    "overlap_on_public_named_wall_m":overlap,
                })
        selected_hosts={c["row"]["host_guid"] for c in candidates}
        if len(candidates)!=2 or len(selected_hosts)!=1:
            raise ValueError("Original native opposite parallel Wall window spans are ambiguous")
        chosen=tuple(sorted(c["row"]["window_guid"] for c in candidates))
        return chosen,{
            "public_original_named_reference_wall_guid":ref_guid,
            "source_original_named_reference_wall_axis_m":[
                [round(float(v),6) for v in p0],
                [round(float(v),6) for v in p1],
            ],
            "original_source_named_reference_wall_length_m":round(L,6),
            "developer_original_native_opposite_host_wall_guids":
                sorted(selected_hosts),
            "developer_original_opposite_wall_window_overlap_m":{
                c["row"]["window_guid"]:
                    round(c["overlap_on_public_named_wall_m"],6)
                for c in sorted(candidates,key=lambda c:c["row"]["window_guid"])
            },
            "source_public_question_excludes_hidden_target":True,
            "developer_fixed_source_native_Window_Guids":list(chosen),
        }
    raise ValueError("Unsupported original fixed D0 task")


def _edited_window_state(raw:bytes,selected:tuple[str,...])->bytes:
    root=etree.fromstring(raw)
    window_nodes=root.find(Q+"Windows")
    removed=[]
    for node in list(window_nodes):
        if node.get("ifcGuid") in selected:
            removed.append(node.get("ifcGuid"))
            window_nodes.remove(node)
    if tuple(sorted(removed))!=tuple(sorted(selected)):
        raise ValueError("Declarative v0.14 original source Window substate delete nodes mismatch")
    return etree.tostring(root,encoding="utf8")


def _diagnose_postfreeze_author_source_target_admission(
    author:Path,original_ifc:Path,tid:str,grade:dict
):
    """Inspect only STATIC PUBLIC AUTHOR TEST targets AFTER candidate freeze.

    Never pass those targets into the developer candidate selection or
    native compiler; never emit original author's potentially hidden GUIDs
    to the result. The original external scorer and IFC inputs remain
    absolutely untouched. This is forensic diagnosis of an unscoreable
    *pre-existing* dataset/author conflict, not alternate scoring.
    """
    script=author/"data"/"tests"/(tid+".py")
    if not script.is_file():
        raise ValueError("Pinned author test file missing post-freeze")
    tree=ast.parse(script.read_text(encoding="utf8"))
    matches=[]
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(
            isinstance(target,ast.Name) and target.id=="WINDOW_GUIDS"
            for target in node.targets
        ):
            matches.append(ast.literal_eval(node.value))
    if len(matches)!=1 or not isinstance(matches[0],list):
        raise ValueError("Author source's original fixed GUID declaration not unambiguous")
    declared=matches[0]
    if (not declared or len(set(declared))!=len(declared)
        or any(not isinstance(x,str) or len(x)!=22 for x in declared)):
        raise ValueError("Original static author Window GUID target declaration malformed")
    source=ifcopenshell.open(str(original_ifc))
    present=0
    missing=0
    for guid in declared:
        try:
            item=source.by_guid(guid)
        except RuntimeError:
            missing+=1
        else:
            if not item.is_a("IfcWindow"):
                raise ValueError("Original author test has non-Window target source GUID")
            present+=1
    if grade.get("status")=="AUTHOR_WORKER_FAILED":
        if grade.get("error_type")!="RuntimeError" or missing<1:
            raise ValueError("Original author failed for an unexplained reason")
        return {
            "status":"PINNED_ORIGINAL_AUTHOR_TARGET_NOT_IN_ORIGINAL_PUBLIC_IFC",
            "original_author_static_declared_target_count":len(declared),
            "original_author_targets_found_in_original_source":present,
            "original_author_targets_absent_from_original_source":missing,
            "original_author_target_GUID_values_excluded_from_report":True,
            "postfreeze_forensics_does_not_modify_candidate_or_score":True,
            "scorer_exception_class":grade["error_type"],
            "the_original_author_implementation_is_not_modified":True,
            "this_is_not_a_replacement_grade":True,
        }
    return {
        "status":"ORIGINAL_AUTHOR_WORKER_RETURNED_SCORE",
        "original_author_static_declared_target_count":len(declared),
        "original_author_targets_found_in_original_source":present,
        "original_author_targets_absent_from_original_source":missing,
        "original_author_target_GUID_values_excluded_from_report":True,
        "postfreeze_forensics_does_not_modify_candidate_or_score":True,
        "this_is_not_a_replacement_grade":True,
    }


def audit(author:Path,dataset:Path):
    if _head(author)!=AUTHOR_SHA or _head(dataset)!=DATA_SHA:
        raise ValueError("Original publicly pinned scorer/data SHA changed")
    tasks={row["test_id"]:row for row in public_45(author,dataset)}
    records=[]
    for taskid in PUBLIC_CASES:
        public=tasks[taskid]
        raw=dataset/"ifc"/public["original_source_ifc_relpath"]
        initial_sha=public["original_ifc_sha256"]
        if file_hash(raw)!=initial_sha:
            raise ValueError("Original public IFC file checksum differs from pinned 45 cohort")
        with tempfile.TemporaryDirectory(prefix="bibimbap142-v14-public-D0-") as td:
            p=Path(td)
            raw_model=ifcopenshell.open(str(raw))
            if raw_model.schema!="IFC4X3" or abs(
                ifcopenshell.util.unit.calculate_unit_scale(raw_model)-.001
            )>1e-12:
                raise ValueError("Original public IFC4X3 data is no longer original millimetres")
            source=p/"original_native_m_source.ifc"
            ifcopenshell.util.unit.convert_file_length_units(
                raw_model,"METER").write(str(source))
            f=ifcopenshell.open(str(source))
            selection,why=_source_only_selection(taskid,public["public_question"],f)
            if not selection:
                raise ValueError("Original public task did not select any Window")
            state=native_full_window_state_v14(source)
            xml=_edited_window_state(state.xml,selection)
            candidate=p/"source_native_deleted_windows_m.ifc"
            compiler=compile_native_hosted_windows_v14(source,xml,candidate)
            independent=verify_source_native_window_delete(
                source,candidate,selection,
                expected_original_source_sha256=compiler.source_sha256,
                expected_output_sha256=compiler.output_sha256)
            if independent["status"]!=(
                "INDEPENDENT_ORIGINAL_NATIVE_IFC4X3_WINDOW_ONLY_DELETE_ORACLE_PASS_V014"):
                raise ValueError("Developer candidate failed independent native source IFC oracle")
            original_mm=p/"candidate_native_original_mm.ifc"
            ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(candidate)),"MILLIMETER"
            ).write(str(original_mm))
            if ifcopenshell.open(str(original_mm)).schema!="IFC4X3":
                raise ValueError("Original native schema lost after score-unit conversion")
            # SOURCE ORIGINAL CANDIDATE FROZEN HERE.
            # Only after normalized XML state, native IFC SHA, full
            # independent physical oracle, and original-mm candidate SHA
            # are established may original author scorer be consulted.
            immutable_candidate_sha=file_hash(candidate)
            original_mm_sha=file_hash(original_mm)
            original_xml_sha=sha256(xml).hexdigest()
            from tools.bibimbap_matched25_cli import grade_author
            author_grade=grade_author(author,raw,original_mm,taskid)
            if (file_hash(candidate)!=immutable_candidate_sha
                or file_hash(original_mm)!=original_mm_sha
                or file_hash(raw)!=initial_sha):
                raise ValueError("Original author post-freeze score mutated IFC source/candidate")
            original_author_source_diagnostic=_diagnose_postfreeze_author_source_target_admission(
                author,raw,taskid,author_grade
            )
            if (file_hash(candidate)!=immutable_candidate_sha
                or file_hash(original_mm)!=original_mm_sha
                or file_hash(raw)!=initial_sha):
                raise ValueError("Post-freeze original author metadata forensics mutated IFC")
            records.append({
                "original_public_task_id":taskid,
                "original_public_question_sha256":public["public_question_sha256"],
                "original_public_ifc_sha256":initial_sha,
                "original_native_schema":"IFC4X3",
                "original_normalized_metres_source_sha256":file_hash(source),
                "original_declarative_full_Window_source_state_sha256":
                    sha256(state.xml).hexdigest(),
                "original_native_readonly_v13_catalog_sha256":
                    state.original_native_source_catalog_sha256,
                "developer_source_only_native_geometric_Window_selection":why,
                "developer_source_only_original_public_selected_window_guids":
                    list(selection),
                "developer_XML_whole_Window_inventory_after_deleting_nodes_sha256":
                    original_xml_sha,
                "original_native_candidate_sha256":immutable_candidate_sha,
                "original_originalunit_mm_candidate_sha256":original_mm_sha,
                "independent_original_native_ifc_oracle":independent,
                "original_author_score_AFTER_frozen_developer_D0":author_grade,
                "postfreeze_original_author_source_target_missing_diagnostic":
                    original_author_source_diagnostic,
                "original_author_score_influenced_candidate_generation":False,
                "original_hidden_author_target_used_for_selection":False,
                "developer_prompt_semantics_are_not_a_held_out_model_trial":True,
                "original_native_opening_and_host_geometry_preserved":True,
                "native_target_only_Window_delete_implemented":True,
                "original_semantic_full45_edit_parity_claim":False,
                "original_Python_matched_I0_baseline_run":False,
                "new_paid_model_calls":0,
            })
    return {
        "status":"ORIGINAL_BIBIMBAP_GEOMETRY18_19_WINDOW_SOURCE_ONLY_V014_D0_NOT_LLM",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/142",
        "original_author_revision":AUTHOR_SHA,
        "original_dataset_revision":DATA_SHA,
        "original_public_45_denominator_retained":45,
        "original_author_test_score_used_only_post_candidate_freeze":True,
        "original_hidden_target_reference_not_accessed_during_authoring":True,
        "source_original_native_window_only_deletion_not_opening_repair":True,
        "source_original_IFC4X3_geometry_test_18_19_original_frozen_D0_cases":
            records,
        "original_author_model_scores_not_new_LLM_scores":True,
        "original_Python_matched_I0_models_run":0,
        "real_matched_XML_Python_LLM_runs":0,
        "new_paid_model_calls":0,
        "new_paid_cost_usd":"0",
        "original_GPT6_Luna_real45_scores_unchanged":True,
        "old_D0_research_evidence_unchanged":True,
        "true_semantic_write_parity_45_not_proven":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--author-repo",type=Path,required=True)
    p.add_argument("--dataset",type=Path,required=True)
    p.add_argument("--output-json",type=Path,required=True)
    args=p.parse_args()
    if args.output_json.exists() or args.output_json.is_symlink():
        p.error("Refusing to overwrite v0.14/previous original D0 evidence")
    result=audit(args.author_repo.resolve(strict=True),
                 args.dataset.resolve(strict=True))
    payload=(json.dumps(result,sort_keys=True,indent=2,
                        ensure_ascii=False)+"\n").encode("utf8")
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    with args.output_json.open("xb") as f:
        f.write(payload)
    print(json.dumps({
        "status":result["status"],
        "original_public_D0_scores":{
            c["original_public_task_id"]:
                c["original_author_score_AFTER_frozen_developer_D0"]
            for c in result["source_original_IFC4X3_geometry_test_18_19_original_frozen_D0_cases"]
        },
        "original_public_developer_selected_Window_counts":{
            c["original_public_task_id"]:
                len(c["developer_source_only_original_public_selected_window_guids"])
            for c in result["source_original_IFC4X3_geometry_test_18_19_original_frozen_D0_cases"]
        },
        "report_sha256":file_hash(args.output_json),
        "new_model_calls":0,
    },sort_keys=True))


if __name__=="__main__":
    main()
