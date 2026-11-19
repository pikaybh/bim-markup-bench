"""Issue #247: offline paired ITT, source-cluster unit, and fail-closed evidence tests."""
from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
from pathlib import Path
import json
import unittest

from tools.bibimbap_v066_cluster_itt import AnalysisInputError, analyse_paired_itt, load_strict_json


def example():
    cohort = []
    outcomes = []
    for i in range(1, 7):
        sha = f"{i:064x}"
        for t in (1, 2):
            key = {"source_sha256": sha, "task_id": f"dev-{i}-{t}", "seed": 42}
            cohort.append({**key, "operation": ("create" if t == 1 else "delete")})
            for arm in ("D_FULL", "D_MANAGED", "I_NATIVE"):
                passed = (
                    (i % 2 == 1) if arm == "D_FULL"
                    else (i % 3 == 0) if arm == "D_MANAGED"
                    else (i <= 2)
                )
                outcomes.append({**key, "arm": arm, "status": "completed", "strict_pass": passed})
    manifest = {
        "protocol_id": "offline-toy-v1",
        "cohort_kind": "developer_exposed_exploratory",
        "regime": "one_shot",
        "arms": ["D_FULL", "D_MANAGED", "I_NATIVE"],
        "cohort": cohort,
    }
    return manifest, outcomes


class TestPairedITT(unittest.TestCase):
    def setUp(self):
        self.manifest, self.outcomes = example()

    def run_it(self, **kwargs):
        return analyse_paired_itt(self.manifest, self.outcomes, bootstrap_resamples=500, **kwargs)

    def expect_blocked(self):
        with self.assertRaises(AnalysisInputError):
            self.run_it()

    def test_correct_matched_ITT_and_cluster_count(self):
        report = self.run_it()
        self.assertEqual(report["n_independent_source_clusters"], 6)
        self.assertEqual(report["n_task_seed_pairs"], 12)
        self.assertEqual(report["by_arm"]["D_FULL"]["strict_passes"], 6)
        self.assertEqual(report["by_arm"]["I_NATIVE"]["strict_passes"], 4)
        self.assertAlmostEqual(report["contrasts"]["D_FULL_minus_I_NATIVE"]["ITT_strict_pass_difference"], 1 / 6, places=5)
        self.assertEqual(report["by_operation"]["create"]["n_task_seed_pairs"], 6)
        self.assertIn("EXPLORATORY", report["verdict"])

    def test_deterministic_and_order_invariant(self):
        one = self.run_it()
        self.manifest["cohort"].reverse()
        self.outcomes.reverse()
        two = self.run_it()
        self.assertEqual(one, two)
        self.assertEqual(one["contrasts"]["D_FULL_minus_I_NATIVE"]["cluster_bootstrap_95pct_CI"],
                         self.run_it()["contrasts"]["D_FULL_minus_I_NATIVE"]["cluster_bootstrap_95pct_CI"])

    def test_exact_bootstrap_seed_pinned(self):
        self.assertEqual(self.run_it(bootstrap_seed=1), self.run_it(bootstrap_seed=1))
        self.assertNotEqual(self.run_it(bootstrap_seed=1)["bootstrap"], self.run_it(bootstrap_seed=2)["bootstrap"])

    def test_small_clusters_report_no_confidence_interval(self):
        self.manifest["cohort"] = self.manifest["cohort"][:4]
        keys = {(r["source_sha256"], r["task_id"], r["seed"]) for r in self.manifest["cohort"]}
        self.outcomes = [r for r in self.outcomes if (r["source_sha256"], r["task_id"], r["seed"]) in keys]
        contrast = self.run_it()["contrasts"]["D_FULL_minus_I_NATIVE"]
        self.assertIsNone(contrast["cluster_bootstrap_95pct_CI"])
        self.assertIn("INSUFFICIENT_CLUSTERS", contrast["uncertainty_note"])

    def test_noncomplete_failures_in_ITT(self):
        for row in self.outcomes:
            if row["arm"] == "D_FULL":
                row["status"] = "unsupported"
                row["strict_pass"] = False
        report = self.run_it()
        self.assertEqual(report["by_arm"]["D_FULL"]["n_ITT"], 12)
        self.assertEqual(report["by_arm"]["D_FULL"]["strict_passes"], 0)
        self.assertEqual(report["by_arm"]["D_FULL"]["status_counts"]["unsupported"], 12)

    def test_all_failures_do_not_disappear(self):
        for row in self.outcomes:
            row["status"] = "not_attempted"
            row["strict_pass"] = False
        report = self.run_it()
        self.assertEqual(report["contrasts"]["D_FULL_minus_I_NATIVE"]["ITT_strict_pass_difference"], 0)

    def test_missing_arm_cannot_silently_select_supported_cases(self):
        self.outcomes.pop()
        self.expect_blocked()

    def test_duplicate_arm_result_rejected(self):
        self.outcomes.append(copy.deepcopy(self.outcomes[0]))
        self.expect_blocked()

    def test_extra_outside_frozen_cohort_rejected(self):
        row = copy.deepcopy(self.outcomes[0])
        row["task_id"] = "not-frozen"
        self.outcomes.append(row)
        self.expect_blocked()

    def test_duplicate_cohort_row_rejected(self):
        self.manifest["cohort"].append(copy.deepcopy(self.manifest["cohort"][0]))
        self.expect_blocked()

    def test_task_answer_hint_field_rejected(self):
        self.outcomes[0]["target_guid"] = "private-answer-should-not-enter-ledger"
        self.expect_blocked()

    def test_reference_ifc_path_field_rejected(self):
        self.manifest["cohort"][0]["ground_truth_ifc"] = "private/secret.ifc"
        self.expect_blocked()

    def test_other_regime_cannot_be_blended(self):
        self.manifest["regime"] = "combined"
        self.expect_blocked()

    def test_no_confirmatory_status_without_independent_review(self):
        self.manifest["cohort_kind"] = "independently_certified_blind"
        self.expect_blocked()

    def test_noncompleted_pass_is_illegal(self):
        self.outcomes[0]["status"] = "timeout"
        self.outcomes[0]["strict_pass"] = True
        self.expect_blocked()

    def test_nonboolean_success_is_illegal(self):
        self.outcomes[0]["strict_pass"] = 1
        self.expect_blocked()

    def test_unsupported_status_typo_is_illegal(self):
        self.outcomes[0]["status"] = "scorer_success"
        self.expect_blocked()

    def test_invalid_source_sha(self):
        self.outcomes[0]["source_sha256"] = "abc"
        self.expect_blocked()

    def test_invalid_seed_boolean(self):
        self.manifest["cohort"][0]["seed"] = True
        self.expect_blocked()

    def test_arm_identity_fixed(self):
        self.manifest["arms"] = ["D_MANAGED", "I_NATIVE"]
        self.expect_blocked()

    def test_empty_cohort_rejected(self):
        self.manifest["cohort"] = []
        self.expect_blocked()

    def test_outcome_report_never_claims_actual_models_or_publication(self):
        report = json.dumps(self.run_it())
        self.assertNotIn("official_score", report)
        self.assertIn("NO_MODEL", report)

    def test_unbounded_bootstrap_allocation_rejected(self):
        with self.assertRaises(AnalysisInputError):
            analyse_paired_itt(self.manifest, self.outcomes, bootstrap_resamples=999999)

    def test_duplicate_json_field_rejected(self):
        with self.assertRaises(AnalysisInputError):
            load_strict_json(b'{"task_id":"one","task_id":"overwritten"}')

    def test_nonfinite_json_constant_rejected(self):
        with self.assertRaises(AnalysisInputError):
            load_strict_json(b'{"strict_pass":NaN}')

    def test_cli_deterministic_report_and_exclusive_create(self):
        manifest, outcomes = example()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            m = folder / "manifest.json"
            o = folder / "outcomes.json"
            report = folder / "report.json"
            m.write_text(json.dumps(manifest), encoding="utf-8")
            o.write_text(json.dumps(outcomes), encoding="utf-8")
            cmd = [
                sys.executable, "-m", "tools.bibimbap_v066_cluster_itt",
                "--manifest", str(m), "--outcomes", str(o),
                "--output", str(report),
            ]
            cwd = Path(__file__).resolve().parents[1]
            first = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["input_sha256"]["manifest"]), 64)
            before = report.read_bytes()
            again = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual(report.read_bytes(), before)

    def test_unsupported_dict_keys_rejected(self):
        self.manifest["paid_provider_approved"] = True
        self.expect_blocked()


if __name__ == "__main__":
    unittest.main()
