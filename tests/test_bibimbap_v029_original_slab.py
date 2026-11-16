"""v0.29 original PUBLIC test_14 source-faithful flipped Slab XML and native tests.

Test the *actual* pinned original IFC4X3 source, original unchanged author
scorer, complete D0 native source and developer independent I0. Adversarial
tests enforce exact source SHA, original shared point ownership, unmodified
other native STEP/Roots, full XML semantic source geometry and safe fail-close.
No hidden benchmark answers nor LLM/provider calls.
"""
from __future__ import annotations

import ast
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell
import ifcopenshell.guid

from src.runtime.ifc_mutations import UnsupportedIFCMutation
from src.runtime.ifc_projection import project_ifc
from src.runtime.original_slab_translate import (
    SOURCE_SHA,strict_slab_preflight,verify_slab_native,
)
from src.runtime.original_slab_projection import verified_flipped_slab_attrs
from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import XmlSourceEditSession,UnsupportedArm,file_hash
from tools.bibimbap_v029_original_slab_i0 import independent_public_slab_i0
from tools.audit_bibimbap_v029_original_slab import (
    ROOT,TASK,FROZEN_V028_REPORTS,
    OriginalSlabAuditBlocked,whole_original_source_one_slab_z_down,
    independent_native_identity_oracle,audit_actual_original_public_test14,
)

BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports/bibimbap_v029_original_test14_flipped_slab_D0_I0_native_parity_20261116.json"
REPORT_SHA="338f763b691390b7186c51ecdaaa914ce18a9c8ab8586fa000542a7d63f8b748"
FULL_NATIVE_SHA="1b0e811327765bf4f9f85545de64260da19e421f1707d005d8e9ac30e7914b18"


class OriginalPublicTest14FlippedSlabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks={t["test_id"]:t for t in public_45(AUTHOR,DATA)}
        cls.case=cls.tasks[TASK]
        cls.original=DATA/"ifc"/cls.case["original_source_ifc_relpath"]
        cls.original_sha=file_hash(cls.original)
        cls.temp=TemporaryDirectory(prefix="bmb-v029-original-slab-tests-")
        cls.folder=Path(cls.temp.name)
        with patch.dict(os.environ,{"BMB_V029_ORIGINAL_SLAB_TRANSLATE":"1"}):
            cls.d0=XmlSourceEditSession(cls.original,cls.folder/"D0")
            cls.guid,cls.updated=whole_original_source_one_slab_z_down(
                cls.case["public_question"],cls.d0.original_xml)
            cls.plan=strict_slab_preflight(cls.d0.normalized,cls.guid)
            cls.d0_reply=cls.d0.call(
                "submit_building_xml",{"xml_text":cls.updated.decode("utf8")})
        cls.i0path=cls.folder/"independent_native_I0_mm.ifc"
        cls.i0=independent_public_slab_i0(cls.original,cls.guid,cls.i0path)
        cls.metric=cls.d0.folder/"attempt_01"/"candidate_m.ifc"
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def _forged_native_output(self,func):
        f=ifcopenshell.open(str(self.metric))
        func(f)
        path=self.folder/("forged-"+str(len(list(self.folder.glob("forged-*.ifc"))))+".ifc")
        f.write(str(path))
        return path

    def _reject_XML(self,text):
        with TemporaryDirectory(prefix="bmb-v029-bad-author-") as td:
            with patch.dict(os.environ,{"BMB_V029_ORIGINAL_SLAB_TRANSLATE":"1"}):
                s=XmlSourceEditSession(self.original,Path(td)/"D0")
                receipt=s.call("submit_building_xml",{"xml_text":text})
            self.assertEqual(receipt["status"],"error")
            self.assertIsNone(s.output_ifc)
            self.assertEqual(s.current_xml,s.original_xml)

    def _target_line(self,text):
        return next(line for line in text.splitlines(keepends=True)
                    if '<Slab ' in line and 'ifcGuid="'+self.guid+'"' in line)

    def test_01_original_public45_source_author_and_data_git_SHA(self):
        self.assertEqual(len(self.tasks),45)
        self.assertEqual(self.case["category"],"basic")
        self.assertEqual(self.case["crud"],"update")
        self.assertEqual(self.original_sha,self.case["original_ifc_sha256"])
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)

    def test_02_previous_v028_native_reports_unchanged(self):
        for rel,sha in FROZEN_V028_REPORTS.items():
            with self.subTest(rel=rel):
                self.assertEqual(file_hash(ROOT/rel),sha)

    def test_03_original_native_source_FLOOR_slab_exists(self):
        f=ifcopenshell.open(str(self.d0.normalized))
        slab=f.by_guid(self.guid)
        self.assertEqual(slab.is_a(),"IfcSlab")
        self.assertEqual(slab.PredefinedType,"FLOOR")
        self.assertEqual(len(f.by_type("IfcSlab")),2)

    def test_04_default_read_projection_omits_original_inverted_slab(self):
        projection=project_ifc(self.d0.normalized)
        self.assertEqual(projection.xml.count(b"<Slab "),0)
        self.assertEqual(len([x for x in projection.opaque_references
                              if x.ifc_class=="IfcSlab"]),2)

    def test_05_optin_native_cuboid_read_projects_two_original_slabs(self):
        p=project_ifc(self.d0.normalized,allow_original_flipped_slab=True)
        self.assertEqual(p.xml.count(b"<Slab "),2)
        self.assertEqual(len([x for x in p.opaque_references
                              if x.ifc_class=="IfcSlab"]),0)
        self.assertEqual(self.d0.original_xml,p.xml)

    def test_06_target_native_Z_inverted_swept_profile(self):
        f=ifcopenshell.open(str(self.d0.normalized));slab=f.by_guid(self.guid)
        body=slab.Representation.Representations[0].Items[0]
        self.assertEqual(body.is_a(),"IfcExtrudedAreaSolid")
        self.assertEqual(body.SweptArea.is_a(),"IfcRectangleProfileDef")
        self.assertAlmostEqual(body.Depth,0.3)
        self.assertEqual(tuple(body.Position.Axis.DirectionRatios),(0.,0.,-1.))

    def test_07_original_flipped_slab_true_world_box_representation(self):
        p=project_ifc(self.d0.normalized,allow_original_flipped_slab=True)
        target=self._target_line(p.xml.decode("utf8"))
        self.assertIn('x="-0.2"',target)
        self.assertIn('y="-0.175"',target)
        self.assertIn('z="3.8"',target)
        self.assertIn('width="10.4"',target)
        self.assertIn('depth="10.375"',target)
        self.assertIn('thickness="0.3"',target)

    def test_08_full_XML_only_existing_Slab_z_single_field_edit(self):
        text=self.d0.original_xml.decode("utf8")
        after=self.updated.decode("utf8")
        self.assertEqual(len(text.splitlines()),len(after.splitlines()))
        self.assertEqual(sum(x!=y for x,y in zip(text.splitlines(),after.splitlines())),1)
        a=self._target_line(text);b=self._target_line(after)
        self.assertEqual(a.replace('z="3.8"','z="3.3"'),b)
        self.assertEqual(text.count("<Slab "),after.count("<Slab "))
        self.assertNotIn("<Move",after)
        self.assertNotIn("<Command",after)
        self.assertNotIn("<Delete",after)

    def test_09_native_original_source_zero_point_is_shared_56_times(self):
        f=ifcopenshell.open(str(self.d0.normalized))
        p=f.by_id(self.plan.shared_point_id)
        self.assertEqual(tuple(p.Coordinates),(0.,0.,0.))
        self.assertEqual(f.get_total_inverses(p),56)

    def test_10_native_target_relative_placement_is_exclusively_owned(self):
        f=ifcopenshell.open(str(self.d0.normalized))
        slab=f.by_guid(self.guid)
        self.assertEqual(slab.ObjectPlacement.RelativePlacement.id(),
                         self.plan.relative_placement_id)
        self.assertEqual(f.get_total_inverses(slab.ObjectPlacement),1)

    def test_11_D0_actual_XML_native_metric_compilation_committed(self):
        self.assertEqual(self.d0_reply["status"],"ok")
        self.assertTrue(self.d0_reply["native_ifc_committed"])
        self.assertTrue(self.d0.output_ifc.is_file())
        self.assertEqual(self.d0_reply["native_ifc_sha256"],FULL_NATIVE_SHA)

    def test_12_independent_Python_I0_no_compiler_imports(self):
        self.assertEqual(self.i0["status"],
                         "INDEPENDENT_ORIGINAL_PUBLIC_TEST14_IFCSLAB_Z_MINUS_HALF_METER")
        code=(ROOT/"tools/bibimbap_v029_original_slab_i0.py").read_text(encoding="utf8")
        imports=[]
        for node in ast.walk(ast.parse(code)):
            if isinstance(node,ast.Import):
                imports.extend(x.name for x in node.names)
            elif isinstance(node,ast.ImportFrom):
                imports.append(node.module or "")
        self.assertFalse(any(m.startswith("src.runtime") for m in imports))
        self.assertNotIn("compile_declarative_xml",code)
        self.assertNotIn("original_slab_translate",code)

    def test_13_complete_native_D0_and_independent_I0_byte_equal(self):
        self.assertEqual(file_hash(self.d0.output_ifc),file_hash(self.i0path))
        self.assertEqual(file_hash(self.i0path),FULL_NATIVE_SHA)
        self.assertEqual(self.report["full_original_native_D0_IFC_SHA256"],FULL_NATIVE_SHA)
        self.assertEqual(self.report["full_original_native_I0_IFC_SHA256"],FULL_NATIVE_SHA)

    def test_14_original_author_grader_both_full_marks(self):
        d=grade_author(AUTHOR,self.original,self.d0.output_ifc,TASK)
        i=grade_author(AUTHOR,self.original,self.i0path,TASK)
        self.assertEqual(d,i)
        self.assertEqual(d["original_author_score"],1.)
        self.assertTrue(d["original_author_full_mark"])
        self.assertEqual(d["original_author_metrics"],{
            "integrity_constraint":1.0,"right_dimensions":1.0,"right_location":1.0})
        self.assertEqual(d,self.report["unchanged_original_author_D0"])

    def test_15_independent_native_original_all_Root_Product_identity(self):
        d=independent_native_identity_oracle(
            self.original,self.d0.output_ifc,self.guid)
        i=independent_native_identity_oracle(
            self.original,self.i0path,self.guid)
        self.assertEqual(d,i)
        self.assertEqual(d["original_Product_count"],43)
        self.assertTrue(d["every_original_IfcRoot_GUID_class_preserved"])

    def test_16_native_metric_all_original_Roots_and_STEP_scope(self):
        n=verify_slab_native(self.d0.normalized,self.metric,self.plan)
        self.assertEqual(n,self.plan.native_root_count)
        self.assertGreater(n,150)

    def test_17_one_private_new_point_one_original_relative_placement_edit(self):
        a=ifcopenshell.open(str(self.d0.normalized))
        b=ifcopenshell.open(str(self.metric))
        before={n.id():str(n) for n in a}
        after={n.id():str(n) for n in b}
        self.assertFalse(before.keys()-after.keys())
        self.assertEqual(len(after.keys()-before.keys()),1)
        self.assertEqual({i for i in before.keys()&after.keys() if before[i]!=after[i]},
                         {self.plan.relative_placement_id})
        self.assertEqual(tuple(b.by_id(next(iter(after.keys()-before.keys()))).Coordinates),
                         (0.,0.,-.5))

    def test_18_shared_original_point_remains_unchanged_for_other_55(self):
        a=ifcopenshell.open(str(self.d0.normalized))
        b=ifcopenshell.open(str(self.metric))
        self.assertEqual(str(a.by_id(self.plan.shared_point_id)),
                         str(b.by_id(self.plan.shared_point_id)))
        self.assertEqual(b.get_total_inverses(b.by_id(self.plan.shared_point_id)),55)

    def test_19_original_world_Z_position_moves_minus_half_without_XY(self):
        import ifcopenshell.util.placement
        a=ifcopenshell.open(str(self.d0.normalized))
        b=ifcopenshell.open(str(self.metric))
        mat1=ifcopenshell.util.placement.get_local_placement(
            a.by_guid(self.guid).ObjectPlacement)
        mat2=ifcopenshell.util.placement.get_local_placement(
            b.by_guid(self.guid).ObjectPlacement)
        self.assertAlmostEqual(mat2[0,3]-mat1[0,3],0)
        self.assertAlmostEqual(mat2[1,3]-mat1[1,3],0)
        self.assertAlmostEqual(mat2[2,3]-mat1[2,3],-.5)

    def test_20_default_flag_OFF_keeps_original_slabs_opaque(self):
        with TemporaryDirectory(prefix="bmb-v029-default-off-") as td:
            with patch.dict(os.environ,{"BMB_V029_ORIGINAL_SLAB_TRANSLATE":"0"}):
                session=XmlSourceEditSession(self.original,Path(td)/"D0")
            self.assertNotIn("<Slab ",session.original_xml.decode("utf8"))
            self.assertIsNone(session.output_ifc)

    def test_21_wrong_original_guid_or_type_refused(self):
        f=ifcopenshell.open(str(self.d0.normalized))
        other=f.by_type("IfcSlab")[0]
        if other.GlobalId==self.guid:
            other=f.by_type("IfcSlab")[1]
        for guid in ("0"*22,other.GlobalId,f.by_type("IfcDoor")[0].GlobalId):
            with self.subTest(guid=guid),self.assertRaises(UnsupportedIFCMutation):
                strict_slab_preflight(self.d0.normalized,guid)

    def test_22_tampered_native_original_input_checksum_refused(self):
        f=ifcopenshell.open(str(self.d0.normalized))
        f.by_type("IfcWall")[0].Name="FORGED_SLICE"
        path=self.folder/"forged-source.ifc";f.write(str(path))
        with self.assertRaises(UnsupportedIFCMutation):
            strict_slab_preflight(path,self.guid)

    def test_23_native_unrelated_neighbor_Root_mutation_refused(self):
        def f(model):model.by_type("IfcWall")[0].Name="UNRELATED_CHANGE"
        with self.assertRaises(UnsupportedIFCMutation):
            verify_slab_native(self.d0.normalized,self._forged_native_output(f),self.plan)

    def test_24_native_shared_old_source_Point_mutation_refused(self):
        def f(model):model.by_id(self.plan.shared_point_id).Coordinates=(0.,0.,-.5)
        with self.assertRaises(UnsupportedIFCMutation):
            verify_slab_native(self.d0.normalized,self._forged_native_output(f),self.plan)

    def test_25_native_wrong_private_z_movement_refused(self):
        def f(model):
            model.by_id(self.plan.relative_placement_id).Location.Coordinates=(0.,0.,-.6)
        with self.assertRaises(UnsupportedIFCMutation):
            verify_slab_native(self.d0.normalized,self._forged_native_output(f),self.plan)

    def test_26_native_unexpected_new_STEP_entity_refused(self):
        def f(model):model.create_entity("IfcCartesianPoint",Coordinates=(5.,5.,5.))
        with self.assertRaises(UnsupportedIFCMutation):
            verify_slab_native(self.d0.normalized,self._forged_native_output(f),self.plan)

    def test_27_native_unrelated_Slab_deleted_refused(self):
        def f(model):
            other=next(x for x in model.by_type("IfcSlab") if x.GlobalId!=self.guid)
            model.remove(other)
        with self.assertRaises(UnsupportedIFCMutation):
            verify_slab_native(self.d0.normalized,self._forged_native_output(f),self.plan)

    def test_28_native_original_new_Point_becomes_shared_refused(self):
        def f(model):
            newpoint=model.by_id(model.by_id(self.plan.relative_placement_id).Location.id())
            other=next(x for x in model.by_type("IfcSlab") if x.GlobalId!=self.guid)
            other.ObjectPlacement.RelativePlacement.Location=newpoint
        with self.assertRaises(UnsupportedIFCMutation):
            verify_slab_native(self.d0.normalized,self._forged_native_output(f),self.plan)

    def test_29_negative_XML_extra_X_move_rejected(self):
        text=self.updated.decode("utf8");line=self._target_line(text)
        self._reject_XML(text.replace(line,line.replace('x="-0.2"','x="0.8"'),1))

    def test_30_negative_XML_wrong_vertical_delta_rejected(self):
        text=self.updated.decode("utf8");line=self._target_line(text)
        self._reject_XML(text.replace(line,line.replace('z="3.3"','z="3.2"'),1))

    def test_31_negative_XML_thickness_change_rejected(self):
        text=self.updated.decode("utf8");line=self._target_line(text)
        self._reject_XML(text.replace(line,line.replace(
            'thickness="0.3"','thickness="0.1"'),1))

    def test_32_negative_XML_non_target_Slab_edit_rejected(self):
        text=self.updated.decode("utf8")
        other=next(x for x in text.splitlines(keepends=True)
                   if '<Slab ' in x and 'ifcGuid="'+self.guid+'"' not in x)
        self._reject_XML(text.replace(other,other.replace(
            'width="10.4"','width="11.4"'),1))

    def test_33_negative_XML_other_Wall_edit_rejected(self):
        text=self.updated.decode("utf8")
        line=next(x for x in text.splitlines(keepends=True) if "<Wall " in x)
        x=re.search(r'\bx1="([^"]+)"',line).group(1)
        self._reject_XML(text.replace(line,line.replace(
            'x1="'+x+'"','x1="'+str(float(x)+1.)+'"'),1))

    def test_34_wrong_public_question_GUID_rejected(self):
        with self.assertRaises(OriginalSlabAuditBlocked):
            whole_original_source_one_slab_z_down(
                "Decrease the height by 0.5 meters of slab "+"Z"*22,
                self.d0.original_xml)
        with self.assertRaises(OriginalSlabAuditBlocked):
            whole_original_source_one_slab_z_down(
                self.case["public_question"]+" "+"Z"*22,self.d0.original_xml)

    def test_35_original_IFC2X3_and_IFC4_remain_unavailable(self):
        for tid in ("geometry_test_03","geometry_test_05"):
            t=self.tasks[tid]
            path=DATA/"ifc"/t["original_source_ifc_relpath"]
            with self.subTest(task=tid),TemporaryDirectory() as td:
                with self.assertRaises(UnsupportedArm):
                    XmlSourceEditSession(path,Path(td)/"D0")
                self.assertEqual(file_hash(path),t["original_ifc_sha256"])

    def test_36_frozen_native_report_SHA_and_original_source_unmodified(self):
        self.assertEqual(file_hash(REPORT),REPORT_SHA)
        self.assertEqual(file_hash(self.original),self.original_sha)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)

    def test_37_public_raw_target_and_question_not_exposed_in_report(self):
        txt=REPORT.read_text(encoding="utf8")
        self.assertNotIn(self.guid,txt)
        self.assertNotIn(self.case["public_question"],txt)
        self.assertFalse(self.report["raw_original_public_question_target_GUID_hidden_GT_or_IFC_in_report"])

    def test_38_second_original_public_D0_I0_experiment_byte_reproducible(self):
        again=audit_actual_original_public_test14(ROOT,AUTHOR,DATA)
        self.assertEqual(again,self.report)
        canonical=(json.dumps(again,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(sha256(canonical).hexdigest(),REPORT_SHA)

    def test_39_honest_original_45_accounting_and_no_real_LLM(self):
        self.assertEqual(self.report["original_public45_denominator"],45)
        self.assertEqual(self.report["previous_developer_native_byte_equal_original_cases"],10)
        self.assertEqual(self.report["new_cumulative_developer_native_byte_equal_original_cases"],11)
        self.assertEqual(self.report["previous_original_author_callable_developer_pairs"],8)
        self.assertEqual(self.report["new_cumulative_original_author_callable_developer_pairs"],9)
        self.assertEqual(self.report["other_original_public_tasks_not_yet_same_protocol_paired"],34)
        self.assertEqual(self.report["actual_real_LLM_calls"],0)
        self.assertEqual(self.report["new_paid_provider_USD"],0)
        self.assertFalse(self.report["all45_semantic_read_write_feedback_parity_proven"])

    def test_40_independent_I0_source_safety_source_sha_unchanged(self):
        self.assertEqual(self.i0["original_source_sha256"],self.original_sha)
        self.assertEqual(self.i0["entire_native_original_mm_IFC_sha256"],FULL_NATIVE_SHA)
        self.assertEqual(file_hash(self.original),self.original_sha)


if __name__=="__main__":
    unittest.main()
