"""v0.20 original all45 frozen evidence + terminal submission offline tests.

No IfcOpenShell, Docker launch, original author code or LLM provider is needed.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import ast
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.bibimbap_v020_original45_capability_gate import (
    AUTHOR_SHA, DATA_SHA, EVIDENCE, FROZEN_AUTHOR_BLOCKED,
    FROZEN_AUTHOR_SCORABLE, FROZEN_NATIVE_EQUAL, ROOT,
    CapabilityGateBlocked, build_original45_capability_gate,
    load_frozen_evidence,
)
from tools.bibimbap_v020_terminal_submission_broker import (
    OfflineTerminalOneShotBroker, PUBLIC_TERMINAL_RECEIPT,
    TerminalSubmissionBlocked, offline_terminal_noninterference_audit,
)

REPORT = ROOT / "reports/bibimbap_v020_original45_capability_and_terminal_gate_20261115.json"
REPORT_SHA = "1aa218a0883186e6df1e7e7d895670fb9e012ef0229799b14881a87473f762be"


class V020OriginalCapabilityAndSubmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = load_frozen_evidence(ROOT)
        cls.matrix = build_original45_capability_gate(cls.inputs)
        if not REPORT.is_file():
            raise unittest.SkipTest("Frozen v020 generated matrix report missing")
        cls.frozen = json.loads(REPORT.read_text(encoding="utf8"))

    def test_all_five_frozen_report_sha256_pins_verified(self):
        self.assertEqual(set(self.inputs),set(EVIDENCE))
        for name,(relative, expected) in EVIDENCE.items():
            with self.subTest(name=name):
                self.assertEqual(sha256((ROOT/relative).read_bytes()).hexdigest(),expected)
        self.assertEqual(sha256(REPORT.read_bytes()).hexdigest(),REPORT_SHA)

    def test_derivation_deterministic_and_identical_to_frozen_45_report(self):
        self.assertEqual(self.matrix,self.frozen)
        self.assertEqual(
            json.dumps(self.matrix,ensure_ascii=False,sort_keys=True,indent=2)+"\n",
            REPORT.read_text(encoding="utf8"))
        self.assertTrue(self.matrix["original_denominator_45_preserved"])
        self.assertEqual(len(self.matrix["all45_original_public_task_capability_matrix"]),45)

    def test_original_45_composition_and_source_schema_preserved(self):
        result=self.matrix
        self.assertEqual(result["pinned_original_author_git_sha"],AUTHOR_SHA)
        self.assertEqual(result["pinned_original_public_data_git_sha"],DATA_SHA)
        self.assertEqual(result["original_15_per_crud"],
                         {"create":15,"update":15,"delete":15})
        self.assertEqual(result["original_3_categories_15_per_category"],
                         {"basic":15,"geometry":15,"topological":15})
        self.assertEqual(result["original_schema_counts"],
                         {"IFC2X3":2,"IFC4":1,"IFC4X3":42})

    def test_frozen_source_read_equal_for_all45_but_not_full_information(self):
        self.assertEqual(self.matrix["original45_with_IDENTICAL_common_source_read_replay"],45)
        self.assertEqual(self.matrix["original45_with_incomplete_typed_native_product_observation"],45)
        self.assertEqual(self.matrix["original45_WITH_PROVEN_FULL_IFC_INFORMATION_PARITY"],0)
        self.assertEqual(self.matrix["original45_WITH_PROVEN_FULL_NATIVE_WRITE_CAPABILITY_PARITY"],0)
        for row in self.matrix["all45_original_public_task_capability_matrix"]:
            with self.subTest(id=row["task_id"]):
                self.assertGreater(row["original_native_products_omitted_from_typed_XML"],0)
                self.assertEqual(row["relevance_of_omitted_products_to_task"],"NOT_ESTABLISHED")
                self.assertEqual(row["original_native_full_source_information_parity"],"NOT_PROVEN")
                self.assertEqual(row["full_two_arm_native_write_capability_equivalence"],"NOT_PROVEN")
                self.assertEqual(row["actual_common_public_source_read_responses"],
                                 "D_AND_I_IDENTICAL_FROZEN_QUERY_REPLAY")
                self.assertEqual(row["real_matched_LLM_trial"],"NOT_RUN")
                self.assertTrue(row["original45_intention_to_test_denominator_member"])
                self.assertFalse(row["unsupported_task_inferred_from_missing_evidence"])
                self.assertFalse(row["failed_task_inferred_from_missing_evidence"])

    def test_only_five_native_equal_developer_cases_not_all45(self):
        rows=self.matrix["all45_original_public_task_capability_matrix"]
        paired={x["task_id"] for x in rows if
                x["actual_developer_native_IFC_byte_equivalence"] ==
                "PROVEN_ON_ORIGINAL_PUBLIC_TASK"}
        self.assertEqual(paired,FROZEN_NATIVE_EQUAL)
        self.assertEqual(self.matrix["original45_developer_both_arm_native_IFC_byte_equivalence"],5)
        self.assertEqual(self.matrix["original45_same_protocol_not_yet_evaluated"],40)
        self.assertEqual(len(rows)-len(paired),40)

    def test_scored_three_author_reference_broken_two_not_failures(self):
        rows=self.matrix["all45_original_public_task_capability_matrix"]
        scores={x["task_id"]:x["actual_original_author_scoring"] for x in rows}
        self.assertEqual(
            {t for t,s in scores.items() if s=="BOTH_ARMS_SCORED"},
            FROZEN_AUTHOR_SCORABLE)
        self.assertEqual(
            {t for t,s in scores.items() if s=="PINNED_AUTHOR_REFERENCE_SOURCE_MISMATCH"},
            FROZEN_AUTHOR_BLOCKED)
        self.assertEqual(sum(s=="NOT_EVALUATED" for s in scores.values()),40)
        self.assertEqual(self.matrix["original45_original_author_scorer_mismatched_reference"],2)
        self.assertEqual(self.matrix["original45_author_scorable_developer_both_arm"],3)

    def test_only_existing_original_test15_sealed_developer_witness(self):
        rows=self.matrix["all45_original_public_task_capability_matrix"]
        sealed=[r for r in rows if r["sealed_own_developer_Python_execution"]!="NOT_TESTED"]
        self.assertEqual(len(sealed),1)
        self.assertEqual(sealed[0]["task_id"],"test_15")
        self.assertEqual(self.matrix["original45_developer_sealed_Python_native_edit_with_author_score"],1)
        self.assertEqual(self.matrix["new_real_matched_LLM_D_I_trials"],0)
        self.assertEqual(self.matrix["new_paid_provider_calls"],0)
        self.assertEqual(self.matrix["new_paid_usd"],0)

    def test_fail_closed_explicit_blockers_not_pilot_ready(self):
        self.assertFalse(self.matrix["any_paid_or_unpaid_real_LLM_launch_permitted"])
        self.assertFalse(self.matrix["causal_XML_vs_Python_pure_representation_performance_claim_permitted"])
        self.assertIn("NO_EXPLICIT_APPROVED_MODEL_AND_PAID_PROVIDER_BUDGET",self.matrix["explicit_blockers"])
        self.assertIn("FULL_ORIGINAL_NATIVE_WRITE_CAPABILITY_PARITY_UNVERIFIED_ALL45",
                      self.matrix["explicit_blockers"])
        self.assertIn("NO_REAL_BLINDED_PAIRED_LLM_TRIALS",self.matrix["explicit_blockers"])

    def test_tampered_original_id_duplicate_and_missing_are_rejected(self):
        changed=deepcopy(self.inputs)
        rows=changed["v016"]["original45_intention_to_test_matrix"]
        rows[1]["task_id"]=rows[0]["task_id"]
        with self.assertRaises(CapabilityGateBlocked):
            build_original45_capability_gate(changed)
        changed=deepcopy(self.inputs)
        changed["v018"]["all_45_public_task_read_observation_audit"].pop()
        with self.assertRaises(CapabilityGateBlocked):
            build_original45_capability_gate(changed)

    def test_tampered_public_question_or_source_sha_rejected(self):
        changed=deepcopy(self.inputs)
        changed["v017_native"]["all_45_public_intention_to_test"][0]["public_question_sha256"]="0"*64
        with self.assertRaises(CapabilityGateBlocked):
            build_original45_capability_gate(changed)
        changed=deepcopy(self.inputs)
        changed["v017_information"]["all_45_task_information_parity_audit"][0]["original_public_ifc_sha256"]="0"*64
        with self.assertRaises(CapabilityGateBlocked):
            build_original45_capability_gate(changed)

    def test_false_or_missing_read_parity_and_fake_scorer_greening_rejected(self):
        changed=deepcopy(self.inputs)
        changed["v018"]["common_read_observation_bytes_equal_across_45_tasks"]=False
        with self.assertRaises(CapabilityGateBlocked):
            build_original45_capability_gate(changed)
        changed=deepcopy(self.inputs)
        changed["v017_native"]["all_45_public_intention_to_test"][0]["new_scoring_status"]="AUTHOR_SCORED_BOTH_DEVELOPER_ARMS"
        with self.assertRaises(CapabilityGateBlocked):
            build_original45_capability_gate(changed)
        changed=deepcopy(self.inputs)
        changed["v017_native"]["original_author_scoreable_both_dev_arms_total"]=4
        with self.assertRaises(CapabilityGateBlocked):
            build_original45_capability_gate(changed)

    def test_fake_native_product_inventory_zero_and_schema_drift_rejected(self):
        changed=deepcopy(self.inputs)
        changed["v017_information"]["all_45_task_information_parity_audit"][0]["native_original_products_not_in_safe_typed_XML"]=0
        with self.assertRaises(CapabilityGateBlocked):
            build_original45_capability_gate(changed)
        changed=deepcopy(self.inputs)
        changed["v018"]["all_45_public_task_read_observation_audit"][0]["actual_original_IFC_schema"]="IFC4"
        with self.assertRaises(CapabilityGateBlocked):
            build_original45_capability_gate(changed)

    def test_fake_paid_LLM_call_evidence_rejected(self):
        changed=deepcopy(self.inputs)
        changed["v017_native"]["all_45_public_intention_to_test"][0]["new_real_matched_LLM_D_I_result"]={"score":1.0}
        with self.assertRaises(CapabilityGateBlocked):
            build_original45_capability_gate(changed)
        changed=deepcopy(self.inputs)
        changed["v019"]["real_model_generated_python_executed"]=True
        with self.assertRaises(CapabilityGateBlocked):
            build_original45_capability_gate(changed)

    def test_tampered_frozen_report_bytes_sha_fail_closed(self):
        with TemporaryDirectory(prefix="bmb-v020-frozen-sha-") as d:
            root=Path(d)
            for rel,_ in EVIDENCE.values():
                target=root/rel
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((ROOT/rel).read_bytes())
            rel,_=EVIDENCE["v018"]
            candidate=root/rel
            candidate.write_bytes(candidate.read_bytes()+b" ")
            with self.assertRaises(CapabilityGateBlocked):
                load_frozen_evidence(root)

    def test_terminal_offline_receipt_constant_with_two_different_payloads(self):
        audit=offline_terminal_noninterference_audit()
        self.assertEqual(audit,self.matrix["offline_terminal_one_shot_noninterference"])
        self.assertEqual(audit["status"],"OFFLINE_TERMINAL_ONE_SHOT_NONINTERFERENCE_PASS")
        self.assertTrue(audit["public_receipt_byte_identical_across_different_code_and_host_results"])
        self.assertEqual(json.loads(PUBLIC_TERMINAL_RECEIPT),audit["constant_public_receipt"])
        self.assertFalse(audit["real_model_transport_implemented"])
        self.assertFalse(audit["real_security_sandbox_attestation_from_this_test"])

    def test_broker_one_shot_submission_and_private_outcome_noninterference(self):
        s=OfflineTerminalOneShotBroker(public_source_packet_sha256="a"*64)
        self.assertFalse(s.terminal)
        receipt=s.submit_once(b"print('SECRET_RESULT')\n")
        self.assertTrue(s.terminal)
        self.assertEqual(receipt,PUBLIC_TERMINAL_RECEIPT)
        private=s.host_only_record_outcome("VERY_PRIVATE_ORIGINAL_AUTHOR_GRADE",
                                           origin="trusted_offline_host")
        self.assertEqual(private.trusted_host_outcome,"VERY_PRIVATE_ORIGINAL_AUTHOR_GRADE")
        self.assertNotIn("VERY_PRIVATE_ORIGINAL_AUTHOR_GRADE",receipt)
        self.assertNotIn(private.developer_or_model_candidate_sha256,receipt)
        with self.assertRaises(TerminalSubmissionBlocked):
            s.model_request_result()
        with self.assertRaises(TerminalSubmissionBlocked):
            s.ask_model_for_continuation()
        with self.assertRaises(TerminalSubmissionBlocked):
            s.submit_once(b"print('RETRY')\n")
        with self.assertRaises(TerminalSubmissionBlocked):
            s.host_only_record_outcome("SECOND_GRADE",origin="trusted_offline_host")
        self.assertEqual(s.attempted_executions,0)

    def test_broker_no_private_host_outcome_before_submission_or_untrusted_origin(self):
        s=OfflineTerminalOneShotBroker(public_source_packet_sha256="a"*64)
        with self.assertRaises(TerminalSubmissionBlocked):
            s.host_only_record_outcome("GRADE",origin="trusted_offline_host")
        s.submit_once(b"print('ok')\n")
        with self.assertRaises(TerminalSubmissionBlocked):
            s.host_only_record_outcome("GRADE",origin="untrusted_model")
        self.assertTrue(s.terminal)
        self.assertEqual(s.attempted_executions,0)

    def test_broker_rejects_invalid_unicode_null_empty_and_oversized_scripts(self):
        for source in (b"",b"\x00",b"\xff",b"x"*(64*1024+1), "notbytes"):
            s=OfflineTerminalOneShotBroker(public_source_packet_sha256="a"*64)
            with self.subTest(source_type=type(source).__name__,length=len(source)),self.assertRaises(TerminalSubmissionBlocked):
                s.submit_once(source)
            self.assertFalse(s.terminal)
        for bad in ("a", "A"*64,"z"*64,"x"*63):
            with self.assertRaises(TerminalSubmissionBlocked):
                OfflineTerminalOneShotBroker(public_source_packet_sha256=bad)

    def test_broker_not_an_unauthorized_python_or_model_executor(self):
        source=Path(__file__).resolve().parents[1]/"tools/bibimbap_v020_terminal_submission_broker.py"
        program=ast.parse(source.read_text(encoding="utf8"))
        imports=[]
        for node in ast.walk(program):
            if isinstance(node,ast.Import): imports.extend(x.name for x in node.names)
            elif isinstance(node,ast.ImportFrom): imports.append(node.module or "")
        self.assertFalse(any(x.startswith(("ifcopenshell","subprocess","docker",
                                          "openai","src.runner")) for x in imports))
        self.assertFalse(any(isinstance(x,ast.Call) and isinstance(x.func,ast.Name)
                             and x.func.id in ("exec","eval","compile") for x in ast.walk(program)))

    def test_original_git_scorer_and_IFC_not_invoked_by_v020_audit(self):
        gate=(ROOT/"tools/bibimbap_v020_original45_capability_gate.py").read_text(encoding="utf8")
        self.assertNotIn("grade_author(",gate)
        self.assertNotIn("ifcopenshell.open",gate)
        self.assertNotIn("DockerIFCExecutor(",gate)
        self.assertFalse(self.matrix["any_paid_or_unpaid_real_LLM_launch_permitted"])


if __name__=="__main__":
    unittest.main()
