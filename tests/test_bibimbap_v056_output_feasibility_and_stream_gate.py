"""v0.56 offline full final-state XML output transport, rights and budget gate.

These tests DO NOT run LLM inference, provider token accounting, hidden grader,
paid API or real Docker. The v0.55 frozen report already attests I-native real
container execution; v0.56 deliberately measures D output transport only.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools import audit_bibimbap_v056_full_xml_feasibility as output
from tools import audit_bibimbap_v056_offline_trial_gate as rights
from tools.bibimbap_v056_whole_state_stream import (
    WholeStateStreamDirectSession056,
    WholeStateStream056Error,
    MAX_CHUNK_UTF8_BYTES,MAX_CHUNKS_PER_COMPLETE_STATE,
    split_whole_final_state_utf8_v056,
)
from tools.bibimbap_v055_transactional_primary_DI_sessions import (
    SchemaGuardedDirectStateSession055,
    SchemaGuardedLivePythonSession055,
)
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_matched25_cli import public_45


OUTPUT_SHA="09b2435f402fd333cdb048681313b05a180fe751bc641b9a8a774b77d7620849"
RIGHTS_SHA="6b8e983a80a88a06f8de9ebefaeee3c52a71231583bbfeb164c05e0c1b17137c"


class V056FullXmlBudgetAdmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(output.REPORT.read_text(encoding="utf8"))
        cls.rights=json.loads(rights.REPORT.read_text(encoding="utf8"))
        cls.tasks={x["test_id"]:x for x in
                   public_45(output.AUTHOR,output.DATA)}

    def setUp(self):
        self.temp=TemporaryDirectory(prefix="v056-unit-")
        self.addCleanup(self.temp.cleanup)
        self.tmp=Path(self.temp.name)

    def source(self,tid="geometry_test_14"):
        r=self.tasks[tid]
        return output.DATA/"ifc"/r["original_source_ifc_relpath"]

    def new_stream(self,tid="geometry_test_14",name="stream"):
        return WholeStateStreamDirectSession056(
            self.source(tid),self.tmp/name)

    def test_01_frozen_full_XML_report_SHA(self):
        self.assertEqual(file_hash(output.REPORT),OUTPUT_SHA)

    def test_02_frozen_rights_report_SHA(self):
        self.assertEqual(file_hash(rights.REPORT),RIGHTS_SHA)

    def test_03_v055_real_Docker_IFC_evidence_unchanged(self):
        self.assertEqual(file_hash(output.ROOT/"reports"/
            "bibimbap_v055_primary_DI_schema_guard_live_transactions_20261118.json"),
            output.PARENT_SHA)

    def test_04_original_45_31_population(self):
        self.assertEqual(len(self.tasks),45)
        self.assertEqual(Counter(r["crud"] for r in self.tasks.values()),
                         {"create":15,"update":15,"delete":15})
        self.assertEqual(len({r["original_ifc_sha256"]
                              for r in self.tasks.values()}),31)

    def test_05_only_engineering_original_four_not_full_45(self):
        self.assertEqual(len(output.TASKS),4)
        self.assertEqual(self.report["other_41_original_tasks_NOT_ATTEMPTED"],41)
        self.assertEqual(
            set(self.report["initial_source_and_tool_schemas"]),set(output.TASKS))

    def test_06_new_streams_are_FULL_XML_not_command_tool(self):
        S=self.new_stream()
        names=[t["name"] for t in S.tools]
        self.assertEqual(names,[
            "read_building_xml","submit_complete_building_xml_chunk"])
        self.assertNotIn("submit_building_xml",names)
        self.assertNotIn("NativeEditPlan",str(S.tools))
        self.assertNotIn("execute_ifc_code",str(S.tools))
        self.assertIn("COMPLETE",S.tools[1]["description"])

    def test_07_source_read_exactly_equal_to_real_old_D_and_I(self):
        tid="geometry_test_14"
        D=SchemaGuardedDirectStateSession055(self.source(tid),self.tmp/"D")
        I=SchemaGuardedLivePythonSession055(self.source(tid),self.tmp/"I")
        S=self.new_stream(tid)
        self.assertEqual(D.call("read_building_xml",{})["xml"],
                         S.call("read_building_xml",{})["xml"])
        self.assertEqual(D.current_xml,I.original_source_xml)

    def test_08_same_original_source_for_all_four(self):
        for i,tid in enumerate(output.TASKS):
            sha=self.tasks[tid]["original_ifc_sha256"]
            self.assertEqual(file_hash(self.source(tid)),sha)
            S=WholeStateStreamDirectSession056(self.source(tid),
                                                 self.tmp/f"S{i}")
            read=S.call("read_building_xml",{})
            self.assertEqual(sha256(read["xml"].encode()).hexdigest(),
                self.report["initial_source_and_tool_schemas"][tid][
                    "initial_XML_SHA256"])

    def test_09_one_shot_source_sizes_are_real_not_provider_tokens(self):
        lengths={t:v["initial_full_XML_UTF8_bytes"] for t,v in
                 self.report["initial_source_and_tool_schemas"].items()}
        self.assertEqual(lengths,{
            "geometry_test_14":39611,
            "geometry_test_15":60856,
            "topological_test_11":172424,
            "topological_test_17":151968,
        })
        self.assertIsNone(self.report["provider_max_completion_tokens"])

    def test_10_new_stream_tool_schema_different_not_falsely_matched(self):
        for x in self.report["initial_source_and_tool_schemas"].values():
            self.assertEqual(x["original_D_tool_schema_JSON_UTF8_bytes"],1324)
            self.assertEqual(x["original_I_tool_schema_JSON_UTF8_bytes"],1255)
            self.assertEqual(x["new_stream_D_tool_schema_JSON_UTF8_bytes"],1746)
            self.assertTrue(x["model_facing_stream_schema_CHANGED_from_v055"])

    def test_11_final_XML_lengths_exact_positive_and_negative(self):
        positive={x["original_task_id"]:x["full_final_state_XML_UTF8_bytes"]
                  for x in self.report["full_final_state_developer_output_records"]
                  if x["source_derived_developer_fixture"]=="positive"}
        self.assertEqual(positive,{
            "geometry_test_14":39602,
            "geometry_test_15":60846,
            "topological_test_11":172420,
            "topological_test_17":151758,
        })

    def test_12_chosen_8192_byte_chunks_within_25_total_calls(self):
        maxima={x["original_task_id"]:max(
            y["D_stream_total_calls_including_one_read"]
            for y in self.report["full_final_state_developer_output_records"]
            if y["original_task_id"]==x["original_task_id"])
            for x in self.report["full_final_state_developer_output_records"]}
        self.assertEqual(maxima,{
            "geometry_test_14":6,
            "geometry_test_15":9,
            "topological_test_11":23,
            "topological_test_17":20,
        })
        self.assertTrue(all(x<=25 for x in maxima.values()))

    def test_13_native_IFC_replayed_equal_for_all_8(self):
        rows=self.report["full_final_state_developer_output_records"]
        self.assertEqual(len(rows),8)
        self.assertTrue(all(x["original_one_shot_D_IFC_SHA256"]==
                            x["streamed_D_IFC_SHA256"] for x in rows))
        self.assertTrue(all(x["new_IFC_schema_error_count"]==0 for x in rows))

    def test_14_reassembler_does_not_mutate_XML_unicode(self):
        state="<?xml version='1.0'?><Building>한글 😀 <![CDATA[x]]></Building>"
        chunks=split_whole_final_state_utf8_v056(state,max_chunk_bytes=6)
        self.assertEqual("".join(chunks),state)
        self.assertTrue(all(len(x.encode("utf8"))<=6 for x in chunks))

    def test_15_emoji_chunk_smaller_than_codepoint_fails_closed(self):
        with self.assertRaises(WholeStateStream056Error):
            split_whole_final_state_utf8_v056("😀",max_chunk_bytes=2)

    def test_16_invalid_unpaired_utf16_surrogate_fails_closed(self):
        with self.assertRaises(WholeStateStream056Error):
            split_whole_final_state_utf8_v056("\ud800")

    def test_17_max_chunk_bound_cannot_grow_to_oversized_tool_call(self):
        with self.assertRaises(WholeStateStream056Error):
            split_whole_final_state_utf8_v056("xml",max_chunk_bytes=8193)

    def test_18_sequence_start_must_be_zero(self):
        S=self.new_stream()
        bad=S.call("submit_complete_building_xml_chunk",{
            "sequence":1,"chunk_text":"abc","final":False})
        self.assertEqual(bad["status"],"error")
        self.assertIsNone(S.output_ifc)
        self.assertEqual(S.calls_used,1)

    def test_19_duplicate_chunks_rejected_and_reset(self):
        S=self.new_stream()
        a=S.call("submit_complete_building_xml_chunk",{
            "sequence":0,"chunk_text":"<?xml","final":False})
        b=S.call("submit_complete_building_xml_chunk",{
            "sequence":0,"chunk_text":"<?xml","final":False})
        self.assertEqual(a["status"],"ok")
        self.assertEqual(b["status"],"error")
        c=S.call("submit_complete_building_xml_chunk",{
            "sequence":0,"chunk_text":"<bad>","final":True})
        self.assertNotEqual(c["error_type"],"ChunkOrderLengthOrCallBudgetRejected")

    def test_20_nonfinal_chunks_never_commit_partial_state(self):
        S=self.new_stream()
        original=S.current_xml
        result=S.call("submit_complete_building_xml_chunk",{
            "sequence":0,"chunk_text":"<BuildingState","final":False})
        self.assertEqual(result["status"],"ok")
        self.assertFalse(result["native_ifc_committed"])
        self.assertEqual(S.current_xml,original)
        self.assertIsNone(S.output_ifc)

    def test_21_byte_limit_enforced_inside_model_tool(self):
        S=self.new_stream()
        r=S.call("submit_complete_building_xml_chunk",{
            "sequence":0,"chunk_text":"x"*8193,"final":False})
        self.assertEqual(r["status"],"error")
        self.assertEqual(r["error_type"],"ChunkOrderLengthOrCallBudgetRejected")

    def test_22_strict_argument_keys_and_types(self):
        S=self.new_stream()
        for bad in ({},{"sequence":True,"chunk_text":"x","final":True},
                    {"sequence":0,"chunk_text":"x","final":1},
                    {"sequence":0,"chunk_text":42,"final":True},
                    {"sequence":0,"chunk_text":"x","final":True,"extra":1}):
            r=S.call("submit_complete_building_xml_chunk",bad)
            self.assertEqual(r["error_type"],"InvalidWholeStateChunkInput")

    def test_23_invalid_UTF8_surrogate_inside_model_tool_rejected(self):
        S=self.new_stream()
        reply=S.call("submit_complete_building_xml_chunk",{
            "sequence":0,"chunk_text":"\ud800","final":True})
        self.assertEqual(reply["error_type"],"InvalidChunkUTF8")
        self.assertIsNone(S.output_ifc)

    def test_24_one_shot_tool_not_available_as_secret_bypass(self):
        S=self.new_stream()
        bad=S.call("submit_building_xml",{"xml_text":"x"})
        self.assertEqual(bad["error_type"],
                         "OneShotToolUnavailableInStreamArm")
        self.assertIsNone(S.output_ifc)

    def test_25_chunk_errors_consume_budget_and_stop_at_25(self):
        S=self.new_stream()
        for _ in range(25):
            reply=S.call("submit_complete_building_xml_chunk",{
                "sequence":99,"chunk_text":"x","final":True})
            self.assertEqual(reply["status"],"error")
        last=S.call("submit_complete_building_xml_chunk",{
            "sequence":0,"chunk_text":"x","final":True})
        self.assertEqual(last["error_type"],"ToolBudgetExhausted")
        self.assertEqual(S.calls_used,25)

    def test_26_genuine_whole_XML_state_positive_commit(self):
        S=self.new_stream()
        source=self.source()
        xml=output.developer_XML_final(
            self.tasks["geometry_test_14"],source,positive=True)
        S.call("read_building_xml",{})
        chunks=split_whole_final_state_utf8_v056(xml)
        for i,chunk in enumerate(chunks):
            r=S.call("submit_complete_building_xml_chunk",{
                "sequence":i,"chunk_text":chunk,
                "final":i==len(chunks)-1})
        self.assertEqual(r["status"],"ok")
        self.assertEqual(S.current_xml,xml.encode("utf8"))
        self.assertEqual(r["native_ifc_sha256"],file_hash(S.output_ifc))
        self.assertEqual(S.calls_used,1+len(chunks))

    def test_27_finished_invalid_XML_preserves_last_valid_IFC(self):
        S=self.new_stream()
        xml=output.developer_XML_final(
            self.tasks["geometry_test_14"],self.source(),positive=True)
        for i,chunk in enumerate(split_whole_final_state_utf8_v056(xml)):
            good=S.call("submit_complete_building_xml_chunk",{
                "sequence":i,"chunk_text":chunk,
                "final":i==len(split_whole_final_state_utf8_v056(xml))-1})
        self.assertEqual(good["status"],"ok")
        sha=file_hash(S.output_ifc)
        xml_before=S.current_xml
        invalid=S.call("submit_complete_building_xml_chunk",{
            "sequence":0,"chunk_text":"<wrong/>","final":True})
        self.assertEqual(invalid["status"],"error")
        self.assertEqual(file_hash(S.output_ifc),sha)
        self.assertEqual(S.current_xml,xml_before)

    def test_28_approved_budget_cannot_bypass_OFFLINE_gate(self):
        for approval in (None,{},{"paid_model":True,
                                  "data_transmission":True,
                                  "token_parity":True}):
            with self.assertRaises(rights.OfflineTrialBlocked056):
                rights.enforce_no_paid_or_unapproved_trial_v056(approval)

    def test_29_dataset_card_CC_BY_claim_is_NOT_full_rights_release(self):
        hf=self.rights["original_huggingface_dataset_readonly_public_metadata"]
        self.assertEqual(hf["revision_sha"],
                         rights.HF_DATASET_SHA)
        self.assertEqual(hf["cardData_license_declared"],"cc-by-4.0")
        self.assertFalse(hf["underlying_individual_IFC_asset_rights_proven"])
        self.assertFalse(hf["user_approved_third_party_model_API_transfer"])

    def test_30_code_repo_license_missing_not_inferred_from_data_card(self):
        author=self.rights["original_author_code_checkout"]
        self.assertFalse(author["license_file_in_pinned_checkout"])
        self.assertFalse(author["code_license_terms_approved"])

    def test_31_actual_token_usage_not_reported_as_bytes(self):
        self.assertIsNone(self.rights["provider_actual_billed_token_parity"])
        self.assertIsNone(self.rights["provider_max_output_tokens"])
        self.assertFalse(self.rights["tool_error_feedback_equivalence"])

    def test_32_no_paid_or_LLM_trial_results(self):
        self.assertEqual(self.report["actual_paid_model_calls"],0)
        self.assertEqual(self.rights["billable_provider_calls"],0)
        self.assertEqual(self.report["actual_LLM_D_I_trials"],0)

    def test_33_primary_I_earlier_Docker_and_new_D_are_not_mixed_trials(self):
        self.assertEqual(self.report["new_I_live_Docker_calls_this_checkpoint"],0)
        self.assertTrue(self.report[
            "prior_I_real_Docker_evidence_retained_in_frozen_v055_report"])
        self.assertTrue(self.report[
            "model_token_budget_causal_parity_not_proven"])

    def test_34_frozen_reports_are_exclusive_create(self):
        for path in (rights.REPORT,output.REPORT):
            with self.assertRaises(FileExistsError):
                with path.open("xb") as file:
                    pass

    def test_35_model_facing_stream_module_does_not_import_GT_provider(self):
        source=(output.ROOT/"tools"/
                "bibimbap_v056_whole_state_stream.py").read_text(
                    encoding="utf8")
        for forbidden in ("from data.tests","import openai",
                          "import anthropic","model_output",
                          "NativeEditPlan","original_author_targets",
                          "developer_python_source"):
            self.assertNotIn(forbidden,source)


if __name__=="__main__":
    unittest.main()
