"""Issue #247: new bounded STEP-label-independent native IFC post-edit gate.

The 2 real IFC2X3/IFC4X3 D-full, 2 reindexed, 2 genuine isolated local
Docker Python-I and 16 negative candidate trials are re-executed via the
frozen offline auditor; report consistency tests are fast. No provider/API,
original author task grader, hidden GT or unseen source is opened.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
from unittest import TestCase, main

import ifcopenshell

from tools import audit_bibimbap_v066_native_semantic_admission as audit
from tools import bibimbap_v066_native_semantic_admission as gate


REPORT_SHA = "f908cc10086f0fb00efee0d8651385d378ef50221b7d6eab00ad42df7441d49b"
NEGATIVE_KINDS = {
    "added_orphan_anonymous_geometry",
    "added_unauthorized_root",
    "changed_existing_source_wall_name",
    "incorrect_real_door_width",
    "modified_existing_anonymous_geometry",
    "modified_existing_native_relationship",
    "modified_existing_source_owner_history",
    "wrong_hosted_wall_relation",
}


class NativeSemanticScope066Tests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(audit.OUTPUT.read_text("utf8"))

    def test_01_frozen_report_sha(self):
        self.assertEqual(sha256(audit.OUTPUT.read_bytes()).hexdigest(), REPORT_SHA)

    def test_02_report_is_canonical_bytes(self):
        self.assertEqual(audit.OUTPUT.read_bytes(), audit.canonical(self.data))

    def test_03_genuine_two_native_schemas_pinned(self):
        self.assertEqual(self.data["two_already_developer_exposed_native_source_schemas"],
                         ["IFC2X3", "IFC4X3"])
        self.assertEqual({c["schema"] for c in self.data["cases"]}, {"IFC2X3", "IFC4X3"})

    def test_04_real_native_D_full_legal(self):
        self.assertEqual(self.data["real_native_legal_D_full_cases"], 2)
        self.assertTrue(all(c["real_native_D_source_preservation_pass"] == gate.STATUS
                            for c in self.data["cases"]))

    def test_05_real_native_reindexed_legal(self):
        self.assertEqual(self.data["real_native_legal_step_reindexed_cases"], 2)
        self.assertTrue(all(c["real_native_reindexed_source_preservation_pass"] == gate.STATUS
                            for c in self.data["cases"]))

    def test_06_real_isolated_docker_python_imperative_valid(self):
        self.assertEqual(self.data[
            "real_pinned_linux_Docker_I_python_native_semantic_pass_cases"], 2)
        self.assertTrue(all(c["real_pinned_linux_docker_independent_python_I_pass"] == gate.STATUS
                            for c in self.data["cases"]))

    def test_07_same_source_native_physical_outcome_three_executions(self):
        self.assertTrue(all(c["D_I_reindexed_native_physical_semantic_digest_equal"]
                            for c in self.data["cases"]))
        self.assertTrue(all(len(c["native_edit_physical_semantic_SHA256"]) == 64
                            for c in self.data["cases"]))

    def test_08_real_negative_original_ifcs_all_rejected(self):
        self.assertEqual(self.data["real_native_illegal_candidates_rejected"], 16)
        self.assertEqual(sum(len(c["negative_real_native_IFC_mutation_rejected"])
                             for c in self.data["cases"]), 16)

    def test_09_same_negative_matrix_both_schemas(self):
        self.assertTrue(all(set(c["negative_real_native_IFC_mutation_rejected"]) == NEGATIVE_KINDS
                            for c in self.data["cases"]))

    def test_10_orphan_native_entity_rejected(self):
        self.assertTrue(all("New orphan" in c["negative_real_native_IFC_mutation_rejected"][
            "added_orphan_anonymous_geometry"] for c in self.data["cases"]))

    def test_11_new_unauthorized_ifcroot_rejected(self):
        self.assertTrue(all("Only one new Door" in c["negative_real_native_IFC_mutation_rejected"][
            "added_unauthorized_root"] for c in self.data["cases"]))

    def test_12_modified_existing_wall_name_rejected_by_graph(self):
        self.assertTrue(all("entity/attribute/reference graph changed" in
                            c["negative_real_native_IFC_mutation_rejected"][
                                "changed_existing_source_wall_name"]
                            for c in self.data["cases"]))

    def test_13_original_owner_history_change_rejected_by_graph(self):
        self.assertTrue(all("entity/attribute/reference graph changed" in
                            c["negative_real_native_IFC_mutation_rejected"][
                                "modified_existing_source_owner_history"]
                            for c in self.data["cases"]))

    def test_14_changed_original_anonymous_geometry_rejected(self):
        self.assertTrue(all("depth 1" in c["negative_real_native_IFC_mutation_rejected"][
            "modified_existing_anonymous_geometry"] for c in self.data["cases"]))

    def test_15_changed_original_ifc_relation_rejected(self):
        self.assertTrue(all("entity/attribute/reference graph changed" in
                            c["negative_real_native_IFC_mutation_rejected"][
                                "modified_existing_native_relationship"]
                            for c in self.data["cases"]))

    def test_16_wrong_native_void_host_rejected(self):
        self.assertTrue(all("Native Door outside" in c["negative_real_native_IFC_mutation_rejected"][
            "wrong_hosted_wall_relation"] for c in self.data["cases"]))

    def test_17_door_width_native_units_rejected(self):
        self.assertTrue(all("Door physical dimensions" in c["negative_real_native_IFC_mutation_rejected"][
            "incorrect_real_door_width"] for c in self.data["cases"]))

    def test_18_original_source_graph_multi_depth_preserved(self):
        self.assertTrue(all(c["source_entities_graph_depths"] == [0,1,2,4,8,16]
                            for c in self.data["cases"]))

    def test_19_source_only_not_author_task_success(self):
        self.assertIn("not target-specific public task correctness",
                      self.data["hard_limitations"][2])
        self.assertTrue(self.data["source_research_original_IFC_not_modified"])

    def test_20_no_provider_original_transfer_or_unseen(self):
        self.assertEqual(self.data["actual_provider_calls"], 0)
        self.assertEqual(self.data["external_original_IFC_uploads"], 0)
        self.assertEqual(self.data["independently_certified_unseen_original_source_families"], 0)
        self.assertTrue(self.data["all_original_provider_transfers_blocked"])

    def test_21_same_graph_not_dependent_on_step_numeric_ids_or_file_order(self):
        def build(swapped):
            f = ifcopenshell.file(schema="IFC4X3")
            if swapped:
                d = f.create_entity("IfcDirection", DirectionRatios=(0., 1., 0.))
                p = f.create_entity("IfcCartesianPoint", Coordinates=(1., 2., 3.))
            else:
                p = f.create_entity("IfcCartesianPoint", Coordinates=(1., 2., 3.))
                d = f.create_entity("IfcDirection", DirectionRatios=(0., 1., 0.))
            f.create_entity("IfcAxis2Placement3D", Location=p, RefDirection=d)
            return f
        self.assertNotEqual(
            [(e.id(), e.is_a()) for e in build(False)],
            [(e.id(), e.is_a()) for e in build(True)])
        self.assertEqual(gate._graph_hashes(build(False), 16),
                         gate._graph_hashes(build(True), 16))

    def test_22_native_graph_detects_nontrivial_original_geometry_mutation(self):
        def build(point):
            f = ifcopenshell.file(schema="IFC4X3")
            f.create_entity("IfcCartesianPoint", Coordinates=(point,2.,3.))
            return f
        self.assertNotEqual(gate._graph_hashes(build(1.0),16),
                            gate._graph_hashes(build(1.001),16))

    def test_23_serialization_roundtrip_quantization_is_bounded(self):
        f = ifcopenshell.file(schema="IFC4X3")
        f.create_entity("IfcCartesianPoint", Coordinates=(1.0000000000001,2.,3.))
        g = ifcopenshell.file(schema="IFC4X3")
        g.create_entity("IfcCartesianPoint", Coordinates=(1.,2.,3.))
        self.assertEqual(gate._graph_hashes(f,16),gate._graph_hashes(g,16))
        h = ifcopenshell.file(schema="IFC4X3")
        h.create_entity("IfcCartesianPoint", Coordinates=(1.000001,2.,3.))
        self.assertNotEqual(gate._graph_hashes(f,16),gate._graph_hashes(h,16))

    def test_24_duplicate_ifc_root_guid_fails_closed(self):
        f = ifcopenshell.file(schema="IFC4X3")
        f.create_entity("IfcBuildingElementProxy", GlobalId="0"*22)
        f.create_entity("IfcBuildingElementProxy", GlobalId="0"*22)
        with self.assertRaises(gate.SemanticNative066Error):
            gate._roots_by_guid(f)

    def test_25_native_status_explicit_scope(self):
        self.assertIn("BOUNDED_STEP_INDEPENDENT",gate.STATUS)
        self.assertEqual(gate.ROOT_CLASSES, sorted(gate.ROOT_CLASSES))
        self.assertIn("not a complete arbitrary IFC", self.data["hard_limitations"][1])


if __name__ == "__main__":
    main()
