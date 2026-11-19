"""No-provider, no-retry regression checks of real 45-row full cohort."""
from __future__ import annotations
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import unittest

from tools.run_bibimbap_full45_luna import (
    ROOT,RUN_ROOT,MANIFEST,COHORT_REPORT,ORIGINAL_PILOT,APPROVED_CAP_USD,
    MAX_OUTPUT_TOKENS,MODEL,_load,
)
from tools.audit_bibimbap_full45_semantics import AUDIT_REPORT,audit


class Original45RealEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prep=_load(MANIFEST)
        cls.report=_load(COHORT_REPORT)
        cls.audit=_load(AUDIT_REPORT)
        cls.rows=cls.report["individual_results"]

    def test_frozen_45_itt_population_exact(self):
        self.assertEqual(len(self.rows),45)
        self.assertEqual(len({x["test_id"] for x in self.rows}),45)
        self.assertEqual(Counter(x["source_crud"] for x in self.rows),
                         {"create":15,"update":15,"delete":15})
        self.assertEqual(Counter(x["source_category"] for x in self.rows),
                         {"basic":15,"geometry":15,"topological":15})
        self.assertEqual(len(self.prep["frozen_population"]),45)
        self.assertEqual([x["test_id"] for x in self.prep["frozen_population"]],
                         [x["test_id"] for x in self.rows])

    def test_all_trails_completed_or_hard_declared_source_block(self):
        self.assertEqual(self.report["status"],
                         "COMPLETE_SINGLE_COHORT_WITH_DECLARED_UNSUPPORTED")
        self.assertEqual(self.report["statuses"],{
            "BLOCKED_UNSUPPORTED_SOURCE_PREDECLARED":9,
            "ORIGINAL_AUTHOR_SCORED":14,
            "REUSED_EXISTING_REAL_ONE_SHOT":1,
            "TRUSTED_XML_OR_NATIVE_GRADING_FAILED":21,
        })
        self.assertEqual(self.report["provider_attempts_including_prior_test05"],36)
        self.assertEqual(self.report["provider_attempts_new_in_this_cohort"],35)
        self.assertEqual(self.prep["future_provider_calls_planned"],35)
        self.assertEqual(self.report["original_author_scorer_successfully_returned_rows"],15)
        self.assertEqual(self.report["original_source_unprojectable_9_as_failures"],9)

    def test_budget_bounded_owner_approved_original_one_shot_once(self):
        first=_load(ORIGINAL_PILOT)
        self.assertEqual(self.report["model"],"gpt-6-luna")
        self.assertEqual(self.report["owner_approved_max_usd"],"1.00")
        self.assertLess(Decimal(self.report["cost_estimated_usd_including_prior_test05"]),
                        APPROVED_CAP_USD)
        self.assertLess(Decimal(self.report["cost_reserved_upper_usd"]),
                        APPROVED_CAP_USD)
        self.assertEqual(first["actual_api_calls_attempted"],1)
        reused=next(x for x in self.rows if x["test_id"]=="test_05")
        self.assertEqual(reused["status"],"REUSED_EXISTING_REAL_ONE_SHOT")
        self.assertFalse(reused["called_during_this_cohort"])
        self.assertEqual(reused["actual_model_output_sha256"],first["raw_model_output_sha256"])
        self.assertEqual(reused["usage_estimated_cost_usd"],first["actual_provider_usage_cost_estimate_usd"])
        self.assertEqual(sum(int(x.get("model_calls_attempted",0)) for x in self.rows),36)
        self.assertEqual(self.prep["max_response_output_tokens"],MAX_OUTPUT_TOKENS)
        self.assertEqual(self.prep["total_provider_call_retries"],0)
        self.assertEqual(sum(Decimal(x.get("usage_estimated_cost_usd") or "0") for x in self.rows),
                         Decimal(self.report["cost_estimated_usd_including_prior_test05"]))

    def test_author_score_completely_separate_from_strict_task_success(self):
        self.assertEqual(self.report["author_full_score_count_45"],3)
        self.assertAlmostEqual(self.report["author_full_score_rate_45"],3/45)
        full={x["test_id"] for x in self.rows if x["author_full_score"]}
        self.assertEqual(full,{"test_05","geometry_test_11","topological_test_13"})
        self.assertIsNone(self.report["independently_verified_45_task_success_rate"])
        self.assertFalse(self.report["task_level_strict_success_independently_verified"])
        self.assertTrue(all(x["strict_success_independent"] is None for x in self.rows))
        self.assertAlmostEqual(self.report["mean_original_author_score_all45_zero_for_non_scored"],
                               0.19629666666666665)

    def test_fullscore_three_are_actual_semantic_edits(self):
        self.assertEqual(self.audit["author_original_fullscore_with_actual_xml_semantic_change_count"],3)
        self.assertEqual(set(self.audit["author_original_fullscore_with_actual_xml_semantic_change_task_ids"]),
                         {"test_05","geometry_test_11","topological_test_13"})
        self.assertEqual(self.audit["model_calls_this_audit"],0)
        self.assertEqual(self.audit["total_actual_provider_calls_reused_and_new"],36)
        saved={x["test_id"]:x for x in self.audit["individual_source_differences"]}
        self.assertEqual(saved["test_05"]["xml_semantic_diff"]["new_id_count"],1)
        self.assertEqual(saved["geometry_test_11"]["xml_semantic_diff"]["modified_existing_id_count"],6)
        self.assertEqual(saved["topological_test_13"]["xml_semantic_diff"]["modified_existing_id_count"],1)

    def test_noop_partial_credit_is_not_called_a_success(self):
        scored=[x for x in self.rows if x["status"] in ("ORIGINAL_AUTHOR_SCORED","REUSED_EXISTING_REAL_ONE_SHOT")]
        self.assertEqual(len(scored),15)
        update=next(x for x in scored if x["test_id"]=="test_12")
        self.assertEqual(update["author_score"],update["original_author_noop_score"])
        self.assertEqual(update["author_score"],2/3)
        self.assertFalse(update["author_full_score"])
        self.assertGreater(float(self.audit["original_author_noop_baseline_mean_45"]),0.2)

    def test_public_packet_does_not_contain_private_scorer_fields(self):
        for row in self.rows:
            if row["status"]=="BLOCKED_UNSUPPORTED_SOURCE_PREDECLARED" or row["test_id"]=="test_05":
                continue
            p=RUN_ROOT/row["test_id"]/"public_packet.json"
            if not p.is_file():
                self.skipTest("Local gitignored raw evidence unavailable in this checkout")
            item=_load(p)
            self.assertEqual(set(item),{"input","instructions"})
            self.assertIn("PUBLIC TASK:",item["input"])
            self.assertNotIn("structured-output",item["input"])
            self.assertNotIn("ground_truth_ifc",item["input"])
            self.assertNotIn("execute_test(",item["input"])

    def test_provider_model_exact_and_raw_original_response_preserved(self):
        for row in self.rows:
            if row["status"]=="REUSED_EXISTING_REAL_ONE_SHOT" or row["status"].startswith("BLOCKED"):
                continue
            self.assertEqual(row["model_calls_attempted"],1)
            self.assertEqual(row["provider_returned_model"],MODEL)
            self.assertEqual(row["provider_status"],"completed")
            self.assertGreater(row["reported_input_tokens"],0)
            self.assertGreater(row["reported_output_tokens"],0)
            f=RUN_ROOT/row["test_id"]/"model_generated_exact.raw.txt"
            if not f.is_file():
                self.skipTest("Local raw response was not checked into Git")
            import hashlib
            self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(),
                             row["model_generated_exact_sha256"])

    def test_reaudit_matches_frozen_independent_ledger(self):
        if not RUN_ROOT.is_dir():
            self.skipTest("Gitignored raw evidence unavailable")
        fresh=audit()
        self.assertEqual(fresh,self.audit)


if __name__=="__main__":
    unittest.main()
