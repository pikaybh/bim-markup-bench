"""v0.58 original BIBIMBAP 45-task capability census + source-cluster holdout.

ALL observations and selection are offline and PRE-MODEL-OUTPUT. Current
four-task implemented native semantics are not conflated with historical
XML readability or the generic Python/IfcOpenShell execution engine.

Six untouched-source tasks are selected deterministically, one from each
geometry/topological x create/update/delete stratum. This is an explicit
narrow 6-stratum candidate holdout, NOT representative of all 45 original
tasks, and NOT executable with current four-task D/I source oracles.

No author evaluator functions/GT, model SDK, original question strings,
LLM data transfer, paid API or published-paper scores enter this module.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path

import ifcopenshell

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v057_provenance import (
    assert_original_source_rights_unchanged_v057,
    refuse_all_model_trials_v057,
    ProviderTrialBlocked057,
)


ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
FROZEN_PARENT_HEAD="661d733b77e801a491e56fee5b362ca59c44c9e7"
FROZEN_PARENT_REPORT_SHA="22b3f30166ba2164278cdc1b2b25e5e4c4d0d0cddb74c25f7b759287bd127e57"
FROZEN_V056_RIGHTS_SHA="6b8e983a80a88a06f8de9ebefaeee3c52a71231583bbfeb164c05e0c1b17137c"
PARENT_REPORT=ROOT/"reports"/"bibimbap_v057_compact_managed_final_state_original4_20261118.json"
V056_RIGHTS_REPORT=ROOT/"reports"/"bibimbap_v056_offline_trial_rights_and_output_budget_gate_20261118.json"
SEED="BIBIMBAP-v058-public-original-untouched-source-six-strata-holdout-20261118"
SEEN_DEV_TASKS=frozenset((
    "geometry_test_14","geometry_test_15",
    "topological_test_11","topological_test_17",
))
ARMS=("D_COMPLETE_XML","D_MANAGED_FINAL_STATE","I_NATIVE")
AUX_ARM="D_COMPLETE_XML_STREAMED"
COMPARISONS=(
    ("D_COMPLETE_XML","I_NATIVE"),
    ("D_MANAGED_FINAL_STATE","I_NATIVE"),
)
STRATA=tuple(
    f"{category}:{crud}"
    for category in ("geometry","topological")
    for crud in ("create","update","delete")
)


class CapabilityRegistry058Error(ValueError):
    pass


def need(condition:bool,reason:str)->None:
    if not condition:
        raise CapabilityRegistry058Error(reason)


def digest(*items:str)->str:
    return sha256("|".join(items).encode("utf8")).hexdigest()


def _schema_and_source_ifc(row:dict)->tuple[str,str]:
    """Independent read-only source .ifc pin and installed native schema."""
    original=DATA/"ifc"/row["original_source_ifc_relpath"]
    need(original.is_file() and not original.is_symlink()
         and original.resolve().is_relative_to((DATA/"ifc").resolve())
         and file_hash(original)==row["original_ifc_sha256"],
         "Original IFC source missing, aliased, out of roots or changed")
    obj=ifcopenshell.open(str(original))
    need(obj.schema in {"IFC2X3","IFC4","IFC4X3"},
         "Unexpected pinned original IFC schema")
    return (obj.schema,row["original_ifc_sha256"])


def _author_evaluator_module_pin(row:dict)->dict:
    """Only hash evaluator module; NEVER import/call GT or expose code."""
    task=row["test_id"]
    need(task.replace("_","").isalnum()
         and task.count(".")==0 and "/" not in task and "\\" not in task,
         "Invalid original public task identifier")
    module=AUTHOR/"data"/"tests"/f"{task}.py"
    need(module.is_file() and not module.is_symlink()
         and module.resolve().is_relative_to((AUTHOR/"data"/"tests").resolve()),
         "Pinned author evaluator module missing or escaped")
    return {
        "path_relative_to_pinned_author_checkout":f"data/tests/{task}.py",
        "author_source_test_module_SHA256":file_hash(module),
        "original_author_checkout_module_exists":True,
        "author_module_was_EXECUTED_during_v058":False,
        "author_repository_metric_available_POST_RUN_ONLY":True,
        "published_paper_official_scorer_version_verified":False,
    }


def _source_cluster_assignments(rows:list[dict])->tuple[dict[str,str],list[str]]:
    """Select exactly 6 untouched source clusters, one per public stratum.

    No private grades, answer coordinates, developer success scores or
    IFC geometry are consulted by selection; only original SHA, CRUD,
    category and a fixed seed. All basic tasks sharing one source must
    be in the SAME group, never split across train/test.
    """
    source_groups:dict[str,list[dict]]=defaultdict(list)
    for row in rows:
        source_groups[row["original_ifc_sha256"]].append(row)
    seen_sha={x["original_ifc_sha256"] for x in rows
              if x["test_id"] in SEEN_DEV_TASKS}
    need(len(seen_sha)==4,"Four previous developer-control sources drifted")
    # Candidate for holdout must be from ORIGINAL SHA-untouched source,
    # non-basic and source has only one original task.
    eligible:dict[str,list[dict]]={x:[] for x in STRATA}
    for row in rows:
        sha=row["original_ifc_sha256"]
        if (sha not in seen_sha and len(source_groups[sha])==1
            and row["category"] in ("geometry","topological")):
            eligible[f'{row["category"]}:{row["crud"]}'].append(row)
    need(all(eligible[k] for k in STRATA),
         "At least one original untouched source required per stratum")
    selected=[]
    for stratum in STRATA:
        candidate=min(
            eligible[stratum],
            key=lambda row:(digest(SEED,"HOLDOUT",stratum,row["original_ifc_sha256"],
                                   row["test_id"]),row["test_id"]),
        )
        selected.append(candidate["test_id"])
    selected_set=set(selected)
    need(len(selected_set)==6 and not selected_set.intersection(SEEN_DEV_TASKS),
         "Original prospective six task selection invalid")
    holdout_sha={row["original_ifc_sha256"] for row in rows
                 if row["test_id"] in selected_set}
    need(len(holdout_sha)==6 and not holdout_sha.intersection(seen_sha),
         "Holdout original source must be new and cluster independent")
    by_sha={}
    for sha,members in source_groups.items():
        taskids={r["test_id"] for r in members}
        if sha in seen_sha:
            label="PRIOR_DEVELOPER_EXPOSED"
        elif sha in holdout_sha:
            label="PROSPECTIVE_UNTOUCHED_SOURCE_HOLDOUT"
        else:
            label="DEVELOPMENT_UNTESTED_CURRENT_ARMS"
        if label=="PROSPECTIVE_UNTOUCHED_SOURCE_HOLDOUT":
            need(taskids.issubset(selected_set),
                 "Original source cluster leaked between holdout and other tasks")
        by_sha[sha]=label
    need(len(by_sha)==31
         and Counter(by_sha.values())=={
             "PRIOR_DEVELOPER_EXPOSED":4,
             "PROSPECTIVE_UNTOUCHED_SOURCE_HOLDOUT":6,
             "DEVELOPMENT_UNTESTED_CURRENT_ARMS":21,
         },
         "Unexpected original source-cluster partition")
    return by_sha,selected


def _capabilities(row:dict,*,native_schema:str)->dict:
    task=row["test_id"]
    verified=task in SEEN_DEV_TASKS
    allowed_schema=native_schema=="IFC4X3"
    result={}
    for arm in ARMS+(AUX_ARM,):
        if verified:
            state="VERIFIED_NATIVE_DEVELOPER_CONTROL_ONLY"
            reason=(
                "Real original IFC positive/negative developer controls "
                "validated by v0.55/v0.56/v0.57, not model trial"
            )
        elif arm=="I_NATIVE":
            state="GENERIC_EXECUTOR_EXISTS_BUT_ORIGINAL_TASK_ORACLE_UNVERIFIED"
            reason=(
                "General pinned Docker Python/IfcOpenShell can execute code; "
                "the currently frozen independent native source/scope task "
                "admission only accepts four original task IDs"
            )
        else:
            state="NOT_SUPPORTED_BY_CURRENT_FOUR_TASK_FINAL_STATE_COMPILER"
            reason=(
                "Current frozen original-state/managed-diff native compiler "
                "accepts only four independently validated task IDs"
            )
        if not allowed_schema and not verified:
            reason+="; production v0.55 source/schema delta requires IFC4X3"
        result[arm]={
            "state":state,
            "evidence":reason,
            "requires_new_independent_task_native_contract":not verified,
            "current_production_native_ifc_schema_compatible":allowed_schema,
            "current_task_bound_executable_and_admissible":verified,
            "model_generated_success_rate":None,
            "provider_paid_execution_count":0,
        }
    return result


def _pair_plan_for_task(task_id:str)->list[dict]:
    outcome=[]
    for index,pair in enumerate(COMPARISONS):
        first=digest(SEED,"ARM_ORDER",task_id,pair[0],pair[1])
        ordered=list(pair if int(first[:2],16)%2==0 else reversed(pair))
        outcome.append({
            "comparison_id":("PRIMARY_FULL_D_vs_I" if index==0 else
                             "ALTERNATIVE_MANAGED_D_vs_I"),
            "arm_order":ordered,
            "fresh_source_clone_per_arm":True,
            "independent_I_baseline_RUN_PER_COMPARISON":True,
            "fresh_provider_context_per_arm":True,
            "no_reuse_of_prior_model_result":True,
            "max_TOTAL_tool_calls_per_arm":25,
            "scheduled_run":False,
            "model_requests":0,
            "original_author_grade_POST_RUN_only":True,
        })
    return outcome


def build_registry()->dict:
    need(file_hash(PARENT_REPORT)==FROZEN_PARENT_REPORT_SHA
         and file_hash(V056_RIGHTS_REPORT)==FROZEN_V056_RIGHTS_SHA,
         "Frozen original four native or rights report SHA drift")
    rights=assert_original_source_rights_unchanged_v057()
    need(rights["status"]=="BLOCKED_NO_MODEL_PROVIDER_TRIAL"
         and rights["model_generated_trials"]==0,
         "Original source rights admission wrongly opened")
    prior=json.loads(PARENT_REPORT.read_text(encoding="utf8"))
    need(prior["actual_LLM_generated_trial_count"]==0
         and len(prior["exploratory_source_native_engineered_tasks"])==4
         and set(prior["exploratory_source_native_engineered_tasks"])==
             SEEN_DEV_TASKS,
         "Frozen original four evidence basis changed")
    rows=public_45(AUTHOR,DATA)
    need(len(rows)==45
         and len({r["test_id"] for r in rows})==45
         and len({r["original_ifc_sha256"] for r in rows})==31
         and Counter(r["crud"] for r in rows)=={
             "create":15,"update":15,"delete":15}
         and Counter(r["category"] for r in rows)=={
             "basic":15,"geometry":15,"topological":15},
         "Pinned 45 original tasks or CRUD/category denominator changed")
    # A 15-task source cluster is *not* fifteen independent source samples.
    source_groups=defaultdict(list)
    for row in rows:
        source_groups[row["original_ifc_sha256"]].append(row)
    need(Counter(len(x) for x in source_groups.values())=={1:30,15:1},
         "Original shared-source cluster topology changed")
    assignments,holdout=_source_cluster_assignments(rows)
    row_by_id={x["test_id"]:x for x in rows}
    registry=[]
    source_schemas={}
    for row in sorted(rows,key=lambda r:r["test_id"]):
        task=row["test_id"]
        native_schema,sha=_schema_and_source_ifc(row)
        if sha in source_schemas:
            need(native_schema==source_schemas[sha],
                 "Shared IFC source native schema changed")
        source_schemas[sha]=native_schema
        evaluator=_author_evaluator_module_pin(row)
        prior_projection=row["xml_source_projection_previously_observed"]
        need(prior_projection in ("PROJECTABLE","BLOCKED"),
             "Historical XML-only preflight label changed")
        group=assignments[sha]
        registry.append({
            "original_test_id":task,
            "category":row["category"],
            "original_crud":row["crud"],
            "source_cluster_ifc_SHA256":sha,
            "original_input_IFC_relative_path":row["original_source_ifc_relpath"],
            "original_input_native_schema":native_schema,
            "original_question_SHA256":row["public_question_sha256"],
            "author_evaluator_source_only":evaluator,
            "historical_XML_readonly_source_projection":prior_projection,
            "historical_XML_readability_IS_NOT_edit_support":True,
            "source_cluster_task_count":len(source_groups[sha]),
            "source_cluster_assignment":group,
            "previously_exposed_four_developer_controls":task in SEEN_DEV_TASKS,
            "current_frozen_native_edit_task_scope":(
                "FOUR_ORIGINAL_DEVELOPER_CONTROLS_ONLY"
                if task in SEEN_DEV_TASKS else "UNTESTED_NOT_ADMITTED"),
            "arms":_capabilities(row,native_schema=native_schema),
            "model_generated_any_arm_run":False,
            "paper_official_published_score":None,
            "original_author_score_this_checkpoint":None,
        })
    # Enforce current eligibility of every prospective unseen task:
    need(all(not row["arms"][arm]["current_task_bound_executable_and_admissible"]
             for row in registry
             if row["source_cluster_assignment"]==
                "PROSPECTIVE_UNTOUCHED_SOURCE_HOLDOUT"
             for arm in ARMS),
         "A holdout trial was mistakenly marked runnable under 4-task oracle")
    by_cluster={
        sha:{
            "source_ifc_SHA256":sha,
            "native_ifc_schema":source_schemas[sha],
            "original_task_ids":sorted(x["test_id"] for x in members),
            "task_count":len(members),
            "assignment":assignments[sha],
            "no_source_cluster_leakage_across_splits":True,
        }
        for sha,members in sorted(source_groups.items())
    }
    # The deliberately modest 6 untouched source holdout is not a full 45
    # generalization claim; shared basic cluster stays entirely development.
    need(all(row_by_id[t]["category"] in ("geometry","topological")
             for t in holdout),
         "Holdout included unplanned basic shared source")
    order=sorted(holdout,
        key=lambda t:(digest(SEED,"PROSPECTIVE_ORDER",t,
                             row_by_id[t]["original_ifc_sha256"]),t))
    schedule=[]
    for task in order:
        row=row_by_id[task]
        schedule.append({
            "task_id":task,
            "stratum":f'{row["category"]}:{row["crud"]}',
            "source_cluster_ifc_SHA256":row["original_ifc_sha256"],
            "comparison_run_plan":_pair_plan_for_task(task),
            "task_is_CURRENTLY_UNSUPPORTED_IN_ALL_THREE_COMPARISON_ARMS":True,
            "no_run_authorized":True,
            "preregistration_approved":False,
        })
    need(len(schedule)==6
         and len({r["stratum"] for r in schedule})==6
         and all(len(s["comparison_run_plan"])==2 for s in schedule),
         "Prospective 6-stratum holdout/24-arm-run candidate plan drift")
    return {
        "status":"V058_OFFLINE_45_TASK_CAPABILITY_CENSUS_AND_PROSPECTIVE_HOLDOUT_FROZEN_NOT_LAUNCHABLE",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/231",
        "frozen_parent_v057_head":FROZEN_PARENT_HEAD,
        "frozen_parent_original_four_report_SHA256":FROZEN_PARENT_REPORT_SHA,
        "frozen_source_rights_report_SHA256":FROZEN_V056_RIGHTS_SHA,
        "original_author_code_git_repository":"https://github.com/nbharathik/bibimbap",
        "original_author_code_checkout_commit":"667004e16bd38fd7d538bcee56191465429fd975",
        "original_HF_data_card_declares_cc_by_4_0":True,
        "original_individual_IFC_chain_of_rights_verified":False,
        "original_code_license_verified":False,
        "user_approved_provider_data_transfer_and_retention":False,
        "total_original_public_edit_tasks":45,
        "original_crud_counts":dict(sorted(Counter(
            r["crud"] for r in rows).items())),
        "original_category_counts":dict(sorted(Counter(
            r["category"] for r in rows).items())),
        "source_input_schema_task_counts":dict(sorted(Counter(
            r["original_input_native_schema"] for r in registry).items())),
        "source_input_schema_unique_cluster_counts":dict(sorted(Counter(
            source_schemas.values()).items())),
        "historical_XML_readonly_projectable_tasks":sum(
            r["historical_XML_readonly_source_projection"]=="PROJECTABLE"
            for r in registry),
        "historical_XML_readonly_blocked_tasks":sum(
            r["historical_XML_readonly_source_projection"]=="BLOCKED"
            for r in registry),
        "historical_XML_readability_does_not_establish_native_EDIT_coverage":True,
        "original_unique_IFC_SHA_clusters":len(source_groups),
        "original_source_cluster_sizes":dict(sorted(Counter(
            len(members) for members in source_groups.values()).items())),
        "source_cluster_assignment_counts":dict(sorted(
            Counter(assignments.values()).items())),
        "task_assignment_counts":dict(sorted(Counter(
            r["source_cluster_assignment"] for r in registry).items())),
        "previously_developer_control_verified_4_original_tasks":
            sorted(SEEN_DEV_TASKS),
        "all_other_41_original_tasks_not_covered_by_current_task_oracle":41,
        "current_supported_developer_control_task_count_each_arm":4,
        "original_author_evaluator_45_modules_SHA_pinned_not_invoked":True,
        "original_author_code_version_paper_official_equivalence_proven":False,
        "three_separate_arm_identities":list(ARMS),
        "streaming_D_auxiliary_identity":AUX_ARM,
        "one_shared_original_source_cluster_spans_basic_CREATE_UPDATE_DELETE":True,
        "six_source_holdout_selection_algorithm":
            "For each original geometry/topological x create/update/delete stratum, "
            "select untouched single-source task minimizing "
            "SHA256(seed|HOLDOUT|stratum|source_IFC_SHA|task_id), excluding "
            "all prior developer-control source SHA clusters",
        "source_cluster_holdout_is_stratified_NOT_representative_of_basic_tasks":True,
        "prospective_selection_seed":SEED,
        "prospective_selection_blind_to_model_outputs_and_author_grades":True,
        "prospective_six_task_holdout_selected_before_ANY_LLM_trial":True,
        "prospective_six_source_heldout_task_ids":sorted(holdout),
        "prospective_six_source_heldout_IFC_sha256":sorted(
            row_by_id[t]["original_ifc_sha256"] for t in holdout),
        "prospective_randomized_task_order":order,
        "paired_schedule":schedule,
        "planned_comparison_ids":[
            "PRIMARY_FULL_D_vs_I","ALTERNATIVE_MANAGED_D_vs_I"],
        "planned_pair_comparison_count_if_admitted":12,
        "planned_independent_arm_task_run_slots_if_admitted":24,
        "I_baseline_must_be_re_run_for_each_separate_comparison":True,
        "holdout_is_not_CURRENTLY_EXPERIMENTALLY_ADMISSIBLE":True,
        "cannot_derive_model_accuracy_or_success_from_capability_matrix":True,
        "missing_or_refused_task_must_remain_in_ITT_denominator":True,
        "structurally_ineligible_tasks_reported_separately_from_model_failure":True,
        "candidate_holdout_ITT_denominator":6,
        "full_population_ITT_denominator_IF_full_supported_and_approved":45,
        "original_author_repository_metric_reporting":
            "BOOLEANS_AND_MEAN_UNMODIFIED_EVALUATOR_ONLY_POST_RUN",
        "physical_task_correctness_reporting":
            "INDEPENDENT_PUBLIC_SOURCE_RESEARCH_PREDICATE_SEPARATE",
        "native_IFC_admission_reporting":
            "INDEPENDENT_SOURCE_SCOPE_PLUS_IFC_SCHEMA_ERROR_DELTA",
        "author_repository_correct_5_column_deletion_score_possible_0_50":True,
        "strict_IFC_schema_success_is_not_same_as_original_author_score":True,
        "provider_exact_model_snapshot":None,
        "provider_data_transfer_authorization":None,
        "provider_billed_D_I_input_tokens":None,
        "provider_billed_D_I_completion_tokens":None,
        "provider_context_and_output_max_tokens":None,
        "paid_usd_cap_authorized":None,
        "budget_equivalent_error_feedback_protocol_frozen":False,
        "retry_timeout_and_seed_pre_registration_approved":False,
        "model_generated_trial_slots_executed":0,
        "billable_provider_calls":0,
        "trial_launch_blocked_even_with_all_TRUE_approvals":True,
        "source_cluster_registry":by_cluster,
        "all_original_45_task_capability_matrix":registry,
    }


def demand_trial_admission_v058(approvals:dict|None=None)->None:
    """No actual launch path is reachable, including synthetic approval."""
    del approvals
    refuse_all_model_trials_v057()
    raise ProviderTrialBlocked057("v0.58 cannot run model trials")


def canonical(data:dict)->bytes:
    return (json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)
            +"\n").encode("utf8")
