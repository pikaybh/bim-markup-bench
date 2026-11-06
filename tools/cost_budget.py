#!/usr/bin/env python3
"""Conservative, offline pilot pricing estimator and paid-run preflight.

No network connections, imports from OpenAI or API calls are made by this script.
Budget checks here are PRE-RUN ONLY: an eventual runner MUST enforce and persist
reservations/charges across concurrent processes and kill tasks at limit.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class BudgetError(ValueError):
    pass

def nonnegative_decimal(value: object, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise BudgetError(f"{field} must be a decimal number") from exc
    if not result.is_finite() or result < 0:
        raise BudgetError(f"{field} must be nonnegative and finite")
    return result

def load_config(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    required = [
        "model", "service_tier", "price_snapshot", "maximum_total_spend_usd",
        "planned_task_count", "planned_arms_per_task", "planned_repetitions",
        "estimated_input_tokens_per_arm_task", "estimated_output_tokens_per_arm_task",
        "maximum_attempts_per_task", "maximum_wall_seconds_per_task",
        "maximum_output_tokens_per_request", "allow_paid_api_calls",
        "explicit_budget_approval", "gate_evidence_verified",
    ]
    missing = [key for key in required if key not in obj]
    if missing:
        raise BudgetError("Missing required fields: " + ", ".join(missing))
    if obj["model"] != "gpt-6-luna" or obj["service_tier"] != "standard":
        raise BudgetError("Unapproved model/service tier; obtain a new price and budget approval")
    rate = obj["price_snapshot"]
    if not isinstance(rate, dict) or any(k not in rate for k in
            ("input_per_million_usd", "output_per_million_usd", "url", "checked_at_utc")):
        raise BudgetError("Incomplete price snapshot")
    for key in ("input_per_million_usd", "output_per_million_usd"):
        if nonnegative_decimal(rate[key], key) == 0:
            raise BudgetError("Rate cannot be zero")
    if nonnegative_decimal(obj["maximum_total_spend_usd"], "maximum_total_spend_usd") == 0:
        raise BudgetError("Spend cap cannot be zero")
    for key in ("planned_task_count", "planned_arms_per_task", "planned_repetitions",
                "estimated_input_tokens_per_arm_task", "estimated_output_tokens_per_arm_task",
                "maximum_attempts_per_task", "maximum_wall_seconds_per_task",
                "maximum_output_tokens_per_request"):
        val = obj[key]
        if isinstance(val, bool) or not isinstance(val, int) or val <= 0:
            raise BudgetError(f"{key} must be a positive integer")
    for key in ("allow_paid_api_calls", "explicit_budget_approval", "gate_evidence_verified"):
        if type(obj[key]) is not bool:
            raise BudgetError(f"{key} must be boolean")
    return obj

def estimate(obj: dict) -> dict:
    n = obj["planned_task_count"] * obj["planned_arms_per_task"] * obj["planned_repetitions"]
    r = obj["price_snapshot"]
    inp = Decimal(obj["estimated_input_tokens_per_arm_task"])
    out = Decimal(obj["estimated_output_tokens_per_arm_task"])
    one = (inp * nonnegative_decimal(r["input_per_million_usd"], "input_rate") +
           out * nonnegative_decimal(r["output_per_million_usd"], "output_rate")) / Decimal("1000000")
    return {"arm_trials": n, "estimated_total_usd": str(one * n),
            "proposed_spend_cap_usd": str(obj["maximum_total_spend_usd"]),
            "expected_cost_under_cap": one * n <= nonnegative_decimal(obj["maximum_total_spend_usd"], "cap"),
            "assumptions": "Short-context standard, no cache, tools, retries or regional uplift; not a charged estimate"}

def guard_paid_execution(obj: dict) -> None:
    if not (obj["explicit_budget_approval"] and obj["allow_paid_api_calls"] and obj["gate_evidence_verified"]):
        raise BudgetError("BLOCKED: explicit approval, run enablement, and gate evidence are all required")
    if not estimate(obj)["expected_cost_under_cap"]:
        raise BudgetError("BLOCKED: modeled upper-bound cost exceeds approved cap")
    # The actual runner is NOT implemented. Never claim this preflight authorizes API calls.
    raise BudgetError("BLOCKED: no audited, durable token/cost-accounting runtime exists yet")

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=Path, default=ROOT / "configs/budget.example.json")
    p.add_argument("--authorize", action="store_true",
                   help="Only check whether live paid run is allowed; never sends API requests")
    args = p.parse_args()
    try:
        obj = load_config(args.config)
        print(json.dumps(estimate(obj), indent=2, sort_keys=True))
        if args.authorize:
            guard_paid_execution(obj)
        return 0
    except (BudgetError, OSError, json.JSONDecodeError) as exc:
        print("ERROR:", str(exc))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
