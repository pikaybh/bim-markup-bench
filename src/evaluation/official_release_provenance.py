"""Official BIM-Edit PUBLIC RELEASE evidence audit, never a scorer.

Source metadata only: inspect pinned Hugging Face repo *filenames* and one
author-released aggregate summary. Never fetch/download source or GT IFCs,
per-task answers, edited IFCs, model traces, or full 3D files.

A paper-reported mean can be compared with a released summary without
proving an executable evaluator, matching scoring implementation, or any
D0-versus-I0 scientific hypothesis. All result statuses are fail-closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal,InvalidOperation
from hashlib import sha256
import json
import re
from typing import Any


RUNS_ID="BIM-Edit/BIM-Edit-runs"
PINNED_RUNS_SHA="9241abc9b3b4efa3906c0bdabcf3321f1558192f"
RUNS_MODELS=frozenset({
    "claude-sonnet","deepseek-v3.2","gemini-flash-3.0",
    "gemma4-31B","gpt-5.4-mini","gpt-5.4","qwen3.6-plus",
})
EXPECTED_EVAL_FILES=frozenset({
    "eval/per_task.csv","eval/report.csv",
    "eval/resolved_defaults.json","eval/summary.json",
})
# Reported rounded values in Section 4.2, Table 1 (Claude Sonnet 4.6).
PAPER_CLAUDE={
    "geometry_mean":Decimal("0.5590"),
    "semantics_mean":Decimal("0.3385"),
    "topology_mean":Decimal("0.4619"),
    "final_score_mean":Decimal("0.4531"),
}
G0_BLOCKED="BLOCKED_OFFICIAL_EXECUTABLE_EVALUATOR_NOT_VERIFIED"


class OfficialReleaseEvidenceError(ValueError):
    """Do not mark author-published results as executable scorer evidence."""


def _decimal(value:Any,field:str)->Decimal:
    if isinstance(value,bool) or not isinstance(value,(int,float,str,Decimal)):
        raise OfficialReleaseEvidenceError("Invalid summary field type: "+field)
    try:
        number=Decimal(str(value))
    except (InvalidOperation,ValueError) as exc:
        raise OfficialReleaseEvidenceError("Invalid decimal summary: "+field) from exc
    if not number.is_finite() or not Decimal(0)<=number<=Decimal(1):
        raise OfficialReleaseEvidenceError("Out-of-range summary fraction: "+field)
    return number


def _public_file_paths(metadata:dict)->set[str]:
    if metadata.get("sha")!=PINNED_RUNS_SHA:
        raise OfficialReleaseEvidenceError("Wrong/unpinned public runs revision")
    siblings=metadata.get("siblings")
    if not isinstance(siblings,list) or len(siblings)<100:
        raise OfficialReleaseEvidenceError("Incomplete public runs metadata list")
    paths=[]
    for row in siblings:
        if not isinstance(row,dict):
            raise OfficialReleaseEvidenceError("Malformed public runs file record")
        path=row.get("rfilename")
        if (not isinstance(path,str) or not path
                or "\\" in path or path.startswith("/")
                or ".." in path.split("/") or path.endswith("/")):
            raise OfficialReleaseEvidenceError("Invalid release path inventory")
        paths.append(path)
    if len(paths)!=len(set(paths)):
        raise OfficialReleaseEvidenceError("Duplicate artifact path inventory")
    return set(paths)


def inventory_public_runs(metadata:dict)->dict:
    """Pure verification of author release artifacts, not reading any GT."""
    paths=_public_file_paths(metadata)
    per_model={}
    for model in sorted(RUNS_MODELS):
        present={x[len(model)+1:] for x in paths
                 if x.startswith(model+"/")}
        missing=sorted(EXPECTED_EVAL_FILES-present)
        if missing:
            raise OfficialReleaseEvidenceError(
                "Published model evaluation report inventory incomplete: "+model)
        per_model[model]={
            "named_evaluation_reports_present":True,
            "required_eval_file_count":len(EXPECTED_EVAL_FILES),
            "evaluation_report_file_count":sum(
                path.startswith("eval/") for path in present),
            "has_per_task_csv":"eval/per_task.csv" in present,
            "has_summary_json":"eval/summary.json" in present,
            "model_output_files_not_downloaded":True,
        }
    # These are filename candidates only. Absence in HF runs snapshot is
    # NOT evidence no source code exists in another repo or submission.
    executables=sorted(p for p in paths if p.lower().endswith(
        (".py",".pyi",".ipynb",".whl",".tar.gz",".zip",".pex",".sh",".toml")))
    return {
        "source":"author-published-huggingface-runs-metadata",
        "repo_id":RUNS_ID,
        "pinned_revision":PINNED_RUNS_SHA,
        "public_file_count":len(paths),
        "author_report_model_count":len(per_model),
        "models":per_model,
        "possible_executable_artifacts_in_THIS_runs_revision":len(executables),
        "executables_in_THIS_runs_revision":executables[:20],
        "other_repos_or_submission_code_availability":"NOT_ESTABLISHED",
        "official_evaluator_entrypoint_verified":False,
        "official_evaluator_version_or_license_file_verified":False,
        "official_evaluator_equivalence_verified":False,
    }


def audit_published_claude_summary(summary:dict)->dict:
    """Check published aggregate numbers against the PAPER (not raw IFC)."""
    if not isinstance(summary,dict) or not isinstance(summary.get("overall"),dict):
        raise OfficialReleaseEvidenceError("Published summary overall missing")
    overall=summary["overall"]
    if (type(overall.get("n_tasks")) is not int or overall["n_tasks"]!=324
            or type(overall.get("n_samples")) is not int
            or overall["n_samples"]!=324):
        raise OfficialReleaseEvidenceError("Expected all 324 reported tasks")
    measured={}
    differences={}
    for field,paper in PAPER_CLAUDE.items():
        reported=_decimal(overall.get(field),field)
        differences[field]=abs(paper-reported)
        measured[field]=str(reported)
        if differences[field]>Decimal("0.0001"):
            raise OfficialReleaseEvidenceError(
                "Published aggregate and paper Table 1 mismatch: "+field)
    arithmetic=sum(
        (_decimal(overall[name],name) for name in (
            "geometry_mean","semantics_mean","topology_mean"
        )),Decimal(0))/Decimal(3)
    if abs(arithmetic-_decimal(overall["final_score_mean"],"final_score_mean"))>Decimal("0.0001"):
        raise OfficialReleaseEvidenceError(
            "Published aggregate axes do not average to final")
    by_scene=summary.get("by_scene_type",{})
    if not isinstance(by_scene,dict):
        raise OfficialReleaseEvidenceError("Invalid by_scene_type summary")
    # The published task card has 162 realistic, 162 synthetic; however
    # this released model summary labels all 324 under 'realistic'.
    # This warns about aggregation LABELS, NOT about per-task accuracy.
    observed_scene={name:item.get("n_tasks")
                    for name,item in by_scene.items()
                    if isinstance(item,dict)
                    and type(item.get("n_tasks")) is int}
    discrepancy=(observed_scene.get("realistic")==324
                 and "artificial" not in observed_scene)
    return {
        "source":"author-published-released-eval-summary",
        "model":"claude-sonnet",
        "n_tasks":324,
        "reported_table1_means":measured,
        "mean_axis_arithmetic_within_publication_rounding":True,
        "paper_table1_rounded_values_match":True,
        "summary_scene_type_label_counts":observed_scene,
        "scene_type_summary_label_may_be_inconsistent_with_task_card":
            discrepancy,
        "release_summary_recomputed_from_raw_IFC":False,
        "official_evaluator_executed":False,
        "independent_evaluator_numerical_parity_tested":False,
    }


def combine_release_evidence(metadata:dict,summary:dict)->dict:
    inventory=inventory_public_runs(metadata)
    calibration=audit_published_claude_summary(summary)
    # A release JSON with results does not identify the executable that
    # computed them. No caller-supplied 'verified' field can change this.
    return {
        "status":G0_BLOCKED,
        "public_reports_confirmed":True,
        "source_inventory":inventory,
        "published_aggregate_check":calibration,
        "official_executable_scorer_available_to_this_project":False,
        "current_local_scorer_metric_origin":"independent-reimplementation",
        "official_scorer_numerically_equivalent_to_local":False,
        "paper_formula_only_is_not_full_ifc_evaluator":True,
        "released_reports_do_not_prove_cross_implementation_parity":True,
        "hidden_ground_truth_accessed":False,
        "task_solutions_accessed":False,
        "paid_model_provider_calls":0,
        "official_tasks_scored_by_this_project":0,
        "G2_G3_paid_or_official_scoring_gate_ready":False,
    }
