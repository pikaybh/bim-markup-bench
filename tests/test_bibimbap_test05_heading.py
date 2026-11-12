"""Issue #104: study author-grader direction effects without any model inference."""
from __future__ import annotations

import json
from math import hypot, isclose
from pathlib import Path
import unittest

from tools.audit_bibimbap_test05_heading import CASES, endpoint
from tools.verify_bibimbap_xml_author import run_witness

ROOT = Path(__file__).resolve().parents[1]


class HeadingValidityAuditTests(unittest.TestCase):
    def test_predeclared_variants_have_expected_true_lengths(self):
        self.assertEqual(len(CASES), 5)
        self.assertEqual(len({x[0] for x in CASES}), 5)
        for _, angle, length in CASES:
            x, y = endpoint(angle, length)
            self.assertTrue(isclose(hypot(x, y + 10.0), length, abs_tol=1e-9))

    def test_invalid_end_is_rejected_before_any_ifc_access(self):
        with self.assertRaises(ValueError):
            run_witness(Path("not-found"), Path("not-found"), end_xy=(float("nan"), -10))
        with self.assertRaises(ValueError):
            run_witness(Path("not-found"), Path("not-found"), end_xy=(0, -10))

    def test_saved_author_score_vector_keeps_negative_control(self):
        record = json.loads((ROOT / "reports/bibimbap_test05_heading_validity_20261112_v2.json").read_text(encoding="utf8"))
        self.assertEqual(record["llm_calls"], 0)
        self.assertEqual(record["paid_api_cost"], 0)
        self.assertFalse(record["author_scorer_modified"])
        self.assertFalse(record["original_full_benchmark_score_reproduced"])
        self.assertEqual([x["case"] for x in record["results"]], [x[0] for x in CASES])
        self.assertTrue(record["all_variants_scored"])
        self.assertEqual(record["valid_heading_dimension_tested_count"], 4)
        self.assertTrue(record["negative_short_wall_dimensions_rejected"])
        for item in record["results"]:
            self.assertTrue(item["original_source_unchanged"])
            self.assertEqual(item["guids_removed"], 0)
            self.assertEqual(item["scorer_status"], "SCORED")
            self.assertTrue(isclose(item["measured_declared_centerline_m"], item["source_declared_length_m"], abs_tol=1e-8))
        # Do NOT assert equal scores: detecting unequal scores among valid
        # headings is the scientific purpose of this audit, not a test failure.


if __name__ == "__main__":
    unittest.main()
