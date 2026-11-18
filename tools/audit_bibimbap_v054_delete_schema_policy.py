"""v0.54 independent IFC4X3 schema-delta validation + author deletion-policy audit.

Evaluator-only trusted developer controls. NO MODEL, NO SCORE OVERRIDES, NO GT.
Source IFC, original author tests, previous reports are read-only.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from hashlib import sha256
import importlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.validate

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v051_independent_native_python_oracle import (
    verify_independent_native_python_v051,
)
from tools.bibimbap_v051_trusted_developer_python_controls import (
    make_independent_native_python_control,
)
from tools.bibimbap_v050_direct_original_state_session import (
    DirectOriginalStateSession050,
)
from tools.audit_bibimbap_v050_declarative_state import (
    developer_control_to_declarative_state,
)
from tools.audit_bibimbap_v048_original4_semantic_controls import (
    positive_developer_source_edit,
)
from src.runtime.experimental_v50_original_declarative_state import (
    project_original_declarative_state_v050,
)
from src.runtime.experimental_v45_original_native_mutations import (
    project_original_native_mutations_v045,
)
from tools.bibimbap_v048_independent_original4_semantic_oracle import (
    evaluate_original_semantic048,
)


ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
AUTHOR_HEAD="667004e16bd38fd7d538bcee56191465429fd975"
V053_AUTHOR_SHA="40742725e59f7b0909f2d1ff061a7d68bcfcf1f35da829c3d15d0624928366e4"
V053_PREREG_SHA="600a951bfb0733a79f09e9db43376526ceaa9e1a66cc3e800e2ca00601862524"
TASK_ID="topological_test_17"
REPORT=ROOT/"reports"/"bibimbap_v054_delete_source_schema_policy_20261118.json"


class SchemaValidationBoundaryError(ValueError):
    pass


def require(truth:bool, message:str)->None:
    if not truth:
        raise SchemaValidationBoundaryError(message)


def original_author_targets_evaluator_only()->set[str]:
    """Never serialize IDs or expose this function in a model-facing session."""
    path=AUTHOR/"data/tests/topological_test_17.py"
    tree=ast.parse(path.read_text(encoding="utf8"))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)
            and n.name=="execute_test")
    items=[ast.literal_eval(n.value) for n in fn.body
           if isinstance(n,ast.Assign) and any(
               isinstance(x,ast.Name) and x.id=="target_column_guids"
               for x in n.targets)]
    require(len(items)==1 and isinstance(items[0],set)
            and len(items[0])==5,"Original author delete targets changed")
    return items[0]


def _source_row()->dict:
    tasks={r["test_id"]:r for r in public_45(AUTHOR,DATA)}
    require(len(tasks)==45 and
            len({r["original_ifc_sha256"] for r in tasks.values()})==31,
            "Original published 45/31 denominator changed")
    return tasks[TASK_ID]


def _file_ifc_error_counter(path:Path)->Counter:
    """Actual installed IfcOpenShell IFC4X3 cardinality/type validator.

    Pre-existing source-schema defects remain visible but cannot be used to
    reject a legal edit solely because the original author input has them.
    Newly introduced schema errors are rejected by multiset subtraction.
    """
    require(path.is_file() and not path.is_symlink(),
            "Untrusted IFC path absent/symlinked")
    logger=ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(str(path),logger,express_rules=False)
    result=Counter()
    for item in logger.statements:
        require(item.get("level")=="error","Unclassified IFC schema validation")
        attribute=str(item.get("attribute") or "")
        msg=str(item.get("message") or "")
        kind=str(item.get("type") or "")
        # Do not emit entity STEP ids, GlobalIds or any source answer.
        result[(kind,attribute,sha256(msg.encode("utf8")).hexdigest())]+=1
    return result


def native_ifc_schema_delta_v054(original_ifc:Path,candidate_ifc:Path,
                                *,expected_source_sha:str)->dict:
    """Non-mutating real IFC schema gate: source defects are not candidate defects."""
    require(file_hash(original_ifc)==expected_source_sha,
            "Original IFC source SHA mismatch")
    baseline=_file_ifc_error_counter(original_ifc)
    produced=_file_ifc_error_counter(candidate_ifc)
    introduced=produced-baseline
    resolved=baseline-produced
    attribute_count=Counter()
    for (_kind,attribute,_digest),v in introduced.items():
        attribute_count[attribute]+=v
    return {
        "status":"PASS_NO_NEW_IFC_SCHEMA_ERRORS" if not introduced
                 else "REJECT_NEW_IFC_SCHEMA_ERRORS",
        "source_existing_schema_error_count":sum(baseline.values()),
        "candidate_schema_error_count":sum(produced.values()),
        "introduced_schema_error_count":sum(introduced.values()),
        "resolved_schema_error_count":sum(resolved.values()),
        "introduced_schema_error_by_attribute":dict(sorted(attribute_count.items())),
        "original_input_hash_unchanged":file_hash(original_ifc)==expected_source_sha,
        "source_is_IFC4X3":ifcopenshell.open(str(original_ifc)).schema=="IFC4X3",
        "output_is_IFC4X3":ifcopenshell.open(str(candidate_ifc)).schema=="IFC4X3",
    }


def strict_native_scope_plus_schema_v054(source:Path,candidate:Path,
                                         *,source_sha:str,task_id:str)->dict:
    """Fail closed even if historical source-physical scope oracle passes."""
    need=native_ifc_schema_delta_v054(
        source,candidate,expected_source_sha=source_sha)
    if need["status"]!="PASS_NO_NEW_IFC_SCHEMA_ERRORS":
        return {**need,"native_scope_status":"NOT_SUFFICIENT_NEW_SCHEMA_ERRORS",
                "admitted":False}
    scope=verify_independent_native_python_v051(
        source,candidate,source_sha=source_sha,task_id=task_id)
    okay=scope["status"]=="V051_INDEPENDENT_SOURCE_NATIVE_IFC_SCOPE_ORACLE_PASS"
    return {**need,"native_scope_status":scope["status"],
            "admitted":okay}


def _target_relation_topology(original_ifc:Path,targets:set[str])->dict:
    file=ifcopenshell.open(str(original_ifc))
    require(file.schema=="IFC4X3" and
            all(file.by_guid(g).is_a("IfcColumn") for g in targets),
            "Source IFC4X3 deletion targets invalid")
    result={}
    for kind in ("IfcRelDefinesByProperties","IfcRelDefinesByType",
                 "IfcRelContainedInSpatialStructure"):
        touches=[]
        for entity in file.by_type(kind):
            related=getattr(entity,"RelatedObjects",None)
            if related is None:
                related=getattr(entity,"RelatedElements",None)
            guids={r.GlobalId for r in (related or ())
                   if getattr(r,"GlobalId",None)}
            matched=guids&targets
            if matched:
                touches.append((len(matched),len(guids-matched)))
        result[kind]={
            "relations_with_deleted_columns":len(touches),
            "relations_exclusively_related_to_deleted_columns":
                sum(unrelated==0 for _hits,unrelated in touches),
            "relations_with_surviving_shared_objects":
                sum(unrelated>0 for _hits,unrelated in touches),
            "deleted_reference_counts":sum(hits for hits,_ in touches),
        }
    return result


def _make_exploratory_native_candidates(source:Path,sha:str,
                                         question:str,folder:Path)->dict[str,Path]:
    # Source-derived developer control with *public* question only.
    good_I=folder/"api_delete.ifc"
    make_independent_native_python_control(
        source,good_I,original_sha=sha,task_id=TASK_ID,
        public_question=question,positive=True)
    x=project_original_native_mutations_v045(source,source_sha=sha).xml
    edit=positive_developer_source_edit(x,source,TASK_ID,question)
    origin=project_original_declarative_state_v050(source,source_sha=sha).xml
    target_xml=developer_control_to_declarative_state(origin,edit)
    direct=DirectOriginalStateSession050(source,folder/"D_true_final_state")
    result=direct.call("submit_building_xml",{"xml_text":target_xml.decode("utf8")})
    require(result["status"]=="ok" and direct.output_ifc is not None,
            "True D-state original native IFc developer edit failed")
    targets=original_author_targets_evaluator_only()
    file=ifcopenshell.open(str(source))
    for guid in sorted(targets):
        file.remove(file.by_guid(guid))
    raw=folder/"raw_delete_invalid.ifc"
    file.write(str(raw))
    require(file_hash(source)==sha,"Immutable original author source modified")
    return {"I_NATIVE_API":good_I,
            "D_STATE":direct.output_ifc,
            "RAW_REMOVE_INVALID_NEGATIVE_CONTROL":raw}


def _author_metrics_private_eval(source:Path,candidate:Path)->dict:
    sys.path.insert(0,str(AUTHOR))
    try:
        scorer=importlib.import_module("data.tests.topological_test_17")
        require(Path(scorer.__file__).resolve()==
                (AUTHOR/"data/tests/topological_test_17.py").resolve(),
                "Scorer module import was shadowed")
        metrics=scorer.execute_test(str(source),str(candidate),None)
        require(isinstance(metrics,dict) and len(metrics)==2
                and all(type(v) is bool for v in metrics.values()),
                "Unexpected original author deletion metrics")
        return {"author_repo_score":sum(metrics.values())/len(metrics),
                "boolean_metrics":dict(sorted(metrics.items()))}
    finally:
        sys.path.remove(str(AUTHOR))


def build_report()->dict:
    require(file_hash(ROOT/"reports"/
        "bibimbap_v053_author_origin_four_original_score_20261118.json")
        ==V053_AUTHOR_SHA,"Frozen prior original author scorer evidence changed")
    require(file_hash(ROOT/"reports"/
        "bibimbap_v053_primary_DI_exploratory_prereg_candidate_20261118.json")
        ==V053_PREREG_SHA,"Frozen primary D/I pre-reg candidate changed")
    row=_source_row()
    source=DATA/"ifc"/row["original_source_ifc_relpath"]
    source_sha=row["original_ifc_sha256"]
    require(file_hash(source)==source_sha,"Original IFC source changed")
    targets=original_author_targets_evaluator_only()
    rel=_target_relation_topology(source,targets)
    require(rel["IfcRelDefinesByProperties"][
        "relations_exclusively_related_to_deleted_columns"]==15
        and rel["IfcRelDefinesByType"][
            "relations_exclusively_related_to_deleted_columns"]==5,
        "Source exclusive target relation structure changed")
    output={}
    with TemporaryDirectory(prefix="v054-private-schema-negative-") as tmp:
        candidates=_make_exploratory_native_candidates(
            source,source_sha,row["public_question"],Path(tmp))
        for name,path in candidates.items():
            schema=native_ifc_schema_delta_v054(
                source,path,expected_source_sha=source_sha)
            scope=verify_independent_native_python_v051(
                source,path,source_sha=source_sha,task_id=TASK_ID)
            combined=strict_native_scope_plus_schema_v054(
                source,path,source_sha=source_sha,task_id=TASK_ID)
            physical=evaluate_original_semantic048(
                source,path,original_sha=source_sha,task_id=TASK_ID,
                public_question=row["public_question"])
            metrics=_author_metrics_private_eval(source,path)
            output[name]={
                "real_native_IFC4X3_SHA256":file_hash(path),
                "source_native_physical_oracle":
                    scope["status"],
                "research_physical_task_predicate":
                    physical["candidatePassesIndependentResearchPhysicalPredicate"],
                "real_IFC_schema_delta":schema,
                "augmented_strict_native_admission":combined["admitted"],
                "original_author_repository_metric":
                    metrics,
                "actual_LLM_generated":False,
            }
        for key in ("D_STATE","I_NATIVE_API"):
            item=output[key]
            require(item["augmented_strict_native_admission"]
                    and item["real_IFC_schema_delta"][
                        "introduced_schema_error_count"]==0
                    and item["original_author_repository_metric"][
                        "author_repo_score"]==0.5,
                    "Correct IFC native API/D-state should retain scorer caveat")
        raw=output["RAW_REMOVE_INVALID_NEGATIVE_CONTROL"]
        require(raw["source_native_physical_oracle"]==
                "V051_INDEPENDENT_SOURCE_NATIVE_IFC_SCOPE_ORACLE_PASS"
                and raw["research_physical_task_predicate"] is True
                and raw["original_author_repository_metric"][
                    "author_repo_score"]==1.0
                and raw["real_IFC_schema_delta"][
                    "introduced_schema_error_count"]==25
                and raw["augmented_strict_native_admission"] is False,
                "Original test scoring loophole/schema correction not reproduced")
    return {
        "status":"V054_AUTHOR_DELETE_POLICY_GAMING_DETECTED_AND_SCHEMA_GATE_PROVEN",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/223",
        "frozen_parent_v053_commit":
            "8ac34a03648fd3987ec171bb5dcca9e2d2b3fb09",
        "source_original_IFC_sha256":source_sha,
        "original_public_question_sha256":row["public_question_sha256"],
        "original_author_code_commit":AUTHOR_HEAD,
        "original_author_deleted_target_count_not_ids":len(targets),
        "source_relationship_ownership_counts_no_GUIDs":rel,
        "source_existing_schema_error_count":
            output["I_NATIVE_API"]["real_IFC_schema_delta"][
                "source_existing_schema_error_count"],
        "SCHEMA_BASELINE_EXISTING_ISSUE_NOT_ATTRIBUTABLE_TO_CANDIDATE":True,
        "raw_direct_remove_new_IFC_schema_cardinality_errors":
            output["RAW_REMOVE_INVALID_NEGATIVE_CONTROL"][
                "real_IFC_schema_delta"]["introduced_schema_error_count"],
        "raw_direct_remove_is_NOT_valid_or_admissible_scientific_edit":True,
        "original_author_score_1_possible_using_schema_invalid_graph":True,
        "valid_D_and_I_controls_same_author_score":True,
        "original_author_score_promoted_to_published_paper_OFFICIAL":False,
        "published_paper_score":None,
        "recommended_scoring_policies":[
            "original_author_repo_fractional_boolean_metric_separate",
            "independent_IFC4X3_schema_no_new_errors",
            "independent_non_target_source_preservation",
            "separate_independent_public_source_physical_task_predicate",
        ],
        "original_IFC_changed":False,
        "LLM_trials":0,
        "billable_provider_calls":0,
        "candidate_evidence":output,
        "frozen_v053_author_report_SHA256":V053_AUTHOR_SHA,
        "frozen_v053_prereg_candidate_SHA256":V053_PREREG_SHA,
    }


def canonical(data:dict)->bytes:
    return (json.dumps(data,sort_keys=True,ensure_ascii=False,indent=2)
            +"\n").encode("utf8")


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write",action="store_true")
    group.add_argument("--check",action="store_true")
    args=parser.parse_args()
    raw=canonical(build_report())
    if args.write:
        with REPORT.open("xb") as target:
            target.write(raw)
    else:
        require(REPORT.is_file() and REPORT.read_bytes()==raw,
                "Original-delete graph/cardinality report replay changed")
    print("V054_ORIGINAL_DELETE_POLICY=PASS RAW_AUTHOR_SCORE=1.0 "
          "RAW_NEW_SCHEMA_ERRORS=25 RAW_STRICT_ADMISSION=REJECT "
          "CORRECT_D_AND_I_AUTHOR_SCORE=0.5 LLM=0 SHA256="
          +sha256(raw).hexdigest())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
