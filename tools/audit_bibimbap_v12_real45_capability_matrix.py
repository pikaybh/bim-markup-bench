"""Original BIBIMBAP 45-case actual read-projection + original D0/I0 ledger.

This is a *pre-experimental capability/evidence matrix*, not a benchmark
score, not a full authoring implementation. The real current source read
operation is measured for every unique original IFC through a separate
read-only subprocess. Original public requirements are frozen per-task,
and prior original-author developer D0 grades are imported only from
sha-pinned immutable reports v0.2–v0.10. Python I0 and matched model
conditions are NOT run, so true common-capability parity is NOT ESTABLISHED.

Original IFC/question cohort hashes are pinned via public_45. The authored
operation-family requirements below reflect *public prompts alone*, not
hidden GT or original evaluator score reverse engineering. Original author
scorer and historical real Luna scores never changed; no new model requests.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import csv
import json
import re
import subprocess
import sys

from tools.audit_bibimbap_v11_full45_ledger import run as previous_census
from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash

# Exact original public task IDs, required native object family, and the
# source model roles a user must inspect to interpret the requested edit.
# A role is not proof of full topological/task-specific edit expressibility.
# operation families only label *required* domain capabilities, NOT that
# our XML compiler implements the entire requested operation.
# (source roles, operation family)
REQUIREMENTS={
    "geometry_test_01":(("Column",),"CREATE_SLAB_ON_FOUR_COLUMN_TOPS"),
    "geometry_test_02":(("Wall",),"CREATE_COLUMN_AT_FOUR_WALL_CENTROID"),
    "geometry_test_03":(("Wall",),"CREATE_HOSTED_DOOR_IN_RELATIVE_NORTH_WALL"),
    "geometry_test_04":(("Column","Wall"),"CREATE_SPACE_LEFT_OF_NAMED_COLUMN"),
    "geometry_test_05":((),"CREATE_WALL_AT_ABSOLUTE_COORDINATES"),
    "geometry_test_11":(("Wall",),"UPDATE_ALL_SECOND_STOREY_WALL_HEIGHTS"),
    "geometry_test_12":(("Wall",),"ROTATE_WALL_45_DEGREES_AROUND_ITS_CENTER"),
    "geometry_test_13":(("Window","Wall"),"MOVE_SELECTED_WIDE_WINDOW_X_PLUS_THREE"),
    "geometry_test_14":(("Slab",),"RESHAPE_EXISTING_SLAB_INTO_SQUARE"),
    "geometry_test_15":(("Column",),"MOVE_COLUMN_TO_RECTANGLE_LAYOUT"),
    "geometry_test_16":(("Door",),"DELETE_DOOR_BETWEEN_TWO_REFERENCES"),
    "geometry_test_17":(("Wall",),"DELETE_DISCONNECTED_EXTERIOR_WALLS"),
    "geometry_test_18":(("Window","Wall"),"DELETE_WINDOWS_IN_WEST_WALLS"),
    "geometry_test_19":(("Window","Wall"),"DELETE_WINDOWS_OPPOSITE_NAMED_WALL"),
    "geometry_test_20":(("Wall","Column"),"DELETE_WALL_NEAREST_TO_NAMED_COLUMN"),
    "test_01":(("Wall",),"CREATE_DOOR_WITH_WALL_VOID"),
    "test_02":((),"CREATE_ABSOLUTE_SLAB"),
    "test_03":(("Slab",),"CREATE_SLAB_CENTERED_OPENING_AND_VOID"),
    "test_04":((),"CREATE_ABSOLUTE_COLUMN"),
    "test_05":((),"CREATE_ABSOLUTE_WALL"),
    "test_11":(("Wall",),"ROTATE_NAMED_WALL_90"),
    "test_12":(("Door","Wall"),"MOVE_HOSTED_DOOR_X_ONE_WITH_OPENING"),
    "test_13":(("Window",),"UPDATE_HOSTED_WINDOW_HEIGHT"),
    "test_14":(("Slab",),"DECREASE_EXISTING_SLAB_THICKNESS"),
    "test_15":(("Column",),"MOVE_NAMED_COLUMN_Y_MINUS_THREE"),
    "test_16":(("Column",),"DELETE_NAMED_COLUMN"),
    "test_17":(("Door","Opening"),"DELETE_HOSTED_DOOR_WITH_DEPENDENCIES"),
    "test_18":(("Opening","Door"),"DELETE_HOSTED_OPENING_AND_FILL"),
    "test_19":(("Wall",),"DELETE_CONNECTED_WALL_DEPENDENCIES"),
    "test_20":(("Space",),"DELETE_NAMED_ROOM"),
    "topological_test_01":(("Space","Wall"),"CREATE_WALL_ENCLOSING_ROOM"),
    "topological_test_02":(("Wall",),"CREATE_COLUMN_INSIDE_WALL_BOUNDS"),
    "topological_test_03":(("Space","Wall"),"CREATE_WALL_SEPARATING_TWO_ROOMS"),
    "topological_test_04":(("Wall",),"CREATE_SLAB_CLOSING_FOUR_WALLS"),
    "topological_test_05":(("Wall","Slab"),"CREATE_EXTERIOR_BOOLEAN_HOSTED_DOOR"),
    "topological_test_11":(("Column","Slab"),"EXTEND_ALL_COLUMNS_TO_NAMED_SLAB"),
    "topological_test_12":(("Wall",),"SHORTEN_EXTERNAL_WALL_RELATIVE_TO_WALL_GROUP"),
    "topological_test_13":(("Window","Wall"),"MOVE_WINDOW_TOUCHING_OPPOSITE_WALL"),
    "topological_test_14":(("Beam","Wall"),"TRIM_BEAMS_TO_NAMED_WALL"),
    "topological_test_15":(("Slab",),"MOVE_SLAB_ONTO_NAMED_SLAB"),
    "topological_test_16":(("Wall",),"DELETE_WALL_TOUCHING_TWO_NAMED_WALLS"),
    "topological_test_17":(("Column","Slab"),"DELETE_COLUMNS_WITHOUT_NAMED_SLAB_PHYSICAL_CONTACT"),
    "topological_test_18":(("Space","Wall"),"DELETE_SPACE_ENCLOSED_BY_NAMED_WALLS"),
    "topological_test_19":(("Column","Wall"),"DELETE_COLUMN_INSIDE_NAMED_WALLS"),
    "topological_test_20":(("Column","Space"),"DELETE_COLUMNS_OUTSIDE_NAMED_ROOMS"),
}
assert len(REQUIREMENTS)==45
SOURCE_GUID_PATTERN=re.compile(r"(?<![0-9A-Za-z_$])[0-9A-Za-z_$]{22}(?![0-9A-Za-z_$])")

# Historical D0 report pins. No dynamic untrusted report discovery;
# adding a new case requires an explicit research protocol amendment.
PINNED_D0_REPORTS={
    "v02":("bibimbap_test04_column_v2_developer_d0_20261113.json",
           "d55ffa4945c74e30e5b2143021f9cc07ea621c7f0b3e1d3316a0bbada6e6a870"),
    "v03":("bibimbap_v3_column_d0_test15_test16_20261113.json",
           "f358d3f65fe89734078ff6712f2543d578fac043e915c9baad6280dbaa7906b7"),
    "v04":("bibimbap_v04_slab_developer_d0_20261113.json",
           "98166dc3a6c606996a5f9bd43e3b0b26fb2852fb61e1c64ea1154aaefc630fec"),
    "v05":("bibimbap_wall_v05_developer_d0_20261113.json",
           "59345a999f2f227ec3437752d26721f36ddf91c5b162ef77bc855da7b2ebb08f"),
    "v06":("bibimbap_hosted_v06_developer_d0_20261113.json",
           "a4252265919e1d7456a53fae1d6afbf7e8cda22bed47a31148c2af762313082f"),
    "v07":("bibimbap_v07_original_nine_source_and_d0_20261113.json",
           "bdccd71a2fb0283221dec191d07adb06e8291a00aafc0c2e21d479a5368b7c55"),
    "v08":("bibimbap_v08_legacy_ifc2x3_ifc4_d0_20261113.json",
           "1264e33403a8b7e554913a34fc79b031890fd0aee832bc6b8f2010f912a5b4e0"),
    "v09":("bibimbap_v09_complex_original_developer_d0_20261113.json",
           "0037c30958437364434cd81696991d5268e2ca5c284eba3bf0329c6597cc01de"),
    "v010":("bibimbap_v010_original_column_multi_developer_d0_20261113.json",
            "9341aa11206b2d9ae2e5c96e816287f66fb5e0bab0b02d506f65ba7e862fe938"),
}
# Hard-coded D0 evidence schema by version. An unrecognized case is
# NOT silently assigned a score or claimed as an implementation.
TASK_FIELD={
    "v02":"source_task_id","v03":"task_id","v04":"original_public_task_id",
    "v05":"task_id","v06":"original_public_task_id",
    "v07":"original_public_task_id",
    "v08":"original_public_task_id","v09":"original_public_task",
    "v010":"original_public_task_id",
}
GRADE_FIELD={
    "v02":"original_author_results",
    "v03":"original_author_result",
    "v04":"original_author_grade_after_compilation",
    "v05":"original_author_score_after_compilation",
    "v06":"original_author_grade_after_d0",
    "v07":"original_author_score",
    "v08":"original_author_grade_after_freezing_d0",
    "v09":"original_author_grade_after_candidate_frozen",
    "v010":"original_author_D0_score_after_candidate_frozen",
}
ORACLE_FIELD={
    "v02":"independent_full_scene_clash_oracle_pass",
    "v03":"independent_native_task_specific_oracle",
    "v04":"independent_native_slab_oracle",
    "v05":"independent_native_oracle",
    "v06":"independent_native_ifc_oracle",
    "v07":"independent_native_edit_oracle",
    "v08":"independent_native_ifc_oracle",
    "v09":"independent_native_ifc_oracle",
    "v010":"independent_original_native_IFC_oracle",
}


def _frozen_d0(root:Path,public:dict)->dict:
    outcomes={}
    for version,(file,digest) in PINNED_D0_REPORTS.items():
        path=root/"reports"/file
        if not path.is_file() or file_hash(path)!=digest:
            raise ValueError("PINNED_PRIOR_D0_REPORT_SHA_DRIFT:"+version)
        obj=json.loads(path.read_text(encoding="utf8"))
        cases=([obj] if version in ("v02","v010")
               else obj["cases"] if version=="v09"
               else obj["developer_fixed_public_task_d0"] if version=="v03"
               else obj["tasks"])
        for case in cases:
            tid=case.get(TASK_FIELD[version])
            if tid not in public:
                raise ValueError("UNRECOGNIZED_PRIOR_D0_TASK:"+str(tid))
            grade=case.get(GRADE_FIELD[version])
            if grade is None:
                # v0.7 included read-only admissions without D0 edit.
                if version=="v07" and not case.get("native_operation_success"):
                    continue
                raise ValueError("PRIOR_D0_SCORE_MISSING:"+version+":"+tid)
            if (not isinstance(grade,dict) or
                grade.get("status")!="AUTHOR_SCORED" or
                not isinstance(grade.get("original_author_score"),(int,float))):
                raise ValueError("PRIOR_D0_GRADE_NOT_ORIGINAL_AUTHOR_SCORED:"+tid)
            if tid in outcomes:
                raise ValueError("DUPLICATE_FROZEN_PRIOR_D0_CANDIDATE:"+tid)
            # Only verify source/target hashes that are unambiguously
            # original public raw IFC bytes/question, not normalized clone.
            native_orig=next((
                case[k] for k in (
                    "original_public_ifc_sha256",
                    "original_source_ifc_sha256",
                    "original_ifc_sha256",
                ) if k in case
            ),None)
            question=next((
                case[k] for k in (
                    "original_public_question_sha256",
                    "public_question_sha256",
                    "question_sha256",
                ) if k in case
            ),None)
            if native_orig and native_orig!=public[tid]["original_ifc_sha256"]:
                raise ValueError("PRIOR_D0_ORIGINAL_IFC_RAW_SHA_MISMATCH:"+tid)
            if question and question!=public[tid]["public_question_sha256"]:
                raise ValueError("PRIOR_D0_PUBLIC_QUESTION_SHA_MISMATCH:"+tid)
            proof=case.get(ORACLE_FIELD[version])
            if version=="v02":
                # The original test_04 report explicitly recorded a NULL
                # *full-scene* clash oracle. This is missing independent
                # full-scene evidence, not a PASS and not a grader failure.
                oracle_status=(
                    "NO_INDEPENDENT_FULL_SCENE_ORACLE_RECORDED"
                    if proof is None else
                    "FULL_SCENE_ORACLE_PASS_RECORDED" if proof is True
                    else "FULL_SCENE_ORACLE_FAILED_OR_UNDETERMINED"
                )
            else:
                if not isinstance(proof,dict):
                    raise ValueError("PRIOR_D0_ORACLE_STRUCTURE_INVALID:"+tid)
                oracle_status="RECORDED_NATIVE_TASK_SPECIFIC_EVIDENCE"

            score=float(grade["original_author_score"])
            if not 0<=score<=1 or (
                bool(grade.get("original_author_full_mark")) !=
                (abs(score-1.)<1e-8)
            ):
                raise ValueError("PRIOR_D0_INVALID_SCORE_OR_FULL_MARK:"+tid)
            outcomes[tid]={
                "historical_version":version,
                "pinned_D0_report_sha256":digest,
                "original_author_score_from_frozen_developer_D0":score,
                "original_author_full_mark_from_D0":bool(
                    grade["original_author_full_mark"]),
                "original_author_submetrics":grade["original_author_metrics"],
                "historical_independent_native_oracle":oracle_status,
                "historical_D0_not_a_new_model_attempt":True,
                "historical_exact_source_only_task_slice_only":True,
                "original_author_score_does_not_prove_strict_task_success":True,
            }
    return dict(sorted(outcomes.items()))


def _worker(root:Path,original:Path,expected_sha:str,timeout_s:int)->dict:
    command=[
        sys.executable,"-u","-X","faulthandler","-m",
        "tools.audit_bibimbap_v12_projection_worker",
        "--original-source",str(original),
        "--original-sha256",expected_sha,
    ]
    try:
        p=subprocess.run(command,cwd=root,capture_output=True,
                         text=True,timeout=timeout_s,check=False)
    except subprocess.TimeoutExpired:
        return {
            "projection_state":"FAIL_CLOSED",
            "projection_failure_code":"WORKER_TIMEOUT",
            "original_ifc_sha256":expected_sha,
        }
    if p.returncode:
        return {
            "projection_state":"FAIL_CLOSED",
            "projection_failure_code":"WORKER_PROCESS_NONZERO",
            "original_ifc_sha256":expected_sha,
            "worker_process_exit_status":p.returncode,
        }
    try:
        payload=json.loads(p.stdout.splitlines()[-1])
        if payload["status"]!="SOURCE_PROJECTION_INSPECTED":
            raise ValueError("Worker returned invalid result")
        record=payload["inspection"]
        if record["original_ifc_sha256"]!=expected_sha:
            raise ValueError("Worker original source hash not bound")
        return record
    except (ValueError,KeyError,IndexError,TypeError):
        return {
            "projection_state":"FAIL_CLOSED",
            "projection_failure_code":"WORKER_STRUCTURED_OUTPUT_INVALID",
            "original_ifc_sha256":expected_sha,
        }


def _type_role(native_ifc_class:str)->str:
    table={
        "IfcWall":"Wall","IfcWallStandardCase":"Wall",
        "IfcSlab":"Slab","IfcSlabStandardCase":"Slab",
        "IfcColumn":"Column","IfcColumnStandardCase":"Column",
        "IfcDoor":"Door","IfcWindow":"Window",
        "IfcOpeningElement":"Opening","IfcSpace":"Space",
        "IfcBeam":"Beam",
    }
    return table.get(native_ifc_class,"UNMANAGED_NATIVE_CLASS")


def _reference_gate(task:dict,inspection:dict,requires:tuple[str,...])->dict:
    refs=sorted(set(SOURCE_GUID_PATTERN.findall(task["public_question"])))
    src=inspection.get("original_product_class_by_guid",{})
    projected=inspection.get("projected_existing_product_xml_type_by_guid",{})
    ref_native=[x for x in refs if x in src]
    ref_missing=[x for x in refs if x not in src]
    ref_projected=[x for x in ref_native if x in projected]
    unprojected=[x for x in ref_native if x not in projected]
    count_src=Counter(_type_role(t) for t in src.values())
    count_projected=Counter(projected.values())
    role_stats={
        role:{
            "source_native_product_count":int(count_src[role]),
            "read_projection_native_product_count":int(count_projected[role]),
            "all_original_products_of_required_role_projected":(
                count_src[role]>0 and count_projected[role]>=count_src[role]
            ),
        }
        for role in requires
    }
    # An absent native reference in the public task is a source
    # discrepancy, not an XML compiler failure. A read-projected GUID
    # does not prove its original IFC geometry/elements/relationships are
    # writable by this narrow source-backed XML schema.
    projected_input=(inspection.get("projection_state")
                     =="PASSED_NATIVE_PARTIAL_SOURCE_READ")
    complete=(
        projected_input and not ref_missing and not unprojected
        and all(x["all_original_products_of_required_role_projected"]
                for x in role_stats.values())
    )
    return {
        "original_public_named_IFC_GlobalId_references":refs,
        "public_named_references_count":len(refs),
        "public_named_native_IFC_reference_found_count":len(ref_native),
        "public_named_IFC_references_missing_from_source":ref_missing,
        "original_public_named_native_references_not_in_XML":unprojected,
        "public_named_native_references_projected_count":len(ref_projected),
        "required_source_roles":list(requires),
        "source_role_projection_coverage":role_stats,
        "complete_named_refs_and_source_roles_in_current_read_view":bool(
            complete),
        "this_is_not_proof_of_semantic_task_write_support":True,
    }


def run(root:Path,author:Path,dataset:Path,*,worker_timeout_s=75)->dict:
    if _head(author)!=AUTHOR_SHA or _head(dataset)!=DATA_SHA:
        raise ValueError("ORIGINAL_AUTHOR_OR_DATASET_COMMIT_DRIFT")
    if not 5<=worker_timeout_s<=600:
        raise ValueError("INVALID_NATIVE_SOURCE_PROJECTION_WORKER_TIMEOUT")
    old=previous_census(root,author,dataset)
    public_rows=public_45(author,dataset)
    public={t["test_id"]:t for t in public_rows}
    if len(public)!=45 or set(public)!=set(REQUIREMENTS):
        raise ValueError("PUBLIC_45_TASK_TO_REQUIREMENT_MAPPING_NOT_BIJECTIVE")
    census={x["original_task_id"]:x for x in old["original_task_ledger"]}
    prior=_frozen_d0(root,public)
    cache={}
    original_source_locations={}
    for t in sorted(public_rows,key=lambda x:x["test_id"]):
        path=dataset/"ifc"/t["original_source_ifc_relpath"]
        digest=t["original_ifc_sha256"]
        if not path.is_file() or path.is_symlink() or file_hash(path)!=digest:
            raise ValueError("ORIGINAL_SOURCE_NOT_PINNED_OR_HASH_DRIFT:"+t["test_id"])
        # Shared original source IFC is evaluated ONCE; task-specific source
        # reference and operation coverage is never shared/cached.
        original_source_locations.setdefault(digest,path)
    for digest,path in sorted(original_source_locations.items()):
        cache[digest]=_worker(root,path,digest,worker_timeout_s)
        if file_hash(path)!=digest:
            raise ValueError("ORIGINAL_READONLY_WORKER_MODIFIED_INPUT_IFC")
    rows=[]
    for tid in sorted(public):
        t=public[tid]
        roles,operation=REQUIREMENTS[tid]
        src=cache[t["original_ifc_sha256"]]
        source_role=_reference_gate(t,src,roles)
        native=prior.get(tid)
        historical=(
            "FROZEN_DEVELOPER_D0_ORIGINAL_AUTHOR_FULL_MARK" if
            native and native["original_author_full_mark_from_D0"]
            else "FROZEN_DEVELOPER_D0_ORIGINAL_AUTHOR_PARTIAL" if native
            else "NO_V02_TO_V010_FROZEN_DEVELOPER_D0")
        # Authoring ability evidence cannot be promoted from source read
        # or one frozen developer-authored XML snippet. Each task's
        # Python I0 is NOT RUN, not a score of zero or a model failure.
        rows.append({
            "original_public_task_id":tid,
            "original_public_crud":t["crud"],
            "original_public_category":t["category"],
            "original_public_source_ifc_sha256":t["original_ifc_sha256"],
            "original_public_question_sha256":t["public_question_sha256"],
            "original_native_schema":census[tid]["original_native_ifc_schema"],
            "required_source_roles_from_public_task":list(roles),
            "required_native_operation_family_from_public_task":operation,
            "observed_source_projection_version":src.get("projection_builder"),
            "actual_source_projection_state":src["projection_state"],
            "actual_readonly_partial_source_projection":(
                src["projection_state"]=="PASSED_NATIVE_PARTIAL_SOURCE_READ"),
            "actual_source_projection_failure_code":src.get(
                "projection_failure_code"),
            "source_historical_v01_projection_status":
                t["xml_source_projection_previously_observed"],
            "source_role_and_public_reference_gate":source_role,
            "frozen_source_only_developer_D0_status":historical,
            "frozen_source_only_developer_D0_evidence":native,
            "native_semantic_write_status":(
                "ONLY_PREVIOUS_FROZEN_TASK_SPECIFIC_D0_CANDIDATE_EVIDENCED"
                if native else
                "NOT_ESTABLISHED_FOR_THIS_ORIGINAL_TASK"
            ),
            "native_independent_D0_oracle_status":(
                native["historical_independent_native_oracle"]
                if native else "NOT_RUN_FOR_THIS_TASK"
            ),
            "native_full_original_task_success_independently_verified":
                False,
            "Python_control_original_IFC_available_to_generic_tool":
                True,
            "Python_control_matching_task_specific_I0_run":
                "NOT_RUN_NO_EVIDENCE",
            "Python_control_independent_task_specific_I0_oracle":
                "NOT_RUN_NO_EVIDENCE",
            "current_real_matched_model_XML_vs_Python_trial":
                "NOT_RUN",
            "true_equal_capability_XML_Python_edit_parity":
                "NOT_PROVEN",
            "excluded_from_original_45_denominator":False,
            "no_paid_model_calls_in_this_audit":True,
        })
    if len(rows)!=45 or len({r["original_public_task_id"] for r in rows})!=45:
        raise ValueError("LOST_ORIGINAL_45_DENOMINATOR")
    status=Counter(r["actual_source_projection_state"] for r in rows)
    evidence=Counter(r["frozen_source_only_developer_D0_status"] for r in rows)
    complete_ref=sum(
        r["source_role_and_public_reference_gate"][
            "complete_named_refs_and_source_roles_in_current_read_view"
        ] for r in rows
    )
    return {
        "status":"ORIGINAL_BIBIMBAP_45_TASK_NATIVE_READ_PROJECTION_AND_FROZEN_D0_I0_MATRIX_V012",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/138",
        "original_author_revision":AUTHOR_SHA,
        "original_dataset_revision":DATA_SHA,
        "original_public_task_population":45,
        "task_requirements_registry_from_original_public_question_only":True,
        "unique_original_ifc_source_count":len(cache),
        "source_projection_worker_isolated_per_unique_original_IFC":True,
        "all_original_source_shas_verified_after_readonly_projection":True,
        "real_source_projection_states_across_45_tasks":dict(sorted(status.items())),
        "real_unique_source_projection_states":dict(sorted(Counter(
            rec["projection_state"] for rec in cache.values()
        ).items())),
        "reference_and_required_source_roles_readonly_complete_task_count":
            complete_ref,
        "historical_v01_projection_count_NOT_CURRENT":old[
            "historical_v01_readonly_source_projection_counts"
        ],
        "frozen_developer_D0_evidence_counts":dict(sorted(evidence.items())),
        "all_45_I0_matched_Python_task_specific_run_count":0,
        "all_45_new_real_matched_model_XML_vs_Python_trial_count":0,
        "original_real_GPT6_Luna_historical_45_task_scores_changed":False,
        "new_provider_requests":0,
        "additional_paid_api_usd":"0",
        "source_read_only_does_not_imply_write_capability":True,
        "historical_D0_full_mark_does_not_prove_strict_native_all_task_parity":True,
        "full_45_native_XML_semantic_write_parity_not_proven":True,
        "full_45_Python_I0_comparison_not_run":True,
        "true_equal_capability_XML_vs_Python_parity_not_proven":True,
        "every_original_task_kept_in_45_denominator":True,
        "original_native_source_observations_by_sha256":{
            digest:record for digest,record in sorted(cache.items())
        },
        "original_45_task_capability_and_evidence_matrix":rows,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-root",type=Path,default=Path.cwd())
    parser.add_argument("--author-repo",type=Path,required=True)
    parser.add_argument("--dataset",type=Path,required=True)
    parser.add_argument("--worker-timeout-s",type=int,default=75)
    parser.add_argument("--output-json",type=Path,required=True)
    parser.add_argument("--output-csv",type=Path)
    args=parser.parse_args()
    destinations=[x for x in (args.output_json,args.output_csv) if x]
    if any(x.exists() or x.is_symlink() for x in destinations):
        parser.error("Refusing overwrite historical/occupied research evidence")
    if len({str(x.resolve()) for x in destinations})!=len(destinations):
        parser.error("JSON and CSV destinations must be distinct")
    result=run(
        args.research_root.resolve(strict=True),
        args.author_repo.resolve(strict=True),
        args.dataset.resolve(strict=True),
        worker_timeout_s=args.worker_timeout_s,
    )
    json_bytes=(json.dumps(result,sort_keys=True,indent=2,
                          ensure_ascii=False)+"\n").encode("utf8")
    if args.output_csv:
        import io
        buf=io.StringIO(newline="")
        fields=[
            "task","crud","schema","required_operation",
            "actual_read_projection","public_reference_gate_complete",
            "frozen_developer_D0_status","frozen_original_author_D0_score",
            "Python_original_task_I0","strict_equal_backend_parity",
        ]
        writer=csv.DictWriter(buf,fieldnames=fields,lineterminator="\n")
        writer.writeheader()
        for r in result["original_45_task_capability_and_evidence_matrix"]:
            d0=r["frozen_source_only_developer_D0_evidence"]
            writer.writerow({
                "task":r["original_public_task_id"],
                "crud":r["original_public_crud"],
                "schema":r["original_native_schema"],
                "required_operation":r["required_native_operation_family_from_public_task"],
                "actual_read_projection":r["actual_source_projection_state"],
                "public_reference_gate_complete":r[
                    "source_role_and_public_reference_gate"][
                        "complete_named_refs_and_source_roles_in_current_read_view"],
                "frozen_developer_D0_status":r["frozen_source_only_developer_D0_status"],
                "frozen_original_author_D0_score":(
                    d0["original_author_score_from_frozen_developer_D0"]
                    if d0 else ""),
                "Python_original_task_I0":"NOT_RUN",
                "strict_equal_backend_parity":"NOT_PROVEN",
            })
        csv_bytes=buf.getvalue().encode("utf8")
    for path in destinations:
        path.parent.mkdir(parents=True,exist_ok=True)
    with args.output_json.open("xb") as file:
        file.write(json_bytes)
    if args.output_csv:
        with args.output_csv.open("xb") as file:
            file.write(csv_bytes)
    print(json.dumps({
        "status":result["status"],
        "original_population":result["original_public_task_population"],
        "unique_sources":result["unique_original_ifc_source_count"],
        "actual_projection":result["real_source_projection_states_across_45_tasks"],
        "frozen_D0":result["frozen_developer_D0_evidence_counts"],
        "strict_equal_capability_parity_proven":False,
        "Python_I0_completed":0,
        "json_sha256":file_hash(args.output_json),
        "csv_sha256":file_hash(args.output_csv) if args.output_csv else None,
    },sort_keys=True))


if __name__=="__main__":
    main()
