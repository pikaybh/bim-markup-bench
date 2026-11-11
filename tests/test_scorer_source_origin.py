"""G0 #4 official source provenance cannot be forged by third-party code."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from src.evaluation import scorer_source_origin as origin
from tools import audit_scorer_source_origin as cli


class OriginalBIMEditScorerOriginTests(unittest.TestCase):
    def test_original_runs_inventory_does_not_imply_author_scorer_source(self):
        report=origin.audit_scorer_origin()
        self.assertEqual(report["status"],origin.RELEASE_GATE)
        self.assertEqual(report["author_published_run_model_count"],7)
        self.assertEqual(report["author_published_run_file_count"],1417)
        self.assertTrue(report["author_run_reports_available"])
        self.assertFalse(report["author_original_evaluator_cli_entrypoint_verified"])
        self.assertFalse(report["author_original_evaluator_source_commit_verified"])
        self.assertFalse(report["author_original_evaluator_mit_license_file_verified"])
        self.assertFalse(report["author_original_evaluator_scored_output_reproduced"])
        self.assertFalse(report["G0_G1_G2_G3_release_allowed"])
        self.assertEqual(report["official_tasks_scored"],0)
        self.assertEqual(report["paid_model_calls"],0)
        self.assertFalse(report["original_or_gt_ifc_opened"])

    def test_independent_reimplementation_version_pin_and_apache_license(self):
        r=origin.audit_scorer_origin()["third_party_reimplementation"]
        self.assertEqual(r["repository_full_name"],"NTUZZH/VeriBIM")
        self.assertEqual(r["pinned_git_commit"],
                         "cd3fe8cb18e8d33f76e73906253cf896cb5d4d3b")
        self.assertEqual(r["license_observed_in_its_own_repository"],"Apache-2.0")
        self.assertTrue(r["license_is_not_original_bim_edit_license"])
        self.assertEqual(r["cli_documented"],"python -m modifc_score.cli")
        self.assertEqual(len(r["inspected_bounded_source_files"]),6)
        self.assertIn("code/modifc_score/config.py",r["inspected_bounded_source_files"])
        for key,item in r["inspected_bounded_source_files"].items():
            self.assertEqual(len(item["git_blob_sha1"]),40)
            self.assertIn("/blob/"+r["pinned_git_commit"]+"/",item["url"])
        self.assertFalse(r["this_is_original_bim_edit_executable_evaluator"])
        self.assertFalse(r["strict_official_binary_parity_verified"])
        self.assertFalse(r["third_party_claim_checked_against_author_IFCs"])

    def test_paper_vs_independent_readings_are_explicitly_different(self):
        r=origin.audit_scorer_origin()["third_party_reimplementation"]
        self.assertEqual(r["paper_v3_topology"],"0.3 * node_f1 + 0.7 * edge_f1")
        self.assertEqual(r["third_party_documented_topology_default"],"mean_rules")
        self.assertEqual(r["third_party_documented_topology_alternative"],"paper")
        self.assertEqual(r["paper_v3_delete_semantics"],
                         "1.0 if the intended target object is removed, else 0.0")
        self.assertEqual(r["third_party_documented_delete_default"],"matcher")
        self.assertEqual(r["third_party_documented_delete_alternative"],"removal")
        self.assertNotEqual(r["paper_v3_topology"],r["third_party_documented_topology_default"])
        self.assertNotEqual(r["paper_v3_delete_semantics"],r["third_party_documented_delete_default"])

    def test_forged_official_scorer_labels_are_hard_denied(self):
        r=origin.audit_scorer_origin()["third_party_reimplementation"]
        for key,value in (
            ("official_evaluator",True),
            ("authors_verified",True),
            ("scored_tasks",1),
            ("repository_full_name","BIM-Edit/official-scorer"),
            ("pinned_git_commit","0"*40),
            ("license_observed_in_its_own_repository","MIT"),
            ("source_classification","original-author-evaluator"),
            ("cli_documented","python official.py"),
        ):
            with self.subTest(key=key):
                with self.assertRaises(origin.ScorerSourceOriginBlocked):
                    origin.audit_scorer_origin(
                        third_party_attestation={key:value})
        observed=origin.audit_scorer_origin(third_party_attestation={
            "repository_full_name":"NTUZZH/VeriBIM",
            "official_evaluator":False, "scored_tasks":0,
        })
        self.assertEqual(observed["status"],origin.RELEASE_GATE)

    def test_historical_g0_report_sha_tamper_and_symlink_refused(self):
        original=(origin.ROOT/origin.HISTORICAL_G0_REPORT).read_bytes()
        self.assertEqual(sha256(original).hexdigest(),origin.HISTORICAL_G0_SHA)
        with TemporaryDirectory(prefix="g0-origin-tamper-") as td:
            root=Path(td)
            file=root/origin.HISTORICAL_G0_REPORT
            file.parent.mkdir(parents=True)
            file.write_bytes(original)
            self.assertEqual(origin.audit_scorer_origin(root=root)["status"],
                             origin.RELEASE_GATE)
            obj=json.loads(original)
            obj["official_executable_scorer_available_to_this_project"]=True
            file.write_text(json.dumps(obj),encoding="utf8")
            with self.assertRaises(origin.ScorerSourceOriginBlocked):
                origin.audit_scorer_origin(root=root)
            file.unlink()
            with self.assertRaises(origin.ScorerSourceOriginBlocked):
                origin.audit_scorer_origin(root=root)

    def test_untrusted_git_blob_or_repo_constant_not_promoted(self):
        with patch.object(origin,"THIRD_PARTY_COMMIT","BAD"):
            with self.assertRaises(origin.ScorerSourceOriginBlocked):
                origin.audit_scorer_origin()
        with patch.object(origin,"THIRD_PARTY_REPO","BIM-Edit/BIM-Edit"):
            with self.assertRaises(origin.ScorerSourceOriginBlocked):
                origin.audit_scorer_origin()
        with patch.object(origin,"THIRD_PARTY_FILES",{"LICENSE":"not-sha"}):
            with self.assertRaises(origin.ScorerSourceOriginBlocked):
                origin.audit_scorer_origin()

    def test_report_never_contains_raw_gt_tasks_or_secret_and_is_json_safe(self):
        result=origin.audit_scorer_origin()
        content=json.dumps(result,sort_keys=True)
        for private in ("ground_truth_ifc","target_guid",'"target"',
                        '"evaluation"','"prompt"',"API_KEY","Bearer "):
            self.assertNotIn(private,content)
        self.assertFalse(result["third_party_files_fetched_or_imported_by_this_audit"])
        self.assertFalse(result["independent_scorer_metrics_reclassified_as_official"])
        self.assertEqual(json.loads(content)["status"],origin.RELEASE_GATE)

    def test_cli_is_blocking_even_with_public_code_and_historical_scores(self):
        with patch.object(cli,"audit_scorer_origin",
                          return_value=origin.audit_scorer_origin()):
            self.assertEqual(cli.main([]),2)


if __name__=="__main__":
    unittest.main()
