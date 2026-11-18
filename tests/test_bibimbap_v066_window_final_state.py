"""v0.66 declaration-first native Window MOVE/DELETE two-source offline tests."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import unittest

from lxml import etree

from tools import audit_bibimbap_v065_offline_generalization as earlier
from tools import audit_bibimbap_v066_window_final_state as audit
from tools import bibimbap_v066_window_final_state as xml
from tools import bibimbap_v066_window_native_scope as native

REPORT_SHA="b7ee995579d32a887dc5a34882950f2b967861b27e132591b7dd8fab40b7c8be"


class FrozenWindowFinalState066(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(audit.REPORT.read_text("utf8"))

    def test_01_frozen_report_sha(self):
        self.assertEqual(sha256(audit.REPORT.read_bytes()).hexdigest(),REPORT_SHA)

    def test_02_canonical_report_bytes(self):
        self.assertEqual(audit.REPORT.read_bytes(),audit.canonical(self.report))

    def test_03_two_distinct_immutable_developer_exposed_sources(self):
        self.assertEqual(self.report["actual_native_original_source_count"],2)
        self.assertEqual(len({c["source_SHA256"] for c in self.report["cases"]}),2)

    def test_04_only_ifc4x3_not_claimed_other_schemas(self):
        self.assertEqual(self.report["supported_schema"],"IFC4X3")
        self.assertTrue(all(c["source_schema"]=="IFC4X3" for c in self.report["cases"]))
        self.assertIn("IFC2X3 hosted Window move/delete not demonstrated",
                      self.report["unsupported_schema_or_complexity"])

    def test_05_two_operations_each_two_source_families(self):
        self.assertEqual(self.report["operation_source_pairs_executed"],4)
        self.assertTrue(all({c["operation_family"] for c in src["cases"]}
                            == {"move","delete"} for src in self.report["cases"]))

    def test_06_D_full_native_four(self):
        self.assertEqual(self.report["real_native_XML_D_FULL_outputs"],4)
        self.assertTrue(all(c["D_FULL_real_IFC_accepted"] for
                            source in self.report["cases"] for c in source["cases"]))

    def test_07_D_managed_native_four(self):
        self.assertEqual(self.report["real_native_XML_D_MANAGED_outputs"],4)
        self.assertTrue(all(c["D_MANAGED_real_IFC_accepted"] for
                            source in self.report["cases"] for c in source["cases"]))

    def test_08_pinned_actual_linux_docker_python_four(self):
        self.assertEqual(self.report["actual_pinned_Linux_Docker_Python_I_outputs"],4)
        self.assertTrue(all(c[
            "independent_pinned_Linux_Docker_Python_I_real_IFC_accepted"]
            for source in self.report["cases"] for c in source["cases"]))

    def test_09_all_sixteen_native_legal_outputs_including_STEP_relabels(self):
        self.assertEqual(self.report["legal_native_edit_output_accepts"],16)
        self.assertEqual(self.report[
            "actual_native_bijective_STEP_ID_relabel_valid_ifc_outputs"],4)
        self.assertTrue(all(
            c["D_FULL_native_bijective_STEP_ID_relabel_real_IFC_accepted"]
            and c["actual_bijectively_remapped_native_STEP_entities"] > 100
            for s in self.report["cases"] for c in s["cases"]))

    def test_10_all_eight_real_IFC_negative_controls(self):
        self.assertEqual(self.report["illegal_native_mutation_rejects"],8)
        self.assertEqual(sum(len(c["native_illegal_mutations_rejected"])
                             for s in self.report["cases"] for c in s["cases"]),8)

    def test_11_unsynced_window_detail_rejected(self):
        sample=next(s for s in self.report["cases"]
                    if s["already_developer_exposed_source_task_for_audit_only"]
                    =="geometry_test_13")
        move=next(c for c in sample["cases"] if c["operation_family"]=="move")
        self.assertIn("world geometry invalid",
                      move["native_illegal_mutations_rejected"][
                          "unsynced_hosted_detail_proxy"])

    def test_12_extra_window_deletion_rejected(self):
        self.assertTrue(all("Only one already existing Window" in
            c["native_illegal_mutations_rejected"]["delete_second_unapproved_Window"]
            for s in self.report["cases"] for c in s["cases"]
            if c["operation_family"]=="delete"))

    def test_13_existing_wall_tamper_rejected_both(self):
        self.assertTrue(all("native" in
            c["native_illegal_mutations_rejected"][
                "alter_unrelated_existing_Wall_metadata"].lower()
            for s in self.report["cases"] for c in s["cases"]))

    def test_14_native_orphan_rejected(self):
        sample=next(s for s in self.report["cases"]
                    if s["already_developer_exposed_source_task_for_audit_only"]
                    =="geometry_test_19")
        move=next(c for c in sample["cases"] if c["operation_family"]=="move")
        self.assertIn("graph mismatch",
                      move["native_illegal_mutations_rejected"][
                          "add_unauthorized_orphan_native_entity"])

    def test_15_source_groups_2_and_7_documented(self):
        self.assertEqual(sorted(x["native_groups"] for x in self.report["cases"]),
                         [2,7])

    def test_16_assemblies_2_vs_5_fully_sync(self):
        self.assertEqual(set(c["source_native_original_member_group_count"]
                             for s in self.report["cases"] for c in s["cases"]),
                         {2,5})

    def test_17_all_D_full_managed_I_semantic_edit_equal(self):
        self.assertTrue(all(len(c["all_three_same_native_physical_semantic_digest"])==64
                            for s in self.report["cases"] for c in s["cases"]))

    def test_18_declaration_no_command_objects(self):
        code=Path(xml.__file__).read_text("utf8")
        self.assertNotIn('Q+"Move"',code)
        self.assertNotIn('Q+"Delete"',code)
        self.assertNotIn('Q+"Update"',code)
        self.assertTrue(self.report["D_document_has_no_move_delete_command_elements"])

    def test_19_agent_facing_compiler_has_no_task_ID(self):
        src=Path(xml.__file__).read_text("utf8")
        self.assertNotIn("geometry_test_13",src)
        self.assertNotIn("geometry_test_19",src)
        self.assertNotIn("target_guid",src)
        self.assertNotIn("data.tests",src)

    def test_20_no_model_upload_or_original_hidden_evaluator_access(self):
        self.assertEqual(self.report["model_provider_calls"],0)
        self.assertEqual(self.report["original_IFC_uploads"],0)
        self.assertEqual(self.report["original_author_or_private_grader_accesses"],0)
        self.assertTrue(self.report["all_original_source_SHA_checks_unchanged"])

    def test_21_original_blind_and_transfer_still_blocked(self):
        self.assertEqual(self.report["independently_certified_blind_original_IFC_sources"],0)
        self.assertEqual(self.report[
            "source_net_ISOLATION_and_preregistered_external_transfer_rights"],"BLOCKED")

    def test_22_xml_full_and_managed_source_sizes_measured(self):
        self.assertTrue(all(
            0 < c["D_MANAGED_source_xml_bytes"] < c["D_FULL_source_xml_bytes"]
            and c["D_MANAGED_final_state_xml_bytes"] <
                c["D_FULL_final_state_xml_bytes"]
            for s in self.report["cases"] for c in s["cases"]))

    def test_23_kind_cannot_claim_original_author_success(self):
        self.assertIn("not original author task correctness",
                      self.report["unsupported_schema_or_complexity"][3])
        self.assertIn("paper",native.__doc__.lower())

    def test_24_native_scope_does_not_use_step_numbers(self):
        self.assertIn("STEP-label-independent",native.__doc__)
        self.assertIn("SET_FIELDS",Path(native.__file__).read_text("utf8"))

    def test_25_frozen_parent_report_not_mutated(self):
        self.assertEqual(earlier.file_hash(audit.PARENT),audit.PARENT_SHA)


class DynamicWindowFinalState066(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        row=next(r for r in earlier.public_45(earlier.AUTHOR,earlier.DATA)
                 if r["test_id"]=="geometry_test_13")
        cls.original=earlier.DATA/"ifc"/row["original_source_ifc_relpath"]
        cls.sha=row["original_ifc_sha256"]
        cls.original_model=xml.source(cls.original,cls.sha)
        cls.groups=xml.groups(cls.original_model)
        cls.guids=sorted(cls.groups)
        cls.full=xml.full_source_state(cls.original,cls.sha)
        cls.managed=xml.managed_source_state(cls.original,cls.sha)
        cls.first={p.GlobalId for p in cls.groups[cls.guids[0]]["members"]}
        cls.second={p.GlobalId for p in cls.groups[cls.guids[1]]["members"]}

    def edited(self,which="full",change=None):
        node=etree.fromstring(self.full if which=="full" else self.managed)
        rows=list(node[1]) if which=="full" else list(node)
        if change:
            change(node,rows)
        return etree.tostring(node,encoding="utf8",xml_declaration=True)

    def deleted(self,which="full"):
        def change(_,rows):
            for e in rows:
                if e.get("ifcGuid") in self.first:
                    e.set("present","false")
        return self.edited(which,change)

    def moved(self,which="full"):
        def change(_,rows):
            for e in rows:
                if e.get("ifcGuid") in self.first:
                    e.set("finalWorldMinXM",f"{float(e.get('finalWorldMinXM'))+.2:.6f}")
        return self.edited(which,change)

    def test_26_declarative_single_group_deletion_full(self):
        r=xml.parse_full_state(self.original,self.sha,self.deleted())
        self.assertEqual(r["kind"],"delete")

    def test_27_declarative_single_group_move_full(self):
        r=xml.parse_full_state(self.original,self.sha,self.moved())
        self.assertEqual(r["kind"],"move")
        self.assertEqual(r["world_m"],(.2,0.,0.))

    def test_28_deletion_managed_expands_byte_identically(self):
        full, state=xml.expand_managed_state(
            self.original,self.sha,self.deleted("managed"))
        self.assertEqual(full,self.deleted())
        self.assertEqual(state["kind"],"delete")

    def test_29_move_managed_expands_byte_identically(self):
        full, state=xml.expand_managed_state(
            self.original,self.sha,self.moved("managed"))
        self.assertEqual(full,self.moved())
        self.assertEqual(state["kind"],"move")

    def test_30_missing_managed_roster_member_rejected(self):
        def mutate(_,rows):
            rows[-1].getparent().remove(rows[-1])
        with self.assertRaises((xml.FinalWindow066Error,ValueError)):
            xml.expand_managed_state(self.original,self.sha,self.edited("managed",mutate))

    def test_31_partial_assembly_deletion_rejected(self):
        first_member=next(iter(self.first))
        def mutate(_,rows):
            next(x for x in rows if x.get("ifcGuid")==first_member).set("present","false")
        with self.assertRaises(xml.FinalWindow066Error):
            xml.parse_full_state(self.original,self.sha,self.edited(change=mutate))

    def test_32_partial_assembly_move_rejected(self):
        first_member=next(iter(self.first))
        def mutate(_,rows):
            x=next(x for x in rows if x.get("ifcGuid")==first_member)
            x.set("finalWorldMinXM",f"{float(x.get('finalWorldMinXM'))+.2:.6f}")
        with self.assertRaises(xml.FinalWindow066Error):
            xml.parse_full_state(self.original,self.sha,self.edited(change=mutate))

    def test_33_both_group_simultaneous_delete_rejected(self):
        def mutate(_,rows):
            for e in rows:e.set("present","false")
        with self.assertRaises(xml.FinalWindow066Error):
            xml.parse_full_state(self.original,self.sha,self.edited(change=mutate))

    def test_34_move_and_delete_mixed_rejected(self):
        def mutate(_,rows):
            for e in rows:
                if e.get("ifcGuid") in self.first:
                    e.set("finalWorldMinXM",f"{float(e.get('finalWorldMinXM'))+.2:.6f}")
                elif e.get("ifcGuid") in self.second:
                    e.set("present","false")
        with self.assertRaises(xml.FinalWindow066Error):
            xml.parse_full_state(self.original,self.sha,self.edited(change=mutate))

    def test_35_nested_command_tag_rejected(self):
        def mutate(_,rows):
            etree.SubElement(rows[0],xml.Q+"Move")
        with self.assertRaises(xml.FinalWindow066Error):
            xml.parse_full_state(self.original,self.sha,self.edited(change=mutate))

    def test_36_noncanonical_coordinate_rejected(self):
        def mutate(_,rows):
            rows[0].set("finalWorldMinXM","1.2")
        with self.assertRaises(xml.FinalWindow066Error):
            xml.parse_full_state(self.original,self.sha,self.edited(change=mutate))

    def test_37_mutated_opaque_source_rejected(self):
        def mutate(root,rows):
            root[0].set("sourceIFCSha256","0"*64)
        with self.assertRaises(xml.FinalWindow066Error):
            xml.parse_full_state(self.original,self.sha,self.edited(change=mutate))

    def test_38_stale_managed_original_SHA_rejected(self):
        def mutate(root,rows):root.set("originalIFCSha256","0"*64)
        with self.assertRaises(xml.FinalWindow066Error):
            xml.expand_managed_state(self.original,self.sha,
                                     self.edited("managed",mutate))

    def test_39_illegal_z_translation_rejected(self):
        def mutate(_,rows):
            for e in rows:
                if e.get("ifcGuid") in self.first:
                    e.set("finalWorldMinZM",f"{float(e.get('finalWorldMinZM'))+.2:.6f}")
        with self.assertRaises(xml.FinalWindow066Error):
            xml.parse_full_state(self.original,self.sha,self.edited(change=mutate))

    def test_40_over_one_metre_move_rejected(self):
        def mutate(_,rows):
            for e in rows:
                if e.get("ifcGuid") in self.first:
                    e.set("finalWorldMinXM",f"{float(e.get('finalWorldMinXM'))+1.5:.6f}")
        with self.assertRaises(xml.FinalWindow066Error):
            xml.parse_full_state(self.original,self.sha,self.edited(change=mutate))

    def test_41_missing_source_sha_rejected(self):
        with self.assertRaises(xml.FinalWindow066Error):
            xml.full_source_state(self.original,"0"*64)

    def test_42_XXE_document_rejected(self):
        dirty=(b"<!DOCTYPE BuildingState [<!ENTITY x SYSTEM "
               b"'file:///etc/passwd'>]>\n")
        with self.assertRaises(Exception):
            xml.parse_full_state(self.original,self.sha,dirty+self.moved())

    def test_43_modified_full_roster_order_rejected(self):
        def mutate(_,rows):
            parent=rows[0].getparent()
            parent.remove(rows[0])
            parent.append(rows[0])
        with self.assertRaises(xml.FinalWindow066Error):
            xml.parse_full_state(self.original,self.sha,self.edited(change=mutate))

    def test_44_unchanged_noop_full_state_rejected(self):
        with self.assertRaises(xml.FinalWindow066Error):
            xml.parse_full_state(self.original,self.sha,self.full)


if __name__=="__main__":
    unittest.main()
