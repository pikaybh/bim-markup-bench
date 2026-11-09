"""Issue #4: scorer source-vs-paper provenance checks, no benchmark/GT access."""
import unittest
from unittest.mock import patch
from src.evaluation.metric_gap_audit import audit_scorer_gap
from src.evaluation.geometry_metrics import GeometrySettings


class GapAuditTests(unittest.TestCase):
    def test_unverified_official_source_never_promoted_to_official_score(self):
        r=audit_scorer_gap()
        self.assertEqual(r["status"],"BLOCKED_OFFICIAL_SCORER_UNVERIFIED")
        self.assertEqual(r["metric_origin"],"independent-reimplementation")
        self.assertFalse(r["official_metric_numerical_equivalence"])
        self.assertFalse(r["official_evaluator_source_commit_verified"])
        self.assertEqual(r["official_tasks_scored"],0)
        self.assertEqual(r["paid_model_calls"],0)
        self.assertTrue(all(r["current_code_evidence"].values()))

    def test_published_rounded_arithmetic_is_only_scalar_not_raw_ifc(self):
        rows=audit_scorer_gap()["paper_examples_scalar_only"]
        self.assertEqual(len(rows),4)
        self.assertAlmostEqual(rows[1]["scalar_mean"],(1+1+.47)/3)
        self.assertAlmostEqual(rows[2]["scalar_mean"],.7)
        self.assertEqual([r["scalar_strict_pass"] for r in rows],
                         [True,False,False,False])
        self.assertTrue(all(not r["raw_ifc_recomputed"] for r in rows))

    def test_sample_count_is_not_mistaken_for_paper_equivalent_policy(self):
        r=audit_scorer_gap(geometry_settings=GeometrySettings(sample_count=512))
        self.assertEqual(r["independent_default_sample_count"],512)
        self.assertEqual(r["paper_sampling_per_object_upper_bound"],4096)
        self.assertFalse(r["sampling_schedule_equivalence_verified"])

    def test_code_behavior_change_is_fail_closed(self):
        with patch("src.evaluation.metric_gap_audit.inspect.getsource",return_value="pass"):
            r=audit_scorer_gap()
        self.assertEqual(r["status"],"BLOCKED_REAUDIT_CODE_SIGNATURE_CHANGED")
        self.assertFalse(all(r["current_code_evidence"].values()))


if __name__=="__main__":
    unittest.main()
