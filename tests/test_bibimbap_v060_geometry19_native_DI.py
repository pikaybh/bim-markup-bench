"""v0.60 first original 2-window hosted-opening D/I native hardening.

Real pinned Docker executions and separately isolated original-author grader
errors are replayed via the immutable v0.60 --check audit. Focused tests
never call a paid/remote model or modify original IFC / grader / GT.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main
from unittest.mock import patch
import json

import ifcopenshell
import ifcopenshell.api
from lxml import etree

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash,DockerIFCExecutor
from tools import audit_bibimbap_v060_geometry19_native_DI as audit
from tools.bibimbap_v060_geometry19_native import (
    SOURCE_SHA,TASK,MAX_CALLS,
    Geometry19Native060Error,
    _source,source_full_state_v060,compact_source_state_v060,
    parse_full_final_state_v060,restore_compact_final_state_v060,
    compile_two_window_removal_v060,
    independent_two_window_native_scope_v060,
    canonical_original_native_semantic_digest_v060,
)
from tools.bibimbap_v060_geometry19_sessions import (
    DirectFullState060,DirectManagedState060,LiveDockerPython060,
)
from tools.bibimbap_v057_provenance import (
    refuse_all_model_trials_v057,ProviderTrialBlocked057,
)


FROZEN_SHA="e40204f381ccd17876708dd861c7031c1836cc41b7335e49909e797647f042ae"


class OriginalWindowOpeningDIPaired060(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(audit.REPORT.read_text(encoding="utf8"))
        cls.row=next(r for r in public_45(audit.AUTHOR,audit.DATA)
                     if r["test_id"]==TASK)
        cls.source=audit.DATA/"ifc"/cls.row["original_source_ifc_relpath"]
        cls.initial=source_full_state_v060(cls.source,source_sha=SOURCE_SHA)
        cls.managed=compact_source_state_v060(cls.source,source_sha=SOURCE_SHA)
        cls.guids=sorted(x.GlobalId for x in
                         ifcopenshell.open(str(cls.source)).by_type("IfcWindow"))

    def setUp(self):
        self.temp=TemporaryDirectory(prefix="v060-focus-")
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)

    def d(self):
        return DirectFullState060(self.source,self.folder/"D")

    def m(self):
        return DirectManagedState060(self.source,self.folder/"M")

    def i(self):
        return LiveDockerPython060(self.source,self.folder/"I")

    def full(self,indices=(0,1)):
        node=etree.fromstring(self.initial)
        for index in indices:
            node[1][index].set("present","false")
        return etree.tostring(node,encoding="utf8",xml_declaration=True).decode()

    def compact(self,indices=(0,1)):
        node=etree.fromstring(self.managed)
        for index in indices:
            node[index].set("present","false")
        return etree.tostring(node,encoding="utf8",xml_declaration=True).decode()

    def bad_full(self,xml):
        with self.assertRaises(Exception):
            parse_full_final_state_v060(
                self.source,xml.encode("utf8"),source_sha=SOURCE_SHA)

    def bad_compact(self,xml):
        with self.assertRaises(Exception):
            restore_compact_final_state_v060(
                self.source,xml.encode("utf8"),source_sha=SOURCE_SHA)

    def test_01_frozen_semantic_report_sha(self):
        self.assertEqual(file_hash(audit.REPORT),FROZEN_SHA)

    def test_02_canonical_frozen_report_exact_bytes(self):
        self.assertEqual(audit.canonical(self.report),audit.REPORT.read_bytes())

    def test_03_prior_v059_immutable(self):
        self.assertEqual(file_hash(audit.PARENT_REPORT),audit.PARENT_REPORT_SHA)

    def test_04_prior_v058_holdout_immutable(self):
        self.assertEqual(file_hash(audit.PREV_HOLDOUT),audit.PREV_HOLDOUT_SHA)

    def test_05_frozen_six_task_selection_unchanged(self):
        self.assertEqual(self.report["fixed_six_original_source_tasks_unchanged"],
                         audit.FIXED_HOLDOUT)

    def test_06_new_native_task_only_geometry19(self):
        self.assertEqual(self.report["v060_new_original_source_native_task_added"],
                         [TASK])

    def test_07_other_four_original_holdout_tasks_unsupported(self):
        self.assertEqual(
            self.report["remaining_six_source_tasks_not_yet_native_admitted"],
            sorted(set(audit.FIXED_HOLDOUT)-audit.CURRENT_ADMITTED))
        self.assertEqual(len(self.report[
            "remaining_six_source_tasks_not_yet_native_admitted"]),4)

    def test_08_exact_original_IFC_sha_and_schema(self):
        self.assertEqual(file_hash(self.source),SOURCE_SHA)
        self.assertEqual(ifcopenshell.open(str(self.source)).schema,"IFC4X3")

    def test_09_original_seven_windows_seven_openings_eight_walls(self):
        f=_source(self.source,source_sha=SOURCE_SHA)
        self.assertEqual(
            (len(f.by_type("IfcWindow")),
             len(f.by_type("IfcOpeningElement")),
             len(f.by_type("IfcWall"))),(7,7,8))

    def test_10_each_original_window_has_unique_host_opening(self):
        f=_source(self.source,source_sha=SOURCE_SHA)
        self.assertEqual(len({
            w.FillsVoids[0].RelatingOpeningElement.GlobalId
            for w in f.by_type("IfcWindow")}),7)

    def test_11_original_source_read_parity_three_actual_sessions(self):
        sessions=(self.d(),self.m(),self.i())
        values=[s.call("read_building_xml",{"query":"source"}) for s in sessions]
        self.assertTrue(all(v["status"]=="ok" for v in values))
        self.assertTrue(all(v["xml"]==values[0]["xml"] for v in values))
        self.assertEqual(values[0]["xml"].encode("utf8"),self.initial)

    def test_12_full_source_xml_and_compact_sizes(self):
        self.assertEqual(len(self.initial),7433)
        self.assertEqual(len(self.managed),808)

    def test_13_complete_original_seven_roster_order(self):
        root=etree.fromstring(self.initial)
        self.assertEqual([x.get("ifcGuid") for x in root[1]],self.guids)
        self.assertTrue(all(x.get("present")=="true" for x in root[1]))

    def test_14_compact_all_seven_original_guid_roster(self):
        root=etree.fromstring(self.managed)
        self.assertEqual([x.get("ifcGuid") for x in root],self.guids)
        self.assertTrue(all(x.get("present")=="true" for x in root))

    def test_15_tool_read_schemas_identical_D_I(self):
        d,m,i=self.d(),self.m(),self.i()
        self.assertEqual(d.tools[0],m.tools[0])
        self.assertEqual(m.tools[0],i.tools[0])

    def test_16_D_full_compact_and_python_tools_separate(self):
        self.assertEqual([self.d().tools[1]["name"],self.m().tools[1]["name"],
                          self.i().tools[1]["name"]],
            ["submit_building_xml","submit_managed_final_state","execute_ifc_code"])

    def test_17_real_I_exact_DockerIFCExecutor(self):
        self.assertIs(type(self.i().executor),DockerIFCExecutor)

    def test_18_source_public_opposite_class_2_true_5_false(self):
        physical=audit.public_question_opposite_windows_only_v060(
            self.source,self.row["public_question"])
        self.assertEqual(Counter(physical.values()),{True:2,False:5})

    def test_19_source_only_three_developer_pairs(self):
        cases=audit.selected_three_developer_pairs_v060(
            self.source,self.row["public_question"])
        self.assertEqual(len(cases),3)
        self.assertEqual(len({v for _,v in cases}),3)
        self.assertEqual({x for x,_ in cases},{
            "PUBLIC_SOURCE_GEOMETRY_POSITIVE",
            "PUBLIC_SOURCE_GEOMETRY_WRONG_MIXED",
            "PUBLIC_SOURCE_GEOMETRY_WRONG_BOTH",
        })

    def test_20_D_full_true_native_original_window_deletion(self):
        s=self.d()
        result=s.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(result["status"],"ok")
        self.assertTrue(result["native_ifc_committed"])
        self.assertEqual(result["introduced_schema_error_count"],0)
        self.assertEqual(file_hash(s.output_ifc),result["native_ifc_sha256"])

    def test_21_D_managed_true_native_original_window_deletion(self):
        s=self.m()
        result=s.call("submit_managed_final_state",{"xml_text":self.compact()})
        self.assertEqual(result["status"],"ok")
        self.assertTrue(result["native_ifc_committed"])
        self.assertEqual(result["introduced_schema_error_count"],0)

    def test_22_D_complete_and_compact_final_xml_identical(self):
        s=self.d()
        t=self.m()
        self.assertEqual(s.call("submit_building_xml",
                                {"xml_text":self.full()})["status"],"ok")
        self.assertEqual(t.call("submit_managed_final_state",
                                {"xml_text":self.compact()})["status"],"ok")
        self.assertEqual(s.current_xml,t.current_xml)

    def test_23_D_semantic_digest_equal_even_if_raw_sha_varies(self):
        s=self.d()
        t=self.m()
        self.assertEqual(s.call("submit_building_xml",
                                {"xml_text":self.full()})["status"],"ok")
        self.assertEqual(t.call("submit_managed_final_state",
                                {"xml_text":self.compact()})["status"],"ok")
        self.assertEqual(
            canonical_original_native_semantic_digest_v060(s.output_ifc),
            canonical_original_native_semantic_digest_v060(t.output_ifc))

    def test_24_compact_reconstructs_full_without_command(self):
        full,absent=restore_compact_final_state_v060(
            self.source,self.compact().encode("utf8"),source_sha=SOURCE_SHA)
        self.assertEqual(full,self.full().encode("utf8"))
        self.assertEqual(absent,tuple(self.guids[:2]))

    def test_25_three_real_Docker_cases_in_frozen_audit(self):
        rows=self.report["three_evaluator_only_developer_source_pair_controls"]
        self.assertEqual(len(rows),3)
        self.assertTrue(all(r["actual_genuine_isolated_Docker_Python_executed"]
                            for r in rows))
        self.assertEqual(self.report[
            "actual_real_pinned_linux_Docker_I_native_developer_cases"],3)

    def test_26_original_native_semantic_digests_equal_across_all_arms(self):
        rows=self.report["three_evaluator_only_developer_source_pair_controls"]
        self.assertEqual(len({r["all_three_native_Ifc_semantic_digest_SHA256"]
                              for r in rows}),3)
        self.assertTrue(self.report[
            "canonical_IFC_semantic_digest_equal_D_MANAGED_I"])

    def test_27_model_trials_and_paid_calls_zero(self):
        self.assertEqual(self.report["model_generated_trials"],0)
        self.assertEqual(self.report["paid_provider_model_calls"],0)
        self.assertEqual(self.report["original_IFC_uploads_to_model_provider"],0)

    def test_28_raw_IFC_SHA_not_falsely_identified_between_arms(self):
        self.assertTrue(self.report[
            "raw_native_IFC_SHA256_not_stable_due_to_IfcOwnerHistory_real_timestamp_and_SET_order"])
        self.assertTrue(all(not x["native_IFC_raw_binary_SHA_identical_claim"]
            for x in self.report["three_evaluator_only_developer_source_pair_controls"]))

    def test_29_unmodified_original_scorer_missing_one_of_two_target_GUIDs(self):
        self.assertTrue(self.report[
            "original_author_declares_two_window_target_GUIDs_but_one_absent_from_original_IFC"])
        for c in self.report["three_evaluator_only_developer_source_pair_controls"]:
            grade=c["author_repo_metric_evaluator_only"]
            self.assertEqual(grade[
                "original_author_declared_window_target_count"],2)
            self.assertEqual(grade[
                "original_author_window_targets_absent_from_input_IFC"],1)
            self.assertIsNone(grade["author_repository_mean_boolean_score"])

    def test_30_scorer_failure_status_explicit_not_success_grade(self):
        for c in self.report["three_evaluator_only_developer_source_pair_controls"]:
            self.assertEqual(c["author_repo_metric_evaluator_only"]["status"],
                "BLOCKED_PINNED_AUTHOR_EVALUATOR_MISSING_ORIGINAL_SOURCE_GUID")
            self.assertTrue(c["author_repo_metric_evaluator_only"][
                "raw_exception_target_GUID_redacted"])

    def test_31_original_scorer_target_GUIDs_redacted_from_report(self):
        raw=audit.REPORT.read_text(encoding="utf8")
        self.assertNotIn("WINDOW_GUIDS",raw)
        self.assertNotIn("Instance with GlobalId '",raw)
        self.assertTrue(all(c["window_pair_original_target_GUIDs_in_report"] is None
                            for c in self.report[
                                "three_evaluator_only_developer_source_pair_controls"]))

    def test_32_noop_D_full_refused(self):
        self.bad_full(self.initial.decode("utf8"))

    def test_33_noop_compact_refused(self):
        self.bad_compact(self.managed.decode("utf8"))

    def test_34_one_window_deleted_D_full_refused(self):
        self.bad_full(self.full((0,)))

    def test_35_one_window_deleted_D_compact_refused(self):
        self.bad_compact(self.compact((0,)))

    def test_36_three_window_delete_D_full_refused(self):
        self.bad_full(self.full((0,1,2)))

    def test_37_three_window_delete_compact_refused(self):
        self.bad_compact(self.compact((0,1,2)))

    def test_38_missing_any_original_complete_state_guid_refused(self):
        root=etree.fromstring(self.full().encode())
        root[1].remove(root[1][2])
        self.bad_full(etree.tostring(root).decode())

    def test_39_missing_original_compact_roster_guid_refused(self):
        root=etree.fromstring(self.compact().encode())
        root.remove(root[2])
        self.bad_compact(etree.tostring(root).decode())

    def test_40_unknown_GUID_and_duplicate_rows_refused(self):
        root=etree.fromstring(self.compact().encode())
        root[0].set("ifcGuid","0"*22)
        self.bad_compact(etree.tostring(root).decode())
        root=etree.fromstring(self.full().encode())
        root[1][0].set("ifcGuid",root[1][1].get("ifcGuid"))
        self.bad_full(etree.tostring(root).decode())

    def test_41_reordered_original_roster_refused(self):
        root=etree.fromstring(self.compact().encode())
        root.insert(0,root[-1])
        self.bad_compact(etree.tostring(root).decode())

    def test_42_source_original_SHA_tamper_refused(self):
        root=etree.fromstring(self.full().encode())
        root.set("sourceOriginalIFCSha256","f"*64)
        self.bad_full(etree.tostring(root).decode())

    def test_43_compact_full_source_SHA_tamper_refused(self):
        root=etree.fromstring(self.compact().encode())
        root.set("sourceBuildingStateSha256","f"*64)
        self.bad_compact(etree.tostring(root).decode())

    def test_44_source_products_and_opening_link_tamper_refused(self):
        root=etree.fromstring(self.full().encode())
        win=next(x for x in root[0][0] if x.get("ifcClass")=="IfcWindow")
        win.set("originalOpeningGuid","0"*22)
        self.bad_full(etree.tostring(root).decode())

    def test_45_native_world_bbox_tamper_refused(self):
        root=etree.fromstring(self.full().encode())
        obj=next(x for x in root[0][0] if x.get("minXM") is not None)
        obj.set("minXM","123.000000")
        self.bad_full(etree.tostring(root).decode())

    def test_46_unsupported_edit_commands_or_extra_attributes_rejected(self):
        root=etree.fromstring(self.compact().encode())
        root[0].set("operation","delete")
        self.bad_compact(etree.tostring(root).decode())
        root=etree.fromstring(self.full().encode())
        etree.SubElement(root[1][0],"{urn:bim-markup-bench:toy:v0}NativeEditPlan")
        self.bad_full(etree.tostring(root).decode())

    def test_47_DTD_XXE_injection_rejected(self):
        xml=self.full().encode()
        dtd=(b"<!DOCTYPE BuildingState ["
             b"<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>")
        self.bad_full(xml.replace(b"?>",b"?>"+dtd,1).decode("utf8"))

    def test_48_native_wrong_source_SHA_rejected(self):
        with self.assertRaises(Geometry19Native060Error):
            source_full_state_v060(self.source,source_sha="0"*64)

    def test_49_native_source_as_its_own_candidate_rejected(self):
        with self.assertRaises(Geometry19Native060Error):
            independent_two_window_native_scope_v060(
                self.source,self.source,source_sha=SOURCE_SHA)

    def test_50_raw_native_window_delete_without_opening_refused(self):
        with TemporaryDirectory(prefix="v060-raw-") as t:
            model=ifcopenshell.open(str(self.source))
            for w in model.by_type("IfcWindow")[:2]:
                model.remove(w)
            out=Path(t)/"bad.ifc"
            model.write(str(out))
            with self.assertRaises(Geometry19Native060Error):
                independent_two_window_native_scope_v060(
                    self.source,out,source_sha=SOURCE_SHA)

    def test_51_off_target_wall_name_mutation_refused(self):
        with TemporaryDirectory(prefix="v060-wall-") as t:
            model=ifcopenshell.open(str(self.source))
            for guid in self.guids[:2]:
                w=model.by_guid(guid)
                op=w.FillsVoids[0].RelatingOpeningElement
                ifcopenshell.api.run("root.remove_product",model,product=w)
                ifcopenshell.api.run("root.remove_product",model,product=op)
            model.by_type("IfcWall")[0].Name="FORGED_DIFFERENT_WALL"
            out=Path(t)/"wall_changed.ifc"
            model.write(str(out))
            with self.assertRaises(Geometry19Native060Error):
                independent_two_window_native_scope_v060(
                    self.source,out,source_sha=SOURCE_SHA)

    def test_52_owner_history_old_timestamp_forgery_rejected(self):
        with TemporaryDirectory(prefix="v060-time-") as t:
            out=Path(t)/"wrong_history.ifc"
            compile_two_window_removal_v060(
                self.source,out,source_sha=SOURCE_SHA,
                absent_guids=tuple(self.guids[:2]))
            model=ifcopenshell.open(str(out))
            for owner in model.by_type("IfcOwnerHistory"):
                if owner.LastModifiedDate is not None:
                    owner.LastModifiedDate=123456789
            model.write(str(out))
            with self.assertRaises(Geometry19Native060Error):
                independent_two_window_native_scope_v060(
                    self.source,out,source_sha=SOURCE_SHA)

    def test_53_last_good_D_full_rollback(self):
        d=self.d()
        good=d.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(good["status"],"ok")
        before_sha=file_hash(d.output_ifc)
        before_doc=d.current_xml
        bad=d.call("submit_building_xml",{"xml_text":"<wrong/>"})
        self.assertEqual(bad["status"],"error")
        self.assertEqual(file_hash(d.output_ifc),before_sha)
        self.assertEqual(d.current_xml,before_doc)

    def test_54_last_good_D_compact_rollback(self):
        m=self.m()
        good=m.call("submit_managed_final_state",{"xml_text":self.compact()})
        self.assertEqual(good["status"],"ok")
        before_sha=file_hash(m.output_ifc)
        before_doc=m.current_xml
        bad=m.call("submit_managed_final_state",{"xml_text":"<wrong/>"})
        self.assertEqual(bad["status"],"error")
        self.assertEqual(file_hash(m.output_ifc),before_sha)
        self.assertEqual(m.current_xml,before_doc)

    def test_55_same_accepted_D_full_replay_rejected(self):
        d=self.d()
        self.assertEqual(d.call("submit_building_xml",
                                {"xml_text":self.full()})["status"],"ok")
        sha=file_hash(d.output_ifc)
        wrong=d.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(wrong["error_type"],"IdenticalFinalStateReplayRejected")
        self.assertEqual(file_hash(d.output_ifc),sha)

    def test_56_25_tool_calls_limit_all_D_I(self):
        for s in (self.d(),self.m(),self.i()):
            for j in range(MAX_CALLS):
                self.assertEqual(s.call("read_building_xml",
                                        {"query":"source"})["status"],"ok")
            self.assertEqual(s.call("read_building_xml",
                                    {"query":"source"})["error_type"],
                             "ToolBudgetExhausted")

    def test_57_wrong_D_tool_not_executable_through_compact(self):
        m=self.m()
        self.assertEqual(
            m.call("submit_building_xml",{"xml_text":self.full()})["error_type"],
            "WrongDeclarativeFinalStateTool")

    def test_58_no_Docker_runtime_no_python_invoked(self):
        i=self.i()
        with patch(
            "tools.bibimbap_v060_geometry19_sessions.live_pinned_local_runtime_admission_v052",
            return_value={"status":"BLOCKED_RUNTIME","reason":"NO_LINUX"}
        ), patch.object(i.executor,"run") as fake:
            answer=i.call("execute_ifc_code",{"code":"commit()"})
        self.assertEqual(answer["error_type"],"BLOCKED_RUNTIME")
        fake.assert_not_called()
        self.assertIsNone(i.output_ifc)

    def test_59_fake_Docker_success_not_accepted_without_native_edit(self):
        i=self.i()
        with patch(
            "tools.bibimbap_v060_geometry19_sessions.live_pinned_local_runtime_admission_v052",
            return_value={"status":"RUNTIME_ADMITTED"}
        ),patch.object(i.executor,"run",return_value={
            "status":"ok","committed":True,
            "backend":"linux_docker_sandbox"}):
            answer=i.call("execute_ifc_code",{"code":"commit()"})
        self.assertEqual(answer["error_type"],"NativeWorkerOrScopeRejected")
        self.assertIsNone(i.output_ifc)

    def test_60_model_facing_code_no_author_grader_private_TARGET(self):
        for filename in ("bibimbap_v060_geometry19_native.py",
                         "bibimbap_v060_geometry19_sessions.py"):
            content=(audit.ROOT/"tools"/filename).read_text(encoding="utf8")
            for forbidden in ("import data.tests",
                              "from data.tests","import openai",
                              "import anthropic","module.WINDOW_GUIDS",
                              "author_repository_mean_boolean_score",
                              "public_question_opposite_windows_only_v060"):
                self.assertNotIn(forbidden,content)

    def test_61_actual_Docker_rollback_in_frozen_audit(self):
        self.assertTrue(self.report[
            "true_pinned_Docker_good_then_bad_last_IFC_sha_unchanged"])
        self.assertTrue(self.report[
            "raw_unlinked_Docker_two_Window_remove_rejected"])
        self.assertTrue(self.report[
            "D_complete_bad_after_good_XML_and_last_native_ifc_unchanged"])

    def test_62_no_launch_even_fake_all_approvals(self):
        with self.assertRaises(ProviderTrialBlocked057):
            refuse_all_model_trials_v057({
                "rights":True,"model":True,"money":True,
            })
        self.assertEqual(self.report["model_generated_trials"],0)

    def test_63_frozen_report_exclusive_creation(self):
        with self.assertRaises(FileExistsError):
            with audit.REPORT.open("xb"):
                pass


if __name__=="__main__":
    main()
