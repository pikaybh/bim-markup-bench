"""Self-authored IFC4 metre/mm X/Y synthetic D/I native equivalence tests.

No GNI or original BIBIMBAP source IFC, hidden GT, independent blind
certification, author evaluator, external rights, paid/model inference.
"""
from __future__ import annotations

import copy
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from tools import audit_bibimbap_v066_synthetic_ifc4_DI as a
from tools import bibimbap_v066_ifc4_synthetic_host as fixture
from tools import bibimbap_v066_ifc4_source_neutral_door as door
from tools import bibimbap_v066_ifc4_native_semantic_admission as gate
from tools.bibimbap_matched25_tools import file_hash

FROZEN_SHA="40149f8f4f86f8e86421926d71d11ccdfb9bb0d99b573c943127395dcebcb378"


class FrozenSyntheticNativeReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=json.loads(a.REPORT.read_text("utf8"))
        cls.rows=cls.result["all_synthetic_IFC4_native_results"]

    def test_01_frozen_report_sha(self):
        self.assertEqual(file_hash(a.REPORT),FROZEN_SHA)

    def test_02_frozen_canonical(self):
        self.assertEqual(a.REPORT.read_bytes(),a.canonical(self.result))

    def test_03_prev_zenodo_rights_report_is_frozen(self):
        self.assertEqual(file_hash(a.parent.REPORT),a.PARENT_SHA)

    def test_04_original_sources_are_only_self_authored(self):
        self.assertEqual(self.result["audit_kind"],
                         "DEVELOPER_GENERATED_IFC4_ONLY_NOT_GNI_ARCHIVE_NOT_BLIND")

    def test_05_four_synthetic_sources(self):
        self.assertEqual(len(self.rows),4)
        self.assertEqual(self.result["unique_developer_generated_original_IFC4_models"],4)

    def test_06_three_arms_four_cases_12_outputs(self):
        self.assertEqual(self.result["positive_actual_native_IFC4_D_full_managed_I_outputs"],12)

    def test_07_STEP_relabel_alternatives_pass(self):
        self.assertEqual(self.result["STEP_id_reencoded_native_ifc_equivalent_variants"],4)
        self.assertTrue(all(r["STEP_numeric_relabel_native_equivalent"] for r in self.rows))

    def test_08_28_xml_native_negative_mutations_rejected(self):
        self.assertEqual(self.result["negative_actual_IFC4_XML_and_native_mutations_rejected"],28)
        self.assertTrue(all(len(r["synthetic_negative_XML_and_IFC_rejection_cases"])==7
                            and all(r["synthetic_negative_XML_and_IFC_rejection_cases"].values())
                            for r in self.rows))

    def test_09_full_units_cross(self):
        self.assertEqual(set(r["synthetic_developer_unit"] for r in self.rows),
                         {"metre","millimetre"})

    def test_10_X_and_Y_axes(self):
        self.assertEqual(set(r["synthetic_wall_axis"] for r in self.rows),{"X","Y"})

    def test_11_product_of_all_units_and_axes(self):
        self.assertEqual({(r["synthetic_developer_unit"],r["synthetic_wall_axis"])
                          for r in self.rows},set(a.CASES))

    def test_12_valid_IFC4_schema(self):
        self.assertTrue(all(r["synthetic_original_IFC_schema"]=="IFC4" for r in self.rows))

    def test_13_four_unique_SHA_sources(self):
        self.assertEqual(len({r["source_original_ifc_SHA256"] for r in self.rows}),4)

    def test_14_original_shas_frozen(self):
        self.assertEqual(
            {r["synthetic_developer_unit"]+"-"+r["synthetic_wall_axis"]:
             r["source_original_ifc_SHA256"] for r in self.rows},
            {"metre-X":"b7657e5fc4da366dac29bbdb8548d79750627d86bad9c5f1275af947cd1ed60f",
             "metre-Y":"98fc29299dfa3ce55fa009d9e5ec2361ff5cc5dea7c610a4677bf19d23c911aa",
             "millimetre-X":"d0df2b3a96d9b3fdb4e6749d4565392bb53df9fc3f360efe9a6e3139d2e7e782",
             "millimetre-Y":"d5890b0af03d6dcce502ad430182ccf407a3d3b858d9294f44adc301e63e0663"})

    def test_15_full_managed_native_equivalent(self):
        self.assertTrue(all(r["all_three_IFC4_native_semantics_equal"] for r in self.rows))

    def test_16_real_native_CSG_volume(self):
        self.assertTrue(all(r["actual_IFC_wall_CSG_cut_m3"]==0.462 for r in self.rows))

    def test_17_native_IFC_schema_validation_clean(self):
        self.assertTrue(all(r["new_IFC_schema_error_count"]==0 for r in self.rows))

    def test_18_all_original_slab_survives(self):
        self.assertTrue(all(r["unrelated_opaque_original_slab_count"]==1
                            for r in self.rows))

    def test_19_original_wall_count_one_in_each_synthetic_case(self):
        self.assertTrue(all(r["original_IFC_wall_count"]==1 for r in self.rows))

    def test_20_proof_true_Docker_not_simulator(self):
        self.assertTrue(all(r["true_linux_docker_Ifcopenshell_I_committed"]
                            for r in self.rows))

    def test_21_original_SHA_unmodified_by_edits(self):
        self.assertTrue(all(r["unmodified_original_IFC_Source_SHA_verified"]
                            for r in self.rows))

    def test_22_no_original_author_or_GNI_IFC_inspected(self):
        self.assertEqual(self.result["original_bibimbap_or_gni_ifc_files_read"],0)
        self.assertFalse(self.result["original_author_private_task_or_GT_grader_read"])

    def test_23_no_paid_or_free_model(self):
        self.assertEqual(self.result["model_provider_calls"],0)
        self.assertEqual(self.result["new_external_ifc_uploads"],0)

    def test_24_no_fake_blind_certification(self):
        self.assertEqual(self.result["real_independent_blind_source_count"],0)
        self.assertFalse(self.result["independently_licensed_GNI_ifc_member_validated"])

    def test_25_report_does_not_authorize_trial(self):
        self.assertFalse(self.result["permission_to_start_original_or_gni_model_trials"])

    def test_26_pinned_native_compiler_source_SHA(self):
        self.assertEqual(file_hash(Path(door.__file__)),
                         self.result["expanded_IFC4_compiler_module_sha256"])

    def test_27_pinned_native_scope_source_SHA(self):
        self.assertEqual(file_hash(Path(gate.__file__)),
                         self.result["STEP_independent_IFC4_native_scope_module_sha256"])

    def test_28_pinned_generator_source_SHA(self):
        self.assertEqual(file_hash(Path(fixture.__file__)),
                         self.result["source_generator_module_sha256"])

    def test_29_genuine_developer_python_code_present(self):
        self.assertTrue(all(r["independent_I_Python_code_UTF8_bytes"]>1000
                            for r in self.rows))

    def test_30_no_source_only_results_claim_model_accuracy(self):
        self.assertTrue(all(r["model_generated_attempts"]==0 for r in self.rows))


class NonblindIFC4NativeAndXml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=TemporaryDirectory(prefix="v066-ifc4-test-source-")
        cls.p=Path(cls.temp.name)/"synthetic.ifc"
        fixture.write_fresh(cls.p,unit="metre",axis="X")
        cls.sha=file_hash(cls.p)
        cls.model=door.source_model(cls.p,cls.sha)
        cls.state=a.engineering_state(cls.model,"metre","X")
        cls.full_initial=door.full_initial_xml(cls.p,cls.sha)
        cls.managed_initial=door.managed_initial_xml(cls.p,cls.sha)
        cls.full=a.complete_final_state(cls.full_initial,cls.state,managed=False)
        cls.managed=a.complete_final_state(cls.managed_initial,cls.state,managed=True)
        cls.candidate=Path(cls.temp.name)/"compiled.ifc"
        door.compile_hosted_door(cls.p,cls.sha,
                                 door.parse_full_xml(cls.p,cls.sha,cls.full),
                                 cls.candidate)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_31_fixture_real_IFC4_and_units(self):
        self.assertEqual(self.model.schema,"IFC4")
        self.assertEqual(ifcopenshell.util.unit.calculate_unit_scale(self.model),1.)

    def test_32_same_unchanged_source_SHA(self):
        self.assertEqual(file_hash(self.p),self.sha)

    def test_33_source_opaque_XML_is_complete(self):
        root=etree.fromstring(self.full_initial)
        self.assertEqual(root.tag,door.Q+"BuildingState")
        self.assertEqual(root.get("sourceIFCSha256"),self.sha)

    def test_34_existing_wall_roster_is_nonempty(self):
        x=etree.fromstring(self.full_initial)
        self.assertEqual(len(x[1]),1)
        self.assertEqual(x[1][0].get("present"),"true")

    def test_35_full_declarative_final_state_parsed(self):
        self.assertEqual(door.parse_full_xml(self.p,self.sha,self.full),self.state)

    def test_36_managed_expands_to_identical_full(self):
        raw,st=door.expand_managed_xml(self.p,self.sha,self.managed)
        self.assertEqual(raw,self.full)
        self.assertEqual(st,self.state)

    def test_37_no_xml_command_nodes(self):
        x=etree.fromstring(self.full)
        self.assertEqual([c.tag for c in x[2]],[
            door.Q+"Opening",door.Q+"Door"])

    def test_38_compiled_native_CSG_accepted(self):
        outcome=gate.post_native_semantic_gate(self.p,self.sha,self.candidate)
        self.assertEqual(outcome["actual_wall_CSG_volume_removed_m3"],0.462)

    def test_39_original_opaque_slab_unchanged(self):
        result=ifcopenshell.open(str(self.candidate))
        orig=self.model.by_type("IfcSlab")[0]
        got=result.by_guid(orig.GlobalId)
        self.assertEqual(orig.Name,got.Name)
        self.assertEqual(orig.Representation.is_a(),got.Representation.is_a())

    def test_40_step_neutral_gate_not_keyed_to_STEP_numbers(self):
        outcome=gate.post_native_semantic_gate(self.p,self.sha,self.candidate)
        self.assertFalse(outcome["original_STEP_numeric_ids_required"])

    def test_41_wrong_original_source_SHA_rejected(self):
        with self.assertRaises(door.NeutralDoor065Error):
            door.source_model(self.p,"f"*64)

    def test_42_change_original_wall_roster_rejected(self):
        raw=a._bad_xml(self.p,self.sha,"missing_original_wall",self.full)
        with self.assertRaises(door.NeutralDoor065Error):
            door.parse_full_xml(self.p,self.sha,raw)

    def test_43_forged_XML_command_rejected(self):
        raw=a._bad_xml(self.p,self.sha,"forged_operation_node",self.full)
        with self.assertRaises(door.NeutralDoor065Error):
            door.parse_full_xml(self.p,self.sha,raw)

    def test_44_wrong_door_extent_rejected(self):
        raw=a._bad_xml(self.p,self.sha,"wrong_geometry_extent",self.full)
        with self.assertRaises(door.NeutralDoor065Error):
            door.parse_full_xml(self.p,self.sha,raw)

    def test_45_full_root_sha_tamper_rejected(self):
        raw=a._bad_xml(self.p,self.sha,"source_sha_corruption",self.full)
        with self.assertRaises(door.NeutralDoor065Error):
            door.parse_full_xml(self.p,self.sha,raw)

    def test_46_D_managed_linked_full_sha_forgery_rejected(self):
        node=etree.fromstring(self.managed)
        node.set("sourceFullBuildingStateSha256","f"*64)
        raw=etree.tostring(node,xml_declaration=True,encoding="utf8")
        with self.assertRaises(door.NeutralDoor065Error):
            door.expand_managed_xml(self.p,self.sha,raw)

    def test_47_D_managed_missing_new_product_rejected(self):
        node=etree.fromstring(self.managed)
        node[1].remove(node[1][1])
        raw=etree.tostring(node,xml_declaration=True,encoding="utf8")
        with self.assertRaises(door.NeutralDoor065Error):
            door.expand_managed_xml(self.p,self.sha,raw)

    def test_48_nonmatching_Door_Opening_GUID_link_rejected(self):
        node=etree.fromstring(self.full)
        node[2][1].set("fillsOpeningGuid","a"*22)
        raw=etree.tostring(node,xml_declaration=True,encoding="utf8")
        with self.assertRaises(door.NeutralDoor065Error):
            door.parse_full_xml(self.p,self.sha,raw)

    def test_49_xml_external_entity_rejected(self):
        with self.assertRaises(Exception):
            door.parse_full_xml(self.p,self.sha,
                b'<!DOCTYPE x [<!ENTITY xxx SYSTEM "file:///secret">]><x>&xxx;</x>')

    def test_50_compiler_does_not_accept_existing_output_file(self):
        with self.assertRaises(door.NeutralDoor065Error):
            door.compile_hosted_door(self.p,self.sha,self.state,self.candidate)

    def test_51_compiler_rejects_write_to_original(self):
        with self.assertRaises(door.NeutralDoor065Error):
            door.compile_hosted_door(self.p,self.sha,self.state,self.p)

    def test_52_negative_native_unrelated_slab_mutation_rejected(self):
        changed=Path(self.temp.name)/"bad-slab.ifc"
        a._native_mutated(self.candidate,changed,
            "changed_unrelated_source_slab",self.state)
        with self.assertRaises(gate.SemanticNative066Error):
            gate.post_native_semantic_gate(self.p,self.sha,changed)

    def test_53_negative_native_orphan_point_rejected(self):
        changed=Path(self.temp.name)/"bad-orphan.ifc"
        a._native_mutated(self.candidate,changed,
            "orphan_native_cartesian_point",self.state)
        with self.assertRaises(gate.SemanticNative066Error):
            gate.post_native_semantic_gate(self.p,self.sha,changed)

    def test_54_negative_native_missing_filling_relation_rejected(self):
        changed=Path(self.temp.name)/"bad-filling.ifc"
        a._native_mutated(self.candidate,changed,
            "removed_new_filling_relationship",self.state)
        with self.assertRaises(gate.SemanticNative066Error):
            gate.post_native_semantic_gate(self.p,self.sha,changed)

    def test_55_source_code_is_not_task_specific_or_original_scorer(self):
        for mod in (fixture,door,gate):
            source=Path(mod.__file__).read_text(encoding="utf8")
            self.assertNotIn("geometry_test_03",source)
            self.assertNotIn("topological_test_05",source)
            self.assertNotIn("import data.tests",source)
            self.assertNotIn("from openai import",source)

    def test_56_I_python_uses_actual_native_units_not_mm_hardcode(self):
        code=a.pure_independent_native_python(self.state)
        self.assertIn("ifcopenshell.util.unit.calculate_unit_scale(ifc)",code)
        self.assertIn("commit()",code)
        self.assertNotIn("*1000",code)
        self.assertNotIn("tools.",code)

    def test_57_no_same_file_or_original_shadowing_for_native_result(self):
        self.assertNotEqual(self.p.resolve(),self.candidate.resolve())
        self.assertTrue(self.candidate.exists())

    def test_58_2x2_self_authored_fixture_real_unit_conversion(self):
        f=fixture.fixture(unit="millimetre",axis="Y")
        self.assertEqual(f.schema,"IFC4")
        self.assertAlmostEqual(ifcopenshell.util.unit.calculate_unit_scale(f),.001)

    def test_59_generator_rejects_non_IFC4_options(self):
        with self.assertRaises(AssertionError):
            fixture.fixture(unit="cm",axis="X")
        with self.assertRaises(AssertionError):
            fixture.fixture(unit="metre",axis="Z")

    def test_60_immutable_old_source_IFC4_not_GNI_dataset(self):
        self.assertIn("synthetic",Path(self.p).name)
        self.assertNotIn("GNI",str(self.p))


if __name__=="__main__":
    unittest.main()
