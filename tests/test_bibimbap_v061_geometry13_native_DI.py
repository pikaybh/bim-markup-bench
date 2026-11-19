"""v0.61 original IFC4X3 Window/hosted Opening/three Proxy native tests.

63 focused source SHA, XML whole-state, physical native scope/schema,
genuine independent Docker report attestation and security/rollback tests.
This module never calls a model or sends original IFC to any provider.
Original author evaluator stays strictly in evaluator-only audit.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main
from unittest.mock import patch
import json

import ifcopenshell
from lxml import etree

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import DockerIFCExecutor,file_hash
from tools import audit_bibimbap_v061_geometry13_native_DI as audit
from tools.bibimbap_v061_geometry13_native import (
    SOURCE_SHA,TASK,MAX_CALLS,
    Geometry13Native061Error,_source,_mesh_bounds,
    original_assembly_groups_v061,full_source_final_state_v061,
    compact_complete_final_state_v061,
    parse_complete_final_state_v061,
    restore_compact_final_state_v061,
    compile_group_move_v061,independent_assembly_world_scope_v061,
    semantic_digest_after_native_oracle_v061,
)
from tools.bibimbap_v061_geometry13_sessions import (
    DirectFullState061,DirectManagedState061,LiveDockerPython061,
)
from tools.bibimbap_v057_provenance import (
    ProviderTrialBlocked057,refuse_all_model_trials_v057,
)

FROZEN_REPORT_SHA="a620f6a6ac6ed164d1bbf0eec56ca84d117233fcefa0303d8d732c0a648314c3"


class OriginalMoveWindowDIPaired061(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(audit.REPORT.read_text(encoding="utf8"))
        cls.row=next(x for x in public_45(audit.AUTHOR,audit.DATA)
                     if x["test_id"]==TASK)
        cls.source=audit.DATA/"ifc"/cls.row["original_source_ifc_relpath"]
        cls.initial=full_source_final_state_v061(cls.source,source_sha=SOURCE_SHA)
        cls.managed=compact_complete_final_state_v061(
            cls.source,source_sha=SOURCE_SHA)
        cls.original=_source(cls.source,source_sha=SOURCE_SHA)
        cls.groups=original_assembly_groups_v061(cls.original)
        cls.keys=sorted(cls.groups)
        cls.correct=next(k for k,g in cls.groups.items() if
                         g["source_window_bbox"][0][1]-
                         g["source_window_bbox"][0][0]>1.5)
        cls.incorrect=next(k for k in cls.groups if k!=cls.correct)

    def setUp(self):
        self.temp=TemporaryDirectory(prefix="v061-original-window-")
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)

    def d(self):
        return DirectFullState061(self.source,self.folder/"D")

    def m(self):
        return DirectManagedState061(self.source,self.folder/"M")

    def i(self):
        return LiveDockerPython061(self.source,self.folder/"I")

    def full(self,guid=None,dx=3.):
        return audit._full_submit(
            self.initial,self.groups[guid or self.correct],dx)

    def compact(self,guid=None,dx=3.):
        return audit._managed_submit(
            self.managed,self.groups[guid or self.correct],dx)

    def bad_full(self,value):
        with self.assertRaises(Exception):
            parse_complete_final_state_v061(
                self.source,value.encode("utf8"),source_sha=SOURCE_SHA)

    def bad_compact(self,value):
        with self.assertRaises(Exception):
            restore_compact_final_state_v061(
                self.source,value.encode("utf8"),source_sha=SOURCE_SHA)

    def write_candidate(self,target,filename="edit.ifc"):
        p=self.folder/filename
        compile_group_move_v061(
            self.source,p,source_sha=SOURCE_SHA,target=target)
        return p

    def test_01_frozen_real_Docker_report_checksum(self):
        self.assertEqual(file_hash(audit.REPORT),FROZEN_REPORT_SHA)

    def test_02_report_canonical_full_bytes(self):
        self.assertEqual(audit.REPORT.read_bytes(),
                         audit.canonical(self.report))

    def test_03_prior_v060_report_exact_SHA(self):
        self.assertEqual(file_hash(audit.PARENT),audit.PARENT_SHA)

    def test_04_prior_v058_selection_exact_SHA(self):
        self.assertEqual(file_hash(audit.FROZEN),audit.FROZEN_SHA)

    def test_05_six_original_source_tasks_still_fixed(self):
        self.assertEqual(self.report[
            "original_v058_six_task_selection_unchanged"],audit.HOLDOUT)

    def test_06_new_native_task_only_geometry13(self):
        self.assertEqual(self.report[
            "new_original_native_task_supported_in_v061"],[TASK])

    def test_07_three_of_six_supported_and_three_explicitly_blocked(self):
        self.assertEqual(self.report[
            "all_three_current_v058_selected_source_native_developer_supported"],
            sorted(audit.SUPPORTED))
        self.assertEqual(self.report[
            "remaining_original_six_source_tasks_not_admitted"],
            sorted(set(audit.HOLDOUT)-audit.SUPPORTED))

    def test_08_total_original_45_31_source_cluster_population(self):
        self.assertEqual(self.report["original_public_task_count"],45)
        self.assertEqual(self.report[
            "original_unique_IFC_input_SHA_cluster_count"],31)

    def test_09_source_original_SHA_independent(self):
        self.assertEqual(file_hash(self.source),SOURCE_SHA)
        self.assertEqual(self.row["original_ifc_sha256"],SOURCE_SHA)

    def test_10_schema_IFC4X3_original_source_native_mm(self):
        self.assertEqual(self.original.schema,"IFC4X3")
        self.assertEqual(self.report[
            "original_IFC_length_unit_native_mm_WORLD_geometry_m"],True)

    def test_11_source_two_windows_two_openings_six_proxies_one_wall(self):
        self.assertEqual(len(self.original.by_type("IfcWindow")),2)
        self.assertEqual(len(self.original.by_type("IfcOpeningElement")),2)
        self.assertEqual(len(self.original.by_type("IfcBuildingElementProxy")),6)
        self.assertEqual(len(self.original.by_type("IfcWall")),1)

    def test_12_source_native_window_width_source_mesh_0_6_1_6(self):
        self.assertEqual(sorted(round(g["source_window_bbox"][0][1]-
                           g["source_window_bbox"][0][0],2)
                            for g in self.groups.values()),[.6,1.6])

    def test_13_source_only_correct_width_predicate_one_of_two(self):
        scores=audit.public_source_width_predicate_only_v061(
            self.source,self.row["public_question"])
        self.assertEqual(Counter(scores.values()),{True:1,False:1})
        self.assertTrue(scores[self.correct])
        self.assertFalse(scores[self.incorrect])

    def test_14_original_window_local_origin_is_shared(self):
        points=[g["window"].ObjectPlacement.RelativePlacement.Location
                for g in self.groups.values()]
        self.assertEqual(points[0].id(),points[1].id())
        self.assertEqual(len(self.original.get_inverse(points[0])),30)

    def test_15_exact_two_disjoint_five_product_assembly_groups(self):
        self.assertEqual(len(self.groups),2)
        self.assertEqual(len({p.GlobalId for g in self.groups.values()
                              for p in g["members"]}),10)
        self.assertEqual([len(g["members"]) for g in self.groups.values()],[5,5])

    def test_16_each_assembly_four_unique_exclusive_placement_points(self):
        for g in self.groups.values():
            self.assertEqual(len({p.id() for p in g["placement_points"]}),4)
            self.assertTrue(all(len(self.original.get_inverse(p))==1
                                for p in g["placement_points"]))

    def test_17_source_XML_initial_D_full_D_managed_I_exact_parity(self):
        D,M,I=self.d(),self.m(),self.i()
        reads=[x.call("read_building_xml",{"query":"source"}) for x in (D,M,I)]
        self.assertEqual([r["status"] for r in reads],["ok"]*3)
        self.assertEqual(reads[0]["xml"],reads[1]["xml"])
        self.assertEqual(reads[1]["xml"],reads[2]["xml"])
        self.assertEqual(reads[0]["xml"].encode("utf8"),self.initial)

    def test_18_source_full_XML_bytes_4947(self):
        self.assertEqual(len(self.initial),4947)
        self.assertEqual(self.report[
            "source_full_original_BuildingState_UTF8_bytes"],4947)

    def test_19_source_complete_managed_initial_XML_bytes_1437(self):
        self.assertEqual(len(self.managed),1437)
        self.assertEqual(self.report[
            "source_compact_original_complete_managed_UTF8_bytes"],1437)

    def test_20_full_declarative_has_all_ten_source_products(self):
        state=etree.fromstring(self.initial)
        self.assertEqual(len(state[1]),10)
        self.assertEqual(len({x.get("ifcGuid") for x in state[1]}),10)

    def test_21_compact_complete_roster_has_ten(self):
        state=etree.fromstring(self.managed)
        self.assertEqual(len(state),10)
        self.assertEqual(len({x.get("ifcGuid") for x in state}),10)

    def test_22_native_full_managed_python_distinct_tool_schemas(self):
        D,M,I=self.d(),self.m(),self.i()
        self.assertEqual(D.tools[0],M.tools[0])
        self.assertEqual(M.tools[0],I.tools[0])
        self.assertEqual([D.tools[1]["name"],M.tools[1]["name"],
                          I.tools[1]["name"]],[
            "submit_building_xml","submit_managed_final_state",
            "execute_ifc_code"])

    def test_23_I_exact_genuine_DockerIFCExecutor(self):
        self.assertIs(type(self.i().executor),DockerIFCExecutor)

    def test_24_D_full_actual_native_IFC_movement_and_schema(self):
        D=self.d()
        r=D.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(r["status"],"ok")
        self.assertEqual(r["source_world_X_shift_metres_magnitude"],3.)
        self.assertEqual(r["introduced_IFC_schema_errors"],0)
        self.assertEqual(file_hash(D.output_ifc),r["native_ifc_sha256"])

    def test_25_D_managed_actual_native_IFC_movement_and_schema(self):
        M=self.m()
        r=M.call("submit_managed_final_state",
                 {"xml_text":self.compact()})
        self.assertEqual(r["status"],"ok")
        self.assertEqual(r["source_world_X_shift_metres_magnitude"],3.)
        self.assertEqual(r["introduced_IFC_schema_errors"],0)

    def test_26_D_full_and_managed_reconstruct_identical_final_XML(self):
        D,M=self.d(),self.m()
        self.assertEqual(D.call("submit_building_xml",
            {"xml_text":self.full()})["status"],"ok")
        self.assertEqual(M.call("submit_managed_final_state",
            {"xml_text":self.compact()})["status"],"ok")
        self.assertEqual(D.current_xml,M.current_xml)

    def test_27_D_full_and_managed_semantic_SHA_after_native_gate(self):
        D,M=self.d(),self.m()
        self.assertEqual(D.call("submit_building_xml",
            {"xml_text":self.full()})["status"],"ok")
        self.assertEqual(M.call("submit_managed_final_state",
            {"xml_text":self.compact()})["status"],"ok")
        self.assertEqual(
            semantic_digest_after_native_oracle_v061(D.output_ifc),
            semantic_digest_after_native_oracle_v061(M.output_ifc))

    def test_28_complete_managed_reconstruct_exact_bytes(self):
        full,target=restore_compact_final_state_v061(
            self.source,self.compact().encode("utf8"),source_sha=SOURCE_SHA)
        self.assertEqual(full,self.full().encode("utf8"))
        self.assertEqual(target,(self.correct,3.))

    def test_29_wrong_source_narrow_window_still_structure_admitted(self):
        cand=self.write_candidate((self.incorrect,3.))
        result=independent_assembly_world_scope_v061(
            self.source,cand,source_sha=SOURCE_SHA)
        self.assertEqual(result[
            "five_physical_products_world_X_moved"],5)
        self.assertEqual(result["original_IfcOpenShell_schema_errors_introduced"],0)

    def test_30_wrong_distance_2m_still_structure_admitted(self):
        cand=self.write_candidate((self.correct,2.))
        result=independent_assembly_world_scope_v061(
            self.source,cand,source_sha=SOURCE_SHA)
        self.assertEqual(result["source_X_delta_magnitude"],2.)
        self.assertEqual(result["original_IfcOpenShell_schema_errors_introduced"],0)

    def test_31_good_native_3m_source_Wide_physically_moved(self):
        cand=self.write_candidate((self.correct,3.))
        result=independent_assembly_world_scope_v061(
            self.source,cand,source_sha=SOURCE_SHA)
        self.assertEqual(result["source_x_direction"],"POSITIVE")
        self.assertEqual(result["source_X_delta_magnitude"],3.)
        self.assertEqual(result["native_four_placement_points_moved"],4)

    def test_32_three_real_Linux_Docker_I_controls_in_audit(self):
        cases=self.report["three_original_source_developer_controls"]
        self.assertEqual(len(cases),3)
        self.assertEqual(self.report[
            "actual_original_native_IFC_genuine_Docker_python_cases"],3)
        self.assertTrue(all(x["actual_genuine_Docker_code_executed"]
                            for x in cases))

    def test_33_nine_genuine_real_IFC_D_M_I_developer_controls(self):
        self.assertEqual(self.report[
            "total_native_original_IFC_successful_developer_controls"],9)
        self.assertEqual(self.report["actual_original_native_IFC_D_FULL_cases"],3)
        self.assertEqual(self.report["actual_original_native_IFC_D_MANAGED_cases"],3)

    def test_34_original_author_repo_correct_score_1_0(self):
        grade=self.report["three_original_source_developer_controls"][0][
            "original_author_repository_metric_evaluator_only"]
        self.assertEqual(grade["status"],
                         "EVALUATOR_RETURNED_BOOLEAN_METRICS")
        self.assertEqual(grade["author_repository_mean_boolean_score"],1.0)
        self.assertTrue(all(grade["author_repository_boolean_metrics"].values()))

    def test_35_original_author_repo_two_wrong_scores_one_third(self):
        for case in self.report["three_original_source_developer_controls"][1:]:
            grade=case["original_author_repository_metric_evaluator_only"]
            self.assertEqual(grade["status"],
                             "EVALUATOR_RETURNED_BOOLEAN_METRICS")
            self.assertEqual(grade["author_repository_mean_boolean_score"],.333333)
            self.assertFalse(grade["author_repository_boolean_metrics"][
                "right_location"])

    def test_36_original_author_score_not_official_paper_equivalence(self):
        self.assertTrue(all(
            c["original_author_repository_metric_evaluator_only"][
                "official_paper_grader_revision_verified"] is False
            for c in self.report["three_original_source_developer_controls"]))
        self.assertIsNone(self.report["published_paper_official_model_score"])

    def test_37_developer_target_GUIDs_redacted_from_report(self):
        raw=audit.REPORT.read_text(encoding="utf8")
        for original_window_GUID in self.keys:
            self.assertNotIn(original_window_GUID,raw)
        self.assertTrue(all(
            x["target_original_window_GUID_redacted"] is True
            for x in self.report["three_original_source_developer_controls"]))

    def test_38_all_D_I_semantic_digests_equal_for_each_case(self):
        cases=self.report["three_original_source_developer_controls"]
        self.assertEqual(len({
            c["source_native_IFC_semantic_SHA256_all_D_and_I"]
            for c in cases
        }),3)
        self.assertTrue(self.report[
            "D_I_normalized_native_semantic_digests_match_each_case"])

    def test_39_model_generated_and_paid_provider_zero(self):
        self.assertEqual(self.report["actual_LLM_generated_trial_count"],0)
        self.assertEqual(self.report["paid_model_provider_calls"],0)
        self.assertEqual(self.report["original_IFC_provider_upload_count"],0)

    def test_40_unchanged_full_source_noop_rejected(self):
        self.bad_full(self.initial.decode("utf8"))

    def test_41_unchanged_complete_managed_noop_rejected(self):
        self.bad_compact(self.managed.decode("utf8"))

    def test_42_incomplete_full_ten_element_roster_rejected(self):
        node=etree.fromstring(self.full().encode())
        node[1].remove(node[1][0])
        self.bad_full(etree.tostring(node).decode())

    def test_43_incomplete_compact_roster_rejected(self):
        node=etree.fromstring(self.compact().encode())
        node.remove(node[0])
        self.bad_compact(etree.tostring(node).decode())

    def test_44_wrong_or_duplicate_GUID_in_full_rejected(self):
        node=etree.fromstring(self.full().encode())
        node[1][0].set("ifcGuid","0"*22)
        self.bad_full(etree.tostring(node).decode())
        node=etree.fromstring(self.full().encode())
        node[1][0].set("ifcGuid",node[1][1].get("ifcGuid"))
        self.bad_full(etree.tostring(node).decode())

    def test_45_reordered_compact_full_roster_rejected(self):
        node=etree.fromstring(self.compact().encode())
        node.insert(0,node[-1])
        self.bad_compact(etree.tostring(node).decode())

    def test_46_original_source_IFC_SHA_spoof_rejected(self):
        node=etree.fromstring(self.full().encode())
        node.set("sourceOriginalIFCSha256","f"*64)
        self.bad_full(etree.tostring(node).decode())

    def test_47_compact_full_source_XML_SHA_spoof_rejected(self):
        node=etree.fromstring(self.compact().encode())
        node.set("sourceFullBuildingStateSha256","f"*64)
        self.bad_compact(etree.tostring(node).decode())

    def test_48_immutable_native_original_Product_host_rewrite_refused(self):
        node=etree.fromstring(self.full().encode())
        window=next(e for e in node[0][0]
                    if e.get("ifcClass")=="IfcWindow")
        window.set("sourceHostedOpeningGuid","0"*22)
        self.bad_full(etree.tostring(node).decode())

    def test_49_immutable_source_native_world_mesh_X_modification_refused(self):
        node=etree.fromstring(self.full().encode())
        entity=next(e for e in node[0][0] if e.get("minXM"))
        entity.set("minXM","123.000000")
        self.bad_full(etree.tostring(node).decode())

    def test_50_only_one_assembly_can_move_in_full_state(self):
        node=etree.fromstring(self.full().encode())
        other={p.GlobalId for p in self.groups[self.incorrect]["members"]}
        for entry in node[1]:
            if entry.get("ifcGuid") in other:
                entry.set("finalWorldMinXM",f"{float(entry.get('finalWorldMinXM'))+3.:.6f}")
        self.bad_full(etree.tostring(node).decode())

    def test_51_all_five_assembly_elements_must_move_same_delta(self):
        node=etree.fromstring(self.full().encode())
        one=next(p.GlobalId for p in self.groups[self.correct]["members"]
                 if p.is_a()=="IfcBuildingElementProxy")
        for entry in node[1]:
            if entry.get("ifcGuid")==one:
                entry.set("finalWorldMinXM",f"{float(entry.get('finalWorldMinXM'))-3.:.6f}")
        self.bad_full(etree.tostring(node).decode())

    def test_52_wrong_native_3000_metre_instead_of_mm_move_refused(self):
        with self.assertRaises(Geometry13Native061Error):
            self.write_candidate((self.correct,3000.))

    def test_53_negative_3000_mm_opposite_direction_source_structurally_admitted(self):
        cand=self.write_candidate((self.correct,-3.))
        result=independent_assembly_world_scope_v061(
            self.source,cand,source_sha=SOURCE_SHA)
        self.assertEqual(result["source_x_direction"],"NEGATIVE")
        self.assertEqual(result["source_X_delta_magnitude"],3.)

    def test_54_forged_X_translation_missing_one_proxy_rejected(self):
        f=ifcopenshell.open(str(self.source))
        g=original_assembly_groups_v061(f)[self.correct]
        for point in g["placement_points"][:-1]:
            p=list(point.Coordinates);p[0]+=3000;point.Coordinates=tuple(p)
        out=self.folder/"proxy_missing.ifc"
        f.write(str(out))
        with self.assertRaises(Geometry13Native061Error):
            independent_assembly_world_scope_v061(
                self.source,out,source_sha=SOURCE_SHA)

    def test_55_wrong_original_window_shared_origin_edit_rejected(self):
        f=ifcopenshell.open(str(self.source))
        w=original_assembly_groups_v061(f)[self.correct]["window"]
        point=w.ObjectPlacement.RelativePlacement.Location
        p=list(point.Coordinates);p[0]+=3000;point.Coordinates=tuple(p)
        out=self.folder/"forged_shared_point.ifc";f.write(str(out))
        with self.assertRaises(Geometry13Native061Error):
            independent_assembly_world_scope_v061(
                self.source,out,source_sha=SOURCE_SHA)

    def test_56_off_target_wall_name_changed_rejected(self):
        f=ifcopenshell.open(str(self.source))
        g=original_assembly_groups_v061(f)[self.correct]
        for point in g["placement_points"]:
            p=list(point.Coordinates);p[0]+=3000;point.Coordinates=tuple(p)
        f.by_type("IfcWall")[0].Name="FORGED_WALL_NAME"
        out=self.folder/"forged_wall.ifc";f.write(str(out))
        with self.assertRaises(Geometry13Native061Error):
            independent_assembly_world_scope_v061(
                self.source,out,source_sha=SOURCE_SHA)

    def test_57_off_target_proxy_Y_changed_rejected(self):
        f=ifcopenshell.open(str(self.source))
        g=original_assembly_groups_v061(f)[self.correct]
        for point in g["placement_points"]:
            p=list(point.Coordinates);p[0]+=3000;point.Coordinates=tuple(p)
        point=g["placement_points"][1]
        xyz=list(point.Coordinates);xyz[1]+=100.;point.Coordinates=tuple(xyz)
        out=self.folder/"forged_proxy_Y.ifc";f.write(str(out))
        with self.assertRaises(Geometry13Native061Error):
            independent_assembly_world_scope_v061(
                self.source,out,source_sha=SOURCE_SHA)

    def test_58_do_not_modify_source_as_its_own_candidate(self):
        with self.assertRaises(Geometry13Native061Error):
            independent_assembly_world_scope_v061(
                self.source,self.source,source_sha=SOURCE_SHA)

    def test_59_XXE_DTD_in_final_state_refused(self):
        b=self.full().encode("utf8")
        dtd=(b"<!DOCTYPE BuildingState ["
             b"<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>")
        self.bad_full(b.replace(b"?>",b"?>"+dtd,1).decode("utf8"))

    def test_60_D_native_last_good_state_rollback_on_bad_xml(self):
        D=self.d()
        good=D.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(good["status"],"ok")
        origsha=file_hash(D.output_ifc);oldxml=D.current_xml
        wrong=D.call("submit_building_xml",{"xml_text":"<wrong/>"})
        self.assertEqual(wrong["status"],"error")
        self.assertEqual(file_hash(D.output_ifc),origsha)
        self.assertEqual(D.current_xml,oldxml)

    def test_61_D_managed_last_good_state_rollback_on_bad_xml(self):
        M=self.m()
        good=M.call("submit_managed_final_state",
                    {"xml_text":self.compact()})
        self.assertEqual(good["status"],"ok")
        origsha=file_hash(M.output_ifc);oldxml=M.current_xml
        wrong=M.call("submit_managed_final_state",{"xml_text":"<wrong/>"})
        self.assertEqual(wrong["status"],"error")
        self.assertEqual(file_hash(M.output_ifc),origsha)
        self.assertEqual(M.current_xml,oldxml)

    def test_62_strict_25_total_tool_calls_all_three_arms(self):
        D,M,I=self.d(),self.m(),self.i()
        for s in (D,M,I):
            for _ in range(MAX_CALLS):
                self.assertEqual(s.call("read_building_xml",
                    {"query":"source"})["status"],"ok")
            self.assertEqual(s.call("read_building_xml",
                {"query":"source"})["error_type"],"ToolBudgetExhausted")

    def test_63_wrong_D_tool_cannot_bypass_compact(self):
        M=self.m()
        r=M.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(r["error_type"],"WrongDeclarativeTool")

    def test_64_D_whole_state_replay_idempotent_rejected(self):
        D=self.d()
        self.assertEqual(D.call("submit_building_xml",
            {"xml_text":self.full()})["status"],"ok")
        native_sha=file_hash(D.output_ifc)
        r=D.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(r["error_type"],"IdenticalStateReplayRejected")
        self.assertEqual(file_hash(D.output_ifc),native_sha)

    def test_65_fake_Docker_preflight_blocks_execution(self):
        I=self.i()
        with patch("tools.bibimbap_v061_geometry13_sessions.live_pinned_local_runtime_admission_v052",
                   return_value={"status":"BLOCKED_RUNTIME",
                                 "reason":"NO_LINUX"}),patch.object(I.executor,"run") as fake:
            r=I.call("execute_ifc_code",{"code":"commit()"})
        self.assertEqual(r["error_type"],"BLOCKED_RUNTIME")
        self.assertIsNone(I.output_ifc)
        fake.assert_not_called()

    def test_66_fake_Docker_attestation_without_native_edit_refused(self):
        I=self.i()
        with patch("tools.bibimbap_v061_geometry13_sessions.live_pinned_local_runtime_admission_v052",
                   return_value={"status":"RUNTIME_ADMITTED"}),patch.object(
                       I.executor,"run",return_value={
                           "status":"ok","committed":True,
                           "backend":"linux_docker_sandbox"}):
            result=I.call("execute_ifc_code",{"code":"commit()"})
        self.assertEqual(result["error_type"],"NativeWorkerOrScopeRejected")
        self.assertIsNone(I.output_ifc)

    def test_67_actual_Docker_opening_without_proxies_refused_in_audit(self):
        self.assertTrue(self.report[
            "genuine_Docker_opening_only_missing_proxies_rejected"])

    def test_68_actual_Docker_good_then_wrong_last_IFC_safe_in_audit(self):
        self.assertTrue(self.report[
            "genuine_Docker_good_then_invalid_second_group_last_IFC_preserved"])

    def test_69_original_author_grader_not_exposed_to_model_host(self):
        for name in ("bibimbap_v061_geometry13_native.py",
                     "bibimbap_v061_geometry13_sessions.py"):
            content=(audit.ROOT/"tools"/name).read_text(encoding="utf8")
            for forbidden in ("from data.tests","import data.tests",
                              "import openai","import anthropic",
                              "public_source_width_predicate_only_v061",
                              "original_author_repository_evaluator_only"):
                self.assertNotIn(forbidden,content)

    def test_70_no_launch_even_all_fake_permissions(self):
        with self.assertRaises(ProviderTrialBlocked057):
            refuse_all_model_trials_v057({
                "model":True,"budget":True,"rights":True,"approval":True})
        self.assertEqual(self.report["paid_model_provider_calls"],0)

    def test_71_source_original_provider_rights_not_assumed(self):
        self.assertFalse(self.report[
            "approved_original_underlying_IFC_owner_permission_and_provider_transfer"])
        self.assertIsNone(self.report[
            "approved_paid_model_snapshot_budget_protocol"])

    def test_72_frozen_report_is_exclusive_create(self):
        with self.assertRaises(FileExistsError):
            with audit.REPORT.open("xb"):
                pass


if __name__=="__main__":
    main()
