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

from src.runner.local_docker_transport import (
    LocalDockerTransportError,pinned_local_docker_argv,
)


class DockerIsolationError(RuntimeError):
    pass


IMAGE_ID=re.compile(r"^sha256:[0-9a-f]{64}$")
KNOWN_PROBE_ID="g2-docker-kernel-probe-v0.1"
# Two fixed, audited paths; never accept a caller-supplied arbitrary executable.
PYTHON_ENTRYPOINTS=("/usr/bin/python3","/usr/local/bin/python3")
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


def _make_trusted_pilot_probe() -> str:
    """Reuse the vetted kernel checks, with an exact input/payload hash variant.

    This script has NO programmable inputs other than fixed, public SHA256s.
    It cannot import, evaluate or run the model's generated Python.
    """
    code=TRUSTED_PROBE
    transformations=(
        ("import json,os,socket", "import hashlib,json,os,socket"),
        ("source=Path('/input/read_only_probe.txt')", "source=Path('/input/input.ifc')"),
        ("source.read_bytes()==b'BIM_MARKUP_BENCH_OWN_IMMUTABLE_PROBE_INPUT_V1'",
         "hashlib.sha256(source.read_bytes()).hexdigest()==os.environ.get('BIM_STAGE_SOURCE_SHA256')"),
    )
    for old,new in transformations:
        if code.count(old)!=1:
            raise DockerIsolationError("Trusted source-only pilot probe base drifted")
        code=code.replace(old,new)
    insert_before="Path('/output/probe_result.json').write_text"
    if code.count(insert_before)!=1:
        raise DockerIsolationError("Trusted source-only pilot probe output boundary drifted")
    supplemental=r"""
task_file=Path('/input/task.json')
raw_payload=task_file.read_bytes()
payload=json.loads(raw_payload.decode('utf-8'))
input_entries=sorted(p.name for p in Path('/input').iterdir())
safe_fields=(isinstance(payload,dict)
             and set(payload)=={'task_id','instruction','input_file'}
             and payload.get('input_file')=='input.ifc'
             and isinstance(payload.get('task_id'),str)
             and isinstance(payload.get('instruction'),str))
evidence.update({
    'only_staged_source_and_task_visible':input_entries==['input.ifc','task.json'],
    'payload_sha256_matches_pinned_host':hashlib.sha256(raw_payload).hexdigest()==os.environ.get('BIM_STAGE_PAYLOAD_SHA256'),
    'agent_fields_exactly_allowlisted':safe_fields,
    'task_file_readonly':denied(lambda:task_file.write_text('ATTACK')),
    'other_task_not_mounted':not Path('/other-task/marker').exists(),
    'original_dataset_not_mounted':not Path('/repo/data/tasks.jsonl').exists(),
    'reference_not_in_staged_directory':not Path('/input/ground_truth.ifc').exists(),
})
"""
    code=code.replace(insert_before,supplemental+"\n"+insert_before)
    return code


TRUSTED_PILOT_INPUT_PROBE=_make_trusted_pilot_probe()
PILOT_PROBE_ID="g2-pinned-bim-edit-input-mount-v0.1"
PILOT_CHECK_NAMES=(
    "only_staged_source_and_task_visible",
    "payload_sha256_matches_pinned_host",
    "agent_fields_exactly_allowlisted",
    "task_file_readonly",
    "other_task_not_mounted",
    "original_dataset_not_mounted",
    "reference_not_in_staged_directory",
)


@dataclass(frozen=True)
class DockerProbePolicy:
    image_id:str
    memory_bytes:int=134217728
    pid_limit:int=16
    cpu_share:float=0.5
    wall_timeout_seconds:int=25
    python_entrypoint:str="/usr/bin/python3"

    def __post_init__(self):
        if not isinstance(self.image_id,str) or not IMAGE_ID.fullmatch(self.image_id):
            raise DockerIsolationError(
                "Security probe must use immutable full sha256 local image ID, never a tag"
            )
        if self.memory_bytes!=134217728 or self.pid_limit!=16:
            raise DockerIsolationError("Probe cgroup limits must match frozen policy")
        if self.cpu_share!=0.5 or self.wall_timeout_seconds!=25:
            raise DockerIsolationError("Probe CPU/wall-time limits must match frozen policy")
        if self.python_entrypoint not in PYTHON_ENTRYPOINTS:
            raise DockerIsolationError("Probe Python entrypoint must be one of two fixed trusted paths")


def _docker_binary()->str:
    cli=shutil.which("docker")
    if not cli or not Path(cli).is_file():
        raise DockerIsolationError("Docker client not installed")
    return str(Path(cli).resolve())


def _invoke(args:list[str],*,timeout:int=12)->subprocess.CompletedProcess:
    # Only a minimal host environment reaches the Docker client. The sentinel
    # exercises the guarantee it does NOT flow into the worker container.
    if os.name=="nt":
        env={key:os.environ[key] for key in (
            "SYSTEMROOT","WINDIR","COMSPEC","TEMP","TMP","USERPROFILE"
        ) if key in os.environ}
        env["PATH"]=str(Path(args[0]).parent)
    else:
        env={"HOME":str(Path.home()),
             "PATH":"/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"}
    # Deliberately fake sentinel reaches Docker client only, never container.
    env["OPENAI_API_KEY"]="BIM_BENCH_FAKE_LOCAL_PROBE_SENTINEL"
    try:
        anchored=pinned_local_docker_argv(args)
    except LocalDockerTransportError as exc:
        raise DockerIsolationError("Trusted probe must use fixed local Docker engine") from exc
    try:
        return subprocess.run(
            anchored,capture_output=True,text=True,timeout=timeout,
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
        "--entrypoint="+policy.python_entrypoint,
        policy.image_id,"-c",TRUSTED_PROBE,
    ]


def _validate_created(container:dict,policy:DockerProbePolicy,
                      expected_probe:str=TRUSTED_PROBE)->dict:
    if expected_probe not in (TRUSTED_PROBE,TRUSTED_PILOT_INPUT_PROBE):
        raise DockerIsolationError("Unapproved probe program or model-generated code")
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
            cfg.get("Entrypoint")==[policy.python_entrypoint]
            and (cfg.get("Cmd") or [])==["-c",expected_probe]
        ),
    }
    return checks


def build_pilot_input_probe_argv(
    binary:str,policy:DockerProbePolicy,name:str,stage_root:Path,
    output_root:Path,source_sha256:str,payload_sha256:str,
)->list[str]:
    """Construct *fixed trusted* source-input-only kernel probe, NEVER an LLM executor."""
    for digest in (source_sha256,payload_sha256):
        if not isinstance(digest,str) or not re.fullmatch(r"[0-9a-f]{64}",digest):
            raise DockerIsolationError("Pinned task/source SHA256 missing or malformed")
    argv=build_probe_argv(binary,policy,name,stage_root,output_root)
    if argv[-1]!=TRUSTED_PROBE:
        raise DockerIsolationError("Trusted probe base was unexpectedly replaced")
    argv[-1]=TRUSTED_PILOT_INPUT_PROBE
    idx=argv.index("--entrypoint="+policy.python_entrypoint)
    argv[idx:idx]=[
        "--env=BIM_STAGE_SOURCE_SHA256="+source_sha256,
        "--env=BIM_STAGE_PAYLOAD_SHA256="+payload_sha256,
    ]
    return argv


def _validate_pilot_created(
    container:dict,policy:DockerProbePolicy,stage_root:Path,
    output_root:Path,source_sha256:str,payload_sha256:str,
)->dict:
    """Independent created-container checks, including actual HOST source mount origins."""
    checks=_validate_created(container,policy,TRUSTED_PILOT_INPUT_PROBE)
    env=container.get("Config",{}).get("Env") or []
    actual=[v for v in env if v.startswith("BIM_STAGE_")]
    checks["only_expected_public_sha_env"]=sorted(actual)==sorted((
        "BIM_STAGE_SOURCE_SHA256="+source_sha256,
        "BIM_STAGE_PAYLOAD_SHA256="+payload_sha256,
    ))
    host_mounts=(container.get("HostConfig") or {}).get("Mounts") or []
    observed=set()
    for item in host_mounts:
        if item.get("Type")!="bind":
            observed.add(("INVALID",True,""))
            continue
        origin=item.get("Source","")
        if not isinstance(origin,str) or not origin:
            observed.add(("INVALID",True,""))
            continue
        # HostConfig.Mounts.Source preserves the original native host path.
        observed.add((
            item.get("Target"),
            item.get("ReadOnly") is True,
            str(Path(origin).resolve()).casefold(),
        ))
    expected={
        ("/input",True,str(stage_root.resolve(strict=True)).casefold()),
        ("/output",False,str(output_root.resolve(strict=True)).casefold()),
    }
    checks["exact_host_stage_and_output_mount_origins"]=(len(host_mounts)==2 and observed==expected)
    return checks


def _validate_pilot_runtime(data:dict,policy:DockerProbePolicy)->dict:
    checks=_validate_runtime(data,policy)
    checks.update({key:data.get(key) is True for key in PILOT_CHECK_NAMES})
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
                "image_id":policy.image_id,
                "python_entrypoint":policy.python_entrypoint,
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


def run_pinned_pilot_input_mount_probe(policy:DockerProbePolicy,root:Path)->dict:
    """Use ONE original cached IFC solely as opaque bytes in three fixed trusted probes.

    Strict read-only Docker local-engine mount proof; no model-generated code,
    no GT/evaluator access, no network, no inference and no IFC parsing.
    """
    from src.data.bim_edit import repo_asset_path
    from src.data.pilot_workspace import (
        _frozen_inputs, pilot_staging_preflight, stage_verified_pilot_input
    )

    root=root.resolve(strict=True)
    if not root.is_dir() or not (root/"AGENTS.md").is_file():
        raise DockerIsolationError("Not the established frozen research checkout")
    statuses=pilot_staging_preflight(root)
    if (statuses["original_tasks"]!=36 or statuses["input_available_tasks"]!=30
            or statuses["blocked_input_tasks"]!=6
            or statuses["llm_launch_allowed"] is not False):
        raise DockerIsolationError("Original full-denominator pilot admission unexpectedly changed")
    selected,audited,_,_=_frozen_inputs(root)
    # Exercise a REAL original source also used as another task's GT by filename.
    # It is accessed exclusively in this task's own INPUT role, as opaque bytes.
    task_id=next((
        tid for tid in sorted(selected)
        if statuses["task_status"][tid]=="STAGING_INPUT_AVAILABLE_NO_LAUNCH"
        and audited[repo_asset_path(selected[tid]["input_ifc"])].get(
            "is_cross_task_reference_alias_in_original_324"
        ) is True
    ),None)
    if task_id is None:
        raise DockerIsolationError("No pinned, cached cross-task-reference-alias input")
    _ensure_cached_image(_docker_binary(),policy.image_id)
    binary=_docker_binary()
    arm_results=[]
    source_shas=set()
    payload_shas=set()
    with tempfile.TemporaryDirectory(prefix="bim-bench-pilot-mount-trusted-") as tmp:
        work=Path(tmp)
        scratch=work/"staged"
        scratch.mkdir()
        # OWN fake canaries are outside all Docker mounts, not real reference assets.
        canary_dirs=(work/"grader",work/"other-task",work/"repo"/"data")
        for folder in canary_dirs:
            folder.mkdir(parents=True)
        canaries=(
            (canary_dirs[0]/"ground_truth.ifc",b"OWN_FAKE_REFERENCE_NOT_MOUNTED"),
            (canary_dirs[1]/"marker",b"OWN_FAKE_OTHER_TASK_NOT_MOUNTED"),
            (canary_dirs[2]/"tasks.jsonl",b"OWN_FAKE_FULL_CORPUS_NOT_MOUNTED"),
        )
        for file,contents in canaries:
            file.write_bytes(contents)
        originals={str(file):sha256(file.read_bytes()).hexdigest()
                   for file,_ in canaries}
        for arm in statuses["arms"]:
            stage=stage_verified_pilot_input(root,scratch,task_id,arm)
            stage_file=stage.workspace/"input.ifc"
            payload_file=stage.workspace/"task.json"
            source_digest=stage.source_byte_sha256
            task_digest=sha256(payload_file.read_bytes()).hexdigest()
            if sha256(stage_file.read_bytes()).hexdigest()!=source_digest:
                raise DockerIsolationError("Original pinned source copy digest changed")
            source_shas.add(source_digest)
            payload_shas.add(task_digest)
            output=work/("out-"+arm)
            output.mkdir(mode=0o777)
            output.chmod(0o777)
            name="bim-bench-probe-"+uuid.uuid4().hex[:16]
            argv=build_pilot_input_probe_argv(
                binary,policy,name,stage.workspace,output,source_digest,task_digest
            )
            container_id=None
            try:
                created=_invoke(argv,timeout=15)
                if created.returncode!=0:
                    raise DockerIsolationError("Trusted pilot source-only container create failed")
                container_id=created.stdout.strip()
                if not re.fullmatch(r"[0-9a-f]{64}",container_id):
                    raise DockerIsolationError("Untrusted container identifier")
                inspection=_invoke([binary,"inspect",container_id],timeout=10)
                if inspection.returncode!=0:
                    raise DockerIsolationError("Cannot inspect created source-only container")
                try:
                    records=json.loads(inspection.stdout)
                except (TypeError,ValueError) as exc:
                    raise DockerIsolationError("Invalid Docker inspect JSON") from exc
                if not isinstance(records,list) or len(records)!=1:
                    raise DockerIsolationError("Docker inspect must return exactly one container")
                config_checks=_validate_pilot_created(
                    records[0],policy,stage.workspace,output,source_digest,task_digest
                )
                if not all(config_checks.values()):
                    raise DockerIsolationError(
                        "Pinned pilot Docker HostConfig, mount origin or env policy violated"
                    )
                started=_invoke(
                    [binary,"start","--attach",container_id],
                    timeout=policy.wall_timeout_seconds
                )
                if started.returncode!=0:
                    raise DockerIsolationError("Fixed pilot mount probe process failed")
                try:
                    run=json.loads(started.stdout.strip())
                except (ValueError,TypeError) as exc:
                    raise DockerIsolationError("Invalid trusted pilot probe stdout") from exc
                evidence=output/"probe_result.json"
                if (evidence.is_symlink() or not evidence.is_file()
                        or {f.name for f in output.iterdir()}!={"probe_result.json"}):
                    raise DockerIsolationError("Unexpected or missing trusted pilot output")
                if json.loads(evidence.read_text(encoding="utf8"))!=run:
                    raise DockerIsolationError("Container stdout and output evidence disagree")
                runtime_checks=_validate_pilot_runtime(run,policy)
                if not all(runtime_checks.values()):
                    raise DockerIsolationError("Actual OS or task-isolation restriction failed")
                if (sha256(stage_file.read_bytes()).hexdigest()!=source_digest
                        or sha256(payload_file.read_bytes()).hexdigest()!=task_digest):
                    raise DockerIsolationError("Staged input or sanitized task mutated")
                arm_results.append({
                    "arm":arm,
                    "staged_source_sha256":source_digest,
                    "staged_payload_sha256":task_digest,
                    "container_prestart_checks":config_checks,
                    "actual_kernel_and_task_file_checks":runtime_checks,
                    "original_staged_files_unchanged":True,
                    "passed":True,
                })
            finally:
                cleanup=_invoke([binary,"rm","--force",name],timeout=12)
                if container_id and cleanup.returncode!=0:
                    raise DockerIsolationError("Failed cleaning own trusted pilot probe container")
        if len(source_shas)!=1 or len(payload_shas)!=1 or len(arm_results)!=3:
            raise DockerIsolationError("Paired arm task input or prompt differs")
        for file,_ in canaries:
            if sha256(file.read_bytes()).hexdigest()!=originals[str(file)]:
                raise DockerIsolationError("Unmounted original fake reference canary modified")

    return {
        "probe_id":PILOT_PROBE_ID,
        "status":"PINNED_PILOT_DOCKER_INPUT_MOUNT_PROBE_PASS",
        "original_pilot_denominator":36,
        "locally_ready_task_rows":30,
        "missing_or_blocked_task_rows":6,
        "single_pinned_task_id":task_id,
        "input_also_other_task_reference_path":True,
        "arm_count":len(arm_results),
        "same_original_IFC_sha256_across_arms":True,
        "same_sanitized_prompt_sha256_across_arms":True,
        "image_id":policy.image_id,
        "python_entrypoint":policy.python_entrypoint,
        "docker_server_version":_docker_version(binary),
        "arm_probes":arm_results,
        "OWN_hidden_reference_and_other_task_canaries_unchanged":True,
        "temporary_task_workspaces_and_containers_cleaned":True,
        "original_IFC_native_geometry_parsed":False,
        "original_GT_role_file_opened":False,
        "official_tasks_scored":0,
        "model_generated_python_executed":False,
        "real_model_provider_called":False,
        "rights_for_model_provider_verified":False,
        "worker_image_scientifically_approved":False,
        "paid_model_pilot_ready":False,
        "production_scored_python_enabled":False,
    }


def _docker_version(binary:str)->str:
    version=_invoke([binary,"version","--format","{{.Server.Version}}"],timeout=8)
    if version.returncode!=0:
        raise DockerIsolationError("Docker daemon became unreachable")
    value=version.stdout.strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+.*",value):
        raise DockerIsolationError("Unexpected Docker server version")
    return value
