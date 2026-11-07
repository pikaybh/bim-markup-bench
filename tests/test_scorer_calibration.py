"""G2 calibration replay, seeded violation detection, privacy and hard gates."""
from __future__ import annotations

import csv
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from src.data.bim_edit import read_tasks
from src.evaluation.calibration import (
    calibrate_own_synthetic,tolerance_sensitivity,CATALOG,SRC,WALL_GT,
    build_calibration_artifacts
)
from src.evaluation.capability_matrix import build_capability_rows
from src.evaluation.bim_edit_scorer import GraderTask,score_ifc_result
from src.evaluation.metric_contract import final_score

ROOT=Path(__file__).resolve().parents[1]
CALIBRATION_REPORT=ROOT/"reports/evaluator_calibration.json"
CAPABILITY_REPORT=ROOT/"reports/arm_capability_matrix.csv"
G2_GATE=ROOT/"reports/G2_readiness.json"

def file_sha(path):
    return sha256(path.read_bytes()).hexdigest()


class CalibrationSyntheticTests(unittest.TestCase):
    def test_all_frozen_cases_detect_every_seeded_error(self):
        catalog=json.loads(CATALOG.read_text())
        self.assertEqual(len(catalog["cases"]),17)
        ids=[case["id"] for case in catalog["cases"]]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(sum(case["strict_pass"] for case in catalog["cases"]),3)
        before=(file_sha(SRC),file_sha(WALL_GT))
        with tempfile.TemporaryDirectory() as temp:
            result=calibrate_own_synthetic(Path(temp))
        self.assertEqual(result["evaluated_own_synthetic_cases"],17)
        self.assertEqual(result["synthetic_cases_matching_frozen_expectations"],17)
        self.assertTrue(result["all_frozen_expectations_pass"])
        self.assertEqual(result["synthetic_detection_ratio"],1.)
        self.assertEqual(result["official_dataset_cases_scored"],0)
        self.assertFalse(result["official_paper_score_reproduced"])
        self.assertEqual(result["model_provider_calls"],0)
        for row in result["cases"]:
            with self.subTest(case=row["case_id"]):
                self.assertTrue(row["all_expected_properties_pass"])
                self.assertTrue(all(row["checks"].values()))
        self.assertEqual((file_sha(SRC),file_sha(WALL_GT)),before)

    def test_two_fresh_runs_same_per_case_metrics(self):
        with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
            first=calibrate_own_synthetic(Path(t1))
            second=calibrate_own_synthetic(Path(t2))
        self.assertEqual(first,second)

    def test_translation_rotation_tolerance_sensitivity_replay(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as repeat:
            root=Path(temp); again=Path(repeat)
            result=tolerance_sensitivity(root)
            other=tolerance_sensitivity(again)
        self.assertEqual(result,other)
        trans=result["translation"]
        rotations=result["rotation"]
        self.assertEqual(trans[0]["geometry"],1.0)
        self.assertEqual(trans[1]["geometry"],1.0)
        self.assertTrue(all(
            trans[i]["geometry"]>=trans[i+1]["geometry"]-1e-8
            for i in range(len(trans)-1)
        ))
        self.assertEqual(rotations[0]["geometry"],1.0)
        self.assertTrue(all(
            rotations[i]["geometry"]>=rotations[i+1]["geometry"]-1e-8
            for i in range(len(rotations)-1)
        ))
        self.assertLess(trans[-1]["geometry"],.98)
        self.assertLess(rotations[-1]["geometry"],.98)

    def test_same_ifc_scores_equal_regardless_external_arm_label(self):
        guid="2L_lrSH5fHAgIRV7tit5Pp"
        task=GraderTask("OWN-LABEL-SHUFFLE","update","IfcWall",(guid,))
        by_label={}
        for label in ("control","direct","direct","control"):
            score=score_ifc_result(
                source_ifc=SRC,ground_truth_ifc=WALL_GT,
                result_ifc=WALL_GT,task=task)
            by_label.setdefault(label,[]).append(score)
        self.assertEqual(by_label["control"],by_label["direct"])
        self.assertTrue(by_label["direct"][0]["strict_pass"])
        self.assertEqual(by_label["direct"][0]["metric_origin"],
                         "independent-reimplementation")

    def test_scoring_does_not_rewrite_input_reference_or_candidate(self):
        guid="2L_lrSH5fHAgIRV7tit5Pp"
        task=GraderTask("OWN-NO-MUTATION","update","IfcWall",(guid,))
        with tempfile.TemporaryDirectory() as temp:
            files=build_calibration_artifacts(Path(temp))
            pred=files["wall_translate"]
            paths=(SRC,WALL_GT,pred)
            before=tuple(file_sha(p) for p in paths)
            for _ in range(3):
                val=score_ifc_result(
                    source_ifc=SRC,ground_truth_ifc=WALL_GT,
                    result_ifc=pred,task=task)
                self.assertEqual(val["status"],"INDEPENDENT_IFC_SCORED")
                self.assertFalse(val["source_or_gt_mutated"])
            self.assertEqual(tuple(file_sha(p) for p in paths),before)

    def test_paper_rounded_examples_are_arithmetic_only(self):
        self.assertAlmostEqual(final_score(1.,1.,.47)["final_score"],.82333333333)
        self.assertAlmostEqual(final_score(.38,.72,1.)["final_score"],.7)
        self.assertTrue(final_score(1.,1.,1.)["strict_pass"])
        self.assertFalse(final_score(.38,.72,1.)["strict_pass"])
        self.assertEqual(final_score(1.,1.,.47)["metric_origin"],
                         "paper-formula-only")

    def test_checked_in_calibration_report_matches_reproduction(self):
        report=json.loads(CALIBRATION_REPORT.read_text())
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            reproduced=calibrate_own_synthetic(root)
            reproduced["tolerance_sensitivity"]=tolerance_sensitivity(root)
        for field in ("cases","metric_origin","evaluated_own_synthetic_cases",
                      "synthetic_cases_matching_frozen_expectations",
                      "tolerance_sensitivity"):
            self.assertEqual(report[field],reproduced[field])
        self.assertEqual(report["official_dataset_cases_scored"],0)


class CapabilityAndReleaseGateTests(unittest.TestCase):
    def test_108_strata_matrix_has_no_claimed_official_success(self):
        with CAPABILITY_REPORT.open(newline="",encoding="utf-8") as f:
            csv_rows=list(csv.DictReader(f))
        self.assertEqual(len(csv_rows),108)
        self.assertEqual(sum(int(row["public_task_count"]) for row in csv_rows),324)
        self.assertEqual(sum(int(row["static_engine_unsupported"]) for row in csv_rows),246)
        self.assertEqual(sum(int(row["source_dependent_unverified"]) for row in csv_rows),78)
        for row in csv_rows:
            self.assertEqual(row["verified_official_D0_tasks"],"0")
            self.assertEqual(row["verified_official_I0_tasks"],"0")
            self.assertEqual(row["matched_official_scored_tasks"],"0")
            self.assertEqual(row["readiness"],"BLOCKED_NO_OFFICIAL_IFC_EVALUATION")

    def test_matrix_matches_pinned_metadata_when_cached(self):
        pinned=ROOT/"data/tasks.jsonl"
        if not pinned.exists():
            self.skipTest("Optional pinned public task metadata is not cached")
        expected=build_capability_rows(pinned)
        with CAPABILITY_REPORT.open(newline="",encoding="utf-8") as f:
            actual=list(csv.DictReader(f))
        self.assertEqual(len(expected),len(actual))
        for a,b in zip(expected,actual):
            for key,value in a.items():
                self.assertEqual(str(value),b[key])

    def test_enforce_exit_two_and_no_fake_benchmark_scores(self):
        if not (ROOT/"data/tasks.jsonl").exists():
            self.skipTest("Optional pinned public task metadata is not cached")
        with tempfile.TemporaryDirectory() as temp:
            temp=Path(temp)
            command=[sys.executable,"-m","tools.calibrate_g2",
                    "--output",str(temp/"calibration.json"),
                    "--matrix",str(temp/"capabilities.csv"),
                    "--gate",str(temp/"gate.json"),
                    "--metadata",str(ROOT/"data/tasks.jsonl"),
                    "--enforce"]
            proc=subprocess.run(command,cwd=ROOT,capture_output=True,
                                text=True,timeout=35)
            self.assertEqual(proc.returncode,2,proc.stdout+proc.stderr)
            result=json.loads(proc.stdout)
            self.assertEqual(result["expectations_satisfied"],17)
            self.assertEqual(result["official_tasks_scored"],0)
            self.assertFalse(result["paid_run_ready"])
            gate=json.loads((temp/"gate.json").read_text())
            self.assertEqual(gate["status"],"BLOCKED_FOR_LIVE_MODEL_PILOT")
            self.assertFalse(gate["paid_run_ready"])
            self.assertFalse(gate["OS_generated_python_execution_enabled"])
            self.assertEqual(gate["provider_model_calls"],0)

    def test_g2_gate_no_billing_or_isolation_claim(self):
        gate=json.loads(G2_GATE.read_text())
        self.assertEqual(gate["official_tasks_scored"],0)
        self.assertEqual(gate["verified_official_D0_tasks"],0)
        self.assertEqual(gate["verified_official_I0_tasks"],0)
        self.assertFalse(gate["model_API_keys_required"])
        self.assertFalse(gate["paid_run_ready"])
        self.assertEqual(gate["gates"]["G2_independent_scorer_calibration"],
                         "YES_OWN_SYNTHETIC_ONLY")
        self.assertEqual(gate["gates"]["G2_verified_OS_network_process_secret_isolation"],
                         "NO")
        self.assertEqual(gate["gates"]["G0_official_IFC_input_GT_324_content_audit"],
                         "NO")

if __name__=="__main__":unittest.main()
