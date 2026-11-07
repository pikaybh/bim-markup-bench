"""Read-only trusted Linux Docker isolation probe for G2 #19.

This module NEVER executes a model-generated program. It tests a known,
fixed probe in a Docker container with pinned local image ID. It verifies
the daemon-created HostConfig and mounts BEFORE starting the container,
then checks runtime kernel restrictions. This is not approval of any
unreviewed worker image or of paid/model-generated code execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid


class DockerIsolationError(RuntimeError):
    pass


IMAGE_ID=re.compile(r"^sha256:[0-9a-f]{64}$")
KNOWN_PROBE_ID="g2-docker-kernel-probe-v0.1"
TRUSTED_MARKER=b"BIM_MARKUP_BENCH_OWN_IMMUTABLE_PROBE_INPUT_V1"
SECRET_NAMES=("OPENAI_API_KEY","AWS_SECRET_ACCESS_KEY","GITHUB_TOKEN",
              "GH_TOKEN","SSH_AUTH_SOCK","AZURE_CLIENT_SECRET")


# The code below is owned by the harness, not a generated assistant script.
# It exercises OS-level boundaries only on own ephemeral synthetic content.
TRUSTED_PROBE=r'''
import json,os,socket
from pathlib import Path

def denied(f):
    try:
        f()
        return False
    except (OSError,PermissionError):
        return True

source=Path('/input/read_only_probe.txt')
status=Path('/proc/self/status').read_text()
def line(key):
    return next((s.split(':',1)[1].strip() for s in status.splitlines()
                 if s.startswith(key+':')),None)

evidence={
    'uid':os.geteuid(),
    'source_visible':source.read_bytes()==b'BIM_MARKUP_BENCH_OWN_IMMUTABLE_PROBE_INPUT_V1',
    'source_write_denied':denied(lambda:source.write_bytes(b'UNAUTHORIZED_CHANGE')),
    'host_gt_path_hidden':not Path('/grader/ground_truth.ifc').exists(),
    'parent_traversal_hidden':not Path('/input/../grader/ground_truth.ifc').exists(),
    'docker_sock_hidden':not Path('/var/run/docker.sock').exists(),
    'launcher_key_hidden':os.environ.get('OPENAI_API_KEY') is None,
    'host_root_write_denied':denied(
        lambda:Path('/etc/BIM_BENCH_SHOULD_NOT_EXIST').write_text('UNAUTHORIZED')
    ),
    'network_denied':denied(
        lambda:socket.create_connection(('1.1.1.1',443),timeout=1.5)
    ),
    'effective_caps_hex':line('CapEff'),
    'no_new_privileges':line('NoNewPrivs'),
    'seccomp_filter':line('Seccomp'),
    'cgroup_memory_bytes':int(Path('/sys/fs/cgroup/memory.max').read_text().strip()),
    'cgroup_pid_limit':int(Path('/sys/fs/cgroup/pids.max').read_text().strip()),
    'cgroup_cpu_limit':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
}
Path('/output/probe_result.json').write_text(json.dumps(evidence,sort_keys=True)+'\n')
print(json.dumps(evidence,sort_keys=True))
'''


@dataclass(frozen=True)
class DockerProbePolicy:
    image_id:str
    memory_bytes:int=134217728
    pid_limit:int=16
    cpu_share:float=0.5
    wall_timeout_seconds:int=25

    def __post_init__(self):
        if not isinstance(self.image_id,str) or not IMAGE_ID.fullmatch(self.image_id):
            raise DockerIsolationError(
                "Security probe must use immutable full sha256 local image ID, never a tag"
            )
        if self.memory_bytes!=134217728 or self.pid_limit!=16:
            raise DockerIsolationError("Probe cgroup limits must match frozen policy")
        if self.cpu_share!=0.5 or self.wall_timeout_seconds!=25:
            raise DockerIsolationError("Probe CPU/wall-time limits must match frozen policy")


def _docker_binary()->str:
    cli=shutil.which("docker")
    if not cli or not Path(cli).is_file():
        raise DockerIsolationError("Docker client not installed")
    return str(Path(cli).resolve())


def _invoke(args:list[str],*,timeout:int=12)->subprocess.CompletedProcess:
    # Only a minimal host environment reaches the Docker client. The sentinel
    # exercises the guarantee it does NOT flow into the worker container.
    env={
        "HOME":str(Path.home()),
        "PATH":"/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin",
        "OPENAI_API_KEY":"BIM_BENCH_FAKE_LOCAL_PROBE_SENTINEL",
    }
    try:
        return subprocess.run(
            args,capture_output=True,text=True,timeout=timeout,
            env=env,check=False
        )
    except subprocess.TimeoutExpired as exc:
        raise DockerIsolationError("Docker control command exceeded time limit") from exc


def _ensure_cached_image(binary:str,image_id:str)->None:
    check=_invoke([binary,"image","inspect",image_id],timeout=10)
    if check.returncode!=0:
        raise DockerIsolationError(
            "Pinned worker image is not cached; no implicit image/network pull allowed"
        )
    try:
        found=json.loads(check.stdout)
    except (ValueError,TypeError) as exc:
        raise DockerIsolationError("Docker image inspect returned invalid JSON") from exc
    if not isinstance(found,list) or len(found)!=1 or found[0].get("Id")!=image_id:
        raise DockerIsolationError("Docker image ID does not match immutable pin")
    if found[0].get("Os")!="linux":
        raise DockerIsolationError("Worker image is not a Linux container image")


def _assert_mount_input(root:Path)->None:
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise DockerIsolationError("Scratch input/output directory must be a real absolute directory")
    if "," in str(root) or "\n" in str(root):
        raise DockerIsolationError("Unsafe comma/newline in Docker mount path")


def build_probe_argv(binary:str,policy:DockerProbePolicy,
                     name:str,source_root:Path,output_root:Path)->list[str]:
    """Pure argument generator, safe to audit without a Docker runtime."""
    for path in (source_root,output_root):
        _assert_mount_input(path)
    if not re.fullmatch(r"bim-bench-probe-[0-9a-f]{16}",name):
        raise DockerIsolationError("Probe container name must be namespaced and immutable")
    return [
        binary,"create","--pull=never",
        "--name="+name,
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges:true",
        "--user=65534:65534",
        "--cgroupns=private",
        "--ipc=none",
        "--pids-limit="+str(policy.pid_limit),
        "--memory="+str(policy.memory_bytes),
        "--memory-swap="+str(policy.memory_bytes),
        "--cpus="+str(policy.cpu_share),
        "--ulimit=nofile=64:64",
        "--tmpfs=/tmp:rw,nosuid,nodev,noexec,size=16m",
        "--mount=type=bind,source="+str(source_root)+",target=/input,readonly",
        "--mount=type=bind,source="+str(output_root)+",target=/output",
        "--workdir=/",
        "--env=HOME=/tmp",
        "--env=PYTHONDONTWRITEBYTECODE=1",
        "--entrypoint=/usr/bin/python3",
        policy.image_id,"-c",TRUSTED_PROBE,
    ]


def _validate_created(container:dict,policy:DockerProbePolicy)->dict:
    h=container.get("HostConfig") or {}
    cfg=container.get("Config") or {}
    mounts=container.get("Mounts") or []
    checks={
        "network_disabled":h.get("NetworkMode")=="none",
        "read_only_root":h.get("ReadonlyRootfs") is True,
        "all_capabilities_dropped":"ALL" in (h.get("CapDrop") or []),
        "no_new_privileges":any("no-new-privileges" in s
              for s in (h.get("SecurityOpt") or [])),
        "non_root_user":cfg.get("User")=="65534:65534",
        "private_cgroup_namespace":h.get("CgroupnsMode")=="private",
        "ipc_disabled":h.get("IpcMode")=="none",
        "pid_limit":h.get("PidsLimit")==policy.pid_limit,
        "memory_limit":h.get("Memory")==policy.memory_bytes,
        "memory_swap_limit":h.get("MemorySwap")==policy.memory_bytes,
        "cpu_limit":h.get("NanoCpus")==int(policy.cpu_share*1_000_000_000),
        "no_privileged":h.get("Privileged") is False,
        "two_allowlisted_bind_mounts":len(mounts)==2 and {
            (row.get("Destination"),row.get("RW"),row.get("Type"))
            for row in mounts
        }=={("/input",False,"bind"),("/output",True,"bind")},
        "no_inherited_host_secret_env":not any(
            line.split("=",1)[0] in SECRET_NAMES for line in cfg.get("Env",[])
        ),
        "trusted_probe_only":(
            cfg.get("Entrypoint")==["/usr/bin/python3"]
            and (cfg.get("Cmd") or [])==["-c",TRUSTED_PROBE]
        ),
    }
    return checks


def _validate_runtime(data:dict,policy:DockerProbePolicy)->dict:
    cpu=data.get("cgroup_cpu_limit","")
    parts=cpu.split()
    cpu_limited=False
    if len(parts)==2 and parts[0].isdigit() and parts[1].isdigit():
        quota=int(parts[0]);period=int(parts[1])
        cpu_limited=(period>0 and quota>0 and quota/period<=policy.cpu_share+1e-6)
    return {
        "non_root_uid":data.get("uid")==65534,
        "read_only_input_visible":data.get("source_visible") is True,
        "read_only_input_write_denied":data.get("source_write_denied") is True,
        "GT_unmounted":data.get("host_gt_path_hidden") is True,
        "path_traversal_no_GT":data.get("parent_traversal_hidden") is True,
        "docker_socket_not_mounted":data.get("docker_sock_hidden") is True,
        "launcher_api_key_not_visible":data.get("launcher_key_hidden") is True,
        "immutable_rootfs_write_denied":data.get("host_root_write_denied") is True,
        "external_network_socket_denied":data.get("network_denied") is True,
        "zero_effective_capabilities":data.get("effective_caps_hex")=="0000000000000000",
        "no_new_privileges_kernel":data.get("no_new_privileges")=="1",
        "linux_seccomp_filter_active":data.get("seccomp_filter")=="2",
        "memory_cgroup_enforced":data.get("cgroup_memory_bytes")==policy.memory_bytes,
        "pids_cgroup_enforced":data.get("cgroup_pid_limit")==policy.pid_limit,
        "cpu_cgroup_enforced":cpu_limited,
    }


def run_trusted_docker_probe(policy:DockerProbePolicy)->dict:
    """Run ONLY the trusted probe; never accept candidate code or file paths.

    A positive probe is necessary, NOT sufficient, for approving the actual
    Python+IfcOpenShell worker image/IFC dataset/model provider.
    """
    binary=_docker_binary()
    _ensure_cached_image(binary,policy.image_id)
    name="bim-bench-probe-"+uuid.uuid4().hex[:16]
    with tempfile.TemporaryDirectory(prefix="bim-bench-own-docker-probe-") as tmp:
        root=Path(tmp)
        source=root/"input"
        output=root/"output"
        grader=root/"grader"
        for folder,mode in ((source,0o755),(output,0o777),(grader,0o700)):
            folder.mkdir(mode=mode)
            folder.chmod(mode)
        (source/"read_only_probe.txt").write_bytes(TRUSTED_MARKER)
        (source/"read_only_probe.txt").chmod(0o444)
        grader_file=grader/"ground_truth.ifc"
        grader_file.write_bytes(b"OWN_FAKE_GT_NEVER_MOUNTED")
        original_sha=sha256((source/"read_only_probe.txt").read_bytes()).hexdigest()
        gt_sha=sha256(grader_file.read_bytes()).hexdigest()
        argv=build_probe_argv(binary,policy,name,source,output)
        container_id=None
        try:
            created=_invoke(argv,timeout=15)
            if created.returncode!=0:
                raise DockerIsolationError("Docker create failed under frozen isolation policy")
            container_id=created.stdout.strip()
            if not re.fullmatch(r"[0-9a-f]{64}",container_id):
                raise DockerIsolationError("Docker daemon gave invalid container identity")
            inspect=_invoke([binary,"inspect",container_id],timeout=10)
            if inspect.returncode!=0:
                raise DockerIsolationError("Docker inspect refused newly created probe")
            try:
                inspected=json.loads(inspect.stdout)
            except (ValueError,TypeError) as exc:
                raise DockerIsolationError("Invalid Docker inspect JSON") from exc
            if len(inspected)!=1:
                raise DockerIsolationError("Docker inspect returned multiple containers")
            preflight=_validate_created(inspected[0],policy)
            if not all(preflight.values()):
                raise DockerIsolationError("Docker HostConfig/mount/env is not compliant; refusing start")
            started=_invoke(
                [binary,"start","--attach",container_id],
                timeout=policy.wall_timeout_seconds
            )
            if started.returncode!=0:
                raise DockerIsolationError("Trusted OS restriction probe failed within container")
            try:
                result=json.loads(started.stdout.strip())
            except (ValueError,TypeError) as exc:
                raise DockerIsolationError("Trusted probe did not emit valid JSON") from exc
            result_file=output/"probe_result.json"
            if result_file.is_symlink() or not result_file.is_file():
                raise DockerIsolationError("Probe output must be an existing real file")
            if json.loads(result_file.read_text(encoding="utf-8"))!=result:
                raise DockerIsolationError("Container stdout/output evidence disagree")
            checks=_validate_runtime(result,policy)
            if sha256((source/"read_only_probe.txt").read_bytes()).hexdigest()!=original_sha:
                raise DockerIsolationError("Original readonly probe source changed")
            if sha256(grader_file.read_bytes()).hexdigest()!=gt_sha:
                raise DockerIsolationError("Hidden GT marker changed")
            if not all(checks.values()):
                raise DockerIsolationError("At least one actual OS kernel restriction check failed")
            return {
                "probe_id":KNOWN_PROBE_ID,
                "status":"KERNEL_ISOLATION_PROBE_PASS",
                "docker_server_version":_docker_version(binary),
                "image_digest_matches_pinned_local_id":True,
                "worker_image_scientifically_approved":False,
                "production_scored_python_enabled":False,
                "real_model_provider_called":False,
                "paid_model_pilot_ready":False,
                "independent_created_host_config_checks":preflight,
                "actual_container_kernel_checks":checks,
                "host_input_unchanged":True,
                "hidden_gt_unchanged":True,
                "docker_container_cleaned_after_probe":True,
            }
        finally:
            # Always use our unguessable, namespaced name for cleanup, even
            # if Docker returned malformed container-ID text after creation.
            cleanup=_invoke([binary,"rm","--force",name],timeout=12)
            if container_id and cleanup.returncode!=0:
                raise DockerIsolationError(
                    "Failed to remove own probe container after verification"
                )


def _docker_version(binary:str)->str:
    version=_invoke([binary,"version","--format","{{.Server.Version}}"],timeout=8)
    if version.returncode!=0:
        raise DockerIsolationError("Docker daemon became unreachable")
    value=version.stdout.strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+.*",value):
        raise DockerIsolationError("Unexpected Docker server version")
    return value
