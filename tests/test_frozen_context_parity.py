"""Positive and fail-closed checks for frozen GT-free source context coverage."""
import json
from pathlib import Path
from unittest import TestCase, mock

from src.runner import frozen_context_parity as audit


class FrozenSourceParityTests(TestCase):
    def test_pinned_population_counts_without_looking_at_gt(self):
        tasks, selected, gates, files = audit._load_fixed_inputs(audit.ROOT)
        self.assertEqual(len(selected), 36)
        self.assertEqual(len([i for i in selected if
                             gates[i]["reason_code"] == "STATIC_ENGINE_UNSUPPORTED"]), 23)
        self.assertEqual(len([i for i in selected if
                             gates[i]["source_bytes_verified_for_conditional_probe"] is True]), 11)
        self.assertIn("WAL-CRE-SPA-A-003", tasks)
        self.assertTrue(files)

    def test_task_revision_mismatch_fails_closed(self):
        with mock.patch.object(audit, "TASK_SHA", "0" * 64):
            with self.assertRaisesRegex(audit.FrozenContextAuditError, "Frozen public"):
                audit._load_fixed_inputs(audit.ROOT)

    def test_frozen_sample_mismatch_fails_closed(self):
        with mock.patch.object(audit, "SAMPLE_SHA", "0" * 64):
            with self.assertRaisesRegex(audit.FrozenContextAuditError, "Frozen public"):
                audit._load_fixed_inputs(audit.ROOT)

    def test_pinned_prior_report_tamper_fails_closed(self):
        with mock.patch.object(audit, "SOURCE_AUDIT_SHA", "0" * 64):
            with self.assertRaisesRegex(audit.FrozenContextAuditError, "eligibility"):
                audit._load_fixed_inputs(audit.ROOT)

    def test_pinned_remote_tree_tamper_fails_closed(self):
        with mock.patch.object(audit, "REMOTE_TREE_SHA", "0" * 64):
            with self.assertRaisesRegex(audit.FrozenContextAuditError, "remote IFC"):
                audit._load_fixed_inputs(audit.ROOT)

    def test_actual_conditional_cases_have_no_gt_or_model_claim(self):
        evidence = audit.audit_frozen_source_contexts()
        self.assertEqual(evidence["tasks_total"], 36)
        self.assertEqual(sum(evidence["status_counts"].values()), 36)
        self.assertEqual(evidence["static_engine_unsupported_not_tested"], 23)
        self.assertEqual(evidence["missing_conditional_source_inputs"], 2)
        self.assertEqual(
            evidence["context_parity_checked"] + evidence["context_parity_blocked"], 11)
        self.assertFalse(evidence["GT_ifc_opened"])
        self.assertFalse(evidence["live_pilot_authorized"])
        self.assertFalse(evidence["model_context_transport_verified"])
        self.assertEqual(evidence["official_benchmark_tasks_scored"], 0)
        self.assertEqual(evidence["model_calls"], 0)
        serialized = json.dumps(evidence)
        self.assertNotIn("ground_truth_ifc", serialized)
        self.assertNotIn("input_ifc", serialized)
        self.assertNotIn("evaluation", serialized)
        for item in evidence["tasks"]:
            self.assertNotIn("instruction", item)
            self.assertNotIn("ifc_path", item)
            self.assertNotIn("candidate_python", item)

    def test_native_context_mismatch_remains_blocked(self):
        # Existing public source is authentic, but a forged D/I comparison
        # must never become a PASS or an experiment authorization.
        with mock.patch.object(audit, "matched_shared_components",
                               side_effect=audit.FrozenContextAuditError("forged")):
            evidence = audit.audit_frozen_source_contexts()
        self.assertEqual(evidence["context_parity_checked"], 0)
        self.assertEqual(evidence["context_parity_blocked"], 11)
        self.assertEqual(
            evidence["status_counts"].get("BLOCKED_NATIVE_SOURCE_OR_CONTEXT"), 11)
        self.assertFalse(evidence["live_pilot_authorized"])
