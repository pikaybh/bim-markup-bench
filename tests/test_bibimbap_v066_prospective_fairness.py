"""Issue #247: offline only/prospective 3-arm shared-read and budget tests.

No native IFC author grader, GT, LLM provider or external transfer.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import unittest

from tools import audit_bibimbap_v066_prospective_fairness as audit
from tools import bibimbap_v066_prospective_fairness_contract as fair
from tools.bibimbap_v057_provenance import (
    refuse_all_model_trials_v057, ProviderTrialBlocked057,
)
from tools.bibimbap_matched25_tools import file_hash


FROZEN_SHA="39925fa8723b276f4cf44d115db4999f5691437c9e32922370c1d72ad2bd50ee"


class FrozenThreeArmEvidence066(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(audit.REPORT.read_text("utf8"))

    def test_01_exact_new_audit_sha(self):
        self.assertEqual(file_hash(audit.REPORT),FROZEN_SHA)

    def test_02_canonical_output_bytes(self):
        self.assertEqual(audit.REPORT.read_bytes(),audit.canonical(self.report))

    def test_03_existing_door_v065_sha_unchanged(self):
        self.assertEqual(file_hash(audit.FROZEN_V065),audit.V065_SHA)

    def test_04_existing_window_v066_sha_unchanged(self):
        self.assertEqual(file_hash(audit.FROZEN_WINDOW),audit.WINDOW_SHA)

    def test_05_four_unique_developer_exposed_source_sha_families(self):
        d=self.report
        self.assertEqual(d["actual_original_developer_exposed_unique_IFC_source_SHA_clusters"],4)
        self.assertEqual(len({x["native_original_IFC_SHA256"] for x in
                              d["exposed_source_operation_byte_rows"]}),4)

    def test_06_six_source_operation_rows(self):
        self.assertEqual(self.report["actual_source_operation_rows"],6)
        self.assertEqual(len(self.report["exposed_source_operation_byte_rows"]),6)

    def test_07_actual_native_edit_families(self):
        self.assertEqual(self.report["actual_edit_family_coverage"],
                         ["create","delete","move"])

    def test_08_actual_two_native_ifc_schema_names(self):
        self.assertEqual(self.report["actual_native_schema_coverage"],
                         ["IFC2X3","IFC4X3"])

    def test_09_actual_original_ifc_file_lengths_are_local_only(self):
        self.assertTrue(all(x["original_native_IFC_file_bytes_local_only"]>500
                            for x in self.report["exposed_source_operation_byte_rows"]))

    def test_10_shared_source_read_proposed_identical_for_arms(self):
        for row in self.report["exposed_source_operation_byte_rows"]:
            arms=row["proposed_arm_submission_payloads"]
            ids={arms[arm]["source_read_envelope_SHA256"] for arm in fair.ARMS}
            self.assertEqual(len(ids),1)
            self.assertTrue(row["same_proposed_read_envelope_SHA256_for_all_three"])

    def test_11_same_ifc_source_move_delete_exact_same_proposed_read(self):
        grouped={}
        for r in self.report["exposed_source_operation_byte_rows"]:
            h=r["native_original_IFC_SHA256"]
            v=r["proposed_arm_submission_payloads"]["D_FULL"][
                "source_read_envelope_SHA256"]
            if h in grouped:self.assertEqual(grouped[h],v)
            grouped[h]=v

    def test_12_d_managed_written_submissions_smaller_all_cases(self):
        for r in self.report["exposed_source_operation_byte_rows"]:
            a=r["proposed_arm_submission_payloads"]
            self.assertLess(a["D_MANAGED"]["real_developer_control_submission"]["UTF8_bytes"],
                            a["D_FULL"]["real_developer_control_submission"]["UTF8_bytes"])

    def test_13_python_submissions_are_real_nonempty_code(self):
        for r in self.report["exposed_source_operation_byte_rows"]:
            i=r["proposed_arm_submission_payloads"]["I_NATIVE"]
            self.assertGreater(i["real_developer_control_submission"]["UTF8_bytes"],200)
            self.assertEqual(len(i["developer_control_submission_sha256"]),64)

    def test_14_precise_bytes_reported_separately_from_proxy(self):
        for r in self.report["exposed_source_operation_byte_rows"]:
            for arm in fair.ARMS:
                x=r["proposed_arm_submission_payloads"][arm]["real_developer_control_submission"]
                self.assertEqual(x["proxy_bytes_div_4_ceiling"],
                                 (x["UTF8_bytes"]+3)//4)
                self.assertEqual(x["proxy_codepoints_div_4_ceiling"],
                                 (x["unicode_codepoints"]+3)//4)
                self.assertIsNone(x["actual_provider_billed_tokens"])

    def test_15_real_provider_tokens_are_not_claimed(self):
        self.assertIsNone(self.report["actual_billed_input_output_cached_reasoning_tokens"])
        self.assertIsNone(self.report["missing_actual_tokenizer_name"])
        self.assertIsNone(self.report["prospective_design_and_hard_scientific_blockers"][
            "cost_of_actual_billed_provider_tokens"])

    def test_16_model_and_transfer_have_zero_new_calls(self):
        self.assertEqual(self.report["new_model_provider_API_calls"],0)
        self.assertFalse(self.report["source_original_IFC_uploaded_externally"])
        self.assertEqual(self.report["actual_paid_USD"],0)

    def test_17_hidden_grader_absence_and_original_rights_blocked(self):
        self.assertFalse(self.report["original_task_author_grader_or_hidden_GT_accessed"])
        p=self.report["prospective_design_and_hard_scientific_blockers"]
        self.assertFalse(p["original_IFC_per_file_external_transfer_rights_verified"])
        self.assertFalse(p["native_IFC_provider_upload_or_retention_allowed"])
        self.assertEqual(p["independently_certified_blind_original_sources"],0)

    def test_18_cost_proxy_not_billed_tokenizer(self):
        self.assertIn("not provider usage or pricing",
                      self.report["naive_token_proxy_definition"])

    def test_19_no_paid_model_activation_fields(self):
        p=self.report["prospective_design_and_hard_scientific_blockers"]
        for f in ("proposed_model_snapshot","proposed_provider_name",
                  "proposed_decoding_params","proposed_price_USD_per_million_tokens",
                  "proposed_owner_budget_USD","proposed_context_or_completion_token_cap"):
            self.assertIsNone(p[f])

    def test_20_no_premature_causal_inference_claim(self):
        p=self.report["prospective_design_and_hard_scientific_blockers"]
        self.assertFalse(p["causal_claim_representation_only_currently_admissible"])
        self.assertFalse(p["identical_source_information_to_I_runtime"])
        self.assertFalse(p["same_native_operation_capabilities_D_vs_I"])

    def test_21_research_is_only_prospective(self):
        self.assertEqual(self.report["audit_kind"],"PROSPECTIVE_NOT_ACTIVE_OR_PREREGISTERED_MODEL_TRIAL")
        self.assertFalse(self.report["prospective_design_and_hard_scientific_blockers"][
            "frozen_cohort_selected_for_confirmatory_study"])

    def test_22_proposed_exact_tool_schema_sha_matches_source_code(self):
        for arm in fair.ARMS:
            real=sha256(fair.model_tool_schema_bytes(arm)).hexdigest()
            self.assertEqual(self.report["proposed_tool_schema_SHA256_by_arm"][arm],real)
            self.assertEqual(
                self.report["proposed_tool_schema_metrics_by_arm"][arm]["UTF8_bytes"],
                len(fair.model_tool_schema_bytes(arm)))

    def test_23_prospective_tool_contract_sha_bound(self):
        self.assertEqual(file_hash(Path(fair.__file__)),
                         self.report["proposed_tool_contract_source_SHA256"])

    def test_24_all_tools_two_per_arm_and_common_read_is_identical(self):
        self.assertEqual(len(fair.ARMS),3)
        self.assertTrue(all(len(fair.TOOLSETS[a])==2 for a in fair.ARMS))
        self.assertEqual(len({fair.canonical_bytes(fair.TOOLSETS[a][0])
                              for a in fair.ARMS}),1)

    def test_25_real_provenance_source_anchored_sha(self):
        self.assertTrue(all(r["real_original_IFC_file_SHA256_rechecked"]
                            for r in self.report["exposed_source_operation_byte_rows"]))


class ProspectiveBudgetAndLeakage066(unittest.TestCase):
    def test_26_one_shot_exact_two_calls_all_three_arms(self):
        for arm in fair.ARMS:
            ledger=fair.OfflineBudgetLedger(arm,"one_shot")
            self.assertEqual(ledger.read()["status"],"source_read_ok")
            out=ledger.submit("admitted_native_scope")
            self.assertEqual(out["status"],"trial_finalized")
            self.assertFalse(out["feedback_visible_during_generation"])
            self.assertEqual(ledger.finalize()["actual_tool_calls"],2)

    def test_27_iterative_exact_25_calls_and_24_attempts(self):
        for arm in fair.ARMS:
            ledger=fair.OfflineBudgetLedger(arm,"feedback")
            ledger.read()
            for i in range(24):
                result=ledger.submit("invalid_submission")
                self.assertEqual(result["attempts_remaining"],23-i)
                self.assertIsNone(result["author_task_score"])
            self.assertEqual(ledger.finalize()["actual_tool_calls"],25)

    def test_28_read_twice_not_allowed(self):
        s=fair.OfflineBudgetLedger("D_FULL","feedback")
        s.read()
        with self.assertRaises(fair.ProspectiveProtocolBlocked):s.read()

    def test_29_submission_before_read_rejected(self):
        s=fair.OfflineBudgetLedger("I_NATIVE","feedback")
        with self.assertRaises(fair.ProspectiveProtocolBlocked):
            s.submit("admitted_native_scope")

    def test_30_budget_overspend_rejected(self):
        s=fair.OfflineBudgetLedger("D_MANAGED","feedback")
        s.read()
        for _ in range(24):s.submit("native_scope_rejected")
        with self.assertRaises(fair.ProspectiveProtocolBlocked):
            s.submit("native_scope_rejected")

    def test_31_one_shot_retry_rejected(self):
        s=fair.OfflineBudgetLedger("D_FULL","one_shot")
        s.read();s.submit("native_execution_failure")
        with self.assertRaises(fair.ProspectiveProtocolBlocked):
            s.submit("native_execution_failure")

    def test_32_illegal_arm_or_regime_rejected(self):
        for args in (("D_XML","feedback"),("D_FULL","extra")):
            with self.assertRaises(fair.ProspectiveProtocolBlocked):
                fair.OfflineBudgetLedger(*args)

    def test_33_raw_traceback_must_not_reach_LLM(self):
        s=fair.OfflineBudgetLedger("I_NATIVE","feedback")
        s.read()
        for invalid in ("Traceback (most recent call last)",{"traceback":"SECRET"},
                        "author_task_score:1.0","invalid_submission\nPRIVATE"):
            with self.assertRaises(fair.ProspectiveProtocolBlocked):
                s.submit(invalid)
        self.assertEqual(s.attempts,0)

    def test_34_no_grader_fields_or_target_in_proposed_tool_contract(self):
        tools=fair.canonical_bytes(fair.TOOLSETS)
        for forbidden in (b"geometry_test_13",b"geometry_test_19",
                          b"private_target_GUID",b"author_grader",
                          b"reference_solution",b"model_provider_API_key"):
            self.assertNotIn(forbidden,tools)

    def test_35_read_only_shared_source_XML_binds_SHA(self):
        x=fair.common_read_envelope(
            original_sha="a"*64,original_schema="IFC4X3",
            full_xml=b'<?xml version="1.0"?><BuildingState>'+b'x'*120+b'</BuildingState>',
            managed_xml=b'<?xml version="1.0"?><ManagedFinalState>'+b'x'*120+b'</ManagedFinalState>')
        self.assertEqual(x["source_sha256"],"a"*64)
        self.assertIsNone(x["author_task_score"])

    def test_36_bad_original_source_SHA_rejected(self):
        with self.assertRaises(fair.ProspectiveProtocolBlocked):
            fair.common_read_envelope(
                original_sha="NOT_A_SHA",original_schema="IFC4X3",
                full_xml=b'<?xml version="1.0"?><BuildingState/>',
                managed_xml=b'<?xml version="1.0"?><ManagedFinalState/>')

    def test_37_private_GT_in_read_rejected(self):
        with self.assertRaises(fair.ProspectiveProtocolBlocked):
            fair.common_read_envelope(
                original_sha="b"*64,original_schema="IFC4X3",
                full_xml=b'<?xml version="1.0"?><BuildingState>PRIVATE_GT</BuildingState>',
                managed_xml=b'<?xml version="1.0"?><ManagedFinalState/>')

    def test_38_provider_rights_forgery_cannot_launch(self):
        with self.assertRaises(ProviderTrialBlocked057):
            refuse_all_model_trials_v057({
                "paid_cap_USD":100000,
                "all_rights_certified":True,
                "provider":"claimed",
            })

    def test_39_truly_pure_contract_no_network_or_model_activation(self):
        src=Path(fair.__file__).read_text("utf8")
        for forbidden in ("from openai import","import openai","requests.post(",
                          "urllib.request.urlopen(","subprocess.run(",
                          "def launch_trial(","def call_model("):
            self.assertNotIn(forbidden,src)

    def test_40_feedback_transcript_contains_no_score(self):
        s=fair.OfflineBudgetLedger("I_NATIVE","feedback")
        s.read()
        p=s.submit("admitted_native_scope")
        self.assertEqual(set(p),{"status","coarse_engine_outcome",
                                 "attempts_remaining","author_task_score"})
        self.assertIsNone(p["author_task_score"])

    def test_41_metric_is_actual_utf8_not_provider_toks(self):
        x=fair.byte_metrics("가나다".encode("utf8"))
        self.assertEqual(x["UTF8_bytes"],9)
        self.assertEqual(x["unicode_codepoints"],3)
        self.assertEqual(x["proxy_bytes_div_4_ceiling"],3)
        self.assertEqual(x["proxy_codepoints_div_4_ceiling"],1)
        self.assertIsNone(x["actual_provider_billed_tokens"])

    def test_42_bad_utf8_and_invalid_tool_arm_block(self):
        with self.assertRaises(UnicodeDecodeError):
            fair.byte_metrics(b"\xff")
        with self.assertRaises(fair.ProspectiveProtocolBlocked):
            fair.model_tool_schema_bytes("HIDDEN")

    def test_43_cannot_finalize_without_read_and_submission(self):
        for arm in fair.ARMS:
            s=fair.OfflineBudgetLedger(arm,"feedback")
            with self.assertRaises(fair.ProspectiveProtocolBlocked):s.finalize()
            s.read()
            with self.assertRaises(fair.ProspectiveProtocolBlocked):s.finalize()

    def test_44_cannot_read_again_after_submission(self):
        s=fair.OfflineBudgetLedger("D_FULL","feedback")
        s.read();s.submit("admitted_native_scope")
        with self.assertRaises(fair.ProspectiveProtocolBlocked):s.read()

    def test_45_an_invalid_feedback_never_spends_attempt_quota(self):
        s=fair.OfflineBudgetLedger("D_FULL","feedback");s.read()
        with self.assertRaises(fair.ProspectiveProtocolBlocked):
            s.submit(100)
        self.assertEqual((s.calls,s.attempts),(1,0))


if __name__=="__main__":
    unittest.main()
