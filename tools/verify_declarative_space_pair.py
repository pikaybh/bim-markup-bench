"""Trusted manual D0/I0 declarative Space partition oracle; not a scored LLM trial.

The two implementations independently author native IFC, using identical
SHA-pinned public input and source-only manually derived task geometry. No GT,
official scorer, model API, or normative BIXML/Xim sources are touched.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import uuid

import ifcopenshell
import ifcopenshell.validate

from src.runtime.compiler import compile_declarative_xml
from src.runtime.binder import allocate_new_ifc_guid
from src.runtime.space_metadata_gate import verify_native_space_metadata
from tests.test_declarative_space_partition_compiler import (
    make_space_split_state,NEW_FAR_ID,
)
from tests.test_native_t_path_junction import authored_markup
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference
from tests.oracles.python.independent_ifc_checker import parity_report
from tests.oracles.python.independent_space_partition import (
    author_independent_space_partition,
)


def verified_paired_space_partition()->dict:
    source,edited=make_space_split_state()
    _,refs,geometry,_=authored_markup()
    source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
    new_wall=allocate_new_ifc_guid(source_sha,"Wall",
                                   "g1_t_path_join_manual",set())
    far=allocate_new_ifc_guid(source_sha,"Space",NEW_FAR_ID,set())
    with TemporaryDirectory(prefix="g1-manual-space-pair-") as name:
        work=Path(name)
        d0=work/"D0.ifc"
        i_wall=work/"I0_wall.ifc"
        i_joined=work/"I0_connected.ifc"
        i0=work/"I0.ifc"
        d_report=compile_declarative_xml(source,edited,d0)
        operations=[op.operation for op in d_report.operations]
        if operations!=["CREATE_WALL","ADD_WALL_PATH_CONNECTION",
                        "ADD_WALL_PATH_CONNECTION","SPLIT_SPACE"]:
            raise ValueError("Unexpected declarative bounded-space operation plan")
        manual_ifc_reference(
            source,i_wall,"CREATE_WALL",new_guid=new_wall,
            storey_guid=geometry["storey_guid"],
            start=tuple(float(x) for x in geometry["start"]),
            end=tuple(float(x) for x in geometry["end"]),
            height=float(geometry["height"]),
            thickness=float(geometry["thickness"]))
        b=ifcopenshell.open(str(i_wall))
        created=b.by_guid(new_wall)
        for existing,term in zip(refs[:2],("ATSTART","ATEND")):
            identity_name=f"connect-v0.1:{source_sha}:{existing}:{new_wall}"
            rel_guid=ifcopenshell.guid.compress(uuid.uuid5(
                uuid.UUID("38502454-46ea-44b8-8e87-6c6a7e66c111"),
                identity_name).hex)
            b.createIfcRelConnectsPathElements(
                GlobalId=rel_guid,RelatingElement=b.by_guid(existing),
                RelatedElement=created,
                RelatingConnectionType="ATPATH",
                RelatedConnectionType=term,
                RelatingPriorities=(),RelatedPriorities=())
        b.write(str(i_joined))
        author_independent_space_partition(
            i_joined,i0,source_sha=source_sha,
            source_space_guid=refs[2],
            new_wall_guid=new_wall,new_space_guid=far)
        parity=parity_report(d0,i0)
        if not parity["parity"]:
            raise ValueError("Independent Python and declarative IFC observations differ")
        a=ifcopenshell.open(str(d0))
        if (len(a.by_type("IfcSpace"))!=3
                or len(a.by_type("IfcRelSpaceBoundary"))!=19
                or len(a.by_guid(far).BoundedBy)!=6):
            raise ValueError("Compiled native Space partition relation counts unexpected")
        existing=ifcopenshell.open(str(source))
        # Independently authored I0 must preserve source SpaceType and Psets
        # without cloning instance-specific references to the far room.
        d_meta=verify_native_space_metadata(existing,a,refs[2],far)
        i_meta=verify_native_space_metadata(
            existing,ifcopenshell.open(str(i0)),refs[2],far)
        if d_meta!=i_meta:
            raise ValueError("D0/I0 native source Space metadata policies diverged")
        original_boundaries={x.GlobalId for x in existing.by_type("IfcRelSpaceBoundary")}
        actual_boundaries={x.GlobalId for x in a.by_type("IfcRelSpaceBoundary")}
        if not original_boundaries <= actual_boundaries:
            raise ValueError("Original native Space boundaries lost")
        schema_errors={}
        for label,path in (("original",source),("declarative",d0)):
            logger=ifcopenshell.validate.json_logger()
            ifcopenshell.validate.validate(str(path),logger,express_rules=False)
            schema_errors[label]=Counter((str(error.get("type")),str(error.get("attribute")),
                                          str(error.get("message")))
                                         for error in logger.statements if error.get("level")=="error")
        if any(count>schema_errors["original"][category]
               for category,count in schema_errors["declarative"].items()):
            raise ValueError("New IFC schema errors introduced by bounded Space partition")
        result={
            "status":"PASS_ONE_TRUSTED_PAIRED_DECLARATIVE_SPACE_ORACLE_NOT_OFFICIAL_BIM_EDIT",
            "frozen_task_id":"WAL-CRE-SPA-A-003",
            "same_pinned_public_source":True,
            "original_input_sha256":source_sha,
            "declarative_result_sha256":hashlib.sha256(d0.read_bytes()).hexdigest(),
            "imperative_result_sha256":hashlib.sha256(i0.read_bytes()).hexdigest(),
            "native_independent_ifc_parity":True,
            "native_ifc_comparison_categories":["ifc_schema","identities","products",
                                                "relations","property_sets","materials"],
            "native_space_objects_total":3,
            "new_native_space_count":1,
            "native_space_boundaries_total":19,
            "new_native_boundary_relations":len(actual_boundaries-original_boundaries),
            "far_native_space_boundary_count":len(a.by_guid(far).BoundedBy),
            "declarative_compiler_operations":operations,
            "original_ifc_schema_error_count":sum(schema_errors["original"].values()),
            "declarative_ifc_schema_error_count":sum(schema_errors["declarative"].values()),
            "new_ifc_schema_error_categories":0,
            "new_space_independent_type_assignment_proven":len(a.by_guid(far).IsTypedBy)>0,
            "new_space_independent_psets_proven":len(a.by_guid(far).IsDefinedBy)>0,
            "source_type_pset_qto_semantics_verified_equal_between_arms":True,
            "source_space_metadata_gate":d_meta.report(),
            "model_interpreted_natural_language":False,
            "input_information_equivalence_proven":False,
            "manual_source_only_geometry_resolution":True,
            "official_evaluator_executed":False,
            "official_tasks_scored":0,
            "LLM_provider_calls":0,
            "ground_truth_loaded":False,
            "result_ifc_committed_to_repository":False,
            "frozen_sample_modified":False,
        }
    if hashlib.sha256(source.read_bytes()).hexdigest()!=source_sha:
        raise ValueError("Pinned source IFC modified by manual oracle")
    return result


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    options=parser.parse_args()
    outcome=verified_paired_space_partition()
    if options.output_json:
        dest=options.output_json
        if dest.exists() or dest.is_symlink() or not dest.parent.is_dir():
            parser.error("Refuse overwrite, symlink or nonexistent evidence directory")
        with dest.open("x",encoding="utf8",newline="\n") as file:
            file.write(json.dumps(outcome,indent=2,sort_keys=True)+"\n")
    print(json.dumps(outcome,indent=2,sort_keys=True))
    # The geometry/relationship oracle passes. The model/evaluator/fairness
    # gates do not: intentionally nonzero to prevent CI declaring task solved.
    return 2


if __name__=="__main__":
    raise SystemExit(main())
