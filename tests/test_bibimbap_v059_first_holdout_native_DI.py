"""v0.59 genuine original-native topo18 first heldout task D/I hardening.

Real Docker I execution is replayed in the separately frozen --check audit,
not mocked by this focused test module. All task answer/author scorer access
is confined to evaluator-only audit, never a model-facing host.
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
from lxml import etree

from tools.bibimbap_matched25_tools import file_hash, DockerIFCExecutor
from tools.bibimbap_matched25_cli import public_45
from tools import audit_bibimbap_v059_first_holdout_native_DI as audit
from tools.bibimbap_v059_topo18_native import (
    SOURCE_SHA,TASK,Q,MAX_CALLS,MAX_COMPACT,
    Topo18Native059Error,
    _source,source_full_state_v059,compact_original_state_v059,
    parse_full_final_state_v059,restore_compact_final_state_v059,
    compile_space_deletion_v059,native_space_delete_scope_v059,
)
from tools.bibimbap_v059_topo18_sessions import (
    DirectFullState059,DirectManagedFinalState059,LiveDockerPython059,
)
from tools.bibimbap_v057_provenance import (
    ProviderTrialBlocked057,refuse_all_model_trials_v057,
)


REPORT_SHA="a40d236129d39014b9127619fd5b63fca5b19eaf3f967027e2ee1338ac6af4ec"


class V059NewNativeOriginalTopo18(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(audit.REPORT.read_text(encoding="utf8"))
        cls.rows={r["test_id"]:r for r in
                  public_45(audit.AUTHOR,audit.DATA)}
        cls.source=audit.DATA/"ifc"/cls.rows[TASK]["original_source_ifc_relpath"]
        cls.initial=source_full_state_v059(cls.source,source_sha=SOURCE_SHA)

    def setUp(self):
        self.temp=TemporaryDirectory(prefix="v059-topo18-test-")
        self.addCleanup(self.temp.cleanup)
        self.tmp=Path(self.temp.name)

    def d(self):
        return DirectFullState059(self.source,self.tmp/"d")

    def m(self):
        return DirectManagedFinalState059(self.source,self.tmp/"m")

    def i(self):
        return LiveDockerPython059(self.source,self.tmp/"i")

    def full(self,index:int=0)->str:
        root=etree.fromstring(self.initial)
        root[1][index].set("present","false")
        return etree.tostring(root,encoding="utf8",
                              xml_declaration=True).decode("utf8")

    def compact(self,index:int=0)->str:
        root=etree.fromstring(compact_original_state_v059(
            self.source,source_sha=SOURCE_SHA))
        root[index].set("present","false")
        return etree.tostring(root,encoding="utf8",
                              xml_declaration=True).decode("utf8")

    def bad_full(self,xml:str)->None:
        with self.assertRaises(Exception):
            parse_full_final_state_v059(
                self.source,xml.encode("utf8"),source_sha=SOURCE_SHA)

    def bad_compact(self,xml:str)->None:
        with self.assertRaises(Exception):
            restore_compact_final_state_v059(
                self.source,xml.encode("utf8"),source_sha=SOURCE_SHA)

    def test_01_frozen_actual_native_D_I_report_sha(self):
        self.assertEqual(file_hash(audit.REPORT),REPORT_SHA)

    def test_02_previous_v058_original45_registry_immutable(self):
        self.assertEqual(file_hash(audit.PARENT_REPORT),audit.PARENT_SHA)

    def test_03_same_six_frozen_selection_and_order(self):
        self.assertEqual(self.report[
            "original_six_source_strata_selected_task_ids"],sorted(audit.KIND))
        self.assertEqual(self.report["exact_original_six_holdout_order_unchanged"],
            json.loads(audit.PARENT_REPORT.read_text(encoding="utf8"))[
                "prospective_randomized_task_order"])

    def test_04_native_original_45_31_unmodified(self):
        rows=self.rows.values()
        self.assertEqual(len(self.rows),45)
        self.assertEqual(len({x["original_ifc_sha256"] for x in rows}),31)

    def test_05_all_six_original_sources_identified_by_task_semantics(self):
        entry=self.report["all_six_original_public_source_diagnostics"]
        self.assertEqual(len(entry),6)
        self.assertEqual({x["original_task_id"] for x in entry},set(audit.KIND))

    def test_06_exact_one_new_task_and_five_other_unsupported(self):
        self.assertEqual(self.report["v059_source_native_task_scope_added"],[TASK])
        self.assertEqual(
            self.report["remaining_five_holdout_source_native_tasks_unsupported"],
            sorted(set(audit.KIND)-{TASK}))

    def test_07_IFC2X3_geometry_create_not_mislabelled_supported(self):
        row=next(x for x in self.report[
            "all_six_original_public_source_diagnostics"]
            if x["original_task_id"]=="geometry_test_03")
        self.assertEqual(row["source_native_schema"],"IFC2X3")
        self.assertFalse(row["v059_real_source_native_D_FULL_admitted"])
        self.assertFalse(row["v059_real_source_native_pinned_Docker_I_admitted"])

    def test_08_original_native_source_reopens_three_rooms_seven_walls(self):
        model=_source(self.source,SOURCE_SHA)
        self.assertEqual(model.schema,"IFC4X3")
        self.assertEqual(len(model.by_type("IfcSpace")),3)
        self.assertEqual(len(model.by_type("IfcWall")),7)

    def test_09_immutable_original_source_sha(self):
        self.assertEqual(file_hash(self.source),SOURCE_SHA)
        self.assertEqual(self.rows[TASK]["original_ifc_sha256"],SOURCE_SHA)

    def test_10_initial_same_model_read_all_three(self):
        D=self.d()
        M=self.m()
        I=self.i()
        reads=[s.call("read_building_xml",{"query":"source"})
               for s in (D,M,I)]
        self.assertEqual({r["status"] for r in reads},{"ok"})
        self.assertEqual(reads[0]["xml"],reads[1]["xml"])
        self.assertEqual(reads[1]["xml"],reads[2]["xml"])
        self.assertEqual(len(reads[0]["xml"].encode("utf8")),3143)

    def test_11_compact_full_source_roster_580_bytes(self):
        c=compact_original_state_v059(self.source,source_sha=SOURCE_SHA)
        self.assertEqual(len(c),580)
        self.assertEqual(len(etree.fromstring(c)),3)

    def test_12_all_original_managed_IFCspace_Guids_lexical(self):
        model=_source(self.source,SOURCE_SHA)
        expected=sorted(x.GlobalId for x in model.by_type("IfcSpace"))
        self.assertEqual([x.get("ifcGuid")
                          for x in etree.fromstring(self.initial)[1]],expected)

    def test_13_two_D_tool_schemas_distinct_from_I_genuine(self):
        a=self.d()
        b=self.m()
        c=self.i()
        self.assertEqual(a.tools[0],b.tools[0])
        self.assertEqual(b.tools[0],c.tools[0])
        self.assertEqual(a.tools[1]["name"],"submit_building_xml")
        self.assertEqual(b.tools[1]["name"],"submit_managed_final_state")
        self.assertEqual(c.tools[1]["name"],"execute_ifc_code")
        self.assertIs(type(c.executor),DockerIFCExecutor)

    def test_14_full_and_compact_model_tool_no_grader_or_answer_hints(self):
        for obj in (self.d(),self.m(),self.i()):
            tool=json.dumps(obj.tools)
            for bad in ("author test","target GUID answer","NativeEditPlan",
                        "execute_test","developer_positive",
                        "original_author_grade"):
                self.assertNotIn(bad,tool)

    def test_15_valid_actual_native_D_full_commit(self):
        D=self.d()
        res=D.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(res["status"],"ok")
        self.assertEqual(res["introduced_schema_errors"],0)
        self.assertEqual(res["native_ifc_sha256"],file_hash(D.output_ifc))
        self.assertEqual(D.calls_used,1)
        self.assertIsNone(res["original_author_score"])

    def test_16_valid_actual_native_D_compact_commit(self):
        M=self.m()
        res=M.call("submit_managed_final_state",{"xml_text":self.compact()})
        self.assertEqual(res["status"],"ok")
        self.assertEqual(res["introduced_schema_errors"],0)
        self.assertEqual(res["native_ifc_sha256"],file_hash(M.output_ifc))
        self.assertEqual(M.calls_used,1)

    def test_17_all_three_rooms_native_D_candidates_real_and_source_safe(self):
        model=ifcopenshell.open(str(self.source))
        for index,room in enumerate(sorted(
                model.by_type("IfcSpace"),key=lambda x:x.GlobalId)):
            dest=self.tmp/f"candidate_{index}.ifc"
            compile_space_deletion_v059(
                self.source,dest,source_sha=SOURCE_SHA,
                absent_guid=room.GlobalId)
            result=native_space_delete_scope_v059(
                self.source,dest,source_sha=SOURCE_SHA)
            self.assertEqual(result["status"],
                "V059_SOURCE_ONLY_ORIGINAL_SPACE_NATIVE_SCOPE_AND_SCHEMA_PASS")
            self.assertEqual(result["new_schema_errors"],0)
        self.assertEqual(file_hash(self.source),SOURCE_SHA)

    def test_18_same_D_full_and_D_compact_native_ifc_hash(self):
        D=self.d()
        M=self.m()
        full=D.call("submit_building_xml",{"xml_text":self.full()})
        compact=M.call("submit_managed_final_state",{"xml_text":self.compact()})
        self.assertEqual(full["native_ifc_sha256"],
                         compact["native_ifc_sha256"])
        self.assertEqual(D.current_xml,M.current_xml)

    def test_19_compact_restores_byte_identical_full_state(self):
        full,absent=restore_compact_final_state_v059(
            self.source,self.compact().encode("utf8"),
            source_sha=SOURCE_SHA)
        self.assertEqual(full,self.full().encode("utf8"))
        self.assertIsInstance(absent,str)

    def test_20_source_six_walls_contact_positive_1_negative_2(self):
        s=audit.public_question_source_contact_v059(
            self.rows[TASK],self.source)
        self.assertEqual(len(s),3)
        self.assertEqual(Counter(s.values()),{True:1,False:2})

    def test_21_three_real_Docker_I_cases_frozen_not_mock(self):
        rows=self.report["topo18_developer_only_native_D_I_cases"]
        self.assertEqual(len(rows),3)
        self.assertTrue(all(x["real_Docker_python_worker_executed"]
                            for x in rows))
        self.assertTrue(all(x["D_and_I_semantic_and_original_author_metric_match"]
                            for x in rows))

    def test_22_grader_metrics_positive_0_5_and_two_zero(self):
        rows=self.report["topo18_developer_only_native_D_I_cases"]
        graded={
            x["developer_source_only_research_predicate"]:
                x["original_author_repo_evaluator_side_only"][
                    "original_author_repository_mean_boolean_score"]
            for x in rows
        }
        self.assertEqual(graded["PUBLIC_SOURCE_GEOMETRIC_POSITIVE"],0.5)
        self.assertEqual(graded["PUBLIC_SOURCE_GEOMETRIC_NEGATIVE"],0.0)
        self.assertTrue(all(x["original_author_repo_evaluator_side_only"][
            "paper_published_official_equivalence_verified"] is False
                            for x in rows))

    def test_23_developer_target_Guid_not_committed_in_report(self):
        raw=audit.REPORT.read_text(encoding="utf8")
        for guid in audit.public_question_source_contact_v059(
                self.rows[TASK],self.source):
            self.assertNotIn(guid,raw)

    def test_24_previous_holdout_unseen_status_now_burned(self):
        self.assertTrue(self.report[
            "v058_six_candidate_no_longer_fully_unexposed_to_developer_implementation"])
        self.assertTrue(self.report["v059_topo18_already_developer_fixture_exposed"])

    def test_25_three_original_python_runs_without_LLM(self):
        self.assertEqual(self.report[
            "actual_genuine_pinned_Linux_Docker_ifcopenshell_successful_cases"],3)
        self.assertEqual(self.report["actual_model_generated_trials"],0)
        self.assertEqual(self.report["paid_model_calls"],0)

    def test_26_full_XML_with_missing_space_roster_rejected(self):
        root=etree.fromstring(self.full().encode())
        root[1].remove(root[1][1])
        self.bad_full(etree.tostring(root).decode())

    def test_27_compact_with_missing_space_roster_rejected(self):
        root=etree.fromstring(self.compact().encode())
        root.remove(root[1])
        self.bad_compact(etree.tostring(root).decode())

    def test_28_double_space_deletion_rejected_D(self):
        root=etree.fromstring(self.full().encode())
        root[1][1].set("present","false")
        self.bad_full(etree.tostring(root).decode())

    def test_29_double_space_deletion_rejected_compact(self):
        root=etree.fromstring(self.compact().encode())
        root[1].set("present","false")
        self.bad_compact(etree.tostring(root).decode())

    def test_30_noop_full_managed_roster_rejected(self):
        self.bad_full(self.initial.decode())

    def test_31_noop_compact_managed_roster_rejected(self):
        self.bad_compact(compact_original_state_v059(
            self.source,source_sha=SOURCE_SHA).decode())

    def test_32_reordered_original_space_GUID_rows_refused(self):
        root=etree.fromstring(self.full().encode())
        e0,e1=root[1][0],root[1][1]
        root[1].replace(e0,etree.fromstring(etree.tostring(e1)))
        self.bad_full(etree.tostring(root).decode())

    def test_33_unknown_or_duplicate_ifc_guid_refused(self):
        for guid in ("0"*22,"BAD_ID",None):
            root=etree.fromstring(self.compact().encode())
            if guid is None:
                del root[0].attrib["ifcGuid"]
            else:
                root[0].set("ifcGuid",guid)
            self.bad_compact(etree.tostring(root).decode())

    def test_34_source_SHA_tampering_refused(self):
        root=etree.fromstring(self.full().encode())
        root.set("sourceOriginalIFCSha256","f"*64)
        self.bad_full(etree.tostring(root).decode())

    def test_35_compact_building_state_anchor_tampering_refused(self):
        root=etree.fromstring(self.compact().encode())
        root.set("sourceBuildingStateSha256","f"*64)
        self.bad_compact(etree.tostring(root).decode())

    def test_36_original_native_products_bounds_immutable_in_full_D(self):
        root=etree.fromstring(self.full().encode())
        root[0][0][0].set("ifcClass","IfcSpace")
        self.bad_full(etree.tostring(root).decode())

    def test_37_extra_managed_property_or_nested_commands_refused(self):
        root=etree.fromstring(self.full().encode())
        root[1][0].set("editOpcode","delete")
        self.bad_full(etree.tostring(root).decode())
        root=etree.fromstring(self.compact().encode())
        etree.SubElement(root[0],Q+"NativeEditPlan")
        self.bad_compact(etree.tostring(root).decode())

    def test_38_DTD_entity_expansion_XXE_refused(self):
        base=self.full().encode()
        dtd=(b"<!DOCTYPE BuildingState ["
             b"<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>")
        bad=base.replace(b"?>",b"?>"+dtd,1)
        self.bad_full(bad.decode("utf8"))

    def test_39_extra_original_roster_room_refused(self):
        root=etree.fromstring(self.compact().encode())
        root.append(etree.fromstring(etree.tostring(root[0])))
        self.bad_compact(etree.tostring(root).decode())

    def test_40_not_one_original_space_removed_native_refused(self):
        with TemporaryDirectory(prefix="v059-no-op-") as t:
            clone=Path(t)/"source.ifc"
            clone.write_bytes(self.source.read_bytes())
            with self.assertRaises(Topo18Native059Error):
                native_space_delete_scope_v059(
                    self.source,clone,source_sha=SOURCE_SHA)

    def test_41_native_raw_unlinked_remove_refused(self):
        with TemporaryDirectory(prefix="v059-raw-") as t:
            model=ifcopenshell.open(str(self.source))
            model.remove(model.by_type("IfcSpace")[0])
            out=Path(t)/"raw.ifc"
            model.write(str(out))
            with self.assertRaises(Topo18Native059Error):
                native_space_delete_scope_v059(
                    self.source,out,source_sha=SOURCE_SHA)

    def test_42_off_target_wall_name_mutation_after_clean_delete_refused(self):
        with TemporaryDirectory(prefix="v059-wall-hack-") as t:
            model=ifcopenshell.open(str(self.source))
            ifcopenshell.api.run("root.remove_product",model,
                                product=model.by_type("IfcSpace")[0])
            model.by_type("IfcWall")[0].Name="MODEL_MODIFIED_UNRELATED_WALL"
            out=Path(t)/"offtarget.ifc"
            model.write(str(out))
            with self.assertRaises(Topo18Native059Error):
                native_space_delete_scope_v059(
                    self.source,out,source_sha=SOURCE_SHA)

    def test_43_extra_IfSpace_after_deletion_refused(self):
        with TemporaryDirectory(prefix="v059-extra-") as t:
            model=ifcopenshell.open(str(self.source))
            ifcopenshell.api.run("root.remove_product",model,
                                product=model.by_type("IfcSpace")[0])
            ifcopenshell.api.run("root.create_entity",model,
                ifc_class="IfcSpace")
            out=Path(t)/"extra.ifc"
            model.write(str(out))
            with self.assertRaises(Topo18Native059Error):
                native_space_delete_scope_v059(
                    self.source,out,source_sha=SOURCE_SHA)

    def test_44_wrong_source_identity_refused(self):
        with self.assertRaises(Topo18Native059Error):
            source_full_state_v059(self.source,source_sha="0"*64)

    def test_45_source_ifc_alias_as_output_refused(self):
        with self.assertRaises(Topo18Native059Error):
            native_space_delete_scope_v059(
                self.source,self.source,source_sha=SOURCE_SHA)

    def test_46_bad_D_after_valid_preserves_last_ifc_XML(self):
        D=self.d()
        valid=D.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(valid["status"],"ok")
        previous=file_hash(D.output_ifc)
        current=D.current_xml
        bad=D.call("submit_building_xml",{"xml_text":"<Invalid/>"})
        self.assertEqual(bad["status"],"error")
        self.assertEqual(file_hash(D.output_ifc),previous)
        self.assertEqual(D.current_xml,current)

    def test_47_bad_compact_after_valid_preserves_last_ifc_XML(self):
        M=self.m()
        valid=M.call("submit_managed_final_state",{"xml_text":self.compact()})
        self.assertEqual(valid["status"],"ok")
        previous=file_hash(M.output_ifc)
        current=M.current_xml
        bad=M.call("submit_managed_final_state",{"xml_text":"<Invalid/>"})
        self.assertEqual(bad["status"],"error")
        self.assertEqual(file_hash(M.output_ifc),previous)
        self.assertEqual(M.current_xml,current)

    def test_48_exact_previous_final_state_replay_refused(self):
        D=self.d()
        self.assertEqual(D.call("submit_building_xml",
                              {"xml_text":self.full()})["status"],"ok")
        copysha=file_hash(D.output_ifc)
        ans=D.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(ans["error_type"],"ExactFinalStateReplayRejected")
        self.assertEqual(file_hash(D.output_ifc),copysha)

    def test_49_D_and_I_budgets_25_calls(self):
        for kind,session in enumerate((self.d(),self.m(),self.i())):
            for j in range(MAX_CALLS):
                self.assertEqual(session.call(
                    "read_building_xml",{"query":"source"})["status"],"ok")
            ans=session.call("read_building_xml",{"query":"source"})
            self.assertEqual(ans["error_type"],"ToolBudgetExhausted")
            self.assertIsNone(session.output_ifc)

    def test_50_wrong_D_tool_cannot_bypass_compact(self):
        M=self.m()
        bad=M.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(bad["error_type"],"WrongDRepresentationTool")

    def test_51_I_without_Docker_admission_runs_nothing(self):
        I=self.i()
        with patch(
            "tools.bibimbap_v059_topo18_sessions.live_pinned_local_runtime_admission_v052",
            return_value={"status":"BLOCKED_RUNTIME","reason":"NO_LINUX_TEST"}
        ),patch.object(I.executor,"run") as fake:
            answer=I.call("execute_ifc_code",{"code":"commit()"})
        self.assertEqual(answer["error_type"],"BLOCKED_RUNTIME")
        fake.assert_not_called()
        self.assertIsNone(I.output_ifc)

    def test_52_I_fake_worker_commit_cannot_pass_native_scope(self):
        I=self.i()
        with patch(
            "tools.bibimbap_v059_topo18_sessions.live_pinned_local_runtime_admission_v052",
            return_value={"status":"RUNTIME_ADMITTED"}
        ),patch.object(I.executor,"run",return_value={
            "status":"ok","committed":True,"backend":"linux_docker_sandbox"}):
            answer=I.call("execute_ifc_code",{"code":"commit()"})
        self.assertEqual(answer["error_type"],"NativeWorkerOrScopeRejected")
        self.assertIsNone(I.output_ifc)

    def test_53_model_host_does_not_import_author_evaluator(self):
        root=audit.ROOT
        for file in ("bibimbap_v059_topo18_native.py",
                     "bibimbap_v059_topo18_sessions.py"):
            txt=(root/"tools"/file).read_text(encoding="utf8")
            for forbidden in ("from data.tests","import data.tests",
                              "import openai","import anthropic",
                              "original_author_targets_evaluator_only",
                              "author_repository_mean_boolean_score",
                              "public_question_source_contact_v059"):
                self.assertNotIn(forbidden,txt)

    def test_54_official_paper_metric_not_falsely_claimed(self):
        self.assertFalse(self.report[
            "official_published_paper_grader_provenance_verified"])
        self.assertIsNone(self.report["actual_published_paper_score"])

    def test_55_6_task_holdout_comparison_still_blocked(self):
        self.assertTrue(self.report[
            "full_benchmark_or_confirmatory_holdout_still_blocked"])
        self.assertEqual(self.report["remaining_five_holdout_source_native_tasks_unsupported"],
                         sorted(set(audit.KIND)-{TASK}))

    def test_56_no_paid_LLM_even_if_all_fake_approvals_TRUE(self):
        with self.assertRaises(ProviderTrialBlocked057):
            refuse_all_model_trials_v057({
                "provider":True,"rights":True,"budget":True,"approval":True,
            })
        self.assertEqual(self.report["actual_model_generated_trials"],0)
        self.assertEqual(self.report["paid_model_calls"],0)

    def test_57_frozen_report_exclusive_create(self):
        with self.assertRaises(FileExistsError):
            with audit.REPORT.open("xb") as f:
                pass


if __name__=="__main__":
    unittest.main()
