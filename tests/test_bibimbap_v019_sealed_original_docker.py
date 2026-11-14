"""v0.19 original public IFC sealed Linux Docker one-shot writer regression.

Tests the actually pinned original public source + previously committed
v0.18 read parity evidence. Host-private outputs never reach LLM receipts.
Dynamic OS execution covers only OWN developer programs and negative probes.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import os
import tempfile
import unittest

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.audit_bibimbap_v019_sealed_original import (
    V018_FROZEN_SHA, audit,
)
from tools.bibimbap_v019_sealed_original_docker import (
    PINNED_LOCAL_IMAGE, OWN_SECURITY_TEST_SCRIPT, OWN_LEAK_OUTPUT_SCRIPT,
    OWN_INFINITE_LOOP_SCRIPT, SealedWorkerBlocked,
    build_sealed_docker_create_args, original_public_column15_owned_script,
    run_owned_original_sealed, terminal_model_visible_receipt,
    validate_original_source_and_owned_fixture,
)

BASE = Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE", r"D:\문서\D__1_Projects\202611"))
HERE = Path(__file__).resolve().parents[1]
AUTHOR = BASE / "bibimbap-author-upstream"
DATA = BASE / "bibimbap-author-data"
OLD = HERE / "reports" / "bibimbap_v018_original45_common_read_observation_audit_20261114.json"
NEW = HERE / "reports" / "bibimbap_v019_sealed_original_test15_os_and_author_20261114.json"
NEW_SHA = "5a49f85e74398269ad5a094db9ec362fe9ed4658a89028a68b3c08452059075e"


class V019SealedOriginalIFCWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (NEW.is_file() and OLD.is_file() and AUTHOR.is_dir() and DATA.is_dir()):
            raise unittest.SkipTest("Pinned original author/public-data evidence not installed")
        cls.report = json.loads(NEW.read_text(encoding="utf8"))
        cls.tasks = {x["test_id"]:x for x in public_45(AUTHOR, DATA)}
        cls.task = cls.tasks["test_15"]
        cls.source = DATA / "ifc" / cls.task["original_source_ifc_relpath"]
        cls.original_sha = file_hash(cls.source)

    def test_original_45_denominator_and_pinned_source_grader_unchanged(self):
        self.assertEqual(len(self.tasks),45)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)
        self.assertEqual(Counter(x["crud"] for x in self.tasks.values()),
                         Counter({"create":15,"update":15,"delete":15}))
        self.assertEqual(file_hash(OLD),V018_FROZEN_SHA)
        self.assertEqual(file_hash(NEW),NEW_SHA)
        self.assertEqual(self.original_sha,self.task["original_ifc_sha256"])
        self.assertEqual(self.report["original_all45_denominator_preserved"],45)
        self.assertEqual(self.report["parent_v018_frozen_report_sha256"],V018_FROZEN_SHA)
        self.assertFalse(self.report["original_data_or_scorer_edited"])

    def test_own_public_IfcColumn_native_result_and_original_author_grader(self):
        self.assertEqual(
            self.report["status"],
            "ORIGINAL_PUBLIC_TEST15_SEALED_DOCKER_NATIVE_AND_AUTHOR_VALIDATION_PASS")
        self.assertEqual(self.report["original_case"],"test_15")
        self.assertEqual(self.report["original_public_question_sha256"],
                         self.task["public_question_sha256"])
        self.assertEqual(self.report["real_sealed_candidate_independent_native_IFC_oracle"],
                         "INDEPENDENT_REAL_IFC_TEST15_COLUMN_MOVE_VALIDATED")
        grade=self.report["real_sealed_candidate_has_original_native_author_score"]
        self.assertEqual(grade["status"],"AUTHOR_SCORED")
        self.assertEqual(grade["original_author_score"],1.0)
        self.assertGreater(self.report["real_sealed_candidate_ifc_bytes"],1000)
        self.assertEqual(len(self.report["real_sealed_candidate_native_ifc_sha256"]),64)
        self.assertTrue(self.report["whole_original_ifc_native_identity_and_geometry_oracle_PASS"])
        self.assertTrue(self.report["real_original_source_unit_mm_retained"])

    def test_original_security_denials_all_actually_probed_in_docker(self):
        flags=self.report["Docker_kernel_security_original_source_checks"]
        self.assertEqual(len(flags),14)
        self.assertEqual(set(flags),{
            "uid_nonroot","input_readable","source_readonly","own_code_readonly",
            "secrets_absent","gt_unmounted","host_user_hidden",
            "docker_socket_absent","network_denied","spawn_denied",
            "root_readonly","seccomp_active","capabilities_zero","no_new_privs"})
        self.assertTrue(all(v is True for v in flags.values()))
        self.assertTrue(self.report["Docker_readonly_source_and_code"])
        self.assertTrue(self.report["Docker_network_disabled"])
        self.assertTrue(self.report["Docker_no_private_GT_or_secrets_mounted"])
        self.assertTrue(self.report["container_logs_suppressed"])
        self.assertTrue(self.report["hung_one_shot_process_killed_and_container_cleanup"])

    def test_model_terminal_receipt_never_contains_candidate_artifact_or_status(self):
        model=terminal_model_visible_receipt()
        self.assertEqual(model,{
            "status":"SEALED_ONE_SHOT_SUBMISSION_RECORDED",
            "execution_feedback_available":False,
            "tool_continuation_allowed":False,
        })
        self.assertEqual(self.report["outgoing_model_feedback_after_submission"],model)
        text=json.dumps(model,sort_keys=True)
        self.assertNotIn("candidate_sha256",text)
        self.assertNotIn(self.original_sha,text)
        self.assertNotIn("V019_FAKE_PRIVATE_CANARY_AND_IFC_DATA_LEAK",text)
        self.assertFalse(self.report["stdout_canary_model_receipt_leak"])
        self.assertEqual(self.report["host_private_stdout_canary_probe_result"],
                         "NOT_RETURNED_TO_MODEL")

    def test_real_model_not_launched_and_research_not_falsely_promoted(self):
        self.assertEqual(self.report["new_real_paid_or_unpaid_LLM_calls"],0)
        self.assertEqual(self.report["new_paid_provider_USD"],0)
        self.assertEqual(self.report["new_original_public_developer_matched_edit_task_additions"],0)
        self.assertEqual(self.report["previous_actual_developer_edit_D0_I0_native_parity"],5)
        self.assertEqual(self.report["previous_original_author_scoreable_developer_edit_pairs"],3)
        self.assertEqual(self.report["previous_original_author_scorer_reference_errors"],2)
        self.assertEqual(self.report["other_original_edit_cases_same_D0_I0_protocol_UNTESTED"],40)
        self.assertFalse(self.report["pilot_causal_LLM_trial_approved"])
        self.assertFalse(self.report["real_model_generated_python_executed"])
        self.assertTrue(self.report[
            "python_code_can_still_interrogate_native_IFC_inside_one_shot_execution"])
        self.assertFalse(self.report[
            "full_original_IFC_information_and_native_write_capability_parity_proven"])

    def test_pinned_local_image_and_ownership_allowlist(self):
        code=original_public_column15_owned_script(self.task["public_question"])
        self.assertEqual(sha256(code).hexdigest(),
                         self.report["developer_owned_original_source_task_code_sha256"])
        self.assertEqual(PINNED_LOCAL_IMAGE,
                         self.report["trusted_cached_Linux_image_id"])
        self.assertTrue(code.startswith(b"\nimport ifcopenshell"))
        self.assertNotIn(b"tools.",code)
        self.assertNotIn(b"src.",code)
        validate_original_source_and_owned_fixture(
            self.source,self.original_sha,code,PINNED_LOCAL_IMAGE,18)

    def test_docker_create_argv_denies_root_network_secrets_privileged_mounts(self):
        with tempfile.TemporaryDirectory(prefix="bmb-v019-argv-") as d:
            inp=Path(d)/"input";task=Path(d)/"task"
            inp.mkdir();task.mkdir()
            argv=build_sealed_docker_create_args(
                PINNED_LOCAL_IMAGE,"bmb-v019-sealed-"+"a"*16,inp,task)
        required={
            "--pull=never","--network=none","--read-only",
            "--user=65534:65534","--cap-drop=ALL",
            "--security-opt=no-new-privileges:true","--pids-limit=1",
            "--memory=512m","--memory-swap=512m","--cpus=0.75",
            "--ipc=none","--cgroupns=private","--log-driver=none",
            "--ulimit=fsize=33554432:33554432"}
        self.assertTrue(required.issubset(set(argv)))
        self.assertEqual(sum("--mount=" in x for x in argv),2)
        self.assertFalse(any("target=/output" in x for x in argv))
        self.assertFalse(any("target=/grader" in x for x in argv))
        self.assertFalse(any("target=/var/run/docker.sock" in x for x in argv))
        self.assertTrue(all(x.endswith(",readonly") for x in argv if x.startswith("--mount=")))
        self.assertEqual(argv[-2:], [PINNED_LOCAL_IMAGE, "/opt/ifc_worker/run_candidate.py"])
        self.assertNotIn("--privileged",argv)

    def test_reject_image_tag_and_invalid_name_before_running_any_code(self):
        with tempfile.TemporaryDirectory(prefix="bmb-v019-invalid-") as d:
            p=Path(d);inp=p/"input";task=p/"task";inp.mkdir();task.mkdir()
            with self.assertRaises(SealedWorkerBlocked):
                build_sealed_docker_create_args(
                    "bim-markup-bench/ifc-worker:amd64-0.1.0",
                    "bmb-v019-sealed-"+"a"*16,inp,task)
            with self.assertRaises(SealedWorkerBlocked):
                build_sealed_docker_create_args(
                    PINNED_LOCAL_IMAGE,"not-our-container",inp,task)

    def test_reject_wrong_original_source_hash_and_script_before_Docker(self):
        with self.assertRaises(SealedWorkerBlocked):
            run_owned_original_sealed(self.source,"0"*64,OWN_SECURITY_TEST_SCRIPT,
                                      expects_ifc_result=False)
        with self.assertRaises(SealedWorkerBlocked):
            run_owned_original_sealed(self.source,self.original_sha,
                                      b"print('ARBITRARY_UNTRUSTED_CODE')\n",
                                      expects_ifc_result=False)
        with self.assertRaises(SealedWorkerBlocked):
            run_owned_original_sealed(self.source,self.original_sha,
                                      OWN_LEAK_OUTPUT_SCRIPT,expects_ifc_result=False)
        with self.assertRaises(SealedWorkerBlocked):
            run_owned_original_sealed(self.source,self.original_sha,
                                      OWN_SECURITY_TEST_SCRIPT,
                                      image_id="bim-markup-bench/ifc-worker:amd64-0.1.0",
                                      expects_ifc_result=False)

    def test_source_is_not_modified_and_no_external_provider_calls(self):
        self.assertEqual(file_hash(self.source),self.original_sha)
        self.assertEqual(_head(DATA),DATA_SHA)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertFalse(self.report["original_public_IFC_modified"])
        self.assertFalse(self.report["original_author_scorer_mounted_in_container"])

    def test_full_original_sealed_audit_byte_reproduces_independently(self):
        regenerated=audit(AUTHOR,DATA,OLD)
        self.assertEqual(regenerated,self.report)
        self.assertEqual(file_hash(self.source),self.original_sha)
        self.assertFalse(regenerated["real_model_generated_python_executed"])


if __name__=="__main__":
    unittest.main()
