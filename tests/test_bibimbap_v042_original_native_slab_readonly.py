"""v0.42 original P3 read-only source native IfcSlab exact-index and IFC tests.

Negative tests deliberately try to falsify original Slab mesh/Storey/identity,
non-pinned inputs, unauthorized actions, and last-good native IFC handling.
No original author grader, hidden GT, paid LLM, Docker or live benchmark score.
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
import ifcopenshell.api
import ifcopenshell.util.unit
from lxml import etree

from tools import audit_bibimbap_v042_original_native_slab_source as audit
from tools.bibimbap_matched25_tools import (
    XmlSourceEditSession,UnsupportedArm,file_hash)
from tools.bibimbap_v042_native_slab_source_oracle import (
    verify_original_native_slab_evidence,
    verify_v042_output_original_native,IndependentNativeSlab042Error)
from src.runtime.experimental_v42_native_slab_readonly import (
    OriginalSlabEvidence042Error,
    strip_verified_original_slab_evidence,
    XSD,
)

BASE=Path(r"D:\\문서\\D__1_Projects\\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=audit.ROOT/"reports"/"bibimbap_v042_original_P3_source_native_slab_readonly_reproducible_20261117.json"
FROZEN_SHA="f883dfb095746ceebbaa9f718e5355c61dbb2a356387b7882b400036cdf1b20e"
Q="{urn:bim-markup-bench:toy:v0}"


class OriginalNativeSlabV042(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cohort=audit.input_cohort(audit.ROOT,AUTHOR,DATA)
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))
        cls.rows={r["task_id"]:r for r in cls.report["rows"]}

    def setUp(self):
        tmp=TemporaryDirectory(prefix="bmb-v042-exact-source-slab-")
        self.addCleanup(tmp.cleanup)
        self.tmp=Path(tmp.name)

    def source(self,tid="topological_test_02"):
        return DATA/"ifc"/self.cohort[tid]["original_source_ifc_relpath"]

    def session(self,tid="topological_test_02"):
        return XmlSourceEditSession(
            self.source(tid),self.tmp/"s",
            experimental_original_native_slab_v042=True)

    def valid(self,tid="topological_test_02"):
        s=self.session(tid)
        edited=audit.illustrative_non_answer_xml(
            s.current_xml,kind=audit.PINS[tid]["kind"])
        root=etree.fromstring(edited)
        return s,root

    def reject(self,s,payload):
        source=s.original_ifc
        sha=file_hash(source)
        old_xml=s.current_xml
        native=s.output_ifc
        native_sha=file_hash(native) if native else None
        if isinstance(payload,etree._Element):
            payload=etree.tostring(payload,encoding="unicode")
        result=s.call("submit_building_xml",{"xml_text":payload})
        self.assertEqual(result["status"],"error",result)
        self.assertFalse(result.get("native_ifc_committed",False))
        self.assertTrue(result.get("last_valid_xml_preserved",False))
        self.assertEqual(s.current_xml,old_xml)
        self.assertEqual(s.output_ifc,native)
        if native:self.assertEqual(file_hash(native),native_sha)
        self.assertEqual(file_hash(source),sha)
        return result

    def write(self,tid="topological_test_02"):
        s,root=self.valid(tid)
        payload=etree.tostring(root,encoding="utf8")
        result=s.call("submit_building_xml",{"xml_text":payload.decode("utf8")})
        self.assertEqual(result["status"],"ok",result)
        self.assertIsNotNone(s.output_ifc)
        return s,root,payload

    def native(self,root,index=0):
        return root.find(Q+"OriginalNativeSlabEvidence").find(Q+"NativeSlabs")[index]

    def relation(self,root,index=0):
        return root.find(Q+"OriginalNativeSlabEvidence").find(
            Q+"OriginalExplicitSlabRelations")[index]

    def test_01_frozen_report_SHA256(self):
        self.assertEqual(file_hash(REPORT),FROZEN_SHA)

    def test_02_previous_v037_v040_v041_and_preliminary_v042_reports_unchanged(self):
        for p,sha in (audit.V037,audit.V040,audit.V041,audit.V042_PRELIM):
            self.assertEqual(file_hash(audit.ROOT/p),sha)

    def test_03_original_45_public_and_15_create_unchanged(self):
        self.assertEqual(len(self.cohort),45)
        self.assertEqual(Counter(t["crud"] for t in self.cohort.values()),
                         {"create":15,"update":15,"delete":15})
        self.assertEqual(self.report["original_public_ITT_tasks_total"],45)
        self.assertEqual(self.report["original_PUBLIC_create_tasks_total"],15)

    def test_04_two_original_public_input_and_question_SHA_pins(self):
        for tid,pin in audit.PINS.items():
            t=self.cohort[tid]
            self.assertEqual(t["original_ifc_sha256"],pin["source_sha"])
            self.assertEqual(t["public_question_sha256"],pin["question_sha"])
            self.assertEqual(file_hash(self.source(tid)),pin["source_sha"])

    def test_05_native_original_slab_source_inventory_counts(self):
        for tid,pin in audit.PINS.items():
            f=ifcopenshell.open(str(self.source(tid)))
            self.assertEqual(f.schema,"IFC4X3")
            self.assertAlmostEqual(
                ifcopenshell.util.unit.calculate_unit_scale(f),.001)
            self.assertEqual(len(f.by_type("IfcSlab")),pin["native_slabs"])
            self.assertEqual(len(f.by_type("IfcWall")),pin["existing_walls"])
            self.assertEqual(len(f.by_type("IfcRoot")),pin["source_roots"])

    def test_06_source_old_P3_XML_truly_did_not_expose_slab(self):
        for tid in audit.TARGETS:
            with TemporaryDirectory(prefix="v042-old-host-") as temp:
                s=XmlSourceEditSession(
                    self.source(tid),Path(temp)/"old",
                    experimental_original_p3_v041=True)
                doc=etree.fromstring(s.current_xml)
                self.assertEqual(
                    len([n for n in doc.find(Q+"Elements") if n.tag==Q+"Slab"]),0)

    def test_07_v042_two_original_native_slab_information_visible(self):
        row=self.rows["topological_test_02"]
        self.assertEqual(row["v042_XML_native_readonly_reference_Slabs"],2)
        self.assertEqual(row["v042_XML_editable_existing_original_Slabs"],0)

    def test_08_v042_other_original_one_slab_readonly_and_not_editable(self):
        row=self.rows["topological_test_04"]
        self.assertEqual(row["v042_XML_native_readonly_reference_Slabs"],1)
        self.assertEqual(row["v042_XML_editable_existing_original_Slabs"],0)

    def test_09_all_three_slabs_exact_original_native_mm_indexed_triangles(self):
        self.assertEqual(self.report[
            "source_native_original_Slab_mesh_verts_total"],24)
        self.assertEqual(self.report[
            "source_native_original_Slab_mesh_triangle_indices_total"],36)
        for row in self.rows.values():
            evidence=row["v042_read_source_mesh_original_native_mm_independent_oracle"]
            for slab in evidence["slabs"]:
                self.assertEqual(slab["source_mm_ordered_vertices"],8)
                self.assertEqual(slab["source_mm_ordered_index_triangles"],12)
                self.assertTrue(slab["model_visible_triangle_indices_exact_match"])
                self.assertTrue(slab["model_visible_ordered_world_vertices_exact_match_at_1um_decimal"])

    def test_10_native_relationship_original_storey_and_real_GUIDs(self):
        evidence=self.rows["topological_test_02"][
            "v042_read_source_mesh_original_native_mm_independent_oracle"]
        refs={x["original_native_slab_guid"]:x for x in evidence["slabs"]}
        self.assertEqual(refs["3_DHXxtdb3wRKlXgyMiHD0"][
            "original_native_storey_guid"],"2JF4e6axWHqu3u0C1FZlmi")
        self.assertEqual(refs["3_DHXxtdb3wRKlXgyMiHCa"][
            "original_native_storey_guid"],"1ZGO8hrFCHqw0v0026FpFv")
        self.assertEqual(refs["3_DHXxtdb3wRKlXgyMiHD0"][
            "original_native_spatial_relation_guid"],"2JF4e6axWHqu3u0C5FZlmi")

    def test_11_native_floor_lower_and_upper_world_bounds_real(self):
        a=self.rows["topological_test_02"][
            "v042_read_source_mesh_original_native_mm_independent_oracle"]["slabs"]
        boxes={x["original_native_slab_guid"]:x["original_world_bounds_m"] for x in a}
        self.assertEqual(boxes["3_DHXxtdb3wRKlXgyMiHD0"]["min"],[0,0,-.3])
        self.assertEqual(boxes["3_DHXxtdb3wRKlXgyMiHCa"]["max"],[5.05,6.4,3.])

    def test_12_unchanged_native_slab_metadata_type_and_name(self):
        s=self.session()
        root=etree.fromstring(s.current_xml)
        for slab in root.find(Q+"OriginalNativeSlabEvidence").find(Q+"NativeSlabs"):
            self.assertEqual(slab.get("nativeIfcClass"),"IfcSlab")
            self.assertEqual(slab.get("originalPredefinedType"),"FLOOR")
            self.assertEqual(slab.get("compilerEditPermission"),"NONE_READ_ONLY")
            self.assertTrue(slab.get("originalName"))
        self.assertEqual(len(root.find(Q+"Elements")),4)

    def test_13_prior_P3_models_typed_Wall_levels_and_relations_unchanged(self):
        for tid in audit.TARGETS:
            row=self.rows[tid]
            self.assertTrue(row["v042_model_visible_XML_unchanged_existing_typed_state"])
            self.assertEqual(row["original_native_source_wall_count"],audit.PINS[tid]["existing_walls"])

    def test_14_actual_model_tools_still_only_read_and_submit_whole_XML(self):
        s=self.session()
        self.assertEqual({x["name"] for x in s.tools},
                         {"read_building_xml","submit_building_xml"})
        self.assertEqual(s.call("run_python",{"python":"pass"})["status"],"error")
        r=s.call("read_building_xml",{})
        self.assertEqual(r["status"],"ok")
        self.assertEqual(r["xml"],s.current_xml.decode("utf8"))
        self.assertFalse(r["native_candidate_available"])

    def test_15_only_two_P3_native_model_writers_now_have_original_source_slab_context(self):
        self.assertEqual(self.report["new_actual_model_facing_P3_native_create_writers_verified"],2)
        self.assertEqual(self.report["actual_original_native_Slabs_newly_visible_as_read_only_in_XML_instances"],3)

    def test_16_original_topology_column_creation_still_works(self):
        s,_,payload=self.write("topological_test_02")
        r=verify_v042_output_original_native(
            self.source("topological_test_02"),s.output_ifc,
            task_id="topological_test_02",submitted_xml=payload)
        self.assertEqual(r["original_native_mm_output_physical_oracle"][
            "new_original_native_IFC_class"],"IfcColumn")

    def test_17_original_topology_slab_creation_still_works(self):
        s,_,payload=self.write("topological_test_04")
        r=verify_v042_output_original_native(
            self.source("topological_test_04"),s.output_ifc,
            task_id="topological_test_04",submitted_xml=payload)
        self.assertEqual(r["original_native_mm_output_physical_oracle"][
            "new_original_native_IFC_class"],"IfcSlab")

    def test_18_actual_new_native_output_all_original_root_and_physical_shapes_preserved(self):
        for tid in audit.TARGETS:
            row=self.rows[tid]
            oracle=row["v042_reopened_original_native_IFC_independent_oracle"]
            self.assertEqual(oracle["all_original_root_Guids_classes_names_descriptions_preserved"],
                             audit.PINS[tid]["source_roots"])
            self.assertEqual(oracle["all_original_opaque_native_Slab_physical_shapes_preserved"],
                             audit.PINS[tid]["native_slabs"])
            self.assertEqual(oracle["output_IfcRelSpaceBoundary_count"],0)

    def test_19_p3_geometry_only_native_xml_model_vs_python_not_claimed_equal(self):
        self.assertEqual(
            self.report["complete_matched_XML_Python_information_parity_45_tasks"],0)
        self.assertEqual(
            self.report["complete_matched_XML_Python_native_mutation_parity_45_tasks"],0)
        self.assertFalse(self.report["full_other_original_IFC_metadata_information_parity_proven"])

    def test_20_no_original_author_GT_Docker_paid_model_call(self):
        self.assertEqual(self.report["original_author_evaluator_invocations"],0)
        self.assertEqual(self.report["real_matched_LLM_XML_vs_Python_trials"],0)
        self.assertEqual(self.report["Docker_calls"],0)
        self.assertEqual(self.report["paid_provider_calls"],0)

    def test_21_only_exact_pinned_two_original_native_source_inputs_admitted(self):
        bad=DATA/"ifc"/"01/01/01_01_002.ifc"
        with self.assertRaisesRegex(UnsupportedArm,"only admits two"):
            XmlSourceEditSession(bad,self.tmp/"bad",
                experimental_original_native_slab_v042=True)

    def test_22_tampered_source_rejected(self):
        f=ifcopenshell.open(str(self.source()))
        f.by_type("IfcBuilding")[0].Name="Tampered source"
        candidate=self.tmp/"changed_source.ifc"
        f.write(str(candidate))
        with self.assertRaises(UnsupportedArm):
            XmlSourceEditSession(candidate,self.tmp/"bad",
                experimental_original_native_slab_v042=True)

    def test_23_wrong_units_rejected(self):
        f=ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(self.source())),"METER")
        candidate=self.tmp/"metres.ifc"
        f.write(str(candidate))
        with self.assertRaises(UnsupportedArm):
            XmlSourceEditSession(candidate,self.tmp/"bad",
                experimental_original_native_slab_v042=True)

    def test_24_other_optins_mutually_exclusive_and_default_unchanged(self):
        for i,flag in enumerate((
            "experimental_original_p3_v041",
            "experimental_original_room_v040",
            "experimental_original_complex_v039",
            "experimental_original_legacy_v08",
        )):
            with self.assertRaisesRegex(UnsupportedArm,"mutually exclusive"):
                XmlSourceEditSession(self.source(),self.tmp/str(i),
                    experimental_original_native_slab_v042=True,
                    **{flag:True})

    def test_25_original_native_source_catalog_missing_rejected(self):
        s,r=self.valid()
        r.remove(r.find(Q+"OriginalNativeSlabEvidence"))
        self.reject(s,r)

    def test_26_source_catalog_duplicate_rejected(self):
        s,r=self.valid()
        catalog=r.find(Q+"OriginalNativeSlabEvidence")
        r.append(etree.fromstring(etree.tostring(catalog)))
        self.reject(s,r)

    def test_27_catalog_section_out_of_order_rejected(self):
        s,r=self.valid()
        catalog=r.find(Q+"OriginalNativeSlabEvidence")
        r.remove(catalog)
        r.insert(1,catalog)
        self.reject(s,r)

    def test_28_catalog_immutable_SHA256_root_ref_rejected(self):
        s,r=self.valid()
        r.find(Q+"OriginalNativeSlabEvidence").set("originalIFCSha256","a"*64)
        self.reject(s,r)

    def test_29_catalog_wrong_native_schema_class_rejected(self):
        s,r=self.valid()
        self.native(r).set("nativeIfcClass","IfcSpace")
        self.reject(s,r)

    def test_30_catalog_read_only_permission_injection_rejected(self):
        s,r=self.valid()
        self.native(r).set("compilerEditPermission","RW_CREATE")
        self.reject(s,r)

    def test_31_catalog_evidence_version_changed_rejected(self):
        s,r=self.valid()
        r.find(Q+"OriginalNativeSlabEvidence").set("evidenceVersion","0.41")
        self.reject(s,r)

    def test_32_source_IfcSlab_GUID_spoof_rejected(self):
        s,r=self.valid()
        self.native(r).set("ifcGuid","0"*22)
        self.reject(s,r)

    def test_33_original_native_slab_Name_metadata_tamper_rejected(self):
        s,r=self.valid()
        self.native(r).set("originalName","Spoofed FLOOR name")
        self.reject(s,r)

    def test_34_slab_original_floor_predefined_type_change_rejected(self):
        s,r=self.valid()
        self.native(r).set("originalPredefinedType","ROOF")
        self.reject(s,r)

    def test_35_source_native_Slab_Storey_GUID_tamper_rejected(self):
        s,r=self.valid()
        self.native(r).set("sourceContainedStoreyGuid","0"*22)
        self.reject(s,r)

    def test_36_source_native_spatial_containment_relation_GUID_tamper_rejected(self):
        s,r=self.valid()
        self.native(r).set("sourceContainmentRelationGuid","0"*22)
        self.reject(s,r)

    def test_37_original_native_relation_retarget_rejected(self):
        s,r=self.valid()
        self.relation(r).set("originalRelatedGuid","0"*22)
        self.reject(s,r)

    def test_38_invented_original_Slab_rels_rejected(self):
        s,r=self.valid()
        self.relation(r).set("ifcClass","IfcRelSpaceBoundary")
        self.reject(s,r)

    def test_39_original_source_Vertex_X_coordinate_mutated_rejected(self):
        s,r=self.valid()
        first=self.native(r).find(Q+"WorldVertices")[0]
        first.set("x","123.123456")
        self.reject(s,r)

    def test_40_original_source_Vertex_index_permutation_rejected(self):
        s,r=self.valid()
        first=self.native(r).find(Q+"WorldVertices")[0]
        first.set("index","1")
        self.reject(s,r)

    def test_41_original_source_triangle_index_mutated_rejected(self):
        s,r=self.valid()
        first=self.native(r).find(Q+"WorldTriangles")[0]
        first.set("a","7")
        self.reject(s,r)

    def test_42_native_source_triangle_order_modified_rejected(self):
        s,r=self.valid()
        faces=self.native(r).find(Q+"WorldTriangles")
        first=faces[0]
        faces.remove(first)
        faces.append(first)
        self.reject(s,r)

    def test_43_source_mesh_digest_spoof_rejected(self):
        s,r=self.valid()
        self.native(r).set("worldMeshSha256","f"*64)
        self.reject(s,r)

    def test_44_source_mesh_bbox_tamper_rejected(self):
        s,r=self.valid()
        self.native(r).set("worldMaxZ","13")
        self.reject(s,r)

    def test_45_source_Slab_nodes_removal_rejected(self):
        s,r=self.valid()
        section=r.find(Q+"OriginalNativeSlabEvidence").find(Q+"NativeSlabs")
        section.remove(section[0])
        self.reject(s,r)

    def test_46_source_Slab_nodes_duplicate_rejected(self):
        s,r=self.valid()
        section=r.find(Q+"OriginalNativeSlabEvidence").find(Q+"NativeSlabs")
        section.append(etree.fromstring(etree.tostring(section[0])))
        self.reject(s,r)

    def test_47_edit_original_native_ifc_Slab_not_allowed_via_typed_XML(self):
        s,r=self.valid()
        node=self.native(r)
        etree.SubElement(r.find(Q+"Elements"),Q+"Slab",{
            "id":"fake_edit_existing_Slab",
            "ifcGuid":node.get("ifcGuid"),
            "level":next(x for x in r.find(Q+"Levels") if float(x.get("elevation"))==0).get("id"),
            "x":"0","y":"0","z":"0","width":"2","depth":"2","thickness":"0.3",
        })
        self.reject(s,r)

    def test_48_reject_mutated_original_wall_typed_geometry(self):
        s,r=self.valid()
        r.find(Q+"Elements")[0].set("x1","17")
        self.reject(s,r)

    def test_49_reject_extra_new_columns_mixed_mutations(self):
        s,r=self.valid()
        other=etree.fromstring(etree.tostring(r.find(Q+"Elements")[-1]))
        other.set("id","other_column")
        r.find(Q+"Elements").append(other)
        self.reject(s,r)

    def test_50_reject_new_unknown_IfcGUID_spoof(self):
        s,r=self.valid()
        r.find(Q+"Elements")[-1].set("ifcGuid","0"*22)
        self.reject(s,r)

    def test_51_reject_wrong_new_Slab_in_Column_case(self):
        s,r=self.valid()
        n=r.find(Q+"Elements")[-1]
        n.tag=Q+"Slab"
        n.attrib.pop("height")
        n.set("thickness","0.2")
        self.reject(s,r)

    def test_52_reject_XXE_DTD_and_preserve_original_bytes(self):
        s=self.session()
        self.reject(s,'<!DOCTYPE Building [<!ENTITY foo SYSTEM "file:///C:/secret">]><Building>&foo;</Building>')

    def test_53_last_valid_candidate_preserved_after_invalid_edit(self):
        s,r,payload=self.write()
        previous_sha=file_hash(s.output_ifc)
        self.reject(s,"<malformed>")
        self.assertEqual(file_hash(s.output_ifc),previous_sha)
        self.assertTrue(s.call("read_building_xml",{})["native_candidate_available"])

    def test_54_one_new_Column_can_be_revised_then_same_source_evidence(self):
        s,r,payload=self.write()
        before_sha=file_hash(s.output_ifc)
        r.find(Q+"Elements")[-1].set("width","0.65")
        updated=etree.tostring(r,encoding="utf8")
        response=s.call("submit_building_xml",{"xml_text":updated.decode("utf8")})
        self.assertEqual(response["status"],"ok",response)
        self.assertNotEqual(before_sha,file_hash(s.output_ifc))
        result=verify_v042_output_original_native(
            self.source(),s.output_ifc,
            task_id="topological_test_02",submitted_xml=updated)
        self.assertEqual(result["original_native_mm_output_physical_oracle"][
            "new_native_world_bbox_m"]["max"][0],8.65)

    def test_55_independent_oracle_rejects_source_model_vertex_poisoning(self):
        s=self.session()
        root=etree.fromstring(s.current_xml)
        self.native(root).find(Q+"WorldVertices")[0].set("z","99")
        with self.assertRaisesRegex(IndependentNativeSlab042Error,
                                    "coordinates"):
            verify_original_native_slab_evidence(
                self.source(),etree.tostring(root),
                task_id="topological_test_02")

    def test_56_independent_oracle_rejects_source_triangle_flip(self):
        s=self.session()
        root=etree.fromstring(s.current_xml)
        face=self.native(root).find(Q+"WorldTriangles")[0]
        face.set("c","0")
        with self.assertRaisesRegex(IndependentNativeSlab042Error,
                                    "triangle"):
            verify_original_native_slab_evidence(
                self.source(),etree.tostring(root),
                task_id="topological_test_02")

    def test_57_independent_restored_oracle_rejects_removed_original_slab(self):
        s,r,payload=self.write()
        candidate=self.tmp/"tampered-native.ifc"
        f=ifcopenshell.open(str(s.output_ifc))
        original_slab=next(x for x in f.by_type("IfcSlab"))
        f.remove(original_slab)
        f.write(str(candidate))
        with self.assertRaises(Exception):
            verify_v042_output_original_native(
                self.source(),candidate,task_id="topological_test_02",
                submitted_xml=payload)

    def test_58_report_exact_byte_replay_from_two_original_source_IFCs(self):
        result=audit.audit(audit.ROOT,AUTHOR,DATA)
        body=(json.dumps(result,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(body,REPORT.read_bytes())
        self.assertEqual(sha256(body).hexdigest(),FROZEN_SHA)

    def test_59_previous_frozen_report_no_overwrite(self):
        with self.assertRaises(FileExistsError):
            with REPORT.open("xb") as f:f.write(b"NO")
        self.assertEqual(file_hash(REPORT),FROZEN_SHA)

    def test_60_unauthorized_original_public_question_sha_poison_rejected(self):
        fake=[dict(x) for x in self.cohort.values()]
        next(x for x in fake if x["test_id"]=="topological_test_02")[
            "public_question_sha256"]="0"*64
        with patch.object(audit,"public_45",return_value=fake):
            with self.assertRaisesRegex(ValueError,"question/input sha"):
                audit.input_cohort(audit.ROOT,AUTHOR,DATA)

    def test_61_45_ITT_population_duplicate_task_rejected(self):
        fake=[dict(x) for x in self.cohort.values()]
        fake[0]["test_id"]=fake[1]["test_id"]
        with patch.object(audit,"public_45",return_value=fake):
            with self.assertRaisesRegex(ValueError,"45 ITT"):
                audit.input_cohort(audit.ROOT,AUTHOR,DATA)

    def test_62_existing_5_D0_I0_pairs_still_only_five(self):
        self.assertEqual(self.report[
            "original_previous_task_specific_developer_D0_I0_create_pairs"],5)
        self.assertEqual(self.report[
            "original_create_tasks_still_without_task_specific_D0_I0_pairs"],10)

    def test_63_full_original45_model_read_write_parity_still_unknown(self):
        self.assertFalse(self.report["new_native_Slab_evidence_is_editable"])
        self.assertEqual(self.report["complete_matched_XML_Python_information_parity_45_tasks"],0)
        self.assertEqual(self.report["complete_matched_XML_Python_native_mutation_parity_45_tasks"],0)
        self.assertEqual(self.report["original_public_task_specific_D0_I0_solution_proven_by_v042"],0)

    def test_64_original_author_data_remain_git_clean_and_frozen(self):
        self.assertEqual(audit._head(AUTHOR),audit.AUTHOR_SHA)
        self.assertEqual(audit._head(DATA),audit.DATA_SHA)
        for tid in audit.TARGETS:
            self.assertEqual(file_hash(self.source(tid)),audit.PINS[tid]["source_sha"])

    def test_65_default_old_XSD_and_existing_p3_compiler_not_modified_by_v042(self):
        old=(audit.ROOT/"spec"/"toy_markup_v0.xsd").read_text(encoding="utf8")
        self.assertNotIn("OriginalNativeSlabEvidence",old)
        self.assertNotIn("NativeWorldVertex042",old)
        self.assertTrue(XSD.is_file())
        etree.XMLSchema(etree.parse(str(XSD)))
        self.assertEqual(self.report["original_default_XSD_modified"],False)


if __name__=="__main__":
    unittest.main()
