"""G0 #3 pinned remaining-pilot data accounting without any downloader."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from src.data.bim_edit import AuditError
from src.data.remaining_pilot_gate import build_remaining_gate,summarize_remaining,ROOT
from tools.cache_small_pilot_ifcs import MAX_LOCAL_BATCH_BYTES


class RemainingGateTests(unittest.TestCase):
    def test_shared_pair_is_deduplicated_across_tasks(self):
        pairs=[
            ("T1","create","IfcWall",{"i","g"}),
            ("T2","create","IfcWall",{"i","g"}),
            ("T3","update","IfcSlab",{"u","v"}),
        ]
        result=summarize_remaining(pairs,
                                 {"i":40,"g":60,"u":40,"v":80},
                                 {"i","g","u","v"})
        self.assertEqual(result["remaining_task_count"],3)
        self.assertEqual(result["remaining_unique_file_count"],4)
        self.assertEqual(result["remaining_unique_bytes"],220)
        self.assertEqual(result["smallest_task_incremental_bytes"],100)

    def test_bad_remote_bytes_refused(self):
        pairs=[("T1","create","IfcWall",{"i","g"})]
        for meta in ({"i":1},{"i":1,"g":0},{"i":1,"g":2.5}):
            with self.subTest(meta=meta),self.assertRaises(AuditError):
                summarize_remaining(pairs,meta,{"i","g"})

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").exists(),"Pinned metadata not cached")
    def test_real_frozen_36_reports_exact_gap_no_gt_names(self):
        outcome=build_remaining_gate()
        self.assertEqual(outcome["fixed_sample_size"],36)
        self.assertEqual(outcome["byte_verified_task_input_reference_pair_count"],30)
        self.assertEqual(outcome["missing_task_count"],6)
        self.assertEqual(outcome["unique_missing_asset_count"],10)
        self.assertEqual(outcome["unique_missing_bytes"],1476908702)
        self.assertEqual(outcome["smallest_remaining_pair_bytes"],94044329)
        self.assertFalse(outcome["any_remaining_pair_fits_existing_batch"])
        self.assertEqual(outcome["max_existing_bounded_batch_bytes"],50000000)
        self.assertFalse(outcome["individual_asset_redistribution_clearance_complete"])
        self.assertFalse(outcome["download_performed"])
        self.assertEqual(outcome["official_tasks_scored"],0)
        self.assertEqual(outcome["paid_model_calls"],0)
        published=json.dumps(outcome)
        for string in ('ground_truth_ifc','input_ifc','data/realistic',
                       'simple/','complex/','/grader/','target_guids','prompt'):
            self.assertNotIn(string,published)

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").exists(),"Pinned metadata not cached")
    def test_corrupted_candidate_rejected_before_any_download(self):
        candidate=ROOT/"manifests/pilot_36_candidate_v0.json"
        with TemporaryDirectory() as tmp:
            corrupt=Path(tmp)/"candidate.json"
            row=json.loads(candidate.read_text(encoding="utf-8"))
            row["tasks"]=row["tasks"][:-1]
            corrupt.write_text(json.dumps(row),encoding="utf-8")
            with self.assertRaises(AuditError):
                build_remaining_gate(candidate_path=corrupt)

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").exists(),"Pinned metadata not cached")
    def test_cached_asset_tamper_refused_before_gate(self):
        with patch("src.data.remaining_pilot_gate.verify_local_asset_bytes",
                   side_effect=AuditError("tampered")):
            with self.assertRaises(AuditError):
                build_remaining_gate()


if __name__=="__main__":
    unittest.main()
