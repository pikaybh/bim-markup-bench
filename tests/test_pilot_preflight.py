"""G3-01 candidate integrity without model/API access or false readiness."""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools.pilot_preflight import (
    preflight,ROOT,CANDIDATE,CONFIG,DRAFT,PINNED,G2
)
from tools.prepare_pilot_candidate import select

PUBLIC_TASKS=ROOT/"data/tasks.jsonl"
PUBLIC_SHA="9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83"


def clone_json(path:Path,dest:Path,change):
    data=json.loads(path.read_text())
    change(data)
    dest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    return dest


class PilotCandidateAuditTests(unittest.TestCase):
    def test_actual_public_metadata_sha_and_deterministic_36_candidates(self):
        if not PUBLIC_TASKS.is_file():
            self.skipTest("Pinned optional public task metadata not cached")
        self.assertEqual(sha256(PUBLIC_TASKS.read_bytes()).hexdigest(),PUBLIC_SHA)
        expected=select(PUBLIC_TASKS)
        self.assertEqual(expected,json.loads(CANDIDATE.read_text()))
        self.assertEqual(expected["status"],"CANDIDATE_NOT_PREREGISTERED")
        self.assertEqual(expected["sample_size"],36)
        self.assertEqual(len(expected["tasks"]),36)
        self.assertEqual(sum(expected["class_counts"].values()),36)
        counts=Counter(
            (x["operation"],x["category"],x["scene"])
            for x in expected["tasks"]
        )
        self.assertEqual(len(counts),18)
        self.assertEqual(set(counts.values()),{2})

    def test_full_preflight_passes_candidate_only_and_blocks_live(self):
        audit=preflight()
        self.assertEqual(audit["candidate_integrity"],"PASS")
        self.assertEqual(audit["status"],"BLOCKED_NOT_A_RUNNABLE_PREREGISTRATION")
        self.assertEqual(audit["official_benchmark_tasks_scored"],0)
        self.assertEqual(audit["paid_model_calls"],0)
        self.assertEqual(audit["problems"],[])
        self.assertEqual(len(audit["unmet_release_requirements"]),8)
        self.assertTrue(audit["evidence"]["candidate_reproducible"])
        self.assertFalse(audit["evidence"]["per_task_IFC_GT_sha_verified"])
        self.assertFalse(audit["evidence"]["live_model_calls_permitted"])
        self.assertFalse(audit["evidence"]["api_keys_inspected"])
        self.assertEqual(audit["evidence"]["candidate_size"],36)
        self.assertEqual(audit["evidence"]["paired_arm_slots_per_repetition"],72)

    def test_injected_benchmark_gt_field_rejected_before_live(self):
        with TemporaryDirectory() as tmp:
            candidate=Path(tmp)/"candidate.json"
            def inject(data):
                data["tasks"][0]["ground_truth_ifc"]="hidden_gt.ifc"
            clone_json(CANDIDATE,candidate,inject)
            outcome=preflight(candidate=candidate)
            self.assertEqual(outcome["candidate_integrity"],"FAIL")
            self.assertIn("Candidate contains unapproved fields or hidden GT details",
                          outcome["problems"])
            self.assertEqual(outcome["paid_model_calls"],0)

    def test_candidate_task_swap_and_duplicate_are_rejected(self):
        with TemporaryDirectory() as tmp:
            candidate=Path(tmp)/"candidate.json"
            def replace(data):
                data["tasks"][0]["task_id"]="NOT_FROZEN_ID"
            clone_json(CANDIDATE,candidate,replace)
            outcome=preflight(candidate=candidate)
            self.assertEqual(outcome["candidate_integrity"],"FAIL")
            self.assertTrue(any("differ from frozen" in x for x in outcome["problems"]))
            def duplicate(data):
                data["tasks"][1]["task_id"]=data["tasks"][0]["task_id"]
            clone_json(CANDIDATE,candidate,duplicate)
            outcome=preflight(candidate=candidate)
            self.assertEqual(outcome["candidate_integrity"],"FAIL")
            self.assertTrue(any("36 unique" in x for x in outcome["problems"]))

    def test_public_metadata_sha_tamper_is_rejected(self):
        with TemporaryDirectory() as tmp:
            changed=Path(tmp)/"tasks.jsonl"
            changed.write_bytes(PUBLIC_TASKS.read_bytes()+b"\n")
            outcome=preflight(metadata=changed)
            self.assertEqual(outcome["candidate_integrity"],"FAIL")
            self.assertFalse(outcome["evidence"]["candidate_reproducible"])
            self.assertEqual(outcome["paid_model_calls"],0)

    def test_stale_or_unverified_provider_model_rejected(self):
        with TemporaryDirectory() as tmp:
            cfg=Path(tmp)/"plan.json"
            def invalid(data):
                data["model_id"]="gpt-6-luna"
                data["paid_calls_enabled"]=True
            clone_json(CONFIG,cfg,invalid)
            outcome=preflight(plan=cfg)
            self.assertEqual(outcome["candidate_integrity"],"FAIL")
            self.assertFalse(outcome["evidence"]["live_model_calls_permitted"])
            self.assertEqual(outcome["official_benchmark_tasks_scored"],0)

    def test_budget_approval_flag_cannot_bypass_scientific_gate(self):
        with TemporaryDirectory() as tmp:
            cfg=Path(tmp)/"plan.json"
            def approve(data):
                data["maximum_total_spend_usd_explicitly_authorized"]=True
            clone_json(CONFIG,cfg,approve)
            result=preflight(plan=cfg)
            self.assertEqual(result["candidate_integrity"],"FAIL")
            self.assertEqual(result["status"],"BLOCKED_NOT_A_RUNNABLE_PREREGISTRATION")
            self.assertEqual(result["paid_model_calls"],0)

    def test_unapproved_new_price_in_yaml_rejected(self):
        import yaml
        with TemporaryDirectory() as tmp:
            yaml_path=Path(tmp)/"experiment.yaml"
            data=yaml.safe_load(DRAFT.read_text())
            data["estimated_input_usd_per_million"]=0.10
            data["pilot_frozen"]=True
            yaml_path.write_text(yaml.safe_dump(data))
            result=preflight(protocol=yaml_path)
            self.assertEqual(result["candidate_integrity"],"FAIL")
            self.assertEqual(result["paid_model_calls"],0)

    def test_paired_attempt_time_and_token_budget_config_mismatch_blocked(self):
        with TemporaryDirectory() as tmp:
            cfg=Path(tmp)/"plan.json"
            def change(data):
                data["max_output_tokens_per_attempt"]=7000
                data["paired_trial_seeds"]=[11,29]
            clone_json(CONFIG,cfg,change)
            result=preflight(plan=cfg)
            self.assertEqual(result["candidate_integrity"],"FAIL")
            self.assertTrue(any("mismatch" in p.lower() for p in result["problems"]))

    def test_environment_key_presence_cannot_change_audit_or_trigger_calls(self):
        with patch.dict(os.environ,{"OPENAI_API_KEY":"fake_key_must_not_be_read"}):
            with_key=preflight()
        with patch.dict(os.environ,{"OPENAI_API_KEY":""}):
            without_key=preflight()
        self.assertEqual(with_key,without_key)
        self.assertFalse(with_key["evidence"]["api_keys_inspected"])

    def test_cli_intentionally_returns_two_without_any_model_calls(self):
        completed=subprocess.run(
            [sys.executable,"-m","tools.pilot_preflight"],
            cwd=ROOT,capture_output=True,text=True,timeout=18,
        )
        self.assertEqual(completed.returncode,2,completed.stderr)
        result=json.loads(completed.stdout)
        self.assertEqual(result["candidate_integrity"],"PASS")
        self.assertEqual(result["paid_model_calls"],0)
        self.assertEqual(result["official_benchmark_tasks_scored"],0)

    def test_no_fabricated_frozen_v1_manifest(self):
        self.assertFalse((ROOT/"manifests/pilot_tasks_v1.json").exists())
        self.assertFalse(json.loads(CONFIG.read_text())["paid_calls_enabled"])
        self.assertNotIn(
            "FROZEN_PREREGISTERED",json.loads(CANDIDATE.read_text())["status"]
        )

if __name__=="__main__":
    unittest.main()
