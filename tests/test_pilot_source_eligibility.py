"""G1 #16 frozen pilot source predicates; no GT, IFC writes or model calls."""
from __future__ import annotations
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from src.data.bim_edit import AuditError
from tools.audit_pilot_source_eligibility import (
    ROOT,audit_frozen_pilot,_conditional_source_probe,
)


class FrozenPilotReadinessTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/"data/tasks.jsonl").is_file(),
                         "Pinned public metadata not available")
    def test_every_frozen_task_accounted_for_no_premature_success(self):
        r=audit_frozen_pilot()
        self.assertEqual(r["task_count"],36)
        self.assertEqual(r["static_unsupported_count"],23)
        self.assertEqual(r["source_conditionals_checked"],11)
        self.assertEqual(r["missing_conditional_source_count"],2)
        self.assertEqual(r["verified_official_d0_i0_task_oracles"],0)
        self.assertEqual(r["official_scores_computed"],0)
        self.assertEqual(r["paid_model_calls"],0)
        self.assertFalse(r["GT_file_loaded"])
        self.assertFalse(r["model_agent_exposed_to_target_metadata"])
        self.assertEqual(len({x["task_id"] for x in r["tasks"]}),36)
        self.assertTrue(all(x["paired_d0_i0_task_oracle_verified"] is False
                            for x in r["tasks"]))

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").is_file(),
                         "Pinned public metadata not available")
    def test_real_source_preconditions_distinct_from_missing_bytes(self):
        tasks={t["task_id"]:t for t in audit_frozen_pilot()["tasks"]}
        for tid,expected in (
            ("WAL-DEL-TOP-A-001","WALL_DELETE_SOURCE_DEPENDENCIES_BLOCKED"),
            ("WAL-UPD-DIR-R-003","WALL_THICKNESS_NATIVE_DEPENDENCIES_BLOCKED"),
            ("WIN-DEL-SPA-A-002","WINDOW_DELETE_NATIVE_RELATIONS_BLOCKED"),
            ("WIN-UPD-SPA-A-003","WINDOW_OPENING_DIMENSION_CHANGE_UNIMPLEMENTED"),
            ("WIN-UPD-DIR-A-002","WINDOW_MOVE_VECTOR_AND_PAIRED_ORACLE_NOT_PROVEN"),
            ("WAL-CRE-SPA-R-002","MISSING_PINNED_INPUT_IFC"),
        ):
            with self.subTest(task_id=tid):
                self.assertEqual(tasks[tid]["reason_code"],expected)
        self.assertEqual(tasks["WAL-CRE-SPA-A-003"]["reason_code"],
                         "WALL_CREATE_SPATIAL_ORACLE_NOT_PROVEN")

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").is_file(),
                         "Pinned public metadata not available")
    def test_sanitized_agent_proof_ledger_has_no_hidden_fields(self):
        r=audit_frozen_pilot()
        payload=json.dumps(r,sort_keys=True)
        for token in ("ground_truth_ifc","input_ifc","target_guids",
                      "GlobalId","prompt","solution.py","/grader/",
                      "complex/","simple/","data/ifc","OPENAI_API_KEY"):
            with self.subTest(token=token):
                self.assertNotIn(token,payload)

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").is_file(),
                         "Pinned public metadata not available")
    def test_modified_sample_is_rejected_not_resampled(self):
        current=json.loads((ROOT/"manifests/pilot_36_candidate_v0.json").read_text())
        with TemporaryDirectory() as folder:
            path=Path(folder)/"candidate.json"
            current["tasks"].pop()
            path.write_text(json.dumps(current),encoding="utf-8")
            with self.assertRaises(AuditError):
                audit_frozen_pilot(candidate_file=path)

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").is_file(),
                         "Pinned public metadata not available")
    def test_tampered_local_cached_bytes_fail_closed(self):
        with patch("tools.audit_pilot_source_eligibility.verify_local_asset_bytes",
                   side_effect=AuditError("OWN simulated corruption")):
            with self.assertRaises(AuditError):
                audit_frozen_pilot()

    def test_invalid_source_does_not_mark_conditional_success(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)/"bad_source.ifc"
            path.write_bytes(b"UNTRUSTED")
            result,projection=_conditional_source_probe(
                {"target":{"entity_type":"IfcWall","guids":[]},
                 "operation":"create","prompt":"Create a wall"},path)
        self.assertEqual(result,"SOURCE_NATIVE_PROBE_BLOCKED")
        self.assertIsNone(projection)


if __name__=="__main__":
    unittest.main()
