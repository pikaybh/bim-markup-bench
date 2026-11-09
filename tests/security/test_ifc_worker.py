"""Curated Linux ARM64 and AMD64 IFC workers, gated kernel smoke."""
from __future__ import annotations
import os
from pathlib import Path
import unittest
import json
import subprocess
import sys

from src.runner.ifc_worker import (
    TRUSTED_CASES, run_own_fixture, _verify_local_image, _inspect_config
)
from unittest.mock import patch
from src.runner.docker_isolation import DockerIsolationError

ROOT=Path(__file__).resolve().parents[2]
WORKER=ROOT/"docker/ifc_worker"
LOCAL_IMAGE=os.environ.get("BIM_BENCH_IFC_WORKER_IMAGE_SHA","")

class WorkerStaticTests(unittest.TestCase):
    def test_digest_pinned_base_and_hash_pinned_native_dependencies(self):
        dockerfile=(WORKER/"Dockerfile").read_text()
        lock=(WORKER/"requirements.lock").read_text()
        self.assertIn("python:3.12-slim-bookworm@sha256:df540bfd",dockerfile)
        self.assertIn("--require-hashes",dockerfile)
        self.assertIn("--only-binary=:all:",dockerfile)
        self.assertIn("USER 65534:65534",dockerfile)
        self.assertIn("OPENBLAS_NUM_THREADS=1",dockerfile)
        self.assertIn("ifcopenshell==0.8.4.post1",lock)
        self.assertIn("sha256:904ff0f1e44c",lock)  # pinned ARM64 CPython 3.12 wheel
        for name in ("numpy","shapely","lark","isodate","python-dateutil"):
            self.assertIn(name+"==",lock)
        for banned in ("openai==","python-dotenv==","requests=="):
            self.assertNotIn(banned,lock)

    def test_amd64_worker_pinned_base_and_hash_locked_wheels(self):
        dockerfile=(WORKER/"Dockerfile.amd64").read_text()
        lock=(WORKER/"requirements.amd64.lock").read_text()
        self.assertIn("python:3.12-slim-bookworm@sha256:0f086103",dockerfile)
        self.assertIn("requirements.amd64.lock",dockerfile)
        self.assertIn("--require-hashes",dockerfile)
        self.assertIn("--only-binary=:all:",dockerfile)
        self.assertIn("USER 65534:65534",dockerfile)
        self.assertIn("ifcopenshell==0.8.4.post1",lock)
        self.assertIn("--hash=sha256:",lock)
        self.assertNotIn("openai==",lock)

    def test_missing_output_tmpfs_or_output_bind_refused_before_start(self):
        image="sha256:"+"a"*64
        report={
            "Image":image,
            "HostConfig":{
                "NetworkMode":"none","ReadonlyRootfs":True,
                "Privileged":False,"CapDrop":["ALL"],
                "SecurityOpt":["no-new-privileges:true"],
                "IpcMode":"none","CgroupnsMode":"private",
                "PidsLimit":1,"Memory":536870912,
                "MemorySwap":536870912,"NanoCpus":750000000,
                "PidMode":"","Tmpfs":{
                    "/tmp":"rw,nosuid,nodev,noexec,size=16m",
                    "/output":"rw,nosuid,nodev,noexec,size=64m",
                },
            },
            "Config":{"User":"65534:65534",
                      "Entrypoint":["/usr/local/bin/python3"],
                      "Cmd":["/opt/ifc_worker/trusted_probe.py"],
                      "Env":["HOME=/tmp","OPENBLAS_NUM_THREADS=1"]},
            "Mounts":[{"Destination":"/input","RW":False,"Type":"bind"}],
        }
        def check(item,should_fail=False):
            result=subprocess.CompletedProcess(["docker","inspect"],0,
                json.dumps([item]),"")
            with patch("src.runner.ifc_worker._run",return_value=result):
                if should_fail:
                    with self.assertRaises(DockerIsolationError):
                        _inspect_config("own-container",image,False)
                else:
                    _inspect_config("own-container",image,False)
        check(report)
        mutated=json.loads(json.dumps(report))
        del mutated["HostConfig"]["Tmpfs"]["/output"]
        check(mutated,True)
        mutated=json.loads(json.dumps(report))
        mutated["Mounts"].append({"Destination":"/output","RW":True,"Type":"bind"})
        check(mutated,True)
        mutated=json.loads(json.dumps(report))
        mutated["HostConfig"]["Tmpfs"]["/output"]="rw,size=4g"
        check(mutated,True)

    def test_unexpected_docker_mount_types_and_host_namespace_are_refused(self):
        image="sha256:"+"a"*64
        baseline={
            "Image":image,
            "HostConfig":{
                "NetworkMode":"none","ReadonlyRootfs":True,
                "Privileged":False,"CapDrop":["ALL"],
                "SecurityOpt":["no-new-privileges:true"],
                "IpcMode":"none","CgroupnsMode":"private",
                "PidsLimit":1,"Memory":536870912,
                "MemorySwap":536870912,"NanoCpus":750000000,
                "PidMode":"","Tmpfs":{
                    "/tmp":"rw,nosuid,nodev,noexec,size=16m",
                    "/output":"rw,nosuid,nodev,noexec,size=64m",
                },
            },
            "Config":{"User":"65534:65534",
                      "Entrypoint":["/usr/local/bin/python3"],
                      "Cmd":["/opt/ifc_worker/run_candidate.py"],
                      "Env":["HOME=/tmp"]},
            "Mounts":[
                {"Destination":"/input","RW":False,"Type":"bind"},
                {"Destination":"/task","RW":False,"Type":"bind"},
            ],
        }
        def inspect(data, denied=False):
            fake=subprocess.CompletedProcess(["docker","inspect"],0,
                                              json.dumps([data]),"")
            with patch("src.runner.ifc_worker._run",return_value=fake):
                if denied:
                    with self.assertRaises(DockerIsolationError):
                        _inspect_config("own-container",image,True)
                else:
                    _inspect_config("own-container",image,True)

        inspect(baseline)
        for label, change in (
            ("named_volume",lambda v:v["Mounts"].append({
                "Destination":"/grader","RW":False,"Type":"volume"
            })),
            ("extra_tmpfs_mount",lambda v:v["Mounts"].append({
                "Destination":"/secrets","RW":True,"Type":"tmpfs"
            })),
            ("host_cgroup_namespace",lambda v:v["HostConfig"].update(
                CgroupnsMode="host")),
            ("host_secret_environment",lambda v:v["Config"]["Env"].append(
                "OPENAI_API_KEY=FAKE_TEST_CANARY")),
            ("wrong_task_mount",lambda v:v["Mounts"][1].update(
                Destination="/grader")),
        ):
            with self.subTest(label=label):
                mutated=json.loads(json.dumps(baseline))
                change(mutated)
                inspect(mutated,denied=True)

    def test_no_arbitrary_generated_code_interface(self):
        self.assertEqual(len(TRUSTED_CASES),5)
        for name,script in TRUSTED_CASES.items():
            compile(script,name,"exec")
        with self.assertRaises(DockerIsolationError):
            run_own_fixture("sha256:"+"0"*64,"MODEL_GENERATED_SCRIPT")
        with self.assertRaises(DockerIsolationError):
            run_own_fixture("latest","edit-wall")

    def test_trusted_worker_limits_in_source(self):
        source=(ROOT/"src/runner/ifc_worker.py").read_text()
        for strict in ("--pull=never","--network=none","--read-only",
                       "--cap-drop=ALL","--pids-limit=1","--memory=512m",
                       "--memory-swap=512m","--ulimit=fsize=33554432:33554432",
                       "DockerIsolationError","--mount=type=bind",
                       "container_name"):
            self.assertIn(strict,source)
        self.assertIn("--tmpfs=/output:rw,nosuid,nodev,noexec,size=64m",source)
        wrapper=(WORKER/"run_candidate.py").read_text()
        self.assertIn("resource.RLIMIT_FSIZE",wrapper)
        self.assertIn("resource.RLIMIT_CPU",wrapper)
        self.assertIn("resource.RLIMIT_CORE",wrapper)
        self.assertIn("Path(\"/task/solution.py\")",wrapper)

    def test_old_primary_gates_unchanged(self):
        from src.runner.sandbox import execute_untrusted_candidate,SandboxNotReady
        with self.assertRaises(SandboxNotReady):
            execute_untrusted_candidate("print('this cannot execute')")
        from src.runner.cli import main
        self.assertEqual(main(["score"]),2)

@unittest.skipUnless(LOCAL_IMAGE,"Run curated Docker integration with exact image ID")
class WorkerLiveDockerTests(unittest.TestCase):
    def test_native_ifc_read_write_and_edit_with_shared_input_unchanged(self):
        for name in ("trusted-native-smoke","edit-wall"):
            with self.subTest(case=name):
                result=run_own_fixture(LOCAL_IMAGE,name)
                self.assertEqual(result["status"],"OWN_TRUSTED_WORKER_FIXTURE_PASS")
                self.assertTrue(result["source_unchanged"])
                self.assertTrue(result["hidden_gt_unchanged"])
                self.assertFalse(result["model_generated_python_executed"])
                self.assertEqual(result["paid_model_calls"],0)

    def test_malicious_file_process_network_and_environment_denied(self):
        result=run_own_fixture(LOCAL_IMAGE,"deny-attacks")
        self.assertEqual(result["status"],"OWN_TRUSTED_WORKER_FIXTURE_PASS")
        data=result["result"]
        self.assertEqual(data["uid"],65534)
        self.assertTrue(all(v is True for k,v in data.items() if k!="uid"))

    def test_file_size_limit_and_wall_clock_timeout_are_enforced(self):
        oversize=run_own_fixture(LOCAL_IMAGE,"oversize-output")
        self.assertTrue(oversize["result"]["oversize_output_blocked"])
        full=run_own_fixture(LOCAL_IMAGE,"bounded-output-volume")
        self.assertTrue(full["result"]["total_directory_quota_blocked"])
        self.assertLess(full["result"]["files_written"],3)
        runaway=run_own_fixture(LOCAL_IMAGE,"infinite-loop",wall_seconds=3)
        self.assertEqual(runaway["status"],"BLOCKED_WALL_CLOCK_TIMEOUT")
        self.assertEqual(runaway["paid_model_calls"],0)

    def test_runner_does_not_leave_its_containers(self):
        from src.runner.ifc_worker import _docker_cli
        p=subprocess.run([_docker_cli(),"ps","-a","--filter",
             "name=bim-bench-own-worker","--format","{{.ID}}"],
             capture_output=True,text=True,timeout=15)
        self.assertEqual(p.returncode,0)
        self.assertEqual(p.stdout.strip(),"")

    def test_enforced_live_gate_remains_blocked(self):
        cmd=[sys.executable,"-m","tools.verify_ifc_worker",
             "--image-id",LOCAL_IMAGE,"--enforce-live"]
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=100)
        self.assertEqual(p.returncode,2,p.stderr)
        data=json.loads(p.stdout)
        self.assertEqual(data["status"],"CURATED_WORKER_OWN_SYNTHETIC_TESTS_PASS")
        self.assertEqual(data["G2_paid_pilot_gate"],"BLOCKED")
        self.assertEqual(data["paid_model_calls"],0)

if __name__=="__main__":
    unittest.main()
