"""v0.62 evaluator-only 8 original Wall/center-preserving shortened native D/I.

Actual D_FULL, D_MANAGED, real pinned Linux Docker Python edits of the
original SHA-pinned IFC4X3 source. Developer controls: true centered 1m
shortening and false centered .5m and 1.5m shortenings. Original author
repository scorer runs ONLY in this evaluator-only audit, never model tool
or Docker worker. Source-native gate is a strict original-source-specific
representation subset, NOT an official scorer or causal model result.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import importlib
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory

import ifcopenshell
from lxml import etree

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v057_provenance import (
    assert_original_source_rights_unchanged_v057,
)
from tools.bibimbap_v062_topology12_native import (
    TASK,SOURCE_SHA,_source,_mesh_bounds,
    original_wall_axis_length_m_v062,isolated_original_swept_wall_v062,
    full_source_state_v062,compact_complete_state_v062,
    independent_wall_native_scope_v062,canonical_native_semantic_digest_v062,
)
from tools.bibimbap_v062_topology12_sessions import (
    DirectFullState062,DirectManagedState062,LiveDockerPython062,
)


ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v062_original8wall_centered_shortening_native_DI_20261118.json"
PARENT=ROOT/"reports"/"bibimbap_v061_window_opening_proxy_native_DI_20261118.json"
PARENT_SHA="a620f6a6ac6ed164d1bbf0eec56ca84d117233fcefa0303d8d732c0a648314c3"
PARENT_HEAD="fb59e9e113a0e0f0709e8d2ede8569f023e243b3"
FROZEN=ROOT/"reports"/"bibimbap_v058_original45_capability_prospective_holdout_20261118.json"
FROZEN_SHA="0d8e7ca07a08af0afa3a08c10de5a76427e179d41cd1ca9b9df508f40fcc96c8"
FIXED_SIX=[
    "geometry_test_03","geometry_test_13","geometry_test_19",
    "topological_test_05","topological_test_12","topological_test_18",
]
SUPPORTED={"geometry_test_13","geometry_test_19",
           "topological_test_12","topological_test_18"}


def need(ok:bool,reason:str):
    if not ok:
        raise AssertionError(reason)


def canonical(obj:dict)->bytes:
    return (json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)
            +"\n").encode("utf8")


def public_source_exterior_wall_and_question_predicate_v062(
    source:Path,question:str,
)->dict:
    """PUBLIC original question only; no original author GT/scorer.

    Six original Wall GUIDs describe original connected exterior loop,
    while the eligible original SweptSolid standalone wall (no path edges)
    is one of two omitted original walls. The other omitted original wall
    has a path connection. A valid source-public wall shortening should
    retain original world center and shorten physical long dimension 1m.
    """
    original=_source(source,source_sha=SOURCE_SHA)
    mentioned=set(re.findall(r"[0-9A-Za-z_$]{22}",question))
    need(len(mentioned)==6
         and all(original.by_guid(g).is_a("IfcWall") for g in mentioned)
         and "shorten" in question.lower()
         and "1m" in question.lower(),
         "Original public question's six wall identities/1m task drift")
    walls={w.GlobalId:w for w in original.by_type("IfcWall")}
    not_named=set(walls)-mentioned
    need(len(not_named)==2,"Original six-wall exclusion target ambiguous")
    isolated=isolated_original_swept_wall_v062(original)[0]
    need(isolated.GlobalId in not_named,
         "Native source eligibility contradicted public exterior exclusion")
    connected_unlisted=[
        w for guid,w in walls.items()
        if guid in not_named and guid!=isolated.GlobalId
        and any(x.is_a("IfcRelConnectsPathElements")
                for x in original.get_inverse(w))
    ]
    need(len(connected_unlisted)==1,
         "Other unlisted Wall must be source-connected interior Wall")
    bounds=_mesh_bounds(isolated)
    need(abs((bounds[1][1]-bounds[1][0])-2.)<.0001
         and .19<=(bounds[0][1]-bounds[0][0])<=.21
         and abs(bounds[2][1]-2.7)<.00001,
         "Real original external standalone Wall source bbox changed")
    return {
        "public_original_question_named_outer_wall_count":6,
        "source_original_wall_count":8,
        "outside_original_named_six_wall_count":2,
        "one_omitted_original_wall_is_connected_to_six":True,
        "one_omitted_original_wall_is_standalone_SweptSolid":True,
        "source_original_standalone_wall_length_m":2.0,
        "source_physical_correct_shortening_m":1.0,
        "source_center_should_be_preserved_in_this_developer_policy":True,
    }


def _full_final(initial:bytes,wall_guid:str,length_m:float)->str:
    doc=etree.fromstring(initial)
    found=False
    for row in doc[1]:
        if row.get("ifcGuid")==wall_guid:
            row.set("finalAxisLengthM",f"{length_m:.6f}")
            found=True
    need(found,"Original one eligible Wall missing in full final state")
    return etree.tostring(doc,encoding="utf8",xml_declaration=True).decode()


def _managed_final(initial:bytes,wall_guid:str,length_m:float)->str:
    doc=etree.fromstring(initial)
    found=False
    for row in doc:
        if row.get("ifcGuid")==wall_guid:
            row.set("finalAxisLengthM",f"{length_m:.6f}")
            found=True
    need(found,"Original one eligible Wall missing in managed final state")
    return etree.tostring(doc,encoding="utf8",xml_declaration=True).decode()


def _developer_actual_python_code(length_m:float)->str:
    """Source-only original topology and physical profile edit; no target GUID.

    This executes unmodified general Python/IfcOpenShell inside genuine
    pinned Linux Docker, not a typed AST or hidden answer.
    """
    need(length_m in (1.,.5,1.5),"Only three original-source developer controls")
    mm=int(round(length_m*1000))
    return (
        "wall=next(w for w in ifc.by_type('IfcWall') "
        "if any(rep.RepresentationIdentifier=='Body' "
        "and rep.Items[0].is_a('IfcExtrudedAreaSolid') "
        "for rep in w.Representation.Representations))\n"
        "axis=next(rep.Items[0] for rep in wall.Representation.Representations "
        "if rep.RepresentationIdentifier=='Axis')\n"
        "body=next(rep.Items[0] for rep in wall.Representation.Representations "
        "if rep.RepresentationIdentifier=='Body')\n"
        "profile=body.SweptArea\n"
        "center=float(profile.Position.Location.Coordinates[0])\n"
        "original_end_point=axis.Points[1]\n"
        f"new_native_length_mm={mm}\n"
        "start=ifc.create_entity('IfcCartesianPoint',"
        "Coordinates=(center-new_native_length_mm/2,0.))\n"
        "axis.Points=(start,original_end_point)\n"
        "original_end_point.Coordinates=(center+new_native_length_mm/2,0.)\n"
        "profile.XDim=float(new_native_length_mm)\n"
        "result={'final_wall_length_mm':new_native_length_mm}\n"
        "commit()\n"
    )


def original_author_repo_only(source:Path,candidate:Path)->dict:
    """Unmodified scorer is evaluator-side only; never model-facing."""
    sys.path.insert(0,str(AUTHOR))
    try:
        module=importlib.import_module("data.tests.topological_test_12")
        need(Path(module.__file__).resolve()==
             (AUTHOR/"data"/"tests"/"topological_test_12.py").resolve(),
             "Unexpected original author scorer module provenance")
        try:
            metrics=module.execute_test(str(source),str(candidate),None)
        except Exception as exc:
            return {
                "status":"BLOCKED_ORIGINAL_AUTHOR_EVALUATOR_EXCEPTION",
                "original_author_evaluator_exception_type":type(exc).__name__,
                "original_author_evaluator_message_redacted":True,
                "author_repository_mean_boolean_score":None,
                "author_repository_boolean_metrics":None,
                "official_published_paper_scorer_version_verified":False,
            }
        need(isinstance(metrics,dict) and metrics
             and all(type(v) is bool for v in metrics.values()),
             "Original repo grader returned nonbool or empty metrics")
        return {
            "status":"EVALUATOR_RETURNED_BOOLEAN_METRICS",
            "author_repository_mean_boolean_score":
                round(sum(metrics.values())/len(metrics),6),
            "author_repository_boolean_metrics":dict(sorted(metrics.items())),
            "official_published_paper_scorer_version_verified":False,
        }
    finally:
        sys.path.remove(str(AUTHOR))


def build_report()->dict:
    need(file_hash(PARENT)==PARENT_SHA
         and file_hash(FROZEN)==FROZEN_SHA,
         "Prior frozen original D/I reports changed")
    previous=json.loads(PARENT.read_text(encoding="utf8"))
    holdout=json.loads(FROZEN.read_text(encoding="utf8"))
    need(previous["new_original_native_task_supported_in_v061"]==
             ["geometry_test_13"]
         and previous["actual_LLM_generated_trial_count"]==0
         and sorted(holdout["prospective_six_source_heldout_task_ids"])==
             FIXED_SIX,
         "Frozen original public source/task selection or prior results drift")
    rights=assert_original_source_rights_unchanged_v057()
    need(rights["status"]=="BLOCKED_NO_MODEL_PROVIDER_TRIAL",
         "Paid/provider original data consent gate unexpectedly changed")
    registry={r["test_id"]:r for r in public_45(AUTHOR,DATA)}
    need(len(registry)==45
         and len({r["original_ifc_sha256"] for r in registry.values()})==31,
         "Original 45 task/31 source IFC population drifted")
    row=registry[TASK]
    original=DATA/"ifc"/row["original_source_ifc_relpath"]
    need(file_hash(original)==SOURCE_SHA
         and row["original_ifc_sha256"]==SOURCE_SHA,
         "Original source wall IFC4X3 SHA drift")
    f=_source(original,source_sha=SOURCE_SHA)
    wall=isolated_original_swept_wall_v062(f)[0]
    srcphysical=public_source_exterior_wall_and_question_predicate_v062(
        original,row["public_question"])
    source_xml=full_source_state_v062(original,source_sha=SOURCE_SHA)
    managed=compact_complete_state_v062(original,source_sha=SOURCE_SHA)
    cases=[
        ("PUBLIC_SOURCE_PHYSICAL_CENTERED_SHORTEN_1M_CORRECT",1.),
        ("PUBLIC_SOURCE_PHYSICAL_CENTERED_SHORTEN_0_5M_WRONG",1.5),
        ("PUBLIC_SOURCE_PHYSICAL_CENTERED_SHORTEN_1_5M_WRONG",.5),
    ]
    outcomes=[]
    with TemporaryDirectory(prefix="v062-ORIGINAL-ACTUAL-LINUX-DOCKER-WALL-") as tmp:
        folder=Path(tmp)
        for j,(label,length) in enumerate(cases):
            case=folder/f"developer_case_{j}"
            D=DirectFullState062(original,case/"D")
            M=DirectManagedState062(original,case/"M")
            I=LiveDockerPython062(original,case/"I")
            reads=[s.call("read_building_xml",{"query":"source"})
                   for s in (D,M,I)]
            need(all(r["status"]=="ok" for r in reads)
                 and all(r["xml"]==reads[0]["xml"] for r in reads)
                 and reads[0]["xml"].encode("utf8")==source_xml,
                 "D_FULL, D_MANAGED, Docker I original input read not identical")
            full=_full_final(source_xml,wall.GlobalId,length)
            compact=_managed_final(managed,wall.GlobalId,length)
            code=_developer_actual_python_code(length)
            d=D.call("submit_building_xml",{"xml_text":full})
            m=M.call("submit_managed_final_state",{"xml_text":compact})
            i=I.call("execute_ifc_code",{"code":code})
            need(d["status"]==m["status"]==i["status"]=="ok"
                 and i["real_pinned_Docker_python_executed"] is True
                 and i["actual_linux_sandbox_backend"]=="linux_docker_sandbox"
                 and D.current_xml==M.current_xml==full.encode("utf8"),
                 "Actual original IFC D/I original source wall edit failed")
            outcomes_native=[]
            for arm in (D,M,I):
                result=independent_wall_native_scope_v062(
                    original,arm.output_ifc,source_sha=SOURCE_SHA)
                need(result["status"]==
                     "V062_ORIGINAL_ONE_UNCONNECTED_WALL_SHORTENED_NATIVE_SCOPE_SCHEMA_PASS"
                     and result["original_external_wall_world_center_preserved"]
                     and result["introduced_original_IFC_schema_error_count"]==0
                     and abs(result["final_swept_solid_wall_length_m"]-length)<=.000001,
                     "Original native physical 8-Wall source scope/schema failed")
                outcomes_native.append(
                    canonical_native_semantic_digest_v062(arm.output_ifc))
            need(outcomes_native[0]==outcomes_native[1]==outcomes_native[2],
                 "Native source D_FULL/MANAGED/real Docker I semantic IFC mismatch")
            grades={
                "D_FULL":original_author_repo_only(original,D.output_ifc),
                "D_MANAGED":original_author_repo_only(original,M.output_ifc),
                "I_REAL_DOCKER":original_author_repo_only(original,I.output_ifc),
            }
            need(grades["D_FULL"]==grades["D_MANAGED"]==
                 grades["I_REAL_DOCKER"],
                 "Original author scorer outcomes differ across valid D/I native IFC")
            outcomes.append({
                "developer_source_only_public_physical_label":label,
                "original_author_target_wall_GUID_redacted":True,
                "developer_generated_Python_source_code_redacted":True,
                "final_native_original_Wall_length_metres":length,
                "actual_center_preserving_native_physical_shortening_m":round(
                    2.-length,6),
                "D_full_complete_final_XML_UTF8_bytes":len(full.encode("utf8")),
                "D_managed_complete_final_XML_UTF8_bytes":len(compact.encode("utf8")),
                "I_developer_only_native_Python_UTF8_bytes":len(code.encode("utf8")),
                "all_three_original_native_IFC_canonical_semantic_SHA256":
                    outcomes_native[0],
                "native_original_source_IFC_schema_new_findings":0,
                "source_scope_D_full_managed_Docker_I_all_PASS":True,
                "original_author_repository_evaluator_side_only":grades["D_FULL"],
                "actual_genuine_isolated_linux_Docker_Python_executed":True,
                "model_generated_answer":False,
            })
            need(file_hash(original)==SOURCE_SHA,
                 "Original source modified by a developer trial")
        # Independent actual Docker malformed edit: shorten Axis but do
        # NOT alter native profile nor detach source SHARED axis start.
        raw=LiveDockerPython062(original,folder/"RAW_AXIS_ONLY")
        bad=raw.call("execute_ifc_code",{"code":(
            "wall=next(w for w in ifc.by_type('IfcWall') "
            "if any(rep.RepresentationIdentifier=='Body' "
            "and rep.Items[0].is_a('IfcExtrudedAreaSolid') "
            "for rep in w.Representation.Representations))\n"
            "axis=next(rep.Items[0] for rep in "
            "wall.Representation.Representations "
            "if rep.RepresentationIdentifier=='Axis')\n"
            "axis.Points[1].Coordinates=(1000.,0.)\n"
            "result={'axis_only_invalid':True}\n"
            "commit()\n"
        )})
        need(bad["status"]=="error"
             and bad["native_ifc_committed"] is False
             and raw.output_ifc is None,
             "Actual Docker Axis-only wall edit improperly promoted")
        # Genuine Docker valid 1m -> attempt corrupt unrelated Wall after
        # native commit: MUST preserve previous real IFC SHA byte-identical.
        chain=LiveDockerPython062(original,folder/"VALID_THEN_INVALID")
        first=chain.call("execute_ifc_code",{
            "code":_developer_actual_python_code(1.)})
        need(first["status"]=="ok" and chain.output_ifc is not None,
             "Actual Linux Docker source wall first edit failed")
        prior_native_SHA=file_hash(chain.output_ifc)
        second=chain.call("execute_ifc_code",{"code":(
            "wall=next(w for w in ifc.by_type('IfcWall') "
            "if any(rep.RepresentationIdentifier=='Body' "
            "and rep.Items[0].is_a('IfcBooleanClippingResult') "
            "for rep in w.Representation.Representations))\n"
            "wall.Name='OFF_TARGET_WALL_CORRUPTED'\n"
            "commit()\n"
        )})
        need(second["status"]=="error"
             and second["native_ifc_committed"] is False
             and file_hash(chain.output_ifc)==prior_native_SHA,
             "Actual Docker off-target changed previously valid IFC")
        # Complete declarative D after valid final: delete a managed Wall
        # from document: reject WITHOUT changing prior native IFC or XML.
        D=DirectFullState062(original,folder/"GOOD_D_BAD_COMPLETE_ROSTER")
        first_D=D.call("submit_building_xml",{
            "xml_text":_full_final(source_xml,wall.GlobalId,1.)})
        need(first_D["status"]=="ok","Baseline original full D failed")
        priorXML=D.current_xml
        priorSHA=file_hash(D.output_ifc)
        root=etree.fromstring(priorXML)
        root[1].remove(root[1][0])
        rejected=D.call("submit_building_xml",{
            "xml_text":etree.tostring(root,encoding="utf8").decode("utf8")})
        need(rejected["status"]=="error"
             and file_hash(D.output_ifc)==priorSHA
             and D.current_xml==priorXML,
             "Bad complete source Wall roster lost last valid D native IFC")
    need(file_hash(original)==SOURCE_SHA
         and len(outcomes)==3
         and len({x["developer_source_only_public_physical_label"]
                  for x in outcomes})==3
         and all(x["actual_genuine_isolated_linux_Docker_Python_executed"]
                 for x in outcomes),
         "Three actual original source wall D/I developer controls missing")
    return {
        "status":"V062_ORIGINAL_WALL_AXIS_RECT_PROFILE_CENTERED_SHORTENED_D_FULL_MANAGED_REAL_DOCKER_I_PASS",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/239",
        "parent_v061_exact_HEAD":PARENT_HEAD,
        "parent_v061_frozen_report_SHA256":PARENT_SHA,
        "frozen_original_v058_six_source_selection_SHA256":FROZEN_SHA,
        "original_45_public_task_population":45,
        "original_31_unique_source_IFC_population":31,
        "original_six_preselected_source_tasks_unchanged":FIXED_SIX,
        "v062_new_original_native_task_supported":[TASK],
        "current_four_of_six_original_source_task_specific_native_developer_supported":
            sorted(SUPPORTED),
        "remaining_two_original_fixed_tasks_not_yet_native_eligible":
            sorted(set(FIXED_SIX)-SUPPORTED),
        "total_original_45_task_specific_native_developer_controls_supported":8,
        "remaining_original_45_public_tasks_without_native_developer_control":37,
        "original_public_IFC_source_SHA256":SOURCE_SHA,
        "original_IFC_source_schema":"IFC4X3",
        "original_public_question_SHA256":row["public_question_sha256"],
        "original_author_repo_evaluator_file_SHA256":
            file_hash(AUTHOR/"data"/"tests"/f"{TASK}.py"),
        "original_source_public_six_wall_exclusion_and_physical_predicate":
            srcphysical,
        "original_wall_count":8,
        "original_wall_path_connections_preserved":7,
        "source_single_native_SweptSolid_standalone_wall_m":2.0,
        "source_other_seven_clipped_connected_walls_not_general_editable":True,
        "source_native_axis_start_shared_with_other_entities":True,
        "one_new_independent_native_IfcCartesianPoint_instead_of_shared_source_mutation":True,
        "actual_wall_center_preserved_in_native_World_Metre_geometry":True,
        "native_source_millimetres_vs_world_geometry_metres":True,
        "all_three_arms_identical_initial_original_source_XML_bytes":
            len(source_xml),
        "original_complete_managed_eight_wall_initial_UTF8_bytes":len(managed),
        "original_source_wall_managed_roster_complete_eight":True,
        "real_native_D_full_source_IFC_developer_cases":3,
        "real_native_D_complete_managed_source_IFC_developer_cases":3,
        "real_native_pinned_Linux_Docker_I_developer_cases":3,
        "total_native_original_source_IFC_edits_admitted":9,
        "original_IFC_new_schema_findings":0,
        "all_three_D_I_semantic_digest_per_case_equal":True,
        "original_author_scorer_evaluator_only_D_I_grades_agree":True,
        "actual_genuine_Docker_axis_only_native_invalid_rejected":True,
        "actual_genuine_Docker_good_then_offtarget_last_IFC_preserved":True,
        "full_D_good_then_incomplete_roster_last_XML_and_IFC_preserved":True,
        "centered_versus_start_anchored_development_evaluator_exposure":True,
        "initial_developer_trial_start_anchored_shortening_author_grade_two_thirds":True,
        "centered_source_wall_target_author_repo_score_one_for_true_1m":True,
        "strict_source_STEP_representation_may_bias_general_Python_I":True,
        "original_six_candidate_sources_no_longer_fully_developer_blind":True,
        "original_IFC_provider_uploads":0,
        "actual_LLM_generated_model_trials":0,
        "paid_provider_model_calls":0,
        "published_paper_official_scorer_equivalence_verified":False,
        "original_ifc_underlying_rights_and_provider_transfer_consent_verified":False,
        "approved_paid_provider_model_snapshot_budget":None,
        "original_paper_official_LLM_score":None,
        "three_original_source_centered_Wall_developer_control_results":outcomes,
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    z=p.add_mutually_exclusive_group(required=True)
    z.add_argument("--write",action="store_true")
    z.add_argument("--check",action="store_true")
    args=p.parse_args()
    report=canonical(build_report())
    if args.write:
        with REPORT.open("xb") as f:
            f.write(report)
    else:
        need(REPORT.is_file() and not REPORT.is_symlink()
             and REPORT.read_bytes()==report,
             "Frozen v0.62 real original IFC D/I Docker report replay not byte-identical")
    print("V062_ORIGINAL_WALL_CENTERED_SHORTENED_NATIVE_D_I=PASS "
          "ACTUAL_IFC=9/9 ACTUAL_PINNED_LINUX_DOCKER=3/3 "
          "MODEL=0 PAID=0 FROZEN_SHA256="+sha256(report).hexdigest())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
