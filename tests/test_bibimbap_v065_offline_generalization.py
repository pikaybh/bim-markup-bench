"""v0.65 original-source clusters, blind/rights firewall and cross-schema proof.

All native geometry tests use already-exposed original IFC2X3 and IFC4X3
files. Does not open any prospective source IFC or private grader.
Real pinned Linux Docker independently audited in frozen v0.65 JSON.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main
from unittest.mock import patch
import json
import uuid

import ifcopenshell
import ifcopenshell.api.root
from lxml import etree

from tools.bibimbap_matched25_tools import file_hash
from tools import audit_bibimbap_v065_offline_generalization as audit
from tools.bibimbap_v065_source_neutral_door import (
    Q,STATUS,_box_attrs,source_model,full_initial_xml,
    managed_initial_xml,parse_full_xml,expand_managed_xml,
    compile_hosted_door,post_native_ifc_gate,semantic_digest,
    NeutralDoor065Error,
)
from tools.bibimbap_v065_offline_trial_admission import (
    TrialBlocked065,proposal_manifest,deny_original_model_trial,
    deny_if_all_approvals_are_forged,
)


FROZEN_SHA="cc55f6623fc65d3936cf6ee9bbacf1c46d3893aa94122317632d9f90d009382d"


class BIBIMBAPOfflineGeneralization065(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(audit.REPORT.read_text("utf8"))
        cls.v058=json.loads(audit.FROZEN58.read_text("utf8"))
        cls.allrows={r["test_id"]:r for r in
                     audit.public_45(audit.AUTHOR,audit.DATA)}
        cls.rows={}
        for task in ("geometry_test_03","topological_test_05"):
            r=cls.allrows[task]
            p=audit.DATA/"ifc"/r["original_source_ifc_relpath"]
            f=source_model(p,r["original_ifc_sha256"])
            cls.rows[task]=(p,r["original_ifc_sha256"],f,
                            audit._case_fixture(f,f.schema))

    def setUp(self):
        self.temp=TemporaryDirectory(prefix="v065-source-neutral-")
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)

    def source(self,task="geometry_test_03"):
        return self.rows[task]

    def state_xml(self,task="geometry_test_03"):
        p,sha,f,st=self.source(task)
        init=full_initial_xml(p,sha)
        compact=managed_initial_xml(p,sha)
        return (p,sha,st,
                audit._final_xml(init,st),
                audit._final_xml(compact,st,managed=True))

    def native(self,task="geometry_test_03"):
        p,sha,st,full,_=self.state_xml(task)
        info=parse_full_xml(p,sha,full)
        output=self.path/(task+".ifc")
        compile_hosted_door(p,sha,info,output)
        return p,sha,output

    def invalid(self,raw,task="geometry_test_03",managed=False):
        p,sha,_,_,_=self.state_xml(task)
        payload=raw.encode("utf8") if isinstance(raw,str) else raw
        with self.assertRaises(Exception):
            if managed:expand_managed_xml(p,sha,payload)
            else:parse_full_xml(p,sha,payload)

    def test_01_exact_frozen_reproduced_report_SHA(self):
        self.assertEqual(file_hash(audit.REPORT),FROZEN_SHA)

    def test_02_report_canonical_JSON_bytes(self):
        self.assertEqual(audit.REPORT.read_bytes(),audit.canonical(self.report))

    def test_03_parent_v064_original_report_sha(self):
        self.assertEqual(file_hash(audit.PARENT64),audit.SHA64)

    def test_04_parent_v063_original_report_sha(self):
        self.assertEqual(file_hash(audit.PARENT63),audit.SHA63)

    def test_05_prospective_v058_six_original_sha(self):
        self.assertEqual(file_hash(audit.FROZEN58),audit.SHA58)

    def test_06_exact_original_45_public_task_population(self):
        self.assertEqual(self.report["original_public_edit_task_count"],45)

    def test_07_exact_31_original_IFC_source_sha_clusters(self):
        self.assertEqual(self.report["original_unique_source_sha_clusters"],31)

    def test_08_basic_15_tasks_share_one_source_sha(self):
        clusters=self.report["original_source_per_file_rights_ledger"]
        self.assertEqual(sum(c["source_task_count"] for c in clusters),45)
        self.assertEqual(sorted([c["source_task_count"] for c in clusters])[-1],15)

    def test_09_source_sha_cluster_task_partition_disjoint(self):
        clusters=self.report["original_source_per_file_rights_ledger"]
        tasks=[tid for c in clusters for tid in c["original_public_task_ids"]]
        self.assertEqual(len(tasks),len(set(tasks)))
        self.assertEqual(set(tasks),set(self.allrows))

    def test_10_distinct_original_source_sha_not_duplicate(self):
        cluster=self.report["original_source_per_file_rights_ledger"]
        self.assertEqual(len({c["original_source_ifc_SHA256"] for c in cluster}),31)

    def test_11_10_original_source_families_developer_exposed(self):
        self.assertEqual(self.report["actual_developer_exposed_source_clusters_count"],10)

    def test_12_all_six_former_untouched_now_exposed(self):
        self.assertTrue(self.report[
            "v058_former_prespecified_six_are_NOW_developer_exposed"])
        previous=set(self.v058["prospective_six_source_heldout_task_ids"])
        current=set(c for c in audit.CONFIRMED_EXPOSED)
        self.assertTrue(previous<=current)

    def test_13_previous_four_developer_exposed(self):
        self.assertTrue(audit.OLDER_VERIFIED<=audit.CONFIRMED_EXPOSED)

    def test_14_21_remaining_catalogued_NOT_certified_unseen(self):
        self.assertEqual(self.report[
            "source_clusters_catalogued_but_NOT_CERTIFIED_unseen"],21)

    def test_15_certified_confirmatory_unseen_ZERO(self):
        self.assertEqual(self.report[
            "certified_independent_unseen_confirmatory_clusters"],0)

    def test_16_all_31_source_file_rights_block_provider(self):
        for item in self.report["original_source_per_file_rights_ledger"]:
            self.assertFalse(item["per_original_IFC_license_proven"])
            self.assertFalse(item["external_model_provider_upload_rights_verified"])
            self.assertFalse(item["external_model_provider_retention_rights_verified"])
            self.assertEqual(item["source_external_provider_trial"],"BLOCKED")

    def test_17_no_source_individually_certified_blind(self):
        self.assertTrue(all(
            not row["unseen_source_confirmed_by_independent_fresh_auditor"]
            for row in self.report["original_source_per_file_rights_ledger"]))

    def test_18_provisional_candidate_selector_source_disjoint(self):
        selection=self.report["potential_new_quarantined_candidate_metadata_only"]
        shas=[x["source_ifc_SHA256"] for x in selection[
            "candidate_SHA_and_task_ids"]]
        self.assertEqual(len(shas),len(set(shas)))
        self.assertTrue(selection["source_family_cluster_disjoint"])

    def test_19_provisional_candidate_selector_not_an_admission(self):
        selection=self.report["potential_new_quarantined_candidate_metadata_only"]
        self.assertFalse(selection["candidate_task_scoring_or_provider_trial_admitted"])
        self.assertTrue(all(not s["independent_blind_certified"]
            for s in selection["candidate_SHA_and_task_ids"]))

    def test_20_provisional_candidates_are_not_developer_exposed(self):
        exposed={c["original_source_ifc_SHA256"] for c in
                 self.report["original_source_per_file_rights_ledger"]
                 if c["v065_updated_exposure_classification"]==
                    audit.EXPOSURE_LABEL}
        selected={c["source_ifc_SHA256"] for c in
                  self.report["potential_new_quarantined_candidate_metadata_only"][
                      "candidate_SHA_and_task_ids"]}
        self.assertFalse(exposed&selected)

    def test_21_candidate_selection_deterministic_from_metadata(self):
        clusters=self.report["original_source_per_file_rights_ledger"]
        self.assertEqual(audit.select_quarantined_metadata_candidates(clusters),
                         self.report["potential_new_quarantined_candidate_metadata_only"])

    def test_22_model_trial_manifest_NOT_preregistered(self):
        m=self.report["offline_non_registered_provider_trial_candidate_manifest"]
        self.assertEqual(m["status"],
                         "NOT_PREREGISTERED_NOT_APPROVED_UNCONDITIONAL_NO_LAUNCH")
        self.assertFalse(m["source_cluster_blind_exposure_auditor_approved"])

    def test_23_no_model_provider_snapshot_or_cap(self):
        m=self.report["offline_non_registered_provider_trial_candidate_manifest"]
        self.assertIsNone(m["model_provider"])
        self.assertIsNone(m["model_snapshot"])
        self.assertIsNone(m["approved_paid_USD_cap"])

    def test_24_no_billed_tokens_or_paid_calls(self):
        m=self.report["offline_non_registered_provider_trial_candidate_manifest"]
        self.assertIsNone(m["provider_actual_billable_input_tokens"])
        self.assertIsNone(m["provider_actual_billable_output_tokens"])
        self.assertEqual(self.report["paid_or_unpaid_model_generation_calls_count"],0)

    def test_25_forged_all_approvals_still_hard_blocked(self):
        with self.assertRaises(TrialBlocked065):
            deny_original_model_trial(
                rights=True,model="approved",
                max_budget=99999999,model_provider_upload=True,
                fake_user_consent=True)

    def test_26_fake_full_permissions_second_interface_hard_blocked(self):
        with self.assertRaises(TrialBlocked065):
            deny_if_all_approvals_are_forged(
                paid=True,source_original_IFC_rights=True,
                verified_model_snapshot=True)

    def test_27_zero_source_provider_uploads(self):
        self.assertEqual(self.report["original_IFC_provider_upload_count"],0)

    def test_28_original_author_checkout_PINNED_head(self):
        self.assertEqual(self.report[
            "original_repository_author_checkout_commit"],audit.AUTHOR_HEAD)

    def test_29_pinned_original_author_code_LICENSE_not_proven(self):
        self.assertFalse(self.report[
            "original_author_checkout_license_file_recognized"])

    def test_30_data_card_cc_by_label_not_individual_source_rights(self):
        self.assertEqual(self.report["dataset_card_license_label_only"],"cc-by-4.0")
        self.assertFalse(self.report[
            "source_original_IFC_per_file_license_chain_of_title_verified"])

    def test_31_original_published_official_scorer_parity_not_proven(self):
        self.assertFalse(self.report[
            "paper_official_scorer_vs_pinned_checkout_parity_VERIFIED"])

    def test_32_scorer_discrepancy_4_research_cases_recorded(self):
        caveats={x["task"]:x for x in
                 self.report["source_author_scorer_known_discrepancies"]}
        self.assertEqual(set(caveats),{
            "topological_test_05","topological_test_17",
            "geometry_test_03","geometry_test_19"})

    def test_33_author_exterior_error_per_previous_frozen_report(self):
        self.assertTrue(json.loads(audit.PARENT63.read_text("utf8"))[
            "original_author_score_equal_for_valid_exterior_and_invalid_interior"])

    def test_34_source_neutral_adapter_does_not_hardcode_task_ids(self):
        source=(audit.ROOT/"tools/bibimbap_v065_source_neutral_door.py").read_text("utf8")
        for forbidden in (
            "geometry_test_03","topological_test_05","geometry_test_19",
            "topological_test_17",
            "data.tests","original_author_repo_only","origin_target_guid"):
            self.assertNotIn(forbidden,source)

    def test_35_source_neutral_adapter_does_not_embed_specific_IFC_source_SHA(self):
        src=(audit.ROOT/"tools/bibimbap_v065_source_neutral_door.py").read_text("utf8")
        for _,sha,_,_ in self.rows.values():
            self.assertNotIn(sha,src)

    def test_36_source_neutral_support_both_actual_IFC_schemas(self):
        schemas={f.schema for _,_,f,_ in self.rows.values()}
        self.assertEqual(schemas,{"IFC2X3","IFC4X3"})

    def test_37_source_neutral_original_2_task_initial_full_xml_size(self):
        for task in self.rows:
            p,sha,_,_=self.rows[task]
            xml=full_initial_xml(p,sha)
            self.assertGreater(len(xml),1600)
            self.assertIn(b"sourceIFCSha256",xml)

    def test_38_original_source_2_task_managed_is_smaller(self):
        for task in self.rows:
            p,sha,_,_=self.rows[task]
            self.assertLess(len(managed_initial_xml(p,sha)),
                            len(full_initial_xml(p,sha)))

    def test_39_original_two_source_schema_in_XML(self):
        for task,(p,sha,m,_) in self.rows.items():
            doc=etree.fromstring(full_initial_xml(p,sha))
            self.assertEqual(doc.get("schema"),m.schema)

    def test_40_original_two_source_complete_wall_roster(self):
        for task,(p,sha,m,_) in self.rows.items():
            doc=etree.fromstring(full_initial_xml(p,sha))
            self.assertEqual(
                [node.get("guid") for node in doc[1]],
                sorted(w.GlobalId for w in m.by_type("IfcWall")))

    def test_41_managed_to_full_final_exact_byte_reconstruction(self):
        for task in self.rows:
            p,sha,st,full,compact=self.state_xml(task)
            from_managed,from_state=expand_managed_xml(p,sha,compact)
            self.assertEqual(from_managed,full)
            self.assertEqual(from_state,parse_full_xml(p,sha,full))

    def test_42_actual_real_IFC2X3_native_D_compiler_full_CSGBool(self):
        p,sha,out=self.native("geometry_test_03")
        verdict=post_native_ifc_gate(p,sha,out)
        self.assertEqual(verdict["status"],STATUS)
        self.assertEqual(verdict["original_ifc_schema"],"IFC2X3")
        self.assertEqual(verdict["actual_wall_csg_volume_removed_m3"],.418)

    def test_43_actual_real_IFC4X3_native_D_compiler_full_CSGBool(self):
        p,sha,out=self.native("topological_test_05")
        verdict=post_native_ifc_gate(p,sha,out)
        self.assertEqual(verdict["status"],STATUS)
        self.assertEqual(verdict["original_ifc_schema"],"IFC4X3")
        self.assertEqual(verdict["actual_wall_csg_volume_removed_m3"],.418)

    def test_44_exact_three_native_edit_paths_report_for_each_schema(self):
        for r in self.report[
            "source_neutral_developer_only_two_source_cross_schema_controls"]:
            self.assertTrue(r[
                "same_task_independent_source_neutral_D_Full_Managed_I_admitted"])
            self.assertTrue(r["real_pinned_linux_docker_general_python_run"])
            self.assertEqual(r["new_native_IFC2X3_IFC4X3_schema_errors"],0)

    def test_45_actual_two_local_pinned_Linux_Docker_runs(self):
        self.assertEqual(self.report[
            "source_neutral_real_original_IFC_edits_Docker_I"],2)
        self.assertEqual(len(self.report[
            "source_neutral_developer_only_two_source_cross_schema_controls"]),2)

    def test_46_actual_two_native_D_full_managed_each(self):
        self.assertEqual(self.report[
            "source_neutral_real_original_IFC_edits_D_full_managed"],4)

    def test_47_source_neutral_actual_zero_new_schema_findings(self):
        self.assertEqual(self.report[
            "source_neutral_actual_new_IFC2X3_IFC4X3_schema_errors"],0)

    def test_48_new_unrelated_Root_rejected_by_same_native_gate(self):
        p,sha,out=self.native()
        m=ifcopenshell.open(str(out))
        ifcopenshell.api.root.create_entity(m,ifc_class="IfcBuildingElementProxy")
        m.write(str(out))
        with self.assertRaises(NeutralDoor065Error):
            post_native_ifc_gate(p,sha,out)

    def test_49_modified_existing_source_Wall_rejected(self):
        p,sha,out=self.native()
        m=ifcopenshell.open(str(out))
        x=m.by_type("IfcWall")[0]
        x.Name="FORBIDDEN_ORIGINAL_SOURCE_CHANGE"
        m.write(str(out))
        with self.assertRaises(NeutralDoor065Error):
            post_native_ifc_gate(p,sha,out)

    def test_50_XXE_DTD_rejected_in_generic_full_state(self):
        p,sha,st,full,_=self.state_xml()
        dirty=b"<!DOCTYPE BuildingState [<!ENTITY e SYSTEM 'file:///etc/passwd'>]>"
        with self.assertRaises(Exception):
            parse_full_xml(p,sha,dirty+full)

    def test_51_missing_original_Wall_roster_row_rejected(self):
        p,sha,st,full,_=self.state_xml()
        doc=etree.fromstring(full)
        doc[1].remove(doc[1][0])
        self.invalid(etree.tostring(doc))

    def test_52_source_native_length_unit_tamper_rejected(self):
        p,sha,st,full,_=self.state_xml()
        doc=etree.fromstring(full)
        doc.set("nativeLengthUnitSI","1.000000")
        self.invalid(etree.tostring(doc))

    def test_53_compact_full_source_SHA_mutation_rejected(self):
        p,sha,st,_,compact=self.state_xml()
        doc=etree.fromstring(compact)
        doc.set("sourceFullBuildingStateSha256","f"*64)
        self.invalid(etree.tostring(doc),managed=True)

    def test_54_missing_fills_opening_guid_rejected(self):
        p,sha,st,full,_=self.state_xml()
        doc=etree.fromstring(full)
        doc[2][1].set("fillsOpeningGuid","0"*22)
        self.invalid(etree.tostring(doc))

    def test_55_duplicate_new_Door_Opening_Guid_rejected(self):
        p,sha,st,full,_=self.state_xml()
        doc=etree.fromstring(full)
        doc[2][1].set("guid",doc[2][0].get("guid"))
        self.invalid(etree.tostring(doc))

    def test_56_original_source_Guid_reused_by_new_Door_rejected(self):
        p,sha,st,full,_=self.state_xml()
        doc=etree.fromstring(full)
        doc[2][1].set("guid",st["host"])
        self.invalid(etree.tostring(doc))

    def test_57_opening_shallow_not_through_source_Wall_rejected(self):
        p,sha,st,full,_=self.state_xml()
        doc=etree.fromstring(full)
        doc[2][0].set("minYM","1.540000")
        doc[2][0].set("maxYM","1.630000")
        doc[2][1].set("minYM","1.555000")
        doc[2][1].set("maxYM","1.600000")
        self.invalid(etree.tostring(doc))

    def test_58_original_source_sha_mismatch_refused(self):
        p,sha,st,full,_=self.state_xml()
        with self.assertRaises(NeutralDoor065Error):
            source_model(p,"f"*64)

    def test_59_actual_IFC2X3_OwnerHistory_present(self):
        p,sha,out=self.native()
        f=ifcopenshell.open(str(out))
        self.assertTrue(all(x.OwnerHistory is not None
                            for x in f.by_type("IfcRoot")))

    def test_60_absent_original_lawful_rights_still_BLOCKED(self):
        self.assertFalse(self.report[
            "original_IFC_per_file_model_provider_upload_or_retention_authorized"])
        self.assertTrue(self.report[
            "hard_unconditional_no_provider_launcher_even_forged_all_true"])

    def test_61_no_test_workload_can_overwrite_frozen_report(self):
        with self.assertRaises(FileExistsError):
            with audit.REPORT.open("xb"):pass


if __name__=="__main__":
    main()
