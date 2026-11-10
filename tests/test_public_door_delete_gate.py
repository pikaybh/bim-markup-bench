"""G1 #16: real pinned public Door Delete, I0 probe and D0 fail-closed gate."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell
import ifcopenshell.api.root

from src.data.bim_edit import read_tasks
from tests.oracles.python.independent_public_door_delete import (
    IndependentDoorDeleteBlocked, native_door_opening_delete,
)
from tests.oracles.python.public_door_delete_postconditions import (
    INPUT_SHA, PublicDoorDeleteBlocked, check_native_i0_result, published_guids,
)
from tools import verify_public_door_delete_gate as gate


class RealPublicDoorDeletionGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public, cls.guids, cls.source = gate.verified_public_source()
        cls.temp = TemporaryDirectory(prefix="public-door-delete-test-")
        cls.output = Path(cls.temp.name) / "I0.ifc"
        native_door_opening_delete(
            cls.source, cls.output, cls.guids["door"], cls.guids["opening"],
        )
        cls.native = check_native_i0_result(
            cls.source, cls.output, cls.public["instruction"])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_frozen_prompt_and_existing_source_are_public_only(self):
        self.assertEqual(set(self.public), {"task_id", "instruction", "input_file"})
        self.assertEqual(self.public["task_id"], gate.CASE)
        self.assertEqual(gate._sha(self.source), INPUT_SHA)
        self.assertEqual(len(set(self.guids.values())), 4)
        self.assertEqual(self.guids, published_guids(self.public["instruction"]))

    def test_actual_independent_i0_dependency_cleanup_and_one_missing_storey_relation(self):
        self.assertEqual(self.native["native_IfcRoot_deleted"], 10)
        self.assertEqual(self.native["native_IfcRelSpaceBoundary_deleted"], 1)
        self.assertEqual(self.native["surviving_shared_relations_updated"], 3)
        self.assertTrue(self.native["shared_type_relation_owner_history_automatically_modified"])
        self.assertEqual(self.native["original_Opening_direct_storey_assignments"], 0)
        self.assertFalse(self.native["explicit_opening_storey_assignment_existed"])
        self.assertTrue(self.native["host_wall_opening_void_closed"])
        self.assertAlmostEqual(self.native["host_wall_mesh_volume_gain_m3"], 0.374, places=4)
        self.assertFalse(self.native["unmentioned_space_boundary_policy_resolved"])
        self.assertEqual(self.native["official_tasks_scored"], 0)
        self.assertEqual(self.native["provider_model_calls"], 0)

    def test_full_gate_retains_blocked_status_and_rolls_back_d0(self):
        before = gate._sha(self.source)
        outcome = gate.verify_public_door_delete_gate()
        self.assertEqual(outcome["status"],
                         "BLOCKED_D0_DELETE_COMPILER_AND_PUBLIC_SPACE_BOUNDARY_POLICY")
        self.assertTrue(outcome["D0_XML_both_public_objects_visible_and_removed"])
        self.assertTrue(outcome["D0_valid_declarative_snapshot_accepted"])
        self.assertTrue(outcome["D0_trusted_compiler_failed_closed_before_write"])
        self.assertFalse(outcome["D0_native_output_written"])
        self.assertTrue(outcome["D0_shared_public_source_view_bytes_matched_I0"])
        self.assertTrue(outcome["source_Opening_direct_storey_assignment_does_not_exist"])
        self.assertTrue(outcome["I0_unmentioned_door_space_boundary_was_deleted"])
        self.assertFalse(outcome["D0_I0_both_native_success_proven"])
        self.assertFalse(outcome["full_task_oracle_proven"])
        self.assertFalse(outcome["G1_G2_G3_release_allowed"])
        self.assertEqual(outcome["official_tasks_scored"], 0)
        self.assertEqual(outcome["LLM_calls"], 0)
        self.assertEqual(gate._sha(self.source), before)

    def test_output_report_redacted_and_task_set_immutable(self):
        result = gate.verify_public_door_delete_gate()
        encoded = json.dumps(result, sort_keys=True)
        for private in (
            self.public["instruction"],
            *self.guids.values(), "ground_truth_ifc",
            "target_guid", '"evaluation"', '"target"',
            '"prompt"', "model_visible_GT", "API_KEY",
        ):
            self.assertNotIn(private, encoded)
        self.assertEqual(len(result["public_instruction_sha256"]), 64)
        self.assertEqual(result["input_ifc_sha256"], INPUT_SHA)

    def test_invalid_public_prompt_or_wrong_class_is_denied(self):
        instruction = self.public["instruction"]
        for mutation in (
            instruction + " Also delete the building.",
            instruction.replace("Delete the door", "Delete the window"),
            instruction.replace("the opening", "the space"),
            instruction.replace("and opening to storey", "and opening to room"),
            instruction.replace(self.guids["door"], self.guids["opening"]),
            instruction.replace(self.guids["wall"], "!" * 22),
        ):
            with self.subTest(instruction_sha=sha256(mutation.encode()).hexdigest()[:8]):
                with self.assertRaises(PublicDoorDeleteBlocked):
                    published_guids(mutation)

    def test_wrong_frozen_inputs_fail_before_any_mutation(self):
        for name in ("TASKS_SHA", "PILOT_SHA", "TREE_SHA"):
            with self.subTest(name=name), patch.object(gate, name, "0" * 64):
                with self.assertRaisesRegex(
                    PublicDoorDeleteBlocked, "frozen|Frozen|pin"):
                    gate.verified_public_source()
        with patch.object(gate, "INPUT_SHA", "0" * 64):
            with self.assertRaises(PublicDoorDeleteBlocked):
                gate.verified_public_source()

    def test_forged_private_task_metadata_cannot_change_public_oracle(self):
        row = next(x for x in read_tasks(gate.ROOT/"data/tasks.jsonl")
                   if x["task_id"] == gate.CASE)
        bad = dict(row)
        bad["target"] = {"guids": ["X"*22], "class": "IfcWall"}
        bad["ground_truth_ifc"] = "FORBIDDEN_REFERENCE.ifc"
        bad["evaluation"] = {"expected_score": 100}
        with patch.object(gate, "read_tasks", return_value=[bad]):
            public, guids, src = gate.verified_public_source()
        self.assertEqual(public, self.public)
        self.assertEqual(guids, self.guids)
        self.assertEqual(src, self.source)

    def test_independent_i0_does_not_overwrite_original_or_existing_output(self):
        with TemporaryDirectory(prefix="g1-native-input-only-") as td:
            already = Path(td) / "already.ifc"
            already.write_bytes(b"cannot replace")
            with self.assertRaises(IndependentDoorDeleteBlocked):
                native_door_opening_delete(
                    self.source, already, self.guids["door"], self.guids["opening"])
            self.assertEqual(already.read_bytes(), b"cannot replace")
            with self.assertRaises(IndependentDoorDeleteBlocked):
                native_door_opening_delete(
                    self.source, self.source, self.guids["door"], self.guids["opening"])
        self.assertEqual(gate._sha(self.source), INPUT_SHA)

    def test_i0_extra_unrelated_door_removal_rejected(self):
        with TemporaryDirectory(prefix="g1-native-extra-remove-") as td:
            out = Path(td) / "wrong.ifc"
            m = ifcopenshell.open(str(self.output))
            other = next(x for x in m.by_type("IfcDoor")
                         if x.GlobalId != self.guids["door"])
            ifcopenshell.api.root.remove_product(m, product=other)
            m.write(str(out))
            with self.assertRaises(PublicDoorDeleteBlocked):
                check_native_i0_result(self.source, out, self.public["instruction"])

    def test_i0_unrelated_host_or_product_changes_rejected(self):
        with TemporaryDirectory(prefix="g1-native-collateral-") as td:
            out = Path(td) / "wrong.ifc"
            m = ifcopenshell.open(str(self.output))
            wall = next(w for w in m.by_type("IfcWall") if w.GlobalId != self.guids["wall"])
            point = wall.ObjectPlacement.RelativePlacement.Location
            coords = tuple(float(x) for x in point.Coordinates)
            point.Coordinates = (coords[0] + 0.5, coords[1], coords[2])
            m.write(str(out))
            with self.assertRaises(PublicDoorDeleteBlocked):
                check_native_i0_result(self.source, out, self.public["instruction"])

    def test_i0_ifc_malformed_and_missing_rejected(self):
        with TemporaryDirectory(prefix="g1-invalid-native-delete-") as td:
            bad = Path(td) / "not-ifc.ifc"
            bad.write_bytes(b"not ifc")
            with self.assertRaises(PublicDoorDeleteBlocked):
                check_native_i0_result(self.source, bad, self.public["instruction"])
            with self.assertRaises(PublicDoorDeleteBlocked):
                check_native_i0_result(
                    self.source, Path(td) / "missing.ifc",
                    self.public["instruction"])

    def test_i0_output_physically_closes_original_host_opening(self):
        m = ifcopenshell.open(str(self.output))
        src = ifcopenshell.open(str(self.source))
        self.assertEqual(len(src.by_type("IfcDoor")) - len(m.by_type("IfcDoor")), 1)
        self.assertEqual(len(src.by_type("IfcOpeningElement")) -
                         len(m.by_type("IfcOpeningElement")), 1)
        self.assertEqual(len(src.by_type("IfcSpace")), len(m.by_type("IfcSpace")))
        self.assertEqual(len(src.by_type("IfcRelSpaceBoundary")) -
                         len(m.by_type("IfcRelSpaceBoundary")), 1)


if __name__ == "__main__":
    unittest.main()
