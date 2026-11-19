"""Offline regression checks for BIBIMBAP original grader integration.

External pinned clones are deliberately NOT vendored into this repository.
Set BIBIMBAP_AUTHOR_REPO and BIBIMBAP_DATASET for live-clone tests.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.audit_bibimbap_author import (
    AUTHOR_SHA, DATA_SHA, AuthorAuditError, read_original_tasks, run_audit,
)
from tools.bibimbap_positive_witness import run_positive
from tools.verify_bibimbap_xml_author import run_witness
from tools.verify_bibimbap_xml_update_author import run_witness as run_update_witness

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = os.environ.get("BIBIMBAP_AUTHOR_REPO")
DATA = os.environ.get("BIBIMBAP_DATASET")


class OriginalBibimbapAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not AUTHOR or not DATA:
            raise unittest.SkipTest("External author source/data clones must be specified explicitly")
        cls.author, cls.data = Path(AUTHOR), Path(DATA)
        cls.tests, cls.pins = read_original_tasks(cls.author, cls.data)

    def test_exact_pinned_original_assets_and_task_count(self):
        self.assertEqual(self.pins["author_commit_sha"], AUTHOR_SHA)
        self.assertEqual(self.pins["data_commit_sha"], DATA_SHA)
        self.assertEqual(len(self.tests), 45)
        self.assertEqual(len({x["test_id"] for x in self.tests}), 45)
        from collections import Counter
        self.assertEqual(
            dict(Counter(x["crud"] for x in self.tests)),
            {"create": 15, "update": 15, "delete": 15},
        )
        self.assertFalse(self.pins["source_license_file_present"])
        self.assertTrue(all(x["original_scorer_execute_test"] for x in self.tests))

    def test_missing_or_wrong_dataset_fails_closed(self):
        with TemporaryDirectory() as temp:
            with self.assertRaises((AuthorAuditError, FileNotFoundError)):
                read_original_tasks(self.author, Path(temp))

    def test_recorded_45_negative_control_reproduced(self):
        record = json.loads(
            (ROOT / "reports/bibimbap_original_45_noop_20261112.json").read_text(
                encoding="utf8"
            )
        )
        self.assertEqual(record["original_editing_tasks"], 45)
        self.assertEqual(record["negative_control"]["statuses"], {"SCORED": 45})
        observations = record["negative_control"]["observations"]
        self.assertTrue(all(x["original_and_edited_identical"] for x in observations))
        self.assertEqual(
            {x["test_id"] for x in observations if x["author_noop_score"] > 0},
            {x["test_id"] for x in self.tests if x["crud"] == "update"},
        )
        self.assertTrue(all(x["author_noop_score"] == 0 for x in observations
                            if x["crud"] in ("create", "delete")))

    def test_unit_bridge_and_projection_reports_are_not_model_scores(self):
        rt = json.loads((ROOT / "reports/bibimbap_45_unit_roundtrip_20261112_v2.json").read_text(encoding="utf8"))
        self.assertEqual(rt["controls_matching"], 45)
        self.assertEqual(rt["ifc4x3_compiler_compatible_schema_count"], 42)
        self.assertEqual(set(rt["unsupported_source_schema_task_ids"]),
                         {"geometry_test_03", "geometry_test_04", "geometry_test_05"})
        self.assertEqual(rt["live_llm_calls"], 0)
        projection = json.loads(
            (ROOT / "reports/bibimbap_45_xml_projection_20261112.json").read_text(encoding="utf8")
        )
        self.assertEqual(projection["assessed_editing_task_count"], 45)
        self.assertEqual(projection["unique_editing_source_ifc_count"], 31)
        dispositions = projection["projection_dispositions"]
        self.assertEqual(dispositions["PROJECTABLE"], 36)
        self.assertEqual(dispositions["ORIGINAL_SOURCE_NOT_IFC4X3"], 3)
        self.assertEqual(sum(dispositions.values()), 45)
        self.assertEqual(projection["llm_calls"], 0)
    def test_positive_ifc_scored_and_not_fabricated_xml(self):
        report = run_positive(self.author, self.data)
        scores = {x["test_id"]: x["result"] for x in report["observations"]}
        self.assertEqual(scores["test_15"]["status"], "SCORED")
        self.assertEqual(scores["test_15"]["score"], 1.0)
        self.assertEqual(scores["test_16"]["status"], "SCORED")
        self.assertEqual(scores["test_16"]["metrics"]["object_not_exists"], 1.0)
        self.assertFalse(report["claims_author_paper_reproduction"])

    def test_xml_to_ifc_second_storey_update_author_scored(self):
        report = run_update_witness(self.author, self.data)
        self.assertEqual(report["status"], "XML_AUTHOR_GEOMETRY11_SCORED")
        self.assertTrue(report["original_source_unmodified"])
        self.assertTrue(report["original_guid_preserved"])
        self.assertEqual(report["wall_changes_source_derived"], 6)
        self.assertEqual(report["result_ifc_schema"], "IFC4X3")
        self.assertEqual(report["result_unit_scale"], 0.001)
        self.assertEqual(report["added_root_guid_count"], 0)
        self.assertEqual(report["removed_root_guid_count"], 0)
        self.assertEqual(report["original_author_scorer"]["score"], 1.0)
        self.assertEqual(report["llm_calls"], 0)
    def test_xml_to_ifc_end_to_end_proven_on_test05(self):
        report = run_witness(self.author, self.data)
        self.assertEqual(report["status"], "XML_AUTHOR_WITNESS_SCORED")
        self.assertTrue(report["input_source_hash_unmodified"])
        self.assertEqual(report["root_inventory"]["source_wall"], 16)
        self.assertEqual(report["root_inventory"]["edited_wall"], 17)
        self.assertEqual(report["root_inventory"]["lost_guids"], 0)
        self.assertEqual(
            report["observations"]["xml_wall_created"]["scorer"]["score"], 1.0
        )
        self.assertEqual(
            report["observations"]["unit_roundtrip_noop"]["scorer"]["score"], 0.0
        )
        self.assertEqual(report["model_calls"], 0)


if __name__ == "__main__":
    unittest.main()
