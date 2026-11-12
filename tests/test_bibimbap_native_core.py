"""Non-LLM native IFC geometry core evidence for public test_05 (#108)."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.bibimbap_test05_native_core import (
    NativeCoreError, evaluate_public_test05_core,
)
from tools.audit_bibimbap_test05_heading import CASES

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "bibimbap_test05_heading_native_core_20261112_v3.json"


class NativeCoreContractTests(unittest.TestCase):
    def test_same_ifc_path_rejected_before_parsing(self):
        with self.assertRaises((ValueError, FileNotFoundError)):
            evaluate_public_test05_core(Path(__file__), Path(__file__))

    def test_noop_and_short_wrong_length_fail_real_ifc_core(self):
        r = json.loads(REPORT.read_text(encoding="utf8"))
        self.assertEqual([x["case"] for x in r["results"]], [x[0] for x in CASES])
        self.assertTrue(r["independent_native_invalid_core_rejected"])
        self.assertTrue(r["independent_native_noop_rejected_all"])
        bad = r["results"][-1]["independent_native_task_core"]
        self.assertEqual(bad["added_ifcwall_count"], 1)
        self.assertFalse(bad["public_length_pass"])
        self.assertTrue(bad["public_start_pass"])
        self.assertFalse(bad["public_task_core_success"])
        self.assertIsNone(bad["full_independent_strict_task_success"])

    def test_all_four_valid_directions_have_native_geometry_core(self):
        r = json.loads(REPORT.read_text(encoding="utf8"))
        self.assertEqual(r["schema"], "bibimbap-test05-orientation-validity/v0.2")
        self.assertEqual(r["independent_native_valid_core_count"], 4)
        self.assertFalse(r["independent_full_strict_task_success_implemented"])
        self.assertEqual(r["llm_calls"], 0)
        for item in r["results"][:4]:
            native = item["independent_native_task_core"]
            self.assertTrue(native["public_task_core_success"], item["case"])
            self.assertTrue(native["existing_root_class_identity_preserved"])
            self.assertEqual(native["added_ifcwall_count"], 1)
            self.assertLess(abs(native["native_max_horizontal_vertex_span_m"] - 15.0), 0.05)
            self.assertLess(native["native_nearest_start_vertex_m"], 0.5)
            self.assertEqual(native["source_original_sha256"], r["original_ifc_sha256"])
            self.assertFalse(native["author_grader_consulted"])
            self.assertFalse(native["clash_nonregression_verified"])
            self.assertFalse(native["untouched_geometry_identical_verified"])
            self.assertIsNone(native["full_independent_strict_task_success"])

    def test_author_fractional_integrity_differs_from_public_geometry(self):
        r = json.loads(REPORT.read_text(encoding="utf8"))
        for item in r["results"][2:4]:
            self.assertTrue(item["independent_native_task_core"]["public_task_core_success"])
            self.assertGreater(item["author_score"], 0.9)
            self.assertLess(item["author_score"], 1.0)
            self.assertEqual(item["author_metric_vector"]["right_dimensions"], 1.0)
            self.assertEqual(item["author_metric_vector"]["right_location"], 1.0)
            self.assertLess(item["author_metric_vector"]["integrity_constraint"], 1.0)


if __name__ == "__main__":
    unittest.main()
