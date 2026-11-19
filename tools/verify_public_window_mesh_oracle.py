"""G1 #16: validate strict public Window task against native IFC world meshes.

No official GT, target annotation, evaluator, LLM or paid inference.
Uses existing D0/I0 compilation solely to obtain two ephemeral IFC candidates,
then a separate independently implemented IFC-only physical postcondition.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tests.oracles.python.public_window_mesh_oracle import audit_window_public_mesh
from tools.verify_prompt_grounded_window_pair import verify_prompt_grounded_window_pair

ROOT = Path(__file__).resolve().parents[1]


def _observe_both(original: Path, direct: Path, imperative: Path,
                  instruction: str) -> dict:
    d0 = audit_window_public_mesh(original, direct, instruction)
    i0 = audit_window_public_mesh(original, imperative, instruction)
    verified_keys = [
        "status", "original_ifc_sha256", "public_instruction_sha256",
        "represented_products_checked",
        "unaffected_product_world_meshes_preserved",
        "window_and_opening_exact_world_mesh_shift",
        "host_void_rim_replaced_by_translated_rim",
        "host_outer_world_bounds_volume_and_triangle_count_preserved",
        "native_roots_relations_and_other_step_rows_preserved",
    ]
    if any(d0[key] != i0[key] for key in verified_keys):
        raise ValueError("D0/I0 strict physical postcondition observations differ")
    return {
        "status": "PASS_BOTH_STRICT_PUBLIC_NATIVE_MESH_POSTCONDITIONS",
        "d0_native_ifc_sha256": d0["candidate_ifc_sha256"],
        "i0_native_ifc_sha256": i0["candidate_ifc_sha256"],
        "source_ifc_sha256": d0["original_ifc_sha256"],
        "public_instruction_sha256": d0["public_instruction_sha256"],
        "represented_products_checked_per_arm": d0["represented_products_checked"],
        "unaffected_world_meshes_preserved_per_arm":
            d0["unaffected_product_world_meshes_preserved"],
        "window_and_opening_world_mesh_translation_both_arms": True,
        "host_wall_regenerated_void_rim_both_arms": True,
        "host_wall_outer_bounds_and_volume_preserved_both_arms": True,
        "reference_GT_ifc_or_scorer_loaded": False,
        "full_official_task_oracle_proven": False,
        "LLM_calls": 0,
        "official_tasks_scored": 0,
        "G1_G2_G3_unblocked": False,
    }


def verify_source_only_window_physical_oracle() -> dict:
    proof = verify_prompt_grounded_window_pair(physical_observer=_observe_both)
    evidence = proof["source_only_physical_postcondition_evidence"]
    if proof["official_tasks_scored"] != 0 or not proof[
        "independent_native_D0_I0_observation_parity"
    ] or evidence["full_official_task_oracle_proven"]:
        raise ValueError("Trusted source-only physical observation unexpectedly promoted")
    return {
        "version": "g1-public-window-native-physical-check-v0.1",
        "frozen_task_id": proof["task_id"],
        **evidence,
        "treatment_independent_of_oracle": True,
        "native_physical_postconditions_are_not_official_evaluator": True,
        "approved_llm_runs": 0,
        "research_gate": "BLOCKED_OFFICIAL_GT_SCORER_AND_MATCHED_LLM",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    report = verify_source_only_window_physical_oracle()
    if args.output_json is not None:
        dest = args.output_json
        if dest.is_symlink() or dest.exists() or not dest.parent.is_dir():
            parser.error("Output path exists, is linked, or parent is absent")
        with dest.open("x", encoding="utf8", newline="\n") as fh:
            json.dump(report, fh, sort_keys=True, indent=2)
            fh.write("\n")
    print(json.dumps({
        "status": report["status"],
        "frozen_task_id": report["frozen_task_id"],
        "represented_products_checked_per_arm":
            report["represented_products_checked_per_arm"],
        "unaffected_world_meshes_preserved_per_arm":
            report["unaffected_world_meshes_preserved_per_arm"],
        "official_tasks_scored": 0,
        "LLM_calls": 0,
        "research_gate": report["research_gate"],
    }, sort_keys=True))
    return 2  # Always BLOCKED for official/paid benchmark claims.


if __name__ == "__main__":
    raise SystemExit(main())
