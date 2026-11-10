"""Read-only / mocked Docker CLI routing audit for OWN-only worker #19.

No Docker daemon/service is started, no image is pulled, no container,
candidate program, GT, scorer, or LLM is launched. Forced local endpoint
is captured for four distinct CLI paths and compared with read-only
live host admission. Expected exit 2 because real Docker/model gate remains
unverified even if mocked routing controls pass.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

from src.runner.local_docker_transport import _local_docker_endpoint
from src.runner.ifc_worker import _run
from src.runner.generated_candidate import _limited_attach
from src.runner.docker_isolation import _invoke
from tools.audit_local_worker_admission import audit_local_worker_admission


def offline_mock_routing_evidence()->dict:
    endpoint=_local_docker_endpoint()
    seen={}
    def fake_run(argv,**kwargs):
        seen.setdefault("worker_control",[]).append(
            {"argv":argv,"env":kwargs.get("env",{})})
        return subprocess.CompletedProcess(argv,0,"{}","")
    with (patch("src.runner.ifc_worker.subprocess.run",side_effect=fake_run)):
        for operation in (
            ["docker","image","inspect","sha256:"+"a"*64],
            ["docker","create","--pull=never","--name=bim-bench-own-synthetic"],
            ["docker","inspect","b"*64],
            ["docker","start","--attach","b"*64],
            ["docker","rm","--force","bim-bench-own-synthetic"],
        ):
            _run(operation)
    attached=[]
    def refuse_popen(argv,**kwargs):
        attached.append({"argv":argv,"env":kwargs.get("env",{})})
        raise RuntimeError("EXPECTED_NO_DOCKER_ATTACH")
    with patch("src.runner.generated_candidate.subprocess.Popen",
               side_effect=refuse_popen):
        try:
            _limited_attach("c"*64,5)
        except RuntimeError as exc:
            if str(exc)!="EXPECTED_NO_DOCKER_ATTACH":
                raise
        else:
            raise RuntimeError("Actual Docker attach unexpectedly executed")
    observed_probe=[]
    def fake_probe(argv,**kwargs):
        observed_probe.append({"argv":argv,"env":kwargs.get("env",{})})
        return subprocess.CompletedProcess(argv,0,"{}","")
    with patch("src.runner.docker_isolation.subprocess.run",side_effect=fake_probe):
        _invoke(["docker","info","--format","{{json .}}"])
    collected=seen["worker_control"]+attached+observed_probe
    if len(collected)!=7:
        raise RuntimeError("Not every OWN Docker control operation was instrumented")
    for item in collected:
        args=item["argv"];env=item["env"]
        if (args[1:3]!=["--host",endpoint] or
                any(name in env for name in (
                    "DOCKER_HOST","DOCKER_CONTEXT","DOCKER_TLS_VERIFY",
                    "DOCKER_CERT_PATH","GITHUB_TOKEN","GH_TOKEN",
                    "AWS_SECRET_ACCESS_KEY"))):
            raise RuntimeError("Docker control command not bound to local socket")
    current=audit_local_worker_admission()
    if current["G2_paid_or_generated_model_worker_authorized"]:
        raise RuntimeError("Unapproved external worker became authorized")
    return {
        "status":"PASS_MOCKED_LOCAL_DOCKER_CONTROL_ROUTING_LIVE_WORKER_BLOCKED",
        "execution_endpoint":endpoint,
        "same_endpoint_all_control_operations":True,
        "mocked_worker_inspect_create_start_cleanup_commands":5,
        "mocked_candidate_attach_commands":1,
        "mocked_kernel_probe_commands":1,
        "real_docker_commands_executed_by_routing_mock":0,
        "actual_host_admission_check":current["status"],
        "actual_local_engine_reachable":current["host_observation"][
            "local_engine_reachable"],
        "actual_image_cache_verified":current["host_observation"][
            "exact_image_id_present"],
        "actual_kernel_os_isolation_verified":False,
        "official_BIM_Edit_evaluator_verified":False,
        "candidate_python_executed":False,
        "paid_model_calls":0,
        "official_tasks_scored":0,
        "production_i_arm_worker_approved":False,
    }


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    report=offline_mock_routing_evidence()
    if args.output_json:
        target=args.output_json
        if target.is_symlink() or target.exists() or not target.parent.is_dir():
            parser.error("Output exists/symlink or parent directory unavailable")
        with target.open("x",encoding="utf8",newline="\n") as file:
            file.write(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
