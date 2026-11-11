"""G1 #15: original IFC4X3 3D product mesh vs inherited boundary relation gap."""
from __future__ import annotations

from hashlib import sha256
import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell
import ifcopenshell.geom
from lxml import etree

from src.runtime.compiler import compile_declarative_xml
from tests.oracles.python.independent_public_door_delete import native_door_opening_delete
from tests.oracles.python import public_space_shell_gap as audit
from tools.verify_public_door_3d_shell_gap import run_source_inherited_3d_shell_gap_audit
from tools.verify_public_door_delete_gate import verified_public_source


class SourceInherited3DSpaceBoundaryGapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public, cls.guids, cls.source=verified_public_source()
        cls.digest=sha256(cls.source.read_bytes()).hexdigest()
        cls.temp=TemporaryDirectory(prefix="g1-source3d-rel-shell-")
        folder=Path(cls.temp.name)
        cls.i0=folder/"I0.ifc"
        cls.d0=folder/"D0.ifc"
        native_door_opening_delete(
            cls.source,cls.i0,cls.guids["door"],cls.guids["opening"])
        from src.runtime.ifc_projection import project_ifc
        root=etree.fromstring(project_ifc(cls.source).xml)
        for node in tuple(root.iter()):
            if node.get("ifcGuid") in (cls.guids["door"],cls.guids["opening"]):
                node.getparent().remove(node)
        compile_declarative_xml(
            cls.source,etree.tostring(root,encoding="utf8",xml_declaration=True),
            cls.d0)
        cls.native_source=ifcopenshell.open(str(cls.source))
        cls.boundary=cls.native_source.by_guid(
            cls.guids["door"]).ProvidesBoundaries[0].GlobalId

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def _audit(self, path:Path):
        return audit.verify_source_inherited_space_boundary_gap(
            self.source,path,self.boundary)

    def test_original_room_product_meshes_are_closed_rectangular_solids(self):
        evidence=self._audit(self.i0)
        self.assertEqual(evidence["space_count"],2)
        self.assertTrue(evidence["original_and_output_general_boundary_concrete_classes_only"])
        self.assertEqual(evidence["actual_IfcRelSpaceBoundary1stLevel_subclass_records"],0)
        self.assertEqual(evidence["original_generic_firstlevel_named_boundary_count"],12)
        self.assertEqual(evidence["output_generic_firstlevel_named_boundary_count"],11)
        self.assertTrue(evidence["native_IfcSpace_product_meshes_closed_and_preserved"])
        byarea={r["plan_area_m2"]:r for r in evidence["per_room"]}
        self.assertEqual(set(byarea),{65.0,83.0})
        self.assertEqual(byarea[65.0]["signed_mesh_volume_m3"],198.12)
        self.assertEqual(byarea[83.0]["signed_mesh_volume_m3"],252.984)
        for area,record in byarea.items():
            self.assertEqual(record["native_mesh_vertices"],8)
            self.assertEqual(record["native_mesh_triangles"],12)
            self.assertEqual(record["native_mesh_edges"],18)
            self.assertTrue(record["original_and_result_mesh_closed_oriented"])
            self.assertEqual(record["product_floor_mesh_triangles"],2)
            self.assertEqual(record["product_ceiling_mesh_triangles"],2)
            self.assertEqual(record["product_floor_mesh_area_m2"],area)
            self.assertEqual(record["product_ceiling_mesh_area_m2"],area)
            self.assertEqual(record["unrepaired_horizontal_coverage_gap_m2"],2*area)

    def test_d0_and_i0_source_3d_mesh_and_missing_boundary_caps_agree(self):
        d=self._audit(self.d0)
        i=self._audit(self.i0)
        comparable=set(d)-{"candidate_sha256"}
        self.assertTrue(all(d[k]==i[k] for k in comparable))
        self.assertEqual(d["planar_wall_perimeter_count_closed"],2)
        self.assertTrue(d["native_IfcRelSpaceBoundary_floor_ceiling_surfaces_absent_in_source"])
        self.assertTrue(d["native_IfcRelSpaceBoundary_floor_ceiling_surfaces_absent_in_output"])
        self.assertTrue(d["baseline_relative_unmodified_3d_relation_gap"])
        self.assertFalse(d["full_3d_spatial_boundary_shell_proven"])
        self.assertEqual(d["official_tasks_scored"],0)
        self.assertEqual(d["LLM_calls"],0)
        self.assertEqual(sha256(self.source.read_bytes()).hexdigest(),self.digest)

    def test_only_one_original_door_patch_missing_and_no_horizontal_surfaces(self):
        evidence=self._audit(self.d0)
        byarea={r["plan_area_m2"]:r for r in evidence["per_room"]}
        self.assertEqual(byarea[65.0]["original_firstlevel_relation_surfaces"],[6,0])
        self.assertEqual(byarea[65.0]["result_firstlevel_relation_surfaces"],[5,0])
        self.assertEqual(byarea[83.0]["original_firstlevel_relation_surfaces"],[6,0])
        self.assertEqual(byarea[83.0]["result_firstlevel_relation_surfaces"],[6,0])

    def test_end_to_end_sanitized_report_hard_blocks_benchmark_claims(self):
        result=run_source_inherited_3d_shell_gap_audit()
        self.assertEqual(result["version"],
                         "G1_PUBLIC_DOOR_NATIVE_SOURCE_3D_SHELL_GAP_V0.4")
        self.assertTrue(result["d0_i0_per_room_3d_shape_relations_gap_match"])
        self.assertFalse(result["normative_closed_shell_condition_satisfied_by_relationships"])
        self.assertFalse(result["G1_G2_G3_release_allowed"])
        self.assertEqual(result["space_boundaries_newly_generated"],0)
        self.assertEqual(result["official_tasks_scored"],0)
        self.assertEqual(result["LLM_calls"],0)
        self.assertTrue(result["no_retroactive_frozen_support_reclassification"])
        text=json.dumps(result,sort_keys=True)
        for forbidden in (
            self.public["instruction"],*self.guids.values(),self.boundary,
            "ground_truth_ifc",'"target"','"evaluation"','"prompt"',"API_KEY",
        ):
            self.assertNotIn(forbidden,text)

    def _tamper(self, mutation):
        with TemporaryDirectory(prefix="g1-shell-negative-") as td:
            output=Path(td)/"tampered.ifc"
            m=ifcopenshell.open(str(self.i0))
            mutation(m)
            m.write(str(output))
            with self.assertRaises((audit.SourceSpaceShellEvidenceBlocked,
                                    ValueError)):
                self._audit(output)

    def test_modified_existing_room_height_fails_mesh_preservation(self):
        def mutate(model):
            room=next(x for x in model.by_type("IfcSpace") if x.Name=="132")
            solid=room.Representation.Representations[0].Items[0]
            solid.Depth=float(solid.Depth)*0.75
        self._tamper(mutate)

    def test_removed_existing_room_representation_fails(self):
        def mutate(model):
            room=next(x for x in model.by_type("IfcSpace") if x.Name=="132")
            room.Representation=None
        self._tamper(mutate)

    def test_missing_existing_wall_boundary_fails(self):
        def mutate(model):
            room=next(x for x in model.by_type("IfcSpace") if x.Name=="132")
            rel=next(x for x in room.BoundedBy if x.RelatedBuildingElement.is_a("IfcWall"))
            model.remove(rel)
        self._tamper(mutate)

    def test_nonvertical_relation_surface_fails_instead_of_proving_horizontal_fix(self):
        def mutate(model):
            room=next(x for x in model.by_type("IfcSpace") if x.Name=="132")
            rel=next(x for x in room.BoundedBy if x.RelatedBuildingElement.is_a("IfcWall"))
            surface=rel.ConnectionGeometry.SurfaceOnRelatingElement
            surface.ExtrudedDirection.DirectionRatios=(1.0,0.0,0.0)
        self._tamper(mutate)

    def test_fabricated_floor_relation_does_not_complete_original_source(self):
        def mutate(model):
            room=next(x for x in model.by_type("IfcSpace") if x.Name=="132")
            boundary=next(x for x in room.BoundedBy if x.RelatedBuildingElement.is_a("IfcWall"))
            clone=model.create_entity(
                "IfcRelSpaceBoundary",GlobalId=ifcopenshell.guid.new(),
                Name="1stLevel",RelatingSpace=room,
                RelatedBuildingElement=boundary.RelatedBuildingElement,
                ConnectionGeometry=boundary.ConnectionGeometry,
                PhysicalOrVirtualBoundary="PHYSICAL",
                InternalOrExternalBoundary="EXTERNAL")
        self._tamper(mutate)

    def test_broken_source_digest_is_denied(self):
        with TemporaryDirectory(prefix="g1-shell-spoof-source-") as td:
            wrong=Path(td)/"source.ifc"
            wrong.write_bytes(self.source.read_bytes()+b" ")
            with self.assertRaisesRegex(audit.SourceSpaceShellEvidenceBlocked,
                                        "original IFC hash changed"):
                audit.verify_source_inherited_space_boundary_gap(
                    wrong,self.i0,self.boundary)

    def test_missing_or_invalid_result_does_not_emit_success(self):
        with TemporaryDirectory(prefix="g1-shell-invalid-") as td:
            for path in (Path(td)/"missing.ifc",Path(td)/"bad.ifc"):
                if path.name=="bad.ifc":
                    path.write_bytes(b"NOT IFC")
                with self.subTest(path=path.name),self.assertRaises(
                    (audit.SourceSpaceShellEvidenceBlocked,FileNotFoundError)):
                    self._audit(path)

    def test_no_authoring_engine_or_official_scorer_inside_trusted_witness(self):
        code=inspect.getsource(audit)
        for forbidden in (
            "from src.direct_markup",
            "from src.imperative_control",
            "from src.evaluation.bim_edit_scorer",
            "ground_truth_ifc",
        ):
            self.assertNotIn(forbidden,code)


if __name__=="__main__":
    unittest.main()
