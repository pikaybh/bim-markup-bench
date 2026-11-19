"""Offline, no-provider regressions for the matched-25 experimental harness."""
from __future__ import annotations
from decimal import Decimal
from datetime import datetime,timezone
import json
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import Mock

from tools.bibimbap_matched25_agent import (
    MODEL,MAX_TOOL_CALLS,MAX_OUTPUT_TOKENS,PairProtocol,
    DurableBudget,ProviderBudgetError,ProtocolError,
    FakeUsage,OfflineFakeClient,_FunctionCall,arm_messages,run_agent,
)
from tools.bibimbap_matched25_tools import (
    PINNED_DOCKER_IMAGE, SecurityGate, build_pinned_docker_command,
    DockerIFCExecutor, XmlSourceEditSession,PythonIfcCodeSession,
)
from tools.bibimbap_matched25_cli import (
    public_45,offline_preflight,run_one_pair,paired_summary,
)

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",r"D:\문서\D__1_Projects\202611"))
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"

class StubSession:
    """No IFC; checks tool-call accounting deterministically."""
    output_ifc=None
    def __init__(self):self.calls=[]
    @property
    def tools(self):
        return [{"type":"function","name":"query","description":"mock",
                 "parameters":{"type":"object","properties":{},"additionalProperties":False},"strict":True}]
    def call(self,name,arguments):
        self.calls.append((name,arguments))
        return {"status":"error" if name=="fail" else "ok","retry_hint":"fix and retry"}

class ProtocolTests(unittest.TestCase):
    def test_protocol_is_frozen_and_both_arms_equal_model_turn_caps(self):
        p=PairProtocol()
        self.assertEqual(p.model,MODEL)
        self.assertEqual(p.max_tool_calls,25)
        self.assertEqual(p.max_output_tokens,12000)
        self.assertEqual(p.automatic_retries,0)
        self.assertFalse(p.store)
        with self.assertRaises(ProtocolError):
            PairProtocol(max_tool_calls=24)
        with self.assertRaises(ProtocolError):
            PairProtocol(model="gpt-5.4")

    def test_fully_stateless_fake_multiturn_with_feedback(self):
        client=OfflineFakeClient([
            [_FunctionCall("query","{}","fake_id_1")],
            [_FunctionCall("fail","{}","fake_id_2")],
            [_FunctionCall("query","{}","fake_id_3")],
            [],
        ])
        tool=StubSession()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"saved.json"
            out=run_agent(client,tool,arm="XML",public_question="Test task",
                          protocol=PairProtocol(),budget=None,record_file=p)
            self.assertEqual(out["status"],"MODEL_FINAL_MESSAGE")
            self.assertEqual(out["tool_calls"],3)
            self.assertEqual(out["model_requests"],4)
            self.assertEqual(len(tool.calls),3)
            self.assertTrue(p.is_file())
            records=json.loads(p.read_text(encoding="utf8"))
            self.assertEqual(sum("tool_feedback" in e for e in records),3)
            self.assertEqual(sum(e["tool_feedback"]["status"]=="error" for e in records if "tool_feedback" in e),1)

    def test_exact_25_cap_never_dispatches_a_26th_tool(self):
        fake=OfflineFakeClient([
            [_FunctionCall("query","{}",f"c{i:02d}") for i in range(31)]
        ])
        tool=StubSession()
        out=run_agent(fake,tool,arm="PYTHON",public_question="One test",
                      protocol=PairProtocol(),budget=None)
        self.assertEqual(out["tool_calls"],25)
        self.assertEqual(len(tool.calls),25)
        self.assertEqual(out["model_requests"],1)
        self.assertEqual(out["status"],"MAX_25_TOOL_CALLS_REACHED")

    def test_model_cannot_select_imperative_tool_in_xml_condition(self):
        fake=OfflineFakeClient([[_FunctionCall("execute_ifc_code",
                             '{"code":"print(1)"}',"call_x")],[]])
        tool=StubSession()
        out=run_agent(fake,tool,arm="XML",public_question="Do something",
                      protocol=PairProtocol(),budget=None)
        self.assertEqual(out["tool_calls"],1)
        self.assertEqual(out["model_requests"],2)
        self.assertEqual(tool.calls[0][0],"execute_ifc_code")
        instr,task=arm_messages("XML","Do something")
        self.assertIn("Do NOT write or invoke Python",instr)
        self.assertNotIn("execute_ifc_code",task)

    def test_no_real_provider_client_without_approved_budget(self):
        class Unexpected:
            class responses:
                @staticmethod
                def create(**kwargs):
                    raise AssertionError("Provider must not be called")
        with self.assertRaises(ProviderBudgetError):
            run_agent(Unexpected(),StubSession(),arm="PYTHON",
                      public_question="Task",protocol=PairProtocol(),budget=None)

    def test_budget_approval_schema_negative_and_no_second_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"budget.json"
            with self.assertRaises(ProviderBudgetError):
                DurableBudget(p,"2",approval={"approved":True})
            self.assertFalse(p.exists())
            approved={
                "approved":True,
                "issue":"https://github.com/pikaybh/bim-markup-bench/issues/114",
                "model":"gpt-6-luna","cap_usd":"2",
                "max_tool_calls":25,"max_output_tokens":12000,
                "pricing_checked_utc":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "approved_at_utc":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "input_per_million_usd":"0.10","output_per_million_usd":"0.50",
                "pricing_url":"https://developers.openai.com/api/docs/pricing",
            }
            budget=DurableBudget(p,"2",approval=approved)
            i=budget.reserve(input_payload={"input":[{"role":"user","content":"task"}]},
                             tools=StubSession().tools,max_output=MAX_OUTPUT_TOKENS)
            budget.settle(i,FakeUsage(input_tokens=100,output_tokens=100),
                          confirmed_model=MODEL)
            self.assertEqual(budget.data["requests_reserved"],1)
            self.assertEqual(budget.data["requests_settled"],1)
            self.assertEqual(Decimal(budget.data["token_usage_estimated_usd"]),Decimal("0.00006"))
            with self.assertRaises(ProviderBudgetError):
                DurableBudget(p,"2",approval=approved)

    def test_budget_fails_closed_below_next_request_even_after_unknown_usage(self):
        with tempfile.TemporaryDirectory() as d:
            budget=DurableBudget(Path(d)/"budget.json","0.001")
            with self.assertRaises(ProviderBudgetError):
                budget.reserve(input_payload={"input":"task"},tools=StubSession().tools,
                               max_output=MAX_OUTPUT_TOKENS)
            self.assertEqual(budget.data["requests_reserved"],0)
            self.assertEqual(budget.data["status"],"BUDGET_EXHAUSTED")
        with tempfile.TemporaryDirectory() as d:
            budget=DurableBudget(Path(d)/"budget.json","0.03")
            i=budget.reserve(input_payload={"input":"task"},tools=StubSession().tools,
                             max_output=MAX_OUTPUT_TOKENS)
            budget.settle(i,None,confirmed_model=None)
            self.assertEqual(budget.data["request_ledger"][0]["status"],
                             "SETTLED_CONSERVATIVE_UNKNOWN_USAGE")
            self.assertEqual(budget.data["requests_settled"],1)

    def test_docker_command_must_be_linux_isolated_local_and_pinned(self):
        from tools.bibimbap_matched25_tools import WORKER
        with tempfile.TemporaryDirectory() as d:
            cmd=build_pinned_docker_command(PINNED_DOCKER_IMAGE,
                     "bibi-ifc-abcdef1234567890",Path(d))
            full=" ".join(cmd)
            for mandatory in ("--network=none","--read-only","--cap-drop=ALL",
                              "--pids-limit=32","--memory=768m",
                              "--user=65534:65534","--security-opt=no-new-privileges",
                              "target=/worker.py,readonly","target=/workspace"):
                self.assertIn(mandatory,full)
            self.assertIn(PINNED_DOCKER_IMAGE,full)
            with self.assertRaises(SecurityGate):
                build_pinned_docker_command("python:latest",
                    "bibi-ifc-abcdef1234567890",Path(d))

class PairedMetricsOfflineTests(unittest.TestCase):
    def test_matched_subset_vs_true_full45_reporting_is_not_conflated(self):
        pair=[
            {"task_id":"test_05","crud":"create","category":"basic",
             "arms":{
                 "XML":{"status":"MODEL_FINAL_MESSAGE","model_requests":3,
                        "original_author_result":{"status":"AUTHOR_SCORED","original_author_score":1.0}},
                 "PYTHON":{"status":"MODEL_FINAL_MESSAGE","model_requests":4,
                           "original_author_result":{"status":"AUTHOR_SCORED","original_author_score":0.75}},
             }},
            {"task_id":"geometry_test_05","crud":"create","category":"geometry",
             "arms":{
                 "XML":{"status":"UNSUPPORTED_BACKEND_NOT_MODEL_FAILURE","model_requests":0},
                 "PYTHON":{"status":"MODEL_FINAL_MESSAGE","model_requests":3,
                           "original_author_result":{"status":"AUTHOR_SCORED","original_author_score":0.5}},
             }},
        ]
        agg=paired_summary(pair,selected_count=2)
        self.assertEqual(agg["paired_tasks_recorded"],2)
        self.assertFalse(agg["full_45_intention_to_test_complete"])
        self.assertTrue(agg["incomplete_result_not_a_full_45_score"])
        self.assertAlmostEqual(agg["arms"]["XML"]["author_mean_zero_filled"],0.5)
        self.assertAlmostEqual(agg["arms"]["PYTHON"]["author_mean_zero_filled"],0.625)
        self.assertAlmostEqual(agg["paired_mean_delta_xml_minus_python"],-0.125)
        self.assertEqual(agg["arms"]["XML"]["explicit_unsupported_backend_task_count"],1)
        self.assertIsNone(agg["independent_strict_binary_success_rates"])
        self.assertEqual(agg["category_breakdown"]["geometry"]["XML"]["original_author_full_marks_count"],0)

    def test_reject_double_counted_task(self):
        duplicated={"task_id":"test_05","crud":"create","category":"basic",
                    "arms":{"XML":{},"PYTHON":{}}}
        with self.assertRaises(ValueError):
            paired_summary([duplicated,duplicated],selected_count=2)

@unittest.skipUnless(AUTHOR.is_dir() and DATA.is_dir(),"Pinned original author/data not mounted")
class OriginalPapersOfflineTests(unittest.TestCase):
    def test_original_45_frozen_public_questions_no_provider(self):
        plan=offline_preflight(AUTHOR,DATA)
        self.assertEqual(plan["status"],"PROTOCOL_PREPARED_NO_MODEL_REQUESTS")
        self.assertEqual(plan["original_45_edit_task_denominator"],45)
        self.assertEqual(plan["xml_previously_projectable_inputs"],36)
        self.assertEqual(plan["xml_previously_unsupported_inputs"],9)
        self.assertEqual(plan["model_calls"],0)
        self.assertFalse(plan["paper_equivalent_full_ifc_backend_coverage"])
        self.assertTrue(plan["new_paid_inference_requires_separate_owner_budget"])
        ids=[x["test_id"] for x in plan["original_tasks"]]
        self.assertIn("test_05",ids)
        self.assertEqual(len(ids),len(set(ids)))
        self.assertTrue(all("public_question" not in x for x in plan["original_tasks"]))

    def test_no_xml_unsupported_source_is_hidden_or_called(self):
        tasks=public_45(AUTHOR,DATA)
        original=next(x for x in tasks if x["test_id"]=="geometry_test_05")
        source=DATA/"ifc"/original["original_source_ifc_relpath"]
        self.assertEqual(original["xml_source_projection_previously_observed"],"BLOCKED")
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(Exception,"IFC4X3"):
                XmlSourceEditSession(source,Path(d)/"xml")

    def test_matched_pair_offline_fake_model_and_original_author_grader(self):
        """Full XML + Python arms with original author-grade, zero real LLM."""
        from lxml import etree
        tasks=public_45(AUTHOR,DATA)
        t=next(x for x in tasks if x["test_id"]=="test_05")
        source=DATA/"ifc"/t["original_source_ifc_relpath"]
        # Prepare a developer-authored known-positive *XML test fixture* only.
        # The user-visible benchmark record never counts these as model output.
        with tempfile.TemporaryDirectory(prefix="matched25-paired-") as d:
            root=Path(d)
            public=XmlSourceEditSession(source,root/"prep")
            tree=etree.fromstring(public.original_xml)
            ns=etree.QName(tree).namespace
            level=next(x for x in tree.find("{"+ns+"}Levels") if x.get("elevation")=="0")
            etree.SubElement(tree.find("{"+ns+"}Elements"),"{"+ns+"}Wall",attrib={
                "id":"offline_pair_wall","level":level.get("id"),"x1":"0",
                "y1":"-10","z1":"0","x2":"15","y2":"-10",
                "z2":"0","height":"3","thickness":"0.2",
            })
            full=etree.tostring(tree,encoding="unicode")
            fake=OfflineFakeClient([
                [_FunctionCall("read_building_xml","{}","xml1")],
                [_FunctionCall("submit_building_xml",json.dumps({"xml_text":full}),"xml2")],
                [],
                [_FunctionCall("execute_ifc_code",json.dumps({
                    "code":"result=ifc.by_type('IfcWall')[0].GlobalId;commit()"
                }),"py1")],
                [],
            ])
            result=run_one_pair(fake,t,AUTHOR,DATA,root/"both")
            self.assertEqual(result["arms"]["XML"]["tool_calls"],2)
            self.assertEqual(result["arms"]["PYTHON"]["tool_calls"],1)
            self.assertEqual(result["arms"]["XML"]["original_author_result"]["status"],"AUTHOR_SCORED")
            self.assertEqual(result["arms"]["XML"]["original_author_result"]["original_author_score"],1.0)
            self.assertEqual(result["arms"]["PYTHON"]["original_author_result"]["status"],"AUTHOR_SCORED")
            self.assertEqual(fake.responses.calls,5)
            self.assertTrue((root/"both"/"pair_summary.json").is_file())
            self.assertEqual(result["arms"]["XML"]["status"],"MODEL_FINAL_MESSAGE")
            self.assertEqual(result["arms"]["PYTHON"]["status"],"MODEL_FINAL_MESSAGE")

if __name__=="__main__":
    unittest.main()
