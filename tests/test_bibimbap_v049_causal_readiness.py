"""Positive and adversarial tests for the offline v0.49 causal admission gate."""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import audit_bibimbap_v049_causal_readiness as gate


ROOT = Path(__file__).resolve().parents[1]


class V049CausalIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = gate.build_report(ROOT)
        cls.raw = gate.canonical_bytes(cls.report)

    def test_reproducible_exact_frozen_report(self):
        self.assertEqual((ROOT / "reports" / gate.REPORT_NAME).read_bytes(), self.raw)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), "14a3dd1bd2a00c4fbd7efdafca88c89d00b7c4d247152782d53055b494d54478")
        self.assertEqual(gate.canonical_bytes(gate.build_report(ROOT)), self.raw)

    def test_original_population_and_four_explicitly_selected_tasks(self):
        r = self.report
        self.assertEqual(r["original_public_population"], {"tasks": 45, "unique_source_ifcs": 31, "create": 15, "update": 15, "delete": 15})
        self.assertEqual(r["other_original_tasks_outside_pilot"], 41)
        self.assertEqual({x["task_id"] for x in r["exploratory_post_selected_four_original_tasks"]}, set(gate.FOUR_TASKS))
        self.assertTrue(r["primary_estimand"]["four_selected_tasks_are_exploratory_not_confirmatory"])
        self.assertTrue(all(len(x["public_question_sha256"]) == len(x["original_source_ifc_sha256"]) == 64 for x in r["exploratory_post_selected_four_original_tasks"]))

    def test_neither_xml_command_surface_nor_python_ast_is_primary(self):
        self.assertEqual(gate.classify_claim(gate.AUX_XML, gate.AUX_PYTHON), "AUXILIARY_RESTRICTED_TYPED_CONTRAST_ONLY")
        self.assertEqual(gate.classify_claim(gate.PRIMARY_D, gate.PRIMARY_I), "PRIMARY_CAUSAL_CONTRAST_CONCEPT")
        self.assertIn("NOT the direct declarative D arm", self.report["surface_identity"][gate.AUX_XML])
        self.assertIn("NOT I arm", self.report["surface_identity"][gate.AUX_PYTHON])

    def test_mixed_or_mislabeled_arm_interfaces_fail_closed(self):
        for arms in (
            (gate.AUX_XML, gate.PRIMARY_I),
            (gate.PRIMARY_D, gate.AUX_PYTHON),
            (gate.AUX_XML, gate.AUX_XML),
            (gate.PRIMARY_D, gate.PRIMARY_D),
            ("D_XML_NATIVE_EDIT_PLAN", gate.AUX_PYTHON),
            ("UNKNOWN", gate.PRIMARY_I),
        ):
            with self.subTest(arms=arms), self.assertRaises(gate.EvidenceError):
                gate.classify_claim(*arms)

    def test_paid_trial_cannot_launch_from_offline_gate_even_all_flags(self):
        fields = {
            "authorized_paid_budget": True,
            "approved_model_and_tokenizer": True,
            "verified_original_author_evaluator": True,
            "verified_unrestricted_python_sandbox": True,
            "verified_declarative_state_writer": True,
        }
        with self.assertRaisesRegex(gate.EvidenceError, "non-executing"):
            gate.demand_trial_admission(gate.classify_claim(gate.PRIMARY_D, gate.PRIMARY_I), **fields)

    def test_unapproved_or_auxiliary_launch_refused(self):
        with self.assertRaisesRegex(gate.EvidenceError, "Auxiliary"):
            gate.demand_trial_admission(gate.classify_claim(gate.AUX_XML, gate.AUX_PYTHON))
        with self.assertRaisesRegex(gate.EvidenceError, "D-state"):
            gate.demand_trial_admission(gate.classify_claim(gate.PRIMARY_D, gate.PRIMARY_I))

    def test_no_invented_author_grades_tokens_or_costs(self):
        r = self.report
        self.assertIsNone(r["auxiliary_restricted_surface_evidence"]["original_author_scores"])
        self.assertIsNone(r["primary_estimand"]["author_benchmark_score"])
        self.assertIsNone(r["primary_estimand"]["token_count_by_model"])
        self.assertIsNone(r["primary_estimand"]["paid_usd_cost"])
        self.assertFalse(r["launch_gate"]["model_launch_allowed"])
        self.assertEqual(r["no_external_actions"]["paid_model_calls"], 0)
        self.assertEqual(r["no_external_actions"]["original_ifc_mutations"], 0)

    def test_prior_reports_hash_pins_are_exact(self):
        for version, (filename, expected) in gate.SOURCE_REPORTS.items():
            with self.subTest(version=version):
                self.assertEqual(gate._raw_hash(ROOT / "reports" / filename), expected)
                self.assertEqual(self.report["prior_frozen_report_sha256"][version], expected)

    def test_reject_tampered_prior_frozen_hash(self):
        # Use a disposable isolated directory; NEVER edit the original frozen reports.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "reports").mkdir()
            for filename, _ in gate.SOURCE_REPORTS.values():
                shutil.copyfile(ROOT / "reports" / filename, root / "reports" / filename)
            shutil.copyfile(ROOT / "AGENTS.md", root / "AGENTS.md")
            (root / "docs").mkdir()
            shutil.copyfile(ROOT / "docs" / "ARCHITECTURE.md", root / "docs" / "ARCHITECTURE.md")
            filename = gate.SOURCE_REPORTS["v047"][0]
            with (root / "reports" / filename).open("ab") as file:
                file.write(b" ")
            with self.assertRaisesRegex(gate.EvidenceError, "Frozen SHA mismatch"):
                gate.build_report(root)

    def test_reject_research_semantic_oracle_as_author_score(self):
        data, _ = gate._read_evidence(ROOT)
        bad = copy.deepcopy(data["v048"])
        bad["author_original_evaluator_equivalence_proven"] = True
        with self.assertRaisesRegex(gate.EvidenceError, "author evaluator"):
            gate._source_rows(data["v047"], bad)
        bad = copy.deepcopy(data["v048"])
        bad["original_author_benchmark_task_score_claimed"] = True
        with self.assertRaisesRegex(gate.EvidenceError, "benchmark result"):
            gate._source_rows(data["v047"], bad)

    def test_reject_prior_code_overclaims_and_missing_source_parity(self):
        data, _ = gate._read_evidence(ROOT)
        bad = copy.deepcopy(data["v047"])
        bad["default_original_benchmark_Python_IfcOpenShell_unrestricted_tool_equivalent"] = True
        with self.assertRaisesRegex(gate.EvidenceError, "misreported"):
            gate._source_rows(bad, data["v048"])
        bad = copy.deepcopy(data["v047"])
        bad["original_four_paired_rows"][0]["source_XML_read_SHA_identical_both_arms"] = "bogus"
        with self.assertRaisesRegex(gate.EvidenceError, "digest"):
            gate._source_rows(bad, data["v048"])

    def test_reject_unblinded_developer_example_as_llm_solution(self):
        data, _ = gate._read_evidence(ROOT)
        bad = copy.deepcopy(data["v047"])
        bad["original_four_paired_rows"][2]["developer_generated_illustrative_candidate_NOT_original_task_solution"] = False
        with self.assertRaisesRegex(gate.EvidenceError, "Unblinded"):
            gate._source_rows(bad, data["v048"])
        bad = copy.deepcopy(data["v047"])
        bad["original_four_paired_rows"][1]["original_task_semantic_success_or_score_proven"] = True
        with self.assertRaisesRegex(gate.EvidenceError, "task success"):
            gate._source_rows(bad, data["v048"])

    def test_reject_45_task_denominator_promotion(self):
        data, _ = gate._read_evidence(ROOT)
        bad = copy.deepcopy(data["v047"])
        bad["original_45_equal_native_write_authority_proven"] = True
        with self.assertRaisesRegex(gate.EvidenceError, "full coverage"):
            gate._source_rows(bad, data["v048"])

    def test_writing_existing_report_must_fail(self):
        with mock.patch("sys.argv", ["gate", "--root", str(ROOT), "--write"]):
            with self.assertRaises(FileExistsError):
                gate.main()


if __name__ == "__main__":
    unittest.main()
