"""v0.55 production genuine D-state and I-native commit-schema transaction tests.

Report's real-Docker 8+ adversarial cases are reproducibly re-executed in the
separate audit --check; these tests assert pinned provenance, failed-session
rollback, source parity, runtime-only grader separation and admission budget.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash,PINNED_DOCKER_IMAGE,DockerIFCExecutor
from tools.bibimbap_v050_direct_original_state_session import (
    DirectOriginalStateSession050,
)
from tools.bibimbap_v052_live_original_native_python_session import (
    LiveOriginalNativePythonSession052,
)
from tools.bibimbap_v055_transactional_primary_DI_sessions import (
    SchemaGuardedDirectStateSession055,SchemaGuardedLivePythonSession055,
)
from tools.bibimbap_v055_production_schema_gate import (
    NativeSourceSchema055Error,
    production_native_schema_delta_v055,
    validate_production_native_commit_v055,
)
from tools import audit_bibimbap_v055_live_schema_transactions as audit


REPORT_SHA="e651a612e718281fa1ecb2741cf29216796be5df6f6d00439894e0b591b0437c"


class V055PrimarySchemaTransactional(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(audit.REPORT.read_text(encoding="utf8"))
        cls.tasks=audit.row_registry()

    def setUp(self):
        self.temporary=TemporaryDirectory(prefix="v055-tests-")
        self.addCleanup(self.temporary.cleanup)
        self.scratch=Path(self.temporary.name)

    def source(self,tid="geometry_test_14"):
        row=self.tasks[tid]
        return audit.DATA/"ifc"/row["original_source_ifc_relpath"]

    def test_01_exact_live_report_SHA(self):
        self.assertEqual(file_hash(audit.REPORT),REPORT_SHA)

    def test_02_v054_schema_report_unchanged(self):
        self.assertEqual(
            file_hash(audit.ROOT/"reports"/
              "bibimbap_v054_delete_source_schema_policy_20261118.json"),
            audit.PARENT_V054_SCHEMA_SHA)

    def test_03_v054_token_rights_report_unchanged(self):
        self.assertEqual(
            file_hash(audit.ROOT/"reports"/
              "bibimbap_v054_offline_paired_token_and_source_rights_20261118.json"),
            audit.PARENT_V054_RIGHTS_SHA)

    def test_04_original_45_31_population_untouched(self):
        self.assertEqual(len(self.tasks),45)
        self.assertEqual(len({
            t["original_ifc_sha256"] for t in self.tasks.values()}),31)
        self.assertEqual(Counter(t["crud"] for t in self.tasks.values()),
                         {"create":15,"update":15,"delete":15})

    def test_05_v055_D_I_have_exact_unmodified_tool_schemas(self):
        src=self.source()
        D=SchemaGuardedDirectStateSession055(src,self.scratch/"d")
        I=SchemaGuardedLivePythonSession055(src,self.scratch/"i")
        d_old=DirectOriginalStateSession050(src,self.scratch/"old_d")
        i_old=LiveOriginalNativePythonSession052(src,self.scratch/"old_i")
        self.assertEqual(D.tools,d_old.tools)
        self.assertEqual(I.tools,i_old.tools)

    def test_06_initial_XML_bytes_equal_for_all_original_four(self):
        for index,tid in enumerate(audit.TASKS):
            src=self.source(tid)
            D=SchemaGuardedDirectStateSession055(src,self.scratch/f"D{index}")
            I=SchemaGuardedLivePythonSession055(src,self.scratch/f"I{index}")
            d=D.call("read_building_xml",{})
            i=I.call("read_building_xml",{})
            self.assertEqual(d["status"],"ok")
            self.assertEqual(i["status"],"ok")
            self.assertEqual(d["xml"],i["xml"])
            self.assertEqual(
                sha256(d["xml"].encode("utf8")).hexdigest(),
                self.report["original_source_XML_info_parity"][tid][
                    "initial_source_XML_SHA256"])

    def test_07_schema_function_uses_genuine_ifcopenshell_native_validator(self):
        import inspect
        from tools import bibimbap_v055_production_schema_gate as source
        txt=inspect.getsource(source._schema_error_counter)
        self.assertIn("ifcopenshell.validate.validate",txt)
        self.assertIn("express_rules=False",txt)

    def test_08_evaluator_private_targets_never_imported_in_production(self):
        for part in ("bibimbap_v055_transactional_primary_DI_sessions.py",
                     "bibimbap_v055_production_schema_gate.py"):
            text=(audit.ROOT/"tools"/part).read_text(encoding="utf8")
            for bad in ("original_author_targets_evaluator_only",
                        "from data.tests","import data.tests",
                        "import openai","import anthropic",
                        "positive_developer_source_edit",
                        "author_origin","benchmark.py"):
                self.assertNotIn(bad,text)

    def test_09_true_live_worker_uses_exact_real_Docker_executor(self):
        i=SchemaGuardedLivePythonSession055(self.source(),self.scratch/"i")
        self.assertIs(type(i.executor),DockerIFCExecutor)
        self.assertFalse(i.is_offline_double)

    def test_10_model_tool_call_budget_25_D_I(self):
        D=SchemaGuardedDirectStateSession055(self.source(),self.scratch/"D")
        I=SchemaGuardedLivePythonSession055(self.source(),self.scratch/"I")
        for k in range(25):
            self.assertEqual(D.call("read_building_xml",{})["status"],"ok")
            self.assertEqual(I.call("read_building_xml",{})["status"],"ok")
        self.assertEqual(
            D.call("submit_building_xml",{"xml_text":"x"})["error_type"],
            "ToolBudgetExhausted")
        self.assertEqual(
            I.call("execute_ifc_code",{"code":"commit()"})["error_type"],
            "ToolBudgetExhausted")

    def test_11_16_original_real_native_D_I_developer_cases(self):
        self.assertEqual(len(self.report["native_developer_case_records"]),16)
        self.assertEqual(self.report["developer_control_native_candidates_D_I"],16)
        self.assertEqual(self.report["accepted_native_D_controls"],8)
        self.assertEqual(self.report["accepted_true_Docker_I_controls"],8)

    def test_12_real_I_cases_attested_true_Linux_not_copied_IFC(self):
        for row in self.report["native_developer_case_records"]:
            self.assertEqual(len(row["real_IFC4X3_SHA256"]),64)
            self.assertEqual(
                row["actual_Python_run_in_pinned_Linux_Docker"],
                row["arm"]=="I_NATIVE_DOCKER")
            self.assertFalse(row["model_generated"])

    def test_13_all_16_native_IFCs_zero_NEW_schema_errors(self):
        self.assertTrue(self.report[
            "all_accepted_candidates_no_new_IFC4X3_schema_errors"])
        for row in self.report["native_developer_case_records"]:
            self.assertEqual(row["newly_introduced_schema_errors"],0)
            self.assertEqual(row["v055_original_source_native_scope_and_schema"],
                             "PASS")

    def test_14_positive_and_negative_public_research_physical_classification(self):
        records=self.report["native_developer_case_records"]
        self.assertEqual(sum(row["physical_research_predicate"]
                             for row in records),8)
        self.assertEqual(sum(not row["physical_research_predicate"]
                             for row in records),8)
        self.assertEqual({
            row["task_id"] for row in records},set(audit.TASKS))

    def test_15_source_pins_original_task_questions(self):
        for tid,info in self.report["original_source_XML_info_parity"].items():
            row=self.tasks[tid]
            self.assertEqual(info["original_public_IFC_SHA256"],
                             row["original_ifc_sha256"])
            self.assertEqual(info["public_question_SHA256"],
                             row["public_question_sha256"])
            self.assertEqual(file_hash(self.source(tid)),
                             row["original_ifc_sha256"])

    def test_16_raw_Docker_five_Column_invalid_commit_rejected(self):
        evidence=self.report["real_Docker_adversarial_commit_and_atomic_rollback"]
        self.assertEqual(evidence["raw_5_columns_real_Docker_worker_status"],"ok")
        self.assertTrue(evidence["raw_5_columns_worker_committed"])
        self.assertFalse(evidence["raw_5_columns_host_committed"])
        self.assertEqual(evidence["new_schema_guard_response_type"],
                         "NativeSchemaOrScopeRejected")

    def test_17_real_pinned_Docker_raw_five_column_has_25_NEW_errors(self):
        evidence=self.report["real_Docker_adversarial_commit_and_atomic_rollback"]
        self.assertEqual(evidence[
            "raw_5_columns_schema_new_findings_from_separate_real_Docker_output"],25)
        self.assertEqual(evidence["original_source_schema_preexisting_findings"],1)

    def test_18_live_Docker_prior_good_then_bad_keeps_hash(self):
        evidence=self.report["real_Docker_adversarial_commit_and_atomic_rollback"]
        self.assertTrue(evidence[
            "invalid_5th_column_real_worker_executed_and_committed"])
        self.assertTrue(evidence[
            "invalid_5th_column_previous_last_good_preserved"])
        self.assertEqual(len(evidence[
            "last_good_4_column_Docker_IFC_SHA256"]),64)

    def test_19_live_Docker_recovery_after_invalid_schema(self):
        evidence=self.report["real_Docker_adversarial_commit_and_atomic_rollback"]
        self.assertTrue(evidence[
            "subsequent_safe_5th_column_native_recovery"])

    def test_20_D_XML_malformed_after_valid_rolls_back(self):
        self.assertTrue(self.report[
            "real_Docker_adversarial_commit_and_atomic_rollback"]
            ["D_state_after_valid_malformed_XML_rolled_back"])

    def test_21_D_actual_model_call_enforces_native_schema_gate(self):
        D=SchemaGuardedDirectStateSession055(
            self.source(),self.scratch/"d")
        state=audit.developer_XML_final(
            self.tasks["geometry_test_14"],self.source(),positive=True)
        with patch(
          "tools.bibimbap_v055_transactional_primary_DI_sessions.validate_production_native_commit_v055",
          side_effect=NativeSourceSchema055Error("InjectedMissingSchemaAdmission")):
            bad=D.call("submit_building_xml",{"xml_text":state})
        self.assertEqual(bad["status"],"error")
        self.assertEqual(bad["error_type"],"NativeSchemaOrScopeRejected")
        self.assertIsNone(D.output_ifc)
        self.assertEqual(D.current_xml,D.original_xml)
        self.assertFalse((D.folder/"attempt_001"/
            "candidate_original_native_mm.ifc").exists())

    def test_22_real_model_D_success_and_old_source_has_existing_error(self):
        D=SchemaGuardedDirectStateSession055(
            self.source(),self.scratch/"d")
        result=D.call("submit_building_xml",{
            "xml_text":audit.developer_XML_final(
                self.tasks["geometry_test_14"],self.source(),positive=True)})
        self.assertEqual(result["status"],"ok")
        check=production_native_schema_delta_v055(
            self.source(),D.output_ifc,
            source_sha=self.tasks["geometry_test_14"]["original_ifc_sha256"])
        self.assertEqual(check["introduced_schema_error_count"],0)

    def test_23_D_no_commit_on_bad_state_after_success(self):
        D=SchemaGuardedDirectStateSession055(self.source(),self.scratch/"d")
        source=self.source()
        valid=audit.developer_XML_final(
            self.tasks["geometry_test_14"],source,positive=True)
        a=D.call("submit_building_xml",{"xml_text":valid})
        self.assertEqual(a["status"],"ok")
        digest=file_hash(D.output_ifc)
        state=D.current_xml
        b=D.call("submit_building_xml",{"xml_text":"<bad/>"})
        self.assertEqual(b["status"],"error")
        self.assertEqual(file_hash(D.output_ifc),digest)
        self.assertEqual(D.current_xml,state)

    def test_24_I_no_Docker_runtime_blocks_before_any_candidate(self):
        I=SchemaGuardedLivePythonSession055(
            self.source(),self.scratch/"i")
        with patch(
          "tools.bibimbap_v055_transactional_primary_DI_sessions.live_pinned_local_runtime_admission_v052",
          return_value={"status":"BLOCKED_RUNTIME","reason":"TEST_NO_ENGINE"}),patch.object(
          I.executor,"run") as fake:
            bad=I.call("execute_ifc_code",{"code":"commit()"})
        self.assertEqual(bad["status"],"error")
        self.assertEqual(bad["error_type"],"BLOCKED_RUNTIME")
        fake.assert_not_called()
        self.assertEqual(list(I.folder.iterdir()),[])

    def test_25_I_requires_nonempty_proper_code(self):
        I=SchemaGuardedLivePythonSession055(
            self.source(),self.scratch/"i")
        for arguments in ({},{"code":""},{"code":42},
                          {"not_code":"commit()"},{"code":"ok","other":True}):
            bad=I.call("execute_ifc_code",arguments)
            self.assertEqual(bad["error_type"],"InvalidPythonCodeInput")
        self.assertEqual(list(I.folder.iterdir()),[])

    def test_26_wrong_original_ifc_sha_refused(self):
        with self.assertRaises(NativeSourceSchema055Error):
            production_native_schema_delta_v055(
                self.source(),self.source(),
                source_sha="0"*64)

    def test_27_candidate_alias_original_rejected(self):
        source=self.source()
        with self.assertRaises(NativeSourceSchema055Error):
            production_native_schema_delta_v055(
                source,source,
                source_sha=self.tasks["geometry_test_14"]["original_ifc_sha256"])

    def test_28_schema_validator_does_not_self_certify_complete_IFC(self):
        self.assertTrue(self.report[
            "new_validator_is_not_full_IFC_EXPRESS_WHERE_semantic_completeness"])

    def test_29_original_source_must_remain_unchanged(self):
        self.assertTrue(self.report["no_initial_source_IFC_mutated"])
        for tid in audit.TASKS:
            self.assertEqual(file_hash(self.source(tid)),
                self.tasks[tid]["original_ifc_sha256"])

    def test_30_NO_LLM_or_paid_model_calls(self):
        self.assertEqual(self.report[
            "actual_paired_model_generated_Python_XML_trials"],0)
        self.assertEqual(self.report["paid_provider_model_calls"],0)
        self.assertIsNone(self.report["original_author_paper_score"])
        self.assertFalse(self.report[
            "license_and_provider_transfer_rights_approved"])
        self.assertFalse(self.report[
            "provider_billed_input_output_token_parity_proven"])

    def test_31_prior_frozen_reports_keep_hashes(self):
        self.assertEqual(self.report["old_v054_frozen_schema_report_SHA256"],
                         audit.PARENT_V054_SCHEMA_SHA)
        self.assertEqual(self.report["old_v054_frozen_rights_report_SHA256"],
                         audit.PARENT_V054_RIGHTS_SHA)

    def test_32_no_private_author_GT_or_editor_patch_in_public_report(self):
        packet=audit.REPORT.read_text(encoding="utf8")
        for forbidden in ("target_column_guids","make_illustrative_plan",
                          "positive_developer_source_edit",
                          "original_author_targets_evaluator_only"):
            self.assertNotIn(forbidden,packet)

    def test_33_frozen_report_exclusive_create(self):
        with self.assertRaises(FileExistsError):
            with audit.REPORT.open("xb") as fd:
                pass

    def test_34_output_native_schema_gate_always_checks_SOURCE(self):
        body=(audit.ROOT/"tools"/
              "bibimbap_v055_production_schema_gate.py").read_text(
                  encoding="utf8")
        self.assertIn("source_ifc",body)
        self.assertIn("_schema_error_counter(source_ifc)",body)
        self.assertIn("_schema_error_counter(candidate_ifc)",body)
        self.assertNotIn("from data.tests",body)

    def test_35_I_real_worker_failed_after_commit_refused(self):
        self.assertTrue(self.report[
            "real_Docker_adversarial_commit_and_atomic_rollback"]
            ["I_native_real_worker_exception_after_commit_rejected"])


if __name__=="__main__":
    unittest.main()
