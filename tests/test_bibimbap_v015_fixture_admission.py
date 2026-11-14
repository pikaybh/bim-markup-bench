"""Read-only isolated-worktree prerequisite diagnostics for prior broad tests."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from tools.inspect_v015_fixture_admission import (
    inspect_fixture_admission, PUBLIC_TASKS, PREVIOUS_PREFLIGHT,
)

HERE = Path(__file__).resolve().parents[1]
RECORDED = HERE / "reports" / "bibimbap_v015_fixture_admission_20261114.json"


class FixtureAdmissionV015Tests(unittest.TestCase):
    def test_existing_unmounted_legacy_fixtures_do_not_equal_green_suite(self):
        if not RECORDED.exists():
            raise unittest.SkipTest("Original read-only fixture audit not available")
        document = json.loads(RECORDED.read_text(encoding="utf8"))
        self.assertEqual(document["status"], "BLOCKED_KNOWN_FIXTURES_NOT_ADMITTED")
        self.assertEqual(document["prior_832_case_run_had"]["tests_run"], 832)
        self.assertEqual(document["prior_832_case_run_had"]["errors"], 65)
        self.assertTrue(document["fixture_admission_is_not_full_suite_success"])
        self.assertFalse(document["automatic_copy_or_original_data_modification"])
        self.assertEqual(len(document["fixtures"]), 2)

    def test_invalid_worktree_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            with self.assertRaises(ValueError):
                inspect_fixture_admission(p, p, p)

    def test_missing_but_existing_seed_is_classified_without_copy(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            branch, primary, archive = p / "branch", p / "primary", p / "archive"
            branch.mkdir()
            (branch / "AGENTS.md").write_text("research-only")
            primary.mkdir()
            archive.mkdir()
            result = inspect_fixture_admission(branch, primary, archive)
            self.assertEqual(result["status"], "BLOCKED_KNOWN_FIXTURES_NOT_ADMITTED")
            self.assertFalse((branch / PUBLIC_TASKS).exists())
            self.assertFalse((branch / PREVIOUS_PREFLIGHT).exists())
            self.assertEqual(
                {r["admission_status"] for r in result["fixtures"]},
                {"MISSING_ISOLATED_FIXTURE_AND_SEED"},
            )

    def test_altered_local_fixture_must_not_be_admitted(self):
        # Synthetic deliberately invalid bytes only, no original data included.
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            branch, primary, archive = p / "branch", p / "primary", p / "archive"
            for root in (branch, primary, archive):
                root.mkdir()
            (branch / "AGENTS.md").write_text("research-only")
            for path, content in (
                (primary / PUBLIC_TASKS, "synthetic wrong SHA"),
                (branch / PUBLIC_TASKS, "synthetic different wrong SHA"),
                (archive / PREVIOUS_PREFLIGHT, "different source"),
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf8")
            result = inspect_fixture_admission(branch, primary, archive)
            self.assertEqual(result["status"], "BLOCKED_KNOWN_FIXTURES_NOT_ADMITTED")
            self.assertEqual(result["fixtures"][0]["admission_status"],
                             "SOURCE_HASH_PIN_MISMATCH")
            self.assertEqual(result["fixtures"][1]["admission_status"],
                             "MISSING_ISOLATED_WORKTREE_MOUNT")
            self.assertFalse((branch / PREVIOUS_PREFLIGHT).exists())


    def test_unpinned_historical_record_without_seed_cannot_be_admitted(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            branch, primary, archive = p / "branch", p / "primary", p / "archive"
            for root in (branch, primary, archive):
                root.mkdir()
            (branch / "AGENTS.md").write_text("research-only")
            local = branch / PREVIOUS_PREFLIGHT
            local.parent.mkdir(parents=True)
            local.write_text("unverifiable historic record", encoding="utf8")
            prior = local.read_bytes()
            report = inspect_fixture_admission(branch, primary, archive)
            self.assertEqual(report["status"], "BLOCKED_KNOWN_FIXTURES_NOT_ADMITTED")
            self.assertEqual(report["fixtures"][1]["admission_status"],
                             "LOCAL_PRESENT_WITHOUT_VERIFIABLE_SEED")
            self.assertEqual(local.read_bytes(), prior)

if __name__ == "__main__":
    unittest.main()
