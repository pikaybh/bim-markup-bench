"""v0.26 test_19 original-public connected Wall safety/admission regression.

No new D0 success may be reported: candidate XML state is syntactically
valid only after two original declared connections are also removed, while
the current trusted compiler correctly refuses the native mutation. A
low-level developer-only diagnostic generates an orphaned native IFC; the
original author score (0.5) is explicitly NOT evidence of edit parity.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import XmlSourceEditSession, file_hash
from tools.audit_bibimbap_v026_connected_wall_safety import (
    ROOT,TASK_ID,NATIVE_ORIGINAL_NORMALIZED_SHA,FROZEN_PREVIOUS_REPORTS,
    UnsafeOriginalConnectedWall,proposed_complete_connected_wall_xml,
    exact_declarative_graph_proposal,developer_only_incomplete_native_probe,
    audit_original_connected_wall,
)

BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports/bibimbap_v026_original_test19_connected_wall_fail_closed_20261116.json"
REPORT_SHA="fe6137a71789bf0d6c55dcf6c62a43a70f86fa5614e5c87faee2894e855ac848"


class OriginalPublic19ConnectedWallSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks={x["test_id"]:x for x in public_45(AUTHOR,DATA)}
        cls.case=cls.tasks[TASK_ID]
        cls.source=DATA/"ifc"/cls.case["original_source_ifc_relpath"]
        cls.source_sha=file_hash(cls.source)
        cls.guid=re.search(r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",
                           cls.case["public_question"]).group(0)
        cls.temp=TemporaryDirectory(prefix="bmb-v026-wall-admission-tests-")
        cls.folder=Path(cls.temp.name)
        cls.session=XmlSourceEditSession(cls.source,cls.folder/"D0")
        cls.public_guid,cls.updated=proposed_complete_connected_wall_xml(
            cls.case["public_question"],cls.session.original_xml)
        cls.proposal=exact_declarative_graph_proposal(cls.session,cls.updated)
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_01_pinned_original_author_and_dataset_still_clean_revision(self):
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)
        self.assertEqual(len(self.tasks),45)
        self.assertEqual(self.case["category"],"basic")
        self.assertEqual(self.case["crud"],"delete")
        self.assertEqual(self.source_sha,self.case["original_ifc_sha256"])

    def test_02_old_v023_v024_v025_native_results_immutable(self):
        for filename,sha in FROZEN_PREVIOUS_REPORTS.items():
            with self.subTest(filename=filename):
                self.assertEqual(file_hash(ROOT/filename),sha)

    def test_03_one_public_original_wall_is_present_as_editable_XML(self):
        self.assertEqual(self.guid,self.public_guid)
        wall=ifcopenshell.open(str(self.source)).by_guid(self.guid)
        self.assertEqual(wall.is_a(),"IfcWall")
        self.assertEqual(len(wall.HasOpenings),0)

    def test_04_original_native_wall_has_exactly_two_path_links(self):
        model=ifcopenshell.open(str(self.session.normalized))
        wall=model.by_guid(self.guid)
        paths=[x for x in model.get_inverse(wall)
               if x.is_a("IfcRelConnectsPathElements")]
        self.assertEqual(len(paths),2)
        self.assertTrue(all(rel.RelatedElement==wall for rel in paths))
        self.assertEqual(len({x.RelatingElement.GlobalId for x in paths}),2)
        self.assertTrue(all(x.RelatingElement.is_a("IfcWall") for x in paths))

    def test_05_valid_complete_proposal_removes_wall_and_two_links(self):
        before=self.session.original_xml.decode("utf8")
        after=self.updated.decode("utf8")
        self.assertEqual(len(before.splitlines())-len(after.splitlines()),3)
        self.assertNotIn(self.guid,after)
        self.assertNotIn("<Delete",after)
        self.assertNotIn("<Command",after)
        self.assertIn("<Wall",after)
        self.assertIn("<Connects",after)
        self.assertEqual(self.proposal["original_existing_wall_node_removed"],1)
        self.assertEqual(self.proposal["original_existing_connects_edges_removed"],2)
        self.assertEqual(self.proposal["original_existing_in_storey_edge_removed"],1)

    def test_06_legacy_XML_dangling_join_rejected_without_native_commit(self):
        with TemporaryDirectory(prefix="bmb-v026-dangling-connection-") as tmp:
            s=XmlSourceEditSession(self.source,Path(tmp)/"D0")
            xml=s.original_xml.decode("utf8")
            wall=next(l for l in xml.splitlines(keepends=True)
                      if "<Wall " in l and 'ifcGuid="'+self.guid+'"' in l)
            response=s.call("submit_building_xml",{"xml_text":xml.replace(wall,"")})
            self.assertEqual(response["status"],"error")
            self.assertIsNone(s.output_ifc)
            self.assertEqual(s.current_xml,s.original_xml)

    def test_07_legacy_compiler_correctly_blocks_valid_connected_wall_diff(self):
        response=self.session.call(
            "submit_building_xml",{"xml_text":self.updated.decode("utf8")})
        self.assertEqual(response["status"],"error")
        self.assertIsNone(self.session.output_ifc)
        self.assertEqual(self.session.current_xml,self.session.original_xml)
        self.assertTrue(response["last_valid_xml_preserved"])

    def test_08_native_diagnostic_wall_product_identity_not_safety_pass(self):
        d=self.report["diagnostic_low_level_native_only"]
        self.assertEqual(d["status"],
                         "DIAGNOSTIC_NATIVE_REMOVAL_INADMISSIBLE_ORPHANED_GEOMETRY")
        self.assertEqual(d["source_original_IfcProduct_count"],43)
        self.assertEqual(d["diagnostic_original_IfcProduct_count"],42)
        self.assertTrue(d["remaining_native_product_classes_and_GUIDs_unchanged"])
        self.assertTrue(d["result_is_not_an_admitted_D0_or_I0_original_public_edit"])

    def test_09_owned_property_and_path_link_root_removals_are_bounded(self):
        removed=self.report["diagnostic_low_level_native_only"][
            "exact_original_native_roots_removed_class_inventory"]
        self.assertEqual(len(removed),9)
        self.assertEqual(removed.count("IfcWall"),1)
        self.assertEqual(removed.count("IfcRelConnectsPathElements"),2)
        self.assertEqual(removed.count("IfcRelDefinesByProperties"),3)
        self.assertEqual(removed.count("IfcPropertySet"),3)

    def test_10_orphan_source_wall_shape_and_placement_blocks_parity(self):
        d=self.report["diagnostic_low_level_native_only"]
        self.assertEqual(
            d["retained_original_Wall_shapes_not_owned_by_surviving_products"],2)
        self.assertEqual(
            d["additional_original_orphaned_entities"]["IfcLocalPlacement"],1)
        self.assertEqual(
            d["additional_original_orphaned_entities"]["IfcProductDefinitionShape"],1)
        self.assertEqual(
            d["additional_original_orphaned_entities"]["IfcShapeRepresentation"],0)
        self.assertFalse(self.report["connected_wall_source_model_compiler_supported"])

    def test_11_original_author_half_score_is_diagnostic_not_full(self):
        original=self.report["diagnostic_low_level_native_only"][
            "original_author_diagnostic_score"]
        self.assertEqual(original["status"],"AUTHOR_SCORED")
        self.assertEqual(original["original_author_score"],0.5)
        self.assertEqual(original["original_author_metrics"],
                         {"object_not_exists":1.0,"integrity_constraint":0.0})
        self.assertFalse(original["original_author_full_mark"])

    def test_12_reject_forged_or_ambiguous_public_target(self):
        with self.assertRaises(UnsafeOriginalConnectedWall):
            proposed_complete_connected_wall_xml(
                "Remove wall "+"Z"*22,self.session.original_xml)
        with self.assertRaises(UnsafeOriginalConnectedWall):
            proposed_complete_connected_wall_xml(
                self.case["public_question"]+" "+"Z"*22,self.session.original_xml)

    def test_13_reject_missing_original_join_or_unrelated_extra_join(self):
        before=self.session.original_xml.decode("utf8")
        edge=next(line for line in before.splitlines(keepends=True)
                  if '<Connects ' in line
                  and ('to="'+re.search(r'\bid="([^"]+)"',
                     next(x for x in before.splitlines(keepends=True)
                         if '<Wall ' in x and 'ifcGuid="'+self.guid+'"' in x)
                  ).group(1)+'"') in line)
        with self.assertRaises(UnsafeOriginalConnectedWall):
            proposed_complete_connected_wall_xml(
                self.case["public_question"],
                before.replace(edge,"").encode("utf8"))

    def test_14_reject_wrong_normalized_source_or_tampered_file(self):
        with TemporaryDirectory(prefix="bmb-v026-forged-native-") as tmp:
            bogus=Path(tmp)/"bogus.ifc"
            bogus.write_bytes(b"not an original IFC4X3 file")
            with self.assertRaises(UnsafeOriginalConnectedWall):
                developer_only_incomplete_native_probe(
                    self.source,bogus,self.guid,Path(tmp),AUTHOR)

    def test_15_frozen_report_byte_sha_and_original_source_not_modified(self):
        self.assertEqual(file_hash(REPORT),REPORT_SHA)
        self.assertEqual(file_hash(self.source),self.source_sha)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)

    def test_16_no_public_original_target_or_question_raw_in_report(self):
        raw=REPORT.read_text(encoding="utf8")
        self.assertNotIn(self.guid,raw)
        self.assertNotIn(self.case["public_question"],raw)
        self.assertTrue(self.report["no_private_original_answer_or_public_target_GUID_in_report"])

    def test_17_second_real_public_audit_reproduces_byte_identical_report(self):
        result=audit_original_connected_wall(ROOT,AUTHOR,DATA)
        self.assertEqual(result,self.report)
        raw=(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(sha256(raw).hexdigest(),REPORT_SHA)

    def test_18_honest_full45_and_real_LLM_call_accounting(self):
        self.assertEqual(self.report["original_benchmark_denominator"],45)
        self.assertEqual(self.report["new_native_original_developer_D0_I0_byte_equal_pairs"],0)
        self.assertEqual(self.report["cumulative_actual_developer_D0_I0_equal_original_pairs"],8)
        self.assertEqual(self.report["cumulative_original_author_callable_developer_pairs"],6)
        self.assertEqual(self.report["other_original_tasks_unverified_same_protocol"],37)
        self.assertEqual(self.report["real_LLM_calls"],0)
        self.assertEqual(self.report["paid_provider_usd"],0)
        self.assertFalse(self.report["full_original45_information_and_write_parity_proven"])


if __name__=="__main__":
    unittest.main()
