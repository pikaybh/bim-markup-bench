"""No-provider tests: exact 45-capability taxonomy and independent IFC oracle.

Uses real public BIBIMBAP source IFC only; never reads author grader/GT,
never makes paid calls. Test IFCs are local scratch clones.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import json
import os
import tempfile
import unittest

import ifcopenshell
import ifcopenshell.util.unit

from tools.audit_bibimbap45_capability import SPEC,CODE_SUPPORTED,structural_45
from tools.oracle_bibimbap_geometry11_height import (
    OracleFailure,independent_oracle,
)
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",r"D:\문서\D__1_Projects\202611"))
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
MATRIX=Path(__file__).resolve().parents[1]/"reports"/"bibimbap45_capability_audit_20261113.json"
EXTERNAL=AUTHOR.is_dir() and DATA.is_dir()

@unittest.skipUnless(EXTERNAL,"Pinned original public BIBIMBAP assets missing")
class Original45CapabilityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stored=json.loads(MATRIX.read_text(encoding="utf8"))

    def test_exact_45_population_and_stratification(self):
        data=self.stored["individual_task_gap_matrix"]
        self.assertEqual(len(data),45)
        self.assertEqual(set(SPEC),{x["original_task_id"] for x in data})
        self.assertEqual(Counter(x["crud"] for x in data),
                         {"create":15,"update":15,"delete":15})
        self.assertEqual(Counter(x["category"] for x in data),
                         {"basic":15,"geometry":15,"topological":15})
        self.assertTrue(self.stored["all_45_original_editing_task_ids_accounted"])
        self.assertEqual(self.stored["original_45_itt_denominator"],45)

    def test_source_and_schema_read_only_from_pinned_public_data(self):
        for row in self.stored["individual_task_gap_matrix"]:
            p=DATA/"ifc"/row["original_source_ifc_relpath"]
            self.assertEqual(file_hash(p),row["original_source_ifc_sha256"])
            self.assertEqual(len(row["public_question_sha256"]),64)
            self.assertNotIn("question",row)
            self.assertNotIn("ground_truth",row)
            self.assertIn(row["original_ifc_schema"],("IFC2X3","IFC4","IFC4X3"))
        blocked=[x for x in self.stored["individual_task_gap_matrix"]
                 if not x["source_xml_projectable_previously"]]
        self.assertEqual(len(blocked),9)
        self.assertEqual(Counter(x["original_ifc_schema"] for x in blocked),
                         {"IFC4X3":6,"IFC2X3":2,"IFC4":1})

    def test_zero_model_calls_and_historical_scores_remain_unchanged(self):
        self.assertEqual(self.stored["model_requests"],0)
        self.assertEqual(self.stored["api_spend_usd"],"0")
        self.assertTrue(self.stored["this_is_not_an_LLM_benchmark_result"])
        self.assertTrue(self.stored["this_is_not_45_D0_oracle_passes"])
        self.assertFalse(self.stored["paper_equivalent_45_task_bim_backend_available"])
        self.assertEqual(self.stored["strict_task_oracle_complete_count"],0)
        self.assertEqual(self.stored["source_projected_36_of_45"],36)
        self.assertEqual(self.stored["source_blocked_9_of_45"],9)
        self.assertEqual(self.stored["gates_by_count"],{
            "SOURCE_PROJECTION_BLOCKED":9,
            "NATIVE_COMPILER_MISSING":20,
            "XML_DECLARATIVE_SCHEMA_GAP":2,
            "CONDITIONAL_BACKEND_WITHOUT_TASK_ORACLE":12,
            "SUPPORTED_SLICE_STRICT_TASK_UNVERIFIED":2,
        })
        old=Path(__file__).resolve().parents[1]/"reports"/"bibimbap_original45_luna_20261112.json"
        self.assertEqual(file_hash(old),self.stored["baseline_luna45_report_sha256"])
        self.assertEqual(self.stored["historical_21_failures_replayed_read_only"],True)
        self.assertEqual(sum(self.stored["historical_failures_by_replay_category"].values()),21)

    def test_gaps_are_not_falsely_promoted_to_native_support(self):
        rows={x["original_task_id"]:x for x in self.stored["individual_task_gap_matrix"]}
        self.assertEqual(rows["test_03"]["xml_schema_declaration_expressible"],"NO")
        self.assertEqual(rows["topological_test_14"]["xml_schema_declaration_expressible"],"NO")
        for key in ("test_01","test_02","test_04","test_20",
                    "geometry_test_02","topological_test_20"):
            self.assertEqual(rows[key]["compiler_native_operation_gate"],"MISSING")
        self.assertEqual(rows["geometry_test_05"]["original_ifc_schema"],"IFC4")
        self.assertEqual(rows["test_05"]["compiler_native_operation_gate"],"IMPLEMENTED_SUBSET")
        self.assertEqual(rows["geometry_test_11"]["compiler_native_operation_gate"],"IMPLEMENTED_SUBSET")
        self.assertTrue(all(not x["future_D0_end_to_end_oracle_proved"] for x in rows.values()))

    def test_generated_structural_only_matrix_does_not_change(self):
        # Ignore per-task replay attachments; these are a *separate*
        # forensic layer derived from frozen previous paid responses.
        expected=structural_45(AUTHOR,DATA)
        ours=dict(self.stored)
        for row in ours["individual_task_gap_matrix"]:
            row.pop("historical_read_only_compile_replay",None)
        ours.pop("historical_21_failures_replayed_read_only",None)
        ours.pop("historical_failures_by_replay_category",None)
        self.assertEqual(ours,expected)

@unittest.skipUnless(EXTERNAL,"Real public BIBIMBAP original IFC absent")
class IndependentGeometry11NativeOracleTests(unittest.TestCase):
    def setUp(self):
        self.scratch=tempfile.TemporaryDirectory(prefix="bibi116-geom11-oracle-")
        self.addCleanup(self.scratch.cleanup)
        self.tmp=Path(self.scratch.name)
        inp=DATA/"ifc"/"01"/"01"/"01_01_011.ifc"
        self.immutable_sha=file_hash(inp)
        original=ifcopenshell.open(str(inp))
        self.source=self.tmp/"source_m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(original,"METER").write(str(self.source))
        self.result=self.tmp/"correct_m.ifc"
        self.solids=(219,241,263,285,307,329)
        candidate=ifcopenshell.open(str(self.source))
        for entity_id in self.solids:
            solid=candidate.by_id(entity_id)
            self.assertTrue(solid.is_a("IfcExtrudedAreaSolid"))
            self.assertAlmostEqual(float(solid.Depth),3.5)
            solid.Depth=float(solid.Depth)-0.5
        candidate.write(str(self.result))
        self.addCleanup(lambda:self.assertEqual(file_hash(inp),self.immutable_sha))

    def test_positive_independent_real_native_ifc_source_geometry(self):
        a=independent_oracle(self.source,self.result)
        self.assertEqual(a["verified_modified_second_storey_walls"],6)
        self.assertEqual(a["verified_unchanged_non_target_walls"],6)
        self.assertEqual(a["exact_step_changed_entity_count"],6)
        self.assertTrue(a["only_target_extrusions_modified"])
        self.assertTrue(a["native_world_mesh_each_target_verified"])
        self.assertFalse(a["full_collision_and_building_topology_independently_verified"])

    def test_negative_noop_cannot_pass(self):
        with self.assertRaises(OracleFailure):
            independent_oracle(self.source,self.source)
        other=self.tmp/"noop_m.ifc"
        other.write_bytes(self.source.read_bytes())
        with self.assertRaisesRegex(OracleFailure,"height reduction"):
            independent_oracle(self.source,other,verify_mesh=False)

    def test_negative_wrong_height_one_target_rejected(self):
        candidate=ifcopenshell.open(str(self.result))
        candidate.by_id(self.solids[0]).Depth=3.25
        wrong=self.tmp/"wrong_height.ifc";candidate.write(str(wrong))
        with self.assertRaisesRegex(OracleFailure,"Wrong second-storey"):
            independent_oracle(self.source,wrong,verify_mesh=False)

    def test_negative_unrelated_wall_modification_rejected(self):
        candidate=ifcopenshell.open(str(self.result))
        wall=candidate.by_type("IfcWall")[0]
        wall.Name="Unexpected non-target renaming"
        wrong=self.tmp/"wrong_untouched.ifc";candidate.write(str(wrong))
        with self.assertRaisesRegex(OracleFailure,"Unexpected native STEP entity delta"):
            independent_oracle(self.source,wrong,verify_mesh=False)

    def test_negative_added_entity_rejected(self):
        candidate=ifcopenshell.open(str(self.result))
        candidate.createIfcCartesianPoint((0.,0.,0.))
        wrong=self.tmp/"unexpected_extra.ifc";candidate.write(str(wrong))
        with self.assertRaisesRegex(OracleFailure,"entity inventory"):
            independent_oracle(self.source,wrong,verify_mesh=False)

    def test_negative_modify_wrong_storey_wall_rejected(self):
        candidate=ifcopenshell.open(str(self.result))
        first_level=candidate.by_type("IfcWall")[0]
        # First wall lives on L1; use its native extrusion to prove
        # every original STEP entity is audited, not only modified targets.
        solids=[item for rep in first_level.Representation.Representations
                for item in rep.Items if item.is_a("IfcExtrudedAreaSolid")]
        self.assertEqual(len(solids),1)
        solids[0].Depth-=.5
        wrong=self.tmp/"wrong_level.ifc";candidate.write(str(wrong))
        with self.assertRaisesRegex(OracleFailure,"Unexpected native STEP entity delta"):
            independent_oracle(self.source,wrong,verify_mesh=False)

if __name__=="__main__":
    unittest.main()
