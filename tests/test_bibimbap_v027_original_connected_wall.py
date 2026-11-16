"""v0.27 real original PUBLIC test_19 isolated Wall deletion and adversarial QA.

All real native IFC modifications are developer-only/test-local. The D0 arm
submits ordinary complete declarative XML with one Wall and its two declared
connections removed. No LLM calls, no model-facing native editor.
"""
from __future__ import annotations

import ast
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ifcopenshell
import ifcopenshell.guid

from src.runtime.connected_wall_delete import (
    PINNED_NORMALIZED_SOURCE_SHA,ConnectedWallPlan,
    preflight_original_connected_wall,verify_original_connected_wall,
    supervised_worker,
)
from src.runtime.ifc_mutations import UnsupportedIFCMutation
from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import XmlSourceEditSession,UnsupportedArm,file_hash
from tools.audit_bibimbap_v026_connected_wall_safety import (
    proposed_complete_connected_wall_xml,exact_declarative_graph_proposal,
)
from tools.audit_bibimbap_v027_original_wall import (
    ROOT,TASK_ID,PARENT_V026_REPORTS,OriginalPublicWallPairAuditBlocked,
    _run_independent_i0,original_product_identity_check,audit_real_original_test19,
)

BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports/bibimbap_v027_original_test19_connected_wall_D0_I0_native_parity_20261116.json"
REPORT_SHA="9cee40c6cd75f5f5fc3c35f1d8ee5b0580681e38820da6178f39c413c71d63b4"
FINAL_IFC_SHA="5a3bf2626f32219cc770b5b8d68277f6e959aa7822a5ad92974931eb47b9941d"


class OriginalPublic19IsolatedConnectedWallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cohort={t["test_id"]:t for t in public_45(AUTHOR,DATA)}
        cls.task=cls.cohort[TASK_ID]
        cls.original=DATA/"ifc"/cls.task["original_source_ifc_relpath"]
        cls.source_sha=file_hash(cls.original)
        cls.temp=TemporaryDirectory(prefix="bmb-v027-original19-tests-")
        cls.folder=Path(cls.temp.name)
        cls.session=XmlSourceEditSession(cls.original,cls.folder/"D0")
        cls.guid,cls.edited=proposed_complete_connected_wall_xml(
            cls.task["public_question"],cls.session.original_xml)
        cls.plan=preflight_original_connected_wall(cls.session.normalized,cls.guid)
        with patch.dict(os.environ,{"BMB_V027_ORIGINAL_CONNECTED_WALL_NATIVE":"1"}):
            cls.d0out=cls.session.call(
                "submit_building_xml",{"xml_text":cls.edited.decode("utf8")})
        cls.i0path=cls.folder/"independent_i0_native_original_mm.ifc"
        cls.i0out=_run_independent_i0(cls.guid,cls.original,cls.i0path,ROOT)
        cls.native_stage=cls.session.folder/"attempt_01"/"candidate_m.ifc"
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def _new_normalized_file(self,configure):
        output=self.folder/("adversarial-"+str(len(list(self.folder.glob("adversarial-*"))))+".ifc")
        f=ifcopenshell.open(str(self.session.normalized))
        configure(f)
        f.write(str(output))
        return output

    def _preflight_modified(self,config):
        original=self._new_normalized_file(config)
        # Pinned source SHA security gate is not weakened in production.
        # In this controlled negative test only, allow the newly generated
        # source's checksum to reach the structural preflight.
        with patch("src.runtime.connected_wall_delete.PINNED_NORMALIZED_SOURCE_SHA",
                   file_hash(original)):
            return preflight_original_connected_wall(original,self.guid)

    def test_01_original_public45_and_source_author_git_revisions(self):
        self.assertEqual(len(self.cohort),45)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)
        self.assertEqual(self.source_sha,self.task["original_ifc_sha256"])
        self.assertEqual(self.task["crud"],"delete")
        self.assertEqual(self.task["category"],"basic")

    def test_02_previous_v026_blocked_reports_unchanged(self):
        for rel,sha in PARENT_V026_REPORTS.items():
            with self.subTest(report=rel):
                self.assertEqual(file_hash(ROOT/rel),sha)

    def test_03_original_public_wall_has_two_exact_native_path_links(self):
        m=ifcopenshell.open(str(self.session.normalized))
        w=m.by_guid(self.guid)
        self.assertTrue(w.is_a("IfcWall"))
        paths=[x for x in m.get_inverse(w) if x.is_a("IfcRelConnectsPathElements")]
        self.assertEqual(len(paths),2)
        self.assertEqual(len({p.RelatingElement.GlobalId for p in paths}),2)
        self.assertEqual(len(self.plan.removed_native_root_guids),9)
        self.assertEqual(len(self.plan.changed_native_root_guids),4)

    def test_04_original_declarative_state_exact_one_wall_plus_connections(self):
        self.assertEqual(len(self.session.original_xml.splitlines())-
                         len(self.edited.splitlines()),3)
        self.assertEqual(self.guid,
             re.search(r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",
                       self.task["public_question"]).group(0))
        self.assertNotIn(self.guid,self.edited.decode("utf8"))
        self.assertNotIn("<Delete",self.edited.decode("utf8"))
        self.assertNotIn("<Command",self.edited.decode("utf8"))
        state=exact_declarative_graph_proposal(self.session,self.edited)
        self.assertEqual(state["original_existing_wall_node_removed"],1)
        self.assertEqual(state["original_existing_connects_edges_removed"],2)

    def test_05_feature_gate_OFF_preserves_v026_fail_closed_behavior(self):
        with TemporaryDirectory(prefix="bmb-v027-default-off-") as td:
            s=XmlSourceEditSession(self.original,Path(td)/"D0")
            with patch.dict(os.environ,{"BMB_V027_ORIGINAL_CONNECTED_WALL_NATIVE":"0"}):
                out=s.call("submit_building_xml",{"xml_text":self.edited.decode("utf8")})
            self.assertEqual(out["status"],"error")
            self.assertIsNone(s.output_ifc)
            self.assertEqual(s.current_xml,s.original_xml)

    def test_06_feature_gate_ON_actual_declarative_IFC_committed(self):
        self.assertEqual(self.d0out["status"],"ok")
        self.assertTrue(self.d0out["native_ifc_committed"])
        self.assertEqual(self.d0out["compile_status"],
                         "COMMITTED_SCOPED_IFC4X3_TOPOLOGY_EDIT")
        self.assertTrue(self.session.output_ifc.is_file())
        self.assertEqual(self.d0out["native_ifc_sha256"],FINAL_IFC_SHA)

    def test_07_independent_I0_separate_native_process_and_no_XML_import(self):
        self.assertEqual(self.i0out["status"],
                         "INDEPENDENT_ORIGINAL_NATIVE_CONNECTED_WALL_DELETE")
        self.assertTrue(self.i0out["original_public_wall_absent"])
        self.assertEqual(self.i0out["original_other_IFC_Product_count"],42)
        source=(ROOT/"tools/bibimbap_v027_independent_wall_i0.py").read_text(encoding="utf8")
        names=[]
        for node in ast.walk(ast.parse(source)):
            if isinstance(node,ast.Import):
                names.extend(x.name for x in node.names)
            elif isinstance(node,ast.ImportFrom):
                names.append(node.module or "")
        self.assertFalse(any(name.startswith("src.runtime") for name in names))
        self.assertNotIn("compile_declarative_xml",source)
        self.assertNotIn("bibimbap_v027_wall_worker",source)

    def test_08_actual_original_D0_and_I0_entire_IFC_sha_byte_equal(self):
        self.assertEqual(file_hash(self.session.output_ifc),file_hash(self.i0path))
        self.assertEqual(file_hash(self.i0path),FINAL_IFC_SHA)
        self.assertEqual(self.report["D0_complete_native_original_mm_IFC_sha256"],FINAL_IFC_SHA)
        self.assertEqual(self.report["I0_complete_native_original_mm_IFC_sha256"],FINAL_IFC_SHA)

    def test_09_independent_actual_original_IfcProduct_identity_parity(self):
        result=original_product_identity_check(
            self.original,self.session.output_ifc,self.guid)
        independent=original_product_identity_check(
            self.original,self.i0path,self.guid)
        self.assertEqual(result,independent)
        self.assertEqual(result["original_product_count"],43)
        self.assertEqual(result["candidate_product_count"],42)
        self.assertTrue(result["all_other_original_native_products_preserved"])

    def test_10_original_author_scorer_both_half_not_full(self):
        d=grade_author(AUTHOR,self.original,self.session.output_ifc,TASK_ID)
        i=grade_author(AUTHOR,self.original,self.i0path,TASK_ID)
        self.assertEqual(d,i)
        self.assertEqual(d["original_author_score"],.5)
        self.assertEqual(d["original_author_metrics"],
                         {"integrity_constraint":0.0,"object_not_exists":1.0})
        self.assertFalse(d["original_author_full_mark"])
        self.assertEqual(d,self.report["unchanged_original_author_D0"])

    def test_11_independent_normalized_native_all_roots_and_STEPS_preserved(self):
        untouched=verify_original_connected_wall(
            self.session.normalized,self.native_stage,self.plan)
        self.assertEqual(untouched,self.report["original_native_surviving_roots_fully_verified"])
        self.assertGreater(untouched,200)

    def test_12_target_wall_two_shapes_product_shape_and_placement_removed(self):
        m=ifcopenshell.open(str(self.native_stage))
        for obj_id in (self.plan.original_product_shape_id,
                       self.plan.original_wall_placement_id,
                       *self.plan.original_shape_rep_ids):
            with self.subTest(entity=obj_id):
                with self.assertRaises(RuntimeError):
                    m.by_id(obj_id)

    def test_13_only_original_wall_product_removed(self):
        original=ifcopenshell.open(str(self.session.normalized))
        output=ifcopenshell.open(str(self.native_stage))
        self.assertEqual(len(original.by_type("IfcProduct")),43)
        self.assertEqual(len(output.by_type("IfcProduct")),42)
        self.assertEqual(len(self.plan.original_shape_rep_ids),2)

    def test_14_unknown_or_wrong_original_native_guid_rejected(self):
        f=ifcopenshell.open(str(self.session.normalized))
        for target in ("0"*22,f.by_type("IfcWindow")[0].GlobalId):
            with self.subTest(target=target),self.assertRaises(UnsupportedIFCMutation):
                preflight_original_connected_wall(self.session.normalized,target)

    def test_15_tampered_native_original_checksum_refused_even_valid_IFC(self):
        def perturb(f):f.by_type("IfcWall")[0].Name="TAMPERED"
        path=self._new_normalized_file(perturb)
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_original_connected_wall(path,self.guid)

    def test_16_native_additional_original_path_link_rejected(self):
        def mutate(f):
            w=f.by_guid(self.guid);other=f.by_type("IfcWall")[0]
            f.create_entity("IfcRelConnectsPathElements",
                GlobalId=ifcopenshell.guid.new(),
                RelatingElement=other,RelatedElement=w)
        with self.assertRaises(UnsupportedIFCMutation):
            self._preflight_modified(mutate)

    def test_17_native_shared_original_owned_PropertySet_rejected(self):
        def mutate(f):
            w=f.by_guid(self.guid)
            prop=next(x for x in f.get_inverse(w)
                      if x.is_a("IfcRelDefinesByProperties"))
            other=next(x for x in f.by_type("IfcWall") if x!=w)
            prop.RelatedObjects=tuple(prop.RelatedObjects)+(other,)
        with self.assertRaises(UnsupportedIFCMutation):
            self._preflight_modified(mutate)

    def test_18_native_unexpected_source_wall_boundary_rejected(self):
        def mutate(f):
            wall=f.by_guid(self.guid)
            f.create_entity("IfcRelSpaceBoundary",
                GlobalId=ifcopenshell.guid.new(),
                RelatingSpace=f.by_type("IfcSpace")[0],
                RelatedBuildingElement=wall,
                PhysicalOrVirtualBoundary="PHYSICAL",
                InternalOrExternalBoundary="INTERNAL")
        with self.assertRaises(UnsupportedIFCMutation):
            self._preflight_modified(mutate)

    def test_19_native_removed_surviving_neighbor_Root_metadata_rejected(self):
        candidate=self._new_normalized_file(lambda f:None)
        # For the candidate use the actual safe output, then forge one
        # unrelated original neighbor Wall's native Name.
        f=ifcopenshell.open(str(self.native_stage))
        f.by_type("IfcWall")[0].Name="UNAUTHORIZED_NEIGHBOR"
        forged=self.folder/"forged-other-root.ifc"
        f.write(str(forged))
        with self.assertRaises(UnsupportedIFCMutation):
            verify_original_connected_wall(self.session.normalized,forged,self.plan)

    def test_20_shared_native_layer_other_representation_removal_rejected(self):
        f=ifcopenshell.open(str(self.native_stage))
        layer=f.by_id(self.plan.presentation_layer_id)
        layer.AssignedItems=tuple(layer.AssignedItems[:-1])
        forged=self.folder/"forged-layer-change.ifc"
        f.write(str(forged))
        with self.assertRaises(UnsupportedIFCMutation):
            verify_original_connected_wall(self.session.normalized,forged,self.plan)

    def test_21_native_shared_storey_member_extra_removal_rejected(self):
        f=ifcopenshell.open(str(self.native_stage))
        rel=next(x for x in f.by_type("IfcRelContainedInSpatialStructure")
                 if x.GlobalId in self.plan.changed_native_root_guids)
        rel.RelatedElements=tuple(rel.RelatedElements[:-1])
        forged=self.folder/"forged-container-change.ifc"
        f.write(str(forged))
        with self.assertRaises(UnsupportedIFCMutation):
            verify_original_connected_wall(self.session.normalized,forged,self.plan)

    def test_22_native_unexpected_new_STEP_entity_rejected(self):
        f=ifcopenshell.open(str(self.native_stage))
        f.create_entity("IfcCartesianPoint",Coordinates=(500.,100.,20.))
        forged=self.folder/"forged-new-step.ifc"
        f.write(str(forged))
        with self.assertRaises(UnsupportedIFCMutation):
            verify_original_connected_wall(self.session.normalized,forged,self.plan)

    def test_23_native_failed_wrong_subprocess_exit_isolated(self):
        with TemporaryDirectory(prefix="bmb-v027-native-child-crash-") as td:
            stage=Path(td)/"empty.ifc"
            stage.touch()
            crash=SimpleNamespace(returncode=3221225477,stdout="",stderr="native crash")
            with patch("src.runtime.connected_wall_delete.subprocess.run",
                       return_value=crash):
                with self.assertRaisesRegex(UnsupportedIFCMutation,"0xc0000005"):
                    supervised_worker(self.session.normalized,self.guid,stage)
            self.assertEqual(stage.stat().st_size,0)

    def test_24_native_child_timeout_isolated_and_rejected(self):
        with TemporaryDirectory(prefix="bmb-v027-native-child-timeout-") as td:
            stage=Path(td)/"empty.ifc";stage.touch()
            with patch("src.runtime.connected_wall_delete.subprocess.run",
                       side_effect=subprocess.TimeoutExpired("child",3)):
                with self.assertRaisesRegex(UnsupportedIFCMutation,"time limit"):
                    supervised_worker(self.session.normalized,self.guid,stage,
                                      timeout_seconds=3)
            self.assertEqual(stage.stat().st_size,0)

    def test_25_native_child_nonempty_stage_and_invalid_receipt_refused(self):
        with TemporaryDirectory(prefix="bmb-v027-native-child-receipt-") as td:
            stage=Path(td)/"nonempty.ifc";stage.write_bytes(b"not empty")
            with self.assertRaises(UnsupportedIFCMutation):
                supervised_worker(self.session.normalized,self.guid,stage)
            stage.unlink();stage.touch()
            corrupted=SimpleNamespace(returncode=0,stdout="invalid-json",stderr="")
            with patch("src.runtime.connected_wall_delete.subprocess.run",
                       return_value=corrupted):
                with self.assertRaises(UnsupportedIFCMutation):
                    supervised_worker(self.session.normalized,self.guid,stage)

    def test_26_XML_remove_only_Wall_dangling_connections_rejected_with_GATE(self):
        with TemporaryDirectory(prefix="bmb-v027-dangling-xml-") as td:
            s=XmlSourceEditSession(self.original,Path(td)/"D0")
            xml=s.original_xml.decode("utf8")
            wall=next(x for x in xml.splitlines(keepends=True)
                      if '<Wall ' in x and 'ifcGuid="'+self.guid+'"' in x)
            with patch.dict(os.environ,{"BMB_V027_ORIGINAL_CONNECTED_WALL_NATIVE":"1"}):
                receipt=s.call("submit_building_xml",{"xml_text":xml.replace(wall,"")})
            self.assertEqual(receipt["status"],"error")
            self.assertIsNone(s.output_ifc)
            self.assertEqual(s.current_xml,s.original_xml)

    def test_27_unrelated_XML_Wall_deleted_with_target_rejected(self):
        with TemporaryDirectory(prefix="bmb-v027-foreign-xml-") as td:
            s=XmlSourceEditSession(self.original,Path(td)/"D0")
            text=self.edited.decode("utf8")
            unrelated=next(x for x in text.splitlines(keepends=True)
                           if '<Wall ' in x)
            with patch.dict(os.environ,{"BMB_V027_ORIGINAL_CONNECTED_WALL_NATIVE":"1"}):
                receipt=s.call("submit_building_xml",
                    {"xml_text":text.replace(unrelated,"")})
            self.assertEqual(receipt["status"],"error")
            self.assertIsNone(s.output_ifc)
            self.assertEqual(s.current_xml,s.original_xml)

    def test_28_non_IFC4X3_original_sources_still_rejected(self):
        for test_id in ("geometry_test_03","geometry_test_05"):
            other=self.cohort[test_id]
            original=DATA/"ifc"/other["original_source_ifc_relpath"]
            with self.subTest(test_id=test_id),TemporaryDirectory() as td:
                with self.assertRaises(UnsupportedArm):
                    XmlSourceEditSession(original,Path(td)/"D0")
                self.assertEqual(file_hash(original),other["original_ifc_sha256"])

    def test_29_original_source_and_new_report_checksum_unchanged(self):
        self.assertEqual(file_hash(REPORT),REPORT_SHA)
        self.assertEqual(file_hash(self.original),self.source_sha)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)

    def test_30_no_original_public_question_or_GUID_in_committed_report(self):
        report_text=REPORT.read_text(encoding="utf8")
        self.assertNotIn(self.guid,report_text)
        self.assertNotIn(self.task["public_question"],report_text)
        self.assertFalse(
            self.report["raw_original_public_target_GUID_or_full_public_question_in_report"])

    def test_31_second_independent_actual_original_audit_byte_identical(self):
        real=audit_real_original_test19(ROOT,AUTHOR,DATA)
        self.assertEqual(real,self.report)
        by=(json.dumps(real,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(sha256(by).hexdigest(),REPORT_SHA)

    def test_32_scientific_denominator_and_NO_real_LLM_overclaim(self):
        self.assertEqual(self.report["frozen_original_public45_denominator"],45)
        self.assertEqual(self.report["prior_frozen_developer_original_native_D0_I0_byte_equal"],8)
        self.assertEqual(self.report["new_cumulative_developer_original_native_D0_I0_byte_equal"],9)
        self.assertEqual(self.report["new_cumulative_original_author_callable_developer_pairs"],7)
        self.assertEqual(self.report["other_original_same_protocol_tasks_not_verified"],36)
        self.assertEqual(self.report["real_model_calls"],0)
        self.assertEqual(self.report["paid_provider_USD"],0)
        self.assertFalse(self.report["real_matching_LLM_XML_vs_Python_causal_performance_proven"])
        self.assertFalse(self.report["all45_semantic_source_and_write_access_parity_proven"])


if __name__=="__main__":
    unittest.main()
