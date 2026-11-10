"""G1 #16: source-only 36-task readiness reconciler, positive/negative.

No IFC GT, model provider, evaluator, agent workspace or network touched
by these tests. Real cached input IFCs are checked only by the separate
one-shot CLI integration audit, not by the in-memory failure fixtures.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
import unittest

from src.data.bim_edit import AuditError
from src.evaluation.frozen_pilot_readiness import (
    ROOT,FROZEN_FILES,EXPECTED_MANUAL_IDS,
    load_pinned_evidence,reconcile_pilot_evidence,
)

WORKER={
    "status":"BLOCKED_LOCAL_DOCKER_ENGINE_UNAVAILABLE",
    "local_engine_reachable":False,
    "real_candidate_execution_authorized":False,
    "paid_model_run_authorized":False,
    "worker_os_isolation_currently_verified":False,
}


class FrozenPilotReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen=load_pinned_evidence()

    def setUp(self):
        self.docs=deepcopy(self.frozen)
        self.current=deepcopy(self.docs["g1_36"])
        self.worker=deepcopy(WORKER)

    def run_reconciliation(self):
        return reconcile_pilot_evidence(
            self.docs,self.current,
            worker_observation=self.worker,
            official_scorer=self.docs["official"],
            budget=self.docs["budget"],
        )

    def test_positive_all_36_sample_slots_accounted_for_without_support_claim(self):
        result=self.run_reconciliation()
        self.assertEqual(result["task_count"],36)
        self.assertEqual(result["static_metadata_task_count"],324)
        self.assertEqual(result["static_engine_unsupported_count"],23)
        self.assertEqual(result["conditional_source_task_count"],13)
        self.assertEqual(result["currently_cached_conditional_input_probed_count"],11)
        self.assertEqual(result["missing_conditional_input_count"],2)
        self.assertEqual(result["historical_verified_input_and_reference_deltas_count"],30)
        self.assertEqual(result["historical_unavailable_source_or_GT_asset_count"],6)
        self.assertEqual(result["distinct_manual_source_only_pair_task_count"],2)
        self.assertEqual(result["full_instruction_specific_paired_D0_I0_task_oracles_proven"],0)
        self.assertFalse(result["historical_asset_evidence_reverified_now"])
        self.assertEqual(result["official_task_scores"],0)
        self.assertEqual(result["real_model_provider_calls"],0)
        self.assertFalse(result["paid_or_official_pilot_approved"])
        self.assertEqual(result["disposition_counts"],{
            "STATIC_ENGINE_UNSUPPORTED":23,
            "INPUT_IFC_NOT_CACHED":2,
            "SOURCE_DEPENDENCY_OR_ORACLE_BLOCKED":9,
            "MANUAL_SOURCE_ONLY_EVIDENCE_WITH_GATES":2,
        })

    def test_manual_evidence_is_distinct_tasks_and_never_promoted_to_full(self):
        result=self.run_reconciliation()
        manual={r["task_id"]:r for r in result["tasks"]
                if r["manual_evidence_code"] is not None}
        self.assertEqual(set(manual),EXPECTED_MANUAL_IDS)
        self.assertEqual(
            manual["WIN-UPD-DIR-A-002"]["manual_evidence_code"],
            "MANUAL_VECTOR_SELECTED_SOURCE_ONLY_PARITY_NOT_FULL_TASK")
        self.assertEqual(
            manual["WAL-CRE-SPA-A-003"]["manual_evidence_code"],
            "EXPERIMENTAL_V02_SPACE_NATIVE_PARITY_NOT_MODEL_FACING")
        self.assertTrue(all(not row["task_oracle_fully_proven"]
                            for row in manual.values()))
        self.assertTrue(all(not row["same_information_D0_I0_model_facing_approved"]
                            for row in manual.values()))

    def test_output_redacts_sensitive_source_GT_paths_guid_prompts_and_raw_models(self):
        report=json.dumps(self.run_reconciliation(),sort_keys=True)
        for forbidden in (
            "ground_truth_ifc",
            "trusted_manual_target_selection",
            "reference_expected_bytes",
            "world_translation_m",
            "target_guids",
            "prompt",
            "source_ifc_path",
            "model_output_text",
            "native_space_boundary_guids",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn('"'+forbidden+'"',report)
        self.assertEqual(len({r["task_id"] for r in
                              self.run_reconciliation()["tasks"]}),36)
        self.assertFalse(self.run_reconciliation()[
            "ground_truth_IFC_opened_by_this_reconciler"])

    def test_candidate_not_preregistered_and_not_paid_guard_mandatory(self):
        self.docs["candidate"]["status"]="PREREGISTERED"
        with self.assertRaises(AuditError):
            self.run_reconciliation()
        self.setUp()
        self.docs["candidate"]["gate_status"]["BUDGET"]="APPROVED"
        with self.assertRaises(AuditError):
            self.run_reconciliation()

    def test_mismatched_public_task_ids_duplicate_and_removed_source_row_rejected(self):
        self.docs["candidate"]["tasks"][0]["task_id"]=self.docs["candidate"]["tasks"][1]["task_id"]
        with self.assertRaisesRegex(AuditError,"duplicated"):
            self.run_reconciliation()
        self.setUp()
        self.docs["g1_36"]["tasks"].pop()
        self.current=deepcopy(self.docs["g1_36"])
        with self.assertRaises(AuditError):
            self.run_reconciliation()
        self.setUp()
        self.docs["assets"]["tasks"][0]["task_id"]="WAL-CRE-DIR-A-999"
        with self.assertRaises(AuditError):
            self.run_reconciliation()

    def test_live_native_probe_status_drift_not_silently_reclassified(self):
        self.current["tasks"][0]["reason_code"]="NEW_CAPABILITY_SUCCESS"
        with self.assertRaisesRegex(AuditError,"live source-only audit drifted"):
            self.run_reconciliation()

    def test_static_support_claim_count_forgery_rejected(self):
        self.docs["g1_324"]["static_engine_unsupported_count"]=0
        with self.assertRaises(AuditError):
            self.run_reconciliation()
        self.setUp()
        self.docs["g1_324"]["tasks"][0]["target_class"]="IfcSite"
        # The changed row may not be one of the 36, so force a picked ID.
        chosen=self.docs["candidate"]["tasks"][0]["task_id"]
        entry=next(r for r in self.docs["g1_324"]["tasks"]
                   if r["task_id"]==chosen)
        entry["target_class"]="IfcSite"
        with self.assertRaisesRegex(AuditError,"metadata cross-ledger"):
            self.run_reconciliation()

    def test_source_reason_count_manipulation_rejected(self):
        self.docs["g1_36"]["fail_closed_reason_counts"]["STATIC_ENGINE_UNSUPPORTED"]=0
        self.current=deepcopy(self.docs["g1_36"])
        with self.assertRaisesRegex(AuditError,"reason code totals"):
            self.run_reconciliation()

    def test_past_reference_asset_count_not_conflated_with_live_GT_check(self):
        self.docs["assets"]["task_status_counts"]["VERIFIED_PINNED_BYTES_AND_CLASS_DELTA"]=36
        with self.assertRaises(AuditError):
            self.run_reconciliation()
        self.setUp()
        # A forged successful GT state on a missing dataset pair is rejected.
        row=next(r for r in self.docs["assets"]["tasks"]
                 if r["status"]=="MISSING_LOCAL_IFC_BYTES")
        row["status"]="VERIFIED_PINNED_BYTES_AND_CLASS_DELTA"
        with self.assertRaises(AuditError):
            self.run_reconciliation()

    def test_manual_window_parity_false_or_model_calls_forged_blocks(self):
        self.docs["manual_window"]["paired_independent_ifc_observation_parity"]=False
        with self.assertRaisesRegex(AuditError,"manually selected window"):
            self.run_reconciliation()
        self.setUp()
        self.docs["manual_window"]["paid_model_calls"]=1
        with self.assertRaises(AuditError):
            self.run_reconciliation()

    def test_manual_wall_information_equivalence_not_false_approval(self):
        self.docs["manual_wall"]["input_information_equivalence_proven"]=True
        with self.assertRaisesRegex(AuditError,"wall D0/I0"):
            self.run_reconciliation()
        self.setUp()
        self.docs["manual_wall"]["official_tasks_scored"]=1
        with self.assertRaises(AuditError):
            self.run_reconciliation()

    def test_experimental_v02_cannot_be_promoted_to_model_facing(self):
        self.docs["manual_wall_v02"]["model_facing_v02_promoted"]=True
        with self.assertRaisesRegex(AuditError,"v0.2 space"):
            self.run_reconciliation()
        self.setUp()
        self.docs["manual_wall_v02"]["full_native_space_semantics_proven"]=True
        with self.assertRaises(AuditError):
            self.run_reconciliation()

    def test_worker_probe_ready_does_not_grant_live_trial(self):
        self.worker.update(status="READY_FOR_TRUSTED_OWN_PROBE_ONLY_NOT_GENERATED_PYTHON",
                           local_engine_reachable=True)
        result=self.run_reconciliation()
        self.assertFalse(result["paid_or_official_pilot_approved"])
        self.assertEqual(result["official_task_scores"],0)
        self.assertEqual(result["full_instruction_specific_paired_D0_I0_task_oracles_proven"],0)

    def test_invalid_docker_worker_execution_claim_refuses(self):
        self.worker["real_candidate_execution_authorized"]=True
        with self.assertRaises(AuditError):
            self.run_reconciliation()
        self.setUp()
        self.worker["worker_os_isolation_currently_verified"]=True
        with self.assertRaises(AuditError):
            self.run_reconciliation()

    def test_official_scorer_or_billed_model_fake_approval_blocks(self):
        self.docs["official"]["official_executable_scorer_available_to_this_project"]=True
        with self.assertRaisesRegex(AuditError,"official scorer"):
            self.run_reconciliation()
        self.setUp()
        self.docs["budget"]["full_g2_or_g3_live_release_authorized"]=True
        with self.assertRaisesRegex(AuditError,"paid model"):
            self.run_reconciliation()

    def test_pinned_manifest_or_manual_report_byte_tampering_fails_before_reconciliation(self):
        with TemporaryDirectory(prefix="pilot-frozen-report-tamper-") as td:
            base=Path(td)
            for rel,_ in FROZEN_FILES.values():
                source=ROOT/rel
                copy=base/rel
                copy.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source,copy)
            self.assertEqual(set(load_pinned_evidence(root=base)),set(FROZEN_FILES))
            altered=base/FROZEN_FILES["manual_wall_v02"][0]
            with altered.open("ab") as f:
                f.write(b" ")
            with self.assertRaisesRegex(AuditError,"digest mismatch"):
                load_pinned_evidence(root=base)

    def test_no_additional_pilot_subset_selection_or_scoring(self):
        result=self.run_reconciliation()
        self.assertEqual(result["op_counts"],{
            "create":12,"delete":12,"update":12})
        self.assertEqual(result["category_counts"],{
            "direct":12,"spatial":12,"topological":12})
        self.assertEqual(result["scene_counts"],{
            "scene:A":18,"scene:R":18})
        self.assertTrue(all(not row["official_benchmark_task_scored"]
                            for row in result["tasks"]))
        self.assertFalse(result["model_provider_price_and_token_usage_approved"])


if __name__=="__main__":
    unittest.main()
