"""v0.22 actual original BIBIMBAP 45-task IFC/source role and XML admission QA.

Selected real native IFC samples are read-only. No model, scorer, Docker,
IFC mutation, hidden target lookup or original dataset change.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
import ast

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import (
    XmlSourceEditSession, UnsupportedArm, file_hash,
)
from tools.bibimbap_v022_task_relevant_source_role_audit import (
    ROOT, FROZEN_V013, FROZEN_V020, FROZEN_V021,
    PublicRoleAuditBlocked, audit, read_frozen_json,
    source_native_product_maps, classify_original45,
)

BASE = Path(r"D:\문서\D__1_Projects\202611")
AUTHOR = BASE / "bibimbap-author-upstream"
DATA = BASE / "bibimbap-author-data"
FROZEN = ROOT / "reports/bibimbap_v022_original45_task_relevant_roles_and_xml_input_20261115.json"
REPORT_SHA = "f606994defa7517f898e22ee6e39d5e82da6dc40288c1b38cec25c98b7cd492e"
ROLE_GAPS = {
    "geometry_test_18","geometry_test_19","geometry_test_20","test_20",
    "topological_test_01","topological_test_03","topological_test_14",
    "topological_test_18","topological_test_20",
}
EXPLICIT_GAPS = {"topological_test_01","topological_test_20"}
SCHEMA_BLOCKS = {"geometry_test_03","geometry_test_04","geometry_test_05"}


class V022Original45SourceRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not FROZEN.is_file():
            raise unittest.SkipTest("Frozen original-source v022 report not installed")
        cls.public = public_45(AUTHOR, DATA)
        cls.v13 = read_frozen_json(ROOT, FROZEN_V013)
        cls.v20 = read_frozen_json(ROOT, FROZEN_V020)
        cls.v21 = read_frozen_json(ROOT, FROZEN_V021)
        cls.sources = source_native_product_maps(cls.public, DATA, cls.v13)
        cls.report = json.loads(FROZEN.read_text(encoding="utf8"))
        cls.by_id = {x["task_id"]: x for x in cls.report[
            "all45_per_task_actual_source_role_and_admission_rows"]}

    def test_01_original_author_data_sha_and_all45_preserved(self):
        self.assertEqual(_head(AUTHOR), AUTHOR_SHA)
        self.assertEqual(_head(DATA), DATA_SHA)
        self.assertEqual(self.report["original_public_task_denominator"],45)
        self.assertEqual(len(self.public),45)
        self.assertEqual(len(self.by_id),45)
        self.assertEqual(self.report["original_crud_distribution"],
                         {"create":15,"update":15,"delete":15})
        self.assertEqual(self.report["original_category_distribution"],
                         {"basic":15,"geometry":15,"topological":15})

    def test_02_all_31_actual_IFC_full_native_guid_maps_match_frozen_oracle(self):
        self.assertEqual(len(self.sources),31)
        self.assertEqual(self.report["actual_unique_original_source_IFC_file_count"],31)
        self.assertEqual(
            self.report["actual_original_source_IfcProduct_catalogs_exactly_match_independent_v013"],31)
        self.assertEqual(self.report["actual_unique_native_IfcProduct_total"],480)
        self.assertEqual(
            sum(len(source["all_actual_native_source"]) for source in self.sources.values()),480)
        for digest,source in self.sources.items():
            with self.subTest(source_digest=digest[:8]):
                self.assertEqual(
                    set(source["all_actual_native_source"]),
                    set(source["frozen_typed_XML_subset"]) |
                    set(source["frozen_opaque_readonly_subset"]))
                self.assertFalse(
                    set(source["frozen_typed_XML_subset"]) &
                    set(source["frozen_opaque_readonly_subset"]))

    def test_03_frozen_prior_reports_sha_and_recomputed_v022_json(self):
        self.assertEqual(file_hash(FROZEN),REPORT_SHA)
        for frozen in (FROZEN_V013,FROZEN_V020,FROZEN_V021):
            with self.subTest(report=frozen[0]):
                self.assertEqual(file_hash(ROOT/frozen[0]),frozen[1])
        fresh = classify_original45(self.public,self.sources,self.v13,self.v20,self.v21)
        self.assertEqual(fresh,self.report)
        encoded=(json.dumps(fresh,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
        self.assertEqual(sha256(encoded).hexdigest(),REPORT_SHA)

    def test_04_actual_public_named_IFC_source_guids_never_missing(self):
        self.assertEqual(
            self.report["original45_explicit_named_public_original_product_guid_missing_native_source"],0)
        self.assertTrue(all(x["explicit_public_named_guids_missing_original_source"]==0
                            for x in self.by_id.values()))

    def test_05_exact_nine_required_role_editable_XML_gaps(self):
        actual={t for t,x in self.by_id.items()
                if x["required_roles_with_missing_editable_XML_objects"]}
        self.assertEqual(actual,ROLE_GAPS)
        self.assertEqual(self.report["original45_required_source_role_editable_XML_incomplete"],9)
        self.assertEqual(self.report["original45_required_source_role_editable_XML_complete"],36)
        for task in actual:
            self.assertFalse(self.by_id[task]["all_required_roles_and_explicit_refs_present_editable_XML"])

    def test_06_exact_two_public_named_source_GUID_gaps_not_hidden_targets(self):
        actual={t for t,x in self.by_id.items()
                if x["explicit_public_named_guids_missing_editable_XML"]>0}
        self.assertEqual(actual,EXPLICIT_GAPS)
        self.assertEqual(self.report["original45_explicit_named_public_product_guids_missing_editable_XML_cases"],2)
        self.assertEqual(
            {t:self.by_id[t]["explicit_public_named_guids_missing_editable_XML"] for t in actual},
            {"topological_test_01":1,"topological_test_20":2})

    def test_07_three_actual_schema_rejections_exact_public_names(self):
        actual={t for t,x in self.by_id.items()
                if x["current_direct_XML_session_source_admission"].startswith(
                    "DIRECT_XML_SESSION_REJECTS")}
        self.assertEqual(actual,SCHEMA_BLOCKS)
        self.assertEqual(self.report["original45_current_XML_input_schema_or_unit_admission_rejects"],3)
        self.assertEqual(self.report["original45_input_schema_and_unit_admissible_not_proven_writable"],42)
        self.assertEqual(self.by_id["geometry_test_03"]["original_ifc_schema"],"IFC2X3")
        self.assertEqual(self.by_id["geometry_test_04"]["original_ifc_schema"],"IFC2X3")
        self.assertEqual(self.by_id["geometry_test_05"]["original_ifc_schema"],"IFC4")

    def test_08_real_current_XML_session_ctor_rejects_three_sources_without_edit(self):
        public = {x["test_id"]:x for x in self.public}
        for task_id in sorted(SCHEMA_BLOCKS):
            task=public[task_id]
            source=DATA/"ifc"/task["original_source_ifc_relpath"]
            previous=file_hash(source)
            with self.subTest(task=task_id),TemporaryDirectory(prefix="v022-real-schema-") as temp:
                with self.assertRaisesRegex(
                    UnsupportedArm,
                    "XML source compiler only accepts IFC4X3"):
                    XmlSourceEditSession(source,Path(temp)/"xml_session")
                self.assertEqual(file_hash(source),previous)

    def test_09_42_schema_admissible_not_equivalent_write_capability(self):
        self.assertEqual(self.report["original45_complete_native_write_capability_equivalence_proven"],0)
        self.assertEqual(self.report["original45_complete_original_IFC_semantic_information_equivalence_proven"],0)
        self.assertEqual(self.report["new_actual_XML_native_write_probes_in_this_version"],0)
        self.assertTrue(all(x["full_D_I_native_write_capability_equivalence"]=="NOT_PROVEN"
                            for x in self.by_id.values()))
        for t,x in self.by_id.items():
            if t not in SCHEMA_BLOCKS:
                self.assertEqual(x["current_direct_XML_session_source_admission"],
                                 "SCHEMA_AND_UNIT_ADMISSIBLE_PROJECTION_WRITE_NOT_PROVEN")

    def test_10_original_source_required_role_counts_match_frozen_native_typed(self):
        for t,row in self.by_id.items():
            with self.subTest(task=t):
                count=row["required_role_visibility_counts"]
                self.assertEqual(set(count),set(row["required_public_source_roles"]))
                for role,val in count.items():
                    self.assertGreaterEqual(val["actual_original_native_count"],
                                            val["existing_frozen_editable_typed_XML_count"])
                    self.assertEqual(
                        val["required_role_missing_editable_IfcProducts_count"],
                        val["actual_original_native_count"] -
                        val["existing_frozen_editable_typed_XML_count"])

    def test_11_whole_native_IfcProduct_count_exceeds_typed_every_task(self):
        self.assertEqual(
            self.report["original45_current_safe_typed_XML_omits_some_native_products"],45)
        for row in self.by_id.values():
            self.assertGreater(row["native_IfcProducts_outside_editable_typed_XML"],0)

    def test_12_prior_matched_D0_I0_developer_evidence_not_inflated(self):
        self.assertEqual(self.report["original45_developer_native_D0_I0_byte_equivalence_previous"],5)
        self.assertEqual(self.report["original45_original_author_scorable_both_developer_arms_previous"],3)
        self.assertEqual(self.report["original45_pinned_original_author_scorer_missing_reference_previous"],2)
        self.assertEqual(self.report["original45_other_same_protocol_edit_cases_not_evaluated"],40)
        self.assertEqual(sum(row["previously_developer_proven_D0_I0_native_bytes_equal"]
                             for row in self.by_id.values()),5)

    def test_13_new_models_paid_grading_and_source_writes_zero(self):
        self.assertEqual(self.report["new_real_LLM_trials_or_scores"],0)
        self.assertEqual(self.report["new_provider_paid_USD"],0)
        self.assertEqual(self.report["new_original_public_scorer_grades_this_version"],0)
        self.assertTrue(self.report["read_only_actual_original_IFC_no_mutation"])
        self.assertFalse(self.report["actual_pure_representation_causal_LLM_launch_permitted"])

    def test_14_report_contains_no_original_named_guid_or_full_questions(self):
        text=FROZEN.read_text(encoding="utf8")
        for row in self.public:
            self.assertNotIn(row["public_question"],text)
        self.assertTrue(self.report["explicit_guids_raw_original_catalog_and_questions_NOT_in_report"])
        self.assertNotIn("original_native_product_class_by_guid",self.report)

    def test_15_duplicate_original_public_task_id_fails(self):
        changed=deepcopy(self.public)
        changed[0]["test_id"]=changed[1]["test_id"]
        with self.assertRaises(PublicRoleAuditBlocked):
            classify_original45(changed,self.sources,self.v13,self.v20,self.v21)

    def test_16_missing_public_task_fails(self):
        with self.assertRaises(PublicRoleAuditBlocked):
            classify_original45(self.public[:-1],self.sources,self.v13,self.v20,self.v21)

    def test_17_public_question_sha_tampering_fails(self):
        changed=deepcopy(self.public)
        changed[0]["public_question_sha256"]="0"*64
        with self.assertRaises(PublicRoleAuditBlocked):
            classify_original45(changed,self.sources,self.v13,self.v20,self.v21)

    def test_18_public_target_missing_from_frozen_named_guid_evidence_fails(self):
        changed=deepcopy(self.public)
        changed_map={x["test_id"]:x for x in changed}
        changed_map["test_15"]["public_question"]="Change 0AAAAAAAAAAAAAAAAAAAAA"
        with self.assertRaises(PublicRoleAuditBlocked):
            classify_original45(changed,self.sources,self.v13,self.v20,self.v21)

    def test_19_forged_typed_source_map_missing_original_class_fails(self):
        changed=deepcopy(self.sources)
        first_sha=next(iter(changed))
        changed[first_sha]["all_actual_native_source"]={"Z"*22:"IfcWall"}
        with self.assertRaises(PublicRoleAuditBlocked):
            classify_original45(self.public,changed,self.v13,self.v20,self.v21)

    def test_20_forged_role_coverage_from_frozen_oracle_fails(self):
        changed=deepcopy(self.v13)
        item=next(x for x in changed["original45_task_readonly_vs_native_write_status"]
                  if x["original_public_task_id"]=="topological_test_14")
        item["v013_original_role_readonly_vs_typed_coverage"]["Beam"]["safe_typed_XML_existing_count"]=4
        with self.assertRaises(PublicRoleAuditBlocked):
            classify_original45(self.public,self.sources,changed,self.v20,self.v21)

    def test_21_forged_matched_developer_edit_counter_fails(self):
        changed=deepcopy(self.v20)
        changed["original45_developer_both_arm_native_IFC_byte_equivalence"]=6
        with self.assertRaises(PublicRoleAuditBlocked):
            classify_original45(self.public,self.sources,self.v13,changed,self.v21)

    def test_22_forged_v021_real_LLM_experiment_fails(self):
        changed=deepcopy(self.v21)
        changed["new_real_LLM_trial_calls"]=1
        with self.assertRaises(PublicRoleAuditBlocked):
            classify_original45(self.public,self.sources,self.v13,self.v20,changed)

    def test_23_corrupt_frozen_v13_sha_rejected(self):
        with TemporaryDirectory(prefix="v022-corrupt-pinned-report-") as d:
            root=Path(d)
            target=root/FROZEN_V013[0]
            target.parent.mkdir(parents=True)
            target.write_bytes((ROOT/FROZEN_V013[0]).read_bytes()+b"\n")
            with self.assertRaises(PublicRoleAuditBlocked):
                read_frozen_json(root,FROZEN_V013)

    def test_24_actual_source_corrupt_copy_sha_rejected_without_original_mutation(self):
        task=self.public[0]
        source=DATA/"ifc"/task["original_source_ifc_relpath"]
        prior=file_hash(source)
        with TemporaryDirectory(prefix="v022-corrupt-public-source-") as d:
            root=Path(d)
            temp=root/"ifc"/task["original_source_ifc_relpath"]
            temp.parent.mkdir(parents=True)
            shutil.copyfile(source,temp)
            temp.write_bytes(temp.read_bytes()+b"\n")
            with self.assertRaises(PublicRoleAuditBlocked):
                source_native_product_maps([task],root,self.v13)
        self.assertEqual(file_hash(source),prior)

    def test_25_report_recomputed_from_real_original_source_IFCs_identical(self):
        recomputed=audit(ROOT,AUTHOR,DATA)
        self.assertEqual(recomputed,self.report)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)

    def test_26_new_auditor_does_not_import_hidden_grader_or_native_mutator(self):
        path=ROOT/"tools"/"bibimbap_v022_task_relevant_source_role_audit.py"
        s=path.read_text(encoding="utf8")
        tree=ast.parse(s)
        modules=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                modules += [x.name for x in node.names]
            if isinstance(node,ast.ImportFrom):
                modules.append(node.module or "")
        self.assertNotIn("ifcopenshell.api",modules)
        self.assertNotIn("tools.bibimbap_author_worker",modules)
        self.assertNotIn("grade_author(",s)
        self.assertNotIn("compile_declarative_xml(",s)


if __name__ == "__main__":
    unittest.main()
