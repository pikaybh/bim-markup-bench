"""Stateless Responses tool-loop for *future-approved* matched BIBIMBAP runs.

No inference occurs unless a caller explicitly supplies a provider and a
durable budget authorization. Offline stubs support deterministic rehearsal.
Same model, decoding, per-call output and up-to-25 tool-call caps both arms.
Never sends original evaluator/GT to model, never silently retries.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

from tools.bibimbap_matched25_tools import ToolSession

MODEL = "gpt-6-luna"
MAX_TOOL_CALLS = 25
MAX_OUTPUT_TOKENS = 12000
INPUT_RATE=Decimal("0.10")
OUTPUT_RATE=Decimal("0.50")
RATE_DENOM=Decimal("1000000")
ISSUE="https://github.com/pikaybh/bim-markup-bench/issues/114"
DEFAULT_SYSTEM=(
    "You are a BIM assistent. Whenever you have questions about values, "
    "infer them or use default values. Always execute the commands and "
    "do not ask for confirmation. You must always load the ifc file first. "
    "For any operation, make sure to use the correct unit scale of the IFC file."
)

class ProviderBudgetError(ValueError): pass
class ProtocolError(ValueError): pass

def sha_bytes(raw:bytes)->str:
    return sha256(raw).hexdigest()

def js(data:object)->str:
    return json.dumps(data,ensure_ascii=False,sort_keys=True,default=repr)

def atomic_write(path:Path,item:dict)->None:
    tmp=path.with_name(path.name+".pending")
    if tmp.exists():
        raise ProviderBudgetError("Unexpected pending ledger; refuse paid run")
    with tmp.open("xb") as f:
        f.write((json.dumps(item,indent=2,ensure_ascii=False,sort_keys=True)+"\n").encode("utf8"))
    tmp.replace(path)

class DurableBudget:
    """Single-process durable per-provider-request reservation and settlement.

    Unknown usage / timeout is conservatively charged as the entire
    reservation, never retried. This is a local upper-bound control, not
    a provider account-level hard billing limit.
    """
    def __init__(self,path:Path,cap_usd:str,*,approval:dict|None=None):
        self.path=path
        cap=Decimal(cap_usd)
        if not cap.is_finite() or cap<=0:
            raise ProviderBudgetError("Approved positive finite cost cap required")
        if path.exists() or path.is_symlink():
            raise ProviderBudgetError("New paid budget ledger must not pre-exist")
        if approval is not None:
            self._check_approval(approval,cap)
        self.cap=cap
        self.data={
            "approved_cap_usd":str(cap),
            "approved_issue":ISSUE,
            "model":MODEL,
            "status":"READY",
            "requests_reserved":0,
            "requests_settled":0,
            "token_usage_estimated_usd":"0",
            "pessimistically_reserved_and_unsettled_usd":"0",
            "request_ledger":[],
            "provider_invoice_reconciled":False,
        }
        atomic_write(path,self.data)

    @staticmethod
    def _check_approval(a:dict,cap:Decimal):
        required={"approved","issue","model","cap_usd","max_tool_calls",
                  "max_output_tokens","approved_at_utc","pricing_checked_utc",
                  "input_per_million_usd","output_per_million_usd","pricing_url"}
        if type(a) is not dict or set(a)!=required:
            raise ProviderBudgetError("Explicit full owner approval schema required")
        try:
            parsed_cap=Decimal(a["cap_usd"]) if type(a["cap_usd"]) is str else None
            inp=Decimal(a["input_per_million_usd"]) if type(a["input_per_million_usd"]) is str else None
            out=Decimal(a["output_per_million_usd"]) if type(a["output_per_million_usd"]) is str else None
            checked=datetime.strptime(a["pricing_checked_utc"],"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            approved=datetime.strptime(a["approved_at_utc"],"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except (ValueError,TypeError,KeyError) as exc:
            raise ProviderBudgetError("Malformed approval prices or timestamps") from exc
        if (a["approved"] is not True or a["issue"]!=ISSUE or a["model"]!=MODEL
            or a["max_tool_calls"]!=MAX_TOOL_CALLS or
            a["max_output_tokens"]!=MAX_OUTPUT_TOKENS or
            a["pricing_url"]!="https://developers.openai.com/api/docs/pricing"
            or inp!=INPUT_RATE or out!=OUTPUT_RATE or parsed_cap!=cap
            or not cap.is_finite() or
            checked>datetime.now(timezone.utc)+timedelta(hours=1)
            or checked<datetime.now(timezone.utc)-timedelta(days=7)
            or approved<checked or approved>datetime.now(timezone.utc)+timedelta(hours=1)):
            raise ProviderBudgetError("Approved model, cap, tariff or recent price verification invalid")

    def _reserved_total(self)->Decimal:
        return Decimal(self.data["pessimistically_reserved_and_unsettled_usd"])

    def _spent(self)->Decimal:
        return Decimal(self.data["token_usage_estimated_usd"])

    def reserve(self, *, input_payload:object, tools:list[dict],max_output:int)->int:
        if max_output!=MAX_OUTPUT_TOKENS or not tools or self.data["status"]=="BUDGET_EXHAUSTED":
            raise ProviderBudgetError("Unsupported provider request settings")
        # Bound every potential input token conservatively by UTF-8 bytes of
        # model-visible messages PLUS tool schema + 4096 API framing margin.
        bytes_upper=len(js(input_payload).encode("utf8"))+len(js(tools).encode("utf8"))+4096
        if bytes_upper>900000:
            raise ProviderBudgetError("Context is too large to bound")
        reserved=(Decimal(bytes_upper)*INPUT_RATE + Decimal(MAX_OUTPUT_TOKENS)*OUTPUT_RATE)/RATE_DENOM
        if self._spent()+self._reserved_total()+reserved>=self.cap:
            self.data["status"]="BUDGET_EXHAUSTED"
            atomic_write(self.path,self.data)
            raise ProviderBudgetError("Budget ceiling reached before next provider request")
        idx=len(self.data["request_ledger"])
        self.data["request_ledger"].append({
            "index":idx,"reserved_usd":str(reserved),
            "payload_sha256":sha_bytes(js(input_payload).encode("utf8")),
            "tools_sha256":sha_bytes(js(tools).encode("utf8")),
            "status":"ISSUED_USAGE_UNCONFIRMED",
            "max_output_tokens":max_output,
        })
        self.data["requests_reserved"]+=1
        self.data["pessimistically_reserved_and_unsettled_usd"]=str(self._reserved_total()+reserved)
        atomic_write(self.path,self.data)
        return idx

    def settle(self,idx:int, usage:object|None, *, confirmed_model:str|None):
        item=self.data["request_ledger"][idx]
        if item["status"]!="ISSUED_USAGE_UNCONFIRMED":
            raise ProviderBudgetError("Duplicate provider settlement not allowed")
        reserved=Decimal(item["reserved_usd"])
        if (usage is not None and confirmed_model==MODEL and
            isinstance(getattr(usage,"input_tokens",None),int) and
            isinstance(getattr(usage,"output_tokens",None),int) and
            0<=usage.input_tokens and 0<=usage.output_tokens<=MAX_OUTPUT_TOKENS):
            estimate=(Decimal(usage.input_tokens)*INPUT_RATE+
                      Decimal(usage.output_tokens)*OUTPUT_RATE)/RATE_DENOM
            if estimate>reserved:
                raise ProviderBudgetError("Reported usage exceeds reserved bound")
            item["status"]="SETTLED_REPORTED_USAGE"
            item["reported_input_tokens"]=usage.input_tokens
            item["reported_output_tokens"]=usage.output_tokens
        else:
            estimate=reserved
            item["status"]="SETTLED_CONSERVATIVE_UNKNOWN_USAGE"
        item["cost_estimated_usd"]=str(estimate)
        self.data["token_usage_estimated_usd"]=str(self._spent()+estimate)
        self.data["pessimistically_reserved_and_unsettled_usd"]=str(self._reserved_total()-reserved)
        self.data["requests_settled"]+=1
        atomic_write(self.path,self.data)

@dataclass(frozen=True)
class PairProtocol:
    model:str=MODEL
    max_tool_calls:int=MAX_TOOL_CALLS
    max_output_tokens:int=MAX_OUTPUT_TOKENS
    reasoning_effort:str="medium"
    store:bool=False
    service_tier:str="default"
    automatic_retries:int=0
    samples_per_task:int=1

    def __post_init__(self):
        if (self.model!=MODEL or self.max_tool_calls!=25
            or self.max_output_tokens!=12000 or self.reasoning_effort!="medium"
            or self.store is not False or self.service_tier!="default"
            or self.automatic_retries!=0 or self.samples_per_task!=1):
            raise ProtocolError("Prospective paired protocol is frozen; no asymmetric config")

@dataclass
class FakeUsage:
    input_tokens:int=100
    output_tokens:int=100

class _FunctionCall:
    def __init__(self,name:str,arguments:str,call_id:str):
        self.type="function_call";self.name=name;self.arguments=arguments;self.call_id=call_id
    def model_dump(self,*,exclude_none:bool=True):
        return {"type":"function_call","name":self.name,"arguments":self.arguments,"call_id":self.call_id}

class OfflineFakeResponse:
    def __init__(self,model:str,turn:int,tools:list[_FunctionCall],answer:str=""):
        self.status="completed"
        self.model=model
        self.id=f"OFFLINE_FAKE_RESPONSE_{turn}"
        self.output=tools if tools else []
        self.output_text=answer
        self.usage=FakeUsage()
    def model_dump(self,*,exclude_none:bool=True):
        return {"id":self.id,"status":self.status,"model":self.model,
                "output":[t.model_dump() for t in self.output]}

class OfflineFakeClient:
    """Deterministic dryrun; never loads an API key or uses a network client."""
    class Responses:
        def __init__(self,steps:list[list[_FunctionCall]]):
            self.steps=steps;self.calls=0
        def create(self,**kwargs):
            if self.calls>=len(self.steps):
                raise AssertionError("Offline test consumed all scripted calls")
            calls=self.steps[self.calls];self.calls+=1
            return OfflineFakeResponse(kwargs["model"],self.calls,calls)
    def __init__(self,steps:list[list[_FunctionCall]]):
        self.responses=self.Responses(steps)

def _serialized_output(item:object)->dict:
    if hasattr(item,"model_dump"):
        return item.model_dump(exclude_none=True)
    if isinstance(item,dict):
        return dict(item)
    raise ProtocolError("Unexpected Responses output item type")

def _function_calls(answer:object)->list:
    return [x for x in answer.output if
            (getattr(x,"type",None) if not isinstance(x,dict) else x.get("type"))=="function_call"]

def _field(item,name):
    return item.get(name) if isinstance(item,dict) else getattr(item,name,None)

def arm_messages(arm:str,question:str)->tuple[str,str]:
    if arm not in ("XML","PYTHON"):
        raise ProtocolError("Unknown matched arm")
    if not isinstance(question,str) or not 0<len(question.encode("utf8"))<=12000:
        raise ProtocolError("Missing/unbounded public question")
    if arm=="XML":
        system=DEFAULT_SYSTEM + (
            "\nFor this condition edit declarative source text ONLY. You may call "
            "read_building_xml to inspect the available complete XML state and "
            "submit_building_xml to submit a complete updated XML document. "
            "The trusted external compiler returns syntax/IFC feedback. "
            "You can re-inspect, correct the document and resubmit within the same tool-call budget. "
            "Do NOT write or invoke Python, IfcOpenShell, executable operations or external BIM APIs. "
            "Finish with a normal final message; the latest successful compiled IFC is the only scoreable artifact."
        )
        user=question+"\n\nUse the available XML source-file tools to inspect and edit the current building."
    else:
        system=DEFAULT_SYSTEM
        user=question+(
            "\n\nUse the tool execute_ifc_code to run ifcopenshell code. "
            "The current IFC file is preloaded as ifc. "
            "Rules:\n- Avoid numpy.\n- Avoid ifcopenshell.geom/create_shape unless necessary."
            "\n- The tool loads ifc.\n- Set result to return data."
            "\n- Call commit() to save modifications back to the same path."
        )
    return system,user

def run_agent(client:object,session:ToolSession,*,arm:str,public_question:str,
              protocol:PairProtocol,budget:DurableBudget|None,
              record_file:Path|None=None) -> dict:
    """One BIBIMBAP task/arm; tool calls are never automatically repeated."""
    instructions,user=arm_messages(arm,public_question)
    messages=[{"role":"user","content":user}]
    raw_events=[]
    tool_count=0
    model_calls=0
    in_total=out_total=0
    output_hashes=[]
    done="INCOMPLETE"
    if record_file is not None and (record_file.exists() or record_file.is_symlink()):
        raise ProtocolError("Run evidence must be unique")
    while True:
        if tool_count>=protocol.max_tool_calls:
            done="MAX_25_TOOL_CALLS_REACHED"
            break
        if model_calls>protocol.max_tool_calls:
            done="MAX_PROVIDER_RESPONSES_REACHED"
            break
        # In mock mode no paid budget is required, but the only client passed
        # must be an explicit offline fake, preventing accidental billing.
        if budget is None and not isinstance(client,OfflineFakeClient):
            raise ProviderBudgetError("Paid provider client requires owner-approved durable budget")
        reservation=None
        if budget is not None:
            reservation=budget.reserve(input_payload={"instructions":instructions,"input":messages},
                                       tools=session.tools,max_output=protocol.max_output_tokens)
        try:
            answer=client.responses.create(
                model=protocol.model,instructions=instructions,
                input=messages,tools=session.tools,
                max_output_tokens=protocol.max_output_tokens,
                reasoning={"effort":protocol.reasoning_effort},
                service_tier=protocol.service_tier,store=False,
                include=["reasoning.encrypted_content"],
            )
        except Exception as exc:
            if budget is not None:
                budget.settle(reservation,None,confirmed_model=None)
            done="PROVIDER_ERROR_NO_RETRY"
            raw_events.append({"provider_error_type":type(exc).__name__})
            break
        if budget is not None:
            budget.settle(reservation,getattr(answer,"usage",None),
                          confirmed_model=getattr(answer,"model",None))
        model_calls+=1
        usage=getattr(answer,"usage",None)
        if usage is not None:
            in_total+=int(usage.input_tokens)
            out_total+=int(usage.output_tokens)
        answer_dump=answer.model_dump(exclude_none=True)
        # Full transcript is local, ignored by Git, with raw provider text
        # and tool arguments. No original author grader/ground truth here.
        raw_events.append({"provider_response":answer_dump})
        output_hashes.append(sha_bytes(js(answer_dump).encode("utf8")))
        if getattr(answer,"model",None)!=protocol.model:
            done="PROVIDER_RETURNED_WRONG_MODEL"
            break
        if getattr(answer,"status",None)!="completed":
            done="PROVIDER_RESPONSE_INCOMPLETE"
            break
        messages.extend(_serialized_output(x) for x in answer.output)
        calls=_function_calls(answer)
        if not calls:
            done="MODEL_FINAL_MESSAGE"
            break
        for call in calls:
            if tool_count>=protocol.max_tool_calls:
                done="MAX_25_TOOL_CALLS_REACHED"
                break
            tool_count+=1
            args=_field(call,"arguments")
            name=_field(call,"name")
            call_id=_field(call,"call_id")
            try:
                obj=json.loads(args)
                if not isinstance(obj,dict):
                    raise ValueError("Tool arguments must be a JSON object")
                feedback=session.call(name,obj)
            except Exception as exc:
                feedback={"status":"error","error_type":type(exc).__name__,
                          "error":"Malformed tool arguments or trusted runtime error"}
            messages.append({"type":"function_call_output","call_id":call_id,
                             "output":json.dumps(feedback,ensure_ascii=False,default=repr)})
            raw_events.append({"tool_name":name,"call_id_hash":sha_bytes(str(call_id).encode()),
                               "tool_arguments_sha256":sha_bytes(str(args).encode()),
                               "tool_feedback":feedback})
        if done=="MAX_25_TOOL_CALLS_REACHED":
            break
    if record_file is not None:
        with record_file.open("xb") as f:
            f.write((json.dumps(raw_events,ensure_ascii=False,indent=2,default=repr)+"\n").encode("utf8"))
    return {
        "status":done,"arm":arm,"model":protocol.model,"tool_calls":tool_count,
        "model_requests":model_calls,"input_tokens":in_total,"output_tokens":out_total,
        "response_hashes":output_hashes,
        "native_output_available":session.output_ifc is not None,
        "native_output_path_local_only":str(session.output_ifc) if session.output_ifc else None,
        "raw_transcript_sha256":sha_bytes(record_file.read_bytes()) if record_file else None,
    }
