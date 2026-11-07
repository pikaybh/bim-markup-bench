"""Offline BIM markup pilot dispatcher. There is deliberately NO live-run API.

Entry: ./bin/bench or python -m src.runner.cli
Subcommands:
    doctor, validate-data, run, score, report
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

import jsonschema

from src.data.bim_edit import read_tasks,validate_tasks,AuditError
from src.runner.costs import TrialBudgetError
from src.runner.manifest import RunManifestError
from src.runner.offline import (
    OfflineRunError, load_offline_configuration,read_mock_task_list,
    run_mock_schedule,OFFLINE_STATUS
)
from src.runner.sandbox import approved_execution_status
from src.runner.agent_visibility import VisibilityError

DEFAULT_CONFIG=Path("configs/experiment.sample.yaml")
DEFAULT_TASKS=Path("tests/fixtures/offline_two_tasks.json")
DEFAULT_SOURCE=Path("tests/fixtures/synthetic/input.ifc")


def _json(value:dict)->None:
    print(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False))


def _parse_seeds(raw:str)->tuple[int,...]:
    try:
        value=tuple(int(x.strip(),10) for x in raw.split(","))
    except ValueError as exc:
        raise OfflineRunError("Comma-separated seeds must be integers") from exc
    if not value or any(x<0 for x in value) or len(set(value))!=len(value):
        raise OfflineRunError("Seeds must be unique nonnegative integers")
    return value


def _doctor(enforce:bool=False)->int:
    from importlib.metadata import version
    import platform
    evidence=approved_execution_status().as_dict()
    _json({
        "status":"BLOCKED_FOR_LIVE_PILOT",
        "python_version":platform.python_version(),
        "ifcopenshell_version":version("ifcopenshell"),
        "source_file_editing":"OFFLINE_STUB_SUPPORTED",
        "python_control_execution":"DISABLED",
        "online_provider_calling":"DISABLED",
        "official_evaluator_available":False,
        "G1_release_status":"BLOCKED_NO_OFFICIAL_EVALUATION",
        "G2_OS_isolation":evidence,
        "offline_mock_scheduler_available":True,
    })
    return 2 if enforce else 0


def _validate(args:argparse.Namespace)->int:
    if args.official_metadata:
        data=read_tasks(args.official_metadata)
        result=validate_tasks(data,full=True)
        _json({
            "status":"PUBLIC_METADATA_VALIDATED_IFC_CONTENT_NOT_VERIFIED",
            "task_count":result["record_count"],
            "strata":result["num_strata"],
            "native_IFC_assets_checked":0,
            "official_tasks_scored":0,
        })
    else:
        task=read_mock_task_list(args.task_list)
        _json({
            "status":"OWN_SYNTHETIC_TASK_ENVELOPES_VALIDATED",
            "task_count":len(task),
            "GT_annotations_exposed":False,
            "real_IFC_content_scored":False,
        })
    return 0


def _run(args:argparse.Namespace)->int:
    if not args.offline_mock:
        raise OfflineRunError(
            "Non-mock execution is forbidden: #19 container isolation and official G1 are blocked"
        )
    config=load_offline_configuration(args.budget)
    if args.model!=config["model_id"]:
        raise OfflineRunError("Requested model differs from frozen config")
    tasks=read_mock_task_list(args.task_list)
    result=run_mock_schedule(
        source_ifc=args.input_ifc,
        tasks=tasks,
        config=config,
        output_root=args.output_root,
        seeds=_parse_seeds(args.seeds),
        shuffle_seed=args.shuffle_seed,
        arm_filter=args.arm,
        attempt=args.attempt,
        resume=args.resume,
    )
    _json(result)
    return 0


def _score(args:argparse.Namespace)->int:
    _json({
        "status":"BLOCKED_OFFICIAL_SCORER_NOT_VERIFIED",
        "score":None,
        "official_tasks_scored":0,
        "data_leakage_guard":"NO_GT_OR_SCORER_MOUNT_IN_MOCK",
        "paid_pilot_authorized":False,
    })
    return 2


def _report(args:argparse.Namespace)->int:
    from hashlib import sha256
    from src.runner.offline import RUN_SCHEMA_PATH
    schema=json.loads(RUN_SCHEMA_PATH.read_text())
    output=args.output_root
    if output.is_symlink() or not output.is_dir():
        raise OfflineRunError("No safe prior run output directory")
    manifests=output/"manifests"
    if manifests.is_symlink() or not manifests.is_dir():
        raise OfflineRunError("No manifest directory")
    records=[]
    for p in sorted(manifests.glob("*.json")):
        if p.is_symlink() or not p.is_file():
            raise OfflineRunError("Unsafe manifest file")
        record=json.loads(p.read_text(encoding="utf-8"))
        jsonschema.validate(record,schema)
        if p.stem!=record.get("run_id"):
            raise RunManifestError("Manifest filename and run ID mismatch")
        if record.get("status") not in (
            OFFLINE_STATUS,"BLOCKED_TOKEN_BUDGET","BLOCKED_WALL_TIME"
        ):
            raise RunManifestError("Unsupported offline run status")
        if record.get("result_sha") is not None or record.get("llm_calls")!=0:
            raise RunManifestError("Mock report contains a false real model/IFC result")
        from src.runner.manifest import verify_record_artifacts
        verify_record_artifacts(output,record)
        refs=record.get("artifact_refs")
        if not isinstance(refs,dict):
            raise RunManifestError("Missing artifact references")
        for path in refs.values():
            if not isinstance(path,str) or not path.startswith(
                "trials/"+record["run_id"]+"/"
            ):
                raise RunManifestError("Untrusted artifact reference")
            item=output/path
            if item.is_symlink() or not item.is_file() or not item.resolve().is_relative_to(output.resolve()):
                raise RunManifestError("Missing, linked or escaped result artifact")
        data=(output/refs["raw_response"]).read_bytes()
        if sha256(data).hexdigest()!=record["raw_response_sha256"]:
            raise RunManifestError("Mock response bytes changed after recording")
        source=(output/refs["source"]).read_bytes()
        if sha256(source).hexdigest()!=record["source_artifact_sha256"]:
            raise RunManifestError("Recorded source file changed")
        records.append(record)
    if not records:
        raise OfflineRunError("No offline records to report")
    statuses=sorted({r["status"] for r in records})
    _json({
        "status":"OFFLINE_RECORD_INTEGRITY_CHECKED_NO_SCORES",
        "total_records":len(records),
        "unique_run_ids":len({r["run_id"] for r in records}),
        "statuses":{x:sum(r["status"]==x for r in records) for x in statuses},
        "arms":{x:sum(r["arm"]==x for r in records)
                for x in ("direct_xml","imperative_python")},
        "seed_count":len({r["seed"] for r in records}),
        "official_tasks_scored":0,
        "provider_model_calls":0,
        "paid_spend_usd":None,
        "evidence":"MODEL_INPUT_AND_MOCK_RESPONSE_SHA256_VERIFIED",
    })
    return 0


def main(argv:Sequence[str]|None=None)->int:
    cli=argparse.ArgumentParser(prog="bench",
        description="Reproducible offline BIM markup experiment. No paid model run capability.")
    commands=cli.add_subparsers(dest="command",required=True)
    doctor=commands.add_parser("doctor")
    doctor.add_argument("--enforce",action="store_true",
        help="Exit nonzero until actual OS isolation and scorer are ready")
    validate=commands.add_parser("validate-data")
    validate.add_argument("--task-list",type=Path,default=DEFAULT_TASKS)
    validate.add_argument("--official-metadata",type=Path)
    run=commands.add_parser("run")
    run.add_argument("--offline-mock",action="store_true",required=False)
    run.add_argument("--task-list",type=Path,default=DEFAULT_TASKS)
    run.add_argument("--input-ifc",type=Path,default=DEFAULT_SOURCE)
    run.add_argument("--arm",choices=["both","direct_xml","imperative_python"],default="both")
    run.add_argument("--model",default="offline/mock-v0")
    run.add_argument("--seeds",default="11,29")
    run.add_argument("--shuffle-seed",type=int,default=1234)
    run.add_argument("--budget",type=Path,default=DEFAULT_CONFIG)
    run.add_argument("--output-root",type=Path,required=True)
    run.add_argument("--attempt",type=int,default=0)
    run.add_argument("--resume",action="store_true")
    score=commands.add_parser("score")
    report=commands.add_parser("report")
    report.add_argument("--output-root",type=Path,required=True)
    args=cli.parse_args(argv)
    try:
        if args.command=="doctor":
            return _doctor(args.enforce)
        if args.command=="validate-data":
            return _validate(args)
        if args.command=="run":
            return _run(args)
        if args.command=="score":
            return _score(args)
        if args.command=="report":
            return _report(args)
        raise OfflineRunError("Unknown command")
    except (OfflineRunError,TrialBudgetError,RunManifestError,
            VisibilityError,AuditError,OSError,ValueError,KeyError,
            jsonschema.ValidationError) as exc:
        _json({
            "status":"BLOCKED_OR_INVALID",
            "reason":type(exc).__name__,
            "model_api_calls":0,
            "official_tasks_scored":0,
        })
        return 2


if __name__=="__main__":
    raise SystemExit(main())
