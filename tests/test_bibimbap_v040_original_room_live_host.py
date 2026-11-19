"""v0.40 P2 original public IfcSpace source and model-facing XML negative/positive gates.

Focused experiments: no hidden author scorer or real matched LLM call.
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
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v40_native_room_evidence import (
    Q,NativeRoomV040Error,check_original_native_room_input,
    file_hash as source_file_hash,
    project_native_room_v040,strip_and_validate_room_evidence,
)
from tools import audit_bibimbap_v040_original_room_live_host as audit
from tools.bibimbap_matched25_tools import XmlSourceEditSession,UnsupportedArm,file_hash
from tools.bibimbap_v040_native_room_oracle import (
    verify_p2_native_wall_create,IndependentRoomNativeError,
)
from tools.bibimbap_v038_legacy_live_gate import _world_mesh


BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",
    r"D:\\문서\\D__1_Projects\\202611"))
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=(audit.ROOT/"reports"/
        "bibimbap_v040_original_p2_room_native_mm_exact_20261117.json")
FROZEN_REPORT_SHA="8f5a9d8df436e52139a09c6fd78a961d71684303eb8499d8d61513adca305f3e"
PRELIMINARY_REPORT=(audit.ROOT/"reports"/
    "bibimbap_v040_original_p2_room_readonly_xml_live_20261117.json")
PRELIMINARY_REPORT_SHA="20dfa8000f2f8198eaedfa2a53ecbaa8e55b31981a5cba7c4ef85741aaa9daf0"


class P2OriginalRoomLiveNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))
        cls.rows={x["task_id"]:x for x in cls.report["rows"]}
        cls.tasks,cls.prior=audit.inputs(audit.ROOT,AUTHOR,DATA)

    def setUp(self):
        t=TemporaryDirectory(prefix="bmb-v040-room-test-")
        self.addCleanup(t.cleanup)
        self.tmp=Path(t.name)

    def source(self,tid="topological_test_01"):
        return DATA/"ifc"/self.tasks[tid]["original_source_ifc_relpath"]

    def make_session(self,tid="topological_test_01"):
        return XmlSourceEditSession(
            self.source(tid),self.tmp/"session",
            experimental_original_room_v040=True)

    def make_wall(self,tid="topological_test_01"):
        s=self.make_session(tid)
        xml=audit.illustrative_wall(s.current_xml)
        return s,etree.fromstring(xml)

    def reject(self,s,edited):
        prev=s.current_xml
        previous_ifc=s.output_ifc
        if isinstance(edited,etree._Element):
            edited=etree.tostring(edited,encoding="unicode")
        r=s.call("submit_building_xml",{"xml_text":edited})
        self.assertEqual(r["status"],"error",r)
        self.assertFalse(r.get("native_ifc_committed"))
        self.assertEqual(s.current_xml,prev)
        self.assertEqual(s.output_ifc,previous_ifc)
        return r

    def actual_write(self,tid="topological_test_01"):
        s,xml=self.make_wall(tid)
        payload=etree.tostring(xml,encoding="utf8")
        result=s.call("submit_building_xml",{"xml_text":payload.decode("utf8")})
        self.assertEqual(result["status"],"ok",result)
        return s,xml,payload

    def test_01_frozen_sha_and_prior_reports_immutable(self):
        self.assertEqual(file_hash(REPORT),FROZEN_REPORT_SHA)
        self.assertEqual(file_hash(PRELIMINARY_REPORT),PRELIMINARY_REPORT_SHA)
        for rel,pin in (audit.V037,audit.V039):
            self.assertEqual(file_hash(audit.ROOT/rel),pin)

    def test_02_original_population_45_15_10_and_five_controls_unchanged(self):
        r=self.report
        self.assertEqual(r["original45_public_ITT_denominator"],45)
        self.assertEqual(r["original15_CREATE_denominator"],15)
        self.assertEqual(r["original_5_previous_task_specific_developer_D0_I0_semantic_pairs"],5)
        self.assertEqual(r["original_10_CREATE_without_task_specific_native_D0_I0_pairs"],10)
        self.assertEqual(len(self.tasks),45)
        self.assertEqual(Counter(x["crud"] for x in self.tasks.values()),
                         {"create":15,"update":15,"delete":15})

    def test_03_real_original_IFC4X3_mm_sources_SHA_and_questions_pinned(self):
        for tid in audit.TARGETS:
            src=self.source(tid)
            native=ifcopenshell.open(str(src))
            self.assertEqual(native.schema,"IFC4X3")
            self.assertAlmostEqual(ifcopenshell.util.unit.calculate_unit_scale(native),.001)
            self.assertEqual(file_hash(src),self.tasks[tid]["original_ifc_sha256"])
            self.assertEqual(self.rows[tid]["original_public_question_sha256"],
                             self.prior[tid]["public_question_sha256"])

    def test_04_original_default_XML_admits_but_omits_All_IfcSpaces(self):
        for tid in audit.TARGETS:
            with TemporaryDirectory(prefix="v040-baseline-default-") as t:
                ses=XmlSourceEditSession(self.source(tid),Path(t)/"default")
                doc=etree.fromstring(ses.current_xml)
                typed={x.get("ifcGuid") for x in doc.find(Q+"Elements")}
                original={x.GlobalId for x in ifcopenshell.open(
                    str(self.source(tid))).by_type("IfcSpace")}
                self.assertFalse(typed & original)
                self.assertIsNone(ses.room_original_task_id)
                self.assertEqual(len(doc),3)

    def test_05_v040_optin_read_is_still_two_XML_tools_not_Python_IFC(self):
        s=self.make_session()
        self.assertEqual({x["name"] for x in s.tools},
                         {"read_building_xml","submit_building_xml"})
        self.assertEqual(s.call("execute_ifc_code",{"code":"pass"})["status"],"error")
        read=s.call("read_building_xml",{})
        self.assertEqual(read["status"],"ok")
        self.assertEqual(read["xml"],s.current_xml.decode("utf8"))
        self.assertFalse(read["native_candidate_available"])

    def test_06_original_named_space_GUID_in_case01_now_in_readonly_evidence(self):
        row=self.rows["topological_test_01"]
        self.assertEqual(row["model_visible_original_IfcSpace_readonly_count"],1)
        self.assertFalse(row["original_public_room_noun_mismatch_explicit"])
        self.assertEqual(row["public_guid_actual_IFC_class"],
                         {"3_DHXxtdb3wRKlXgyMiH4s":"IfcSpace"})

    def test_07_both_public_named_room_GUIDs_in_case03_are_real_IfcWall(self):
        row=self.rows["topological_test_03"]
        self.assertEqual(row["model_visible_original_IfcSpace_readonly_count"],2)
        self.assertTrue(row["original_public_room_noun_mismatch_explicit"])
        self.assertEqual(row["public_guid_actual_IFC_class"],
                         {"0rMMWWDi1E0Qbe7dlPjRaK":"IfcWall",
                          "0rMMWWDi1E0Qbe7dlPjRcx":"IfcWall"})
        self.assertTrue(self.report[
            "public_room_identifier_semantic_conflict_repaired_by_editing_original_dataset"] is False)

    def test_08_source_IfcSpace_natively_l_shaped_mesh_not_fabricated_cuboid(self):
        row=self.rows["topological_test_03"]
        rooms=row["model_visible_real_original_IfcSpace_meshes"]
        self.assertEqual(len(rooms),2)
        self.assertTrue(all(x["read_only_world_vertex_count"]==12 for x in rooms))
        self.assertTrue(all(x["read_only_original_physical_triangle_count"]==20 for x in rooms))
        self.assertTrue(all(not x["editable_as_fake_rectangular_XML_Space"] for x in rooms))

    def test_09_case01_source_native_Space_has_real_8_vertices_12_triangles(self):
        room=self.rows["topological_test_01"]["model_visible_real_original_IfcSpace_meshes"][0]
        self.assertEqual(room["read_only_world_vertex_count"],8)
        self.assertEqual(room["read_only_original_physical_triangle_count"],12)
        self.assertEqual(room["world_bounds_m"],[.2,.2,0.,4.85,6.2,2.7])

    def test_10_real_original_aggregate_storey_not_faked_IfcContainment(self):
        for tid in audit.TARGETS:
            f=ifcopenshell.open(str(self.source(tid)))
            rooms={x["ifc_guid"]:x for x in self.rows[tid][
                "model_visible_real_original_IfcSpace_meshes"]}
            for space in f.by_type("IfcSpace"):
                agg=ifcopenshell.util.element.get_aggregate(space)
                self.assertEqual(rooms[space.GlobalId][
                    "original_aggregate_storey_guid"],agg.GlobalId)
                self.assertIsNone(ifcopenshell.util.element.get_container(space))

    def test_11_zero_original_explicit_IfcRelSpaceBoundary_not_invented(self):
        self.assertEqual(self.report["v040_new_IfcRelSpaceBoundary_records_invented"],0)
        for tid in audit.TARGETS:
            row=self.rows[tid]
            self.assertEqual(row["original_IfcRelSpaceBoundary_count"],0)
            self.assertEqual(row["model_visible_original_IfcSpace_explicit_aggregate_relations"],
                             row["model_visible_original_IfcSpace_readonly_count"])
            self.assertEqual(row["independent_reopened_native_IFC_oracle"][
                "output_explicit_IfcRelSpaceBoundary_count"],0)

    def test_12_all_referenced_original_IfcSpace_meshes_match_actual_native(self):
        for tid in audit.TARGETS:
            f=ifcopenshell.open(str(self.source(tid)))
            for item in self.rows[tid]["model_visible_real_original_IfcSpace_meshes"]:
                native=f.by_guid(item["ifc_guid"])
                self.assertTrue(native.is_a("IfcSpace"))
                self.assertEqual(_world_mesh(native)[2],
                    item["read_only_original_physical_triangle_count"])

    def test_13_actual_two_P2_model_facing_native_IFC_writes_confirmed(self):
        self.assertEqual(self.report["v040_original_P2_illustrative_native_Wall_writes"],2)
        self.assertEqual(self.report["v040_original_P2_source_room_evidence_XML_admitted"],2)
        self.assertEqual(self.report["v040_original_native_IfcSpace_entities_readonly_exposed"],3)
        for tid,row in self.rows.items():
            self.assertTrue(row["actual_model_facing_native_Wall_written"])
            self.assertTrue(row["original_IFC_source_unchanged"])
            self.assertFalse(row["illustrative_wall_is_original_topological_task_answer"])

    def test_14_independent_actual_native_root_mesh_counts_and_room_preservation(self):
        a=self.rows["topological_test_01"]["independent_reopened_native_IFC_oracle"]
        b=self.rows["topological_test_03"]["independent_reopened_native_IFC_oracle"]
        self.assertEqual(a["original_Root_guids_and_classes_names_preserved"],88)
        self.assertEqual(b["original_Root_guids_and_classes_names_preserved"],112)
        self.assertEqual(a["original_native_IfcProducts_preserved"],10)
        self.assertEqual(b["original_native_IfcProducts_preserved"],13)
        self.assertEqual(a["original_world_mesh_triangles_preserved"],72)
        self.assertEqual(b["original_world_mesh_triangles_preserved"],124)
        self.assertEqual(a["source_native_IfcSpaces_preserved"],1)
        self.assertEqual(b["source_native_IfcSpaces_preserved"],2)

    def test_15_illustrative_walls_are_far_outside_real_rooms_not_task_solutions(self):
        for tid in audit.TARGETS:
            bbox=self.rows[tid]["independent_reopened_native_IFC_oracle"][
                "new_wall_world_bounds_m"]
            self.assertEqual(bbox["min"],[8.,0.,0.])
            self.assertEqual(bbox["max"],[9.,.2,2.5])
            self.assertEqual(bbox["triangles"],12)

    def test_16_current_ITT_0_matched_LLM_and_0_original_task_scores(self):
        r=self.report
        self.assertEqual(r["actual_real_matched_LLM_XML_Python_trials"],0)
        self.assertEqual(r["actual_original_task_specific_grader_scores_in_v040"],0)
        self.assertEqual(r["new_paid_provider_requests"],0)
        self.assertEqual(r["Docker_worker_executions"],0)
        self.assertEqual(r["complete_original45_model_visible_source_facts_equal_across_D_I_proven"],0)
        self.assertEqual(r["complete_original45_native_edit_rights_equal_across_D_I_proven"],0)
        self.assertFalse(r["causal_original_45_XML_vs_imperative_LLM_performance_effect_proven"])

    def test_17_default_host_unmodified_original_v0_XSD_is_not_new_v040_XSD(self):
        with TemporaryDirectory(prefix="v040-default-xsd-") as d:
            s=XmlSourceEditSession(self.source(),Path(d)/"default")
            self.assertIsNone(s.room_original_task_id)
        default=Path(audit.ROOT/"spec"/"toy_markup_v0.xsd")
        new=Path(audit.ROOT/"spec"/"toy_markup_native_room_evidence_v040.xsd")
        self.assertTrue(default.is_file() and new.is_file())
        self.assertNotEqual(file_hash(default),file_hash(new))
        self.assertIn("OriginalNativeRoomEvidence",new.read_text(encoding="utf8"))
        self.assertNotIn("OriginalNativeRoomEvidence",default.read_text(encoding="utf8"))

    def test_18_unknown_but_valid_IFC4X3_not_v040_allowlisted(self):
        source=DATA/"ifc"/"basic_tasks.ifc"
        with self.assertRaisesRegex(UnsupportedArm,"exact two pinned"):
            XmlSourceEditSession(source,self.tmp/"bad",
                                 experimental_original_room_v040=True)

    def test_19_original_native_same_schema_different_sha_rejected(self):
        copied=self.tmp/"changed-source.ifc"
        original=ifcopenshell.open(str(self.source()))
        original.by_type("IfcBuilding")[0].Name="test-changed-readonly-source"
        original.write(str(copied))
        self.assertEqual(ifcopenshell.open(str(copied)).schema,"IFC4X3")
        with self.assertRaisesRegex(UnsupportedArm,"exact two pinned"):
            XmlSourceEditSession(copied,self.tmp/"rejected",
                                 experimental_original_room_v040=True)

    def test_20_original_IFC_native_units_changed_to_metres_refused(self):
        copied=self.tmp/"converted-source-m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(self.source())),"METER").write(str(copied))
        with self.assertRaisesRegex(UnsupportedArm,"exact two pinned"):
            XmlSourceEditSession(copied,self.tmp/"rejected",
                                 experimental_original_room_v040=True)

    def test_21_all_three_experimental_host_flags_mutually_exclusive(self):
        for index,old in enumerate((
            {"experimental_original_complex_v039":True},
            {"experimental_original_legacy_v08":True},
            {"experimental_original_complex_v039":True,
             "experimental_original_legacy_v08":True},
        )):
            with self.assertRaisesRegex(UnsupportedArm,"mutually exclusive"):
                XmlSourceEditSession(
                    self.source(),self.tmp/("bad-"+str(index)),
                    experimental_original_room_v040=True,**old)

    def test_22_source_Room_mesh_sha_modification_fails_closed(self):
        s,root=self.make_wall()
        space=root.find(".//"+Q+"NativeSpace")
        space.set("worldMeshSha256","f"*64)
        result=self.reject(s,root)
        self.assertIn("Immutable native source Room",result["error"])

    def test_23_source_Room_actual_GUID_spoof_fails_closed(self):
        s,root=self.make_wall()
        root.find(".//"+Q+"NativeSpace").set("ifcGuid","0"*22)
        self.reject(s,root)

    def test_24_source_native_IFC_original_Storey_aggregate_remap_fails_closed(self):
        s,root=self.make_wall()
        root.find(".//"+Q+"NativeSpace").set("sourceAggregateStoreyGuid","0"*22)
        self.reject(s,root)

    def test_25_source_mesh_triangle_index_change_even_in_range_fails_closed(self):
        s,root=self.make_wall("topological_test_03")
        tri=root.find(".//"+Q+"NativeSpace").find(".//"+Q+"Triangle")
        tri.set("a","2" if tri.get("a")!="2" else "3")
        self.reject(s,root)

    def test_26_public_named_Guid_real_IfcWall_mismatch_cannot_be_hidden(self):
        s,root=self.make_wall("topological_test_03")
        ref=root.find(".//"+Q+"PublicRoomReference")
        ref.set("actualNativeIfcClass","IfcSpace")
        self.reject(s,root)

    def test_27_public_named_room_Guid_cannot_be_silently_replaced(self):
        s,root=self.make_wall("topological_test_03")
        root.find(".//"+Q+"PublicRoomReference").set(
            "publicGuid","0rMMWWDi1E0Qbe7dlPjRlq")
        self.reject(s,root)

    def test_28_fabricated_source_SpaceBoundary_relation_rejected(self):
        s,root=self.make_wall()
        ref=root.find(".//"+Q+"OriginalExplicitSpaceRelations")
        etree.SubElement(ref,Q+"Relation",{
            "ifcClass":"IfcRelSpaceBoundary",
            "relationGuid":"0"*22,
            "originalRelatingGuid":"1"*22,
            "originalRelatedGuid":"2"*22,
            "origin":"EXPLICIT_SOURCE_IFC_ONLY"})
        self.reject(s,root)

    def test_29_evidence_removed_incomplete_XML_rejected(self):
        s,root=self.make_wall()
        root.remove(root.find(Q+"OriginalNativeRoomEvidence"))
        self.reject(s,root)

    def test_30_original_top_level_native_source_SHA_spoof_rejected(self):
        s,root=self.make_wall()
        root.set("sourceModelSha256","f"*64)
        self.reject(s,root)
        root.set("sourceModelSha256",etree.fromstring(s.original_xml).get(
            "sourceModelSha256"))
        root.find(Q+"OriginalNativeRoomEvidence").set("originalIFCSha256","f"*64)
        self.reject(s,root)

    def test_31_invalid_XML_XXE_and_DTD_fails_without_system_file_read(self):
        s=self.make_session()
        self.reject(s,'<!DOCTYPE Building [<!ENTITY xxe SYSTEM "file:///C:/secret">]><Building>&xxe;</Building>')
        self.assertEqual(s.submissions,1)

    def test_32_another_typed_IfcSpace_not_allowed_in_native_Wall_only_writer(self):
        s,root=self.make_wall()
        first=root.find(Q+"Levels")[0]
        etree.SubElement(root.find(Q+"Elements"),Q+"Space",{
            "id":"fabricated_room","level":first.get("id"),
            "x":"0","y":"0","z":"0","width":"2","depth":"2","height":"2"})
        self.reject(s,root)

    def test_33_two_new_Walls_unsupported_by_one_new_Wall_mutation_gate(self):
        s,root=self.make_wall()
        etree.SubElement(root.find(Q+"Elements"),Q+"Wall",{
            "id":"second_new_wall","level":root.find(Q+"Levels")[0].get("id"),
            "x1":"5","y1":"0","z1":"0",
            "x2":"6","y2":"0","z2":"0",
            "height":"2.5","thickness":"0.2"})
        self.reject(s,root)

    def test_34_original_wall_typed_geometry_not_authorized_to_change(self):
        s,root=self.make_wall()
        wall=next(x for x in root.find(Q+"Elements")
                  if x.tag==Q+"Wall" and x.get("ifcGuid"))
        wall.set("x1",str(float(wall.get("x1"))+1.))
        self.reject(s,root)

    def test_35_failed_retry_preserves_last_valid_native_wall_and_XML(self):
        s,root,payload=self.actual_write()
        good_xml=s.current_xml
        good_hash=file_hash(s.output_ifc)
        self.reject(s,"<malformed>")
        self.assertEqual(s.current_xml,good_xml)
        self.assertEqual(file_hash(s.output_ifc),good_hash)
        self.assertEqual(s.submissions,2)
        self.assertTrue(s.call("read_building_xml",{})["native_candidate_available"])

    def test_36_independent_oracle_rejects_original_native_IfcSpace_move(self):
        s,root,payload=self.actual_write()
        changed=self.tmp/"tampered-room-native-mm.ifc"
        candidate=ifcopenshell.open(str(s.output_ifc))
        space=candidate.by_type("IfcSpace")[0]
        placement=space.ObjectPlacement.RelativePlacement.Location
        xyz=list(placement.Coordinates)
        xyz[0]+=5000.
        placement.Coordinates=tuple(xyz)
        candidate.write(str(changed))
        with self.assertRaisesRegex(IndependentRoomNativeError,
                                    "world mesh geometry"):
            verify_p2_native_wall_create(
                self.source(),changed,task_id="topological_test_01",
                submitted_xml=payload)

    def test_37_independent_oracle_rejects_new_wall_missing_actual_representation(self):
        s,root,payload=self.actual_write()
        changed=self.tmp/"tampered-new-wall-mm.ifc"
        candidate=ifcopenshell.open(str(s.output_ifc))
        old={x.GlobalId for x in ifcopenshell.open(str(self.source())).by_type("IfcRoot")}
        newwall=next(x for x in candidate.by_type("IfcWall")
                     if x.GlobalId not in old)
        newwall.Representation=None
        candidate.write(str(changed))
        with self.assertRaisesRegex(IndependentRoomNativeError,
                                    "physical representation"):
            verify_p2_native_wall_create(
                self.source(),changed,task_id="topological_test_01",
                submitted_xml=payload)

    def test_38_public_original_question_hash_poison_does_not_pass_original_gate(self):
        tasks=[dict(x) for x in self.tasks.values()]
        t=next(x for x in tasks if x["test_id"]=="topological_test_03")
        t["public_question_sha256"]="0"*64
        with patch.object(audit,"public_45",return_value=tasks):
            with self.assertRaisesRegex(ValueError,"pre-registered"):
                audit.inputs(audit.ROOT,AUTHOR,DATA)

    def test_39_duplicate_original_45_ID_forbidden_not_resampled(self):
        tasks=[dict(x) for x in self.tasks.values()]
        tasks[0]["test_id"]=tasks[1]["test_id"]
        with patch.object(audit,"public_45",return_value=tasks):
            with self.assertRaisesRegex(ValueError,"Original 45 public"):
                audit.inputs(audit.ROOT,AUTHOR,DATA)

    def test_40_source_replay_produces_exact_same_frozen_report_bytes(self):
        recreated=audit.audit(audit.ROOT,AUTHOR,DATA)
        blob=(json.dumps(recreated,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(blob,REPORT.read_bytes())
        self.assertEqual(sha256(blob).hexdigest(),FROZEN_REPORT_SHA)

    def test_41_frozen_machine_report_exclusive_create_cannot_overwrite(self):
        with self.assertRaises(FileExistsError):
            with REPORT.open("xb") as output:output.write(b"never")
        self.assertEqual(file_hash(REPORT),FROZEN_REPORT_SHA)

    def test_42_original_source_data_Git_and_IFC_bytes_still_unmodified(self):
        self.assertEqual(audit._head(AUTHOR),audit.AUTHOR_SHA)
        self.assertEqual(audit._head(DATA),audit.DATA_SHA)
        for tid in audit.TARGETS:
            self.assertEqual(file_hash(self.source(tid)),
                             self.tasks[tid]["original_ifc_sha256"])

    def test_44_original_mm_exact_source_indexed_vertices_and_faces_in_XML(self):
        for tid in audit.TARGETS:
            with TemporaryDirectory(prefix="v040-mesh-exact-native-mm-") as td:
                session=XmlSourceEditSession(
                    self.source(tid),Path(td)/"native_source",
                    experimental_original_room_v040=True)
                doc=etree.fromstring(session.current_xml)
                nodes={x.get("ifcGuid"):x for x in doc.findall(
                    ".//"+Q+"NativeSpace")}
                original=ifcopenshell.open(str(self.source(tid)))
                options=ifcopenshell.geom.settings()
                options.set(options.USE_WORLD_COORDS,True)
                for space in original.by_type("IfcSpace"):
                    owner=ifcopenshell.geom.create_shape(options,space)
                    body=owner.geometry
                    source_vertices=list(body.verts)
                    source_faces=list(body.faces)
                    node=nodes[space.GlobalId]
                    xml_vertices=[tuple(float(x.get(axis)) for axis in
                        ("x","y","z")) for x in node.findall(
                        "./"+Q+"WorldVertices/"+Q+"Vertex")]
                    xml_triangles=[tuple(int(x.get(axis)) for axis in
                        ("a","b","c")) for x in node.findall(
                        "./"+Q+"WorldTriangles/"+Q+"Triangle")]
                    self.assertEqual(len(xml_vertices)*3,len(source_vertices))
                    self.assertEqual(len(xml_triangles)*3,len(source_faces))
                    for i,coords in enumerate(xml_vertices):
                        for j,number in enumerate(coords):
                            self.assertAlmostEqual(number,source_vertices[3*i+j],delta=5.00001e-7)
                    self.assertEqual(xml_triangles,[tuple(source_faces[i:i+3])
                        for i in range(0,len(source_faces),3)])
        self.assertTrue(self.report[
            "v040_all_original_IfcSpace_ordered_vertices_and_indexed_triangles_verbatim_from_native_mm"])

    def test_45_pre_forensic_report_is_preserved_but_not_canonical(self):
        self.assertTrue(PRELIMINARY_REPORT.exists())
        self.assertEqual(file_hash(PRELIMINARY_REPORT),PRELIMINARY_REPORT_SHA)
        self.assertNotEqual(PRELIMINARY_REPORT.read_bytes(),REPORT.read_bytes())
        for row in self.report["rows"]:
            self.assertTrue(all(x[
                "read_only_XML_indexed_mesh_matches_original_native_mm_IFC_exactly"]
                for x in row["model_visible_real_original_IfcSpace_meshes"]))

    def test_43_original_benchmark_scorer_hidden_GT_model_not_called(self):
        for file in (
            Path(audit.__file__),
            audit.ROOT/"src/runtime/experimental_v40_native_room_evidence.py",
            audit.ROOT/"tools/bibimbap_v040_native_room_oracle.py",
        ):
            content=file.read_text(encoding="utf8")
            self.assertNotIn("grade_author(",content)
            self.assertNotIn("OPENAI_API_KEY",content)
            self.assertNotIn("DockerIFCExecutor(",content)
            self.assertNotIn("execute_ifc_code(",content)
        self.assertFalse(self.report[
            "causal_original_45_XML_vs_imperative_LLM_performance_effect_proven"])


if __name__=="__main__":
    unittest.main()
