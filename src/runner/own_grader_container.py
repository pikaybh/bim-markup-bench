"""Independently isolated Docker grader for OWN synthetic IFC only.

The grader sees an OWN reference IFC, but never a candidate script.
The candidate container sees the script, but never the reference IFC.
This module does NOT implement or certify the official BIM-Edit scorer.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import tempfile
import uuid

from src.runner.docker_isolation import DockerIsolationError
from src.runner.ifc_worker import _run,_verify_local_image,_sha
from src.runner.generated_candidate import _limited_attach

OWN_GT=Path(__file__).resolve().parents[2]/"tests/fixtures/synthetic/expected_wall_height.ifc"

TRUSTED_GRADER_PROGRAM=r"""
import ifcopenshell,json
from pathlib import Path

original=ifcopenshell.open("/source/source.ifc")
submitted=ifcopenshell.open("/submission/candidate.ifc")
reference=ifcopenshell.open("/ground_truth/expected.ifc")
if any(model.schema!="IFC4X3" for model in (original,submitted,reference)):
    raise ValueError("Wrong native IFC4X3 schema")
if any(len(model.by_type("IfcWall"))!=1 for model in (original,submitted,reference)):
    raise ValueError("Unexpected wall count")

def depth(model):
    wall=model.by_type("IfcWall")[0]
    solid=next(x for rep in wall.Representation.Representations
               for x in rep.Items if x.is_a("IfcExtrudedAreaSolid"))
    return float(solid.Depth)

if abs(depth(original)-3.0)>1e-6:
    raise ValueError("Owned source baseline mismatch")
if abs(depth(reference)-3.3)>1e-6 or abs(depth(submitted)-depth(reference))>1e-6:
    raise ValueError("Candidate failed independent reference height check")
start={x.id():str(x) for x in original}
finish={x.id():str(x) for x in submitted}
if set(start)!=set(finish):
    raise ValueError("Unexpected IFC entity creation/deletion")
delta=[i for i in start if start[i]!=finish[i]]
if len(delta)!=1 or not original.by_id(delta[0]).is_a("IfcExtrudedAreaSolid"):
    raise ValueError("Extra mutations outside declared wall height")
original_ids={(x.GlobalId,x.is_a()) for x in original.by_type("IfcRoot")}
submitted_ids={(x.GlobalId,x.is_a()) for x in submitted.by_type("IfcRoot")}
if original_ids!=submitted_ids:
    raise ValueError("Root identity/type mismatch")
print(json.dumps({
    "status":"OWN_ISOLATED_GRADER_PASS",
    "GT_mounted_in_separate_grader_only":True,
    "candidate_script_mounted_in_grader":False,
    "reference_expected_height":depth(reference),
    "candidate_observed_height":depth(submitted),
    "only_expected_native_STEP_changed":True,
    "official_scores_computed":0,
    "paid_model_calls":0,
},sort_keys=True))
"""


def inspect_own_grader(container_id:str,image_id:str)->None:
    res=_run(["docker","inspect",container_id],timeout=12)
    if res.returncode!=0:
        raise DockerIsolationError("OWN independent grader inspect failed")
    try:
        instances=json.loads(res.stdout)
        if not isinstance(instances,list) or len(instances)!=1:
            raise ValueError
        entry=instances[0]
        h=entry["HostConfig"];c=entry["Config"]
        mounts=entry["Mounts"]
        required={"/source":False,"/submission":False,"/ground_truth":False}
        actual={m.get("Destination"):m.get("RW")
                for m in mounts if m.get("Type")=="bind"}
        expected_cmd=["-c",TRUSTED_GRADER_PROGRAM]
        conditions=[
            entry.get("Image")==image_id,
            h.get("NetworkMode")=="none",
            h.get("ReadonlyRootfs") is True,
            h.get("Privileged") is False,
            "ALL" in (h.get("CapDrop") or []),
            any("no-new-privileges" in x for x in (h.get("SecurityOpt") or [])),
            h.get("IpcMode")=="none",
            h.get("PidsLimit")==1,
            h.get("Memory")==536870912,
            h.get("MemorySwap")==536870912,
            h.get("NanoCpus")==750000000,
            c.get("User")=="65534:65534",
            c.get("Entrypoint")==["/usr/local/bin/python3"],
            c.get("Cmd")==expected_cmd,
            actual==required and len(mounts)==3,
            all(m.get("Type")=="bind" and m.get("RW") is False for m in mounts),
            not any(m.get("Destination") in ("/task","/input","/output") for m in mounts),
            not any(line.split("=",1)[0] in
                    ("OPENAI_API_KEY","AWS_SECRET_ACCESS_KEY","GH_TOKEN","SSH_AUTH_SOCK")
                    for line in c.get("Env",[])),
            "/tmp" in (h.get("Tmpfs") or {}),
        ]
        if not all(conditions):
            raise DockerIsolationError("Independent grader HostConfig safety policy failed")
    except (ValueError,IndexError,KeyError,TypeError) as exc:
        raise DockerIsolationError("Invalid isolated grader Docker metadata") from exc


def run_own_isolated_grader(image_id:str,source_ifc:Path,
                           result_ifc:Path)->dict:
    """Only local OWN synthetic GT is staged; never an official GT asset."""
    _verify_local_image(image_id)
    if any(path.is_symlink() or not path.is_file()
           for path in (OWN_GT,source_ifc,result_ifc)):
        raise DockerIsolationError("OWN grader inputs must be ordinary files")
    hidden_gt_digest=_sha(OWN_GT)
    source_digest=_sha(source_ifc)
    candidate_digest=_sha(result_ifc)
    name="bim-bench-own-grader-"+uuid.uuid4().hex[:12]
    created_id=None
    with tempfile.TemporaryDirectory(prefix="bim-bench-own-grader-") as folder:
        root=Path(folder)
        source_dir=root/"source";out_dir=root/"submitted";gt_dir=root/"expected"
        for directory in (source_dir,out_dir,gt_dir):directory.mkdir()
        (source_dir/"source.ifc").write_bytes(source_ifc.read_bytes())
        (out_dir/"candidate.ifc").write_bytes(result_ifc.read_bytes())
        (gt_dir/"expected.ifc").write_bytes(OWN_GT.read_bytes())
        args=[
            "docker","create","--pull=never","--name="+name,
            "--network=none","--read-only","--user=65534:65534",
            "--cap-drop=ALL","--security-opt=no-new-privileges:true",
            "--pids-limit=1","--memory=512m","--memory-swap=512m",
            "--cpus=0.75","--ipc=none","--cgroupns=private",
            "--ulimit=nofile=64:64","--ulimit=core=0:0",
            "--tmpfs=/tmp:rw,nosuid,nodev,noexec,size=16m",
            "--log-driver=json-file","--log-opt=max-size=1m","--log-opt=max-file=1",
            "--mount=type=bind,source="+str(source_dir)+",target=/source,readonly",
            "--mount=type=bind,source="+str(out_dir)+",target=/submission,readonly",
            "--mount=type=bind,source="+str(gt_dir)+",target=/ground_truth,readonly",
            "--env=HOME=/tmp","--env=OPENBLAS_NUM_THREADS=1",
            "--env=OMP_NUM_THREADS=1","--env=MKL_NUM_THREADS=1",
            "--entrypoint=/usr/local/bin/python3",
            image_id,"-c",TRUSTED_GRADER_PROGRAM,
        ]
        try:
            created=_run(args,timeout=15)
            if created.returncode!=0:
                raise DockerIsolationError("Independent OWN grader create denied")
            created_id=created.stdout.strip()
            if not re.fullmatch(r"[0-9a-f]{64}",created_id):
                raise DockerIsolationError("Invalid independent grader container ID")
            inspect_own_grader(created_id,image_id)
            executed=_limited_attach(created_id,12)
            if executed.returncode!=0:
                raise DockerIsolationError("Independent OWN grader rejected output")
            try:
                lines=[json.loads(x) for x in executed.stdout.splitlines()
                       if x.startswith("{")]
            except ValueError as exc:
                raise DockerIsolationError("Invalid trusted grader JSON") from exc
            if len(lines)!=1 or lines[0].get("status")!="OWN_ISOLATED_GRADER_PASS":
                raise DockerIsolationError("Independent OWN grader did not pass")
            if (_sha(source_ifc)!=source_digest
                    or _sha(result_ifc)!=candidate_digest
                    or _sha(OWN_GT)!=hidden_gt_digest):
                raise DockerIsolationError("Grader altered an original protected asset")
            return lines[0]
        finally:
            cleanup=_run(["docker","rm","--force",name],timeout=12)
            if created_id is not None and cleanup.returncode!=0:
                raise DockerIsolationError("Failed to clean own isolated grader")
