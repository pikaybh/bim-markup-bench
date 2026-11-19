"""v0.34 original public Wall CREATE I0/D0 and guarded v0.6 compiler tests.

Run with pinned local BIBIMBAP author/data. These are developer-authored native
controls, not matched generative model trial samples or benchmark scores.
"""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.util.unit
from lxml import etree
import numpy as np

from tools import bibimbap_v034_original_wall_i0 as i0
from tools import audit_bibimbap_v034_original_wall_pair as audit
from tools.bibimbap_matched25_tools import file_hash
from src.runtime.experimental_v6_wall_create import (
    compile_declarative_xml_v6_wall_create,WallV6CreateError)
from src.runtime.experimental_v5_wall import compile_declarative_xml_v5,WallV5Error
from src.runtime.experimental_v4_projection import project_ifc_v4

BASE=Path(os.environ.get(
    "BIBIMBAP_EXPERIMENT_BASE",r"D:\\문서\\D__1_Projects\\202611"))
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
SOURCE=DATA/"ifc"/"basic_tasks.ifc"
REPORT=audit.ROOT/"reports"/"bibimbap_v034_original_test05_wall_D0_I0_native_semantic_pair_20261117.json"
REPORT_SHA="d4bc58a426fd30b6215fef0c2c8d0907c109df1127fa64d44f7d8ab911d4073d"


class V034OriginalWallCreateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen=json.loads(REPORT.read_text(encoding="utf8"))

    def setUp(self):
        t=TemporaryDirectory(prefix="bmb-v034-tests-")
        self.addCleanup(t.cleanup)
        self.folder=Path(t.name)

    def native_i0(self):
        result=self.folder/"native_i0.ifc"
        summary=i0.create_original_test05_wall_i0(SOURCE,result)
        return result,summary

    def metric_source_and_xml(self):
        src=self.folder/"metric_source.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(SOURCE)),"METER").write(str(src))
        projected=project_ifc_v4(src)
        original=etree.fromstring(projected.xml)
        updated=etree.fromstring(projected.xml)
        levels=updated.find(audit.NS+"Levels")
        ground=[x for x in levels if x.get("elevation")=="0"]
        self.assertEqual(len(ground),1)
        element=etree.SubElement(
            updated.find(audit.NS+"Elements"),audit.NS+"Wall",
            attrib={
                "id":audit.XML_ID,"level":ground[0].get("id"),
                "x1":"0","y1":"-10","z1":"0",
                "x2":"15","y2":"-10","z2":"0",
                "height":"3","thickness":"0.2",
            })
        return src,original,updated,element

    def test_01_frozen_exact_original_public_task_and_denominator(self):
        r=self.frozen
        self.assertEqual(r["original_45_intention_to_test_unchanged"],45)
        self.assertEqual(r["original_test_id"],"test_05")
        self.assertEqual(r["original_public_task_question_SHA256"],audit.QUESTION_SHA)
        self.assertEqual(r["original_IFC_native_input_SHA256"],i0.SOURCE_SHA)
        self.assertEqual(r["predeclared_world_axis_start_m"],[0.,-10.,0.])
        self.assertEqual(r["predeclared_world_axis_end_m"],[15.,-10.,0.])
        self.assertEqual(r["predeclared_h_height_m"],3.)
        self.assertEqual(r["predeclared_t_thickness_m"],.2)

    def test_02_native_original_author_both_fully_scored_not_model(self):
        r=self.frozen
        self.assertEqual(r["original_author_D0"],r["original_author_I0"])
        self.assertEqual(r["original_author_D0"]["original_author_score"],1.)
        self.assertEqual(r["original_author_D0"]["status"],"AUTHOR_SCORED")
        self.assertEqual(r["original_author_D0"]["original_author_metrics"],{
            "integrity_constraint":1.,"object_exists":1.,
            "right_dimensions":1.,"right_location":1.,
        })
        self.assertTrue(r["native_geometry_axis_source_products_equivalent"])
        self.assertFalse(r["full_IFC_D0_I0_bytes_equal"])
        self.assertTrue(r["this_is_not_a_causal_LLM_benchmark_result"])

    def test_03_old_witness_population_and_model_launch_blocked(self):
        r=self.frozen
        self.assertEqual(r["previous_full_native_byte_equal_developer_11_unchanged"],11)
        self.assertEqual(r["cumulative_full_native_byte_equal_developer_witnesses"],11)
        self.assertTrue(r["previous_two_original_CREATE_semantic_only_cases_unchanged"])
        self.assertTrue(r["new_Create_semantic_only_developer_case"])
        self.assertEqual(r["original_Create_cases_without_semantically_validated_developer_pair"],12)
        self.assertEqual(r["original45_full_information_read_parity_proven"],0)
        self.assertEqual(r["original45_full_native_edit_write_parity_proven"],0)
        self.assertEqual(r["matched_real_LLM_D_I_trials"],0)
        self.assertEqual(r["paid_provider_requests"],0)
        self.assertFalse(r["model_host_new_v06_Wall_compiler_available"])

    def test_04_actual_native_independent_oracle_source_meshes(self):
        a=self.frozen["native_independent_original_IFC_semantic_oracle_both"]
        self.assertEqual(a["existing_original_native_IfcRoot_count"],358)
        self.assertEqual(a["existing_original_native_IfcProduct_count"],43)
        self.assertEqual(a["existing_native_world_mesh_object_count"],39)
        self.assertEqual(a["existing_world_mesh_original_triangle_face_count"],1652)
        self.assertEqual(a["new_wall_exact_axis_start_end_m"],
                         [[0.,-10.,0.],[15.,-10.,0.]])
        self.assertEqual(a["new_wall_world_body_bbox_m"],
                         [0.,-10.1,0.,15.,-9.9,3.])
        self.assertEqual(a["new_wall_extrusion_height_m"],3.)
        self.assertTrue(a["all_preexisting_original_IfcProduct_world_meshes_unchanged"])
        self.assertFalse(a["whole_original_IFC_STEP_entity_preservation_proven"])

    def test_05_frozen_report_and_original_sources_pinned(self):
        self.assertEqual(file_hash(REPORT),REPORT_SHA)
        self.assertEqual(file_hash(SOURCE),i0.SOURCE_SHA)
        for rel,digest in audit.PREVIOUS_REPORTS:
            self.assertEqual(file_hash(audit.ROOT/rel),digest)

    def test_06_python_i0_source_cannot_import_D0_XML_or_grader(self):
        code=Path(i0.__file__).read_text(encoding="utf8")
        modules=[]
        for node in ast.walk(ast.parse(code)):
            if isinstance(node,ast.ImportFrom) and node.module:
                modules.append(node.module)
            elif isinstance(node,ast.Import):
                modules.extend(x.name for x in node.names)
        forbidden=("experimental_v6","experimental_v5","ifc_projection",
                   "xml_parser","binder","matched25","grader","audit_bibimbap",
                   "author_worker")
        self.assertFalse([m for m in modules if any(q in m for q in forbidden)])
        self.assertEqual(i0.SPEC,(0.,-10.,0.,15.,-10.,0.,3.,.2))

    def test_07_real_independent_i0_original_ifc_and_read_oracle(self):
        before=file_hash(SOURCE)
        result,summary=self.native_i0()
        self.assertEqual(file_hash(result),summary["new_candidate_native_mm_ifc_SHA256"])
        check=audit.verify_new_native_original_wall(
            SOURCE,result,summary["new_native_IfcWall_GUID"])
        self.assertEqual(check,self.frozen["native_independent_original_IFC_semantic_oracle_both"])
        self.assertEqual(file_hash(SOURCE),before)

    def test_08_i0_rejects_modified_original_public_source(self):
        altered=self.folder/"bad_source.ifc"
        shutil.copy2(SOURCE,altered)
        with altered.open("ab") as h:
            h.write(b" ")
        out=self.folder/"must_not_exist.ifc"
        with self.assertRaisesRegex(i0.IndependentWallI0Blocked,"SHA"):
            i0.create_original_test05_wall_i0(altered,out)
        self.assertFalse(out.exists())

    def test_09_i0_never_overwrites_existing_output(self):
        dest=self.folder/"existing.ifc"
        dest.write_bytes(b"existing evidence must remain")
        with self.assertRaisesRegex(i0.IndependentWallI0Blocked,"output fresh"):
            i0.create_original_test05_wall_i0(SOURCE,dest)
        self.assertEqual(dest.read_bytes(),b"existing evidence must remain")

    def test_10_i0_refuses_source_as_output(self):
        with self.assertRaisesRegex(i0.IndependentWallI0Blocked,"output fresh"):
            i0.create_original_test05_wall_i0(SOURCE,SOURCE)
        self.assertEqual(file_hash(SOURCE),i0.SOURCE_SHA)

    def test_11_independent_oracle_rejects_no_new_wall(self):
        unchanged=self.folder/"original_copy.ifc"
        shutil.copy2(SOURCE,unchanged)
        with self.assertRaisesRegex(audit.OriginalWallV034Blocked,"Exactly one new original-native"):
            audit.verify_new_native_original_wall(SOURCE,unchanged)

    def test_12_oracle_rejects_spoofed_writer_claim(self):
        output,_=self.native_i0()
        with self.assertRaisesRegex(audit.OriginalWallV034Blocked,"identity differs"):
            audit.verify_new_native_original_wall(SOURCE,output,"0"*22)

    def test_13_oracle_rejects_shifted_axis_even_with_real_native_wall(self):
        output,summary=self.native_i0()
        f=ifcopenshell.open(str(output))
        m=ifcopenshell.util.unit.convert_file_length_units(f,"METER")
        wall=m.by_guid(summary["new_native_IfcWall_GUID"])
        mat=np.eye(4);mat[:3,3]=[5.,-10.,0.]
        ifcopenshell.api.geometry.edit_object_placement(
            m,product=wall,matrix=mat)
        ifcopenshell.util.unit.convert_file_length_units(
            m,"MILLIMETER").write(str(output))
        with self.assertRaisesRegex(audit.OriginalWallV034Blocked,"world axis"):
            audit.verify_new_native_original_wall(SOURCE,output)

    def test_14_oracle_rejects_wrong_wall_height(self):
        output,summary=self.native_i0()
        model=ifcopenshell.open(str(output))
        wall=model.by_guid(summary["new_native_IfcWall_GUID"])
        solid=next(s for rep in wall.Representation.Representations
                   for s in rep.Items if s.is_a("IfcExtrudedAreaSolid"))
        solid.Depth=2200.0
        model.write(str(output))
        with self.assertRaisesRegex(audit.OriginalWallV034Blocked,"extrusion height"):
            audit.verify_new_native_original_wall(SOURCE,output)

    def test_15_existing_v05_wall_create_still_explicitly_rejected(self):
        src,_,edited,_=self.metric_source_and_xml()
        with self.assertRaisesRegex(WallV5Error,"no creates"):
            compile_declarative_xml_v5(
                src,etree.tostring(edited,encoding="utf8"),
                self.folder/"should_not_compile.ifc")

    def test_16_v06_rejects_two_new_wall_nodes(self):
        src,_,edited,first=self.metric_source_and_xml()
        second=etree.SubElement(
            edited.find(audit.NS+"Elements"),audit.NS+"Wall",
            attrib={**first.attrib,"id":"second_wall_unapproved"})
        with self.assertRaisesRegex(WallV6CreateError,"only|Only"):
            compile_declarative_xml_v6_wall_create(
                src,etree.tostring(edited,encoding="utf8"),
                self.folder/"should_fail_two.ifc")

    def test_17_v06_rejects_existing_wall_plus_one_new_modification(self):
        src,_,edited,new=self.metric_source_and_xml()
        old=next(x for x in edited.find(audit.NS+"Elements")
                 if x.tag==audit.NS+"Wall" and x.get("ifcGuid"))
        old.set("x2",str(float(old.get("x2"))+.5))
        with self.assertRaisesRegex(WallV6CreateError,"Only exactly one"):
            compile_declarative_xml_v6_wall_create(
                src,etree.tostring(edited,encoding="utf8"),
                self.folder/"should_fail_mixed.ifc")

    def test_18_v06_rejects_zero_length_or_nonfinite(self):
        src,_,edited,node=self.metric_source_and_xml()
        node.set("x2","0");node.set("y2","-10")
        with self.assertRaisesRegex(Exception,"degenerate|bounded|Wall"):
            compile_declarative_xml_v6_wall_create(
                src,etree.tostring(edited,encoding="utf8"),
                self.folder/"should_fail_zero.ifc")

    def test_19_original_author_spoof_cannot_register_a_success(self):
        from tools import bibimbap_matched25_cli as original
        with patch.object(original,"grade_author",return_value={
            "status":"FAKE","original_author_score":1.,
            "original_author_full_mark":True,"original_author_metrics":{},
        }):
            with self.assertRaisesRegex(audit.OriginalWallV034Blocked,"did not produce"):
                audit.audit_original_test05_wall_pair(audit.ROOT,AUTHOR,DATA)

    def test_20_frozen_historical_report_integrity_failure(self):
        file=self.folder/audit.PREVIOUS_REPORTS[2][0]
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_bytes(b"tampered")
        with self.assertRaisesRegex(audit.OriginalWallV034Blocked,"evidence SHA drift"):
            audit.pinned_json(self.folder,audit.PREVIOUS_REPORTS[2])

    def test_21_actual_whole_xml_native_created_and_independent_oracle(self):
        out=self.folder/"xml_reproduction_mm.ifc"
        d0=audit.create_full_declarative_D0(SOURCE,out)
        result=audit.verify_new_native_original_wall(
            SOURCE,out,d0["new_native_wall_guid"])
        self.assertEqual(result,self.frozen["native_independent_original_IFC_semantic_oracle_both"])
        self.assertEqual(d0["compiler"],"experimental-wall-create-v0.6")

    def test_22_run_original_public_pair_replay_geometry_and_scores(self):
        r=audit.audit_original_test05_wall_pair(audit.ROOT,AUTHOR,DATA)
        self.assertEqual(r["native_independent_original_IFC_semantic_oracle_both"],
                         self.frozen["native_independent_original_IFC_semantic_oracle_both"])
        self.assertEqual(r["original_author_D0"],self.frozen["original_author_D0"])
        self.assertEqual(r["original_author_I0"],self.frozen["original_author_I0"])
        self.assertFalse(r["full_IFC_D0_I0_bytes_equal"])
        self.assertEqual(file_hash(SOURCE),i0.SOURCE_SHA)

    def test_23_report_does_not_leak_answers_or_existing_IFC(self):
        contents=REPORT.read_text(encoding="utf8").lower()
        for secret in ("ground_truth","hidden_target_guid","private_target_guid",
                       "original_public_question_text","model_prompt_body",
                       "ifc_step_source_bytes","credential"):
            self.assertNotIn(secret,contents)
        self.assertLess(REPORT.stat().st_size,16000)

if __name__=="__main__":
    unittest.main()
