"""Offline, source-only v0.14 Window deletion reproducibility audit.

Requires original publicly provided BIBIMBAP input IFCs on disk.
Never opens ground truth, task target metadata, a model endpoint, or grader.
Writes only a small derived JSON ledger, never any source IFC to Git.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import tempfile

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from tools.audit_bibimbap_author import _head,AUTHOR_SHA,DATA_SHA
from tools.bibimbap_matched25_cli import public_45
from src.runtime.experimental_v13_opaque_source import project_original_native_v13
from src.runtime.experimental_v14_native_window_delete import (
    NS, native_full_window_state_v14, compile_native_hosted_windows_v14,
)
from tools.oracle_bibimbap_v14_window_delete import verify_source_native_window_delete

SOURCES = {
    "geometry_test_18": "01/01/01_01_018.ifc",
    "geometry_test_19": "01/01/01_01_019.ifc",
}
TAG = "{" + NS + "}"


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def state_without(xml: bytes, guids: tuple[str, ...]) -> bytes:
    root = etree.fromstring(xml)
    windows = root.find(TAG + "Windows")
    assert windows is not None
    to_drop = set(guids)
    found = set()
    for element in list(windows):
        if element.get("ifcGuid") in to_drop:
            found.add(element.get("ifcGuid"))
            windows.remove(element)
    if found != to_drop:
        raise ValueError("Original public source Window inventory changed")
    return etree.tostring(root, encoding="utf8")


def audit(base: Path) -> dict:
    author=base/"bibimbap-author-upstream"
    data=base/"bibimbap-author-data"
    if _head(author)!=AUTHOR_SHA or _head(data)!=DATA_SHA:
        raise ValueError("Pinned original author or dataset revision changed")
    public={x["test_id"]:x for x in public_45(author,data)}
    if not set(SOURCES)<=set(public) or len(public)!=45:
        raise ValueError("Original public BIBIMBAP 45 denominator drift")
    rows = []
    for case, relative in SOURCES.items():
        raw = base / "bibimbap-author-data" / "ifc" / relative
        if not raw.is_file():
            raise FileNotFoundError(f"Missing original public dataset asset: {relative}")
        prior_hash = digest(raw)
        if (public[case]["original_source_ifc_relpath"]!=relative
            or public[case]["original_ifc_sha256"]!=prior_hash):
            raise ValueError("Pinned original public BIBIMBAP source IFC SHA mismatch")
        with tempfile.TemporaryDirectory(prefix="bibimbap-v014-source-only-") as d:
            tmp = Path(d)
            normalized = tmp / "source_m.ifc"
            ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(raw)), "METER"
            ).write(str(normalized))
            normalized_hash = digest(normalized)
            original = project_original_native_v13(normalized)
            state = native_full_window_state_v14(normalized)
            nodes = etree.fromstring(state.xml).find(TAG + "Windows")
            inventory = [n.get("ifcGuid") for n in nodes]
            demoted = list(original.demoted_fill_guids)
            order = demoted + [g for g in inventory if g not in demoted]
            if not demoted or len(order) < 7:
                raise ValueError("Original hosted Window test inventory changed")
            # These are deterministic developer source-input slices, NOT a
            # benchmark ground-truth target selection or a scored LLM trial.
            slices = {
                "one_v013_opaque_window": tuple(demoted[:1]),
                "six_source_windows": tuple(sorted(order[:6])),
            }
            observations = {}
            for label, targets in slices.items():
                edited = state_without(state.xml, targets)
                candidate = tmp / (label + ".ifc")
                compiled = compile_native_hosted_windows_v14(
                    normalized, edited, candidate
                )
                independent = verify_source_native_window_delete(
                    normalized, candidate, targets,
                    expected_original_source_sha256=normalized_hash,
                    expected_output_sha256=compiled.output_sha256,
                )
                observations[label] = {
                    "declarative_xml_sha256": sha256(edited).hexdigest(),
                    "native_candidate_ifc_sha256": compiled.output_sha256,
                    "windows_removed_count": len(targets),
                    "exclusive_source_ifc_roots_removed_count":
                        len(independent["independently_expected_deleted_owned_root_guids"]),
                    "unrelated_ifc_root_count_preserved":
                        independent["non_target_original_root_count_preserved"],
                    "original_native_world_meshes_preserved":
                        independent["actual_world_native_product_meshes_preserved"],
                    "independent_ifc_oracle_status": independent["status"],
                    "host_void_and_opening_preserved":
                        independent["original_host_wall_opening_unchanged"],
                }
            if digest(raw) != prior_hash or digest(normalized) != normalized_hash:
                raise AssertionError("Source public IFC changed during v0.14 audit")
            rows.append({
                "public_case": case,
                "original_public_asset_relative_path": relative,
                "original_public_asset_sha256": prior_hash,
                "metre_normalized_source_sha256": normalized_hash,
                "original_full_window_inventory_count": len(inventory),
                "v013_readonly_demoted_windows_count": len(demoted),
                "v014_full_declarative_window_state_sha256":
                    sha256(state.xml).hexdigest(),
                "original_native_catalog_sha256":
                    state.original_native_source_catalog_sha256,
                "offline_d0_candidate_observations": observations,
            })
    return {
        "status": "V014_OFFLINE_SOURCE_ONLY_D0_AND_INDEPENDENT_IFC_ORACLE",
        "origin": "independent-source-only-experimental-no-official-score",
        "benchmarks_scored": 0,
        "LLM_trials": 0,
        "Python_I0_oracles": 0,
        "official_author_grader_runs": 0,
        "hidden_ground_truth_access": False,
        "original_BIBIMBAP_45_edit_parity_proven": False,
        "full_BIM_XML_source_claim": False,
        "hosted_window_native_delete_only": True,
        "hosted_opening_delete_supported": False,
        "model_or_paid_API_calls": 0,
        "cases": rows,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or args.output.is_symlink():
        p.error("Do not overwrite original native Window research evidence")
    result = audit(args.base.resolve(strict=True))
    payload=(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)+"\n").encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as f:
        f.write(payload)
    print(f"v0.14 source-only audit PASS: {len(result['cases'])} original IFCs,"
          f" 4 independent native candidate checks, 0 LLM trials")
    print(f"report_sha256={digest(args.output)}")


if __name__ == "__main__":
    main()
