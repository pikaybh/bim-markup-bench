"""Issue #247: pure offline PROPOSED D/I tool/feedback protocol, not a runner.

There is no model SDK, provider, network request, subprocess, IFC mutator,
file writer, hidden target, scoring predicate, or trial-launch method here.
These static, prospective interfaces are *not* deployed v0.66 sessions.

Every arm receives the same source-only, SHA-pinned FULL and MANAGED
declarative XML read envelope. I additionally gets the native source IFC in
its isolated local Python executor; that genuine affordance asymmetry is
explicitly a blocker to a representation-only causal estimand.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Literal

ARMS=("D_FULL","D_MANAGED","I_NATIVE")
REGIMES=("one_shot","feedback")
MAX_CALLS={"one_shot":2,"feedback":25}
MAX_ATTEMPTS={"one_shot":1,"feedback":24}
MAX_READS=1

# Shared model-facing tool names intentionally have no benchmark task names,
# target GlobalIds, action/typed plans, "correct" markers, or grader hints.
def _tool(name, description, arg):
    return {
        "type":"function", "name":name, "description":description,
        "parameters":{
            "type":"object",
            "properties":{arg:{"type":"string"}},
            "required":[arg],
            "additionalProperties":False,
        },
        "strict":True,
    }

READ=_tool(
    "read_source_state",
    "Read the same SHA-bound original IFC-backed source-only FULL and MANAGED "
    "declarative XML states for all three conditions. Both XML documents are "
    "source projections and do not expose private answers, an editor, or "
    "a benchmark score. Exactly one read per trial.",
    "view",
)
D_FULL_WRITE=_tool(
    "submit_full_final_state",
    "Submit a complete replacement of the original source-anchored FULL "
    "declarative XML state, not an XML operation list, command, script or "
    "patch. Trusted runtime infers the edit from the before/after final state "
    "and performs separate IFC validation.",
    "xml_text",
)
D_MANAGED_WRITE=_tool(
    "submit_managed_final_state",
    "Submit the complete source-anchored MANAGED declarative XML final state "
    "including all managed object IDs and original FULL source SHA link, "
    "not an XML command, sparse patch or code.",
    "xml_text",
)
I_NATIVE_WRITE=_tool(
    "execute_ifc_python",
    "Submit general Python/IfcOpenShell source code for execution on a fresh "
    "original native IFC clone inside an isolated, pinned Linux Docker "
    "sandbox. Explicit commit() is mandatory. Stdout/traceback are withheld "
    "from model feedback under this PROPOSED protocol; a common post-native "
    "validator reports the same coarse outcome class as D.",
    "code",
)
WRITE={"D_FULL":D_FULL_WRITE,
       "D_MANAGED":D_MANAGED_WRITE,
       "I_NATIVE":I_NATIVE_WRITE}
TOOLSETS={a:(READ,WRITE[a]) for a in ARMS}

# These are native-engine-stage coarse codes. They CANNOT be used as
# author task correctness, topology target hints or source-related prompts.
FEEDBACK_CLASSES=(
    "admitted_native_scope",
    "invalid_submission",
    "unsupported_source",
    "native_execution_failure",
    "native_scope_rejected",
    "engine_timeout",
)
ADMISSIONS={"admitted_native_scope"}


class ProspectiveProtocolBlocked(ValueError):
    pass


def need(condition, why):
    if not condition:
        raise ProspectiveProtocolBlocked(why)


def canonical_bytes(data):
    return json.dumps(data,ensure_ascii=False,sort_keys=True,
                      separators=(",",":"),allow_nan=False).encode("utf8")


def common_read_envelope(*,original_sha,original_schema,
                         full_xml:bytes,managed_xml:bytes):
    """The *same* response is available to all three arms; no answer data.

    Called only in offline byte-telemetry auditing. It must not be used to
    issue provider calls or to claim the I native IFC affordance disappeared.
    """
    need(isinstance(original_sha,str) and len(original_sha)==64
         and all(c in "0123456789abcdef" for c in original_sha),
         "Exact SHA256 provenance required")
    need(original_schema in ("IFC2X3","IFC4X3"),
         "Unsupported source schema")
    need(isinstance(full_xml,bytes) and isinstance(managed_xml,bytes)
         and full_xml.startswith(b"<?xml") and managed_xml.startswith(b"<?xml")
         and len(full_xml)>100 and len(managed_xml)>100,
         "Only real nonempty source-projected initial XML states allowed")
    full=full_xml.decode("utf8","strict")
    managed=managed_xml.decode("utf8","strict")
    need("PRIVATE_GT" not in full and "PRIVATE_GT" not in managed,
         "Private target answer marker must not be in common read")
    return {
        "status":"source_read_ok",
        "schema":original_schema,
        "source_sha256":original_sha,
        "full_initial_xml":full,
        "managed_initial_xml":managed,
        "author_task_score":None,
    }


def byte_metrics(data:bytes):
    need(isinstance(data,bytes),"Only exact UTF8 bytes can be measured")
    text=data.decode("utf8","strict")
    # These are counts and VERY ROUGH proxies, NEVER tokenizer results.
    return {
        "UTF8_bytes":len(data),
        "unicode_codepoints":len(text),
        "proxy_bytes_div_4_ceiling":(len(data)+3)//4,
        "proxy_codepoints_div_4_ceiling":(len(text)+3)//4,
        "actual_provider_billed_tokens":None,
    }


def model_tool_schema_bytes(arm):
    need(arm in ARMS,"Unknown prospective arm")
    return canonical_bytes(TOOLSETS[arm])


@dataclass
class OfflineBudgetLedger:
    """Pure, deterministic conceptual transcript accounting; never executes.

    One-shot: 1 shared read + 1 submitted candidate, no model-visible
    validation feedback until finalization.
    Feedback: 1 shared read + at most 24 submitted candidate attempts,
    all outputs reduced to fixed coarse engine status classes; NO author
    task score, file path, stdout, raw exception, source or private GT.
    """
    arm: str
    regime: str
    calls: int=0
    reads: int=0
    attempts: int=0
    concluded: bool=False
    stages: list[str]=field(default_factory=list)

    def __post_init__(self):
        need(self.arm in ARMS and self.regime in REGIMES,
             "Only three pinned prospective arms and two budgets")

    def read(self):
        need(not self.concluded and self.reads < MAX_READS
             and self.attempts == 0 and self.calls < MAX_CALLS[self.regime],
             "Read only once before editing, no read-after-feedback")
        self.reads+=1
        self.calls+=1
        self.stages.append("read")
        return {"status":"source_read_ok"}

    def submit(self,outcome):
        need(not self.concluded and self.reads == 1
             and self.calls < MAX_CALLS[self.regime]
             and self.attempts < MAX_ATTEMPTS[self.regime],
             "Submission requires one shared read and remaining attempt budget")
        need(type(outcome) is str and outcome in FEEDBACK_CLASSES,
             "Unknown or answer-bearing evaluation feedback forbidden")
        self.calls+=1
        self.attempts+=1
        self.stages.append("submit")
        if self.regime == "one_shot":
            self.concluded=True
            return {"status":"trial_finalized","feedback_visible_during_generation":False}
        return {
            "status":"native_engine_feedback",
            "coarse_engine_outcome":outcome,
            "attempts_remaining":MAX_ATTEMPTS[self.regime]-self.attempts,
            "author_task_score":None,
        }

    def finalize(self):
        need(self.reads == 1 and self.attempts>=1,
             "Every evaluated trial must read and submit at least once")
        self.concluded=True
        return {
            "arm":self.arm,"regime":self.regime,
            "actual_tool_calls":self.calls,
            "actual_submissions":self.attempts,
            "author_score_or_graded_result_exposed":False,
        }


# This intentionally does not contain any provider-activation function.
# A later owner-approved trial implementation requires an independent gate,
# per-original-source permissions and a separate new protocol version.
