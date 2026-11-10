"""G2 #19: controlled *offline OWN-synthetic* dynamic Python isolation slice.

An opaque Python program supplied by a trusted caller is NEVER imported,
compiled or executed on the host. The isolated Linux worker is given only
OWN_SOURCE, its immutable script, a bounded tmpfs, and a synthetic GT canary
which is deliberately NOT mounted. A separate trusted grading process
receives only the bytes exported from the stopped worker.

This is NOT a production LLM, external IFC, official scorer, or paid pilot
interface. Nothing here removes the primary sandbox.py live execution block.
"""
from __future__ import annotations

import base64
import binascii
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid

from src.runner.docker_isolation import DockerIsolationError
from src.runner.local_docker_transport import (
    LocalDockerTransportError,pinned_local_docker_argv,
)
from src.runner.ifc_worker import (
    _docker_cli, _inspect_config, _sha, _verify_local_image, _run,
    OWN_SOURCE,
)

MAX_SOURCE_BYTES=64*1024
MAX_RESULT_BYTES=256*1024
MAX_STDOUT_BYTES=512*1024
MAX_STDERR_BYTES=16*1024
MAX_WALL_SECONDS=20


def candidate_content_sha256(code:bytes)->str:
    if not isinstance(code,bytes) or not 0<len(code)<=MAX_SOURCE_BYTES:
        raise DockerIsolationError("OWN candidate must be a nonempty <=64KiB byte string")
    if b"\x00" in code:
        raise DockerIsolationError("NUL in candidate source")
    try:
        code.decode("utf-8",errors="strict")
    except UnicodeDecodeError as exc:
        raise DockerIsolationError("Candidate is not valid UTF-8") from exc
    return sha256(code).hexdigest()


def _limited_attach(container_id:str,timeout_seconds:int)->subprocess.CompletedProcess:
    """Bounded stdout/stderr byte collections even for hostile os.write loops.

    The Linux Docker daemon itself is configured with a 1MiB container log
    rotation cap. This host reader also limits pipe memory, kills the CLI
    upon overrun, and the caller must remove its own unique container in a
    finally block. Candidate output is never sent verbatim to callers.
    """
    if not re.fullmatch(r"[a-f0-9]{64}",container_id):
        raise DockerIsolationError("Untrusted container ID")
    from src.runner.ifc_worker import _host_docker_env
    try:
        argv=pinned_local_docker_argv(
            [_docker_cli(),"start","--attach",container_id])
    except LocalDockerTransportError as exc:
        raise DockerIsolationError("Candidate attach must use fixed local Docker engine") from exc
    child=subprocess.Popen(
        argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,env=_host_docker_env(),
        creationflags=0,close_fds=True,
    )
    outputs=[bytearray(),bytearray()]
    exceeded=threading.Event()
    failed=threading.Event()

    def collect(stream,buffer:bytearray,limit:int)->None:
        try:
            while True:
                part=stream.read(8192)
                if not part:
                    return
                if len(buffer)+len(part)>limit:
                    exceeded.set()
                    # Always drain the pipe while terminating the Docker CLI,
                    # but do not store additional attacker-controlled data.
                    continue
                buffer.extend(part)
        except (OSError,ValueError):
            failed.set()

    readers=[
        threading.Thread(target=collect,args=(child.stdout,outputs[0],MAX_STDOUT_BYTES),daemon=True),
        threading.Thread(target=collect,args=(child.stderr,outputs[1],MAX_STDERR_BYTES),daemon=True),
    ]
    for thread in readers:
        thread.start()
    try:
        deadline=time.monotonic()+timeout_seconds
        while child.poll() is None:
            if exceeded.is_set() or failed.is_set():
                child.kill()
                child.wait(timeout=3)
                raise DockerIsolationError("Worker stdout/stderr exceeded bounded host capture")
            if time.monotonic()>=deadline:
                child.kill()
                child.wait(timeout=3)
                raise DockerIsolationError("Worker exceeded external wall clock limit")
            time.sleep(0.04)
        for thread in readers:
            thread.join(timeout=2)
        if exceeded.is_set() or failed.is_set() or any(x.is_alive() for x in readers):
            raise DockerIsolationError("Worker output stream invalid or exceeded cap")
        return subprocess.CompletedProcess(
            argv,child.returncode,
            outputs[0].decode("utf-8",errors="replace"),
            outputs[1].decode("utf-8",errors="replace"),
        )
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=3)
        child.stdout.close()
        child.stderr.close()


def _recover_ifc(result_text:str)->bytes:
    payloads=[]
    for line in result_text.splitlines():
        if not line.startswith("{"):
            continue
        try:
            message=json.loads(line)
        except (ValueError,TypeError):
            continue
        if isinstance(message,dict) and "trusted_small_ifc_b64" in message:
            payloads.append(message["trusted_small_ifc_b64"])
    if len(payloads)!=1 or not isinstance(payloads[0],str) or len(payloads[0])>350000:
        raise DockerIsolationError("Missing, duplicated, or overlong worker result")
    try:
        raw=base64.b64decode(payloads[0],validate=True)
    except (binascii.Error,ValueError) as exc:
        raise DockerIsolationError("Invalid worker result base64") from exc
    if not 0<len(raw)<=MAX_RESULT_BYTES:
        raise DockerIsolationError("Result IFC exceeds trusted OWN output cap")
    if not raw.lstrip().startswith(b"ISO-10303-21;"):
        raise DockerIsolationError("Result does not resemble an IFC STEP file")
    return raw


def _trusted_separate_own_grader(source:Path,result:Path)->dict:
    """Run an owned IFC-only check as a *separate process*, after worker stop.

    Not a substitute for the final official scorer's independently
    containerized source/GT handling and parity audit.
    """
    owned_grader=Path(__file__).resolve().with_name("own_result_grader.py")
    safe_env={
        "PYTHONUTF8":"1","PYTHONIOENCODING":"utf-8",
        "PYTHONDONTWRITEBYTECODE":"1","PYTHONNOUSERSITE":"1",
        "OPENBLAS_NUM_THREADS":"1","OMP_NUM_THREADS":"1",
    }
    if os.name=="nt":
        for key in ("SYSTEMROOT","WINDIR","COMSPEC","TEMP","TMP","USERPROFILE"):
            if key in os.environ:safe_env[key]=os.environ[key]
    else:
        safe_env["PATH"]="/usr/bin:/bin"
    try:
        process=subprocess.run(
            [sys.executable,str(owned_grader),str(source),str(result)],
            cwd=str(owned_grader.parents[2]),env=safe_env,
            capture_output=True,text=True,timeout=12,
        )
    except subprocess.TimeoutExpired as exc:
        raise DockerIsolationError("Trusted independent OWN grader timed out") from exc
    if process.returncode!=0 or len(process.stdout)>4096:
        raise DockerIsolationError("Trusted OWN grader rejected result IFC")
    try:
        score=json.loads(process.stdout)
    except ValueError as exc:
        raise DockerIsolationError("Trusted grader returned malformed result") from exc
    if score.get("status")!="OWN_WALL_EDIT_VERIFIED":
        raise DockerIsolationError("Trusted native OWN grading did not pass")
    return score


def run_offline_own_generated_candidate(
    image_id:str,script_bytes:bytes,expected_script_sha256:str,
    *,wall_seconds:int=15,seed:int=0,
)->dict:
    """Safely isolate *arbitrary bytes* only against a fixed OWN synthetic IFC.

    Caller provides opaque bytes and a separately computed SHA-256.
    Official dataset and source paths cannot be selected through this API.
    No host exec/eval/import of candidate code. Real model and paid pilot
    entry points remain blocked in src.runner.sandbox.execute_untrusted_candidate.
    """
    if not isinstance(seed,int) or isinstance(seed,bool) or not 0<=seed<=2**31-1:
        raise DockerIsolationError("Invalid replay seed")
    if not isinstance(wall_seconds,int) or not 3<=wall_seconds<=MAX_WALL_SECONDS:
        raise DockerIsolationError("Invalid worker wall timeout")
    # Shared strict OWN-only admission is enforced BEFORE checking/using
    # Docker. The binder only hashes opaque code; it neither imports nor
    # executes a candidate or exposes any other IFC source path.
    from src.runner.worker_admission import bind_own_candidate,WorkerAdmissionError
    try:
        admitted=bind_own_candidate(
            script_bytes,expected_script_sha256,_sha(OWN_SOURCE),
            arm="imperative_python",seed=seed)
    except (WorkerAdmissionError,OSError) as exc:
        raise DockerIsolationError("OWN source/candidate admission rejected") from exc
    script_digest=admitted.script_sha256
    source_digest=admitted.source_sha256
    _verify_local_image(image_id)
    run_id=sha256(f"g2-own-only|{source_digest}|{script_digest}|{seed}".encode()).hexdigest()[:24]
    container_name="bim-bench-own-dynamic-"+uuid.uuid4().hex[:12]
    with tempfile.TemporaryDirectory(prefix="bim-bench-owned-dynamic-") as directory:
        root=Path(directory)
        input_root=root/"input";script_root=root/"task"
        hidden_gt=root/"hidden_gt";trusted_grader=root/"trusted_grader"
        for sub in (input_root,script_root,hidden_gt,trusted_grader):
            sub.mkdir()
        staged_source=input_root/"input.ifc"
        shutil.copyfile(OWN_SOURCE,staged_source)
        if _sha(staged_source)!=source_digest:
            raise DockerIsolationError("Source changed during staging")
        staged_source.chmod(0o444)
        script=script_root/"solution.py"
        script.write_bytes(script_bytes)
        if _sha(script)!=script_digest:
            raise DockerIsolationError("Candidate changed during staging")
        script.chmod(0o444)
        canary=hidden_gt/"ground_truth.ifc"
        canary.write_bytes(b"OWN_FAKE_REFERENCE_NEVER_MOUNTED")
        canary_digest=_sha(canary)
        args=[
            "docker","create","--pull=never","--name="+container_name,
            "--network=none","--read-only","--user=65534:65534",
            "--cap-drop=ALL","--security-opt=no-new-privileges:true",
            "--pids-limit=1","--memory=512m","--memory-swap=512m",
            "--cpus=0.75","--ipc=none","--cgroupns=private",
            "--ulimit=nofile=64:64","--ulimit=fsize=33554432:33554432",
            "--ulimit=core=0:0",
            "--tmpfs=/tmp:rw,nosuid,nodev,noexec,size=16m",
            "--tmpfs=/output:rw,nosuid,nodev,noexec,size=64m",
            "--log-driver=json-file","--log-opt=max-size=1m","--log-opt=max-file=1",
            "--mount=type=bind,source="+str(input_root)+",target=/input,readonly",
            "--mount=type=bind,source="+str(script_root)+",target=/task,readonly",
            "--env=HOME=/tmp","--env=OPENBLAS_NUM_THREADS=1",
            "--env=OMP_NUM_THREADS=1","--env=MKL_NUM_THREADS=1",
            "--env=NUMEXPR_NUM_THREADS=1",
            "--entrypoint=/usr/local/bin/python3",image_id,
            "/opt/ifc_worker/run_candidate.py",
        ]
        created_id=None
        try:
            created=_run(args,timeout=14)
            if created.returncode!=0:
                raise DockerIsolationError("OWN dynamic container create denied")
            created_id=created.stdout.strip()
            if not re.fullmatch(r"[a-f0-9]{64}",created_id):
                raise DockerIsolationError("Docker returned invalid container ID")
            _inspect_config(created_id,image_id,True)
            # inspect succeeded before start; do not reuse any other container.
            output=_limited_attach(created_id,wall_seconds)
            if output.returncode!=0:
                raise DockerIsolationError("OWN dynamic code exited nonzero or blocked")
            if _sha(staged_source)!=source_digest or _sha(script)!=script_digest:
                raise DockerIsolationError("Input or script mutation detected")
            if _sha(canary)!=canary_digest:
                raise DockerIsolationError("Hidden grader canary mutated")
            ifc_bytes=_recover_ifc(output.stdout)
            original=trusted_grader/"source.ifc"
            result=trusted_grader/"candidate.ifc"
            shutil.copyfile(OWN_SOURCE,original)
            result.write_bytes(ifc_bytes)
            if _sha(original)!=source_digest:
                raise DockerIsolationError("Trusted grader source mismatch")
            result_digest=_sha(result)
            # Shut down the candidate and discard its namespace BEFORE
            # allowing any synthetic reference into a different container.
            cleanup=_run(["docker","rm","--force",container_name],timeout=12)
            if cleanup.returncode!=0:
                raise DockerIsolationError("Candidate container cleanup failed before grading")
            created_id=None
            grade=_trusted_separate_own_grader(original,result)
            from src.runner.own_grader_container import run_own_isolated_grader
            isolated_grade=run_own_isolated_grader(image_id,original,result)
            if (isolated_grade.get("status")!="OWN_ISOLATED_GRADER_PASS"
                    or isolated_grade.get("candidate_script_mounted_in_grader") is not False
                    or isolated_grade.get("GT_mounted_in_separate_grader_only") is not True):
                raise DockerIsolationError("Independent isolated OWN grading did not pass")
            return {
                "status":"OWN_SYNTHETIC_DYNAMIC_CANDIDATE_VERIFIED",
                "run_id":run_id,"candidate_sha256":script_digest,
                "source_sha256":source_digest,"output_sha256":result_digest,
                "independent_own_grader":grade,
                "isolated_own_grader":isolated_grade,
                "separate_grader_process":True,
                "separate_OS_grader_container_verified":True,
                "GT_accessible_inside_candidate_container":False,
                "original_source_unchanged":True,
                "candidate_host_exec_or_import":False,
                "official_tasks_scored":0,
                "paid_model_calls":0,
                "pilot_ready":False,
            }
        finally:
            # Always remove by our fresh namespaced container name.
            # Never delete containers that did not belong to this call.
            cleanup=_run(["docker","rm","--force",container_name],timeout=12)
            if created_id is not None and cleanup.returncode!=0:
                raise DockerIsolationError("Own dynamic container cleanup failed")
