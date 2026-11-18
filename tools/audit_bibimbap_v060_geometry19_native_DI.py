"""v0.60 evaluator-only original-source 2-window native D/I Docker audit.

All source-physical question interpretation and author repository evaluator
execution occur HERE, never in the model-facing D/I sessions or native gate.

The original IFC is SHA-pinned. Three source-derived developer cases:
1 actual public-question 2-window opposite pair, one wrong pair containing
one correct/one wrong, one wrong pair containing two wrong windows. These
are developer fixtures, NOT LLM completions or an untouched holdout.

Native IfcOpenShell root.remove_product writes a real-time
IfcOwnerHistory.LastModifiedDate; therefore the frozen report uses native
source oracle + normalized SEMANTIC digest. It must not assert raw binary
native IFC SHA equal, even for semantically identical outputs.

Only the actual pinned local isolated Linux Docker worker can attest I.
No paid provider or external IFC uploads. Original author score is an
evaluator-only separate metric, NOT official published paper equivalence.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import argparse
import importlib
import itertools
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory

import ifcopenshell
from lxml import etree

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v060_geometry19_native import (
    SOURCE_SHA,TASK,_source,_bounds,source_full_state_v060,
    compact_source_state_v060,independent_two_window_native_scope_v060,
    canonical_original_native_semantic_digest_v060,
)
from tools.bibimbap_v060_geometry19_sessions import (
    DirectFullState060,DirectManagedState060,LiveDockerPython060,
)
from tools.bibimbap_v057_provenance import (
    assert_original_source_rights_unchanged_v057,
    refuse_all_model_trials_v057,ProviderTrialBlocked057,
)


ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v060_first_window_opening_native_DI_20261118.json"
PARENT_REPORT=ROOT/"reports"/"bibimbap_v059_first_new_source_native_topo18_20261118.json"
PARENT_REPORT_SHA="a40d236129d39014b9127619fd5b63fca5b19eaf3f967027e2ee1338ac6af4ec"
PARENT_HEAD="f1cbde13483818054fe2dcbd7c57f37211fe8ec9"
PREV_HOLDOUT=ROOT/"reports"/"bibimbap_v058_original45_capability_prospective_holdout_20261118.json"
PREV_HOLDOUT_SHA="0d8e7ca07a08af0afa3a08c10de5a76427e179d41cd1ca9b9df508f40fcc96c8"
FIXED_HOLDOUT=[
    "geometry_test_03","geometry_test_13","geometry_test_19",
    "topological_test_05","topological_test_12","topological_test_18",
]
CURRENT_ADMITTED={
    "topological_test_18","geometry_test_19",
}
NATIVE_DEVELOPER_SUPPORTED_PRIOR={
    "geometry_test_14","geometry_test_15",
    "topological_test_11","topological_test_17","topological_test_18",
}


def need(ok:bool,reason:str)->None:
    if not ok:
        raise AssertionError(reason)


def canonical(data:dict)->bytes:
    return (json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)
            +"\n").encode("utf8")


def public_question_opposite_windows_only_v060(
    original_ifc:Path,question:str,
)->dict[str,bool]:
    """Independent PUBLIC geometry physical predicate; no hidden author GT.

    Source question references one y-horizontal wall. 'Opposite' windows
    here means original windows hosted by another Y-horizontal wall
    with x-projection STRICTLY inside the reference wall span, and
    separated in Y. This criterion is research-defined, not the author
    repository's private answer criterion.
    """
    file=_source(original_ifc,source_sha=SOURCE_SHA)
    mentioned=re.findall(r"[0-9A-Za-z_$]{22}",question)
    need(len(mentioned)==1 and file.by_guid(mentioned[0]).is_a("IfcWall"),
         "Exactly one original public question wall reference")
    ref=file.by_guid(mentioned[0])
    base=_bounds(ref)
    need(base[0][1]-base[0][0]>1.0
         and base[1][1]-base[1][0]<0.35,
         "Source reference wall must be horizontal across X")
    midpoint=sum(base[1])/2
    matches={}
    for window in file.by_type("IfcWindow"):
        v=_bounds(window)
        host=window.FillsVoids[0].RelatingOpeningElement.VoidsElements[0].RelatingBuildingElement
        h=_bounds(host)
        matches[window.GlobalId]=(
            h[0][1]-h[0][0]>1.0
            and h[1][1]-h[1][0]<0.35
            and abs(sum(h[1])/2-midpoint)>0.75
            and v[0][0]>base[0][0]+0.01
            and v[0][1]<base[0][1]-0.01
        )
    need(len(matches)==7 and Counter(matches.values())=={
        True:2,False:5,
    },"Public source opposite wall source geometry ambiguous")
    return matches


def selected_three_developer_pairs_v060(
    source_ifc:Path,question:str,
)->list[tuple[str,tuple[str,str]]]:
    scores=public_question_opposite_windows_only_v060(source_ifc,question)
    true=set(g for g,ok in scores.items() if ok)
    false=set(scores)-true
    pairs=list(itertools.combinations(sorted(scores),2))
    good=tuple(sorted(true))
    wrong_mixed=next(p for p in pairs if len(set(p)&true)==1)
    wrong_both=next(p for p in pairs if set(p).issubset(false))
    need(len({good,wrong_mixed,wrong_both})==3,
         "Expected three independent opposite-window developer controls")
    return [
        ("PUBLIC_SOURCE_GEOMETRY_POSITIVE",good),
        ("PUBLIC_SOURCE_GEOMETRY_WRONG_MIXED",wrong_mixed),
        ("PUBLIC_SOURCE_GEOMETRY_WRONG_BOTH",wrong_both),
    ]


def _submitted_full(initial:bytes,guids:tuple[str,str])->str:
    root=etree.fromstring(initial)
    original={row.get("ifcGuid") for row in root[1]}
    need(len(guids)==2 and set(guids).issubset(original),
         "Only original source window IDs")
    for row in root[1]:
        row.set("present","false" if row.get("ifcGuid") in guids else "true")
    return etree.tostring(root,encoding="utf8",xml_declaration=True).decode("utf8")


def _submitted_compact(initial:bytes,guids:tuple[str,str])->str:
    root=etree.fromstring(initial)
    original={row.get("ifcGuid") for row in root}
    need(len(guids)==2 and set(guids).issubset(original),
         "Only original source complete compact IDs")
    for row in root:
        row.set("present","false" if row.get("ifcGuid") in guids else "true")
    return etree.tostring(root,encoding="utf8",xml_declaration=True).decode("utf8")


def _developer_native_python(indices:tuple[int,int])->str:
    """Author-free generic IfcOpenShell Python. No target GUIDs in repo."""
    need(len(indices)==2 and 0<=indices[0]<indices[1]<7,
         "Two source indices only")
    return (
        "import ifcopenshell.api\n"
        "windows=sorted(ifc.by_type('IfcWindow'),key=lambda w:w.GlobalId)\n"
        f"for index in {indices!r}:\n"
        "    win=windows[index]\n"
        "    opening=win.FillsVoids[0].RelatingOpeningElement\n"
        "    ifcopenshell.api.run('root.remove_product',ifc,product=win)\n"
        "    ifcopenshell.api.run('root.remove_product',ifc,product=opening)\n"
        "result={'left_windows':len(ifc.by_type('IfcWindow'))}\n"
        "commit()\n"
    )


def _evaluator_only_original_author_score(
    original:Path,candidate:Path,
)->dict:
    sys.path.insert(0,str(AUTHOR))
    try:
        module=importlib.import_module("data.tests.geometry_test_19")
        need(Path(module.__file__).resolve()==
             (AUTHOR/"data"/"tests"/f"{TASK}.py").resolve(),
             "Original pinned repository evaluator path mismatch")
        # The pinned original author evaluator for this particular task
        # references TWO WINDOW_GUIDS, but ONE does not exist among ANY
        # original source IFC Roots. Do not alter original author code or
        # invent the missing GUID, guess a score, or patch the evaluator.
        roots={x.GlobalId for x in ifcopenshell.open(str(original)).by_type("IfcRoot")}
        author_references=getattr(module,"WINDOW_GUIDS",None)
        need(isinstance(author_references,(tuple,list))
             and len(author_references)==2,
             "Pinned original author target reference shape changed")
        missing=sum(g not in roots for g in author_references)
        need(missing==1,"Pinned original author source-reference mismatch changed")
        try:
            values=module.execute_test(str(original),str(candidate),None)
        except RuntimeError as exc:
            # Do not persist/echo the sensitive target GUID in exception text.
            need("Instance with GlobalId" in str(exc)
                 and "not found" in str(exc),
                 "Unexpected original evaluator runtime error")
            return {
                "status":"BLOCKED_PINNED_AUTHOR_EVALUATOR_MISSING_ORIGINAL_SOURCE_GUID",
                "original_author_declared_window_target_count":2,
                "original_author_window_targets_absent_from_input_IFC":missing,
                "unmodified_original_evaluator_exception_type":"RuntimeError",
                "raw_exception_target_GUID_redacted":True,
                "author_repository_mean_boolean_score":None,
                "author_repository_boolean_metrics":None,
                "published_paper_official_grader_equivalence_verified":False,
            }
        need(isinstance(values,dict) and values
             and all(type(v) is bool for v in values.values()),
             "Original author repository evaluator metric unexpected")
        return {
            "status":"EVALUATOR_RETURNED_BOOLEAN_METRICS",
            "author_repository_mean_boolean_score":
                round(sum(values.values())/len(values),6),
            "author_repository_boolean_metrics":dict(sorted(values.items())),
            "published_paper_official_grader_equivalence_verified":False,
        }
    finally:
        sys.path.remove(str(AUTHOR))


def _native_verified_digest(original:Path,session):
    need(session.output_ifc is not None,
         "No real original IFC committed")
    result=independent_two_window_native_scope_v060(
        original,session.output_ifc,source_sha=SOURCE_SHA)
    need(result["status"]==
         "V060_SOURCE_NATIVE_TWO_WINDOWS_OPENINGS_SCOPE_AND_SCHEMA_PASS",
         "Original-native source scope/schema gate blocked")
    return canonical_original_native_semantic_digest_v060(session.output_ifc)


def build_report()->dict:
    need(file_hash(PARENT_REPORT)==PARENT_REPORT_SHA
         and file_hash(PREV_HOLDOUT)==PREV_HOLDOUT_SHA,
         "Prior frozen source-native and prospective holdout evidence drifted")
    old=json.loads(PARENT_REPORT.read_text(encoding="utf8"))
    frozen=json.loads(PREV_HOLDOUT.read_text(encoding="utf8"))
    need(old["v059_source_native_task_scope_added"]==["topological_test_18"]
         and sorted(frozen["prospective_six_source_heldout_task_ids"])==
             FIXED_HOLDOUT
         and old["actual_model_generated_trials"]==0,
         "Prior original development scope/holdout changed")
    rights=assert_original_source_rights_unchanged_v057()
    need(rights["status"]=="BLOCKED_NO_MODEL_PROVIDER_TRIAL",
         "Original data/model rights hard gate changed")
    rows={r["test_id"]:r for r in public_45(AUTHOR,DATA)}
    need(len(rows)==45,"Original public task population drifted")
    row=rows[TASK]
    source=DATA/"ifc"/row["original_source_ifc_relpath"]
    need(file_hash(source)==SOURCE_SHA and
         row["original_ifc_sha256"]==SOURCE_SHA,
         "Original heldout window IFC changed")
    model=_source(source,source_sha=SOURCE_SHA)
    original_window_sorted=sorted(w.GlobalId for w in model.by_type("IfcWindow"))
    need(len(original_window_sorted)==7,"Seven original public source windows required")
    source_full=source_full_state_v060(source,source_sha=SOURCE_SHA)
    source_compact=compact_source_state_v060(source,source_sha=SOURCE_SHA)
    controls=selected_three_developer_pairs_v060(
        source,row["public_question"])
    results=[]
    with TemporaryDirectory(prefix="v060-GENUINE-LINUX-DOCKER-DEVELOPER-") as scratch:
        root=Path(scratch)
        for index,(label,guids) in enumerate(controls):
            case=root/str(index)
            D=DirectFullState060(source,case/"D")
            M=DirectManagedState060(source,case/"M")
            I=LiveDockerPython060(source,case/"I")
            reads=[s.call("read_building_xml",{"query":"source"}) for s in (D,M,I)]
            need(all(r["status"]=="ok" for r in reads)
                 and all(r["xml"]==reads[0]["xml"] for r in reads)
                 and reads[0]["xml"].encode("utf8")==source_full,
                 "Exact same source input not given to three actual arms")
            full=_submitted_full(source_full,guids)
            compact=_submitted_compact(source_compact,guids)
            d=D.call("submit_building_xml",{"xml_text":full})
            m=M.call("submit_managed_final_state",{"xml_text":compact})
            indices=tuple(sorted(original_window_sorted.index(g) for g in guids))
            code=_developer_native_python(indices)
            i=I.call("execute_ifc_code",{"code":code})
            need(d["status"]==m["status"]==i["status"]=="ok"
                 and i["python_execution_attested"] is True
                 and i["actual_linux_sandbox_backend"]=="linux_docker_sandbox"
                 and d["removed_native_windows"]==
                     m["removed_native_windows"]==
                     i["removed_native_windows"]==2
                 and d["introduced_schema_error_count"]==
                     m["introduced_schema_error_count"]==
                     i["introduced_schema_error_count"]==0,
                 "Actual original IFC native D/I Windows/Opening commit rejected")
            d_sem=_native_verified_digest(source,D)
            m_sem=_native_verified_digest(source,M)
            i_sem=_native_verified_digest(source,I)
            need(d_sem==m_sem==i_sem,
                 "Real D-full/managed/Docker I original-native IFC SEMANTICS differ")
            need(D.current_xml==M.current_xml==full.encode("utf8"),
                 "Full-source reconstructed final-state D expressions differ")
            grades={
                "D_FULL":_evaluator_only_original_author_score(
                    source,D.output_ifc),
                "D_MANAGED":_evaluator_only_original_author_score(
                    source,M.output_ifc),
                "I_REAL_DOCKER":_evaluator_only_original_author_score(
                    source,I.output_ifc),
            }
            need(grades["D_FULL"]==grades["D_MANAGED"]==
                 grades["I_REAL_DOCKER"],
                 "Original author evaluator metrics differ across arms")
            results.append({
                "developer_only_public_source_geometry_class":label,
                "window_pair_original_target_GUIDs_in_report":None,
                "original_native_window_pair_SOURCE_INDEX_in_report":None,
                "all_three_native_Ifc_semantic_digest_SHA256":d_sem,
                "native_IFC_raw_binary_SHA_identical_claim":False,
                "real_ifc_windows_remaining_per_arm":5,
                "real_ifc_openings_remaining_per_arm":5,
                "D_full_final_state_UTF8_bytes":len(full.encode("utf8")),
                "D_managed_final_state_UTF8_bytes":len(compact.encode("utf8")),
                "I_developer_only_python_UTF8_bytes":len(code.encode("utf8")),
                "IFC_source_scope_oracle_D_MANAGED_I":True,
                "native_IFC_schema_introduced_errors":0,
                "author_repo_metric_evaluator_only":grades["D_FULL"],
                "actual_genuine_isolated_Docker_Python_executed":True,
                "actual_LLM_model_authored_code":False,
            })
            need(file_hash(source)==SOURCE_SHA,
                 "Original public IFC changed after actual D/I runs")
        # Adversarial actual Docker: low-level removal leaves orphaned
        # opening/relationship, must fail native scope (regardless of
        # what the worker itself thinks of commit()).
        bad=LiveDockerPython060(source,root/"bad_raw")
        raw=bad.call("execute_ifc_code",{"code":(
            "for w in ifc.by_type('IfcWindow')[:2]:\n"
            "    ifc.remove(w)\n"
            "result={'raw_unlinked_deleted_windows':2}\n"
            "commit()\n"
        )})
        need(raw["status"]=="error"
             and raw["native_ifc_committed"] is False
             and bad.output_ifc is None,
             "Actually executed invalid raw Docker removal incorrectly committed")
        # Real Docker valid first, then a second native edit deletes extra
        # windows from last-good IFC. Must roll back to previous exact SHA.
        second=LiveDockerPython060(source,root/"good_then_wrong")
        first=second.call("execute_ifc_code",{
            "code":_developer_native_python((0,1))})
        need(first["status"]=="ok" and second.output_ifc is not None,
             "Initial actual Docker Windows deletion did not commit")
        preserved_sha=file_hash(second.output_ifc)
        # Source original still has 7 windows; now 5 remain, so deleting
        # two more windows violates exactly-2-removed source-native scope.
        invalid=second.call("execute_ifc_code",{"code":(
            "import ifcopenshell.api\n"
            "windows=sorted(ifc.by_type('IfcWindow'),key=lambda w:w.GlobalId)\n"
            "for index in (0,1):\n"
            "    w=windows[index]\n"
            "    op=w.FillsVoids[0].RelatingOpeningElement\n"
            "    ifcopenshell.api.run('root.remove_product',ifc,product=w)\n"
            "    ifcopenshell.api.run('root.remove_product',ifc,product=op)\n"
            "commit()\n"
        )})
        need(invalid["status"]=="error"
             and invalid["native_ifc_committed"] is False
             and file_hash(second.output_ifc)==preserved_sha,
             "Actual Docker invalid second deletion modified last-good IFC")
        droll=DirectFullState060(source,root/"D_rollback")
        good=droll.call("submit_building_xml",{
            "xml_text":_submitted_full(source_full,controls[0][1])})
        need(good["status"]=="ok","D source-native baseline failed")
        before_xml=droll.current_xml
        before_sha=file_hash(droll.output_ifc)
        node=etree.fromstring(before_xml)
        node[1].remove(node[1][0])
        failed=droll.call("submit_building_xml",{
            "xml_text":etree.tostring(node,encoding="utf8").decode("utf8")})
        need(failed["status"]=="error"
             and droll.current_xml==before_xml
             and file_hash(droll.output_ifc)==before_sha,
             "D source last-good native and complete XML not preserved")
    need(len(results)==3
         and len({x["developer_only_public_source_geometry_class"]
                  for x in results})==3
         and all(x["actual_genuine_isolated_Docker_Python_executed"]
                 for x in results),
         "Three source-derived positive/negative real Docker controls missing")
    need(file_hash(source)==SOURCE_SHA,"Original source mutated")
    return {
        "status":"V060_G19_FIRST_ORIGINAL_WINDOW_OPENING_TWO_DELETE_D_FULL_D_MANAGED_REAL_DOCKER_I_PASS",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/235",
        "parent_v059_exact_HEAD":PARENT_HEAD,
        "parent_v059_frozen_report_SHA256":PARENT_REPORT_SHA,
        "original_v058_six_holdout_selection_SHA256":PREV_HOLDOUT_SHA,
        "fixed_six_original_source_tasks_unchanged":FIXED_HOLDOUT,
        "v060_new_original_source_native_task_added":[TASK],
        "v059_existing_developer_supported_tasks_unchanged":
            sorted(NATIVE_DEVELOPER_SUPPORTED_PRIOR),
        "all_current_six_candidates_native_developer_supported":
            sorted(CURRENT_ADMITTED),
        "remaining_six_source_tasks_not_yet_native_admitted":
            sorted(set(FIXED_HOLDOUT)-CURRENT_ADMITTED),
        "current_6_original_task_specific_native_developer_supported":6,
        "remaining_other_original_edit_tasks_not_implemented":39,
        "original_45_task_population_size":45,
        "original_31_unique_IFC_input_sources":31,
        "original_question_hash_SHA256":row["public_question_sha256"],
        "original_native_source_IFC_SHA256":SOURCE_SHA,
        "original_source_native_IFC_schema":"IFC4X3",
        "original_author_repository_evaluator_module_SHA256":
            file_hash(AUTHOR/"data"/"tests"/f"{TASK}.py"),
        "model_facing_original_full_source_read_XML_UTF8_bytes":len(source_full),
        "original_compact_full_managed_source_state_UTF8_bytes":len(source_compact),
        "model_facing_source_read_identical_D_I":True,
        "model_facing_complete_original_seven_Window_Guids":True,
        "Native_IfcWindow_original_count":7,
        "Native_IfcOpeningElement_original_count":7,
        "original_public_question_source_opposite_window_predicate_true_count":2,
        "original_public_question_source_opposite_window_predicate_false_count":5,
        "public_question_source_physical_predicate_not_author_GT":True,
        "developer_original_window_pair_test_cases":3,
        "actual_D_FULL_ifc_native_developer_cases":3,
        "actual_D_MANAGED_ifc_native_developer_cases":3,
        "actual_real_pinned_linux_Docker_I_native_developer_cases":3,
        "real_original_window_and_linked_opening_candidates_admitted":9,
        "canonical_IFC_semantic_digest_equal_D_MANAGED_I":True,
        "raw_native_IFC_SHA256_not_stable_due_to_IfcOwnerHistory_real_timestamp_and_SET_order":True,
        "the_original_source_schema_delta_introduced_errors":0,
        "independent_all_IFC_other_entities_unchanged":True,
        "author_repository_score_D_I_UNAVAILABLE_due_to_original_source_reference_error":True,
        "original_author_declares_two_window_target_GUIDs_but_one_absent_from_original_IFC":True,
        "original_author_evaluator_all_three_arms_consistently_BLOCKED":True,
        "original_author_evaluator_source_and_GT_not_modified":True,
        "author_repository_official_paper_revision_verified":False,
        "source_native_geometry_classification_and_grader_distinct":True,
        "raw_unlinked_Docker_two_Window_remove_rejected":True,
        "true_pinned_Docker_good_then_bad_last_IFC_sha_unchanged":True,
        "D_complete_bad_after_good_XML_and_last_native_ifc_unchanged":True,
        "v058_six_holdout_candidate_no_longer_wholly_dev_unseen":True,
        "this_window_source_exposed_to_developer_control":True,
        "original_IFC_uploads_to_model_provider":0,
        "model_generated_trials":0,
        "paid_provider_model_calls":0,
        "approved_source_rights_model_provider_transfer":False,
        "approved_provider_model_snapshot":None,
        "approved_budget_USD":None,
        "published_paper_official_model_score":None,
        "three_evaluator_only_developer_source_pair_controls":results,
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--write",action="store_true")
    group.add_argument("--check",action="store_true")
    args=p.parse_args()
    data=canonical(build_report())
    if args.write:
        with REPORT.open("xb") as f:
            f.write(data)
    else:
        need(REPORT.is_file() and not REPORT.is_symlink()
             and REPORT.read_bytes()==data,
             "Real D/I native Docker/author metric report replay not byte identical")
    print("V060_GEOMETRY19_D_FULL_MANAGED_REAL_DOCKER_I=PASS "
          "ACTUAL_NATIVE_IFCS=9/9 GENUINE_DOCKER=3/3 "
          "MODEL=0 PAID=0 FROZEN_SEMANTIC_REPORT_SHA256="+
          sha256(data).hexdigest())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
