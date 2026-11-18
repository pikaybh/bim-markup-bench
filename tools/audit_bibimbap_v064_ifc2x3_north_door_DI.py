"""Evaluator-only true original IFC2X3 nearest-positive-Y Door D/I audit.

Original public source 01/01/01_01_003.ifc: exactly 3 original Walls.
Use actual general IfcOpenShell Python in pinned local Linux Docker (not
a simulated executor) and full/managed declarative final states on the
same original IFC2X3. Score original AUTHOR repository in this audit only,
and independently evaluate actual public nearest-positive-Y wall and
door/ground/relation/CSG validity. Never pass private original evaluator
answer/target to source-only model-facing code.

No paid provider call, no original IFC upload, no model-generated trial.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import importlib
import json
import math
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
import uuid

import ifcopenshell
from lxml import etree

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v057_provenance import (
    assert_original_source_rights_unchanged_v057,
)
from tools import audit_bibimbap_v063_original_exterior_door_DI as v063_audit
from tools.bibimbap_v064_ifc2x3_north_door_native import (
    TASK,SOURCE_SHA,STATUS,
    source_original_ifc2x3,full_original_state_v064,
    managed_original_state_v064,
    source_native_ifc2x3_scope_v064,
    canonical_semantic_digest_v064,
    original_3wall_public_source_bboxes_v064,
)
from tools.bibimbap_v064_ifc2x3_north_door_sessions import (
    DirectFullState064,DirectManagedState064,LiveDockerPython064,
)

BASE=Path(r"D:\문서\D__1_Projects\202611")
ROOT=Path(__file__).resolve().parents[1]
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v064_original_ifc2x3_north_door_native_DI_20261118.json"
PARENT=ROOT/"reports"/"bibimbap_v063_original_external_door_csg_native_DI_20261118.json"
PARENT_SHA="77ea754501be7142319b425d31f17fd60b1ade9addb724ace4ecf7b70aba2437"
PARENT_HEAD="d4038c3ea1cc73bc6228dae0bab430c89a34f8a2"
FROZEN=ROOT/"reports"/"bibimbap_v058_original45_capability_prospective_holdout_20261118.json"
FROZEN_SHA="0d8e7ca07a08af0afa3a08c10de5a76427e179d41cd1ca9b9df508f40fcc96c8"
FIXED_SIX=[
    "geometry_test_03","geometry_test_13","geometry_test_19",
    "topological_test_05","topological_test_12","topological_test_18",
]


def need(ok,why):
    if not ok:raise AssertionError(why)


def canonical(report):
    return (json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)
            +"\n").encode("utf8")


def source_public_north_wall_v064(model,question:str):
    """Original PUBLIC question semantics only, evaluator-side.

    The question itself names source reference Wall GUID. The nearest
    positive-Y alternative among the other original source Wall centres
    is required, not the northernmost/farthest of the three.
    """
    need(question.startswith("Add a door to the wall that is north (+Y direction)")
         and "GlobalId" in question,
         "Original public nearest-north question changed")
    guids=re.findall(r"[0-9A-Za-z_$]{22}",question)
    need(len(guids)==1,"Public IFC source reference Wall ID count changed")
    ref=model.by_guid(guids[0])
    need(ref is not None and ref.is_a("IfcWall"),
         "Original public reference Wall missing")
    wall_rows=original_3wall_public_source_bboxes_v064(model)
    bb_ref=next(bb for w,bb in wall_rows if w.GlobalId==ref.GlobalId)
    cy=(bb_ref[1][0]+bb_ref[1][1])/2
    candidates=[]
    for wall,box in wall_rows:
        center=(box[1][0]+box[1][1])/2
        if center>cy+.001:
            candidates.append((center-cy,wall))
    need(len(candidates)==2,"Original three-Wall north relation changed")
    candidates.sort(key=lambda item:item[0])
    nearest=candidates[0][1]
    far=candidates[1][1]
    return nearest,far,ref


def _new_guid(case:str,kind:str):
    return ifcopenshell.guid.compress(
        uuid.uuid5(uuid.NAMESPACE_DNS,
                   "v064-original-ifc2x3-source-only-"+case+"-"+kind).hex)


def native_source_developer_fixture_v064(case_name,host,width,height):
    """Engineer-authored public original source fixture; no hidden GT."""
    need(width in (.9,.4) and height in (2.1,1.2),
         "Only source-developer controls, no model attempts")
    cy=host.ObjectPlacement.RelativePlacement.Location.Coordinates[1]/1000.
    ymin=round(cy-.1,6)
    opening_width=round(width+.05,6)
    return {
        "host_guid":host.GlobalId,
        "opening_guid":_new_guid(case_name,"OPENING"),
        "door_guid":_new_guid(case_name,"DOOR"),
        "axis":"X",
        "opening_bbox":(
            -opening_width/2,opening_width/2,
            ymin-.1,ymin+.3,0.,height+.1,
        ),
        "door_bbox":(
            -width/2,width/2,
            ymin+.075,ymin+.120,0.,height,
        ),
    }


def _populate(initial:bytes,state,*,managed=False):
    return v063_audit._populate_xml(initial,state,managed=managed)


def _independent_live_python_code_v064(state,source_index,
                                      *,omit_filling=False):
    """Actually execute arbitrary native Python/IfcOpenShell in Docker.

    Underlying actual original IFC2X3 requirement: all newly created
    IfcRel roots get valid mandatory OwnerHistory from their source host.
    No model-facing source caller ever imports this evaluator/audit.
    """
    code=v063_audit._developer_real_python_code(
        state,source_index,omit_filling=omit_filling)
    need(code.endswith("commit()\n"),"Original general Python boilerplate drift")
    return (
        code[:-len("commit()\n")]
        + "for element in ifc.by_type('IfcRoot'):\n"
          "    if element.OwnerHistory is None:\n"
          "        element.OwnerHistory=host.OwnerHistory\n"
          "result['original_schema']='IFC2X3'\n"
          "commit()\n"
    )


def public_nearest_north_physical_v064(original:Path,candidate:Path,
                                      question:str)->dict:
    native=source_native_ifc2x3_scope_v064(
        original,candidate,source_sha=SOURCE_SHA)
    f=source_original_ifc2x3(original,source_sha=SOURCE_SHA)
    near,far,ref=source_public_north_wall_v064(f,question)
    correct=native["native_one_door_host_source_original_guid"]==near.GlobalId
    door_bbox=native["native_door_bbox_m"]
    width=native["door_world_width_m"]
    height=native["door_world_height_m"]
    ground=abs(door_bbox[2][0])<=.01
    plausible=.6<=width<=1.5 and 1.5<=height<=3.
    return {
        "status":"V064_EVALUATOR_ONLY_PUBLIC_NEAREST_POSITIVE_Y_PHYSICAL_PREDICATE",
        "exactly_three_source_Walls":True,
        "two_source_walls_positive_Y_of_public_reference":True,
        "candidate_host_is_nearest_positive_Y_wall":bool(correct),
        "candidate_host_is_farther_positive_Y_wall":bool(
            native["native_one_door_host_source_original_guid"]==far.GlobalId),
        "candidate_actual_Door_ground_Z_equals_zero":bool(ground),
        "candidate_Door_reasonable_dims":bool(plausible),
        "actual_full_thickness_host_Wall_CSG_cut":True,
        "public_original_question_physical_correct":bool(correct and plausible and ground),
        "original_author_scorer_imported_into_model_host":False,
    }


def original_author_repo_evaluator_only_v064(source,candidate):
    sys.path.insert(0,str(AUTHOR))
    try:
        scorer=importlib.import_module("data.tests.geometry_test_03")
        need(Path(scorer.__file__).resolve()==
             (AUTHOR/"data"/"tests"/"geometry_test_03.py").resolve(),
             "Original author pinned scorer source mismatch")
        try:
            metrics=scorer.execute_test(str(source),str(candidate),None)
        except Exception as exc:
            return {
                "status":"ORIGINAL_REPOSITORY_GRADER_EXCEPTION",
                "exception_type":type(exc).__name__,
                "exception_message_redacted":True,
                "author_repo_mean":None,
                "author_repo_numeric_boolean_and_float_metrics":None,
                "official_paper_scorer_equivalence_proven":False,
            }
        need(isinstance(metrics,dict)
             and set(metrics)=={
                 "object_exists","right_dimensions",
                 "right_location","integrity_constraint"}
             and all(isinstance(v,(bool,int,float))
                     and math.isfinite(float(v))
                     and 0<=float(v)<=1
                     for v in metrics.values()),
             "Original pinned IFC2X3 author grader mixed metrics changed")
        return {
            "status":"UNMODIFIED_ORIGINAL_AUTHOR_REPOSITORY_EVALUATOR",
            "author_repo_mean":round(sum(float(v) for v in metrics.values())/4,6),
            "author_repo_numeric_boolean_and_float_metrics":
                dict(sorted(metrics.items())),
            "official_paper_scorer_equivalence_proven":False,
        }
    finally:
        sys.path.remove(str(AUTHOR))


def build_report():
    need(file_hash(PARENT)==PARENT_SHA and file_hash(FROZEN)==FROZEN_SHA,
         "Prior original source report SHA unexpectedly changed")
    prev=json.loads(PARENT.read_text(encoding="utf8"))
    frozen=json.loads(FROZEN.read_text(encoding="utf8"))
    need(prev["new_native_original_task_admitted_v063"]==["topological_test_05"]
         and prev["actual_model_generated_trials"]==0
         and sorted(frozen["prospective_six_source_heldout_task_ids"])==FIXED_SIX,
         "Original fixed six public sources or v0.63 checkpoint drifted")
    rights=assert_original_source_rights_unchanged_v057()
    need(rights["status"]=="BLOCKED_NO_MODEL_PROVIDER_TRIAL",
         "Original IFC rights and paid model launcher unexpectedly enabled")
    all_tasks={r["test_id"]:r for r in public_45(AUTHOR,DATA)}
    need(len(all_tasks)==45
         and len({r["original_ifc_sha256"] for r in all_tasks.values()})==31,
         "Original public 45 tasks or 31 original IFC source hashes drifted")
    task=all_tasks[TASK]
    original=DATA/"ifc"/task["original_source_ifc_relpath"]
    need(task["original_ifc_sha256"]==SOURCE_SHA
         and file_hash(original)==SOURCE_SHA,
         "Original publicly named IFC2X3 file hash mismatch")
    source=source_original_ifc2x3(original,source_sha=SOURCE_SHA)
    near,far,ref=source_public_north_wall_v064(
        source,task["public_question"])
    walls=sorted(source.by_type("IfcWall"),key=lambda w:w.GlobalId)
    sourceXML=full_original_state_v064(original,source_sha=SOURCE_SHA)
    managedXML=managed_original_state_v064(original,source_sha=SOURCE_SHA)
    cases=[
        ("PUBLIC_NEAREST_NORTH_WALL_GROUND_VALID",near,.9,2.1,True),
        ("PUBLIC_FARTHER_NORTH_WALL_SEMANTICALLY_WRONG",far,.9,2.1,False),
        ("PUBLIC_NEAREST_NORTH_DOOR_TOO_SMALL",near,.4,1.2,False),
    ]
    outcomes=[]
    with TemporaryDirectory(prefix="v064-original-ifc2x3-repro-docker-") as temp:
        tmp=Path(temp)
        for i,(name,host,width,height,expected_public) in enumerate(cases):
            idx=walls.index(host)
            state=native_source_developer_fixture_v064(name,host,width,height)
            D=DirectFullState064(original,tmp/f"case{i}"/"D")
            M=DirectManagedState064(original,tmp/f"case{i}"/"M")
            I=LiveDockerPython064(original,tmp/f"case{i}"/"I")
            readings=[
                session.call("read_building_xml",{"query":"source"})
                for session in (D,M,I)
            ]
            need(all(x["status"]=="ok" for x in readings)
                 and all(x["xml"]==readings[0]["xml"] for x in readings)
                 and readings[0]["xml"].encode("utf8")==sourceXML,
                 "Original IFC2X3 D_FULL/MANAGED/I identical-source read failed")
            full=_populate(sourceXML,state,managed=False)
            compact=_populate(managedXML,state,managed=True)
            code=_independent_live_python_code_v064(state,idx)
            d=D.call("submit_building_xml",{"xml_text":full})
            m=M.call("submit_managed_final_state",{"xml_text":compact})
            ai=I.call("execute_ifc_code",{"code":code})
            need(d["status"]==m["status"]==ai["status"]=="ok"
                 and ai["actual_genuine_pinned_Linux_Docker_Python_executed"]
                 and ai["actual_linux_backend"]=="linux_docker_sandbox"
                 and D.current_xml==M.current_xml==full.encode("utf8"),
                 "Original IFC2X3 D/managed/real-Docker I native edit failed")
            admitted=[]
            digests=[]
            physical=[]
            author=[]
            for session in (D,M,I):
                check=source_native_ifc2x3_scope_v064(
                    original,session.output_ifc,source_sha=SOURCE_SHA)
                need(check["status"]==STATUS
                     and check["native_original_IFC2X3_new_schema_errors"]==0
                     and abs(check[
                         "native_original_IFC2X3_wall_full_thickness_volume_lost_m3"]
                         -(width+.05)*.2*(height+.1))<.003,
                     "Original IFC2X3 physical original-model CSG cut failed")
                admitted.append(check)
                digests.append(canonical_semantic_digest_v064(check))
                physical.append(public_nearest_north_physical_v064(
                    original,session.output_ifc,task["public_question"]))
                author.append(original_author_repo_evaluator_only_v064(
                    original,session.output_ifc))
            need(digests[0]==digests[1]==digests[2],
                 "Original IFC2X3 D_FULL/MANAGED/actual Python I semantics differ")
            need(physical[0]==physical[1]==physical[2]
                 and physical[0]["public_original_question_physical_correct"]
                 is expected_public,
                 "Source-public nearest-north physical question evaluation failed")
            need(author[0]==author[1]==author[2],
                 "Original author repository D/I scorer metrics disagree")
            need(author[0]["status"]==
                 "UNMODIFIED_ORIGINAL_AUTHOR_REPOSITORY_EVALUATOR",
                 "Unmodified original author repository grader unavailable")
            outcomes.append({
                "source_only_developer_control_label":name,
                "original_source_correct_target_GUID_redacted":True,
                "new_IFC_guid_values_redacted":True,
                "complete_final_D_FULL_XML_utf8_bytes":len(full.encode("utf8")),
                "complete_final_D_MANAGED_XML_utf8_bytes":len(compact.encode("utf8")),
                "actual_developer_I_python_UTF8_bytes":len(code.encode("utf8")),
                "all_three_genuine_D_I_canonical_IFC_semantic_SHA256":digests[0],
                "native_original_IFC2X3_CSG_wall_volume_cut_m3":admitted[0][
                    "native_original_IFC2X3_wall_full_thickness_volume_lost_m3"],
                "native_original_IFC2X3_schema_new_findings":0,
                "native_source_164_original_STEP_entities_unchanged":True,
                "new_IFC2X3_mandatory_OwnerHistory_complete":True,
                "public_source_nearest_north_evaluator_only":physical[0],
                "original_author_repo_grader_evaluator_only":author[0],
                "actual_genuine_pinned_linux_docker_python":True,
                "model_generated_answer":False,
            })
            need(file_hash(original)==SOURCE_SHA,
                 "Original source IFC2X3 changed by developer control")
        # Real I: source-only no-through opening, correct hosted relation
        # exists but actual source Wall CSG volume is not full thickness.
        shallow=LiveDockerPython064(original,tmp/"SHALLOW_NATIVE_DOCKER")
        broken=native_source_developer_fixture_v064(
            "NEGATIVE_SHALLOW",near,.9,2.1)
        broken["opening_bbox"]=(
            broken["opening_bbox"][0],broken["opening_bbox"][1],
            1.54,1.63,0.,2.2)
        broken["door_bbox"]=(
            broken["door_bbox"][0],broken["door_bbox"][1],
            1.555,1.60,0.,2.1)
        shallowres=shallow.call("execute_ifc_code",{
            "code":_independent_live_python_code_v064(
                broken,walls.index(near))})
        need(shallowres["status"]=="error"
             and shallowres["native_ifc_committed"] is False
             and shallow.output_ifc is None,
             "Native IFC2X3 shallow Opening without full thickness admitted")
        # Real Docker native Door missing fills relation.
        nofill=LiveDockerPython064(original,tmp/"NO_FILL_NATIVE_DOCKER")
        nf=native_source_developer_fixture_v064(
            "NEGATIVE_NO_FILL",near,.9,2.1)
        failed=nofill.call("execute_ifc_code",{
            "code":_independent_live_python_code_v064(
                nf,walls.index(near),omit_filling=True)})
        need(failed["status"]=="error"
             and failed["native_ifc_committed"] is False
             and nofill.output_ifc is None,
             "IFC2X3 native Door without hosted relation admitted")
        # Real Python/IfcOpenShell valid then invalid second Door must
        # preserve previous accepted IFC SHA.
        chain=LiveDockerPython064(original,tmp/"LAST_GOOD_NATIVE_DOCKER")
        good_fixture=native_source_developer_fixture_v064(
            "REAL_DOCKER_GOOD",near,.9,2.1)
        first=chain.call("execute_ifc_code",{
            "code":_independent_live_python_code_v064(
                good_fixture,walls.index(near))})
        need(first["status"]=="ok" and chain.output_ifc is not None,
             "Real initial native IFC2X3 source I Docker commit failed")
        lastgood_sha=file_hash(chain.output_ifc)
        second=chain.call("execute_ifc_code",{"code":(
            "import ifcopenshell.api.root\n"
            "ifcopenshell.api.root.create_entity("
            "ifc,ifc_class='IfcDoor',name='SECOND_FORBIDDEN_DOOR')\n"
            "result={'extra_door':True}\n"
            "commit()\n"
        )})
        need(second["status"]=="error"
             and second["native_ifc_committed"] is False
             and file_hash(chain.output_ifc)==lastgood_sha,
             "Invalid actual native second Door overwrote last-good IFC2X3")
        # Declarative full valid followed by missing original Wall row;
        # explicitly preserve previous good source XML + native IFC.
        D=DirectFullState064(original,tmp/"D_GOOD_BAD_XML")
        good_state=native_source_developer_fixture_v064(
            "GOOD_D_FOR_ROLLBACK",near,.9,2.1)
        ok=D.call("submit_building_xml",{
            "xml_text":_populate(sourceXML,good_state,managed=False)})
        need(ok["status"]=="ok","Valid original D IFC2X3 baseline failed")
        good_sha=file_hash(D.output_ifc)
        good_xml=D.current_xml
        altered=etree.fromstring(good_xml)
        altered[1].remove(altered[1][0])
        bad=D.call("submit_building_xml",{"xml_text":
            etree.tostring(altered,encoding="utf8").decode("utf8")})
        need(bad["status"]=="error"
             and D.current_xml==good_xml
             and file_hash(D.output_ifc)==good_sha,
             "Original D IFC2X3 invalid final-state corrupted last-good native IFC")
    need(len(outcomes)==3
         and all(x["actual_genuine_pinned_linux_docker_python"] for x in outcomes)
         and file_hash(original)==SOURCE_SHA,
         "Original IFC2X3 source task native developer evidence incomplete")
    return {
        "status":"V064_ORIGINAL_IFC2X3_NEAREST_NORTH_DOOR_D_FULL_MANAGED_REAL_DOCKER_I_PASS",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/243",
        "parent_v063_exact_HEAD":PARENT_HEAD,
        "parent_v063_frozen_report_SHA256":PARENT_SHA,
        "prospective_v058_six_original_source_SHA256":FROZEN_SHA,
        "original_total_public_task_count":45,
        "original_total_distinct_IFC_source_files":31,
        "prespecified_six_original_public_task_ids_unchanged":FIXED_SIX,
        "fixed_six_original_source_native_developer_supported":FIXED_SIX,
        "original_fixed_six_now_developer_technically_supported_count":6,
        "original_total_45_task_specific_developer_supported_count":10,
        "original_total_45_tasks_not_developer_native_implemented":35,
        "new_native_source_task_in_v064":[TASK],
        "original_public_IFC_source_SHA256":SOURCE_SHA,
        "original_source_IFC_schema":"IFC2X3",
        "original_original_IFC2X3_native_length_unit":"MILLIMETER",
        "world_mesh_SI_unit":"METRE",
        "original_public_question_SHA256":task["public_question_sha256"],
        "pinned_original_author_evaluator_module_SHA256":
            file_hash(AUTHOR/"data"/"tests"/"geometry_test_03.py"),
        "original_IFC2X3_source_STEP_entities":164,
        "original_IFC2X3_source_IfcRoot_count":52,
        "original_IFC2X3_source_Wall_count":3,
        "original_IFC2X3_source_Door_count":0,
        "original_IFC2X3_source_Opening_count":0,
        "source_has_exact_two_walls_north_positive_Y":True,
        "public_source_nearest_positive_Y_vs_farther_wall_distinguished":True,
        "original_source_exact_three_Wall_initial_full_XML_utf8_bytes":
            len(sourceXML),
        "original_source_compact_three_Wall_XML_utf8_bytes":len(managedXML),
        "original_original_source_read_byte_identical_D_and_I":True,
        "D_full_complete_three_source_Wall_roster_and_two_new_final_elements":True,
        "D_managed_complete_three_Wall_roster_and_full_source_SHA":True,
        "native_real_D_full_original_IFC2X3_edits":3,
        "native_real_D_managed_original_IFC2X3_edits":3,
        "native_real_pinned_Linux_Docker_I_IFC2X3_edits":3,
        "actual_original_native_IFC2X3_developer_candidates_admitted":9,
        "genuine_pinned_OS_isolated_python_scripts_executed":3,
        "real_CSG_full_thickness_original_Wall_cut_in_every_admitted_candidate":True,
        "original_all_164_STEP_entities_preserved_per_candidate":True,
        "new_IFC2X3_mandatory_OwnerHistory_present_in_five_new_roots":True,
        "introduced_IFC2X3_schema_error_count":0,
        "all_D_full_managed_I_canonical_native_semantic_IFC_per_case_equal":True,
        "original_author_repo_mixed_bool_float_results_agree_D_I":True,
        "actual_native_Docker_shallow_ifc2x3_opening_rejected":True,
        "actual_native_Docker_door_without_fill_rejected":True,
        "actual_native_Docker_good_then_second_door_rejected_rollback_sha_preserved":True,
        "complete_D_good_then_missing_3rd_source_wall_rejected_XML_IFC_preserved":True,
        "original_source_dev_exposed_not_unseen_confirmatory_holdout":True,
        "source_specific_strict_STEP_identity_may_bias_general_I_vs_compiler_D":True,
        "unverified_original_IFC_asset_attribution_and_provider_transfer_rights":True,
        "published_paper_official_scorer_revision_equivalence_verified":False,
        "approved_paid_provider_model_snapshot_tokens_budget":None,
        "actual_LLM_generated_model_trials":0,
        "actual_paid_provider_calls":0,
        "original_IFC_provider_uploads":0,
        "source_only_original_IFC2X3_developer_controls":outcomes,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mx=p.add_mutually_exclusive_group(required=True)
    mx.add_argument("--write",action="store_true")
    mx.add_argument("--check",action="store_true")
    args=p.parse_args()
    report=canonical(build_report())
    if args.write:
        with REPORT.open("xb") as f:
            f.write(report)
    else:
        need(REPORT.is_file() and not REPORT.is_symlink()
             and REPORT.read_bytes()==report,
             "Frozen original IFC2X3 real native D/I Docker report bytes differ")
    print("V064_ORIGINAL_IFC2X3_NORTH_DOOR_SOURCE_NATIVE_D_I=PASS "
          "ACTUAL_IFC=9/9 ACTUAL_OS_ISOLATED_DOCKER=3/3 "
          "LLM_TRIALS=0 PAID_CALLS=0 SHA256="+sha256(report).hexdigest())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
