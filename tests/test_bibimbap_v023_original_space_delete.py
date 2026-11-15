"""v0.23 strict original PUBLIC test_20 declarative Room deletion validation.

This validates an actual new source-edited XML native mutation against a
separate IfcOpenShell developer I0 and unchanged original author scorer,
including guard failures for shared metadata, unrelated walls and source
integrity. No real model calls or hidden target lookups are made.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import ast
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.unit

from src.runtime.space_delete import (
    _guard_original_space, verify_bounded_space_deletion,
)
from src.runtime.ifc_mutations import UnsupportedIFCMutation
from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45, grade_author
from tools.bibimbap_matched25_tools import (
    XmlSourceEditSession, file_hash, UnsupportedArm,
)
from tools.bibimbap_v023_original_space_i0 import (
    independent_public_space_delete_i0, OriginalDeveloperI0Blocked,
)
from tools.audit_bibimbap_v023_original_space_delete import (
    ROOT, TASK_ID, PARENT_V022_SHA, PARENT_V022_PATH,
    OriginalSpaceParityBlocked, public_original_space_target_and_declarative_source,
    independent_original_native_identity_oracle, audit_original20,
)

BASE = Path(r"D:\문서\D__1_Projects\202611")
AUTHOR = BASE / "bibimbap-author-upstream"
DATA = BASE / "bibimbap-author-data"
REPORT = ROOT / "reports/bibimbap_v023_original_test20_space_delete_D0_I0_native_parity_20261115.json"
REPORT_SHA = "9abcc4ebd21c18891bf08307624a19f6012a981455eca7db89051ae70ce86102"
CANDIDATE_SHA = "2a3fb1e29e7b6d929b2dd87de898d414d75c944cf8c2fa7d95fa0d7b619162d3"


class OriginalPublic20SpaceDeleteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public = {x["test_id"]: x for x in public_45(AUTHOR, DATA)}
        cls.case = cls.public[TASK_ID]
        cls.source = DATA/"ifc"/cls.case["original_source_ifc_relpath"]
        cls.public_guid = re.search(
            r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",
            cls.case["public_question"]).group(0)
        cls.source_sha=file_hash(cls.source)
        cls.temp=TemporaryDirectory(prefix="bmb-v023-original20-qa-")
        cls.folder=Path(cls.temp.name)
        cls.session=XmlSourceEditSession(cls.source,cls.folder/"D0")
        cls.guid, cls.edited_xml = public_original_space_target_and_declarative_source(
            cls.case["public_question"],cls.session.original_xml)
        cls.resp=cls.session.call("submit_building_xml",
                                  {"xml_text":cls.edited_xml.decode("utf8")})
        cls.i0path=cls.folder/"independent_I0_mm.ifc"
        cls.i0_result=independent_public_space_delete_i0(
            cls.source,cls.guid,cls.i0path)
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_01_original_benchmark_45_and_git_sha_unchanged(self):
        self.assertEqual(len(self.public),45)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)
        self.assertEqual(self.source_sha,self.case["original_ifc_sha256"])
        self.assertEqual(file_hash(self.source),self.source_sha)

    def test_02_frozen_older_role_evidence_unchanged(self):
        self.assertEqual(file_hash(ROOT/PARENT_V022_PATH),PARENT_V022_SHA)
        self.assertEqual(self.report["pinned_parent_v022_report_sha256"],PARENT_V022_SHA)
        self.assertEqual(self.report["original_all45_intention_to_test_denominator"],45)
        self.assertEqual(self.report["original_task_id"],"test_20")

    def test_03_original_public_instruction_bound_to_existing_Space(self):
        self.assertEqual(self.guid,self.public_guid)
        self.assertTrue(ifcopenshell.open(str(self.source)).by_guid(self.guid).is_a("IfcSpace"))
        self.assertIn(self.guid,self.session.original_xml.decode("utf8"))
        self.assertNotIn(self.guid,self.edited_xml.decode("utf8"))
        self.assertEqual(self.case["crud"],"delete")

    def test_04_declarative_XML_edits_only_one_existing_Space_element(self):
        before=self.session.original_xml.decode("utf8")
        after=self.edited_xml.decode("utf8")
        self.assertEqual(len(before.splitlines())-len(after.splitlines()),1)
        self.assertNotIn("<Delete",after)
        self.assertNotIn("<Move",after)
        self.assertNotIn("<Command",after)
        self.assertIn("<Space",after)  # other original declared room preserved
        self.assertTrue(after.startswith("<?xml"))

    def test_05_actual_D0_compiler_commits_original_native_space_delete(self):
        self.assertEqual(self.resp["status"],"ok")
        self.assertTrue(self.resp["native_ifc_committed"])
        self.assertEqual(self.resp["compile_status"],
                         "COMMITTED_SCOPED_IFC4X3_TOPOLOGY_EDIT")
        self.assertIsNotNone(self.session.output_ifc)
        self.assertTrue(self.session.output_ifc.is_file())
        self.assertFalse(any(s.GlobalId==self.guid for s in
                             ifcopenshell.open(str(self.session.output_ifc)).by_type("IfcSpace")))

    def test_06_independent_developer_I0_does_not_use_XML_compiler(self):
        self.assertEqual(self.i0_result["status"],
                         "INDEPENDENT_DEVELOPER_NATIVE_IFC_SPACE_DELETION_CREATED")
        self.assertFalse(self.i0_result["output_contains_target_space"])
        module=ROOT/"tools/bibimbap_v023_original_space_i0.py"
        source=module.read_text(encoding="utf8")
        program=ast.parse(source)
        imports=[]
        for node in ast.walk(program):
            if isinstance(node,ast.Import):imports.extend(x.name for x in node.names)
            elif isinstance(node,ast.ImportFrom):imports.append(node.module or "")
        self.assertFalse(any(i.startswith("src.runtime") for i in imports))
        self.assertFalse(any(i=="tools.bibimbap_matched25_tools" for i in imports))
        self.assertNotIn("compile_declarative_xml(",source)

    def test_07_D0_I0_original_public_IFC_bytes_exact_sha_equal(self):
        a=file_hash(self.session.output_ifc)
        b=file_hash(self.i0path)
        self.assertEqual(a,b)
        self.assertEqual(a,CANDIDATE_SHA)
        self.assertEqual(self.resp["native_ifc_sha256"],CANDIDATE_SHA)
        self.assertEqual(self.report["D0_original_native_output_sha256"],a)
        self.assertEqual(self.report["I0_original_native_output_sha256"],b)

    def test_08_independent_all_original_native_products_preserved(self):
        d=independent_original_native_identity_oracle(
            self.source,self.session.output_ifc,self.guid)
        i=independent_original_native_identity_oracle(
            self.source,self.i0path,self.guid)
        self.assertEqual(d,i)
        self.assertEqual(d["status"],
                         "INDEPENDENT_ORIGINAL_NATIVE_PUBLIC_ROOM_IDENTITY_PASS")
        self.assertEqual(d["source_product_count"],43)
        self.assertEqual(d["candidate_product_count"],42)
        self.assertEqual(d["remaining_original_rooms_unchanged"],2)

    def test_09_original_author_scorer_D0_and_I0_identical_half_not_full(self):
        d=grade_author(AUTHOR,self.source,self.session.output_ifc,TASK_ID)
        i=grade_author(AUTHOR,self.source,self.i0path,TASK_ID)
        self.assertEqual(d,i)
        self.assertEqual(d["status"],"AUTHOR_SCORED")
        self.assertEqual(d["original_author_score"],.5)
        self.assertEqual(d["original_author_metrics"],
                         {"integrity_constraint":0.0,"object_not_exists":1.0})
        self.assertFalse(d["original_author_full_mark"])
        self.assertEqual(self.report["pinned_original_author_D0_score"],d)
        self.assertEqual(self.report["pinned_original_author_I0_score"],i)

    def test_10_normalized_source_independent_native_ROOT_oracle(self):
        normalized=ifcopenshell.open(str(self.session.normalized))
        result_m=self.session.folder/"attempt_01"/"candidate_m.ifc"
        candidate=ifcopenshell.open(str(result_m))
        space,expected_deleted,modified=_guard_original_space(normalized,self.guid)
        stable=verify_bounded_space_deletion(
            normalized,candidate,self.guid,expected_deleted,modified)
        self.assertGreater(stable,0)

    def test_11_validated_original_room_preflight_is_tightly_bounded(self):
        model=ifcopenshell.open(str(self.session.normalized))
        _,removed,changed=_guard_original_space(model,self.guid)
        self.assertEqual(len(changed),1)
        self.assertEqual(len(removed),6)
        self.assertIn(self.guid,removed)

    def test_12_non_space_or_unavailable_original_GUID_rejected(self):
        f=ifcopenshell.open(str(self.session.normalized))
        wall=f.by_type("IfcWall")[0]
        for target in (wall.GlobalId,"0"*22):
            with self.subTest(guid=target),self.assertRaises(UnsupportedIFCMutation):
                _guard_original_space(f,target)

    def test_13_shared_IfcRelDefinesByProperties_rejected(self):
        f=ifcopenshell.open(str(self.session.normalized))
        room=f.by_guid(self.guid)
        pset=next(rel for rel in f.get_inverse(room) if
                  rel.is_a("IfcRelDefinesByProperties"))
        other=next(space for space in f.by_type("IfcSpace") if space.GlobalId!=self.guid)
        pset.RelatedObjects=tuple(list(pset.RelatedObjects)+[other])
        with self.assertRaises(UnsupportedIFCMutation):
            _guard_original_space(f,self.guid)

    def test_14_unsupported_IfcRelSpaceBoundary_dependency_rejected(self):
        f=ifcopenshell.open(str(self.session.normalized))
        room=f.by_guid(self.guid)
        wall=f.by_type("IfcWall")[0]
        f.create_entity("IfcRelSpaceBoundary",GlobalId=ifcopenshell.guid.new(),
                        RelatingSpace=room,RelatedBuildingElement=wall,
                        PhysicalOrVirtualBoundary="PHYSICAL",
                        InternalOrExternalBoundary="INTERNAL")
        with self.assertRaises(UnsupportedIFCMutation):
            _guard_original_space(f,self.guid)

    def test_15_native_aggregation_reference_guard_rejected(self):
        f=ifcopenshell.open(str(self.session.normalized))
        room=f.by_guid(self.guid)
        aggregate=next(r for r in f.get_inverse(room) if r.is_a("IfcRelAggregates"))
        aggregate.RelatedObjects=tuple(x for x in aggregate.RelatedObjects if x!=room)
        with self.assertRaises(UnsupportedIFCMutation):
            _guard_original_space(f,self.guid)

    def test_16_unrelated_surviving_IFC_ROOT_mutation_rejected(self):
        before=ifcopenshell.open(str(self.session.normalized))
        after=ifcopenshell.open(str(self.session.folder/"attempt_01"/"candidate_m.ifc"))
        wall=after.by_type("IfcWall")[0]
        wall.Name="FORGED_UNRELATED_WALL_CHANGE"
        _,deleted,modified=_guard_original_space(before,self.guid)
        with self.assertRaises(UnsupportedIFCMutation):
            verify_bounded_space_deletion(before,after,self.guid,deleted,modified)

    def test_17_unrelated_native_product_deletion_rejected(self):
        before=ifcopenshell.open(str(self.session.normalized))
        after=ifcopenshell.open(str(self.session.folder/"attempt_01"/"candidate_m.ifc"))
        ifcopenshell.api.root.remove_product(after,product=after.by_type("IfcWall")[0])
        _,deleted,modified=_guard_original_space(before,self.guid)
        with self.assertRaises(UnsupportedIFCMutation):
            verify_bounded_space_deletion(before,after,self.guid,deleted,modified)

    def test_18_unrelated_presentation_layer_member_modification_rejected(self):
        before=ifcopenshell.open(str(self.session.normalized))
        after=ifcopenshell.open(str(self.session.folder/"attempt_01"/"candidate_m.ifc"))
        layer=next(l for l in after.by_type("IfcPresentationLayerAssignment")
                   if len(l.AssignedItems)>=2)
        layer.AssignedItems=tuple(layer.AssignedItems[:1])
        _,deleted,modified=_guard_original_space(before,self.guid)
        with self.assertRaises(UnsupportedIFCMutation):
            verify_bounded_space_deletion(before,after,self.guid,deleted,modified)

    def test_19_second_room_removed_alongside_named_target_is_rejected(self):
        with TemporaryDirectory(prefix="bmb-v023-invalid-two-rooms-") as td:
            s=XmlSourceEditSession(self.source,Path(td)/"session")
            text=self.edited_xml.decode("utf8")
            line=next(x for x in text.splitlines(keepends=True) if "<Space " in x)
            attack=text.replace(line,"")
            outcome=s.call("submit_building_xml",{"xml_text":attack})
            self.assertEqual(outcome["status"],"error")
            self.assertIsNone(s.output_ifc)
            self.assertEqual(s.current_xml,s.original_xml)

    def test_20_unrelated_Wall_removed_alongside_room_rejected(self):
        with TemporaryDirectory(prefix="bmb-v023-invalid-wall-") as td:
            s=XmlSourceEditSession(self.source,Path(td)/"session")
            text=self.edited_xml.decode("utf8")
            line=next(x for x in text.splitlines(keepends=True) if "<Wall " in x)
            attack=text.replace(line,"")
            outcome=s.call("submit_building_xml",{"xml_text":attack})
            self.assertEqual(outcome["status"],"error")
            self.assertIsNone(s.output_ifc)
            self.assertEqual(s.current_xml,s.original_xml)

    def test_21_fake_public_instruction_target_fails_closed(self):
        with self.assertRaises(OriginalSpaceParityBlocked):
            public_original_space_target_and_declarative_source(
                "Delete room with id 0"*2,self.session.original_xml)
        with self.assertRaises(OriginalSpaceParityBlocked):
            public_original_space_target_and_declarative_source(
                "Delete room with id "+"Z"*22,self.session.original_xml)

    def test_22_unsupported_older_IFC_schema_still_rejected(self):
        for testcase in ("geometry_test_03","geometry_test_05"):
            public=self.public[testcase]
            original=DATA/"ifc"/public["original_source_ifc_relpath"]
            with self.subTest(testcase=testcase),TemporaryDirectory() as td:
                with self.assertRaises(UnsupportedArm):
                    XmlSourceEditSession(original,Path(td)/"xml")
                self.assertEqual(file_hash(original),public["original_ifc_sha256"])

    def test_23_source_data_and_report_sha_immutable(self):
        self.assertEqual(file_hash(REPORT),REPORT_SHA)
        self.assertEqual(file_hash(self.source),self.source_sha)
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)

    def test_24_new_developer_pair_metrics_not_sold_as_LLM(self):
        self.assertEqual(self.report["prior_frozen_developer_D0_I0_byte_equal_original_cases"],5)
        self.assertEqual(self.report["post_v023_distinct_developer_D0_I0_byte_equal_original_cases"],6)
        self.assertEqual(self.report["prior_frozen_both_original_author_callable_cases"],3)
        self.assertEqual(self.report["post_v023_distinct_developer_both_original_author_callable_cases"],4)
        self.assertEqual(self.report["other_original_public_same_protocol_edit_cases_unverified"],39)
        self.assertEqual(self.report["new_real_paired_LLM_model_calls"],0)
        self.assertEqual(self.report["paid_provider_USD"],0)
        self.assertFalse(self.report["original_author_full_mark_achieved"])
        self.assertFalse(self.report["new_actual_XML_IFC2X3_or_IFC4_write_support"])

    def test_25_second_real_author_and_IFC_audit_byte_identical(self):
        again=audit_original20(ROOT,AUTHOR,DATA)
        self.assertEqual(again,self.report)
        raw=(json.dumps(again,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(sha256(raw).hexdigest(),REPORT_SHA)

    def test_26_no_original_source_or_hidden_reference_inventory_committed(self):
        report_text=REPORT.read_text(encoding="utf8")
        self.assertNotIn(self.guid,report_text)
        self.assertNotIn(self.case["public_question"],report_text)
        self.assertFalse(self.report["raw_target_GUID_original_IFC_or_public_question_text_in_report"])

    def test_27_full_original45_and_general_space_support_not_proven(self):
        self.assertFalse(self.report["new_full_original45_native_information_or_write_parity_proven"])
        self.assertFalse(self.report["other_original_IFC_Source_Space_deletion_universally_supported"])
        self.assertFalse(self.report["new_full_original45_developer_causal_representation_study_claim"])
        self.assertEqual(self.report["original_all45_intention_to_test_denominator"],45)


if __name__=="__main__":
    unittest.main()
