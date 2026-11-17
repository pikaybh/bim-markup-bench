"""v0.53 EVALUATOR-ONLY original-author task source attribution and blind arm check.

The author-origin executable task tests are imported exclusively in this
OFFLINE EVALUATOR, never in a D/I tool session, agent prompt, mounted scratch
folder or provider request. This script does not invoke the original author's
benchmark pipeline or a model. Frozen original tasks/inputs never change.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from src.runtime.experimental_v45_original_native_mutations import project_original_native_mutations_v045
from src.runtime.experimental_v50_original_declarative_state import project_original_declarative_state_v050
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v050_direct_original_state_session import DirectOriginalStateSession050
from tools.audit_bibimbap_v050_declarative_state import developer_control_to_declarative_state
from tools.audit_bibimbap_v045_original4_native_mutations import make_illustrative_plan
from tools.audit_bibimbap_v048_original4_semantic_controls import positive_developer_source_edit
from tools.bibimbap_v051_trusted_developer_python_controls import make_independent_native_python_control
from tools.bibimbap_v051_independent_native_python_oracle import verify_independent_native_python_v051
from tools.bibimbap_v048_independent_original4_semantic_oracle import evaluate_original_semantic048

ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v053_author_origin_four_original_score_20261118.json"
TASKS=("geometry_test_14","geometry_test_15","topological_test_11","topological_test_17")
EXPECTED_AUTHOR_HEAD="667004e16bd38fd7d538bcee56191465429fd975"
V052_REPORT_SHA="83aaebf382ddad136ee55ff4e3b54559e6630b64587c4665f447bb12baffcc31"
AUTHOR_RELATED=("benchmark.py","scripts/eval_cache.py",
                "data/tests/integrity_utils.py","data/tests/delete_integrity.py",
                *(f"data/tests/{task}.py" for task in TASKS))


def need(condition: bool,message:str)->None:
    if not condition:
        raise AssertionError(message)


def read_only_author_origin() -> dict:
    need(AUTHOR.is_dir() and DATA.is_dir() and not AUTHOR.is_symlink(),
         "Original-author checkout or source IFC data missing")
    head=subprocess.run(["git","-C",str(AUTHOR),"rev-parse","HEAD"],
                        capture_output=True,text=True,encoding="utf8",
                        timeout=10,check=True).stdout.strip()
    need(head==EXPECTED_AUTHOR_HEAD,"Original author code HEAD changed")
    files={}
    for rel in AUTHOR_RELATED:
        p=AUTHOR/rel
        need(p.is_file() and not p.is_symlink(),"Missing original author test source")
        raw=p.read_bytes()
        need(len(raw)>90,"Suspicious original author test source")
        files[rel]={"sha256":sha256(raw).hexdigest(),
                    "bytes":len(raw)}
    source=(AUTHOR/"benchmark.py").read_text(encoding="utf8")
    need('metrics = test.execute_test(ifc_path, edited_ifc_path, model_output)' in source
         and "score = sum(metrics.values()) / len(metrics) if metrics else 0" in source,
         "Original author benchmark scoring formula changed")
    for task in TASKS:
        tree=ast.parse((AUTHOR/f"data/tests/{task}.py").read_text(encoding="utf8"))
        functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
        need("execute_test" in functions
             and len(functions["execute_test"].args.args)==3,
             "Original task evaluator callable contract changed")
    # README advertises LICENSE; bundled checkout does not contain it. Never
    # infer public artifact redistribution rights from this source snapshot.
    return {
        "original_author_git_head":head,
        "original_author_test_entrypoint":"data.tests.<task_id>.execute_test",
        "author_benchmark_entrypoint":"benchmark.py",
        "author_benchmark_score_formula":
            "mean(float(metric) for metric in execute_test(...).values())",
        "evaluator_files_sha256":files,
        "author_checkout_license_file_present":(AUTHOR/"LICENSE").is_file(),
        "license_and_IFC_data_redistribution_approved":False,
        "evaluation_invoked_only_outside_model_sandbox":True,
        "published_paper_score_parity":None,
    }


def _get_target_count_from_private_author_test(module_path:Path)->int:
    """Evaluator-only opaque count. No private target GUID ever emitted."""
    tree=ast.parse(module_path.read_text(encoding="utf8"))
    fn=next(n for n in tree.body
            if isinstance(n,ast.FunctionDef) and n.name=="execute_test")
    for assign in fn.body:
        if (isinstance(assign,ast.Assign)
            and any(isinstance(target,ast.Name)
                    and target.id=="target_column_guids"
                    for target in assign.targets)):
            return len(ast.literal_eval(assign.value))
    raise ValueError("Original deletion task target declaration not found")


def _deletion_integrity_diagnostic(original:Path,edited:Path) -> dict:
    # This block is strictly the private developer/evaluator namespace.
    import ifcopenshell
    from data.tests import delete_integrity,integrity_utils
    task_path=AUTHOR/"data/tests/topological_test_17.py"
    target_count=_get_target_count_from_private_author_test(task_path)
    old=ifcopenshell.open(str(original))
    new=ifcopenshell.open(str(edited))
    roots_before={x.GlobalId:x for x in old.by_type("IfcRoot")}
    roots_after={x.GlobalId:x for x in new.by_type("IfcRoot")}
    # Infer target GUIDs ONLY from original evaluator source, not new geometry.
    # Never return these values, or source plan, to report/model-facing tools.
    tree=ast.parse(task_path.read_text(encoding="utf8"))
    fn=next(n for n in tree.body
            if isinstance(n,ast.FunctionDef) and n.name=="execute_test")
    targets=next(ast.literal_eval(n.value) for n in fn.body
                if isinstance(n,ast.Assign) and any(
                    isinstance(x,ast.Name) and x.id=="target_column_guids"
                    for x in n.targets))
    need(len(targets)==target_count==5,"Original source task target set changed")
    groups={}
    for category in ("wall_connections_deleted","spatial_containment_deleted",
                     "openings_deleted","aggregations_deleted"):
        values=[getattr(delete_integrity,category)(old,new,g)
                for g in sorted(targets)]
        groups[category]={"passed":sum(bool(x) for x in values),
                          "total":len(values)}
    missing=set(roots_before)-set(roots_after)
    non_target=set(missing)-set(targets)
    return {
        "original_author_target_count_NOT_IDS":target_count,
        "author_delete_subtests_only_counts":groups,
        "author_non_target_elements_unchanged":
            integrity_utils.non_target_elements_unchanged(
                old,new,list_of_targets=sorted(targets)),
        "author_non_target_root_cascade_missing_by_IFC_class":
            dict(sorted(Counter(roots_before[g].is_a()
                                for g in non_target).items())),
        "new_IfcRoot_count":len(set(roots_after)-set(roots_before)),
        "deleted_target_IFC_Root_count":len(missing & set(targets)),
        "original_input_sha256":file_hash(original),
        "edited_ifc_sha256":file_hash(edited),
    }


def build_report()->dict:
    need(file_hash(ROOT/"reports"/
        "bibimbap_v052_original4_live_docker_python_attestation_20261118.json")
        ==V052_REPORT_SHA,"Frozen v0.52 live Docker evidence changed")
    provenance=read_only_author_origin()
    registry={row["test_id"]:row for row in public_45(AUTHOR,DATA)}
    need(len(registry)==45 and len({r["original_ifc_sha256"]
                                    for r in registry.values()})==31
         and Counter(r["crud"] for r in registry.values())==
             {"create":15,"update":15,"delete":15},
         "Original 45/31 public benchmark population changed")
    old_path=list(sys.path)
    sys.path.insert(0,str(AUTHOR))
    records=[]
    diagnostic=None
    try:
        with TemporaryDirectory(prefix="v053-private-evaluator-only-") as temp:
            workspace=Path(temp)
            for i,tid in enumerate(TASKS):
                task=registry[tid]
                path=DATA/"ifc"/task["original_source_ifc_relpath"]
                source_sha=task["original_ifc_sha256"]
                need(file_hash(path)==source_sha,"Original public source changed")
                author_eval=importlib.import_module("data.tests."+tid)
                need(Path(author_eval.__file__).resolve()==
                     (AUTHOR/f"data/tests/{tid}.py").resolve(),
                     "Author scorer import shadowed or model-visible")
                original_D=project_original_declarative_state_v050(
                    path,source_sha=source_sha).xml
                original_private_typed=project_original_native_mutations_v045(
                    path,source_sha=source_sha).xml
                for positive in (True,False):
                    expected="positive" if positive else "negative"
                    if positive:
                        fixture=positive_developer_source_edit(
                            original_private_typed,path,tid,task["public_question"])
                    else:
                        fixture=make_illustrative_plan(
                            original_private_typed,tid,path)
                    edited_D=developer_control_to_declarative_state(
                        original_D,fixture)
                    s=DirectOriginalStateSession050(
                        path,workspace/f"d_{i}_{expected}")
                    result=s.call("submit_building_xml",{
                        "xml_text":edited_D.decode("utf8")})
                    need(result["status"]=="ok" and s.output_ifc is not None,
                         "D declarative state compiler failed source-native edit")
                    direct=workspace/f"independent_I_{i}_{expected}.ifc"
                    make_independent_native_python_control(
                        path,direct,original_sha=source_sha,task_id=tid,
                        public_question=task["public_question"],positive=positive)
                    native=verify_independent_native_python_v051(
                        path,direct,source_sha=source_sha,task_id=tid)
                    need(native["status"]==
                         "V051_INDEPENDENT_SOURCE_NATIVE_IFC_SCOPE_ORACLE_PASS",
                         "Independently authored I-native candidate invalid")
                    for arm,candidate in (("D_STATE",s.output_ifc),
                                          ("I_NATIVE_DEVELOPER",direct)):
                        research=evaluate_original_semantic048(
                            path,candidate,original_sha=source_sha,
                            task_id=tid,public_question=task["public_question"])
                        need(research[
                             "candidatePassesIndependentResearchPhysicalPredicate"]
                             ==positive,
                             "Original independent task research predicate changed")
                        metrics=author_eval.execute_test(
                            str(path),str(candidate),None)
                        need(isinstance(metrics,dict) and bool(metrics)
                             and all(type(x) is bool for x in metrics.values()),
                             "Original author task did not return Boolean metrics")
                        score=sum(metrics.values())/len(metrics)
                        need(0.0<=score<=1.0,"Invalid author-origin score")
                        records.append({
                            "original_task_id":tid,
                            "original_source_ifc_sha256":source_sha,
                            "public_question_sha256":
                                task["public_question_sha256"],
                            "arm":"D_STATE_DEVELOPER_CONTROL" if arm=="D_STATE"
                                  else "I_NATIVE_DEVELOPER_CONTROL",
                            "fixture":expected+"_SOURCE_DERIVED_NOT_LLM",
                            "candidate_IFC_sha256":file_hash(candidate),
                            "source_original_IFC_unchanged":
                                file_hash(path)==source_sha,
                            "independent_research_physical_semantic_pass":positive,
                            "original_author_repo_test_boolean_metrics":
                                dict(sorted(metrics.items())),
                            "original_author_repo_test_mean_score":score,
                            "original_paper_official_score":None,
                            "no_paid_or_model_generated_inference":True,
                        })
                    if tid=="topological_test_17" and positive:
                        diagnostic=_deletion_integrity_diagnostic(
                            path,direct)
    finally:
        sys.path[:]=old_path
    need(len(records)==16 and diagnostic is not None,
         "16 source-native D/I developer evaluations missing")
    return {
        "status":"V053_AUTHOR_CODE_REPLAY_SUCCEEDED_LLM_LAUNCH_BLOCKED",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/221",
        "frozen_base_v052_commit":
            "a0ef25fad9e86c32661344a45cee0c15a47b675a",
        "selected_exploratory_original_four_tasks":4,
        "original_full_edit_task_population":45,
        "original_full_unique_input_IFCs":31,
        "other_41_tasks_NOT_attempted":41,
        "author_scorer_provenance":provenance,
        "author_origin_task_evaluations_on_developer_native_IFCs":len(records),
        "original_author_published_paper_score_equivalence":None,
        "topological17_IfcOpenShell_cascade_scoring_diagnostic":diagnostic,
        "author_metrics_not_equivalent_to_research_physical_predicate":True,
        "actual_LLM_trials":0,
        "billable_inference_calls":0,
        "official_published_paper_score":None,
        "frozen_v052_SHA256":V052_REPORT_SHA,
        "rights_to_redistribute_original_tests_or_IFCs":False,
        "records":records,
    }


def canonical(data:dict)->bytes:
    return (json.dumps(data,sort_keys=True,ensure_ascii=False,
                       indent=2)+"\n").encode("utf8")


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write",action="store_true")
    modes.add_argument("--check",action="store_true")
    args=parser.parse_args()
    data=canonical(build_report())
    if args.write:
        with REPORT.open("xb") as f:
            f.write(data)
    else:
        need(REPORT.is_file() and REPORT.read_bytes()==data,
             "Frozen original-author code native D/I scorer evidence changed")
    result=json.loads(data)
    print("V053_AUTHOR_ORIGIN_FOUR=PASS EVALUATIONS=16 "
          "ORIGINAL_PUBLISHED_SCORE=NULL LLM_TRIALS=0 "
          "SHA256="+sha256(data).hexdigest())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
