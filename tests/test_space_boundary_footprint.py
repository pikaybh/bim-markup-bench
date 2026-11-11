"""G1 #15: 2D Wall-loop completeness of IfcRelSpaceBoundary after Door delete.

The fixed public IFC has four full-height vertical Wall boundary surfaces
per IfcSpace plus Door/Window patches on existing walls. Verify planar
closed loops (not hypothetical 3D watertightness) in BOTH D0/I0 results.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell
from lxml import etree

from src.runtime.compiler import CompilerError, compile_declarative_xml
from src.runtime.ifc_mutations import UnsupportedIFCMutation
from src.runtime.ifc_projection import project_ifc
from src.runtime.space_boundary_footprint import (
    survey_space_wall_footprints, verify_door_delete_boundary_footprints)
from tests.oracles.python.independent_public_door_delete import native_door_opening_delete
from tools.verify_public_door_delete_gate import verified_public_source


class PublicDoorSpaceBoundaryFootprintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public, cls.guids, cls.source = verified_public_source()
        cls.source_sha = sha256(cls.source.read_bytes()).hexdigest()
        cls.scratch = TemporaryDirectory(prefix="g1-space-boundary-footprints-")
        cls.i0 = Path(cls.scratch.name) / "i0.ifc"
        cls.d0 = Path(cls.scratch.name) / "d0.ifc"
        native_door_opening_delete(cls.source, cls.i0,
                                   cls.guids["door"], cls.guids["opening"])
        root = etree.fromstring(project_ifc(cls.source).xml)
        for element in tuple(root.iter()):
            if element.get("ifcGuid") in (cls.guids["door"], cls.guids["opening"]):
                element.getparent().remove(element)
        cls.xml = etree.tostring(root, encoding="utf8", xml_declaration=True)
        cls.report = compile_declarative_xml(cls.source, cls.xml, cls.d0)
        cls.old = ifcopenshell.open(str(cls.source))
        cls.removed_boundary = cls.old.by_guid(cls.guids["door"]).ProvidesBoundaries[0].GlobalId

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def _check(self, path: Path):
        return verify_door_delete_boundary_footprints(
            self.old, ifcopenshell.open(str(path)), self.removed_boundary)

    def _bad_result(self, mutation, expected_message=None):
        with TemporaryDirectory(prefix="g1-boundary-tamper-") as folder:
            dst=Path(folder)/"tampered.ifc"
            model=ifcopenshell.open(str(self.i0))
            mutation(model)
            model.write(str(dst))
            with self.assertRaisesRegex(
                UnsupportedIFCMutation, expected_message or "."):
                self._check(dst)

    @staticmethod
    def _wall_relation(model, room_name="132"):
        space=next(x for x in model.by_type("IfcSpace") if x.Name==room_name)
        return next(x for x in space.BoundedBy if x.RelatedBuildingElement.is_a("IfcWall"))

    def test_exact_original_source_wall_boundary_footprints_are_closed(self):
        observed=survey_space_wall_footprints(self.old)
        byname={self.old.by_guid(k).Name:v for k,v in observed.items()}
        self.assertEqual(set(byname),{"131","132"})
        self.assertEqual(len(byname["131"].wall_boundary_guids),4)
        self.assertEqual(len(byname["132"].wall_boundary_guids),4)
        self.assertEqual(len(byname["131"].other_boundary_guids),2)
        self.assertEqual(len(byname["132"].other_boundary_guids),2)
        self.assertEqual(byname["131"].enclosed_plan_area_m2,83.0)
        self.assertEqual(byname["131"].wall_perimeter_m,36.6)
        self.assertEqual(byname["132"].enclosed_plan_area_m2,65.0)
        self.assertEqual(byname["132"].wall_perimeter_m,33.0)
        self.assertEqual(byname["132"].wall_boundary_depth_m,3.048)

    def test_both_d0_i0_preserve_two_closed_planar_wall_footprints(self):
        before=sha256(self.source.read_bytes()).hexdigest()
        d=self._check(self.d0)
        i=self._check(self.i0)
        self.assertEqual(d,i)
        self.assertEqual(d["wall_perimeter_count_closed"],2)
        self.assertTrue(d["removed_door_boundary_overlaid_wall_ring"])
        self.assertFalse(d["full_3d_space_boundary_shell_closure_proven"])
        self.assertFalse(d["floor_ceiling_boundary_reconstruction_performed"])
        self.assertFalse(d["author_provided_bim_edit_scorer_executed"])
        byarea={x["wall_footprint_area_m2"]:x for x in d["spaces"]}
        self.assertEqual(byarea[65.0]["source_and_result_wall_segment_counts"],[4,4])
        self.assertEqual(byarea[65.0]["source_and_result_nonwall_boundary_counts"],[2,1])
        self.assertEqual(byarea[83.0]["source_and_result_wall_segment_counts"],[4,4])
        self.assertEqual(byarea[83.0]["source_and_result_nonwall_boundary_counts"],[2,2])
        self.assertEqual(sha256(self.source.read_bytes()).hexdigest(),before)

    def test_original_door_boundary_is_an_overlay_not_wall_perimeter_edge(self):
        records=survey_space_wall_footprints(self.old)
        matching=[r for r in records.values()
                  if self.removed_boundary in r.other_boundary_guids]
        self.assertEqual(len(matching),1)
        self.assertEqual(len(matching[0].wall_boundary_guids),4)

    def test_deleting_unrelated_wall_boundary_is_rejected(self):
        def mutate(model):
            relation=self._wall_relation(model)
            model.remove(relation)
        self._bad_result(mutate, "open/branched")

    def test_retained_wall_boundary_endpoint_moving_breaks_ring(self):
        # This changes a nonroot IfcPolyline point, which root-ID or
        # IfcProduct mesh checks alone would NOT catch.
        def mutate(model):
            rel=self._wall_relation(model)
            point=rel.ConnectionGeometry.SurfaceOnRelatingElement.SweptCurve.Curve.Points[0]
            coordinates=list(point.Coordinates)
            coordinates[0]+=0.3
            point.Coordinates=coordinates
        self._bad_result(mutate,"open/branched")

    def test_wall_boundary_height_change_is_rejected(self):
        def mutate(model):
            rel=self._wall_relation(model)
            surface=rel.ConnectionGeometry.SurfaceOnRelatingElement
            surface.Depth=float(surface.Depth)+0.2
        self._bad_result(mutate,"unequal-height|surfaces")

    def test_retained_door_boundary_detached_from_wall_ring_is_rejected(self):
        def mutate(model):
            room=next(x for x in model.by_type("IfcSpace") if x.Name=="132")
            rel=next(x for x in room.BoundedBy
                     if x.RelatedBuildingElement.is_a("IfcDoor"))
            point=rel.ConnectionGeometry.SurfaceOnRelatingElement.SweptCurve.Curve.Points[0]
            coords=list(point.Coordinates)
            coords[1]+=0.2
            point.Coordinates=coords
        self._bad_result(mutate,"no longer overlays")

    def test_room_boundary_owner_moved_to_wrong_space_is_rejected(self):
        def mutate(model):
            rel=self._wall_relation(model)
            other=next(x for x in model.by_type("IfcSpace") if x.Name=="131")
            rel.RelatingSpace=other
        self._bad_result(mutate, "open/branched|Disconnected|perimeter|fewer")

    def test_restoring_removed_door_boundary_by_new_identity_is_rejected(self):
        def mutate(model):
            source_rel=self.old.by_guid(self.removed_boundary)
            # Use a cloned output-space endpoint but a new replacement
            # boundary root. The source surface is left untouched.
            original_space=source_rel.RelatingSpace.GlobalId
            output_space=model.by_guid(original_space)
            other_door=next(x for x in model.by_type("IfcDoor")
                            if x.GlobalId!=self.guids["door"])
            model.create_entity(
                "IfcRelSpaceBoundary",
                GlobalId=ifcopenshell.guid.new(),Name="1stLevel",
                RelatingSpace=output_space,RelatedBuildingElement=other_door,
                ConnectionGeometry=other_door.ProvidesBoundaries[0].ConnectionGeometry,
                PhysicalOrVirtualBoundary="PHYSICAL",
                InternalOrExternalBoundary="EXTERNAL")
        self._bad_result(mutate, "Unapproved|native|no longer overlays")

    def test_replacing_untouched_wall_surface_with_nonvertical_is_rejected(self):
        def mutate(model):
            rel=self._wall_relation(model)
            surface=rel.ConnectionGeometry.SurfaceOnRelatingElement
            direction=surface.ExtrudedDirection
            direction.DirectionRatios=(1.0,0.0,0.0)
        self._bad_result(mutate,"not vertical")

    def test_validator_failure_rolls_back_compiler_transaction(self):
        with TemporaryDirectory(prefix="g1-space-rollback-") as td:
            dest=Path(td)/"result.ifc"
            with patch("src.runtime.hosted_door_delete.verify_door_delete_boundary_footprints",
                       side_effect=UnsupportedIFCMutation("Injected open ring")):
                with self.assertRaises(CompilerError):
                    compile_declarative_xml(self.source,self.xml,dest)
            self.assertFalse(dest.exists())
            self.assertEqual(tuple(Path(td).glob(".bim-compiler-*")),())
            self.assertEqual(sha256(self.source.read_bytes()).hexdigest(),
                             self.source_sha)


if __name__=="__main__":
    unittest.main()
