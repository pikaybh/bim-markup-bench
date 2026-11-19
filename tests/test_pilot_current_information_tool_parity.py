"""Current 36-task G3 D/I parity audit — actual bytes, transparent blockers.

No provider, trial execution, ground-truth bytes, grader, paid use or new
harness. The full original study denominator is retained in the frozen report.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from src.data.pilot_workspace import _frozen_inputs, pilot_staging_preflight
from src.direct_markup.agent_runner import SourceOnlySettings
from src.imperative_control.agent_runner import (
    ControlConfig, MatchedObservations, ImperativeControlSession, API_NOTES,
)
from src.runner.frozen_context_parity import (
    FrozenContextAuditError,
    audit_current_pilot_information_and_tool_parity,
)
from src.runner.offline_context_cost_gate import (
    OfflineContextGateError, matched_shared_components,
)

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"reports/g3_bim_edit_36_task_information_and_tool_parity_20261119.json"


class G3CurrentPilotInformationAndToolParityTests(unittest.TestCase):
    def test_original_full_sample_retained_and_absent_inputs_remain_blocked(self):
        selected,audited,remote,pilot=_frozen_inputs(ROOT)
        preflight=pilot_staging_preflight(ROOT)
        self.assertEqual(len(selected),36)
        self.assertEqual(len(audited),25)
        self.assertEqual(preflight["original_tasks"],36)
        self.assertEqual(preflight["input_available_tasks"],30)
        self.assertEqual(preflight["blocked_input_tasks"],6)
        self.assertFalse(preflight["llm_launch_allowed"])

    def test_draft_model_attempt_wall_edit_byte_limits_are_structurally_matched(self):
        d=SourceOnlySettings()
        i=ControlConfig()
        self.assertEqual(d.mode,i.mode)
        self.assertEqual(d.max_attempts,i.max_attempts)
        self.assertEqual(d.max_wall_seconds,i.max_wall_seconds)
        self.assertEqual(d.max_edit_bytes,i.max_output_bytes)
        self.assertEqual((d.max_attempts,d.max_wall_seconds,d.max_edit_bytes),
                         (1,180,32768))
        self.assertNotEqual(d.max_xml_bytes,i.max_output_bytes)

    def test_imperative_only_api_notes_really_exposed(self):
        example=MatchedObservations(
            "TEST-AB","This is a fabricated no-IFC prompt","<Building/>",
            "toy-schema","a"*64
        )
        visible=ImperativeControlSession(example,ControlConfig()).model_visible_context()
        self.assertEqual(
            visible["api_reference_notes"],API_NOTES.read_text(encoding="utf8")
        )
        self.assertEqual(len(visible["api_reference_notes"].encode("utf8")),1113)
        self.assertEqual(visible["toy_language_spec"],"toy-schema")
        self.assertEqual(visible["allowed_authoring_operations"],["submit_python_text"])
        self.assertEqual(visible["allowed_execution_operations"],[])
        self.assertFalse(visible["OS_sandbox_available"])

    def test_fabricated_common_xml_difference_is_detected(self):
        shared=SimpleNamespace(
            task_id="TEST-AB",instruction="Invented synthetic instruction",
            xml_text="<Building version='1'/>",language_spec="toy-schema",
        )
        compared=MatchedObservations(
            task_id=shared.task_id,instruction=shared.instruction,
            model_xml_text="<Building version='2'/>",
            toy_language_spec=shared.language_spec,
            input_ifc_sha256="a"*64,
        )
        with self.assertRaisesRegex(
            OfflineContextGateError,"common source observation mismatch"
        ):
            matched_shared_components(shared,compared,"a"*64)

    def test_fabricated_shared_xml_and_schema_positive(self):
        shared=SimpleNamespace(
            task_id="TEST-AB",instruction="Invented synthetic instruction",
            xml_text="<Building version='1'/>",language_spec="toy-schema",
        )
        compared=MatchedObservations(
            task_id=shared.task_id,instruction=shared.instruction,
            model_xml_text=shared.xml_text,
            toy_language_spec=shared.language_spec,
            input_ifc_sha256="a"*64,
        )
        result=matched_shared_components(shared,compared,"a"*64)
        self.assertEqual(result["v01_source_xml"]["sha256"],
                         sha256(shared.xml_text.encode("utf8")).hexdigest())
        self.assertIsNone(result["v01_source_xml"]["provider_input_tokens"])

    def test_changed_full_denominator_is_rejected_before_projection(self):
        with patch("src.runner.frozen_context_parity.pilot_staging_preflight") as preflight:
            preflight.return_value={
                "input_available_tasks":36,"blocked_input_tasks":0,
                "llm_launch_allowed":False,
            }
            with self.assertRaises(FrozenContextAuditError):
                audit_current_pilot_information_and_tool_parity(ROOT)

    def test_existing_two_arm_plan_is_not_silently_rebranded_three_arm_registered(self):
        plan=json.loads((ROOT/"configs/pilot_36_plan_v0.json").read_text("utf8"))
        self.assertEqual(plan["arms"],["direct_xml","imperative_python"])
        self.assertEqual(plan["study_protocol_status"],"DRAFT_NOT_FROZEN")
        self.assertIs(plan["actual_provider_spend_authorized"],False)
        self.assertEqual(pilot_staging_preflight(ROOT)["arms"],
                         ["D_FULL","D_MANAGED","I_NATIVE"])

    def test_frozen_actual_evidence_remains_fail_closed_no_leaked_answers(self):
        if not REPORT.is_file():
            self.skipTest("New canonical report is not yet materialized")
        raw=REPORT.read_bytes()
        self.assertNotIn(b"\r\n",raw)
        self.assertEqual(
            sha256(raw).hexdigest(),
            "c78650e8e30f50029237e927ae6006e18a92e9872416e9e75c03290db22abad8",
        )
        report=json.loads(raw)
        self.assertEqual(report["task_total"],36)
        self.assertEqual(report["cached_input_tasks"],30)
        self.assertEqual(report["missing_input_tasks"],6)
        self.assertEqual(report["actual_independent_d_and_i_source_text_matches"],30)
        self.assertEqual(len(report["per_task_source_only_metadata"]),36)
        self.assertEqual(
            report["status_counts"]["BLOCKED_ORIGINAL_INPUT_MISSING_OR_INVALID"],6
        )
        self.assertEqual(
            report["status_counts"]["COMMON_V01_SOURCE_TEXT_MATCHED_UNEQUAL_EXECUTION_AND_API_GUIDANCE"],30
        )
        self.assertFalse(report["all_model_visible_documents_identical_between_arms"])
        self.assertFalse(report["three_arm_representation_semantics_preregistered"])
        self.assertFalse(report["same_exact_provider_tokens_measured"])
        self.assertFalse(report["model_launch_allowed"])
        self.assertEqual(report["official_benchmark_tasks_scored"],0)
        self.assertFalse(report["real_model_provider_called"])
        self.assertEqual(report["I_only_extra_api_notes"]["utf8_bytes"],1113)
        self.assertEqual(
            len([row for row in report["per_task_source_only_metadata"]
                 if row["source_is_other_task_reference_path"]]),22
        )
        for forbidden in (
            '"ground_truth_ifc"','"target_guid"','"private_grader"',
            '"ifc_content"','"raw_instruction"','"prompt_text"',
        ):
            self.assertNotIn(forbidden,raw.decode("utf8"))
        good=[
            row for row in report["per_task_source_only_metadata"]
            if row["status"].startswith("COMMON_V01_")
        ]
        self.assertEqual(min(r["shared_source_xml_utf8_bytes"] for r in good),624)
        self.assertEqual(max(r["shared_source_xml_utf8_bytes"] for r in good),30043)
        self.assertEqual(
            {r["shared_language_spec_utf8_bytes"] for r in good},{7383}
        )
        self.assertEqual(
            {r["I_only_extra_api_notes_utf8_bytes"] for r in good},{1113}
        )


if __name__=="__main__":
    unittest.main()
