"""Grader-private audit of author's PUBLISHED CSV scores (NOT IFC scoring).

No evaluator executes here. No hidden ground-truth, output IFC, prompt, or
individual task row is ever serialized. This source-audit consumes public
per_task.csv records exclusively in a *trusted grader-side* process,
recomputes published arithmetic, and returns bounded aggregate evidence.

Warning: 'official author-released CSV' is NOT synonymous with 'official
executable scorer has been obtained and independently calibrated'.
"""
from __future__ import annotations

from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import StringIO
import json
import re
from typing import Mapping

from src.evaluation.official_release_provenance import (
    PINNED_RUNS_SHA,RUNS_MODELS,G0_BLOCKED
)

SCORE_FIELDS=("geometry","semantics","topology","final_score")
REQUIRED_FIELDS=frozenset((*SCORE_FIELDS,"task_id","operation","category"))
TASK_PATTERN=re.compile(
    r"^[A-Z]{3}-(CRE|UPD|DEL)-(DIR|SPA|TOP)-(A|R)-[0-9]{3}$"
)
OPERATIONS={"CRE":"create","UPD":"update","DEL":"delete"}
CATEGORIES={"DIR":"direct","SPA":"spatial","TOP":"topological"}
ROUNDING_BOUND=Decimal("0.0001")
SUMMARY_BOUND=Decimal("0.000051")
STRICT_THRESHOLD=Decimal("0.98")
MAX_CSV_BYTES=300_000
MAX_SUMMARY_BYTES=45_000

class PublicScoreAuditBlocked(ValueError):
    """Missing/changed published evidence or publication arithmetic."""


def _bounded_decimal(value:str,name:str)->Decimal:
    if not isinstance(value,str) or not value or len(value)>40:
        raise PublicScoreAuditBlocked("Invalid public metric field: "+name)
    try:
        result=Decimal(value)
    except InvalidOperation as exc:
        raise PublicScoreAuditBlocked("Invalid numeric public metric: "+name) from exc
    if not result.is_finite() or not Decimal(0)<=result<=Decimal(1):
        raise PublicScoreAuditBlocked("Out-of-range public metric: "+name)
    return result


def _bounded_summary_number(value,name:str)->Decimal:
    if isinstance(value,bool) or not isinstance(value,(int,float,str)):
        raise PublicScoreAuditBlocked("Invalid summary numeric field "+name)
    return _bounded_decimal(str(value),name)


def audit_one_published_csv(model:str,raw_csv:bytes,summary:dict,
                            *,expected_n:int=324)->tuple[dict,frozenset[str]]:
    """Returns aggregate-only evidence plus private IDs used only for pairing.

    Source 'prompt'/'ground_truth_ifc' columns are deliberately ignored,
    uninspected and never returned. The caller must NOT persist the IDs.
    """
    if model not in RUNS_MODELS:
        raise PublicScoreAuditBlocked("Unknown published model folder")
    if (not isinstance(raw_csv,bytes) or not 40<=len(raw_csv)<=MAX_CSV_BYTES
            or not isinstance(summary,dict)):
        raise PublicScoreAuditBlocked("Missing, oversized or invalid public CSV/summary")
    if type(expected_n) is not int or not 2<=expected_n<=324:
        raise PublicScoreAuditBlocked("Invalid expected public task count")
    try:
        document=raw_csv.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise PublicScoreAuditBlocked("Invalid UTF-8 in public CSV") from exc
    reader=csv.DictReader(StringIO(document,newline=""),restkey="_EXTRA_FIELDS")
    if (reader.fieldnames is None
            or len(reader.fieldnames)!=len(set(reader.fieldnames))
            or not REQUIRED_FIELDS.issubset(reader.fieldnames)):
        raise PublicScoreAuditBlocked("Public score CSV header missing or duplicated")
    seen=set()
    sums={key:Decimal(0) for key in SCORE_FIELDS}
    operation_counts=Counter()
    category_counts=Counter()
    scene_counts=Counter()
    strict_count=0
    max_row_rounding=Decimal(0)
    for row in reader:
        if None in row or "_EXTRA_FIELDS" in row:
            raise PublicScoreAuditBlocked("Unexpected unbounded public CSV fields")
        task_id=row.get("task_id")
        match=TASK_PATTERN.fullmatch(task_id or "")
        if not match or task_id in seen:
            raise PublicScoreAuditBlocked("Malformed or duplicate public task ID")
        op,cat,scene=match.groups()
        if row.get("operation")!=OPERATIONS[op] or row.get("category")!=CATEGORIES[cat]:
            raise PublicScoreAuditBlocked("Published task ID and category mismatch")
        seen.add(task_id)
        values={name:_bounded_decimal(row[name],name) for name in SCORE_FIELDS}
        difference=abs(values["final_score"]-sum(
            (values[name] for name in SCORE_FIELDS[:3]),Decimal(0))/3)
        if difference>ROUNDING_BOUND:
            raise PublicScoreAuditBlocked("Published per-task final differs from axis mean")
        max_row_rounding=max(max_row_rounding,difference)
        for name,value in values.items():
            sums[name]+=value
        strict_count+=all(values[name]>=STRICT_THRESHOLD
                          for name in SCORE_FIELDS[:3])
        operation_counts[OPERATIONS[op]]+=1
        category_counts[CATEGORIES[cat]]+=1
        scene_counts[scene]+=1
        if len(seen)>expected_n:
            raise PublicScoreAuditBlocked("Too many public tasks")
    n=len(seen)
    if n<expected_n-1:
        raise PublicScoreAuditBlocked("Published task coverage below conservative minimum")
    overall=summary.get("overall")
    if not isinstance(overall,dict) or (
        type(overall.get("n_tasks")) is not int or overall["n_tasks"]!=n
        or type(overall.get("n_samples")) is not int or overall["n_samples"]!=n
    ):
        raise PublicScoreAuditBlocked("Published summary denominator does not match rows")
    differences={}
    for name in SCORE_FIELDS:
        summary_field=name+"_mean"
        observed_mean=sums[name]/n
        expected=_bounded_summary_number(overall.get(summary_field),summary_field)
        diff=abs(observed_mean-expected)
        if diff>SUMMARY_BOUND:
            raise PublicScoreAuditBlocked("Published aggregate mean differs from per-task CSV")
        differences[name]=str(diff)
    published_scene=summary.get("by_scene_type")
    if not isinstance(published_scene,dict):
        raise PublicScoreAuditBlocked("Published scene grouping missing")
    labeled={}
    for name,payload in published_scene.items():
        if (not isinstance(name,str) or not isinstance(payload,dict)
                or type(payload.get("n_tasks")) is not int):
            raise PublicScoreAuditBlocked("Invalid published scene group")
        labeled[name]=payload["n_tasks"]
    mismatch=(labeled.get("realistic")==n and labeled.get("artificial",0)==0
              and scene_counts["A"]>0)
    evidence={
        "model":model,
        "source_kind":"author-published-per-task-CSV-not-official-code",
        "raw_csv_sha256":sha256(raw_csv).hexdigest(),
        "raw_csv_utf8_bytes":len(raw_csv),
        "published_rows":n,
        "unique_public_task_ids":n,
        "task_count_expected_from_full_benchmark":expected_n,
        "published_rows_short_of_full_324":expected_n-n,
        "operation_counts":dict(sorted(operation_counts.items())),
        "instruction_category_counts":dict(sorted(category_counts.items())),
        "task_id_scene_counts":dict(sorted(scene_counts.items())),
        "public_summary_scene_labels":dict(sorted(labeled.items())),
        "scene_summary_label_mismatch_warning":mismatch,
        "per_row_final_arithmetic_within_rounding":True,
        "max_per_row_rounding_difference":str(max_row_rounding),
        "means_match_published_summary_within_rounding":True,
        "max_mean_rounding_difference":str(max(Decimal(x) for x in differences.values())),
        "strict_three_axis_count_from_published_rows":int(strict_count),
        "strict_threshold":str(STRICT_THRESHOLD),
        "per_task_model_prompts_or_GT_paths_exported":False,
        "independent_scorer_executed_against_public_IFC":False,
        "official_score_reproduced_from_IFC":False,
    }
    return evidence,frozenset(seen)


def audit_published_model_set(raw:Mapping[str,tuple[bytes,dict]])->dict:
    if set(raw)!=RUNS_MODELS:
        raise PublicScoreAuditBlocked("Incomplete seven-model published report set")
    records={}
    private_sets={}
    for model in sorted(RUNS_MODELS):
        pair=raw[model]
        if not isinstance(pair,tuple) or len(pair)!=2:
            raise PublicScoreAuditBlocked("Invalid model report pair")
        detail,ids=audit_one_published_csv(model,pair[0],pair[1])
        records[model]=detail
        private_sets[model]=ids
    # Six 324-row sets should agree exactly. No IDs or individual result rows
    # are ever serialized into the public report.
    complete={model:ids for model,ids in private_sets.items()
              if len(ids)==324}
    if len(complete)<1:
        raise PublicScoreAuditBlocked("No published full reference task set")
    representative=next(iter(complete.values()))
    if any(ids!=representative for ids in complete.values()):
        raise PublicScoreAuditBlocked("Published full-model task ID sets differ")
    for model,ids in private_sets.items():
        if not ids.issubset(representative):
            raise PublicScoreAuditBlocked("Published partial run contains unexpected task ID")
        records[model]["task_ids_match_full_reference_set"]=len(ids)==324
        records[model]["missing_id_count_vs_six_full_runs"]=len(representative-ids)
    short_models=sorted(name for name,x in records.items()
                        if x["missing_id_count_vs_six_full_runs"]>0)
    return {
        "status":"AUTHOR_REPORTED_CSV_ARITHMETIC_VERIFIED_SCORER_STILL_BLOCKED",
        "release_revision":PINNED_RUNS_SHA,
        "verified_published_models":len(records),
        "full_324_row_models":len(complete),
        "published_models_with_missing_rows":short_models,
        "total_missing_published_task_rows":sum(
            r["published_rows_short_of_full_324"] for r in records.values()),
        "models":records,
        "official_executable_scorer_verified":False,
        "local_independent_scorer_metric_origin":"independent-reimplementation",
        "numerical_official_evaluator_equivalence_verified":False,
        "native_IFC_or_GT_files_downloaded":0,
        "per_task_results_exported_or_committed":False,
        "paid_model_provider_calls":0,
        "official_tasks_scored_by_this_project":0,
        "G2_G3_live_model_or_official_scoring_gate_ready":False,
        "official_release_gate":G0_BLOCKED,
    }
