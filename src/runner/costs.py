"""Provider-cost provenance, Decimal accounting and hard no-paid test runtime."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

class TrialBudgetError(ValueError):
    pass


def _decimal(value:Any,name:str)->Decimal:
    try:
        d=Decimal(str(value))
    except (InvalidOperation,TypeError,ValueError) as exc:
        raise TrialBudgetError(name+" invalid decimal") from exc
    if not d.is_finite() or d<0:
        raise TrialBudgetError(name+" must be a finite nonnegative Decimal")
    return d

@dataclass(frozen=True)
class CostRecord:
    provider:str
    model_id:str
    currency:str
    price_revision:str
    estimated_input_tokens:int
    estimated_output_tokens:int
    reported_input_tokens:int|None
    reported_output_tokens:int|None
    estimated_usd:str
    actual_provider_charge_usd:str|None
    paid_model_called:bool

    def as_dict(self)->dict:
        return {
            "provider":self.provider,"model_id":self.model_id,
            "currency":self.currency,"price_revision":self.price_revision,
            "estimated_input_tokens":self.estimated_input_tokens,
            "estimated_output_tokens":self.estimated_output_tokens,
            "reported_input_tokens":self.reported_input_tokens,
            "reported_output_tokens":self.reported_output_tokens,
            "estimated_usd":self.estimated_usd,
            "actual_provider_charge_usd":self.actual_provider_charge_usd,
            "paid_model_called":self.paid_model_called,
        }


def make_offline_cost_record(model_id:str,input_tokens:int,output_tokens:int)->CostRecord:
    if model_id!="offline/mock-v0":
        raise TrialBudgetError("Paid model/provider is forbidden in offline run scheduler")
    if (type(input_tokens) is not int or type(output_tokens) is not int
        or input_tokens<0 or output_tokens<0):
        raise TrialBudgetError("Mock token estimates must be integers")
    return CostRecord(
        provider="offline",model_id=model_id,currency="USD",
        price_revision="OFFLINE_ZERO_CHARGE_MOCK_NO_PROVIDER",
        estimated_input_tokens=input_tokens,
        estimated_output_tokens=output_tokens,
        reported_input_tokens=None,reported_output_tokens=None,
        estimated_usd="0.00",actual_provider_charge_usd=None,
        paid_model_called=False,
    )


def enforce_offline_budget(*,maximum_total_spend_usd:Any,
                           max_attempts:int,max_wall_seconds:int,
                           max_input_tokens:int,max_output_tokens:int,
                           model_id:str)->None:
    if model_id!="offline/mock-v0":
        raise TrialBudgetError("Only offline mock model accepted before G2 release gates")
    cap=_decimal(maximum_total_spend_usd,"maximum_total_spend_usd")
    if cap!=Decimal("0"):
        raise TrialBudgetError("Mock experiments must use a zero-dollar spend ceiling")
    for value,name,limit in (
        (max_attempts,"max_attempts",5),
        (max_wall_seconds,"max_wall_seconds",180),
        (max_input_tokens,"max_input_tokens",20000),
        (max_output_tokens,"max_output_tokens",6000),
    ):
        if type(value) is not int or not 1<=value<=limit:
            raise TrialBudgetError(name+" outside frozen offline experiment policy")
