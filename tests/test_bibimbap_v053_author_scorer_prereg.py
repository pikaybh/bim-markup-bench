"""v0.53 genuine-primary DI prereg/no-launch and author-origin scorer evidence.

Everything is offline. No provider, paid model trial or original-author
paper-results claim. Private evaluator source and target GUIDs are NEVER
imported by the model-facing protocol or authored into a prompt.
"""
from __future__ import annotations

from collections import Counter,defaultdict
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v050_direct_original_state_session import (
    DirectOriginalStateSession050,
)
from tools.bibimbap_v052_live_original_native_python_session import (
    LiveOriginalNativePythonSession052,
)
from tools import audit_bibimbap_v053_original_author_provenance as author
from tools import audit_bibimbap_v053_paired_prereg_gate as gate


AUTHOR_SHA="40742725e59f7b0909f2d1ff061a7d68bcfcf1f35da829c3d15d0624928366e4"
GATE_SHA="600a951bfb0733a79f09e9db43376526ceaa9e1a66cc3e800e2ca00601862524"


class OriginalFourPrimaryDIPreregistration053(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.author=json.loads(author.REPORT.read_text(encoding="utf8"))
        cls.gate=json.loads(gate.REPORT.read_text(encoding="utf8"))
        cls.tasks={r["test_id"]:r for r in
                   public_45(author.AUTHOR,author.DATA)}

    def test_01_author_origin_report_frozen_sha(self):
        self.assertEqual(file_hash(author.REPORT),AUTHOR_SHA)

    def test_02_primary_DI_prereg_candidate_frozen_sha(self):
        self.assertEqual(file_hash(gate.REPORT),GATE_SHA)

    def test_03_prior_live_Docker_original_IFC_SHA_unchanged(self):
        self.assertEqual(file_hash(author.ROOT/"reports"/
            "bibimbap_v052_original4_live_docker_python_attestation_20261118.json"),
            author.V052_REPORT_SHA)

    def test_04_original_population_not_posthoc_renamed(self):
        self.assertEqual(len(self.tasks),45)
        self.assertEqual(len({r["original_ifc_sha256"]
                              for r in self.tasks.values()}),31)
        self.assertEqual(Counter(r["crud"] for r in self.tasks.values()),
                         {"create":15,"update":15,"delete":15})

    def test_05_selected_four_engineered_not_preregistered_random_sample(self):
        self.assertEqual(len(author.TASKS),4)
        self.assertTrue(self.gate["not_a_formally_preregistered_or_random_original_cohort"])
        self.assertEqual(self.gate["ITT_denominator_when_authorized"],4)
        self.assertEqual(self.gate["full_population_unattempted_tasks"],41)

    def test_06_four_original_author_test_modules_pinned(self):
        proof=self.author["author_scorer_provenance"]
        self.assertEqual(proof["original_author_git_head"],
                         author.EXPECTED_AUTHOR_HEAD)
        self.assertEqual(len(proof["evaluator_files_sha256"]),
                         len(author.AUTHOR_RELATED))
        for name,info in proof["evaluator_files_sha256"].items():
            p=author.AUTHOR/name
            self.assertEqual(file_hash(p),info["sha256"])

    def test_07_author_scorer_is_repository_test_not_paper_score(self):
        self.assertIsNone(
            self.author["original_author_published_paper_score_equivalence"])
        self.assertIsNone(self.author["official_published_paper_score"])
        self.assertIsNone(self.gate["original_author_paper_scores"])
        self.assertFalse(
            self.gate["original_author_publication_score_equivalence_verified"])

    def test_08_missing_license_cannot_grant_redistribution_rights(self):
        provenance=self.author["author_scorer_provenance"]
        self.assertFalse(provenance["author_checkout_license_file_present"])
        self.assertFalse(provenance["license_and_IFC_data_redistribution_approved"])
        self.assertFalse(self.gate["source_rights_for_republication_verified"])

    def test_09_replay_d_and_I_original_author_developer_cases_16(self):
        rows=self.author["records"]
        self.assertEqual(len(rows),16)
        self.assertEqual(
            self.author["author_origin_task_evaluations_on_developer_native_IFCs"],16)
        cnt=Counter((row["original_task_id"],
                     row["fixture"].startswith("positive"))
                    for row in rows)
        self.assertEqual(len(cnt),8)
        self.assertTrue(all(v==2 for v in cnt.values()))
        self.assertTrue(all(row["no_paid_or_model_generated_inference"]
                            for row in rows))

    def test_10_scorer_positive_and_negative_exact_paired_scores(self):
        groups=defaultdict(dict)
        for row in self.author["records"]:
            groups[(row["original_task_id"],row["fixture"])][row["arm"]]=row
        for (task,fixture),arms in groups.items():
            self.assertEqual(set(arms),{
                "D_STATE_DEVELOPER_CONTROL","I_NATIVE_DEVELOPER_CONTROL"})
            self.assertEqual(
                arms["D_STATE_DEVELOPER_CONTROL"]
                    ["original_author_repo_test_boolean_metrics"],
                arms["I_NATIVE_DEVELOPER_CONTROL"]
                    ["original_author_repo_test_boolean_metrics"])
            d=arms["D_STATE_DEVELOPER_CONTROL"]
            i=arms["I_NATIVE_DEVELOPER_CONTROL"]
            self.assertEqual(d["original_author_repo_test_mean_score"],
                             i["original_author_repo_test_mean_score"])
            self.assertEqual(
                d["independent_research_physical_semantic_pass"],
                fixture.startswith("positive"))

    def test_11_true_original_author_positive_scores_3_full_one_half(self):
        rows={r["original_task_id"]:r for r in self.author["records"]
              if r["arm"]=="I_NATIVE_DEVELOPER_CONTROL"
              and r["fixture"].startswith("positive")}
        for tid in ("geometry_test_14","geometry_test_15",
                    "topological_test_11"):
            self.assertEqual(rows[tid]["original_author_repo_test_mean_score"],1)
        self.assertEqual(rows["topological_test_17"]
                         ["original_author_repo_test_mean_score"],0.5)
        self.assertTrue(rows["topological_test_17"]
                        ["original_author_repo_test_boolean_metrics"]
                        ["object_not_exists"])
        self.assertFalse(rows["topological_test_17"]
                         ["original_author_repo_test_boolean_metrics"]
                         ["integrity_constraint"])

    def test_12_original_author_partial_credit_not_confused_with_strict_pass(self):
        for r in self.author["records"]:
            author_strict=all(
                r["original_author_repo_test_boolean_metrics"].values())
            self.assertEqual(author_strict,
                             r["original_author_repo_test_mean_score"]==1.0)
            self.assertIsNone(r["original_paper_official_score"])

    def test_13_cascade_root_cause_is_fixed_class_counts_not_guids(self):
        d=self.author["topological17_IfcOpenShell_cascade_scoring_diagnostic"]
        self.assertEqual(d["original_author_target_count_NOT_IDS"],5)
        self.assertEqual(
            d["author_non_target_root_cascade_missing_by_IFC_class"],
            {"IfcPropertySet":15,"IfcRelDefinesByProperties":15,
             "IfcRelDefinesByType":5})
        self.assertFalse(d["author_non_target_elements_unchanged"])
        for cat,item in d["author_delete_subtests_only_counts"].items():
            self.assertEqual(item["passed"],item["total"],cat)
            self.assertEqual(item["total"],5)
        self.assertEqual(d["new_IfcRoot_count"],0)
        self.assertEqual(d["deleted_target_IFC_Root_count"],5)

    def test_14_preflight_has_no_hidden_target_guids_or_source_code(self):
        packet=gate.REPORT.read_text(encoding="utf8")
        self.assertNotIn("target_column_guids",packet)
        self.assertNotIn("positive_developer_source_edit",packet)
        self.assertNotIn("NativeEditPlan",packet)
        self.assertNotIn("model_output",packet)
        # Redacted scorer-result report contains counts not hardcoded correct IDs.
        grader=author.REPORT.read_text(encoding="utf8")
        self.assertNotIn("target_column_guids",grader)
        self.assertNotIn("NativeEditPlan",grader)

    def test_15_true_D_state_and_I_native_arm_identity(self):
        self.assertEqual(self.gate["primary_arms"],["D_STATE","I_NATIVE"])
        self.assertFalse(
            self.gate["auxiliary_restricted_T_XML_or_T_Python_in_primary_study"])
        self.assertEqual(
            self.gate["max_total_model_tool_calls_per_arm_task"],25)

    def test_16_initial_public_source_XML_bytes_identical_on_all_four(self):
        with TemporaryDirectory(prefix="v053-pair-read-") as temp:
            for i,tid in enumerate(gate.TASKS):
                r=self.tasks[tid]
                src=gate.DATA/"ifc"/r["original_source_ifc_relpath"]
                d=DirectOriginalStateSession050(src,Path(temp)/f"d_{i}")
                p=LiveOriginalNativePythonSession052(
                    src,Path(temp)/f"p_{i}")
                x=d.call("read_building_xml",{})
                y=p.call("read_building_xml",{})
                self.assertEqual(x["xml"],y["xml"])
                self.assertEqual(
                    sha256(x["xml"].encode("utf8")).hexdigest(),
                    self.gate["native_ifc_exact_source_hashes_and_task_prompt_hashes"]
                    [tid]["initial_D_I_source_xml_sha256"])

    def test_17_same_system_and_user_prompt_to_both_arms(self):
        task=self.tasks["geometry_test_14"]
        with TemporaryDirectory(prefix="v053-prompts-") as tmp:
            src=gate.DATA/"ifc"/task["original_source_ifc_relpath"]
            D=DirectOriginalStateSession050(src,Path(tmp)/"d")
            I=LiveOriginalNativePythonSession052(src,Path(tmp)/"i")
            raw=D.call("read_building_xml",{})["xml"]
            pd=gate.prospective_envelope(task,"D_STATE",raw,D.tools)
            pi=gate.prospective_envelope(task,"I_NATIVE",raw,I.tools)
            self.assertEqual(pd["user_message"],pi["user_message"])
            self.assertEqual(pd["system_message"],pi["system_message"])
            self.assertEqual(pd["initial_read_source_xml"],
                             pi["initial_read_source_xml"])
            self.assertNotEqual(pd["model_tools"],pi["model_tools"])
            self.assertIsNone(pd["model_output_from_provider"])

    def test_18_tool_input_tokens_cannot_be_inferred_from_bytes(self):
        for spec in self.gate[
                "native_ifc_exact_source_hashes_and_task_prompt_hashes"].values():
            self.assertTrue(spec["initial_D_I_source_xml_byte_identical"])
            self.assertNotEqual(
                spec["D_tool_schema_sha256"],spec["I_tool_schema_sha256"])
            self.assertTrue(
                spec["tool_schema_unequal_and_token_budgets_NOT_yet_proven"])
            self.assertIsNone(spec["raw_provider_input_tokens_each_arm"])

    def test_19_exact_source_and_question_hashes_for_every_task(self):
        for task_id,one in self.gate[
                "native_ifc_exact_source_hashes_and_task_prompt_hashes"].items():
            original=self.tasks[task_id]
            self.assertEqual(one["original_source_ifc_sha256"],
                             original["original_ifc_sha256"])
            self.assertEqual(one["original_public_question_sha256"],
                             original["public_question_sha256"])
            self.assertEqual(one["max_tool_calls_each_arm"],25)

    def test_20_assignment_is_deterministic_and_reversed_by_seed(self):
        for tid in gate.TASKS:
            order=gate._future_pair_order(tid)
            self.assertEqual(set(order),set(gate.ARMS))
            self.assertEqual(len(order),2)
            self.assertEqual(
                self.gate["native_ifc_exact_source_hashes_and_task_prompt_hashes"]
                [tid]["assignment_order_preregister_candidate"],order)

    def test_21_unselected_paid_model_and_endpoint_are_null(self):
        self.assertIsNone(self.gate["provider_exact_model_snapshot"])
        self.assertIsNone(self.gate["provider_api_endpoint"])
        self.assertIsNone(self.gate["provider_pricing_quote"])
        self.assertIsNone(self.gate["max_approved_usd_budget"])
        self.assertFalse(self.gate["user_approved_paid_experiment"])

    def test_22_no_model_or_paid_trial_has_been_executed(self):
        self.assertEqual(self.gate["actual_model_trial_slots_executed"],0)
        self.assertEqual(self.author["actual_LLM_trials"],0)
        self.assertEqual(self.author["billable_inference_calls"],0)

    def test_23_offline_gate_unconditionally_refuses_every_call(self):
        for approvals in (None,{},{
            "user_approved":True,"budget_approved":True,
            "provider_snapshot_approved":True,
            "official_grader_verified":True,"rights_approved":True,
            "token_parity_approved":True,
        }):
            with self.assertRaises(gate.TrialLaunchBlocked):
                gate.demand_trial_admission(approvals)

    def test_24_no_model_provider_sdk_or_API_connection_in_gate(self):
        source=(gate.ROOT/"tools"/
                "audit_bibimbap_v053_paired_prereg_gate.py").read_text(
                    encoding="utf8")
        forbidden=(
            "import openai", "import anthropic",
            "import requests","httpx.post(",
            "execute_ifc_code\",{",
            "submit_building_xml\",{",
        )
        self.assertTrue(all(item not in source for item in forbidden))

    def test_25_reject_unknown_or_restricted_pseudoprimary_arm(self):
        row=self.tasks["geometry_test_14"]
        for arm in ("T_XML_TYPED","T_PYTHON_AST","D_NATIVE_COMMAND","INVALID"):
            with self.assertRaises(ValueError):
                gate.prospective_envelope(
                    row,arm,"<?xml version='1.0'?>",[{},{},])

    def test_26_author_origin_head_tampering_fails_closed(self):
        with patch.object(author,"EXPECTED_AUTHOR_HEAD","0"*40):
            with self.assertRaises(AssertionError):
                author.read_only_author_origin()

    def test_27_report_is_exclusive_create_and_never_overwritten(self):
        for p in (author.REPORT,gate.REPORT):
            with self.assertRaises(FileExistsError):
                with p.open("xb") as fp:
                    pass

    def test_28_source_files_and_report_are_not_symlinks(self):
        for p in (author.REPORT,gate.REPORT):
            self.assertTrue(p.is_file())
            self.assertFalse(p.is_symlink())

    def test_29_actual_native_I_and_D_developer_reports_not_called_trials(self):
        self.assertTrue(all(
            r["arm"].endswith("_DEVELOPER_CONTROL")
            for r in self.author["records"]))
        self.assertTrue(self.gate["no_provider_or_author_published_grader_execution_path"])

    def test_30_assigned_pair_per_task_but_no_confirmation_significance(self):
        self.assertEqual(self.gate["candidate_trial_slots"],8)
        self.assertEqual(self.gate["inferential_status"],
                         "DESCRIPTIVE_ONLY_NOT_CONFIRMATORY")
        self.assertEqual(self.gate["original_model_source_cluster_count"],4)


if __name__=="__main__":
    unittest.main()
