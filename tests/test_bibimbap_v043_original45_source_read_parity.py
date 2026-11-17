"""v0.43 original 45/31 IFC vs real XML model read audit gates.

Negative source tampering, false parity and fabricated GUID coverage are
test failures. The original author evaluator/hidden GT are never imported.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from tools import audit_bibimbap_v043_original45_source_read_parity as audit
from tools.bibimbap_matched25_tools import XmlSourceEditSession,file_hash

BASE=Path(r"D:\\문서\\D__1_Projects\\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=audit.ROOT/"reports"/"bibimbap_v043_original45_native_XML_source_read_parity_20261117.json"
REPORT_SHA="eb05633d152b1ff15e4fdd888bb62924b31b126f6cddd05fb23e54fce3ef8dbf"
Q="{urn:bim-markup-bench:toy:v0}"


class Original45SourceReadParity043(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(REPORT.read_text(encoding="utf8"))
        cls.tasks={r["original_public_task_id"]:r for r in cls.data["original_45_task_rows"]}
        cls.sources={r["native_original_ifc_file_sha256"]:r for r in cls.data["original_31_unique_native_source_rows"]}
        cls.cohort=audit.original_population(AUTHOR,DATA)
        cls.testcase=next(x for x in cls.cohort if x["test_id"]=="topological_test_02")
        cls.source=DATA/"ifc"/cls.testcase["original_source_ifc_relpath"]
        _,cls.native=audit.source_native_summary(
            cls.source,cls.testcase["original_ifc_sha256"])
        cls.temporary=TemporaryDirectory(prefix="v043-negative-read-parity-")
        cls.session=XmlSourceEditSession(
            cls.source,Path(cls.temporary.name)/"probe",
            experimental_original_native_slab_v042=True)
        cls.actual_read=cls.session.call("read_building_xml",{})
        assert cls.actual_read["status"]=="ok"

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.temporary=TemporaryDirectory(prefix="v043-negative-signed-")
        self.addCleanup(self.temporary.cleanup)
        self.dir=Path(self.temporary.name)

    def test_01_frozen_report_SHA_immutable(self):
        self.assertEqual(file_hash(REPORT),REPORT_SHA)

    def test_02_prior_v042_report_sha_immutable(self):
        self.assertEqual(file_hash(audit.ROOT/audit.PARENT_REPORT[0]),
                         audit.PARENT_REPORT[1])

    def test_03_original_author_and_dataset_heads_exact(self):
        self.assertEqual(audit._head(AUTHOR),audit.AUTHOR_SHA)
        self.assertEqual(audit._head(DATA),audit.DATA_SHA)
        self.assertTrue(audit._git_clean(AUTHOR))
        self.assertTrue(audit._git_clean(DATA))

    def test_04_original_question_csv_pinned(self):
        self.assertEqual(file_hash(DATA/"prompts/all_questions.csv"),
                         audit.QUESTION_CSV_SHA)

    def test_05_original_population_45_ITT(self):
        self.assertEqual(len(self.cohort),45)
        self.assertEqual(Counter(x["crud"] for x in self.cohort),
                         {"create":15,"update":15,"delete":15})

    def test_06_15_by_each_original_category(self):
        self.assertEqual(Counter(x["category"] for x in self.cohort),
                         {"basic":15,"geometry":15,"topological":15})

    def test_07_exact_31_original_distinct_IFC_source_SHAs(self):
        self.assertEqual(len({x["original_ifc_sha256"] for x in self.cohort}),31)
        self.assertEqual(len(self.data["original_31_unique_native_source_rows"]),31)

    def test_08_all_45_original_source_SHA_and_question_SHA_pinned(self):
        for t in self.cohort:
            r=self.tasks[t["test_id"]]
            self.assertEqual(r["original_public_question_sha256"],
                             t["public_question_sha256"])
            self.assertEqual(r["original_public_ifc_source_sha256"],
                             t["original_ifc_sha256"])
            self.assertEqual(file_hash(DATA/"ifc"/t["original_source_ifc_relpath"]),
                             t["original_ifc_sha256"])

    def test_09_pinned_45_task_no_duplicates(self):
        self.assertEqual(len(self.tasks),45)

    def test_10_original_31_IFC_schemas_are_only_original_IFC_versions(self):
        counts=Counter(x["schema"] for x in self.sources.values())
        self.assertEqual(sum(counts.values()),31)
        self.assertEqual(set(counts),{"IFC2X3","IFC4","IFC4X3"})

    def test_11_native_source_units_all_millimetres(self):
        for source in self.sources.values():
            self.assertAlmostEqual(source["unit_to_metres"],.001)

    def test_12_native_31_source_ifc_products_480(self):
        self.assertEqual(self.data[
            "source_native_products_instances_across_31_unique_source_files"],480)

    def test_13_native_31_source_ifc_relationships_1949(self):
        self.assertEqual(self.data[
            "source_native_ifc_relationship_instances_across_31_unique_source_files"],1949)

    def test_14_native_31_source_property_links_1227(self):
        self.assertEqual(self.data[
            "source_native_property_association_instances_across_unique_files"],1227)

    def test_15_native_31_source_material_associations_153(self):
        self.assertEqual(self.data[
            "source_native_material_association_instances_across_unique_files"],153)

    def test_16_actual_default_reader_exact_36_and_9_not_model_failures(self):
        self.assertEqual(
            self.data["original45_default_XML_model_read_status_counts"],
            {"ACTUAL_MODEL_TOOL_XML_READ_OK":36,
             "UNSUPPORTED_BACKEND_NOT_MODEL_FAILURE":9})

    def test_17_research_selected_actual_reader_exact_41_and_4(self):
        self.assertEqual(
            self.data["original45_research_feature_flag_XML_read_status_counts"],
            {"ACTUAL_MODEL_TOOL_XML_READ_OK":41,
             "UNSUPPORTED_BACKEND_NOT_MODEL_FAILURE":4})

    def test_18_original_four_unsupported_after_research_optins_are_real(self):
        invalid={k for k,v in self.tasks.items()
                 if v["best_research_model_read_status"]!="ACTUAL_MODEL_TOOL_XML_READ_OK"}
        self.assertEqual(invalid,{
            "geometry_test_14","geometry_test_15",
            "topological_test_11","topological_test_17"})

    def test_19_31_unique_source_read_27_plus_4(self):
        rows=[next((v for k,v in source["actual_model_facing_source_variants"].items()
                    if k!="default"),source["actual_model_facing_source_variants"]["default"])
              for source in self.sources.values()]
        self.assertEqual(Counter(x["status"] for x in rows),{
            "ACTUAL_MODEL_TOOL_XML_READ_OK":27,
            "UNSUPPORTED_BACKEND_NOT_MODEL_FAILURE":4,
        })

    def test_20_missing_1743_of_1757_original_relation_GUIDs_from_XML(self):
        missing,total=0,0
        for source in self.sources.values():
            r=next((v for k,v in source["actual_model_facing_source_variants"].items()
                    if k!="default"),source["actual_model_facing_source_variants"]["default"])
            if r["status"]=="ACTUAL_MODEL_TOOL_XML_READ_OK":
                missing+=r["source_native_ifc_relationship_guid_unseen_count"]
                total+=source["native_ifc_relationship_count"]
        self.assertEqual((missing,total),(1743,1757))

    def test_21_missing_121_of_433_native_IfcProducts_from_XML(self):
        missing,total=0,0
        for source in self.sources.values():
            r=next((v for k,v in source["actual_model_facing_source_variants"].items()
                    if k!="default"),source["actual_model_facing_source_variants"]["default"])
            if r["status"]=="ACTUAL_MODEL_TOOL_XML_READ_OK":
                missing+=r["source_native_ifc_product_guid_unseen_count"]
                total+=source["native_ifc_products_count"]
        self.assertEqual((missing,total),(121,433))

    def test_22_all_27_readable_original_IFCs_missing_property_names(self):
        for source in self.sources.values():
            r=next((v for k,v in source["actual_model_facing_source_variants"].items()
                    if k!="default"),source["actual_model_facing_source_variants"]["default"])
            if r["status"]=="ACTUAL_MODEL_TOOL_XML_READ_OK":
                self.assertGreater(source["native_ifc_ifc_property_set_count"],0)
                self.assertEqual(
                    r["original_native_IFC_property_set_names_visible_by_exact_text_count"],0)
                self.assertFalse(r["xml_has_dedicated_native_property_tags"])

    def test_23_all_27_readable_original_IFCs_missing_material_names(self):
        for source in self.sources.values():
            r=next((v for k,v in source["actual_model_facing_source_variants"].items()
                    if k!="default"),source["actual_model_facing_source_variants"]["default"])
            if r["status"]=="ACTUAL_MODEL_TOOL_XML_READ_OK":
                self.assertGreater(source["native_ifc_material_count"],0)
                self.assertEqual(
                    r["original_native_IFC_material_names_visible_by_exact_text_count"],0)
                self.assertFalse(r["xml_has_dedicated_native_material_tags"])

    def test_24_27_actual_read_ok_have_demonstrated_gap(self):
        self.assertTrue(all(r["demonstrated_missing_read_information"]
            for source in self.sources.values()
            for r in source["actual_model_facing_source_variants"].values()
            if r["status"]=="ACTUAL_MODEL_TOOL_XML_READ_OK"))

    def test_25_no_original45_complete_equal_source_read(self):
        self.assertEqual(self.data[
            "original45_fully_proven_equal_IFC_source_read_information_tasks"],0)

    def test_26_no_original45_complete_equal_native_write(self):
        self.assertEqual(self.data[
            "original45_fully_proven_equal_IFC_native_write_authority_tasks"],0)

    def test_27_5_out_of_15_previous_developer_pair_not_fake_claim(self):
        self.assertEqual(self.data[
            "original_CREATE_task_specific_developer_D0_I0_pairs_previously"],5)
        self.assertEqual(self.data[
            "original_CREATE_task_specific_developer_D0_I0_pairs_added_by_v043"],0)

    def test_28_no_hidden_author_grader_model_Docker_runs(self):
        self.assertEqual(self.data["original_author_evaluator_invocations"],0)
        self.assertEqual(self.data["original_LLM_matched_XML_vs_Python_trials"],0)
        self.assertEqual(self.data["paid_provider_calls"],0)
        self.assertEqual(self.data["Docker_executions"],0)

    def test_29_actual_model_read_tool_has_full_xml_and_no_native_candidate(self):
        r=self.actual_read
        self.assertEqual(r["status"],"ok")
        self.assertFalse(r["native_candidate_available"])
        self.assertEqual(r["xml"],self.session.original_xml.decode("utf8"))
        self.assertEqual({x["name"] for x in self.session.tools},
                         {"read_building_xml","submit_building_xml"})

    def test_30_actual_ifc_source_independent_guid_inventory(self):
        n=self.native
        self.assertEqual(len(n["product_guids"]),10)
        self.assertEqual(len(n["relationship_guids"]),45)
        self.assertEqual(len(n["native_ifc_ifc_slab_guids"]),2)

    def test_31_source_derived_xml_exact_relation_guids_not_all_present(self):
        r=audit.model_visible_summary(self.session.original_xml,
                                      self.native,required_xml_read=True)
        self.assertEqual(r["source_native_ifc_product_guid_seen_count"],8)
        self.assertEqual(r["source_native_ifc_relationship_guid_seen_count"],2)
        self.assertEqual(r["source_native_ifc_relationship_guid_unseen_count"],43)

    def test_32_actual_v042_original_hidden_slab_guids_are_visible_but_readonly(self):
        read=etree.fromstring(self.session.original_xml)
        slabs=read.find(Q+"OriginalNativeSlabEvidence").find(Q+"NativeSlabs")
        self.assertEqual(len(slabs),2)
        self.assertEqual({x.get("ifcGuid") for x in slabs},
                         set(self.native["native_ifc_ifc_slab_guids"]))
        self.assertTrue(all(x.get("compilerEditPermission")=="NONE_READ_ONLY"
                            for x in slabs))

    def test_33_original_source_material_attributes_cannot_be_inferred_from_GUID(self):
        r=audit.model_visible_summary(
            self.session.original_xml,self.native,required_xml_read=True)
        self.assertFalse(r["source_identity_visibility_alone_is_full_IFC_information_parity"])
        self.assertFalse(r["full_original_native_IFC_source_information_parity_confirmed"])
        self.assertFalse(r["xml_has_dedicated_native_material_tags"])

    def test_34_independent_native_placement_and_representation_metadata(self):
        source=self.sources[self.testcase["original_ifc_sha256"]]
        self.assertEqual(source["native_ifc_local_placement_count"],10)
        self.assertGreater(source[
            "native_ifc_products_with_geometric_representation_count"],0)

    def test_35_default_public_runner_does_not_enable_explicit_research_optins(self):
        self.assertFalse(self.data[
            "default_model_run_one_pair_auto_enables_experimental_optin"])
        self.assertFalse(self.data[
            "original_native_source_and_grader_mutations"])

    def test_36_original_question_csv_sha_poisoning_refused(self):
        with patch.object(audit,"QUESTION_CSV_SHA","f"*64):
            with self.assertRaisesRegex(audit.ParityAuditError,
                                        "question CSV SHA"):
                audit.original_population(AUTHOR,DATA)

    def test_37_dirty_original_data_refused(self):
        with patch.object(audit,"_git_clean",return_value=False):
            with self.assertRaisesRegex(audit.ParityAuditError,"dirty"):
                audit.original_population(AUTHOR,DATA)

    def test_38_duplicate_original_task_id_refused(self):
        fake=[dict(x) for x in self.cohort]
        fake[0]["test_id"]=fake[1]["test_id"]
        with patch.object(audit,"public_45",return_value=fake):
            with self.assertRaisesRegex(audit.ParityAuditError,
                                        "45/15 ITT"):
                audit.original_population(AUTHOR,DATA)

    def test_39_original_source_path_traversal_refused(self):
        fake=[dict(x) for x in self.cohort]
        fake[0]["original_source_ifc_relpath"]="../../prompts/all_questions.csv"
        with patch.object(audit,"public_45",return_value=fake):
            with self.assertRaisesRegex(audit.ParityAuditError,
                                        "immutable path/file"):
                audit.original_population(AUTHOR,DATA)

    def test_40_modified_original_native_IFC_source_bytes_refused(self):
        changed=ifcopenshell.open(str(self.source))
        changed.by_type("IfcBuilding")[0].Name="POISON_NATIVE_SOURCE"
        path=self.dir/"source.ifc"
        changed.write(str(path))
        with self.assertRaisesRegex(audit.ParityAuditError,"(?i)source.*IFC bytes"):
            audit.source_native_summary(
                path,self.testcase["original_ifc_sha256"])

    def test_41_wrong_native_IFC_unit_refused(self):
        f=ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(self.source)),"METER")
        p=self.dir/"native-metres.ifc"
        f.write(str(p))
        with self.assertRaisesRegex(audit.ParityAuditError,
                                    "native-mm units"):
            audit.source_native_summary(p,file_hash(p))

    def test_42_fabricated_source_product_GUID_rejected(self):
        root=etree.fromstring(self.session.original_xml)
        root.find(Q+"Elements")[0].set("ifcGuid","0"*22)
        with self.assertRaisesRegex(audit.ParityAuditError,
                                    "invented or unpinned"):
            audit.model_visible_summary(
                etree.tostring(root),self.native,required_xml_read=True)

    def test_43_fabricated_source_relation_GUID_rejected(self):
        root=etree.fromstring(self.session.original_xml)
        root.find(Q+"OriginalNativeSlabEvidence").find(
            Q+"OriginalExplicitSlabRelations")[0].set("relationGuid","0"*22)
        with self.assertRaisesRegex(audit.ParityAuditError,
                                    "invented or unpinned"):
            audit.model_visible_summary(
                etree.tostring(root),self.native,required_xml_read=True)

    def test_44_unsupported_XML_source_cannot_be_reported_as_success(self):
        nonpin=next(x for x in self.cohort if x["test_id"]=="geometry_test_14")
        p=DATA/"ifc"/nonpin["original_source_ifc_relpath"]
        _,n=audit.source_native_summary(p,nonpin["original_ifc_sha256"])
        result=audit.audit_model_read(p,nonpin["original_ifc_sha256"],n,
                                      self.dir/"unsupported")
        self.assertEqual(result["status"],"UNSUPPORTED_BACKEND_NOT_MODEL_FAILURE")
        self.assertFalse(result["model_tool_xml_read_available"])
        self.assertFalse(result["full_original_native_IFC_source_information_parity_confirmed"])

    def test_45_read_source_has_no_original_task_answer_or_scores(self):
        self.assertNotIn("public_question",self.data["original_45_task_rows"][0])
        self.assertTrue(self.data["no_hidden_gt_or_original_task_answers_exposed"])
        # A negative-control declaration contains the literal `task_answers`
        # as part of its NAME; only a leaked original answer VALUE is forbidden.
        report_text=REPORT.read_text(encoding="utf8")
        self.assertNotIn('"public_question":',report_text)
        self.assertNotIn('"task_answer":',report_text)

    def test_46_native_45_research_optin_selection_matches_exact_source_sha(self):
        for task in self.cohort:
            f=audit.optin_for_source(
                task["test_id"],task["original_ifc_sha256"],task["crud"])
            if f:
                self.assertEqual(task["crud"],"create")
                self.assertEqual(len(f),1)
        self.assertEqual(audit.optin_for_source(
            "topological_test_02",self.testcase["original_ifc_sha256"],
            "create"),{"experimental_original_native_slab_v042":True})

    def test_47_trying_false_full_parity_from_XML_GUID_is_refuted(self):
        r=audit.model_visible_summary(
            self.session.original_xml,self.native,required_xml_read=True)
        self.assertGreater(r["source_native_ifc_product_guid_seen_count"],0)
        self.assertGreater(r["source_native_ifc_relationship_guid_unseen_count"],0)
        self.assertTrue(r["demonstrated_missing_read_information"])
        self.assertFalse(r["native_ifc_existing_objects_editable_via_XML_safely_parity_proven"])

    def test_48_report_includes_all_31_unique_source_sha256_and_45_question_sha(self):
        self.assertEqual(set(self.sources),{
            x["original_ifc_sha256"] for x in self.cohort})
        self.assertEqual({
            (x["original_public_task_id"],x["original_public_question_sha256"])
            for x in self.data["original_45_task_rows"]},{
            (x["test_id"],x["public_question_sha256"]) for x in self.cohort})

    def test_49_frozen_report_refuses_overwrite(self):
        with self.assertRaises(FileExistsError):
            with REPORT.open("xb") as f:f.write(b"FALSE")
        self.assertEqual(file_hash(REPORT),REPORT_SHA)

    def test_50_original_45_source_live_audit_replay_byte_identical(self):
        report=audit.audit(AUTHOR,DATA)
        raw=(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf8")
        self.assertEqual(sha256(raw).hexdigest(),REPORT_SHA)
        self.assertEqual(raw,REPORT.read_bytes())

    def test_51_native_root_relation_type_samples_not_fabricated(self):
        source=self.sources[self.testcase["original_ifc_sha256"]]
        counts=source["native_relationship_class_counts"]
        self.assertGreater(counts["IfcRelDefinesByProperties"],0)
        self.assertGreater(counts["IfcRelAssociatesMaterial"],0)
        self.assertGreater(counts["IfcRelContainedInSpatialStructure"],0)

    def test_52_distinct_original_baseline_default_and_research_variant(self):
        source=self.sources[self.testcase["original_ifc_sha256"]]
        variants=source["actual_model_facing_source_variants"]
        self.assertEqual(set(variants),{
            "default","experimental_original_native_slab_v042"})
        self.assertEqual(variants["default"]["status"],"ACTUAL_MODEL_TOOL_XML_READ_OK")
        self.assertEqual(variants["experimental_original_native_slab_v042"]["status"],
                         "ACTUAL_MODEL_TOOL_XML_READ_OK")
        self.assertGreater(variants["experimental_original_native_slab_v042"][
            "source_native_ifc_product_guid_seen_count"],
            variants["default"]["source_native_ifc_product_guid_seen_count"])

    def test_53_no_implicit_ifc_write_or_evaluator_attempted_by_readonly_audit(self):
        self.assertEqual(self.session.submissions,0)
        self.assertIsNone(self.session.output_ifc)
        self.assertTrue(self.data["native_product_GUID_visibility_does_not_imply_all_metadata_geometry_parity"])


if __name__=="__main__":
    unittest.main()
