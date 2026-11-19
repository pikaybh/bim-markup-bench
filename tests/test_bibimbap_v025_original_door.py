"""v0.25 original PUBLIC test_17 real IFC D0/I0 native Door deletion tests.

The trusted declarative XML compiler must remove only the exact source Door
and its one hosted Opening, with no unauthorized IFC Root/STEP changes.
Independent developer I0 uses native IfcOpenShell. Original benchmark score
remains 0.5 and no model is ever called.
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
import ifcopenshell.util.element

from src.runtime.door_opening_delete import (
    preflight_bounded_door_opening,verify_bounded_door_opening,
)
from src.runtime.ifc_mutations import UnsupportedIFCMutation
from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import XmlSourceEditSession,UnsupportedArm,file_hash
from tools.bibimbap_v025_original_door_i0 import (
    independent_original_public_door_i0, OriginalPublicDoorI0Blocked,
)
from tools.audit_bibimbap_v025_original_door import (
    ROOT,TASK_ID,ORIGINAL_PUBLIC_NORMALIZED_IFC_SHA,OLDER_REPORT_HASHES,
    OriginalPublicDoorAuditBlocked,actual_public_door_declarative_source,
    independent_native_products_oracle,audit_original_public_test17,
)

BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports/bibimbap_v025_original_test17_door_opening_D0_I0_20261115.json"
REPORT_SHA="4ea264519d011288acf6d059fc15b3ca49aa7d4d21315ccb5cbebe5bb17f3f4a"
IFC_SHA="7807db482647c4cae88678eef38beb5003d365ea1c08e1b589b68e3a8d86196f"


class OriginalPublic17DoorOpeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks={x["test_id"]:x for x in public_45(AUTHOR,DATA)}
        cls.task=cls.tasks[TASK_ID]
        cls.source=DATA/"ifc"/cls.task["original_source_ifc_relpath"]
        cls.srcsha=file_hash(cls.source)
        public=re.findall(
            r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",
            cls.task["public_question"])
        assert len(public)==1
        cls.guid=public[0]
        cls.original=ifcopenshell.open(str(cls.source))
        cls.door=cls.original.by_guid(cls.guid)
        cls.opening_guid=cls.door.FillsVoids[0].RelatingOpeningElement.GlobalId
        cls.temp=TemporaryDirectory(prefix="bmb-v025-original17-tests-")
        cls.folder=Path(cls.temp.name)
        cls.d0=XmlSourceEditSession(cls.source,cls.folder/"D0")
        cls.public_guid,cls.changed=actual_public_door_declarative_source(
            cls.task["public_question"],cls.d0.original_xml)
        cls.outcome=cls.d0.call("submit_building_xml",
                                {"xml_text":cls.changed.decode("utf8")})
        cls.i0out=cls.folder/"I0_original_mm.ifc"
        cls.i0=independent_original_public_door_i0(
            cls.source,cls.guid,cls.i0out)
        cls.before=ifcopenshell.open(str(cls.d0.normalized))
        cls.after=ifcopenshell.open(
            str(cls.d0.folder/"attempt_01"/"candidate_m.ifc"))
        cls.plan=preflight_bounded_door_opening(
            cls.before,cls.opening_guid,cls.guid)
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def _native(self):
        return ifcopenshell.open(str(self.d0.normalized))

    def _candidate(self):
        return ifcopenshell.open(
            str(self.d0.folder/"attempt_01"/"candidate_m.ifc"))

    def test_01_original_public45_population_and_pinned_git_source(self):
        self.assertEqual(len(self.tasks),45)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)
        self.assertEqual(self.srcsha,self.task["original_ifc_sha256"])
        self.assertEqual(file_hash(self.source),self.srcsha)
        self.assertEqual(self.task["crud"],"delete")
        self.assertEqual(self.task["category"],"basic")

    def test_02_frozen_v022_v023_v024_reports_untouched(self):
        for rel,sha in OLDER_REPORT_HASHES.items():
            with self.subTest(report=rel):
                self.assertEqual(file_hash(ROOT/rel),sha)
                self.assertEqual(self.report["prior_frozen_reports_sha256"][rel],sha)

    def test_03_exact_public_native_door_and_hosted_opening_exists(self):
        self.assertEqual(self.guid,self.public_guid)
        self.assertTrue(self.door.is_a("IfcDoor"))
        self.assertEqual(len(self.door.FillsVoids),1)
        opening=self.door.FillsVoids[0].RelatingOpeningElement
        self.assertEqual(opening.GlobalId,self.opening_guid)
        self.assertEqual(opening.is_a(),"IfcOpeningElement")
        self.assertEqual(len(opening.VoidsElements),1)
        self.assertEqual(opening.VoidsElements[0].RelatingBuildingElement.is_a(),"IfcWall")

    def test_04_full_standard_xml_only_existing_two_state_elements_removed(self):
        original=self.d0.original_xml.decode("utf8")
        changed=self.changed.decode("utf8")
        self.assertEqual(len(original.splitlines())-len(changed.splitlines()),2)
        self.assertNotIn(self.guid,changed)
        self.assertNotIn(self.opening_guid,changed)
        self.assertIn("<Wall",changed)
        self.assertIn("<Window",changed)
        self.assertIn("<Space",changed)
        self.assertNotIn("<Delete",changed)
        self.assertNotIn("<Command",changed)
        self.assertNotIn("<Move",changed)

    def test_05_Door_only_existing_XML_removal_remains_rejected(self):
        with TemporaryDirectory(prefix="bmb-v025-door-only-") as tmp:
            s=XmlSourceEditSession(self.source,Path(tmp)/"D0")
            text=s.original_xml.decode("utf8")
            line=next(x for x in text.splitlines(keepends=True)
                      if "<Door " in x and 'ifcGuid="'+self.guid+'"' in x)
            result=s.call("submit_building_xml",{"xml_text":text.replace(line,"")})
            self.assertEqual(result["status"],"error")
            self.assertIsNone(s.output_ifc)
            self.assertEqual(s.current_xml,s.original_xml)

    def test_06_real_XML_D0_native_ifc_transaction_committed(self):
        self.assertEqual(self.outcome["status"],"ok")
        self.assertTrue(self.outcome["native_ifc_committed"])
        self.assertEqual(self.outcome["compile_status"],
                         "COMMITTED_SCOPED_IFC4X3_TOPOLOGY_EDIT")
        self.assertTrue(self.d0.output_ifc.is_file())
        self.assertEqual(self.outcome["native_ifc_sha256"],IFC_SHA)

    def test_07_independent_I0_native_only_no_declarative_compiler(self):
        self.assertEqual(self.i0["status"],
                         "INDEPENDENT_ORIGINAL_PUBLIC_NATIVE_DOOR_AND_OPENING_DELETED")
        self.assertTrue(self.i0["original_public_door_absent"])
        self.assertTrue(self.i0["native_original_filled_opening_absent"])
        s=(ROOT/"tools/bibimbap_v025_original_door_i0.py").read_text(encoding="utf8")
        imports=[]
        for n in ast.walk(ast.parse(s)):
            if isinstance(n,ast.Import):
                imports.extend(a.name for a in n.names)
            if isinstance(n,ast.ImportFrom):
                imports.append(n.module or "")
        self.assertFalse(any(x.startswith("src.runtime") for x in imports))
        self.assertNotIn("compile_declarative_xml",s)

    def test_08_original_D0_I0_full_IFC_byte_equal(self):
        self.assertEqual(file_hash(self.d0.output_ifc),file_hash(self.i0out))
        self.assertEqual(file_hash(self.i0out),IFC_SHA)
        self.assertEqual(self.report["D0_actual_native_output_IFC_sha256"],IFC_SHA)
        self.assertEqual(self.report["I0_actual_native_output_IFC_sha256"],IFC_SHA)

    def test_09_independent_native_product_source_oracle_both_arms(self):
        d=independent_native_products_oracle(
            self.source,self.d0.output_ifc,self.guid,self.opening_guid)
        i=independent_native_products_oracle(
            self.source,self.i0out,self.guid,self.opening_guid)
        self.assertEqual(d,i)
        self.assertEqual(d["original_IfcProduct_count"],43)
        self.assertEqual(d["result_IfcProduct_count"],41)
        self.assertTrue(d["every_other_original_native_IfcProduct_class_and_GUID_preserved"])

    def test_10_unchanged_original_author_scores_both_0_5_not_full(self):
        d=grade_author(AUTHOR,self.source,self.d0.output_ifc,TASK_ID)
        i=grade_author(AUTHOR,self.source,self.i0out,TASK_ID)
        self.assertEqual(d,i)
        self.assertEqual(d["status"],"AUTHOR_SCORED")
        self.assertEqual(d["original_author_score"],.5)
        self.assertEqual(d["original_author_metrics"],
                         {"integrity_constraint":0.0,"object_not_exists":1.0})
        self.assertFalse(d["original_author_full_mark"])
        self.assertEqual(d,self.report["unchanged_original_author_D0"])
        self.assertEqual(i,self.report["unchanged_original_author_I0"])

    def test_11_native_original_root_STEP_gate(self):
        unchanged=verify_bounded_door_opening(self.before,self.after,self.plan)
        self.assertGreater(unchanged,200)
        self.assertEqual(len(self.plan.deleted_root_guids),10)
        self.assertEqual(len(self.plan.modified_root_guids),2)
        self.assertEqual(len(self.plan.modified_layer_step_ids),1)

    def test_12_exact_native_original_class_and_output_cardinality(self):
        self.assertEqual(len(self.before.by_type("IfcProduct")),43)
        self.assertEqual(len(self.after.by_type("IfcProduct")),41)
        self.assertFalse(any(x.GlobalId==self.guid for x in
                             self.after.by_type("IfcDoor")))
        self.assertFalse(any(x.GlobalId==self.opening_guid for x in
                             self.after.by_type("IfcOpeningElement")))

    def test_13_wrong_typed_original_native_guid_rejected(self):
        f=self._native()
        pairs=[("0"*22,self.guid),
               (f.by_type("IfcWall")[0].GlobalId,self.guid),
               (self.opening_guid,f.by_type("IfcWindow")[0].GlobalId)]
        for op,dr in pairs:
            with self.subTest(opening=op,door=dr),self.assertRaises(UnsupportedIFCMutation):
                preflight_bounded_door_opening(f,op,dr)

    def test_14_shared_native_propertyset_assignment_refused(self):
        f=self._native();door=f.by_guid(self.guid)
        rel=next(x for x in f.get_inverse(door)
                 if x.is_a("IfcRelDefinesByProperties"))
        rel.RelatedObjects=tuple(list(rel.RelatedObjects)+[f.by_type("IfcWall")[0]])
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_bounded_door_opening(f,self.opening_guid,self.guid)

    def test_15_native_unknown_room_boundary_refused(self):
        f=self._native();door=f.by_guid(self.guid)
        f.create_entity("IfcRelSpaceBoundary",GlobalId=ifcopenshell.guid.new(),
                        RelatingSpace=f.by_type("IfcSpace")[0],
                        RelatedBuildingElement=door,
                        PhysicalOrVirtualBoundary="PHYSICAL",
                        InternalOrExternalBoundary="INTERNAL")
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_bounded_door_opening(f,self.opening_guid,self.guid)

    def test_16_shared_native_door_type_assignment_refused(self):
        f=self._native();door=f.by_guid(self.guid)
        rel=next(x for x in f.get_inverse(door) if x.is_a("IfcRelDefinesByType"))
        rel.RelatedObjects=tuple(list(rel.RelatedObjects)+[f.by_type("IfcWall")[0]])
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_bounded_door_opening(f,self.opening_guid,self.guid)

    def test_17_shared_native_material_assignment_refused(self):
        f=self._native();door=f.by_guid(self.guid)
        rel=next(x for x in f.get_inverse(door) if x.is_a("IfcRelAssociatesMaterial"))
        rel.RelatedObjects=tuple(list(rel.RelatedObjects)+[f.by_type("IfcWall")[0]])
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_bounded_door_opening(f,self.opening_guid,self.guid)

    def test_18_missing_original_door_storey_containment_refused(self):
        f=self._native();door=f.by_guid(self.guid)
        rel=next(x for x in f.get_inverse(door)
                 if x.is_a("IfcRelContainedInSpatialStructure"))
        rel.RelatedElements=tuple(x for x in rel.RelatedElements if x!=door)
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_bounded_door_opening(f,self.opening_guid,self.guid)

    def test_19_original_opening_with_second_filling_refused(self):
        f=self._native()
        f.create_entity("IfcRelFillsElement",GlobalId=ifcopenshell.guid.new(),
                        RelatingOpeningElement=f.by_guid(self.opening_guid),
                        RelatedBuildingElement=f.by_type("IfcWindow")[0])
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_bounded_door_opening(f,self.opening_guid,self.guid)

    def test_20_forged_surviving_original_IFC_root_rejected(self):
        after=self._candidate()
        after.by_type("IfcWall")[0].Name="FORGED_UNRELATED_WALL"
        with self.assertRaises(UnsupportedIFCMutation):
            verify_bounded_door_opening(self.before,after,self.plan)

    def test_21_unrelated_original_native_product_delete_rejected(self):
        after=self._candidate()
        ifcopenshell.api.root.remove_product(
            after,product=after.by_type("IfcWall")[0])
        with self.assertRaises(UnsupportedIFCMutation):
            verify_bounded_door_opening(self.before,after,self.plan)

    def test_22_shared_presentation_layer_unrelated_member_change_rejected(self):
        after=self._candidate()
        layer=after.by_id(next(iter(self.plan.modified_layer_step_ids)))
        layer.AssignedItems=tuple(layer.AssignedItems[:-1])
        with self.assertRaises(UnsupportedIFCMutation):
            verify_bounded_door_opening(self.before,after,self.plan)

    def test_23_surviving_door_classifier_metadata_change_rejected(self):
        after=self._candidate()
        relation=next(x for x in after.by_type("IfcRelAssociatesClassification")
                      if x.GlobalId in self.plan.modified_root_guids)
        relation.Name="FORGED_CLASSIFIER_NAME"
        with self.assertRaises(UnsupportedIFCMutation):
            verify_bounded_door_opening(self.before,after,self.plan)

    def test_24_unrelated_Wall_deleted_alongside_original_door_pair_refused(self):
        with TemporaryDirectory(prefix="bmb-v025-extra-wall-") as td:
            s=XmlSourceEditSession(self.source,Path(td)/"D0")
            xml=self.changed.decode("utf8")
            line=next(x for x in xml.splitlines(keepends=True) if "<Wall " in x)
            response=s.call("submit_building_xml",{"xml_text":xml.replace(line,"")})
            self.assertEqual(response["status"],"error")
            self.assertIsNone(s.output_ifc)
            self.assertEqual(s.current_xml,s.original_xml)

    def test_25_unrelated_Window_deleted_alongside_original_pair_refused(self):
        with TemporaryDirectory(prefix="bmb-v025-extra-window-") as td:
            s=XmlSourceEditSession(self.source,Path(td)/"D0")
            xml=self.changed.decode("utf8")
            line=next(x for x in xml.splitlines(keepends=True) if "<Window " in x)
            response=s.call("submit_building_xml",{"xml_text":xml.replace(line,"")})
            self.assertEqual(response["status"],"error")
            self.assertIsNone(s.output_ifc)
            self.assertEqual(s.current_xml,s.original_xml)

    def test_26_forged_public_Door_target_guid_rejected(self):
        with self.assertRaises(OriginalPublicDoorAuditBlocked):
            actual_public_door_declarative_source(
                "Remove door with id "+"Z"*22,self.d0.original_xml)
        with self.assertRaises(OriginalPublicDoorAuditBlocked):
            actual_public_door_declarative_source(
                self.task["public_question"]+" and "+"Z"*22,self.d0.original_xml)

    def test_27_other_original_IFC4_or_IFC2X3_source_still_not_admitted(self):
        for task_id in ("geometry_test_03","geometry_test_05"):
            task=self.tasks[task_id]
            original=DATA/"ifc"/task["original_source_ifc_relpath"]
            with self.subTest(task=task_id),TemporaryDirectory() as td:
                with self.assertRaises(UnsupportedArm):
                    XmlSourceEditSession(original,Path(td)/"D0")
                self.assertEqual(file_hash(original),task["original_ifc_sha256"])

    def test_28_original_author_and_native_source_sha_unchanged(self):
        self.assertEqual(file_hash(self.source),self.srcsha)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)
        self.assertEqual(file_hash(REPORT),REPORT_SHA)
        self.assertEqual(self.report["original_IFC4X3_mm_source_sha256"],self.srcsha)

    def test_29_no_original_public_or_grader_target_guid_literals_in_report(self):
        txt=REPORT.read_text(encoding="utf8")
        self.assertNotIn(self.guid,txt)
        self.assertNotIn(self.opening_guid,txt)
        self.assertNotIn(self.task["public_question"],txt)
        self.assertFalse(
            self.report["raw_original_public_named_GUID_or_hidden_original_targets_in_report"])

    def test_30_second_live_audit_reproduces_report_hash_and_native_output(self):
        second=audit_original_public_test17(ROOT,AUTHOR,DATA)
        self.assertEqual(second,self.report)
        encoded=(json.dumps(second,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(sha256(encoded).hexdigest(),REPORT_SHA)

    def test_31_scientific_counts_are_developer_not_model(self):
        self.assertEqual(self.report["prior_frozen_developer_original_native_D0_I0_identical_cases"],7)
        self.assertEqual(self.report["new_cumulative_developer_original_native_D0_I0_identical_cases"],8)
        self.assertEqual(self.report["prior_frozen_original_author_callable_developer_pairs"],5)
        self.assertEqual(self.report["new_cumulative_original_author_callable_developer_pairs"],6)
        self.assertEqual(self.report["other_original_public_same_protocol_cases_unverified"],37)
        self.assertEqual(self.report["real_LLM_model_calls"],0)
        self.assertEqual(self.report["paid_provider_USD"],0)
        self.assertFalse(self.report["developer_output_parity_proves_causal_XML_model_performance"])
        self.assertFalse(self.report["full_original_45_write_information_tool_or_feedback_parity_proven"])

    def test_32_original_grader_integrity_half_score_not_silently_fixed(self):
        self.assertTrue(self.report["original_public_Door_native_spatial_container_exists"])
        self.assertFalse(self.report["original_author_score_full_mark_achieved"])
        self.assertEqual(
            self.report["unchanged_original_author_D0"]["original_author_metrics"],
            {"object_not_exists":1.0,"integrity_constraint":0.0})


if __name__=="__main__":
    unittest.main()
