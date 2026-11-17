"""v0.52 actual Docker Python/IfcOpenShell I-native source attestation tests.

The 8 real executed IFC control results and 6 Docker security probes are
reproducibly replayed by the separate v0.52 --check audit; this focused
suite checks report invariants and fail-closed live runtime/host policy.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import (
    PINNED_DOCKER_IMAGE,MAX_CODE_BYTES,file_hash,DockerIFCExecutor,
    build_pinned_docker_command,
)
from tools.bibimbap_v052_live_docker_controls import (
    TASKS,developer_python_source,deliberately_invalid_python,
    question_named_slab_guid,
)
from tools.bibimbap_v052_live_original_native_python_session import (
    LiveOriginalNativePythonSession052,
    live_pinned_local_runtime_admission_v052,
)
from tools.bibimbap_v050_direct_original_state_session import (
    DirectOriginalStateSession050,
)
from tools import audit_bibimbap_v052_live_docker_native_python as audit


BASE=Path(r"D:\문서\D__1_Projects\202611")
DATA=BASE/"bibimbap-author-data"
AUTHOR=BASE/"bibimbap-author-upstream"
FROZEN_SHA="83aaebf382ddad136ee55ff4e3b54559e6630b64587c4665f447bb12baffcc31"


class OriginalFourRealDockerPython052(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks={r["test_id"]:r for r in public_45(AUTHOR,DATA)}
        cls.report=json.loads(audit.REPORT.read_text(encoding="utf8"))
        cls.temp=TemporaryDirectory(prefix="v052-live-tests-")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.case=TemporaryDirectory(prefix="v052-one-case-")
        self.addCleanup(self.case.cleanup)
        self.root=Path(self.case.name)

    def source(self,tid="geometry_test_14"):
        r=self.tasks[tid]
        return DATA/"ifc"/r["original_source_ifc_relpath"]

    def test_01_frozen_live_report_SHA(self):
        self.assertEqual(file_hash(audit.REPORT),FROZEN_SHA)

    def test_02_prior_two_report_SHA_unchanged(self):
        self.assertEqual(file_hash(audit.ROOT/"reports"/
            "bibimbap_v051_original4_executed_python_runtime_readiness_20261118.json"),
            audit.PARENT_V051)
        self.assertEqual(file_hash(audit.ROOT/"reports"/
            "bibimbap_v050_original4_declarative_state_diff_20261117.json"),
            audit.PARENT_V050)

    def test_03_public_45_31_CUD_counts_preserved(self):
        self.assertEqual(len(self.tasks),45)
        self.assertEqual(len({r["original_ifc_sha256"] for r in self.tasks.values()}),31)
        self.assertEqual(Counter(r["crud"] for r in self.tasks.values()),
                         {"create":15,"update":15,"delete":15})

    def test_04_original_four_exact_source_SHA_pinned(self):
        for tid in TASKS:
            expected=self.tasks[tid]["original_ifc_sha256"]
            self.assertEqual(file_hash(self.source(tid)),expected)
            self.assertEqual(
                self.report["source_question_and_D_I_source_parity"][tid]["original_ifc_sha256"],
                expected)

    def test_05_live_report_eight_real_docker_IFC_cases(self):
        self.assertEqual(
            self.report["actual_real_Docker_Python_source_native_IFC_developer_controls"],8)
        self.assertEqual(self.report["real_native_IFC_independent_scope_oracle_pass"],8)
        self.assertEqual(len(self.report["real_Docker_case_records"]),8)
        self.assertTrue(all(x["actual_sandbox_python_IfcOpenShell_executed"]
                            for x in self.report["real_Docker_case_records"]))

    def test_06_four_real_semantic_positive_four_negative(self):
        rows=self.report["real_Docker_case_records"]
        self.assertEqual(sum(x["independent_research_physical_semantic_predicate_pass"]
                             for x in rows),4)
        self.assertEqual(sum(not x["independent_research_physical_semantic_predicate_pass"]
                             for x in rows),4)
        self.assertEqual(
            {x["task_id"] for x in rows},set(TASKS))

    def test_07_true_Linux_worker_nonroot_and_pinned(self):
        for r in self.report["real_Docker_case_records"]:
            self.assertEqual(r["linux_nonroot_uid"],65534)
            self.assertEqual(r["actual_attested_Docker_worker"],"linux_docker_sandbox")
            self.assertTrue(r["actual_IFC4X3_native_mm"])
            self.assertTrue(r["original_ifc_unchanged"])
            self.assertEqual(len(r["real_native_IFC_SHA256"]),64)

    def test_08_positive_negative_developer_not_LLM_trial(self):
        self.assertEqual(self.report["LLM_generated_native_Python_trial_count"],0)
        self.assertEqual(self.report["paid_model_inference_count"],0)
        self.assertIsNone(self.report["original_author_benchmark_score"])
        self.assertIsNone(self.report["causal_XML_D_vs_Python_I_model_accuracy_result"])
        self.assertEqual(self.report["other_41_original_tasks_NOT_attempted"],41)

    def test_09_all_four_D_I_initial_source_SHA_equal(self):
        for tid,entry in self.report["source_question_and_D_I_source_parity"].items():
            self.assertTrue(entry["D_I_initial_source_exact_byte_equality"])
            self.assertEqual(entry["original_public_question_sha256"],
                             self.tasks[tid]["public_question_sha256"])
            self.assertEqual(entry["model_tool_calls_per_real_I_case"],2)

    def test_10_actual_model_facing_read_is_byte_for_byte_same(self):
        for i,tid in enumerate(TASKS):
            source=self.source(tid)
            d=DirectOriginalStateSession050(source,self.root/f"d_{i}")
            p=LiveOriginalNativePythonSession052(source,self.root/f"i_{i}")
            a=d.call("read_building_xml",{})
            b=p.call("read_building_xml",{})
            self.assertEqual(a["xml"],b["xml"])
            self.assertEqual(len(a["xml"].encode("utf8")),
                             self.report["source_question_and_D_I_source_parity"]
                             [tid]["original_source_XML_bytes"])

    def test_11_task_specific_Python_code_is_executable_not_AST_plan(self):
        for tid in TASKS:
            for pos in (True,False):
                c=developer_python_source(
                    tid,self.tasks[tid]["public_question"],positive=pos)
                self.assertNotIn("NativeEditPlan",c)
                self.assertIn("commit()",c)
                self.assertGreater(len(c),80)
                self.assertLessEqual(len(c.encode("utf8")),MAX_CODE_BYTES)
                self.assertNotIn("open('/private-grader'",c)

    def test_12_developer_positive_negative_distinct(self):
        for tid in TASKS:
            a=developer_python_source(
                tid,self.tasks[tid]["public_question"],positive=True)
            b=developer_python_source(
                tid,self.tasks[tid]["public_question"],positive=False)
            self.assertNotEqual(sha256(a.encode()).hexdigest(),
                                sha256(b.encode()).hexdigest())

    def test_13_question_named_slab_guids_public_only(self):
        for tid in ("topological_test_11","topological_test_17"):
            guid=question_named_slab_guid(self.tasks[tid]["public_question"])
            self.assertEqual(len(guid),22)

    def test_14_malformed_question_fails_closed(self):
        with self.assertRaises(ValueError):
            question_named_slab_guid("Delete some columns with no id")
        with self.assertRaises(ValueError):
            question_named_slab_guid("id abcdefghijklmnopqrstuv and id ABCDEFGHIJKLMNOPQRSTUV")

    def test_15_unrelated_tasks_and_nonbool_control_rejected(self):
        with self.assertRaises(ValueError):
            developer_python_source("create_unknown","",positive=True)
        with self.assertRaises(ValueError):
            developer_python_source("geometry_test_14","",positive=1)

    def test_16_exact_pinned_local_image_id_in_real_report(self):
        self.assertEqual(self.report["real_pinned_Linux_Docker_image_SHA256"],
                         PINNED_DOCKER_IMAGE)
        self.assertEqual(self.report["strict_local_linux_pinned_image_admission"]
                         ["pinned_worker_image_id"],PINNED_DOCKER_IMAGE)

    def test_17_real_docker_six_transaction_security_cases(self):
        cases=self.report["security_transaction_records"]
        self.assertEqual(len(cases),6)
        self.assertEqual(
            self.report["real_Docker_rejected_security_transactions"],5)
        self.assertEqual(
            self.report["real_Docker_positive_native_IFC_security_witness"],1)
        self.assertTrue(all(r["real_Docker_Python_submitted"] for r in cases))
        self.assertTrue(all(r["worker_real_linux_backend"]=="linux_docker_sandbox"
                            for r in cases))
        self.assertTrue(self.report["real_Docker_previous_valid_candidate_rollback_pass"])

    def test_18_security_negative_worker_cannot_commit_into_host(self):
        rows=self.report["security_transaction_records"]
        for row in rows:
            if row["case"]=="sandbox_witness":
                self.assertTrue(row["host_native_ifc_committed"])
                self.assertFalse(row["invalid_transaction_rolled_back"])
            else:
                self.assertFalse(row["host_native_ifc_committed"])
                self.assertTrue(row["invalid_transaction_rolled_back"])

    def test_19_failed_worker_after_commit_truly_returned_error(self):
        row=next(x for x in self.report["security_transaction_records"]
                 if x["case"]=="error_after_commit")
        self.assertEqual(row["worker_status"],"error")
        self.assertTrue(row["worker_called_commit"])
        self.assertFalse(row["host_native_ifc_committed"])

    def test_20_uncommitted_worker_not_persisted(self):
        row=next(x for x in self.report["security_transaction_records"]
                 if x["case"]=="without_commit")
        self.assertEqual(row["worker_status"],"ok")
        self.assertFalse(row["worker_called_commit"])
        self.assertFalse(row["host_native_ifc_committed"])

    def test_21_wrong_Root_or_noop_rejected_after_worker_commit(self):
        rows=self.report["security_transaction_records"]
        for name in ("unrelated_root","source_noop",
                     "accepted_then_unauthorized_wall_rollback"):
            r=next(x for x in rows if x["case"]==name)
            self.assertTrue(r["worker_called_commit"])
            self.assertFalse(r["host_native_ifc_committed"])
            self.assertTrue(r["invalid_transaction_rolled_back"])

    def test_22_offline_source_code_does_not_embed_hidden_GTs(self):
        for name in ("bibimbap_v052_live_docker_controls.py",
                     "bibimbap_v052_live_original_native_python_session.py"):
            data=(audit.ROOT/"tools"/name).read_text(encoding="utf8")
            self.assertNotIn("bibimbap-author-gt",data)
            self.assertNotIn("model-generated answer",data.lower())

    def test_23_live_Docker_sandbox_policy_is_pinned_to_two_mounts(self):
        with TemporaryDirectory() as folder:
            cmd=build_pinned_docker_command(
                PINNED_DOCKER_IMAGE,"bibi-ifc-0123456789abcdef",Path(folder))
            self.assertEqual(cmd[1:3],[
                "--host","npipe:////./pipe/dockerDesktopLinuxEngine"])
            self.assertIn("--network=none",cmd)
            self.assertIn("--read-only",cmd)
            self.assertIn("--cap-drop=ALL",cmd)
            self.assertIn("--user=65534:65534",cmd)
            self.assertIn("--memory=768m",cmd)
            self.assertIn("--pids-limit=32",cmd)
            self.assertEqual(len([x for x in cmd
                if x.startswith("--mount=type=bind,")]),2)

    def test_24_no_local_image_fail_closed(self):
        with patch(
            "tools.bibimbap_v052_live_original_native_python_session.shutil.which",
            return_value=None):
            self.assertEqual(
                live_pinned_local_runtime_admission_v052()["status"],
                "BLOCKED_RUNTIME")

    def test_25_wrong_Linux_OSType_fail_closed(self):
        with patch(
            "tools.bibimbap_v052_live_original_native_python_session.shutil.which",
            return_value="docker"), patch(
            "tools.bibimbap_v052_live_original_native_python_session.subprocess.run",
            return_value=SimpleNamespace(returncode=0,stdout="windows\n",stderr="")):
            r=live_pinned_local_runtime_admission_v052()
        self.assertEqual(r["status"],"BLOCKED_RUNTIME")

    def test_26_wrong_image_sha_fail_closed(self):
        with patch(
            "tools.bibimbap_v052_live_original_native_python_session.shutil.which",
            return_value="docker"), patch(
            "tools.bibimbap_v052_live_original_native_python_session.subprocess.run",
            side_effect=[
                SimpleNamespace(returncode=0,stdout="linux\n",stderr=""),
                SimpleNamespace(returncode=0,stdout="sha256:"+"0"*64,stderr=""),
            ]) as subprocess_mock:
            r=live_pinned_local_runtime_admission_v052()
        self.assertEqual(r["status"],"BLOCKED_RUNTIME")
        self.assertEqual(subprocess_mock.call_count,2)

    def test_27_fast_admission_uses_readonly_version_not_slow_info(self):
        with patch(
            "tools.bibimbap_v052_live_original_native_python_session.shutil.which",
            return_value="docker"), patch(
            "tools.bibimbap_v052_live_original_native_python_session.subprocess.run",
            side_effect=[
                SimpleNamespace(returncode=0,stdout="linux\n",stderr=""),
                SimpleNamespace(returncode=0,stdout=PINNED_DOCKER_IMAGE+"\n",stderr=""),
            ]) as mock_run:
            r=live_pinned_local_runtime_admission_v052()
        self.assertEqual(r["status"],"RUNTIME_ADMITTED")
        args0=mock_run.call_args_list[0].args[0]
        self.assertIn("version",args0)
        self.assertNotIn("info",args0)
        self.assertIn("image",mock_run.call_args_list[1].args[0])

    def test_28_production_session_never_accepts_mock_executor(self):
        s=LiveOriginalNativePythonSession052(
            self.source(),self.root/"native")
        self.assertIs(type(s.executor),DockerIFCExecutor)
        self.assertFalse(s.is_offline_double)

    def test_29_blocked_runtime_never_invokes_executor(self):
        s=LiveOriginalNativePythonSession052(
            self.source(),self.root/"blocked")
        with patch(
            "tools.bibimbap_v052_live_original_native_python_session.live_pinned_local_runtime_admission_v052",
            return_value={"status":"BLOCKED_RUNTIME","reason":"TEST_BLOCKED"}),patch.object(
            s.executor,"run") as fake:
            r=s.call("execute_ifc_code",{"code":"commit()"})
        self.assertEqual(r["error_type"],"BLOCKED_RUNTIME")
        fake.assert_not_called()
        self.assertEqual(list(s.folder.iterdir()),[])

    def test_30_tool_calls_bounded_to_25(self):
        s=LiveOriginalNativePythonSession052(
            self.source(),self.root/"budget")
        for n in range(25):
            self.assertEqual(s.call("read_building_xml",{})["status"],"ok")
        self.assertEqual(s.call("execute_ifc_code",{"code":"commit()"})["error_type"],
                         "ToolBudgetExhausted")

    def test_31_D_I_representation_consistency_not_model_causal_claim(self):
        self.assertEqual(self.report["original_bibimbap_task_count"],45)
        self.assertTrue(
            self.report["selected_original_four_engineering_tasks_not_random_sample"])
        self.assertIsNone(
            self.report["causal_XML_D_vs_Python_I_model_accuracy_result"])

    def test_32_immutable_report_exclusive_creation_gate(self):
        with self.assertRaises(FileExistsError):
            with audit.REPORT.open("xb") as file:
                pass


if __name__=="__main__":
    unittest.main()
