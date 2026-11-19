"""G1 #16 public spatial-Wall strict native IFC checks (offline/source-only).

All IFC files live only in an ephemeral trusted test. The independently
authored native checker is never exposed to an editing agent or official
benchmark scorer; it deliberately cannot certify a new Room split.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tests.oracles.python.public_wall_space_semantics import (
    audit_public_wall_space_semantics,
)
from tools.verify_prompt_grounded_spatial_wall import verify_prompt_grounded_spatial_wall


def _verify_both(original:Path, d0:Path, i0:Path, instruction:str)->dict:
    d=audit_public_wall_space_semantics(original,d0,instruction)
    i=audit_public_wall_space_semantics(original,i0,instruction)
    shared=(
        "status","frozen_source_sha256","public_instruction_sha256",
        "native_source_products_preserved","new_native_wall_count",
        "new_native_path_joins","new_wall_storey_containment_correct",
        "source_room_and_wall_full_cross_section",
        "source_room_wall_overlap_volume_m3",
        "source_room_ifc_space_geometry_unchanged",
        "source_ifc_space_count_before_and_after",
        "source_ifc_space_boundary_count_before_and_after",
        "new_ifc_space_created",
        "new_room_identity_type_name_or_pset_entailed_by_public_instruction",
        "geometry_implies_new_ifc_space_semantics",
        "complete_official_task_oracle_proven",
    )
    if any(d[key]!=i[key] for key in shared):
        raise ValueError("D0 and I0 native independent Wall/Space checks differ")
    if d["complete_official_task_oracle_proven"] or i["complete_official_task_oracle_proven"]:
        raise ValueError("Public-only wall oracle incorrectly claims official completion")
    return {
        "status":"PASS_BOTH_NATIVE_WALL_JOINS_ROOM_PARTITION_NOT_PROVEN",
        "source_ifc_sha256":d["frozen_source_sha256"],
        "public_instruction_sha256":d["public_instruction_sha256"],
        "d0_ifc_sha256":d["produced_ifc_sha256"],
        "i0_ifc_sha256":i["produced_ifc_sha256"],
        "native_source_products_preserved_per_arm":d["native_source_products_preserved"],
        "native_created_walls_per_arm":d["new_native_wall_count"],
        "new_native_t_path_joins_per_arm":d["new_native_path_joins"],
        "correct_containment_per_arm":d["new_wall_storey_containment_correct"],
        "source_only_wall_full_room_cross_section_per_arm":True,
        "wall_overlap_with_unchanged_room_m3":d["source_room_wall_overlap_volume_m3"],
        "ifc_spaces_before_and_after_per_arm":d["source_ifc_space_count_before_and_after"],
        "ifc_space_boundaries_before_and_after_per_arm":d[
            "source_ifc_space_boundary_count_before_and_after"],
        "new_ifc_space_created_in_either_arm":False,
        "room_partition_and_new_room_semantics_proven":False,
        "developer_selected_full_oracle_not_provided_to_models":True,
        "official_ifc_reference_or_scorer_loaded":False,
        "official_tasks_scored":0,
        "llm_calls":0,
        "G1_G2_G3_unblocked":False,
    }


def verify_public_wall_spatial_postconditions()->dict:
    source_only=verify_prompt_grounded_spatial_wall(physical_observer=_verify_both)
    check=source_only["trusted_source_only_native_spatial_evidence"]
    if not source_only["native_d0_i0_ifc_six_category_parity"]:
        raise ValueError("Existing D0/I0 native parity no longer holds")
    if (check["d0_ifc_sha256"]!=source_only["d0_ifc_sha256"]
            or check["i0_ifc_sha256"]!=source_only["i0_ifc_sha256"]):
        raise ValueError("Native observer IFC hashes diverged")
    return {
        "version":"G1_PUBLIC_WALL_SPATIAL_SEMANTICS_SOURCE_ONLY_V0.1",
        "frozen_task_id":source_only["frozen_task_id"],
        **check,
        "official_bim_edit_evaluator_executed":False,
        "research_release_gate":"BLOCKED_FULL_ROOM_ORACLE_AND_OFFICIAL_SCORER",
    }


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    result=verify_public_wall_spatial_postconditions()
    if args.output_json:
        dest=args.output_json
        if dest.is_symlink() or dest.exists() or not dest.parent.is_dir():
            parser.error("Output path exists/linked or parent missing")
        with dest.open("x",encoding="utf8",newline="\n") as f:
            json.dump(result,f,sort_keys=True,indent=2)
            f.write("\n")
    print(json.dumps({
        "status":result["status"],
        "frozen_task_id":result["frozen_task_id"],
        "new_native_t_path_joins_per_arm":result["new_native_t_path_joins_per_arm"],
        "ifc_spaces_before_and_after_per_arm":result["ifc_spaces_before_and_after_per_arm"],
        "room_partition_and_new_room_semantics_proven":False,
        "official_tasks_scored":0,
        "llm_calls":0,
        "research_release_gate":result["research_release_gate"],
    },sort_keys=True))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
