"""Positive/negative qualification tests for frozen independent IFC scorer.

No author CIF or public GT models; no official scorer or LLM is executed.
Tests cannot promote metric_origin to official or change v0.1 score policy.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from src.evaluation.bim_edit_scorer import (
    GraderTask,score_ifc_result,PROVENANCE,EVALUATOR_VERSION,
)
from src.evaluation.calibration import (
    SRC,WALL_GT,CATALOG,WALL_GUID
)
from src.evaluation.independent_replay_attestation import (
    SCHEMA_PATH,EXPECTED_OWN_SOURCE_SHA256,
    QUALIFICATION_CASES,QualificationBlocked,
    run_own_ifc_replay_qualification,
    verify_independent_score_record,
    EXPECTED_LOCAL_SCORER_SOURCE_SHA256,
    _sha,
)


class IndependentScorerReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema=json.loads(SCHEMA_PATH.read_text("utf8"))
        cls.task=GraderTask("OWN-CAL-WALL-UPDATE","update","IfcWall",(WALL_GUID,))
        cls.record=score_ifc_result(
            source_ifc=SRC,ground_truth_ifc=WALL_GT,result_ifc=WALL_GT,
            task=cls.task)
        cls.hashes=tuple(cls.record[key] for key in (
            "source_ifc_sha256","ground_truth_ifc_sha256","result_ifc_sha256"))
        assert cls.record["status"]=="INDEPENDENT_IFC_SCORED"
        assert cls.record["strict_pass"] is True

    def verify(self,row=None,*,status="INDEPENDENT_IFC_SCORED",
               passed=True,hashes=None):
        return verify_independent_score_record(
            self.record if row is None else row,self.schema,
            expected_status=status,expected_strict=passed,
            expected_hashes=self.hashes if hashes is None else hashes)

    def test_positive_self_reference_is_native_and_schema_conformant(self):
        outcome=self.verify()
        self.assertEqual(outcome["metric_origin"],"independent-reimplementation")
        self.assertTrue(outcome["strict_pass"])
        self.assertTrue(outcome["score_fields_present"])
        self.assertEqual(len(outcome["record_sha256"]),64)
        self.assertFalse(outcome["official_equivalence_proven"])

    def test_reference_source_sha_matches_frozen_fixture(self):
        self.assertEqual(_sha(SRC),EXPECTED_OWN_SOURCE_SHA256)
        self.assertEqual(self.record["source_ifc_sha256"],_sha(SRC))
        self.assertEqual(self.record["ground_truth_ifc_sha256"],_sha(WALL_GT))

    def test_independent_scorer_has_no_arm_or_model_source_parameter(self):
        signature=inspect.signature(score_ifc_result)
        self.assertFalse(set(signature.parameters)&{
            "arm","agent","prompt","python_source","xml","model_provider"})
        self.assertEqual(PROVENANCE,"independent-reimplementation")
        self.assertEqual(EVALUATOR_VERSION,"independent-ifc-three-axis-v0.1")

    def test_forged_official_or_dataset_origin_is_denied(self):
        for field,value in (
            ("metric_origin","official"),
            ("official_bim_edit_evaluator_equivalent",True),
            ("scored_official_dataset",True),
            ("model_provider_calls",1),
            ("scorer_version","official-v999"),
        ):
            with self.subTest(field=field):
                row=deepcopy(self.record)
                row[field]=value
                with self.assertRaises(QualificationBlocked):
                    self.verify(row)

    def test_unknown_score_field_and_missing_required_score_rejected(self):
        for mutation in ("add","delete"):
            row=deepcopy(self.record)
            if mutation=="add":
                row["official_paper_score"]=1.
            else:
                del row["semantics"]
            with self.subTest(mutation=mutation):
                with self.assertRaisesRegex(QualificationBlocked,"schema"):
                    self.verify(row)

    def test_changed_source_gt_or_result_digest_rejected(self):
        for slot in range(3):
            expected=list(self.hashes)
            expected[slot]="0"*64
            with self.subTest(slot=slot),self.assertRaisesRegex(
                QualificationBlocked,"different IFC triple"):
                self.verify(hashes=tuple(expected))

    def test_forged_final_mean_rejected(self):
        row=deepcopy(self.record)
        row["final_score"]=0.9
        with self.assertRaisesRegex(QualificationBlocked,"component-mean"):
            self.verify(row)

    def test_forged_strict_pass_without_per_axis_or_clean_collateral_rejected(self):
        row=deepcopy(self.record)
        row["geometry"]=0.5
        row["final_score"]=(0.5+row["semantics"]+row["topology"])/3
        with self.assertRaisesRegex(QualificationBlocked,"not explainable"):
            self.verify(row)
        row=deepcopy(self.record)
        row["collateral_detail"]["collateral_clean"]=False
        with self.assertRaisesRegex(QualificationBlocked,"not explainable"):
            self.verify(row)

    def test_blocked_reference_record_cannot_fabricate_scores(self):
        row=deepcopy(self.record)
        row.update(status="BLOCKED_IFC_UNIT_MISMATCH",
                   geometry=None,semantics=None,topology=None,
                   final_score=None,strict_pass=False)
        proof=self.verify(row,status="BLOCKED_IFC_UNIT_MISMATCH",passed=False)
        self.assertFalse(proof["score_fields_present"])
        row["geometry"]=0.
        with self.assertRaisesRegex(QualificationBlocked,"invented"):
            self.verify(row,status="BLOCKED_IFC_UNIT_MISMATCH",passed=False)

    def test_invalid_output_candidate_must_fail_all_three_axes(self):
        row=deepcopy(self.record)
        row.update(status="INVALID_OUTPUT_IFC",
                   geometry=0.,semantics=0.,topology=0.,
                   final_score=0.,strict_pass=False)
        self.verify(row,status="INVALID_OUTPUT_IFC",passed=False)
        row["geometry"]=0.1
        with self.assertRaisesRegex(QualificationBlocked,"fail zero"):
            self.verify(row,status="INVALID_OUTPUT_IFC",passed=False)

    def test_changed_scoring_failure_state_cannot_silently_pass(self):
        row=deepcopy(self.record)
        row["status"]="BLOCKED_IFC_UNIT_MISMATCH"
        with self.assertRaises(QualificationBlocked):
            self.verify(row)
        row=deepcopy(self.record)
        row["source_or_gt_mutated"]=True
        with self.assertRaisesRegex(QualificationBlocked,"mutated"):
            self.verify(row)

    def test_full_replay_eight_positive_negative_cases_twice(self):
        before=tuple(_sha(path) for path in (SRC,WALL_GT,CATALOG,SCHEMA_PATH))
        result=run_own_ifc_replay_qualification()
        self.assertEqual(result["case_count"],len(QUALIFICATION_CASES))
        self.assertEqual(result["case_count"],8)
        self.assertEqual(result["own_synthetic_strict_pass_cases"],3)
        self.assertTrue(result["all_repeats_identical"])
        self.assertTrue(result["all_input_output_IFC_unchanged"])
        self.assertTrue(result["all_scorer_outputs_match_frozen_json_schema"])
        self.assertFalse(result["official_equivalence_numerically_verified"])
        self.assertFalse(result["G2_G3_live_official_pilot_ready"])
        self.assertEqual(result["model_provider_calls"],0)
        self.assertEqual(result["official_benchmark_tasks_scored"],0)
        self.assertEqual(tuple(_sha(path)
                               for path in (SRC,WALL_GT,CATALOG,SCHEMA_PATH)),before)
        self.assertEqual(sum(item["strict_pass"] for item in result["cases"]),3)
        self.assertEqual(len(set(item["record_sha256"] for item in result["cases"])),8)

    def test_fixed_source_tampering_fails_before_any_artifact_is_generated(self):
        with TemporaryDirectory(prefix="fake-source-") as td:
            fake=Path(td)/"input.ifc"
            fake.write_bytes(SRC.read_bytes()+b"SUSPICIOUS_BYTES")
            with patch("src.evaluation.independent_replay_attestation.SRC",fake):
                with patch(
                    "src.evaluation.independent_replay_attestation.build_calibration_artifacts",
                    side_effect=AssertionError("No fixture generation allowed")
                ):
                    with self.assertRaisesRegex(QualificationBlocked,"modified"):
                        run_own_ifc_replay_qualification()

    def test_replay_pins_all_four_independent_metric_source_files(self):
        self.assertEqual(set(EXPECTED_LOCAL_SCORER_SOURCE_SHA256),{
            "bim_edit_scorer.py","geometry_metrics.py",
            "semantic_diff.py","topology_metrics.py"})
        with patch.dict(EXPECTED_LOCAL_SCORER_SOURCE_SHA256,
                        {"geometry_metrics.py":"0"*64}):
            with self.assertRaisesRegex(QualificationBlocked,"changed"):
                run_own_ifc_replay_qualification()

    def test_replay_refuses_catalog_modified_or_schema_modified(self):
        with TemporaryDirectory() as td:
            changed_catalog=Path(td)/"catalog.json"
            data=json.loads(CATALOG.read_text("utf8"))
            data["cases"]=data["cases"][:-1]
            changed_catalog.write_text(json.dumps(data),encoding="utf8")
            with patch("src.evaluation.independent_replay_attestation.CATALOG",
                       changed_catalog):
                with self.assertRaisesRegex(QualificationBlocked,"digest mismatch"):
                    run_own_ifc_replay_qualification()
            changed_schema=Path(td)/"schema.json"
            schema=json.loads(SCHEMA_PATH.read_text("utf8"))
            schema["title"]="Forged or accidentally changed local scorer schema"
            changed_schema.write_text(json.dumps(schema),encoding="utf8")
            with patch("src.evaluation.independent_replay_attestation.SCHEMA_PATH",
                       changed_schema):
                with self.assertRaisesRegex(QualificationBlocked,"digest mismatch"):
                    run_own_ifc_replay_qualification()


if __name__=="__main__":
    unittest.main()
