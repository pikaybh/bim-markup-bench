"""v0.31 audit tests: offline exact frozen provenance, denominators and honesty."""
from __future__ import annotations

from collections import Counter
from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import audit_bibimbap_v031_eligibility as audit
from tools import audit_bibimbap_v030_reconcile as old


class Original45V031EligibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = audit.eligibility_report()
        cls.encoded = audit.encoded_report(cls.reference)

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="bmb-v031-gate-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "reports").mkdir()
        for name in self.reference["frozen_inputs_sha256"]:
            shutil.copy2(audit.ROOT / "reports" / name, self.root / "reports" / name)

    def test_01_original_45_and_category_crud_denominators(self):
        rows = self.reference["rows"]
        self.assertEqual(len(rows), 45)
        self.assertEqual(len(set(x["task_id"] for x in rows)), 45)
        self.assertEqual(Counter(x["original_category"] for x in rows),
                         {"basic": 15, "geometry": 15, "topological": 15})
        self.assertEqual(Counter(x["original_crud"] for x in rows),
                         {"create": 15, "update": 15, "delete": 15})

    def test_02_priority_tiers_disjoint_exhaustive(self):
        q = self.reference["ordered_offline_audit_queue"]
        self.assertEqual([x["tier"] for x in q], list(audit.TIERS))
        self.assertEqual([len(x["task_ids"]) for x in q], [3, 2, 7, 8, 25])
        self.assertEqual(set(t for x in q for t in x["task_ids"]),
                         {x["task_id"] for x in self.reference["rows"]})
        self.assertEqual(sum(len(x["task_ids"]) for x in q), 45)

    def test_03_three_overlapping_native_pairs_are_not_full_parity(self):
        self.assertEqual(self.reference["original45_developer_witness_and_role_gap_task_ids"],
                         ["geometry_test_18", "geometry_test_19", "test_20"])
        rows = {x["task_id"]: x for x in self.reference["rows"]}
        for task in self.reference["original45_developer_witness_and_role_gap_task_ids"]:
            x = rows[task]
            self.assertTrue(x["developer_original_native_D0_I0_byte_equal_witness"])
            self.assertTrue(x["required_public_source_roles_missing_editable_XML"])
            self.assertFalse(x["task_relevant_native_write_capability_parity_proven"])
            self.assertFalse(x["eligible_for_matched_causal_LLM_trial"])

    def test_04_zero_create_controls_rejects_success_selected_subcohort(self):
        self.assertEqual(self.reference["original45_create_task_developer_native_equal_witnesses"], 0)
        self.assertEqual(self.reference["original45_update_task_developer_native_equal_witnesses"], 4)
        self.assertEqual(self.reference["original45_delete_task_developer_native_equal_witnesses"], 7)
        self.assertEqual(sum(x["developer_original_native_D0_I0_byte_equal_witness"]
                             for x in self.reference["rows"]), 11)

    def test_05_common_observations_are_not_full_source_or_write_parity(self):
        self.assertEqual(self.reference["coarse_necessary_source_role_ref_and_schema_checks_passed_not_sufficient"], 33)
        self.assertEqual(self.reference["full_task_relevant_source_information_equivalence_proven"], 0)
        self.assertEqual(self.reference["full_task_relevant_native_edit_capability_equivalence_proven"], 0)
        self.assertEqual(self.reference["matched_LLM_trial_eligible_tasks"], 0)
        self.assertEqual(self.reference["matched_D_I_LLM_trials_executed"], 0)
        for x in self.reference["rows"]:
            self.assertFalse(x["task_relevant_complete_read_information_parity_proven"])
            self.assertFalse(x["task_relevant_native_write_capability_parity_proven"])
            self.assertFalse(x["eligible_for_matched_causal_LLM_trial"])
            self.assertEqual(x["actual_matched_LLM_outcome"], "NOT_RUN")
            self.assertFalse(x["missing_witness_may_be_counted_as_failure"])

    def test_06_known_schema_and_named_public_reference_gaps_exact(self):
        rows = {x["task_id"]: x for x in self.reference["rows"]}
        for name in ("geometry_test_03", "geometry_test_04", "geometry_test_05"):
            self.assertEqual(rows[name]["XML_schema_and_unit_admission_necessary_check"], "REJECTS_INPUT")
        self.assertEqual(set(self.reference["ordered_offline_audit_queue"][1]["task_ids"]),
                         {"topological_test_01", "topological_test_20"})

    def test_07_author_scorer_diagnostics_separate_from_model_success(self):
        self.assertEqual(self.reference["original45_author_callable_developer_witnesses"], 9)
        self.assertEqual(self.reference["original45_original_author_reference_source_mismatch_witnesses"], 2)
        self.assertEqual(Counter(r["original_author_grader_developer_witness_status"]
                                 for r in self.reference["rows"]),
                         {"AUTHOR_SCORED_DEVELOPER_CONTROL": 9,
                          "AUTHOR_REFERENCE_SOURCE_MISMATCH": 2,
                          "NOT_EVALUATED_UNDETERMINED": 34})

    def test_08_recompute_bytes_deterministic(self):
        self.assertEqual(self.encoded, audit.encoded_report(audit.eligibility_report(self.root)))
        self.assertEqual(self.encoded, audit.encoded_report(audit.eligibility_report()))
        self.assertEqual(len(self.reference["frozen_inputs_sha256"]), 9)

    def test_09_source_evidence_immutable_during_audit(self):
        before = {p.name: sha256(p.read_bytes()).hexdigest()
                  for p in (self.root / "reports").iterdir()}
        audit.eligibility_report(self.root)
        after = {p.name: sha256(p.read_bytes()).hexdigest()
                 for p in (self.root / "reports").iterdir()}
        self.assertEqual(before, after)

    def test_10_prior_reconciliation_tampered_fails_closed(self):
        path = self.root / "reports" / audit.RECONCILED[0]
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(audit.EvidenceError, "hash mismatch"):
            audit.eligibility_report(self.root)

    def test_11_prior_source_roles_tampered_fails_closed(self):
        path = self.root / "reports" / audit.ROLES[0]
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(audit.EvidenceError, "hash mismatch"):
            audit.eligibility_report(self.root)

    def test_12_historical_public_provenance_tampered_fails_closed(self):
        path = self.root / "reports" / audit.BASE[0]
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(audit.EvidenceError, "hash mismatch"):
            audit.eligibility_report(self.root)

    def test_13_upstream_sixth_witness_tampered_fails_closed(self):
        path = self.root / "reports" / old.NEW_CASES[-1][0]
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(audit.EvidenceError, "hash mismatch"):
            audit.eligibility_report(self.root)

    def test_14_missing_input_fails_closed(self):
        (self.root / "reports" / audit.ROLES[0]).unlink()
        with self.assertRaisesRegex(audit.EvidenceError, "Missing or linked report"):
            audit.eligibility_report(self.root)

    def test_15_reconciliation_replay_is_mandatory(self):
        with patch.object(old, "reconciled_report", return_value={}):
            with self.assertRaisesRegex(audit.EvidenceError, "differs from independent replay"):
                audit.eligibility_report(self.root)

    def test_16_public_source_role_claim_drift_fails_closed(self):
        real_loader = old.load_pinned
        def substitute(root, name, expected):
            result = real_loader(root, name, expected)
            if name == audit.ROLES[0]:
                result = copy.deepcopy(result)
                x = result["all45_per_task_actual_source_role_and_admission_rows"]
                x[0]["required_roles_with_missing_editable_XML_objects"] = ["Wall", "Wall"]
            return result
        with patch.object(old, "load_pinned", side_effect=substitute):
            with self.assertRaises(audit.EvidenceError):
                audit.eligibility_report(self.root)

    def test_17_source_bytes_questions_and_hidden_targets_not_serialized(self):
        encoded = self.encoded.decode("utf8").lower()
        for forbidden in ("hidden_target", "target_guid", "original_public_question_text",
                          "ground_truth", "api_key", "native_ifc_sha256",
                          "original_public_question_sha256"):
            self.assertNotIn(forbidden, encoded)
        self.assertLess(len(self.encoded), 75000)

    def test_18_published_report_bytes_match_exact(self):
        path = audit.ROOT / "reports" / "bibimbap_v031_original45_eligibility_and_overlap_20261117.json"
        self.assertTrue(path.is_file(), "Must freeze versioned v0.31 report")
        self.assertEqual(path.read_bytes(), self.encoded)

    def test_19_write_once_cli_and_check_cli(self):
        output = self.root / "report_once.json"
        with patch.object(sys, "argv", ["audit", "--root", str(self.root),
                                        "--write", str(output)]):
            with redirect_stdout(StringIO()):
                audit.main()
        self.assertEqual(output.read_bytes(), self.encoded)
        with patch.object(sys, "argv", ["audit", "--root", str(self.root),
                                        "--write", str(output)]):
            with self.assertRaises(FileExistsError):
                with redirect_stdout(StringIO()):
                    audit.main()
        with patch.object(sys, "argv", ["audit", "--root", str(self.root),
                                        "--check", str(output)]):
            with redirect_stdout(StringIO()) as stdout:
                audit.main()
        self.assertIn("EXACT_MATCH", stdout.getvalue())

    def test_20_report_mutation_detected_by_check(self):
        output = self.root / "report_check.json"
        output.write_bytes(self.encoded + b" ")
        with patch.object(sys, "argv", ["audit", "--root", str(self.root),
                                        "--check", str(output)]):
            with self.assertRaisesRegex(audit.EvidenceError, "differs"):
                audit.main()


if __name__ == "__main__":
    unittest.main()
