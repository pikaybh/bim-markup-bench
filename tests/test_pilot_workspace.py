"""G0: truly frozen pilot task-arm file staging without any model / evaluator.

Tests are offline; synthetic byte fixtures cover bad paths, tampering, repeated
runs, and the original 36-task preflight keeps the six blocked cases.
"""
from __future__ import annotations

from hashlib import sha1, sha256
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.data.bim_edit import repo_asset_path
from src.data.pilot_workspace import (
    OfflineStage, PilotStageBlocked, _check_scratch_root, _frozen_inputs,
    pilot_staging_preflight, stage_verified_pilot_input,
)

ROOT = Path(__file__).resolve().parents[1]


class TestRealPinnedPilotWithoutInference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preflight = pilot_staging_preflight(ROOT)

    def test_all_36_preserved_with_6_blocked(self):
        p = self.preflight
        self.assertEqual(p["original_tasks"], 36)
        self.assertEqual(len(p["task_status"]), 36)
        self.assertEqual(p["input_available_tasks"], 30)
        self.assertEqual(p["blocked_input_tasks"], 6)
        self.assertEqual(sum(v.startswith("STAGING_INPUT") for v in p["task_status"].values()), 30)
        self.assertFalse(p["llm_launch_allowed"])
        self.assertFalse(p["os_level_agent_isolation_verified"])
        self.assertFalse(p["source_rights_verified_for_external_provider"])

    def test_no_silent_reselection_of_six_missing_input_tasks(self):
        blocked = [tid for tid, s in self.preflight["task_status"].items() if s.startswith("BLOCKED")]
        self.assertEqual(len(blocked), 6)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(PilotStageBlocked):
                stage_verified_pilot_input(ROOT, Path(temp), blocked[0], "I_NATIVE")
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_stage_three_arms_on_same_original_file_with_only_two_files(self):
        task_id = next(
            tid for tid, status in self.preflight["task_status"].items()
            if status.startswith("STAGING_INPUT")
        )
        with tempfile.TemporaryDirectory() as temp:
            staged = [
                stage_verified_pilot_input(ROOT, Path(temp), task_id, arm)
                for arm in ("D_FULL", "D_MANAGED", "I_NATIVE")
            ]
            hashes = set()
            for item in staged:
                self.assertIsInstance(item, OfflineStage)
                self.assertFalse(item.model_launch_allowed)
                self.assertFalse(item.os_sandbox_established)
                self.assertEqual(item.task_id, task_id)
                self.assertEqual(
                    {f.name for f in item.workspace.iterdir()}, {"input.ifc", "task.json"}
                )
                self.assertEqual(item.agent_payload["input_file"], "input.ifc")
                self.assertEqual(item.agent_payload["task_id"], task_id)
                self.assertEqual(set(item.agent_payload), {"task_id", "instruction", "input_file"})
                self.assertEqual(
                    json.loads((item.workspace / "task.json").read_text(encoding="utf8")),
                    item.agent_payload,
                )
                self.assertEqual(
                    sha256((item.workspace / "input.ifc").read_bytes()).hexdigest(),
                    item.source_byte_sha256,
                )
                for forbidden in ("ground_truth_ifc", "target", "evaluation", "source_dataset_path"):
                    self.assertNotIn(forbidden, (item.workspace / "task.json").read_text("utf8"))
                hashes.add(item.source_byte_sha256)
            self.assertEqual(len(hashes), 1)
            self.assertEqual(staged[0].agent_payload, staged[1].agent_payload)
            self.assertEqual(staged[1].agent_payload, staged[2].agent_payload)
            self.assertEqual(len(list(Path(temp).iterdir())), 3)

    def test_actual_input_that_other_task_calls_gt_still_exposes_only_its_input(self):
        selected, audited, _, _ = _frozen_inputs(ROOT)
        candidates = [
            tid for tid, task in selected.items()
            if (
                audited[repo_asset_path(task["input_ifc"])]["status"]
                == "PUBLISHER_OBJECT_AND_LOCAL_SHA256_VERIFIED"
                and any(
                    row.get("is_cross_task_reference_alias_in_original_324")
                    and row["public_input_path"] == repo_asset_path(task["input_ifc"])
                    for row in json.loads(
                        (ROOT / "reports/bim_edit_pilot_existing_cached_input_SHA256_20261119.json").read_text("utf8")
                    )["rows"]
                )
            )
        ]
        self.assertGreaterEqual(len(candidates), 1)
        with tempfile.TemporaryDirectory() as temp:
            staged = stage_verified_pilot_input(ROOT, Path(temp), candidates[0], "I_NATIVE")
            self.assertEqual({f.name for f in staged.workspace.iterdir()}, {"input.ifc", "task.json"})
            raw_task = selected[candidates[0]]
            self.assertNotIn(raw_task["ground_truth_ifc"], json.dumps(staged.agent_payload))
            self.assertNotIn("ground_truth_ifc", json.dumps(staged.agent_payload))
            self.assertFalse(staged.os_sandbox_established)
            self.assertFalse(staged.model_launch_allowed)

    def test_cli_checks_and_stages_only_one_disposable_example(self):
        for flag, expected in (
            ("--check", "BIM_EDIT_PILOT_STAGING_PREFLIGHT=PASS"),
            ("--smoke-stage", "BIM_EDIT_OFFLINE_STAGE=PASS"),
        ):
            with self.subTest(flag=flag):
                proc = subprocess.run(
                    [sys.executable, "-m", "src.data.pilot_workspace", flag],
                    cwd=ROOT, capture_output=True, text=True, timeout=25,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn(expected, proc.stdout)
                self.assertIn("model_launch_allowed=false" if flag == "--check"
                              else "model_calls=0 os_sandbox_proven=false", proc.stdout)

    def test_existing_workspace_is_not_overwritten(self):
        task_id = next(tid for tid, status in self.preflight["task_status"].items()
                       if status.startswith("STAGING_INPUT"))
        with tempfile.TemporaryDirectory() as temp:
            a = stage_verified_pilot_input(ROOT, Path(temp), task_id, "D_FULL")
            original = (a.workspace / "task.json").read_bytes()
            with self.assertRaises(PilotStageBlocked):
                stage_verified_pilot_input(ROOT, Path(temp), task_id, "D_FULL")
            self.assertEqual((a.workspace / "task.json").read_bytes(), original)

    def test_unknown_or_other_task_is_not_admitted(self):
        with tempfile.TemporaryDirectory() as temp:
            for tid in ("EXTERNAL-TASK-NEVER-SELECTED", "../out", ""):
                with self.subTest(task=tid), self.assertRaises(PilotStageBlocked):
                    stage_verified_pilot_input(ROOT, Path(temp), tid, "I_NATIVE")
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_forged_arm_is_blocked_before_staging(self):
        tid = next(iter(self.preflight["task_status"]))
        with tempfile.TemporaryDirectory() as temp:
            for arm in ("python", "I_NATIVE;rm -rf", "D", "D_FULL/GT", ""):
                with self.subTest(arm=arm), self.assertRaises(PilotStageBlocked):
                    stage_verified_pilot_input(ROOT, Path(temp), tid, arm)
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_scratch_must_be_outside_repo_and_not_ancestor(self):
        with self.assertRaises(PilotStageBlocked):
            _check_scratch_root(ROOT, ROOT / "data")
        with self.assertRaises(PilotStageBlocked):
            _check_scratch_root(ROOT, ROOT.parent)
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(_check_scratch_root(ROOT, Path(temp)), Path(temp).resolve())


class TestSyntheticUnsafeWorkspaceNegativeCases(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.tmp = Path(self.t.name)
        self.repo = self.tmp / "synthetic_repo"
        source = self.repo / "data/ifc/simple/synthetic.ifc"
        source.parent.mkdir(parents=True)
        self.scratch = self.tmp / "scratch"
        self.scratch.mkdir()
        self.content = b"synthetic non-IFC opaque bytes for safe staging test"
        source.write_bytes(self.content)
        self.source = source
        self.task_id = "WAL-CRE-DIR-A-009"
        self.selected = {
            self.task_id: {
                "task_id": self.task_id,
                "operation": "create",
                "category": "direct",
                "input_ifc": "data/artificial/synthetic.ifc",
                "ground_truth_ifc": "data/artificial/private-ground-truth.ifc",
                "target": {"guids": [], "entity_type": "IfcWall"},
                "evaluation": {"private_answer": "never disclose"},
                "prompt": "Create a wall in the test fixture.",
            }
        }
        self.sha = sha256(self.content).hexdigest()
        oid = sha1(
            b"blob " + str(len(self.content)).encode("ascii") + b"\0" + self.content
        ).hexdigest()
        self.audited = {
            "simple/synthetic.ifc": {
                "status": "PUBLISHER_OBJECT_AND_LOCAL_SHA256_VERIFIED",
                "public_task_ids": [self.task_id],
                "expected_source_bytes": len(self.content),
                "byte_sha256_verified": self.sha,
            }
        }
        self.remote = {
            "simple/synthetic.ifc": {
                "type": "file",
                "path": "simple/synthetic.ifc",
                "size": len(self.content),
                "oid": oid,
            }
        }
        self.pilot = {"status": "CANDIDATE_NOT_PREREGISTERED"}

    def stage(self, *, arm="I_NATIVE"):
        with patch("src.data.pilot_workspace._frozen_inputs") as frozen:
            frozen.return_value = (self.selected, self.audited, self.remote, self.pilot)
            return stage_verified_pilot_input(self.repo, self.scratch, self.task_id, arm)

    def test_synthetic_good_file_surface_has_no_gt_or_compiler(self):
        stage = self.stage()
        self.assertEqual(stage.source_byte_sha256, self.sha)
        self.assertEqual(stage.bytes_copied, len(self.content))
        self.assertEqual(
            set(f.name for f in stage.workspace.iterdir()), {"input.ifc", "task.json"}
        )
        self.assertNotIn("ground_truth_ifc", json.dumps(stage.agent_payload))
        self.assertNotIn("private_answer", json.dumps(stage.agent_payload))
        self.assertEqual((stage.workspace / "input.ifc").read_bytes(), self.content)

    def test_changed_source_after_freeze_is_rejected_without_workspace(self):
        self.source.write_bytes(self.content.replace(b"test", b"demo"))
        with self.assertRaises(PilotStageBlocked):
            self.stage()
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_malicious_publisher_oid_is_rejected(self):
        self.remote["simple/synthetic.ifc"]["oid"] = "a" * 40
        with self.assertRaises(PilotStageBlocked):
            self.stage()

    def test_stale_audited_digest_causes_stage_cleanup(self):
        self.audited["simple/synthetic.ifc"]["byte_sha256_verified"] = "0" * 64
        with self.assertRaises(PilotStageBlocked):
            self.stage()
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_grader_fields_were_never_present_in_agent_payload(self):
        stage = self.stage()
        text = (stage.workspace / "task.json").read_text("utf8")
        for name in ("ground_truth_ifc", "target", "evaluation", "private_answer", "synthetic_repo"):
            self.assertNotIn(name, text)

    def test_suspicious_agent_instruction_is_blocked(self):
        self.selected[self.task_id]["prompt"] = "/grader/secret result is ..."
        with self.assertRaises(PilotStageBlocked):
            self.stage()
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_publisher_size_mismatch_is_blocked(self):
        self.remote["simple/synthetic.ifc"]["size"] = len(self.content) + 1
        with self.assertRaises(PilotStageBlocked):
            self.stage()
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_preexisting_workspace_or_dir_entry_blocks(self):
        path = self.scratch / (self.task_id + "--I_NATIVE")
        path.mkdir()
        sentinel = path / "secret"
        sentinel.write_text("do not touch")
        with self.assertRaises(PilotStageBlocked):
            self.stage()
        self.assertEqual(sentinel.read_text(), "do not touch")

    def test_wrong_staged_input_path_is_never_followed(self):
        self.selected[self.task_id]["input_ifc"] = "data/artificial/../../private.ifc"
        with self.assertRaisesRegex(Exception, "Unsupported|suspicious|source"):
            self.stage()
        self.assertEqual(list(self.scratch.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
