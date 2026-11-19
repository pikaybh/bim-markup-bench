"""G1 #15: inspect native IfcRelSpaceBoundary 2D Wall loops after deletion.

One *source-only* deterministic public task. Closed XY wall footprints
are NOT a watertight 3D IFC room boundary or a scored BIM-Edit task.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import ifcopenshell

from src.runtime.space_boundary_footprint import (
    verify_door_delete_boundary_footprints,
)
from tests.oracles.python.public_door_delete_postconditions import published_guids
from tools.verify_public_door_delete_gate import (
    CASE, verify_public_door_delete_gate,
)


def _observe(source:Path, output:Path, instruction:str) -> dict:
    guids=published_guids(instruction)
    before=ifcopenshell.open(str(source))
    after=ifcopenshell.open(str(output))
    original_door=before.by_guid(guids["door"])
    boundaries=list(original_door.ProvidesBoundaries)
    if len(boundaries)!=1:
        raise ValueError("Published Door native boundary not uniquely determined")
    return verify_door_delete_boundary_footprints(
        before,after,boundaries[0].GlobalId)


def verify_frozen_door_boundary_footprint() -> dict:
    evidence=verify_public_door_delete_gate(spatial_observer=_observe)
    d0=evidence["trusted_D0_planar_boundary_evidence"]
    i0=evidence["trusted_I0_planar_boundary_evidence"]
    if d0!=i0:
        raise ValueError("D0/I0 native SpaceBoundary planar postconditions differ")
    if (evidence["official_tasks_scored"]!=0 or evidence["LLM_calls"]!=0
            or evidence["full_task_oracle_proven"]
            or evidence["G1_G2_G3_release_allowed"]
            or d0["full_3d_space_boundary_shell_closure_proven"]):
        raise ValueError("Source-only wall ring improperly promoted to a full task result")
    return {
        "version":"G1_PUBLIC_DOOR_DELETE_2D_BOUNDARY_FOOTPRINT_V0.3",
        "status":"PASS_PLANAR_WALL_BOUNDARY_RINGS_FULL_3D_SHELL_UNVERIFIED",
        "frozen_task_id":CASE,
        "input_ifc_sha256":evidence["input_ifc_sha256"],
        "public_instruction_sha256":evidence["public_instruction_sha256"],
        "d0_native_ifc_sha256":evidence["D0_deletion_result_sha256"],
        "i0_native_ifc_sha256":evidence["i0_ifc_sha256"],
        "native_IfcRoot_removed_per_arm":evidence["native_IfcRoot_deleted"],
        "native_unrelated_world_meshes_preserved_per_arm":
            evidence["native_unrelated_world_meshes_preserved"],
        "d0_i0_planar_footprint_observations_match":True,
        "d0_i0_wall_perimeter_count_closed":d0["wall_perimeter_count_closed"],
        "per_room_surface_observations":d0["spaces"],
        "removed_door_boundary_overlaid_existing_wall_ring":
            d0["removed_door_boundary_overlaid_wall_ring"],
        "unmentioned_door_space_boundary_removed_per_arm":1,
        "floor_ceiling_spatial_boundary_surfaces_verified":False,
        "full_3d_space_boundary_shell_closure_proven":False,
        "official_bim_edit_reference_or_scorer_checked":False,
        "original_opening_storey_membership_existed":False,
        "post_hoc_engineering_capability_not_preregistered":True,
        "official_tasks_scored":0,
        "LLM_calls":0,
        "G1_G2_G3_release_allowed":False,
    }


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    out=verify_frozen_door_boundary_footprint()
    if args.output_json:
        dest=args.output_json
        if dest.is_symlink() or dest.exists() or not dest.parent.is_dir():
            parser.error("Output already exists/linked or parent missing")
        with dest.open("x",encoding="utf8",newline="\n") as fh:
            json.dump(out,fh,indent=2,sort_keys=True)
            fh.write("\n")
    print(json.dumps({
        "status":out["status"],
        "wall_perimeters_closed":out["d0_i0_wall_perimeter_count_closed"],
        "full_3d_shell_proven":False,
        "official_tasks_scored":0,
        "LLM_calls":0,
    },sort_keys=True))
    return 2  # Releasing official G1/G2/G3 is still blocked.


if __name__=="__main__":
    raise SystemExit(main())
