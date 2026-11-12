"""Offline positive/negative evidence for BIBIMBAP XML-only public launch gate."""
from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools.bibimbap_public_packet import (
    PILOT_PUBLIC_ID, PublicPacketBlocked, make_public_packet,
    public_task_input, read_public_pilot,
)
from tools.audit_bibimbap_launch_gate import (
    LaunchGateBlocked, audit_launch,
)
import tools.audit_bibimbap_launch_gate as gate

ROOT = Path(__file__).resolve().parents[1]


class PublicPacketBoundaryTests(unittest.TestCase):
    def test_only_public_payload_keys_are_allowed(self):
        q = "Add a wall with a length of 15m beginning in (0, -10)."
        self.assertEqual(set(public_task_input(task_id=PILOT_PUBLIC_ID, instruction=q)),
                         {"task_id", "instruction", "input_file"})
        for forbidden in ("target", "evaluation", "ground_truth_ifc",
                          "expected_output", "source_dataset_path", "grader",
                          "private_target_guid"):
            with self.subTest(field=forbidden):
                with self.assertRaises(PublicPacketBlocked):
                    public_task_input(task_id=PILOT_PUBLIC_ID, instruction=q,
                                      **{forbidden: "SENTINEL_PRIVATE_ANSWER"})
        with self.assertRaises(PublicPacketBlocked):
            public_task_input(task_id=PILOT_PUBLIC_ID, instruction=q,
                              input_file="../private/evaluator.py")
        with self.assertRaises(PublicPacketBlocked):
            public_task_input(task_id=PILOT_PUBLIC_ID, instruction=q,
                              input_file="/grader/answer.ifc")

    def test_missing_dataset_fails_before_any_inference(self):
        with TemporaryDirectory() as td:
            with self.assertRaises(PublicPacketBlocked):
                read_public_pilot(Path(td))

    def test_recorded_public_packet_is_hash_only(self):
        record = json.loads(
            (ROOT / "reports/bibimbap_test05_public_packet_preflight_20261112.json")
            .read_text(encoding="utf8")
        )
        self.assertEqual(record["status"], "PUBLIC_PACKET_PREPARED_OFFLINE_ONLY")
        self.assertEqual(record["packet_keys"], ["input", "instructions"])
        self.assertEqual(record["public_trial_id"], PILOT_PUBLIC_ID)
        self.assertEqual(record["llm_calls"], 0)
        self.assertFalse(record["model_visible_original_gt"])
        self.assertFalse(record["model_visible_author_scorer"])
        self.assertFalse(record["model_visible_api_tools"])
        self.assertIsNone(record["model_tokens"])
        self.assertNotIn("input", record)
        self.assertNotIn("instructions", record)

    def test_real_public_packet_contains_no_private_grader_text(self):
        data = os.environ.get("BIBIMBAP_DATASET")
        if not data:
            self.skipTest("Original pinned data path not provided")
        packet, summary = make_public_packet(Path(data))
        self.assertEqual(set(packet), {"input", "instructions"})
        self.assertEqual(summary["llm_calls"], 0)
        self.assertIn("Add a wall with a length of 15m", packet["input"])
        self.assertIn("<Building", packet["input"])
        self.assertIn("Toy Declarative BIM Markup", packet["input"])
        self.assertNotIn("data.tests.", json.dumps(packet))
        self.assertNotIn("execute_test", json.dumps(packet))
        self.assertNotIn("test_05.py", json.dumps(packet))
        self.assertNotIn("SENTINEL_PRIVATE_ANSWER", json.dumps(packet))
        self.assertEqual(summary["model_packet_sha256"],
            __import__("hashlib").sha256(
                json.dumps(packet, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest())


class LaunchEligibilityTests(unittest.TestCase):
    def test_saved_candidate_retains_every_task_and_does_not_count_controls_as_llm(self):
        record = json.loads(
            (ROOT / "reports/bibimbap_xml_only_launch_gate_20261112.json")
            .read_text(encoding="utf8")
        )
        self.assertEqual(record["status"], "NOT_READY")
        self.assertFalse(record["launch_authorized"])
        self.assertEqual(record["protocol_freeze"], "CANDIDATE_NOT_PREREGISTERED")
        self.assertEqual(record["original_editing_population"], 45)
        self.assertEqual(record["excluded_original_retrieval_population"], 55)
        self.assertEqual(record["projection_only_eligible_count"], 36)
        self.assertEqual(record["developer_written_scored_witness_count"], 2)
        self.assertEqual(record["actual_llm_scored_task_count"], 0)
        self.assertEqual(record["prior_noop_positive_partial_credit_count"], 15)
        self.assertEqual(len(record["all_original_editing_tasks_intention_to_test"]), 45)
        self.assertEqual(len({r["candidate_id"] for r in record["all_original_editing_tasks_intention_to_test"]}), 45)
        self.assertTrue(all(r["include_in_intention_to_test_denominator"] for r in record["all_original_editing_tasks_intention_to_test"]))
        self.assertTrue(all(r["independent_strict_task_success"] == "UNVERIFIED_NOT_SCORED" for r in record["all_original_editing_tasks_intention_to_test"]))
        self.assertTrue(all(r["real_llm_trial"] == "NOT_RUN" for r in record["all_original_editing_tasks_intention_to_test"]))
        self.assertFalse(record["allow_future_silent_filtering"])
        self.assertGreaterEqual(len(record["live_run_blockers"]), 6)

    def test_missing_or_tampered_noop_is_rejected(self):
        author = os.environ.get("BIBIMBAP_AUTHOR_REPO")
        data = os.environ.get("BIBIMBAP_DATASET")
        if not author or not data:
            self.skipTest("Pinned author source/data required")
        with TemporaryDirectory() as td:
            corrupted = Path(td) / "bad-evidence.json"
            record = json.loads(gate.NOOP_REPORT.read_text(encoding="utf8"))
            record["negative_control"]["observations"].pop()
            corrupted.write_text(json.dumps(record), encoding="utf8")
            with patch.object(gate, "NOOP_REPORT", corrupted):
                with self.assertRaises(LaunchGateBlocked):
                    audit_launch(Path(author), Path(data))

    def test_current_external_assets_still_fail_live_gate(self):
        author = os.environ.get("BIBIMBAP_AUTHOR_REPO")
        data = os.environ.get("BIBIMBAP_DATASET")
        if not author or not data:
            self.skipTest("Pinned author source/data required")
        report = audit_launch(Path(author), Path(data))
        self.assertEqual(report["status"], "NOT_READY")
        self.assertFalse(report["launch_authorized"])
        self.assertEqual(sum(t["original_author_noop_score"] > 0
                             for t in report["all_original_editing_tasks_intention_to_test"]), 15)


if __name__ == "__main__":
    unittest.main()
