"""Issue #247 synthetic IFC4 Window MOVE/DELETE bounded native D/I audit tests.

These tests do NOT test a model, new GNI/original IFC, blind source, private
GT, paper author's grader, or legal/provider release. Actual real IFC/Docker
outputs are reproduced by the companion --check audit, not mocked.
"""
from __future__ import annotations
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from lxml import etree
import ifcopenshell

from tools import audit_bibimbap_v066_synthetic_ifc4_window_DI as a
from tools import bibimbap_v066_ifc4_window_synthetic_host as synth
from tools import bibimbap_v066_ifc4_window_final_state as window
from tools import bibimbap_v066_ifc4_window_native_scope as scope
from tools.bibimbap_matched25_tools import file_hash

FROZEN_SHA="4d95bb260cd8203bf282b2a5fb7293760aa356ff9a234584f34d5324fdc02300"

class FrozenWindowIFC4Audit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(a.REPORT.read_text("utf8"))
        cls.cases=cls.report["case_results"]
        cls.ops=[v for row in cls.cases for v in row["native_real_operations"]]

    def test_01_frozen_sha(self):
        self.assertEqual(file_hash(a.REPORT),FROZEN_SHA)
    def test_02_canonical_bytes(self):
        self.assertEqual(a.REPORT.read_bytes(),a.canonical(self.report))
    def test_03_previous_doors_report_untouched(self):
        self.assertEqual(file_hash(a.door_audit.REPORT),a.PARENT_SHA)
    def test_04_four_original_IFC4_synthetic(self):
        self.assertEqual(self.report["self_authored_IFC4_source_count"],4)
        self.assertEqual(len(self.cases),4)
    def test_05_units_both(self):
        self.assertEqual(set(x["synthetic_unit"] for x in self.cases),
                         {"metre","millimetre"})
    def test_06_both_wall_orientation_axes(self):
        self.assertEqual(set(x["synthetic_wall_axis"] for x in self.cases),
                         {"X","Y"})
    def test_07_full_cross_product_cases(self):
        self.assertEqual({(x["synthetic_unit"],x["synthetic_wall_axis"])
                          for x in self.cases},set(a.CASES))
    def test_08_all_sources_IFC4(self):
        self.assertTrue(all(x["source_original_schema"]=="IFC4"
                            for x in self.cases))
    def test_09_all_two_original_Windows(self):
        self.assertTrue(all(x["source_initial_unmodified_windows"]==2
                            for x in self.cases))
    def test_10_unrelated_source_slab_preserved(self):
        self.assertTrue(all(x["source_original_unrelated_slabs"]==1
                            for x in self.cases))
    def test_11_four_unique_source_hashes(self):
        self.assertEqual(len({x["source_original_ifc_sha256"]
                              for x in self.cases}),4)
    def test_12_frozen_source_hashes(self):
        expected={
            "metre_X":"fc932427e54f5740b879fc17c382963b2188175c9031843a0f107173328b428a",
            "metre_Y":"c1bbfe9000174ddaa97bc1c15bcb70a2182aac26e070569986635a3e6b4ab020",
            "millimetre_X":"370e83184cfb69a9430a021ece1bf069673d0e1b5118eae1a7cbc69bb77eb6f8",
            "millimetre_Y":"cc4742e8e65ad36ffe480ad119da09f30fa68ca2b823c68e59bbdf45126b191a",
        }
        self.assertEqual({
            x["synthetic_unit"]+"_"+x["synthetic_wall_axis"]:
            x["source_original_ifc_sha256"] for x in self.cases},expected)
    def test_13_pairs_are_8(self):
        self.assertEqual(self.report["source_operation_pairs_executed"],8)
        self.assertEqual(len(self.ops),8)
    def test_14_each_case_move_and_delete(self):
        self.assertTrue(all([v["operation_family"]
                            for v in row["native_real_operations"]]==["move","delete"]
                            for row in self.cases))
    def test_15_all_D_FULL_native_executed(self):
        self.assertEqual(self.report["actual_native_D_FULL_outputs"],8)
    def test_16_all_D_MANAGED_native_executed(self):
        self.assertEqual(self.report["actual_native_D_MANAGED_outputs"],8)
    def test_17_all_independent_Docker_Python_executed(self):
        self.assertEqual(self.report["actual_native_pinned_Linux_Docker_I_outputs"],8)
    def test_18_every_pair_D_I_semantically_equal(self):
        self.assertTrue(all(op["real_native_D_full_managed_I_semantically_equal"]
                            for op in self.ops))
    def test_19_every_case_real_Docker_committed(self):
        self.assertTrue(all(op["real_linux_pinned_Docker_I_committed"]
                            for op in self.ops))
    def test_20_STEP_reencoded_real_native_8(self):
        self.assertEqual(self.report["step_relabel_physically_admissible_outputs"],8)
        self.assertTrue(all(op["actual_native_STEP_reencoded_variant"]
                            for op in self.ops))
    def test_21_invalid_XML_32_rejected(self):
        self.assertEqual(self.report["bad_final_XML_controls_rejected"],32)
        self.assertTrue(all(
            len(op["bad_xml_controls_all_rejected"])==4 and
            all(op["bad_xml_controls_all_rejected"].values()) for op in self.ops))
    def test_22_invalid_native_IFC_24_rejected(self):
        self.assertEqual(self.report["bad_native_IFC_mutations_rejected"],24)
        self.assertTrue(all(
            len(op["bad_native_mutations_all_rejected"])==3 and
            all(op["bad_native_mutations_all_rejected"].values()) for op in self.ops))
    def test_23_source_original_not_mutated(self):
        self.assertTrue(all(op["original_IFC_unchanged"] for op in self.ops))
    def test_24_no_original_BIBIMBAP_or_GNI_IFC_read(self):
        self.assertEqual(self.report["original_BIBIMBAP_or_GNI_ifc_inputs_read"],0)
    def test_25_no_author_private_grader_or_GT(self):
        self.assertEqual(self.report["original_author_hidden_grader_or_GT_read"],0)
    def test_26_no_original_IFC_external_upload(self):
        self.assertEqual(self.report["external_original_ifc_uploads"],0)
    def test_27_no_model_trials(self):
        self.assertEqual(self.report["model_generated_attempts"],0)
        self.assertTrue(all(op["model_generated_trials"]==0 for op in self.ops))
    def test_28_independently_blind_count_remains_zero(self):
        self.assertEqual(self.report["independently_untouched_sample_count"],0)
    def test_29_no_owner_provider_approval(self):
        self.assertFalse(self.report["owner_provider_or_scorer_trial_authorized"])
        self.assertFalse(self.report["per_IFC_rights_or_transfer_approved"])
    def test_30_not_general_IFC4_support(self):
        self.assertTrue(self.report["not_universal_IFC4_support"])
        self.assertTrue(self.report["known_uncovered"])
    def test_31_compiler_source_SHA_recorded(self):
        self.assertEqual(file_hash(Path(window.__file__)),
                         self.report["source_neutral_final_xml_compiler_SHA256"])
    def test_32_native_semantic_scope_SHA_recorded(self):
        self.assertEqual(file_hash(Path(scope.__file__)),
                         self.report["independent_native_step_neutral_gate_SHA256"])
    def test_33_synthetic_generator_source_SHA_recorded(self):
        self.assertEqual(file_hash(Path(synth.__file__)),
                         self.report["source_generator_SHA256"])
    def test_34_no_command_XML_in_model_facing_D(self):
        for token in ("<Move","<Delete","<Update","<Create"):
            self.assertNotIn(token,Path(window.__file__).read_text("utf8"))
    def test_35_no_model_or_grader_or_archive_in_compiler(self):
        src=Path(window.__file__).read_text("utf8")
        for forbidden in ("import data.tests", "from openai import",
                          "geometry_test_13","geometry_test_19",
                          "GNI-BIM-Dataset"):
            self.assertNotIn(forbidden,src)
    def test_36_independent_I_code_not_D_compiler(self):
        src=a.genuine_independent_I_code("move",0,(.25,0.,0.))
        self.assertIn("commit()",src)
        self.assertIn("calculate_unit_scale(ifc)",src)
        self.assertNotIn("bibimbap_v066_ifc4_window_final_state",src)
        self.assertNotIn("tools.",src)
    def test_37_real_native_model_I_code_for_delete(self):
        src=a.genuine_independent_I_code("delete",0,(0.,.25,0.))
        self.assertIn("root.remove_product",src)
        self.assertIn("commit()",src)
    def test_38_selected_group_member_count_2(self):
        self.assertTrue(all(op["original_selected_group_members"]==2
                            for op in self.ops))
    def test_39_move_world_units_25cm(self):
        move=[op for op in self.ops if op["operation_family"]=="move"]
        self.assertEqual([op["source_only_world_offset_metres"] for op in move],
                         [[.25,0.,0.],[0.,.25,0.],[.25,0.,0.],[0.,.25,0.]])
    def test_40_delete_world_offset_absent(self):
        self.assertTrue(all(op["source_only_world_offset_metres"] is None
                            for op in self.ops if op["operation_family"]=="delete"))
    def test_41_full_initial_XML_nonempty(self):
        self.assertTrue(all(op["D_FULL_initial_xml_utf8_bytes"]>1000
                            for op in self.ops))
    def test_42_managed_initial_smaller_than_full(self):
        self.assertTrue(all(op["D_MANAGED_initial_xml_utf8_bytes"]<
                            op["D_FULL_initial_xml_utf8_bytes"] for op in self.ops))
    def test_43_op_final_state_native_digests_separate(self):
        for row in self.cases:
            self.assertEqual(len({
                op["same_physical_native_edit_digest"]
                for op in row["native_real_operations"]}),2)


class SyntheticWindowEngineXML(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=TemporaryDirectory(prefix="v066-ifc4-win-unit-")
        cls.source=Path(cls.temp.name)/"source.ifc"
        synth.write_fresh(cls.source,unit="metre",axis="X")
        cls.sha=file_hash(cls.source)
        cls.model=window.source(cls.source,cls.sha)
        cls.groups=window.groups(cls.model)
        cls.selected=cls.groups[sorted(cls.groups)[0]]
        cls.full=window.full_source_state(cls.source,cls.sha)
        cls.managed=window.managed_source_state(cls.source,cls.sha)
        cls.moved=a.submitted_final_state(
            cls.full,cls.selected,"move",(.25,0.,0.),managed=False)
        cls.deleted=a.submitted_final_state(
            cls.full,cls.selected,"delete",(.25,0.,0.),managed=False)
    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_44_native_IFC4_contains_two_hosted_Windows(self):
        self.assertEqual(self.model.schema,"IFC4")
        self.assertEqual(len(self.groups),2)
    def test_45_Each_Window_parent_to_opening(self):
        self.assertTrue(all(
            g["window"].ObjectPlacement.PlacementRelTo==g["opening"].ObjectPlacement
            for g in self.groups.values()))
    def test_46_source_complete_D_FULL_XML_schema(self):
        node=etree.fromstring(self.full)
        self.assertEqual(node.get("sourceIFCSchema"),"IFC4")
        self.assertEqual(node.get("sourceLengthUnit"),"METRE")
    def test_47_source_managed_XML_initial_two_windows_plus_openings(self):
        self.assertEqual(len(etree.fromstring(self.managed)),4)
    def test_48_full_state_move_is_a_semantic_difference(self):
        out=window.parse_full_state(self.source,self.sha,self.moved)
        self.assertEqual(out["kind"],"move")
        self.assertEqual(out["world_m"],(.25,0.,0.))
    def test_49_full_state_delete_is_a_semantic_difference(self):
        self.assertEqual(
            window.parse_full_state(self.source,self.sha,self.deleted)["kind"],"delete")
    def test_50_D_MANAGED_rehydration_parity(self):
        compact=a.submitted_final_state(self.managed,self.selected,"move",
                                        (.25,0.,0.),managed=True)
        expanded,out=window.expand_managed_state(self.source,self.sha,compact)
        self.assertEqual(expanded,self.moved)
        self.assertEqual(out["kind"],"move")
    def test_51_reject_old_source_sha_forgery(self):
        with self.assertRaises(window.FinalWindow066Error):
            window.source(self.source,"f"*64)
    def test_52_reject_partial_Windows_assembly_change(self):
        wrong=a.invalid_xml(self.moved,self.selected,"move",(.25,0.,0.),
                            "partial_window_group_change")
        with self.assertRaises(window.FinalWindow066Error):
            window.parse_full_state(self.source,self.sha,wrong)
    def test_53_reject_attempt_to_insert_operation_XML(self):
        wrong=a.invalid_xml(self.moved,self.selected,"move",(.25,0.,0.),
                            "forged_XML_move_command")
        with self.assertRaises(window.FinalWindow066Error):
            window.parse_full_state(self.source,self.sha,wrong)
    def test_54_reject_roster_drop(self):
        wrong=a.invalid_xml(self.deleted,self.selected,"delete",(.25,0.,0.),
                            "one_managed_element_missing")
        with self.assertRaises(window.FinalWindow066Error):
            window.parse_full_state(self.source,self.sha,wrong)
    def test_55_reject_no_op_final(self):
        with self.assertRaises(window.FinalWindow066Error):
            window.parse_full_state(self.source,self.sha,self.full)
    def test_56_reject_XML_entity_expansion(self):
        raw=b'<!DOCTYPE a [<!ENTITY xx SYSTEM "file:///private">]><a>&xx;</a>'
        with self.assertRaises(Exception):
            window.parse_full_state(self.source,self.sha,raw)
    def test_57_source_without_original_window_groups_rejected(self):
        from tools.bibimbap_v066_ifc4_synthetic_host import fixture as blank
        source=Path(self.temp.name)/"empty-window-source.ifc"
        blank(unit="metre",axis="X").write(str(source))
        with self.assertRaises(window.FinalWindow066Error):
            window.source(source,file_hash(source))
    def test_58_original_SOURCE_Slab_remains_unrelated(self):
        self.assertEqual(len(self.model.by_type("IfcSlab")),1)
    def test_59_no_paper_scorer_imports_in_tool(self):
        for m in (synth,window,scope):
            t=Path(m.__file__).read_text("utf8")
            self.assertNotIn("from data.tests",t)
            self.assertNotIn("from openai import",t)
    def test_60_source_xml_never_containing_action_command(self):
        self.assertNotIn(b"<Move",self.moved)
        self.assertNotIn(b"<Delete",self.deleted)


if __name__=="__main__":
    unittest.main()
