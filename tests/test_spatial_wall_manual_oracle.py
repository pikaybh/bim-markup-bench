"""G1 #14: trusted manual D0/I0 geometry parity on frozen public input only."""
from __future__ import annotations

import hashlib
import json
import re
import unittest

import ifcopenshell

from src.data.bim_edit import read_tasks,repo_asset_path
from src.data.pilot_asset_audit import _files_in_root
from src.runtime.ifc_projection import project_ifc
from tools.verify_spatial_wall_manual_oracle import (
    ROOT,CASE,_geometry_from_public_instruction,_check_existing_native_relations_preserved,
    verify_one_spatial_wall_ceiling,
)

class SpatialWallManualOracleTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/"data/tasks.jsonl").is_file(),"Pinned public metadata missing")
    def test_frozen_source_manual_pair_has_equal_ifc_observation_not_official_score(self):
        result=verify_one_spatial_wall_ceiling()
        self.assertEqual(result["task_id"],CASE)
        self.assertEqual(result["status"],
                         "BLOCKED_FULL_TASK_TOPOLOGY_ORACLE_PENDING_AFTER_MANUAL_GEOMETRY_PARITY_PASS")
        self.assertTrue(result["native_IFC_parity"])
        self.assertTrue(result["critical_room_geometry_visible_in_xml"])
        self.assertTrue(result["prompt_room_visible_in_direct_markup"])
        self.assertFalse(result["all_input_information_equivalence_proven"])
        self.assertFalse(result["this_is_an_approved_full_task_oracle"])
        self.assertFalse(result["space_boundary_reconstruction_verified"])
        self.assertEqual(result["new_wall_bbox_min_m"],[0.175,5.23275,0.0])
        self.assertEqual(result["new_wall_bbox_max_m"],[4.625,5.40775,2.8])
        self.assertTrue(result["new_wall_storey_containment_verified"])
        self.assertTrue(result["existing_native_relations_preserved"])
        self.assertEqual(result["new_wall_storey_containment_updates"],1)
        self.assertEqual(result["new_wall_native_connects_count"],0)
        self.assertEqual(result["new_wall_native_space_boundary_count"],0)
        self.assertFalse(result["GT_loaded"])
        self.assertEqual(result["official_scores"],0)
        self.assertEqual(result["LLM_provider_calls"],0)
        self.assertFalse(result["new_IFC_files_committed"])
        self.assertFalse(result["fixed_task_sample_modified"])
        self.assertEqual(len(result["D0_sha256"]),64)
        self.assertEqual(len(result["I0_sha256"]),64)

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").is_file(),"Pinned public metadata missing")
    def test_nonpositive_wall_thickness_or_height_from_prompt_fail_closed(self):
        tasks={r["task_id"]:r for r in read_tasks(ROOT/"data/tasks.jsonl")}
        task=tasks[CASE]
        source=_files_in_root((ROOT/"data/ifc").resolve(),repo_asset_path(task["input_ifc"]))
        before=hashlib.sha256(source.read_bytes()).hexdigest()
        original=project_ifc(source)
        model=ifcopenshell.open(str(source))
        for text in (
            task["prompt"].replace("thickness of 0.175m","thickness of 0m"),
            task["prompt"].replace("height of 2.800m","height of 0m"),
        ):
            with self.subTest(prompt_changed=text!=task["prompt"]):
                self.assertNotEqual(text,task["prompt"])
                with self.assertRaisesRegex(ValueError,"Invalid task dimensions"):
                    _geometry_from_public_instruction({**task,"prompt":text},
                                                      model,original)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before)

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").is_file(),"Pinned public metadata missing")
    def test_missing_native_room_reference_does_not_fabricate_geometry(self):
        tasks={r["task_id"]:r for r in read_tasks(ROOT/"data/tasks.jsonl")}
        task=tasks[CASE]
        source=_files_in_root((ROOT/"data/ifc").resolve(),repo_asset_path(task["input_ifc"]))
        model=ifcopenshell.open(str(source))
        source_xml=project_ifc(source)
        refs=re.findall(r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",task["prompt"])
        self.assertEqual(len(refs),3)
        missing="0"*22
        with self.assertRaises(RuntimeError):
            model.by_guid(missing)
        bad=task["prompt"].replace(refs[2],missing)
        with self.assertRaisesRegex(ValueError,"absent native IFC entity"):
            _geometry_from_public_instruction({**task,"prompt":bad},model,source_xml)

    def test_native_relationship_guard_rejects_noncontainment_changes(self):
        original={
            "X":("IfcRelSpaceBoundary",("room",),("wall",)),
            "C":("IfcRelContainedInSpatialStructure",("storey",),("old",)),
        }
        allowed={
            **original,
            "NEW":("IfcRelContainedInSpatialStructure",("storey",),("created",)),
        }
        report=_check_existing_native_relations_preserved(
            original,allowed,new_wall_guid="created",storey_guid="storey")
        self.assertTrue(report["original_native_relations_preserved"])
        self.assertEqual(report["new_wall_storey_containment_updates"],1)
        broken={**allowed,"X":("IfcRelSpaceBoundary",("room",),("created",))}
        with self.assertRaisesRegex(ValueError,"Unrelated"):
            _check_existing_native_relations_preserved(
                original,broken,new_wall_guid="created",storey_guid="storey")
        with self.assertRaisesRegex(ValueError,"deleted"):
            _check_existing_native_relations_preserved(
                original,{"C":original["C"],"NEW":allowed["NEW"]},
                new_wall_guid="created",storey_guid="storey")
        with self.assertRaisesRegex(ValueError,"Unexpected"):
            _check_existing_native_relations_preserved(
                original,{**allowed,"BAD":("IfcRelVoidsElement",("wall",),("void",))},
                new_wall_guid="created",storey_guid="storey")

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").is_file(),"Pinned public metadata missing")
    def test_evidence_report_has_no_target_metadata_or_gt_file_reference(self):
        result=verify_one_spatial_wall_ceiling()
        payload=json.dumps(result,sort_keys=True)
        for forbidden in (
            '"ground_truth_ifc"', '"input_ifc"', "target_guids", "solution.py",
            "/grader/", "data/ifc", '"evaluation"', "OPENAI_API_KEY",
        ):
            self.assertNotIn(forbidden,payload)


if __name__=="__main__":
    unittest.main()
