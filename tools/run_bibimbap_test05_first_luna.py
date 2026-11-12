"""First *actual* BIBIMBAP XML-only GPT-6 Luna trial (#110).

One user-approved standard OpenAI request, one model-generated XML attempt,
and at most USD 1.00. Never an API/typed command, code interpreter or model
feedback. Source and model outputs preserved in ignored local results/.
Run ONLY with --live-approved; --preflight never contacts the provider.
Original author grader is invoked only AFTER the model response is fixed.
No BIXML/Xim source is accessed, modified, or imported.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
MODEL = "gpt-6-luna"
ISSUE = "https://github.com/pikaybh/bim-markup-bench/issues/110"
APPROVED_CAP_USD = Decimal("1.00")
STANDARD_INPUT_USD_PER_1M = Decimal("0.10")
STANDARD_OUTPUT_USD_PER_1M = Decimal("0.50")
MAX_OUTPUT_TOKENS = 16000
PROMPT_EXPECTED_SHA = "2a483f97bf36726c2930ed9df8e80e1106f34bde460416a0c0b11fb3ea736959"
OUTPUT_ROOT = ROOT / "results"
P0_DOTENV = ROOT.parent / "bim-markup-bench" / ".env"
LOCAL_RUN_NAME = "bibimbap_test05_luna_one_shot_20261112_110"

from tools.bibimbap_public_packet import (
    make_public_packet, read_public_pilot, sha,
)


class LiveAdmissionBlocked(ValueError):
    pass


def hash_file(path: Path) -> str:
    return sha(path.read_bytes())


def serial_json(obj: object) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def saved_summary(path: Path, item: dict) -> None:
    # Metadata evolves as the single attempt moves through mutually exclusive
    # stages. Model source/response files use exclusive creation, never update.
    temp = path.with_name(path.name + ".part")
    with temp.open("xb") as f:
        f.write(serial_json(item))
    temp.replace(path)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def preflight(dataset: Path, *, verify_local_key: bool = False) -> tuple[dict, dict]:
    packet, safe = make_public_packet(dataset)
    if safe["model_packet_sha256"] != PROMPT_EXPECTED_SHA:
        raise LiveAdmissionBlocked("Previously frozen public model packet hash drift")
    saved = json.loads(
        (ROOT / "reports" / "bibimbap_test05_public_packet_preflight_20261112.json")
        .read_text(encoding="utf8")
    )
    if safe["normalized_input_ifc_sha256"] != saved["normalized_input_ifc_sha256"]:
        raise LiveAdmissionBlocked("Original normalized IFC data drift")
    if safe["public_xml_sha256"] != saved["public_xml_sha256"]:
        raise LiveAdmissionBlocked("Source XML state drift")
    total_input_bytes = sum(len(x.encode("utf8")) for x in packet.values())
    if total_input_bytes > 120000:
        raise LiveAdmissionBlocked("Input exceeds fixed conservative byte ceiling")
    # For UTF-8 text, token count cannot exceed byte count; add margin
    # and multiply full-tariff estimate by 10 to cover unexpected routing
    # or pricing uplift. One request, no retries and no tool calls.
    pessimistic_input_tokens = total_input_bytes + 2048
    one_request_upper = (
        Decimal(pessimistic_input_tokens) * STANDARD_INPUT_USD_PER_1M +
        Decimal(MAX_OUTPUT_TOKENS) * STANDARD_OUTPUT_USD_PER_1M
    ) / Decimal(1000000)
    tenfold_reservation = one_request_upper * Decimal(10)
    if tenfold_reservation > APPROVED_CAP_USD:
        raise LiveAdmissionBlocked("Bounded model request exceeds owner-approved dollar cap")
    if verify_local_key:
        from dotenv import load_dotenv
        load_dotenv(P0_DOTENV, override=False)
        if os.getenv("OPENAI_MODEL") != MODEL:
            raise LiveAdmissionBlocked("Configured OPENAI_MODEL not the explicitly approved one")
        if not os.getenv("OPENAI_API_KEY"):
            raise LiveAdmissionBlocked("Missing local API key")
        if os.getenv("OPENAI_BASE_URL"):
            raise LiveAdmissionBlocked("Custom provider endpoint blocked for this experiment")
    plan = {
        "scope": "REAL_SINGLE_TASK_BIBIMBAP_XML_ONLY",
        "issue": ISSUE,
        "user_approved_model": MODEL,
        "user_approved_spending_cap_usd": str(APPROVED_CAP_USD),
        "request_count_authorized": 1,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "reasoning_effort": "medium",
        "temperature": "provider_default",
        "standard_service_tier": "default",
        "provider_response_storage": False,
        "provider_tools": [],
        "provider_retries": 0,
        "dataset_sha": safe["dataset_commit_sha"],
        "original_ifc_sha256": safe["original_ifc_sha256"],
        "public_packet_sha256": safe["model_packet_sha256"],
        "model_visible_original_gt": False,
        "model_visible_author_grader": False,
        "standard_pricing_checked_on": "2026-11-12",
        "standard_pricing_url": "https://developers.openai.com/api/docs/pricing",
        "standard_input_per_million_usd": str(STANDARD_INPUT_USD_PER_1M),
        "standard_output_per_million_usd": str(STANDARD_OUTPUT_USD_PER_1M),
        "request_cost_reservation_10x_usd": str(tenfold_reservation),
        "bill_invoice_reconciled": False,
        "actual_api_calls_attempted": 0,
    }
    return packet, plan


def _trusted_score(dataset: Path, author: Path, raw_source: bytes, folder: Path) -> dict:
    """Never called from the model. Exact raw output, no repair/postediting."""
    import ifcopenshell
    import ifcopenshell.util.unit
    from src.runtime.compiler import compile_declarative_xml
    from tools.bibimbap_test05_native_core import evaluate_public_test05_core
    from tools.audit_bibimbap_author import WORKER, _head, AUTHOR_SHA, DATA_SHA
    from src.security.agent_boundary import check_xml_bytes

    if _head(author) != AUTHOR_SHA or _head(dataset) != DATA_SHA:
        raise ValueError("Original author grader or dataset commit mismatch")
    check_xml_bytes(raw_source)
    _public, original_path = read_public_pilot(dataset)
    original_hash = hash_file(original_path)
    raw_input = ifcopenshell.open(str(original_path))
    normalized = ifcopenshell.util.unit.convert_file_length_units(raw_input, "METER")
    normalized_path = folder / "source_normalized_m.ifc"
    normalized.write(str(normalized_path))
    if hash_file(normalized_path) != json.loads(
            (ROOT / "reports/bibimbap_test05_public_packet_preflight_20261112.json")
            .read_text(encoding="utf8"))["normalized_input_ifc_sha256"]:
        raise ValueError("Normalized original IFC hash differs from fixed public packet")
    native_m_path = folder / "candidate_result_m.ifc"
    compilation = compile_declarative_xml(normalized_path, raw_source, native_m_path)
    compiled = ifcopenshell.open(str(native_m_path))
    restored = ifcopenshell.util.unit.convert_file_length_units(compiled, "MILLIMETER")
    native_mm_path = folder / "candidate_result_mm.ifc"
    restored.write(str(native_mm_path))
    original_score = subprocess.run(
        [sys.executable, "-I", str(WORKER),
         "--author-repo", str(author), "--test", "test_05",
         "--source-ifc", str(original_path),
         "--edited-ifc", str(native_mm_path)],
        capture_output=True, text=True, timeout=60, check=False,
    )
    if original_score.returncode != 0 or not original_score.stdout:
        raise ValueError("Pinned original author worker returned no valid scoring result")
    native_author = json.loads(original_score.stdout.splitlines()[-1])
    if native_author.get("status") != "SCORED":
        raise ValueError("Original author scorer did not complete successfully")
    task_core = evaluate_public_test05_core(original_path, native_mm_path)
    if hash_file(original_path) != original_hash:
        raise ValueError("Original external IFC changed while scoring")
    return {
        "trusted_compiler_status": compilation.as_dict()["status"],
        "native_result_sha256": hash_file(native_mm_path),
        "original_author_score": native_author["score"],
        "original_author_metric_vector": native_author["metrics"],
        "original_author_status": native_author["status"],
        "independent_native_public_task_core": task_core,
        "full_independent_strict_task_success": None,
        "native_ifc_path_local_only": str(native_mm_path),
        "author_grader_not_exposed_to_llm": True,
    }


def execute(dataset: Path, author: Path, out: Path) -> dict:
    packet, plan = preflight(dataset, verify_local_key=True)
    from tools.audit_bibimbap_author import _head, AUTHOR_SHA, DATA_SHA
    if _head(author) != AUTHOR_SHA or _head(dataset) != DATA_SHA:
        raise LiveAdmissionBlocked("Original scorer or dataset commit not pinned")
    fixed_local = OUTPUT_ROOT / LOCAL_RUN_NAME
    if out.resolve() != fixed_local.resolve():
        raise LiveAdmissionBlocked("The approved single run has exactly one fixed output path")
    if out.is_symlink() or out.exists():
        raise LiveAdmissionBlocked("Run path already exists; one attempt cannot be rerun")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir(mode=0o700)
    report = {
        **plan, "record_created_utc": now_utc(),
        "status": "PREPARING_SINGLE_APPROVED_REQUEST",
        "raw_model_output_saved": False,
        "actual_provider_usage_cost_estimate_usd": None,
        "provider_bill_reconciliation": "PENDING",
        "model_edit_attempts": 0,
        "original_author_score": None,
        "independent_native_core_success": None,
        "full_independent_strict_task_success": None,
    }
    saved_summary(out / "results_local.json", report)
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                    timeout=160, max_retries=0)
    report["actual_api_calls_attempted"] = 1
    report["model_edit_attempts"] = 1
    report["status"] = "PROVIDER_ATTEMPT_ISSUED"
    saved_summary(out / "results_local.json", report)
    try:
        started = perf_counter()
        answer = client.responses.create(
            model=MODEL, instructions=packet["instructions"],
            input=packet["input"], max_output_tokens=MAX_OUTPUT_TOKENS,
            reasoning={"effort": "medium"},
            store=False, tools=[], service_tier="default",
        )
        report["provider_roundtrip_seconds"] = round(perf_counter() - started, 3)
        report["provider_status"] = answer.status
        report["provider_returned_model"] = answer.model
        report["provider_response_id_sha256"] = sha(str(answer.id).encode("utf8"))
        with (out / "provider_response_raw.json").open("xb") as f:
            f.write(answer.model_dump_json(indent=2).encode("utf8"))
        report["raw_provider_response_sha256"] = hash_file(out / "provider_response_raw.json")
        output = answer.output_text
        with (out / "model_generated_exact.raw.txt").open("xb") as f:
            f.write((output or "").encode("utf8"))
        report["raw_model_output_saved"] = True
        report["raw_model_output_sha256"] = hash_file(out / "model_generated_exact.raw.txt")
        report["raw_model_output_bytes"] = len((output or "").encode("utf8"))
        report["raw_model_output_path_local_only"] = str(out / "model_generated_exact.raw.txt")
        usage = answer.usage
        if usage is not None:
            report["reported_input_tokens"] = usage.input_tokens
            report["reported_output_tokens"] = usage.output_tokens
            report["actual_provider_usage_cost_estimate_usd"] = str(
                (Decimal(usage.input_tokens) * STANDARD_INPUT_USD_PER_1M +
                 Decimal(usage.output_tokens) * STANDARD_OUTPUT_USD_PER_1M
                ) / Decimal(1000000))
        saved_summary(out / "results_local.json", report)
        if answer.status != "completed" or not output:
            report["status"] = "PROVIDER_INCOMPLETE_OR_EMPTY_NO_RETRY"
            return report
        # Critical: raw output exactly as returned, without stripping
        # markdown, XML prefixes, trailing spaces or commentary.
        try:
            grade = _trusted_score(dataset, author, output.encode("utf8"), out)
            report["scoring"] = grade
            report["original_author_score"] = grade["original_author_score"]
            report["independent_native_core_success"] = grade[
                "independent_native_public_task_core"]["public_task_core_success"]
            report["status"] = "ONE_REAL_MODEL_EDIT_SCORED"
        except Exception as exc:
            report["status"] = "MODEL_XML_OR_GRADING_FAILED_NO_RETRY"
            report["grader_failure_type"] = type(exc).__name__
            # Exception strings may include original IFC/answer paths and
            # private grader details; deliberately never log them.
            report["original_author_score"] = None
        return report
    except Exception as exc:
        report["status"] = "PROVIDER_CALL_FAILED_NO_RETRY"
        report["provider_failure_type"] = type(exc).__name__
        return report
    finally:
        report["record_finished_utc"] = now_utc()
        saved_summary(out / "results_local.json", report)


def public_git_summary(report: dict) -> dict:
    allow = [
        "scope", "issue", "user_approved_model",
        "user_approved_spending_cap_usd", "request_count_authorized",
        "max_output_tokens", "reasoning_effort", "temperature",
        "standard_service_tier", "provider_response_storage",
        "provider_tools", "provider_retries",
        "dataset_sha", "original_ifc_sha256",
        "public_packet_sha256", "model_visible_original_gt",
        "model_visible_author_grader", "standard_pricing_checked_on",
        "standard_pricing_url", "standard_input_per_million_usd",
        "standard_output_per_million_usd", "request_cost_reservation_10x_usd",
        "bill_invoice_reconciled", "actual_api_calls_attempted",
        "record_created_utc", "record_finished_utc",
        "status", "raw_model_output_saved", "actual_provider_usage_cost_estimate_usd",
        "provider_bill_reconciliation", "model_edit_attempts",
        "provider_roundtrip_seconds", "provider_status",
        "provider_returned_model", "provider_response_id_sha256",
        "raw_provider_response_sha256", "raw_model_output_sha256",
        "raw_model_output_bytes", "reported_input_tokens",
        "reported_output_tokens", "original_author_score",
        "independent_native_core_success", "full_independent_strict_task_success",
        "grader_failure_type", "provider_failure_type",
    ]
    safe = {k: report[k] for k in allow if k in report}
    if report.get("scoring"):
        v = report["scoring"]
        safe["trusted_compiler_status"] = v["trusted_compiler_status"]
        safe["native_result_sha256"] = v["native_result_sha256"]
        safe["original_author_metric_vector"] = v["original_author_metric_vector"]
        safe["native_public_task_core_metrics"] = {
            k: value for k, value in v["independent_native_public_task_core"].items()
            if k not in ("source_original_sha256", "predicted_result_sha256")
        }
    safe["raw_provider_artifacts_are_git_ignored"] = True
    safe["model_output_modified_after_generation"] = False
    safe["full_45_task_experiment_performed"] = False
    safe["noncausal_single_task_pilot_only"] = True
    return safe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--author-repo", type=Path)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--live-approved", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--safe-summary", type=Path)
    args = parser.parse_args()
    if args.preflight == args.live_approved:
        parser.error("Exactly one of --preflight or --live-approved is required")
    if args.preflight:
        _packet, plan = preflight(args.dataset, verify_local_key=True)
        print(json.dumps({**plan, "preflight": "PASS_ZERO_PAID_CALLS"}, sort_keys=True))
        return 0
    if not args.author_repo or not args.out or not args.safe_summary:
        parser.error("Live approved run requires --author-repo, --out and --safe-summary")
    fixed_git_summary = ROOT / "reports" / "bibimbap_test05_luna_first_real_20261112.json"
    if args.safe_summary.resolve() != fixed_git_summary.resolve():
        parser.error("Only the owner-approved one-shot report destination is allowed")
    if args.safe_summary.exists() or args.safe_summary.is_symlink() or not args.safe_summary.parent.is_dir():
        parser.error("Git-safe result destination must be new and in an existing folder")
    try:
        result = execute(args.dataset, args.author_repo, args.out)
        with args.safe_summary.open("xb") as f:
            f.write(serial_json(public_git_summary(result)))
        print(json.dumps({k: result.get(k) for k in (
            "status", "actual_api_calls_attempted", "reported_input_tokens",
            "reported_output_tokens", "actual_provider_usage_cost_estimate_usd",
            "raw_model_output_sha256", "original_author_score",
            "independent_native_core_success")}, sort_keys=True))
        return 0 if result["status"] == "ONE_REAL_MODEL_EDIT_SCORED" else 2
    except (LiveAdmissionBlocked, ValueError, OSError) as exc:
        # Never leak private paths or API-key values from exception strings.
        print(json.dumps({"status": "EXPERIMENT_ADMISSION_BLOCKED", "error_type": type(exc).__name__}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
