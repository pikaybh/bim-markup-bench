"""Sanitized, SOURCE-ONLY G1 manual native IfcSpace partition sandbox report.

This is a temporary IFC prototype, NOT available through the declarative
XML compiler, NOT a matched D0/I0 space-split oracle, NOT an official
benchmark run.  Reads public input; never reads GT, scorer or model keys.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.validate
import numpy as np

from src.runtime.space_partition_preflight import (
    plan_rectangular_space_partition,_exact_box,_surface_polygon,
)
from src.runtime.space_partition_sandbox import sandbox_native_space_split
from tests.test_space_partition_preflight import own_input_and_provisional_wall


def verify_space_rebuild_sandbox()->dict:
    with TemporaryDirectory(prefix="g1-space-split-audit-") as tmp:
        src,old_guid,new_wall_guid,joined,original_sha=own_input_and_provisional_wall(Path(tmp))
        a=ifcopenshell.open(str(src))
        c=ifcopenshell.open(str(joined))
        plan=plan_rectangular_space_partition(a,c,old_guid,new_wall_guid)
        before_roots={x.GlobalId for x in c.by_type("IfcRoot")}
        before_boundary={r.GlobalId for r in c.by_type("IfcRelSpaceBoundary")}
        if not plan.existing_oriented_surface_reconciliation_validated:
            raise ValueError("Space preflight incomplete")
        preview=sandbox_native_space_split(c,plan,source_sha=original_sha)
        saved=Path(tmp)/"split-result.ifc"
        c.write(str(saved))
        reloaded=ifcopenshell.open(str(saved))
        after_roots={x.GlobalId for x in reloaded.by_type("IfcRoot")}
        after_boundary={r.GlobalId for r in reloaded.by_type("IfcRelSpaceBoundary")}
        near=reloaded.by_guid(old_guid)
        far=reloaded.by_guid(preview["new_space_guid"])
        new_wall=reloaded.by_guid(new_wall_guid)
        if not new_wall or not near or not far:
            raise ValueError("Native Space split products missing after reload")
        if before_roots-after_roots:
            raise ValueError("Native IFC root object dropped during Space split")
        if before_boundary-after_boundary or len(after_boundary-before_boundary)!=6:
            raise ValueError("Original SpaceBoundary lost or unexpected new boundary count")
        if len(near.BoundedBy)!=7 or len(far.BoundedBy)!=6:
            raise ValueError("New SpaceBoundary relationship targets invalid")
        for volume,space,lo,hi in (
            (plan.near_volume_m3,near,plan.near_box_min,plan.near_box_max),
            (plan.far_volume_m3,far,plan.far_box_min,plan.far_box_max),
        ):
            low,high=_exact_box(space,kind="IfcSpace")
            if (not np.allclose(low,lo,atol=1e-6,rtol=0) or
                    not np.allclose(high,hi,atol=1e-6,rtol=0) or
                    not abs(float(np.prod(high-low))-volume)<1e-5):
                raise ValueError("Native Space solid body invalid after reload")
        for space,normal in ((near,np.array((0.,1.,0.))),
                             (far,np.array((0.,-1.,0.)))):
            edges=[rel for rel in space.BoundedBy
                   if rel.RelatedBuildingElement
                   and rel.RelatedBuildingElement.GlobalId==new_wall_guid]
            if len(edges)!=1 or str(edges[0].PhysicalOrVirtualBoundary)!="PHYSICAL":
                raise ValueError("Partition Wall lacks exactly one physical boundary per new Space")
            low,high,axis,direction=_surface_polygon(space,edges[0])
            if axis!=1 or not np.allclose(direction,normal,atol=1e-6,rtol=0):
                raise ValueError("Partition oriented boundary normal incorrect")
        source_errors={}
        for label,filename in (("source",src),("preview",saved)):
            log=ifcopenshell.validate.json_logger()
            ifcopenshell.validate.validate(str(filename),log,express_rules=False)
            source_errors[label]=Counter(
                (str(entry.get("type")),str(entry.get("attribute")),
                 str(entry.get("message")))
                for entry in log.statements if entry.get("level")=="error")
        if any(count>source_errors["source"][kind]
               for kind,count in source_errors["preview"].items()):
            raise ValueError("Native partition preview introduced new IFC schema errors")
        if hashlib.sha256(src.read_bytes()).hexdigest()!=original_sha:
            raise ValueError("Original pinned public IFC mutated")
        report={
            **plan.audit(),
            "status":"PASS_NATIVE_TEMPORARY_SPACE_PARTITION_NOT_XML_AGENT_TASK",
            "fixed_public_task_id":"WAL-CRE-SPA-A-003",
            "pinned_original_input_sha256":original_sha,
            "native_joined_input_sha256":hashlib.sha256(joined.read_bytes()).hexdigest(),
            "native_partition_preview_sha256":hashlib.sha256(saved.read_bytes()).hexdigest(),
            "saved_ifc_reopened_and_geometry_verified":True,
            "existing_ifc_root_guids_preserved":True,
            "original_space_identity_preserved":True,
            "new_native_ifc_space_count":1,
            "existing_native_space_boundary_guids_preserved":True,
            "new_native_space_boundary_count":len(after_boundary-before_boundary),
            "near_space_boundary_count":len(near.BoundedBy),
            "far_space_boundary_count":len(far.BoundedBy),
            "new_partition_wall_face_orientations_verified":True,
            "source_schema_error_count":sum(source_errors["source"].values()),
            "preview_schema_error_count":sum(source_errors["preview"].values()),
            "new_schema_error_categories":0,
            "native_ifc_writes_performed":True,
            "new_ifc_space_boundaries_committed":False,
            "native_ifc_written_only_to_disposable_temp_dir":True,
            "native_new_space_type_assignment_verified":len(far.IsTypedBy)>0,
            "native_new_space_property_sets_verified":len(far.IsDefinedBy)>0,
            "declarative_xml_compiler_space_split_supported":False,
            "independent_python_space_split_parity_verified":False,
            "official_task_succeeded":False,
            "ground_truth_loaded":False,
            "official_scores":0,
            "paid_model_calls":0,
            "fixed_36_sample_changed":False,
        }
        return report


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    report=verify_space_rebuild_sandbox()
    if args.output_json:
        dest=args.output_json
        if dest.exists() or dest.is_symlink() or not dest.parent.is_dir():
            parser.error("Output exists/symlink or parent missing")
        with dest.open("x",encoding="utf-8",newline="\n") as handle:
            handle.write(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True,indent=2))
    # Intentional blocked gate: native prototype is not a fair, agent-facing
    # task implementation and source IFC already has legacy schema errors.
    return 2

if __name__=="__main__":
    raise SystemExit(main())
