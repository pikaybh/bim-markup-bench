"""No-LLM direct XML authoring pilot stub and strict file-tool negative cases."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import ifcopenshell
import jsonschema

from src.direct_markup.agent_runner import (
    SourceOnlySettings,SourceFileEdit,stage_source_only_workspace,
    TrustedCompilationController,FileEditBlocked
)
from src.runtime.ifc_projection import project_ifc
from src.security.agent_boundary import SecurityBoundaryError

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tests/fixtures/synthetic/input.ifc"
SCHEMA=json.loads((ROOT/"schemas/file_edit_trace.schema.json").read_text())
TASK={
    "task_id":"OWN-SYNTHETIC-DIRECT-001",
    "instruction":"Change North Wall height from 3m to 3.3m in XML.",
    "input_file":"input.ifc",
}

def start(temp,settings=None):
    return stage_source_only_workspace(
        SOURCE,Path(temp)/"task_workspace",TASK,
        settings or SourceOnlySettings(mode="one_shot",max_attempts=1),
    )

def edit_height(ctx,settings=None):
    before=ctx.xml_text
    match='height="3" thickness="0.2"'
    assert before.count(match)==1
    return SourceFileEdit(
        filename="building.xml",
        expected_sha256=hashlib.sha256(before.encode("utf-8")).hexdigest(),
        mode="surgical_patch",
        old_text=match,
        new_text='height="3.3" thickness="0.2"',
    )

class DirectMarkupPositiveTests(unittest.TestCase):
    def test_stub_file_patch_compiles_to_actual_ifc_without_agent_bim_api(self):
        before=SOURCE.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            session=start(tmp)
            view=session.agent_visible_context()
            self.assertEqual(view.filename,"building.xml")
            self.assertIn("<Building ",view.xml_text)
            self.assertNotIn("ground_truth_ifc",json.dumps(view.exposed()))
            self.assertNotIn("OPENAI_API_KEY",json.dumps(view.exposed()))
            result=session.attempt(edit_height(view))
            self.assertEqual(result["status"],"ACCEPTED_VALID_XML")
            candidate=session.accepted_xml()
            self.assertIn(b'height="3.3"',candidate)
            output=Path(tmp)/"trusted_output.ifc"
            proof=TrustedCompilationController.compile_accepted(session,SOURCE,output)
            model=ifcopenshell.open(str(output))
            wall=model.by_type("IfcWall")[0]
            swept=next(i for rep in wall.Representation.Representations
                       for i in rep.Items if i.is_a("IfcExtrudedAreaSolid"))
            self.assertAlmostEqual(swept.Depth,3.3)
            self.assertEqual(len(model.by_type("IfcRelVoidsElement")),2)
            self.assertEqual(proof.operations[0].operation,"UPDATE_WALL_HEIGHT")
            trace=session.trace()
            jsonschema.validate(trace,SCHEMA)
            self.assertFalse(trace["trusted_compiler_visible_to_agent"])
            self.assertFalse(trace["real_model_provider_called"])
            self.assertTrue(trace["accepted_valid_xml"])
            self.assertEqual([x["status"] for x in trace["events"]],
                             ["READ","ACCEPTED_VALID_XML"])
            self.assertTrue(all(x["agent_BIM_API_calls"]==0 for x in trace["events"]))
            self.assertIn("--- a/building.xml",trace["events"][-1]["unified_diff"])
        self.assertEqual(SOURCE.read_bytes(),before)

    def test_surgical_patch_preserves_comments_order_and_all_stable_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            session=start(tmp)
            ctx=session.agent_visible_context()
            original=ctx.xml_text
            session.attempt(edit_height(ctx))
            edited=session.accepted_xml().decode()
            self.assertEqual(edited,original.replace(
                'height="3" thickness="0.2"','height="3.3" thickness="0.2"',1))
            self.assertEqual(original.count('id="'),edited.count('id="'))
            self.assertEqual(hashlib.sha256((Path(tmp)/"task_workspace"/"input.ifc").read_bytes()).hexdigest(),
                hashlib.sha256(SOURCE.read_bytes()).hexdigest())

    def test_whole_file_rewrite_is_explicit_and_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            session=start(tmp)
            ctx=session.agent_visible_context()
            updated=ctx.xml_text.replace('height="3" thickness="0.2"',
                                         'height="3.25" thickness="0.2"')
            edit=SourceFileEdit("building.xml",
                hashlib.sha256(ctx.xml_text.encode()).hexdigest(),
                "whole_file_rewrite","",updated)
            self.assertEqual(session.attempt(edit)["status"],"ACCEPTED_VALID_XML")
            self.assertIn(b'height="3.25"',session.accepted_xml())

    def test_feedback_is_separate_policy_and_honors_retry_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings=SourceOnlySettings(mode="feedback",max_attempts=2)
            session=start(tmp,settings)
            ctx=session.agent_visible_context()
            invalid=SourceFileEdit(
                "building.xml",hashlib.sha256(ctx.xml_text.encode()).hexdigest(),
                "surgical_patch",'thickness="0.2"','thickness="-0.2"')
            first=session.attempt(invalid)
            self.assertEqual(first["status"],"REJECTED")
            self.assertIsNotNone(first["diagnostic"])
            self.assertEqual(session.agent_visible_context().xml_text,ctx.xml_text)
            second=session.attempt(edit_height(ctx))
            self.assertEqual(second["status"],"ACCEPTED_VALID_XML")
            trace=session.trace()
            jsonschema.validate(trace,SCHEMA)
            self.assertEqual(trace["attempt_count"],2)
            self.assertEqual(trace["mode"],"feedback")
            self.assertFalse(trace["real_model_provider_called"])

class DirectMarkupNegativeTests(unittest.TestCase):
    def test_arbitrary_bim_python_shell_tools_are_denied_and_audited(self):
        with tempfile.TemporaryDirectory() as tmp:
            session=start(tmp)
            session.agent_visible_context()
            for tool in ("ifcopenshell","python","shell","exec","commandbus",
                         "create_wall","bim_api","fetch"):
                with self.subTest(tool=tool),self.assertRaises(FileEditBlocked):
                    session.reject_tool_call(tool,"building.xml")
            trace=session.trace()
            jsonschema.validate(trace,SCHEMA)
            self.assertEqual(sum(e["agent_BIM_API_calls"] for e in trace["events"]),0)
            self.assertTrue(any(e["status"]=="REJECTED_TOOL" for e in trace["events"]))

    def test_gt_files_and_external_paths_are_not_writable(self):
        with tempfile.TemporaryDirectory() as tmp:
            session=start(tmp)
            ctx=session.agent_visible_context()
            for target in ("input.ifc","ground_truth.ifc","../hidden.ifc",
                           "/etc/passwd","solution.py"):
                edit=edit_height(ctx)
                forged=SourceFileEdit(target,edit.expected_sha256,edit.mode,
                                      edit.old_text,edit.new_text)
                with self.subTest(target=target):
                    self.assertEqual(session.attempt(forged)["status"],"REJECTED")
                    if target!="solution.py":
                        # The one-shot limit prevents more attempts; instantiate
                        # a fresh session per forbidden target in below test.
                        break
            self.assertEqual((Path(tmp)/"task_workspace"/"input.ifc").read_bytes(),SOURCE.read_bytes())

    def test_source_file_cannot_be_replaced_by_sibling_or_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            session=start(tmp,SourceOnlySettings(mode="feedback",max_attempts=5))
            ctx=session.agent_visible_context()
            edit=edit_height(ctx)
            for target in ("input.ifc","ground_truth.ifc","../secret.ifc",
                           "/tmp/secret.ifc","solution.py"):
                attempt=SourceFileEdit(target,edit.expected_sha256,edit.mode,
                                       edit.old_text,edit.new_text)
                self.assertEqual(session.attempt(attempt)["status"],"REJECTED")
            self.assertEqual(session.trace()["attempt_count"],5)
            self.assertEqual(ctx.xml_text,
                (Path(tmp)/"task_workspace"/"building.xml").read_text())
            self.assertEqual(SOURCE.read_bytes(),(Path(tmp)/"task_workspace"/"input.ifc").read_bytes())

    def test_bad_xml_rejected_without_last_valid_xml_change_and_no_compile(self):
        with tempfile.TemporaryDirectory() as tmp:
            session=start(tmp)
            ctx=session.agent_visible_context()
            tampered=SourceFileEdit(
                "building.xml",hashlib.sha256(ctx.xml_text.encode()).hexdigest(),
                "whole_file_rewrite","",'<Building><CreateWall/></Building>')
            self.assertEqual(session.attempt(tampered)["status"],"REJECTED")
            with self.assertRaises(FileEditBlocked):
                session.accepted_xml()
            with self.assertRaises(FileEditBlocked):
                TrustedCompilationController.compile_accepted(
                    session,SOURCE,Path(tmp)/"should_not_exist.ifc")
            self.assertEqual((Path(tmp)/"task_workspace"/"building.xml").read_text(),ctx.xml_text)
            self.assertFalse((Path(tmp)/"should_not_exist.ifc").exists())

    def test_stale_sha_and_duplicate_anchor_do_not_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            session=start(tmp,SourceOnlySettings(mode="feedback",max_attempts=2))
            ctx=session.agent_visible_context()
            bad=SourceFileEdit("building.xml","0"*64,"surgical_patch",
                               'height="3"','height="3.4"')
            self.assertEqual(session.attempt(bad)["status"],"REJECTED")
            duplicate=SourceFileEdit("building.xml",
               hashlib.sha256(ctx.xml_text.encode()).hexdigest(),
               "surgical_patch",'height="3"','height="3.4"')
            self.assertEqual(session.attempt(duplicate)["status"],"REJECTED")
            self.assertFalse(session.trace()["accepted_valid_xml"])

    def test_model_context_and_trace_have_no_external_source_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            session=start(tmp)
            ctx=session.agent_visible_context().exposed()
            self.assertEqual(set(ctx),{
                "task_id","instruction","filename","xml_text",
                "language_spec","allowed_operations","xml_byte_sha256"
            })
            for source in ("/Users/pikaybh","ground_truth_ifc","target_guids",
                           "OPENAI_API_KEY","run_python"):
                self.assertNotIn(source,json.dumps(ctx))
            self.assertFalse(session.trace()["real_model_provider_called"])

    def test_predeclared_mode_and_limits_checked(self):
        for args in (
            {"mode":"one_shot","max_attempts":2},
            {"mode":"feedback","max_attempts":10},
            {"mode":"feedback","max_attempts":0},
            {"max_edit_bytes":0},
            {"max_wall_seconds":1000},
            {"context_mode":"full_illicit_oracle"},
        ):
            with self.subTest(args=args),self.assertRaises(FileEditBlocked):
                SourceOnlySettings(**args)

    def test_agent_payload_gt_fields_are_denied_upfront(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad=dict(TASK,ground_truth_ifc="hidden.ifc")
            with self.assertRaises(SecurityBoundaryError):
                stage_source_only_workspace(SOURCE,Path(tmp)/"workspace",
                                            bad,SourceOnlySettings())

if __name__=="__main__":unittest.main()
