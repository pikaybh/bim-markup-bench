"""Official-BIM-Edit release ≠ installed executable scorer regression tests.

All fixtures are in-memory public metadata SHAPES and rounded author
aggregates. No GT IFC, model run output or official scorer is loaded.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import json
import unittest
from unittest.mock import patch

from src.evaluation.official_release_provenance import (
    PINNED_RUNS_SHA,RUNS_MODELS,EXPECTED_EVAL_FILES,PAPER_CLAUDE,
    OfficialReleaseEvidenceError,inventory_public_runs,
    audit_published_claude_summary,combine_release_evidence,
)
from tools.audit_official_bim_edit_release import _fetch_named_json,run_public_release_audit
from src.evaluation.bim_edit_scorer import PROVENANCE,GraderTask,_base
from src.evaluation.metric_contract import final_score


def metadata_fixture():
    files=[]
    for model in sorted(RUNS_MODELS):
        for path in EXPECTED_EVAL_FILES:
            files.append({"rfilename":model+"/"+path})
    files.extend({"rfilename":f"dummy/entry{i:03d}.ifc"} for i in range(93))
    return {"sha":PINNED_RUNS_SHA,"siblings":files,
            "may_not_override_provenance":"official"}


def summary_fixture():
    return {
        "overall":{
            "n_samples":324,"n_tasks":324,
            "geometry_mean":0.559,
            "semantics_mean":0.3385,
            "topology_mean":0.4619,
            "final_score_mean":0.4531,
        },
        "by_scene_type":{"realistic":{"n_tasks":324}},
        "metric_origin":"official",  # Never accept this as code provenance.
    }


class OfficialReleaseEvidenceTests(unittest.TestCase):
    def test_real_local_ifc_scorer_remains_independent_even_with_author_reports(self):
        self.assertEqual(PROVENANCE,"independent-reimplementation")
        local=_base(GraderTask("OWN-METRIC-CHECK","create","IfcWall",()),
                    None,None,None)
        self.assertEqual(local["metric_origin"],"independent-reimplementation")
        self.assertFalse(local["official_bim_edit_evaluator_equivalent"])
        scalar=final_score(.5590,.3385,.4619)
        self.assertEqual(scalar["metric_origin"],"paper-formula-only")
        self.assertFalse(scalar["full_ifc_evaluator_implemented"])
        self.assertAlmostEqual(scalar["final_score"],.4531333333333333)

    def test_paper_aggregate_matches_author_summary_arithmetic_only(self):
        outcome=audit_published_claude_summary(summary_fixture())
        self.assertTrue(outcome["paper_table1_rounded_values_match"])
        self.assertTrue(outcome["mean_axis_arithmetic_within_publication_rounding"])
        self.assertFalse(outcome["official_evaluator_executed"])
        self.assertFalse(outcome["independent_evaluator_numerical_parity_tested"])
        self.assertTrue(outcome[
            "scene_type_summary_label_may_be_inconsistent_with_task_card"])

    def test_author_runs_inventory_contains_seven_eval_reports_but_no_scorer(self):
        data=inventory_public_runs(metadata_fixture())
        self.assertEqual(data["author_report_model_count"],7)
        self.assertEqual(data["public_file_count"],121)
        self.assertEqual(data["possible_executable_artifacts_in_THIS_runs_revision"],0)
        self.assertFalse(data["official_evaluator_entrypoint_verified"])
        self.assertTrue(all(row["has_per_task_csv"]
                            for row in data["models"].values()))

    def test_a_released_python_file_could_only_trigger_manual_review_not_approval(self):
        candidate=metadata_fixture()
        candidate["siblings"].append({"rfilename":"evaluation/scorer.py"})
        data=inventory_public_runs(candidate)
        self.assertEqual(data["executables_in_THIS_runs_revision"],
                         ["evaluation/scorer.py"])
        self.assertFalse(data["official_evaluator_entrypoint_verified"])
        self.assertFalse(data["official_evaluator_equivalence_verified"])

    def test_missing_model_or_eval_summary_blocks_public_release_confirmation(self):
        for model in sorted(RUNS_MODELS):
            candidate=metadata_fixture()
            candidate["siblings"]=[
                item for item in candidate["siblings"]
                if item["rfilename"]!=model+"/eval/summary.json"
            ]
            with self.subTest(model=model),self.assertRaisesRegex(
                OfficialReleaseEvidenceError,"incomplete"):
                inventory_public_runs(candidate)

    def test_wrong_revision_duplicates_path_traversal_are_rejected(self):
        wrong=metadata_fixture()
        wrong["sha"]="0"*40
        with self.assertRaisesRegex(OfficialReleaseEvidenceError,"revision"):
            inventory_public_runs(wrong)
        dup=metadata_fixture()
        dup["siblings"].append(deepcopy(dup["siblings"][0]))
        with self.assertRaisesRegex(OfficialReleaseEvidenceError,"Duplicate"):
            inventory_public_runs(dup)
        traversal=metadata_fixture()
        traversal["siblings"].append({"rfilename":"../secrets.txt"})
        with self.assertRaisesRegex(OfficialReleaseEvidenceError,"Invalid release path"):
            inventory_public_runs(traversal)

    def test_short_or_untrusted_metadata_fails_closed(self):
        for row in ({"sha":PINNED_RUNS_SHA,"siblings":[]},
                    {"sha":PINNED_RUNS_SHA,"siblings":"not a list"},
                    {"sha":PINNED_RUNS_SHA,"siblings":[{}]*150}):
            with self.subTest(row=row),self.assertRaises(OfficialReleaseEvidenceError):
                inventory_public_runs(row)

    def test_paper_score_mismatch_or_forged_claim_is_not_calibration(self):
        for field in PAPER_CLAUDE:
            fake=summary_fixture()
            fake["overall"][field]=0.99
            with self.subTest(field=field),self.assertRaisesRegex(
                OfficialReleaseEvidenceError,"mismatch"):
                audit_published_claude_summary(fake)

    def test_untrue_average_and_bad_types_rejected(self):
        for bad in (324.0,325,"324",True):
            fake=summary_fixture()
            fake["overall"]["n_tasks"]=bad
            with self.subTest(bad=bad),self.assertRaisesRegex(
                OfficialReleaseEvidenceError,"324"):
                audit_published_claude_summary(fake)
        for bad in ("NaN","inf",-0.1,1.1,True,None):
            fake=summary_fixture()
            fake["overall"]["geometry_mean"]=bad
            with self.subTest(value=bad),self.assertRaises(
                OfficialReleaseEvidenceError):
                audit_published_claude_summary(fake)

    def test_scene_type_warning_is_report_only_not_a_task_score(self):
        sample=summary_fixture()
        sample["by_scene_type"]={
            "realistic":{"n_tasks":162},
            "artificial":{"n_tasks":162},
        }
        checked=audit_published_claude_summary(sample)
        self.assertFalse(checked[
            "scene_type_summary_label_may_be_inconsistent_with_task_card"])
        self.assertFalse(checked["release_summary_recomputed_from_raw_IFC"])

    def test_fabricated_published_official_flags_cannot_enable_local_scorer(self):
        meta=metadata_fixture()
        meta["official_source_verified"]=True
        meta["licensed_evaluator"]="MIT"
        sample=summary_fixture()
        sample["full_official_code_calibrated"]=True
        result=combine_release_evidence(meta,sample)
        self.assertFalse(result[
            "official_executable_scorer_available_to_this_project"])
        self.assertFalse(result["official_scorer_numerically_equivalent_to_local"])
        self.assertFalse(result["G2_G3_paid_or_official_scoring_gate_ready"])
        self.assertEqual(result["current_local_scorer_metric_origin"],
                         "independent-reimplementation")
        self.assertEqual(result["official_tasks_scored_by_this_project"],0)

    def test_public_request_is_strict_two_resource_allowlist(self):
        with self.assertRaisesRegex(ValueError,"Unapproved public release URL"):
            _fetch_named_json("https://attacker.example/private-ifc")
        with self.assertRaisesRegex(ValueError,"Unapproved public release URL"):
            _fetch_named_json("input-ifc-bytes")

    def test_cli_report_fingerprints_two_public_json_not_ifc(self):
        meta=metadata_fixture()
        sample=summary_fixture()
        def mock_fetch(name):
            value=meta if name=="runs_repo_metadata" else sample
            return value,"a"*64 if name=="runs_repo_metadata" else "b"*64
        with patch("tools.audit_official_bim_edit_release._fetch_named_json",
                   side_effect=mock_fetch) as fetch:
            result=run_public_release_audit()
        self.assertEqual(fetch.call_count,2)
        self.assertTrue(result["source_content_integrity"][
            "two_whitelisted_public_JSON_requests"])
        self.assertEqual(result["source_content_integrity"][
            "metadata_raw_json_sha256"],"a"*64)
        self.assertFalse(result["hidden_ground_truth_accessed"])
        self.assertFalse(result["task_solutions_accessed"])
        self.assertEqual(result["paid_model_provider_calls"],0)


if __name__=="__main__":
    unittest.main()
