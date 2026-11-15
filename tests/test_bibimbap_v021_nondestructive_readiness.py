"""v0.21 non-destructive original-public Docker readiness gate tests.

Synthetic probe injection never calls Docker. The committed ACTUAL readiness
report comes from a separately executed host-only read-only command plan.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import unittest

from tools.bibimbap_v021_nondestructive_readiness import (
    AUTHOR_SHA, DATA_SHA, DOCKER_ARGS, DOCKER_ENGINE,
    IMAGE_ID, INFO_ARGS, INSPECT_ARGS, ORPHANS_ARGS, PROBE_COMMANDS,
    PROBE_NAMES, FORBIDDEN_DOCKER_ARGS,
    Observation, HostReadinessBlocked, run_host_probe,
    validate_command_plan, verify_observations,
)

HERE = Path(__file__).resolve().parents[1]
REPORT = HERE / "reports" / "bibimbap_v021_nondestructive_host_readiness_20261115.json"
FROZEN_V020 = HERE / "reports" / "bibimbap_v020_original45_capability_and_terminal_gate_20261115.json"
FROZEN_V020_SHA = "1aa218a0883186e6df1e7e7d895670fb9e012ef0229799b14881a87473f762be"


def good_observations(*, cold: float = 14.422, warm: float = 0.281) -> dict:
    a = {
        name: Observation(name, 0, 0.25, "")
        for name in PROBE_NAMES
    }
    a["cold_image"] = Observation("cold_image", 0, cold, IMAGE_ID)
    a["warm_image"] = Observation("warm_image", 0, warm, IMAGE_ID)
    a["docker_info"] = Observation("docker_info", 0, 0.25, "linux|amd64")
    a["author_sha"] = Observation("author_sha", 0, 0.1, AUTHOR_SHA)
    a["data_sha"] = Observation("data_sha", 0, 0.1, DATA_SHA)
    a["author_clean"] = Observation("author_clean", 0, 0.1, "")
    a["data_clean"] = Observation("data_clean", 0, 0.1, "")
    a["venv_import"] = Observation("venv_import", 0, 0.1, "0.8.4.post1")
    return a


class V021HostReadinessTests(unittest.TestCase):
    def test_all_expected_readonly_docker_commands_fixed(self):
        validate_command_plan()
        self.assertEqual(set(PROBE_COMMANDS),
                         {"cold_image","warm_image","docker_info","old_worker_orphans"})
        self.assertEqual(PROBE_COMMANDS["cold_image"],INSPECT_ARGS)
        self.assertEqual(PROBE_COMMANDS["warm_image"],INSPECT_ARGS)
        self.assertEqual(PROBE_COMMANDS["docker_info"],INFO_ARGS)
        self.assertEqual(PROBE_COMMANDS["old_worker_orphans"],ORPHANS_ARGS)
        self.assertEqual(DOCKER_ARGS[1:],["--host",DOCKER_ENGINE])
        for argv in PROBE_COMMANDS.values():
            self.assertFalse(FORBIDDEN_DOCKER_ARGS.intersection(argv))
            self.assertNotIn("--privileged",argv)
            self.assertNotIn("--mount",argv)
            self.assertNotIn("--volume",argv)

    def test_cold_first_warm_second_is_ready_without_restart(self):
        verdict=verify_observations(good_observations())
        self.assertEqual(verdict["status"],"READY_FOR_SCOPED_OFFLINE_ORIGINAL_DOCKER_REGRESSION_ONLY")
        self.assertTrue(verdict["docker_first_probe_exceeded_prior_12_second_limit"])
        self.assertEqual(verdict["docker_second_image_inspect_seconds"],0.281)
        self.assertFalse(verdict["docker_desktop_or_wsl_service_restarted"])
        self.assertFalse(verdict["causal_pure_representation_comparison_ready"])
        self.assertTrue(verdict["no_real_LLM_trial_or_paid_model_run_authorized"])

    def test_both_fast_is_ready_but_not_continuous_guarantee(self):
        verdict=verify_observations(good_observations(cold=0.77,warm=0.29))
        self.assertFalse(verdict["docker_first_probe_exceeded_prior_12_second_limit"])
        self.assertTrue(verdict["host_readiness_is_a_point_in_time_not_availability_guarantee"])

    def test_warm_image_slower_than_old_worker_12s_margin_fails(self):
        for latency in (10.0,12.0,15.0,19.0):
            with self.subTest(warm=latency):
                x=good_observations(warm=latency)
                with self.assertRaises(HostReadinessBlocked):
                    verify_observations(x)

    def test_original_worker_image_id_tampering_fails(self):
        for key in ("cold_image","warm_image"):
            x=good_observations()
            x[key]=Observation(key,0,0.2,"sha256:"+"f"*64)
            with self.subTest(key=key),self.assertRaises(HostReadinessBlocked):
                verify_observations(x)

    def test_nonlinux_engine_rejected_even_if_image_hash_matches(self):
        x=good_observations()
        x["docker_info"]=Observation("docker_info",0,0.1,"windows|amd64")
        with self.assertRaises(HostReadinessBlocked):
            verify_observations(x)

    def test_stopped_or_running_old_worker_container_requires_manual_review(self):
        x=good_observations()
        x["old_worker_orphans"]=Observation("old_worker_orphans",0,0.1,"abc1234")
        with self.assertRaises(HostReadinessBlocked):
            verify_observations(x)

    def test_scorer_original_author_and_data_git_mutations_fail(self):
        scenarios=[
            ("author_sha", "a"*40),("data_sha","b"*40),
            ("author_clean"," M data/tests/test_15.py"),
            ("data_clean","?? other.ifc"),
            ("venv_import","0.8.3"),
        ]
        for key,changed in scenarios:
            x=good_observations()
            x[key]=Observation(key,0,0.1,changed)
            with self.subTest(key=key),self.assertRaises(HostReadinessBlocked):
                verify_observations(x)

    def test_failed_timeout_or_missing_probe_fails_closed(self):
        for key in PROBE_NAMES:
            x=good_observations()
            x[key]=Observation(key,None,12.0,"",True)
            with self.subTest(key=key),self.assertRaises(HostReadinessBlocked):
                verify_observations(x)
        x=good_observations()
        del x["warm_image"]
        with self.assertRaises(HostReadinessBlocked):
            verify_observations(x)

    def test_malformed_probe_name_or_type_or_negative_latency_fails(self):
        x=good_observations()
        x["warm_image"]=Observation("fake_probe",0,0.1,IMAGE_ID)
        with self.assertRaises(HostReadinessBlocked):verify_observations(x)
        x=good_observations()
        x["warm_image"]=Observation("warm_image",0,-0.5,IMAGE_ID)
        with self.assertRaises(HostReadinessBlocked):verify_observations(x)
        x=good_observations()
        x["warm_image"]=False
        with self.assertRaises(HostReadinessBlocked):verify_observations(x)

    def test_v020_parent_frozen_full45_evidence_unchanged(self):
        self.assertTrue(FROZEN_V020.is_file())
        self.assertEqual(sha256(FROZEN_V020.read_bytes()).hexdigest(),FROZEN_V020_SHA)
        src=json.loads(FROZEN_V020.read_text(encoding="utf8"))
        self.assertEqual(len(src["all45_original_public_task_capability_matrix"]),45)
        self.assertEqual(src["original45_developer_both_arm_native_IFC_byte_equivalence"],5)
        self.assertEqual(src["original45_author_scorable_developer_both_arm"],3)
        self.assertEqual(src["new_real_matched_LLM_D_I_trials"],0)

    def test_committed_actual_host_preflight_does_not_claim_model_success(self):
        if not REPORT.is_file():
            raise unittest.SkipTest("Read-only host readiness audit not captured yet")
        r=json.loads(REPORT.read_text(encoding="utf8"))
        self.assertEqual(r["status"],"READY_FOR_SCOPED_OFFLINE_ORIGINAL_DOCKER_REGRESSION_ONLY")
        self.assertEqual(r["pinned_local_image_sha256"],IMAGE_ID)
        self.assertEqual(r["pinned_original_author_sha"],AUTHOR_SHA)
        self.assertEqual(r["pinned_original_data_sha"],DATA_SHA)
        self.assertFalse(r["docker_desktop_or_wsl_service_restarted"])
        self.assertFalse(r["docker_cli_actually_started_or_modified_containers"])
        self.assertTrue(r["no_real_LLM_trial_or_paid_model_run_authorized"])
        self.assertFalse(r["causal_pure_representation_comparison_ready"])


if __name__ == "__main__":
    unittest.main()
