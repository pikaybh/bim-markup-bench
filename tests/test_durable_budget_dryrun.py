"""Persistent SQLite *offline* quote/usage simulation for issue #20.

Every token count and rate in this file is a synthetic fixture. No paid API,
real tokenizer, provider response or official task/GT is ever opened.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import unittest

from src.runner.durable_budget_dryrun import (
    DryRunBudgetBlocked,DryRunBudgetLedger,DryRunPolicy,
)


def policy(*,cap="0.000300",tries=2,concurrent=3):
    return DryRunPolicy(
        experiment_id="fixture-20",
        maximum_spend_usd=cap,
        hypothetical_input_usd_per_million="1.00",
        hypothetical_output_usd_per_million="1.00",
        max_input_tokens_per_attempt=20000,
        max_output_tokens_per_attempt=6000,
        max_attempts_per_task=tries,
        max_concurrent_attempts=concurrent,
    )


def reserve(ledger,idx=0,*,task=None,arm="direct_xml",
            inp=100,out=50):
    return ledger.reserve(
        attempt_id=f"fixture-{idx}",
        task_id=task or f"TASK-{idx}",
        arm=arm,planned_input_tokens=inp,
        planned_output_tokens=out)


class DurableDryRunLedgerTests(unittest.TestCase):
    def test_two_hypothetical_requests_reserve_and_survive_reopen(self):
        with TemporaryDirectory() as td:
            db=Path(td)/"meter.sqlite3"
            first=DryRunBudgetLedger(db,policy())
            self.assertEqual(reserve(first,1)["reserved_micro_usd"],150)
            self.assertEqual(reserve(first,2)["reserved_micro_usd"],150)
            reopened=DryRunBudgetLedger(db,policy()).snapshot()
            self.assertEqual(reopened["committed_hypothetical_micro_usd"],300)
            self.assertEqual(reopened["remaining_hypothetical_micro_usd"],0)
            self.assertEqual(reopened["attempt_count"],2)
            self.assertIsNone(reopened["actual_provider_tokens"])
            self.assertIsNone(reopened["actual_provider_charges"])
            self.assertEqual(reopened["real_provider_calls"],0)
            self.assertFalse(reopened["paid_run_authorized"])

    def test_six_separate_processes_share_one_atomic_reservation_cap(self):
        with TemporaryDirectory() as td:
            db=Path(td)/"cross-process.sqlite3"
            spec=policy(cap="0.000450",concurrent=10)
            DryRunBudgetLedger(db,spec)
            source="""import sys
from pathlib import Path
from src.runner.durable_budget_dryrun import DryRunBudgetLedger,DryRunBudgetBlocked
from tests.test_durable_budget_dryrun import policy,reserve
try:
    ledger=DryRunBudgetLedger(Path(sys.argv[1]),
                             policy(cap="0.000450",concurrent=10))
    reserve(ledger,int(sys.argv[2]))
except DryRunBudgetBlocked:
    sys.exit(3)
"""
            launched=[subprocess.Popen(
                [sys.executable,"-c",source,str(db),str(i)],
                cwd=Path(__file__).resolve().parents[1],
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True
            ) for i in range(6)]
            completed=[(proc.returncode,stdout,stderr)
                       for proc in launched
                       for stdout,stderr in [proc.communicate(timeout=30)]]
            self.assertEqual(sorted(code for code,_,_ in completed),
                             [0,0,0,3,3,3],msg=completed)
            current=DryRunBudgetLedger(db,spec).snapshot()
            self.assertEqual(current["attempt_count"],3)
            self.assertEqual(current["committed_hypothetical_micro_usd"],450)

    def test_budget_cap_overflow_holds_all_prior_reservations(self):
        with TemporaryDirectory() as td:
            ledger=DryRunBudgetLedger(Path(td)/"meter.sqlite3",policy())
            reserve(ledger,1)
            reserve(ledger,2)
            with self.assertRaisesRegex(DryRunBudgetBlocked,"Budget cap exceeded"):
                reserve(ledger,3)
            self.assertEqual(ledger.snapshot()["attempt_count"],2)

    def test_atomic_concurrent_reservation_does_not_oversubscribe(self):
        with TemporaryDirectory() as td:
            db=Path(td)/"meter.sqlite3"
            spec=policy(cap="0.000450",concurrent=10)
            DryRunBudgetLedger(db,spec)
            def worker(i):
                try:
                    handle=DryRunBudgetLedger(db,spec)
                    reserve(handle,i)
                    return "ACCEPTED"
                except DryRunBudgetBlocked:
                    return "BLOCKED"
            with ThreadPoolExecutor(max_workers=10) as pool:
                results=list(pool.map(worker,range(20)))
            self.assertEqual(results.count("ACCEPTED"),3)
            self.assertEqual(results.count("BLOCKED"),17)
            count=DryRunBudgetLedger(db,spec).snapshot()
            self.assertEqual(count["committed_hypothetical_micro_usd"],450)
            self.assertEqual(count["attempt_count"],3)

    def test_duplicate_attempt_and_max_retries_refused_after_reopen(self):
        with TemporaryDirectory() as td:
            db=Path(td)/"meter.sqlite3"
            ledger=DryRunBudgetLedger(db,policy(cap="0.001",tries=1))
            reserve(ledger,1,task="SAME",arm="direct_xml")
            with self.assertRaisesRegex(DryRunBudgetBlocked,"Duplicate"):
                reserve(DryRunBudgetLedger(db,policy(cap="0.001",tries=1)),
                        1,task="SAME")
            with self.assertRaisesRegex(DryRunBudgetBlocked,"retry budget"):
                reserve(ledger,2,task="SAME",arm="direct_xml")
            reserve(ledger,3,task="SAME",arm="imperative_python")
            self.assertEqual(ledger.snapshot()["attempt_count"],2)

    def test_hypothetical_settlement_reclaims_only_unused_reserved_amount(self):
        with TemporaryDirectory() as td:
            ledger=DryRunBudgetLedger(Path(td)/"meter.sqlite3",policy())
            reserve(ledger,1)
            ledger.mark_hypothetical_dispatch("fixture-1")
            ledger.settle_synthetic_usage(
                "fixture-1",input_tokens=50,output_tokens=20)
            report=ledger.snapshot()
            self.assertEqual(report["settled_synthetic_micro_usd"],70)
            self.assertEqual(report["outstanding_reserved_micro_usd"],0)
            self.assertEqual(report["remaining_hypothetical_micro_usd"],230)
            self.assertEqual(report["states"],{"SETTLED_OFFLINE":1})
            with self.assertRaisesRegex(DryRunBudgetBlocked,"transition"):
                ledger.settle_synthetic_usage(
                    "fixture-1",input_tokens=50,output_tokens=20)

    def test_uncertain_dispatch_cannot_release_full_reserved_amount(self):
        with TemporaryDirectory() as td:
            ledger=DryRunBudgetLedger(Path(td)/"meter.sqlite3",policy())
            reserve(ledger,1)
            ledger.mark_hypothetical_dispatch("fixture-1")
            ledger.hold_unknown_usage("fixture-1")
            with self.assertRaisesRegex(DryRunBudgetBlocked,"transition"):
                ledger.cancel_proven_unsent("fixture-1")
            with self.assertRaisesRegex(DryRunBudgetBlocked,"transition"):
                ledger.settle_synthetic_usage(
                    "fixture-1",input_tokens=1,output_tokens=1)
            self.assertEqual(ledger.snapshot()["outstanding_reserved_micro_usd"],150)

    def test_pre_dispatch_cancel_releases_budget_but_preserves_retry_history(self):
        with TemporaryDirectory() as td:
            ledger=DryRunBudgetLedger(Path(td)/"meter.sqlite3",policy(tries=1))
            reserve(ledger,1,task="SAME")
            ledger.cancel_proven_unsent("fixture-1")
            self.assertEqual(ledger.snapshot()["committed_hypothetical_micro_usd"],0)
            with self.assertRaisesRegex(DryRunBudgetBlocked,"retry budget"):
                reserve(ledger,2,task="SAME")

    def test_unverified_usage_exceeding_plan_fails_and_keeps_full_reserve(self):
        with TemporaryDirectory() as td:
            ledger=DryRunBudgetLedger(Path(td)/"meter.sqlite3",policy())
            reserve(ledger,1)
            ledger.mark_hypothetical_dispatch("fixture-1")
            for values in ((101,1),(50,51)):
                with self.subTest(values=values):
                    with self.assertRaisesRegex(DryRunBudgetBlocked,"exceeded reserved"):
                        ledger.settle_synthetic_usage(
                            "fixture-1",input_tokens=values[0],
                            output_tokens=values[1])
            self.assertEqual(
                ledger.snapshot()["states"],{"DISPATCH_UNCONFIRMED":1})
            self.assertEqual(
                ledger.snapshot()["outstanding_reserved_micro_usd"],150)

    def test_policy_config_cannot_change_after_ledger_creation(self):
        with TemporaryDirectory() as td:
            db=Path(td)/"meter.sqlite3"
            DryRunBudgetLedger(db,policy())
            for replacement in (
                replace(policy(),maximum_spend_usd="0.000301"),
                replace(policy(),hypothetical_input_usd_per_million="2"),
                replace(policy(),experiment_id="other"),
            ):
                with self.subTest(replacement=replacement):
                    with self.assertRaisesRegex(DryRunBudgetBlocked,"Stale or altered"):
                        DryRunBudgetLedger(db,replacement)
            self.assertEqual(DryRunBudgetLedger(db,policy()).snapshot()[
                "attempt_count"],0)

    def test_no_live_model_or_fake_price_revision_can_enter(self):
        for invalid in (
            replace(policy(),model_id="gpt-6"),
            replace(policy(),price_revision="live-price-snapshot"),
            replace(policy(),hypothetical_output_usd_per_million="NaN"),
            replace(policy(),maximum_spend_usd="-1"),
            replace(policy(),maximum_spend_usd="0.0000001"),
            replace(policy(),maximum_spend_usd=0.01),
            replace(policy(),max_attempts_per_task=True),
            replace(policy(),max_input_tokens_per_attempt=20001),
        ):
            with self.subTest(invalid=invalid):
                with TemporaryDirectory() as td:
                    with self.assertRaises(DryRunBudgetBlocked):
                        DryRunBudgetLedger(Path(td)/"meter.sqlite3",invalid)

    def test_hypothetical_amounts_round_up_never_understate(self):
        with TemporaryDirectory() as td:
            spec=replace(policy(),maximum_spend_usd="0.000004",
                         hypothetical_input_usd_per_million="0.1",
                         hypothetical_output_usd_per_million="0.1")
            ledger=DryRunBudgetLedger(Path(td)/"meter.sqlite3",spec)
            self.assertEqual(reserve(ledger,1,inp=2,out=1)[
                "reserved_micro_usd"],1)
            self.assertEqual(reserve(ledger,2,inp=1,out=1)[
                "reserved_micro_usd"],1)
            self.assertEqual(ledger.snapshot()[
                "committed_hypothetical_micro_usd"],2)

    def test_false_success_or_empty_fields_refused(self):
        with TemporaryDirectory() as td:
            ledger=DryRunBudgetLedger(Path(td)/"meter.sqlite3",policy())
            for name in ("../escape","with spaces",""):
                with self.subTest(name=name):
                    with self.assertRaises(DryRunBudgetBlocked):
                        ledger.reserve(attempt_id=name,task_id="X",arm="direct_xml",
                                       planned_input_tokens=100,
                                       planned_output_tokens=50)
            for bad_input in (True,-1,20001,1.25):
                with self.subTest(value=bad_input):
                    with self.assertRaises(DryRunBudgetBlocked):
                        ledger.reserve(attempt_id="bad",task_id="X",arm="direct_xml",
                                       planned_input_tokens=bad_input,
                                       planned_output_tokens=50)
            self.assertEqual(ledger.snapshot()["attempt_count"],0)

    def test_ledger_symlink_and_missing_parent_denied(self):
        with TemporaryDirectory() as td:
            folder=Path(td)
            with self.assertRaises(DryRunBudgetBlocked):
                DryRunBudgetLedger(folder/"missing"/"meter.sqlite3",policy())
            actual=folder/"real.sqlite3"
            DryRunBudgetLedger(actual,policy())
            alias=folder/"alias.sqlite3"
            try:
                alias.symlink_to(actual)
            except OSError:
                # Windows developer-mode symlink privilege is optional.
                self.assertFalse(alias.exists())
            else:
                with self.assertRaises(DryRunBudgetBlocked):
                    DryRunBudgetLedger(alias,policy())


if __name__=="__main__":
    unittest.main()
