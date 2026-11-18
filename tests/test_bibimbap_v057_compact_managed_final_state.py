"""v0.57 original IFC source-anchored compact complete-final-state tests.

No model calls, paid provider or private target GUIDs imported in host.
Checks genuine full state -> compact -> original full IFC SHA equivalence,
complete original GUID roster, strict state grammar and atomic rollback.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from lxml import etree

from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v055_transactional_primary_DI_sessions import (
    SchemaGuardedDirectStateSession055,
    SchemaGuardedLivePythonSession055,
)
from tools.bibimbap_v057_managed_final_state_session import (
    ManagedFinalStateDirectSession057,
)
from src.runtime.experimental_v57_compact_managed_state import (
    ManagedFinalState057Error,
    MAX_MANAGED_STATE_UTF8_BYTES,
    project_managed_final_state_v057,
    compact_from_complete_declarative_state_v057,
    restore_complete_declarative_state_v057,
)
from tools.bibimbap_v057_provenance import (
    ProviderTrialBlocked057,
    assert_original_source_rights_unchanged_v057,
    refuse_all_model_trials_v057,
)
from tools.audit_bibimbap_v055_live_schema_transactions import developer_XML_final
from tools import audit_bibimbap_v057_compact_managed_final_state as audit


REPORT_SHA="22b3f30166ba2164278cdc1b2b25e5e4c4d0d0cddb74c25f7b759287bd127e57"
NS="{urn:bim-markup-bench:toy:v0}"


class ManagedCompleteFinalState057(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(audit.REPORT.read_text(encoding="utf8"))
        cls.rows=audit.row_registry()

    def setUp(self):
        self.temp=TemporaryDirectory(prefix="v057-complete-")
        self.addCleanup(self.temp.cleanup)
        self.scratch=Path(self.temp.name)

    def source(self,tid="geometry_test_14"):
        row=self.rows[tid]
        return audit.DATA/"ifc"/row["original_source_ifc_relpath"]

    def sha(self,tid="geometry_test_14"):
        return self.rows[tid]["original_ifc_sha256"]

    def pristine(self,tid="geometry_test_14"):
        return project_managed_final_state_v057(
            self.source(tid),source_sha=self.sha(tid))

    def good(self,tid="geometry_test_14",positive=True):
        whole=developer_XML_final(
            self.rows[tid],self.source(tid),positive=positive).encode("utf8")
        return compact_from_complete_declarative_state_v057(
            self.source(tid),whole,source_sha=self.sha(tid))

    def edit(self,task="geometry_test_14",positive=True):
        return etree.fromstring(self.good(task,positive))

    def encode(self,root):
        return etree.tostring(root,encoding="utf8",xml_declaration=True)

    def assert_bad(self,xml,tid="geometry_test_14"):
        with self.assertRaises(Exception):
            restore_complete_declarative_state_v057(
                self.source(tid),xml,source_sha=self.sha(tid))

    def test_01_exact_frozen_v057_report_hash(self):
        self.assertEqual(file_hash(audit.REPORT),REPORT_SHA)

    def test_02_earlier_v056_D_report_immutable(self):
        self.assertEqual(file_hash(audit.ROOT/"reports"/
            "bibimbap_v056_original4_full_XML_response_feasibility_20261118.json"),
            audit.PARENT_SHA)

    def test_03_earlier_v056_rights_immutable(self):
        self.assertEqual(file_hash(audit.ROOT/"reports"/
            "bibimbap_v056_offline_trial_rights_and_output_budget_gate_20261118.json"),
            audit.RIGHTS_SHA)

    def test_04_earlier_v055_real_Docker_immutable(self):
        self.assertEqual(file_hash(audit.ROOT/"reports"/
            "bibimbap_v055_primary_DI_schema_guard_live_transactions_20261118.json"),
            audit.V055_SHA)

    def test_05_original_45_31_unchanged(self):
        self.assertEqual(len(self.rows),45)
        self.assertEqual(Counter(x["crud"] for x in self.rows.values()),
                         {"create":15,"update":15,"delete":15})
        self.assertEqual(len({x["original_ifc_sha256"]
                              for x in self.rows.values()}),31)

    def test_06_original_source_XML_identical_D_full_I_and_managed(self):
        for idx,tid in enumerate(audit.TASKS):
            src=self.source(tid)
            D=SchemaGuardedDirectStateSession055(src,self.scratch/f"D{idx}")
            I=SchemaGuardedLivePythonSession055(src,self.scratch/f"I{idx}")
            M=ManagedFinalStateDirectSession057(src,self.scratch/f"M{idx}")
            d=D.call("read_building_xml",{})
            i=I.call("read_building_xml",{})
            m=M.call("read_building_xml",{})
            self.assertEqual(d["xml"],i["xml"])
            self.assertEqual(i["xml"],m["xml"])
            self.assertEqual(m["current_xml_sha256"],
                             d["current_xml_sha256"])

    def test_07_model_tool_id_explicitly_new(self):
        M=ManagedFinalStateDirectSession057(self.source(),self.scratch/"M")
        D=SchemaGuardedDirectStateSession055(self.source(),self.scratch/"D")
        self.assertEqual(M.tools[0],D.tools[0])
        self.assertEqual([x["name"] for x in M.tools],
                         ["read_building_xml","submit_managed_final_state"])
        self.assertNotEqual(M.tools[1],D.tools[1])
        for bad in ("NativeEditPlan","MoveColumnPlacement",
                    "execute_ifc_code","SetSlabRectangleDimensions"):
            self.assertNotIn(bad,str(M.tools))

    def test_08_compact_all_original_managed_roster_counts(self):
        sizes={t:(len(etree.fromstring(self.pristine(t))),
                  len(self.pristine(t))) for t in audit.TASKS}
        self.assertEqual({t:x[0] for t,x in sizes.items()},
             {"geometry_test_14":1,"geometry_test_15":4,
              "topological_test_11":2,"topological_test_17":10})
        self.assertTrue(all(size<=MAX_MANAGED_STATE_UTF8_BYTES
                            for _count,size in sizes.values()))

    def test_09_all_original_roster_members_have_explicit_presence(self):
        for tid in audit.TASKS:
            elements=etree.fromstring(self.pristine(tid))
            self.assertTrue(all(x.get("present")=="true" for x in elements))
            self.assertTrue(all(len(x.attrib)>=2 for x in elements))

    def test_10_all_8_developer_native_IFC_shas_identical(self):
        records=self.report["developer_only_complete_final_state_controls"]
        self.assertEqual(len(records),8)
        for r in records:
            self.assertEqual(r["whole_D_IFC_SHA256"],
                             r["compact_D_IFC_SHA256"])
            self.assertEqual(r["new_ifc_schema_findings"],0)
            self.assertTrue(r["all_original_managed_objects_explicitly_declared"])
            self.assertFalse(r["actual_LLM_generated"])

    def test_11_original_author_scorer_8_pairs_separate(self):
        records=self.report["developer_only_complete_final_state_controls"]
        self.assertTrue(self.report[
            "actual_author_repository_evaluator_scores_verified_8_pairs"])
        for r in records:
            author=r["author_repository_evaluator_only"]
            self.assertIsNone(author["published_paper_official_score"])
            self.assertIsNone(r["actual_published_paper_official_score"])
            self.assertIsInstance(author["author_repository_mean_boolean_score"],
                                  float)

    def test_12_public_source_research_predicate_4_positive_4_negative(self):
        records=self.report["developer_only_complete_final_state_controls"]
        self.assertEqual(sum(x["physical_source_research_predicate"]
                             for x in records),4)
        self.assertEqual(sum(not x["physical_source_research_predicate"]
                             for x in records),4)

    def test_13_compact_initial_source_not_valid_NOOP_edit(self):
        self.assert_bad(self.pristine())

    def test_14_missing_entire_managed_roster_rejected(self):
        root=self.edit("geometry_test_15")
        root.remove(root[1])
        self.assert_bad(self.encode(root),"geometry_test_15")

    def test_15_missing_deleted_columns_not_accepted_as_partial_patch(self):
        root=self.edit("topological_test_17")
        absent=next(x for x in root if x.get("present")=="false")
        root.remove(absent)
        self.assert_bad(self.encode(root),"topological_test_17")

    def test_16_reordered_roster_rejected(self):
        root=self.edit("geometry_test_15")
        root[0],root[1]=root[1],root[0]
        self.assert_bad(self.encode(root),"geometry_test_15")

    def test_17_duplicate_original_managed_guid_rejected(self):
        root=self.edit("geometry_test_15")
        root[1].set("ifcGuid",root[0].get("ifcGuid"))
        self.assert_bad(self.encode(root),"geometry_test_15")

    def test_18_unknown_original_managed_guid_rejected(self):
        root=self.edit("geometry_test_15")
        root[0].set("ifcGuid","0"*22)
        self.assert_bad(self.encode(root),"geometry_test_15")

    def test_19_extra_managed_object_rejected(self):
        root=self.edit("geometry_test_15")
        root.append(etree.fromstring(etree.tostring(root[0])))
        self.assert_bad(self.encode(root),"geometry_test_15")

    def test_20_extra_numeric_final_attribute_rejected(self):
        root=self.edit()
        root[0].set("futureField","300")
        self.assert_bad(self.encode(root))

    def test_21_missing_numeric_final_attribute_rejected(self):
        root=self.edit()
        del root[0].attrib["dimXM"]
        self.assert_bad(self.encode(root))

    def test_22_unsupported_slabs_cannot_be_deleted(self):
        root=self.edit()
        root[0].set("present","false")
        self.assert_bad(self.encode(root))

    def test_23_wrong_boolean_presence_rejected(self):
        root=self.edit("topological_test_17")
        root[0].set("present","maybe")
        self.assert_bad(self.encode(root),"topological_test_17")

    def test_24_absent_non_delete_task_column_rejected(self):
        root=self.edit("geometry_test_15")
        root[0].set("present","false")
        self.assert_bad(self.encode(root),"geometry_test_15")

    def test_25_invalid_shared_mapped_depth_rejected(self):
        root=self.edit("topological_test_11")
        original=float(root[0].get("extrusionDepthM"))
        root[0].set("extrusionDepthM",f"{original+0.01:.6f}")
        self.assert_bad(self.encode(root),"topological_test_11")

    def test_26_nan_and_infinity_in_numeric_rejected(self):
        for invalid in ("NaN","Infinity","-Infinity","1e1000"):
            root=self.edit()
            root[0].set("dimXM",invalid)
            self.assert_bad(self.encode(root))

    def test_27_source_original_ifc_sha_mismatch_rejected(self):
        root=self.edit()
        root.set("sourceOriginalIFCSha256","f"*64)
        self.assert_bad(self.encode(root))

    def test_28_original_full_source_state_sha_mismatch_rejected(self):
        root=self.edit()
        root.set("sourceBuildingStateSha256","f"*64)
        self.assert_bad(self.encode(root))

    def test_29_version_or_representation_tamper_rejected(self):
        root=self.edit()
        root.set("version","0.55")
        self.assert_bad(self.encode(root))
        root=self.edit()
        root.set("representation","D_COMPLETE_XML")
        self.assert_bad(self.encode(root))

    def test_30_managed_boundary_spoof_rejected(self):
        root=self.edit()
        root.set("managedBoundary","EXTERNAL_UNMANAGED")
        self.assert_bad(self.encode(root))

    def test_31_nested_unexpected_elements_rejected(self):
        root=self.edit()
        etree.SubElement(root[0],NS+"NativeEditPlan")
        self.assert_bad(self.encode(root))

    def test_32_source_subtree_cannot_be_injected_into_compact(self):
        root=self.edit()
        etree.SubElement(root,NS+"OriginalNativeIFCSource")
        self.assert_bad(self.encode(root))

    def test_33_comment_and_processing_instruction_handling(self):
        root=self.edit()
        root.insert(0,etree.Comment("bad"))
        self.assert_bad(self.encode(root))
        root=self.edit()
        root.insert(0,etree.ProcessingInstruction("data","bad"))
        self.assert_bad(self.encode(root))

    def test_34_XXE_DTD_must_be_rejected(self):
        # This is a syntactically well-formed XML declaration + DTD +
        # otherwise valid complete managed state. Reject the DTD, not merely
        # an accidentally duplicated XML declaration.
        declaration=(b"<!DOCTYPE ManagedFinalState ["
                     b"<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>")
        xml=self.good().replace(b"?>",b"?>"+declaration,1)
        self.assertIn(b"<!DOCTYPE",xml)
        self.assert_bad(xml)

    def test_35_oversized_state_rejected(self):
        data=self.good()
        self.assert_bad(data+b"x"*(MAX_MANAGED_STATE_UTF8_BYTES+1))

    def test_36_xml_text_nodes_with_untrusted_data_rejected(self):
        root=self.edit()
        root[0].text="unexpected"
        self.assert_bad(self.encode(root))
        root=self.edit()
        root[0].tail="unexpected"
        self.assert_bad(self.encode(root))

    def test_37_wrong_ifc_guid_case_rejected(self):
        root=self.edit("geometry_test_15")
        id1=root[0].get("ifcGuid")
        root[0].set("ifcGuid",id1.swapcase())
        self.assert_bad(self.encode(root),"geometry_test_15")

    def test_38_positive_actual_IFC_valid_one_call(self):
        source=self.source()
        M=ManagedFinalStateDirectSession057(source,self.scratch/"M")
        answer=M.call("submit_managed_final_state",{
            "xml_text":self.good().decode("utf8")})
        self.assertEqual(answer["status"],"ok")
        self.assertEqual(answer["representation"],"D_MANAGED_FINAL_STATE")
        self.assertEqual(answer["introduced_schema_error_count"],0)
        self.assertEqual(file_hash(M.output_ifc),
                         answer["native_ifc_sha256"])
        self.assertEqual(M.calls_used,1)
        self.assertIsNone(answer["original_author_benchmark_score"])

    def test_39_invalid_following_valid_preserves_last_IFC_and_XML(self):
        source=self.source()
        M=ManagedFinalStateDirectSession057(source,self.scratch/"M")
        good=M.call("submit_managed_final_state",{
            "xml_text":self.good().decode()})
        self.assertEqual(good["status"],"ok")
        last_sha=file_hash(M.output_ifc)
        last_xml=M.current_xml
        bad=M.call("submit_managed_final_state",{
            "xml_text":"<InvalidCompleteState/>"})
        self.assertEqual(bad["status"],"error")
        self.assertEqual(last_sha,file_hash(M.output_ifc))
        self.assertEqual(last_xml,M.current_xml)

    def test_40_old_full_XML_tool_cannot_bypass_new_arm(self):
        M=ManagedFinalStateDirectSession057(self.source(),self.scratch/"M")
        resp=M.call("submit_building_xml",{
            "xml_text":self.good().decode()})
        self.assertEqual(resp["error_type"],
                         "OriginalWholeXmlToolNotInCompactArm")
        self.assertIsNone(M.output_ifc)

    def test_41_25_call_limit_preserved(self):
        M=ManagedFinalStateDirectSession057(self.source(),self.scratch/"M")
        for _ in range(25):
            self.assertEqual(M.call("read_building_xml",{})["status"],"ok")
        after=M.call("submit_managed_final_state",{
            "xml_text":self.good().decode()})
        self.assertEqual(after["error_type"],"ToolBudgetExhausted")
        self.assertIsNone(M.output_ifc)

    def test_42_malformed_tool_arguments_consume_budget(self):
        M=ManagedFinalStateDirectSession057(self.source(),self.scratch/"M")
        for args in ({},{"xml_text":23},{"xml_text":"","bad":True},
                     {"bad":"x"}):
            answer=M.call("submit_managed_final_state",args)
            self.assertEqual(answer["status"],"error")
            self.assertFalse(answer["native_ifc_committed"])
        self.assertEqual(M.calls_used,4)

    def test_43_original_ifc_sha_mismatch_blocks_model_tool(self):
        M=ManagedFinalStateDirectSession057(self.source(),self.scratch/"M")
        with patch(
            "tools.bibimbap_v057_managed_final_state_session.file_hash",
            return_value="f"*64):
            bad=M.call("submit_managed_final_state",{
                "xml_text":self.good().decode()})
        self.assertEqual(bad["error_type"],"OriginalSourceChanged")
        self.assertIsNone(M.output_ifc)

    def test_44_forced_host_schema_rejection_does_not_commit(self):
        M=ManagedFinalStateDirectSession057(self.source(),self.scratch/"M")
        from tools.bibimbap_v055_production_schema_gate import NativeSourceSchema055Error
        with patch(
            "tools.bibimbap_v055_transactional_primary_DI_sessions.validate_production_native_commit_v055",
            side_effect=NativeSourceSchema055Error("SchemaReject")):
            bad=M.call("submit_managed_final_state",{
                "xml_text":self.good().decode()})
        self.assertEqual(bad["status"],"error")
        self.assertIsNone(M.output_ifc)
        self.assertEqual(M.current_xml,M.original_xml)

    def test_45_no_private_author_grader_or_dev_fixture_in_model_host(self):
        for path in (
          audit.ROOT/"src"/"runtime"/"experimental_v57_compact_managed_state.py",
          audit.ROOT/"tools"/"bibimbap_v057_managed_final_state_session.py",
        ):
            text=path.read_text(encoding="utf8")
            for marker in ("import openai","from data.tests",
                           "import data.tests","original_author_targets",
                           "developer_python_source","author_origin"):
                self.assertNotIn(marker,text)

    def test_46_no_model_launch_even_with_all_true(self):
        assert_original_source_rights_unchanged_v057()
        with self.assertRaises(ProviderTrialBlocked057):
            refuse_all_model_trials_v057({
                "authorized":True,"money":True,"rights":True,
                "token_parity":True,"snapshot":True})

    def test_47_no_paper_official_or_causal_accuracy_claim(self):
        self.assertEqual(self.report["actual_LLM_generated_trial_count"],0)
        self.assertEqual(self.report["paid_model_calls"],0)
        self.assertIsNone(self.report["actual_original_paper_official_score"])
        self.assertTrue(self.report[
            "model_token_parity_or_accuracy_inference_not_proven"])

    def test_48_frozen_report_exclusive_creation(self):
        with self.assertRaises(FileExistsError):
            with audit.REPORT.open("xb") as f:
                pass

    def test_49_semantic_replay_after_valid_commit_rejected(self):
        M=ManagedFinalStateDirectSession057(self.source(),self.scratch/"M")
        complete=self.good().decode()
        first=M.call("submit_managed_final_state",{"xml_text":complete})
        self.assertEqual(first["status"],"ok")
        before_sha=file_hash(M.output_ifc)
        before_xml=M.current_xml
        replay=M.call("submit_managed_final_state",{"xml_text":complete})
        self.assertEqual(replay["error_type"],
                         "UnchangedManagedFinalStateReplayRejected")
        self.assertEqual(M.calls_used,2)
        self.assertEqual(file_hash(M.output_ifc),before_sha)
        self.assertEqual(M.current_xml,before_xml)

    def test_50_valid_document_with_unrelated_namespaced_attribute_rejected(self):
        root=self.edit()
        root.set("{urn:external:spoof}sourceOriginalIFCSha256",self.sha())
        self.assert_bad(self.encode(root))


if __name__=="__main__":
    unittest.main()
