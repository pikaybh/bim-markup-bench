"""SQLite-backed OFFLINE DRY-RUN budget reservations for paired BIM trials.

This module has NO provider adapter and CANNOT authorize actual API calls.
It stores *hypothetical* token envelopes, not model-token measurements or
provider charges. It demonstrates atomic reservations/reconciliation across
processes before any real model/tokenizer/pricing/billing integration.

No model text, secrets, source IFC, GT, or provider responses are stored.
"""
from __future__ import annotations

from contextlib import contextmanager, closing
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR
import json
from pathlib import Path
import re
import sqlite3

from src.runner.manifest import ARMS, TASK_ID_RE


class DryRunBudgetBlocked(ValueError):
    """Budget overflow, stale policy, unproven usage or illegal state transition."""


MAX_MICRO_USD=2**62
ATTEMPT_ID=re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,110}$")
ALLOWED_STATES=("RESERVED_UNSENT","DISPATCH_UNCONFIRMED",
                "UNKNOWN_USAGE","SETTLED_OFFLINE","CANCELED_UNSENT")


def _decimal(value, field:str, *,allow_zero:bool=False)->Decimal:
    if isinstance(value,(bool,float)):
        raise DryRunBudgetBlocked(field+" must be an exact decimal string")
    try:
        result=Decimal(str(value))
    except (InvalidOperation,ValueError,TypeError) as exc:
        raise DryRunBudgetBlocked(field+" has invalid decimal representation") from exc
    if not result.is_finite() or result<0 or (result==0 and not allow_zero):
        raise DryRunBudgetBlocked(field+" must be finite and positive")
    return result


def _positive_int(value, field:str, minimum:int=1, maximum:int=20000)->int:
    if type(value) is not int or not minimum<=value<=maximum:
        raise DryRunBudgetBlocked(field+" exceeds bounded offline policy")
    return value


@dataclass(frozen=True)
class DryRunPolicy:
    experiment_id:str
    maximum_spend_usd:str
    hypothetical_input_usd_per_million:str
    hypothetical_output_usd_per_million:str
    max_input_tokens_per_attempt:int
    max_output_tokens_per_attempt:int
    max_attempts_per_task:int
    max_concurrent_attempts:int
    model_id:str="offline/mock-v0"
    price_revision:str="OFFLINE_SYNTHETIC_QUOTE_NO_PROVIDER"

    def validate(self)->tuple[int,Decimal,Decimal]:
        if (self.model_id!="offline/mock-v0" or
                self.price_revision!="OFFLINE_SYNTHETIC_QUOTE_NO_PROVIDER"):
            raise DryRunBudgetBlocked("Only explicitly synthetic zero-API fixture allowed")
        if not ATTEMPT_ID.fullmatch(self.experiment_id):
            raise DryRunBudgetBlocked("Experiment ID invalid")
        inp=_decimal(self.hypothetical_input_usd_per_million,"input_rate")
        out=_decimal(self.hypothetical_output_usd_per_million,"output_rate")
        cap=_decimal(self.maximum_spend_usd,"cap")
        cap_micro=int((cap*Decimal(1_000_000)).to_integral_value(
            rounding=ROUND_FLOOR))
        if not 1<=cap_micro<=MAX_MICRO_USD:
            raise DryRunBudgetBlocked("Cap cannot fit positive micro-USD ledger")
        _positive_int(self.max_input_tokens_per_attempt,"input_tokens",maximum=20000)
        _positive_int(self.max_output_tokens_per_attempt,"output_tokens",maximum=6000)
        _positive_int(self.max_attempts_per_task,"attempts",maximum=5)
        _positive_int(self.max_concurrent_attempts,"concurrency",maximum=32)
        if inp*20000+out*6000>MAX_MICRO_USD:
            raise DryRunBudgetBlocked("Hypothetical quote magnitude unsafe")
        return cap_micro,inp,out


class DryRunBudgetLedger:
    """Durable SQLite transactional *simulation*, no real financial authority."""

    def __init__(self,path:Path,policy:DryRunPolicy):
        self.path=Path(path)
        self.policy=policy
        self.cap_micro,self.in_rate,self.out_rate=policy.validate()
        if (self.path.is_symlink() or self.path.is_dir()
                or not self.path.parent.is_dir()
                or self.path.parent.is_symlink()
                or self.path.suffix!=".sqlite3"):
            raise DryRunBudgetBlocked("Unsafe or absent local ledger directory/file")
        self._policy_json=json.dumps(asdict(policy),sort_keys=True,
                                     ensure_ascii=True,separators=(",",":"))
        with closing(self._connect()) as con:
            con.execute("""CREATE TABLE IF NOT EXISTS ledger_policy(
                           id INTEGER PRIMARY KEY CHECK(id=1),
                           config_json TEXT NOT NULL)""")
            con.execute("""CREATE TABLE IF NOT EXISTS attempts(
                           attempt_id TEXT PRIMARY KEY,
                           task_id TEXT NOT NULL,
                           arm TEXT NOT NULL,
                           planned_input INTEGER NOT NULL,
                           planned_output INTEGER NOT NULL,
                           reserve_micro INTEGER NOT NULL,
                           charge_micro INTEGER NOT NULL DEFAULT 0,
                           status TEXT NOT NULL CHECK(status IN
                             ('RESERVED_UNSENT','DISPATCH_UNCONFIRMED',
                              'UNKNOWN_USAGE','SETTLED_OFFLINE',
                              'CANCELED_UNSENT')),
                           observed_input INTEGER,
                           observed_output INTEGER,
                           usage_origin TEXT)""")
            con.execute("BEGIN IMMEDIATE")
            try:
                existing=con.execute(
                    "SELECT config_json FROM ledger_policy WHERE id=1"
                ).fetchone()
                if existing is None:
                    con.execute("INSERT INTO ledger_policy(id,config_json) VALUES(1,?)",
                                (self._policy_json,))
                elif existing[0]!=self._policy_json:
                    raise DryRunBudgetBlocked(
                        "Stale or altered budget/model/price policy on reopen")
                con.commit()
            except BaseException:
                con.rollback()
                raise

    def _connect(self):
        if self.path.is_symlink():
            raise DryRunBudgetBlocked("Ledger DB path became symlink")
        con=sqlite3.connect(str(self.path),timeout=20,isolation_level=None)
        con.execute("PRAGMA busy_timeout=20000")
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=FULL")
        return con

    @contextmanager
    def _transaction(self):
        with closing(self._connect()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                config=con.execute(
                    "SELECT config_json FROM ledger_policy WHERE id=1"
                ).fetchone()
                if config is None or config[0]!=self._policy_json:
                    raise DryRunBudgetBlocked("Ledger policy corrupted or missing")
                yield con
                con.commit()
            except BaseException:
                con.rollback()
                raise

    def _cost_micro(self,input_tokens:int,output_tokens:int)->int:
        _positive_int(input_tokens,"input_tokens",minimum=0,
                      maximum=self.policy.max_input_tokens_per_attempt)
        _positive_int(output_tokens,"output_tokens",minimum=0,
                      maximum=self.policy.max_output_tokens_per_attempt)
        if input_tokens==0 and output_tokens==0:
            raise DryRunBudgetBlocked("Empty synthetic usage envelope")
        return int((self.in_rate*input_tokens+self.out_rate*output_tokens)
                   .to_integral_value(rounding=ROUND_CEILING))

    @staticmethod
    def _totals(con)->tuple[int,int,int,int]:
        rows=con.execute(
            "SELECT status,reserve_micro,charge_micro FROM attempts").fetchall()
        outstanding=sum(r for state,r,_ in rows
                        if state in ("RESERVED_UNSENT",
                                     "DISPATCH_UNCONFIRMED","UNKNOWN_USAGE"))
        settled=sum(c for state,_,c in rows if state=="SETTLED_OFFLINE")
        active=sum(state=="DISPATCH_UNCONFIRMED" for state,_,_ in rows)
        return outstanding,settled,active,len(rows)

    def reserve(self,*,attempt_id:str,task_id:str,arm:str,
                planned_input_tokens:int,planned_output_tokens:int)->dict:
        if (not ATTEMPT_ID.fullmatch(attempt_id)
                or not TASK_ID_RE.fullmatch(task_id) or arm not in ARMS):
            raise DryRunBudgetBlocked("Attempt/task/arm identifier invalid")
        reserve_micro=self._cost_micro(planned_input_tokens,planned_output_tokens)
        if reserve_micro<=0:
            raise DryRunBudgetBlocked("Synthetic budget reservation rounds to zero")
        with self._transaction() as con:
            if con.execute(
                "SELECT 1 FROM attempts WHERE attempt_id=?",(attempt_id,)
            ).fetchone() is not None:
                raise DryRunBudgetBlocked("Duplicate immutable attempt reservation")
            count=con.execute(
                "SELECT COUNT(*) FROM attempts WHERE task_id=? AND arm=?",
                (task_id,arm)).fetchone()[0]
            if count>=self.policy.max_attempts_per_task:
                raise DryRunBudgetBlocked("Per-task/arm retry budget exhausted")
            outstanding,settled,active,_=self._totals(con)
            if active>=self.policy.max_concurrent_attempts:
                raise DryRunBudgetBlocked("Already at maximum inflight attempts")
            if outstanding+settled+reserve_micro>self.cap_micro:
                raise DryRunBudgetBlocked("Budget cap exceeded by new reservation")
            con.execute(
                """INSERT INTO attempts
                (attempt_id,task_id,arm,planned_input,planned_output,
                 reserve_micro,status) VALUES(?,?,?,?,?,?,?)""",
                (attempt_id,task_id,arm,planned_input_tokens,
                 planned_output_tokens,reserve_micro,"RESERVED_UNSENT"))
        return {"attempt_id":attempt_id,"status":"RESERVED_UNSENT",
                "reserved_micro_usd":reserve_micro,
                "provider_tokens_verified":False,"actual_provider_charge":None}

    def _change_state(self,attempt_id:str,required:str,next_state:str,
                      *,input_tokens:int|None=None,
                      output_tokens:int|None=None)->dict:
        if not ATTEMPT_ID.fullmatch(attempt_id):
            raise DryRunBudgetBlocked("Invalid attempt ID")
        with self._transaction() as con:
            row=con.execute(
                """SELECT status,planned_input,planned_output,reserve_micro
                   FROM attempts WHERE attempt_id=?""",
                (attempt_id,)).fetchone()
            if row is None or row[0]!=required:
                raise DryRunBudgetBlocked("Illegal or duplicate budget state transition")
            if next_state=="DISPATCH_UNCONFIRMED":
                _,_,active,_=self._totals(con)
                if active>=self.policy.max_concurrent_attempts:
                    raise DryRunBudgetBlocked("Cannot dispatch beyond concurrent cap")
            if next_state=="SETTLED_OFFLINE":
                if input_tokens is None or output_tokens is None:
                    raise DryRunBudgetBlocked("Synthetic usage values absent")
                charge=self._cost_micro(input_tokens,output_tokens)
                if (input_tokens>row[1] or output_tokens>row[2]
                        or charge>row[3]):
                    raise DryRunBudgetBlocked(
                        "Synthetic actual usage exceeded reserved envelope; hold full reserve")
                con.execute("""UPDATE attempts SET status=?,charge_micro=?,
                               observed_input=?,observed_output=?,usage_origin=?
                               WHERE attempt_id=?""",
                            (next_state,charge,input_tokens,output_tokens,
                             "OFFLINE_SYNTHETIC_FIXTURE_NOT_PROVIDER",attempt_id))
            else:
                con.execute("UPDATE attempts SET status=? WHERE attempt_id=?",
                            (next_state,attempt_id))
        return {"attempt_id":attempt_id,"status":next_state,
                "provider_execution_authorized":False,
                "actual_provider_charge":None}

    def mark_hypothetical_dispatch(self,attempt_id:str)->dict:
        """Simulation only; this method never connects to a provider."""
        return self._change_state(attempt_id,"RESERVED_UNSENT",
                                  "DISPATCH_UNCONFIRMED")

    def settle_synthetic_usage(self,attempt_id:str,*,input_tokens:int,
                               output_tokens:int)->dict:
        """Test fixture usage only; NEVER label as verified API billing."""
        return self._change_state(attempt_id,"DISPATCH_UNCONFIRMED",
                                  "SETTLED_OFFLINE",
                                  input_tokens=input_tokens,
                                  output_tokens=output_tokens)

    def hold_unknown_usage(self,attempt_id:str)->dict:
        """Uncertain dispatch permanently retains full reserved capacity."""
        return self._change_state(attempt_id,"DISPATCH_UNCONFIRMED",
                                  "UNKNOWN_USAGE")

    def cancel_proven_unsent(self,attempt_id:str)->dict:
        """May cancel only a reservation that was never dispatched."""
        return self._change_state(attempt_id,"RESERVED_UNSENT",
                                  "CANCELED_UNSENT")

    def snapshot(self)->dict:
        with self._transaction() as con:
            outstanding,settled,active,attempt_count=self._totals(con)
            states=dict(con.execute(
                "SELECT status,COUNT(*) FROM attempts GROUP BY status").fetchall())
        committed=outstanding+settled
        if committed>self.cap_micro:
            raise DryRunBudgetBlocked("Corrupted ledger exceeds budget cap")
        return {
            "status":"OFFLINE_SIMULATED_LEDGER_NO_LIVE_PROVIDER",
            "model_id":self.policy.model_id,
            "price_revision":self.policy.price_revision,
            "cap_micro_usd":self.cap_micro,
            "committed_hypothetical_micro_usd":committed,
            "outstanding_reserved_micro_usd":outstanding,
            "settled_synthetic_micro_usd":settled,
            "remaining_hypothetical_micro_usd":self.cap_micro-committed,
            "attempt_count":attempt_count,
            "hypothetical_inflight_count":active,
            "states":states,
            "actual_provider_tokens":None,
            "actual_provider_charges":None,
            "real_provider_calls":0,
            "paid_run_authorized":False,
            "official_tasks_scored":0,
        }
