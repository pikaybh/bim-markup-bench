"""Offline-only generated-Python worker admission and local Docker evidence.

All positive Docker evidence is via mocked responses; current real daemon
check does not start Docker services, create containers, or run candidate.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import unittest
from unittest.mock import patch

from src.runner.worker_admission import (
    LocalDockerObservation,WorkerAdmissionError,
    bind_own_candidate,verify_local_own_worker,offline_own_admission_audit,
    _local_readonly_docker,
)
from src.runner.ifc_worker import OWN_SOURCE
from src.runner.sandbox import SandboxNotReady,execute_untrusted_candidate
from src.runner.generated_candidate import run_offline_own_generated_candidate
from src.runner.docker_isolation import DockerIsolationError


CODE=b"print('NEVER EXECUTED BY THIS AUDIT')\n"
IMAGE="sha256:"+"b"*64
SHA=sha256(OWN_SOURCE.read_bytes()).hexdigest()


def record(*,image_id=IMAGE,arch="amd64",os_type="linux",
           user="65534:65534",label="bim-markup-bench isolated IFC4X3 worker"):
    return [{
        "Id":image_id,"Architecture":arch,"Os":os_type,
        "Config":{"User":user,
                  "Labels":{"org.opencontainers.image.title":label}},
    }]


def ok(stdout):
    return subprocess.CompletedProcess(["docker","info"],0,
                                       json.dumps(stdout),"")


def mock_engine(*,arch="x86_64",os_type="linux",image=None,image_fail=False,
                info_fail=False):
    calls=[]
    def invoke(args):
        calls.append(args)
        if args[0]=="info":
            return (subprocess.CompletedProcess(args,1,"","NOT_READY")
                    if info_fail else ok({"Architecture":arch,"OSType":os_type}))
        if args[:2]==["image","inspect"]:
            return (subprocess.CompletedProcess(args,1,"","NOT_CACHED")
                    if image_fail else ok(image if image is not None else record()))
        raise AssertionError("Attempt to execute Docker from read-only admission")
    return invoke,calls


class OwnWorkerAdmissionTests(unittest.TestCase):
    def test_untrusted_python_bytes_are_only_hashed_not_executed(self):
        with patch("src.runner.worker_admission.verify_local_own_worker",
                   side_effect=AssertionError("No Docker needed to validate own bytes")):
            bound=bind_own_candidate(
                CODE,sha256(CODE).hexdigest(),SHA,
                arm="imperative_python",seed=9)
        self.assertEqual(bound.arm,"imperative_python")
        self.assertEqual(bound.source_sha256,SHA)
        self.assertEqual(bound.script_sha256,sha256(CODE).hexdigest())
        self.assertEqual(bound.seed,9)
        self.assertFalse(bound.evidence()["candidate_executed"])
        self.assertEqual(bound.evidence()["official_tasks_scored"],0)

    def test_same_input_seed_code_has_stable_id_but_different_code_is_isolated(self):
        base=bind_own_candidate(
            CODE,sha256(CODE).hexdigest(),SHA,
            arm="imperative_python",seed=7)
        repeat=bind_own_candidate(
            CODE,sha256(CODE).hexdigest(),SHA,
            arm="imperative_python",seed=7)
        another=b"print('different synthetic code')\n"
        changed=bind_own_candidate(
            another,sha256(another).hexdigest(),SHA,
            arm="imperative_python",seed=7)
        self.assertEqual(base.run_id,repeat.run_id)
        self.assertNotEqual(base.run_id,changed.run_id)
        self.assertNotIn("print(",json.dumps(base.evidence()))

    def test_external_source_or_source_digest_tampering_denied_before_docker(self):
        for bad in ("b"*64,"not-a-hex-sha",SHA.upper(),None):
            with self.subTest(bad=bad),self.assertRaises(WorkerAdmissionError):
                bind_own_candidate(CODE,sha256(CODE).hexdigest(),bad,
                                   arm="imperative_python",seed=0)

    def test_mutated_own_ifc_and_matching_forged_source_hash_still_denied(self):
        with TemporaryDirectory(prefix="fake-own-ifc-not-allowed-") as td:
            fake=Path(td)/"input.ifc"
            fake.write_bytes(OWN_SOURCE.read_bytes()+b"ALTERED")
            fake_sha=sha256(fake.read_bytes()).hexdigest()
            with patch("src.runner.worker_admission.OWN_SOURCE",fake):
                with self.assertRaisesRegex(
                    WorkerAdmissionError,"fixture is tampered"):
                    bind_own_candidate(CODE,sha256(CODE).hexdigest(),fake_sha,
                                       arm="imperative_python",seed=0)

    def test_candidate_tampering_and_out_of_scope_arm_denied(self):
        for bad in ("0"*64,"NO_SHA",None):
            with self.subTest(bad=bad),self.assertRaises(WorkerAdmissionError):
                bind_own_candidate(CODE,bad,SHA,
                                   arm="imperative_python",seed=0)
        for arm in ("direct_xml","python","",None):
            with self.subTest(arm=arm),self.assertRaisesRegex(
                WorkerAdmissionError,"imperative arm"):
                bind_own_candidate(CODE,sha256(CODE).hexdigest(),SHA,
                                   arm=arm,seed=0)
        with self.assertRaises(WorkerAdmissionError):
            bind_own_candidate(b"\xff",sha256(b"\xff").hexdigest(),SHA,
                               arm="imperative_python",seed=0)

    def test_invalid_seed_and_oversized_program_denied_without_code_execution(self):
        for seed in (-1,True,2**31,"0",None):
            with self.subTest(seed=seed),self.assertRaises(WorkerAdmissionError):
                bind_own_candidate(CODE,sha256(CODE).hexdigest(),SHA,
                                   arm="imperative_python",seed=seed)
        large=b"A"*(65536+1)
        with self.assertRaises(WorkerAdmissionError):
            bind_own_candidate(large,sha256(large).hexdigest(),SHA,
                               arm="imperative_python",seed=0)

    def test_mutable_image_tags_and_wrong_size_ids_denied_before_any_docker_call(self):
        mock,calls=mock_engine()
        for image in ("latest","worker:amd64","sha256:"+"A"*64,
                      "sha256:"+"0"*63,"","sha256:../"):
            with self.subTest(image=image),self.assertRaises(WorkerAdmissionError):
                verify_local_own_worker(image,invoke=mock)
        self.assertEqual(calls,[])

    def test_unavailable_docker_fails_before_image_lookup(self):
        mock,calls=mock_engine(info_fail=True)
        result=verify_local_own_worker(IMAGE,invoke=mock)
        self.assertEqual(result.status,"BLOCKED_LOCAL_DOCKER_ENGINE_UNAVAILABLE")
        self.assertFalse(result.local_engine_reachable)
        self.assertIsNone(result.exact_image_id_present)
        self.assertEqual(calls,[["info","--format","{{json .}}"]])
        self.assertFalse(result.report()["candidate_container_created"])
        self.assertFalse(result.paid_model_run_authorized)

    def test_local_docker_without_pinned_image_refused(self):
        mock,calls=mock_engine(image_fail=True)
        result=verify_local_own_worker(IMAGE,invoke=mock)
        self.assertEqual(result.status,"BLOCKED_PINNED_IMAGE_NOT_CACHED")
        self.assertTrue(result.local_engine_reachable)
        self.assertFalse(result.exact_image_id_present)
        self.assertEqual(len(calls),2)
        self.assertEqual(calls[-1],["image","inspect",IMAGE])

    def test_nonlinux_engine_denied_before_image_inspection(self):
        for os_type,arch in (("windows","amd64"),("linux","mips64"),("",None)):
            mock,calls=mock_engine(os_type=os_type,arch=arch)
            with self.subTest(os=os_type,arch=arch):
                result=verify_local_own_worker(IMAGE,invoke=mock)
                self.assertEqual(
                    result.status,"BLOCKED_NONLINUX_OR_UNKNOWN_DOCKER_PLATFORM")
                self.assertEqual(len(calls),1)
                self.assertFalse(result.real_candidate_execution_authorized)

    def test_forged_image_digest_os_arch_user_and_label_blocked(self):
        cases=(
            record(image_id="sha256:"+"0"*64),
            record(arch="arm64"),
            record(os_type="windows"),
            record(user="root"),
            record(label="unreviewed worker"),
        )
        for entry in cases:
            mock,_=mock_engine(image=entry)
            with self.subTest(entry=entry):
                result=verify_local_own_worker(IMAGE,invoke=mock)
                self.assertEqual(result.status,"BLOCKED_WRONG_WORKER_IMAGE_OR_PLATFORM")
                self.assertFalse(result.image_build_provenance_verified)
                self.assertFalse(result.real_candidate_execution_authorized)

    def test_positive_mock_only_allows_subsequent_own_trusted_probe_not_live_execution(self):
        mock,calls=mock_engine()
        result=verify_local_own_worker(IMAGE,invoke=mock)
        self.assertEqual(result.status,
            "READY_FOR_TRUSTED_OWN_PROBE_ONLY_NOT_GENERATED_PYTHON")
        self.assertTrue(result.exact_image_id_present)
        self.assertTrue(result.image_is_linux_native)
        self.assertTrue(result.nonroot_oci_user)
        self.assertFalse(result.worker_os_isolation_currently_verified)
        self.assertFalse(result.image_build_provenance_verified)
        self.assertFalse(result.real_candidate_execution_authorized)
        self.assertFalse(result.paid_model_run_authorized)
        self.assertEqual([x[:2] for x in calls],
                         [["info","--format"],["image","inspect"]])

    def test_existing_own_worker_entrypoint_applies_admission_before_docker(self):
        # Integration proof: candidate hash checking is part of the
        # previously existing OWN-only code path, not a stand-alone report.
        with patch("src.runner.generated_candidate._verify_local_image",
                   side_effect=AssertionError("No Docker for forged code")):
            with self.assertRaisesRegex(DockerIsolationError,
                                        "OWN source/candidate admission rejected"):
                run_offline_own_generated_candidate(
                    IMAGE,CODE,"0"*64,wall_seconds=3,seed=4)
        with patch("src.runner.generated_candidate._verify_local_image",
                   side_effect=DockerIsolationError("mock offline Docker")):
            with self.assertRaisesRegex(DockerIsolationError,
                                        "mock offline Docker"):
                run_offline_own_generated_candidate(
                    IMAGE,CODE,sha256(CODE).hexdigest(),wall_seconds=3,seed=4)

    def test_invalid_json_oversized_daemon_and_wrong_image_count_blocked(self):
        bad_json=subprocess.CompletedProcess(["docker"],0,"{","")
        def fake(_):return bad_json
        self.assertEqual(verify_local_own_worker(IMAGE,invoke=fake).status,
                         "BLOCKED_UNVERIFIED_LOCAL_DOCKER_OR_IMAGE_RESPONSE")
        too_big=subprocess.CompletedProcess(["docker"],0,
                                             "X"*70000,"")
        self.assertEqual(verify_local_own_worker(IMAGE,invoke=lambda _:too_big).status,
                         "BLOCKED_OVERSIZED_DOCKER_DAEMON_RESPONSE")
        mock,_=mock_engine(image=[*record(),*record()])
        self.assertEqual(verify_local_own_worker(IMAGE,invoke=mock).status,
                         "BLOCKED_INVALID_IMAGE_INSPECTION")

    def test_no_remote_context_api_key_or_shell_in_real_readonly_docker_invocation(self):
        seen={}
        def intercept(argv,**kwargs):
            seen["argv"]=argv;seen["env"]=kwargs["env"]
            return subprocess.CompletedProcess(argv,1,"","offline")
        with (patch("src.runner.worker_admission._docker_cli",
                    return_value=r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"),
              patch("src.runner.worker_admission._host_docker_env",
                    return_value={"PATH":r"C:\Windows\System32"}),
              patch("src.runner.worker_admission._local_docker_endpoint",
                    return_value="npipe:////./pipe/dockerDesktopLinuxEngine"),
              patch("src.runner.worker_admission.subprocess.run",
                    side_effect=intercept)):
            _local_readonly_docker(["info","--format","{{json .}}"])
        self.assertEqual(seen["argv"][1:3],
                         ["--host","npipe:////./pipe/dockerDesktopLinuxEngine"])
        self.assertNotIn("OPENAI_API_KEY",seen["env"])
        self.assertNotIn("DOCKER_HOST",seen["env"])
        self.assertNotIn("DOCKER_CONTEXT",seen["env"])
        self.assertNotIn("shell",seen)
        self.assertFalse(any(x in seen["argv"]
                             for x in ("start","run","pull","create","exec")))

    def test_sanitization_failure_never_invokes_docker(self):
        with (patch("src.runner.worker_admission._docker_cli",
                    return_value="docker"),
              patch("src.runner.worker_admission._host_docker_env",
                    return_value={"OPENAI_API_KEY":"SHOULD_NOT_PASS"}),
              patch("src.runner.worker_admission.subprocess.run",
                    side_effect=AssertionError("Cannot run with secret"))):
            with self.assertRaisesRegex(WorkerAdmissionError,"sanitized"):
                _local_readonly_docker(["info"])

    def test_real_local_host_inspection_never_grants_generated_python_permission(self):
        current=verify_local_own_worker(
            "sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee")
        self.assertFalse(current.real_candidate_execution_authorized)
        self.assertFalse(current.paid_model_run_authorized)
        self.assertFalse(current.worker_os_isolation_currently_verified)
        self.assertEqual(current.report()["official_tasks_scored"],0)
        self.assertEqual(current.report()["paid_model_calls"],0)
        with self.assertRaises(SandboxNotReady):
            execute_untrusted_candidate(CODE)


if __name__=="__main__":
    unittest.main()
