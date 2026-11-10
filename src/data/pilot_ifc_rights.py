"""G0 #3: offline, hash-pinned IFC source/reference provenance triage.

Reads the trusted, previously audited 30/36 fixed pilot input/reference IFC
pairs solely inside a data-provenance audit. Never exposes reference models,
task target GUIDs, source paths, or IFC HEADER authors to an authoring agent.
An IFC HEADER license string is *not* a grant of redistribution rights.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

from src.data.bim_edit import (
    read_tasks, repo_asset_path, verify_local_asset_bytes,
)
from src.data.pilot_asset_audit import _files_in_root

ROOT = Path(__file__).resolve().parents[2]
TASK_SHA = "9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83"
PILOT_SHA = "75b4847814dbefad95340556c0b62f9cda72cac319cd82ecb23ea4933c9ab694"
REMOTE_TREE_SHA = "f1b150a576f3d72045819768215c34fd84602ab4f6a5f4d2f0202a0ae3a92a39"
PRIOR_AUDIT_SHA = "4657c8a2f4937b5ecc83305ae72fcb0138455af2c40129b8a3cc11dfcb72f927"
RIGHTS_LEDGER_SHA = "43f85c4ebf17184bfaea3fa749b565337e34f4fd397ec1b9536a8f242b2add06"
HEADER_LIMIT = 65536
LICENSE_HINT = re.compile(
    rb"(?<![a-z0-9])(?:license|licence|copyright|creative[ \t_-]?commons|cc[ -]?by)(?![a-z0-9])",
    flags=re.IGNORECASE,
)


class IFCProvenanceBlocked(ValueError):
    """A source, reference or study-rule integrity check failed closed."""


def _digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise IFCProvenanceBlocked("Missing or linked pinned evidence file")
    return sha256(path.read_bytes()).hexdigest()


def summarize_ifc_header(path: Path) -> dict:
    """Bounded HEADER-only check. Never return raw originator/file metadata."""
    if path.is_symlink() or not path.is_file():
        raise IFCProvenanceBlocked("Missing/link IFC model")
    with path.open("rb") as fd:
        sample = fd.read(HEADER_LIMIT + 1)
    # An incomplete header cannot be treated as clean evidence.
    marker = sample.find(b"ENDSEC;")
    if marker < 0 or marker > HEADER_LIMIT:
        raise IFCProvenanceBlocked("IFC STEP HEADER missing or oversized")
    header = sample[:marker]
    if (not header.lstrip().upper().startswith(b"ISO-10303-21;")
            or b"HEADER;" not in header.upper()
            or b"FILE_NAME(" not in header.upper()
            or b"FILE_SCHEMA(" not in header.upper()):
        raise IFCProvenanceBlocked("Invalid IFC STEP HEADER")
    return {
        "step_header_present": True,
        "copyright_or_license_text_hint": bool(LICENSE_HINT.search(header)),
        "explicit_model_rights_verified": False,
    }


def _load_frozen(root: Path):
    locations = {
        "tasks": root / "data/tasks.jsonl",
        "pilot": root / "manifests/pilot_36_candidate_v0.json",
        "tree": root / "data/bim_edit_remote_tree.json",
        "prior": root / "reports/pilot_asset_audit_partial.json",
        "rights": root / "manifests/source_rights.json",
    }
    for key, expected in (
        ("tasks", TASK_SHA), ("pilot", PILOT_SHA),
        ("tree", REMOTE_TREE_SHA), ("prior", PRIOR_AUDIT_SHA),
        ("rights", RIGHTS_LEDGER_SHA),
    ):
        if _digest(locations[key]) != expected:
            raise IFCProvenanceBlocked("Pinned study or rights source changed: " + key)
    records = {x["task_id"]: x for x in read_tasks(locations["tasks"])}
    pilot = json.loads(locations["pilot"].read_text(encoding="utf8"))
    earlier = json.loads(locations["prior"].read_text(encoding="utf8"))
    rights = json.loads(locations["rights"].read_text(encoding="utf8"))
    tree = json.loads(locations["tree"].read_text(encoding="utf8"))
    selected = [x["task_id"] for x in pilot["tasks"]]
    prior = {x["task_id"]: x for x in earlier["tasks"]}
    external = [x for x in rights["records"] if x["source"] == "BIM-Edit/BIM-Edit"]
    if (len(selected) != 36 or len(set(selected)) != 36
            or set(selected) != set(prior) or not set(selected) <= set(records)
            or earlier.get("locally_verified_both_input_and_GT") != 30
            or earlier.get("task_status_counts") != {
                "VERIFIED_PINNED_BYTES_AND_CLASS_DELTA": 30,
                "MISSING_LOCAL_IFC_BYTES": 6,
            }
            or earlier.get("official_scores_computed") != 0
            or len(external) != 1
            or external[0].get("source_revision") !=
                "0ae510bd21865def4e2c6145c1244f01a1e3bcb9"
            or external[0].get("rights_checked") is not False
            or external[0].get("redistribution_permitted") is not False):
        raise IFCProvenanceBlocked("Unapproved pilot, asset, or per-model rights promotion")
    index = {x["path"]: x for x in tree if x.get("type") == "file"}
    if len(index) != sum(x.get("type") == "file" for x in tree):
        raise IFCProvenanceBlocked("Ambiguous pinned remote file inventory")
    return records, selected, prior, index


def audit_pilot_ifc_rights(root: Path = ROOT) -> dict:
    records, selected, prior, index = _load_frozen(root)
    cache = (root / "data/ifc").resolve()
    if not cache.is_dir() or cache.is_symlink():
        raise IFCProvenanceBlocked("IFC cache root is unavailable or linked")
    verified_files: dict[str, dict] = {}
    inaccessible: set[str] = set()
    disposition = []
    for task_id in selected:
        previous = prior[task_id]
        task = records[task_id]
        if previous["status"] == "MISSING_LOCAL_IFC_BYTES":
            # Preserve the historical missing set. Metadata-only size accounting
            # does not attempt download, reopen, or falsely promote missing IFCs.
            status = "BLOCKED_PAIRED_INPUT_REFERENCE_CONTENT_MISSING"
        elif previous["status"] == "VERIFIED_PINNED_BYTES_AND_CLASS_DELTA":
            status = "VERIFIED_PINNED_BYTES_RIGHTS_UNRESOLVED"
        else:
            raise IFCProvenanceBlocked("Unrecognized frozen historical status")
        path_pairs = (
            ("source", repo_asset_path(task["input_ifc"])),
            ("reference", repo_asset_path(task["ground_truth_ifc"])),
        )
        if status == "BLOCKED_PAIRED_INPUT_REFERENCE_CONTENT_MISSING":
            for _, asset in path_pairs:
                if asset not in index:
                    raise IFCProvenanceBlocked("Missing remote asset inventory record")
                inaccessible.add(asset)
            disposition.append({"task_id": task_id, "status": status})
            continue

        # Trusted G0-only reads. Inputs/GT are never mounted or returned to
        # a model/agent. Verification is performed once per unique IFC asset.
        for role, asset in path_pairs:
            if asset not in index:
                raise IFCProvenanceBlocked("Missing remote IFC pin")
            if asset not in verified_files:
                path = _files_in_root(cache, asset)
                try:
                    verify_local_asset_bytes(path, index[asset])
                    header = summarize_ifc_header(path)
                except Exception as exc:
                    raise IFCProvenanceBlocked(
                        "Previously verified source/reference content no longer valid"
                    ) from exc
                verified_files[asset] = {
                    **header, "size": index[asset]["size"],
                }
            if not verified_files[asset]["step_header_present"]:
                raise IFCProvenanceBlocked("IFC HEADER integrity failed")
        disposition.append({"task_id": task_id, "status": status})
    # Some missing tasks share files with verified tasks. Do not count a
    # verified shared input/reference as an additional missing byte object.
    missing_only = inaccessible - set(verified_files)
    total_bytes_missing = sum(index[asset]["size"] for asset in missing_only)
    counts = Counter(x["status"] for x in disposition)
    file_hint_counts = Counter(
        "HEADER_TEXT_HINT_ONLY" if x["copyright_or_license_text_hint"]
        else "NO_HEADER_LICENSE_HINT"
        for x in verified_files.values()
    )
    report = {
        "version": "g0-pilot-asset-provenance-rights-v0.1",
        "task_records_sha256": TASK_SHA,
        "candidate_sha256": PILOT_SHA,
        "pinned_model_revision": "0ae510bd21865def4e2c6145c1244f01a1e3bcb9",
        "basis": "pinned_original_and_reference_ifc_bytes_AND_STEP_HEADER_only",
        "tasks_total": len(disposition),
        "status_counts": dict(sorted(counts.items())),
        "unique_verified_file_count": len(verified_files),
        "unique_verified_file_bytes": sum(x["size"] for x in verified_files.values()),
        "unique_remaining_file_count": len(missing_only),
        "unique_remaining_file_bytes": total_bytes_missing,
        "verified_file_header_hints": dict(sorted(file_hint_counts.items())),
        "individual_model_license_documents_verified": 0,
        "model_redistribution_rights_cleared": False,
        "dataset_card_cc_by_tag_is_model_license_proof": False,
        "source_rights_record_is_pending": True,
        "raw_ifc_header_originator_data_recorded": False,
        "raw_source_or_reference_path_recorded": False,
        "source_reference_ifc_bytes_committed": False,
        "private_grader_targets_consumed": False,
        "model_visible_data_exported": False,
        "official_tasks_scored": 0,
        "LLM_calls": 0,
        "paid_downloads_or_api_calls": 0,
        "full_g0_release_authorized": False,
        "gate_status": "BLOCKED_PER_MODEL_RIGHTS_AND_MISSING_IFC_CONTENT",
        "tasks": disposition,
    }
    if len(disposition) != 36 or sum(counts.values()) != 36:
        raise IFCProvenanceBlocked("Incomplete fixed-candidate accounting")
    return report
