"""BIM-Edit pinned source-only Docker mount proof: pure negative and live tests.

A live Docker test is enabled only with an explicit immutable local image SHA.
It executes the trusted, fixed digest and security probe on existing cached
public source *bytes*; no model-generated program, IFC mutation or grader.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from src.runner.docker_isolation import (
    DockerProbePolicy, DockerIsolationError,
    PILOT_CHECK_NAMES, PILOT_PROBE_ID, TRUSTED_PILOT_INPUT_PROBE,
    build_pilot_input_probe_argv, _validate_pilot_created,
    _validate_pilot_runtime, run_pinned_pilot_input_mount_probe,
)
from tests.security.test_docker_isolation import inspect_stub, runtime_stub

ROOT=Path(__file__).resolve().parents[2]
IMAGE=os.environ.get("BIM_BENCH_DOCKER_PROBE_IMAGE_SHA","")
ENTRYPOINT=os.environ.get("BIM_BENCH_DOCKER_PROBE_PYTHON_ENTRYPOINT","/usr/local/bin/python3")
FAKE_DIGEST="sha256:"+"a"*64
SOURCE_SHA="1"*64
PAYLOAD_SHA="2"*64


def piloted_stub(stage:Path,out:Path)->dict:
    item=inspect_stub()
    item["Config"]["Entrypoint"]=["/usr/local/bin/python3"]
    item["Config"]["Cmd"]=["-c",TRUSTED_PILOT_INPUT_PROBE]
    item["Config"]["Env"]+=[
        "BIM_STAGE_SOURCE_SHA256="+SOURCE_SHA,
        "BIM_STAGE_PAYLOAD_SHA256="+PAYLOAD_SHA,
    ]
    item["HostConfig"]["Mounts"]=[
        {"Type":"bind","Source":str(stage),"Target":"/input","ReadOnly":True},
        {"Type":"bind","Source":str(out),"Target":"/output","ReadOnly":False},
    ]
    return item


class PilotMountPureSecurityTests(unittest.TestCase):
    def setUp(self):
        self.t=TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        root=Path(self.t.name)
        self.stage=root/"staged-task";self.stage.mkdir()
        self.output=root/"only-output";self.output.mkdir()
        self.policy=DockerProbePolicy(
            FAKE_DIGEST,python_entrypoint="/usr/local/bin/python3"
        )

    def inspect(self,data:dict)->dict:
        return _validate_pilot_created(
            data,self.policy,self.stage,self.output,SOURCE_SHA,PAYLOAD_SHA
        )

    def test_static_trusted_code_only_and_opaque_source_hash(self):
        self.assertIn("/input/input.ifc",TRUSTED_PILOT_INPUT_PROBE)
        self.assertIn("/input/task.json",TRUSTED_PILOT_INPUT_PROBE)
        self.assertIn("BIM_STAGE_SOURCE_SHA256",TRUSTED_PILOT_INPUT_PROBE)
        self.assertIn("BIM_STAGE_PAYLOAD_SHA256",TRUSTED_PILOT_INPUT_PROBE)
        self.assertNotIn("ifcopenshell",TRUSTED_PILOT_INPUT_PROBE)
        self.assertNotIn("ground_truth_ifc",TRUSTED_PILOT_INPUT_PROBE)
        self.assertNotIn("eval(",TRUSTED_PILOT_INPUT_PROBE)
        self.assertNotIn("exec(",TRUSTED_PILOT_INPUT_PROBE)
        self.assertEqual(len(PILOT_CHECK_NAMES),7)
        self.assertEqual(PILOT_PROBE_ID,"g2-pinned-bim-edit-input-mount-v0.1")

    def test_generated_argv_contains_only_two_exact_host_mounts_and_fixed_program(self):
        cmd=build_pilot_input_probe_argv(
            "docker",self.policy,"bim-bench-probe-0123456789abcdef",
            self.stage,self.output,SOURCE_SHA,PAYLOAD_SHA
        )
        self.assertEqual(cmd[-1],TRUSTED_PILOT_INPUT_PROBE)
        self.assertEqual(cmd[-3],FAKE_DIGEST)
        self.assertEqual(cmd[-2],"-c")
        self.assertIn("--pull=never",cmd)
        self.assertIn("--network=none",cmd)
        self.assertIn("--read-only",cmd)
        self.assertIn("--cap-drop=ALL",cmd)
        self.assertIn("--security-opt=no-new-privileges:true",cmd)
        self.assertIn("--user=65534:65534",cmd)
        mounts=[x for x in cmd if x.startswith("--mount=")]
        self.assertEqual(len(mounts),2)
        self.assertIn("source="+str(self.stage),mounts[0])
        self.assertIn("target=/input,readonly",mounts[0])
        self.assertIn("source="+str(self.output),mounts[1])
        self.assertIn("target=/output",mounts[1])
        self.assertEqual(
            [x for x in cmd if x.startswith("--env=BIM_STAGE_")],
            ["--env=BIM_STAGE_SOURCE_SHA256="+SOURCE_SHA,
             "--env=BIM_STAGE_PAYLOAD_SHA256="+PAYLOAD_SHA]
        )
        self.assertFalse(any("--privileged" in x or "--network=host" in x for x in cmd))

    def test_fake_user_input_cannot_inject_unbounded_or_unpinned_env_sha(self):
        for digest in ("", "1"*63, "0"*65, "Z"*64, "1"*64+";rm -rf /", None):
            with self.subTest(digest=digest),self.assertRaises(DockerIsolationError):
                build_pilot_input_probe_argv(
                    "docker",self.policy,"bim-bench-probe-0123456789abcdef",
                    self.stage,self.output,digest,PAYLOAD_SHA
                )

    def test_correct_fake_docker_inspect_passes_all_17(self):
        checks=self.inspect(piloted_stub(self.stage,self.output))
        self.assertEqual(len(checks),17)
        self.assertTrue(all(checks.values()),checks)

    def test_forged_host_mount_sources_are_rejected_before_running_python(self):
        good=piloted_stub(self.stage,self.output)
        outside=self.stage.parent/"private-original-GT"
        outside.mkdir()
        attacks=(
            ("gt_instead_of_source",lambda x:x["HostConfig"]["Mounts"][0].update(Source=str(outside))),
            ("same_host_root_for_both",lambda x:x["HostConfig"]["Mounts"][1].update(Source=str(self.stage))),
            ("input_mounted_readwrite",lambda x:x["HostConfig"]["Mounts"][0].update(ReadOnly=False)),
            ("extra_unmounted_file_mapped",lambda x:x["HostConfig"]["Mounts"].append(
                {"Type":"bind","Source":str(outside),"Target":"/grader","ReadOnly":True}
            )),
            ("missing_output",lambda x:x["HostConfig"]["Mounts"].pop()),
            ("docker_mounts_claim_third",lambda x:x["Mounts"].append(
                {"Destination":"/grader","RW":False,"Type":"bind"}
            )),
            ("fake_pilot_sha_env",lambda x:x["Config"]["Env"].append(
                "BIM_STAGE_SOURCE_SHA256="+"f"*64
            )),
            ("secret_env",lambda x:x["Config"]["Env"].append("OPENAI_API_KEY=should_not_be_here")),
            ("model_python_instead_of_fixed_probe",lambda x:x["Config"].update(Cmd=["-c","print('model')"])),
            ("wrong_interpreter",lambda x:x["Config"].update(Entrypoint=["/bin/sh"])),
            ("host_network",lambda x:x["HostConfig"].update(NetworkMode="host")),
            ("privileged",lambda x:x["HostConfig"].update(Privileged=True)),
        )
        for name,attack in attacks:
            with self.subTest(attack=name):
                info=deepcopy(good)
                attack(info)
                self.assertFalse(all(self.inspect(info).values()),name)

    def test_all_22_real_kernel_and_extra_task_checks_have_negative_controls(self):
        sample=runtime_stub()
        sample.update({name:True for name in PILOT_CHECK_NAMES})
        checks=_validate_pilot_runtime(sample,self.policy)
        self.assertEqual(len(checks),22)
        self.assertTrue(all(checks.values()))
        for name in PILOT_CHECK_NAMES:
            with self.subTest(attack=name):
                attack=deepcopy(sample)
                attack[name]=False
                self.assertFalse(all(_validate_pilot_runtime(attack,self.policy).values()))
        attack=deepcopy(sample)
        attack["network_denied"]=False
        self.assertFalse(all(_validate_pilot_runtime(attack,self.policy).values()))

    def test_frozen_real_three_arm_evidence_is_not_launch_authorization(self):
        evidence=ROOT/"reports/g2_bim_edit_pilot_docker_input_mount_20261119.json"
        raw=evidence.read_bytes()
        self.assertEqual(
            sha256(raw).hexdigest(),
            "3f1b2313b285edf6e2fd6a57bc1f608fd6e5cf6c0624b835ea8511f9cbf39dd6",
        )
        self.assertNotIn(b"\r\n",raw)
        report=json.loads(raw)
        self.assertEqual(report["status"],"PINNED_PILOT_DOCKER_INPUT_MOUNT_PROBE_PASS")
        self.assertEqual(report["probe_id"],PILOT_PROBE_ID)
        self.assertEqual(report["original_pilot_denominator"],36)
        self.assertEqual(report["locally_ready_task_rows"],30)
        self.assertEqual(report["missing_or_blocked_task_rows"],6)
        self.assertEqual(report["arm_count"],3)
        self.assertTrue(report["input_also_other_task_reference_path"])
        self.assertTrue(report["same_original_IFC_sha256_across_arms"])
        self.assertTrue(report["same_sanitized_prompt_sha256_across_arms"])
        self.assertEqual(
            [item["arm"] for item in report["arm_probes"]],
            ["D_FULL","D_MANAGED","I_NATIVE"]
        )
        self.assertEqual(len({item["staged_source_sha256"] for item in report["arm_probes"]}),1)
        self.assertEqual(len({item["staged_payload_sha256"] for item in report["arm_probes"]}),1)
        for item in report["arm_probes"]:
            self.assertEqual(len(item["container_prestart_checks"]),17)
            self.assertTrue(all(item["container_prestart_checks"].values()))
            self.assertEqual(len(item["actual_kernel_and_task_file_checks"]),22)
            self.assertTrue(all(item["actual_kernel_and_task_file_checks"].values()))
        for name in (
            "paid_model_pilot_ready","production_scored_python_enabled",
            "worker_image_scientifically_approved","rights_for_model_provider_verified",
            "real_model_provider_called","model_generated_python_executed",
            "original_GT_role_file_opened","original_IFC_native_geometry_parsed",
        ):
            self.assertFalse(report[name],name)
        self.assertEqual(report["official_tasks_scored"],0)
        self.assertTrue(report["temporary_task_workspaces_and_containers_cleaned"])

    def test_cli_pilot_mode_remains_denied_for_billed_model_even_on_success(self):
        from tools import verify_docker_sandbox
        fake={
            "status":"PINNED_PILOT_DOCKER_INPUT_MOUNT_PROBE_PASS",
            "paid_model_pilot_ready":False,"real_model_provider_called":False,
        }
        target=self.stage.parent/"proof.json"
        argv=[
            "verify_docker_sandbox","--image-id",FAKE_DIGEST,
            "--python-entrypoint","/usr/local/bin/python3",
            "--pilot-stage-input-mount","--enforce-live",
            "--output-json",str(target),
        ]
        with patch.object(sys,"argv",argv),patch.object(
            verify_docker_sandbox,"run_pinned_pilot_input_mount_probe",
            return_value=fake
        ) as probe:
            self.assertEqual(verify_docker_sandbox.main(),2)
            self.assertEqual(probe.call_count,1)
            self.assertEqual(json.loads(target.read_text("utf8")),fake)
            self.assertNotIn(b"\r\n",target.read_bytes())
            with self.assertRaises(SystemExit):
                verify_docker_sandbox.main()


@unittest.skipUnless(IMAGE,"Set BIM_BENCH_DOCKER_PROBE_IMAGE_SHA to cached immutable Linux worker image")
class PilotInputMountLiveDockerTests(unittest.TestCase):
    def test_one_cross_task_alias_original_ifc_three_arm_kernel_isolation(self):
        policy=DockerProbePolicy(IMAGE,python_entrypoint=ENTRYPOINT)
        report=run_pinned_pilot_input_mount_probe(policy,ROOT)
        self.assertEqual(report["status"],"PINNED_PILOT_DOCKER_INPUT_MOUNT_PROBE_PASS")
        self.assertEqual(report["original_pilot_denominator"],36)
        self.assertEqual(report["locally_ready_task_rows"],30)
        self.assertEqual(report["missing_or_blocked_task_rows"],6)
        self.assertTrue(report["input_also_other_task_reference_path"])
        self.assertEqual(report["arm_count"],3)
        self.assertEqual(
            [row["arm"] for row in report["arm_probes"]],
            ["D_FULL","D_MANAGED","I_NATIVE"]
        )
        self.assertEqual(
            len({row["staged_source_sha256"] for row in report["arm_probes"]}),1
        )
        self.assertEqual(
            len({row["staged_payload_sha256"] for row in report["arm_probes"]}),1
        )
        for row in report["arm_probes"]:
            with self.subTest(arm=row["arm"]):
                self.assertEqual(len(row["container_prestart_checks"]),17)
                self.assertTrue(all(row["container_prestart_checks"].values()))
                self.assertEqual(len(row["actual_kernel_and_task_file_checks"]),22)
                self.assertTrue(all(row["actual_kernel_and_task_file_checks"].values()))
                self.assertTrue(row["original_staged_files_unchanged"])
        self.assertTrue(report["OWN_hidden_reference_and_other_task_canaries_unchanged"])
        self.assertTrue(report["temporary_task_workspaces_and_containers_cleaned"])
        for name in (
            "paid_model_pilot_ready","production_scored_python_enabled",
            "worker_image_scientifically_approved","rights_for_model_provider_verified",
            "real_model_provider_called","model_generated_python_executed",
            "original_GT_role_file_opened","original_IFC_native_geometry_parsed",
        ):
            self.assertFalse(report[name],name)
        self.assertEqual(report["official_tasks_scored"],0)


if __name__=="__main__":
    unittest.main()
