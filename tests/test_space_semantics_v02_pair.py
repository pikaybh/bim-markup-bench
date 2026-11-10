"""Proposed D/I Space semantics input is byte-equal but *not* promoted.

No real model API, untrusted Python execution or hidden GT access.
"""
from __future__ import annotations

from dataclasses import replace
import unittest

from tools.audit_space_semantics_v02_pair import (
    CandidatePair,verify_paired_candidate_observation,
    audit_candidate_input_pair,
)


PAIR=CandidatePair(
    instruction="Add an explicitly named interior room",
    source_sha256="a"*64,
    base_xml_bytes=b"<Building/>",
    base_spec_bytes=b"Read/author declarative state only",
    candidate_metadata_bytes=b"<SpaceSemantics/>",
)


class SpaceSemanticsPairedContextTests(unittest.TestCase):
    def test_proposed_context_can_be_identically_materialized(self):
        audit=verify_paired_candidate_observation(PAIR,replace(PAIR))
        self.assertTrue(audit["proposed_paired_source_observation_equal"])
        self.assertFalse(audit["model_facing_v02_enabled"])
        self.assertFalse(audit["input_fairness_and_model_budget_approved"])

    def test_different_instructions_always_fail_proposed_parity(self):
        with self.assertRaisesRegex(ValueError,"payloads differ"):
            verify_paired_candidate_observation(
                PAIR,replace(PAIR,instruction=PAIR.instruction+"!"))

    def test_changed_semantic_xml_detected_even_with_equal_base_xml(self):
        with self.assertRaisesRegex(ValueError,"payloads differ"):
            verify_paired_candidate_observation(
                PAIR,replace(PAIR,candidate_metadata_bytes=b"<Missing/>"))

    def test_changed_base_xml_or_language_spec_detected(self):
        for mutated in (
            replace(PAIR,base_xml_bytes=b"<Different/>"),
            replace(PAIR,base_spec_bytes=b"Different spec"),
            replace(PAIR,source_sha256="b"*64),
        ):
            with self.subTest(kind=mutated):
                with self.assertRaisesRegex(ValueError,"payloads differ"):
                    verify_paired_candidate_observation(PAIR,mutated)

    def test_real_source_has_same_unpromoted_overlay_candidate_in_both_arms(self):
        evidence=audit_candidate_input_pair()
        self.assertTrue(evidence["proposed_paired_source_observation_equal"])
        self.assertEqual(evidence["source_space_count"],2)
        self.assertEqual(evidence["source_type_count"],2)
        self.assertEqual(evidence["source_instance_pset_count"],4)
        self.assertEqual(evidence["source_reference_count"],4)
        self.assertGreater(evidence["candidate_xml_bytes"],1000)
        self.assertFalse(evidence["model_facing_v02_enabled"])
        self.assertFalse(evidence["new_space_type_pset_qto_authoring_compiler_implemented"])
        self.assertEqual(evidence["official_scores"],0)
        self.assertEqual(evidence["model_calls"],0)


if __name__=="__main__":
    unittest.main()
