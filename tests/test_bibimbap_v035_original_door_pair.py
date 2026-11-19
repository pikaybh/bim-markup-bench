"""v0.35 source-only original Door+Opening CREATE; real native positive/negative tests.

Original author scorer is invoked only by audited pair AFTER two native-oracle
checks, never by I0/D0 writers. Tests do not edit upstream source or GT.
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
import ifcopenshell.api.feature
import ifcopenshell.api.geometry
import ifcopenshell.util.unit
from lxml import etree
import numpy as np

from tools import audit_bibimbap_v035_original_door_pair as audit
from tools import bibimbap_v035_original_door_i0 as i0
from tools.bibimbap_matched25_tools import file_hash
from src.runtime.experimental_v4_projection import project_ifc_v4
from src.runtime.experimental_v7_hosted_door_create import (
    compile_declarative_xml_v07_hosted_door_create,ScopedDoorV07Blocked,
)
from src.runtime.experimental_v6_wall_create import (
    compile_declarative_xml_v6_wall_create,WallV6CreateError,
)
from src.runtime.experimental_v5_wall import (
    compile_declarative_xml_v5,WallV5Error,
)

BASE=Path(os.environ.get(
    "BIBIMBAP_EXPERIMENT_BASE",r"D:\\문서\\D__1_Projects\\202611"))
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
SOURCE=DATA/"ifc"/"basic_tasks.ifc"
REPORT=audit.ROOT/"reports"/"bibimbap_v035_original_test01_hosted_door_D0_I0_20261117.json"
REPORT_SHA="7ba3a9465996a90d4d324c8e31bc3ff18f3487cb890431e3c30989a516ac82c9"


class V035OriginalHostedDoorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen=json.loads(REPORT.read_text(encoding="utf8"))

    def setUp(self):
        temp=TemporaryDirectory(prefix="bmb-v035-tests-")
        self.addCleanup(temp.cleanup)
        self.dir=Path(temp.name)

    def i0(self):
        path=self.dir/"native_i0.ifc"
        summary=i0.create_original_public_test01_door_i0(SOURCE,path)
        return path,summary

    def full_xml(self):
        metric=self.dir/"source_m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(SOURCE)),"METER").write(str(metric))
        projected=project_ifc_v4(metric)
        root=etree.fromstring(projected.xml)
        host_id=dict(projected.projected_global_ids)[i0.HOST_GUID]
        els=root.find(audit.NS+"Elements")
        op=etree.SubElement(els,audit.NS+"Opening",attrib={
            "id":audit.XML_OPENING_ID,"host":host_id,
            "offset":"5.1","sill":"0","width":"1","height":"2",
        })
        door=etree.SubElement(els,audit.NS+"Door",attrib={
            "id":audit.XML_DOOR_ID,"opening":audit.XML_OPENING_ID,
            "width":"1","height":"2",
        })
        return metric,root,op,door

    def test_01_original_45_and_public_question_pinned(self):
        r=self.frozen
        self.assertEqual(r["original_45_intention_to_test_denominator"],45)
        self.assertEqual(r["original_public_test_id"],"test_01")
        self.assertEqual(r["original_question_sha256"],audit.QUESTION_SHA)
        self.assertEqual(r["original_source_IFC_sha256"],i0.SOURCE_SHA)
        self.assertTrue(r["public_fixed_2_by_1_interpreted_height_2m_width_1m"])
        self.assertTrue(r["unrequested_centered_wall_zero_sill_predeclared"])

    def test_02_not_a_model_benchmark_or_full_native_byte_equivalence(self):
        r=self.frozen
        self.assertTrue(r["native_independent_two_arm_semantic_equivalence"])
        self.assertFalse(r["native_whole_IFC_byte_equal"])
        self.assertEqual(r["prior_full_native_byte_equal_11_witnesses_unchanged"],11)
        self.assertEqual(r["original_Create_task_specific_semantic_paired_count"],4)
        self.assertEqual(r["original_Create_tasks_without_positive_native_semantic_pair"],11)
        self.assertEqual(r["original45_full_information_read_parity_proven"],0)
        self.assertEqual(r["original45_full_native_edit_write_parity_proven"],0)
        self.assertEqual(r["matched_real_LLM_D_I_trials"],0)
        self.assertEqual(r["new_paid_model_provider_calls"],0)
        self.assertFalse(r["causal_representation_effect_permitted"])

    def test_03_actual_original_author_both_scored(self):
        a=self.frozen["original_author_I0"]
        b=self.frozen["original_author_D0"]
        self.assertEqual(a,b)
        self.assertEqual(a["status"],"AUTHOR_SCORED")
        self.assertEqual(a["original_author_score"],1.0)
        self.assertEqual(a["original_author_metrics"],{
            "object_exists":1.,"right_location":1.,
            "right_dimensions":1.,"integrity_constraint":1.,
        })
        self.assertTrue(a["original_author_full_mark"])

    def test_04_native_real_host_void_and_unrelated_scene(self):
        r=self.frozen["native_actual_independent_oracle_both_arms"]
        self.assertEqual(r["source_existing_IfcRoot_count"],358)
        self.assertEqual(r["source_existing_IfcProduct_count"],43)
        self.assertEqual(r["source_original_mesh_bearing_product_count"],39)
        self.assertEqual(r["original_unchanged_nonhost_mesh_bearing_product_count"],38)
        self.assertEqual(r["original_nonhost_triangle_face_count"],1640)
        self.assertAlmostEqual(r["host_wall_old_volume_m3"],7.344,places=5)
        self.assertAlmostEqual(r["host_wall_new_volume_m3"],6.944,places=5)
        self.assertAlmostEqual(r["host_wall_cut_volume_m3"],.4,places=5)
        self.assertEqual(r["host_wall_triangle_count_before"],12)
        self.assertEqual(r["host_wall_triangle_count_after"],28)
        self.assertEqual(r["new_native_door_world_bbox_m"],
                         [23.8,15.08,0.,24.8,15.12,2.])
        self.assertTrue(r["original_wall_void_and_door_fills_relationships_present"])
        self.assertTrue(r["original_storey_containment_preserved_and_door_added"])
        self.assertFalse(r["full_original_native_STEP_lossless_preservation_claimed"])

    def test_05_frozen_original_and_previous_report_hashes(self):
        self.assertEqual(file_hash(REPORT),REPORT_SHA)
        self.assertEqual(file_hash(SOURCE),i0.SOURCE_SHA)
        for rel,digest in audit.FROZEN:
            self.assertEqual(file_hash(audit.ROOT/rel),digest)

    def test_06_i0_does_not_depend_on_XML_D0_or_grader(self):
        script=Path(i0.__file__).read_text(encoding="utf8")
        imports=[]
        for node in ast.walk(ast.parse(script)):
            if isinstance(node,ast.ImportFrom) and node.module:
                imports.append(node.module)
            elif isinstance(node,ast.Import):
                imports.extend(alias.name for alias in node.names)
        forbidden=("experimental_v7","experimental_v6","ifc_projection",
                   "xml_parser","binder","grade_author","matched25_cli",
                   "audit_bibimbap","author_worker")
        self.assertFalse([p for p in imports if any(x in p for x in forbidden)])
        self.assertEqual(i0.DOOR_WIDTH_M,1.)
        self.assertEqual(i0.DOOR_HEIGHT_M,2.)
        self.assertEqual(i0.OFFSET_FROM_HOST_AXIS_START_M,5.1)

    def test_07_actual_original_python_i0_and_independent_native_oracle(self):
        before=file_hash(SOURCE)
        path,summary=self.i0()
        self.assertEqual(file_hash(path),summary["candidate_mm_ifc_sha256"])
        verified=audit.actual_original_native_hosted_door_oracle(
            SOURCE,path,summary["door_guid"],summary["opening_guid"])
        self.assertEqual(verified,self.frozen["native_actual_independent_oracle_both_arms"])
        self.assertEqual(file_hash(SOURCE),before)

    def test_08_original_I0_rejects_mutated_input_hash(self):
        corrupted=self.dir/"corrupt_original.ifc"
        shutil.copy2(SOURCE,corrupted)
        with corrupted.open("ab") as fp:
            fp.write(b" ")
        out=self.dir/"should_not_create.ifc"
        with self.assertRaisesRegex(i0.OriginalPublicDoorI0Blocked,"source SHA"):
            i0.create_original_public_test01_door_i0(corrupted,out)
        self.assertFalse(out.exists())

    def test_09_I0_rejects_existing_output_without_overwrite(self):
        old=self.dir/"existing.ifc"
        old.write_bytes(b"immutable")
        with self.assertRaisesRegex(i0.OriginalPublicDoorI0Blocked,"output fresh"):
            i0.create_original_public_test01_door_i0(SOURCE,old)
        self.assertEqual(old.read_bytes(),b"immutable")

    def test_10_I0_rejects_original_source_as_destination(self):
        with self.assertRaisesRegex(i0.OriginalPublicDoorI0Blocked,"output fresh"):
            i0.create_original_public_test01_door_i0(SOURCE,SOURCE)
        self.assertEqual(file_hash(SOURCE),i0.SOURCE_SHA)

    def test_11_native_oracle_rejects_unchanged_source_no_door(self):
        copy=self.dir/"unchanged.ifc"
        shutil.copy2(SOURCE,copy)
        with self.assertRaisesRegex(audit.OriginalHostedDoorV035Blocked,
                                    "requires exactly two new products"):
            audit.actual_original_native_hosted_door_oracle(SOURCE,copy)

    def test_12_native_oracle_rejects_fake_door_GUID(self):
        path,s=self.i0()
        with self.assertRaisesRegex(audit.OriginalHostedDoorV035Blocked,
                                    "wrong Door GUID"):
            audit.actual_original_native_hosted_door_oracle(
                SOURCE,path,claimed_door_guid="0"*22)

    def test_13_native_oracle_rejects_missing_filling_relationship(self):
        path,s=self.i0()
        f=ifcopenshell.open(str(path))
        ifcopenshell.api.feature.remove_filling(f,element=f.by_guid(s["door_guid"]))
        f.write(str(path))
        with self.assertRaisesRegex(audit.OriginalHostedDoorV035Blocked,
                                    "void/fill|two new void/fill"):
            audit.actual_original_native_hosted_door_oracle(SOURCE,path)

    def test_14_native_oracle_rejects_missing_host_void(self):
        path,s=self.i0()
        f=ifcopenshell.open(str(path))
        ifcopenshell.api.feature.remove_feature(
            f,feature=f.by_guid(s["opening_guid"]))
        f.write(str(path))
        with self.assertRaisesRegex(audit.OriginalHostedDoorV035Blocked,
                                    "two new void/fill|does not void|exactly two new products"):
            audit.actual_original_native_hosted_door_oracle(SOURCE,path)

    def test_15_native_oracle_rejects_displaced_door(self):
        path,s=self.i0()
        f=ifcopenshell.open(str(path))
        m=ifcopenshell.util.unit.convert_file_length_units(f,"METER")
        obj=m.by_guid(s["door_guid"])
        x=np.eye(4);x[:3,3]=[26.,15.1,0.]
        ifcopenshell.api.geometry.edit_object_placement(
            m,product=obj,matrix=x)
        ifcopenshell.util.unit.convert_file_length_units(
            m,"MILLIMETER").write(str(path))
        with self.assertRaisesRegex(audit.OriginalHostedDoorV035Blocked,
                                    "world geometry outside"):
            audit.actual_original_native_hosted_door_oracle(SOURCE,path)

    def test_16_v07_compiler_accepts_exact_original_hosted_D0(self):
        before=file_hash(SOURCE)
        out=self.dir/"declarative_D0_mm.ifc"
        summary=audit.compile_full_declarative_test01_d0(SOURCE,out)
        self.assertEqual(summary["status"],
                         "V035_ORIGINAL_PUBLIC_DOOR_FULL_XML_D0_COMPILED")
        check=audit.actual_original_native_hosted_door_oracle(
            SOURCE,out,summary["created_IfcDoor_guid"],
            summary["created_IfcOpeningElement_guid"])
        self.assertEqual(check,self.frozen["native_actual_independent_oracle_both_arms"])
        self.assertEqual(file_hash(SOURCE),before)

    def test_17_legacy_v06_still_explicitly_rejects_hosted_door(self):
        source,xml,opening,door=self.full_xml()
        with self.assertRaisesRegex(WallV6CreateError,"one new isolated Wall"):
            compile_declarative_xml_v6_wall_create(
                source,etree.tostring(xml,encoding="utf8"),
                self.dir/"v06_must_reject.ifc")

    def test_18_v07_rejects_second_door_even_with_same_opening(self):
        source,xml,opening,door=self.full_xml()
        etree.SubElement(xml.find(audit.NS+"Elements"),audit.NS+"Door",
                         attrib={**door.attrib,"id":"additional_door"})
        with self.assertRaisesRegex(ScopedDoorV07Blocked,
                                    "one new opening"):
            compile_declarative_xml_v07_hosted_door_create(
                source,etree.tostring(xml,encoding="utf8"),
                self.dir/"should_reject_two_doors.ifc")

    def test_19_v07_rejects_mixed_edit_of_original_wall(self):
        source,xml,opening,door=self.full_xml()
        other=next(x for x in xml.find(audit.NS+"Elements")
                   if x.tag==audit.NS+"Wall" and x.get("ifcGuid"))
        other.set("x2",str(float(other.get("x2"))+.5))
        with self.assertRaisesRegex(ScopedDoorV07Blocked,
                                    "Only one new opening"):
            compile_declarative_xml_v07_hosted_door_create(
                source,etree.tostring(xml,encoding="utf8"),
                self.dir/"should_reject_mixed.ifc")

    def test_20_v07_rejects_wrong_original_host_guid(self):
        source,xml,opening,door=self.full_xml()
        alternate=next(x.get("id") for x in xml.find(audit.NS+"Elements")
                       if x.tag==audit.NS+"Wall" and x.get("id")!=opening.get("host"))
        opening.set("host",alternate)
        with self.assertRaisesRegex(ScopedDoorV07Blocked,
                                    "exact original public source Wall"):
            compile_declarative_xml_v07_hosted_door_create(
                source,etree.tostring(xml,encoding="utf8"),
                self.dir/"should_reject_other_host.ifc")

    def test_21_v07_rejects_arbitrary_existing_Guid_for_new_door(self):
        source,xml,opening,door=self.full_xml()
        door.set("ifcGuid",i0.HOST_GUID)
        with self.assertRaisesRegex(Exception,"New XML object|GlobalId|schema|SCHEMA"):
            compile_declarative_xml_v07_hosted_door_create(
                source,etree.tostring(xml,encoding="utf8"),
                self.dir/"should_reject_self_assigned_guid.ifc")

    def test_22_old_v05_still_rejects_hosted_create(self):
        source,xml,opening,door=self.full_xml()
        with self.assertRaisesRegex(WallV5Error,"no creates"):
            compile_declarative_xml_v5(
                source,etree.tostring(xml,encoding="utf8"),
                self.dir/"v05_must_reject.ifc")

    def test_23_original_author_score_fraud_rejected(self):
        from tools import bibimbap_matched25_cli as original
        with patch.object(original,"grade_author",return_value={
            "status":"FORGED","original_author_score":1.,
            "original_author_full_mark":True,"original_author_metrics":{},
        }):
            with self.assertRaisesRegex(audit.OriginalHostedDoorV035Blocked,
                                        "grader unavailable"):
                audit.audit_original_test01_pair(audit.ROOT,AUTHOR,DATA)

    def test_24_original_pair_replay_oracle_and_author_score(self):
        r=audit.audit_original_test01_pair(audit.ROOT,AUTHOR,DATA)
        self.assertEqual(r["native_actual_independent_oracle_both_arms"],
                         self.frozen["native_actual_independent_oracle_both_arms"])
        self.assertEqual(r["original_author_I0"],self.frozen["original_author_I0"])
        self.assertEqual(r["original_author_D0"],self.frozen["original_author_D0"])
        self.assertFalse(r["native_whole_IFC_byte_equal"])
        self.assertEqual(file_hash(SOURCE),i0.SOURCE_SHA)

    def test_25_sanitized_report_no_hidden_answers_or_source_IFC(self):
        raw=REPORT.read_text(encoding="utf8").lower()
        for forbidden in ("ground_truth","private_target_guid",
                          "original_public_question_text","model_prompt_body",
                          "ifc_step_source_bytes","credential"):
            self.assertNotIn(forbidden,raw)
        self.assertLess(REPORT.stat().st_size,18000)

if __name__=="__main__":
    unittest.main()
