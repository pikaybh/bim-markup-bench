"""No-network, no-GT tests for released per_task CSV provenance.

ALL row data is synthetic. Public author CSV may contain prompt/GT path
metadata but this validator NEVER returns either to any authoring arm.
"""
from __future__ import annotations

from copy import deepcopy
import csv
from decimal import Decimal
from io import StringIO
import json
import unittest
from unittest.mock import patch

from src.evaluation.published_per_task_audit import (
    audit_one_published_csv,audit_published_model_set,
    PublicScoreAuditBlocked,ROUNDING_BOUND,RUNS_MODELS
)
from src.evaluation.bim_edit_scorer import PROVENANCE
from src.evaluation.geometry_metrics import GeometrySettings
from tools.audit_published_per_task_scores import _get,run_published_per_task_audit


FIELDS=["task_id","geometry","semantics","topology","final_score",
        "operation","category","prompt","ground_truth_ifc"]
OPERATIONS={"CRE":"create","UPD":"update","DEL":"delete"}
CATEGORIES={"DIR":"direct","SPA":"spatial","TOP":"topological"}
PRIVATE_MARKER="NEVER_PUBLISH_IN_MODEL_INPUT_OR_AUDIT_REPORT"


def synthetic_rows():
    rows=[]
    for op in OPERATIONS:
        for cat in CATEGORIES:
            for scene in ("A","R"):
                for index in range(1,19):
                    rows.append({
                        "task_id":f"WAL-{op}-{cat}-{scene}-{index:03d}",
                        "geometry":"0.8000",
                        "semantics":"0.7000",
                        "topology":"0.9000",
                        "final_score":"0.8000",
                        "operation":OPERATIONS[op],
                        "category":CATEGORIES[cat],
                        "prompt":PRIVATE_MARKER,
                        "ground_truth_ifc":PRIVATE_MARKER,
                    })
    assert len(rows)==324
    return rows


def encode(rows,*,fieldnames=FIELDS):
    out=StringIO(newline="")
    writer=csv.DictWriter(out,fieldnames=fieldnames,extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("utf8")


def fake_summary(rows):
    return {
        "overall":{
            "n_tasks":len(rows),"n_samples":len(rows),
            "geometry_mean":0.8,"semantics_mean":0.7,
            "topology_mean":0.9,"final_score_mean":0.8,
        },
        "by_scene_type":{"realistic":{"n_tasks":len(rows)}},
    }


def all_model_inputs():
    base=synthetic_rows()
    raw={}
    for model in RUNS_MODELS:
        rows=base[:-1] if model=="qwen3.6-plus" else base
        raw[model]=(encode(rows),fake_summary(rows))
    return raw


class PublishedPerTaskAuditTests(unittest.TestCase):
    def test_seven_synthetic_reports_including_one_missing_qwen_row(self):
        audit=audit_published_model_set(all_model_inputs())
        self.assertEqual(audit["verified_published_models"],7)
        self.assertEqual(audit["full_324_row_models"],6)
        self.assertEqual(audit["total_missing_published_task_rows"],1)
        self.assertEqual(audit["published_models_with_missing_rows"],
                         ["qwen3.6-plus"])
        self.assertEqual(audit["models"]["qwen3.6-plus"][
            "missing_id_count_vs_six_full_runs"],1)
        self.assertEqual(audit["models"]["claude-sonnet"][
            "task_id_scene_counts"],{"A":162,"R":162})
        self.assertFalse(audit["G2_G3_live_model_or_official_scoring_gate_ready"])
        self.assertEqual(audit["official_tasks_scored_by_this_project"],0)
        self.assertFalse(audit["numerical_official_evaluator_equivalence_verified"])
        redacted=json.dumps(audit,sort_keys=True)
        self.assertNotIn(PRIVATE_MARKER,redacted)
        self.assertNotIn("ground_truth_ifc",redacted)
        self.assertNotIn("WAL-CRE-DIR-A-001",redacted)

    def test_one_model_exact_rows_mean_and_private_output_boundary(self):
        rows=synthetic_rows()
        report,ids=audit_one_published_csv(
            "claude-sonnet",encode(rows),fake_summary(rows))
        self.assertEqual(len(ids),324)
        self.assertEqual(report["published_rows"],324)
        self.assertTrue(report["means_match_published_summary_within_rounding"])
        self.assertEqual(report["strict_three_axis_count_from_published_rows"],0)
        self.assertTrue(report["scene_summary_label_mismatch_warning"])
        self.assertEqual(report["operation_counts"],
                         {"create":108,"delete":108,"update":108})
        self.assertEqual(report["instruction_category_counts"],
                         {"direct":108,"spatial":108,"topological":108})
        self.assertFalse(report["per_task_model_prompts_or_GT_paths_exported"])

    def test_rounding_differences_under_0_0001_are_accepted(self):
        rows=synthetic_rows()
        rows[0]["geometry"]="0.8000"
        rows[0]["semantics"]="0.7000"
        rows[0]["topology"]="0.9001"
        rows[0]["final_score"]="0.8001"
        # Difference (0.0001 - 0.0000333) is expected when scores
        # are independently rounded to four places.
        audit,_=audit_one_published_csv(
            "claude-sonnet",encode(rows),fake_summary(rows))
        self.assertLessEqual(
            Decimal(audit["max_per_row_rounding_difference"]),ROUNDING_BOUND)

    def test_corrupt_per_row_final_outside_rounding_fails(self):
        rows=synthetic_rows()
        rows[0]["final_score"]="0.9000"
        with self.assertRaisesRegex(PublicScoreAuditBlocked,"per-task final"):
            audit_one_published_csv("claude-sonnet",encode(rows),fake_summary(rows))

    def test_duplicate_row_and_missing_more_than_one_row_fail_closed(self):
        rows=synthetic_rows()
        rows[1]["task_id"]=rows[0]["task_id"]
        with self.assertRaisesRegex(PublicScoreAuditBlocked,"duplicate"):
            audit_one_published_csv("claude-sonnet",encode(rows),fake_summary(rows))
        rows=synthetic_rows()[:-2]
        with self.assertRaisesRegex(PublicScoreAuditBlocked,"coverage"):
            audit_one_published_csv("claude-sonnet",encode(rows),fake_summary(rows))

    def test_mismatched_task_id_operation_and_category_fail(self):
        for key,new in (("operation","delete"),("category","topological")):
            rows=synthetic_rows()
            rows[0][key]=new
            with self.subTest(key=key),self.assertRaisesRegex(
                PublicScoreAuditBlocked,"category mismatch"):
                audit_one_published_csv("claude-sonnet",encode(rows),fake_summary(rows))

    def test_bad_numeric_or_missing_scores_rejected(self):
        for value in ("NaN","Infinity","-0.01","1.01","non-number",""):
            rows=synthetic_rows()
            rows[0]["geometry"]=value
            with self.subTest(value=value),self.assertRaises(
                PublicScoreAuditBlocked):
                audit_one_published_csv("claude-sonnet",encode(rows),fake_summary(rows))

    def test_header_and_field_count_injection_fail(self):
        rows=synthetic_rows()
        data=encode(rows,fieldnames=[name for name in FIELDS if name!="topology"])
        with self.assertRaisesRegex(PublicScoreAuditBlocked,"header"):
            audit_one_published_csv("claude-sonnet",data,fake_summary(rows))
        dup=encode(rows)
        dup=dup.replace(b"task_id,geometry",b"task_id,task_id",1)
        with self.assertRaisesRegex(PublicScoreAuditBlocked,"header"):
            audit_one_published_csv("claude-sonnet",dup,fake_summary(rows))
        extra=encode(rows).replace(b"NEVER_PUBLISH_IN_MODEL_INPUT_OR_AUDIT_REPORT\r\n",
                                  b"NEVER_PUBLISH_IN_MODEL_INPUT_OR_AUDIT_REPORT,EXTRA\r\n",1)
        with self.assertRaises(PublicScoreAuditBlocked):
            audit_one_published_csv("claude-sonnet",extra,fake_summary(rows))

    def test_summary_count_and_mean_must_match_rows(self):
        rows=synthetic_rows()
        for mutation in (("n_tasks",323),("n_samples",323),
                         ("geometry_mean",0.81),("final_score_mean",0.79)):
            summary=fake_summary(rows)
            summary["overall"][mutation[0]]=mutation[1]
            with self.subTest(mutation=mutation),self.assertRaises(
                PublicScoreAuditBlocked):
                audit_one_published_csv("claude-sonnet",encode(rows),summary)

    def test_mismatched_full_set_or_partial_extra_task_refused(self):
        raw=all_model_inputs()
        rows=synthetic_rows()
        rows[0]["task_id"]="WAL-CRE-DIR-A-999"
        raw["gpt-5.4"]=(encode(rows),fake_summary(rows))
        with self.assertRaisesRegex(PublicScoreAuditBlocked,"sets differ"):
            audit_published_model_set(raw)
        raw=all_model_inputs()
        rows=synthetic_rows()[:-1]
        rows[0]["task_id"]="WAL-CRE-DIR-A-999"
        raw["qwen3.6-plus"]=(encode(rows),fake_summary(rows))
        with self.assertRaisesRegex(PublicScoreAuditBlocked,"unexpected task"):
            audit_published_model_set(raw)

    def test_missing_model_cannot_report_seven_complete(self):
        raw=all_model_inputs()
        raw.pop("gemini-flash-3.0")
        with self.assertRaisesRegex(PublicScoreAuditBlocked,"Incomplete"):
            audit_published_model_set(raw)

    def test_strict_pass_rule_requires_each_axis_not_just_final_mean(self):
        rows=synthetic_rows()
        rows[0].update(geometry="1.0000",semantics="1.0000",
                       topology="0.9500",final_score="0.9833")
        # Keep summary independently consistent with changed single row.
        summary=fake_summary(rows)
        for metric in ("geometry","semantics","topology","final_score"):
            summary["overall"][metric+"_mean"]=round(
                sum(float(x[metric]) for x in rows)/len(rows),4)
        report,_=audit_one_published_csv(
            "claude-sonnet",encode(rows),summary)
        self.assertEqual(report["strict_three_axis_count_from_published_rows"],0)

    def test_network_allowlist_never_accepts_raw_ifc_or_other_models(self):
        for model,kind in (("hacker","csv"),("claude-sonnet","raw_ifc"),
                           ("../claude-sonnet","summary")):
            with self.subTest(model=model,kind=kind),self.assertRaises(ValueError):
                _get(model,kind)

    def test_offline_all_model_audit_fetches_only_public_csv_and_summary(self):
        synthetic=all_model_inputs()
        calls=[]
        def fake_fetch(model,kind):
            calls.append((model,kind))
            return synthetic[model][0] if kind=="csv" else json.dumps(
                synthetic[model][1]).encode("utf8")
        with patch("tools.audit_published_per_task_scores._get",
                   side_effect=fake_fetch):
            result=run_published_per_task_audit()
        self.assertEqual(len(calls),14)
        self.assertEqual({kind for _,kind in calls},{"csv","summary"})
        self.assertEqual(result["native_IFC_or_GT_files_downloaded"],0)
        self.assertFalse(result["per_task_results_exported_or_committed"])

    def test_actual_local_scorer_retains_distinct_metric_provenance(self):
        self.assertEqual(PROVENANCE,"independent-reimplementation")
        self.assertEqual(GeometrySettings().sample_count,384)
        self.assertFalse(audit_published_model_set(
            all_model_inputs())["numerical_official_evaluator_equivalence_verified"])


if __name__=="__main__":
    unittest.main()
