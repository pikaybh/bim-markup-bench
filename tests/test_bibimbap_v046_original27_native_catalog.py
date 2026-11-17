"""v0.46 independent original27 complete native IFC catalog/page positive+negative.

No author grader/hidden GT/paid provider/Docker. Original input 45/31 source
population unchanged; huge original IFC STEP contents are PAGED, not truncated.
Every proof uses a genuine model-facing tool request and independent source
IFC oracle (no import from the v0.46 projector in the independent oracle).
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell
from lxml import etree

from tools import audit_bibimbap_v046_original27_native_catalog as audit
from tools.audit_bibimbap_v043_original45_source_read_parity import (
    original_population)
from tools.bibimbap_matched25_tools import XmlSourceEditSession,UnsupportedArm,file_hash
from tools.bibimbap_v046_independent_native_catalog_oracle import (
    verify_native_catalog_046,IndependentOriginalCatalog046Error,
    original_27_sources)
from src.runtime.experimental_v46_original_native_catalog import (
    source_profiles,CATALOGS,PAGE_SIZE,SCHEMA_XSD,NativeCatalog046Error)

BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=audit.ROOT/"reports"/"bibimbap_v046_original27_all_native_IFC_paged_source_catalog_20261117.json"
REPORT_SHA="beab50998c1f2f984342cf784fe910adc384752a16b8f0eed40623421c38509f"
N="{urn:bim-markup-bench:toy:v0}"


class Original27AllNativeSourcePages046(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))
        cls.cohort=original_population(AUTHOR,DATA)
        cls.source_by_id={x["test_id"]:DATA/"ifc"/x["original_source_ifc_relpath"]
                          for x in cls.cohort}
        cls.task={x["test_id"]:x for x in cls.cohort}
        cls.source_rows={x["source_original_public_IFC_sha256"]:x
                         for x in cls.report["original_27_unique_source_results"]}
        cls.tmp=TemporaryDirectory(prefix="v046-source27-negative-gates-")
        cls.sessions={}
        cls.manifests={}
        cls.pages={}
        for idx,tid in enumerate(("geometry_test_03","geometry_test_05",
                                  "geometry_test_16")):
            p=cls.source_by_id[tid]
            s=XmlSourceEditSession(p,Path(cls.tmp.name)/str(idx),
                experimental_original_native_catalog_v046=True)
            cls.sessions[tid]=s
            cls.manifests[tid]=s.call("read_building_xml",{})["xml"].encode("utf8")
            if tid=="geometry_test_03":
                cls.pages[tid]={
                    k:[s.call("read_native_ifc_page",{"catalog":k,"page":i})["xml"].encode("utf8")
                       for i in range((len(v)+PAGE_SIZE-1)//PAGE_SIZE)]
                    for k,v in s.native_catalog_v046.catalog.items()
                }

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.tmp_sub=TemporaryDirectory(prefix="v046-poison-source27-")
        self.addCleanup(self.tmp_sub.cleanup)
        self.work=Path(self.tmp_sub.name)

    def _modified_page(self,catalog,changer,*,page=0,tid="geometry_test_03"):
        pages={name:list(raws) for name,raws in self.pages["geometry_test_03"].items()}
        node=etree.fromstring(pages[catalog][page])
        changer(node)
        pages[catalog][page]=etree.tostring(node,encoding="utf8")
        with self.assertRaises(IndependentOriginalCatalog046Error):
            verify_native_catalog_046(
                self.source_by_id["geometry_test_03"],
                self.task["geometry_test_03"]["original_ifc_sha256"],
                self.manifests["geometry_test_03"],pages)

    def _modified_manifest(self,changer):
        node=etree.fromstring(self.manifests["geometry_test_03"])
        changer(node)
        with self.assertRaises(IndependentOriginalCatalog046Error):
            verify_native_catalog_046(
                self.source_by_id["geometry_test_03"],
                self.task["geometry_test_03"]["original_ifc_sha256"],
                etree.tostring(node),self.pages["geometry_test_03"])

    def test_01_new_v046_frozen_report_sha(self):
        self.assertEqual(file_hash(REPORT),REPORT_SHA)

    def test_02_original_v045_frozen_report_unchanged(self):
        self.assertEqual(file_hash(audit.ROOT/audit.PARENT_REPORT),
                         audit.PARENT_REPORT_SHA)

    def test_03_original_v043_native_parity_report_unchanged(self):
        self.assertEqual(file_hash(audit.ROOT/audit.OLD_REPORT),audit.OLD_SHA)

    def test_04_original_author_data_pinned_original45(self):
        self.assertEqual(len(self.cohort),45)
        self.assertEqual(Counter(t["crud"] for t in self.cohort),
                         {"create":15,"update":15,"delete":15})

    def test_05_original_31_distinct_IFC_sha(self):
        self.assertEqual(len({t["original_ifc_sha256"] for t in self.cohort}),31)

    def test_06_original_27_exact_sha_are_from_frozen45(self):
        self.assertEqual(len(source_profiles()),27)
        self.assertEqual(set(source_profiles()),set(original_27_sources()))
        self.assertEqual(set(source_profiles()),set(self.source_rows))

    def test_07_prior_exact_four_source_excluded(self):
        from src.runtime.experimental_v44_original_native_step_readonly import PINS
        self.assertEqual(len(PINS),4)
        self.assertTrue(set(PINS).isdisjoint(source_profiles()))

    def test_08_source27_reused_by_41_of_original45_tasks(self):
        self.assertEqual(sum(t["original_ifc_sha256"] in source_profiles()
                             for t in self.cohort),41)

    def test_09_original_task_question_sha_provenance_preserved_45(self):
        frozen={t["original_public_task_id"]:t for t in
                self.report["original_45_per_task_provenance"]}
        self.assertEqual(len(frozen),45)
        for item in self.cohort:
            x=frozen[item["test_id"]]
            self.assertEqual(x["original_public_question_sha256"],
                             item["public_question_sha256"])
            self.assertEqual(x["original_source_ifc_sha256"],
                             item["original_ifc_sha256"])

    def test_10_three_source_native_IFC_schema_variants_real(self):
        self.assertEqual({x["schema"] for x in source_profiles().values()},
                         {"IFC2X3","IFC4","IFC4X3"})

    def test_11_original27_source_file_hashes_remain_immutable(self):
        for item in self.cohort:
            self.assertEqual(file_hash(
                DATA/"ifc"/item["original_source_ifc_relpath"]),
                item["original_ifc_sha256"])

    def test_12_model_facing_source_catalog_has_three_real_tools(self):
        for s in self.sessions.values():
            self.assertEqual({x["name"] for x in s.tools},
                             {"read_building_xml","read_native_ifc_page","submit_building_xml"})

    def test_13_initial_manifest_all_eight_catalogs(self):
        for raw in self.manifests.values():
            doc=etree.fromstring(raw)
            self.assertEqual(doc.tag,N+"Building")
            self.assertEqual([r.get("name") for r in doc[0]],list(CATALOGS))

    def test_14_initial_model_facing_manifest_is_small(self):
        for raw in self.manifests.values():
            self.assertLess(len(raw),300000)
            self.assertIn(b"NONE_READ_ONLY",raw)

    def test_15_page_size_16_and_manifest_counts_match_source(self):
        for s in self.sessions.values():
            for k,rows in s.native_catalog_v046.catalog.items():
                response=s.call("read_building_xml",{})
                doc=etree.fromstring(response["xml"].encode("utf8"))
                m=next(x for x in doc[0] if x.get("name")==k)
                self.assertEqual(int(m.get("recordCount")),len(rows))
                self.assertEqual(int(m.get("pageSize")),16)
                self.assertEqual(int(m.get("pageCount")),(len(rows)+15)//16)

    def test_16_three_representative_originals_use_native_mm_units(self):
        for tid,p in ((k,self.source_by_id[k]) for k in self.sessions):
            self.assertAlmostEqual(
                ifcopenshell.util.unit.calculate_unit_scale(ifcopenshell.open(str(p))),
                .001)

    def test_17_all_27_independent_source_oracles_pass(self):
        self.assertTrue(all(x[
            "all_8_original_source_catalogs_fully_validated_independently"]
            for x in self.report["original_27_unique_source_results"]))

    def test_18_all_27_actual_model_source_page_calls_executed(self):
        self.assertEqual(self.report["total_actual_model_facing_original_IFC_page_reads"],2037)

    def test_19_report_exact_original27_step_entity_coverage(self):
        self.assertGreater(self.report["totals_across_27_unique_original_sources"][
            "full_source_step_literal_original_line_count"],20000)

    def test_20_original27_root_GUIDs_all_reachable(self):
        data=self.report["totals_across_27_unique_original_sources"]
        self.assertGreater(data["original_native_root_GUIDs"],1000)
        self.assertGreater(data["original_native_relation_GUIDs_endpoint_lists"],1500)

    def test_21_original27_material_names_all_reachable(self):
        self.assertGreater(self.report["totals_across_27_unique_original_sources"][
            "original_native_materials_original_names"],0)

    def test_22_original27_property_values_all_reachable(self):
        self.assertGreater(self.report["totals_across_27_unique_original_sources"][
            "original_native_property_sets_named_values"],0)

    def test_23_original27_native_local_placement_matrices_all_reachable(self):
        self.assertGreater(self.report["totals_across_27_unique_original_sources"][
            "original_native_local_placement_matrices"],0)

    def test_24_original27_physical_geometry_digests_or_explicit_status(self):
        data=self.report["totals_across_27_unique_original_sources"]
        self.assertEqual(
            data["original_native_product_geometry_digests_or_explicit_unavailable"],
            data["original_native_products_with_computed_physical_world_mesh"]+
            data["original_native_products_with_explicit_unavailable_world_geometry"]+
            data["original_native_products_without_original_representation"])

    def test_25_actual_model_tool_pages_never_exceed_300KB(self):
        self.assertLess(self.report["source_paged_model_tool_max_result_size_bytes"],
                        300000)

    def test_26_large_geometry16_original_STEP_8304_reachable(self):
        t=self.task["geometry_test_16"]
        row=self.source_rows[t["original_ifc_sha256"]]
        self.assertEqual(row["independent_oracle"][
            "full_source_step_literal_original_line_count"],8304)

    def test_27_large_geometry16_original_STEP_519_paged_calls(self):
        s=self.sessions["geometry_test_16"]
        self.assertEqual(
            (len(s.native_catalog_v046.catalog["step"])+15)//16,519)

    def test_28_large_geometry16_last_original_STEP_page_retrievable(self):
        s=self.sessions["geometry_test_16"]
        response=s.call("read_native_ifc_page",{"catalog":"step","page":518})
        self.assertEqual(response["status"],"ok")
        self.assertLess(len(response["xml"]),300000)

    def test_29_native_original_literal_STEP_records_accessible_not_just_hashes(self):
        for tid,s in self.sessions.items():
            r=s.call("read_native_ifc_page",{"catalog":"step","page":0})
            node=etree.fromstring(r["xml"].encode("utf8"))
            self.assertTrue(all(x[-1].tag==N+"LiteralStepText" for x in node))
            self.assertTrue(all(x[-1].text.startswith("#") for x in node))

    def test_30_original_27_source_pages_all_independent_sample_oracle(self):
        tid="geometry_test_03"
        oracle=verify_native_catalog_046(
            self.source_by_id[tid],self.task[tid]["original_ifc_sha256"],
            self.manifests[tid],self.pages[tid])
        self.assertEqual(oracle["status"],
            "V046_INDEPENDENT_ORIGINAL27_FULL_PAGED_NATIVE_SOURCE_ORACLE_PASS")

    def test_31_readonly_mode_creates_no_normalized_IFC(self):
        for s in self.sessions.values():
            self.assertIsNone(s.normalized)
            self.assertIsNone(s.output_ifc)
            self.assertFalse(list(s.folder.rglob("*.ifc")))

    def test_32_model_tool_declares_natively_readonly(self):
        for s in self.sessions.values():
            submit=next(x for x in s.tools if x["name"]=="submit_building_xml")
            self.assertIn("UNSUPPORTED",submit["description"])
            self.assertIn("READ ONLY",submit["description"])

    def test_33_actual_native_edit_submission_fails_closed_on_original_metadata(self):
        s=self.sessions["geometry_test_03"]
        before=s.current_xml
        result=s.call("submit_building_xml",{"xml_text":before.decode("utf8")})
        self.assertEqual(result["status"],"error")
        self.assertEqual(result["error_type"],"UnsupportedArm")
        self.assertTrue(result["last_valid_xml_preserved"])
        self.assertFalse(result["native_ifc_committed"])
        self.assertEqual(s.current_xml,before)
        self.assertIsNone(s.output_ifc)

    def test_34_after_rejected_edit_manifest_still_immutable(self):
        s=self.sessions["geometry_test_03"]
        result=s.call("read_building_xml",{})
        self.assertEqual(result["xml"].encode("utf8"),self.manifests["geometry_test_03"])

    def test_35_model_page_unknown_catalog_rejected(self):
        s=self.sessions["geometry_test_03"]
        r=s.call("read_native_ifc_page",{"catalog":"secret","page":0})
        self.assertEqual(r["status"],"error")

    def test_36_model_page_negative_index_rejected(self):
        s=self.sessions["geometry_test_03"]
        self.assertEqual(s.call("read_native_ifc_page",{
            "catalog":"step","page":-1})["status"],"error")

    def test_37_model_page_string_index_rejected(self):
        s=self.sessions["geometry_test_03"]
        self.assertEqual(s.call("read_native_ifc_page",{
            "catalog":"step","page":"0"})["status"],"error")

    def test_38_model_page_boolean_index_rejected(self):
        s=self.sessions["geometry_test_03"]
        self.assertEqual(s.call("read_native_ifc_page",{
            "catalog":"step","page":True})["status"],"error")

    def test_39_model_page_out_of_range_rejected(self):
        s=self.sessions["geometry_test_03"]
        self.assertEqual(s.call("read_native_ifc_page",{
            "catalog":"step","page":99999})["status"],"error")

    def test_40_model_page_injected_extra_argument_rejected(self):
        s=self.sessions["geometry_test_03"]
        self.assertEqual(s.call("read_native_ifc_page",{
            "catalog":"step","page":0,"eval":"malicious"})["status"],"error")

    def test_41_model_read_unknown_arguments_rejected(self):
        s=self.sessions["geometry_test_03"]
        self.assertEqual(s.call("read_building_xml",{"eval":"no"})["status"],"error")

    def test_42_original_four_v044_source_inputs_not_accepted_in_v046(self):
        from src.runtime.experimental_v44_original_native_step_readonly import PINS
        sha,task=next(iter(PINS.items()))
        p=self.source_by_id[task[0]]
        with self.assertRaises(UnsupportedArm):
            XmlSourceEditSession(p,self.work/"excluded",
                experimental_original_native_catalog_v046=True)

    def test_43_experimental_v046_mutually_exclusive_with_v045(self):
        p=self.source_by_id["geometry_test_03"]
        with self.assertRaisesRegex(UnsupportedArm,"mutually exclusive"):
            XmlSourceEditSession(p,self.work/"exclusive",
                experimental_original_native_catalog_v046=True,
                experimental_original_native_mutations_v045=True)

    def test_44_prior_experiment_v039_legacy_mutual_exclusion(self):
        p=self.source_by_id["geometry_test_03"]
        with self.assertRaisesRegex(UnsupportedArm,"mutually exclusive"):
            XmlSourceEditSession(p,self.work/"legacy",
                experimental_original_native_catalog_v046=True,
                experimental_original_legacy_v08=True)

    def test_45_unpinned_modified_original_IFC_copy_refused(self):
        original=self.source_by_id["geometry_test_03"]
        clone=self.work/"mutated-source.ifc"
        clone.write_bytes(original.read_bytes())
        f=ifcopenshell.open(str(clone))
        f.by_type("IfcProject")[0].Name="SPOOF"
        f.write(str(clone))
        with self.assertRaises(UnsupportedArm):
            XmlSourceEditSession(clone,self.work/"bad-source",
                experimental_original_native_catalog_v046=True)

    def test_46_original_clone_later_modified_blocks_page_and_manifest(self):
        original=self.source_by_id["geometry_test_03"]
        clone=self.work/"tamper-after-source-session.ifc"
        clone.write_bytes(original.read_bytes())
        s=XmlSourceEditSession(clone,self.work/"s",
            experimental_original_native_catalog_v046=True)
        self.assertEqual(s.call("read_native_ifc_page",{
            "catalog":"roots","page":0})["status"],"ok")
        clone.write_bytes(clone.read_bytes()+b"\n#TAMPERED_BYTES")
        self.assertEqual(s.call("read_native_ifc_page",{
            "catalog":"roots","page":0})["error_type"],"OriginalSourceSHAChanged")
        self.assertEqual(s.call("read_building_xml",{})["error_type"],
                         "OriginalSourceSHAChanged")
        self.assertEqual(file_hash(original),self.task[
            "geometry_test_03"]["original_ifc_sha256"])

    def test_47_source_manifest_root_SHA_spoof_rejected(self):
        self._modified_manifest(lambda r:r.set("sourceOriginalIFCSha256","0"*64))

    def test_48_source_manifest_schema_spoof_rejected(self):
        self._modified_manifest(lambda r:r.set("sourceNativeIfcSchema","IFC4X3"))

    def test_49_source_manifest_writer_permission_spoof_rejected(self):
        self._modified_manifest(lambda r:r.set("nativeMutationPermission","READ_WRITE"))

    def test_50_source_manifest_record_count_spoof_rejected(self):
        self._modified_manifest(lambda r:r[0][0].set("recordCount","2"))

    def test_51_source_manifest_pages_count_spoof_rejected(self):
        self._modified_manifest(lambda r:r[0][0].set("pageCount","99"))

    def test_52_source_manifest_catalog_SHA_spoof_rejected(self):
        self._modified_manifest(lambda r:r[0][0].set(
            "canonicalSourceRecordsSha256","0"*64))

    def test_53_source_manifest_catalog_missing_rejected(self):
        self._modified_manifest(lambda r:r[0].remove(r[0][0]))

    def test_54_source_manifest_catalog_duplicate_rejected(self):
        self._modified_manifest(lambda r:r[0].append(
            etree.fromstring(etree.tostring(r[0][0]))))

    def test_55_source_page_index_spoof_rejected(self):
        self._modified_page("roots",lambda r:r.set("page","99"))

    def test_56_source_page_original_root_GUID_spoof_rejected(self):
        self._modified_page("roots",lambda r:r[0].set("ifcGuid","0"*22))

    def test_57_source_page_original_root_name_spoof_rejected(self):
        self._modified_page("roots",lambda r:r[0].set("originalName","FORGED"))

    def test_58_source_page_original_product_GUID_spoof_rejected(self):
        self._modified_page("products",lambda r:r[0].set("ifcGuid","0"*22))

    def test_59_source_page_original_placement_ref_spoof_rejected(self):
        self._modified_page("products",lambda r:r[0][2].set("value","999"))

    def test_60_source_page_original_relationship_GUID_spoof_rejected(self):
        self._modified_page("relationships",lambda r:r[0].set("ifcGuid","0"*22))

    def test_61_source_page_original_relationship_endpoint_spoof_rejected(self):
        def tamper(r):
            ref=next(x for e in r for x in e if x.tag==N+"Ref")
            ref.set("sourceStepId","99999")
        self._modified_page("relationships",tamper)

    def test_62_source_page_original_relationship_role_spoof_rejected(self):
        def tamper(r):
            ref=next(x for e in r for x in e if x.tag==N+"Ref")
            ref.set("role","FAKE_TOPOLOGY")
        self._modified_page("relationships",tamper)

    def test_63_source_page_original_propertySet_GUID_spoof_rejected(self):
        self._modified_page("property_sets",lambda r:r[0].set("ifcGuid","0"*22))

    def test_64_source_page_original_property_nominal_value_spoof_rejected(self):
        def tamper(r):
            x=next(x for e in r for x in e if x.tag==N+"Field")
            x.set("value",'{"originalNominalValue":"FAKE"}')
        self._modified_page("property_sets",tamper)

    def test_65_source_page_original_material_name_spoof_rejected(self):
        self._modified_page("materials",lambda r:r[0].set("originalName","FAKE"))

    def test_66_source_page_original_placement_matrix_spoof_rejected(self):
        self._modified_page("placements",lambda r:r[0][0].set("value","12345"))

    def test_67_source_page_original_placement_parent_spoof_rejected(self):
        self._modified_page("placements",lambda r:r[0][-2].set("value","9999"))

    def test_68_source_page_original_geometry_mesh_status_spoof_rejected(self):
        self._modified_page("geometry",lambda r:r[0].set("meshStatus","FAKE_MESH"))

    def test_69_source_page_original_geometry_world_sha_spoof_rejected(self):
        def tamper(r):
            x=next(x for x in r if x.get("worldMeshSHA256"))
            x.set("worldMeshSHA256","0"*64)
        self._modified_page("geometry",tamper)

    def test_70_source_page_original_geometry_bounding_box_spoof_rejected(self):
        def tamper(r):
            x=next(x for x in r if x.get("worldMeshSHA256"))
            x.set("bboxMaxZ","99999.000")
        self._modified_page("geometry",tamper)

    def test_71_source_page_original_STEP_literal_changed_rejected(self):
        self._modified_page("step",lambda r:r[0][-1].__setattr__(
            "text","#1=IFCFAKE();"))

    def test_72_source_page_original_STEP_sha256_spoof_rejected(self):
        self._modified_page("step",lambda r:r[0].set("literalSha256","0"*64))

    def test_73_source_page_original_STEP_entity_ID_spoof_rejected(self):
        self._modified_page("step",lambda r:r[0].set("sourceStepId","99999"))

    def test_74_source_page_original_STEP_entity_IFC_class_spoof_rejected(self):
        self._modified_page("step",lambda r:r[0].set("nativeIfcClass","IFCFAKE"))

    def test_75_source_page_original_STEP_entity_missing_rejected(self):
        self._modified_page("step",lambda r:r.remove(r[0]))

    def test_76_source_page_original_STEP_entity_duplicated_rejected(self):
        self._modified_page("step",lambda r:r.append(
            etree.fromstring(etree.tostring(r[0]))))

    def test_77_source_page_original_STEP_entity_order_reordered_rejected(self):
        def tamper(r):
            first=r[0];r.remove(first);r.append(first)
        self._modified_page("step",tamper)

    def test_78_source_page_extra_unknown_xml_field_rejected(self):
        self._modified_page("step",lambda r:r[0].set("arbitraryCode","RUN"))

    def test_79_source_page_missing_category_pages_rejected(self):
        pages={x:list(y) for x,y in self.pages["geometry_test_03"].items()}
        pages["step"].pop()
        with self.assertRaises(IndependentOriginalCatalog046Error):
            verify_native_catalog_046(
                self.source_by_id["geometry_test_03"],
                self.task["geometry_test_03"]["original_ifc_sha256"],
                self.manifests["geometry_test_03"],pages)

    def test_80_source_page_duplicate_page_number_rejected(self):
        pages={x:list(y) for x,y in self.pages["geometry_test_03"].items()}
        pages["step"].append(pages["step"][-1])
        with self.assertRaises(IndependentOriginalCatalog046Error):
            verify_native_catalog_046(
                self.source_by_id["geometry_test_03"],
                self.task["geometry_test_03"]["original_ifc_sha256"],
                self.manifests["geometry_test_03"],pages)

    def test_81_native_source_sample_dedicated_XSD_valid(self):
        schema=etree.XMLSchema(etree.parse(str(SCHEMA_XSD)))
        self.assertTrue(schema.validate(etree.fromstring(
            self.manifests["geometry_test_03"])))
        for arr in self.pages["geometry_test_03"].values():
            for xml in arr:
                self.assertTrue(schema.validate(etree.fromstring(xml)))

    def test_82_v046_native_original_source_catalog_immutable_readonly(self):
        self.assertEqual(self.report["total_fail_closed_model_facing_native_edit_submissions"],54)
        self.assertEqual(self.report["total_original_native_IFC_candidate_files"],0)
        self.assertFalse(self.report["new_native_IFC_writer_authority_in_v046"])

    def test_83_full_original45_equal_information_write_not_proven(self):
        self.assertFalse(self.report["full_original45_equal_information_and_native_edit_authority_proven"])
        self.assertFalse(self.report["full_Python_IfcOpenShell_executable_model_interface_parity_proven"])
        self.assertFalse(self.report["same_model_initial_context_size_and_token_budget_proven"])

    def test_84_no_original_author_grader_paid_provider_or_Docker(self):
        self.assertEqual(self.report["original_author_evaluator_calls"],0)
        self.assertEqual(self.report["paid_provider_calls"],0)
        self.assertEqual(self.report["Docker_executions"],0)
        self.assertEqual(self.report["real_original_XML_vs_Python_matched_LLM_trials"],0)

    def test_85_old_CREATE_D0_I0_developer_pairs_not_inflated(self):
        self.assertEqual(self.report["previous_original_CREATE_task_specific_D0_I0_developer_pairs"],5)
        self.assertEqual(self.report["new_original_CREATE_task_specific_D0_I0_developer_pairs"],0)

    def test_86_default_paired_provider_runner_does_not_enable_v046(self):
        self.assertFalse(self.report["default_paid_provider_runner_automatically_enables_v046"])
        self.assertNotIn("experimental_original_native_catalog_v046=True",
            (audit.ROOT/"tools"/"bibimbap_matched25_cli.py").read_text(encoding="utf8"))

    def test_87_prior_v045_native_edit_frozen_mode_preserved(self):
        from src.runtime.experimental_v44_original_native_step_readonly import PINS
        sha,pin=next(iter(PINS.items()))
        source=self.source_by_id[pin[0]]
        with TemporaryDirectory() as tmp:
            s=XmlSourceEditSession(source,Path(tmp)/"v045",
                experimental_original_native_mutations_v045=True)
            self.assertIsNotNone(s.native_mutation_original_task_id)
            self.assertIsNone(s.native_catalog_v046)
            self.assertEqual(s.call("read_building_xml",{})["status"],"ok")

    def test_88_report_fails_overwrite_immutability(self):
        with self.assertRaises(FileExistsError):
            with REPORT.open("xb") as f:f.write(b"FORGED")
        self.assertEqual(file_hash(REPORT),REPORT_SHA)

    def test_89_all_27_original_source_report_replay_byte_identical(self):
        fresh=audit.audit(AUTHOR,DATA)
        raw=(json.dumps(fresh,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf8")
        self.assertEqual(sha256(raw).hexdigest(),REPORT_SHA)
        self.assertEqual(raw,REPORT.read_bytes())

    def test_90_all_original_ifc_source_sha_still_same_after_real_pages(self):
        for tid in ("geometry_test_03","geometry_test_05","geometry_test_16"):
            self.assertEqual(file_hash(self.source_by_id[tid]),
                             self.task[tid]["original_ifc_sha256"])


if __name__=="__main__":
    unittest.main()
