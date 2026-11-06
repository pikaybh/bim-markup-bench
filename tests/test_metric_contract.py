import json
import math
import unittest
from pathlib import Path

from src.evaluation.metric_contract import (
    InvalidScore, final_score, geometry_from_median_chamfer, semantic_score, topology_score,
)

class FormulaContractTests(unittest.TestCase):
    def test_perfect_case(self):
        v=final_score(1,1,1)
        self.assertEqual(v["final_score"],1)
        self.assertTrue(v["strict_pass"])
        self.assertFalse(v["full_ifc_evaluator_implemented"])

    def test_paper_example_2_partial_topology(self):
        v=final_score(1.00,1.00,0.47)
        self.assertAlmostEqual(v["final_score"], (1+1+0.47)/3)
        self.assertFalse(v["strict_pass"])

    def test_paper_example_3_partial_geometry(self):
        v=final_score(0.38,0.72,1.0)
        self.assertAlmostEqual(v["final_score"], 0.7)
        self.assertFalse(v["strict_pass"])

    def test_paper_example_4_zero(self):
        self.assertEqual(final_score(0,0,0)["final_score"],0)

    def test_strict_threshold_inclusive_all_axes(self):
        self.assertTrue(final_score(0.98,0.98,0.98)["strict_pass"])
        self.assertFalse(final_score(0.98,0.979999,1.0)["strict_pass"])

    def test_geometry_exponential_decay(self):
        self.assertAlmostEqual(geometry_from_median_chamfer(0,1),1)
        self.assertAlmostEqual(geometry_from_median_chamfer(math.log(2)/5,1),0.5)

    def test_geometry_degenerate_rejected_not_invented(self):
        for cd,d in [(1,0),(-1,2),(float("nan"),1),(0,float("inf"))]:
            with self.subTest(cd=cd,d=d), self.assertRaises(InvalidScore):
                geometry_from_median_chamfer(cd,d)

    def test_semantics_unmatched_zero_and_delete(self):
        self.assertAlmostEqual(semantic_score([(True,1),(False,0.6)],3),(1 + 0.3)/3)
        self.assertEqual(semantic_score([],0,deletion_removed=True),1)
        self.assertEqual(semantic_score([],0,deletion_removed=False),0)
        with self.assertRaises(InvalidScore):
            semantic_score([(True,1)]*2,1)

    def test_topology_node_edge_03_07(self):
        self.assertAlmostEqual(topology_score(.8,.5,reference_has_topology_change=True,prediction_has_topology_change=True),.59)
        self.assertEqual(topology_score(None,None,reference_has_topology_change=False,prediction_has_topology_change=False),1)
        self.assertEqual(topology_score(None,None,reference_has_topology_change=False,prediction_has_topology_change=True),0)
        with self.assertRaises(InvalidScore):
            topology_score(None,.5,reference_has_topology_change=True,prediction_has_topology_change=True)

    def test_invalid_nan_and_out_of_range(self):
        for value in [float("nan"),-0.01,1.0001]:
            with self.assertRaises(InvalidScore):
                final_score(value,1,1)

    def test_output_schema_of_formula_only(self):
        import jsonschema
        root=Path(__file__).resolve().parents[1]
        schema=json.loads((root/"schemas/metric_output.schema.json").read_text())
        jsonschema.validate(final_score(.7,.8,.9),schema)
        self.assertEqual(schema["properties"]["metric_origin"]["enum"][0],"paper-formula-only")

if __name__=="__main__":
    unittest.main()
