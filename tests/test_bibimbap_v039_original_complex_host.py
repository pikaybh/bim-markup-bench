"""v0.39 original two P1 complex native source whole-XML host gates.

All real IFC input files are opened read-only. No private GT, scorer, LLM,
external API, Docker or execution of model-generated Python.
"""
from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v39_complex_overlay import (
    Q,NS,PINS,ComplexV039Error,project_complex_v039,
    check_pinned_original,
)
from tools.bibimbap_matched25_tools import (
    XmlSourceEditSession,UnsupportedArm,file_hash,
)
from tools.bibimbap_v039_complex_native_oracle import (
    verify_complex_original_restored,IndependentComplexNativeError,
)
from tools import audit_bibimbap_v039_original_complex_host as v39


BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",
    r"D:\\문서\\D__1_Projects\\202611"))
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=v39.ROOT/"reports"/"bibimbap_v039_original_p1_complex_native_xml_live_20261117.json"
FROZEN_REPORT_SHA="3d7a5e642b22b024c938d5c1f712c0eaab8e11ffb6fbe274b0c90ddef074b09a"


class OriginalP1ComplexNativeLive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))
        cls.tasks,cls.prior=v39.inputs(v39.ROOT,AUTHOR,DATA)
        cls.rows={x["task_id"]:x for x in cls.report["rows"]}

    def setUp(self):
        t=TemporaryDirectory(prefix="v039-p1-negative-tests-")
        self.addCleanup(t.cleanup)
        self.tmp=Path(t.name)

    def source(self,tid="geometry_test_01"):
        return DATA/"ifc"/self.tasks[tid]["original_source_ifc_relpath"]

    def session(self,tid="geometry_test_01"):
        return XmlSourceEditSession(
            self.source(tid),self.tmp/"live",
            experimental_original_complex_v039=True)

    def prepared(self,tid="geometry_test_01"):
        s=self.session(tid)
        original=s.current_xml
        updated=v39.illustrative_xml(original,tid)
        self.assertNotEqual(original,updated)
        return s,etree.fromstring(updated)

    def reject(self,s,root,part=""):
        raw=etree.tostring(root,encoding="unicode") if not isinstance(root,str) else root
        old=s.current_xml
        current_output=s.output_ifc
        result=s.call("submit_building_xml",{"xml_text":raw})
        self.assertEqual(result["status"],"error",result)
        self.assertFalse(result.get("native_ifc_committed"))
        self.assertEqual(s.current_xml,old)
        self.assertEqual(s.output_ifc,current_output)
        if part:
            self.assertIn(part,result["error"])
        return result

    def native_committed(self,tid="geometry_test_01"):
        s,root=self.prepared(tid)
        raw=etree.tostring(root,encoding="utf8")
        result=s.call("submit_building_xml",{"xml_text":raw.decode("utf8")})
        self.assertEqual(result["status"],"ok",result)
        return s,root,raw

    def test_01_prior_frozen_evidence_and_v039_report_sha(self):
        self.assertEqual(file_hash(REPORT),FROZEN_REPORT_SHA)
        for file,pin in (v39.V037,v39.V038):
            self.assertEqual(file_hash(v39.ROOT/file),pin)

    def test_02_original_45_15_10_denominators_and_original_five_controls(self):
        report=self.report
        self.assertEqual(report["original_45_public_ITT_denominator"],45)
        self.assertEqual(report["original_15_CREATE_denominator"],15)
        self.assertEqual(report[
            "original_10_CREATE_without_new_task_specific_native_D0_I0_pair"],10)
        self.assertEqual(report["previous_task_specific_original_developer_D0_I0_pairs"],5)
        self.assertEqual(len(self.tasks),45)
        self.assertEqual(Counter(x["crud"] for x in self.tasks.values()),
                         {"create":15,"update":15,"delete":15})

    def test_03_actual_original_input_sha_schema_mm_and_question_pinned(self):
        for tid in v39.TARGETS:
            src=self.source(tid);t=self.tasks[tid]
            self.assertEqual(file_hash(src),t["original_ifc_sha256"])
            model=ifcopenshell.open(str(src))
            self.assertEqual(model.schema,"IFC4X3")
            self.assertAlmostEqual(ifcopenshell.util.unit.calculate_unit_scale(model),.001)
            self.assertEqual(t["public_question_sha256"],
                             self.prior[tid]["public_question_sha256"])

    def test_04_old_default_P1_complex_schema_projection_still_refuses(self):
        for i,tid in enumerate(v39.TARGETS):
            with self.assertRaisesRegex(UnsupportedArm,"UnsupportedIFCGeometry"):
                XmlSourceEditSession(self.source(tid),self.tmp/str(i))
        self.assertEqual(self.report["default_XML_source_P1_admissions"],0)

    def test_05_v039_research_optin_read_exact_original_source_mesh_class(self):
        for i,tid in enumerate(v39.TARGETS):
            with TemporaryDirectory(prefix="v039-real-read-") as t:
                s=XmlSourceEditSession(
                    self.source(tid),Path(t)/"session",
                    experimental_original_complex_v039=True)
                read=s.call("read_building_xml",{})
                self.assertEqual(read["status"],"ok")
                self.assertEqual(read["xml"].encode("utf8"),s.original_xml)
                self.assertFalse(read["native_candidate_available"])
                root=etree.fromstring(s.current_xml)
                self.assertEqual(root.tag,Q+"Building")
                self.assertEqual(root.get("sourceStateCompleteness"),
                    "PARTIAL_NATIVE_REFERENCE_OVERLAY_NOT_LOSSLESS_IFC")
                products=root.findall(".//"+Q+"Product")
                klass="IfcColumn" if tid=="geometry_test_01" else "IfcWall"
                rep="MappedRepresentation" if tid=="geometry_test_01" else "Clipping"
                self.assertEqual(
                    sum(x.get("nativeBodyRepresentationType")==rep
                        for x in products if x.get("ifcClass")==klass),
                    4 if tid=="geometry_test_01" else 7)
                self.assertTrue(all(x.get("worldTrianglesSha256")
                                    for x in products if x.get("ifcClass")==klass))
                self.assertEqual(s.complex_original_task_id,tid)

    def test_06_model_visible_tools_only_read_and_submit_complete_xml(self):
        s=self.session()
        self.assertEqual({x["name"] for x in s.tools},
                         {"read_building_xml","submit_building_xml"})
        self.assertEqual(s.call("execute_ifc_code",{"code":"print(1)"})["status"],"error")
        self.assertIsNone(s.output_ifc)

    def test_07_actual_two_native_IFC_generations_frozen_and_non_scored(self):
        rows=self.rows
        self.assertEqual(set(rows),set(v39.TARGETS))
        self.assertTrue(all(x["actual_native_schema_restored_write_committed"]
                            for x in rows.values()))
        self.assertEqual(rows["geometry_test_01"][
            "actual_candidate_native_mm_sha256"],
            "068723a7ab0752f4009dd8a3a83ac4ef1f6379405797110dbd650b35d869fb72")
        self.assertEqual(rows["topological_test_05"][
            "actual_candidate_native_mm_sha256"],
            "59344c62e813ce08929871ac29eb18f20ed4bc1e883911579261b9d23c9f8d19")
        for row in rows.values():
            self.assertFalse(row["original_author_grader_invoked"])
            self.assertFalse(row["real_model_inference_called"])
            self.assertFalse(row["submitted_illustrative_is_original_task_solution"])
            self.assertFalse(row["causal_XML_vs_Python_impact_supported"])

    def test_08_original_IfcColumn_mapped_geometry_root_and_source_containment(self):
        oracle=self.rows["geometry_test_01"][
            "separate_independent_restored_native_physical_oracle"]
        self.assertEqual(oracle["old_original_Roots_preserved"],63)
        self.assertEqual(oracle["old_original_Products_preserved"],8)
        self.assertEqual(oracle["unchanged_original_physical_mesh_products_verified"],4)
        self.assertEqual(oracle["unchanged_original_physical_mesh_triangles_verified"],48)
        self.assertEqual(oracle["native_created_products_by_class"],{"IfcSlab":1})
        self.assertEqual(oracle["native_created_physical_extents"]["IfcSlab"]["min_m"],
                         [1.0,1.0,3.0])
        self.assertEqual(oracle["native_created_physical_extents"]["IfcSlab"]["max_m"],
                         [2.0,2.0,3.2])

    def test_09_original_clipped_Wall_native_Boolean_and_door_Fill(self):
        oracle=self.rows["topological_test_05"][
            "separate_independent_restored_native_physical_oracle"]
        self.assertEqual(oracle["old_original_Roots_preserved"],116)
        self.assertEqual(oracle["old_original_Products_preserved"],13)
        self.assertEqual(oracle["unchanged_original_physical_mesh_products_verified"],8)
        self.assertEqual(oracle["unchanged_original_physical_mesh_triangles_verified"],96)
        self.assertEqual(oracle["native_created_products_by_class"],
                         {"IfcDoor":1,"IfcOpeningElement":1})
        self.assertTrue(oracle["physical_original_clipped_wall_void_created"])
        self.assertEqual(oracle["native_created_physical_extents"]["IfcDoor"]["triangles"],12)

    def test_10_raw_original_IFC_not_relabelled_or_flattened(self):
        for row in self.rows.values():
            self.assertTrue(row[
                "original_opaque_geometry_is_readonly_not_simplified_typed_rectangle"])
            self.assertEqual(row["original_source_native_ifc_schema"],"IFC4X3")
            self.assertEqual(row["original_source_native_length_unit_to_m"],.001)
            self.assertTrue(row["original_source_bytes_unchanged"])
        self.assertFalse(self.report[
            "original_native_geometry_of_mapped_or_clipped_source_simplified_or_replaced"])

    def test_11_real_LLM_inference_and_causal_comparison_still_zero(self):
        r=self.report
        self.assertEqual(r["real_paired_LLM_XML_Python_model_trials"],0)
        self.assertEqual(r["new_paid_provider_requests"],0)
        self.assertEqual(r["original_task_specific_author_scores_run"],0)
        self.assertFalse(r["Docker_code_execution_invoked"])
        self.assertFalse(r["complete_original_native_source_state_visible_in_XML_proven"])
        self.assertFalse(r["full_original_task_write_equivalence_between_D_and_I_proven"])
        self.assertFalse(r["causal_LLM_representation_performance_claim_supported"])

    def test_12_source_SHA_not_allowlisted_blocked_even_matching_IFC4X3(self):
        original=self.source()
        f=ifcopenshell.open(str(original))
        with self.assertRaisesRegex(ComplexV039Error,"exact pinned"):
            check_pinned_original(original,"0"*64,f)

    def test_13_mutated_original_data_copy_same_schema_refused(self):
        source=self.source()
        model=ifcopenshell.open(str(source))
        model.by_type("IfcBuilding")[0].Name="research-trial-mutated-source-copy"
        copied=self.tmp/"changed-original.ifc"
        model.write(str(copied))
        self.assertEqual(ifcopenshell.open(str(copied)).schema,"IFC4X3")
        with self.assertRaisesRegex(UnsupportedArm,"exact pinned"):
            XmlSourceEditSession(
                copied,self.tmp/"reject",
                experimental_original_complex_v039=True)

    def test_14_original_normalized_meter_file_not_accepted_as_original_mm(self):
        source=self.source()
        copied=self.tmp/"altered-units.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(source)),"METER").write(str(copied))
        with self.assertRaisesRegex(UnsupportedArm,"exact pinned"):
            XmlSourceEditSession(copied,self.tmp/"reject",
                                 experimental_original_complex_v039=True)

    def test_15_P1_optin_never_admits_v038_IFC2X3_or_elsewhere_IFC4X3(self):
        for i,src in enumerate((DATA/"ifc"/"basic_tasks.ifc",
                 DATA/"ifc"/"01/01/01_01_003.ifc")):
            with self.assertRaisesRegex(UnsupportedArm,"exact pinned"):
                XmlSourceEditSession(src,self.tmp/str(i),
                                     experimental_original_complex_v039=True)

    def test_16_P0_v038_and_P1_v039_optin_flags_are_exclusive(self):
        with self.assertRaisesRegex(UnsupportedArm,"mutually exclusive"):
            XmlSourceEditSession(
                self.source(),self.tmp/"both",
                experimental_original_complex_v039=True,
                experimental_original_legacy_v08=True)

    def test_17_wrong_Guid_and_Original_native_source_state_tamper_rejected(self):
        s,root=self.prepared()
        product=root.find(".//"+Q+"Product")
        product.set("ifcGuid","0"*22)
        self.reject(s,root,"Immutable native source")

    def test_18_original_mapped_mesh_digest_spoof_rejected(self):
        s,root=self.prepared()
        product=next(x for x in root.findall(".//"+Q+"Product")
                     if x.get("ifcClass")=="IfcColumn")
        product.set("worldTrianglesSha256","f"*64)
        self.reject(s,root,"Immutable native source")

    def test_19_original_native_source_relation_spoof_rejected(self):
        s,root=self.prepared("topological_test_05")
        relation=root.find(".//"+Q+"Relation")
        relation.set("relatedGuid","1"*22)
        self.reject(s,root,"Immutable native source")

    def test_20_original_source_product_list_removal_rejected(self):
        s,root=self.prepared()
        products=root.find(Q+"OriginalNativeSource").find(Q+"Products")
        products.remove(products[0])
        self.reject(s,root,"Immutable native source")

    def test_21_sourceModelSha256_and_originalIFCSha256_spoof_rejected(self):
        s,root=self.prepared()
        root.set("sourceModelSha256","0"*64)
        self.reject(s,root,"Immutable native source")
        root.set("sourceModelSha256",etree.fromstring(s.original_xml).get(
            "sourceModelSha256"))
        root.set("originalIFCSha256","0"*64)
        self.reject(s,root,"Immutable native source")

    def test_22_DOCTYPE_XXE_unsafe_XML_refused(self):
        s=self.session()
        self.reject(s,'<!DOCTYPE foo [<!ENTITY x SYSTEM "file:///C:/secret">]><foo>&x;</foo>')

    def test_23_injected_XML_Python_commands_not_accepted(self):
        s,root=self.prepared()
        etree.SubElement(root.find(Q+"Elements"),Q+"ExecutePython",
                         attrib={"code":"import os"})
        self.reject(s,root,"v0.39 XML XSD")

    def test_24_injected_XML_processing_instruction_rejected(self):
        s,root=self.prepared()
        root.append(etree.ProcessingInstruction("python","print(1)"))
        self.reject(s,root)

    def test_25_mutated_original_native_IfcBuildingStorey_copy_rejected(self):
        s,root=self.prepared()
        product=next(x for x in root.findall(".//"+Q+"Product")
                     if x.get("ifcClass")=="IfcBuildingStorey")
        product.set("originalName","faked-storey")
        self.reject(s,root,"Immutable native source")

    def test_26_empty_or_incomplete_slabs_not_accepted_for_P1(self):
        s=self.session()
        self.reject(s,etree.fromstring(s.current_xml),
                    "one new declarative IfcSlab")

    def test_27_two_new_slabs_rejected_no_unrelated_mutation(self):
        s,root=self.prepared()
        first=root.find(Q+"Elements")[0]
        etree.SubElement(root.find(Q+"Elements"),Q+"Slab",attrib={
            **dict(first.attrib),"id":"second_invalid_slab"})
        self.reject(s,root,"one new declarative IfcSlab")

    def test_28_wrong_original_storey_identifier_refused(self):
        s,root=self.prepared()
        root.find(Q+"Elements")[0].set("levelGuid","f"*22)
        self.reject(s,root,"original native Storey")

    def test_29_nonfinite_slab_dimensions_refused_by_XSD(self):
        s,root=self.prepared()
        root.find(Q+"Elements")[0].set("length","nan")
        self.reject(s,root,"v0.39 XML XSD")

    def test_30_door_without_physical_hosted_opening_refused(self):
        s,root=self.prepared("topological_test_05")
        op=root.find(Q+"Elements")[0]
        root.find(Q+"Elements").remove(op)
        self.reject(s,root,"Opening then Door")

    def test_31_unsupported_second_door_or_extra_Opening_refused(self):
        s,root=self.prepared("topological_test_05")
        etree.SubElement(root.find(Q+"Elements"),Q+"Door",{
            "id":"new_duplicate","opening":"illustrative_opscope",
            "width":"1","height":"2"})
        self.reject(s,root,"v0.39 XML XSD")

    def test_32_door_referencing_non_wall_original_IfcSlab_refused(self):
        s,root=self.prepared("topological_test_05")
        original_slab=next(x.get("ifcGuid")
                          for x in root.findall(".//"+Q+"Product")
                          if x.get("ifcClass")=="IfcSlab")
        root.find(Q+"Elements")[0].set("hostGuid",original_slab)
        self.reject(s,root,"non-original source Wall")

    def test_33_door_original_wall_reference_mismatched_footprint_refused(self):
        s,root=self.prepared("topological_test_05")
        another=next(x.get("ifcGuid") for x in root.findall(".//"+Q+"Product")
                     if x.get("ifcClass")=="IfcWall"
                     and x.get("ifcGuid")!="3Vyqk8cSj8TOuAk6zHUwAc")
        root.find(Q+"Elements")[0].set("hostGuid",another)
        self.reject(s,root)

    def test_34_door_opening_outside_original_clipped_Wall_refused(self):
        s,root=self.prepared("topological_test_05")
        root.find(Q+"Elements")[0].set("centerX","70")
        self.reject(s,root)

    def test_35_door_physical_Opening_height_above_clipped_Wall_refused(self):
        s,root=self.prepared("topological_test_05")
        root.find(Q+"Elements")[0].set("sillZ","1.5")
        self.reject(s,root,"physical source clipped Wall height")

    def test_36_new_Door_and_opening_dimension_mismatch_refused(self):
        s,root=self.prepared("topological_test_05")
        root.find(Q+"Elements")[1].set("height","2.2")
        self.reject(s,root,"declared sizes differ")

    def test_37_unsafe_duplicate_local_new_guids_refused(self):
        s,root=self.prepared("topological_test_05")
        root.find(Q+"Elements")[1].set("id","illustrative_opscope")
        self.reject(s,root,"Duplicate or missing declarative new IDs")

    def test_38_after_success_malformed_retry_preserves_last_valid_IFC(self):
        s,root,raw=self.native_committed()
        oldfile=s.output_ifc
        oldhash=file_hash(oldfile)
        oldxml=s.current_xml
        self.reject(s,"<malformed>")
        self.assertEqual(s.output_ifc,oldfile)
        self.assertEqual(file_hash(s.output_ifc),oldhash)
        self.assertEqual(s.current_xml,oldxml)
        self.assertEqual(s.submissions,2)
        self.assertTrue(s.call("read_building_xml",{})["native_candidate_available"])

    def test_39_independent_oracle_rejects_old_IfcColumn_name_tamper(self):
        s,root,raw=self.native_committed()
        copied=self.tmp/"mutated-original-column.ifc"
        model=ifcopenshell.open(str(s.output_ifc))
        model.by_type("IfcColumn")[0].Name="metadata-attack"
        model.write(str(copied))
        with self.assertRaisesRegex(IndependentComplexNativeError,
                                    "Root Name/Description"):
            verify_complex_original_restored(
                self.source(),copied,task_id="geometry_test_01",
                submitted_xml=raw)

    def test_40_independent_oracle_rejects_physical_mapped_column_translation(self):
        s,root,raw=self.native_committed()
        copied=self.tmp/"displaced-source-column.ifc"
        f=ifcopenshell.open(str(s.output_ifc))
        col=f.by_type("IfcColumn")[0]
        p=col.ObjectPlacement.RelativePlacement.Location
        vals=list(p.Coordinates)
        vals[0]+=3000.
        p.Coordinates=tuple(vals)
        f.write(str(copied))
        with self.assertRaisesRegex(IndependentComplexNativeError,
                                    "original native product mesh"):
            verify_complex_original_restored(
                self.source(),copied,task_id="geometry_test_01",
                submitted_xml=raw)

    def test_41_independent_oracle_rejects_created_Slab_without_physical_mesh(self):
        s,root,raw=self.native_committed()
        copied=self.tmp/"new-slab-no-shape.ifc"
        f=ifcopenshell.open(str(s.output_ifc))
        new_slab=f.by_type("IfcSlab")[0]
        new_slab.Representation=None
        f.write(str(copied))
        with self.assertRaisesRegex(IndependentComplexNativeError,
                                    "physical Representation is missing"):
            verify_complex_original_restored(
                self.source(),copied,task_id="geometry_test_01",
                submitted_xml=raw)

    def test_42_independent_oracle_rejects_missing_new_native_Wall_Voids_relation(self):
        s,root,raw=self.native_committed("topological_test_05")
        copied=self.tmp/"missing-native-void.ifc"
        f=ifcopenshell.open(str(s.output_ifc))
        rel=f.by_type("IfcRelVoidsElement")[0]
        f.remove(rel)
        f.write(str(copied))
        with self.assertRaisesRegex(IndependentComplexNativeError,
                                    "exactly one new physical void"):
            verify_complex_original_restored(
                self.source("topological_test_05"),copied,
                task_id="topological_test_05",submitted_xml=raw)

    def test_43_v039_frozen_machine_report_actual_replay_identical_bytes(self):
        replay=v39.audit(v39.ROOT,AUTHOR,DATA)
        raw=(json.dumps(replay,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(raw,REPORT.read_bytes())

    def test_44_frozen_machine_evidence_exclusive_write_cannot_overwrite(self):
        with self.assertRaises(FileExistsError):
            with REPORT.open("xb") as handle:handle.write(b"illegal")
        self.assertEqual(file_hash(REPORT),FROZEN_REPORT_SHA)

    def test_45_original_Git_repositories_and_IFC_input_not_modified(self):
        self.assertEqual(v39._head(AUTHOR),v39.AUTHOR_SHA)
        self.assertEqual(v39._head(DATA),v39.DATA_SHA)
        for tid in v39.TARGETS:
            self.assertEqual(file_hash(self.source(tid)),
                             self.tasks[tid]["original_ifc_sha256"])

    def test_46_P1_xml_host_and_oracle_never_call_private_author_grader(self):
        source=Path(v39.__file__).read_text(encoding="utf8")
        self.assertNotIn("grade_author(",source)
        self.assertNotIn("OPENAI_API_KEY",source)
        self.assertNotIn("execute_ifc_code(",source)
        self.assertNotIn("bibimbap_author_worker",source)
        self.assertNotIn("DockerIFCExecutor(",source)

    def test_47_untrusted_source_named_IfcColumn_not_interpreted_as_code(self):
        row=self.rows["geometry_test_01"]
        self.assertTrue(row[
            "original_opaque_geometry_is_readonly_not_simplified_typed_rectangle"])
        self.assertEqual(row["source_original_opaque_representation_type"],
                         "MappedRepresentation")
        self.assertEqual(row["source_original_opaque_product_count"],4)
        row=self.rows["topological_test_05"]
        self.assertEqual(row["source_original_opaque_representation_type"],
                         "Clipping")
        self.assertEqual(row["source_original_opaque_product_count"],7)


if __name__=="__main__":
    unittest.main()
