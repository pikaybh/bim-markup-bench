"""v0.36 original public test_03: native I0/D0 Slab Opening and opt-in XML gates.

Permanently retain default Wall-only XSD/binder; the original official/author
grader is invoked only after both saved native IFC candidates are verified.
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

from src.runtime.xml_parser import parse_xml,MarkupParseError
from src.runtime.binder import bind_document
from src.runtime.semantic_graph import BindingError,graph_diff
from src.runtime.experimental_v4_projection import project_ifc_v4
from src.runtime.experimental_v8_slab_opening_create import (
    compile_declarative_xml_v08_slab_opening_create,
    V08NativeSlabOpeningBlocked,
)
from tools import audit_bibimbap_v036_original_slab_opening_pair as audit
from tools import bibimbap_v036_original_slab_opening_i0 as i0
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",
    r"D:\\문서\\D__1_Projects\\202611"))
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
SOURCE=DATA/"ifc"/"basic_tasks.ifc"
REPORT=audit.ROOT/"reports"/"bibimbap_v036_original_test03_slab_opening_D0_I0_20261117.json"
REPORT_SHA="04def65798913aab267b4894f234b2d8ba8f173baff001b3059eed55bdade138"


class V036SlabOpeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=json.loads(REPORT.read_text(encoding="utf8"))

    def setUp(self):
        context=TemporaryDirectory(prefix="bmb-v036-tests-")
        self.addCleanup(context.cleanup)
        self.directory=Path(context.name)

    def metric_source_XML(self):
        metric=self.directory/"source_m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(SOURCE)),"METER").write(str(metric))
        projection=project_ifc_v4(metric)
        doc=etree.fromstring(projection.xml)
        host_id=dict(projection.projected_global_ids)[i0.PUBLIC_HOST_GUID]
        host=next(node for node in doc.find(audit.NS+"Elements")
                  if node.get("id")==host_id)
        self.assertEqual(host.tag,audit.NS+"Slab")
        self.assertEqual(host.attrib["width"],"10.4")
        self.assertEqual(host.attrib["depth"],"10.375")
        opening=etree.SubElement(doc.find(audit.NS+"Elements"),
                 audit.NS+"Opening",attrib={
                     "id":audit.XML_OPENING_ID,
                     "host":host_id,
                     "offset":"2.7","sill":"2.6875",
                     "width":"5","height":"5",
                 })
        return metric,projection,doc,host,opening

    def actual_I0(self):
        result=self.directory/"standalone_I0.ifc"
        record=i0.create_original_test03_slab_opening_i0(SOURCE,result)
        return result,record

    def test_01_original_public_task_source_and_denominator_pinned(self):
        r=self.evidence
        self.assertEqual(r["original_public_task_id"],"test_03")
        self.assertEqual(r["original_45_intention_to_test_denominator"],45)
        self.assertEqual(r["original_question_sha256"],audit.QUESTION_SHA)
        self.assertEqual(r["original_native_IFC_source_sha256"],i0.SOURCE_SHA)
        self.assertTrue(r["original_host_kind_real_native_IfcSlab"])
        self.assertEqual(r["preregistered_5x5_world_center_xy_m"],[5.,5.0125])
        self.assertEqual(r["preregistered_opening_world_bbox_m"],[
            2.5,2.5125,3.7,7.5,7.5125,4.2])

    def test_02_not_a_causal_LLM_result_and_no_full_native_byte_parity(self):
        r=self.evidence
        self.assertTrue(r["D0_I0_actual_native_semantic_equivalence"])
        self.assertFalse(r["D0_I0_entire_IFC_byte_identical"])
        self.assertEqual(r["historical_developer_native_byte_equal_11_unchanged"],11)
        self.assertEqual(r["original_Create_semantic_only_developer_pairs"],5)
        self.assertEqual(r["original_Create_remaining_without_native_semantic_pair"],10)
        self.assertEqual(r["original45_full_task_relevant_read_parity_proven"],0)
        self.assertEqual(r["original45_full_native_write_parity_proven"],0)
        self.assertEqual(r["matched_real_LLM_D_I_trials"],0)
        self.assertEqual(r["paid_LLM_provider_calls"],0)
        self.assertFalse(r["causal_LLM_representation_comparison_permitted"])
        self.assertFalse(r["new_slab_opening_compiler_registered_in_trial_host"])

    def test_03_original_author_score_nonfull_both_identical_no_retuning(self):
        r=self.evidence
        self.assertEqual(r["original_author_D0"],r["original_author_I0"])
        self.assertFalse(r["original_author_D0_full_mark"])
        self.assertFalse(r["original_author_I0_full_mark"])
        self.assertEqual(r["original_author_D0"]["status"],"AUTHOR_SCORED")
        self.assertEqual(r["original_author_D0"]["original_author_score"],0.916675)
        self.assertEqual(r["original_author_D0"]["original_author_metrics"],{
            "object_exists":1.0,"right_dimensions":1.0,
            "right_location":1.0,"integrity_constraint":.6667,
        })
        self.assertTrue(r["original_benchmark_task_under_determined_choices_preregistered"])

    def test_04_independent_native_scene_and_actual_void(self):
        o=self.evidence["both_actual_native_oracles"]
        self.assertTrue(o["new_void_hosted_by_original_IfcSlab_not_wall"])
        self.assertTrue(o["native_IfcRelVoidsElement_exists"])
        self.assertTrue(o["existing_containment_and_aggregate_relations_unchanged"])
        self.assertEqual(o["original_IfcRoot_count"],358)
        self.assertEqual(o["original_IfcProduct_count"],43)
        self.assertEqual(o["original_mesh_bearing_products"],39)
        self.assertEqual(o["original_nonhost_mesh_bearing_products_unchanged"],38)
        self.assertEqual(o["original_nonhost_triangle_face_count"],1640)
        self.assertEqual(o["original_slab_world_bbox_m"],[
            -.2,-.175,3.8,10.2,10.2,4.1])
        self.assertEqual(o["native_opening_world_bbox_m"],[
            2.5,2.5125,3.7,7.5,7.5125,4.2])
        self.assertEqual(o["original_slab_volume_m3"],32.37)
        self.assertEqual(o["new_slab_volume_m3"],24.87)
        self.assertEqual(o["physically_removed_slab_volume_m3"],7.5)
        self.assertEqual(o["native_void_tool_volume_m3"],12.5)
        self.assertEqual(o["original_slab_triangles_before"],12)
        self.assertEqual(o["original_slab_triangles_after"],32)
        self.assertFalse(o["original_source_full_STEP_entity_preservation_claimed"])

    def test_05_frozen_result_and_all_ancestor_hashes(self):
        self.assertEqual(file_hash(REPORT),REPORT_SHA)
        self.assertEqual(file_hash(SOURCE),i0.SOURCE_SHA)
        for relative,pin in audit.PRIOR:
            self.assertEqual(file_hash(audit.ROOT/relative),pin)

    def test_06_I0_does_not_import_D0_XML_or_grader(self):
        text=Path(i0.__file__).read_text(encoding="utf8")
        imports=[]
        for node in ast.walk(ast.parse(text)):
            if isinstance(node,ast.Import):
                imports.extend(x.name for x in node.names)
            elif isinstance(node,ast.ImportFrom):
                imports.append(node.module or "")
        forbidden=("experimental_v8","experimental_v7","xml_parser","binder",
                   "ifc_projection","grade_author","matched25","audit_bibimbap")
        self.assertFalse([x for x in imports if any(f in x for f in forbidden)])
        self.assertEqual(i0.OPENING_CENTER_M,(5.,5.0125,3.7))
        self.assertEqual(i0.OPENING_WIDTH_M,5.)
        self.assertEqual(i0.OPENING_DEPTH_M,5.)

    def test_07_actual_original_I0_and_independent_saved_IFC_oracle(self):
        source_sha=file_hash(SOURCE)
        file,result=self.actual_I0()
        self.assertEqual(file_hash(file),result["candidate_original_mm_IFC_sha256"])
        verified=audit.actual_original_native_slab_opening_oracle(
            SOURCE,file,result["new_native_opening_guid"])
        self.assertEqual(verified,self.evidence["both_actual_native_oracles"])
        self.assertEqual(file_hash(SOURCE),source_sha)

    def test_08_I0_rejects_mutated_original_source(self):
        corrupted=self.directory/"changed_source.ifc"
        shutil.copy2(SOURCE,corrupted)
        with corrupted.open("ab") as dest:dest.write(b" ")
        target=self.directory/"no_new.ifc"
        with self.assertRaisesRegex(i0.IndependentSlabOpeningI0Blocked,"sha256"):
            i0.create_original_test03_slab_opening_i0(corrupted,target)
        self.assertFalse(target.exists())

    def test_09_I0_rejects_preexisting_result_and_never_overwrites(self):
        dest=self.directory/"existing.ifc"
        dest.write_bytes(b"do not overwrite evidence")
        with self.assertRaisesRegex(i0.IndependentSlabOpeningI0Blocked,"fresh"):
            i0.create_original_test03_slab_opening_i0(SOURCE,dest)
        self.assertEqual(dest.read_bytes(),b"do not overwrite evidence")

    def test_10_I0_rejects_source_as_destination(self):
        with self.assertRaisesRegex(i0.IndependentSlabOpeningI0Blocked,"fresh"):
            i0.create_original_test03_slab_opening_i0(SOURCE,SOURCE)
        self.assertEqual(file_hash(SOURCE),i0.SOURCE_SHA)

    def test_11_native_oracle_rejects_no_opening(self):
        copy=self.directory/"no_op.ifc"
        shutil.copy2(SOURCE,copy)
        with self.assertRaisesRegex(audit.OriginalSlabOpeningV036Blocked,
                                    "Exactly one new IFC product"):
            audit.actual_original_native_slab_opening_oracle(SOURCE,copy)

    def test_12_native_oracle_rejects_fake_claimed_GUID(self):
        f,reference=self.actual_I0()
        with self.assertRaisesRegex(audit.OriginalSlabOpeningV036Blocked,
                                    "Claimed newly authored opening GUID"):
            audit.actual_original_native_slab_opening_oracle(
                SOURCE,f,claimed_opening_guid="0"*22)

    def test_13_native_oracle_rejects_missing_void_relationship(self):
        f,reference=self.actual_I0()
        m=ifcopenshell.open(str(f))
        ifcopenshell.api.feature.remove_feature(
            m,feature=m.by_guid(reference["new_native_opening_guid"]))
        m.write(str(f))
        with self.assertRaises(audit.OriginalSlabOpeningV036Blocked):
            audit.actual_original_native_slab_opening_oracle(SOURCE,f)

    def test_14_native_oracle_rejects_wrong_cut_location(self):
        f,reference=self.actual_I0()
        model=ifcopenshell.open(str(f))
        metric=ifcopenshell.util.unit.convert_file_length_units(model,"METER")
        opening=metric.by_guid(reference["new_native_opening_guid"])
        mat=np.eye(4,dtype=float)
        mat[:3,3]=[6.,5.0125,3.7]
        ifcopenshell.api.geometry.edit_object_placement(
            metric,product=opening,matrix=mat)
        ifcopenshell.util.unit.convert_file_length_units(
            metric,"MILLIMETER").write(str(f))
        with self.assertRaisesRegex(audit.OriginalSlabOpeningV036Blocked,
                                    "geometry bbox"):
            audit.actual_original_native_slab_opening_oracle(SOURCE,f)

    def test_15_native_oracle_rejects_wrong_physically_cut_area(self):
        f,reference=self.actual_I0()
        m=ifcopenshell.open(str(f))
        opening=m.by_guid(reference["new_native_opening_guid"])
        solid=next(x for rep in opening.Representation.Representations
                   for x in rep.Items if x.is_a("IfcExtrudedAreaSolid"))
        solid.SweptArea.XDim=4000.
        m.write(str(f))
        with self.assertRaises(audit.OriginalSlabOpeningV036Blocked):
            audit.actual_original_native_slab_opening_oracle(SOURCE,f)

    def test_16_pinned_default_XML_schema_still_rejects_Slab_host(self):
        metric,projection,root,slab,opening=self.metric_source_XML()
        blob=etree.tostring(root,encoding="utf8")
        with self.assertRaises(MarkupParseError):
            parse_xml(blob,expected_source_sha256=projection.source.source_sha256)
        # A versioned schema can admit this without changing the original.
        parsed=parse_xml(blob,
            expected_source_sha256=projection.source.source_sha256,
            schema_variant="slab_opening_v08")
        self.assertEqual(len(parsed.elements),len(etree.fromstring(projection.xml).find(audit.NS+"Elements"))+1)

    def test_17_pinned_default_typed_binder_still_rejects_Slab(self):
        metric,projection,root,slab,opening=self.metric_source_XML()
        parsed=parse_xml(etree.tostring(root,encoding="utf8"),
            expected_source_sha256=projection.source.source_sha256,
            schema_variant="slab_opening_v08")
        with self.assertRaises(BindingError):
            bind_document(parsed,projection=projection,verify_native_edges=False)
        allowed=bind_document(parsed,projection=projection,
                              verify_native_edges=False,
                              allow_slab_opening_hosts=True)
        base=bind_document(parse_xml(projection.xml,
             expected_source_sha256=projection.source.source_sha256),projection=projection)
        delta=graph_diff(base.graph,allowed.graph)
        self.assertEqual(len(delta.added_nodes),1)
        self.assertEqual(len(delta.added_edges),1)
        self.assertEqual(delta.added_edges[0].relation,"host_void")
        self.assertEqual(allowed.graph.by_id()[delta.added_edges[0].source].kind,"Slab")

    def test_18_v08_schema_still_accepts_original_Wall_hosted_openings(self):
        metric,projection,root,slab,opening=self.metric_source_XML()
        pre=parse_xml(projection.xml,
            expected_source_sha256=projection.source.source_sha256)
        alternative=parse_xml(projection.xml,
            expected_source_sha256=projection.source.source_sha256,
            schema_variant="slab_opening_v08")
        self.assertEqual(len(pre.elements),len(alternative.elements))
        self.assertEqual(bind_document(pre,projection=projection).graph.fingerprint,
                         bind_document(alternative,projection=projection).graph.fingerprint)

    def test_19_v08_schema_variants_never_accept_arbitrary_path(self):
        metric,projection,root,slab,opening=self.metric_source_XML()
        blob=etree.tostring(root,encoding="utf8")
        with self.assertRaisesRegex(ValueError,"Unrecognized|untrusted"):
            parse_xml(blob,expected_source_sha256=projection.source.source_sha256,
                      schema_variant="D:/temp/attacker.xml")

    def test_20_v08_rejects_unresolved_or_wrong_class_host(self):
        metric,projection,root,slab,opening=self.metric_source_XML()
        opening.set("host","nonexistent_slab_id")
        with self.assertRaises(MarkupParseError):
            parse_xml(etree.tostring(root,encoding="utf8"),
                expected_source_sha256=projection.source.source_sha256,
                schema_variant="slab_opening_v08")

    def test_21_v08_binder_rejects_opening_outside_Slab_X_extent(self):
        metric,projection,root,slab,opening=self.metric_source_XML()
        opening.set("offset","7")
        parsed=parse_xml(etree.tostring(root,encoding="utf8"),
            expected_source_sha256=projection.source.source_sha256,
            schema_variant="slab_opening_v08")
        with self.assertRaisesRegex(BindingError,"Slab's XY footprint"):
            bind_document(parsed,projection=projection,verify_native_edges=False,
                          allow_slab_opening_hosts=True)

    def test_22_v08_binder_rejects_opening_outside_Slab_Y_extent(self):
        metric,projection,root,slab,opening=self.metric_source_XML()
        opening.set("sill","7")
        parsed=parse_xml(etree.tostring(root,encoding="utf8"),
            expected_source_sha256=projection.source.source_sha256,
            schema_variant="slab_opening_v08")
        with self.assertRaisesRegex(BindingError,"Slab's XY footprint"):
            bind_document(parsed,projection=projection,verify_native_edges=False,
                          allow_slab_opening_hosts=True)

    def test_23_v08_compiler_rejects_second_Slab_opening(self):
        metric,projection,root,slab,opening=self.metric_source_XML()
        etree.SubElement(root.find(audit.NS+"Elements"),audit.NS+"Opening",
                         attrib={**opening.attrib,"id":"additional_opening"})
        target=self.directory/"double_rejected.ifc"
        with self.assertRaisesRegex(V08NativeSlabOpeningBlocked,"Only one new"):
            compile_declarative_xml_v08_slab_opening_create(
                metric,etree.tostring(root,encoding="utf8"),target)
        self.assertFalse(target.exists())

    def test_24_v08_compiler_rejects_mixed_original_Slab_edit(self):
        metric,projection,root,slab,opening=self.metric_source_XML()
        slab.set("width","10.3")
        target=self.directory/"mixed_rejected.ifc"
        with self.assertRaisesRegex(V08NativeSlabOpeningBlocked,"Only one new"):
            compile_declarative_xml_v08_slab_opening_create(
                metric,etree.tostring(root,encoding="utf8"),target)
        self.assertFalse(target.exists())

    def test_25_v08_compiler_rejects_new_Opening_self_assigned_IFC_GUID(self):
        metric,projection,root,slab,opening=self.metric_source_XML()
        opening.set("ifcGuid",i0.PUBLIC_HOST_GUID)
        with self.assertRaises(Exception):
            compile_declarative_xml_v08_slab_opening_create(
                metric,etree.tostring(root,encoding="utf8"),
                self.directory/"fake_guid_rejected.ifc")

    def test_26_v08_compiler_rejects_extra_Door_not_requested(self):
        metric,projection,root,slab,opening=self.metric_source_XML()
        etree.SubElement(root.find(audit.NS+"Elements"),audit.NS+"Door",
                         attrib={"id":"unrequested_door","opening":opening.get("id"),
                                 "width":"1","height":"2"})
        with self.assertRaisesRegex(V08NativeSlabOpeningBlocked,"Only one new"):
            compile_declarative_xml_v08_slab_opening_create(
                metric,etree.tostring(root,encoding="utf8"),
                self.directory/"extra_door_rejected.ifc")

    def test_27_v08_compiler_rejects_wrong_original_Slab_host(self):
        metric,projection,root,slab,opening=self.metric_source_XML()
        alternate=next(x for x in root.find(audit.NS+"Elements")
                       if x.tag==audit.NS+"Slab" and x.get("id")!=slab.get("id"))
        opening.set("host",alternate.get("id"))
        with self.assertRaisesRegex(V08NativeSlabOpeningBlocked,
                                    "original public source IfcSlab"):
            compile_declarative_xml_v08_slab_opening_create(
                metric,etree.tostring(root,encoding="utf8"),
                self.directory/"wrong_host_rejected.ifc")

    def test_28_actual_full_declarative_D0_native_and_independent_oracle(self):
        before=file_hash(SOURCE)
        p=self.directory/"replayed_XML_D0.ifc"
        r=audit.compile_full_xml_slab_D0(SOURCE,p)
        self.assertEqual(r["status"],"V08_SCOPED_FULL_XML_SLAB_OPENING_COMMITTED")
        self.assertEqual(r["schema_variant"],"slab_opening_v08")
        verified=audit.actual_original_native_slab_opening_oracle(
            SOURCE,p,r["created_IfcOpeningElement_GUID"])
        self.assertEqual(verified,self.evidence["both_actual_native_oracles"])
        self.assertEqual(file_hash(SOURCE),before)

    def test_29_replay_both_arms_and_original_author_grade_unchanged(self):
        result=audit.audit_original_test03_pair(audit.ROOT,AUTHOR,DATA)
        self.assertEqual(result["both_actual_native_oracles"],
                         self.evidence["both_actual_native_oracles"])
        self.assertEqual(result["original_author_D0"],self.evidence["original_author_D0"])
        self.assertEqual(result["original_author_I0"],self.evidence["original_author_I0"])
        self.assertFalse(result["D0_I0_entire_IFC_byte_identical"])
        self.assertEqual(file_hash(SOURCE),i0.SOURCE_SHA)

    def test_30_author_grader_forgery_is_not_a_success(self):
        from tools import bibimbap_matched25_cli as original
        with patch.object(original,"grade_author",return_value={
            "status":"FORGED","original_author_score":1.,
            "original_author_full_mark":True,"original_author_metrics":{},
        }):
            with self.assertRaisesRegex(audit.OriginalSlabOpeningV036Blocked,
                                        "grader produced no valid result"):
                audit.audit_original_test03_pair(audit.ROOT,AUTHOR,DATA)

    def test_31_existing_frozen_evidence_cannot_be_overwritten(self):
        self.assertTrue(REPORT.is_file())
        with self.assertRaises(FileExistsError):
            with REPORT.open("xb") as output:
                output.write(b"must not overwrite")
        self.assertEqual(file_hash(REPORT),REPORT_SHA)

    def test_32_sanitized_nonblinded_report_has_no_hidden_GT_or_raw_IFC(self):
        text=REPORT.read_text(encoding="utf8").lower()
        for term in ("ground_truth","private_target_guid","source_step_entire_bytes",
                     "raw_model_prompt","user_credential","hidden_grader_reference_ifc"):
            self.assertNotIn(term,text)
        self.assertLess(REPORT.stat().st_size,18000)


if __name__=="__main__":
    unittest.main()
