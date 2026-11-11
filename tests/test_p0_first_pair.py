"""#97: prepare real LLM pair prompts; mock transport is NOT a model trial.

Only the integration test's FakeClient uses preauthored oracles. The live
runner MUST consume actual provider-generated outputs from two real calls;
none of these tests proves a model solved the task or makes a paid request.
"""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import json
import unittest

from tools import p0_first_pair as p0
from tests.security.test_generated_candidate import OWN_DYNAMIC_PROGRAM
from src.runner.generated_candidate import run_offline_own_generated_candidate
from src.runner.docker_isolation import DockerIsolationError
from hashlib import sha256


class FakeResponses:
    def __init__(self,outputs):
        self.outputs=outputs
        self.count=0
        self.requests=[]
        self.responses=self
    def create(self,**kwargs):
        self.requests.append(kwargs)
        self.count+=1
        return SimpleNamespace(
            status="completed",
            output_text=self.outputs[self.count-1],
            usage=SimpleNamespace(input_tokens=2500,output_tokens=450),
        )


def fake_approved():
    return {
        "approved":True,
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/97",
        "model":"mock-transport-not-an-llm",
        "input_rate_per_million_usd":"0.5",
        "output_rate_per_million_usd":"2.0",
        "cap_usd":"1.0",
        "price_reference":"https://developers.openai.com/api/docs/pricing",
        "price_checked_utc":"2026-11-12T00:00:00Z",
        "max_output_tokens":3500,
    }


class FirstRealPairPrepTests(unittest.TestCase):
    def test_offline_preparation_uses_only_own_bim_and_matches_context(self):
        p=p0.manifest()
        self.assertEqual(p["status"],"PREPARED_ZERO_LLM_CALLS")
        self.assertTrue(p["owned_fixture"])
        self.assertFalse(p["official_bim_edit_task"])
        self.assertEqual(p["provider_calls"],0)
        self.assertEqual(p["paid_spend_usd"],"0")
        d=p["prompts"]["D_XML"]
        i=p["prompts"]["I_PYTHON"]
        self.assertEqual(d["input"].split("Imperative-only")[0].split(
            "Return complete updated XML.")[0].strip(),
            i["input"].split("Imperative-only")[0].strip())
        self.assertIn('height="3"',d["input"])
        self.assertIn('height="3"',i["input"])
        self.assertIn("Return complete updated XML",d["input"])
        self.assertIn("IfcOpenShell",i["input"])
        self.assertNotIn("OWN_DYNAMIC_PROGRAM",d["input"])

    def test_unapproved_budget_and_missing_model_rejected_pre_call(self):
        p=p0.packets()
        cfg=fake_approved()
        cfg["approved"]=False
        with self.assertRaises(ValueError):
            p0.approved_budget(cfg,p)
        cfg=fake_approved()
        cfg["cap_usd"]="0.000001"
        with self.assertRaises(ValueError):
            p0.approved_budget(cfg,p)
        cfg=fake_approved()
        cfg["max_output_tokens"]=7000
        with self.assertRaises(ValueError):
            p0.approved_budget(cfg,p)

    def test_export_overwrite_rejected_before_any_docker_execution(self):
        with TemporaryDirectory(prefix="p0-export-no-overwrite-") as td:
            target=Path(td)/"already_exists.ifc"
            target.write_text("do not overwrite",encoding="utf8")
            original=target.read_bytes()
            with self.assertRaises(DockerIsolationError):
                run_offline_own_generated_candidate(
                    p0.IMAGE_ID,OWN_DYNAMIC_PROGRAM,
                    sha256(OWN_DYNAMIC_PROGRAM).hexdigest(),
                    seed=97,export_verified_own_ifc=target)
            self.assertEqual(target.read_bytes(),original)

    def test_own_source_and_output_code_are_not_embedded_in_provider_input(self):
        p=p0.packets()
        for key in ("D_XML","I_PYTHON"):
            self.assertNotIn("expected_wall_height.ifc",p[key]["input"])
            self.assertNotIn("ground_truth",p[key]["input"])
            self.assertNotIn("solid.Depth=3.3",p[key]["input"])


class FakeTransportIntegrationTests(unittest.TestCase):
    def test_preauthored_oracles_through_fake_transport_verify_both_paths(self):
        # This is only integration coverage. NEVER count as LLM experiment.
        d=(p0.ROOT/"tests/oracles/xml/update_wall_height.xml").read_text("utf8")
        i=OWN_DYNAMIC_PROGRAM.decode("utf8")
        fake=FakeResponses([d,i])
        with TemporaryDirectory(prefix="p0-fake-model-smoke-") as td:
            folder=Path(td)/"new_run"
            out=p0.run(fake_approved(),folder,client=fake)
            self.assertEqual(out["status"],"FIRST_REAL_LLM_PAIR_ATTEMPTED")
            self.assertTrue(out["two_native_successes"])
            self.assertEqual(out["actual_model_calls_attempted"],2)
            self.assertTrue(out["arms"]["D_XML"]["native_success"])
            self.assertTrue(out["arms"]["I_PYTHON"]["native_success"])
            self.assertEqual(fake.count,2)
            self.assertFalse(any(call["store"] for call in fake.requests))
            self.assertTrue(all(call["tools"]==[] for call in fake.requests))
            self.assertTrue((folder/"D_result.ifc").is_file())
            self.assertTrue((folder/"I_model_generated.py").is_file())
            self.assertTrue((folder/"I_result.ifc").is_file())
            # Exact model-output bytes (not Windows CRLF translated text).
            from hashlib import sha256
            for arm,name in (("D_XML","D_model_generated.xml"),
                             ("I_PYTHON","I_model_generated.py")):
                self.assertEqual(
                    sha256((folder/name).read_bytes()).hexdigest(),
                    out["arms"][arm]["source_sha256"])
            self.assertEqual(
                json.loads((folder/"results.json").read_text("utf8"))["actual_model_calls_attempted"],2)

    def test_exact_provider_source_bytes_without_docker_dependency(self):
        # A source-serialization regression: mock execution/grade only.
        # No LLM API calls or arbitrary Python execution occurs here.
        from unittest.mock import patch
        from hashlib import sha256
        texts=("<Building>\n  <Wall height='3.3'/>\n</Building>\n",
               "import ifcopenshell\nmodel = ifcopenshell.open('input.ifc')\n")
        fake=FakeResponses(list(texts))
        with TemporaryDirectory(prefix="p0-source-byte-roundtrip-") as td:
            folder=Path(td)/"new_run"
            with (patch.object(p0,"_d_output",return_value={"passed":True}),
                  patch.object(p0,"_i_output",return_value={"passed":True})):
                report=p0.run(fake_approved(),folder,client=fake)
            for arm,name,expected in (
                    ("D_XML","D_model_generated.xml",texts[0]),
                    ("I_PYTHON","I_model_generated.py",texts[1])):
                raw=(folder/name).read_bytes()
                self.assertEqual(raw,expected.encode("utf8"))
                self.assertEqual(sha256(raw).hexdigest(),
                                 report["arms"][arm]["source_sha256"])
                self.assertNotIn(b"\r\n",raw)
            self.assertEqual(fake.count,2)

    def test_failed_python_is_explicit_not_hidden_or_retried(self):
        d=(p0.ROOT/"tests/oracles/xml/update_wall_height.xml").read_text("utf8")
        fake=FakeResponses([d,"print('This does not edit IFC')"])
        with TemporaryDirectory(prefix="p0-negative-fake-") as td:
            out=p0.run(fake_approved(),Path(td)/"new_run",client=fake)
            self.assertEqual(fake.count,2)
            self.assertTrue(out["arms"]["D_XML"]["native_success"])
            self.assertFalse(out["arms"]["I_PYTHON"]["native_success"])
            self.assertFalse(out["two_native_successes"])
            self.assertIn("error_type",out["arms"]["I_PYTHON"])


if __name__=="__main__":
    unittest.main()
