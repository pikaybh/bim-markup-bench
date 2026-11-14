"""v0.20 OFFLINE ONLY: one-shot terminal model-submission state-machine audit.

This is a pure Python host-simulation with no model transport, no container,
no generated-code execution and no scorer/provider import. It shows the
required one-way host/model boundary, but is NOT a network/API security
boundary, host integration, or production sandbox admission.

The trusted host receives private candidate bytes through its own object.
The hypothetical model's ONLY observable outcome after submission is a
fixed, terminal receipt independent of source text, status, exceptions,
model budget, score, stdout or native IFC. No further model tool calls.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json


MAX_ONE_SHOT_SOURCE_BYTES = 64 * 1024
PUBLIC_TERMINAL_RECEIPT = (
    '{"execution_feedback_available":false,'
    '"status":"SEALED_ONE_SHOT_SUBMISSION_RECORDED",'
    '"tool_continuation_allowed":false}'
)


class TerminalSubmissionBlocked(ValueError):
    pass


@dataclass(frozen=True)
class HostPrivateSealedRecord:
    """Trusted host only; never marshal into an agent/model tool response."""
    developer_or_model_candidate_sha256: str
    input_code_size_bytes: int
    staged_original_source_id_sha256: str
    trusted_host_outcome: str | None


class OfflineTerminalOneShotBroker:
    """Offline test double. Deliberately exposes NO method to run code."""

    def __init__(self, *, public_source_packet_sha256: str):
        if (not isinstance(public_source_packet_sha256, str)
            or len(public_source_packet_sha256) != 64
            or any(c not in "0123456789abcdef" for c in public_source_packet_sha256)):
            raise TerminalSubmissionBlocked("Require pinned public source packet SHA256")
        self._source_packet_sha256 = public_source_packet_sha256
        self._submitted: HostPrivateSealedRecord | None = None
        self._host_finished = False

    @property
    def terminal(self) -> bool:
        return self._submitted is not None

    @property
    def attempted_executions(self) -> int:
        """Always zero: this offline broker has no executor."""
        return 0

    def submit_once(self, code: bytes) -> str:
        """The hypothetical model's sole terminal action and ONLY response."""
        if self._submitted is not None:
            raise TerminalSubmissionBlocked("Terminal: no second submission or retry")
        if (not isinstance(code, bytes)
            or not 0 < len(code) <= MAX_ONE_SHOT_SOURCE_BYTES
            or b"\x00" in code):
            raise TerminalSubmissionBlocked("Invalid bounded one-shot UTF-8 input")
        try:
            code.decode("utf8", errors="strict")
        except UnicodeDecodeError as exc:
            raise TerminalSubmissionBlocked("Invalid bounded one-shot UTF-8 input") from exc
        self._submitted = HostPrivateSealedRecord(
            developer_or_model_candidate_sha256=sha256(code).hexdigest(),
            input_code_size_bytes=len(code),
            staged_original_source_id_sha256=self._source_packet_sha256,
            trusted_host_outcome=None,
        )
        return PUBLIC_TERMINAL_RECEIPT

    def host_only_record_outcome(self, result: str, *, origin: str) -> HostPrivateSealedRecord:
        """Private offline HOST diagnostic; not a model-facing tool endpoint."""
        if self._submitted is None or self._host_finished:
            raise TerminalSubmissionBlocked("No pending host-only seal or already finalized")
        if origin != "trusted_offline_host":
            raise TerminalSubmissionBlocked("Only trusted offline host may finalize")
        if not isinstance(result, str) or not 0 < len(result) <= 4096:
            raise TerminalSubmissionBlocked("Invalid host-only outcome")
        prior = self._submitted
        private = HostPrivateSealedRecord(
            developer_or_model_candidate_sha256=prior.developer_or_model_candidate_sha256,
            input_code_size_bytes=prior.input_code_size_bytes,
            staged_original_source_id_sha256=prior.staged_original_source_id_sha256,
            trusted_host_outcome=result,
        )
        self._submitted = private
        self._host_finished = True
        return private

    def ask_model_for_continuation(self) -> None:
        """Always blocked: no model-side retries or iterative observations."""
        raise TerminalSubmissionBlocked("No continuation; terminal one-shot only")

    def model_request_result(self) -> None:
        """Always blocked, even before HOST finishes; no scorer/status leaks."""
        raise TerminalSubmissionBlocked("Result query and tool observations blocked")


def offline_terminal_noninterference_audit() -> dict:
    """Exercise two model payloads and independent private host outcomes."""
    pinned = "f" * 64
    baseline = OfflineTerminalOneShotBroker(public_source_packet_sha256=pinned)
    malicious = OfflineTerminalOneShotBroker(public_source_packet_sha256=pinned)
    result_a = baseline.submit_once(b"print('FIXTURE_A')\n")
    result_b = malicious.submit_once(
        b"print('FAKE_HIDDEN_GRADE_AND_IFC_CANARY')\n")
    if (result_a != PUBLIC_TERMINAL_RECEIPT
        or result_b != PUBLIC_TERMINAL_RECEIPT
        or result_a != result_b):
        raise TerminalSubmissionBlocked("Model receipts vary with candidate content")
    public_receipt = json.loads(result_a)
    if public_receipt != {
        "execution_feedback_available": False,
        "status": "SEALED_ONE_SHOT_SUBMISSION_RECORDED",
        "tool_continuation_allowed": False,
    }:
        raise TerminalSubmissionBlocked("One-shot model receipt changed")
    private_a = baseline.host_only_record_outcome("HOST_PRIVATE_ORIGINAL_AUTHOR_SCORE_1.0",
                                                  origin="trusted_offline_host")
    private_b = malicious.host_only_record_outcome(
        "HOST_PRIVATE_IFC_PARSE_ERROR_WITH_FAKE_SENSITIVE_CONTENT",
        origin="trusted_offline_host")
    if (private_a.trusted_host_outcome == private_b.trusted_host_outcome
        or private_a.developer_or_model_candidate_sha256 ==
           private_b.developer_or_model_candidate_sha256
        or private_a.trusted_host_outcome in result_a
        or private_b.trusted_host_outcome in result_b):
        raise TerminalSubmissionBlocked("Host-only diagnostics leaked to model receipt")
    for session in (baseline, malicious):
        for action in (
            lambda: session.submit_once(b"print('TRY_AGAIN')\n"),
            session.model_request_result,
            session.ask_model_for_continuation,
        ):
            try:
                action()
            except TerminalSubmissionBlocked:
                pass
            else:
                raise TerminalSubmissionBlocked("Model accessed a forbidden post-terminal path")
        if not session.terminal or session.attempted_executions != 0:
            raise TerminalSubmissionBlocked("Offline broker tried to execute native code")
    return {
        "status": "OFFLINE_TERMINAL_ONE_SHOT_NONINTERFERENCE_PASS",
        "constant_public_receipt": public_receipt,
        "public_receipt_byte_identical_across_different_code_and_host_results": True,
        "post_terminal_model_continue_and_result_observation_rejected": True,
        "post_terminal_retry_rejected": True,
        "private_host_outcomes_differ_but_model_observation_does_not": True,
        "real_model_transport_implemented": False,
        "real_Docker_or_Python_candidate_execution_by_broker": False,
        "real_security_sandbox_attestation_from_this_test": False,
        "new_real_matched_LLM_trials": 0,
        "paid_provider_calls": 0,
    }
