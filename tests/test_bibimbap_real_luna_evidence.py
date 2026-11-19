"""Offline regression for one real GPT-6 Luna BIBIMBAP pilot (#110).

No inference, billing, mutation of actual result or original author code.
"""
from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import unittest
from lxml import etree

from tools.audit_bibimbap_test05_real_semantic import analyze, audit
from tools.run_bibimbap_test05_first_luna import (
    APPROVED_CAP_USD, LOCAL_RUN_NAME, MAX_OUTPUT_TOKENS,
    PROMPT_EXPECTED_SHA, ROOT, public_git_summary,
)

REPORT = ROOT / "reports" / "bibimbap_test05_luna_first_real_20261112.json"
SEMANTIC = ROOT / "reports" / "bibimbap_test05_luna_semantic_diff_20261112.json"
LOCAL_SOURCE = ROOT / "results" / LOCAL_RUN_NAME / "model_generated_exact.raw.txt"


def xml_without_wall() -> bytes:
    return b'<Building xmlns="urn:bim-markup-bench:toy:v0" units="m"><Elements><Wall id="w1" x1="1" y1="2" x2="5" y2="2" height="3" thickness="0.2"/></Elements><Relations/></Building>'


def xml_with_wall() -> bytes:
    return b'<Building xmlns="urn:bim-markup-bench:toy:v0" units="m"><Elements><Wall id="w1" x1="1" y1="2" x2="5" y2="2" height="3" thickness="0.2"/><Wall id="w2" x1="0" y1="-10" x2="15" y2="-10" height="3.3" thickness="0.15"/></Elements><Relations/></Building>'


class RealSingleAttemptEvidenceTests(unittest.TestCase):
    def test_original_score_and_provider_usage_are_real_and_bounded(self):
        saved = json.loads(REPORT.read_text(encoding="utf8"))
        self.assertEqual(saved["status"], "ONE_REAL_MODEL_EDIT_SCORED")
        self.assertEqual(saved["actual_api_calls_attempted"], 1)
        self.assertEqual(saved["model_edit_attempts"], 1)
        self.assertEqual(saved["user_approved_model"], "gpt-6-luna")
        self.assertEqual(saved["provider_returned_model"], "gpt-6-luna")
        self.assertEqual(saved["public_packet_sha256"], PROMPT_EXPECTED_SHA)
        self.assertEqual(saved["provider_status"], "completed")
        self.assertTrue(saved["raw_model_output_saved"])
        self.assertEqual(saved["provider_retries"], 0)
        self.assertEqual(saved["max_output_tokens"], MAX_OUTPUT_TOKENS)
        self.assertLessEqual(Decimal(saved["request_cost_reservation_10x_usd"]), APPROVED_CAP_USD)
        self.assertLess(Decimal(saved["actual_provider_usage_cost_estimate_usd"]), APPROVED_CAP_USD)
        self.assertGreater(saved["reported_input_tokens"], 0)
        self.assertGreater(saved["reported_output_tokens"], 0)
        self.assertEqual(saved["original_author_score"], 1)
        self.assertTrue(saved["independent_native_core_success"])
        self.assertIsNone(saved["full_independent_strict_task_success"])
        self.assertEqual(saved["original_author_metric_vector"], {
            "object_exists": 1.0, "right_location": 1.0,
            "right_dimensions": 1.0, "integrity_constraint": 1.0,
        })
        self.assertTrue(saved["raw_provider_artifacts_are_git_ignored"])
        self.assertNotIn("raw_model_output_path_local_only", saved)
        self.assertNotIn("native_ifc_path_local_only", saved)

    def test_reproduced_public_source_adds_one_wall_and_leaves_25_ids_untouched(self):
        saved = json.loads(SEMANTIC.read_text(encoding="utf8"))
        diff = saved["difference"]
        self.assertEqual(saved["model_calls_this_audit"], 0)
        self.assertFalse(saved["raw_model_output_edited_or_corrected"])
        self.assertEqual(saved["model_output_exact_sha256"],
                         json.loads(REPORT.read_text(encoding="utf8"))["raw_model_output_sha256"])
        self.assertEqual(diff["semantic_source_id_count"], 25)
        self.assertEqual(diff["semantic_model_id_count"], 26)
        self.assertEqual(diff["new_id_count"], 1)
        self.assertEqual(diff["new_element_types"], ["Wall"])
        self.assertEqual(diff["dropped_existing_id_count"], 0)
        self.assertEqual(diff["modified_existing_id_count"], 0)
        self.assertTrue(diff["old_relation_container_and_nonid_nodes_unchanged"])
        self.assertTrue(diff["source_only_add_one_wall"])
        self.assertTrue(diff["new_wall_geometry_matches_public"])

    def test_mutated_existing_wall_detected_without_grader(self):
        root = etree.fromstring(xml_with_wall())
        old_wall = root.find(".//{*}Wall")
        old_wall.set("height", "4")
        diff = analyze(xml_without_wall(), etree.tostring(root, encoding="utf8"))
        self.assertFalse(diff["source_only_add_one_wall"])
        self.assertEqual(diff["modified_existing_id_count"], 1)
        self.assertEqual(diff["new_id_count"], 1)

    def test_wrong_new_length_rejected_in_semantic_audit(self):
        root = etree.fromstring(xml_with_wall())
        new = root.findall(".//{*}Wall")[-1]
        new.set("x2", "10")
        diff = analyze(xml_without_wall(), etree.tostring(root, encoding="utf8"))
        self.assertTrue(diff["source_only_add_one_wall"])
        self.assertFalse(diff["new_wall_geometry_matches_public"])

    def test_raw_artifact_hash_if_available(self):
        if not LOCAL_SOURCE.is_file():
            self.skipTest("Raw provider result intentionally excluded from Git")
        import hashlib
        raw = LOCAL_SOURCE.read_bytes()
        saved = json.loads(REPORT.read_text(encoding="utf8"))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), saved["raw_model_output_sha256"])
        self.assertEqual(len(raw), saved["raw_model_output_bytes"])

    def test_public_git_summary_explicitly_excludes_local_secret_or_answer_paths(self):
        fake = {
            "scope": "REAL_SINGLE_TASK_BIBIMBAP_XML_ONLY",
            "status": "ONE_REAL_MODEL_EDIT_SCORED",
            "local_key": "SHOULD_NOT_EXPORT",
            "raw_model_output_path_local_only": "SHOULD_NOT_EXPORT",
            "token_secret": "SHOULD_NOT_EXPORT",
        }
        public = public_git_summary(fake)
        self.assertNotIn("local_key", public)
        self.assertNotIn("raw_model_output_path_local_only", public)
        self.assertNotIn("token_secret", public)


if __name__ == "__main__":
    unittest.main()
