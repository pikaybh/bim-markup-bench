"""v0.27 real original PUBLIC test_19 supervised native Wall parity tests.

The positive case invokes the genuine complete declarative XML compiler, a
one-shot native Windows worker and an independent Python I0. The negatives
verify native source, shared relationships, whole IFC Root/STEP data, both
connections, source-schema admission, child crash/timeout and transaction
fail-closed behavior. No LLM/model calls or original source modification.
"""
from __future__ import annotations

import ast
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

import ifcopenshell

from src.runtime.connected_wall_delete import (
    PINNED_NORMALIZED_ORIGINAL_IFC_SHA,
    ConnectedWallPlan,
    UnsupportedIFCMutation,
    preflight_original_connected_wall,
    supervised_native_child,
    verify_original_connected_wall,
    _model_orphans,
)
from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import XmlSourceEditSession,UnsupportedArm,file_hash
from tools.audit_bibimbap_v026_connected_wall_safety import (
    proposed_complete_connected_wall_xml,exact_declarative_graph_proposal,
)
from tools.audit_bibimbap_v027_original_wall_parity import (
    ROOT,TASK_ID,FROZEN_PRIOR_REPORTS,
    audit_original19_native_pair,independent_original_public_native_oracle,
)
from tools.bibimbap_v027_independent_connected_wall_i0 import (
    independent_original_connected_wall_i0,
)

BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports/bibimbap_v027_original_test19_complete_native_D0_I0_parity_20261116.json"
REPORT_SHA="5f1d3601910048e514678869f86868bca90cf2073e23883463bd7a89233c0f04"
CANDIDATE_SHA="5a3bf2626f32219cc770b5b8d68277f6e959aa7822a5ad92974931eb47b9941d"


class OriginalPublic19ConnectedWallParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all45={x["test_id"]:x for x in public_45(AUTHOR,DATA)}
        cls.case=cls.all45[TASK_ID]
        cls.source=DATA/"ifc"/cls.case["original_source_ifc_relpath"]
        cls.srcsha=file_hash(cls.source)
        original=ifcopenshell.open(str(cls.source))
        cls.guid=re.search(
            r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",
            cls.case["public_question"]).group(0)
        cls.original=original
        cls.temp=TemporaryDirectory(prefix="bmb-v027-original19-qa-")
        cls.folder=Path(cls.temp.name)
        cls.d=XmlSourceEditSession(cls.source,cls.folder/"D0")
        cls.public_guid,cls.xml=proposed_complete_connected_wall_xml(
            cls.case["public_question"],cls.d.original_xml)
        cls.graph=exact_declarative_graph_proposal(cls.d,cls.xml)
        cls.resp=cls.d.call("submit_building_xml",{"xml_text":cls.xml.decode("utf8")})
        cls.i0path=cls.folder/"independent_I0_original_mm.ifc"
        cls.independent=independent_original_connected_wall_i0(
            cls.source,cls.guid,cls.i0path)
        cls.before=ifcopenshell.open(str(cls.d.normalized))
        cls.after=ifcopenshell.open(
            str(cls.d.folder/"attempt_01"/"candidate_m.ifc"))
        cls.plan=preflight_original_connected_wall(cls.before,cls.guid)
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def _before(self):
        return ifcopenshell.open(str(self.d.normalized))

    def _after(self):
        return ifcopenshell.open(
            str(self.d.folder/"attempt_01"/"candidate_m.ifc"))

    def test_01_real_public45_source_and_upstream_git_shas_pinned(self):
        self.assertEqual(len(self.all45),45)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)
        self.assertEqual(file_hash(self.source),self.case["original_ifc_sha256"])
        self.assertEqual(self.case["crud"],"delete")
        self.assertEqual(self.case["category"],"basic")

    def test_02_all_frozen_prior_reports_unchanged(self):
        for rel,sha in FROZEN_PRIOR_REPORTS.items():
            with self.subTest(rel=rel):
                self.assertEqual(file_hash(ROOT/rel),sha)
                self.assertEqual(
                    self.report["frozen_v024_v025_v026_evidence_sha256"][rel],sha)

    def test_03_public_source_wall_has_two_distinct_connected_neighbors(self):
        self.assertEqual(self.public_guid,self.guid)
        wall=self.before.by_guid(self.guid)
        connections=[x for x in self.before.get_inverse(wall)
                     if x.is_a("IfcRelConnectsPathElements")]
        self.assertEqual(len(connections),2)
        self.assertTrue(all(x.RelatedElement==wall for x in connections))
        self.assertEqual(len(self.plan.neighbor_wall_guids),2)
        self.assertEqual(self.plan.wall_guid,self.guid)

    def test_04_D0_is_full_XML_state_not_imperative_commands(self):
        before=self.d.original_xml.decode("utf8")
        after=self.xml.decode("utf8")
        self.assertEqual(len(before.splitlines())-len(after.splitlines()),3)
        self.assertNotIn(self.guid,after)
        self.assertIn("<Wall",after)
        self.assertIn("<Connects",after)
        self.assertNotIn("<Delete",after)
        self.assertNotIn("<Command",after)
        self.assertNotIn("<Move",after)
        self.assertEqual(self.graph["original_existing_wall_node_removed"],1)
        self.assertEqual(self.graph["original_existing_connects_edges_removed"],2)

    def test_05_original_legacy_Wall_only_is_still_schema_rejected(self):
        with TemporaryDirectory(prefix="bmb-v027-illegal-dangling-connect-") as td:
            d=XmlSourceEditSession(self.source,Path(td)/"D0")
            orig=d.original_xml.decode("utf8")
            line=next(x for x in orig.splitlines(keepends=True)
                      if "<Wall " in x and 'ifcGuid="'+self.guid+'"' in x)
            result=d.call("submit_building_xml",{"xml_text":orig.replace(line,"")})
            self.assertEqual(result["status"],"error")
            self.assertIsNone(d.output_ifc)
            self.assertEqual(d.current_xml,d.original_xml)

    def test_06_original_real_D0_compiler_now_native_commits(self):
        self.assertEqual(self.resp["status"],"ok")
        self.assertTrue(self.resp["native_ifc_committed"])
        self.assertEqual(self.resp["compile_status"],
                         "COMMITTED_SCOPED_IFC4X3_WALL_EDIT")
        self.assertTrue(self.d.output_ifc.is_file())
        self.assertEqual(self.resp["native_ifc_sha256"],CANDIDATE_SHA)

    def test_07_independent_I0_only_uses_native_API_not_XML_compiler(self):
        self.assertEqual(self.independent["status"],
            "INDEPENDENT_DEVELOPER_ORIGINAL_CONNECTED_WALL_I0_NATIVE_OUTPUT")
        self.assertTrue(self.independent["original_public_Wall_absent"])
        s=(ROOT/"tools/bibimbap_v027_independent_connected_wall_i0.py").read_text(
            encoding="utf8")
        imports=[]
        for node in ast.walk(ast.parse(s)):
            if isinstance(node,ast.Import):
                imports.extend(a.name for a in node.names)
            elif isinstance(node,ast.ImportFrom):
                imports.append(node.module or "")
        self.assertFalse(any(x.startswith("src.runtime") for x in imports))
        self.assertNotIn("compile_declarative_xml",s)
        self.assertNotIn("bibimbap_v027_wall_native_worker",s)

    def test_08_D0_I0_entire_native_IFC_bytes_identical(self):
        self.assertEqual(file_hash(self.d.output_ifc),CANDIDATE_SHA)
        self.assertEqual(file_hash(self.i0path),CANDIDATE_SHA)
        self.assertEqual(
            self.report["D0_new_original_native_entire_IFC_SHA256"],CANDIDATE_SHA)
        self.assertEqual(
            self.report["I0_independent_original_native_entire_IFC_SHA256"],CANDIDATE_SHA)

    def test_09_independent_original_native_products_oracle_both_arms(self):
        d=independent_original_public_native_oracle(
            self.source,self.d.output_ifc,self.guid)
        i=independent_original_public_native_oracle(
            self.source,self.i0path,self.guid)
        self.assertEqual(d,i)
        self.assertEqual(d["original_IfcProducts"],43)
        self.assertEqual(d["result_IfcProducts"],42)
        self.assertTrue(d["every_remaining_original_product_GUID_and_class_preserved"])
        self.assertEqual(d["original_neighbour_walls_preserved"],2)

    def test_10_original_author_scores_both_half_not_full(self):
        d=grade_author(AUTHOR,self.source,self.d.output_ifc,TASK_ID)
        i=grade_author(AUTHOR,self.source,self.i0path,TASK_ID)
        self.assertEqual(d,i)
        self.assertEqual(d["original_author_score"],.5)
        self.assertEqual(d["original_author_metrics"],
                         {"object_not_exists":1.0,"integrity_constraint":0.0})
        self.assertFalse(d["original_author_full_mark"])
        self.assertEqual(d,self.report["unchanged_original_author_D0_score"])
        self.assertEqual(i,self.report["unchanged_original_author_I0_score"])

    def test_11_full_original_Root_STEP_and_owned_geometry_gate(self):
        unchanged=verify_original_connected_wall(self.before,self.after,self.plan)
        self.assertGreater(unchanged,100)
        self.assertEqual(len(self.plan.deleted_root_guids),9)
        self.assertEqual(len(self.plan.modified_root_guids),4)

    def test_12_native_original_shape_placement_removed_and_no_new_orphans(self):
        old={x.id():x.is_a() for x in self.before}
        new={x.id():x.is_a() for x in self.after}
        expected=set(self.plan.representation_ids)|{
            self.plan.product_shape_id,self.plan.placement_id}
        self.assertFalse(expected&new.keys())
        self.assertEqual(_model_orphans(self.before),_model_orphans(self.after))
        self.assertEqual(set(_model_orphans(self.after).values()),{0})
        self.assertEqual(len(self.after.by_type("IfcProduct")),42)

    def test_13_native_unknown_target_or_wrong_IfcProduct_type_rejected(self):
        before=self._before()
        for wrong in ("0"*22,before.by_type("IfcDoor")[0].GlobalId):
            with self.subTest(wrong=wrong),self.assertRaises(UnsupportedIFCMutation):
                preflight_original_connected_wall(before,wrong)

    def test_14_native_shared_Pset_or_second_owner_rejected(self):
        before=self._before()
        wall=before.by_guid(self.guid)
        rel=next(x for x in before.get_inverse(wall)
                 if x.is_a("IfcRelDefinesByProperties"))
        rel.RelatedObjects=tuple(rel.RelatedObjects)+(
            before.by_type("IfcWall")[0],)
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_original_connected_wall(before,self.guid)

    def test_15_native_extra_space_boundary_dependency_rejected(self):
        before=self._before()
        before.create_entity("IfcRelSpaceBoundary",
            GlobalId=ifcopenshell.guid.new(),
            RelatingSpace=before.by_type("IfcSpace")[0],
            RelatedBuildingElement=before.by_guid(self.guid),
            PhysicalOrVirtualBoundary="PHYSICAL",
            InternalOrExternalBoundary="INTERNAL")
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_original_connected_wall(before,self.guid)

    def test_16_native_shared_geometry_ownership_rejected(self):
        before=self._before()
        target=before.by_guid(self.guid)
        alternate=next(x for x in before.by_type("IfcWall")
                       if x.GlobalId!=self.guid)
        # No original source file is written; this is a malicious in-memory
        # simulated native sharing violation.
        alternate.Representation=target.Representation
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_original_connected_wall(before,self.guid)

    def test_17_native_wrong_path_connection_direction_rejected(self):
        before=self._before()
        target=before.by_guid(self.guid)
        link=next(x for x in before.get_inverse(target)
                  if x.is_a("IfcRelConnectsPathElements"))
        link.RelatedElement=link.RelatingElement
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_original_connected_wall(before,self.guid)

    def test_18_child_wrong_original_sha_fail_closed_before_launch(self):
        with TemporaryDirectory(prefix="bmb-v027-wrong-source-") as td:
            stage=Path(td)/"stage.ifc"
            with self.assertRaises(UnsupportedIFCMutation):
                supervised_native_child(
                    self.d.normalized,stage,self.guid,"0"*64)
            self.assertFalse(stage.exists())

    def test_19_child_process_CRASH_exit_code_fail_closed(self):
        with TemporaryDirectory(prefix="bmb-v027-crash-sim-") as td:
            stage=Path(td)/"stage.ifc"
            process=subprocess.CompletedProcess(
                args=[],returncode=3221225477,stdout=b"",stderr=b"")
            with mock.patch(
                "src.runtime.connected_wall_delete.subprocess.run",
                return_value=process):
                with self.assertRaises(UnsupportedIFCMutation):
                    supervised_native_child(
                        self.d.normalized,stage,self.guid,
                        PINNED_NORMALIZED_ORIGINAL_IFC_SHA)
            self.assertFalse(stage.exists())
            self.assertFalse(any(Path(td).glob("*.child.ifc")))

    def test_20_child_process_TIMEOUT_fail_closed(self):
        with TemporaryDirectory(prefix="bmb-v027-timeout-sim-") as td:
            stage=Path(td)/"stage.ifc"
            with mock.patch(
                "src.runtime.connected_wall_delete.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd=["python"],timeout=.1)):
                with self.assertRaises(UnsupportedIFCMutation):
                    supervised_native_child(
                        self.d.normalized,stage,self.guid,
                        PINNED_NORMALIZED_ORIGINAL_IFC_SHA,timeout_seconds=1)
            self.assertFalse(stage.exists())

    def test_21_child_success_without_real_candidate_file_rejected(self):
        with TemporaryDirectory(prefix="bmb-v027-fake-child-") as td:
            stage=Path(td)/"stage.ifc"
            fabricated=json.dumps({
                "mode":"fixed_source_bound_deep_cleanup",
                "source_sha256":PINNED_NORMALIZED_ORIGINAL_IFC_SHA,
                "original_Wall_absent":True,"product_count":42,
                "orphan_rep_count":0,"orphan_pds_count":0,"orphan_place_count":0,
                "result_sha256":"0"*64,
            })
            cp=subprocess.CompletedProcess(
                args=[],returncode=0,stdout=(
                    "V027_WORKER_JSON "+fabricated+"\n").encode(),stderr=b"")
            with mock.patch(
                "src.runtime.connected_wall_delete.subprocess.run",return_value=cp):
                with self.assertRaises(UnsupportedIFCMutation):
                    supervised_native_child(
                        self.d.normalized,stage,self.guid,
                        PINNED_NORMALIZED_ORIGINAL_IFC_SHA)
            self.assertFalse(stage.exists())

    def test_22_unrelated_surviving_IfcWall_name_mutation_rejected(self):
        after=self._after()
        after.by_type("IfcWall")[0].Name="FORGED_UNRELATED_WALL"
        with self.assertRaises(UnsupportedIFCMutation):
            verify_original_connected_wall(self.before,after,self.plan)

    def test_23_second_unrelated_native_IfcProduct_deletion_rejected(self):
        after=self._after()
        after.remove(after.by_type("IfcDoor")[0])
        with self.assertRaises(UnsupportedIFCMutation):
            verify_original_connected_wall(self.before,after,self.plan)

    def test_24_original_shared_layer_other_member_removed_rejected(self):
        after=self._after()
        layer=after.by_id(self.plan.shared_layer_id)
        layer.AssignedItems=tuple(layer.AssignedItems[:-1])
        with self.assertRaises(UnsupportedIFCMutation):
            verify_original_connected_wall(self.before,after,self.plan)

    def test_25_original_modified_shared_classification_metadata_rejected(self):
        after=self._after()
        rel=next(x for x in after.by_type("IfcRelAssociatesClassification")
                 if x.GlobalId in self.plan.modified_root_guids)
        rel.Name="FORGED_RELATION_NAME"
        with self.assertRaises(UnsupportedIFCMutation):
            verify_original_connected_wall(self.before,after,self.plan)

    def test_26_unrelated_window_deleted_in_same_XML_state_rejected(self):
        with TemporaryDirectory(prefix="bmb-v027-illegal-extra-edit-") as td:
            d=XmlSourceEditSession(self.source,Path(td)/"D0")
            text=self.xml.decode("utf8")
            line=next(x for x in text.splitlines(keepends=True) if "<Window " in x)
            out=d.call("submit_building_xml",{"xml_text":text.replace(line,"")})
            self.assertEqual(out["status"],"error")
            self.assertIsNone(d.output_ifc)
            self.assertEqual(d.current_xml,d.original_xml)

    def test_27_other_original_IFC2X3_and_IFC4_source_still_rejected(self):
        for tid in ("geometry_test_03","geometry_test_05"):
            c=self.all45[tid]
            path=DATA/"ifc"/c["original_source_ifc_relpath"]
            with self.subTest(tid=tid),TemporaryDirectory() as td:
                with self.assertRaises(UnsupportedArm):
                    XmlSourceEditSession(path,Path(td)/"D0")

    def test_28_report_pins_original_data_without_modification(self):
        self.assertEqual(file_hash(REPORT),REPORT_SHA)
        self.assertEqual(file_hash(self.source),self.srcsha)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)

    def test_29_no_actual_public_guid_or_question_in_committed_json(self):
        raw=REPORT.read_text(encoding="utf8")
        self.assertNotIn(self.guid,raw)
        self.assertNotIn(self.case["public_question"],raw)
        self.assertFalse(
            self.report["public_original_target_GUID_or_full_question_or_hidden_answers_in_report"])

    def test_30_second_actual_original_public_audit_exact_json_reproduces(self):
        result=audit_original19_native_pair(ROOT,AUTHOR,DATA)
        self.assertEqual(result,self.report)
        encoded=(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(sha256(encoded).hexdigest(),REPORT_SHA)

    def test_31_frozen_v026_unsafe_diagnostic_is_not_counted_as_new_D0(self):
        self.assertTrue(
            self.report["v026_inadmissible_native_wall_diagnostic_still_historical_not_paired"])
        self.assertEqual(self.report["previous_actual_developer_original_D0_I0_native_byte_equal"],8)
        self.assertEqual(self.report["new_cumulative_developer_original_D0_I0_native_byte_equal"],9)
        self.assertEqual(self.report["previous_original_author_callable_developer_pairs"],6)
        self.assertEqual(self.report["new_cumulative_original_author_callable_developer_pairs"],7)
        self.assertEqual(self.report["other_original_public_original45_cases_not_paired_under_same_protocol"],36)

    def test_32_no_real_model_or_causal_study_claims(self):
        self.assertEqual(self.report["original_public_intention_to_test_denominator"],45)
        self.assertEqual(self.report["real_model_LLM_calls"],0)
        self.assertEqual(self.report["provider_paid_USD"],0)
        self.assertFalse(self.report["unchanged_original_author_full_mark"])
        self.assertFalse(self.report["full_original45_source_information_write_and_feedback_parity_proven"])
        self.assertFalse(self.report["actual_causal_XML_Python_LLM_performance_comparison"])


if __name__=="__main__":
    unittest.main()
