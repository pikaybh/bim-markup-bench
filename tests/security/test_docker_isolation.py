"""Strict OS Docker probe tests, no generated/unknown Python candidates run."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from src.runner.docker_isolation import (
    DockerIsolationError,DockerProbePolicy,KNOWN_PROBE_ID,TRUSTED_PROBE,
    build_probe_argv,_validate_created,_validate_runtime,
    run_trusted_docker_probe
)

ROOT=Path(__file__).resolve().parents[2]
FAKE_DIGEST="sha256:"+"a"*64
LOCAL_IMAGE=os.environ.get("BIM_BENCH_DOCKER_PROBE_IMAGE_SHA","")


def inspect_stub():
    return {
        "HostConfig":{
            "NetworkMode":"none",
            "ReadonlyRootfs":True,
            "CapDrop":["ALL"],
            "SecurityOpt":["no-new-privileges:true"],
            "PidsLimit":16,
            "Memory":134217728,
            "MemorySwap":134217728,
            "NanoCpus":500000000,
            "Privileged":False,
            "IpcMode":"none",
            "CgroupnsMode":"private",
        },
        "Config":{
            "User":"65534:65534",
            "Env":["HOME=/tmp","PYTHONDONTWRITEBYTECODE=1"],
            "Entrypoint":["/usr/bin/python3"],
            "Cmd":["-c",TRUSTED_PROBE],
        },
        "Mounts":[
            {"Destination":"/input","RW":False,"Type":"bind"},
            {"Destination":"/output","RW":True,"Type":"bind"},
        ]
    }


def runtime_stub():
    return {
        "uid":65534,
        "source_visible":True,
        "source_write_denied":True,
        "host_gt_path_hidden":True,
        "parent_traversal_hidden":True,
        "docker_sock_hidden":True,
        "launcher_key_hidden":True,
        "host_root_write_denied":True,
        "network_denied":True,
        "effective_caps_hex":"0000000000000000",
        "no_new_privileges":"1",
        "seccomp_filter":"2",
        "cgroup_memory_bytes":134217728,
        "cgroup_pid_limit":16,
        "cgroup_cpu_limit":"50000 100000",
    }


class DockerStaticSecurityTests(unittest.TestCase):
    def test_only_exact_pinned_sha256_image_allowed(self):
        for bad in ("ubuntu:22.04","busybox:latest","sha256:abc",
                    "sha256:"+"z"*64,"","a"*64,
                    "sha256:"+"a"*64+";rm -rf /"):
            with self.subTest(bad=bad[:25]),self.assertRaises(DockerIsolationError):
                DockerProbePolicy(bad)
        self.assertEqual(DockerProbePolicy(FAKE_DIGEST).image_id,FAKE_DIGEST)

    def test_limits_cannot_be_relaxed_by_caller(self):
        for update in (
            {"memory_bytes":2**30},
            {"pid_limit":1024},
            {"cpu_share":4.0},
            {"wall_timeout_seconds":3600},
        ):
            with self.subTest(update=update),self.assertRaises(DockerIsolationError):
                DockerProbePolicy(FAKE_DIGEST,**update)

    def test_kernel_security_flags_and_only_two_mounted_directories(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=root/"src";output=root/"result"
            source.mkdir();output.mkdir()
            args=build_probe_argv(
                "/usr/local/bin/docker",DockerProbePolicy(FAKE_DIGEST),
                "bim-bench-probe-0123456789abcdef",source,output
            )
            self.assertEqual(args[1],"create")
            for flag in (
                "--pull=never","--network=none","--read-only",
                "--cap-drop=ALL","--security-opt=no-new-privileges:true",
                "--user=65534:65534","--cgroupns=private","--ipc=none",
                "--pids-limit=16","--memory=134217728",
                "--memory-swap=134217728","--cpus=0.5",
                "--tmpfs=/tmp:rw,nosuid,nodev,noexec,size=16m",
                "--entrypoint=/usr/bin/python3",
            ):
                self.assertIn(flag,args)
            mounted=[v for v in args if v.startswith("--mount=")]
            self.assertEqual(len(mounted),2)
            self.assertIn("target=/input,readonly",mounted[0])
            self.assertIn("target=/output",mounted[1])
            self.assertFalse("readonly" in mounted[1])
            # Only inspect Docker control flags, not the fixed negative
            # probe script which intentionally mentions forbidden paths.
            joined=" ".join(args[:-3])
            for banned in ("--privileged","--network=host","docker.sock",
                           "ground_truth.ifc","--cap-add","--pid=host",
                           "--device=","--env=OPENAI_API_KEY"):
                self.assertNotIn(banned,joined)
            self.assertEqual(args[-3:],[FAKE_DIGEST,"-c",TRUSTED_PROBE])

    def test_docker_mount_symlink_and_unsafe_path_refused(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=root/"source";source.mkdir()
            symlink=root/"sym";symlink.symlink_to(source,target_is_directory=True)
            with self.assertRaises(DockerIsolationError):
                build_probe_argv("docker",DockerProbePolicy(FAKE_DIGEST),
                    "bim-bench-probe-0123456789abcdef",symlink,source)
            with self.assertRaises(DockerIsolationError):
                build_probe_argv("docker",DockerProbePolicy(FAKE_DIGEST),
                    "bim-bench-probe-0123456789abcdef",Path("/nonexistent/dir"),source)
            with self.assertRaises(DockerIsolationError):
                build_probe_argv("docker",DockerProbePolicy(FAKE_DIGEST),
                    "container-from-other-workflow",source,source)

    def test_real_docker_inspect_all_15_prestart_checks(self):
        policy=DockerProbePolicy(FAKE_DIGEST)
        checks=_validate_created(inspect_stub(),policy)
        self.assertEqual(len(checks),15)
        self.assertTrue(all(checks.values()))

    def test_mutated_inspect_network_privilege_secrets_mount_all_fail(self):
        policy=DockerProbePolicy(FAKE_DIGEST)
        alterations=(
            ("network",lambda x:x["HostConfig"].update(NetworkMode="bridge")),
            ("read_write_root",lambda x:x["HostConfig"].update(ReadonlyRootfs=False)),
            ("privileged",lambda x:x["HostConfig"].update(Privileged=True)),
            ("root_user",lambda x:x["Config"].update(User="0")),
            ("missing_no_new_priv",lambda x:x["HostConfig"].update(SecurityOpt=[])),
            ("all_caps_not_dropped",lambda x:x["HostConfig"].update(CapDrop=[])),
            ("secret_env",lambda x:x["Config"]["Env"].append("OPENAI_API_KEY=SENTINEL")),
            ("third_mount",lambda x:x["Mounts"].append({
                "Destination":"/grader","RW":False,"Type":"bind"
            })),
            ("wrong_entrypoint",lambda x:x["Config"].update(Entrypoint=["/bin/sh"])),
            ("too_many_pids",lambda x:x["HostConfig"].update(PidsLimit=500)),
            ("unbounded_mem",lambda x:x["HostConfig"].update(Memory=0)),
            ("host_ipc",lambda x:x["HostConfig"].update(IpcMode="host")),
        )
        for label,mutate in alterations:
            with self.subTest(label=label):
                image=inspect_stub();mutate(image)
                self.assertFalse(all(_validate_created(image,policy).values()))

    def test_runtime_kernel_constraints_and_negative_flags(self):
        policy=DockerProbePolicy(FAKE_DIGEST)
        good=_validate_runtime(runtime_stub(),policy)
        self.assertEqual(len(good),15)
        self.assertTrue(all(good.values()))
        alterations=(
            ("uid",0),
            ("source_write_denied",False),
            ("host_gt_path_hidden",False),
            ("docker_sock_hidden",False),
            ("launcher_key_hidden",False),
            ("network_denied",False),
            ("effective_caps_hex","0000000000000001"),
            ("no_new_privileges","0"),
            ("seccomp_filter","0"),
            ("cgroup_memory_bytes",0),
            ("cgroup_pid_limit",5000),
            ("cgroup_cpu_limit","max 100000"),
        )
        for key,bad in alterations:
            with self.subTest(field=key):
                data=runtime_stub();data[key]=bad
                self.assertFalse(all(_validate_runtime(data,policy).values()))

    def test_probe_contains_only_owned_static_checks_no_backend_api(self):
        self.assertEqual(KNOWN_PROBE_ID,"g2-docker-kernel-probe-v0.1")
        self.assertNotIn("ifcopenshell",TRUSTED_PROBE)
        self.assertNotIn("commandbus",TRUSTED_PROBE.lower())
        self.assertNotIn("ground_truth_ifc",TRUSTED_PROBE)
        self.assertNotIn("exec(",TRUSTED_PROBE)
        from src.runner.sandbox import execute_untrusted_candidate,SandboxNotReady
        with self.assertRaises(SandboxNotReady):
            execute_untrusted_candidate("print('UNKNOWN_MODEL_SCRIPT')")


@unittest.skipUnless(LOCAL_IMAGE,"Set BIM_BENCH_DOCKER_PROBE_IMAGE_SHA for live OS smoke test")
class LiveDockerProbeTests(unittest.TestCase):
    def test_restrictions_verified_against_real_docker_kernel(self):
        result=run_trusted_docker_probe(DockerProbePolicy(LOCAL_IMAGE))
        self.assertEqual(result["status"],"KERNEL_ISOLATION_PROBE_PASS")
        self.assertEqual(len(result["independent_created_host_config_checks"]),15)
        self.assertTrue(all(result["independent_created_host_config_checks"].values()))
        self.assertEqual(len(result["actual_container_kernel_checks"]),15)
        self.assertTrue(all(result["actual_container_kernel_checks"].values()))
        self.assertTrue(result["host_input_unchanged"])
        self.assertTrue(result["hidden_gt_unchanged"])
        self.assertTrue(result["docker_container_cleaned_after_probe"])
        self.assertFalse(result["worker_image_scientifically_approved"])
        self.assertFalse(result["production_scored_python_enabled"])
        self.assertFalse(result["paid_model_pilot_ready"])
        self.assertFalse(result["real_model_provider_called"])

    def test_live_enforce_gate_returns_two_even_after_successful_probe(self):
        result=subprocess.run(
            [sys.executable,"-m","tools.verify_docker_sandbox",
             "--image-id",LOCAL_IMAGE,"--enforce-live"],
            cwd=ROOT,capture_output=True,text=True,timeout=35
        )
        self.assertEqual(result.returncode,2,result.stderr)
        data=json.loads(result.stdout)
        self.assertEqual(data["status"],"KERNEL_ISOLATION_PROBE_PASS")
        self.assertFalse(data["paid_model_pilot_ready"])


if __name__=="__main__":
    unittest.main()
