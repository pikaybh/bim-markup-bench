"""One repository/one frozen cohort: G3 3-arm scientific DRAFT guardrails.

Positive checks deliberately exercise only deterministic offline planning,
never a model worker, token provider, evaluator or original GT file.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.runner.manifest import (
    ARMS, THREE_ARM_DRAFT, ThreeArmDraftBlocked,
    validate_three_arm_candidate, three_arm_candidate_schedule,
    validate_synthetic_one_shot_trace, validate_synthetic_token_ceiling,
    make_run_id, paired_schedule,
)

ROOT=Path(__file__).resolve().parents[1]
PROPOSAL=ROOT/"configs/pilot_36_three_arm_candidate_v0.json"
EVIDENCE=ROOT/"reports/g3_three_arm_108_slot_candidate_schedule_20261120.json"


def proposal():
    return json.loads(PROPOSAL.read_text(encoding="utf8"))


class ThreeArmCandidateStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=proposal()
        cls.report=three_arm_candidate_schedule(ROOT,cls.plan)

    def test_full_original_denominator_and_exact_slots(self):
        a=self.report
        self.assertEqual(a["original_task_denominator"],36)
        self.assertEqual(a["candidate_slots_all"],108)
        self.assertEqual(a["source_available_nonrunnable_slots"],90)
        self.assertEqual(a["missing_source_blocked_slots"],18)
        self.assertEqual(a["runnable_slots"],0)
        self.assertFalse(a["approved_for_preregistration"])
        self.assertFalse(a["model_launch_allowed"])
        self.assertEqual(a["live_provider_calls"],0)
        self.assertEqual(a["official_tasks_scored"],0)

    def test_balanced_first_second_third_positions_whole_cohort(self):
        self.assertEqual(
            self.report["arm_order_by_position"],
            {arm:[12,12,12] for arm in THREE_ARM_DRAFT}
        )
        by_task={}
        for row in self.report["candidate_slots"]:
            by_task.setdefault(row["task_id"],[]).append(row)
        self.assertEqual(len(by_task),36)
        for tid,slots in by_task.items():
            with self.subTest(task=tid):
                self.assertEqual(len(slots),3)
                self.assertEqual(set(s["arm"] for s in slots),set(THREE_ARM_DRAFT))
                self.assertEqual(set(s["order_position"] for s in slots),{0,1,2})
                self.assertEqual(len(set(s["source_sha256"] for s in slots)),1)
                self.assertTrue(all(s["trial_launch_allowed"] is False for s in slots))

    def test_repeated_scheduling_is_stable_not_random_provider_or_benchmark(self):
        again=three_arm_candidate_schedule(ROOT,self.plan)
        self.assertEqual(again,self.report)
        self.assertEqual(len({s["candidate_slot_id"]
                              for s in self.report["candidate_slots"]}),108)
        self.assertTrue(all(s["candidate_slot_id"].startswith("candidate-")
                            for s in self.report["candidate_slots"]))

    def test_two_arm_api_stays_unchanged(self):
        self.assertEqual(ARMS,("direct_xml","imperative_python"))
        self.assertEqual(len(paired_schedule(
            [{"task_id":"SYNTHETIC-TASK"}],(11,),"synthetic-v0","a"*64,
        )),2)
        with self.assertRaises(Exception):
            make_run_id("synthetic","SYNTHETIC","D_FULL",11,0,"a"*64)

    def test_all_inputs_blocked_by_study_even_if_cached(self):
        a=self.report
        statuses={r["status"] for r in a["candidate_slots"]}
        self.assertEqual(statuses,{
            "SOURCE_AVAILABLE_STUDY_BLOCKED",
            "ORIGINAL_INPUT_ABSENT_BLOCKED",
        })
        self.assertIsNone(a["actual_provider_input_tokens"])
        self.assertIsNone(a["actual_provider_output_tokens"])
        self.assertFalse(a["verified_model_tokenizer"])
        self.assertFalse(a["provider_usage_receipt_verified"])
        self.assertFalse(a["D_full_native_coverage_verified"])
        self.assertFalse(a["D_full_vs_managed_treatment_difference_verified"])
        self.assertFalse(a["actual_live_tool_feedback_parity_verified"])

    def test_original_old_plan_cohort_and_parity_hash_are_preserved(self):
        self.assertEqual(
            sha256((ROOT/"configs/pilot_36_plan_v0.json").read_bytes()).hexdigest(),
            self.plan["original_two_arm_plan_sha256"]
        )
        self.assertEqual(
            sha256((ROOT/"manifests/pilot_36_candidate_v0.json").read_bytes()).hexdigest(),
            self.plan["original_36_task_pilot_sha256"]
        )
        self.assertEqual(
            sha256((ROOT/"reports/g3_bim_edit_36_task_information_and_tool_parity_20261119.json").read_bytes()).hexdigest(),
            self.plan["original_g3_source_differential_sha256"]
        )

    def test_changed_model_visible_arm_docs_refuse_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            forged=Path(temp)/"forged.md"
            forged.write_text("This is not the real XML language or I API notes.",encoding="utf8")
            for module_path in (
                "src.direct_markup.agent_runner.LANGUAGE_SPEC",
                "src.imperative_control.agent_runner.API_NOTES",
            ):
                with self.subTest(module=module_path),patch(module_path,forged):
                    with self.assertRaisesRegex(ThreeArmDraftBlocked,"documentation"):
                        validate_three_arm_candidate(ROOT,self.plan)

    def test_exact_shared_one_shot_bounds_and_imperative_extra_notes_disclosed(self):
        validation=validate_three_arm_candidate(ROOT,self.plan)
        self.assertEqual(len(validation["selected"]),36)
        self.assertEqual(len(validation["audited"]),25)
        self.assertEqual(self.plan["shared_limits"],{
            "max_attempts_per_task_arm":1,"max_wall_seconds_per_task_arm":180,
            "max_submission_utf8_bytes":32768,"max_model_input_tokens_per_attempt":20000,
            "max_model_output_tokens_per_attempt":6000,"max_model_authored_submissions":1,
            "feedback_rounds":0,"max_concurrent_model_calls":1,
        })
        self.assertNotEqual(
            self.plan["arm_contracts"]["D_FULL"]["authoring"],
            self.plan["arm_contracts"]["I_NATIVE"]["authoring"]
        )
        self.assertNotEqual(
            self.plan["arm_contracts"]["D_FULL"]["api_guidance"],
            self.plan["arm_contracts"]["I_NATIVE"]["api_guidance"]
        )

    def test_swapping_contract_versions_or_approvals_fails_closed(self):
        attacks=(
            ("silent_2arm_rename",("arms",),["D_FULL","I_NATIVE"]),
            ("duplicate_arm",("arms",),["D_FULL","D_FULL","I_NATIVE"]),
            ("pretend_registration",("status",),"REGISTERED"),
            ("fake_tokenizer",("provider","verified_exact_tokenizer_revision"),"fake"),
            ("fake_receipt",("provider","provider_usage_receipts"),True),
            ("paid_models",("provider","paid_calls_enabled"),True),
            ("fake_licensing",("provider","external_IFC_transfer_approved"),True),
            ("over_budget",("shared_limits","max_model_input_tokens_per_attempt"),30000),
            ("too_many_tries",("shared_limits","max_attempts_per_task_arm"),3),
            ("feedback_enabled",("shared_limits","feedback_rounds"),1),
            ("fake_d_full_done",("arm_contracts","D_FULL","native_capability"),"VERIFIED_FULL"),
            ("fake_d_managed_done",("arm_contracts","D_MANAGED","tool_status"),"APPROVED"),
            ("model_exec",("execution","model_generated_code_enabled"),True),
            ("reduced_denominator",("execution","dataset_original_tasks"),30),
            ("missing_zeroed",("execution","missing_input_rows"),0),
            ("asymmetric_seed",("randomized_order","seed"),99),
        )
        for name,path,value in attacks:
            with self.subTest(attack=name):
                data=deepcopy(self.plan)
                ref=data
                for key in path[:-1]:
                    ref=ref[key]
                ref[path[-1]]=value
                with self.assertRaises(ThreeArmDraftBlocked):
                    validate_three_arm_candidate(ROOT,data)

    def test_invalid_synthetic_tool_actions_and_feedback_never_accepted(self):
        actions={"D_FULL":"edit_xml","D_MANAGED":"edit_xml",
                 "I_NATIVE":"submit_python_text"}
        for arm,action in actions.items():
            with self.subTest(arm=arm):
                good=[{"action":action,"payload_bytes":32768,"feedback_round":0}]
                result=validate_synthetic_one_shot_trace(arm,good)
                self.assertEqual(result["provider_calls"],0)
                self.assertFalse(result["real_tool_runtime_verified"])
                for bad in (
                    [],good*2,
                    [{"action":"run_python","payload_bytes":1,"feedback_round":0}],
                    [{"action":action,"payload_bytes":32769,"feedback_round":0}],
                    [{"action":action,"payload_bytes":0,"feedback_round":0}],
                    [{"action":action,"payload_bytes":True,"feedback_round":0}],
                    [{"action":action,"payload_bytes":1,"feedback_round":1}],
                    [{"action":action,"payload_bytes":1,"feedback_round":True}],
                    [{"action":action,"payload_bytes":1,"feedback_round":0,"secret":"GT"}],
                ):
                    with self.assertRaises(ThreeArmDraftBlocked):
                        validate_synthetic_one_shot_trace(arm,bad)

    def test_synthetic_token_ceiling_boundary_no_real_model_usage(self):
        for count in ((1,0),(20000,6000),(20000,0)):
            a=validate_synthetic_token_ceiling(input_tokens=count[0],
                                               output_tokens=count[1])
            self.assertIsNone(a["real_provider_usage_receipt"])
            self.assertFalse(a["true_provider_token_count_verified"])
            self.assertEqual(a["provider_calls"],0)
        for left,right in (
            (20001,0),(1,6001),(0,1),(-1,1),(True,1),
            (1,False),(1,6000.5),("123",1)
        ):
            with self.subTest(input=left,output=right),self.assertRaises(ThreeArmDraftBlocked):
                validate_synthetic_token_ceiling(input_tokens=left,output_tokens=right)

    def test_proposed_evidence_replays_and_is_not_an_approved_study(self):
        if not EVIDENCE.is_file():
            self.skipTest("New report not yet written")
        raw=EVIDENCE.read_bytes()
        self.assertNotIn(b"\r\n",raw)
        self.assertEqual(sha256(raw).hexdigest(),
                         "c47e9222e3d533c7771ab49e3fc1a237a6344a9c7835c28e8ed8594090a58707")
        self.assertEqual(json.loads(raw),self.report)
        self.assertEqual(self.report["runnable_slots"],0)
        self.assertEqual(self.report["live_provider_calls"],0)


if __name__=="__main__":
    unittest.main()
