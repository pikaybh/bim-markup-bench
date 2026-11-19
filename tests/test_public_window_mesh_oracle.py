"""G1 #16 real IFC window world-mesh postconditions, no benchmark GT read."""
from __future__ import annotations

from hashlib import sha256
import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell

from tests.oracles.python import public_window_mesh_oracle as physical
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference
from tools.verify_prompt_grounded_window_pair import (
    verified_public_task_and_source, parse_public_window_move,
)
from tools.verify_public_window_mesh_oracle import (
    verify_source_only_window_physical_oracle,
)


class PublicWindowMeshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.published, cls.source, cls.source_sha = verified_public_task_and_source()
        cls.instruction = cls.published["instruction"]
        cls.movement = parse_public_window_move(cls.instruction)
        cls.temp = TemporaryDirectory(prefix="g1-own-world-mesh-tests-")
        cls.candidate = Path(cls.temp.name) / "imperative.ifc"
        manual_ifc_reference(
            cls.source, cls.candidate, "MOVE_OPENING",
            target_guid=cls.movement.opening_guid, delta_x=1.0,
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_actual_window_opening_host_and_other_25_native_world_meshes(self):
        record = physical.audit_window_public_mesh(
            self.source, self.candidate, self.instruction)
        self.assertEqual(record["status"],
                         "PASS_STRICT_PUBLIC_SOURCE_NATIVE_MESH_POSTCONDITIONS")
        self.assertEqual(record["represented_products_checked"], 28)
        self.assertEqual(record["unaffected_product_world_meshes_preserved"], 25)
        self.assertTrue(record["host_void_rim_replaced_by_translated_rim"])
        self.assertTrue(record["window_and_opening_exact_world_mesh_shift"])
        self.assertEqual(record["original_ifc_sha256"], self.source_sha)
        self.assertFalse(record["complete_official_task_oracle_proven"])
        self.assertEqual(record["official_tasks_scored"], 0)
        self.assertEqual(record["llm_calls"], 0)

    def test_unrecognized_public_task_or_altered_axis_is_blocked(self):
        for wrong in (
            self.instruction + " And change the wall height.",
            self.instruction.replace("positive y direction", "positive x direction"),
            self.instruction.replace("by 1m", "by 2m"),
            self.instruction.replace(self.movement.window_guid, "A" * 22),
        ):
            with self.subTest(change=wrong[:20]), self.assertRaises(
                physical.PublicWindowMeshBlocked
            ):
                physical.audit_window_public_mesh(
                    self.source, self.candidate, wrong)

    def test_incorrect_but_native_ifc_edit_world_translation_fails(self):
        with TemporaryDirectory(prefix="g1-incorrect-window-move-") as td:
            bad = Path(td) / "wrong.ifc"
            manual_ifc_reference(
                self.source, bad, "MOVE_OPENING",
                target_guid=self.movement.opening_guid, delta_x=0.5,
            )
            with self.assertRaisesRegex(
                physical.PublicWindowMeshBlocked, "world mesh displacement"
            ):
                physical.audit_window_public_mesh(self.source, bad, self.instruction)

    def test_unrelated_window_geometry_change_denied(self):
        with TemporaryDirectory(prefix="g1-unrelated-window-change-") as td:
            bad = Path(td) / "wrong.ifc"
            m = ifcopenshell.open(str(self.candidate))
            unrelated = next(w for w in m.by_type("IfcWindow")
                             if w.GlobalId != self.movement.window_guid)
            point = unrelated.ObjectPlacement.RelativePlacement.Location
            coords = list(point.Coordinates)
            coords[0] += 0.2
            point.Coordinates = coords
            m.write(str(bad))
            with self.assertRaisesRegex(
                physical.PublicWindowMeshBlocked, "STEP entities modified"
            ):
                physical.audit_window_public_mesh(self.source, bad, self.instruction)

    def test_dropped_void_link_denied(self):
        with TemporaryDirectory(prefix="g1-host-link-missing-") as td:
            bad = Path(td) / "wrong.ifc"
            m = ifcopenshell.open(str(self.candidate))
            opening = m.by_guid(self.movement.opening_guid)
            rel = list(opening.VoidsElements)[0]
            m.remove(rel)
            m.write(str(bad))
            with self.assertRaisesRegex(
                physical.PublicWindowMeshBlocked, "graph invalid"
            ):
                physical.audit_window_public_mesh(self.source, bad, self.instruction)

    def test_host_void_must_be_regenerated_even_if_link_and_window_look_right(self):
        # Fault injection in geometry observation, after native graph & row
        # verification: simulated broken mesher retains the old wall hole.
        real = physical._shapes
        calls = []
        def stale_host(model):
            shapes = real(model)
            calls.append(shapes)
            if len(calls) == 2:
                old = calls[0]
                window, opening = physical._public_guids(self.instruction)
                host = physical._host_guid(
                    ifcopenshell.open(str(self.source)), window, opening)
                shapes[host] = old[host]
            return shapes
        with patch.object(physical, "_shapes", side_effect=stale_host):
            with self.assertRaisesRegex(
                physical.PublicWindowMeshBlocked, "Host wall void"
            ):
                physical.audit_window_public_mesh(
                    self.source, self.candidate, self.instruction)

    def test_unchanged_other_object_mesh_is_not_assumed(self):
        real = physical._shapes
        calls = []
        def shifted_unrelated(model):
            shapes = real(model)
            calls.append(shapes)
            if len(calls) == 2:
                window, opening = physical._public_guids(self.instruction)
                host = physical._host_guid(
                    ifcopenshell.open(str(self.source)), window, opening)
                unrelated = next(g for g in shapes if g not in {window, opening, host})
                pts, tris, volume = shapes[unrelated]
                shapes[unrelated] = pts + [0., 0.2, 0.], tris, volume
            return shapes
        with patch.object(physical, "_shapes", side_effect=shifted_unrelated):
            with self.assertRaisesRegex(
                physical.PublicWindowMeshBlocked, "Unrelated IFC product"
            ):
                physical.audit_window_public_mesh(
                    self.source, self.candidate, self.instruction)

    def test_bad_ifc_and_missing_file_fail_without_partial_evidence(self):
        with TemporaryDirectory(prefix="g1-malformed-window-ifc-") as td:
            malformed = Path(td) / "broken.ifc"
            malformed.write_bytes(b"THIS IS NOT IFC")
            with self.assertRaises(physical.PublicWindowMeshBlocked):
                physical.audit_window_public_mesh(
                    self.source, malformed, self.instruction)
            with self.assertRaises(physical.PublicWindowMeshBlocked):
                physical.audit_window_public_mesh(
                    self.source, Path(td) / "missing.ifc", self.instruction)

    def test_independent_checker_does_not_import_authoring_or_official_scorer(self):
        source = inspect.getsource(physical)
        for phrase in (
            "from tools.verify_prompt_grounded_window_pair",
            "from src.direct_markup",
            "from src.imperative_control",
            "from src.evaluation.bim_edit_scorer",
            "ground_truth_ifc",
        ):
            self.assertNotIn(phrase, source)

    def test_both_real_d0_i0_source_only_postconditions_and_report_redaction(self):
        proof = verify_source_only_window_physical_oracle()
        self.assertEqual(proof["frozen_task_id"], self.published["task_id"])
        self.assertEqual(proof["represented_products_checked_per_arm"], 28)
        self.assertEqual(proof["unaffected_world_meshes_preserved_per_arm"], 25)
        self.assertTrue(proof["host_wall_regenerated_void_rim_both_arms"])
        self.assertFalse(proof["full_official_task_oracle_proven"])
        self.assertEqual(proof["official_tasks_scored"], 0)
        self.assertEqual(proof["LLM_calls"], 0)
        encoded = json.dumps(proof)
        self.assertNotIn(self.instruction, encoded)
        for forbidden in ("ground_truth_ifc", '"target"', '"evaluation"', '"prompt"'):
            self.assertNotIn(forbidden, encoded)
        self.assertNotIn(self.movement.window_guid, encoded)
        self.assertNotIn(self.movement.opening_guid, encoded)
        self.assertEqual(sha256(self.source.read_bytes()).hexdigest(), self.source_sha)


if __name__ == "__main__":
    unittest.main()
