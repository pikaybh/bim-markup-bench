"""Original 45 public task read-vs-write capability matrix v0.12 regression.

Unlike a read-only XML projection, a successful benchmark result requires
a task-specific actual *native writer*, an independent oracle and a matched
Python I0. None of those may be fabricated from source/score metadata.
"""
from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
import tempfile
import unittest

from tools.audit_bibimbap_v12_real45_capability_matrix import (
    REQUIREMENTS,PINNED_D0_REPORTS,_frozen_d0,_reference_gate,
    _type_role,SOURCE_GUID_PATTERN,run,
)
from tools.audit_bibimbap_v12_projection_worker import inspect
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",
                         r"D:\문서\D__1_Projects\202611"))
ROOT=Path(__file__).resolve().parents[1]
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
JSON=ROOT/"reports"/"bibimbap_v012_actual_original45_native_read_and_D0I0_matrix_20261114.json"
CSV=ROOT/"reports"/"bibimbap_v012_actual_original45_native_read_and_D0I0_matrix_20261114.csv"


class FrozenOriginal45V12Matrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (AUTHOR.is_dir() and DATA.is_dir() and JSON.exists() and CSV.exists()):
            raise unittest.SkipTest("Original pinned author/dataset or v0.12 report absent")
        cls.matrix=json.loads(JSON.read_text(encoding="utf8"))
        cls.rows={
            x["original_public_task_id"]:x
            for x in cls.matrix["original_45_task_capability_and_evidence_matrix"]
        }
        cls.public={
            x["test_id"]:x for x in public_45(AUTHOR,DATA)
        }

    def test_original_exact_public_45_are_in_registry_and_matrix(self):
        self.assertEqual(len(REQUIREMENTS),45)
        self.assertEqual(set(self.rows),set(self.public))
        self.assertEqual(set(self.rows),set(REQUIREMENTS))
        self.assertEqual(len(self.matrix["original_45_task_capability_and_evidence_matrix"]),45)
        self.assertEqual(self.matrix["original_public_task_population"],45)
        self.assertTrue(self.matrix["every_original_task_kept_in_45_denominator"])
        for task,row in self.rows.items():
            self.assertFalse(row["excluded_from_original_45_denominator"])
            self.assertEqual(row["original_public_question_sha256"],
                             self.public[task]["public_question_sha256"])
            self.assertEqual(row["original_public_source_ifc_sha256"],
                             self.public[task]["original_ifc_sha256"])

    def test_source_unique_31_and_per_task_45_original_source_projection(self):
        m=self.matrix
        self.assertEqual(m["unique_original_ifc_source_count"],31)
        self.assertEqual(len(m["original_native_source_observations_by_sha256"]),31)
        self.assertEqual(m["real_unique_source_projection_states"],{
            "FAIL_CLOSED":2,
            "PASSED_NATIVE_PARTIAL_SOURCE_READ":29,
        })
        self.assertEqual(m["real_source_projection_states_across_45_tasks"],{
            "FAIL_CLOSED":2,
            "PASSED_NATIVE_PARTIAL_SOURCE_READ":43,
        })
        self.assertTrue(m["source_projection_worker_isolated_per_unique_original_IFC"])
        self.assertTrue(m["all_original_source_shas_verified_after_readonly_projection"])

    def test_two_original_native_sources_rejected_by_actual_host_opening_binder(self):
        failures={t:r for t,r in self.rows.items()
                  if r["actual_source_projection_state"]=="FAIL_CLOSED"}
        self.assertEqual(set(failures),{
            "geometry_test_18","geometry_test_19",
        })
        for task,r in failures.items():
            self.assertEqual(
                r["actual_source_projection_failure_code"],
                "HOSTED_OPENING_OUTSIDE_SOURCE_WALL_XML_BINDER_EXTENT")
            self.assertEqual(r["original_native_schema"],"IFC4X3")
            self.assertFalse(r["actual_readonly_partial_source_projection"])

    def test_36_task_relevant_read_gates_are_not_write_parity(self):
        self.assertEqual(
            self.matrix["reference_and_required_source_roles_readonly_complete_task_count"],
            36,
        )
        self.assertEqual(sum(
            r["source_role_and_public_reference_gate"][
                "complete_named_refs_and_source_roles_in_current_read_view"]
            for r in self.rows.values()
        ),36)
        for r in self.rows.values():
            self.assertTrue(r["source_role_and_public_reference_gate"][
                "this_is_not_proof_of_semantic_task_write_support"])
            self.assertEqual(r["true_equal_capability_XML_Python_edit_parity"],
                             "NOT_PROVEN")
            self.assertFalse(r["native_full_original_task_success_independently_verified"])

    def test_genuine_group_reference_coverage_blocks_full_read_success(self):
        for task in (
            "geometry_test_20","test_20","topological_test_01",
            "topological_test_03","topological_test_14",
            "topological_test_18","topological_test_20",
        ):
            gate=self.rows[task]["source_role_and_public_reference_gate"]
            self.assertFalse(gate[
                "complete_named_refs_and_source_roles_in_current_read_view"])
            self.assertTrue(
                any(not r["all_original_products_of_required_role_projected"]
                    for r in gate["source_role_projection_coverage"].values()),
                task,
            )

    def test_missing_native_Beam_role_is_NOT_mislabelled_as_editable(self):
        r=self.rows["topological_test_14"]
        self.assertEqual(r["required_native_operation_family_from_public_task"],
                         "TRIM_BEAMS_TO_NAMED_WALL")
        coverage=r["source_role_and_public_reference_gate"][
            "source_role_projection_coverage"]
        self.assertEqual(coverage["Beam"]["source_native_product_count"],4)
        self.assertEqual(coverage["Beam"]["read_projection_native_product_count"],0)
        self.assertFalse(coverage["Beam"][
            "all_original_products_of_required_role_projected"])
        self.assertEqual(r["native_semantic_write_status"],
                         "NOT_ESTABLISHED_FOR_THIS_ORIGINAL_TASK")

    def test_original_native_products_are_not_faked_by_partial_xml_projection(self):
        source=self.matrix["original_native_source_observations_by_sha256"][
            self.rows["test_02"]["original_public_source_ifc_sha256"]
        ]
        self.assertEqual(source["projection_state"],
                         "PASSED_NATIVE_PARTIAL_SOURCE_READ")
        self.assertEqual(source["original_source_product_count"],43)
        self.assertEqual(source["projected_native_existing_product_count"],35)
        self.assertEqual(source["original_native_products_not_in_XML_count"],8)
        self.assertTrue(source[
            "partial_projection_not_full_IFC_source_SERIALIZATION"])
        self.assertTrue(source["no_native_write_operation_executed"])
        self.assertEqual(source["source_stable_id_binding_status"],
                         "ORIGINAL_SOURCE_ID_GRAPH_BOUND")

    def test_original_legacy_ifc_schema_is_preserved_with_separate_read_namespace(self):
        schemas=Counter(x["original_native_schema"] for x in self.rows.values())
        self.assertEqual(schemas,{"IFC4X3":42,"IFC2X3":2,"IFC4":1})
        for task in ("geometry_test_03","geometry_test_04","geometry_test_05"):
            row=self.rows[task]
            self.assertTrue(row["actual_readonly_partial_source_projection"])
            obs=self.matrix["original_native_source_observations_by_sha256"][
                row["original_public_source_ifc_sha256"]]
            self.assertEqual(obs["source_stable_id_binding_status"],
                "SCHEMA_NATIVE_LEGACY_READONLY_XML_NOT_IFC4X3_BINDER")
            self.assertTrue(obs["normalized_original_schema_preserved"])

    def test_previous_v01_readability_is_historical_not_current_45_edit_pass(self):
        self.assertEqual(self.matrix["historical_v01_projection_count_NOT_CURRENT"],{
            "BLOCKED":9,"PROJECTABLE":36})
        self.assertEqual(
            self.matrix["real_source_projection_states_across_45_tasks"][
                "PASSED_NATIVE_PARTIAL_SOURCE_READ"],43)
        self.assertTrue(self.matrix["source_read_only_does_not_imply_write_capability"])
        self.assertTrue(self.matrix[
            "full_45_native_XML_semantic_write_parity_not_proven"])

    def test_prior_nine_sha_pinned_D0_reports_still_immutable(self):
        self.assertEqual(len(PINNED_D0_REPORTS),9)
        for version,(name,expected_sha) in PINNED_D0_REPORTS.items():
            with self.subTest(version=version):
                self.assertEqual(file_hash(ROOT/"reports"/name),expected_sha)

    def test_22_frozen_developer_D0_full11_partial11_with_no_invented_cases(self):
        m=self.matrix
        self.assertEqual(m["frozen_developer_D0_evidence_counts"],{
            "FROZEN_DEVELOPER_D0_ORIGINAL_AUTHOR_FULL_MARK":11,
            "FROZEN_DEVELOPER_D0_ORIGINAL_AUTHOR_PARTIAL":11,
            "NO_V02_TO_V010_FROZEN_DEVELOPER_D0":23,
        })
        evidence=_frozen_d0(ROOT,self.public)
        self.assertEqual(len(evidence),22)
        self.assertEqual(sum(
            v["original_author_full_mark_from_D0"] for v in evidence.values()
        ),11)
        for tid,row in self.rows.items():
            self.assertEqual(row["frozen_source_only_developer_D0_evidence"],
                             evidence.get(tid))
            if tid in evidence:
                self.assertEqual(row["native_semantic_write_status"],
                    "ONLY_PREVIOUS_FROZEN_TASK_SPECIFIC_D0_CANDIDATE_EVIDENCED")
                self.assertTrue(evidence[tid][
                    "original_author_score_does_not_prove_strict_task_success"])
            else:
                self.assertEqual(row["native_semantic_write_status"],
                                 "NOT_ESTABLISHED_FOR_THIS_ORIGINAL_TASK")
                self.assertIsNone(row["frozen_source_only_developer_D0_evidence"])

    def test_author_full_mark_without_full_scene_oracle_is_explicitly_unverified(self):
        d0=self.rows["test_04"]["frozen_source_only_developer_D0_evidence"]
        self.assertEqual(d0["original_author_score_from_frozen_developer_D0"],1.)
        self.assertEqual(d0["historical_independent_native_oracle"],
                         "NO_INDEPENDENT_FULL_SCENE_ORACLE_RECORDED")
        self.assertEqual(self.rows["test_04"]["native_independent_D0_oracle_status"],
                         "NO_INDEPENDENT_FULL_SCENE_ORACLE_RECORDED")
        self.assertFalse(self.rows["test_04"][
            "native_full_original_task_success_independently_verified"])

    def test_all_per_task_Python_I0_are_unknown_not_zero_scored(self):
        m=self.matrix
        self.assertEqual(m["all_45_I0_matched_Python_task_specific_run_count"],0)
        self.assertEqual(m["all_45_new_real_matched_model_XML_vs_Python_trial_count"],0)
        self.assertTrue(m["true_equal_capability_XML_vs_Python_parity_not_proven"])
        self.assertTrue(m["full_45_Python_I0_comparison_not_run"])
        for row in self.rows.values():
            self.assertEqual(row["Python_control_matching_task_specific_I0_run"],
                             "NOT_RUN_NO_EVIDENCE")
            self.assertEqual(row["Python_control_independent_task_specific_I0_oracle"],
                             "NOT_RUN_NO_EVIDENCE")
            self.assertEqual(row["current_real_matched_model_XML_vs_Python_trial"],
                             "NOT_RUN")

    def test_source_role_coverage_does_not_confuse_lowercase_IFC_guid(self):
        # IFC compressed 22-character GUIDs are CASE-SENSITIVE: original
        # ICF2X3 references 0...rK and 0...rk must never be collapsed.
        task={"public_question":
              "Columns with IDs 2IIWDJ6bzEPxU4iXeUX9rK and "
              "2IIWDJ6bzEPxU4iXeUX9rk"}
        rec={
            "projection_state":"PASSED_NATIVE_PARTIAL_SOURCE_READ",
            "original_product_class_by_guid":{
                "2IIWDJ6bzEPxU4iXeUX9rK":"IfcColumn",
                "2IIWDJ6bzEPxU4iXeUX9rk":"IfcColumn",
            },
            "projected_existing_product_xml_type_by_guid":{
                "2IIWDJ6bzEPxU4iXeUX9rK":"Column",
            },
        }
        gate=_reference_gate(task,rec,("Column",))
        self.assertEqual(gate["public_named_references_count"],2)
        self.assertEqual(gate["public_named_native_references_projected_count"],1)
        self.assertFalse(gate[
            "complete_named_refs_and_source_roles_in_current_read_view"])

    def test_invalid_worker_wrong_original_ifc_hash_rejected(self):
        source=DATA/"ifc"/"basic_tasks.ifc"
        with self.assertRaisesRegex(ValueError,"INPUT_SOURCE_SHA"):
            inspect(source,"0"*64)

    def test_every_public_guid_reference_is_accounted_for_exactly(self):
        for task,row in self.rows.items():
            gate=row["source_role_and_public_reference_gate"]
            self.assertEqual(
                gate["public_named_references_count"],
                (gate["public_named_native_IFC_reference_found_count"]
                 +len(gate["public_named_IFC_references_missing_from_source"]))
            )
            self.assertEqual(
                gate["public_named_native_IFC_reference_found_count"],
                (gate["public_named_native_references_projected_count"]
                 +len(gate["original_public_named_native_references_not_in_XML"]))
            )

    def test_case_specific_required_operation_registry_not_inferred_from_grade(self):
        self.assertEqual(len({x[1] for x in REQUIREMENTS.values()}),45)
        for task,(roles,op) in REQUIREMENTS.items():
            row=self.rows[task]
            self.assertEqual(row["required_source_roles_from_public_task"],list(roles))
            self.assertEqual(row["required_native_operation_family_from_public_task"],op)
            self.assertEqual(op,op.upper())
            self.assertTrue(row["task_requirements_registry_from_original_public_question_only"]
                            if "task_requirements_registry_from_original_public_question_only" in row
                            else self.matrix["task_requirements_registry_from_original_public_question_only"])

    def test_generated_complete_csv_45_rows_and_no_fake_python_scores(self):
        import csv
        with CSV.open("r",encoding="utf8",newline="") as file:
            rows=list(csv.DictReader(file))
        self.assertEqual(len(rows),45)
        self.assertEqual({r["task"] for r in rows},set(self.rows))
        self.assertEqual({r["Python_original_task_I0"] for r in rows},{"NOT_RUN"})
        self.assertEqual({r["strict_equal_backend_parity"] for r in rows},{"NOT_PROVEN"})
        for r in rows:
            value=r["frozen_original_author_D0_score"]
            if value:
                self.assertTrue(0<=float(value)<=1)
            else:
                self.assertNotIn(r["task"],{
                    t for t in self.rows if
                    self.rows[t]["frozen_source_only_developer_D0_evidence"]
                    is not None
                })


if __name__=="__main__":
    unittest.main()
