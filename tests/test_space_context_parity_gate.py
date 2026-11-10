"""Model-visible core context parity gates on frozen public IFC and mocks.

No model calls, hidden GT, Python code execution or scored experiments.
"""
from __future__ import annotations

from dataclasses import replace
import unittest

from src.direct_markup.agent_runner import AgentVisibleSource
from src.imperative_control.agent_runner import MatchedObservations
from tools.audit_space_metadata_context_parity import (
    audit_one_public_space_context,verify_core_text_observation_parity,
)


SOURCE_HASH="4"*64
DIRECT=AgentVisibleSource(
    task_id="OWN-PUBLIC-INPUT-01",
    instruction="Create one partitioning Wall in an existing Space.",
    filename="building.xml",xml_text="<Building/>",
    language_spec="No execution tools in declarative XML",
    xml_byte_sha256="1"*64)
IMPERATIVE=MatchedObservations(
    task_id=DIRECT.task_id,instruction=DIRECT.instruction,
    model_xml_text=DIRECT.xml_text,toy_language_spec=DIRECT.language_spec,
    input_ifc_sha256=SOURCE_HASH)


class SourceInputParityAuditTests(unittest.TestCase):
    def test_exact_shared_core_context_passes_without_claiming_full_parity(self):
        verified=verify_core_text_observation_parity(DIRECT,IMPERATIVE,SOURCE_HASH)
        self.assertTrue(all(verified.values()))
        self.assertEqual(len(verified),5)

    def test_altered_imperative_instruction_rejected(self):
        wrong=replace(IMPERATIVE,instruction=IMPERATIVE.instruction+" ")
        with self.assertRaisesRegex(ValueError,"source observations diverged"):
            verify_core_text_observation_parity(DIRECT,wrong,SOURCE_HASH)

    def test_altered_imperative_xml_projection_rejected(self):
        wrong=replace(IMPERATIVE,model_xml_text="<Building><Leak/></Building>")
        with self.assertRaisesRegex(ValueError,"source observations diverged"):
            verify_core_text_observation_parity(DIRECT,wrong,SOURCE_HASH)

    def test_altered_language_spec_or_ifc_checksum_rejected(self):
        for wrong in (
            replace(IMPERATIVE,toy_language_spec="Different grammar"),
            replace(IMPERATIVE,input_ifc_sha256="f"*64),
        ):
            with self.subTest(kind=wrong):
                with self.assertRaisesRegex(ValueError,"source observations diverged"):
                    verify_core_text_observation_parity(DIRECT,wrong,SOURCE_HASH)

    def test_real_source_shared_text_matches_but_native_metadata_is_missing(self):
        report=audit_one_public_space_context()
        self.assertTrue(report["core_source_text_context_equal"])
        self.assertTrue(report["native_type_and_psets_omitted_from_xml_projection"])
        self.assertEqual(report["source_ifc_space_type_relation_count"],1)
        self.assertEqual(report["source_ifc_space_instance_pset_relation_count"],2)
        self.assertEqual(report["source_ifc_space_association_count"],0)
        self.assertFalse(report["both_arms_cover_source_native_type_pset"])
        self.assertFalse(report["model_information_equivalence_proven"])
        self.assertEqual(report["official_scores"],0)
        self.assertEqual(report["model_provider_calls"],0)
        self.assertTrue(report["immutable_input_ifc_bytes_preserved"])


if __name__=="__main__":
    unittest.main()
