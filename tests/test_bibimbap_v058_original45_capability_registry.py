"""v0.58 original 45-task read-only provenance and prospective cluster split.

All tests are pure local pinned-source/metadata/offline release gates.
There is no model trial, Docker mutation, author scorer execution, external
provider or rights-assumption inference.
"""
from __future__ import annotations

from collections import Counter,defaultdict
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from unittest import TestCase,main
from unittest.mock import patch

import ifcopenshell

from tools import bibimbap_v058_original45_capability_registry as cap
from tools import audit_bibimbap_v058_original45_prospective_registry as audit
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_matched25_cli import public_45


FROZEN_SHA="0d8e7ca07a08af0afa3a08c10de5a76427e179d41cd1ca9b9df508f40fcc96c8"


class Original45ProspectiveCapabilityRegistry058(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=audit.REPORT.read_bytes()
        cls.report=json.loads(cls.raw)
        cls.rows=public_45(cap.AUTHOR,cap.DATA)
        cls.by_id={r["test_id"]:r for r in cls.rows}
        cls.tasks=cls.report["all_original_45_task_capability_matrix"]
        cls.by_task={r["original_test_id"]:r for r in cls.tasks}
        cls.clusters=cls.report["source_cluster_registry"]

    def test_01_frozen_report_SHA(self):
        self.assertEqual(file_hash(audit.REPORT),FROZEN_SHA)

    def test_02_canonical_exact_json_report(self):
        self.assertEqual(cap.canonical(self.report),self.raw)

    def test_03_previous_v057_actual_ifc_and_author_report_immutable(self):
        self.assertEqual(file_hash(cap.PARENT_REPORT),cap.FROZEN_PARENT_REPORT_SHA)

    def test_04_previous_rights_report_immutable(self):
        self.assertEqual(file_hash(cap.V056_RIGHTS_REPORT),cap.FROZEN_V056_RIGHTS_SHA)

    def test_05_pinned_parent_sha_not_main(self):
        self.assertEqual(cap.FROZEN_PARENT_HEAD,
                         "661d733b77e801a491e56fee5b362ca59c44c9e7")

    def test_06_45_tasks_all_unique(self):
        self.assertEqual(len(self.tasks),45)
        self.assertEqual(len(self.by_task),45)
        self.assertEqual(set(self.by_task),set(self.by_id))

    def test_07_equal_crud_15_15_15(self):
        self.assertEqual(self.report["original_crud_counts"],
                         {"create":15,"update":15,"delete":15})

    def test_08_15_basic_15_geometry_15_topological(self):
        self.assertEqual(self.report["original_category_counts"],
                         {"basic":15,"geometry":15,"topological":15})

    def test_09_31_independent_source_clusters(self):
        self.assertEqual(len(self.clusters),31)
        self.assertEqual(self.report["original_unique_IFC_SHA_clusters"],31)

    def test_10_shared_basic_source_has_15_tasks(self):
        dist=Counter(c["task_count"] for c in self.clusters.values())
        self.assertEqual(dist,{1:30,15:1})
        shared=[c for c in self.clusters.values() if c["task_count"]==15]
        self.assertEqual(len(shared),1)
        self.assertTrue(all(t.startswith("test_")
                            for t in shared[0]["original_task_ids"]))

    def test_11_shared_source_cluster_never_leaks_to_holdout(self):
        shared=next(c for c in self.clusters.values() if c["task_count"]==15)
        self.assertEqual(shared["assignment"],
                         "DEVELOPMENT_UNTESTED_CURRENT_ARMS")

    def test_12_all_IFC_schema_count_by_tasks(self):
        self.assertEqual(self.report["source_input_schema_task_counts"],
                         {"IFC4X3":42,"IFC2X3":2,"IFC4":1})

    def test_13_all_IFC_schema_count_by_clusters(self):
        self.assertEqual(self.report["source_input_schema_unique_cluster_counts"],
                         {"IFC4X3":28,"IFC2X3":2,"IFC4":1})

    def test_14_production_IFC4X3_gates_not_compatible_with_3_tasks(self):
        for entry in self.tasks:
            if entry["original_input_native_schema"]!="IFC4X3":
                for arm in cap.ARMS:
                    self.assertFalse(entry["arms"][arm][
                        "current_production_native_ifc_schema_compatible"])
        self.assertEqual(sum(
            e["original_input_native_schema"]!="IFC4X3" for e in self.tasks),3)

    def test_15_historical_readonly_projectable_36(self):
        self.assertEqual(self.report["historical_XML_readonly_projectable_tasks"],36)
        self.assertEqual(self.report["historical_XML_readonly_blocked_tasks"],9)

    def test_16_historical_readonly_is_not_edit_coverage(self):
        self.assertTrue(self.report[
            "historical_XML_readability_does_not_establish_native_EDIT_coverage"])
        self.assertEqual(self.by_task["geometry_test_14"][
            "historical_XML_readonly_source_projection"],"BLOCKED")
        self.assertTrue(self.by_task["geometry_test_14"]["arms"][
            "D_COMPLETE_XML"]["current_task_bound_executable_and_admissible"])

    def test_17_four_prior_developer_controls_only(self):
        self.assertEqual(
            self.report["previously_developer_control_verified_4_original_tasks"],
            sorted(cap.SEEN_DEV_TASKS))
        self.assertEqual(sum(e["previously_exposed_four_developer_controls"]
                             for e in self.tasks),4)

    def test_18_other_41_are_not_real_model_tested(self):
        self.assertEqual(self.report[
            "all_other_41_original_tasks_not_covered_by_current_task_oracle"],41)
        self.assertTrue(all(not e["model_generated_any_arm_run"]
                            for e in self.tasks))

    def test_19_per_arm_verified_only_original_four(self):
        for arm in cap.ARMS+(cap.AUX_ARM,):
            verified={e["original_test_id"] for e in self.tasks
                      if e["arms"][arm][
                          "current_task_bound_executable_and_admissible"]}
            self.assertEqual(verified,cap.SEEN_DEV_TASKS)

    def test_20_I_engine_generic_is_not_task_oracle_for_41(self):
        states=Counter(
            e["arms"]["I_NATIVE"]["state"] for e in self.tasks)
        self.assertEqual(states,{
            "VERIFIED_NATIVE_DEVELOPER_CONTROL_ONLY":4,
            "GENERIC_EXECUTOR_EXISTS_BUT_ORIGINAL_TASK_ORACLE_UNVERIFIED":41,
        })

    def test_21_D_full_41_unsupported_task_compiler(self):
        self.assertEqual(sum(
            e["arms"]["D_COMPLETE_XML"]["state"]==
              "NOT_SUPPORTED_BY_CURRENT_FOUR_TASK_FINAL_STATE_COMPILER"
            for e in self.tasks),41)

    def test_22_D_managed_41_unsupported_task_compiler(self):
        self.assertEqual(sum(
            e["arms"]["D_MANAGED_FINAL_STATE"]["state"]==
              "NOT_SUPPORTED_BY_CURRENT_FOUR_TASK_FINAL_STATE_COMPILER"
            for e in self.tasks),41)

    def test_23_D_stream_appropriately_auxiliary_not_primary(self):
        self.assertEqual(self.report["streaming_D_auxiliary_identity"],
                         "D_COMPLETE_XML_STREAMED")
        self.assertNotIn("D_COMPLETE_XML_STREAMED",
                         self.report["three_separate_arm_identities"])

    def test_24_original_author_scorer_45_modules_EXIST_SHA_pinned(self):
        for entry in self.tasks:
            source=cap.AUTHOR/entry[
                "author_evaluator_source_only"]["path_relative_to_pinned_author_checkout"]
            self.assertTrue(source.is_file())
            self.assertEqual(file_hash(source),entry[
                "author_evaluator_source_only"][
                    "author_source_test_module_SHA256"])

    def test_25_author_modules_are_not_executed(self):
        self.assertTrue(self.report[
            "original_author_evaluator_45_modules_SHA_pinned_not_invoked"])
        for entry in self.tasks:
            self.assertFalse(entry["author_evaluator_source_only"][
                "author_module_was_EXECUTED_during_v058"])

    def test_26_original_paper_official_version_not_inferred(self):
        self.assertFalse(self.report[
            "original_author_code_version_paper_official_equivalence_proven"])
        for entry in self.tasks:
            self.assertIsNone(entry["paper_official_published_score"])

    def test_27_all_original_IFC_and_question_SHA_equal_manifest(self):
        for entry in self.tasks:
            r=self.by_id[entry["original_test_id"]]
            source=cap.DATA/"ifc"/entry["original_input_IFC_relative_path"]
            self.assertEqual(file_hash(source),r["original_ifc_sha256"])
            self.assertEqual(entry["original_question_SHA256"],
                             r["public_question_sha256"])

    def test_28_original_31_native_IFC_schemas_ACTUALLY_reopen(self):
        # This is a genuine source-file native format check, not a metadata label.
        for sha,c in self.clusters.items():
            path=cap.DATA/"ifc"/self.by_id[c["original_task_ids"][0]][
                "original_source_ifc_relpath"]
            self.assertEqual(file_hash(path),sha)
            self.assertEqual(ifcopenshell.open(str(path)).schema,
                             c["native_ifc_schema"])

    def test_29_SOURCE_assignments_count_21_4_6(self):
        self.assertEqual(self.report["source_cluster_assignment_counts"],{
            "DEVELOPMENT_UNTESTED_CURRENT_ARMS":21,
            "PRIOR_DEVELOPER_EXPOSED":4,
            "PROSPECTIVE_UNTOUCHED_SOURCE_HOLDOUT":6,
        })

    def test_30_TASK_assignments_count_35_4_6(self):
        self.assertEqual(self.report["task_assignment_counts"],{
            "DEVELOPMENT_UNTESTED_CURRENT_ARMS":35,
            "PRIOR_DEVELOPER_EXPOSED":4,
            "PROSPECTIVE_UNTOUCHED_SOURCE_HOLDOUT":6,
        })

    def test_31_each_source_cluster_has_one_partition(self):
        bysource=defaultdict(set)
        for e in self.tasks:
            bysource[e["source_cluster_ifc_SHA256"]].add(
                e["source_cluster_assignment"])
        self.assertTrue(all(len(x)==1 for x in bysource.values()))

    def test_32_none_prior_exposed_source_in_holdout(self):
        holdout=set(self.report["prospective_six_source_heldout_IFC_sha256"])
        old={e["source_cluster_ifc_SHA256"] for e in self.tasks
             if e["previously_exposed_four_developer_controls"]}
        self.assertEqual(len(holdout),6)
        self.assertFalse(holdout.intersection(old))

    def test_33_six_strata_each_one_holdout(self):
        schedule=self.report["paired_schedule"]
        self.assertEqual(len(schedule),6)
        self.assertEqual({s["stratum"] for s in schedule},set(cap.STRATA))
        self.assertEqual(len({s["source_cluster_ifc_SHA256"] for s in schedule}),6)

    def test_34_no_basic_task_holdout_pretends_full_population(self):
        for s in self.report["paired_schedule"]:
            self.assertTrue(s["task_id"].startswith(
                ("geometry_test_","topological_test_")))
        self.assertTrue(self.report[
            "source_cluster_holdout_is_stratified_NOT_representative_of_basic_tasks"])

    def test_35_selection_exactly_recomputed_from_seed(self):
        assignments,selected=cap._source_cluster_assignments(self.rows)
        self.assertEqual(sorted(selected),
                         self.report["prospective_six_source_heldout_task_ids"])
        for row in self.tasks:
            self.assertEqual(row["source_cluster_assignment"],
                             assignments[row["source_cluster_ifc_SHA256"]])

    def test_36_SELECTION_ignores_author_grades_and_question_contents(self):
        forged=deepcopy(self.rows)
        for row in forged:
            row["public_question"]="FORGED_NEVER_AUTHOR_OR_MODEL_INPUT"
            row["public_question_sha256"]="f"*64
            row["original_noop_score_prior"]=-1.0
        self.assertEqual(
            cap._source_cluster_assignments(forged),
            cap._source_cluster_assignments(self.rows))

    def test_37_seed_change_changes_selection_but_not_source_hashes(self):
        original=cap._source_cluster_assignments(self.rows)[1]
        with patch.object(cap,"SEED","v058 ALTERNATIVE explicitly NOT frozen seed"):
            changed=cap._source_cluster_assignments(self.rows)[1]
        self.assertNotEqual(original,changed)

    def test_38_order_is_seed_frozen_public_inputs_only(self):
        ids=self.report["prospective_randomized_task_order"]
        self.assertEqual(ids,sorted(ids,key=lambda task:(
            cap.digest(cap.SEED,"PROSPECTIVE_ORDER",task,
                       self.by_id[task]["original_ifc_sha256"]),task)))

    def test_39_each_holdout_task_two_separate_comparisons(self):
        for row in self.report["paired_schedule"]:
            self.assertEqual(len(row["comparison_run_plan"]),2)
            self.assertEqual({p["comparison_id"] for p in row[
                "comparison_run_plan"]},{
                "PRIMARY_FULL_D_vs_I","ALTERNATIVE_MANAGED_D_vs_I"})

    def test_40_primary_D_full_pairs_only_real_I(self):
        for row in self.report["paired_schedule"]:
            first=row["comparison_run_plan"][0]
            self.assertEqual(set(first["arm_order"]),
                             {"D_COMPLETE_XML","I_NATIVE"})

    def test_41_alternative_managed_D_pairs_only_real_I(self):
        for row in self.report["paired_schedule"]:
            second=row["comparison_run_plan"][1]
            self.assertEqual(set(second["arm_order"]),
                             {"D_MANAGED_FINAL_STATE","I_NATIVE"})

    def test_42_no_reusing_I_control_across_two_D_comparisons(self):
        for row in self.report["paired_schedule"]:
            for pair in row["comparison_run_plan"]:
                self.assertTrue(pair[
                    "independent_I_baseline_RUN_PER_COMPARISON"])
                self.assertTrue(pair["fresh_source_clone_per_arm"])
                self.assertTrue(pair["fresh_provider_context_per_arm"])
                self.assertTrue(pair["no_reuse_of_prior_model_result"])

    def test_43_future_12_pairs_24_arm_slots_zero_executed(self):
        self.assertEqual(self.report[
            "planned_pair_comparison_count_if_admitted"],12)
        self.assertEqual(self.report[
            "planned_independent_arm_task_run_slots_if_admitted"],24)
        self.assertEqual(self.report["model_generated_trial_slots_executed"],0)

    def test_44_HOLDOUT_currently_unexecutable_not_false_model_failure(self):
        for row in self.report["paired_schedule"]:
            self.assertTrue(row[
                "task_is_CURRENTLY_UNSUPPORTED_IN_ALL_THREE_COMPARISON_ARMS"])
            self.assertTrue(row["no_run_authorized"])
            task=self.by_task[row["task_id"]]
            self.assertTrue(all(not task["arms"][arm][
                "current_task_bound_executable_and_admissible"]
                for arm in cap.ARMS))
        self.assertTrue(self.report[
            "structurally_ineligible_tasks_reported_separately_from_model_failure"])

    def test_45_any_ineligible_trial_stays_in_ITT_denominator(self):
        self.assertEqual(self.report["candidate_holdout_ITT_denominator"],6)
        self.assertEqual(self.report[
            "full_population_ITT_denominator_IF_full_supported_and_approved"],45)
        self.assertTrue(self.report[
            "missing_or_refused_task_must_remain_in_ITT_denominator"])

    def test_46_delete_scoring_loophole_not_hidden(self):
        self.assertTrue(self.report[
            "author_repository_correct_5_column_deletion_score_possible_0_50"])
        self.assertTrue(self.report[
            "strict_IFC_schema_success_is_not_same_as_original_author_score"])

    def test_47_separate_original_author_vs_physical_vs_schema_layers(self):
        self.assertNotEqual(
            self.report["original_author_repository_metric_reporting"],
            self.report["physical_task_correctness_reporting"])
        self.assertNotEqual(
            self.report["physical_task_correctness_reporting"],
            self.report["native_IFC_admission_reporting"])

    def test_48_no_paid_call_any_row(self):
        self.assertEqual(self.report["billable_provider_calls"],0)
        for row in self.tasks:
            for arm in cap.ARMS:
                self.assertEqual(row["arms"][arm][
                    "provider_paid_execution_count"],0)

    def test_49_unconditional_no_launch_even_all_true(self):
        with self.assertRaises(cap.ProviderTrialBlocked057):
            cap.demand_trial_admission_v058({
                "rights":True,"money":True,"snapshot":True,
                "token_receipts":True,"paid_llm":True,
            })

    def test_50_original_data_card_license_not_automatic_provider_permission(self):
        self.assertTrue(self.report["original_HF_data_card_declares_cc_by_4_0"])
        self.assertFalse(self.report[
            "original_individual_IFC_chain_of_rights_verified"])
        self.assertFalse(self.report[
            "user_approved_provider_data_transfer_and_retention"])

    def test_51_provider_model_price_and_token_receipts_all_unset(self):
        for field in (
            "provider_exact_model_snapshot","provider_data_transfer_authorization",
            "provider_billed_D_I_input_tokens",
            "provider_billed_D_I_completion_tokens",
            "provider_context_and_output_max_tokens",
            "paid_usd_cap_authorized",
        ):
            self.assertIsNone(self.report[field])

    def test_52_no_GT_or_model_provider_client_imported(self):
        code=(cap.ROOT/"tools"/
              "bibimbap_v058_original45_capability_registry.py").read_text(
                  encoding="utf8")
        for bad in ("import openai","import anthropic","from data.tests",
                    "import data.tests","requests.post(",
                    "developer_python_source","positive_developer_source_edit"):
            self.assertNotIn(bad,code)

    def test_53_no_raw_original_questions_or_evaluator_code_in_report(self):
        raw=audit.REPORT.read_text(encoding="utf8")
        for row in self.rows:
            # Original user questions are private local dataset source;
            # the report should only contain SHA pins, not their text.
            self.assertNotIn(row["public_question"],raw)
        self.assertNotIn("def execute_test(",raw)
        self.assertNotIn("target_column_guids",raw)

    def test_54_report_exclusive_create_once(self):
        with self.assertRaises(FileExistsError):
            with audit.REPORT.open("xb") as fd:
                pass

    def test_55_bad_45_source_distribution_refuses_sampling(self):
        shortened=[r for r in self.rows if r["test_id"]!="geometry_test_15"]
        with self.assertRaises(cap.CapabilityRegistry058Error):
            cap._source_cluster_assignments(shortened)

    def test_56_every_author_test_and_source_ifc_SHA_64_hex(self):
        for row in self.tasks:
            a=row["author_evaluator_source_only"]
            self.assertEqual(len(a["author_source_test_module_SHA256"]),64)
            self.assertEqual(len(row["source_cluster_ifc_SHA256"]),64)
            self.assertEqual(len(row["original_question_SHA256"]),64)

    def test_57_provider_arm_error_budget_not_falsely_equivalent(self):
        self.assertFalse(self.report[
            "budget_equivalent_error_feedback_protocol_frozen"])
        self.assertFalse(self.report[
            "retry_timeout_and_seed_pre_registration_approved"])
        self.assertTrue(self.report["holdout_is_not_CURRENTLY_EXPERIMENTALLY_ADMISSIBLE"])


if __name__=="__main__":
    main()
