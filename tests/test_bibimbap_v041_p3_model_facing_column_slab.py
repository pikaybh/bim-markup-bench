"""v0.41 original public P3 real model-facing XML Column/Slab native gates.

Offline explicit source-pinned research tests. No paid LLM/Docker/hidden
ground truth/original author grader; original IFCs and Xim untouched.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v41_p3_column_slab import PINS
from tools.bibimbap_matched25_tools import XmlSourceEditSession,UnsupportedArm,file_hash
from tools import audit_bibimbap_v041_p3_live_column_slab as audit
from tools.bibimbap_v041_p3_native_oracle import (
    verify_p3_original_native_add,P3IndependentNativeError)

BASE=Path(os.environ.get(
    "BIBIMBAP_EXPERIMENT_BASE",
    r"D:\\문서\\D__1_Projects\\202611"))
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=audit.ROOT/"reports"/"bibimbap_v041_original_p3_column_slab_live_source_and_native_writer_20261117.json"
FROZEN_SHA="370a70de43399f77fc57f22b4669ca15b5b63204005b6ddb7414c923bcde0b1e"
Q="{urn:bim-markup-bench:toy:v0}"


class P3ModelFacingColumnSlabNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))
        cls.rows={x["task_id"]:x for x in cls.report["rows"]}
        cls.tasks=audit.input_cohort(audit.ROOT,AUTHOR,DATA)

    def setUp(self):
        tmp=TemporaryDirectory(prefix="bmb-v041-original-p3-focus-")
        self.addCleanup(tmp.cleanup)
        self.tmp=Path(tmp.name)

    def source(self,tid="geometry_test_02"):
        return DATA/"ifc"/self.tasks[tid]["original_source_ifc_relpath"]

    def session(self,tid="geometry_test_02"):
        return XmlSourceEditSession(
            self.source(tid),self.tmp/"session",
            experimental_original_p3_v041=True)

    def candidate(self,tid="geometry_test_02"):
        s=self.session(tid)
        edited=audit.illustrative_non_answer_xml(
            s.current_xml,kind=audit.PINS[tid]["created_kind"])
        return s,etree.fromstring(edited)

    def reject(self,s,root):
        last=s.current_xml
        native=s.output_ifc
        native_sha=file_hash(native) if native else None
        if isinstance(root,etree._Element):
            root=etree.tostring(root,encoding="unicode")
        outcome=s.call("submit_building_xml",{"xml_text":root})
        self.assertEqual(outcome.get("status"),"error",outcome)
        self.assertFalse(outcome.get("native_ifc_committed"))
        self.assertTrue(outcome.get("last_valid_xml_preserved"))
        self.assertEqual(s.current_xml,last)
        self.assertEqual(s.output_ifc,native)
        if native:self.assertEqual(file_hash(native),native_sha)
        return outcome

    def write(self,tid="geometry_test_02"):
        s,root=self.candidate(tid)
        xml=etree.tostring(root,encoding="utf8")
        result=s.call("submit_building_xml",{"xml_text":xml.decode("utf8")})
        self.assertEqual(result["status"],"ok",result)
        return s,root,xml

    def test_01_final_frozen_report_digest(self):
        self.assertEqual(file_hash(REPORT),FROZEN_SHA)

    def test_02_previous_frozen_report_v037_v040_sha_immutable(self):
        for path,sha in (audit.V037,audit.V040):
            self.assertEqual(file_hash(audit.ROOT/path),sha)

    def test_03_original_full_45_and_15_15_15_ITT(self):
        self.assertEqual(len(self.tasks),45)
        self.assertEqual(Counter(t["crud"] for t in self.tasks.values()),
                         {"create":15,"update":15,"delete":15})
        self.assertEqual(self.report["original45_public_ITT_denominator"],45)
        self.assertEqual(self.report["original15_CREATE_denominator"],15)

    def test_04_prior_original_task_specific_pair_count_unchanged(self):
        self.assertEqual(self.report[
            "previous_original_task_specific_developer_D0_I0_semantic_pairs"],5)
        self.assertEqual(self.report[
            "original_CREATE_without_task_specific_D0_I0_semantic_pair"],10)

    def test_05_three_original_question_and_native_IFC_sha_pins(self):
        for tid,pin in audit.PINS.items():
            t=self.tasks[tid]
            self.assertEqual(t["public_question_sha256"],pin["question_sha"])
            self.assertEqual(t["original_ifc_sha256"],pin["original_sha"])
            self.assertEqual(file_hash(self.source(tid)),pin["original_sha"])

    def test_06_three_actual_original_native_schema_and_mm_units(self):
        for tid,pin in audit.PINS.items():
            f=ifcopenshell.open(str(self.source(tid)))
            self.assertEqual(f.schema,"IFC4X3")
            self.assertAlmostEqual(ifcopenshell.util.unit.calculate_unit_scale(f),.001)
            self.assertEqual(len(f.by_type("IfcWall")),pin["source_native_walls"])
            self.assertEqual(len(f.by_type("IfcSlab")),pin["source_opaque_native_slabs"])

    def test_07_p3_optin_not_default_enabled_and_same_full_source_XML(self):
        for tid in audit.TARGETS:
            with TemporaryDirectory(prefix="v041-default-") as t:
                previous=XmlSourceEditSession(self.source(tid),Path(t)/"old")
                self.assertIsNone(previous.p3_original_task_id)
                s=XmlSourceEditSession(self.source(tid),Path(t)/"new",
                    experimental_original_p3_v041=True)
                self.assertEqual(previous.current_xml,s.current_xml)
                self.assertEqual(len(s.current_xml),len(previous.current_xml))

    def test_08_exact_two_model_visible_XML_tools_only(self):
        s=self.session()
        self.assertEqual({x["name"] for x in s.tools},
                         {"read_building_xml","submit_building_xml"})
        self.assertEqual(s.call("execute_ifc_code",{"code":"pass"})["status"],"error")
        data=s.call("read_building_xml",{})
        self.assertEqual(data["xml"],s.current_xml.decode("utf8"))
        self.assertFalse(data["native_candidate_available"])

    def test_09_column01_actual_native_and_original_source_verified(self):
        self.assertEqual(self.rows["geometry_test_02"][
            "independent_original_native_millimetre_IFC_oracle"][
            "new_original_native_IFC_class"],"IfcColumn")
        self.assertEqual(self.rows["geometry_test_02"][
            "independent_original_native_millimetre_IFC_oracle"][
            "all_original_root_Guids_classes_names_descriptions_preserved"],68)

    def test_10_column_topology_actual_original_opaque_slabs_preserved(self):
        row=self.rows["topological_test_02"]
        self.assertEqual(row["original_native_IfcSlabs"],2)
        self.assertEqual(row["original_XML_original_Slabs_visible"],0)
        self.assertEqual(row["independent_original_native_millimetre_IFC_oracle"][
            "all_original_opaque_native_Slab_physical_shapes_preserved"],2)

    def test_11_slab_topology_actual_native_and_old_slab_preserved(self):
        row=self.rows["topological_test_04"]
        self.assertEqual(row["new_declared_XML_element_kind"],"Slab")
        self.assertEqual(row["independent_original_native_millimetre_IFC_oracle"][
            "all_original_opaque_native_Slab_physical_shapes_preserved"],1)
        self.assertEqual(row["independent_original_native_millimetre_IFC_oracle"][
            "all_original_root_Guids_classes_names_descriptions_preserved"],108)

    def test_12_three_original_public_native_adds_confirmed_not_task_answers(self):
        self.assertEqual(self.report[
            "v041_original_public_P3_real_native_create_writers"],3)
        self.assertEqual(self.report[
            "v041_original_P3_model_facing_Column_creation_triggers"],2)
        self.assertEqual(self.report[
            "v041_original_P3_model_facing_Slab_creation_triggers"],1)
        for row in self.rows.values():
            self.assertTrue(row["actual_illustrative_native_IFC_created"])
            self.assertFalse(row["submitted_new_geometry_is_original_task_answer"])

    def test_13_original_physical_products_real_triangles_not_screenshot(self):
        expected={"geometry_test_02":48,
                  "topological_test_02":72,
                  "topological_test_04":96}
        for tid,triangles in expected.items():
            oracle=self.rows[tid]["independent_original_native_millimetre_IFC_oracle"]
            self.assertEqual(oracle["old_physical_IfcProduct_triangles_preserved"],triangles)
            self.assertEqual(oracle["new_native_physical_mesh_triangles"],12)

    def test_14_each_new_native_world_box_matches_full_XML(self):
        for tid in audit.TARGETS:
            oracle=self.rows[tid]["independent_original_native_millimetre_IFC_oracle"]
            self.assertTrue(oracle["new_native_box_matches_full_declarative_XML"])
            self.assertTrue(oracle["new_spatial_relationship_only_existing_Storey"])
            self.assertEqual(oracle["original_IfcRelSpaceBoundary_count"],0)
            self.assertEqual(oracle["output_IfcRelSpaceBoundary_count"],0)

    def test_15_create_rectangular_column_real_tool_and_reopened_mm(self):
        s,root,payload=self.write()
        oracle=verify_p3_original_native_add(
            self.source(),s.output_ifc,task_id="geometry_test_02",
            submitted_xml=payload)
        self.assertEqual(oracle["new_original_native_IFC_class"],"IfcColumn")

    def test_16_create_rectangular_slab_real_tool_and_reopened_mm(self):
        s,root,payload=self.write("topological_test_04")
        oracle=verify_p3_original_native_add(
            self.source("topological_test_04"),s.output_ifc,
            task_id="topological_test_04",submitted_xml=payload)
        self.assertEqual(oracle["new_original_native_IFC_class"],"IfcSlab")

    def test_17_unsupported_original_IFC4X3_valid_pins_rejected(self):
        with self.assertRaisesRegex(UnsupportedArm,"exactly one of three"):
            XmlSourceEditSession(DATA/"ifc"/"basic_tasks.ifc",self.tmp/"bad",
                experimental_original_p3_v041=True)

    def test_18_same_schema_tampered_original_native_source_sha_rejected(self):
        changed=self.tmp/"tampered-original-mm.ifc"
        f=ifcopenshell.open(str(self.source()))
        f.by_type("IfcBuilding")[0].Name="User-evasion-p3"
        f.write(str(changed))
        with self.assertRaisesRegex(UnsupportedArm,"exactly one of three"):
            XmlSourceEditSession(changed,self.tmp/"bad",
                experimental_original_p3_v041=True)

    def test_19_converted_native_metre_source_refused_if_not_original_mm(self):
        changed=self.tmp/"converted-original-metre.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(self.source())),"METER").write(str(changed))
        with self.assertRaisesRegex(UnsupportedArm,"exactly one of three"):
            XmlSourceEditSession(changed,self.tmp/"bad",
                experimental_original_p3_v041=True)

    def test_20_explicit_experimental_flags_v038_v039_v040_mutually_exclusive(self):
        for index,flag in enumerate((
            {"experimental_original_legacy_v08":True},
            {"experimental_original_complex_v039":True},
            {"experimental_original_room_v040":True},
        )):
            with self.assertRaisesRegex(UnsupportedArm,"mutually exclusive"):
                XmlSourceEditSession(self.source(),self.tmp/str(index),
                    experimental_original_p3_v041=True,**flag)

    def test_21_wrong_new_slabs_on_column_criterion_rejected(self):
        s,root=self.candidate()
        root.find(Q+"Elements")[-1].tag=Q+"Slab"
        root.find(Q+"Elements")[-1].attrib.pop("height")
        root.find(Q+"Elements")[-1].set("thickness","0.2")
        self.reject(s,root)

    def test_22_wrong_new_column_on_slab_criterion_rejected(self):
        s,root=self.candidate("topological_test_04")
        new=root.find(Q+"Elements")[-1]
        new.tag=Q+"Column"
        new.attrib.pop("thickness")
        new.set("height","2.5")
        self.reject(s,root)

    def test_23_extra_second_native_column_rejected(self):
        s,root=self.candidate()
        original=root.find(Q+"Elements")[-1]
        clone=etree.fromstring(etree.tostring(original))
        clone.set("id","second_new_column")
        root.find(Q+"Elements").append(clone)
        self.reject(s,root)

    def test_24_extra_second_native_slab_rejected(self):
        s,root=self.candidate("topological_test_04")
        clone=etree.fromstring(etree.tostring(root.find(Q+"Elements")[-1]))
        clone.set("id","second_new_slab")
        root.find(Q+"Elements").append(clone)
        self.reject(s,root)

    def test_25_existing_original_public_Wall_Guid_spoof_rejected(self):
        s,root=self.candidate()
        root.find(Q+"Elements")[0].set("ifcGuid","0"*22)
        self.reject(s,root)

    def test_26_existing_original_source_wall_geometry_changed_rejected(self):
        s,root=self.candidate()
        root.find(Q+"Elements")[0].set("x1","77")
        self.reject(s,root)

    def test_27_existing_native_wall_removed_rejected(self):
        s,root=self.candidate()
        section=root.find(Q+"Elements")
        section.remove(section[0])
        self.reject(s,root)

    def test_28_original_source_model_sha_spoof_rejected(self):
        s,root=self.candidate()
        root.set("sourceModelSha256","f"*64)
        self.reject(s,root)

    def test_29_new_IfcGuid_arbitrary_not_model_assignable(self):
        s,root=self.candidate()
        root.find(Q+"Elements")[-1].set("ifcGuid","0"*22)
        self.reject(s,root)

    def test_30_level_from_opaque_or_nonexistent_foreign_GUID_rejected(self):
        s,root=self.candidate()
        root.find(Q+"Elements")[-1].set("level","unregistered_level")
        self.reject(s,root)

    def test_31_new_column_nonfinite_geometry_rejected(self):
        s,root=self.candidate()
        root.find(Q+"Elements")[-1].set("width","NaN")
        self.reject(s,root)

    def test_32_new_column_zero_width_rejected(self):
        s,root=self.candidate()
        root.find(Q+"Elements")[-1].set("width","0")
        self.reject(s,root)

    def test_33_new_slab_negative_thickness_rejected(self):
        s,root=self.candidate("topological_test_04")
        root.find(Q+"Elements")[-1].set("thickness","-1")
        self.reject(s,root)

    def test_34_new_slab_unbounded_50metre_limit_rejected(self):
        s,root=self.candidate("topological_test_04")
        root.find(Q+"Elements")[-1].set("width","1000")
        self.reject(s,root)

    def test_35_XXE_DTD_bad_xml_rejected_no_original_bytes_touched(self):
        s=self.session()
        before=file_hash(self.source())
        self.reject(s,'<!DOCTYPE Building [<!ENTITY attack SYSTEM "file:///C:/secret">]><Building>&attack;</Building>')
        self.assertEqual(file_hash(self.source()),before)

    def test_36_failed_last_valid_native_IFC_and_editable_XML_preserved(self):
        s,root,payload=self.write()
        native_sha=file_hash(s.output_ifc)
        xml=s.current_xml
        self.reject(s,"<malformed>")
        self.assertEqual(s.current_xml,xml)
        self.assertEqual(file_hash(s.output_ifc),native_sha)
        self.assertEqual(s.submissions,2)
        self.assertTrue(s.call("read_building_xml",{})["native_candidate_available"])

    def test_37_new_native_revised_single_column_geometry_can_be_recompiled(self):
        s,root,payload=self.write()
        first_native_sha=file_hash(s.output_ifc)
        root.find(Q+"Elements")[-1].set("width","0.65")
        second=etree.tostring(root,encoding="utf8")
        r=s.call("submit_building_xml",{"xml_text":second.decode()})
        self.assertEqual(r["status"],"ok",r)
        self.assertNotEqual(first_native_sha,file_hash(s.output_ifc))
        native=verify_p3_original_native_add(
            self.source(),s.output_ifc,task_id="geometry_test_02",
            submitted_xml=second)
        self.assertAlmostEqual(
            native["new_native_world_bbox_m"]["max"][0],8.65)

    def test_38_independent_native_oracle_rejects_lost_original_opaque_Slab(self):
        s,root,payload=self.write("topological_test_02")
        changed=self.tmp/"bad-slab-removal.ifc"
        f=ifcopenshell.open(str(s.output_ifc))
        target=f.by_type("IfcSlab")[0]
        f.remove(target)
        f.write(str(changed))
        with self.assertRaises(P3IndependentNativeError):
            verify_p3_original_native_add(
                self.source("topological_test_02"),changed,
                task_id="topological_test_02",submitted_xml=payload)

    def test_39_independent_native_oracle_rejects_tampered_column_world_bbox(self):
        s,root,payload=self.write()
        changed=self.tmp/"bad-new-column-geometry.ifc"
        f=ifcopenshell.open(str(s.output_ifc))
        old={x.GlobalId for x in ifcopenshell.open(str(self.source())).by_type("IfcRoot")}
        product=next(x for x in f.by_type("IfcColumn") if x.GlobalId not in old)
        position=product.ObjectPlacement.RelativePlacement.Location
        coords=list(position.Coordinates);coords[0]+=500.
        position.Coordinates=tuple(coords)
        f.write(str(changed))
        with self.assertRaisesRegex(P3IndependentNativeError,"bbox"):
            verify_p3_original_native_add(
                self.source(),changed,task_id="geometry_test_02",
                submitted_xml=payload)

    def test_40_independent_native_oracle_rejects_missing_real_slab_geometry(self):
        s,root,payload=self.write("topological_test_04")
        changed=self.tmp/"bad-new-slab-norep.ifc"
        f=ifcopenshell.open(str(s.output_ifc))
        old={x.GlobalId for x in ifcopenshell.open(
            str(self.source("topological_test_04"))).by_type("IfcRoot")}
        product=next(x for x in f.by_type("IfcSlab") if x.GlobalId not in old)
        product.Representation=None
        f.write(str(changed))
        with self.assertRaisesRegex(P3IndependentNativeError,
                                    "physical representation"):
            verify_p3_original_native_add(
                self.source("topological_test_04"),changed,
                task_id="topological_test_04",submitted_xml=payload)

    def test_41_original_public_question_SHA_poison_rejected_in_read_only_cohort(self):
        tasks=[dict(t) for t in self.tasks.values()]
        next(t for t in tasks if t["test_id"]=="geometry_test_02")[
            "public_question_sha256"]="0"*64
        with patch.object(audit,"public_45",return_value=tasks):
            with self.assertRaisesRegex(ValueError,"pre-registration"):
                audit.input_cohort(audit.ROOT,AUTHOR,DATA)

    def test_42_45task_original_benchmark_denominator_duplicate_forbidden(self):
        tasks=[dict(t) for t in self.tasks.values()]
        tasks[0]["test_id"]=tasks[1]["test_id"]
        with patch.object(audit,"public_45",return_value=tasks):
            with self.assertRaisesRegex(ValueError,"45"):
                audit.input_cohort(audit.ROOT,AUTHOR,DATA)

    def test_43_original_report_full_byte_exact_replay(self):
        recreated=audit.audit(audit.ROOT,AUTHOR,DATA)
        blob=(json.dumps(recreated,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(blob,REPORT.read_bytes())
        self.assertEqual(sha256(blob).hexdigest(),FROZEN_SHA)

    def test_44_frozen_report_exclusive_open_cannot_overwrite(self):
        with self.assertRaises(FileExistsError):
            with REPORT.open("xb") as out:out.write(b"never")
        self.assertEqual(file_hash(REPORT),FROZEN_SHA)

    def test_45_no_native_Wall_or_default_XSD_changed(self):
        s=self.session()
        self.assertTrue(s.compiler_supported_subset_only)
        default=Path(audit.ROOT/"spec"/"toy_markup_v0.xsd")
        self.assertNotIn("P3",default.read_text(encoding="utf8"))
        self.assertNotIn("original_p3",default.read_text(encoding="utf8"))
        self.assertEqual({x["name"] for x in s.tools},
                         {"read_building_xml","submit_building_xml"})

    def test_46_full_matched_LLM_read_write_parity_and_scores_not_claimed(self):
        r=self.report
        self.assertFalse(r["v041_original_P3_readable_source_information_parity_with_Python_arm"])
        self.assertFalse(r["v041_original_P3_full_native_mutation_parity_with_Python_arm"])
        self.assertEqual(r["actual_real_matched_LLM_XML_Python_trials"],0)
        self.assertEqual(r["v041_original_public_P3_author_task_solutions_confirmed"],0)
        self.assertFalse(r["causal_XML_vs_Python_LLM_effect_established"])

    def test_47_original_public_author_data_git_unchanged(self):
        self.assertEqual(audit._head(AUTHOR),audit.AUTHOR_SHA)
        self.assertEqual(audit._head(DATA),audit.DATA_SHA)
        for tid in audit.TARGETS:
            self.assertEqual(file_hash(self.source(tid)),
                             audit.PINS[tid]["original_sha"])

    def test_48_no_author_evaluator_hidden_GT_paid_LLM_or_Docker_paths(self):
        self.assertEqual(self.report["original_author_evaluator_invocations"],0)
        self.assertEqual(self.report["Docker_executions"],0)
        self.assertEqual(self.report["new_paid_provider_requests"],0)
        for p in (audit.ROOT/"tools"/"audit_bibimbap_v041_p3_live_column_slab.py",
                  audit.ROOT/"tools"/"bibimbap_v041_p3_native_oracle.py",
                  audit.ROOT/"src/runtime"/"experimental_v41_p3_column_slab.py"):
            s=p.read_text(encoding="utf8")
            self.assertNotIn("grade_author(",s)
            self.assertNotIn("OPENAI_API_KEY",s)
            self.assertNotIn("DockerIFCExecutor(",s)


if __name__=="__main__":
    unittest.main()
