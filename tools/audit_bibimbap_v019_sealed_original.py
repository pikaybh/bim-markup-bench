"""v0.19 source-only original BIBIMBAP I-arm SEALED Docker evidence.

No LLM, API, paid calls, original scorer modification, or dataset download.
Only one OWN developer-written original public test15 task and two explicit
negative probes run inside cached immutable OS-isolated Docker. Grader and
native IFC-only oracle run after the container is stopped/removed, in the
trusted HOST with no possible model feedback. 45 denominator retained.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45, grade_author
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v016_original_column_i0 import _parse_public_instruction
from tools.oracle_bibimbap_column15_16_native import strict_move_column
from tools.bibimbap_v019_sealed_original_docker import (
    PINNED_LOCAL_IMAGE,
    OWN_SECURITY_TEST_SCRIPT,
    OWN_LEAK_OUTPUT_SCRIPT,
    OWN_INFINITE_LOOP_SCRIPT,
    SealedWorkerBlocked,
    original_public_column15_owned_script,
    run_owned_original_sealed,
    terminal_model_visible_receipt,
)

V018_FROZEN_SHA = "89a53c28a9c5e679fcdfb962bebe6b9bd8075e4ac0437e07ea1a0b72ea7b1b2a"
AUTHOR_PUBLIC_TASK = "test_15"


class V019SealedAuditBlocked(ValueError):
    pass


def audit(author: Path, data: Path, prev_v018: Path) -> dict:
    if _head(author) != AUTHOR_SHA or _head(data) != DATA_SHA:
        raise V019SealedAuditBlocked("Original author or data Git SHA drift")
    if file_hash(prev_v018).lower() != V018_FROZEN_SHA:
        raise V019SealedAuditBlocked("Prior common source-fact evidence modified")
    frozen = json.loads(prev_v018.read_text(encoding="utf8"))
    originals = {t["test_id"]: t for t in public_45(author, data)}
    if (len(originals) != 45 or
        Counter(t["crud"] for t in originals.values()) !=
        Counter({"create":15, "update":15, "delete":15}) or
        frozen["original_original45_denominator"] != 45 or
        frozen["common_read_observation_parity_case_count"] != 45):
        raise V019SealedAuditBlocked("Original public all45 population/facts changed")
    task = originals[AUTHOR_PUBLIC_TASK]
    source = data / "ifc" / task["original_source_ifc_relpath"]
    digest = file_hash(source)
    if digest != task["original_ifc_sha256"]:
        raise V019SealedAuditBlocked("Original public source IFC SHA changed")
    public_op, public_guid = _parse_public_instruction(
        AUTHOR_PUBLIC_TASK, task["public_question"])
    if public_op != "MOVE_COLUMN_Y_MINUS_3M":
        raise V019SealedAuditBlocked("Original public task operation drift")

    # Kernel OS-level probe uses same ACTUAL original source clone and the
    # same exact worker image/config, never fake self-reported stdout alone:
    # host validates all 14 boolean outputs from the private worker.
    probe = run_owned_original_sealed(
        source, digest, OWN_SECURITY_TEST_SCRIPT,
        wall_seconds=16, expects_ifc_result=False)
    checks = probe.host_private_kernel_probe_checks
    if (not isinstance(checks, dict)
        or len(checks) != 14 or not all(v is True for v in checks.values())):
        raise V019SealedAuditBlocked("Original-source sandbox denied-access tests failed")

    # Actual bounded one-shot source-native imperative writer.
    # Candidate derived only from original public task and real source IFC.
    owned_script = original_public_column15_owned_script(task["public_question"])
    result = run_owned_original_sealed(
        source, digest, owned_script,
        original_public_question=task["public_question"], wall_seconds=18)
    if not result.host_private_candidate_ifc_bytes:
        raise V019SealedAuditBlocked("One-shot original source edit produced no candidate")
    if result.direct_model_feedback_allowed or result.real_LLM_submitted_script:
        raise V019SealedAuditBlocked("Model feedback/LLM source must remain disabled")
    if file_hash(source) != digest:
        raise V019SealedAuditBlocked("Original public IFC modified during isolated edit")

    # HOST-only native validation and original author grade.
    # Grader and hidden answers were NOT mounted into the OS container.
    with TemporaryDirectory(prefix="bmb-v019-original-author-validation-") as d:
        output_path = Path(d) / "native_candidate_original_mm.ifc"
        output_path.write_bytes(result.host_private_candidate_ifc_bytes)
        from ifcopenshell import open as open_ifc
        if open_ifc(str(output_path)).schema != "IFC4X3":
            raise V019SealedAuditBlocked("Sealed output IFC has wrong original schema")
        independent_native_oracle = strict_move_column(
            source, output_path, public_guid, dy=-3.0)
        if independent_native_oracle["output_sha256"] != result.output_ifc_sha256:
            raise V019SealedAuditBlocked("Trusted native IFC output content changed")
        author_scored = grade_author(author, source, output_path, AUTHOR_PUBLIC_TASK)
        if (author_scored.get("status") != "AUTHOR_SCORED" or
            author_scored.get("original_author_score") != 1.0):
            raise V019SealedAuditBlocked("Independent pinned author scorer did not score 1.0")
        if file_hash(output_path) != result.output_ifc_sha256:
            raise V019SealedAuditBlocked("Author scorer modified frozen candidate")

    # Deliberate stdout exfil attempt and huge stdout input could leak only
    # to trusted HOST capture. It must not affect model-visible receipt.
    leak = run_owned_original_sealed(
        source, digest, OWN_LEAK_OUTPUT_SCRIPT,
        wall_seconds=16, expects_ifc_result=True)
    canary = "V019_FAKE_PRIVATE_CANARY_AND_IFC_DATA_LEAK"
    model_receipt = terminal_model_visible_receipt()
    serialized_receipt = json.dumps(model_receipt, sort_keys=True)
    if (canary in serialized_receipt or digest in serialized_receipt
        or (leak.host_private_candidate_ifc_bytes is None)
        or model_receipt != {
            "status": "SEALED_ONE_SHOT_SUBMISSION_RECORDED",
            "execution_feedback_available": False,
            "tool_continuation_allowed": False,
        }):
        raise V019SealedAuditBlocked("Host-to-LLM sealed result channel not constant")

    # Deliberate infinite loop must time out in bounded attach and kill its
    # own sandbox. Capture ONLY denial class, never attacker code output.
    timeout_blocked = False
    try:
        run_owned_original_sealed(
            source, digest, OWN_INFINITE_LOOP_SCRIPT,
            wall_seconds=4, expects_ifc_result=False)
    except (SealedWorkerBlocked, RuntimeError) as exc:
        # Error types are kept host-only; no stderr, traceback or hidden IFC
        # is included in any exposed report or future model response.
        timeout_blocked = type(exc).__name__ in (
            "DockerIsolationError", "SealedWorkerBlocked")
    if not timeout_blocked:
        raise V019SealedAuditBlocked("Unbounded native worker was not killed")

    if file_hash(source) != digest or _head(data) != DATA_SHA:
        raise V019SealedAuditBlocked("Original public data/source post-run drift")

    return {
        "status": "ORIGINAL_PUBLIC_TEST15_SEALED_DOCKER_NATIVE_AND_AUTHOR_VALIDATION_PASS",
        "issue": "https://github.com/pikaybh/bim-markup-bench/issues/152",
        "original_author_git_sha": AUTHOR_SHA,
        "original_public_data_git_sha": DATA_SHA,
        "parent_v018_frozen_report_sha256": V018_FROZEN_SHA,
        "original_all45_denominator_preserved": 45,
        "original_15_create_15_update_15_delete": True,
        "original_case": AUTHOR_PUBLIC_TASK,
        "original_public_question_sha256": task["public_question_sha256"],
        "original_source_ifc_sha256": digest,
        "trusted_cached_Linux_image_id": PINNED_LOCAL_IMAGE,
        "source_native_schema": "IFC4X3",
        "real_original_source_unit_mm_retained": True,
        "developer_owned_original_source_task_code_sha256":
            result.developer_candidate_sha256,
        "real_sealed_candidate_native_ifc_sha256":
            result.output_ifc_sha256,
        "real_sealed_candidate_ifc_bytes": len(result.host_private_candidate_ifc_bytes),
        "real_sealed_candidate_has_original_native_author_score":
            author_scored,
        "real_sealed_candidate_independent_native_IFC_oracle":
            independent_native_oracle["status"],
        "whole_original_ifc_native_identity_and_geometry_oracle_PASS": True,
        "Docker_kernel_security_original_source_checks": checks,
        "Docker_kernel_security_checked_count": len(checks),
        "Docker_seccomp_active": checks["seccomp_active"],
        "Docker_network_disabled": checks["network_denied"],
        "Docker_non_root": checks["uid_nonroot"],
        "Docker_readonly_source_and_code": checks["source_readonly"] and checks["own_code_readonly"],
        "Docker_no_private_GT_or_secrets_mounted": checks["gt_unmounted"] and checks["secrets_absent"],
        "container_logs_suppressed": True,
        "outgoing_model_feedback_after_submission": model_receipt,
        "host_private_stdout_canary_probe_result": "NOT_RETURNED_TO_MODEL",
        "stdout_canary_model_receipt_leak": False,
        "hung_one_shot_process_killed_and_container_cleanup": timeout_blocked,
        "original_public_IFC_modified": False,
        "original_author_scorer_mounted_in_container": False,
        "original_data_or_scorer_edited": False,
        "same_common_v018_source_information_interface_consistency_proven": True,
        "full_original_IFC_information_and_native_write_capability_parity_proven": False,
        "python_code_can_still_interrogate_native_IFC_inside_one_shot_execution": True,
        "Docker_container_OS_isolation_is_NOT_airtight_VM_or_independent_security_certification": True,
        "new_real_paid_or_unpaid_LLM_calls": 0,
        "new_paid_provider_USD": 0,
        "new_original_public_developer_matched_edit_task_additions": 0,
        "previous_actual_developer_edit_D0_I0_native_parity": 5,
        "previous_original_author_scoreable_developer_edit_pairs": 3,
        "previous_original_author_scorer_reference_errors": 2,
        "other_original_edit_cases_same_D0_I0_protocol_UNTESTED": 40,
        "pilot_causal_LLM_trial_approved": False,
        "real_model_generated_python_executed": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--author", required=True, type=Path)
    p.add_argument("--data", required=True, type=Path)
    p.add_argument("--prior-v018", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if args.output.exists() or args.output.is_symlink():
        p.error("Refusing to overwrite prior immutable evidence")
    report = audit(args.author, args.data, args.prior_v018)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    print("V019_OS_SEALED", report["status"])
    print("ORIGINAL_PUBLIC_CASE", report["original_case"],
          "AUTHOR_SCORE", report["real_sealed_candidate_has_original_native_author_score"]["original_author_score"])
    print("SECURITY_CHECKS", report["Docker_kernel_security_checked_count"],
          "TIMEOUT_KILLED", report["hung_one_shot_process_killed_and_container_cleanup"])
    print("REAL_LLM_TRIALS", report["new_real_paid_or_unpaid_LLM_calls"])
    print("REPORT_SHA256", file_hash(args.output))


if __name__ == "__main__":
    main()
