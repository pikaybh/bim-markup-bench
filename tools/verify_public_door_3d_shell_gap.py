"""G1 #15: reconcile original/edited 3D IfcSpace product shape and 1st-level boundary surfaces.

The published native source already lacks horizontal IfcRelSpaceBoundary
surfaces, despite its closed IfcSpace product solids. This report must NOT
claim a complete 3D boundary shell or official BIM-Edit success.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import ifcopenshell

from tests.oracles.python.public_space_shell_gap import (
    verify_source_inherited_space_boundary_gap,
)
from tests.oracles.python.public_door_delete_postconditions import published_guids
from tools.verify_public_door_delete_gate import (
    CASE, verify_public_door_delete_gate,
)


def _observe(original: Path, candidate: Path, instruction: str) -> dict:
    ids = published_guids(instruction)
    base = ifcopenshell.open(str(original))
    door = base.by_guid(ids["door"])
    if door is None or not door.is_a("IfcDoor") or len(door.ProvidesBoundaries)!=1:
        raise ValueError("The public Door space-boundary is not unique")
    return verify_source_inherited_space_boundary_gap(
        original,candidate,door.ProvidesBoundaries[0].GlobalId)


def run_source_inherited_3d_shell_gap_audit() -> dict:
    legacy = verify_public_door_delete_gate(spatial_observer=_observe)
    a = legacy["trusted_D0_planar_boundary_evidence"]
    b = legacy["trusted_I0_planar_boundary_evidence"]
    comparable = [
        "status","source_sha256","space_count",
        "planar_wall_perimeter_count_closed","per_room",
        "native_IfcSpace_product_meshes_closed_and_preserved",
        "native_IfcRelSpaceBoundary_floor_ceiling_surfaces_absent_in_source",
        "native_IfcRelSpaceBoundary_floor_ceiling_surfaces_absent_in_output",
        "baseline_relative_unmodified_3d_relation_gap",
        "full_3d_spatial_boundary_shell_proven",
        "author_provided_evaluator_scoring_requirement_verified",
        "official_tasks_scored","LLM_calls",
    ]
    if any(a[k]!=b[k] for k in comparable):
        raise ValueError("D0/I0 source-baseline 3D shape-vs-relation gap differs")
    if (a["candidate_sha256"] != legacy["D0_deletion_result_sha256"]
            or b["candidate_sha256"] != legacy["i0_ifc_sha256"]
            or not legacy["D0_I0_both_native_success_proven"]
            or not legacy["D0_I0_common_dependency_counts_match"]
            or legacy["official_tasks_scored"] != 0
            or legacy["LLM_calls"] != 0
            or legacy["G1_G2_G3_release_allowed"]
            or a["full_3d_spatial_boundary_shell_proven"]):
        raise ValueError("3D baseline audit inadvertently claims scored success")
    return {
        "version":"G1_PUBLIC_DOOR_NATIVE_SOURCE_3D_SHELL_GAP_V0.4",
        "status":"SOURCE_PRESERVED_SHAPE_BUT_3D_FIRSTLEVEL_RELATION_SHELL_INCOMPLETE",
        "frozen_task_id":CASE,
        "source_ifc_sha256":legacy["input_ifc_sha256"],
        "public_instruction_sha256":legacy["public_instruction_sha256"],
        "d0_candidate_ifc_sha256":a["candidate_sha256"],
        "i0_candidate_ifc_sha256":b["candidate_sha256"],
        "native_IFC4X3_firstlevel_relative_to_baseline_only":True,
        "source_IfcSpace_and_output_native_shape_watertight":True,
        "source_and_output_horizontal_space_boundary_rels_missing":True,
        "d0_i0_per_room_3d_shape_relations_gap_match":True,
        "planar_closed_wall_rings_per_arm":a["planar_wall_perimeter_count_closed"],
        "per_room_source_and_both_outputs":a["per_room"],
        "benchmark_author_explicit_floor_ceiling_repair_requirement_found":False,
        "official_evaluator_code_available_and_executed":False,
        "normative_closed_shell_condition_satisfied_by_relationships":False,
        "space_boundaries_newly_generated":0,
        "strict_baseline_relative_check_only":True,
        "no_retroactive_frozen_support_reclassification":True,
        "official_tasks_scored":0,
        "LLM_calls":0,
        "G1_G2_G3_release_allowed":False,
    }


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    outcome=run_source_inherited_3d_shell_gap_audit()
    if args.output_json is not None:
        target=args.output_json
        if target.exists() or target.is_symlink() or not target.parent.is_dir():
            parser.error("Output exists, linked, or directory is missing")
        with target.open("x",encoding="utf8",newline="\n") as fh:
            json.dump(outcome,fh,sort_keys=True,indent=2)
            fh.write("\n")
    print(json.dumps({
        "status":outcome["status"],
        "planar_closed_wall_rings_per_arm":outcome["planar_closed_wall_rings_per_arm"],
        "3d_relations_shell_incomplete":True,
        "official_tasks_scored":0,
        "LLM_calls":0,
    },sort_keys=True))
    return 2  # Scientific G1/G2/G3 release remains blocked.


if __name__=="__main__":
    raise SystemExit(main())
