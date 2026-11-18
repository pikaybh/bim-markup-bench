"""v0.61 original native Window/Opening+3 details D/I real Docker audit.

ORIGINAL SOURCE PUBLIC QUESTION and author evaluator are read ONLY here,
outside model-facing tools, code/compiler, and actual Docker worker.
Developer controls: 1 physically correct >1.50m/+3m source Window, 2
wrong cases (short Window/+3m, correct wide Window/+2m). All may be
structurally admissible IFC while research/public-question correctness
remains separate. Author metrics are a distinct unmodified repo layer.

Canonical report does not contain public solution target GUID, model code,
private author GT or input IFC content. No paid LLM calls or uploads.
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
from tools.bibimbap_v061_geometry13_native import (
    SOURCE_SHA,TASK,_source,_mesh_bounds,original_assembly_groups_v061,
    full_source_final_state_v061,compact_complete_final_state_v061,
    independent_assembly_world_scope_v061,
    semantic_digest_after_native_oracle_v061,
)
from tools.bibimbap_v061_geometry13_sessions import (
    DirectFullState061,DirectManagedState061,LiveDockerPython061,
)


ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v061_window_opening_proxy_native_DI_20261118.json"
PARENT=ROOT/"reports"/"bibimbap_v060_first_window_opening_native_DI_20261118.json"
PARENT_SHA="e40204f381ccd17876708dd861c7031c1836cc41b7335e49909e797647f042ae"
PARENT_HEAD="e317a3965899274535d807e39ea8de64fe0fa3dd"
FROZEN=ROOT/"reports"/"bibimbap_v058_original45_capability_prospective_holdout_20261118.json"
FROZEN_SHA="0d8e7ca07a08af0afa3a08c10de5a76427e179d41cd1ca9b9df508f40fcc96c8"
HOLDOUT=[
    "geometry_test_03","geometry_test_13","geometry_test_19",
    "topological_test_05","topological_test_12","topological_test_18",
]
SUPPORTED={"geometry_test_13","geometry_test_19","topological_test_18"}


def need(ok:bool,why:str):
    if not ok:
        raise AssertionError(why)


def canonical(v:dict)->bytes:
    return (json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)
            +"\n").encode("utf8")


def public_source_width_predicate_only_v061(source:Path,question:str)->dict[str,bool]:
    """Evaluator-only public task width condition, NOT author hidden GT."""
    need(bool(re.search(r"3m",question))
         and bool(re.search(r"1\.50m",question))
         and "window" in question.lower(),
         "Original public question geometry predicate changed")
    model=_source(source,source_sha=SOURCE_SHA)
    groups=original_assembly_groups_v061(model)
    correct={}
    for guid,group in groups.items():
        box=group["source_window_bbox"]
        width=box[0][1]-box[0][0]
        correct[guid]=width>1.5
    need(len(correct)==2 and Counter(correct.values())=={
        True:1,False:1,
    },"Original source must have 1 wide and 1 narrow Window")
    return correct


def _full_submit(initial:bytes,group,dx:float)->str:
    node=etree.fromstring(initial)
    guids={p.GlobalId for p in group["members"]}
    need(len(guids)==5,"Source native assembly must have 5 physical products")
    for entry in node[1]:
        if entry.get("ifcGuid") in guids:
            initial_x=float(entry.get("finalWorldMinXM"))
            entry.set("finalWorldMinXM",f"{initial_x+dx:.6f}")
    return etree.tostring(node,encoding="utf8",xml_declaration=True).decode("utf8")


def _managed_submit(initial:bytes,group,dx:float)->str:
    node=etree.fromstring(initial)
    guids={p.GlobalId for p in group["members"]}
    for entry in node:
        if entry.get("ifcGuid") in guids:
            initial_x=float(entry.get("finalWorldMinXM"))
            entry.set("finalWorldMinXM",f"{initial_x+dx:.6f}")
    return etree.tostring(node,encoding="utf8",xml_declaration=True).decode("utf8")


def _dev_native_code(source_window_index:int,dx:float,
                     *,only_three_details:bool=True)->str:
    """Evaluator-side source-derived generic Python, no target GUID leaked."""
    need(source_window_index in (0,1)
         and dx in (2.,3.),
         "Source developer control index/distance invalid")
    # Use world mesh center (metres) to infer which three original native
    # details physically belong to chosen original hosted Window. Source
    # IFC placements themselves are native mm and opening parented.
    return (
        "import ifcopenshell.geom\n"
        "settings=ifcopenshell.geom.settings()\n"
        "settings.set(settings.USE_WORLD_COORDS,True)\n"
        "windows=sorted(ifc.by_type('IfcWindow'),key=lambda x:x.GlobalId)\n"
        f"win=windows[{source_window_index}]\n"
        "shape=ifcopenshell.geom.create_shape(settings,win)\n"
        "v=list(shape.geometry.verts)\n"
        "center=(min(v[0::3])+max(v[0::3]))/2\n"
        "opening=win.FillsVoids[0].RelatingOpeningElement\n"
        "details=[p for p in ifc.by_type('IfcBuildingElementProxy') "
        "if abs(p.ObjectPlacement.RelativePlacement.Location.Coordinates[0]/1000"
        "-center)<.015]\n"
        + ("elements=[opening,*details]\n" if only_three_details else
           "elements=[opening]\n")
        + "for product in elements:\n"
        "    point=product.ObjectPlacement.RelativePlacement.Location\n"
        "    values=list(point.Coordinates)\n"
        f"    values[0]+={int(dx*1000)}\n"
        "    point.Coordinates=tuple(values)\n"
        "result={'source_assembly_objects_moved':len(elements)}\n"
        "commit()\n"
    )


def original_author_repository_evaluator_only(
    source:Path,candidate:Path,
)->dict:
    """Original scorer is NEVER in model session/compiler/actual Python."""
    sys.path.insert(0,str(AUTHOR))
    try:
        m=importlib.import_module("data.tests.geometry_test_13")
        need(Path(m.__file__).resolve()==
             (AUTHOR/"data"/"tests"/"geometry_test_13.py").resolve(),
             "Original author evaluator module location changed")
        try:
            raw=m.execute_test(str(source),str(candidate),None)
        except Exception as exc:
            # Author target GUID and internal scorer code are not exposed.
            return {
                "status":"ORIGINAL_REPOSITORY_EVALUATOR_UNAVAILABLE",
                "original_exception_class":type(exc).__name__,
                "original_exception_message_redacted":True,
                "author_repository_mean_boolean_score":None,
                "author_repository_boolean_metrics":None,
                "official_paper_grader_revision_verified":False,
            }
        need(isinstance(raw,dict) and raw
             and all(type(v) is bool for v in raw.values()),
             "Original author evaluator returned non-boolean metrics")
        return {
            "status":"EVALUATOR_RETURNED_BOOLEAN_METRICS",
            "author_repository_mean_boolean_score":
                round(sum(raw.values())/len(raw),6),
            "author_repository_boolean_metrics":dict(sorted(raw.items())),
            "official_paper_grader_revision_verified":False,
        }
    finally:
        sys.path.remove(str(AUTHOR))


def build_report()->dict:
    need(file_hash(PARENT)==PARENT_SHA
         and file_hash(FROZEN)==FROZEN_SHA,
         "Prior frozen reports changed")
    old=json.loads(PARENT.read_text(encoding="utf8"))
    reg=json.loads(FROZEN.read_text(encoding="utf8"))
    need(old["v060_new_original_source_native_task_added"]==["geometry_test_19"]
         and sorted(reg["prospective_six_source_heldout_task_ids"])==HOLDOUT
         and old["model_generated_trials"]==0,
         "Original public six task selection or prior report changed")
    rights=assert_original_source_rights_unchanged_v057()
    need(rights["status"]=="BLOCKED_NO_MODEL_PROVIDER_TRIAL",
         "Provider original data/model trial rights gate changed")
    rows={r["test_id"]:r for r in public_45(AUTHOR,DATA)}
    need(len(rows)==45 and len({r["original_ifc_sha256"]
                               for r in rows.values()})==31,
         "45-task/31 original source population drift")
    row=rows[TASK]
    source=DATA/"ifc"/row["original_source_ifc_relpath"]
    need(row["original_ifc_sha256"]==SOURCE_SHA
         and file_hash(source)==SOURCE_SHA,
         "Original exact geometry13 public IFC source changed")
    model=_source(source,source_sha=SOURCE_SHA)
    groups=original_assembly_groups_v061(model)
    source_pred=public_source_width_predicate_only_v061(
        source,row["public_question"])
    keys=sorted(groups)
    valid=next(k for k in keys if source_pred[k])
    invalid=next(k for k in keys if not source_pred[k])
    developer_cases=[
        ("PUBLIC_SOURCE_PHYSICAL_CORRECT_WIDE_PLUS_3M",valid,3.),
        ("PUBLIC_SOURCE_PHYSICAL_WRONG_NARROW_PLUS_3M",invalid,3.),
        ("PUBLIC_SOURCE_PHYSICAL_WRONG_WIDE_PLUS_2M",valid,2.),
    ]
    initial=full_source_final_state_v061(source,source_sha=SOURCE_SHA)
    managed=compact_complete_final_state_v061(source,source_sha=SOURCE_SHA)
    controls=[]
    with TemporaryDirectory(prefix="v061-ACTUAL-D-I-DOCKER-source-") as tmp:
        trial=Path(tmp)
        for index,(label,guid,dx) in enumerate(developer_cases):
            folder=trial/f"case_{index}"
            D=DirectFullState061(source,folder/"D")
            M=DirectManagedState061(source,folder/"M")
            I=LiveDockerPython061(source,folder/"I")
            reads=[s.call("read_building_xml",{"query":"source"})
                   for s in (D,M,I)]
            need(all(r["status"]=="ok" for r in reads)
                 and reads[0]["xml"].encode("utf8")==initial
                 and reads[0]["xml"]==reads[1]["xml"]==reads[2]["xml"],
                 "Original source D/I read-input parity violated")
            whole=_full_submit(initial,groups[guid],dx)
            compact=_managed_submit(managed,groups[guid],dx)
            indices=(keys.index(guid))
            python_code=_dev_native_code(indices,dx)
            d=D.call("submit_building_xml",{"xml_text":whole})
            m=M.call("submit_managed_final_state",{"xml_text":compact})
            i=I.call("execute_ifc_code",{"code":python_code})
            need(d["status"]==m["status"]==i["status"]=="ok"
                 and i["real_pinned_Docker_python_executed"] is True
                 and i["actual_linux_sandbox_backend"]=="linux_docker_sandbox",
                 "Actual original Window native D/I good/wrong control failed")
            need(D.current_xml==M.current_xml==whole.encode("utf8"),
                 "Trusted complete-state reconstructed D full != D managed")
            s=[]
            for arm in (D,M,I):
                result=independent_assembly_world_scope_v061(
                    source,arm.output_ifc,source_sha=SOURCE_SHA)
                need(result["status"]==
                     "V061_TWO_WINDOW_SOURCE_ONE_ASSEMBLY_NATIVE_MOVE_SCOPE_PASS"
                     and result["five_physical_products_world_X_moved"]==5
                     and result["original_IfcOpenShell_schema_errors_introduced"]==0
                     and abs(result["source_X_delta_magnitude"]-dx)<0.00001,
                     "Actual IFC source-native spatial relationship/original schema failed")
                s.append(semantic_digest_after_native_oracle_v061(
                    arm.output_ifc))
            need(s[0]==s[1]==s[2],
                 "Actual original native IFC D/M/I canonical semantic fingerprints differ")
            grade={
                "D_FULL":original_author_repository_evaluator_only(
                    source,D.output_ifc),
                "D_MANAGED":original_author_repository_evaluator_only(
                    source,M.output_ifc),
                "I_PINNED_DOCKER":original_author_repository_evaluator_only(
                    source,I.output_ifc),
            }
            need(grade["D_FULL"]==grade["D_MANAGED"]==grade["I_PINNED_DOCKER"],
                 "Original author evaluator-only outcomes differ across arms")
            controls.append({
                "developer_only_public_source_physical_label":label,
                "target_original_window_GUID_redacted":True,
                "target_window_source_index_redacted":True,
                "source_native_IFC_semantic_SHA256_all_D_and_I":s[0],
                "D_full_final_XML_bytes":len(whole.encode("utf8")),
                "D_managed_final_XML_bytes":len(compact.encode("utf8")),
                "I_developer_python_code_bytes":len(python_code.encode("utf8")),
                "actual_native_products_world_X_moved":5,
                "original_native_IfcOpenShell_new_schema_errors":0,
                "original_author_repository_metric_evaluator_only":grade["D_FULL"],
                "all_three_native_D_I_actual_original_semantics_match":True,
                "actual_genuine_Docker_code_executed":True,
                "actual_LLM_model_generated":False,
            })
            need(file_hash(source)==SOURCE_SHA,
                 "Original source IFC mutated during Docker tests")
        # Genuine Docker missing-three-proxies adversarial case: even if
        # Window follows Opening it is NOT a correct full native assembly.
        bad=LiveDockerPython061(source,trial/"BAD_OPENING_ONLY")
        raw=bad.call("execute_ifc_code",{
            "code":_dev_native_code(keys.index(valid),3.,only_three_details=False),
        })
        need(raw["status"]=="error" and raw["native_ifc_committed"] is False
             and bad.output_ifc is None,
             "Missing all three actual detail proxies wrongly admitted")
        # Genuine Docker good + bad: second independent target group is
        # changed too, MUST reject while last-good IFC bytes remain intact.
        last=LiveDockerPython061(source,trial/"GOOD_THEN_BAD")
        good=last.call("execute_ifc_code",{
            "code":_dev_native_code(keys.index(valid),3.),
        })
        need(good["status"]=="ok" and last.output_ifc is not None,
             "Actual Docker prior good IFC was not committed")
        oldsha=file_hash(last.output_ifc)
        second=last.call("execute_ifc_code",{
            "code":_dev_native_code(keys.index(invalid),3.),
        })
        need(second["status"]=="error"
             and second["native_ifc_committed"] is False
             and file_hash(last.output_ifc)==oldsha,
             "Actual Docker invalid second group move changed last-good IFC")
        # D complete-state valid->incomplete roster must also roll back.
        drollback=DirectFullState061(source,trial/"D_LAST_GOOD")
        dgood=drollback.call("submit_building_xml",{
            "xml_text":_full_submit(initial,groups[valid],3.)})
        need(dgood["status"]=="ok","D full original source good edit failed")
        oldxml=drollback.current_xml
        oldfile=file_hash(drollback.output_ifc)
        malformed=etree.fromstring(oldxml)
        malformed[1].remove(malformed[1][0])
        dbad=drollback.call("submit_building_xml",{
            "xml_text":etree.tostring(malformed,encoding="utf8").decode("utf8")})
        need(dbad["status"]=="error"
             and drollback.current_xml==oldxml
             and file_hash(drollback.output_ifc)==oldfile,
             "D original complete final state failed post-invalid rollback")
    need(len(controls)==3
         and len({c["developer_only_public_source_physical_label"]
                 for c in controls})==3
         and all(c["actual_genuine_Docker_code_executed"] for c in controls),
         "Actual 3 original native Window source developer controls missing")
    return {
        "status":"V061_ORIGINAL_WINDOW_OPENING_THREE_DETAILS_NATIVE_D_FULL_D_MANAGED_REAL_DOCKER_I_PASS",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/237",
        "parent_v060_exact_HEAD":PARENT_HEAD,
        "parent_v060_report_SHA256":PARENT_SHA,
        "original_v058_six_source_holdout_selection_report_SHA256":FROZEN_SHA,
        "original_public_task_count":45,
        "original_unique_IFC_input_SHA_cluster_count":31,
        "original_v058_six_task_selection_unchanged":HOLDOUT,
        "new_original_native_task_supported_in_v061":[TASK],
        "all_three_current_v058_selected_source_native_developer_supported":
            sorted(SUPPORTED),
        "remaining_original_six_source_tasks_not_admitted":
            sorted(set(HOLDOUT)-SUPPORTED),
        "current_original_task_specific_native_engineering_controls":7,
        "remaining_original_public_tasks_unverified":38,
        "original_IFC_SHA256":SOURCE_SHA,
        "original_IFC_schema":"IFC4X3",
        "original_public_question_SHA256":row["public_question_sha256"],
        "original_author_repo_evaluator_module_SHA256":
            file_hash(AUTHOR/"data"/"tests"/"geometry_test_13.py"),
        "source_native_window_widths_metres":[0.6,1.6],
        "public_source_window_threshold_m":1.5,
        "source_correct_window_positive_count":1,
        "source_wrong_window_negative_count":1,
        "original_native_IfcWindow_count":2,
        "original_native_IfcOpeningElement_count":2,
        "original_native_IfcBuildingElementProxy_count":6,
        "native_source_window_local_origin_shared":True,
        "all_original_four_managed_independent_placement_points_per_assembly":True,
        "original_IFC_length_unit_native_mm_WORLD_geometry_m":True,
        "original_D_FULL_and_D_MANAGED_and_Docker_I_identical_source_XML":
            True,
        "source_full_original_BuildingState_UTF8_bytes":len(initial),
        "source_compact_original_complete_managed_UTF8_bytes":len(managed),
        "full_original_source_managed_elements_explicit":10,
        "actual_original_native_IFC_D_FULL_cases":3,
        "actual_original_native_IFC_D_MANAGED_cases":3,
        "actual_original_native_IFC_genuine_Docker_python_cases":3,
        "total_native_original_IFC_successful_developer_controls":9,
        "native_source_scope_IFC_schema_introduced_errors":0,
        "actual_source_only_correctness_is_separate_from_original_author_repo_score":True,
        "D_I_normalized_native_semantic_digests_match_each_case":True,
        "genuine_Docker_opening_only_missing_proxies_rejected":True,
        "genuine_Docker_good_then_invalid_second_group_last_IFC_preserved":True,
        "D_complete_state_good_then_bad_last_IFC_and_XML_preserved":True,
        "strict_source_STEP_placegraph_limits_other_equivalent_encoding_support":True,
        "v058_preselected_original_six_no_longer_developer_blind":True,
        "geometry13_source_developer_exposed":True,
        "original_IFC_provider_upload_count":0,
        "actual_LLM_generated_trial_count":0,
        "paid_model_provider_calls":0,
        "approved_original_underlying_IFC_owner_permission_and_provider_transfer":False,
        "approved_paid_model_snapshot_budget_protocol":None,
        "published_paper_official_model_score":None,
        "three_original_source_developer_controls":controls,
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    z=p.add_mutually_exclusive_group(required=True)
    z.add_argument("--write",action="store_true")
    z.add_argument("--check",action="store_true")
    args=p.parse_args()
    content=canonical(build_report())
    if args.write:
        with REPORT.open("xb") as f:
            f.write(content)
    else:
        need(REPORT.is_file() and not REPORT.is_symlink()
             and REPORT.read_bytes()==content,
             "Frozen real D/I source-native Docker IFC report replay drifted")
    print("V061_ORIGINAL_WINDOW_OPENING_PROXY_NATIVE_D_I=PASS "
          "REAL_IFCS=9/9 ACTUAL_ISOLATED_DOCKER_PYTHON=3/3 "
          "MODEL_TRIALS=0 PAID=0 "
          "FROZEN_REPORT_SHA256="+sha256(content).hexdigest())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
