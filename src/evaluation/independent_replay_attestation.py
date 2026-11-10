"""Independent scorer qualification: reproducible grader-private IFC replay.

Does NOT implement, call, wrap, or claim equivalence with the BIM-Edit
official scorer. All cases are frozen repo-OWN synthetic IFC fixtures;
public author reported model predictions, per-task GT, and agent-visible
contexts are never loaded.

This separate gate leaves the v0.1 scorer/sampling policy and benchmark
metrics UNCHANGED, and tests only current scorer invariants. It cannot
authorize real G2/G3 scoring, model inference or live provider billing.
"""
from __future__ import annotations

from hashlib import sha256
import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import jsonschema

from src.evaluation.bim_edit_scorer import (
    EVALUATOR_VERSION,PROVENANCE,STRICT_THRESHOLD,
    score_ifc_result
)
from src.evaluation.calibration import (
    SRC,WALL_GT,CATALOG,build_calibration_artifacts,_grading_task,
)
from src.evaluation.geometry_metrics import GeometrySettings

ROOT=Path(__file__).resolve().parents[2]
SCHEMA_PATH=ROOT/"schemas/score_result.schema.json"
EXPECTED_OWN_SOURCE_SHA256="10d57d3eeb6e50fb51493b03d7cb508d57eadeb76719afaeb71fa6658c3ecf58"
EXPECTED_OWN_REFERENCE_SHA256="bb93df8babb11612f4c81f60145a7cf520ef7e19f3abfe49731bf45d92ccda6b"
EXPECTED_SCORE_SCHEMA_SHA256="06aecf3712faeaf64681c5b5bd7ada41c95c89c9566aea6e18e1f2c62bcdac4d"
EXPECTED_FROZEN_CATALOG_SHA256="678c469281e41de368be1ba4f3f27b8dd1fdaa393278a7b0b15e7952137b5806"
# Code-byte integrity prevents silent scorer edits without a newly reviewed
# versioned qualification fixture. None of these implementation files
# are modified by the scorer replay.
EXPECTED_LOCAL_SCORER_SOURCE_SHA256={
    "bim_edit_scorer.py":"d6e4ccb238a7deaf9bcd6c9d6b0998cfaeb367c1d3036ebd332e503327c12288",
    "geometry_metrics.py":"47b9bc8d6e6a32f62cb15b15397a57c814d750ad71c897cd929f20b65bb14e2c",
    "semantic_diff.py":"c67afc9db5f3d647a3e20a17b2970565d0429e97d7761a40557ea4cb6f5f6f33",
    "topology_metrics.py":"4cddaacc54ff0f0d88ec044212a4185721c57399771bc71928139d373f70ff90",
}
QUALIFICATION_CASES=(
    "update_identical_reference",
    "update_wrong_height",
    "update_missing_space_boundary",
    "update_collateral_door_deletion",
    "invalid_candidate_bytes",
    "create_equivalent_new_guid",
    "delete_window_correct",
    "changed_ifc_length_units",
)
ALLOWED_STATUS=("INDEPENDENT_IFC_SCORED",
                "INVALID_OUTPUT_IFC","BLOCKED_IFC_UNIT_MISMATCH")


class QualificationBlocked(ValueError):
    """Fail closed on scorer provenance or nonrepeatability."""


def _sha(path:Path)->str:
    if path.is_symlink() or not path.is_file():
        raise QualificationBlocked("Missing or redirected own synthetic IFC")
    return sha256(path.read_bytes()).hexdigest()


def _stable_digest(row:dict)->str:
    return sha256(json.dumps(row,sort_keys=True,allow_nan=False,
                             separators=(",",":")).encode("utf8")).hexdigest()


def verify_independent_score_record(record:dict,schema:dict, *,
                                    expected_status:str,
                                    expected_strict:bool,
                                    expected_hashes:tuple[str,str,str])->dict:
    """Validate the actual scorer's schema, exact provenance and invariants.

    This verifies neither official BIM-Edit equivalence nor correctness of
    the three independently implemented geometric/semantic/topology formulas.
    """
    if not isinstance(record,dict) or not isinstance(schema,dict):
        raise QualificationBlocked("Invalid scorer record/schema")
    try:
        jsonschema.validate(record,schema)
    except jsonschema.ValidationError as exc:
        raise QualificationBlocked("Independent scorer output schema violated") from exc
    if (record["metric_origin"]!=PROVENANCE
        or record["scorer_version"]!=EVALUATOR_VERSION
        or record["official_bim_edit_evaluator_equivalent"] is not False
        or record["scored_official_dataset"] is not False
        or record["model_provider_calls"]!=0):
        raise QualificationBlocked("Forged scorer origin or official/model claim")
    if record["source_or_gt_mutated"]:
        raise QualificationBlocked("Source/GT/output was mutated during scoring")
    keys=("source_ifc_sha256","ground_truth_ifc_sha256","result_ifc_sha256")
    if tuple(record[k] for k in keys)!=expected_hashes:
        raise QualificationBlocked("Scorer hashed a different IFC triple")
    if record["status"]!=expected_status or record["status"] not in ALLOWED_STATUS:
        raise QualificationBlocked("Unexpected independent scorer status")
    if type(record["strict_pass"]) is not bool or record["strict_pass"]!=expected_strict:
        raise QualificationBlocked("Independent strict pass decision changed")
    axes=(record[k] for k in ("geometry","semantics","topology"))
    axes=tuple(axes)
    if record["status"]=="INDEPENDENT_IFC_SCORED":
        if any(x is None for x in axes):
            raise QualificationBlocked("Scored IFC without all three numeric axes")
        if record["final_score"] is None:
            raise QualificationBlocked("Scored IFC without final mean")
        if abs(record["final_score"]-sum(axes)/3)>1e-12:
            raise QualificationBlocked("Independent scorer component-mean invariant failed")
        collateral=record["collateral_detail"]
        if not isinstance(collateral,dict):
            raise QualificationBlocked("Scored IFC has no native collateral audit")
        qualifies=(all(x>=STRICT_THRESHOLD for x in axes)
                   and collateral.get("collateral_clean") is True
                   and not record["failure_codes"])
        if record["strict_pass"] is not qualifies:
            raise QualificationBlocked("Independent strict pass not explainable by axes/collateral")
    elif record["status"]=="INVALID_OUTPUT_IFC":
        if (axes!=(0.,0.,0.) or record["final_score"]!=0
                or record["strict_pass"]):
            raise QualificationBlocked("Invalid IFC candidate did not fail zero")
    else:
        if (any(x is not None for x in axes)
                or record["final_score"] is not None
                or record["strict_pass"]):
            raise QualificationBlocked("Blocked reference/units invented a numeric score")
    return {
        "record_sha256":_stable_digest(record),
        "metric_origin":PROVENANCE,
        "status":record["status"],
        "strict_pass":record["strict_pass"],
        "failure_code_count":len(record["failure_codes"]),
        "score_fields_present":all(x is not None for x in axes),
        "local_three_axis_version":EVALUATOR_VERSION,
        "official_equivalence_proven":False,
    }


def run_own_ifc_replay_qualification()->dict:
    """Exercise three operation types and known negative statuses twice.

    Runs in a temp grader-only fixture directory; no LLM, vendor, official
    evaluator, public benchmark input/GT, or modified frozen scorer source.
    """
    if _sha(SRC)!=EXPECTED_OWN_SOURCE_SHA256:
        raise QualificationBlocked("Pinned OWN source IFC has been modified")
    expected_files=(
        (WALL_GT,EXPECTED_OWN_REFERENCE_SHA256),
        (CATALOG,EXPECTED_FROZEN_CATALOG_SHA256),
        (SCHEMA_PATH,EXPECTED_SCORE_SCHEMA_SHA256),
    )
    for path,expected in expected_files:
        if _sha(path)!=expected:
            raise QualificationBlocked("Frozen OWN GT/schema/catalog digest mismatch")
    scorer_files={
        name:(ROOT/"src"/"evaluation"/name)
        for name in EXPECTED_LOCAL_SCORER_SOURCE_SHA256
    }
    for name,path in scorer_files.items():
        if _sha(path)!=EXPECTED_LOCAL_SCORER_SOURCE_SHA256[name]:
            raise QualificationBlocked("Frozen independent scorer code changed")
    frozen=json.loads(CATALOG.read_text("utf8"))
    catalog={r["id"]:r for r in frozen["cases"]}
    if (len(catalog)!=len(frozen["cases"]) or
            len(frozen["cases"])!=17 or
            not set(QUALIFICATION_CASES).issubset(catalog)):
        raise QualificationBlocked("Frozen OWN evaluator fixture catalog diverged")
    schema=json.loads(SCHEMA_PATH.read_text("utf8"))
    grader_signature=inspect.signature(score_ifc_result)
    if any(name in grader_signature.parameters for name in (
            "arm","agent","prompt","xml","python_source","provider")):
        raise QualificationBlocked("Independent scorer exposed agent arm/source")
    hashes_before=(_sha(SRC),_sha(WALL_GT),_sha(CATALOG),_sha(SCHEMA_PATH))
    results=[]
    with TemporaryDirectory(prefix="bim-own-independent-grader-replay-") as td:
        files=build_calibration_artifacts(Path(td))
        references={
            "wall_update":files["wall_gt"],
            "wall_pset":files["wall_pset_gt"],
            "wall_create":files["create_gt"],
            "window_delete":files["delete_window"],
        }
        for case_id in QUALIFICATION_CASES:
            case=catalog[case_id]
            reference=references[case["task"]]
            prediction=files[case["condition"]]
            expected_hashes=(_sha(SRC),_sha(reference),_sha(prediction))
            task=_grading_task(case["task"])
            first=score_ifc_result(source_ifc=SRC,ground_truth_ifc=reference,
                                  result_ifc=prediction,task=task)
            second=score_ifc_result(source_ifc=SRC,ground_truth_ifc=reference,
                                   result_ifc=prediction,task=task)
            proof=verify_independent_score_record(
                first,schema,expected_status=case["status"],
                expected_strict=case["strict_pass"],
                expected_hashes=expected_hashes)
            duplicate=verify_independent_score_record(
                second,schema,expected_status=case["status"],
                expected_strict=case["strict_pass"],
                expected_hashes=expected_hashes)
            if proof["record_sha256"]!=duplicate["record_sha256"] or first!=second:
                raise QualificationBlocked("Non-deterministic IFC grader replay")
            if tuple(_sha(path) for path in (SRC,reference,prediction))!=expected_hashes:
                raise QualificationBlocked("IFC fixture bytes changed while evaluating")
            proof["case"]=case_id
            proof["exact_repeated_result_equal"]=True
            proof["IFC_triplet_sha256"]=list(expected_hashes)
            proof["official_tasks_scored"]=0
            results.append(proof)
    if tuple(_sha(path) for path in (SRC,WALL_GT,CATALOG,SCHEMA_PATH))!=hashes_before:
        raise QualificationBlocked("Frozen local fixture or score schema mutated")
    for name,path in scorer_files.items():
        if _sha(path)!=EXPECTED_LOCAL_SCORER_SOURCE_SHA256[name]:
            raise QualificationBlocked("Scorer implementation mutated during replay")
    if len(results)!=len(QUALIFICATION_CASES):
        raise QualificationBlocked("Expected independent replay cases absent")
    if sum(int(row["strict_pass"]) for row in results)!=3:
        raise QualificationBlocked("Unexpected positive OWN replay case count")
    return {
        "status":"OWN_INDEPENDENT_IFC_REPLAY_VERIFIED_OFFICIAL_PARITY_BLOCKED",
        "case_count":len(results),
        "repetitions_per_case":2,
        "own_synthetic_strict_pass_cases":3,
        "own_synthetic_nonpassing_or_blocked_cases":len(results)-3,
        "metric_origin":PROVENANCE,
        "scorer_version":EVALUATOR_VERSION,
        "geometry_version":GeometrySettings().metric_version,
        "geometry_sample_count":GeometrySettings().sample_count,
        "geometry_seed":GeometrySettings().random_seed,
        "score_schema_sha256":hashes_before[3],
        "frozen_scorer_implementation_source_sha256":
            dict(sorted(EXPECTED_LOCAL_SCORER_SOURCE_SHA256.items())),
        "frozen_case_catalog_sha256":hashes_before[2],
        "own_source_ifc_sha256":hashes_before[0],
        "own_reference_ifc_sha256":hashes_before[1],
        "all_repeats_identical":True,
        "all_scorer_outputs_match_frozen_json_schema":True,
        "all_input_output_IFC_unchanged":True,
        "author_published_csv_used_as_training_target":False,
        "author_executable_scorer_obtained":False,
        "official_equivalence_numerically_verified":False,
        "published_per_task_csv_regraded":False,
        "public_benchmark_ifc_or_GT_loaded":False,
        "model_provider_calls":0,
        "official_benchmark_tasks_scored":0,
        "G2_G3_live_official_pilot_ready":False,
        "cases":results,
    }
