"""Source-equivalent imperative arm submission, static preflight and hard no-exec."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import ifcopenshell

from src.direct_markup.agent_runner import (
    SourceOnlySettings, stage_source_only_workspace, SourceFileEdit,
    TrustedCompilationController
)
from src.imperative_control.agent_runner import (
    ControlConfig, CandidateCode,create_matched_observations,
    ImperativeControlSession,UnsafeExecutionBlocked,
)
from src.imperative_control.tool_policy import (
    preflight_generated_python,ImperativePreflightError,
)
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference
from tests.oracles.python.independent_ifc_checker import parity_report

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tests/fixtures/synthetic/input.ifc"
TASK={
    "task_id":"OWN-G2-MATCHED-INPUT-001",
    "instruction":"Change North Wall height from 3 to 3.3 m.",
    "input_file":"input.ifc",
}
VALID_CODE=b'''import ifcopenshell
model = ifcopenshell.open("input.ifc")
wall = model.by_type("IfcWall")[0]
wall.Name = "test"
model.write("result.ifc")
'''


class TraceSchemaTests(unittest.TestCase):
    def test_schema_validates_nonexecuted_control_trace(self):
        import jsonschema
        schema=json.loads((ROOT/"schemas/imperative_preflight_trace.schema.json").read_text())
        data=create_matched_observations(SOURCE,TASK)
        session=ImperativeControlSession(data,ControlConfig())
        session.submit_code(CandidateCode(data.input_ifc_sha256,VALID_CODE.decode()))
        jsonschema.validate(session.trace(),schema)
        self.assertFalse(session.trace()["python_executed"])
        self.assertFalse(session.trace()["model_provider_called"])

class MatchedObservationTests(unittest.TestCase):
    def test_both_arms_have_identical_core_model_context_and_source(self):
        with tempfile.TemporaryDirectory() as t:
            direct=stage_source_only_workspace(
                SOURCE,Path(t)/"direct",TASK,SourceOnlySettings())
            visible=direct.agent_visible_context()
            data=create_matched_observations(SOURCE,TASK)
            self.assertEqual(data.task_id,visible.task_id)
            self.assertEqual(data.instruction,visible.instruction)
            self.assertEqual(data.model_xml_text,visible.xml_text)
            self.assertEqual(data.toy_language_spec,visible.language_spec)
            self.assertEqual(data.input_ifc_sha256,
                hashlib.sha256(SOURCE.read_bytes()).hexdigest())
            session=ImperativeControlSession(data,ControlConfig())
            view=session.model_visible_context()
            self.assertEqual(view["model_xml_text"],visible.xml_text)
            self.assertEqual(view["instruction"],visible.instruction)
            self.assertIn("ifcopenshell",view["api_reference_notes"])
            self.assertNotIn("ground_truth_ifc",json.dumps(view))
            self.assertNotIn("OPENAI_API_KEY",json.dumps(view))
            self.assertEqual(view["allowed_execution_operations"],[])
            self.assertFalse(view["OS_sandbox_available"])

    def test_static_policy_accepts_legitimate_ifcopenshell_source_as_text(self):
        check=preflight_generated_python(VALID_CODE)
        self.assertTrue(check.syntax_only_pass)
        self.assertFalse(check.execution_authorized)
        self.assertIn("ifcopenshell",check.imported_roots)
        self.assertEqual(check.source_sha256,hashlib.sha256(VALID_CODE).hexdigest())
        self.assertFalse(check.as_dict()["OS_sandbox_available"])

    def test_accepted_python_source_is_never_executed(self):
        with tempfile.TemporaryDirectory() as t:
            data=create_matched_observations(SOURCE,TASK)
            baseline=ImperativeControlSession(data,ControlConfig())
            result=baseline.submit_code(CandidateCode(
                data.input_ifc_sha256,VALID_CODE.decode("utf-8")))
            self.assertEqual(result["status"],"ACCEPTED_SOURCE_ONLY_NOT_EXECUTABLE")
            self.assertFalse(result["executed"])
            with self.assertRaisesRegex(UnsafeExecutionBlocked,"isolated OS"):
                baseline.execute_generated_solution()
            self.assertFalse((Path(t)/"result.ifc").exists())
            trace=baseline.trace()
            self.assertFalse(trace["python_executed"])
            self.assertEqual(trace["attempt_count"],1)
            self.assertEqual(trace["events"][0]["api_runtime_calls"],0)
            self.assertIsNone(trace["events"][0]["actual_model_tokens"])

    def test_trusted_manual_oracle_and_direct_xml_ifc_are_equivalent(self):
        # I0 independent G1 oracle is trusted, manually reviewed source;
        # NOT the user's generated or submitted solution.py.
        before=SOURCE.read_bytes()
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            session=stage_source_only_workspace(
                SOURCE,root/"direct",TASK,SourceOnlySettings())
            context=session.agent_visible_context()
            old='height="3" thickness="0.2"'
            patch=SourceFileEdit("building.xml",context.xml_byte_sha256,
                                 "surgical_patch",old,'height="3.3" thickness="0.2"')
            self.assertEqual(session.attempt(patch)["status"],"ACCEPTED_VALID_XML")
            D0=root/"direct.ifc"
            TrustedCompilationController.compile_accepted(session,SOURCE,D0)
            I0=root/"control.ifc"
            source=ifcopenshell.open(str(SOURCE))
            wall=source.by_type("IfcWall")[0]
            manual_ifc_reference(SOURCE,I0,"UPDATE_WALL_HEIGHT",
                                 target_guid=wall.GlobalId,height=3.3)
            self.assertTrue(parity_report(D0,I0)["parity"])
            self.assertEqual(before,SOURCE.read_bytes())

class BadCodeStaticPolicyTests(unittest.TestCase):
    def test_obvious_unsafe_execution_and_secret_reads_are_rejected(self):
        unsafe=(
            b'import os\nos.system("whoami")\n',
            b'import subprocess\nsubprocess.run(["ls"])\n',
            b'import socket\nsocket.socket()\n',
            b'from pathlib import Path\nPath("/grader").read_text()\n',
            b'from urllib.request import urlopen\n',
            b'open("/etc/passwd").read()\n',
            b'eval("1+1")\n',
            b'exec("print(1)")\n',
            b'__import__("os")\n',
            b'bad = (1).__class__.__mro__\n',
            b'ground_truth_ifc = "secret"\n',
            b'import importlib\n',
            b'from .internal import secret\n',
            b'from builtins import open\n',
        )
        for text in unsafe:
            with self.subTest(text=text[:35]),self.assertRaises(ImperativePreflightError):
                preflight_generated_python(text)

    def test_invalid_encoding_empty_large_source_blocked(self):
        for source in (b'',b'\xff',b'a='+(b"x"*(65*1024)),b'print('):
            with self.subTest(size=len(source)),self.assertRaises(ImperativePreflightError):
                preflight_generated_python(source)

    def test_hidden_gt_task_payload_rejected_by_same_frontier(self):
        bad=dict(TASK,ground_truth_ifc="secret.ifc")
        with self.assertRaises(Exception):
            create_matched_observations(SOURCE,bad)

    def test_stale_source_sha_rejected_and_refuses_execute(self):
        data=create_matched_observations(SOURCE,TASK)
        runner=ImperativeControlSession(data,ControlConfig())
        result=runner.submit_code(CandidateCode("0"*64,VALID_CODE.decode()))
        self.assertEqual(result["status"],"REJECTED")
        self.assertFalse(result["executed"])
        with self.assertRaises(UnsafeExecutionBlocked):
            runner.execute_generated_solution()
        self.assertEqual(runner.trace()["events"][0]["reject_reason"],"SOURCE_SHA_MISMATCH")

    def test_one_shot_and_feedback_budgets_strictly_separate(self):
        for kwargs in (
            {"mode":"one_shot","max_attempts":2},
            {"mode":"feedback","max_attempts":0},
            {"mode":"feedback","max_attempts":6},
            {"max_wall_seconds":181},
            {"max_output_bytes":65537},
        ):
            with self.subTest(kwargs=kwargs),self.assertRaises(UnsafeExecutionBlocked):
                ControlConfig(**kwargs)
        data=create_matched_observations(SOURCE,TASK)
        runner=ImperativeControlSession(data,ControlConfig("feedback",2))
        first=runner.submit_code(CandidateCode(data.input_ifc_sha256,"import os\n"))
        self.assertEqual(first["status"],"REJECTED")
        second=runner.submit_code(CandidateCode(data.input_ifc_sha256,VALID_CODE.decode()))
        self.assertEqual(second["status"],"ACCEPTED_SOURCE_ONLY_NOT_EXECUTABLE")
        self.assertEqual(runner.trace()["attempt_count"],2)
        self.assertFalse(runner.trace()["python_executed"])

    def test_no_generated_python_is_written_or_run_by_preflight(self):
        before=SOURCE.read_bytes()
        with tempfile.TemporaryDirectory() as t:
            data=create_matched_observations(SOURCE,TASK)
            runner=ImperativeControlSession(data,ControlConfig())
            code='import ifcopenshell\nf=ifcopenshell.open("input.ifc")\nf.write("result.ifc")\n'
            runner.submit_code(CandidateCode(data.input_ifc_sha256,code))
            self.assertEqual(list(Path(t).iterdir()),[])
            self.assertEqual(before,SOURCE.read_bytes())
            self.assertFalse(runner.trace()["OS_sandbox_available"])

if __name__=="__main__":unittest.main()
