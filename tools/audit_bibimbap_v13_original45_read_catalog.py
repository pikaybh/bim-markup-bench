"""Real current original-BIBIMBAP full45 v0.13 source-only read audit.

Every distinct original IFC source is normalized preserving schema, read
through new opt-in v0.13 typed+opaque native read-only XML and checked by an
INDEPENDENT IFC-only oracle in an isolated child process. The 45 public
task denominator, earlier v0.12 strict binder failures, v0.2–v0.10 D0 scores,
and complete lack of Python I0 matched runs remain explicit.

READ-ONLY reference completeness is NOT editable XML source coverage, BIM
semantic writer support, full original task success, nor causal paired result.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import csv
import io
import json
import subprocess
import sys

from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.audit_bibimbap_v12_real45_capability_matrix import (
    REQUIREMENTS,_type_role,SOURCE_GUID_PATTERN,
)

PREVIOUS_V12="bibimbap_v012_actual_original45_native_read_and_D0I0_matrix_20261114.json"
PREVIOUS_V12_SHA="8fcaed91fc0578051ea99151925daaa9e6a742d46c218b6db39ec83531ef6758"


def _worker(root:Path,input:Path,source_sha:str,timeout_s:int)->dict:
    cmd=[
        sys.executable,"-u","-X","faulthandler","-m",
        "tools.audit_bibimbap_v13_source_worker",
        "--original-source",str(input),"--original-sha256",source_sha,
    ]
    try:
        proc=subprocess.run(
            cmd,cwd=root,capture_output=True,text=True,
            timeout=timeout_s,check=False)
    except subprocess.TimeoutExpired:
        return {"actual_original_source_native_read_status":"FAIL_CLOSED",
                "failure_code":"ISOLATED_NATIVE_WORKER_TIMEOUT"}
    if proc.returncode:
        return {"actual_original_source_native_read_status":"FAIL_CLOSED",
                "failure_code":"ISOLATED_NATIVE_WORKER_NONZERO",
                "worker_exit":proc.returncode}
    try:
        payload=json.loads(proc.stdout.splitlines()[-1])
        if payload["status"]!="V013_ORIGINAL_SOURCE_READ_INDEPENDENTLY_VERIFIED":
            raise ValueError("Unexpected native worker protocol")
        record=payload["inspection"]
        if record["original_public_ifc_sha256"]!=source_sha:
            raise ValueError("Original source identity not bound")
        return record
    except (KeyError,IndexError,TypeError,ValueError):
        return {"actual_original_source_native_read_status":"FAIL_CLOSED",
                "failure_code":"ISOLATED_NATIVE_WORKER_INVALID_RESULT"}


def run(root:Path,author:Path,dataset:Path,*,timeout_s:int=100)->dict:
    if _head(author)!=AUTHOR_SHA or _head(dataset)!=DATA_SHA:
        raise ValueError("Pinned public author/dataset revision changed")
    if not 5<=timeout_s<=600:
        raise ValueError("Invalid isolated original native source timeout")
    previous=root/"reports"/PREVIOUS_V12
    if file_hash(previous)!=PREVIOUS_V12_SHA:
        raise ValueError("Previous original v0.12 evidence SHA256 drift")
    old=json.loads(previous.read_text(encoding="utf8"))
    public={x["test_id"]:x for x in public_45(author,dataset)}
    if len(public)!=45 or set(public)!=set(REQUIREMENTS):
        raise ValueError("Lost or duplicated public original45 tasks")
    frozen={r["original_public_task_id"]:r
            for r in old["original_45_task_capability_and_evidence_matrix"]}
    if set(frozen)!=set(public):
        raise ValueError("Original v0.12 frozen evidence altered original cohort")
    unique={}
    for t in public.values():
        source=dataset/"ifc"/t["original_source_ifc_relpath"]
        h=t["original_ifc_sha256"]
        if not source.is_file() or source.is_symlink() or file_hash(source)!=h:
            raise ValueError("Original IFC input hash mismatch")
        unique.setdefault(h,source)
    obs={}
    for digest,path in sorted(unique.items()):
        obs[digest]=_worker(root,path,digest,timeout_s)
        if file_hash(path)!=digest:
            raise ValueError("Original source IFC changed during real native read worker")
    rows=[]
    for tid in sorted(public):
        t=public[tid]
        prev=frozen[tid]
        if (t["original_ifc_sha256"]!=prev["original_public_source_ifc_sha256"]
            or t["public_question_sha256"]!=prev["original_public_question_sha256"]):
            raise ValueError("Previous original public source/question evidence drift")
        roles,operation=REQUIREMENTS[tid]
        source=obs[t["original_ifc_sha256"]]
        success=(source.get("actual_original_source_native_read_status")
                 =="READ_ONLY_SOURCE_AND_INDEPENDENT_NATIVE_CATALOG_ORACLE_PASS")
        ids=sorted(set(SOURCE_GUID_PATTERN.findall(t["public_question"])))
        all_products=source.get("original_native_product_class_by_guid",{})
        typed=source.get("source_native_original_product_typed_XML_class_by_guid",{})
        missing_src=[x for x in ids if x not in all_products]
        missing_typed=[x for x in ids if x in all_products and x not in typed]
        original_count=Counter(_type_role(x) for x in all_products.values())
        typed_count=Counter(_type_role(x) for x in typed.values())
        source_role={
            x:{
                "original_native_IFC_count":int(original_count[x]),
                "safe_typed_XML_existing_count":int(typed_count[x]),
                "native_source_readonly_catalog_count":int(original_count[x]),
                "all_original_native_role_in_safe_typed_XML":(
                    original_count[x]>0 and typed_count[x]>=original_count[x]
                ),
            }
            for x in roles
        }
        safe_typed=bool(success and not missing_src and not missing_typed
                         and all(x["all_original_native_role_in_safe_typed_XML"]
                                 for x in source_role.values()))
        source_catalog=bool(
            success and not missing_src and
            all(source_role[x]["native_source_readonly_catalog_count"]>0
                for x in roles)
        )
        rows.append({
            "original_public_task_id":tid,
            "original_public_IFC_sha256":t["original_ifc_sha256"],
            "original_public_question_sha256":t["public_question_sha256"],
            "original_public_operation_family_required":operation,
            "original_native_schema":prev["original_native_schema"],
            "v012_historical_actual_typed_XML_read_status":
                prev["actual_source_projection_state"],
            "v012_historical_typed_XML_read_failure":
                prev["actual_source_projection_failure_code"],
            "v013_original_source_independent_read_status":
                source["actual_original_source_native_read_status"],
            "v013_source_independent_read_failure":
                source.get("failure_code"),
            "v013_original_native_source_product_count":
                source.get("original_native_product_count"),
            "v013_source_safe_typed_XML_product_count":
                len(typed),
            "v013_original_product_count_readonly_catalog_only":
                len(source.get("original_product_guids_readonly_catalog_only",{})),
            "v013_original_public_named_reference_GUIDs":ids,
            "v013_named_public_refs_absent_original_IFC":missing_src,
            "v013_named_public_refs_excluded_safe_typed_XML":missing_typed,
            "v013_original_required_source_roles":list(roles),
            "v013_original_role_readonly_vs_typed_coverage":source_role,
            "v013_safe_typed_source_role_and_reference_gate":safe_typed,
            "v013_readonly_native_catalog_source_role_and_reference_gate":
                source_catalog,
            "v013_original_native_hosted_openings_readonly_demoted":
                source.get("original_openings_demoted_due_to_real_native_host_extent",[]),
            "v013_original_linked_fills_readonly_demoted":
                source.get("original_dependant_fills_demoted_due_to_real_native_host_extent",[]),
            "v013_independent_native_catalog_oracle":
                source.get("independent_original_IFC_only_oracle_status"),
            "v013_readonly_catalog_can_compile_native_ifc_edits":False,
            "v013_demoted_native_opening_fill_edit_support":False,
            "v013_original_Space_Beam_Wall_opaque_readonly_reference_visibility":
                source_catalog,
            "historical_original_task_developer_D0_status":
                prev["frozen_source_only_developer_D0_status"],
            "historical_original_task_developer_D0_evidence":
                prev["frozen_source_only_developer_D0_evidence"],
            "matching_original_Python_I0_source_task_result":
                "NOT_RUN_NO_EVIDENCE",
            "matching_original_XML_LLM_source_task_result":
                "NOT_RUN",
            "original_task_native_XML_semantic_write_equivalence":
                "NOT_PROVEN",
            "original_task_native_XML_vs_Python_feature_parity":
                "NOT_PROVEN",
            "excluded_from_original_45_denominator":False,
        })
    counts=Counter(row["v013_original_source_independent_read_status"]
                   for row in rows)
    if sum(counts.values())!=45 or len(rows)!=45:
        raise ValueError("Full original 45 denominator missing")
    return {
        "status":"BIBIMBAP_ORIGINAL45_READONLY_NATIVE_TYPED_PLUS_OPAQUE_CATALOG_V013",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/140",
        "pinned_original_author_revision":AUTHOR_SHA,
        "pinned_original_public_data_revision":DATA_SHA,
        "frozen_prior_v012_report_sha256":PREVIOUS_V12_SHA,
        "original_public_45_denominator":45,
        "original_native_unique_IFC_source_count":len(unique),
        "actual_v013_native_source_read_oracle_status_counts":
            dict(sorted(counts.items())),
        "actual_v013_native_unique_source_read_status_counts":dict(sorted(
            Counter(o["actual_original_source_native_read_status"]
                    for o in obs.values()).items())),
        "actual_v013_safe_typed_XML_source_role_gate_count":sum(
            row["v013_safe_typed_source_role_and_reference_gate"] for row in rows
        ),
        "actual_v013_source_readonly_catalog_roles_and_ref_gate_count":sum(
            row["v013_readonly_native_catalog_source_role_and_reference_gate"]
            for row in rows
        ),
        "native_original_openings_readonly_demoted_count_across_unique_sources":
            sum(len(o.get("original_openings_demoted_due_to_real_native_host_extent",[]))
                for o in obs.values()),
        "native_original_fills_readonly_demoted_count_across_unique_sources":
            sum(len(o.get("original_dependant_fills_demoted_due_to_real_native_host_extent",[]))
                for o in obs.values()),
        "frozen_v012_native_source_read_status_comparison":old[
            "real_source_projection_states_across_45_tasks"],
        "frozen_v012_historical_D0_counts_unchanged":old[
            "frozen_developer_D0_evidence_counts"],
        "native_read_catalog_is_NOT_an_editable_ifc_source":True,
        "native_source_original_ifc_mesh_geometry_unmodified":True,
        "native_IfcRelVoids_IfcRelFills_original_source_links_unmodified":True,
        "no_original_BIBIMBAP_scorer_or_hidden_GT_called":True,
        "full_original45_IFC_semantic_write_parity_not_proven":True,
        "matched_Python_I0_original_task_runs":0,
        "matched_real_XML_vs_Python_LLM_runs":0,
        "real_Luna_historical_original45_scores_unchanged":True,
        "new_paid_provider_calls":0,
        "additional_paid_usd":"0",
        "all_45_original_tasks_preserved_in_denominator":True,
        "original_native_IFC_unique_source_read_evidence":{
            k:obs[k] for k in sorted(obs)
        },
        "original45_task_readonly_vs_native_write_status":rows,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--research-root",type=Path,default=Path.cwd())
    p.add_argument("--author-repo",type=Path,required=True)
    p.add_argument("--dataset",type=Path,required=True)
    p.add_argument("--worker-timeout-s",type=int,default=100)
    p.add_argument("--output-json",type=Path,required=True)
    p.add_argument("--output-csv",type=Path)
    args=p.parse_args()
    paths=[x for x in (args.output_json,args.output_csv) if x]
    if len({str(x.resolve()) for x in paths})!=len(paths):
        p.error("Report output paths must be different")
    if any(x.exists() or x.is_symlink() for x in paths):
        p.error("Refuse overwriting research evidence")
    result=run(
        args.research_root.resolve(strict=True),
        args.author_repo.resolve(strict=True),
        args.dataset.resolve(strict=True),
        timeout_s=args.worker_timeout_s,
    )
    raw=(json.dumps(result,indent=2,sort_keys=True,
                    ensure_ascii=False)+"\n").encode("utf8")
    if args.output_csv:
        b=io.StringIO(newline="")
        names=[
            "task","schema","required_original_operation","original_v12_read",
            "v13_native_source_read","safe_typed_XML_roles_and_refs",
            "source_READONLY_catalog_roles_and_refs",
            "demoted_native_openings","demoted_original_fills",
            "frozen_developer_D0_status","frozen_original_author_D0_grade",
            "matched_Python_I0","actual_native_XML_edit_parity",
        ]
        wr=csv.DictWriter(b,fieldnames=names,lineterminator="\n")
        wr.writeheader()
        for row in result["original45_task_readonly_vs_native_write_status"]:
            prior=row["historical_original_task_developer_D0_evidence"]
            wr.writerow({
                "task":row["original_public_task_id"],
                "schema":row["original_native_schema"],
                "required_original_operation":
                    row["original_public_operation_family_required"],
                "original_v12_read":row["v012_historical_actual_typed_XML_read_status"],
                "v13_native_source_read":row["v013_original_source_independent_read_status"],
                "safe_typed_XML_roles_and_refs":row["v013_safe_typed_source_role_and_reference_gate"],
                "source_READONLY_catalog_roles_and_refs":
                    row["v013_readonly_native_catalog_source_role_and_reference_gate"],
                "demoted_native_openings":len(
                    row["v013_original_native_hosted_openings_readonly_demoted"]),
                "demoted_original_fills":len(
                    row["v013_original_linked_fills_readonly_demoted"]),
                "frozen_developer_D0_status":row["historical_original_task_developer_D0_status"],
                "frozen_original_author_D0_grade":(
                    prior["original_author_score_from_frozen_developer_D0"]
                    if prior else ""),
                "matched_Python_I0":"NOT_RUN",
                "actual_native_XML_edit_parity":"NOT_PROVEN",
            })
        flat=b.getvalue().encode("utf8")
    for x in paths:
        x.parent.mkdir(parents=True,exist_ok=True)
    with args.output_json.open("xb") as handle:
        handle.write(raw)
    if args.output_csv:
        with args.output_csv.open("xb") as handle:
            handle.write(flat)
    print(json.dumps({
        "status":result["status"],
        "denominator":45,
        "native_source_read":result["actual_v013_native_source_read_oracle_status_counts"],
        "typed_roles":result["actual_v013_safe_typed_XML_source_role_gate_count"],
        "readonly_roles":result["actual_v013_source_readonly_catalog_roles_and_ref_gate_count"],
        "source_demoted_openings":
            result["native_original_openings_readonly_demoted_count_across_unique_sources"],
        "source_demoted_fills":
            result["native_original_fills_readonly_demoted_count_across_unique_sources"],
        "native_writer_full45_parity":False,
        "D0_frozen":result["frozen_v012_historical_D0_counts_unchanged"],
        "json_sha256":file_hash(args.output_json),
        "csv_sha256":file_hash(args.output_csv) if args.output_csv else None,
        "model_requests":0,
    },sort_keys=True))


if __name__=="__main__":
    main()
