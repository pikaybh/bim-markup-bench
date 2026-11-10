"""No-provider, no-GT fairness and token-accounting guard regressions.

Exact UTF-8 bytes and hashes are measurable; actual model tokens/cost are
UNKNOWN until a real approved provider transport and tokenizer are pinned.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.direct_markup.agent_runner import AgentVisibleSource
from src.imperative_control.agent_runner import MatchedObservations
from src.runner.offline_context_cost_gate import (
    OfflineContextGateError,component,matched_shared_components,
    verify_overlay_pair,_bounded_plan_readiness,evaluate_release_gate,
    audit_one_frozen_real_context,
)
from src.runtime.space_semantics_candidate import project_space_semantics_candidate
from src.data.bim_edit import read_tasks,repo_asset_path,verify_local_asset_bytes
from src.data.pilot_asset_audit import _files_in_root


ROOT=Path(__file__).resolve().parents[1]
SOURCE_SHA="a"*64
D=AgentVisibleSource(task_id="ONLY_PUBLIC_TASK",
                     instruction="Add one wall.",
                     filename="building.xml",
                     xml_text="<Building/>",
                     language_spec="XML source only",
                     xml_byte_sha256="0"*64)
I=MatchedObservations(task_id=D.task_id,
                      instruction=D.instruction,
                      model_xml_text=D.xml_text,
                      toy_language_spec=D.language_spec,
                      input_ifc_sha256=SOURCE_SHA)


def _fixed_source():
    tasks={x["task_id"]:x for x in read_tasks(ROOT/"data/tasks.jsonl")}
    row=tasks["WAL-CRE-SPA-A-003"]
    rel=repo_asset_path(row["input_ifc"])
    entries=json.loads((ROOT/"data/bim_edit_remote_tree.json").read_text("utf8"))
    remote={x["path"]:x for x in entries if x.get("type")=="file"}
    source=_files_in_root((ROOT/"data/ifc").resolve(),rel)
    verify_local_asset_bytes(source,remote[rel])
    return source


class OfflineContextCostAuditTests(unittest.TestCase):
    def test_component_counts_real_utf8_bytes_not_invented_tokens(self):
        note=component("A안 건축")
        self.assertGreater(note.byte_length,note.codepoint_length)
        self.assertEqual(note.sha256,hashlib.sha256("A안 건축".encode()).hexdigest())
        self.assertIsNone(note.as_dict()["provider_input_tokens"])
        self.assertIsNone(note.as_dict()["billable_provider_tokens"])

    def test_shared_source_task_and_full_text_match_exactly(self):
        verified=matched_shared_components(D,I,SOURCE_SHA)
        self.assertEqual(set(verified),{
            "public_task_id","public_instruction","v01_source_xml",
            "v01_schema_spec","source_ifc_digest"})
        self.assertTrue(all(value["provider_input_tokens"] is None
                            for value in verified.values()))

    def test_altered_instruction_xml_spec_task_or_digest_fail_closed(self):
        modifications=(
            replace(I,instruction="altered"),
            replace(I,model_xml_text="<Different/>"),
            replace(I,toy_language_spec="another specification"),
            replace(I,task_id="OTHER_TASK"),
            replace(I,input_ifc_sha256="b"*64),
        )
        for altered in modifications:
            with self.subTest(altered=altered):
                with self.assertRaisesRegex(
                    OfflineContextGateError,"D/I common source observation mismatch"):
                    matched_shared_components(D,altered,SOURCE_SHA)

    def test_nonhex_source_digest_and_nontext_not_accepted(self):
        with self.assertRaisesRegex(OfflineContextGateError,"digest"):
            matched_shared_components(D,replace(I,input_ifc_sha256="x"*64),"x"*64)
        with self.assertRaises(OfflineContextGateError):
            component(b"not a string")

    def test_overlay_requires_same_bytes_and_exact_source_only_metadata(self):
        source=_fixed_source()
        valid=project_space_semantics_candidate(source).xml
        proved=verify_overlay_pair(source,valid,valid)
        self.assertEqual(proved["utf8_bytes"],len(valid))
        self.assertFalse(proved["candidate_model_facing_enabled"])
        self.assertFalse(proved["candidate_authoring_answer_exposed"])
        with self.assertRaisesRegex(OfflineContextGateError,"bytes differ"):
            verify_overlay_pair(source,valid,valid+b" ")
        with self.assertRaisesRegex(OfflineContextGateError,"source-verified"):
            verify_overlay_pair(source,b"<SplitSpace/>",b"<SplitSpace/>")

    def test_budget_plan_remains_draft_without_inventing_actual_tokens_or_cost(self):
        base={
            "max_input_tokens_per_attempt":20000,
            "max_output_tokens_per_attempt":6000,
            "max_attempts_per_task":1,
            "study_protocol_status":"DRAFT_NOT_FROZEN",
            "model_id":None,
            "model_provider":None,
            "actual_provider_spend_authorized":False,
            "paid_calls_enabled":False,
        }
        snapshot=_bounded_plan_readiness(base)
        self.assertTrue(snapshot["draft_only"])
        self.assertEqual(snapshot["planned_input_token_limit_per_attempt"],20000)
        self.assertIsNone(snapshot["provider_input_tokens"])
        self.assertIsNone(snapshot["estimated_usd_from_measured_tokens"])
        self.assertFalse(snapshot["live_provider_billing_authorized"])
        for bad in (dict(base,max_input_tokens_per_attempt=0),
                    dict(base,max_attempts_per_task=True)):
            with self.assertRaises(OfflineContextGateError):
                _bounded_plan_readiness(bad)

    def test_pretend_success_flags_cannot_open_model_gate(self):
        fabricated={
            "shared_source_facts_identical":True,
            "proposed_v02_metadata":{"source_only":True},
            "official_evaluator_verified":True,
        }
        verdict=evaluate_release_gate(fabricated)
        self.assertFalse(verdict["all_prerequisites_satisfied"])
        self.assertIsNone(verdict["actual_provider_tokens"])
        self.assertIsNone(verdict["actual_usd_cost"])
        self.assertEqual(verdict["model_calls"],0)

    def test_real_context_and_frozen_pilot_is_audited_without_any_llm_call(self):
        result=audit_one_frozen_real_context(ROOT)
        self.assertTrue(result["shared_source_facts_identical"])
        self.assertTrue(result["proposed_v02_metadata"]["source_only"])
        self.assertEqual(result["v02_candidate_added_exact_utf8_bytes"],2211)
        self.assertTrue(result["input_ifc_original_sha_unchanged"])
        self.assertEqual(result["frozen_pilot"]["frozen_candidate_size"],36)
        self.assertTrue(result["frozen_pilot"][
            "source_classifier_is_conservative_legacy_v01_not_latest_native"])
        self.assertFalse(result["imperative_os_sandbox_available"])
        self.assertFalse(result["official_evaluator_verified"])
        self.assertIsNone(result["real_provider_token_count"])
        self.assertFalse(result["release"]["all_prerequisites_satisfied"])
        self.assertFalse(result["v02_experimental_authoring_answer_present_in_model_input"])
        self.assertFalse(result["source_model_rights_cleared"])
        self.assertEqual(result["release"]["official_task_scores"],0)
        self.assertEqual(result["release"]["model_calls"],0)
        # Serialized audit contains hashes and measurements only, never
        # public prompt, source-room Reference or hidden GT metadata.
        serialized=json.dumps(result,sort_keys=True)
        self.assertNotIn("Add a new",serialized)
        self.assertNotIn("pilotroom 131",serialized)
        self.assertNotIn("ground_truth_ifc",serialized)


if __name__=="__main__":
    unittest.main()
