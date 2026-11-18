"""v0.59 REAL original-public source native D/I first heldout task controls.

Only developer/evaluator-side code accesses the original public question and
author's pinned test module. Model-facing v0.59 native/compiler/sessions never
import this module, author test, answer GUIDs or GT. All actual native controls
are built from source geometry and question text, NOT original-author hidden
test targets. No model inference or paid provider.

This task is now source-inspected and developer-control exposed, so the
original v0.58 "untouched" pilot candidate has been DEVELOPMENT-EXPOSED
for this task and can no longer be described as fully untouched.
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
from tools.bibimbap_v059_topo18_native import (
    SOURCE_SHA,TASK,Q,
    _source,_bounds,_mesh_points,
    source_full_state_v059,compact_original_state_v059,
    parse_full_final_state_v059,restore_compact_final_state_v059,
    native_space_delete_scope_v059,
)
from tools.bibimbap_v059_topo18_sessions import (
    DirectFullState059,DirectManagedFinalState059,LiveDockerPython059,
)
from tools.bibimbap_v057_provenance import (
    assert_original_source_rights_unchanged_v057,
    refuse_all_model_trials_v057,
    ProviderTrialBlocked057,
)


ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v059_first_new_source_native_topo18_20261118.json"
PARENT_REPORT=ROOT/"reports"/"bibimbap_v058_original45_capability_prospective_holdout_20261118.json"
PARENT_SHA="0d8e7ca07a08af0afa3a08c10de5a76427e179d41cd1ca9b9df508f40fcc96c8"
PARENT_HEAD="c8f66d4839e038d4edf481d44de71cbe98eaf6c3"
KIND={
    "geometry_test_03":"IFC2X3_CREATE_DOOR_AND_WALL_OPENING",
    "geometry_test_13":"IFC4X3_MOVE_WINDOW_AND_OPENING_BY_WORLD_X",
    "geometry_test_19":"IFC4X3_REMOVE_TWO_OPPOSITE_WINDOWS_LINKED_OPENINGS",
    "topological_test_05":"IFC4X3_CREATE_EXTERIOR_DOOR_AND_OPENING",
    "topological_test_12":"IFC4X3_SHORTEN_ONE_BOUNDARY_WALL_ONE_METRE",
    "topological_test_18":"IFC4X3_REMOVE_SOURCE_ENCLOSED_ROOM_AND_LINKED_METADATA",
}


def need(ok:bool,msg:str)->None:
    if not ok:
        raise AssertionError(msg)


def canonical(data:dict)->bytes:
    return (json.dumps(data,sort_keys=True,ensure_ascii=False,indent=2)
            +"\n").encode("utf8")


def _wall_contact_score(room,wall)->bool:
    """Source-native geometry: room mesh vertices meet selected wall bbox.

    Public source only; no author hidden target. A source-mesh geometric
    contact predicate is NOT the same as the original author's test score.
    """
    pts=_mesh_points(room)
    b=_bounds(wall)
    tol=0.005
    return any(
        b[0][0]-tol<=p[0]<=b[0][1]+tol
        and b[1][0]-tol<=p[1]<=b[1][1]+tol
        for p in pts
    )


def public_question_source_contact_v059(row:dict,source_ifc:Path)->dict[str,bool]:
    """Research-only physical predicate, never model tool or grader."""
    source=_source(source_ifc,row["original_ifc_sha256"])
    ids=re.findall(r"[0-9A-Za-z_$]{22}",row["public_question"])
    need(len(ids)==6 and len(set(ids))==6
         and all(source.by_guid(g).is_a("IfcWall") for g in ids),
         "Public question must identify six actual source walls")
    walls=[source.by_guid(g) for g in ids]
    scores={}
    for room in source.by_type("IfcSpace"):
        scores[room.GlobalId]=all(_wall_contact_score(room,wall) for wall in walls)
    need(len(scores)==3 and sum(scores.values())==1,
         "Native source six-wall geometry must distinguish one room")
    return scores


def _author_evaluator_only(source:Path,candidate:Path)->dict:
    """Explicit evaluator side; original code is never imported by tools."""
    sys.path.insert(0,str(AUTHOR))
    try:
        module=importlib.import_module("data.tests.topological_test_18")
        need(Path(module.__file__).resolve()==
             (AUTHOR/"data"/"tests"/"topological_test_18.py").resolve(),
             "Original author evaluator module source changed")
        raw=module.execute_test(str(source),str(candidate),None)
        need(isinstance(raw,dict) and raw
             and all(type(x) is bool for x in raw.values()),
             "Original author evaluator returned unexpected results")
        return {
            "original_author_repository_mean_boolean_score":round(
                sum(raw.values())/len(raw),6),
            "original_author_repository_per_metric":
                dict(sorted(raw.items())),
            "paper_published_official_equivalence_verified":False,
        }
    finally:
        sys.path.remove(str(AUTHOR))


def _code_for_source_derived_room(index:int)->str:
    # The code is NOT an AST-only fake, and the selected index is based
    # on all original spaces in the SOURCE list, without author GT.
    return (
        "import ifcopenshell.api\n"
        "spaces=ifc.by_type('IfcSpace')\n"
        f"ifcopenshell.api.run('root.remove_product', ifc, product=spaces[{index}])\n"
        "result={'actual_ifcopenshell_python_executed':True,"
        " 'remaining_spaces':len(ifc.by_type('IfcSpace'))}\n"
        "commit()\n"
    )


def _d_final_state(initial:bytes, guid:str)->str:
    doc=etree.fromstring(initial)
    found=False
    for room in doc[1]:
        if room.get("ifcGuid")==guid:
            found=True
            room.set("present","false")
    need(found,"Absent GUID not present in original managed D roster")
    return etree.tostring(doc,encoding="utf8",xml_declaration=True).decode("utf8")


def _managed_final_state(initial:bytes,guid:str)->str:
    doc=etree.fromstring(initial)
    found=False
    for room in doc:
        if room.get("ifcGuid")==guid:
            found=True
            room.set("present","false")
    need(found,"Absent GUID not present in original managed compact roster")
    return etree.tostring(doc,encoding="utf8",xml_declaration=True).decode("utf8")


def build_report()->dict:
    need(file_hash(PARENT_REPORT)==PARENT_SHA,
         "v0.58 source cluster/task shortlist report modified")
    rights=assert_original_source_rights_unchanged_v057()
    need(rights["status"]=="BLOCKED_NO_MODEL_PROVIDER_TRIAL",
         "Source data provider trial rights gate opened")
    parent=json.loads(PARENT_REPORT.read_text(encoding="utf8"))
    need(parent["total_original_public_edit_tasks"]==45
         and parent["original_unique_IFC_SHA_clusters"]==31
         and set(parent["prospective_six_source_heldout_task_ids"])==set(KIND)
         and TASK in parent["prospective_six_source_heldout_task_ids"]
         and parent["billable_provider_calls"]==0,
         "Original untouched-source fixed six-task selection drifted")
    rows={r["test_id"]:r for r in public_45(AUTHOR,DATA)}
    need(len(rows)==45,"Original question/provenance denominator drifted")
    seis=[]
    for task in sorted(KIND):
        row=rows[task]
        original=DATA/"ifc"/row["original_source_ifc_relpath"]
        need(file_hash(original)==row["original_ifc_sha256"],
             "Original source IFC source pin changed")
        f=ifcopenshell.open(str(original))
        objects=f.by_type("IfcProduct")
        seis.append({
            "original_task_id":task,
            "original_question_SHA256":row["public_question_sha256"],
            "original_source_IFC_SHA256":row["original_ifc_sha256"],
            "source_native_schema":f.schema,
            "native_IfcProduct_count":len(objects),
            "native_IfcSpace_count":len(f.by_type("IfcSpace")),
            "native_IfcWall_count":len(f.by_type("IfcWall")),
            "native_IfcWindow_count":len(f.by_type("IfcWindow")),
            "native_IfcDoor_count":len(f.by_type("IfcDoor")),
            "required_source_edit_class":KIND[task],
            "v059_real_source_native_D_FULL_admitted":
                task==TASK,
            "v059_real_source_native_D_MANAGED_admitted":
                task==TASK,
            "v059_real_source_native_pinned_Docker_I_admitted":
                task==TASK,
            "unimplemented_native_contract_and_geometry_oracle":
                None if task==TASK else "SOURCE_NATIVE_SEMANTICS_NOT_YET_IMPLEMENTED",
            "source_newly_exposed_to_developer_controls":task==TASK,
            "original_published_paper_score":None,
            "model_trials_this_checkpoint":0,
        })
    source=DATA/"ifc"/rows[TASK]["original_source_ifc_relpath"]
    original_sha=rows[TASK]["original_ifc_sha256"]
    need(original_sha==SOURCE_SHA,"First supported native source pin changed")
    contact=public_question_source_contact_v059(rows[TASK],source)
    native=ifcopenshell.open(str(source))
    original_guids=[room.GlobalId for room in native.by_type("IfcSpace")]
    need(set(original_guids)==set(contact),"Original 3 native rooms changed")
    test_module=AUTHOR/"data"/"tests"/f"{TASK}.py"
    module_sha=file_hash(test_module)
    controls=[]
    with TemporaryDirectory(prefix="v059-DEVELOPER-ONLY-real-docker-") as tmp:
        sandbox=Path(tmp)
        for i,guid in enumerate(original_guids):
            group="PUBLIC_SOURCE_GEOMETRIC_POSITIVE" if contact[guid] \
                else "PUBLIC_SOURCE_GEOMETRIC_NEGATIVE"
            folder=sandbox/f"{i}"
            D=DirectFullState059(source,folder/"D")
            M=DirectManagedFinalState059(source,folder/"M")
            I=LiveDockerPython059(source,folder/"I")
            dr=D.call("read_building_xml",{"query":"source"})
            mr=M.call("read_building_xml",{"query":"source"})
            ir=I.call("read_building_xml",{"query":"source"})
            need(dr["status"]==mr["status"]==ir["status"]=="ok"
                 and dr["xml"]==mr["xml"]==ir["xml"],
                 "Actual original source D-full/D-managed/I read mismatch")
            doc=_d_final_state(D.source_xml,guid)
            compact=_managed_final_state(
                compact_original_state_v059(source,source_sha=original_sha),
                guid,
            )
            d=D.call("submit_building_xml",{"xml_text":doc})
            m=M.call("submit_managed_final_state",{"xml_text":compact})
            native_code=_code_for_source_derived_room(i)
            outcome=I.call("execute_ifc_code",{"code":native_code})
            need(d["status"]==m["status"]==outcome["status"]=="ok"
                 and d["native_ifc_sha256"]==m["native_ifc_sha256"]
                 and outcome["python_execution_attested"] is True
                 and outcome["actual_linux_sandbox_backend"]==
                     "linux_docker_sandbox"
                 and d["introduced_schema_errors"]==
                     m["introduced_schema_errors"]==
                     outcome["introduced_schema_errors"]==0,
                 "True D/I original IFC native source holdout editing failed")
            for item in (D,M,I):
                inspected=native_space_delete_scope_v059(
                    source,item.output_ifc,source_sha=original_sha)
                need(inspected["deleted_original_IfcSpace_count"]==1
                     and inspected["new_schema_errors"]==0,
                     "Independent actual IFC scope gate failed")
                # Separate evaluator-only original repository grader. Never
                # include its values in D/I model-visible tool return.
            grades={
                "D_COMPLETE_XML_V059":_author_evaluator_only(source,D.output_ifc),
                "D_MANAGED_FINAL_STATE_V059":_author_evaluator_only(source,M.output_ifc),
                "I_NATIVE_DOCKER_V059":_author_evaluator_only(source,I.output_ifc),
            }
            need(grades["D_COMPLETE_XML_V059"]==
                 grades["D_MANAGED_FINAL_STATE_V059"]==
                 grades["I_NATIVE_DOCKER_V059"],
                 "Original-author source-grader metrics differ between D/I")
            controls.append({
                "developer_source_only_research_predicate":group,
                "original_space_source_index":i,
                # Never publish the task target GUID/answer in a model-data file.
                "original_target_space_GUID_in_Git_report":None,
                "D_full_native_candidate_SHA256":d["native_ifc_sha256"],
                "D_compact_native_candidate_SHA256":m["native_ifc_sha256"],
                "I_genuine_Docker_native_candidate_SHA256":
                    outcome["native_ifc_sha256"],
                "D_and_I_semantic_and_original_author_metric_match":True,
                "original_author_repo_evaluator_side_only":grades["D_COMPLETE_XML_V059"],
                "all_D_I_candidate_native_schema_error_delta":0,
                "input_source_XML_UTF8_bytes":len(D.source_xml),
                "D_full_final_state_XML_UTF8_bytes":len(doc.encode("utf8")),
                "D_compact_final_XML_UTF8_bytes":len(compact.encode("utf8")),
                "I_developer_python_UTF8_bytes":len(native_code.encode("utf8")),
                "real_Docker_python_worker_executed":True,
                "actual_model_generated":False,
            })
            need(file_hash(source)==original_sha,
                 "Original native source changed after actual D/I commit")
        # Adversarial unclean raw deletion in real pinned Docker: no linked
        # metadata cleanup. Even if worker calls commit(), host must reject.
        bad=LiveDockerPython059(source,sandbox/"invalid_raw")
        raw=bad.call("execute_ifc_code",{
            "code":(
                "space=ifc.by_type('IfcSpace')[0]\n"
                "ifc.remove(space)\n"
                "result={'attempted_raw_low_level_remove':True}\n"
                "commit()\n"
            ),
        })
        need(raw["status"]=="error"
             and raw["native_ifc_committed"] is False
             and bad.output_ifc is None,
             "True Docker raw invalid source room deletion was accepted")
        # Actual I worker good -> malformed second commit -> last-good bytes
        # unchanged. No model sees the grader, failure reason bounded.
        series=LiveDockerPython059(source,sandbox/"rollback")
        first=series.call("execute_ifc_code",{
            "code":_code_for_source_derived_room(0)})
        need(first["status"]=="ok","Actual first good Docker edit failed")
        goodsha=file_hash(series.output_ifc)
        # Remove a SECOND room after the first already removed -> violates
        # fixed source task exactly-one-space-removed contract.
        broken=series.call("execute_ifc_code",{
            "code":_code_for_source_derived_room(0)})
        need(broken["status"]=="error"
             and broken["native_ifc_committed"] is False
             and file_hash(series.output_ifc)==goodsha,
             "True Docker second invalid edit modified last-good IFC")
        # Whole-XML D valid then structurally incomplete XML should also
        # preserve both last-good XML and real native IFC bytes.
        drollback=DirectFullState059(source,sandbox/"drollback")
        dvalid=drollback.call("submit_building_xml",{
            "xml_text":_d_final_state(drollback.source_xml,original_guids[0])})
        need(dvalid["status"]=="ok","D-state baseline IFC failed")
        gooddoc=drollback.current_xml
        goodifc=file_hash(drollback.output_ifc)
        invalidroot=etree.fromstring(gooddoc)
        invalidroot[1].remove(invalidroot[1][0])
        derror=drollback.call("submit_building_xml",{
            "xml_text":etree.tostring(invalidroot,encoding="utf8").decode("utf8")})
        need(derror["status"]=="error"
             and drollback.current_xml==gooddoc
             and file_hash(drollback.output_ifc)==goodifc,
             "D whole original roster failed to roll back")
    need(len(controls)==3
         and Counter(x["developer_source_only_research_predicate"]
                     for x in controls)=={
             "PUBLIC_SOURCE_GEOMETRIC_POSITIVE":1,
             "PUBLIC_SOURCE_GEOMETRIC_NEGATIVE":2,
         },
         "Original public source geometry has unexpected outcome partition")
    return {
        "status":"V059_FIRST_ORIGINAL_HOLDOUT_TOPO18_D_FULL_D_MANAGED_REAL_DOCKER_I_NATIVE_PASS",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/233",
        "parent_v058_frozen_head":PARENT_HEAD,
        "parent_v058_report_SHA256":PARENT_SHA,
        "original_public_cohort_size":45,
        "original_unique_IFC_source_count":31,
        "original_six_source_strata_selected_task_ids":
            sorted(KIND),
        "exact_original_six_holdout_order_unchanged":
            parent["prospective_randomized_task_order"],
        "v059_source_native_task_scope_added":[TASK],
        "remaining_five_holdout_source_native_tasks_unsupported":
            sorted(set(KIND)-{TASK}),
        "previous_engineered_four_original_native_supported_unchanged":True,
        "current_5_total_native_task_specific_developer_supported":5,
        "other_40_original_public_tasks_unverified":40,
        "v058_six_candidate_no_longer_fully_unexposed_to_developer_implementation":True,
        "v059_topo18_already_developer_fixture_exposed":True,
        "full_benchmark_or_confirmatory_holdout_still_blocked":True,
        "original_native_source_ifc_schema":"IFC4X3",
        "original_native_source_ifc_sha256":original_sha,
        "original_public_question_SHA256":rows[TASK]["public_question_sha256"],
        "original_pinned_author_source_eval_module_SHA256":module_sha,
        "original_public_source_geometry_six_wall_contact_unique_room":True,
        "original_space_geometry_positive_count":1,
        "original_space_geometry_negative_count":2,
        "original_source_D_I_initial_XML_byte_identical":True,
        "three_native_IfcSpace_developer_control_targets_x_three_arms":9,
        "actual_genuine_pinned_Linux_Docker_ifcopenshell_successful_cases":3,
        "actual_D_full_native_cases":3,
        "actual_D_managed_native_cases":3,
        "source_only_ifc4x3_root_and_nonroot_native_scope_and_schema_delta_PASS":True,
        "source_only_IfcSpace_root_api_cleanup_without_author_GT":True,
        "actual_original_author_repo_metric_D_I_matched_per_case":True,
        "official_published_paper_grader_provenance_verified":False,
        "actual_published_paper_score":None,
        "actual_Docker_raw_room_remove_rejected":True,
        "actual_Docker_after_valid_invalid_commit_last_good_sha_preserved":True,
        "actual_D_full_after_valid_missing_managed_roster_rollback":True,
        "allowed_native_IFC_alternative_encodings_not_guaranteed":True,
        "source_only_6_wall_geometry_is_not_author_hidden_GT":True,
        "all_six_original_public_source_diagnostics":seis,
        "topo18_developer_only_native_D_I_cases":controls,
        "actual_model_generated_trials":0,
        "paid_model_calls":0,
        "model_and_provider_snapshot":None,
        "approved_original_IFC_model_transfer":False,
        "approved_model_billed_token_and_USD_budget":None,
    }


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write",action="store_true")
    group.add_argument("--check",action="store_true")
    args=parser.parse_args()
    output=canonical(build_report())
    if args.write:
        with REPORT.open("xb") as f:
            f.write(output)
    else:
        need(REPORT.is_file() and REPORT.read_bytes()==output,
             "Frozen actual source-original D/I Docker replay drifted")
    print("V059_ORIGINAL_TOPO18_D_FULL_D_MANAGED_REAL_DOCKER_I=PASS "
          "NATIVE_CANDIDATES=9/9 GENUINE_DOCKER_I=3/3 "
          "SOURCE_CONTACT_POSITIVE=1 NEGATIVE=2 MODEL=0 PAID=0 SHA256="+
          sha256(output).hexdigest())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
