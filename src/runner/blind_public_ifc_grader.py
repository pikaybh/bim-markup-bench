"""G2 #21: three PRESELECTED pinned public IFC blind-grader self-checks.

Only trusted research code selects source and GT from byte-verified local
BIM-Edit public audit cache. The candidate/model cannot call this tool,
see target metadata or inspect the hidden reference. This does NOT execute
any model-generated code and uses an INDEPENDENT (NOT OFFICIAL) scorer.

Supported candidate conditions are frozen self-checks:
  reference_self_check, unchanged_source, invalid_output
No arbitrary result path, model prompt, arm identifier or provider API input.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import uuid

from src.data.bim_edit import (
    read_tasks,repo_asset_path,verify_local_asset_bytes,validate_remote_tree
)
from src.data.pilot_asset_audit import _files_in_root
from src.runner.docker_isolation import DockerIsolationError
from src.runner.generated_candidate import _limited_attach
from src.runner.ifc_worker import _run,_sha
from src.evaluation.bim_edit_scorer import PROVENANCE,EVALUATOR_VERSION

ROOT=Path(__file__).resolve().parents[2]
IMAGE_ID=re.compile(r"sha256:[0-9a-f]{64}\Z")
CONTAINER_NAME=re.compile(r"bim-bench-blind-grader-[0-9a-f]{12}\Z")
ALLOWED_TASKS=frozenset({
    "WAL-UPD-TOP-A-001",
    "WAL-DEL-TOP-A-001",
    "DOR-CRE-TOP-A-002",
})
ALLOWED_MODES=frozenset({
    "reference_self_check","unchanged_source","invalid_output",
})
_EXPECTED_LABEL="bim-markup-bench independent blind IFC scorer"
_MAX_ASSET_BYTES=12_000_000
_REPORT_FIELDS=frozenset({
    "task_id","status","scorer_version","metric_origin",
    "official_bim_edit_evaluator_equivalent","official_tasks_scored",
    "geometry","semantics","topology","final_score","strict_pass",
    "failure_codes","reference_or_target_metadata_in_agent_context",
    "paid_model_calls",
})


def verify_blind_image(image_id:str)->None:
    if not isinstance(image_id,str) or not IMAGE_ID.fullmatch(image_id):
        raise DockerIsolationError("Require immutable local SHA256 blind scorer image")
    result=_run(["docker","image","inspect",image_id],timeout=12)
    platform=_run(["docker","info","--format","{{.Architecture}}"],timeout=12)
    if result.returncode or platform.returncode:
        raise DockerIsolationError("Local pinned grader image/Linux daemon absent")
    try:
        images=json.loads(result.stdout)
        if not isinstance(images,list) or len(images)!=1:
            raise ValueError
        actual=images[0]
        expected_arch={"x86_64":"amd64","aarch64":"arm64"}.get(
            platform.stdout.strip(),platform.stdout.strip())
        labels=actual.get("Config",{}).get("Labels") or {}
        conditions=(
            actual.get("Id")==image_id,
            actual.get("Os")=="linux",
            actual.get("Architecture")==expected_arch,
            expected_arch=="amd64",
            actual.get("Config",{}).get("User")=="65534:65534",
            labels.get("org.opencontainers.image.title")==_EXPECTED_LABEL,
            labels.get("org.opencontainers.image.version")==EVALUATOR_VERSION,
        )
        if not all(conditions):
            raise ValueError
    except (ValueError,IndexError,TypeError,KeyError) as exc:
        raise DockerIsolationError("Blind scorer image provenance or architecture invalid") from exc


def verify_blind_container(container_id:str,image_id:str)->None:
    if not isinstance(container_id,str) or not re.fullmatch(r"[0-9a-f]{64}",container_id):
        raise DockerIsolationError("Invalid grader container identity")
    result=_run(["docker","inspect",container_id],timeout=12)
    if result.returncode:
        raise DockerIsolationError("Blind grader prestart Docker inspect failed")
    try:
        data=json.loads(result.stdout)
        if not isinstance(data,list) or len(data)!=1:
            raise ValueError
        info=data[0]
        h=info["HostConfig"];c=info["Config"]
        mounts=info["Mounts"]
        allowed_mounts={"/source","/ground_truth","/prediction","/metadata"}
        mapped={m.get("Destination") for m in mounts}
        env=c.get("Env") or []
        prohibited={"OPENAI_API_KEY","AWS_SECRET_ACCESS_KEY","GH_TOKEN",
                    "SSH_AUTH_SOCK","ARM","EXPERIMENT_ARM"}
        required={
            "source":"/source",
            "gt":"/ground_truth",
            "candidate":"/prediction",
            "trusted_task_meta":"/metadata"
        }
        checks=[
            info.get("Image")==image_id,
            h.get("NetworkMode")=="none",
            h.get("ReadonlyRootfs") is True,
            h.get("Privileged") is False,
            "ALL" in (h.get("CapDrop") or []),
            any("no-new-privileges" in s for s in (h.get("SecurityOpt") or [])),
            h.get("IpcMode")=="none",
            h.get("PidsLimit")==1,
            h.get("Memory")==536870912,
            h.get("MemorySwap")==536870912,
            h.get("NanoCpus")==750000000,
            c.get("User")=="65534:65534",
            c.get("Entrypoint")==["/usr/local/bin/python3"],
            c.get("Cmd")==["/opt/blind/worker.py"],
            len(mounts)==4 and mapped==allowed_mounts,
            all(m.get("Type")=="bind" and m.get("RW") is False for m in mounts),
            all(m.get("Destination") not in ("/task","/output","/agent","/workspace")
                for m in mounts),
            not any(line.split("=",1)[0] in prohibited for line in env),
            "/tmp" in (h.get("Tmpfs") or {}),
            "size=16m" in (h.get("Tmpfs") or {}).get("/tmp",""),
        ]
        if not all(checks):
            raise ValueError
    except (ValueError,KeyError,TypeError,IndexError) as exc:
        raise DockerIsolationError(
            "Blind grader HostConfig/mount/tool/secret validation FAILED before start"
        ) from exc


def _trusted_pinned_task(task_id:str)->tuple[dict,Path,Path]:
    if task_id not in ALLOWED_TASKS:
        raise DockerIsolationError("Only three preregistered public scorer probes allowed")
    tasks=read_tasks(ROOT/"data/tasks.jsonl")
    tree=json.loads((ROOT/"data/bim_edit_remote_tree.json").read_text(encoding="utf-8"))
    validate_remote_tree(tasks,tree)
    frozen=json.loads((ROOT/"manifests/pilot_36_candidate_v0.json").read_text())
    if task_id not in {row["task_id"] for row in frozen["tasks"]}:
        raise DockerIsolationError("Task absent from frozen pilot IDs")
    by_id={row["task_id"]:row for row in tasks}
    task=by_id[task_id]
    entries={row["path"]:row for row in tree if row.get("type")=="file"}
    base=ROOT/"data/ifc"
    locations=[]
    for name in (task["input_ifc"],task["ground_truth_ifc"]):
        rel=repo_asset_path(name)
        file=_files_in_root(base,rel)
        if not file.is_file() or file.is_symlink():
            raise DockerIsolationError("Pinned local source/GT IFC not cached")
        if not 0<file.stat().st_size<=_MAX_ASSET_BYTES:
            raise DockerIsolationError("Public scorer smoke file too large")
        verify_local_asset_bytes(file,entries[rel])
        locations.append(file)
    return task,locations[0],locations[1]


def _checked_public_result(text:str,task_id:str,mode:str)->dict:
    if len(text.encode("utf-8"))>8192:
        raise DockerIsolationError("Blind grader output unexpectedly long")
    lines=text.strip().splitlines()
    if len(lines)!=1:
        raise DockerIsolationError("Blind grader emitted multiple/non-JSON records")
    try:
        report=json.loads(lines[0])
    except (ValueError,TypeError) as exc:
        raise DockerIsolationError("Malformed blind grader result") from exc
    if not isinstance(report,dict) or set(report)!=_REPORT_FIELDS:
        raise DockerIsolationError("Unexpected private data in independent grader result")
    if (report["task_id"]!=task_id
        or report["scorer_version"]!=EVALUATOR_VERSION
        or report["metric_origin"]!=PROVENANCE
        or report["official_bim_edit_evaluator_equivalent"] is not False
        or report["reference_or_target_metadata_in_agent_context"] is not False
        or report["official_tasks_scored"]!=0 or report["paid_model_calls"]!=0
        or type(report["strict_pass"]) is not bool):
        raise DockerIsolationError("Blind grader provenance contract violated")
    if not isinstance(report["failure_codes"],list) or not all(
            isinstance(value,str) and
            re.fullmatch(r"[A-Z][A-Z0-9_]{0,127}",value)
            for value in report["failure_codes"]):
        raise DockerIsolationError("Blind grader failure-code format invalid")
    for key in ("geometry","semantics","topology","final_score"):
        value=report[key]
        if value is not None and (
            type(value) not in (int,float) or not 0.0<=value<=1.0):
            raise DockerIsolationError("Blind grader numeric axis invalid")
    if mode=="reference_self_check":
        if (report["status"]!="INDEPENDENT_IFC_SCORED"
                or report["strict_pass"] is not True
                or any(report[k]!=1.0 for k in
                       ("geometry","semantics","topology","final_score"))):
            raise DockerIsolationError("Frozen reference self-check failed")
    else:
        if report["strict_pass"] is not False:
            raise DockerIsolationError("Invalid or unchanged output passed strict scorer")
        if mode=="unchanged_source" and report["status"]!="INDEPENDENT_IFC_SCORED":
            raise DockerIsolationError("Unmodified public candidate did not evaluate natively")
        if mode=="invalid_output" and (
             report["status"]!="INVALID_OUTPUT_IFC" or
             any(report[k]!=0.0 for k in
                 ("geometry","semantics","topology","final_score"))):
            raise DockerIsolationError("Invalid prediction did not score as failure")
    return report


def run_pinned_blind_scorer(image_id:str,task_id:str,mode:str)->dict:
    """Trusted offline grader ONLY; no model code or arbitrary host file paths."""
    if mode not in ALLOWED_MODES:
        raise DockerIsolationError("Only frozen GT/self/source/invalid control cases")
    task,source,gt=_trusted_pinned_task(task_id)
    verify_blind_image(image_id)
    source_sha=_sha(source);gt_sha=_sha(gt)
    run_digest=sha256(f"g2-blind|{task_id}|{mode}|{source_sha}|{gt_sha}".encode()).hexdigest()[:24]
    name="bim-bench-blind-grader-"+uuid.uuid4().hex[:12]
    created_id=None
    stage=ROOT/"data"
    if stage.is_symlink() or not stage.is_dir():
        raise DockerIsolationError("Untrusted blind scorer scratch")
    with tempfile.TemporaryDirectory(prefix=".blind-public-",dir=stage) as directory:
        root=Path(directory)
        folders={name:(root/name) for name in
                 ("source","ground_truth","prediction","metadata")}
        for folder in folders.values():folder.mkdir()
        staged_source=folders["source"]/"input.ifc"
        staged_gt=folders["ground_truth"]/"expected.ifc"
        staged_pred=folders["prediction"]/"result.ifc"
        shutil.copyfile(source,staged_source)
        shutil.copyfile(gt,staged_gt)
        if mode=="reference_self_check":
            shutil.copyfile(gt,staged_pred)
        elif mode=="unchanged_source":
            shutil.copyfile(source,staged_pred)
        else:
            staged_pred.write_bytes(b"NOT_IFC4X3_PRIVATE_TEST")
        hidden_task={
            "task_id":task_id,
            "operation":task["operation"],
            "target_class":task["target"]["entity_type"],
            "target_guids":task["target"]["guids"],
        }
        secret_file=folders["metadata"]/"task.json"
        secret_file.write_text(json.dumps(hidden_task,sort_keys=True)+"\n",
                               encoding="utf-8")
        if _sha(staged_source)!=source_sha or _sha(staged_gt)!=gt_sha:
            raise DockerIsolationError("Source/reference changed during trusted staging")
        predicted_sha=_sha(staged_pred)
        for file in (staged_source,staged_gt,staged_pred,secret_file):
            file.chmod(0o444)
        args=[
            "docker","create","--pull=never","--name="+name,
            "--network=none","--read-only","--user=65534:65534",
            "--cap-drop=ALL","--security-opt=no-new-privileges:true",
            "--pids-limit=1","--memory=512m","--memory-swap=512m",
            "--cpus=0.75","--ipc=none","--cgroupns=private",
            "--ulimit=nofile=64:64","--ulimit=core=0:0",
            "--tmpfs=/tmp:rw,nosuid,nodev,noexec,size=16m",
            "--log-driver=json-file","--log-opt=max-size=1m","--log-opt=max-file=1",
            "--mount=type=bind,source="+str(folders["source"])+",target=/source,readonly",
            "--mount=type=bind,source="+str(folders["ground_truth"])+",target=/ground_truth,readonly",
            "--mount=type=bind,source="+str(folders["prediction"])+",target=/prediction,readonly",
            "--mount=type=bind,source="+str(folders["metadata"])+",target=/metadata,readonly",
            "--env=HOME=/tmp","--env=OPENBLAS_NUM_THREADS=1",
            "--env=OMP_NUM_THREADS=1","--env=MKL_NUM_THREADS=1",
            "--entrypoint=/usr/local/bin/python3",image_id,
            "/opt/blind/worker.py",
        ]
        try:
            made=_run(args,timeout=15)
            if made.returncode:
                raise DockerIsolationError("Trust-only blind grader Docker create failed")
            created_id=made.stdout.strip()
            if not re.fullmatch(r"[a-f0-9]{64}",created_id):
                raise DockerIsolationError("Docker returned invalid grader identity")
            verify_blind_container(created_id,image_id)
            finished=_limited_attach(created_id,25)
            if finished.returncode:
                raise DockerIsolationError("Blind grader container failed")
            report=_checked_public_result(finished.stdout,task_id,mode)
            if (_sha(staged_source)!=source_sha or _sha(staged_gt)!=gt_sha
                or _sha(staged_pred)!=predicted_sha
                or _sha(source)!=source_sha or _sha(gt)!=gt_sha):
                raise DockerIsolationError("Source, GT or candidate changed during scoring")
            return {
                "status":"PUBLIC_PINNED_BLIND_INDEPENDENT_SCORER_SMOKE_PASS",
                "run_id":run_digest,
                "task_id":task_id,
                "candidate_case":mode,
                "grader_image_id":image_id,
                "independent_grader_result":report,
                "GT_path_or_guid_exposed_in_report":False,
                "agent_program_executed":False,
                "independent_not_official":True,
                "official_tasks_scored":0,
                "paid_model_calls":0,
                "live_pilot_ready":False,
            }
        finally:
            removed=_run(["docker","rm","--force",name],timeout=12)
            if created_id is not None and removed.returncode:
                raise DockerIsolationError("Failed to remove blind scorer namespace")
