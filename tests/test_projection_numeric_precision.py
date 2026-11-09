"""Issue #11: projected floating-point world coords must stay XML-schema valid."""
from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path
import unittest

from src.runtime.ifc_projection import _number, project_ifc, UnsupportedIFCGeometry
from src.runtime.xml_parser import parse_xml

ROOT=Path(__file__).resolve().parents[1]


class ProjectionPrecisionTests(unittest.TestCase):
    def test_near_zero_binary_float_serializes_as_schema_valid_zero(self):
        for value in (-5.995204332975845e-14, 5.995204332975845e-14,
                      -1e-15, -0.0):
            with self.subTest(value=value):
                self.assertEqual(_number(value), "0")

    def test_projection_has_bounded_world_coordinate_error(self):
        samples=(0.0, -3.216, 0.175, 2.8, 1.3025, 31.676,
                 6_371_000.000123456, -18.1234567890123)
        for value in samples:
            with self.subTest(value=value):
                text=_number(value)
                self.assertNotIn("e",text.lower())
                self.assertLessEqual(abs(float(text)-value), 5.1e-10)
                self.assertLessEqual(len(text.split(".")[-1]) if "." in text else 0,9)

    def test_nonfinite_and_unsafe_world_coordinates_fail_closed(self):
        for value in (float("nan"), float("inf"), float("-inf"), 1e10):
            with self.subTest(value=value),self.assertRaises(UnsupportedIFCGeometry):
                _number(value)

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").is_file(),
                         "Pinned public metadata cache not present")
    def test_cached_public_input_projection_parses_without_unbounded_decimal(self):
        from src.data.bim_edit import (read_tasks,repo_asset_path,verify_local_asset_bytes)
        from src.data.pilot_asset_audit import _files_in_root
        tasks={x["task_id"]:x for x in read_tasks(ROOT/"data/tasks.jsonl")}
        task=tasks["WIN-UPD-DIR-A-002"]
        source_rel=repo_asset_path(task["input_ifc"])
        root=ROOT/"data/ifc"
        if not root.is_dir():
            self.skipTest("Public cache not mounted")
        source=_files_in_root(root,source_rel)
        if not source.is_file():
            self.skipTest("Public input file not locally available")
        tree=json.loads((ROOT/"data/bim_edit_remote_tree.json").read_text(encoding="utf-8"))
        meta={x["path"]:x for x in tree if x.get("type")=="file"}
        verify_local_asset_bytes(source,meta[source_rel])
        before=sha256(source.read_bytes()).hexdigest()
        projection=project_ifc(source)
        parse_xml(projection.xml, expected_source_sha256=before)
        self.assertEqual(sha256(source.read_bytes()).hexdigest(),before)
        self.assertTrue(projection.source_file_preserved if hasattr(projection,"source_file_preserved") else
                        projection.report()["source_file_preserved"])


if __name__=="__main__":
    unittest.main()
