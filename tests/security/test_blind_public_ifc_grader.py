"""G2 #21 blind native IFC scorer isolation, strict negative and parity tests.

Only three pinned public tasks; no external model or official scored trial.
"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from src.runner.blind_public_ifc_grader import (
    ALLOWED_MODES, ALLOWED_TASKS, _REPORT_FIELDS, _checked_public_result,
    _trusted_pinned_task, run_pinned_blind_scorer, verify_blind_container,
)
from src.runner.docker_isolation import DockerIsolationError
from src.runner.ifc_worker import _docker_cli
from src.evaluation.bim_edit_scorer import EVALUATOR_VERSION, PROVENANCE

IMAGE = os.environ.get("BIM_BENCH_BLIND_SCORER_SHA256", "")


def fake_inspect(image: str) -> dict:
    return {
        "Image": image,
        "HostConfig": {
            "NetworkMode": "none", "ReadonlyRootfs": True,
            "Privileged": False, "CapDrop": ["ALL"],
            "SecurityOpt": ["no-new-privileges:true"], "IpcMode": "none",
            "PidsLimit": 1, "Memory": 536870912, "MemorySwap": 536870912,
            "NanoCpus": 750000000,
            "Tmpfs": {"/tmp": "rw,nosuid,nodev,noexec,size=16m"},
        },
        "Config": {
            "User": "65534:65534",
            "Entrypoint": ["/usr/local/bin/python3"],
            "Cmd": ["/opt/blind/worker.py"],
            "Env": ["HOME=/tmp", "OPENBLAS_NUM_THREADS=1"],
        },
        "Mounts": [
            {"Destination": dest, "RW": False, "Type": "bind"}
            for dest in ("/source", "/ground_truth", "/prediction", "/metadata")
        ],
    }


class BlindPublicOfflineTests(unittest.TestCase):
    def test_frozen_task_id_and_mode_restrictions(self):
        self.assertEqual(ALLOWED_TASKS, {
            "WAL-UPD-TOP-A-001", "WAL-DEL-TOP-A-001", "DOR-CRE-TOP-A-002",
        })
        self.assertEqual(ALLOWED_MODES, {
            "reference_self_check", "unchanged_source", "invalid_output",
        })
        with self.assertRaises(DockerIsolationError):
            run_pinned_blind_scorer(
                "sha256:" + "0"*64, "WAL-UPD-TOP-A-001", "model_generated"
            )
        with self.assertRaises(DockerIsolationError):
            _trusted_pinned_task("UNAPPROVED-ID")

    def test_docker_context_does_not_send_IFC_GT_or_env_secret(self):
        repo=Path(__file__).resolve().parents[2]
        rules=(repo/".dockerignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("**",rules)
        allowed=set(line[1:] for line in rules if line.startswith("!"))
        self.assertTrue({
            "src/evaluation/*.py",
            "docker/ifc_worker/requirements.amd64.lock",
            "docker/ifc_blind_grader/worker.py",
        }.issubset(allowed))
        for private in ("data/","data/ifc/","tests/fixtures/",
                        ".git/",".env",".venv/","secrets/"):
            self.assertNotIn(private,allowed)
        scorer=(repo/"docker/ifc_blind_grader/Dockerfile.amd64").read_text()
        self.assertIn("python:3.12-slim-bookworm@sha256:",scorer)
        self.assertIn("--require-hashes --only-binary=:all:",scorer)
        self.assertNotIn("COPY data/",scorer)
        self.assertNotIn("COPY tests/",scorer)
        self.assertNotIn("COPY . ",scorer)

    def test_prestop_inspection_rejects_GT_and_agent_leaks(self):
        image = "sha256:" + "a"*64
        good = fake_inspect(image)

        def check(meta, should_fail):
            completed = subprocess.CompletedProcess(
                ["docker", "inspect"], 0, json.dumps([meta]), ""
            )
            with patch("src.runner.blind_public_ifc_grader._run",
                       return_value=completed):
                if should_fail:
                    with self.assertRaises(DockerIsolationError):
                        verify_blind_container("a"*64, image)
                else:
                    verify_blind_container("a"*64, image)

        check(good, False)
        changes = {
            "missing_gt": lambda x: x["Mounts"].pop(1),
            "writable_gt": lambda x: x["Mounts"][1].update(RW=True),
            "agent_script_mount": lambda x: x["Mounts"].append({
                "Destination": "/task", "Type": "bind", "RW": False,
            }),
            "host_output_mount": lambda x: x["Mounts"].append({
                "Destination": "/output", "Type": "bind", "RW": True,
            }),
            "secret_env": lambda x: x["Config"]["Env"].append(
                "OPENAI_API_KEY=FORBIDDEN"
            ),
            "arm_label": lambda x: x["Config"]["Env"].append("ARM=direct_xml"),
            "changed_grader_command": lambda x: x["Config"].update(
                Cmd=["-c", "print('forged')"]
            ),
            "network_enabled": lambda x: x["HostConfig"].update(
                NetworkMode="bridge"
            ),
            "privileged": lambda x: x["HostConfig"].update(Privileged=True),
            "unbounded_tmp": lambda x: x["HostConfig"].update(Tmpfs={}),
        }
        for reason, modify in changes.items():
            altered = copy.deepcopy(good)
            modify(altered)
            with self.subTest(reason=reason):
                check(altered, True)

    def test_sanitized_record_rejects_hidden_details_and_fake_success(self):
        good = {
            "task_id": "WAL-UPD-TOP-A-001",
            "status": "INDEPENDENT_IFC_SCORED",
            "scorer_version": EVALUATOR_VERSION,
            "metric_origin": PROVENANCE,
            "official_bim_edit_evaluator_equivalent": False,
            "official_tasks_scored": 0,
            "geometry": 1.0, "semantics": 1.0, "topology": 1.0,
            "final_score": 1.0, "strict_pass": True,
            "failure_codes": [],
            "reference_or_target_metadata_in_agent_context": False,
            "paid_model_calls": 0,
        }
        self.assertEqual(set(good), _REPORT_FIELDS)
        _checked_public_result(
            json.dumps(good), good["task_id"], "reference_self_check"
        )
        variants = [
            dict(good, target_guid="SECRET"),
            dict(good, ground_truth_path="SECRET"),
            dict(good, official_tasks_scored=1),
            dict(good, geometry=1.1),
            dict(good, strict_pass=False),
            dict(good, metric_origin="official-BIM-Edit"),
            dict(good, paid_model_calls=1),
        ]
        for variant in variants:
            with self.subTest(data=variant), self.assertRaises(
                DockerIsolationError
            ):
                _checked_public_result(
                    json.dumps(variant), good["task_id"], "reference_self_check"
                )
        with self.assertRaises(DockerIsolationError):
            _checked_public_result(
                json.dumps(good) + "\n" + json.dumps(good),
                good["task_id"], "reference_self_check",
            )

    def test_pinned_metadata_is_present_if_cached(self):
        try:
            row, src, gt = _trusted_pinned_task("WAL-UPD-TOP-A-001")
        except (FileNotFoundError, ValueError) as exc:
            self.skipTest("Optional local pinned IFC cache absent: " + type(exc).__name__)
        self.assertEqual(row["target"]["entity_type"], "IfcWall")
        self.assertNotEqual(src.read_bytes(), gt.read_bytes())

    def test_primary_model_and_paid_scoring_are_still_refused(self):
        from src.runner.sandbox import execute_untrusted_candidate, SandboxNotReady
        with self.assertRaises(SandboxNotReady):
            execute_untrusted_candidate(b"import ifcopenshell")
        from src.runner.cli import main
        self.assertEqual(main(["score"]), 2)


@unittest.skipUnless(IMAGE, "Explicit immutable Linux AMD64 blind scorer ID required")
class BlindPublicRealDockerTests(unittest.TestCase):
    def test_three_public_reference_self_checks(self):
        for task in sorted(ALLOWED_TASKS):
            with self.subTest(task_id=task):
                proof = run_pinned_blind_scorer(IMAGE, task, "reference_self_check")
                result = proof["independent_grader_result"]
                self.assertTrue(result["strict_pass"])
                self.assertEqual(
                    [result[x] for x in ("geometry", "semantics", "topology")],
                    [1.0, 1.0, 1.0],
                )
                self.assertFalse(result["official_bim_edit_evaluator_equivalent"])
                self.assertEqual(result["official_tasks_scored"], 0)
                self.assertFalse(proof["agent_program_executed"])

    def test_unmodified_and_invalid_candidates_fail(self):
        task = "WAL-UPD-TOP-A-001"
        unmodified = run_pinned_blind_scorer(
            IMAGE, task, "unchanged_source"
        )["independent_grader_result"]
        invalid = run_pinned_blind_scorer(
            IMAGE, task, "invalid_output"
        )["independent_grader_result"]
        self.assertFalse(unmodified["strict_pass"])
        self.assertEqual(unmodified["status"], "INDEPENDENT_IFC_SCORED")
        self.assertFalse(invalid["strict_pass"])
        self.assertEqual(invalid["status"], "INVALID_OUTPUT_IFC")
        self.assertEqual(
            [invalid[k] for k in ("geometry", "semantics", "topology")],
            [0.0, 0.0, 0.0],
        )

    def test_repeat_produces_identical_run_id_and_score(self):
        task = "WAL-UPD-TOP-A-001"
        a = run_pinned_blind_scorer(IMAGE, task, "reference_self_check")
        b = run_pinned_blind_scorer(IMAGE, task, "reference_self_check")
        self.assertEqual(a["run_id"], b["run_id"])
        self.assertEqual(
            a["independent_grader_result"], b["independent_grader_result"]
        )

    def test_no_leftover_blind_grader_containers(self):
        process = subprocess.run(
            [_docker_cli(), "ps", "-a", "--filter",
             "name=bim-bench-blind-grader", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
