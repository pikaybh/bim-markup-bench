"""v0.28 genuine original PUBLIC test_11 Wall +90° center rotation QA.

Original IFC4X3 public wall and original unchanged author scorer execute in tests;
no hidden answer inventory, real LLM model calls, or paid inference.
The source is never modified. Trusted D0 compiler is opt-in and source pinned;
default-off regression remains deliberately denied.
"""
from __future__ import annotations

import ast
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell
import ifcopenshell.guid
import ifcopenshell.util.placement

from src.runtime.ifc_mutations import UnsupportedIFCMutation
from src.runtime.original_wall_rotation import (
    plan_original_wall_rotation,rotation_xml_plan,verify_wall_rotation,
    PINNED_ORIGINAL_NORMALIZED_SHA,
)
from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import XmlSourceEditSession,UnsupportedArm,file_hash
from tools.audit_bibimbap_v028_original_wall_rotation import (
    ROOT,TASK_ID,PREVIOUS_REPORT_SHA,
    OriginalWallRotateAuditBlocked,
    full_public_XML_center_rotation,
    independently_verify_original_native_products,
    audit_original_public_test11,
)
from tools.bibimbap_v028_original_wall_rotation_i0 import (
    independent_public_wall_center_rotate_i0,OriginalRotationI0Blocked,
)

BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports/bibimbap_v028_original_test11_wall_center_rotate_D0_I0_native_parity_20261116.json"
REPORT_SHA="6818e6bfa2990f8dc9ee3730ba9a7197c72d6f3131af9bae9fbda8d22fefd8cb"
FULL_NATIVE_IFC_SHA="5af3a2bd423c101e63cacad0a53342761b4496a0e9337ed0ce5b4b6d2a13f755"


class OriginalPublicTest11WallCenterRotateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cohort={x["test_id"]:x for x in public_45(AUTHOR,DATA)}
        cls.case=cls.cohort[TASK_ID]
        cls.source=DATA/"ifc"/cls.case["original_source_ifc_relpath"]
        cls.source_sha=file_hash(cls.source)
        cls.temp=TemporaryDirectory(prefix="bmb-v028-original-test11-")
        cls.folder=Path(cls.temp.name)
        cls.d0=XmlSourceEditSession(cls.source,cls.folder/"D0")
        cls.guid,cls.updated=full_public_XML_center_rotation(
            cls.case["public_question"],cls.d0.original_xml)
        cls.plan=plan_original_wall_rotation(cls.d0.normalized,cls.guid)
        with patch.dict(os.environ,{"BMB_V028_ORIGINAL_WALL_CENTER_ROTATE":"1"}):
            cls.d0_reply=cls.d0.call(
                "submit_building_xml",{"xml_text":cls.updated.decode("utf8")})
        cls.metric=cls.d0.folder/"attempt_01"/"candidate_m.ifc"
        cls.i0path=cls.folder/"independent_original_I0_mm.ifc"
        cls.i0_result=independent_public_wall_center_rotate_i0(
            cls.source,cls.guid,cls.i0path)
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def _tampered_native(self,edit):
        f=ifcopenshell.open(str(self.metric))
        edit(f)
        file=self.folder/("forged-"+str(len(list(self.folder.glob("forged-*"))))+".ifc")
        f.write(str(file))
        return file

    def _new_session(self,txt):
        with TemporaryDirectory(prefix="bmb-v028-negative-xml-") as td:
            session=XmlSourceEditSession(self.source,Path(td)/"D0")
            with patch.dict(os.environ,{"BMB_V028_ORIGINAL_WALL_CENTER_ROTATE":"1"}):
                response=session.call("submit_building_xml",{"xml_text":txt})
            self.assertEqual(response["status"],"error")
            self.assertIsNone(session.output_ifc)
            self.assertEqual(session.original_xml,session.current_xml)

    def _line(self):
        return next(line for line in self.d0.original_xml.decode("utf8").splitlines(keepends=True)
                    if '<Wall ' in line and 'ifcGuid="'+self.guid+'"' in line)

    def test_01_original_public_population_frozen(self):
        self.assertEqual(len(self.cohort),45)
        self.assertEqual(self.case["crud"],"update")
        self.assertEqual(self.case["category"],"basic")
        self.assertEqual(self.source_sha,self.case["original_ifc_sha256"])
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)

    def test_02_predecessor_reports_immutable(self):
        for rel,sha in PREVIOUS_REPORT_SHA.items():
            with self.subTest(rel=rel):
                self.assertEqual(file_hash(ROOT/rel),sha)

    def test_03_target_native_IFC_is_original_unique_straight_wall(self):
        self.assertEqual(file_hash(self.d0.normalized),PINNED_ORIGINAL_NORMALIZED_SHA)
        f=ifcopenshell.open(str(self.d0.normalized))
        wall=f.by_guid(self.guid)
        self.assertTrue(wall.is_a("IfcWall"))
        self.assertFalse(wall.HasOpenings or wall.ConnectedFrom or wall.ConnectedTo)
        self.assertEqual(len(wall.ProvidesBoundaries),0)
        self.assertEqual(self.plan.axis_local_length,5.0)

    def test_04_original_native_source_refdirection_shared_by_fourteen(self):
        f=ifcopenshell.open(str(self.d0.normalized))
        self.assertEqual(f.get_total_inverses(
            f.by_id(self.plan.shared_direction_id)),14)
        self.assertEqual(len(f.get_inverse(
            f.by_id(self.plan.point_id))),1)

    def test_05_D0_only_four_XML_endpoint_attributes_changed(self):
        original=self.d0.original_xml.decode("utf8")
        changed=self.updated.decode("utf8")
        self.assertEqual(len(original.splitlines()),len(changed.splitlines()))
        self.assertEqual(sum(x!=y for x,y in zip(original.splitlines(),changed.splitlines())),1)
        self.assertIn(self.guid,changed)
        self.assertNotIn("<Command",changed)
        self.assertNotIn("<Delete",changed)
        self.assertNotIn("<Move",changed)
        self.assertEqual(changed.count("<Wall "),original.count("<Wall "))

    def test_06_XML_original_center_unchanged_and_angle_rotated(self):
        l=self._line()
        after=next(q for q in self.updated.decode("utf8").splitlines()
                   if 'ifcGuid="'+self.guid+'"' in q)
        def x(line,key):
            return float(re.search(r'\b'+key+r'="([^"]+)"',line).group(1))
        old=[x(l,n) for n in ("x1","y1","x2","y2")]
        new=[x(after,n) for n in ("x1","y1","x2","y2")]
        self.assertAlmostEqual((old[0]+old[2])/2,(new[0]+new[2])/2)
        self.assertAlmostEqual((old[1]+old[3])/2,(new[1]+new[3])/2)
        self.assertAlmostEqual(new[0],5.0)
        self.assertAlmostEqual(new[1],16.4952)
        self.assertAlmostEqual(new[2],5.0)
        self.assertAlmostEqual(new[3],11.4952)

    def test_07_real_D0_trusted_source_XML_IFC_transaction_committed(self):
        self.assertEqual(self.d0_reply["status"],"ok")
        self.assertTrue(self.d0_reply["native_ifc_committed"])
        self.assertEqual(self.d0_reply["compile_status"],"COMMITTED_SCOPED_IFC4X3_WALL_EDIT")
        self.assertTrue(self.d0.output_ifc.is_file())
        self.assertEqual(self.d0_reply["native_ifc_sha256"],FULL_NATIVE_IFC_SHA)

    def test_08_separate_imperative_I0_does_not_import_D0_compiler(self):
        self.assertEqual(self.i0_result["status"],
                         "INDEPENDENT_IMPERATIVE_ORIGINAL_PUBLIC_WALL_90_CENTER")
        self.assertTrue(self.i0_result["original_target_wall_preserved"])
        source=(ROOT/"tools/bibimbap_v028_original_wall_rotation_i0.py").read_text(encoding="utf8")
        imports=[]
        for node in ast.walk(ast.parse(source)):
            if isinstance(node,ast.Import):
                imports.extend(x.name for x in node.names)
            elif isinstance(node,ast.ImportFrom):
                imports.append(node.module or "")
        self.assertFalse(any(x.startswith("src.runtime") for x in imports))
        self.assertNotIn("compile_declarative_xml",source)
        self.assertNotIn("original_wall_rotation",source)

    def test_09_D0_I0_original_entire_IFC_bytes_equal(self):
        self.assertEqual(file_hash(self.d0.output_ifc),file_hash(self.i0path))
        self.assertEqual(file_hash(self.i0path),FULL_NATIVE_IFC_SHA)
        self.assertEqual(self.report["D0_complete_original_native_IFC_SHA256"],FULL_NATIVE_IFC_SHA)
        self.assertEqual(self.report["I0_complete_original_native_IFC_SHA256"],FULL_NATIVE_IFC_SHA)

    def test_10_original_author_scorer_full_marks_both(self):
        grade_d=grade_author(AUTHOR,self.source,self.d0.output_ifc,TASK_ID)
        grade_i=grade_author(AUTHOR,self.source,self.i0path,TASK_ID)
        self.assertEqual(grade_d,grade_i)
        self.assertEqual(grade_d["original_author_score"],1.0)
        self.assertTrue(grade_d["original_author_full_mark"])
        self.assertEqual(grade_d["original_author_metrics"],{
            "right_location":1.0,"right_dimensions":1.0,"integrity_constraint":1.0})
        self.assertEqual(grade_d,self.report["unchanged_original_author_D0"])

    def test_11_independent_original_native_all_IfcRoots_and_IfcProducts(self):
        oracle=independently_verify_original_native_products(
            self.source,self.d0.output_ifc,self.guid)
        self.assertEqual(oracle["original_native_IfcProduct_count"],43)
        self.assertTrue(oracle["original_native_Root_GUIDs_classes_unchanged"])
        self.assertTrue(oracle["original_native_all_Product_GUIDs_classes_unchanged"])

    def test_12_metric_native_STEP_only_two_original_placement_steps_modified(self):
        self.assertEqual(
            verify_wall_rotation(self.d0.normalized,self.metric,self.plan),
            self.plan.source_root_count)
        original=ifcopenshell.open(str(self.d0.normalized))
        result=ifcopenshell.open(str(self.metric))
        before={x.id():str(x) for x in original}
        after={x.id():str(x) for x in result}
        self.assertEqual(len(after.keys()-before.keys()),1)
        self.assertEqual(
            {eid for eid in before.keys()&after.keys() if before[eid]!=after[eid]},
            {self.plan.point_id,self.plan.relative_placement_id})

    def test_13_original_shared_RefDirection_preserved_other_thirteen(self):
        original=ifcopenshell.open(str(self.d0.normalized))
        result=ifcopenshell.open(str(self.metric))
        old=original.by_id(self.plan.shared_direction_id)
        new=result.by_id(self.plan.shared_direction_id)
        self.assertEqual(str(old),str(new))
        self.assertEqual(original.get_total_inverses(old),14)
        self.assertEqual(result.get_total_inverses(new),13)

    def test_14_original_target_wall_orientation_is_physically_plus_90(self):
        native=ifcopenshell.open(str(self.metric)).by_guid(self.guid)
        matrix=ifcopenshell.util.placement.get_local_placement(native.ObjectPlacement)
        for actual,expected in zip(matrix[:3,0],(0.,-1.,0.)):
            self.assertAlmostEqual(float(actual),expected,places=7)
        for actual,expected in zip(matrix[:3,3],(5.,16.4952,0.)):
            self.assertAlmostEqual(float(actual),expected,places=7)

    def test_15_feature_default_off_still_denies_original_wall_rotation(self):
        with TemporaryDirectory(prefix="bmb-v028-default-off-") as td:
            s=XmlSourceEditSession(self.source,Path(td)/"D0")
            with patch.dict(os.environ,{"BMB_V028_ORIGINAL_WALL_CENTER_ROTATE":"0"}):
                receipt=s.call("submit_building_xml",{"xml_text":self.updated.decode("utf8")})
            self.assertEqual(receipt["status"],"error")
            self.assertIsNone(s.output_ifc)
            self.assertEqual(s.current_xml,s.original_xml)

    def test_16_wrong_public_GUID_or_native_type_fails(self):
        f=ifcopenshell.open(str(self.d0.normalized))
        for guid in ("0"*22,f.by_type("IfcDoor")[0].GlobalId):
            with self.subTest(guid=guid),self.assertRaises(UnsupportedIFCMutation):
                plan_original_wall_rotation(self.d0.normalized,guid)

    def test_17_native_forged_original_IFC_source_SHA_rejected(self):
        f=ifcopenshell.open(str(self.d0.normalized))
        f.by_type("IfcWall")[0].Name="FORGED_SOURCE_INPUT"
        path=self.folder/"forged-source.ifc"
        f.write(str(path))
        with self.assertRaises(UnsupportedIFCMutation):
            plan_original_wall_rotation(path,self.guid)

    def test_18_native_original_source_refdirection_shared_would_be_refused_if_unshared(self):
        f=ifcopenshell.open(str(self.d0.normalized))
        wall=f.by_guid(self.guid)
        private=f.create_entity("IfcDirection",DirectionRatios=(-1.,0.,0.))
        wall.ObjectPlacement.RelativePlacement.RefDirection=private
        path=self.folder/"forged-private-original-refdirection.ifc"
        f.write(str(path))
        with patch("src.runtime.original_wall_rotation.PINNED_ORIGINAL_NORMALIZED_SHA",
                   file_hash(path)):
            with self.assertRaises(UnsupportedIFCMutation):
                plan_original_wall_rotation(path,self.guid)

    def test_19_native_new_unexpected_neighbor_connection_refused(self):
        f=ifcopenshell.open(str(self.d0.normalized))
        wall=f.by_guid(self.guid)
        other=next(x for x in f.by_type("IfcWall") if x!=wall)
        f.create_entity("IfcRelConnectsPathElements",
                        GlobalId=ifcopenshell.guid.new(),
                        RelatingElement=other,RelatedElement=wall)
        path=self.folder/"forged-original-connects.ifc"
        f.write(str(path))
        with patch("src.runtime.original_wall_rotation.PINNED_ORIGINAL_NORMALIZED_SHA",
                   file_hash(path)):
            with self.assertRaises(UnsupportedIFCMutation):
                plan_original_wall_rotation(path,self.guid)

    def test_20_native_unrelated_wall_root_mutation_rejected(self):
        def tweak(f):
            f.by_type("IfcWall")[0].Name="UNRELATED_WALL_EDIT"
        output=self._tampered_native(tweak)
        with self.assertRaises(UnsupportedIFCMutation):
            verify_wall_rotation(self.d0.normalized,output,self.plan)

    def test_21_native_shared_direction_mutation_rejected(self):
        def tweak(f):
            f.by_id(self.plan.shared_direction_id).DirectionRatios=(1.,0.,0.)
        output=self._tampered_native(tweak)
        with self.assertRaises(UnsupportedIFCMutation):
            verify_wall_rotation(self.d0.normalized,output,self.plan)

    def test_22_native_original_wall_place_point_forgery_rejected(self):
        def tweak(f):
            p=f.by_id(self.plan.point_id)
            p.Coordinates=(8.0,16.4952,0.0)
        with self.assertRaises(UnsupportedIFCMutation):
            verify_wall_rotation(self.d0.normalized,
                self._tampered_native(tweak),self.plan)

    def test_23_native_original_reference_direction_forgery_rejected(self):
        def tweak(f):
            wall=f.by_guid(self.guid)
            direction=f.create_entity("IfcDirection",DirectionRatios=(1.,0.,0.))
            wall.ObjectPlacement.RelativePlacement.RefDirection=direction
        with self.assertRaises(UnsupportedIFCMutation):
            verify_wall_rotation(self.d0.normalized,
                self._tampered_native(tweak),self.plan)

    def test_24_native_new_unrelated_STEP_added_rejected(self):
        def tweak(f):
            f.create_entity("IfcCartesianPoint",Coordinates=(11.,99.,4.))
        with self.assertRaises(UnsupportedIFCMutation):
            verify_wall_rotation(self.d0.normalized,
                self._tampered_native(tweak),self.plan)

    def test_25_native_other_product_removed_rejected(self):
        def tweak(f):
            f.remove(f.by_type("IfcWindow")[0])
        with self.assertRaises(UnsupportedIFCMutation):
            verify_wall_rotation(self.d0.normalized,
                self._tampered_native(tweak),self.plan)

    def test_26_negative_XML_wrong_90_direction_rejected(self):
        source=self.updated.decode("utf8")
        line=next(x for x in source.splitlines(keepends=True)
                  if 'ifcGuid="'+self.guid+'"' in x)
        bad=line.replace('y1="16.4952"','y1="11.4952"').replace(
            'y2="11.4952"','y2="16.4952"')
        self._new_session(source.replace(line,bad))

    def test_27_negative_XML_wall_center_translation_rejected(self):
        source=self.updated.decode("utf8")
        line=next(x for x in source.splitlines(keepends=True)
                  if 'ifcGuid="'+self.guid+'"' in x)
        bad=line.replace('x1="5"','x1="6"').replace('x2="5"','x2="6"')
        self._new_session(source.replace(line,bad))

    def test_28_negative_XML_height_edit_alongside_rotation_rejected(self):
        source=self.updated.decode("utf8")
        line=next(x for x in source.splitlines(keepends=True)
                  if 'ifcGuid="'+self.guid+'"' in x)
        bad=line.replace('height="3.6"','height="4.1"')
        self._new_session(source.replace(line,bad))

    def test_29_negative_XML_non_target_Wall_coordinate_change_rejected(self):
        source=self.updated.decode("utf8")
        other=next(x for x in source.splitlines(keepends=True)
                   if '<Wall ' in x and 'ifcGuid="'+self.guid+'"' not in x)
        m=re.search(r'\bx1="([^"]+)"',other)
        bad=other.replace('x1="'+m.group(1)+'"', 'x1="'+str(float(m.group(1))+1.)+'"')
        self._new_session(source.replace(other,bad))

    def test_30_negative_original_public_question_forgery_rejected(self):
        with self.assertRaises(OriginalWallRotateAuditBlocked):
            full_public_XML_center_rotation(
                "Rotate wall "+"Z"*22+" by +90 degree around z axis",
                self.d0.original_xml)
        with self.assertRaises(OriginalWallRotateAuditBlocked):
            full_public_XML_center_rotation(
                self.case["public_question"]+" and "+"Z"*22,self.d0.original_xml)

    def test_31_original_non_IFC4X3_source_schemas_remain_unsupported(self):
        for tid in ("geometry_test_03","geometry_test_05"):
            c=self.cohort[tid]
            original=DATA/"ifc"/c["original_source_ifc_relpath"]
            with self.subTest(tid=tid),TemporaryDirectory() as td:
                with self.assertRaises(UnsupportedArm):
                    XmlSourceEditSession(original,Path(td)/"D0")
                self.assertEqual(file_hash(original),c["original_ifc_sha256"])

    def test_32_frozen_report_SHA_and_source_clean(self):
        self.assertEqual(file_hash(REPORT),REPORT_SHA)
        self.assertEqual(file_hash(self.source),self.source_sha)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)

    def test_33_public_named_target_and_question_not_leaked(self):
        text=REPORT.read_text(encoding="utf8")
        self.assertNotIn(self.guid,text)
        self.assertNotIn(self.case["public_question"],text)
        self.assertFalse(self.report["raw_original_public_question_target_GUID_or_private_GT_in_report"])

    def test_34_second_actual_original_D0_I0_rerun_reproduces_report(self):
        second=audit_original_public_test11(ROOT,AUTHOR,DATA)
        self.assertEqual(second,self.report)
        encoded=(json.dumps(second,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(sha256(encoded).hexdigest(),REPORT_SHA)

    def test_35_frozen_45_cumulative_scientific_accounting(self):
        self.assertEqual(self.report["original_public45_denominator"],45)
        self.assertEqual(self.report["prior_developer_original_native_byte_equal_D0_I0_tasks"],9)
        self.assertEqual(self.report["new_cumulative_developer_original_native_byte_equal_D0_I0_tasks"],10)
        self.assertEqual(self.report["prior_original_author_callable_developer_pairs"],7)
        self.assertEqual(self.report["new_cumulative_original_author_callable_developer_pairs"],8)
        self.assertEqual(self.report["other_original_public_tasks_unverified_identical_protocol"],35)
        self.assertEqual(self.report["real_LLM_model_calls"],0)
        self.assertEqual(self.report["paid_provider_USD"],0)
        self.assertFalse(self.report["causal_D0_vs_I0_model_performance_proven"])
        self.assertFalse(self.report["complete_original45_source_information_writable_feedback_parity_proven"])


if __name__=="__main__":
    unittest.main()
