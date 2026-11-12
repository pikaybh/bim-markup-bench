"""No-network and no-payment safeguards for the XML-only pivot (#100)."""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.evaluation.xml_only_readiness import (
    ROOT, ReadinessEvidenceError, audit_xml_only,
)
from tools.audit_xml_only_readiness import main

CACHE_VAR = "BIM_EDIT_PINNED_TASK_JSONL"


class XmlOnlyReadinessTests(unittest.TestCase):
    def test_missing_public_metadata_fails_closed(self):
        with TemporaryDirectory() as temp:
            with self.assertRaises(ReadinessEvidenceError):
                audit_xml_only(evidence_root=ROOT,
                               task_jsonl=Path(temp) / "missing.jsonl")

    def test_unpinned_public_metadata_fails_closed(self):
        with TemporaryDirectory() as temp:
            metadata = Path(temp) / "tasks.jsonl"
            metadata.write_text('{"task_id":"fake"}\n', encoding="utf8")
            with self.assertRaisesRegex(ReadinessEvidenceError, "SHA-256 mismatch"):
                audit_xml_only(evidence_root=ROOT, task_jsonl=metadata)

    def test_cli_refuses_missing_metadata_without_paid_execution(self):
        with TemporaryDirectory() as temp:
            with redirect_stdout(io.StringIO()) as captured:
                code = main(["--task-jsonl", str(Path(temp) / "no.jsonl")])
            self.assertEqual(code, 2)
            response = json.loads(captured.getvalue())
            self.assertEqual(response["status"], "EVIDENCE_INVALID")

    def test_pinned_public_snapshot_integration_when_provided(self):
        metadata_path = os.environ.get(CACHE_VAR)
        if not metadata_path or not Path(metadata_path).is_file():
            self.skipTest(f"Provide {CACHE_VAR} for optional 324-row cached integration")
        report = audit_xml_only(evidence_root=ROOT, task_jsonl=Path(metadata_path))
        self.assertEqual(report["status"], "BLOCKED_NOT_REGISTERED_OR_SCORABLE")
        self.assertEqual(report["primary_condition"], "direct_xml_only")
        self.assertEqual(report["published_population_size"], 324)
        self.assertEqual(report["existing_candidate_size"], 36)
        self.assertFalse(report["candidate_preregistered"])
        self.assertEqual(report["prospective_itt_denominator_if_registered"], 36)
        self.assertEqual(report["model_calls_in_this_audit"], 0)
        self.assertEqual(report["official_bim_edit_tasks_scored_in_this_audit"], 0)
        self.assertFalse(report["can_claim_causal_xml_vs_api_or_python"])
        self.assertEqual(report["candidate_readiness_dispositions"], {
            "INPUT_IFC_NOT_CACHED": 2,
            "MANUAL_SOURCE_ONLY_EVIDENCE_WITH_GATES": 2,
            "SOURCE_DEPENDENCY_OR_ORACLE_BLOCKED": 9,
            "STATIC_ENGINE_UNSUPPORTED": 23,
        })
        self.assertEqual(len(report["task_rows_no_prompt_or_ground_truth"]), 36)
        for row in report["task_rows_no_prompt_or_ground_truth"]:
            self.assertEqual(row["official_score"], None)
            self.assertFalse(row["xml_llm_trial_performed"])
            self.assertFalse(row["full_task_oracle_proven"])
            self.assertNotIn("prompt", row)
            self.assertNotIn("ground_truth_ifc", row)
            self.assertNotIn("input_ifc", row)
            self.assertNotIn("target", row)
        self.assertEqual(report["author_published_models_audited"], 7)
        self.assertEqual(report["published_baseline_rows_missing"], 1)
        self.assertIn("official_author_scorer", report["launch_blockers"])
        self.assertIn("per_model_redistribution_rights", report["launch_blockers"])

    def test_cli_write_once_on_pinned_cache_if_provided(self):
        metadata_path = os.environ.get(CACHE_VAR)
        if not metadata_path or not Path(metadata_path).is_file():
            self.skipTest(f"Provide {CACHE_VAR} for optional cached integration")
        with TemporaryDirectory() as temp:
            out = Path(temp) / "report.json"
            args = ["--task-jsonl", metadata_path, "--output-json", str(out)]
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(args), 2)  # blocked, report still saved
            self.assertTrue(out.exists())
            report = json.loads(out.read_text(encoding="utf8"))
            self.assertEqual(report["existing_candidate_size"], 36)
            with redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    main(args)  # refuse overwrite


if __name__ == "__main__":
    unittest.main()
