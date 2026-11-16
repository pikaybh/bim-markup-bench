"""Offline v0.30 evidence integrity, preservation, leakage and negative controls."""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools import audit_bibimbap_v030_reconcile as a


class V030Original45ReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = a.ROOT
        cls.expected_report = a.reconciled_report(cls.root)
        cls.report_path = cls.root / "reports" / (
            "bibimbap_v030_original45_evidence_reconciliation_20261116.json"
        )

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bmb-v030-evidence-")
        self.addCleanup(self.temp.cleanup)
        self.sandbox = Path(self.temp.name)
        (self.sandbox / "reports").mkdir()
        for name, _ in (a.BASE, a.ROLES, *((t[0], t[1]) for t in a.NEW_CASES)):
            shutil.copy2(self.root / "reports" / name, self.sandbox / "reports" / name)

    def test_01_exact_frozen_original_45_rows(self):
        r = self.expected_report
        self.assertEqual(r["original45_ITT_denominator"], 45)
        self.assertEqual(len(r["rows"]), 45)
        self.assertEqual(len({x["task_id"] for x in r["rows"]}), 45)
        self.assertEqual(Counter(x["original_crud"] for x in r["rows"]),
                         {"create": 15, "update": 15, "delete": 15})
        self.assertEqual(Counter(x["original_category"] for x in r["rows"]),
                         {"basic": 15, "geometry": 15, "topological": 15})

    def test_02_counted_only_actual_historical_developer_evidence(self):
        r = self.expected_report
        self.assertEqual(r["original45_developer_native_D0_I0_full_ifc_byte_equal"], 11)
        self.assertEqual(r["original45_original_author_callable_developer_pairs"], 9)
        self.assertEqual(r["original45_historical_author_reference_source_mismatch"], 2)
        self.assertEqual(r["original45_not_yet_developer_native_D0_I0_byte_equal_proven"], 34)
        self.assertEqual(Counter(x["developer_author_scorer_status"] for x in r["rows"]),
                         {"AUTHOR_SCORED_DEVELOPER_CONTROL": 9,
                          "AUTHOR_REFERENCE_SOURCE_MISMATCH": 2,
                          "NOT_EVALUATED_UNDETERMINED": 34})

    def test_03_v030_does_not_infer_model_performance_or_full_access_parity(self):
        r = self.expected_report
        self.assertEqual(r["original45_full_IFC_information_parity_proven"], 0)
        self.assertEqual(r["original45_full_native_write_capability_parity_proven"], 0)
        self.assertEqual(r["original45_latest_protocol_actual_matched_LLM_trials"], 0)
        self.assertFalse(r["causal_representation_only_XML_vs_Python_performance_claim_permitted"])
        self.assertTrue(r["missing_developer_evidence_is_not_a_task_failure_or_unsupported_proof"])
        self.assertFalse(r["new_paid_inference_or_new_IFC_experiment_in_v030"])
        self.assertFalse(r["independently_reexecuted_prior_six_developer_controls_in_v030"])
        self.assertTrue(all(x["actual_matched_D_I_LLM_result"] == "NOT_RUN" for x in r["rows"]))
        self.assertTrue(all(x["source_information_parity"] == "NOT_PROVEN" for x in r["rows"]))

    def test_04_second_independent_reconciliation_byte_stable(self):
        one = a.encoded_report(a.reconciled_report(self.sandbox))
        two = a.encoded_report(a.reconciled_report(self.root))
        self.assertEqual(one, two)

    def test_05_frozen_report_exact_bytes_match_generated(self):
        self.assertTrue(self.report_path.is_file(), "v0.30 versioned report not written")
        self.assertEqual(self.report_path.read_bytes(),
                         a.encoded_report(self.expected_report))

    def test_06_reports_are_not_mutated_by_read_only_reconciliation(self):
        before = {
            p.name: sha256(p.read_bytes()).hexdigest()
            for p in (self.sandbox / "reports").iterdir()
        }
        a.reconciled_report(self.sandbox)
        after = {
            p.name: sha256(p.read_bytes()).hexdigest()
            for p in (self.sandbox / "reports").iterdir()
        }
        self.assertEqual(before, after)

    def test_07_tampered_historical_report_refused(self):
        p = self.sandbox / "reports" / a.BASE[0]
        p.write_bytes(p.read_bytes() + b" ")
        with self.assertRaisesRegex(a.EvidenceError, "hash mismatch"):
            a.reconciled_report(self.sandbox)

    def test_08_tampered_latest_report_refused(self):
        p = self.sandbox / "reports" / a.NEW_CASES[-1][0]
        p.write_bytes(p.read_bytes() + b" ")
        with self.assertRaisesRegex(a.EvidenceError, "hash mismatch"):
            a.reconciled_report(self.sandbox)

    def test_09_tampered_role_coverage_refused(self):
        p = self.sandbox / "reports" / a.ROLES[0]
        p.write_bytes(p.read_bytes() + b" ")
        with self.assertRaisesRegex(a.EvidenceError, "hash mismatch"):
            a.reconciled_report(self.sandbox)

    def test_10_missing_evidence_report_fails_closed(self):
        (self.sandbox / "reports" / a.NEW_CASES[2][0]).unlink()
        with self.assertRaisesRegex(a.EvidenceError, "Missing or linked report"):
            a.reconciled_report(self.sandbox)

    def test_11_symlink_substitute_refused(self):
        p = self.sandbox / "reports" / a.NEW_CASES[0][0]
        target = self.root / "reports" / a.NEW_CASES[0][0]
        p.unlink()
        try:
            p.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Host symlinks unavailable without privilege")
        with self.assertRaisesRegex(a.EvidenceError, "Missing or linked report"):
            a.reconciled_report(self.sandbox)

    def test_12_same_new_task_double_count_refused(self):
        duplicate = a.NEW_CASES + (a.NEW_CASES[-1],)
        with patch.object(a, "NEW_CASES", duplicate):
            with self.assertRaisesRegex(a.EvidenceError, "duplicated"):
                a.reconciled_report(self.sandbox)

    def test_13_new_case_reordered_progression_fails(self):
        swapped = list(a.NEW_CASES)
        swapped[0], swapped[1] = swapped[1], swapped[0]
        with patch.object(a, "NEW_CASES", tuple(swapped)):
            with self.assertRaisesRegex(a.EvidenceError, "count chain mismatch"):
                a.reconciled_report(self.sandbox)

    def test_14_only_exact_6_new_original_public_tasks_are_added(self):
        native_ids = {x["task_id"] for x in self.expected_report["rows"]
                      if x["developer_native_D0_I0_bytes_equal_proven"]}
        self.assertTrue({"test_11", "test_14", "test_17", "test_18", "test_19", "test_20"}
                        .issubset(native_ids))
        historical = {x["task_id"] for x in self.expected_report["rows"]
                      if x["frozen_evidence_report"] == a.BASE[0]}
        self.assertEqual(len(historical), 5)
        self.assertTrue(historical.isdisjoint(
            {"test_11", "test_14", "test_17", "test_18", "test_19", "test_20"}))

    def test_15_original_author_partial_scores_not_misreported_as_full(self):
        scores = {x["task_id"]: x["developer_author_score_each_arm"]
                  for x in self.expected_report["rows"]}
        self.assertEqual(scores["test_20"], 0.5)
        self.assertEqual(scores["test_18"], 0.5)
        self.assertEqual(scores["test_17"], 0.5)
        self.assertEqual(scores["test_19"], 0.5)
        self.assertEqual(scores["test_11"], 1.0)
        self.assertEqual(scores["test_14"], 1.0)

    def test_16_no_questions_target_guids_or_raw_ifc_in_public_output(self):
        encoded = a.encoded_report(self.expected_report).decode("utf8").lower()
        for forbidden in ("public_question", "target_guid", "ground_truth",
                          "ifc_bytes", "original_question_text", "api_key",
                          "original_target", "hidden_gt"):
            self.assertNotIn(forbidden, encoded)
        self.assertLess(len(encoded), 50000)

    def test_17_new_invalid_report_name_refused(self):
        with self.assertRaisesRegex(a.EvidenceError, "Invalid report filename"):
            a.load_pinned(self.sandbox, "../report.json", "0" * 64)

    def test_18_only_new_v030_report_created(self):
        report = self.expected_report
        self.assertEqual(report["source_parent_git_commit"], a.PARENT)
        self.assertEqual(report["issue"], a.ISSUE)
        self.assertEqual(len(report["frozen_inputs_sha256"]), 8)


if __name__ == "__main__":
    unittest.main()
