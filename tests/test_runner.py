"""Offline 2-task×2-arm×2-seed orchestration, integrity and strict block gates."""
from __future__ import annotations

import copy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import jsonschema

from src.runner.offline import (
    load_offline_configuration,read_mock_task_list,run_mock_schedule,
    OfflineRunError,OFFLINE_STATUS,RUN_SCHEMA_PATH
)
from src.runner.manifest import (
    paired_schedule,make_run_id,RunManifestError,read_existing
)
from src.runner.costs import (
    enforce_offline_budget,make_offline_cost_record,TrialBudgetError,
)

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/"tests/fixtures/synthetic/input.ifc"
SAMPLE=ROOT/"configs/experiment.sample.yaml"
TASKS=ROOT/"tests/fixtures/offline_two_tasks.json"
SHA=sha256(FIXTURE.read_bytes()).hexdigest()
SCHEMA=json.loads(RUN_SCHEMA_PATH.read_text())


class OfflineRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks=read_mock_task_list(TASKS)
        cls.config=load_offline_configuration(SAMPLE)

    def run_schedule(self,path,*,config=None,attempt=0,resume=False,
                     arm="both",seeds=(11,29),clock=None):
        kwargs=dict(
            source_ifc=FIXTURE,tasks=self.tasks,
            config=config or self.config,output_root=path,
            seeds=seeds,shuffle_seed=1234,
            arm_filter=arm,attempt=attempt,resume=resume,
        )
        if clock is not None:
            kwargs["clock"]=clock
        return run_mock_schedule(**kwargs)

    def test_two_by_two_by_two_eight_unique_immutable_records(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            result=self.run_schedule(root)
            self.assertEqual(result["created"],8)
            self.assertEqual(result["total_slots"],8)
            self.assertEqual(result["official_benchmark_tasks_scored"],0)
            self.assertEqual(result["provider_model_calls"],0)
            self.assertTrue(result["model_context_hash_matched_per_task_seed"])
            self.assertEqual(result["statuses"],{OFFLINE_STATUS:8})
            self.assertEqual(len(set(result["manifest_ids"])),8)
            self.assertEqual(len(list(root.glob("manifests/*.json"))),8)
            self.assertEqual(len(list(root.glob("trials/*/raw_model_response.json"))),8)
            for slot in result["planned_order"]:
                rec=read_existing(root/"manifests",slot["run_id"])
                jsonschema.validate(rec,SCHEMA)
                self.assertEqual(rec["input_sha"],SHA)
                self.assertIsNone(rec["result_sha"])
                self.assertIsNone(rec["metrics_ref"])
                self.assertEqual(rec["llm_calls"],0)
                self.assertFalse(rec["OS_isolation_verified"])
                self.assertFalse(rec["paid_pilot_authorized"])
                self.assertFalse(rec["python_code_executed"])
                self.assertFalse(rec["trusted_compiler_executed"])
                self.assertFalse(rec["independent_grader_executed"])
                self.assertIsNone(rec["cost"]["reported_input_tokens"])
                self.assertIsNone(rec["cost"]["actual_provider_charge_usd"])
                self.assertEqual(rec["cost"]["estimated_usd"],"0.00")
                response=(root/rec["artifact_refs"]["raw_response"]).read_bytes()
                self.assertEqual(sha256(response).hexdigest(),rec["raw_response_sha256"])
                self.assertFalse(json.loads(response)["is_real_llm_response"])
            self.assertEqual(SHA,sha256(FIXTURE.read_bytes()).hexdigest())

    def test_each_pair_gets_identical_model_information_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            result=self.run_schedule(root)
            for task in self.tasks:
                for seed in (11,29):
                    records=[read_existing(root/"manifests",slot["run_id"])
                             for slot in result["planned_order"]
                             if slot["task_id"]==task["task_id"] and slot["seed"]==seed]
                    self.assertEqual({r["arm"] for r in records},
                        {"direct_xml","imperative_python"})
                    self.assertEqual(len({r["model_input_sha256"] for r in records}),1)
                    self.assertEqual(len({r["input_sha"] for r in records}),1)
                    self.assertEqual(len({r["max_attempts"] for r in records}),1)

    def test_reproducible_arm_order_and_unique_run_ids(self):
        first=paired_schedule(self.tasks,(11,29),"g2-offline-pairing-v0",SHA,
                              shuffle_seed=1234)
        self.assertEqual(first,paired_schedule(self.tasks,(29,11),
                            "g2-offline-pairing-v0",SHA,shuffle_seed=1234))
        self.assertEqual(len(first),8)
        self.assertEqual(len({x.run_id for x in first}),8)
        groups={}
        for x in first:
            groups.setdefault((x.task_id,x.seed),[]).append(x.arm)
        self.assertEqual(len(groups),4)
        self.assertTrue(all(set(x)=={"direct_xml","imperative_python"}
                            for x in groups.values()))
        # Two distinct presentation orders occur across the four pairs.
        self.assertEqual(len({tuple(x) for x in groups.values()}),2)
        reverse=paired_schedule(self.tasks,(11,29),"g2-offline-pairing-v0",SHA,
                                shuffle_seed=1235)
        self.assertEqual({x.run_id for x in first},{x.run_id for x in reverse})
        self.assertNotEqual([x.arm for x in first],[x.arm for x in reverse])

    def test_resume_is_idempotent_and_no_original_trace_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            original=self.run_schedule(root)
            paths=list(root.glob("manifests/*.json"))
            checksums={str(p):sha256(p.read_bytes()).hexdigest() for p in paths}
            with self.assertRaises(RunManifestError):
                self.run_schedule(root)
            resumed=self.run_schedule(root,resume=True)
            self.assertEqual(resumed["created"],0)
            self.assertEqual(resumed["skipped_unchanged"],8)
            self.assertEqual(original["manifest_ids"],resumed["manifest_ids"])
            self.assertEqual({str(p):sha256(p.read_bytes()).hexdigest()
                              for p in paths},checksums)

    def test_new_attempt_id_not_allowed_without_larger_attempt_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            first=self.run_schedule(root,seeds=(11,),arm="direct_xml")
            with self.assertRaisesRegex(OfflineRunError,"retry budget"):
                self.run_schedule(root,seeds=(11,),arm="direct_xml",attempt=1)
            custom=dict(self.config,max_attempts_per_task=2)
            second=self.run_schedule(root,config=custom,seeds=(11,),
                                     arm="direct_xml",attempt=1)
            self.assertEqual(second["created"],2)
            self.assertTrue(set(first["manifest_ids"]).isdisjoint(second["manifest_ids"]))
            self.assertEqual(len(list(root.glob("manifests/*.json"))),4)

    def test_resume_rejects_modified_artifacts_or_model_context(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            result=self.run_schedule(root,seeds=(11,),arm="direct_xml")
            manifest=read_existing(root/"manifests",result["manifest_ids"][0])
            artifact=root/manifest["artifact_refs"]["model_context"]
            artifact.write_bytes(artifact.read_bytes()+b"\n")
            with self.assertRaisesRegex(RunManifestError,"hash mismatch"):
                self.run_schedule(root,seeds=(11,),arm="direct_xml",resume=True)

        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            self.run_schedule(root,seeds=(11,),arm="direct_xml")
            changed_task=copy.deepcopy(self.tasks)
            changed_task[0]["instruction"]="Changed the registered task after first run"
            with self.assertRaisesRegex(RunManifestError,"changed prompt, context"):
                run_mock_schedule(
                    source_ifc=FIXTURE,tasks=changed_task,config=self.config,
                    output_root=root,seeds=(11,),shuffle_seed=1234,
                    arm_filter="direct_xml",resume=True,
                )

    def test_resume_rejects_changed_budget_or_model_config(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            self.run_schedule(root,seeds=(11,),arm="imperative_python")
            changed=dict(self.config,max_input_tokens_per_attempt=18000)
            with self.assertRaisesRegex(RunManifestError,"changed prompt, context"):
                self.run_schedule(root,config=changed,seeds=(11,),
                                  arm="imperative_python",resume=True)

    def test_token_cap_exceeded_records_explicit_blocked_trial(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            custom=dict(self.config,max_input_tokens_per_attempt=1)
            result=self.run_schedule(root,config=custom,seeds=(11,),arm="direct_xml")
            self.assertEqual(result["created"],2)
            self.assertEqual(result["statuses"],{"BLOCKED_TOKEN_BUDGET":2})
            for name in result["manifest_ids"]:
                record=read_existing(root/"manifests",name)
                self.assertEqual(record["failures"],["ESTIMATED_INPUT_TOKENS_EXCEED_CAP"])
                self.assertEqual(record["llm_calls"],0)
                self.assertIsNone(record["result_sha"])

    def test_wall_clock_cutoff_records_blocked_status(self):
        class SimulatedClock:
            def __init__(self):
                self.ticks=0
            def __call__(self):
                self.ticks+=1
                return (self.ticks-1)*200
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            result=self.run_schedule(root,seeds=(11,),arm="direct_xml",
                                     clock=SimulatedClock())
            self.assertEqual(result["statuses"],{"BLOCKED_WALL_TIME":2})
            self.assertEqual(result["created"],2)
            records=[read_existing(root/"manifests",name)
                     for name in result["manifest_ids"]]
            self.assertTrue(all(r["failures"]==["MOCK_TIME_BUDGET_EXCEEDED"]
                                for r in records))

    def test_paid_provider_and_unsafe_config_rejected(self):
        bad_configs=(
            {"model_id":"gpt-6"},
            {"provider":"openai"},
            {"maximum_total_spend_usd":"5.00"},
            {"actual_provider_spend_authorized":True},
            {"max_concurrent_attempts":2},
            {"provider_seed_supported":True},
            {"model_temperature":0.8},
            {"required_g1_release_status":"ignore"},
        )
        import yaml
        for diff in bad_configs:
            with self.subTest(diff=diff),tempfile.TemporaryDirectory() as temp:
                path=Path(temp)/"config.yaml"
                path.write_text(yaml.safe_dump(dict(self.config,**diff)))
                with self.assertRaises((OfflineRunError,TrialBudgetError)):
                    load_offline_configuration(path)
        with tempfile.TemporaryDirectory() as temp:
            config=dict(self.config,model_id="gpt-6")
            with self.assertRaises((OfflineRunError,TrialBudgetError)):
                self.run_schedule(Path(temp),config=config)
            self.assertEqual(list(Path(temp).iterdir()),[])

    def test_gt_or_duplicate_tasks_never_enter_run_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"raw.json"
            hidden=[dict(self.tasks[0],ground_truth_ifc="hidden.ifc")]
            path.write_text(json.dumps(hidden))
            with self.assertRaises(Exception):
                read_mock_task_list(path)
            path.write_text(json.dumps([self.tasks[0],self.tasks[0]]))
            with self.assertRaisesRegex(OfflineRunError,"Duplicate"):
                read_mock_task_list(path)
            self.assertFalse((Path(temp)/"manifests").exists())

    def test_missing_source_and_unsafe_paths_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with self.assertRaises(Exception):
                run_mock_schedule(source_ifc=root/"none.ifc",tasks=self.tasks,
                                  config=self.config,output_root=root,
                                  seeds=(11,))
            with self.assertRaises(OfflineRunError):
                self.run_schedule(Path("relative/output"))
            self.assertEqual(list(root.iterdir()),[])

    def test_mock_cost_has_estimates_without_claiming_provider_usage(self):
        record=make_offline_cost_record("offline/mock-v0",5000,100)
        self.assertFalse(record.paid_model_called)
        self.assertEqual(record.estimated_input_tokens,5000)
        self.assertIsNone(record.reported_input_tokens)
        self.assertIsNone(record.actual_provider_charge_usd)
        with self.assertRaises(TrialBudgetError):
            make_offline_cost_record("gpt-6",500,100)
        with self.assertRaises(TrialBudgetError):
            enforce_offline_budget(maximum_total_spend_usd="0.001",
                                   max_attempts=1,max_wall_seconds=30,
                                   max_input_tokens=1000,max_output_tokens=100,
                                   model_id="offline/mock-v0")


class OfflineCLITests(unittest.TestCase):
    def _cli(self,*args):
        return subprocess.run([sys.executable,"-m","src.runner.cli",*map(str,args)],
                              cwd=ROOT,capture_output=True,text=True,timeout=15)

    def test_doctor_and_official_scorer_blocked(self):
        doctor=self._cli("doctor","--enforce")
        self.assertEqual(doctor.returncode,2)
        self.assertEqual(json.loads(doctor.stdout)["status"],"BLOCKED_FOR_LIVE_PILOT")
        scorer=self._cli("score")
        self.assertEqual(scorer.returncode,2)
        self.assertIsNone(json.loads(scorer.stdout)["score"])

    def test_mock_run_without_flag_refuses_model_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            result=self._cli("run","--output-root",temp,"--model","gpt-6")
            self.assertEqual(result.returncode,2)
            self.assertEqual(json.loads(result.stdout)["model_api_calls"],0)
            self.assertEqual(list(Path(temp).iterdir()),[])

    def test_validate_run_report_integrity_and_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            env=Path(temp)
            self.assertEqual(self._cli("validate-data").returncode,0)
            create=self._cli("run","--offline-mock","--output-root",env)
            self.assertEqual(create.returncode,0,create.stderr+create.stdout)
            self.assertEqual(json.loads(create.stdout)["created"],8)
            report=self._cli("report","--output-root",env)
            self.assertEqual(report.returncode,0,report.stderr+report.stdout)
            self.assertEqual(json.loads(report.stdout)["total_records"],8)
            one=sorted(env.glob("trials/*/raw_model_response.json"))[0]
            one.write_text('{"unsafe":"changed"}')
            bad=self._cli("report","--output-root",env)
            self.assertEqual(bad.returncode,2)
            self.assertEqual(json.loads(bad.stdout)["status"],"BLOCKED_OR_INVALID")

    def test_new_attempt_never_silently_overwrites_original(self):
        with tempfile.TemporaryDirectory() as temp:
            env=Path(temp)
            initial=self._cli("run","--offline-mock","--output-root",env)
            self.assertEqual(initial.returncode,0)
            repeated=self._cli("run","--offline-mock","--output-root",env)
            self.assertEqual(repeated.returncode,2)
            continued=self._cli("run","--offline-mock","--output-root",env,"--resume")
            self.assertEqual(continued.returncode,0)
            self.assertEqual(json.loads(continued.stdout)["created"],0)

if __name__=="__main__":
    unittest.main()
