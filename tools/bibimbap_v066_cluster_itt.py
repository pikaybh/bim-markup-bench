"""Offline, evaluator-side paired intention-to-treat analysis for Issue #247.

This module deliberately has no model, IFC, filesystem-scanning, or grader imports.
It never authenticates blindness/rights or authorizes a trial.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ARMS = ("D_FULL", "D_MANAGED", "I_NATIVE")
STATUSES = frozenset(
    ("completed", "unsupported", "invalid", "engine_error", "timeout", "aborted", "not_attempted")
)
REGIMES = frozenset(("one_shot", "iterative"))
OPERATIONS = frozenset(("create", "update", "delete"))
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,79}\Z")
MANIFEST_KEYS = frozenset(("protocol_id", "cohort_kind", "regime", "arms", "cohort"))
COHORT_KEYS = frozenset(("source_sha256", "task_id", "seed", "operation"))
OUTCOME_KEYS = frozenset(("source_sha256", "task_id", "seed", "arm", "status", "strict_pass"))
CONTRASTS = (("D_FULL", "I_NATIVE"), ("D_MANAGED", "I_NATIVE"), ("D_FULL", "D_MANAGED"))


class AnalysisInputError(ValueError):
    """Invalid or incomplete prospective trial ledger; never silently drop an ITT row."""


def _unique_json_pairs(pairs: list[tuple[str, Any]]) -> dict:
    """Reject duplicate JSON fields instead of silently overriding frozen values."""
    result = {}
    for name, value in pairs:
        if name in result:
            raise AnalysisInputError(f"duplicate JSON key: {name}")
        result[name] = value
    return result


def load_strict_json(payload: bytes) -> Any:
    """Parse strict JSON with no duplicate keys or NaN/Infinity."""
    def invalid_constant(value: str) -> None:
        raise AnalysisInputError(f"non-JSON numeric constant: {value}")

    return json.loads(payload, object_pairs_hook=_unique_json_pairs, parse_constant=invalid_constant)


def _fields(value: Any, required: frozenset[str], where: str) -> dict:
    if not isinstance(value, dict) or set(value) != required:
        raise AnalysisInputError(f"{where}: expected exactly {sorted(required)}")
    return value


def _identity(value: dict, where: str) -> tuple[str, str, int]:
    source = value["source_sha256"]
    task = value["task_id"]
    seed = value["seed"]
    if not isinstance(source, str) or SHA256.fullmatch(source) is None:
        raise AnalysisInputError(f"{where}: source_sha256 must be 64 lowercase hex characters")
    if not isinstance(task, str) or TASK_ID.fullmatch(task) is None:
        raise AnalysisInputError(f"{where}: invalid task_id")
    if type(seed) is not int or seed < 0 or seed >= (2**32):
        raise AnalysisInputError(f"{where}: seed must be an unsigned 32-bit integer")
    return source, task, seed


def _validated(manifest: Any, outcomes: Any) -> tuple[dict, dict, list[tuple[str, str, int]]]:
    m = _fields(manifest, MANIFEST_KEYS, "manifest")
    if not isinstance(m["protocol_id"], str) or not TASK_ID.fullmatch(m["protocol_id"]):
        raise AnalysisInputError("manifest: invalid protocol_id")
    if m["cohort_kind"] != "developer_exposed_exploratory":
        raise AnalysisInputError("Only exploratory developer-exposed cohorts are admitted without independent external certification")
    if m["regime"] not in REGIMES:
        raise AnalysisInputError("manifest: invalid regime")
    if type(m["arms"]) is not list or m["arms"] != list(ARMS):
        raise AnalysisInputError("manifest: three fixed arms in canonical order required")
    if not isinstance(m["cohort"], list) or not m["cohort"]:
        raise AnalysisInputError("manifest: nonempty cohort list required")
    manifest_rows: dict[tuple[str, str, int], dict] = {}
    for index, raw in enumerate(m["cohort"]):
        row = _fields(raw, COHORT_KEYS, f"cohort[{index}]")
        key = _identity(row, f"cohort[{index}]")
        if row["operation"] not in OPERATIONS:
            raise AnalysisInputError(f"cohort[{index}]: invalid operation")
        if key in manifest_rows:
            raise AnalysisInputError(f"cohort[{index}]: duplicate source/task/seed")
        manifest_rows[key] = row

    if not isinstance(outcomes, list):
        raise AnalysisInputError("outcomes must be an array of arm records")
    observed: dict[tuple[str, str, int, str], dict] = {}
    for index, raw in enumerate(outcomes):
        row = _fields(raw, OUTCOME_KEYS, f"outcomes[{index}]")
        key = _identity(row, f"outcomes[{index}]")
        arm = row["arm"]
        if arm not in ARMS:
            raise AnalysisInputError(f"outcomes[{index}]: invalid arm")
        if row["status"] not in STATUSES:
            raise AnalysisInputError(f"outcomes[{index}]: invalid status")
        if type(row["strict_pass"]) is not bool:
            raise AnalysisInputError(f"outcomes[{index}]: strict_pass must be a boolean")
        if row["status"] != "completed" and row["strict_pass"]:
            raise AnalysisInputError(f"outcomes[{index}]: non-completed attempts must not pass")
        four_key = (*key, arm)
        if four_key in observed:
            raise AnalysisInputError(f"outcomes[{index}]: duplicate arm result")
        if key not in manifest_rows:
            raise AnalysisInputError(f"outcomes[{index}]: result outside frozen cohort")
        observed[four_key] = row

    expected = {(*key, arm) for key in manifest_rows for arm in ARMS}
    if set(observed) != expected:
        missing = expected - set(observed)
        extras = set(observed) - expected
        raise AnalysisInputError(
            f"ITT is incomplete: missing={len(missing)} extra={len(extras)}; "
            "use explicit not_attempted/aborted rows, never omit failures"
        )
    return manifest_rows, observed, sorted(manifest_rows)


def _percentile(sorted_values: list[float], q: float) -> float:
    offset = (len(sorted_values) - 1) * q
    lo = math.floor(offset)
    hi = math.ceil(offset)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (offset - lo)


def _cluster_interval(
    paired: list[tuple[str, int]],
    *,
    seed: int,
    resamples: int,
) -> list[float] | None:
    groups: dict[str, list[int]] = defaultdict(list)
    for source_sha256, difference in paired:
        groups[source_sha256].append(difference)
    if len(groups) < 5:
        return None  # Too few independent source clusters for a useful percentile interval.
    keys = sorted(groups)
    rng = random.Random(seed)
    bootstrap: list[float] = []
    for _ in range(resamples):
        selected = [keys[rng.randrange(len(keys))] for _ in keys]
        numerator = sum(sum(groups[k]) for k in selected)
        denominator = sum(len(groups[k]) for k in selected)
        bootstrap.append(numerator / denominator)
    bootstrap.sort()
    return [round(_percentile(bootstrap, 0.025), 6), round(_percentile(bootstrap, 0.975), 6)]


def analyse_paired_itt(
    manifest: dict,
    outcomes: list[dict],
    *,
    bootstrap_seed: int = 20261119,
    bootstrap_resamples: int = 4000,
) -> dict:
    """Analyse COMPLETE synthetic/exploratory ledgers only; no hidden task scoring.

    Resample whole source-IFC clusters, retaining all task/seed pairs together.
    Task-weighted ITT difference is the primary descriptive estimand.
    """
    if type(bootstrap_seed) is not int or not (0 <= bootstrap_seed < 2**32):
        raise AnalysisInputError("bootstrap_seed must be an unsigned 32-bit integer")
    if type(bootstrap_resamples) is not int or not (500 <= bootstrap_resamples <= 20000):
        raise AnalysisInputError("bootstrap_resamples must be in [500, 20000]")
    manifest_rows, observed, keys = _validated(manifest, outcomes)
    by_arm = {}
    for arm in ARMS:
        counts = Counter(observed[(*key, arm)]["status"] for key in keys)
        passes = sum(observed[(*key, arm)]["strict_pass"] for key in keys)
        by_arm[arm] = {
            "n_ITT": len(keys),
            "strict_passes": passes,
            "strict_pass_rate_ITT": round(passes / len(keys), 6),
            "status_counts": {status: counts[status] for status in sorted(STATUSES)},
        }

    contrasts = {}
    for a, b in CONTRASTS:
        paired = [
            (key[0], int(observed[(*key, a)]["strict_pass"]) - int(observed[(*key, b)]["strict_pass"]))
            for key in keys
        ]
        diffs = [item[1] for item in paired]
        distinct_clusters = len({key[0] for key in keys})
        contrasts[f"{a}_minus_{b}"] = {
            "n_task_seed_pairs": len(keys),
            "n_independent_source_clusters": distinct_clusters,
            "ITT_strict_pass_difference": round(sum(diffs) / len(diffs), 6),
            "cluster_bootstrap_95pct_CI": _cluster_interval(
                paired, seed=bootstrap_seed, resamples=bootstrap_resamples
            ),
            "D_only_passes": sum(diff == 1 for diff in diffs),
            "comparator_only_passes": sum(diff == -1 for diff in diffs),
            "both_same": sum(diff == 0 for diff in diffs),
            "uncertainty_note": (
                "Exploratory task-weighted cluster bootstrap, NOT confirmatory inference"
                if distinct_clusters >= 5
                else "INSUFFICIENT_CLUSTERS: descriptive difference only"
            ),
        }

    by_operation = {}
    for operation in sorted(OPERATIONS):
        ops = [key for key in keys if manifest_rows[key]["operation"] == operation]
        if ops:
            by_operation[operation] = {
                "n_task_seed_pairs": len(ops),
                "ITT_pass_rates": {
                    arm: round(sum(observed[(*key, arm)]["strict_pass"] for key in ops) / len(ops), 6)
                    for arm in ARMS
                },
            }

    return {
        "verdict": "EXPLORATORY_DESCRIPTIVE_ONLY_NO_MODEL_OR_BLIND_CERTIFICATION",
        "protocol_id": manifest["protocol_id"],
        "regime": manifest["regime"],
        "cohort_kind": manifest["cohort_kind"],
        "n_independent_source_clusters": len({key[0] for key in keys}),
        "n_task_seed_pairs": len(keys),
        "bootstrap": {"seed": bootstrap_seed, "resamples": bootstrap_resamples, "unit": "source_ifc_sha256"},
        "by_arm": by_arm,
        "contrasts": contrasts,
        "by_operation": by_operation,
        "limitations": [
            "No genuine independent blind-source or data-rights certification",
            "No representation-only causal identification (D/I tool affordances differ)",
            "No official published scorer equivalence, paper-score claim, or actual model result implied",
            "Model launch blocked separately; this analysis never calls a provider",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline evaluator-side paired cluster ITT (exploratory only)")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--outcomes", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="Create only; refuses to replace an existing report")
    parser.add_argument("--bootstrap-seed", type=int, default=20261119)
    args = parser.parse_args()
    manifest_bytes = args.manifest.read_bytes()
    outcome_bytes = args.outcomes.read_bytes()
    report = analyse_paired_itt(
        load_strict_json(manifest_bytes), load_strict_json(outcome_bytes),
        bootstrap_seed=args.bootstrap_seed
    )
    report["input_sha256"] = {
        "manifest": hashlib.sha256(manifest_bytes).hexdigest(),
        "outcomes": hashlib.sha256(outcome_bytes).hexdigest(),
    }
    payload = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as file:
            file.write(payload)
        print(f"ANALYSIS_EXPLORATORY_ONLY={args.output}")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
