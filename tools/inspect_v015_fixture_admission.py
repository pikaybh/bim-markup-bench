"""Read-only admission check for known legacy worktree-only test fixtures.

This does NOT auto-copy private/large assets, change benchmark pinning,
rewrite frozen reports, or deem an entire historic test suite valid.
Used to distinguish an unmounted fixture from actual runtime regressions.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from src.data.bim_edit import TASK_SHA256

PREVIOUS_PREFLIGHT = Path(
    "results/bibimbap_original_45_luna_20261112_issue112/preflight.json"
)
PUBLIC_TASKS = Path("data/tasks.jsonl")


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def inspect_fixture_admission(worktree: Path, primary_repo: Path,
                              issue112_repo: Path) -> dict:
    if not worktree.is_dir() or not (worktree / "AGENTS.md").is_file():
        raise ValueError("Existing research worktree with AGENTS.md required")
    mapped = (
        ("frozen_bim_edit_public_task_catalog", PUBLIC_TASKS,
         primary_repo / PUBLIC_TASKS, TASK_SHA256.lower()),
        ("historical_bibimbap_model_preflight", PREVIOUS_PREFLIGHT,
         issue112_repo / PREVIOUS_PREFLIGHT, None),
    )
    records = []
    for name, rel, proposed_seed, expected in mapped:
        destination = worktree / rel
        seed_exists = proposed_seed.is_file() and not proposed_seed.is_symlink()
        destination_exists = destination.is_file() and not destination.is_symlink()
        seed_digest = _sha(proposed_seed) if seed_exists else None
        current_digest = _sha(destination) if destination_exists else None
        if expected and seed_digest is not None and seed_digest != expected:
            state = "SOURCE_HASH_PIN_MISMATCH"
        elif expected and current_digest is not None and current_digest != expected:
            state = "LOCAL_HASH_PIN_MISMATCH"
        elif destination_exists and seed_exists and seed_digest != current_digest:
            state = "WORKTREE_FIXTURE_DIFFERS_FROM_SEED"
        elif destination_exists and (
            (expected is not None and current_digest == expected)
            or (seed_exists and seed_digest == current_digest)
        ):
            state = "ADMITTED_LOCAL_MATCH"
        elif destination_exists and not seed_exists:
            state = "LOCAL_PRESENT_WITHOUT_VERIFIABLE_SEED"
        elif seed_exists:
            state = "MISSING_ISOLATED_WORKTREE_MOUNT"
        else:
            state = "MISSING_ISOLATED_FIXTURE_AND_SEED"
        records.append({
            "logical_fixture": name,
            "worktree_relative_path": rel.as_posix(),
            "source_hash_expected_if_pinned": expected,
            "source_hash_actual_if_available": seed_digest,
            "worktree_hash_actual_if_available": current_digest,
            "source_file_available": seed_exists,
            "worktree_file_available": destination_exists,
            "admission_status": state,
            "source_file_content_in_report": False,
        })
    return {
        "status": "PASS_KNOWN_FIXTURES_ADMITTED" if all(
            r["admission_status"] == "ADMITTED_LOCAL_MATCH" for r in records
        ) else "BLOCKED_KNOWN_FIXTURES_NOT_ADMITTED",
        "fixture_admission_is_not_full_suite_success": True,
        "prior_832_case_run_had": {
            "tests_run": 832, "failures": 9, "errors": 65, "skipped": 67,
            "run_origin": "independent_existing_v014_isolated_worktree_run_20261114",
        },
        "unresolved_legacy_gate_and_code_page_failures_require_separate_evidence": True,
        "automatic_copy_or_original_data_modification": False,
        "official_scores_or_model_calls": 0,
        "fixtures": records,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--worktree", type=Path, required=True)
    p.add_argument("--primary-repo", type=Path, required=True)
    p.add_argument("--issue112-repo", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists() or a.output.is_symlink():
        p.error("Refusing to overwrite an existing fixture admission record")
    record = inspect_fixture_admission(a.worktree, a.primary_repo, a.issue112_repo)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x", encoding="utf8", newline="\n") as f:
        json.dump(record, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")
    print(record["status"], "known fixtures:", len(record["fixtures"]))


if __name__ == "__main__":
    main()
