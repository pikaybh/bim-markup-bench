"""Curated Linux ARM64/AMD64 IFC worker runner -- trusted OWN tests ONLY.

This runner deliberately DOES NOT accept arbitrary user/LLM code. Only two
hardcoded, owned fixture programs execute under Docker. Independent work is
required before exposing a model-generated code path.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid

from src.runner.docker_isolation import DockerIsolationError

BASE = Path(__file__).resolve().parents[2]
OWN_SOURCE = BASE / "tests/fixtures/synthetic/input.ifc"
IMAGE_PATTERN = re.compile(r"sha256:[a-f0-9]{64}\Z")

TRUSTED_CASES = {
    "edit-wall": r'''
import hashlib,ifcopenshell,json
from pathlib import Path
source=Path("/input/input.ifc")
before=hashlib.sha256(source.read_bytes()).hexdigest()
f=ifcopenshell.open(str(source))
wall=f.by_type("IfcWall")[0]
solid=next(
    item for rep in wall.Representation.Representations
    for item in rep.Items if item.is_a("IfcExtrudedAreaSolid")
)
solid.Depth=3.3
f.write("/output/result.ifc")
print(json.dumps({"case":"edit-wall","source_unchanged":hashlib.sha256(source.read_bytes()).hexdigest()==before,"reopened_wall_depth":next(item.Depth for rep in ifcopenshell.open("/output/result.ifc").by_type("IfcWall")[0].Representation.Representations for item in rep.Items if item.is_a("IfcExtrudedAreaSolid"))}))
''',
    "infinite-loop": "while True: pass\n",
    "oversize-output": '''
from pathlib import Path
import json
blocked=False
try:
    with Path("/output/bounded_file.dat").open("wb") as f:
        f.write(b"X"*(33*1024*1024))
except OSError:
    blocked=True
print(json.dumps({"oversize_output_blocked":blocked}))
''',
    "bounded-output-volume": """
import json
from pathlib import Path
blocked=False
files_written=0
for i in range(5):
    try:
        (Path("/output")/f"bounded_{i}.bin").write_bytes(b"A"*(24*1024*1024))
        files_written+=1
    except OSError:
        blocked=True
        break
print(json.dumps({"total_directory_quota_blocked":blocked,
                  "files_written":files_written}))
""",
    "deny-attacks": r'''
import json,os,socket,subprocess
from pathlib import Path
source=Path("/input/input.ifc")
def denied(f):
 try:
  f()
  return False
 except Exception:
  return True
out={
 "input_write_denied":denied(lambda:source.write_bytes(b"EVIL")),
 "gt_missing":not Path("/grader/ground_truth.ifc").exists(),
 "parent_traversal_denied":denied(lambda:Path("/input/../grader/ground_truth.ifc").read_bytes()),
 "parent_key_absent":os.getenv("OPENAI_API_KEY") is None,
 "network_denied":denied(lambda:socket.create_connection(("1.1.1.1",443),timeout=1)),
 "subprocess_denied":denied(lambda:subprocess.run(["/bin/sh","-c","echo hello"],timeout=2,check=True)),
 "docker_socket_hidden":not Path("/var/run/docker.sock").exists(),
 "rootfs_write_denied":denied(lambda:Path("/etc/fake_file_bim").write_text("no")),
 "uid":os.geteuid()
}
print(json.dumps(out,sort_keys=True))
''',
}


def _docker_cli()->str:
    """Resolve ONLY the host Docker CLI, never a path supplied by a model."""
    if os.name=="nt":
        candidate=(Path(os.environ.get("ProgramFiles",r"C:\Program Files"))
                   /"Docker"/"Docker"/"resources"/"bin"/"docker.exe")
        if candidate.is_file():
            return str(candidate)
    binary=shutil.which("docker")
    if binary is None:
        raise DockerIsolationError("Local Docker CLI unavailable; no candidate execution")
    return binary


def _host_docker_env()->dict[str,str]:
    """Fixed Docker-control process environment; never inject provider keys."""
    if os.name=="nt":
        env={}
        for name in ("SYSTEMROOT","WINDIR","COMSPEC","TEMP","TMP",
                     "USERPROFILE","APPDATA","LOCALAPPDATA"):
            if name in os.environ:
                env[name]=os.environ[name]
        env["PATH"]=os.pathsep.join((str(Path(_docker_cli()).parent),
                                    os.environ.get("SYSTEMROOT",r"C:\\Windows")
                                    +r"\\System32"))
        return env
    return {"PATH":"/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin",
            "HOME":str(Path.home())}


def _run(args:list[str], timeout:int=12)->subprocess.CompletedProcess:
    env=_host_docker_env()
    fixed=[_docker_cli() if i==0 and arg=="docker" else arg
           for i,arg in enumerate(args)]
    return subprocess.run(fixed,capture_output=True,text=True,
                          timeout=timeout,env=env)

def _sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_local_image(image_id:str)->None:
    if not IMAGE_PATTERN.fullmatch(image_id):
        raise DockerIsolationError("Require exact immutable SHA256 worker image ID")
    result=_run(["docker","image","inspect",image_id])
    if result.returncode!=0:
        raise DockerIsolationError("Pinned worker image is unavailable")
    image=json.loads(result.stdout)[0]
    # Docker Desktop may identify an OCI image index by its manifest
    # digest. Only accept a local exact sha256 ID and the engine's native
    # architecture; emulated ARM64 is not a verified x64 worker.
    platform=_run(["docker","info","--format","{{.Architecture}}"])
    if platform.returncode!=0:
        raise DockerIsolationError("Docker Linux daemon unavailable")
    host_arch={"x86_64":"amd64","aarch64":"arm64"}.get(
        platform.stdout.strip(),platform.stdout.strip()
    )
    if (image.get("Id")!=image_id
        or image.get("Architecture")!=host_arch
        or host_arch not in ("amd64","arm64")
        or image.get("Os")!="linux"):
        raise DockerIsolationError("Worker image must match native Linux daemon architecture")
    labels=image.get("Config",{}).get("Labels") or {}
    if labels.get("org.opencontainers.image.title")!="bim-markup-bench isolated IFC4X3 worker":
        raise DockerIsolationError("Image lacks exact named worker provenance")
    if image.get("Config",{}).get("User")!="65534:65534":
        raise DockerIsolationError("Image does not declare non-root default user")


def _inspect_config(container_id:str, image_id:str, with_task:bool)->None:
    res=_run(["docker","inspect",container_id])
    if res.returncode!=0:
        raise DockerIsolationError("Container inspect failed")
    info=json.loads(res.stdout)[0]
    h=info["HostConfig"];c=info["Config"]
    assert_or_raise=lambda x: x or (_ for _ in ()).throw(DockerIsolationError("Prestart Docker HostConfig isolation check failed"))
    assert_or_raise(info.get("Image")==image_id)
    assert_or_raise(h.get("NetworkMode")=="none")
    assert_or_raise(h.get("ReadonlyRootfs") is True)
    assert_or_raise(h.get("Privileged") is False)
    assert_or_raise("ALL" in (h.get("CapDrop") or []))
    assert_or_raise(any("no-new-privileges" in s for s in (h.get("SecurityOpt") or [])))
    assert_or_raise(c.get("User")=="65534:65534")
    assert_or_raise(h.get("IpcMode")=="none")
    assert_or_raise(h.get("CgroupnsMode")=="private")
    assert_or_raise(h.get("PidsLimit")==1)
    assert_or_raise(h.get("Memory")==536870912)
    assert_or_raise(h.get("MemorySwap")==536870912)
    assert_or_raise(h.get("NanoCpus")==750000000)
    assert_or_raise(h.get("PidMode") in ("","private",None))
    assert_or_raise(c.get("Entrypoint")==["/usr/local/bin/python3"])
    assert_or_raise(c.get("Cmd")==(["/opt/ifc_worker/run_candidate.py"] if with_task else ["/opt/ifc_worker/trusted_probe.py"]))
    env=c.get("Env") or []
    assert_or_raise(not any(line.split("=",1)[0] in ("OPENAI_API_KEY","AWS_SECRET_ACCESS_KEY","GH_TOKEN","SSH_AUTH_SOCK") for line in env))
    mounts=info["Mounts"]
    expected={"/input":False}
    if with_task:expected["/task"]=False
    # Count all mount types: an injected Docker volume is also forbidden.
    assert_or_raise(len(mounts)==len(expected))
    bind_mounts=[m for m in mounts if m.get("Type")=="bind"]
    assert_or_raise(len(bind_mounts)==len(expected))
    assert_or_raise({m.get("Destination"):m.get("RW") for m in bind_mounts}==expected)
    assert_or_raise(all(m.get("Type")=="bind" for m in bind_mounts))
    assert_or_raise(not any(m.get("Destination")=="/output" and
                        m.get("Type")=="bind" for m in mounts))
    tmpfs=h.get("Tmpfs") or {}
    assert_or_raise("/output" in tmpfs and "size=64m" in tmpfs["/output"])
    assert_or_raise("/tmp" in tmpfs and "size=16m" in tmpfs["/tmp"])


def run_own_fixture(image_id:str, case:str="edit-wall", *,wall_seconds:int=20)->dict:
    """Run one fixed program; returned evidence never includes GT or secrets."""
    if case not in ("edit-wall","deny-attacks","oversize-output",
                    "bounded-output-volume","infinite-loop","trusted-native-smoke"):
        raise DockerIsolationError("No arbitrary Python candidate accepted")
    if not 2<=wall_seconds<=25:
        raise DockerIsolationError("Unsafe wall-clock timeout")
    _verify_local_image(image_id)
    container_name="bim-bench-own-worker-"+uuid.uuid4().hex[:12]
    container_id=None
    with tempfile.TemporaryDirectory(prefix="bim-bench-worker-") as d:
        root=Path(d)
        inp=root/"input";task=root/"task";hidden=root/"hidden_gt"
        for folder,mode in ((inp,0o755),(task,0o755),(hidden,0o700)):
            folder.mkdir();folder.chmod(mode)
        input_file=inp/"input.ifc"
        shutil.copyfile(OWN_SOURCE,input_file)
        input_file.chmod(0o444)
        hidden_file=hidden/"ground_truth.ifc";hidden_file.write_bytes(b"OWN_FAKE_GT_DO_NOT_MOUNT")
        before=_sha(input_file)
        gt_before=_sha(hidden_file)
        with_task=case!="trusted-native-smoke"
        if with_task:
            script=task/"solution.py";script.write_text(TRUSTED_CASES[case]);script.chmod(0o444)
        argv=[
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
            "--mount=type=bind,source="+str(inp)+",target=/input,readonly",
            "--env=HOME=/tmp","--env=OPENBLAS_NUM_THREADS=1",
            "--env=OMP_NUM_THREADS=1","--env=MKL_NUM_THREADS=1",
            "--env=NUMEXPR_NUM_THREADS=1",
        ]
        if with_task:
            argv.append("--mount=type=bind,source="+str(task)+",target=/task,readonly")
        argv+=[
            "--entrypoint=/usr/local/bin/python3",image_id,
            "/opt/ifc_worker/run_candidate.py" if with_task else "/opt/ifc_worker/trusted_probe.py"
        ]
        try:
            created=_run(argv,timeout=12)
            if created.returncode!=0:raise DockerIsolationError("Docker worker create failed: "+created.stderr[-200:])
            container_id=created.stdout.strip()
            if not re.fullmatch(r"[0-9a-f]{64}",container_id):
                raise DockerIsolationError("Container ID invalid")
            _inspect_config(container_id,image_id,with_task)
            try:
                started=_run(["docker","start","--attach",container_id],timeout=wall_seconds)
            except subprocess.TimeoutExpired:
                return {"status":"BLOCKED_WALL_CLOCK_TIMEOUT","case":case,
                        "code_executed_inside_container":True,"paid_model_calls":0}
            if started.returncode!=0:
                raise DockerIsolationError("Trusted worker fixture did not execute correctly: "+started.stderr[-200:])
            # The owned script emits a structured result; the trusted
            # wrapper may additionally emit a tiny, bounded IFC artifact.
            messages=[json.loads(line) for line in started.stdout.splitlines()
                      if line.startswith("{")]
            result=next((m for m in messages if "case" in m or
                         "oversize_output_blocked" in m or
                         "total_directory_quota_blocked" in m or
                         "input_write_denied" in m or
                         m.get("status")=="TRUSTED_IFC_WORKER_SMOKE_PASS"),None)
            if result is None:
                raise DockerIsolationError("Trusted worker emitted no supported result")
            if _sha(input_file)!=before or _sha(hidden_file)!=gt_before:
                raise DockerIsolationError("Original IFC or hidden GT was modified")
            if case=="edit-wall":
                import ifcopenshell
                artifact=next((m.get("trusted_small_ifc_b64")
                               for m in messages if "trusted_small_ifc_b64" in m),None)
                if not isinstance(artifact,str) or len(artifact)>350000:
                    raise DockerIsolationError("Missing/bloated trusted IFC artifact")
                try:
                    bytes_out=base64.b64decode(artifact,validate=True)
                except (ValueError,binascii.Error) as exc:
                    raise DockerIsolationError("Invalid IFC artifact transport") from exc
                if not 0<len(bytes_out)<=256*1024:
                    raise DockerIsolationError("Unbounded IFC output artifact")
                host_result=root/"trusted_owned_result.ifc"
                host_result.write_bytes(bytes_out)
                model=ifcopenshell.open(str(host_result))
                depth=next(item.Depth for rep in model.by_type("IfcWall")[0].Representation.Representations
                           for item in rep.Items if item.is_a("IfcExtrudedAreaSolid"))
                if abs(depth-3.3)>1e-7 or result.get("source_unchanged") is not True:
                    raise DockerIsolationError("Native IFC edited wall failed independent re-open")
            elif case=="deny-attacks":
                expected=("input_write_denied","gt_missing","parent_traversal_denied",
                          "parent_key_absent","network_denied","subprocess_denied",
                          "docker_socket_hidden","rootfs_write_denied")
                if not all(result.get(key) is True for key in expected) or result.get("uid")!=65534:
                    raise DockerIsolationError("OS malicious-action probe did not deny everything")
            elif case=="oversize-output":
                if result.get("oversize_output_blocked") is not True:
                    raise DockerIsolationError("Kernel file-size limit was not enforced")
            elif case=="bounded-output-volume":
                if (result.get("total_directory_quota_blocked") is not True
                        or result.get("files_written",6)>=3):
                    raise DockerIsolationError("Whole-directory tmpfs quota not enforced")
            elif case=="trusted-native-smoke" and result.get("status")!="TRUSTED_IFC_WORKER_SMOKE_PASS":
                raise DockerIsolationError("Native trusted IFC smoke failed")
            return {"status":"OWN_TRUSTED_WORKER_FIXTURE_PASS","case":case,
                    "image_id":image_id,"result":result,
                    "source_unchanged":True,"hidden_gt_unchanged":True,
                    "paid_model_calls":0,"official_tasks_scored":0,
                    "model_generated_python_executed":False,
                    "real_model_provider_approved":False}
        finally:
            # Cleanup by our unique allocated name only, including timed out.
            _run(["docker","rm","-f",container_name],timeout=12)
