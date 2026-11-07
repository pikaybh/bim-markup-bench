"""G1 official task ledger and fail-closed release safety tests."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from src.data.bim_edit import read_tasks,AuditError
from src.evaluation.g1_coverage import (
    generate_coverage_ledger,STATIC_UNSUPPORTED,CONDITIONAL,GATE_BLOCKED,
)
ROOT=Path(__file__).resolve().parents[1]

class Frozen324AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=ROOT/"data/tasks.jsonl"
        if not p.exists():
            raise unittest.SkipTest("Public pinned 180 KiB tasks not cached; official coverage gate stays blocked")
        cls.rows=read_tasks(p)

    def test_all_324_tasks_have_reasons_and_no_fake_pass(self):
        output=generate_coverage_ledger(self.rows)
        self.assertEqual(output["status"],GATE_BLOCKED)
        self.assertEqual(output["metadata_validated_task_count"],324)
        self.assertEqual(output["coverage_accounted_for"],324)
        self.assertEqual(output["official_tasks_scored"],0)
        self.assertEqual(output["verified_official_engine_supported"],0)
        self.assertEqual(output["static_engine_unsupported_count"]+
                         output["conditional_source_dependent_unverified_count"],324)
        self.assertEqual(len(output["tasks"]),324)
        self.assertEqual(len({t["task_id"] for t in output["tasks"]}),324)
        for row in output["tasks"]:
            self.assertIn(row["engine_status"],(STATIC_UNSUPPORTED,CONDITIONAL))
            self.assertGreater(len(row["reason_codes"]),0)
            self.assertIsNone(row["official_task_success"])
            self.assertFalse(row["official_evaluator_run"])
            self.assertFalse(row["native_ground_truth_ifc_verified"])
            self.assertFalse(row["native_input_ifc_verified"])

    def test_no_prompts_guid_gt_paths_evaluation_secrets_in_ledger(self):
        output=json.dumps(generate_coverage_ledger(self.rows),sort_keys=True)
        for forbidden in (
            '"ground_truth_ifc":', '"input_ifc":', '"evaluation":',
            '"target_guid":','"prompt":','"target":',
            '"full_model_path":',"OPENAI_API_KEY",
        ):
            self.assertFalse(forbidden in output, f"Report included grader-only field {forbidden}")
        # One known official target GUID cannot leak through task-level
        # coverage report into prompt-facing model context.
        for source in self.rows:
            for guid in source["target"].get("guids",[]):
                self.assertNotIn(guid,output)

    def test_coverage_report_in_repo_is_reproducible(self):
        report_path=ROOT/"reports/g1_324_support_matrix.json"
        tracked=json.loads(report_path.read_text())
        fresh=generate_coverage_ledger(self.rows)
        self.assertEqual(tracked,fresh)

class GateRejectionTests(unittest.TestCase):
    def test_enforced_full_release_gate_fails_with_no_trial(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/"private.json"
            run=subprocess.run([sys.executable,"-m","tools.g1_release_gate",
                "--tasks",str(ROOT/"data/tasks.jsonl"),
                "--output",str(output),"--enforce"],
                cwd=ROOT,capture_output=True,text=True,timeout=15)
            self.assertEqual(run.returncode,2)
            self.assertTrue(output.exists())
            info=json.loads(run.stdout)
            self.assertEqual(info["status"],GATE_BLOCKED)
            self.assertEqual(info["model_api_calls"],0)
            self.assertEqual(info["official_tasks_scored"],0)

    def test_invalid_or_missing_task_record_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            for item in (None,b'{"task_id":"something"}\n'):
                candidate=Path(tmp)/"tasks.jsonl"
                if item is not None:candidate.write_bytes(item)
                elif candidate.exists():candidate.unlink()
                run=subprocess.run([sys.executable,"-m","tools.g1_release_gate",
                   "--tasks",str(candidate),"--output",str(Path(tmp)/"report.json"),
                   "--enforce"],cwd=ROOT,capture_output=True,text=True,timeout=10)
                self.assertEqual(run.returncode,2)
                self.assertIn("BLOCKED",run.stdout)

    def test_synthetic_evidence_cannot_unlock_official_release(self):
        evidence=json.loads((ROOT/"reports/deterministic_ceiling.json").read_text())
        self.assertEqual(evidence["status"],"PASS_SYNTHETIC_ONLY")
        self.assertTrue(evidence["all_scenarios_native_ifc_semantic_parity"])
        self.assertEqual(evidence["scenarios_verified"],6)
        self.assertEqual(evidence["official_bim_edit_tasks_tested"],0)
        self.assertFalse(evidence["paid_model_pilot_ready"])
        self.assertIn("BLOCKED",evidence["release_gate"])

if __name__=="__main__":unittest.main()
