"""G1 trusted public-prompt Wall/Path native IFC pair security/regression.

Strictly synthetic/developer-selected parsing and source-only native IFC.
Never score private benchmark GT, enable model billing or count a solved
official task. Tests include forged answer metadata, bad public text,
source tampering and topology modification rejection.
"""
from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell
from src.data.bim_edit import read_tasks
from src.runner.offline_context_cost_gate import OfflineContextGateError
from tools import verify_prompt_grounded_spatial_wall as gate


class PromptGroundedSpatialWallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public,cls.original,cls.sha=gate.verified_public_input()
        cls.spec=gate.parse_public_wall_spec(cls.public["instruction"])

    def test_published_instruction_only_and_three_original_native_identifiers(self):
        self.assertEqual(set(self.public),{"task_id","instruction","input_file"})
        self.assertEqual(self.sha,gate.SOURCE_SHA)
        self.assertEqual(self.spec.door_right_jamb_offset_y_m,Decimal("1.3025"))
        self.assertEqual(self.spec.thickness_m,Decimal("0.175"))
        self.assertEqual(self.spec.height_m,Decimal("2.800"))
        self.assertEqual(len({self.spec.first_wall,self.spec.second_wall,self.spec.room}),3)
        self.assertEqual(
            sha256(self.public["instruction"].encode("utf8")).hexdigest(),
            "31a00588498f68ef6791a133b033cc3da442749d5a237e76f0f5817cf095d14d")

    def test_real_source_geometry_derived_without_task_target_or_gt(self):
        native,projection,g=gate._actual_world_geometry(
            self.public,self.original,self.spec)
        self.assertEqual(native.schema,"IFC4X3")
        self.assertTrue(g["prompt_room_visible_in_xml"])
        self.assertAlmostEqual(float(g["start"][0]),0.175,places=5)
        self.assertAlmostEqual(float(g["end"][0]),4.625,places=5)
        self.assertAlmostEqual(float(g["start"][1]),5.23275,places=5)
        self.assertAlmostEqual(float(g["end"][1]),5.23275,places=5)
        self.assertEqual(g["height"],self.spec.height_m)
        self.assertEqual(g["thickness"],self.spec.thickness_m)

    def test_prompt_grounded_d0_document_and_independent_i0_native(self):
        report=gate.verify_prompt_grounded_spatial_wall()
        self.assertEqual(report["frozen_task_id"],gate.CASE)
        self.assertTrue(report["native_d0_i0_ifc_six_category_parity"])
        self.assertEqual(report["native_path_joins_to_prompt_walls"],2)
        self.assertTrue(report["original_native_relationships_preserved"])
        self.assertTrue(report["existing_native_roots_preserved"])
        self.assertTrue(report["existing_space_boundaries_unmodified"])
        self.assertEqual(report["native_wall_bbox_min_m"],[0.175,5.23275,0.0])
        self.assertEqual(report["native_wall_bbox_max_m"],[4.625,5.40775,2.8])
        self.assertEqual(report["source_room_wall_volume_overlap_m3"],2.1805)
        self.assertEqual(len(report["d0_ifc_sha256"]),64)
        self.assertEqual(len(report["i0_ifc_sha256"]),64)
        self.assertFalse(report["full_ifc_files_byte_equal"])
        self.assertTrue(report["common_model_source_components_byte_identical"])
        self.assertEqual(len(report["common_actual_model_visible_text_component_hashes"]),5)
        self.assertGreater(report["I0_only_api_reference_bytes"],0)
        self.assertFalse(report["equal_provider_model_tokenization_or_execution_feedback_proven"])
        self.assertFalse(report["new_room_name_type_psets_qto_in_public_instruction"])
        self.assertFalse(report["room_split_if_required_by_official_target_proven"])
        self.assertFalse(report["complete_task_oracle_proven"])
        self.assertFalse(report["model_generated_output_used"])
        self.assertEqual(report["official_tasks_scored"],0)
        self.assertEqual(report["model_provider_calls"],0)

    def test_repeatable_native_semantic_evidence_but_no_raw_file_sha_claim(self):
        first=gate.verify_prompt_grounded_spatial_wall()
        second=gate.verify_prompt_grounded_spatial_wall()
        # Existing IfcOpenShell IFC relationship IDs may be random; the
        # report deliberately records real output bytes, but a reproducible
        # native semantic check must NOT claim byte-stable IFC files.
        for result in (first,second):
            self.assertTrue(result["native_d0_i0_ifc_six_category_parity"])
            self.assertTrue(result["original_native_relationships_preserved"])
            self.assertTrue(result["existing_space_boundaries_unmodified"])
            self.assertEqual(result["native_path_joins_to_prompt_walls"],2)
            self.assertEqual(result["source_room_wall_volume_overlap_m3"],2.1805)
            self.assertFalse(result["complete_task_oracle_proven"])
        for key in set(first)-{"d0_ifc_sha256","i0_ifc_sha256"}:
            self.assertEqual(first[key],second[key],key)
        self.assertEqual(gate._sha(self.original),self.sha)

    def test_private_task_metadata_poisoning_never_affects_pair(self):
        task=next(x for x in read_tasks(gate.ROOT/"data/tasks.jsonl")
                  if x["task_id"]==gate.CASE)
        adversarial=dict(task)
        adversarial["target"]={"guids":["0"*22],"class":"IfcDoor"}
        adversarial["ground_truth_ifc"]="secret_result.ifc"
        adversarial["evaluation"]={"perfect_answer":"NEVER_EXPOSE_TO_MODEL"}
        with patch.object(gate,"read_tasks",return_value=[adversarial]):
            report=gate.verify_prompt_grounded_spatial_wall()
        self.assertFalse(report["source_private_target_or_ground_truth_used"])
        self.assertTrue(report["native_d0_i0_ifc_six_category_parity"])

    def test_reject_extra_commands_wrong_direction_and_unrecognized_grammar(self):
        s=self.public["instruction"]
        cases={
            "extra_instruction":s+" Then remove the Door.",
            "new_direction":s.replace("+y direction","+x direction"),
            "negative_direction":s.replace("+y direction","-y direction"),
            "left_of_door":s.replace("right side of the door","left side of the door"),
            "outside_room":s.replace("inside of the room","outside of the room"),
            "non_orthogonal":s.replace("spans orthogonally","spans diagonally"),
            "missing_referenced_wall":s.replace("wall with the ID","slab with the ID",1),
            "missing_height":s.replace(" and a height of 2.800m",""),
            "missing_spacing":s.replace(" begins at ","begins at "),
            "empty":"",
            "excessive_text":"X"*700,
            "not_text":None,
        }
        for name,text in cases.items():
            with self.subTest(name=name),self.assertRaises(gate.WallPromptGateBlocked):
                gate.parse_public_wall_spec(text)

    def test_dimensions_and_wall_offset_cannot_be_posthoc_changed(self):
        s=self.public["instruction"]
        variants=(
            s.replace("1.3025m","1.3000m"),
            s.replace("1.3025m","0m"),
            s.replace("1.3025m","999m"),
            s.replace("0.175m","0.200m"),
            s.replace("0.175m","-0.175m"),
            s.replace("2.800m","2.900m"),
            s.replace("2.800m","0m"),
        )
        for text in variants:
            with self.subTest(text_sha=sha256(text.encode()).hexdigest()[:8]):
                with self.assertRaises(gate.WallPromptGateBlocked):
                    gate.parse_public_wall_spec(text)

    def test_same_public_numeric_value_with_extra_zeros_is_not_new_task(self):
        changed=self.public["instruction"].replace("1.3025m","1.302500m")
        self.assertEqual(self.spec,gate.parse_public_wall_spec(changed))

    def test_duplicate_and_malformed_guid_rejected(self):
        s=self.public["instruction"]
        for text in (
            s.replace(self.spec.first_wall,self.spec.second_wall),
            s.replace(self.spec.room,self.spec.first_wall),
            s.replace(self.spec.first_wall,"A"*21),
            s.replace(self.spec.second_wall,"!"*22),
        ):
            with self.assertRaises(gate.WallPromptGateBlocked):
                gate.parse_public_wall_spec(text)

    def test_nonexistent_guid_or_wrong_native_classes_rejected(self):
        for candidate in (
            replace(self.spec,first_wall="A"*22),
            replace(self.spec,room=self.spec.first_wall),
        ):
            with self.assertRaises((gate.WallPromptGateBlocked,ValueError)):
                gate._actual_world_geometry(
                    self.public,self.original,candidate)

    def test_old_native_relationship_deletion_and_unrelated_change_denied(self):
        original={
            "r1":("IfcRelSpaceBoundary",("space",),("wall",)),
            "r2":("IfcRelContainedInSpatialStructure",("level",),("old_wall",)),
        }
        accepted={
            **original,
            "r2":("IfcRelContainedInSpatialStructure",("level",),
                  ("old_wall","new_wall")),
            "r3":("IfcRelConnectsPathElements",("a",),("new_wall",)),
            "r4":("IfcRelConnectsPathElements",("b",),("new_wall",)),
        }
        self.assertEqual(gate._original_native_relations_preserved(
            original,accepted,"new_wall"),2)
        cases=(
            {k:v for k,v in accepted.items() if k!="r1"},
            {**accepted,"r1":("IfcRelSpaceBoundary",("space",),("other_wall",))},
            {**accepted,"r5":("IfcRelFillsElement",("a",),("b",))},
            {**accepted,"r2":("IfcRelContainedInSpatialStructure",
                             ("level",),("other_wall",))},
        )
        for variant in cases:
            with self.assertRaises(gate.WallPromptGateBlocked):
                gate._original_native_relations_preserved(
                    original,variant,"new_wall")

    def test_wrong_source_hash_or_modified_frozen_candidate_denied(self):
        for key in ("SOURCE_SHA","TASKS_SHA","PILOT_SHA"):
            with self.subTest(key=key),patch.object(gate,key,"0"*64):
                with self.assertRaises(gate.WallPromptGateBlocked):
                    gate.verified_public_input()

    def test_public_graph_source_observation_parity_failure_is_not_silenced(self):
        from src.imperative_control.agent_runner import create_matched_observations
        genuine=create_matched_observations(self.original,self.public)
        altered=replace(genuine,instruction=genuine.instruction+" EXTRA")
        with patch.object(gate,"create_matched_observations",return_value=altered):
            with patch.object(gate.TrustedCompilationController,"compile_accepted",
                              side_effect=AssertionError("Should never compile")):
                with self.assertRaises(OfflineContextGateError):
                    gate.verify_prompt_grounded_spatial_wall()

    def test_report_contains_only_provenance_and_no_prompt_or_target_ids(self):
        report=gate.verify_prompt_grounded_spatial_wall()
        serialized=json.dumps(report,sort_keys=True)
        for forbidden in (
            self.spec.first_wall,self.spec.second_wall,self.spec.room,
            self.public["instruction"],
            "NEVER_EXPOSE_TO_MODEL",
            '"ground_truth_ifc"','"target"','"evaluation"','"prompt"',
            "raw_ifc","new_wall_xml","generated_python_source",
        ):
            with self.subTest(forbidden=forbidden[:40]):
                self.assertNotIn(forbidden,serialized)
        self.assertFalse(report["experimental_v02_space_authoring_exposed_to_model"])
        self.assertFalse(report["G1_G2_G3_experiment_unblocked"])
        self.assertFalse(report["paid_spend_authorized"])

    def test_new_wall_identity_is_source_bound_and_no_command_xml_api(self):
        name=gate._created_guid(self.sha)
        self.assertEqual(len(name),22)
        self.assertNotEqual(name,gate._created_guid("0"*64))
        func=inspect.getsource(gate.verify_prompt_grounded_spatial_wall)
        self.assertNotIn("ground_truth_ifc",func)
        self.assertNotIn("compile_declarative_xml(",func)
        self.assertNotIn("source_space_metadata",func)
        self.assertNotIn("task.target",func)


if __name__=="__main__":
    unittest.main()
