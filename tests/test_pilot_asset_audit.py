"""No-network data audit of pinned 36 candidate, plus tampered IFC negative cases."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell

from src.data.bim_edit import AuditError
from src.data.pilot_asset_audit import (
    audit_fixed_candidate,audit_single_task,
)
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference

ROOT=Path(__file__).resolve().parents[1]
OWN=ROOT/"tests/fixtures/synthetic/input.ifc"


def git_hash(raw:bytes)->str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()


def own_task(target_class="IfcWall"):
    return {
        "task_id":"OWN-CREATE-WALL-001",
        "operation":"create",
        "category":"spatial",
        "input_ifc":"data/artificial/sample_input.ifc",
        "ground_truth_ifc":"data/artificial/sample_gt.ifc",
        "target":{"entity_type":target_class,"guids":[]},
    }


def prepare_fake_assets(root:Path)->dict:
    simple=root/"simple"
    simple.mkdir()
    source=simple/"sample_input.ifc"
    gt=simple/"sample_gt.ifc"
    shutil.copyfile(OWN,source)
    f=ifcopenshell.open(str(OWN))
    storey=f.by_type("IfcBuildingStorey")[0].GlobalId
    manual_ifc_reference(
        OWN,gt,"CREATE_WALL",new_guid="1UXHdOzirKMwnUzfD_y3ME",
        storey_guid=storey
    )
    return {
        "simple/"+path.name:{
            "type":"file","path":"simple/"+path.name,
            "size":path.stat().st_size,"oid":git_hash(path.read_bytes())
        } for path in (source,gt)
    }


class OneTaskNativeAuditTests(unittest.TestCase):
    def test_owned_create_pair_genuine_bytes_and_native_delta(self):
        with TemporaryDirectory() as t:
            root=Path(t)
            tree=prepare_fake_assets(root)
            result=audit_single_task(own_task(),tree,root)
            self.assertEqual(result["status"],"VERIFIED_PINNED_BYTES_AND_CLASS_DELTA")
            self.assertTrue(result["input_bytes_verified"])
            self.assertTrue(result["reference_bytes_verified"])
            self.assertTrue(result["native_target_delta_verified"])
            self.assertEqual(result["created_target_class_count"],1)
            self.assertEqual(result["schema"],"IFC4X3")
            self.assertNotIn("sample_gt.ifc",json.dumps(result))
            self.assertNotIn("1UXHdOzirKMwnUzfD_y3ME",json.dumps(result))

    def test_missing_reference_never_marked_success(self):
        with TemporaryDirectory() as t:
            root=Path(t);tree=prepare_fake_assets(root)
            (root/"simple/sample_gt.ifc").unlink()
            result=audit_single_task(own_task(),tree,root)
            self.assertEqual(result["status"],"MISSING_LOCAL_IFC_BYTES")
            self.assertTrue(result["input_bytes_verified"])
            self.assertFalse(result["reference_bytes_verified"])
            self.assertFalse(result["native_target_delta_verified"])

    def test_modified_original_or_gt_detected_by_git_oid(self):
        for filename in ("sample_input.ifc","sample_gt.ifc"):
            with self.subTest(filename=filename),TemporaryDirectory() as t:
                root=Path(t);tree=prepare_fake_assets(root)
                file=root/"simple"/filename
                file.write_bytes(file.read_bytes()+b"INJECT")
                result=audit_single_task(own_task(),tree,root)
                self.assertEqual(result["status"],"BLOCKED_LOCAL_ASSET_DIGEST_MISMATCH")
                self.assertFalse(result["native_target_delta_verified"])

    def test_wrong_target_class_fails_native_delta(self):
        with TemporaryDirectory() as t:
            root=Path(t);tree=prepare_fake_assets(root)
            result=audit_single_task(own_task("IfcWindow"),tree,root)
            self.assertEqual(result["status"],"BLOCKED_CREATE_DELTA")
            self.assertFalse(result["native_target_delta_verified"])

    def test_symlinked_reference_is_rejected(self):
        with TemporaryDirectory() as t:
            root=Path(t);tree=prepare_fake_assets(root)
            p=root/"simple/sample_gt.ifc"
            real=root/"private_gt.ifc"
            p.rename(real)
            p.symlink_to(real)
            with self.assertRaises(AuditError):
                audit_single_task(own_task(),tree,root)

    def test_bad_ifc_with_matching_bytes_is_not_native_verified(self):
        with TemporaryDirectory() as t:
            root=Path(t);tree=prepare_fake_assets(root)
            bad=root/"simple/sample_gt.ifc"
            bad.write_bytes(b"NOT_AN_IFC")
            tree["simple/sample_gt.ifc"]["size"]=bad.stat().st_size
            tree["simple/sample_gt.ifc"]["oid"]=git_hash(bad.read_bytes())
            result=audit_single_task(own_task(),tree,root)
            self.assertEqual(result["status"],"BLOCKED_NATIVE_IFC_PARSE")
            self.assertFalse(result["native_target_delta_verified"])

    def test_update_without_a_real_observable_change_must_not_pass(self):
        with TemporaryDirectory() as t:
            root=Path(t);tree=prepare_fake_assets(root)
            shutil.copyfile(root/"simple/sample_input.ifc",
                            root/"simple/sample_gt.ifc")
            p=root/"simple/sample_gt.ifc"
            tree["simple/sample_gt.ifc"]["size"]=p.stat().st_size
            tree["simple/sample_gt.ifc"]["oid"]=git_hash(p.read_bytes())
            task=own_task()
            task["operation"]="update"
            task["target"]["guids"]=[
                ifcopenshell.open(str(OWN)).by_type("IfcWall")[0].GlobalId
            ]
            result=audit_single_task(task,tree,root)
            self.assertEqual(result["status"],"BLOCKED_UPDATE_DELTA_UNPROVEN")
            self.assertFalse(result["native_target_delta_verified"])

    def test_missing_model_asset_tree_entry_fails_closed(self):
        with TemporaryDirectory() as t:
            root=Path(t);tree=prepare_fake_assets(root)
            tree.pop("simple/sample_gt.ifc")
            self.assertEqual(
                audit_single_task(own_task(),tree,root)["status"],
                "BLOCKED_MISSING_PINNED_REMOTE_FILE"
            )


class PinnedPilotAssetAuditTests(unittest.TestCase):
    def test_all_36_missing_local_root_is_reported_not_scored(self):
        if not (ROOT/"data/tasks.jsonl").is_file():
            self.skipTest("Public pinned metadata is not locally cached")
        with TemporaryDirectory() as t:
            result=audit_fixed_candidate(
                task_file=ROOT/"data/tasks.jsonl",
                tree_file=ROOT/"data/bim_edit_remote_tree.json",
                local_root=Path(t),
            )
            self.assertEqual(result["total_candidate_tasks"],36)
            self.assertEqual(result["unique_referenced_assets"],52)
            self.assertEqual(result["estimated_unique_download_bytes"],1564261830)
            self.assertEqual(result["locally_verified_both_input_and_GT"],0)
            self.assertEqual(result["native_delta_verified_tasks"],0)
            self.assertFalse(result["full_324_IFC_content_audit_complete"])
            self.assertFalse(result["all_pilot_bytes_and_deltas_verified"])
            self.assertEqual(result["task_status_counts"],{"MISSING_LOCAL_IFC_BYTES":36})
            self.assertEqual(result["official_scores_computed"],0)
            self.assertEqual(result["paid_model_calls"],0)

    def test_six_classes_verified_from_small_pinned_public_pairs_when_cached(self):
        files=("01_gt.ifc","task002-delete-ground-truth.ifc",
               "task003-create-ground-truth.ifc",
               "task004-update-ground-truth.ifc",
               "task005-create-ground-truth.ifc",
               "task007-create-ground-truth.ifc")
        if not all((ROOT/"data/ifc/simple"/name).is_file() for name in files):
            self.skipTest("Six small public source/GT pairs not cached")
        result=audit_fixed_candidate(
            task_file=ROOT/"data/tasks.jsonl",
            tree_file=ROOT/"data/bim_edit_remote_tree.json",
            local_root=ROOT/"data/ifc"
        )
        self.assertEqual(result["native_delta_verified_tasks"],7)
        self.assertEqual(result["task_status_counts"],{
            "MISSING_LOCAL_IFC_BYTES":29,
            "VERIFIED_PINNED_BYTES_AND_CLASS_DELTA":7
        })
        kinds={x["target_class"] for x in result["tasks"]
               if x["native_target_delta_verified"]}
        self.assertEqual(kinds,{"IfcWall","IfcSlab","IfcSpace","IfcDoor",
                                "IfcWindow","IfcColumn"})
        self.assertFalse(result["all_pilot_bytes_and_deltas_verified"])
        self.assertEqual(result["official_scores_computed"],0)

    def test_local_single_pilot_case_is_verified_if_cached(self):
        expected=ROOT/"data/ifc/simple/01_gt.ifc"
        if not expected.is_file():
            self.skipTest("Optional real pinned public pilot IFC pair absent")
        result=audit_fixed_candidate(
            task_file=ROOT/"data/tasks.jsonl",
            tree_file=ROOT/"data/bim_edit_remote_tree.json",
            local_root=ROOT/"data/ifc"
        )
        self.assertGreaterEqual(result["native_delta_verified_tasks"],1)
        case=next(x for x in result["tasks"] if x["task_id"]=="WAL-CRE-SPA-A-003")
        self.assertTrue(case["native_target_delta_verified"])
        self.assertEqual(case["created_target_class_count"],1)
        self.assertEqual(result["status"],"BLOCKED_FULL_PILOT_ASSET_VERIFICATION")
        self.assertNotIn("ground_truth_ifc",json.dumps(result))
        self.assertNotIn("simple/01_gt.ifc",json.dumps(result))

if __name__=="__main__":unittest.main()
