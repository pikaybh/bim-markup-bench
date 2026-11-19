"""G1 #16 frozen public Wall source-only IFC semantics and negative fixtures."""
from __future__ import annotations

from hashlib import sha256
import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell

from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference
from tests.oracles.python import public_wall_space_semantics as checker
from tools import verify_prompt_grounded_spatial_wall as gate
from tools.verify_public_wall_spatial_postconditions import (
    verify_public_wall_spatial_postconditions,
)


class PublicWallNativeSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public, cls.source, cls.source_sha = gate.verified_public_input()
        cls.spec = gate.parse_public_wall_spec(cls.public["instruction"])
        _, _, cls.native_geometry = gate._actual_world_geometry(
            cls.public, cls.source, cls.spec)
        cls.new_guid = gate._created_guid(cls.source_sha)
        cls.scratch = TemporaryDirectory(prefix="g1-private-wall-physical-")
        folder = Path(cls.scratch.name)
        baseline = folder / "I0-base.ifc"
        cls.original_candidate = folder / "I0-joined.ifc"
        g = cls.native_geometry
        manual_ifc_reference(
            cls.source, baseline, "CREATE_WALL",
            new_guid=cls.new_guid, storey_guid=g["storey_guid"],
            start=tuple(float(x) for x in g["start"]),
            end=tuple(float(x) for x in g["end"]),
            height=float(cls.spec.height_m),
            thickness=float(cls.spec.thickness_m))
        model = ifcopenshell.open(str(baseline))
        new_wall = model.by_guid(cls.new_guid)
        for host, terminal in (
            (cls.spec.first_wall, "ATSTART"),
            (cls.spec.second_wall, "ATEND"),
        ):
            model.createIfcRelConnectsPathElements(
                GlobalId=gate._join_guid(cls.source_sha, host, cls.new_guid),
                RelatingElement=model.by_guid(host),
                RelatedElement=new_wall,
                RelatingConnectionType="ATPATH",
                RelatedConnectionType=terminal,
                RelatingPriorities=(),
                RelatedPriorities=(),
            )
        model.write(str(cls.original_candidate))

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def _changed(self, mutation):
        """Mutate only a copied trusted output, then validate fail-closed."""
        with TemporaryDirectory(prefix="g1-wall-negative-") as d:
            test = Path(d) / "invalid.ifc"
            model = ifcopenshell.open(str(self.original_candidate))
            mutation(model)
            model.write(str(test))
            with self.assertRaises(checker.PublicWallSpaceBlocked):
                checker.audit_public_wall_space_semantics(
                    self.source, test, self.public["instruction"])

    def test_real_source_only_physical_cross_section_is_not_space_partition(self):
        evidence = checker.audit_public_wall_space_semantics(
            self.source, self.original_candidate, self.public["instruction"])
        self.assertEqual(evidence["status"],
                         "PASS_SOURCE_ONLY_PHYSICAL_WALL_JOINS_ROOM_SEMANTIC_SPLIT_UNPROVEN")
        self.assertEqual(evidence["native_source_products_preserved"], 10)
        self.assertEqual(evidence["new_native_wall_count"], 1)
        self.assertEqual(evidence["new_native_path_joins"], 2)
        self.assertTrue(evidence["new_wall_storey_containment_correct"])
        self.assertTrue(evidence["source_room_and_wall_full_cross_section"])
        self.assertEqual(evidence["source_room_wall_overlap_volume_m3"], 2.1805)
        self.assertEqual(evidence["source_ifc_space_count_before_and_after"], [2, 2])
        self.assertEqual(evidence["source_ifc_space_boundary_count_before_and_after"], [13, 13])
        self.assertFalse(evidence["new_ifc_space_created"])
        self.assertFalse(evidence["geometry_implies_new_ifc_space_semantics"])
        self.assertFalse(evidence["complete_official_task_oracle_proven"])
        self.assertEqual(evidence["official_tasks_scored"], 0)
        self.assertEqual(evidence["llm_calls"], 0)

    def test_real_d0_i0_compilation_both_independent_native_postconditions(self):
        evidence = verify_public_wall_spatial_postconditions()
        self.assertEqual(evidence["frozen_task_id"], gate.CASE)
        self.assertEqual(evidence["status"],
                         "PASS_BOTH_NATIVE_WALL_JOINS_ROOM_PARTITION_NOT_PROVEN")
        self.assertEqual(evidence["native_source_products_preserved_per_arm"], 10)
        self.assertEqual(evidence["new_native_t_path_joins_per_arm"], 2)
        self.assertEqual(evidence["ifc_spaces_before_and_after_per_arm"], [2, 2])
        self.assertEqual(evidence["ifc_space_boundaries_before_and_after_per_arm"], [13, 13])
        self.assertTrue(evidence["source_only_wall_full_room_cross_section_per_arm"])
        self.assertEqual(evidence["wall_overlap_with_unchanged_room_m3"], 2.1805)
        self.assertFalse(evidence["room_partition_and_new_room_semantics_proven"])
        self.assertEqual(evidence["official_tasks_scored"], 0)
        self.assertEqual(evidence["llm_calls"], 0)
        self.assertNotEqual(evidence["d0_ifc_sha256"], evidence["i0_ifc_sha256"])
        self.assertEqual(sha256(self.source.read_bytes()).hexdigest(), self.source_sha)
        # The checker exposes no model-visible reference geometry or private GT.
        serialized = json.dumps(evidence)
        for forbidden in (
            self.public["instruction"], self.spec.first_wall,
            self.spec.second_wall, self.spec.room, self.new_guid,
            "ground_truth_ifc", '"target"', '"evaluation"', '"prompt"',
        ):
            self.assertNotIn(forbidden, serialized)

    def test_bad_prompt_or_wrong_public_source_rejected(self):
        for instruction in (
            self.public["instruction"] + " Also split the Room.",
            self.public["instruction"].replace("0.175m", "0.200m"),
            self.public["instruction"].replace("+y direction", "+x direction"),
        ):
            with self.assertRaises(checker.PublicWallSpaceBlocked):
                checker.audit_public_wall_space_semantics(
                    self.source, self.original_candidate, instruction)
        with TemporaryDirectory(prefix="g1-wall-spoof-source-") as td:
            spoof = Path(td) / "source.ifc"
            spoof.write_bytes(self.source.read_bytes() + b" ")
            with self.assertRaisesRegex(
                checker.PublicWallSpaceBlocked, "source IFC hash changed"):
                checker.audit_public_wall_space_semantics(
                    spoof, self.original_candidate, self.public["instruction"])

    def test_wrong_new_wall_world_position_rejected(self):
        def corrupt(model):
            point = model.by_guid(self.new_guid).ObjectPlacement.RelativePlacement.Location
            xyz = list(point.Coordinates)
            xyz[1] += 0.2
            point.Coordinates = xyz
        self._changed(corrupt)

    def test_missing_t_path_connection_rejected(self):
        def corrupt(model):
            relation = next(
                r for r in model.by_type("IfcRelConnectsPathElements")
                if r.RelatedElement.GlobalId == self.new_guid)
            model.remove(relation)
        self._changed(corrupt)

    def test_new_wall_attached_to_wrong_storey_rejected(self):
        # This public source contains only one relevant storey; dropping
        # containment is an unambiguous native relationship violation.
        def remove_containment(model):
            wall = model.by_guid(self.new_guid)
            rel = wall.ContainedInStructure[0]
            if len(rel.RelatedElements) == 1:
                model.remove(rel)
            else:
                rel.RelatedElements = tuple(
                    x for x in rel.RelatedElements if x.GlobalId != self.new_guid)
        self._changed(remove_containment)

    def test_wrong_existing_wall_mesh_rejected(self):
        def corrupt(model):
            wall = model.by_guid(self.spec.first_wall)
            point = wall.ObjectPlacement.RelativePlacement.Location
            xyz = list(point.Coordinates)
            xyz[1] += 0.25
            point.Coordinates = xyz
        self._changed(corrupt)

    def test_unrequested_new_space_rejected(self):
        def corrupt(model):
            model.createIfcSpace(GlobalId=ifcopenshell.guid.new(),
                                 Name="UNREQUESTED-SPACE")
        self._changed(corrupt)

    def test_original_space_boundary_relation_deleted_rejected(self):
        def corrupt(model):
            relation = model.by_type("IfcRelSpaceBoundary")[0]
            model.remove(relation)
        self._changed(corrupt)

    def test_existing_room_geometry_mutated_rejected(self):
        def corrupt(model):
            room = model.by_guid(self.spec.room)
            solid = room.Representation.Representations[0].Items[0]
            solid.Depth = float(solid.Depth) * 0.9
        self._changed(corrupt)

    def test_malformed_ifc_missing_ifc_and_no_private_scorer_import(self):
        with TemporaryDirectory(prefix="g1-wall-invalid-ifc-") as td:
            malformed = Path(td) / "bad.ifc"
            malformed.write_bytes(b"NOT AN IFC")
            for path in (malformed, Path(td) / "missing.ifc"):
                with self.assertRaises(checker.PublicWallSpaceBlocked):
                    checker.audit_public_wall_space_semantics(
                        self.source, path, self.public["instruction"])
        source = inspect.getsource(checker)
        for forbidden in (
            "from tools.verify_prompt_grounded_spatial_wall",
            "from src.direct_markup",
            "from src.imperative_control",
            "from src.evaluation.bim_edit_scorer",
            "ground_truth_ifc",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
