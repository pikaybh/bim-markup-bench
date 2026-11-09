"""Offline capped immutable public IFC downloader planning and security checks."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from src.data.bim_edit import AuditError,read_tasks
from tools.cache_small_pilot_ifcs import (
    MAX_LOCAL_BATCH_BYTES,ROOT,bounded_plan,fetch_verified
)

def git_blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+bytes((0,))+data).hexdigest()

class SmallPilotDownloadTests(unittest.TestCase):
    def test_fixed_public_manifest_planner_never_replaces_task_ids(self):
        if not (ROOT/"data/tasks.jsonl").exists():
            self.skipTest("Public pinned metadata not cached")
        records=read_tasks(ROOT/"data/tasks.jsonl")
        candidate=json.loads((ROOT/"manifests/pilot_36_candidate_v0.json").read_text())
        tree=json.loads((ROOT/"data/bim_edit_remote_tree.json").read_text())
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            budget=8_000_000
            planned=bounded_plan(records,candidate,tree,root,budget)
            self.assertGreaterEqual(len(planned["fixed_task_ids"]),11)
            self.assertLessEqual(planned["planned_download_bytes"],budget)
            self.assertEqual(planned["planned_download_file_count"],
                             len(planned["unique_missing_assets"]))
            self.assertEqual(len(planned["unique_missing_assets"]),
                             len(set(planned["unique_missing_assets"])))
            self.assertEqual(planned["status"],"PLAN_ONLY_NOT_A_BENCHMARK_RUN")
            ids={x["task_id"] for x in candidate["tasks"]}
            self.assertTrue(set(planned["fixed_task_ids"]).issubset(ids))

    def test_negative_and_unbounded_budget_rejected(self):
        with TemporaryDirectory() as tmp:
            for budget in (-1,MAX_LOCAL_BATCH_BYTES+1,1.25):
                with self.subTest(budget=budget),self.assertRaises(AuditError):
                    bounded_plan([],{"tasks":[]},[],Path(tmp),budget)

    def test_fake_pinned_bytes_success_only_from_approved_asset(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            content=b"FAKE_OWN_TEST_IFC_BYTES"
            remote=[{"path":"simple/known.ifc","type":"file",
                     "size":len(content),"oid":git_blob(content)}]
            plan={"unique_missing_assets":["simple/known.ifc"],
                  "planned_download_bytes":len(content)}
            with patch("tools.cache_small_pilot_ifcs.urllib.request.urlopen",
                       return_value=io.BytesIO(content)) as mocked:
                result=fetch_verified(plan,remote,root)
            self.assertEqual(result["downloaded_files"],1)
            self.assertEqual(result["downloaded_bytes"],len(content))
            self.assertFalse(result["GT_exposed_to_agent"])
            self.assertEqual((root/"simple/known.ifc").read_bytes(),content)
            self.assertEqual(len(list((root/"simple").glob("*.part"))),0)
            self.assertEqual(mocked.call_count,1)

    def test_tampered_or_oversize_content_never_published(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            correct=b"ABCD"
            remote=[{"path":"simple/known.ifc","type":"file",
                     "size":len(correct),"oid":git_blob(correct)}]
            plan={"unique_missing_assets":["simple/known.ifc"],
                  "planned_download_bytes":len(correct)}
            for attack in (b"AAAA",b"ABCDE"):
                with self.subTest(attack=attack):
                    with patch("tools.cache_small_pilot_ifcs.urllib.request.urlopen",
                               return_value=io.BytesIO(attack)):
                        with self.assertRaises(AuditError):
                            fetch_verified(plan,remote,root)
                    self.assertFalse((root/"simple/known.ifc").exists())
                    self.assertEqual(list((root/"simple").glob("*.part")),[])

    def test_existing_byte_invalidity_fails_closed(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/"simple";folder.mkdir()
            local=folder/"known.ifc";local.write_bytes(b"BAD!")
            good=b"GOOD"
            records=[{
                "task_id":"ONE","input_ifc":"data/artificial/known.ifc",
                "ground_truth_ifc":"data/artificial/known.ifc"
            }]
            candidate={"tasks":[{"task_id":"ONE"}]}
            remote=[{"path":"simple/known.ifc","type":"file",
                     "size":4,"oid":git_blob(good)}]
            with self.assertRaises(AuditError):
                bounded_plan(records,candidate,remote,root,10)

    def test_tampered_frozen_plan_budget_or_duplicate_fails_without_network(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            content=b"FAKE_BYTES"
            remote=[{"path":"simple/known.ifc","type":"file",
                     "size":len(content),"oid":git_blob(content)}]
            forged_plans=[
                {"unique_missing_assets":["simple/known.ifc"],
                 "planned_download_bytes":len(content)-1},
                {"unique_missing_assets":["simple/known.ifc"]*2,
                 "planned_download_bytes":len(content)*2},
                {"unique_missing_assets":["simple/unknown.ifc"],
                 "planned_download_bytes":1},
                {"unique_missing_assets":["simple/known.ifc"],
                 "planned_download_bytes":MAX_LOCAL_BATCH_BYTES+1},
            ]
            with patch("tools.cache_small_pilot_ifcs.urllib.request.urlopen") as request:
                for forged in forged_plans:
                    with self.subTest(plan=forged),self.assertRaises(AuditError):
                        fetch_verified(forged,remote,root)
                request.assert_not_called()
            self.assertFalse((root/"simple/known.ifc").exists())

    def test_cli_without_apply_does_not_download(self):
        if not (ROOT/"data/tasks.jsonl").exists():
            self.skipTest("Optional pinned public metadata absent")
        process=subprocess.run(
            [sys.executable,"-m","tools.cache_small_pilot_ifcs",
             "--limit-bytes","0"],
            cwd=ROOT,capture_output=True,text=True,timeout=20,
        )
        self.assertEqual(process.returncode,0,process.stderr)
        outcome=json.loads(process.stdout)
        self.assertFalse(outcome["apply_requested"])
        self.assertEqual(outcome["paid_model_calls"],0)
        self.assertEqual(outcome["official_tasks_scored"],0)
        self.assertEqual(outcome["planned_download_file_count"],0)

if __name__=="__main__":
    unittest.main()
