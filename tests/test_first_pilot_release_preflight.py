"""First matched pilot source-only diagnostic readiness: genuine IFC + gate tests."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from src.evaluation import first_pilot_release_preflight as ready
from tools import audit_first_matched_pilot_preflight as cli


class FirstMatchedPilotPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=ready.run_first_pilot_preflight()
        cls.input_hashes={
            k:sha256((ready.ROOT/rel).read_bytes()).hexdigest()
            for k,(rel,_) in ready.EVIDENCE.items()
        }

    def test_actual_six_native_ifcs_pass_source_relative_surrogate_only(self):
        r=self.result
        self.assertEqual(r["status"],
                         "TECHNICAL_SOURCE_RELATIVE_PAIRS_PASS_REAL_LLM_PILOT_BLOCKED")
        self.assertEqual(r["offline_d0_i0_ifc_pairs_rerun"],3)
        self.assertEqual(r["offline_native_outputs_scored_by_surrogate"],6)
        self.assertEqual(r["surrogate_postconditions_passed"],6)
        self.assertEqual(r["posthoc_demonstration_cases"],list(ready.CASES))
        for case in r["cases"]:
            self.assertEqual(case["surrogate_metric_origin"],"surrogate")
            self.assertTrue(case["d0_source_relative_native_pass"])
            self.assertTrue(case["i0_source_relative_native_pass"])
            self.assertFalse(case["full_task_scored"])
            self.assertIn(case["task_id"],ready.CASES)
            self.assertEqual(len(case["source_sha256"]),64)

    def test_neither_new_rubric_nor_old_pilot_claims_model_success(self):
        r=self.result
        self.assertEqual(r["original_fixed_pilot_task_count"],36)
        self.assertFalse(r["frozen_candidate_population_modified"])
        self.assertEqual(r["full_task_instruction_oracles_approved"],0)
        self.assertEqual(r["official_bim_edit_scores_computed"],0)
        self.assertEqual(r["model_generated_attempts"],0)
        self.assertEqual(r["provider_or_network_calls"],0)
        self.assertEqual(r["real_paid_spend_usd"],0)
        self.assertFalse(r["real_matched_llm_trial_allowed"])
        self.assertFalse(r["independent_full_task_evaluator_prospectively_approved"])

    def test_per_model_rights_worker_and_price_authorization_hard_blocked(self):
        r=self.result
        for key in ("source_model_rights_cleared",
                    "worker_linux_engine_available",
                    "candidate_python_isolation_verified",
                    "model_provider_and_exact_tokenizer_selected",
                    "provider_input_output_tokens_measured",
                    "price_snapshot_verified",
                    "explicit_paid_spend_authorization",
                    "model_context_tool_feedback_parity_approved"):
            with self.subTest(key=key):
                self.assertIs(r[key],False)
        self.assertEqual(r["approved_original_bim_edit_external_model_count"],0)

    def test_original_fixed_data_rights_and_host_reports_untouched(self):
        self.assertEqual({
            k:sha256((ready.ROOT/rel).read_bytes()).hexdigest()
            for k,(rel,_) in ready.EVIDENCE.items()
        },self.input_hashes)
        self.assertEqual(self.result["linked_evidence_hashes"],{
            k:value[1] for k,value in sorted(ready.EVIDENCE.items())
        })

    def test_wrong_original_36_or_rights_hash_fails_before_any_run(self):
        rights=ready.EVIDENCE["model_rights"]
        with patch.dict(ready.EVIDENCE,{
            "model_rights":(rights[0],"0"*64)
        }):
            with self.assertRaisesRegex(ready.FirstPilotNotReady,"changed"):
                ready.checked_evidence(ready.ROOT)

    def test_wrong_budget_or_worker_digests_are_rejected(self):
        for name in ("offline_budget","local_worker"):
            old=ready.EVIDENCE[name]
            with self.subTest(name=name),patch.dict(ready.EVIDENCE,{
                name:(old[0],"0"*64)
            }):
                with self.assertRaises(ready.FirstPilotNotReady):
                    ready.checked_evidence(ready.ROOT)

    def test_missing_task_case_runner_never_promoted_to_pilot(self):
        with self.assertRaisesRegex(ready.FirstPilotNotReady,
                                    "population"):
            ready.run_first_pilot_preflight(runners={
                "WIN-UPD-DIR-A-002":lambda **kw:{},
            })

    def test_submitted_result_cannot_include_hidden_data_or_fake_score(self):
        s=json.dumps(self.result,sort_keys=True)
        for token in ('"prompt"','"target"','"evaluation"','"ground_truth_ifc"',
                      "API_KEY","Bearer ","reference_ifc_path"):
            with self.subTest(token=token):
                self.assertNotIn(token,s)
        self.assertNotIn("official-score",s)

    def test_cli_exit_two_and_write_once_sanitized_output(self):
        with TemporaryDirectory(prefix="g2-preflight-report-") as td:
            file=Path(td)/"report.json"
            with patch.object(cli,"run_first_pilot_preflight",return_value=self.result):
                self.assertEqual(cli.main(["--output-json",str(file)]),2)
                once=file.read_bytes()
                with self.assertRaises(SystemExit):
                    cli.main(["--output-json",str(file)])
                self.assertEqual(once,file.read_bytes())
            self.assertEqual(json.loads(once)["surrogate_postconditions_passed"],6)

    def test_historical_native_result_assumptions_are_honest(self):
        cases={item["task_id"]:item for item in self.result["cases"]}
        self.assertEqual(cases["WAL-CRE-SPA-A-003"]["unproven_full_task_condition"],
                         "ROOM_PARTITION_AND_METADATA_NOT_ORACLE_PROVEN")
        self.assertEqual(cases["DOR-DEL-DIR-A-001"]["unproven_full_task_condition"],
                         "UNMENTIONED_BOUNDARY_POLICY_AND_ABSENT_OPENING_STOREY_UNKNOWN")
        self.assertTrue(self.result["source_relative_rubric_posthoc_not_preregistered"])


if __name__=="__main__":
    unittest.main()
