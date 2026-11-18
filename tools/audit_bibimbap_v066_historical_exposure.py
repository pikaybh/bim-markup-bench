"""v0.66 historical exposure audit: REPORTS ONLY, NOT unseen IFC/scorer access.

Research safeguard: an earlier metadata/source-tool inventory is NOT evidence
that a researcher read the answer, but it *is* evidence the source was processed.
An earlier XML-only model trial is NOT a matched XML vs Python result.

This script may only open the four SHA-pinned *existing research reports* below.
It never imports IfcOpenShell, opens original IFCs, reads original author graders,
uses credentials, connects to a provider, or changes earlier evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    "v065": (
        "bibimbap_v065_source_neutral_cross_schema_leakage_no_launch_20261118.json",
        "cc55f6623fc65d3936cf6ee9bbacf1c46d3893aa94122317632d9f90d009382d",
    ),
    "v043": (
        "bibimbap_v043_original45_native_XML_source_read_parity_20261117.json",
        "eb05633d152b1ff15e4fdd888bb62924b31b126f6cddd05fb23e54fce3ef8dbf",
    ),
    "v046": (
        "bibimbap_v046_original27_all_native_IFC_paged_source_catalog_20261117.json",
        "beab50998c1f2f984342cf784fe910adc384752a16b8f0eed40623421c38509f",
    ),
    "luna45": (
        "bibimbap_original45_luna_20261112.json",
        "719e3c2fbdbaee36e08249b7d671fe8b4a22a8f6e9d109101f87f2e0b34b86fb",
    ),
}
OUTPUT = ROOT / "reports" / "bibimbap_v066_historical_exposure_reconciliation_20261118.json"
DEVELOPER_EXPOSED = "EXPOSED_SOURCE_DEVELOPER_IMPLEMENTED_AUTHOR_METRICS"


class ExposureEvidenceError(ValueError):
    """Historical evidence changed or insufficiently specific."""


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise ExposureEvidenceError(message)


def canonical(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def load_pinned_reports(base: Path = ROOT) -> dict:
    result = {}
    for key, (name, expected_hash) in INPUTS.items():
        p = base / "reports" / name
        raw = p.read_bytes()
        require(sha256(raw).hexdigest() == expected_hash,
                f"{key}: frozen historical report SHA drift")
        result[key] = json.loads(raw)
    return result


def build_report(reports: dict) -> dict:
    """Use only pre-existing report metadata, never new IFC/GT or author grader."""
    v065, v043, v046, historical = (
        reports["v065"], reports["v043"], reports["v046"], reports["luna45"]
    )
    registry = v065["original_source_per_file_rights_ledger"]
    require(len(registry) == 31, "source-family registry must have exactly 31 SHAs")
    reg = {r["original_source_ifc_SHA256"]: r for r in registry}
    require(len(reg) == 31, "duplicate original source SHA")
    task_to_sha = {}
    for r in registry:
        for task_id in r["original_public_task_ids"]:
            require(task_id not in task_to_sha, "task belongs to multiple source clusters")
            task_to_sha[task_id] = r["original_source_ifc_SHA256"]
    require(len(task_to_sha) == 45, "original cohort must have 45 unique task IDs")

    native_rows = v043["original_31_unique_native_source_rows"]
    native_shas = [r["native_original_ifc_file_sha256"] for r in native_rows]
    require(len(native_shas) == 31 and len(set(native_shas)) == 31,
            "v0.43 source-native read registry must have 31 distinct source files")
    require(set(native_shas) == set(reg),
            "v0.43 native-read source hashes do not match v0.65 original cohort")
    # A source-native IFC counting/class/placement catalog is prior automated
    # inspection, NOT proof of a user/human manually reviewing a grader.
    for row in native_rows:
        require(isinstance(row.get("native_ifc_products_count"), int),
                "v0.43 must have actually counted native IFC source products")
        require(isinstance(row.get("native_ifc_products_with_geometric_representation_count"), int),
                "v0.43 must contain source representation census")

    catalog_rows = v046["original_27_unique_source_results"]
    catalog_shas = [r["source_original_public_IFC_sha256"] for r in catalog_rows]
    require(len(catalog_shas) == 27 and len(set(catalog_shas)) == 27,
            "v0.46 metadata/STEP catalog must have 27 distinct source families")
    require(set(catalog_shas).issubset(reg), "v0.46 contains unregistered source")

    attempts = historical["individual_results"]
    require(len(attempts) == 45, "prior original XML-only cohort must have 45 rows")
    attempt_by_task = {}
    for row in attempts:
        tid = row["test_id"]
        require(tid not in attempt_by_task, "duplicate historical trial task")
        require(tid in task_to_sha, "historical trial outside original 45 task population")
        require(row["original_ifc_sha256"] == task_to_sha[tid],
                "historical XML-only task/source family mismatch")
        require(row.get("strict_success_independent") is None,
                "historical independent strict success unexpectedly changed")
        attempt_by_task[tid] = row
    require(set(attempt_by_task) == set(task_to_sha),
            "historical XML-only task population does not match source ledger")
    prior_calls = sum(int(r["model_calls_attempted"]) for r in attempts)
    require(prior_calls == historical["provider_attempts_including_prior_test05"] == 36,
            "prior model-attempt count changed")
    require(sum(bool(r.get("author_full_score")) for r in attempts)
            == historical["author_full_score_count_45"] == 3,
            "prior author-score full-mark evidence changed")
    require(sum(r["status"] in {"ORIGINAL_AUTHOR_SCORED", "REUSED_EXISTING_REAL_ONE_SHOT"} for r in attempts) == 15,
            "prior author-scored original task population changed")
    require(v065["certified_independent_unseen_confirmatory_clusters"] == 0,
            "v0.65 source-blind evidence status drifted")
    require(v065["original_unique_source_sha_clusters"] == 31,
            "v0.65 source cluster count drifted")

    entries = []
    for source_sha, r in sorted(reg.items()):
        task_ids = sorted(r["original_public_task_ids"])
        cohort_rows = [attempt_by_task[t] for t in task_ids]
        calls = sum(int(a["model_calls_attempted"]) for a in cohort_rows)
        author_scores = sum(a["status"] in {"ORIGINAL_AUTHOR_SCORED", "REUSED_EXISTING_REAL_ONE_SHOT"} for a in cohort_rows)
        directly = r["v065_updated_exposure_classification"] == DEVELOPER_EXPOSED
        require(r["v065_updated_exposure_classification"] in
                {DEVELOPER_EXPOSED, "NOT_CERTIFIED_UNSEEN_CATALOG_METADATA_PRESENT"},
                "unexpected v0.65 exposure classification")
        require(not r["unseen_source_confirmed_by_independent_fresh_auditor"],
                "source unexpectedly certified unseen")
        require(r["source_external_provider_trial"] == "BLOCKED",
                "per-original-IFC transfer rights unexpectedly changed")
        entries.append({
            "original_source_ifc_SHA256": source_sha,
            "original_public_task_ids": task_ids,
            "schema": r["original_schema"],
            "task_rows_sharing_family": len(task_ids),
            "v043_automated_native_IFC_product_and_representation_read": True,
            "v046_automated_native_paged_STEP_geometry_read": source_sha in catalog_shas,
            "v065_explicit_task_specific_developer_control_evidence": directly,
            "v065_no_explicit_task_specific_control_evidence": not directly,
            "historical_20261112_XML_only_provider_calls": calls,
            "historical_20261112_XML_only_author_scored_tasks": author_scores,
            "historical_model_facing_XML_was_not_full_native_IFC": True,
            "human_task_specific_inspection_status": (
                "DOCUMENTED_BY_V065" if directly
                else "POSSIBLE_NOT_CLEARED_BY_INDEPENDENT_AUDITOR"
            ),
            "independently_certified_untouched": False,
            "confirmatory_source_admission": "BLOCKED",
            "external_original_IFC_transfer_rights": "UNVERIFIED_BLOCKED",
        })
    counts = Counter()
    for e in entries:
        counts["developer_task_specific_documented"] += e[
            "v065_explicit_task_specific_developer_control_evidence"]
        counts["developer_task_specific_not_audited"] += e[
            "v065_no_explicit_task_specific_control_evidence"]
        counts["v043_automated_native_read"] += e[
            "v043_automated_native_IFC_product_and_representation_read"]
        counts["v046_paged_native_read"] += e[
            "v046_automated_native_paged_STEP_geometry_read"]
        counts["source_families_in_earlier_XML_only_LLM_trial"] += (
            e["historical_20261112_XML_only_provider_calls"] > 0)
        counts["source_families_with_earlier_author_score"] += (
            e["historical_20261112_XML_only_author_scored_tasks"] > 0)

    require(counts["developer_task_specific_documented"] == 10,
            "developer exposure count differs from frozen v0.65")
    require(counts["developer_task_specific_not_audited"] == 21,
            "unconfirmed developer-source population differs from frozen v0.65")
    require(sum(e["historical_20261112_XML_only_provider_calls"] for e in entries) == 36,
            "per-source prior LLM cohort call counts do not add up")
    require(sum(e["historical_20261112_XML_only_author_scored_tasks"] for e in entries) == 15,
            "per-source author-scored attempts do not add up")
    require(sorted(e["task_rows_sharing_family"] for e in entries)[-1] == 15,
            "original basic source family expected to share 15 tasks")

    return {
        "status": "V066_OFFLINE_HISTORICAL_EXPOSURE_RECONCILED_NOT_BLIND_CERTIFIED",
        "issue": 247,
        "method": "Read only four SHA-frozen existing research JSON reports; no new source IFC, hidden answer, original grader, network, or model execution",
        "parent_v065_head": "03c21572dfb09929eaf69c87e9e1bf2841833ac8",
        "input_report_SHA256": {key: expected for key, (_, expected) in INPUTS.items()},
        "original_edit_task_population": 45,
        "original_source_SHA_families": 31,
        "documented_task_specific_developer_exposed_families": counts["developer_task_specific_documented"],
        "not_independently_audited_for_task_specific_human_inspection": counts["developer_task_specific_not_audited"],
        "previously_automatically_native_IFC_examined_families_v043": counts["v043_automated_native_read"],
        "previously_paged_native_IFC_examined_families_v046": counts["v046_paged_native_read"],
        "historical_XML_only_model_calls_20261112": prior_calls,
        "historical_XML_only_provider_exposed_source_families": counts["source_families_in_earlier_XML_only_LLM_trial"],
        "historical_XML_only_original_author_scored_tasks": 15,
        "historical_XML_only_scored_source_families": counts["source_families_with_earlier_author_score"],
        "historical_XML_only_author_full_score_tasks": 3,
        "historical_XML_only_independent_strict_success_rate": None,
        "historical_XML_only_Python_matched_control_trials": 0,
        "new_provider_calls_during_this_v066_audit": 0,
        "new_original_IFC_files_opened_during_this_v066_audit": 0,
        "new_original_author_grader_files_opened_during_this_v066_audit": 0,
        "original_per_source_IFC_rights_verified_count": 0,
        "independently_certified_blind_families": 0,
        "all_confirmatory_original_source_admissions": "BLOCKED",
        "interpretation_limits": [
            "Programmatic IFC metadata/geometry census is proven, but does not by itself establish that human developers opened task-specific grader answers",
            "The 21 not-explicitly-controlled families cannot be certified unseen from repository reports; an independent auditor and source-history review remain required",
            "The earlier 36 GPT-6 Luna XML-only calls were not matched against Python and their reported 3/45 author full marks are not independently verified strict success",
            "Earlier source preprocessing and model-facing XML exposure must be disclosed even if a future independent source-holdout uses other criteria",
            "No rights to transmit original IFC content to a commercial model provider were established",
        ],
        "families": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    args = parser.parse_args()
    raw = canonical(build_report(load_pinned_reports()))
    if args.write:
        with OUTPUT.open("xb") as handle:
            handle.write(raw)
    else:
        require(OUTPUT.read_bytes() == raw,
                "frozen v0.66 evidence differs from independently recomputed metadata")
    summary = json.loads(raw)
    print(f"V066_HISTORICAL_EXPOSURE_{'WRITE' if args.write else 'CHECK'}=PASS "
          f"families={len(summary['families'])} "
          f"native_preprocessed={summary['previously_automatically_native_IFC_examined_families_v043']} "
          f"earlier_xml_calls={summary['historical_XML_only_model_calls_20261112']} "
          f"certified_blind={summary['independently_certified_blind_families']}")


if __name__ == "__main__":
    main()
