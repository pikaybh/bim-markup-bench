"""Synthetic-only blind IFC scorer: positive and independent negative fixtures."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.api.pset
import jsonschema

from src.evaluation.bim_edit_scorer import (
    GraderTask,score_ifc_result,PROVENANCE
)
from src.evaluation.geometry_metrics import (
    GeometrySettings,surface_sample,compare_surface_geometry,
    UnsupportedGeometry
)
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"tests/fixtures/synthetic/input.ifc"
GT_WALL=ROOT/"tests/fixtures/synthetic/expected_wall_height.ifc"
SCHEMA=json.loads((ROOT/"schemas/score_result.schema.json").read_text())
SOURCE_GUID=ifcopenshell.open(str(SRC)).by_type("IfcWall")[0].GlobalId
WINDOW_GUID=ifcopenshell.open(str(SRC)).by_type("IfcWindow")[0].GlobalId
LEVEL_GUID=ifcopenshell.open(str(SRC)).by_type("IfcBuildingStorey")[0].GlobalId

def original_hashes(*paths):
    return tuple(sha256(p.read_bytes()).hexdigest() for p in paths)

def wall_task():
    return GraderTask("OWN-WALL-UPDATE","update","IfcWall",(SOURCE_GUID,))

def wall_eval(prediction:Path,source=SRC,gt=GT_WALL):
    return score_ifc_result(source_ifc=source,
         ground_truth_ifc=gt,result_ifc=prediction,task=wall_task())

def write_modified(source:Path,destination:Path,callback):
    model=ifcopenshell.open(str(source))
    callback(model)
    model.write(str(destination))
    return destination


class GeometryAndScorerPositiveTests(unittest.TestCase):
    def test_reference_vs_itself_is_perfect_and_schema_valid(self):
        before=original_hashes(SRC,GT_WALL)
        score=wall_eval(GT_WALL)
        jsonschema.validate(score,SCHEMA)
        self.assertEqual(score["status"],"INDEPENDENT_IFC_SCORED")
        self.assertEqual(score["metric_origin"],PROVENANCE)
        self.assertFalse(score["official_bim_edit_evaluator_equivalent"])
        self.assertEqual((score["geometry"],score["semantics"],score["topology"]),
                         (1.,1.,1.))
        self.assertEqual(score["final_score"],1.)
        self.assertTrue(score["strict_pass"])
        self.assertEqual(score["failure_codes"],[])
        self.assertTrue(score["collateral_detail"]["collateral_clean"])
        self.assertEqual(before,original_hashes(SRC,GT_WALL))

    def test_repeated_grading_bitwise_deterministic_and_arm_blind(self):
        a=wall_eval(GT_WALL)
        b=wall_eval(GT_WALL)
        self.assertEqual(json.dumps(a,sort_keys=True),json.dumps(b,sort_keys=True))
        # Grader API has deliberately no arm argument: both authoring arms'
        # identical IFC file paths are indistinguishable to its implementation.
        self.assertNotIn("arm",json.dumps(a).lower())
        self.assertEqual(a["model_provider_calls"],0)

    def test_different_backend_same_native_IFC_scores_perfect(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"i0_manually_authored.ifc"
            manual_ifc_reference(
                SRC,out,"UPDATE_WALL_HEIGHT",
                target_guid=SOURCE_GUID,height=3.3
            )
            result=wall_eval(out)
            self.assertTrue(result["strict_pass"],result)
            self.assertEqual(result["geometry"],1.)
            self.assertEqual(result["topology"],1.)

    def test_create_same_geometry_different_guid_matches_without_leaking_id(self):
        with tempfile.TemporaryDirectory() as temp:
            temp=Path(temp)
            gt=temp/"create_gt.ifc"
            pred=temp/"create_pred.ifc"
            manual_ifc_reference(
                SRC,gt,"CREATE_WALL",
                new_guid="1UXHdOzirKMwnUzfD_y3ME",
                storey_guid=LEVEL_GUID)
            manual_ifc_reference(
                SRC,pred,"CREATE_WALL",
                new_guid="0atSxzNVbS9gi82DTpTUq9",
                storey_guid=LEVEL_GUID)
            task=GraderTask("OWN-WALL-CREATE","create","IfcWall",())
            value=score_ifc_result(
                source_ifc=SRC,ground_truth_ifc=gt,
                result_ifc=pred,task=task)
            self.assertTrue(value["strict_pass"],value)
            self.assertEqual(value["geometry"],1.)
            self.assertEqual(value["topology"],1.)
            self.assertEqual(value["target_matching_method"],
                             "NEAREST_NEW_WORLD_GEOMETRY")
            self.assertNotIn("0atSxzNVbS9gi82DTpTUq9",json.dumps(value))
            jsonschema.validate(value,SCHEMA)

    def test_delete_window_reference_matches_and_preserves_other_objects(self):
        with tempfile.TemporaryDirectory() as temp:
            gt=Path(temp)/"window_gt.ifc"
            manual_ifc_reference(SRC,gt,"DELETE_WINDOW",target_guid=WINDOW_GUID)
            task=GraderTask("OWN-WINDOW-DELETE","delete","IfcWindow",(WINDOW_GUID,))
            value=score_ifc_result(source_ifc=SRC,ground_truth_ifc=gt,
                                    result_ifc=gt,task=task)
            self.assertTrue(value["strict_pass"],value)
            self.assertEqual(value["geometry"],1.)
            self.assertEqual(value["semantics"],1.)
            self.assertEqual(value["topology"],1.)
            self.assertGreater(value["topology_detail"]["reference_edges_edited"],0)

    def test_surface_point_sampling_same_seed_and_mesh_exact(self):
        f=ifcopenshell.open(str(GT_WALL))
        wall=f.by_type("IfcWall")[0]
        cfg=GeometrySettings(sample_count=512,random_seed=55)
        self.assertTrue((surface_sample(wall,cfg)==surface_sample(wall,cfg)).all())
        metrics=compare_surface_geometry(wall,wall,cfg)
        self.assertEqual(metrics["score"],1.0)
        self.assertEqual(metrics["median_bidirectional_surface_distance_m"],0.0)
        self.assertEqual(metrics["world_unit"],"m")


class IndependentScorerNegativeTests(unittest.TestCase):
    def test_wrong_wall_height_is_geometry_failure(self):
        value=wall_eval(SRC)
        self.assertEqual(value["status"],"INDEPENDENT_IFC_SCORED")
        self.assertLess(value["geometry"],.98)
        self.assertTrue(value["semantics"]>=.98)
        self.assertFalse(value["strict_pass"])
        self.assertIn("TARGET_GEOMETRY_DIFFERENCE",value["failure_codes"])

    def test_translated_wall_geometry_degrades_geometric_score(self):
        with tempfile.TemporaryDirectory() as temp:
            def translate(model):
                wall=model.by_guid(SOURCE_GUID)
                point=wall.ObjectPlacement.RelativePlacement.Location
                p=tuple(float(n) for n in point.Coordinates)
                point.Coordinates=(p[0]+1.0,p[1],p[2])
            bad=write_modified(GT_WALL,Path(temp)/"shifted.ifc",translate)
            value=wall_eval(bad)
            self.assertFalse(value["strict_pass"])
            self.assertLess(value["geometry"],.98)
            self.assertGreater(value["geometry_detail"]["maximum_aabb_coordinate_difference_m"],.5)

    def test_lost_opening_relation_degrades_native_geometry_and_topology(self):
        with tempfile.TemporaryDirectory() as temp:
            def strip(model):
                rel=model.by_type("IfcRelVoidsElement")[0]
                model.remove(rel)
            bad=write_modified(GT_WALL,Path(temp)/"unhosted.ifc",strip)
            value=wall_eval(bad)
            # A real wall void is computed from IfcRelVoidsElement: removing
            # it both changes graph topology AND physically restores wall mesh.
            self.assertLess(value["geometry"],1.)
            self.assertLess(value["topology"],1.)
            self.assertFalse(value["strict_pass"])
            self.assertIn("IFC_TOPOLOGY_DIFFERENCE",value["failure_codes"])

    def test_missing_ifc_space_boundary_fails_topology(self):
        with tempfile.TemporaryDirectory() as temp:
            def strip(model):
                rel=model.by_type("IfcRelSpaceBoundary")[0]
                model.remove(rel)
            bad=write_modified(GT_WALL,Path(temp)/"no_room_boundary.ifc",strip)
            value=wall_eval(bad)
            self.assertEqual(value["geometry"],1.)
            self.assertLess(value["topology"],1.)
            self.assertFalse(value["strict_pass"])

    def test_collateral_door_delete_fails_even_when_wall_target_is_correct(self):
        with tempfile.TemporaryDirectory() as temp:
            def collateral(model):
                door=model.by_type("IfcDoor")[0]
                ifcopenshell.api.root.remove_product(model,product=door)
            bad=write_modified(GT_WALL,Path(temp)/"deleted_unrelated_door.ifc",collateral)
            value=wall_eval(bad)
            self.assertEqual(value["geometry"],1.)
            self.assertGreater(value["collateral_detail"]["collateral_changed_count"],0)
            self.assertLess(value["semantics"],1.)
            self.assertFalse(value["strict_pass"])
            self.assertIn("UNEXPECTED_COLLATERAL_IFC_OBJECT_MUTATION",
                          value["failure_codes"])

    def test_wrong_entity_mutation_fails_target_and_collateral(self):
        with tempfile.TemporaryDirectory() as temp:
            def change_wrong(model):
                column=model.by_type("IfcColumn")[0]
                point=column.ObjectPlacement.RelativePlacement.Location
                x,y,z=(float(x) for x in point.Coordinates)
                point.Coordinates=(x+2,y,z)
            bad=write_modified(SRC,Path(temp)/"wrong_column.ifc",change_wrong)
            value=wall_eval(bad)
            self.assertFalse(value["strict_pass"])
            self.assertLess(value["geometry"],1.)
            self.assertGreater(value["collateral_detail"]["collateral_changed_count"],0)

    def test_wrong_target_ifc_class_degrades_semantic_axis(self):
        with tempfile.TemporaryDirectory() as temp:
            def retype(model):
                wall=model.by_guid(SOURCE_GUID)
                ifcopenshell.api.root.reassign_class(
                    model,product=wall,ifc_class="IfcSlab"
                )
            bad=write_modified(GT_WALL,Path(temp)/"wrong_class.ifc",retype)
            value=wall_eval(bad)
            self.assertEqual(value["status"],"INDEPENDENT_IFC_SCORED")
            self.assertLess(value["semantics"],.98)
            self.assertFalse(value["semantics_detail"]["class_match"])
            self.assertFalse(value["strict_pass"])
            self.assertIn("TARGET_SEMANTICS_DIFFERENCE",value["failure_codes"])

    def test_missing_expected_property_degrades_semantics_only(self):
        with tempfile.TemporaryDirectory() as temp:
            temp=Path(temp)
            def expected_with_pset(model):
                wall=model.by_guid(SOURCE_GUID)
                prop=ifcopenshell.api.pset.add_pset(
                    model,product=wall,name="Pset_WallCommon"
                )
                ifcopenshell.api.pset.edit_pset(
                    model,pset=prop,
                    properties={"Reference":"CONFIDENTIAL_SYNTHETIC",
                                "FireRating":"REI 180"}
                )
            gt=write_modified(GT_WALL,temp/"pset_gt.ifc",expected_with_pset)
            value=wall_eval(GT_WALL,gt=gt)
            self.assertEqual(value["geometry"],1.)
            self.assertLess(value["semantics"],.98)
            self.assertFalse(value["strict_pass"])
            self.assertNotIn("CONFIDENTIAL_SYNTHETIC",json.dumps(value))

    def test_invalid_ifc_result_fails_with_zero_not_crash(self):
        with tempfile.TemporaryDirectory() as temp:
            bad=Path(temp)/"garbage.ifc"
            bad.write_bytes(b"Not a valid IFC")
            value=wall_eval(bad)
            jsonschema.validate(value,SCHEMA)
            self.assertEqual(value["status"],"INVALID_OUTPUT_IFC")
            self.assertEqual((value["geometry"],value["semantics"],value["topology"]),
                              (0.,0.,0.))
            self.assertFalse(value["strict_pass"])

    def test_invalid_grader_reference_blocks_without_made_up_score(self):
        with tempfile.TemporaryDirectory() as temp:
            bad=Path(temp)/"garbage_gt.ifc"
            bad.write_bytes(b"Not valid")
            value=wall_eval(GT_WALL,gt=bad)
            self.assertEqual(value["status"],"BLOCKED_REFERENCE_IFC_INVALID")
            self.assertIsNone(value["geometry"])
            self.assertIsNone(value["semantics"])
            self.assertIsNone(value["topology"])
            jsonschema.validate(value,SCHEMA)

    def test_reference_space_with_no_shape_is_unsupported_not_perfect(self):
        space_guid=ifcopenshell.open(str(SRC)).by_type("IfcSpace")[0].GlobalId
        task=GraderTask("OWN-SPACE-UNSUPPORTED","update","IfcSpace",(space_guid,))
        value=score_ifc_result(source_ifc=SRC,ground_truth_ifc=SRC,
                               result_ifc=SRC,task=task)
        self.assertEqual(value["status"],"BLOCKED_REFERENCE_GEOMETRY_UNAVAILABLE")
        self.assertIsNone(value["final_score"])
        self.assertFalse(value["strict_pass"])
        jsonschema.validate(value,SCHEMA)

    def test_no_edit_prediction_for_create_cannot_fake_success(self):
        with tempfile.TemporaryDirectory() as temp:
            gt=Path(temp)/"reference.ifc"
            manual_ifc_reference(
                SRC,gt,"CREATE_WALL",
                new_guid="1UXHdOzirKMwnUzfD_y3ME",
                storey_guid=LEVEL_GUID)
            value=score_ifc_result(
                source_ifc=SRC,ground_truth_ifc=gt,result_ifc=SRC,
                task=GraderTask("OWN-CREATE-NOOP","create","IfcWall",()))
            self.assertFalse(value["strict_pass"])
            self.assertEqual(value["geometry"],0.)
            self.assertEqual(value["semantics"],0.)
            self.assertLess(value["topology"],.98)

    def test_scorer_modules_have_no_authoring_runtime_or_gt_leak(self):
        for name in (
            "src/evaluation/bim_edit_scorer.py",
            "src/evaluation/semantic_diff.py",
            "src/evaluation/geometry_metrics.py",
            "src/evaluation/topology_metrics.py"
        ):
            data=(ROOT/name).read_text(encoding="utf-8")
            for forbidden in (
                "from src.runtime.compiler","from src.direct_markup",
                "from src.imperative_control","openai.chat",
                "compile_declarative_xml(", "eval(", "exec("
            ):
                self.assertNotIn(forbidden,data)

    def test_invalid_task_target_metadata_is_blocked(self):
        with self.assertRaises(ValueError):
            GraderTask("S","update","IfcWall",())
        with self.assertRaises(ValueError):
            GraderTask("S","create","IfcWall",(SOURCE_GUID,))
        with self.assertRaises(ValueError):
            GraderTask("S","update","IfcWall",("not_a_guid",))

if __name__=="__main__": unittest.main()
