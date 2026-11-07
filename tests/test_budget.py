"""No paid calls, no API connection. Negative security, malformed and budget scenarios."""
import copy
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from tools.cost_budget import BudgetError, load_config, estimate, guard_paid_execution

ROOT = Path(__file__).resolve().parents[1]

class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.template = json.loads((ROOT / "configs/budget.example.json").read_text())

    def test_expected_initial_cost(self):
        result = estimate(load_config(ROOT / "configs/budget.example.json"))
        self.assertEqual(result["arm_trials"], 72)
        self.assertEqual(Decimal(result["estimated_total_usd"]), Decimal("0.324"))
        self.assertTrue(result["expected_cost_under_cap"])

    def test_paid_run_fails_closed_without_all_three_flags(self):
        conf = self.template
        with self.assertRaisesRegex(BudgetError, "approval"):
            guard_paid_execution(conf)
        for field in ("explicit_budget_approval", "allow_paid_api_calls", "gate_evidence_verified"):
            conf = copy.deepcopy(self.template)
            conf[field] = True
            with self.assertRaises(BudgetError):
                guard_paid_execution(conf)

    def test_even_enabled_paid_run_fails_without_durable_runtime(self):
        conf = copy.deepcopy(self.template)
        for field in ("explicit_budget_approval", "allow_paid_api_calls", "gate_evidence_verified"):
            conf[field] = True
        with self.assertRaisesRegex(BudgetError, "durable"):
            guard_paid_execution(conf)

    def test_malformed_fields_fail_closed(self):
        for key, bad in [
            ("model", "expensive-other-model"),
            ("planned_repetitions", -1),
            ("maximum_total_spend_usd", "NaN"),
            ("maximum_attempts_per_task", True),
            ("allow_paid_api_calls", "true"),
        ]:
            with self.subTest(key=key):
                conf = copy.deepcopy(self.template)
                conf[key] = bad
                with tempfile.TemporaryDirectory() as tmp:
                    p = Path(tmp) / "budget.json"
                    p.write_text(json.dumps(conf))
                    with self.assertRaises(BudgetError):
                        load_config(p)

    def test_exceeding_spend_cap_detected(self):
        conf = copy.deepcopy(self.template)
        conf["planned_repetitions"] = 1000
        self.assertFalse(estimate(conf)["expected_cost_under_cap"])
        for field in ("explicit_budget_approval", "allow_paid_api_calls", "gate_evidence_verified"):
            conf[field] = True
        with self.assertRaisesRegex(BudgetError, "exceeds"):
            guard_paid_execution(conf)

    def test_missing_config_field_denied(self):
        conf = copy.deepcopy(self.template)
        del conf["estimated_output_tokens_per_arm_task"]
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "budget.json"
            p.write_text(json.dumps(conf))
            with self.assertRaisesRegex(BudgetError, "Missing required"):
                load_config(p)

if __name__ == "__main__":
    unittest.main()
