"""Demonstrate a crash-safe *synthetic only* token-cost ledger.

No model provider, no network, no official evaluator, no IFC, no hidden GT.
Test token quantities and prices are deliberately invented OFFLINE fixtures
and MUST NEVER be described as real model usage or current USD quotes.
Returns exit 2 to preserve the live-run science gate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from src.runner.durable_budget_dryrun import (
    DryRunBudgetLedger,DryRunBudgetBlocked,DryRunPolicy,
)


def verify_offline_simulation()->dict:
    spec=DryRunPolicy(
        experiment_id="offline-budget-safety-simulation",
        maximum_spend_usd="0.000300",
        hypothetical_input_usd_per_million="1.00",
        hypothetical_output_usd_per_million="1.00",
        max_input_tokens_per_attempt=20000,
        max_output_tokens_per_attempt=6000,
        max_attempts_per_task=2,
        max_concurrent_attempts=2,
    )
    with TemporaryDirectory(prefix="bim-budget-dryrun-") as temporary:
        db=Path(temporary)/"budget.sqlite3"
        meter=DryRunBudgetLedger(db,spec)
        d=meter.reserve(attempt_id="D0-1",task_id="mock-T01",
                        arm="direct_xml",planned_input_tokens=100,
                        planned_output_tokens=50)
        i=meter.reserve(attempt_id="I0-1",task_id="mock-T01",
                        arm="imperative_python",planned_input_tokens=100,
                        planned_output_tokens=50)
        if d["reserved_micro_usd"]!=150 or i["reserved_micro_usd"]!=150:
            raise ValueError("Synthetic D/I envelope mismatch")
        try:
            meter.reserve(attempt_id="D0-2",task_id="mock-T02",
                          arm="direct_xml",planned_input_tokens=100,
                          planned_output_tokens=50)
        except DryRunBudgetBlocked as exc:
            cap_refusal="Budget cap exceeded" in str(exc)
        else:
            cap_refusal=False
        if not cap_refusal:
            raise ValueError("Over-cap request accepted")
        meter.mark_hypothetical_dispatch("D0-1")
        meter.settle_synthetic_usage("D0-1",input_tokens=75,output_tokens=25)
        meter.mark_hypothetical_dispatch("I0-1")
        meter.hold_unknown_usage("I0-1")
        try:
            meter.cancel_proven_unsent("I0-1")
        except DryRunBudgetBlocked as exc:
            uncertain_cancellation_refused="transition" in str(exc)
        else:
            uncertain_cancellation_refused=False
        if not uncertain_cancellation_refused:
            raise ValueError("Unknown dispatch released reserve improperly")
        meter.reserve(attempt_id="D0-3",task_id="mock-T02",
                      arm="direct_xml",planned_input_tokens=25,
                      planned_output_tokens=25)
        meter.cancel_proven_unsent("D0-3")
        reopened=DryRunBudgetLedger(db,spec)
        snap=reopened.snapshot()
        if (snap["attempt_count"]!=3 or
                snap["settled_synthetic_micro_usd"]!=100 or
                snap["outstanding_reserved_micro_usd"]!=150 or
                snap["committed_hypothetical_micro_usd"]!=250 or
                snap["remaining_hypothetical_micro_usd"]!=50 or
                snap["states"]!={"SETTLED_OFFLINE":1,"UNKNOWN_USAGE":1,
                                 "CANCELED_UNSENT":1}):
            raise ValueError("Ledger durability or accounting invariant broken")
    return {
        "status":"PASS_OFFLINE_DURABLE_BUDGET_SIMULATION_LIVE_G3_BLOCKED",
        "experiment_source":"OFFLINE_SYNTHETIC_VALUES_ONLY",
        "tokenizer_provenance":"NO_APPROVED_MODEL_TOKENIZER",
        "provider_token_counts":None,
        "provider_prices_verified":False,
        "real_provider_charges_usd":None,
        "input_context_measurement_upgraded_to_tokens":False,
        "state_after_database_reopen":snap,
        "over_cap_request_rejected":cap_refusal,
        "unknown_usage_refuses_automatic_reservation_release":
            uncertain_cancellation_refused,
        "real_network_or_model_calls":0,
        "official_benchmark_tasks_scored":0,
        "full_g2_or_g3_live_release_authorized":False,
    }


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    report=verify_offline_simulation()
    if args.output_json:
        path=args.output_json
        if path.exists() or path.is_symlink() or not path.parent.is_dir():
            parser.error("Refuse overwritten/symlink/absent evidence path")
        with path.open("x",encoding="utf8",newline="\n") as handle:
            handle.write(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
