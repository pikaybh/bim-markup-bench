"""v0.24 real original public test_18 Opening+Window D0/I0 native parity tests.

Tests exercise the new trusted declarative original-IFC writer against the
untouched public source and unmodified original author grader; adversarial
graph/provenance/IFC-metadata/STEP mutations fail closed. No model calls.
"""
from __future__ import annotations

import ast
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.unit

from src.runtime.opening_window_delete import (
    preflight_bounded_window_opening, verify_bounded_window_opening,
)
from src.runtime.ifc_mutations import UnsupportedIFCMutation
from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.audit_bibimbap_v024_original_opening import (
    ROOT,TASK_ID,OLD_V023_REPORT,OLD_V023_SHA,OLD_V022_REPORT,OLD_V022_SHA,
    OriginalOpeningParityBlocked, original_public_opening_xml_edit,
    independent_original_native_products_oracle,audit_original_test18,
)
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import XmlSourceEditSession,UnsupportedArm,file_hash
from tools.bibimbap_v024_original_opening_i0 import (
    original_public_opening_window_i0, IndependentOpeningI0Blocked,
)

BASE = Path(r"D:\문서\D__1_Projects\202611")
AUTHOR = BASE/"bibimbap-author-upstream"
DATA = BASE/"bibimbap-author-data"
REPORT=ROOT/"reports/bibimbap_v024_original_test18_opening_window_D0_I0_20261115.json"
REPORT_SHA="a31e74dacdece9924304de6c74c5d9e8769497a8ad68287779ddd4a37bac6a67"
ORIGINAL_IFC_SHA="41dc92e4d667e82f14a0355ac55471429213ae95cad859713c5917e275c354ea"


class OriginalPublic18OpeningWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all45={x["test_id"]:x for x in public_45(AUTHOR,DATA)}
        cls.case=cls.all45[TASK_ID]
        cls.source=DATA/"ifc"/cls.case["original_source_ifc_relpath"]
        cls.source_sha=file_hash(cls.source)
        cls.original=ifcopenshell.open(str(cls.source))
        cls.temp=TemporaryDirectory(prefix="bmb-v024-original18-tests-")
        cls.folder=Path(cls.temp.name)
        cls.d0=XmlSourceEditSession(cls.source,cls.folder/"D0")
        cls.guid,cls.changed=original_public_opening_xml_edit(
            cls.case["public_question"],cls.d0.original_xml)
        cls.window_guid=cls.original.by_guid(cls.guid).HasFillings[0].RelatedBuildingElement.GlobalId
        cls.outcome=cls.d0.call("submit_building_xml",{"xml_text":cls.changed.decode("utf8")})
        cls.i0path=cls.folder/"I0_mm.ifc"
        cls.imperative=original_public_opening_window_i0(
            cls.source,cls.guid,cls.i0path)
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))
        cls.native_m_source=ifcopenshell.open(str(cls.d0.normalized))
        cls.native_m_result=ifcopenshell.open(str(cls.d0.folder/"attempt_01"/"candidate_m.ifc"))
        cls.plan=preflight_bounded_window_opening(
            cls.native_m_source,cls.guid,cls.window_guid)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_01_all45_original_public_cohort_and_source_git_pin(self):
        self.assertEqual(len(self.all45),45)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)
        self.assertEqual(file_hash(self.source),self.source_sha)
        self.assertEqual(self.source_sha,self.case["original_ifc_sha256"])
        self.assertEqual(self.case["category"],"basic")
        self.assertEqual(self.case["crud"],"delete")

    def test_02_historical_frozen_v022_and_v023_results_untouched(self):
        self.assertEqual(file_hash(ROOT/OLD_V022_REPORT),OLD_V022_SHA)
        self.assertEqual(file_hash(ROOT/OLD_V023_REPORT),OLD_V023_SHA)
        self.assertEqual(self.report["pinned_previous_v023_report_sha256"],OLD_V023_SHA)
        self.assertEqual(self.report["pinned_original45_source_roles_report_sha256"],OLD_V022_SHA)

    def test_03_original_public_target_has_single_native_window_filling(self):
        opening=self.original.by_guid(self.guid)
        self.assertEqual(opening.is_a(),"IfcOpeningElement")
        self.assertEqual(len(opening.HasFillings),1)
        self.assertEqual(opening.HasFillings[0].RelatedBuildingElement.is_a(),"IfcWindow")
        self.assertEqual(len(opening.VoidsElements),1)
        self.assertEqual(opening.VoidsElements[0].RelatingBuildingElement.is_a(),"IfcWall")

    def test_04_complete_xml_only_two_existing_state_elements_removed(self):
        xml=self.d0.original_xml.decode("utf8")
        edited=self.changed.decode("utf8")
        self.assertEqual(len(xml.splitlines())-len(edited.splitlines()),2)
        self.assertNotIn(self.guid,edited)
        self.assertNotIn(self.window_guid,edited)
        self.assertNotIn("<Delete",edited)
        self.assertNotIn("<Command",edited)
        self.assertNotIn("<Move",edited)
        self.assertIn("<Wall",edited)
        self.assertIn("<Space",edited)

    def test_05_existing_XML_unsupported_opening_only_still_rejected_by_schema(self):
        with TemporaryDirectory(prefix="bmb-v024-single-opening-") as td:
            s=XmlSourceEditSession(self.source,Path(td)/"s")
            xml=s.original_xml.decode("utf8")
            line=next(l for l in xml.splitlines(keepends=True)
                      if '<Opening ' in l and 'ifcGuid="'+self.guid+'"' in l)
            out=s.call("submit_building_xml",{"xml_text":xml.replace(line,"")})
            self.assertEqual(out["status"],"error")
            self.assertIsNone(s.output_ifc)
            self.assertEqual(s.current_xml,s.original_xml)

    def test_06_actual_native_D0_original_IFC_committed(self):
        self.assertEqual(self.outcome["status"],"ok")
        self.assertTrue(self.outcome["native_ifc_committed"])
        self.assertEqual(self.outcome["compile_status"],
                         "COMMITTED_SCOPED_IFC4X3_TOPOLOGY_EDIT")
        self.assertTrue(self.d0.output_ifc.is_file())
        self.assertEqual(self.outcome["native_ifc_sha256"],ORIGINAL_IFC_SHA)

    def test_07_separate_native_I0_has_no_XML_compiler_imports(self):
        self.assertEqual(self.imperative["status"],
                         "INDEPENDENT_DEVELOPER_NATIVE_OPENING_AND_WINDOW_DELETE")
        self.assertTrue(self.imperative["public_opening_absent"])
        self.assertTrue(self.imperative["original_filling_window_absent"])
        source=(ROOT/"tools/bibimbap_v024_original_opening_i0.py").read_text(encoding="utf8")
        imports=[]
        for node in ast.walk(ast.parse(source)):
            if isinstance(node,ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node,ast.ImportFrom):
                imports.append(node.module or "")
        self.assertFalse(any(x.startswith("src.runtime") for x in imports))
        self.assertNotIn("compile_declarative_xml",source)

    def test_08_original_D0_I0_FULL_native_ifc_sha_byte_equal(self):
        self.assertEqual(file_hash(self.d0.output_ifc),file_hash(self.i0path))
        self.assertEqual(file_hash(self.i0path),ORIGINAL_IFC_SHA)
        self.assertEqual(self.report["original_D0_full_native_IFC_sha256"],ORIGINAL_IFC_SHA)
        self.assertEqual(self.report["original_I0_full_native_IFC_sha256"],ORIGINAL_IFC_SHA)

    def test_09_independent_native_product_oracle_both_arms(self):
        d=independent_original_native_products_oracle(
            self.source,self.d0.output_ifc,self.guid,self.window_guid)
        i=independent_original_native_products_oracle(
            self.source,self.i0path,self.guid,self.window_guid)
        self.assertEqual(d,i)
        self.assertEqual(d["original_IfcProducts"],43)
        self.assertEqual(d["candidate_IfcProducts"],41)
        self.assertTrue(d["all_other_original_IfcProduct_GUIDs_and_classes_preserved"])

    def test_10_original_author_grader_identical_0_5_not_full(self):
        d=grade_author(AUTHOR,self.source,self.d0.output_ifc,TASK_ID)
        i=grade_author(AUTHOR,self.source,self.i0path,TASK_ID)
        self.assertEqual(d,i)
        self.assertEqual(d["status"],"AUTHOR_SCORED")
        self.assertEqual(d["original_author_score"],.5)
        self.assertEqual(d["original_author_metrics"],
                         {"object_not_exists":1.0,"integrity_constraint":0.0})
        self.assertFalse(d["original_author_full_mark"])
        self.assertEqual(self.report["original_author_grader_D0"],d)
        self.assertEqual(self.report["original_author_grader_I0"],i)

    def test_11_native_original_root_STEP_integrity_gate(self):
        count=verify_bounded_window_opening(
            self.native_m_source,self.native_m_result,self.plan)
        self.assertGreater(count,250)
        self.assertEqual(len(self.plan.deleted_root_guids),10)
        self.assertEqual(len(self.plan.modified_root_guids),2)
        self.assertEqual(len(self.plan.modified_layer_step_ids),1)

    def test_12_native_original_window_opening_product_preservation(self):
        self.assertIsNone(next((x for x in self.native_m_result.by_type("IfcOpeningElement")
                      if x.GlobalId==self.guid),None))
        self.assertIsNone(next((x for x in self.native_m_result.by_type("IfcWindow")
                      if x.GlobalId==self.window_guid),None))
        self.assertEqual(len(self.native_m_source.by_type("IfcProduct")),43)
        self.assertEqual(len(self.native_m_result.by_type("IfcProduct")),41)

    def test_13_native_unknown_GUID_or_wrong_original_class_rejected(self):
        f=ifcopenshell.open(str(self.d0.normalized))
        for first,second in (
            ("0"*22,self.window_guid),
            (f.by_type("IfcWall")[0].GlobalId,self.window_guid),
            (self.guid,f.by_type("IfcDoor")[0].GlobalId),
        ):
            with self.subTest(first=first,second=second):
                with self.assertRaises(UnsupportedIFCMutation):
                    preflight_bounded_window_opening(f,first,second)

    def test_14_native_shared_PropertySet_membership_rejected(self):
        f=ifcopenshell.open(str(self.d0.normalized))
        window=f.by_guid(self.window_guid)
        prop=next(x for x in f.get_inverse(window)
                  if x.is_a("IfcRelDefinesByProperties"))
        other=f.by_type("IfcWall")[0]
        prop.RelatedObjects=tuple(list(prop.RelatedObjects)+[other])
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_bounded_window_opening(f,self.guid,self.window_guid)

    def test_15_native_unexpected_space_boundary_dependency_rejected(self):
        f=ifcopenshell.open(str(self.d0.normalized))
        window=f.by_guid(self.window_guid)
        f.create_entity(
            "IfcRelSpaceBoundary",GlobalId=ifcopenshell.guid.new(),
            RelatingSpace=f.by_type("IfcSpace")[0],
            RelatedBuildingElement=window,
            PhysicalOrVirtualBoundary="PHYSICAL",
            InternalOrExternalBoundary="INTERNAL",
        )
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_bounded_window_opening(f,self.guid,self.window_guid)

    def test_16_native_shared_type_assignment_rejected(self):
        f=ifcopenshell.open(str(self.d0.normalized))
        window=f.by_guid(self.window_guid)
        typ=next(x for x in f.get_inverse(window)
                 if x.is_a("IfcRelDefinesByType"))
        typ.RelatedObjects=tuple(list(typ.RelatedObjects)+[f.by_type("IfcWall")[0]])
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_bounded_window_opening(f,self.guid,self.window_guid)

    def test_17_native_containment_missing_target_rejected(self):
        f=ifcopenshell.open(str(self.d0.normalized))
        window=f.by_guid(self.window_guid)
        rel=next(x for x in f.get_inverse(window)
                 if x.is_a("IfcRelContainedInSpatialStructure"))
        rel.RelatedElements=tuple(p for p in rel.RelatedElements if p!=window)
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_bounded_window_opening(f,self.guid,self.window_guid)

    def test_18_native_forged_unrelated_root_name_rejected(self):
        source=ifcopenshell.open(str(self.d0.normalized))
        candidate=ifcopenshell.open(str(self.d0.folder/"attempt_01"/"candidate_m.ifc"))
        candidate.by_type("IfcWall")[0].Name="UNAUTHORIZED_ORIGINAL_ROOT_REWRITE"
        with self.assertRaises(UnsupportedIFCMutation):
            verify_bounded_window_opening(source,candidate,self.plan)

    def test_19_native_unrelated_product_removal_rejected(self):
        source=ifcopenshell.open(str(self.d0.normalized))
        candidate=ifcopenshell.open(str(self.d0.folder/"attempt_01"/"candidate_m.ifc"))
        ifcopenshell.api.root.remove_product(
            candidate,product=candidate.by_type("IfcDoor")[0])
        with self.assertRaises(UnsupportedIFCMutation):
            verify_bounded_window_opening(source,candidate,self.plan)

    def test_20_native_unrelated_presentation_layer_member_change_rejected(self):
        source=ifcopenshell.open(str(self.d0.normalized))
        candidate=ifcopenshell.open(str(self.d0.folder/"attempt_01"/"candidate_m.ifc"))
        layer=candidate.by_id(next(iter(self.plan.modified_layer_step_ids)))
        layer.AssignedItems=tuple(layer.AssignedItems[:-1])
        with self.assertRaises(UnsupportedIFCMutation):
            verify_bounded_window_opening(source,candidate,self.plan)

    def test_21_native_classifier_member_modification_rejected(self):
        source=ifcopenshell.open(str(self.d0.normalized))
        candidate=ifcopenshell.open(str(self.d0.folder/"attempt_01"/"candidate_m.ifc"))
        rel=next(x for x in candidate.by_type("IfcRelAssociatesClassification")
                 if x.GlobalId in self.plan.modified_root_guids)
        rel.Name="FORGED_CLASSIFIER_NAME"
        with self.assertRaises(UnsupportedIFCMutation):
            verify_bounded_window_opening(source,candidate,self.plan)

    def test_22_unrelated_walls_not_allowed_in_same_xml_submission(self):
        with TemporaryDirectory(prefix="bmb-v024-edit-wall-with-pair-") as td:
            s=XmlSourceEditSession(self.source,Path(td)/"D0")
            xml=self.changed.decode("utf8")
            line=next(l for l in xml.splitlines(keepends=True) if "<Wall " in l)
            attempt=xml.replace(line,"")
            out=s.call("submit_building_xml",{"xml_text":attempt})
            self.assertEqual(out["status"],"error")
            self.assertIsNone(s.output_ifc)
            self.assertEqual(s.current_xml,s.original_xml)

    def test_23_unrelated_window_not_allowed_in_same_xml_submission(self):
        with TemporaryDirectory(prefix="bmb-v024-edit-door-with-pair-") as td:
            s=XmlSourceEditSession(self.source,Path(td)/"D0")
            xml=self.changed.decode("utf8")
            line=next(l for l in xml.splitlines(keepends=True) if "<Door " in l)
            attempt=xml.replace(line,"")
            out=s.call("submit_building_xml",{"xml_text":attempt})
            self.assertEqual(out["status"],"error")
            self.assertIsNone(s.output_ifc)
            self.assertEqual(s.current_xml,s.original_xml)

    def test_24_forged_original_guid_or_multiple_public_ids_refused(self):
        with self.assertRaises(OriginalOpeningParityBlocked):
            original_public_opening_xml_edit(
                "Delete opening with id "+"Z"*22,self.d0.original_xml)
        with self.assertRaises(OriginalOpeningParityBlocked):
            original_public_opening_xml_edit(
                self.case["public_question"]+" and "+"Z"*22,self.d0.original_xml)

    def test_25_original_ifc2x3_and_ifc4_input_admission_still_refused(self):
        for task in ("geometry_test_03","geometry_test_05"):
            c=self.all45[task]
            path=DATA/"ifc"/c["original_source_ifc_relpath"]
            with self.subTest(task=task),TemporaryDirectory() as td:
                with self.assertRaises(UnsupportedArm):
                    XmlSourceEditSession(path,Path(td)/"D0")
                self.assertEqual(file_hash(path),c["original_ifc_sha256"])

    def test_26_original_public_source_author_and_report_checksum_unchanged(self):
        self.assertEqual(file_hash(self.source),self.source_sha)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)
        self.assertEqual(file_hash(REPORT),REPORT_SHA)
        self.assertEqual(self.report["original_native_IFC_sha256"],self.source_sha)

    def test_27_original_public_target_GUID_not_in_committed_reports(self):
        report_text=REPORT.read_text(encoding="utf8")
        self.assertNotIn(self.guid,report_text)
        self.assertNotIn(self.window_guid,report_text)
        self.assertNotIn(self.case["public_question"],report_text)
        self.assertFalse(self.report["original_raw_IFC_GTs_or_original_public_target_GUID_committed"])

    def test_28_real_second_audit_reproduces_full_sha_and_original_grades(self):
        again=audit_original_test18(ROOT,AUTHOR,DATA)
        self.assertEqual(again,self.report)
        b=(json.dumps(again,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(sha256(b).hexdigest(),REPORT_SHA)

    def test_29_cumulative_honest_developer_only_outcomes(self):
        self.assertEqual(self.report["historical_prior_developer_D0_I0_original_native_byte_equal"],6)
        self.assertEqual(self.report["new_cumulative_developer_D0_I0_original_native_byte_equal"],7)
        self.assertEqual(self.report["historical_prior_developer_original_author_callable_pairs"],4)
        self.assertEqual(self.report["new_cumulative_developer_original_author_callable_pairs"],5)
        self.assertEqual(self.report["other_original_same_protocol_cases_not_proven"],38)
        self.assertEqual(self.report["real_model_calls"],0)
        self.assertEqual(self.report["paid_model_cost_usd"],0)
        self.assertFalse(self.report["original_author_full_mark"])
        self.assertFalse(self.report["all_original45_write_information_capability_parity_proven"])
        self.assertFalse(self.report["causal_representation_performance_conclusion_supported"])

    def test_30_original_author_integrity_counts_dependant_window_non_target(self):
        import ifcopenshell.util.element
        public_opening=self.original.by_guid(self.guid)
        self.assertTrue(self.report["original_target_has_native_IfcRelVoidsElement"])
        self.assertFalse(self.report["original_target_has_no_native_get_container"])
        self.assertIsNotNone(ifcopenshell.util.element.get_container(public_opening))
        self.assertIsNone(next((x for x in ifcopenshell.open(str(self.i0path)).by_type("IfcWindow")
                                if x.GlobalId==self.window_guid),None))
        self.assertFalse(self.report["original_author_scorer_or_input_modified"])


if __name__=="__main__":unittest.main()
