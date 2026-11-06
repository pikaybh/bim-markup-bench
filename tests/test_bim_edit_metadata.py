import copy
import json
import unittest
from pathlib import Path

from src.data.bim_edit import AuditError, agent_view, read_tasks, repo_asset_path, validate_tasks, validate_remote_tree

ROOT = Path(__file__).resolve().parents[1]
GOOD = {
    "task_id": "WAL-UPD-DIR-R-999",
    "operation": "update",
    "category": "direct",
    "input_ifc": "data/realistic/example-input.ifc",
    "ground_truth_ifc": "data/realistic/example-gt.ifc",
    "prompt": "Change wall thickness to 0.30 m.",
    "target": {"entity_type": "IfcWall", "guids": ["0" * 22]},
    "evaluation": {},
    "tags": ["update", "IfcWall", "scene:R", "direct"]
}

class MetadataTests(unittest.TestCase):
    def test_safe_agent_payload_excludes_grader(self):
        p = agent_view(GOOD)
        self.assertEqual(p, {
            "task_id": GOOD["task_id"],
            "instruction": GOOD["prompt"],
            "input_file": "input.ifc",
        })
        for sensitive in ("target", "ground_truth_ifc", "evaluation", "input_ifc"):
            self.assertNotIn(sensitive, p)

    def test_metadata_path_alias(self):
        self.assertEqual(repo_asset_path(GOOD["input_ifc"]), "complex/example-input.ifc")
        self.assertEqual(repo_asset_path("data/artificial/01_input.ifc"), "simple/01_input.ifc")

    def test_bad_paths_fail_closed(self):
        for bad in ["data/realistic/foo.ifc.ifc", "../model.ifc", "data/realistic/../../secret.ifc", "/etc/passwd", "data/complex/foo.ifc", "data/artificial/foo.IFC"]:
            with self.subTest(bad=bad), self.assertRaises(AuditError):
                repo_asset_path(bad)

    def test_single_good_record(self):
        s = validate_tasks([GOOD], full=False)
        self.assertEqual(s["record_count"], 1)
        self.assertEqual(s["unique_referenced_ifc_assets"], 2)

    def test_duplicate_or_missing_id_fails(self):
        with self.assertRaisesRegex(AuditError, "duplicate"):
            validate_tasks([GOOD, GOOD], full=False)

    def test_guid_count_and_chars(self):
        for broken in ({"entity_type": "IfcWall", "guids": []}, {"entity_type": "IfcWall", "guids": ["BAD_GUID"]}):
            row = copy.deepcopy(GOOD)
            row["target"] = broken
            with self.assertRaises(AuditError):
                validate_tasks([row], full=False)

    def test_missing_or_unexpected_scene(self):
        row = copy.deepcopy(GOOD)
        row["tags"] = ["update", "IfcWall"]
        with self.assertRaisesRegex(AuditError, "scene"):
            validate_tasks([row], full=False)

    def test_missing_remote_asset_fails(self):
        with self.assertRaises(AuditError):
            validate_remote_tree([GOOD], [])  # missing input and GT, strict

    def test_real_pinned_dataset_if_cached(self):
        raw = ROOT / "data/tasks.jsonl"
        if not raw.exists():
            self.skipTest("Public task JSONL is gitignored; rerun metadata-only fetch for full audit")
        rows = read_tasks(raw)
        import jsonschema
        schema = json.loads((ROOT / "schemas/task_manifest.schema.json").read_text())
        checker = jsonschema.Draft202012Validator(schema)
        for row in rows:
            self.assertEqual(list(checker.iter_errors(row)), [], row["task_id"])
        meta = validate_tasks(rows)
        self.assertEqual(meta["record_count"], 324)
        self.assertEqual(meta["unique_referenced_ifc_assets"], 148)

if __name__ == "__main__":
    unittest.main()

class LocalByteVerificationTests(unittest.TestCase):
    def test_lfs_sha256_checked(self):
        import hashlib, tempfile
        from src.data.bim_edit import verify_local_asset_bytes
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"tiny.ifc"
            data=b"ISO-10303-21;\nEND-ISO-10303-21;"
            path.write_bytes(data)
            entry={"type":"file","size":len(data),"lfs":{"oid":hashlib.sha256(data).hexdigest()}}
            result=verify_local_asset_bytes(path,entry)
            self.assertTrue(result["content_sha256_verified"])
            entry["lfs"]["oid"] = "0"*64
            with self.assertRaisesRegex(AuditError,"SHA256"):
                verify_local_asset_bytes(path,entry)

    def test_git_blob_sha1_checked(self):
        import hashlib, tempfile
        from src.data.bim_edit import verify_local_asset_bytes
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"tiny.ifc"
            data=b"SMALL_GIT_BLOB"
            path.write_bytes(data)
            blob=hashlib.sha1(("blob "+str(len(data))+"\0").encode()+data).hexdigest()
            entry={"type":"file","size":len(data),"oid":blob}
            self.assertTrue(verify_local_asset_bytes(path,entry)["git_blob_sha1_verified"])
            entry["size"]=len(data)+1
            with self.assertRaisesRegex(AuditError,"size"):
                verify_local_asset_bytes(path,entry)

class RealOneFileAssetTests(unittest.TestCase):
    def test_small_real_ifc_when_cached(self):
        p=ROOT/"data/ifc/simple/17_input.ifc"
        tree=ROOT/"data/bim_edit_remote_tree.json"
        if not p.exists() or not tree.exists():
            self.skipTest("15KB IFC smoke asset is ignored; run metadata audit to cache it")
        import ifcopenshell
        from src.data.bim_edit import verify_local_asset_bytes
        remote=next(x for x in json.loads(tree.read_text()) if x.get("path")=="simple/17_input.ifc")
        self.assertTrue(verify_local_asset_bytes(p,remote)["git_blob_sha1_verified"])
        model=ifcopenshell.open(str(p))
        self.assertEqual(model.schema,"IFC4X3")
        self.assertEqual(len(model.by_type("IfcProject")),1)
        self.assertEqual(len(model.by_type("IfcWall")),5)
