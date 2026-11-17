"""v0.38 live opt-in legacy original IFCS: audited positive and negative gates.

No original author grade, GT, model provider, network, Docker or paid calls.
All original IFC sources are read-only and pinned; all edited IFC copies local.
"""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v8_legacy_projection import Q,parse_v8
from tools import audit_bibimbap_v038_original_legacy_host as v038
from tools.bibimbap_matched25_tools import (
    XmlSourceEditSession,UnsupportedArm,file_hash,
)
from tools.bibimbap_v038_legacy_live_gate import (
    LegacyLiveGateError,SOURCE_PROFILES,
    check_original_legacy_source,verify_native_original_restored,
)


BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",
    r"D:\\문서\\D__1_Projects\\202611"))
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=(v038.ROOT/"reports"/
    "bibimbap_v038_original_p0_legacy_xml_live_optin_20261117.json")
FROZEN_SHA="c04448087528aa07b9cee64830defe61e5b3a7836fc4cae8f073dac4bfc7aad4"


class V038LegacyLiveHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))
        cls.rows={r["task_id"]:r for r in cls.report["rows"]}
        cls.public,_=v038.original_inputs(v038.ROOT,AUTHOR,DATA)

    def setUp(self):
        tmp=TemporaryDirectory(prefix="bmb-v038-tests-")
        self.addCleanup(tmp.cleanup)
        self.tmp=Path(tmp.name)

    def source(self,tid):
        task=self.public[tid]
        return DATA/"ifc"/task["original_source_ifc_relpath"]

    def live(self,tid):
        return XmlSourceEditSession(
            self.source(tid),self.tmp/"live",
            experimental_original_legacy_v08=True)

    def test_01_report_bytes_pin_and_no_previous_frozen_sha_drift(self):
        self.assertEqual(file_hash(REPORT),FROZEN_SHA)
        for rel,pin in (v038.PARENT_REPORT,v038.LEGACY_REPORT):
            self.assertEqual(file_hash(v038.ROOT/rel),pin)

    def test_02_original_population_45_15_10_3_unchanged(self):
        r=self.report
        self.assertEqual(r["original_45_ITT_denominator"],45)
        self.assertEqual(r["original_15_CREATE_denominator"],15)
        self.assertEqual(r["ten_original_CREATE_still_without_task_specific_native_pair"],10)
        self.assertEqual(r["five_old_original_CREATE_developer_semantic_pairs"],5)
        self.assertEqual(r["prior_v037_P0_actual_schema_rejected_count"],3)
        self.assertEqual(set(self.rows),set(v038.TASKS))
        self.assertEqual(r["v038_P0_explicit_optin_real_XML_source_admitted_count"],3)
        self.assertEqual(r["v038_P0_explicit_optin_real_native_IFC_write_count"],3)
        self.assertEqual(r["v038_default_no_optin_original_schema_admitted_count"],0)

    def test_03_original_source_hashes_and_schema_actual(self):
        for tid,row in self.rows.items():
            src=self.source(tid)
            f=ifcopenshell.open(str(src))
            self.assertEqual(file_hash(src),self.public[tid]["original_ifc_sha256"])
            self.assertEqual(f.schema,row["original_native_schema"])
            self.assertAlmostEqual(ifcopenshell.util.unit.calculate_unit_scale(f),.001)
            self.assertEqual(row["original_source_length_unit_to_m"],.001)
            self.assertEqual(row["public_original_question_sha256"],
                             self.public[tid]["public_question_sha256"])

    def test_04_legacy_default_unchanged_rejects_all_three(self):
        for i,tid in enumerate(v038.TASKS):
            with self.assertRaisesRegex(UnsupportedArm,"IFC4X3"):
                XmlSourceEditSession(self.source(tid),self.tmp/str(i))
        self.assertFalse(self.report["default_existing_IFC4X3_model_host_changed"])

    def test_05_actual_optin_model_facing_read_building_xml_all3(self):
        for tid in v038.TASKS:
            with TemporaryDirectory(prefix="v038-optin-read-") as d:
                s=XmlSourceEditSession(self.source(tid),Path(d)/"xml",
                                        experimental_original_legacy_v08=True)
                status=s.call("read_building_xml",{})
                self.assertEqual(status["status"],"ok")
                self.assertIn('xmlns="urn:bim-markup-bench:legacy:v0.8"',status["xml"])
                self.assertEqual(status["xml"],s.current_xml.decode("utf8"))
                self.assertFalse(status["native_candidate_available"])
                self.assertEqual(s.submissions,0)
                self.assertEqual(s.legacy_original_task_id,tid)
                parse_v8(s.current_xml,source_sha256=file_hash(s.normalized),
                         native_schema=s.original_native_schema)

    def test_06_only_two_model_visible_tools_remain_XML_only(self):
        s=self.live("geometry_test_05")
        self.assertEqual({x["name"] for x in s.tools},
                         {"read_building_xml","submit_building_xml"})
        self.assertEqual(s.call("execute_ifc_code",{"code":"pass"})["status"],"error")
        self.assertEqual(s.submissions,0)

    def test_07_correct_optin_native_Ifc2x3_Door_real_void_and_fill(self):
        row=self.rows["geometry_test_03"]
        self.assertTrue(row["real_model_facing_native_write_committed"])
        native=row["native_source_restored_oracle"]
        self.assertEqual(native["native_output_schema"],"IFC2X3")
        self.assertEqual(native["new_native_products_by_class"],
                         {"IfcOpeningElement":1,"IfcDoor":1})
        self.assertTrue(native["original_wall_physically_voided"])
        self.assertEqual(native["all_original_products_preserved"],7)
        self.assertEqual(native["all_original_root_GUIDs_preserved"],52)

    def test_08_correct_optin_native_Ifc2x3_Space_aggregation(self):
        row=self.rows["geometry_test_04"]
        native=row["native_source_restored_oracle"]
        self.assertTrue(row["real_model_facing_native_write_committed"])
        self.assertEqual(native["native_output_schema"],"IFC2X3")
        self.assertEqual(native["new_native_products_by_class"],{"IfcSpace":1})
        self.assertEqual(native["all_original_products_preserved"],11)
        self.assertEqual(native["all_original_root_GUIDs_preserved"],93)
        self.assertEqual(native["unchanged_original_product_verified_surface_triangle_count"],84)

    def test_09_correct_optin_native_Ifc4_Wall_and_null_elevation(self):
        row=self.rows["geometry_test_05"]
        native=row["native_source_restored_oracle"]
        self.assertTrue(row["real_model_facing_native_write_committed"])
        self.assertEqual(native["native_output_schema"],"IFC4")
        self.assertEqual(native["new_native_products_by_class"],{"IfcWall":1})
        self.assertEqual(native["all_original_products_preserved"],3)
        self.assertEqual(native["all_original_root_GUIDs_preserved"],76)
        s=self.live("geometry_test_05")
        doc=etree.fromstring(s.original_xml)
        self.assertTrue(any(x.get("elevationState")=="MISSING"
                            and x.get("elevation") is None
                            for x in doc.findall("./"+Q+"Levels/"+Q+"Level")))

    def test_10_non_task_solutions_explicitly_do_not_score(self):
        for tid in v038.TASKS:
            row=self.rows[tid]
            self.assertFalse(row["illustrative_benchmark_task_answer"])
            self.assertFalse(row["original_author_scorer_invoked"])
            self.assertFalse(row["agent_or_paid_model_invoked"])
            self.assertFalse(row["actual_matched_LLM_trial_eligible_for_causal_claim"])
            self.assertTrue(row["model_visible_XML_opaque_partial_view_not_entire_IFC"])
            self.assertTrue(row["input_native_source_unchanged"])
            self.assertEqual(row["LLM_tool_names"],
                             ["read_building_xml","submit_building_xml"])
        self.assertEqual(self.report["task_specific_original_author_results_obtained_in_v038"],0)
        self.assertEqual(self.report["actual_original_model_scored_LLM_trials"],0)
        self.assertEqual(self.report["new_paid_provider_requests"],0)
        self.assertEqual(self.report["Docker_or_isolated_Python_LLM_trials"],0)

    def test_11_full_source_information_and_write_parity_unchanged_zero(self):
        self.assertEqual(self.report["original45_entire_source_visible_information_parity_proven"],0)
        self.assertEqual(self.report["original45_full_approved_native_edit_capability_parity_proven"],0)
        self.assertFalse(self.report["full_original_STEP_byte_or_entity_preservation_proven"])
        self.assertFalse(self.report["causal_XML_vs_imperative_model_claim_supported"])
        self.assertFalse(self.report["P1_P2_P3_other_remaining_CREATE_gates_resolved"])

    def test_12_schema_and_units_hard_pins_disallow_arbitrary_source_bytes(self):
        src=self.source("geometry_test_05")
        f=ifcopenshell.open(str(src))
        with self.assertRaisesRegex(LegacyLiveGateError,"pinned source SHA"):
            check_original_legacy_source(src,"f"*64,f)
        with self.assertRaisesRegex(LegacyLiveGateError,"native IFC schema mismatch"):
            check_original_legacy_source(src,self.public["geometry_test_03"]["original_ifc_sha256"],f)

    def test_13_optin_rejects_existing_IFC4X3_original_no_new_default(self):
        src=DATA/"ifc"/"basic_tasks.ifc"
        with self.assertRaisesRegex(UnsupportedArm,"pinned"):
            XmlSourceEditSession(src,self.tmp/"optin",
                                 experimental_original_legacy_v08=True)
        default=XmlSourceEditSession(src,self.tmp/"default")
        self.assertIsNone(default.legacy_original_task_id)
        self.assertIn("ifcSchema=\"IFC4X3\"",default.current_xml.decode("utf8"))

    def test_14_optin_rejects_original_legacy_units_conversion_source_tamper(self):
        src=self.source("geometry_test_05")
        copy=self.tmp/"converted_metres.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(src)),"METER").write(str(copy))
        with self.assertRaisesRegex(UnsupportedArm,"pinned source SHA"):
            XmlSourceEditSession(copy,self.tmp/"bad",
                                 experimental_original_legacy_v08=True)

    def test_15_same_schema_rewritten_IFC_native_bytes_not_implicitly_allowlisted(self):
        src=self.source("geometry_test_04")
        copy=self.tmp/"same_legacy_schema_different_bytes.ifc"
        f=ifcopenshell.open(str(src))
        f.by_type("IfcBuilding")[0].Name="v038_mutated_original_copy"
        f.write(str(copy))
        self.assertEqual(ifcopenshell.open(str(copy)).schema,"IFC2X3")
        self.assertNotEqual(file_hash(src),file_hash(copy))
        with self.assertRaisesRegex(UnsupportedArm,"pinned source SHA"):
            XmlSourceEditSession(copy,self.tmp/"blocked",
                                 experimental_original_legacy_v08=True)
        self.assertEqual(file_hash(src),self.public["geometry_test_04"]["original_ifc_sha256"])

    def test_16_optin_keyword_cannot_be_passed_positionally(self):
        with self.assertRaises(TypeError):
            XmlSourceEditSession(self.source("geometry_test_05"),
                                 self.tmp/"positional",True)

    def test_17_rejects_DTD_XXE_and_does_not_update_session_source_state(self):
        s=self.live("geometry_test_05")
        old=s.current_xml
        bad='<!DOCTYPE Building [<!ENTITY xxe SYSTEM "file:///C:/secret">]><Building>&xxe;</Building>'
        result=s.call("submit_building_xml",{"xml_text":bad})
        self.assertEqual(result["status"],"error")
        self.assertFalse(result["native_ifc_committed"])
        self.assertEqual(s.current_xml,old)
        self.assertIsNone(s.output_ifc)
        self.assertEqual(s.submissions,1)

    def test_18_rejects_original_sourceModelSha256_spoofing(self):
        s=self.live("geometry_test_05")
        root=etree.fromstring(s.current_xml)
        root.set("sourceModelSha256","0"*64)
        result=s.call("submit_building_xml",{
            "xml_text":etree.tostring(root,encoding="unicode")})
        self.assertEqual(result["status"],"error")
        self.assertIsNone(s.output_ifc)
        self.assertEqual(s.current_xml,s.original_xml)

    def test_19_rejects_relabelled_IFC2X3_as_IFC4(self):
        s=self.live("geometry_test_04")
        root=etree.fromstring(s.current_xml)
        root.set("sourceIfcSchema","IFC4")
        result=s.call("submit_building_xml",{
            "xml_text":etree.tostring(root,encoding="unicode")})
        self.assertEqual(result["status"],"error")
        self.assertIsNone(s.output_ifc)

    def test_20_rejects_fabricating_missing_IFC4_storey_elevation(self):
        s=self.live("geometry_test_05")
        root=etree.fromstring(s.current_xml)
        missing=next(x for x in root.findall("./"+Q+"Levels/"+Q+"Level")
                     if x.get("elevationState")=="MISSING")
        missing.set("elevationState","EXPLICIT")
        missing.set("elevation","0")
        result=s.call("submit_building_xml",{
            "xml_text":etree.tostring(root,encoding="unicode")})
        self.assertEqual(result["status"],"error")
        self.assertIsNone(s.output_ifc)

    def test_21_rejects_command_tag_instead_of_declarative_elements(self):
        s=self.live("geometry_test_05")
        root=etree.fromstring(s.current_xml)
        etree.SubElement(root.find(Q+"Elements"),Q+"Create",{"operation":"Wall"})
        result=s.call("submit_building_xml",{
            "xml_text":etree.tostring(root,encoding="unicode")})
        self.assertEqual(result["status"],"error")
        self.assertIsNone(s.output_ifc)

    def test_22_rejects_two_new_ifc4_walls_in_one_bounded_transaction(self):
        s=self.live("geometry_test_05")
        root=etree.fromstring(v038.illustrative_legacy_xml(
            s.current_xml,"geometry_test_05"))
        etree.SubElement(root.find(Q+"Elements"),Q+"Wall",{
            "id":"v038_second_wall","level":root.find(Q+"Levels")[0].get("id"),
            "x1":"0","y1":"0","z1":"0","x2":"2","y2":"0","z2":"0",
            "height":"3","thickness":"0.2"})
        result=s.call("submit_building_xml",{
            "xml_text":etree.tostring(root,encoding="unicode")})
        self.assertEqual(result["status"],"error")
        self.assertIsNone(s.output_ifc)

    def test_23_rejects_unknown_existing_door_host_and_preserves_source(self):
        s=self.live("geometry_test_03")
        original=file_hash(self.source("geometry_test_03"))
        root=etree.fromstring(v038.illustrative_legacy_xml(
            s.current_xml,"geometry_test_03"))
        opening=next(x for x in root.find(Q+"Elements")
                     if x.tag==Q+"Opening")
        opening.set("host","not_an_original_source_wall")
        result=s.call("submit_building_xml",{
            "xml_text":etree.tostring(root,encoding="unicode")})
        self.assertEqual(result["status"],"error")
        self.assertIsNone(s.output_ifc)
        self.assertEqual(file_hash(self.source("geometry_test_03")),original)

    def test_24_failed_revision_after_native_commit_does_not_wipe_last_valid(self):
        s=self.live("geometry_test_05")
        edited=v038.illustrative_legacy_xml(s.current_xml,"geometry_test_05")
        first=s.call("submit_building_xml",{"xml_text":edited.decode("utf8")})
        self.assertEqual(first["status"],"ok")
        original_hash=file_hash(s.output_ifc)
        self.assertEqual(s.current_xml,edited)
        error=s.call("submit_building_xml",{"xml_text":"<wrong>"})
        self.assertEqual(error["status"],"error")
        self.assertEqual(s.current_xml,edited)
        self.assertTrue(s.output_ifc.is_file())
        self.assertEqual(file_hash(s.output_ifc),original_hash)
        self.assertEqual(s.submissions,2)
        self.assertTrue(s.call("read_building_xml",{})["native_candidate_available"])

    def test_25_original_source_class_tamper_in_output_detected_after_commit(self):
        s=self.live("geometry_test_04")
        edited=v038.illustrative_legacy_xml(s.current_xml,"geometry_test_04")
        result=s.call("submit_building_xml",{"xml_text":edited.decode("utf8")})
        self.assertEqual(result["status"],"ok")
        altered=self.tmp/"tampered_native_mm.ifc"
        model=ifcopenshell.open(str(s.output_ifc))
        col=model.by_type("IfcColumn")[0]
        col.Name="v038_tampered_original_column"
        model.write(str(altered))
        with self.assertRaisesRegex(LegacyLiveGateError,"identity/name/description"):
            verify_native_original_restored(self.source("geometry_test_04"),
                                            altered,task_id="geometry_test_04",
                                            expected_schema="IFC2X3")

    def test_26_original_source_Wall_physical_move_in_output_rejected(self):
        s=self.live("geometry_test_04")
        edited=v038.illustrative_legacy_xml(s.current_xml,"geometry_test_04")
        result=s.call("submit_building_xml",{"xml_text":edited.decode("utf8")})
        self.assertEqual(result["status"],"ok")
        altered=self.tmp/"changed_original_wall_native_mm.ifc"
        model=ifcopenshell.open(str(s.output_ifc))
        wall=model.by_type("IfcWallStandardCase")[0]
        placement=wall.ObjectPlacement.RelativePlacement
        loc=placement.Location
        coords=list(loc.Coordinates)
        coords[0]+=1000.
        loc.Coordinates=tuple(coords)
        model.write(str(altered))
        with self.assertRaisesRegex(
                LegacyLiveGateError,"world vertices or physical planar faces"):
            verify_native_original_restored(
                self.source("geometry_test_04"),altered,
                task_id="geometry_test_04",expected_schema="IFC2X3")

    def test_27_source_schema_tamper_in_restored_output_rejected(self):
        s=self.live("geometry_test_05")
        edited=v038.illustrative_legacy_xml(s.current_xml,"geometry_test_05")
        result=s.call("submit_building_xml",{"xml_text":edited.decode("utf8")})
        self.assertEqual(result["status"],"ok")
        with self.assertRaisesRegex(LegacyLiveGateError,"schema"):
            verify_native_original_restored(
                self.source("geometry_test_05"),s.output_ifc,
                task_id="geometry_test_05",expected_schema="IFC2X3")

    def test_28_original_input_not_changed_across_any_pinned_task(self):
        for tid in v038.TASKS:
            self.assertEqual(file_hash(self.source(tid)),
                             self.public[tid]["original_ifc_sha256"])
            self.assertTrue(self.rows[tid]["input_native_source_unchanged"])

    def test_29_source_question_drift_in_prior_frozen_metadata_fails_closed(self):
        source=dict(self.public["geometry_test_03"])
        source["public_question_sha256"]="0"*64
        tasks=[dict(self.public[k]) for k in sorted(self.public)]
        ix=next(i for i,x in enumerate(tasks) if x["test_id"]=="geometry_test_03")
        tasks[ix]=source
        with patch.object(v038,"public_45",return_value=tasks):
            with self.assertRaisesRegex(v038.V038EvidenceDrift,"source/question"):
                v038.original_inputs(v038.ROOT,AUTHOR,DATA)

    def test_30_duplicate_public_task_denominator_fails_closed(self):
        tasks=[dict(self.public[k]) for k in sorted(self.public)]
        tasks[0]["test_id"]=tasks[1]["test_id"]
        with patch.object(v038,"public_45",return_value=tasks):
            with self.assertRaisesRegex(v038.V038EvidenceDrift,"45 task"):
                v038.original_inputs(v038.ROOT,AUTHOR,DATA)

    def test_31_no_embedded_scorer_or_hidden_GT_in_research_host_adapter(self):
        for p in (Path(v038.__file__),
                  Path(__import__(
                    "tools.bibimbap_v038_legacy_live_gate",
                    fromlist=["x"]).__file__)):
            text=p.read_text(encoding="utf8")
            modules=[]
            for n in ast.walk(ast.parse(text)):
                if isinstance(n,ast.Import):
                    modules.extend(a.name for a in n.names)
                elif isinstance(n,ast.ImportFrom):
                    modules.append(n.module or "")
            for bad in ("openai","bibimbap_author_worker","DockerIFCExecutor",
                        "torch","requests","subprocess"):
                self.assertFalse(any(bad in name for name in modules))
            self.assertNotIn("grade_author(",text)
            self.assertNotIn("execute_ifc_code(",text)

    def test_32_atomic_frozen_evidence_is_write_once(self):
        with self.assertRaises(FileExistsError):
            with REPORT.open("xb") as f:
                f.write(b"forbidden")
        self.assertEqual(file_hash(REPORT),FROZEN_SHA)

    def test_33_actually_replays_three_native_optin_tool_sessions_same_bytes(self):
        r=v038.audit(v038.ROOT,AUTHOR,DATA)
        raw=(json.dumps(r,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(raw,REPORT.read_bytes())
        self.assertEqual(len(r["rows"]),3)
        self.assertEqual([x["task_id"] for x in r["rows"]],list(v038.TASKS))

    def test_34_report_does_not_contain_raw_original_IFC_or_model_response(self):
        text=REPORT.read_text(encoding="utf8")
        self.assertNotIn("raw_IFC_bytes",text)
        self.assertNotIn("private_ground_truth",text)
        self.assertNotIn("provider_response",text)
        self.assertNotIn("API_KEY",text)
        self.assertLess(len(text),24000)

    def test_35_model_HOST_does_not_reinterpret_same_original_input_as_ifc4x3(self):
        for tid in v038.TASKS:
            row=self.rows[tid]
            self.assertEqual(row["original_native_schema"],
                             v038.EXPECTED_IFC_CLASSES[tid][0])
            self.assertNotEqual(row["original_native_schema"],"IFC4X3")
            self.assertTrue(row["native_source_restored_oracle"][
                "source_original_units_and_schema_preserved"])

    def test_36_restored_new_product_missing_native_geometry_rejected(self):
        s=self.live("geometry_test_05")
        edited=v038.illustrative_legacy_xml(s.current_xml,"geometry_test_05")
        result=s.call("submit_building_xml",{"xml_text":edited.decode("utf8")})
        self.assertEqual(result["status"],"ok")
        altered=self.tmp/"new_wall_without_geometry.ifc"
        model=ifcopenshell.open(str(s.output_ifc))
        original_guids={x.GlobalId for x in ifcopenshell.open(
            str(self.source("geometry_test_05"))).by_type("IfcRoot")}
        added=[x for x in model.by_type("IfcWall") if x.GlobalId not in original_guids]
        self.assertEqual(len(added),1)
        added[0].Representation=None
        model.write(str(altered))
        with self.assertRaisesRegex(LegacyLiveGateError,"physical representation missing"):
            verify_native_original_restored(self.source("geometry_test_05"),
                                            altered,task_id="geometry_test_05",
                                            expected_schema="IFC4")


if __name__=="__main__":
    unittest.main()
