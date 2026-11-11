"""G1 #16 — frozen 36 inclusion and actual three offline native pairs.

The real pinned public input IFCs are executed in setUpClass, but no
reference/GT IFC, private target metadata, model provider or paid solver
is read. All 33 other original sample IDs retain their historical status.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from src.evaluation import offline_three_pair_readiness as oracle
from tools import verify_frozen_36_offline_pairs as cli


class OfflineThreePairFrozen36Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_sha = {
            key:sha256((oracle.ROOT/filename).read_bytes()).hexdigest()
            for key,(filename,_) in oracle.EXTRA_PINS.items()
        }
        # Real source-only D0/XML and independent I0/Python trials, one
        # each, once per test class — NOT a model benchmark run.
        cls.live={case:oracle.RUNNERS[case]() for case in oracle.CASES}
        cls.report=oracle.run_offline_three_pair_recheck(
            runners={case:(lambda x=case:cls.live[x]) for case in oracle.CASES})

    def test_all_three_actual_pinned_source_pairs_executed(self):
        data=self.report
        self.assertEqual(data["posthoc_dev_native_pairs_executed_now"],3)
        self.assertEqual(data["posthoc_dev_native_pairs_passed_now"],3)
        self.assertEqual(data["source_only_pair_task_ids"],list(oracle.CASES))
        self.assertEqual(set(self.live),set(oracle.CASES))
        for case in oracle.CASES:
            self.assertEqual(self.live[case]["status"],oracle.EXPECTED_STATUS[case])

    def test_fixed_36_unchanged_and_historical_30_6_assets_count(self):
        report=self.report
        self.assertEqual(report["fixed_candidate_sha256"],oracle.PINNED_TASK_SHA)
        self.assertEqual(report["frozen_candidates"],36)
        self.assertEqual(report["frozen_source_reference_pairs_historically_verified"],30)
        self.assertEqual(report["frozen_source_reference_pairs_missing"],6)
        rows=report["tasks"]
        self.assertEqual(len(rows),36)
        self.assertEqual(len({r["task_id"] for r in rows}),36)
        self.assertEqual(sum(r["pinned_source_and_reference_bytes_historically_checked"]
                             for r in rows),30)
        self.assertEqual(sum(r["source_only_pair_rerun_now"] for r in rows),3)
        self.assertEqual(sum(not r["source_only_pair_rerun_now"] for r in rows),33)
        self.assertTrue(report["all_other_33_tasks_not_rerun_not_silently_dropped"])

    def test_door_posthoc_capability_does_not_rewrite_static_unsupported(self):
        byid={r["task_id"]:r for r in self.report["tasks"]}
        door=byid[oracle.CASES[2]]
        self.assertEqual(door["historical_reason_code_unchanged"],
                         "STATIC_ENGINE_UNSUPPORTED")
        self.assertTrue(door["source_only_pair_rerun_now"])
        self.assertTrue(door["posthoc_engineering_proof_not_scored"])
        self.assertFalse(door["full_instruction_specific_oracle_approved"])
        self.assertEqual(sum(r["historical_reason_code_unchanged"]==
                             "STATIC_ENGINE_UNSUPPORTED"
                             for r in self.report["tasks"]),23)
        self.assertFalse(self.report["historical_pilot_task_scope_retroactively_changed"])

    def test_three_distinct_operation_and_source_only_status_scopes(self):
        byid={r["task_id"]:r for r in self.report["tasks"]}
        self.assertEqual(byid[oracle.CASES[0]]["operation"],"update")
        self.assertEqual(byid[oracle.CASES[1]]["operation"],"create")
        self.assertEqual(byid[oracle.CASES[2]]["operation"],"delete")
        self.assertEqual(byid[oracle.CASES[1]]["native_subclaim"]["native_wall_join_count"],2)
        self.assertEqual(byid[oracle.CASES[2]]["native_subclaim"]["deleted_ifc_roots"],10)
        self.assertEqual(byid[oracle.CASES[2]]["native_subclaim"]
                         ["unrelated_world_meshes_preserved"],13)
        self.assertEqual(self.report["tested_instruction_categories"],["direct","spatial"])

    def test_full_llm_and_official_benchmark_gates_remain_blocked(self):
        data=self.report
        self.assertEqual(data["full_instruction_specific_D0_I0_task_oracles_proven"],0)
        self.assertEqual(data["actual_LLM_trials"],0)
        self.assertEqual(data["official_bim_edit_tasks_scored"],0)
        self.assertFalse(data["official_bim_edit_scorer_executed"])
        self.assertFalse(data["actual_model_generated_XML_or_Python_used"])
        self.assertFalse(data["paid_budget_approved"])
        self.assertFalse(data["G0_G1_G2_G3_live_experiment_release_allowed"])
        self.assertEqual(data["unique_external_ifc_asset_rights_individually_cleared"],0)
        self.assertFalse(data["linux_worker_admission_verified"])
        self.assertFalse(data["model_provider_token_usage_measured"])
        self.assertTrue(all(not r["live_LLM_trial_authorized"]
                            and not r["official_score_computed"] for r in data["tasks"]))

    def test_historical_evidence_is_unchanged_and_has_no_gt_leak(self):
        self.assertEqual({
            key:sha256((oracle.ROOT/filename).read_bytes()).hexdigest()
            for key,(filename,_) in oracle.EXTRA_PINS.items()
        },self.original_sha)
        out=json.dumps(self.report,sort_keys=True)
        for hidden in ('"prompt"','"target"','"evaluation"','"ground_truth_ifc"',
                       "API_KEY","Bearer ","\\data\\ifc\\","source_ifc_path"):
            with self.subTest(hidden=hidden):
                self.assertNotIn(hidden,out)
        self.assertFalse(self.report["GT_or_target_fields_exposed_to_model"])
        self.assertFalse(self.report["reference_IFC_read_by_this_orchestrator"])

    def test_static_sample_is_rejected_if_one_id_duplicated(self):
        with self.assertRaisesRegex(oracle.OfflinePairReadinessBlocked,
                                    "duplicate task"):
            oracle._index([{"task_id":"X"},{"task_id":"X"}],2,"fixture")

    def test_old_report_or_rights_digest_spoof_is_rejected(self):
        old=oracle.EXTRA_PINS["rights"]
        with patch.dict(oracle.EXTRA_PINS,{
            "rights":(old[0],"0"*64),
        }):
            with self.assertRaisesRegex(oracle.OfflinePairReadinessBlocked,"SHA"):
                oracle._load_evidence(oracle.ROOT)

    def test_forged_paid_llm_or_author_scorer_status_rejected(self):
        records=oracle._load_evidence(oracle.ROOT)
        copy=deepcopy(records)
        copy["scorer_origin"]["author_original_evaluator_cli_entrypoint_verified"]=True
        with self.assertRaises(oracle.OfflinePairReadinessBlocked):
            oracle._assert_same_frozen_task_population(copy)
        copy=deepcopy(records)
        copy["rights"]["individual_model_license_documents_verified"]=36
        with self.assertRaises(oracle.OfflinePairReadinessBlocked):
            oracle._assert_same_frozen_task_population(copy)

    def test_incorrect_or_ambiguous_pilot_case_report_fails_closed(self):
        for case in oracle.CASES:
            item=deepcopy(self.live[case])
            item["status"]="ACCEPTED_OFFICIAL"
            with self.subTest(case=case,reason="status"),self.assertRaises(
                    oracle.OfflinePairReadinessBlocked):
                oracle._assert_live_demo(case,item)
            item=deepcopy(self.live[case])
            item["official_tasks_scored"]=1
            with self.subTest(case=case,reason="score"),self.assertRaises(
                    oracle.OfflinePairReadinessBlocked):
                oracle._assert_live_demo(case,item)

    def test_individual_native_metric_forgery_rejected(self):
        win=deepcopy(self.live[oracle.CASES[0]])
        win["all_existing_relationships_preserved"]=False
        with self.assertRaises(oracle.OfflinePairReadinessBlocked):
            oracle._assert_live_demo(oracle.CASES[0],win)
        wall=deepcopy(self.live[oracle.CASES[1]])
        wall["complete_task_oracle_proven"]=True
        with self.assertRaises(oracle.OfflinePairReadinessBlocked):
            oracle._assert_live_demo(oracle.CASES[1],wall)
        door=deepcopy(self.live[oracle.CASES[2]])
        door["native_IfcRoot_deleted"]=9
        with self.assertRaises(oracle.OfflinePairReadinessBlocked):
            oracle._assert_live_demo(oracle.CASES[2],door)

    def test_silent_posthoc_pilot_subset_change_rejected(self):
        runners={case:(lambda x=case:self.live[x]) for case in oracle.CASES[:2]}
        with self.assertRaisesRegex(oracle.OfflinePairReadinessBlocked,"caller changed"):
            oracle.run_offline_three_pair_recheck(runners=runners)

    def test_cli_returns_blocking_exit_and_refuses_report_overwrite(self):
        with TemporaryDirectory(prefix="g1-36-preflight-cli-") as td:
            path=Path(td)/"first.json"
            with patch.object(cli,"run_offline_three_pair_recheck",
                              return_value=self.report):
                self.assertEqual(cli.main(["--output-json",str(path)]),2)
                first=path.read_bytes()
                with self.assertRaises(SystemExit):
                    cli.main(["--output-json",str(path)])
                self.assertEqual(path.read_bytes(),first)
                self.assertEqual(json.loads(first)["frozen_candidates"],36)


if __name__=="__main__":
    unittest.main()
