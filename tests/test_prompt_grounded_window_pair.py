"""G1 #16: exact public Window prompt -> D0/I0 real-source edit tests.

Negative cases must reject mutated public text, wrong GUID bindings,
private target contamination, changed native non-target entities, and
unequal public-source observations. Never opens benchmark ground truth.
"""
from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell

from src.data.bim_edit import read_tasks
from src.runner.offline_context_cost_gate import OfflineContextGateError
from tools import verify_prompt_grounded_window_pair as gate


class PublicPromptWindowPairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public,cls.original,cls.digest=gate.verified_public_task_and_source()
        cls.move=gate.parse_public_window_move(cls.public["instruction"])

    def test_public_sentence_parses_correctly_without_private_answer_metadata(self):
        move=self.move
        self.assertEqual(move.positive_world_y_m,Decimal("1"))
        self.assertEqual(len(move.window_guid),22)
        self.assertEqual(len(move.opening_guid),22)
        self.assertNotEqual(move.window_guid,move.opening_guid)
        self.assertEqual(set(self.public),{"task_id","instruction","input_file"})
        self.assertEqual(self.digest,gate.PINNED_INPUT_SHA)

    def test_same_public_instruction_yields_full_native_equivalent_d0_i0(self):
        result=gate.verify_prompt_grounded_window_pair()
        self.assertEqual(result["task_id"],gate.FROZEN_TASK)
        self.assertEqual(result["original_public_ifc_sha256"],self.digest)
        self.assertTrue(result["public_window_and_opening_ids_resolved_without_grader_target_field"])
        self.assertTrue(result["world_move_read_from_public_instruction"])
        self.assertTrue(result["common_model_facing_observation_byte_identical"])
        self.assertTrue(result["window_and_opening_native_world_move_matches_instruction"])
        self.assertTrue(result["all_existing_relationships_preserved"])
        self.assertTrue(result["all_existing_IfcRoot_ids_preserved"])
        self.assertEqual(result["changed_native_entity_count_per_arm"],1)
        self.assertEqual(result["only_changed_native_entity_class"],"IfcCartesianPoint")
        self.assertTrue(result["independent_native_D0_I0_observation_parity"])
        self.assertTrue(result["IFC_full_file_d0_i0_equal"])
        self.assertEqual(result["d0_ifc_sha256"],result["i0_ifc_sha256"])
        self.assertEqual(result["d0_ifc_sha256"],
                         "10c68b5a1320f51e1f75f0e12868e1b38f84bc316a92a3c123059d0358bdfe16")
        self.assertEqual(result["official_tasks_scored"],0)
        self.assertEqual(result["LLM_calls"],0)
        self.assertFalse(result["G1_G2_G3_live_release_authorized"])
        self.assertFalse(result["full_official_reference_IFC_task_success_proven"])

    def test_full_pair_repeats_with_identical_result_and_preserved_original(self):
        old_sha=gate._sha(self.original)
        a=gate.verify_prompt_grounded_window_pair()
        b=gate.verify_prompt_grounded_window_pair()
        self.assertEqual(a,b)
        self.assertEqual(old_sha,gate._sha(self.original))

    def test_private_target_guid_and_GT_evaluation_fields_do_not_change_manual_pair(self):
        # Even forged private metadata is never consulted. Actual input
        # bytes and original task-file SHA are separately pinned.
        task=next(row for row in read_tasks(gate.ROOT/"data/tasks.jsonl")
                  if row["task_id"]==gate.FROZEN_TASK)
        forged=dict(task)
        forged["target"]={"entity_type":"IfcDoor","guids":["0"*22]}
        forged["ground_truth_ifc"]="NEVER_OPEN_FOR_AUTHORING.ifc"
        forged["evaluation"]={"solution":"FORBIDDEN"}
        with patch.object(gate,"read_tasks",return_value=[forged]):
            observed=gate.verify_prompt_grounded_window_pair()
        self.assertTrue(observed["source_task_target_metadata_read_for_authoring"] is False)
        self.assertEqual(
            observed["d0_ifc_sha256"],
            "10c68b5a1320f51e1f75f0e12868e1b38f84bc316a92a3c123059d0358bdfe16")
        self.assertFalse(observed["full_official_reference_IFC_task_success_proven"])

    def test_wrong_axes_sizes_extra_instructions_and_missing_relationships_denied(self):
        valid=self.public["instruction"]
        variants={
            "wrong_world_axis":valid.replace("positive y direction","positive x direction"),
            "negative_world_direction":valid.replace("positive y direction","negative y direction"),
            "wrong_metres":valid.replace("by 1m","by 2m"),
            "zero_distance":valid.replace("by 1m","by 0m"),
            "scientific_format":valid.replace("by 1m","by 1e2m"),
            "missing_opening":valid.replace("Also move the opening ","Also move the void "),
            "missing_preservation":valid.replace(" and preserve all relationships",""),
            "extra_instruction":valid+" Also delete the host.",
            "path_injection":valid+" ../grader/answers",
            "uncertain_english":valid.replace("the same","perhaps similarly"),
            "empty":"",
        }
        for name,text in variants.items():
            with self.subTest(name=name),self.assertRaises(
                gate.PromptGroundedOracleBlocked):
                gate.parse_public_window_move(text)

    def test_invalid_guid_shape_and_same_id_denied(self):
        valid=self.public["instruction"]
        for wrong in (
            valid.replace(self.move.window_guid,"!"*22),
            valid.replace(self.move.opening_guid,self.move.window_guid),
            valid.replace(self.move.window_guid,"A"*21),
        ):
            with self.subTest(raw=wrong[:30]),self.assertRaises(
                gate.PromptGroundedOracleBlocked):
                gate.parse_public_window_move(wrong)

    def test_same_prompt_magnitude_enforced_despite_valid_grammar(self):
        for replacement in ("0.5","1.00001","2","123456789"):
            wrong=self.public["instruction"].replace("by 1m","by "+replacement+"m")
            with self.subTest(distance=replacement),self.assertRaisesRegex(
                gate.PromptGroundedOracleBlocked,"frozen"):
                gate.parse_public_window_move(wrong)
        positive=self.public["instruction"].replace("by 1m","by 1.0m")
        # Exact same numeric value (1m) is deliberately not a new task.
        self.assertEqual(gate.parse_public_window_move(positive),
                         self.move)

    def test_public_guid_not_present_in_original_source_denied(self):
        native=ifcopenshell.open(str(self.original))
        wrong=replace(self.move,window_guid="A"*22)
        with self.assertRaisesRegex(gate.PromptGroundedOracleBlocked,"unresolved"):
            gate._native_prompt_bindings(native,wrong)

    def test_swapped_public_window_and_opening_class_denied(self):
        native=ifcopenshell.open(str(self.original))
        wrong=replace(self.move,window_guid=self.move.opening_guid,
                      opening_guid=self.move.window_guid)
        with self.assertRaisesRegex(gate.PromptGroundedOracleBlocked,"unresolved"):
            gate._native_prompt_bindings(native,wrong)

    def test_unrelated_existing_ifc_entity_guid_cannot_masquerade_as_window(self):
        native=ifcopenshell.open(str(self.original))
        wall=native.by_type("IfcWall")[0]
        with self.assertRaisesRegex(gate.PromptGroundedOracleBlocked,"unresolved"):
            gate._native_prompt_bindings(
                native,replace(self.move,window_guid=wall.GlobalId))

    def test_valid_world_vector_maps_to_only_native_host_local_offset(self):
        native=ifcopenshell.open(str(self.original))
        win,opening,host,offset=gate._native_prompt_bindings(native,self.move)
        self.assertEqual(win.GlobalId,self.move.window_guid)
        self.assertEqual(opening.GlobalId,self.move.opening_guid)
        self.assertTrue(host.is_a("IfcWall"))
        self.assertAlmostEqual(offset,1.0,places=9)

    def test_extra_native_ifc_mutation_other_than_one_point_fails(self):
        with TemporaryDirectory(prefix="own-extra-ifc-change-") as td:
            source=ifcopenshell.open(str(self.original))
            doc=Path(td)/"corrupt.ifc"
            # Another root attribute modified, not a valid move.
            source.by_type("IfcWall")[0].Name="Unexpected native mutation"
            source.write(str(doc))
            invalid=ifcopenshell.open(str(doc))
            original=ifcopenshell.open(str(self.original))
            opening=original.by_guid(self.move.opening_guid)
            point_id=opening.ObjectPlacement.RelativePlacement.Location.id()
            with self.assertRaisesRegex(
                gate.PromptGroundedOracleBlocked,"besides"):
                gate._changed_native_entity_classes(original,invalid,point_id)

    def test_no_change_or_wrong_native_entity_rejected(self):
        source=ifcopenshell.open(str(self.original))
        opening=source.by_guid(self.move.opening_guid)
        point_id=opening.ObjectPlacement.RelativePlacement.Location.id()
        with self.assertRaisesRegex(gate.PromptGroundedOracleBlocked,"besides"):
            gate._changed_native_entity_classes(source,source,point_id)

    def test_unequal_core_model_observations_fail_before_any_compilation(self):
        from src.imperative_control.agent_runner import create_matched_observations
        good=create_matched_observations(self.original,self.public)
        bad=replace(good,instruction=good.instruction+" Different public text.")
        with (
            patch.object(gate,"create_matched_observations",return_value=bad),
            patch.object(gate.TrustedCompilationController,"compile_accepted",
                         side_effect=AssertionError("Must not compile")),
        ):
            with self.assertRaises(OfflineContextGateError):
                gate._compile_pair_from_public_prompt(
                    self.public,self.original,self.digest,self.move)

    def test_wrong_frozen_task_metadata_sha_rejected(self):
        with patch.object(gate,"PINNED_PUBLIC_TASK_DATA_SHA","0"*64):
            with self.assertRaisesRegex(
                gate.PromptGroundedOracleBlocked,"digest changed"):
                gate.verified_public_task_and_source()
        with patch.object(gate,"PINNED_SAMPLE_SHA","0"*64):
            with self.assertRaisesRegex(
                gate.PromptGroundedOracleBlocked,"digest changed"):
                gate.verified_public_task_and_source()

    def test_wrong_input_ifc_sha_rejected(self):
        with patch.object(gate,"PINNED_INPUT_SHA","0"*64):
            with self.assertRaisesRegex(
                gate.PromptGroundedOracleBlocked,"original IFC bytes changed"):
                gate.verified_public_task_and_source()

    def test_audit_report_does_not_contain_task_answer_or_private_fields(self):
        report=gate.verify_prompt_grounded_window_pair()
        encoded=json.dumps(report,sort_keys=True)
        self.assertNotIn(self.move.window_guid,encoded)
        self.assertNotIn(self.move.opening_guid,encoded)
        self.assertNotIn(self.public["instruction"],encoded)
        for forbidden in (
            '"ground_truth_ifc"','"target"','"evaluation"','"prompt"',
            '"agent_generated_code"','"new_offset"',
            '"world_translation_m"','"wall_world_frame"',
        ):
            self.assertNotIn(forbidden,encoded)
        self.assertIsNone(report["model_provider_token_counts"])
        self.assertIsNone(report["paid_provider_charges_USD"])
        self.assertFalse(report["model_facing_tool_and_feedback_parity_approved"])
        self.assertFalse(report["developer_chosen_result_exposed_to_either_model"])

    def test_origin_of_independent_manual_implementation_remains_separate(self):
        import inspect
        source=inspect.getsource(gate.manual_ifc_reference)
        self.assertNotIn("compile_declarative_xml",source)
        self.assertNotIn("TrustedCompilationController",source)
        self.assertNotIn("parse_xml",source)


if __name__=="__main__":
    unittest.main()
