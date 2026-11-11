"""G0 #4: public third-party scorer provenance, NOT original BIM-Edit scorer.

Read-only evidence registry. No executable 3rd-party source is downloaded or
run, no GT IFC is opened, and no independent metric is promoted to "official".

This module deliberately accepts no "official=True" override supplied by
a found repository or previously released aggregate summary. Actual
original-author code provenance and scorer calibration MUST be established
in a separately reviewed release contract.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from src.evaluation.official_release_provenance import PINNED_RUNS_SHA

ROOT = Path(__file__).resolve().parents[2]

HISTORICAL_G0_REPORT = "reports/g0_official_bim_edit_public_release_20261110.json"
HISTORICAL_G0_SHA = "f7232a0217617b54c97c8ae7f8efd965e2e7a8b051a04490ea05c1af87ad3e48"

# A separately authored and independently published reproducibility project.
# The repository is NOT author-origin evidence for the original paper's
# executable evaluator. GitHub blob SHA values are provenance descriptors,
# not SHA-256 hashes, and refer to this one pinned commit only.
THIRD_PARTY_REPO = "NTUZZH/VeriBIM"
THIRD_PARTY_COMMIT = "cd3fe8cb18e8d33f76e73906253cf896cb5d4d3b"
THIRD_PARTY_FILES = {
    "README.md": "59c8719521ca104449d8a4ba307bbc6ca7fa1836",
    "LICENSE": "d645695673349e3947e8e5ae42332d0ac3164cd7",
    "code/modifc_score/README.md": "3baba7221bbf80a3fa2d8f64dbda93910759b0b8",
    "code/modifc_score/config.py": "6bb236cbc9542cd011344121062b4bd24481ec2b",
    "code/modifc_score/scorer.py": "83b3f3176ba0b239e85193727434a602ae87a130",
    "code/modifc_score/cli.py": "68a915116a7323b8ee898dee9864e6638d410088",
}

# These are not asserted to be exhaustive source searches; they identify
# the public places actually inspected on 2026-11-11.
AUTHOR_RELATED_REPOSITORY_SEARCHES = (
    "GitHub repository search: user:nbharathik",
    "GitHub repository search: user:Tsesterh",
    "GitHub repository search: org:Show2Instruct",
    "GitHub repository search: org:bartelt-lab",
    "GitHub code search: BIM-Edit-runs, BIM-Edit-Tasks, 2606.20146",
)

PAPER = "https://arxiv.org/html/2606.20146v3"
PAPER_TOPOLOGY_FORMULA = "0.3 * node_f1 + 0.7 * edge_f1"
PAPER_DELETE_SEMANTICS = "1.0 if the intended target object is removed, else 0.0"
EXTERNAL_CONFIG_TOPOLOGY_DEFAULT = "mean_rules"
EXTERNAL_CONFIG_TOPOLOGY_ALTERNATIVE = "paper"
EXTERNAL_CONFIG_DELETE_DEFAULT = "matcher"
EXTERNAL_CONFIG_DELETE_ALTERNATIVE = "removal"

EXTERNAL_LICENSE = "Apache-2.0"
ORIGINAL_PAPER_LICENSE_CLAIM = "MIT"
RELEASE_GATE = "BLOCKED_OFFICIAL_AUTHOR_CODE_ENTRYPOINT_AND_SCORE_PARITY_UNVERIFIED"


class ScorerSourceOriginBlocked(ValueError):
    """Repository, author, license or official-source provenance is unsafe."""


def _read_archived_g0(root: Path) -> dict[str, Any]:
    file = root / HISTORICAL_G0_REPORT
    if file.is_symlink() or not file.is_file():
        raise ScorerSourceOriginBlocked("Original pinned G0 report absent or linked")
    raw = file.read_bytes()
    if sha256(raw).hexdigest() != HISTORICAL_G0_SHA:
        raise ScorerSourceOriginBlocked("Historical G0 scorer audit was changed")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ScorerSourceOriginBlocked("Historical G0 scorer report invalid") from exc
    if (data.get("status") !=
        "BLOCKED_OFFICIAL_EXECUTABLE_EVALUATOR_NOT_VERIFIED"
        or data.get("source_inventory", {}).get("pinned_revision") != PINNED_RUNS_SHA
        or data.get("official_executable_scorer_available_to_this_project") is not False
        or data.get("official_tasks_scored_by_this_project") != 0
        or data.get("source_inventory",{}).get("public_file_count") != 1417
        or data.get("source_inventory",{}).get("author_report_model_count") != 7):
        raise ScorerSourceOriginBlocked("Original G0 provenance assertions invalid")
    return data


def _pinned_third_party_evidence() -> dict[str, Any]:
    if (not re.fullmatch(r"[0-9a-f]{40}", THIRD_PARTY_COMMIT)
            or any(not re.fullmatch(r"[0-9a-f]{40}",sha)
                   for sha in THIRD_PARTY_FILES.values())):
        raise ScorerSourceOriginBlocked("Invalid immutable GitHub commit/blob provenance")
    if THIRD_PARTY_REPO == "BIM-Edit/BIM-Edit" or not THIRD_PARTY_REPO.startswith("NTUZZH/"):
        raise ScorerSourceOriginBlocked("External evaluator publisher identity spoofed")
    return {
        "source_classification": "third-party-independent-reimplementation",
        "repository_full_name": THIRD_PARTY_REPO,
        "pinned_git_commit": THIRD_PARTY_COMMIT,
        "repository": "https://github.com/" + THIRD_PARTY_REPO,
        "inspected_bounded_source_files": {
            path: {
                "url": ("https://github.com/"+THIRD_PARTY_REPO+"/blob/"
                        +THIRD_PARTY_COMMIT+"/"+path),
                "git_blob_sha1":sha,
            }
            for path, sha in sorted(THIRD_PARTY_FILES.items())
        },
        "license_observed_in_its_own_repository": EXTERNAL_LICENSE,
        "license_is_not_original_bim_edit_license": True,
        "cli_documented": "python -m modifc_score.cli",
        "this_is_original_bim_edit_executable_evaluator": False,
        "executed_on_original_bim_edit_gt_or_any_ifc": False,
        "source_authors_distinct_from_original_bim_edit_authors": True,
        "paper_v3_topology": PAPER_TOPOLOGY_FORMULA,
        "third_party_documented_topology_default": EXTERNAL_CONFIG_TOPOLOGY_DEFAULT,
        "third_party_documented_topology_alternative": EXTERNAL_CONFIG_TOPOLOGY_ALTERNATIVE,
        "paper_v3_delete_semantics": PAPER_DELETE_SEMANTICS,
        "third_party_documented_delete_default": EXTERNAL_CONFIG_DELETE_DEFAULT,
        "third_party_documented_delete_alternative": EXTERNAL_CONFIG_DELETE_ALTERNATIVE,
        "third_party_claims_to_reproduce_author_runs_independently": True,
        "third_party_claim_checked_against_author_IFCs": False,
        "strict_official_binary_parity_verified": False,
        "claim_origin": (
            "third-party public README and config at pinned commit, "
            "not certified author evaluator behavior"
        ),
    }


def audit_scorer_origin(root: Path = ROOT,
                        *, third_party_attestation: dict | None = None) -> dict:
    """Return bounded public provenance evidence, with release gate FALSE."""
    previous = _read_archived_g0(root)
    registry = _pinned_third_party_evidence()
    if third_party_attestation is not None:
        # Untrusted external metadata can supply corroborating information
        # but must NEVER set official evaluator provenance.
        if not isinstance(third_party_attestation, dict):
            raise ScorerSourceOriginBlocked("Unsupported external attestation")
        for key in ("repository_full_name","pinned_git_commit",
                    "license_observed_in_its_own_repository",
                    "source_classification","cli_documented"):
            if (third_party_attestation.get(key) is not None and
                    third_party_attestation[key] != registry[key]):
                raise ScorerSourceOriginBlocked("Third-party origin attestation mismatch")
        if (third_party_attestation.get("official_evaluator") is True
                or third_party_attestation.get("authors_verified") is True
                or third_party_attestation.get("scored_tasks",0) != 0):
            raise ScorerSourceOriginBlocked("Fabricated official evaluator attestation")

    return {
        "version": "G0_BIM_EDIT_PUBLIC_ORIGINAL_SCORER_SOURCE_REAUDIT_20261111",
        "status": RELEASE_GATE,
        "research_project": "independent-bim-markup-bench",
        "paper": PAPER,
        "paper_claimed_author_code_license": ORIGINAL_PAPER_LICENSE_CLAIM,
        "paper_describes_code_folder_but_executable_repository_url_unverified": True,
        "paper_claim_is_not_license_proof_for_unlocated_code": True,
        "original_author_public_repo_search_scopes": AUTHOR_RELATED_REPOSITORY_SEARCHES,
        "original_author_public_repo_search_was_exhaustive": False,
        "author_published_hf_runs_revision": PINNED_RUNS_SHA,
        "author_published_run_model_count": previous["source_inventory"]["author_report_model_count"],
        "author_published_run_file_count": previous["source_inventory"]["public_file_count"],
        "author_run_reports_available": previous["public_reports_confirmed"],
        "source_run_inventory_sha256": HISTORICAL_G0_SHA,
        "author_original_evaluator_source_uri_verified": False,
        "author_original_evaluator_source_commit_verified": False,
        "author_original_evaluator_mit_license_file_verified": False,
        "author_original_evaluator_lockfile_verified": False,
        "author_original_evaluator_cli_entrypoint_verified": False,
        "author_original_evaluator_callable_on_arbitrary_prediction": False,
        "author_original_evaluator_scored_output_reproduced": False,
        "original_evaluator_scoring_of_unmentioned_space_boundaries_known": False,
        "third_party_reimplementation": registry,
        "published_official_metric_vs_third_party_alternatives_not_equivalent_by_provenance": True,
        "third_party_files_fetched_or_imported_by_this_audit": False,
        "original_or_gt_ifc_opened": False,
        "paid_model_calls": 0,
        "official_tasks_scored": 0,
        "independent_scorer_metrics_reclassified_as_official": False,
        "G0_G1_G2_G3_release_allowed": False,
        "next_gate": (
            "Obtain author-controlled repository URL/commit, license file, "
            "dependency lock and CLI; validate offline with author-published "
            "raw IFC predictions and reference files under isolated grader "
            "once source/GT rights are resolved"
        ),
    }
