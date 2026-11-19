"""Evidence-only, source-pinned T-junction D0/I0 manual test. No scorer/GT/LLM.

Public frozen task metadata is accessed only by this trusted audit process,
never passed to a model. Both edited IFCs exist exclusively in TemporaryDirectory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import uuid

import ifcopenshell
import numpy as np

from src.runtime.compiler import compile_declarative_xml
from src.runtime.topology_ops import native_topology_inventory
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference
from tests.oracles.python.independent_ifc_checker import parity_report
from tests.test_native_t_path_junction import (
    CASE, _new_guid, _path_summary,
    authored_markup,
)
from tools.verify_spatial_wall_manual_oracle import _world_bounds

def verify_real_t_junction_pair()->dict:
    source,refs,geom,markup=authored_markup()
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    old=ifcopenshell.open(str(source))
    old_rels=native_topology_inventory(old)
    wall_guid=_new_guid(before)
    with TemporaryDirectory(prefix="g1-native-t-path-source-only-") as directory:
        folder=Path(directory)
        direct=folder/"D0.ifc"
        baseline=folder/"I0_base.ifc"
        imperative=folder/"I0.ifc"
        compiled=compile_declarative_xml(source,markup,direct)
        operations=[action.operation for action in compiled.operations]
        if operations!=["CREATE_WALL","ADD_WALL_PATH_CONNECTION","ADD_WALL_PATH_CONNECTION"]:
            raise ValueError("Unexpected native operation plan")
        d=ifcopenshell.open(str(direct))
        d_edges=_path_summary(d,wall_guid)
        if len(d_edges)!=2 or not all(row[2]=="ATPATH" for row in d_edges):
            raise ValueError("Expected two T native path relationships")
        rel_after=native_topology_inventory(d)
        for rel_id,origin in old_rels.items():
            current=rel_after.get(rel_id)
            if current is None:
                raise ValueError("Original IFC relation deleted")
            if origin[0]=="IfcRelContainedInSpatialStructure":
                if origin[1]!=current[1] or not set(origin[2]).issubset(current[2]):
                    raise ValueError("Existing IFC containment was corrupted")
            elif origin!=current:
                raise ValueError("Existing IFC relationship mutated")
        new_rels=set(rel_after)-set(old_rels)
        if (len(new_rels)!=2 or
                any(rel_after[k][0]!="IfcRelConnectsPathElements" for k in new_rels)):
            raise ValueError("Unexpected native relationship addition")
        manual_ifc_reference(
            source,baseline,"CREATE_WALL",new_guid=wall_guid,
            storey_guid=geom["storey_guid"],
            start=tuple(float(x) for x in geom["start"]),
            end=tuple(float(x) for x in geom["end"]),
            height=float(geom["height"]),thickness=float(geom["thickness"]))
        b=ifcopenshell.open(str(baseline))
        created=b.by_guid(wall_guid)
        for host_id,end_type in zip(refs[:2],("ATSTART","ATEND")):
            rel_name=f"connect-v0.1:{before}:{host_id}:{wall_guid}"
            relation_guid=ifcopenshell.guid.compress(uuid.uuid5(
                uuid.UUID("38502454-46ea-44b8-8e87-6c6a7e66c111"),
                rel_name).hex)
            b.create_entity(
                "IfcRelConnectsPathElements",
                GlobalId=relation_guid,
                RelatingElement=b.by_guid(host_id),RelatedElement=created,
                RelatingConnectionType="ATPATH",
                RelatedConnectionType=end_type,
                RelatingPriorities=(),RelatedPriorities=())
        b.write(str(imperative))
        if _path_summary(b,wall_guid)!=d_edges:
            raise ValueError("Independent Python T relationships differ")
        independent=parity_report(direct,imperative)
        if not independent["parity"]:
            raise ValueError("Native-only D0/I0 output observation mismatch")
        native_boundaries=sum(x.is_a("IfcRelSpaceBoundary")
                              for x in d.get_inverse(d.by_guid(wall_guid)))
        if native_boundaries!=0:
            raise ValueError("Unverified native SpaceBoundary was generated")
        native_room=old.by_guid(refs[2])
        room_min,room_max=_world_bounds(native_room)
        branch_min,branch_max=_world_bounds(d.by_guid(wall_guid))
        intersection=np.maximum(np.minimum(room_max,branch_max)-
                                np.maximum(room_min,branch_min),0.)
        interior_wall_overlap=float(np.prod(intersection))
        if interior_wall_overlap<1 or not np.allclose(branch_min[[0,2]],room_min[[0,2]],atol=1e-6):
            raise ValueError("Space/Wall interior conflict differs from source-only audit")
        output_hashes=[hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (direct,imperative)]
    if hashlib.sha256(source.read_bytes()).hexdigest()!=before:
        raise ValueError("Frozen original public IFC was modified")
    return {
        "status":"BLOCKED_NATIVE_SPACE_BOUNDARY_AND_OFFICIAL_EVALUATOR",
        "frozen_task_id":CASE,
        "original_input_sha256":before,
        "declarative_output_sha256":output_hashes[0],
        "imperative_output_sha256":output_hashes[1],
        "model_generated_edits":False,
        "manually_resolved_source_only_oracle":True,
        "new_native_path_joins":2,
        "native_connection_types":["ATPATH-ATSTART","ATPATH-ATEND"],
        "original_native_relations_preserved_except_storey_membership":True,
        "independent_D0_I0_ifc_parity":True,
        "native_join_body_boolean_geometry_verified":False,
        "new_wall_native_space_boundaries":native_boundaries,
        "unsplit_source_space_intersects_new_wall":True,
        "native_room_wall_volume_overlap_m3":round(interior_wall_overlap,6),
        "space_subdivision_required_by_official_target":None,
        "space_subdivision_or_reconciliation_verified":False,
        "full_task_oracle_approved":False,
        "all_input_information_equivalence_proven":False,
        "ground_truth_loaded":False,
        "official_score_count":0,
        "paid_model_calls":0,
        "result_ifc_committed":False,
    }

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    report=verify_real_t_junction_pair()
    if args.output_json:
        destination=args.output_json
        if destination.exists() or destination.is_symlink() or not destination.parent.is_dir():
            parser.error("Refusing evidence overwrite/symlink or missing parent")
        with destination.open("x",encoding="utf-8",newline="\n") as file:
            file.write(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True,indent=2))
    return 2

if __name__=="__main__":
    raise SystemExit(main())
