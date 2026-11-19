"""Fail-closed local Docker admission for OWN-synthetic Python worker tests.

READ-ONLY until a separately approved worker invokes the existing OWN-only
container runner. This code NEVER executes Python, starts Docker services,
pulls images, creates containers, opens benchmark GT or authorizes a live run.

An exact pinned image ID is necessary but not proof of image build provenance,
dependency SBOM or official/scientific worker fitness. A previously passing
probe report is historical, not live host attestation.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Callable

from src.runner.generated_candidate import candidate_content_sha256
from src.runner.ifc_worker import OWN_SOURCE,_docker_cli,_host_docker_env
from src.runner.sandbox import canonical_run_id
from src.runner.docker_isolation import DockerIsolationError
from src.runner.local_docker_transport import _local_docker_endpoint,LocalDockerTransportError

IMAGE_ID=re.compile(r"^sha256:[0-9a-f]{64}$")
SOURCE_DIGEST=re.compile(r"^[0-9a-f]{64}$")
MAX_DOCKER_JSON_BYTES=65536
# This OWN fixture hash is independent of a caller-provided or dynamically
# computed hash. Otherwise a modified file plus its modified hash would pass.
EXPECTED_OWN_SOURCE_SHA256="10d57d3eeb6e50fb51493b03d7cb508d57eadeb76719afaeb71fa6658c3ecf58"
BLOCKED="BLOCKED_LOCAL_WORKER_ADMISSION"

class WorkerAdmissionError(ValueError):
    """Never pass an unverified submission to any subprocess/container."""


@dataclass(frozen=True)
class OwnSubmission:
    arm:str
    source_sha256:str
    script_sha256:str
    seed:int
    run_id:str

    def evidence(self)->dict:
        return {
            "arm":self.arm,
            "source_sha256":self.source_sha256,
            "candidate_sha256":self.script_sha256,
            "run_id":self.run_id,
            "seed":self.seed,
            "source_scope":"REPOSITORY_OWN_SYNTHETIC_ONLY",
            "candidate_executed":False,
            "external_benchmark_input_supported":False,
            "official_tasks_scored":0,
            "model_calls":0,
        }


def bind_own_candidate(script_bytes:bytes,expected_script_sha256:str,
                       expected_source_sha256:str,*,arm:str,seed:int)->OwnSubmission:
    """No arbitrary IFC path, host command, evaluator, or code execution.

    Only this repository's own fixed tiny source fixture is admitted;
    model-facing task data and target IFC paths cannot enter this API.
    """
    if arm!="imperative_python":
        raise WorkerAdmissionError("Python worker accepts imperative arm only")
    if (not isinstance(expected_source_sha256,str)
            or not SOURCE_DIGEST.fullmatch(expected_source_sha256)):
        raise WorkerAdmissionError("Invalid original source digest")
    if OWN_SOURCE.is_symlink() or not OWN_SOURCE.is_file():
        raise WorkerAdmissionError("OWN synthetic IFC fixture missing/unsafe")
    source_sha=sha256(OWN_SOURCE.read_bytes()).hexdigest()
    if source_sha!=EXPECTED_OWN_SOURCE_SHA256:
        raise WorkerAdmissionError("OWN immutable synthetic IFC fixture is tampered")
    if expected_source_sha256!=source_sha:
        raise WorkerAdmissionError("External or changed source IFC is not admitted")
    try:
        script_sha=candidate_content_sha256(script_bytes)
    except DockerIsolationError as exc:
        raise WorkerAdmissionError("Invalid opaque Python submission bytes") from exc
    if (not isinstance(expected_script_sha256,str)
            or not SOURCE_DIGEST.fullmatch(expected_script_sha256)
            or script_sha!=expected_script_sha256):
        raise WorkerAdmissionError("Candidate source digest mismatch")
    if type(seed) is not int or not 0<=seed<=2**31-1:
        raise WorkerAdmissionError("Invalid replay seed")
    base_id=canonical_run_id("OWN-SYNTHETIC-ONLY",arm,seed,source_sha)
    # Bind candidate bytes into the replay ID. Different code with the same
    # task, seed and source must never share a working directory or trace.
    run_id="own-"+sha256(
        f"g2-admission-v01|{base_id}|{script_sha}".encode("utf8")
    ).hexdigest()[:24]
    # This is admission of captured immutable bytes, not Python compilation.
    return OwnSubmission(arm,source_sha,script_sha,seed,run_id)


@dataclass(frozen=True)
class LocalDockerObservation:
    status:str
    local_engine_reachable:bool
    exact_image_id_present:bool|None
    runtime_architecture:str|None
    image_digest_matches:bool|None
    image_is_linux_native:bool|None
    nonroot_oci_user:bool|None
    named_worker_label_matches:bool|None
    image_build_provenance_verified:bool
    worker_os_isolation_currently_verified:bool
    real_candidate_execution_authorized:bool
    paid_model_run_authorized:bool

    def report(self)->dict:
        return {
            **self.__dict__,
            "host_execution_attempted":False,
            "docker_service_started":False,
            "docker_image_pulled":False,
            "candidate_container_created":False,
            "official_tasks_scored":0,
            "paid_model_calls":0,
        }


def _blocked(status:str,*,daemon:bool=False,image_present:bool|None=None,
             arch:str|None=None,digest:bool|None=None,linux:bool|None=None,
             user:bool|None=None,label:bool|None=None)->LocalDockerObservation:
    return LocalDockerObservation(status,daemon,image_present,arch,digest,
        linux,user,label,False,False,False,False)


def _local_readonly_docker(argv:list[str])->subprocess.CompletedProcess:
    binary=_docker_cli()
    env=_host_docker_env()
    # Both Docker client environment and command transport are fixed, and
    # we do NOT pass API keys, SSH agents, Docker host selector, or proxies.
    if any(name in env for name in ("DOCKER_HOST","DOCKER_CONTEXT",
                                    "DOCKER_CERT_PATH","OPENAI_API_KEY",
                                    "GITHUB_TOKEN","SSH_AUTH_SOCK")):
        raise WorkerAdmissionError("Docker control environment not sanitized")
    safe=[binary,"--host",_local_docker_endpoint(),*argv]
    try:
        done=subprocess.run(safe,capture_output=True,text=True,
                            env=env,timeout=7,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise WorkerAdmissionError("Local Docker engine unreachable") from exc
    if len(done.stdout)>MAX_DOCKER_JSON_BYTES or len(done.stderr)>4096:
        raise WorkerAdmissionError("Oversized local Docker inspection response")
    return done


def verify_local_own_worker(image_id:str, *,
                            invoke:Callable[[list[str]],subprocess.CompletedProcess]|None=None
                            )->LocalDockerObservation:
    """Read-only host/image lookup, nothing that can run arbitrary code.

    Even an all-positive observation is ONLY sufficient for a subsequent
    researcher-owned synthetic kernel probe. It is NOT permission to run
    actual agent-generated code or to grade external BIM-Edit tasks.
    """
    if not isinstance(image_id,str) or not IMAGE_ID.fullmatch(image_id):
        raise WorkerAdmissionError("Require exact immutable full worker image SHA256")
    probe=invoke if invoke is not None else _local_readonly_docker
    try:
        info=probe(["info","--format","{{json .}}"])
        if info.returncode!=0:
            return _blocked("BLOCKED_LOCAL_DOCKER_ENGINE_UNAVAILABLE")
        if len(info.stdout)>MAX_DOCKER_JSON_BYTES:
            return _blocked("BLOCKED_OVERSIZED_DOCKER_DAEMON_RESPONSE")
        data=json.loads(info.stdout)
        if not isinstance(data,dict):
            return _blocked("BLOCKED_INVALID_DOCKER_DAEMON_IDENTITY")
        server_arch=data.get("Architecture")
        server_os=data.get("OSType")
        if server_os!="linux" or server_arch not in ("x86_64","amd64","aarch64","arm64"):
            return _blocked("BLOCKED_NONLINUX_OR_UNKNOWN_DOCKER_PLATFORM",
                            daemon=True,arch=server_arch if isinstance(server_arch,str) else None)
        normalized_arch={"x86_64":"amd64","aarch64":"arm64"}.get(
            server_arch,server_arch)
        # Explicit local linux daemon responsiveness does NOT imply that
        # the image is present or that it was built from checked source.
        inspected=probe(["image","inspect",image_id])
        if inspected.returncode!=0:
            return _blocked("BLOCKED_PINNED_IMAGE_NOT_CACHED",
                            daemon=True,image_present=False,arch=normalized_arch)
        if len(inspected.stdout)>MAX_DOCKER_JSON_BYTES:
            return _blocked("BLOCKED_OVERSIZED_IMAGE_INSPECTION",
                            daemon=True,image_present=None,arch=normalized_arch)
        image=json.loads(inspected.stdout)
        if not isinstance(image,list) or len(image)!=1 or not isinstance(image[0],dict):
            return _blocked("BLOCKED_INVALID_IMAGE_INSPECTION",
                            daemon=True,arch=normalized_arch)
        record=image[0]
        cfg=record.get("Config") or {}
        if not isinstance(cfg,dict):
            return _blocked("BLOCKED_INVALID_IMAGE_CONFIG",
                            daemon=True,arch=normalized_arch)
        digest_ok=record.get("Id")==image_id
        linux_ok=(record.get("Os")=="linux"
                  and record.get("Architecture")==normalized_arch)
        nonroot=cfg.get("User")=="65534:65534"
        labels=cfg.get("Labels") or {}
        if not isinstance(labels,dict):
            return _blocked("BLOCKED_INVALID_IMAGE_CONFIG",
                            daemon=True,image_present=True,arch=normalized_arch)
        label=labels.get("org.opencontainers.image.title")=="bim-markup-bench isolated IFC4X3 worker"
        if not all((digest_ok,linux_ok,nonroot,label)):
            return _blocked("BLOCKED_WRONG_WORKER_IMAGE_OR_PLATFORM",
                            daemon=True,image_present=True,arch=normalized_arch,
                            digest=digest_ok,linux=linux_ok,user=nonroot,label=label)
        return LocalDockerObservation(
            "READY_FOR_TRUSTED_OWN_PROBE_ONLY_NOT_GENERATED_PYTHON",
            True,True,normalized_arch,True,True,True,True,
            False,False,False,False)
    except (ValueError,TypeError,KeyError,WorkerAdmissionError,LocalDockerTransportError,subprocess.SubprocessError):
        return _blocked("BLOCKED_UNVERIFIED_LOCAL_DOCKER_OR_IMAGE_RESPONSE")


def offline_own_admission_audit(image_id:str,script_bytes:bytes,
                                script_sha:str,source_sha:str,seed:int=0)->dict:
    """Never calls Docker if the own-source/hash contract has not passed."""
    bound=bind_own_candidate(
        script_bytes,script_sha,source_sha,arm="imperative_python",seed=seed)
    host=verify_local_own_worker(image_id)
    return {
        "status":host.status,
        "own_submission":bound.evidence(),
        "host_observation":host.report(),
        "model_generated_code_executed":False,
        "actual_OS_isolation_test_executed":False,
        "true_external_task_worker_approved":False,
        "paid_llm_calls":0,
        "official_tasks_scored":0,
    }
