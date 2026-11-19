"""Prospective original-author scoring *submetric* forensics for frozen D0.

This tool reproduces 4 unchanged, previously frozen, developer-fixed source
IFC candidates using their original v0.8/v0.9/v0.10 source-only fixtures.
Every generated native result and unit-converted result MUST match the
immutable historical SHA256 in their previous D0 reports *before any public
author scoring helper is called*. No original author score is recomputed
or modified. No hidden solutions or targets are read. This examines only
public scorer definitions and original source (not LLM-facing). Results
explain discrepancies, never retune candidate or official evaluator.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import argparse
import json
from pathlib import Path
import sys
import tempfile

import ifcopenshell
import ifcopenshell.util.unit
import ifcopenshell.util.element
import numpy as np
from lxml import etree

from src.runtime.markup_normal_form import NS
from src.runtime.experimental_v8_legacy_projection import project_legacy_v8
from src.runtime.experimental_v8_legacy_compiler import compile_declarative_xml_v8
from src.runtime.experimental_v9_projection import project_ifc_v9
from src.runtime.experimental_v9_complex_compiler import compile_declarative_xml_v9
from src.runtime.experimental_v10_column_multi import (
    source_native_slab_contact_plan,compile_declarative_xml_v10,
)
from tools.audit_bibimbap_v08_legacy_d0 import _fixture as v08_public_fixture
from tools.audit_bibimbap_v09_complex_d0 import _fixed_source_only_state as v09_public_fixture
from tools.oracle_bibimbap_v08_native import verify_ifc2x3_space
from tools.oracle_bibimbap_v09_native import (
    verify_v09_rotated_slab_square,verify_v09_shared_columns_touch_slab,
)
from tools.oracle_bibimbap_v10_native_multi import (
    verify_v10_original_native_column_multi_delete,
)
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_matched25_cli import public_45
from tools.audit_bibimbap_author import _head,AUTHOR_SHA,DATA_SHA

Q="{"+NS+"}"
PINNED={
    "geometry_test_04":{
        "prior_report":"bibimbap_v08_legacy_ifc2x3_ifc4_d0_20261113.json",
        "prior_report_sha256":"1264e33403a8b7e554913a34fc79b031890fd0aee832bc6b8f2010f912a5b4e0",
        "original_score":.916675,
        "failed_metric":"integrity_constraint",
    },
    "geometry_test_14":{
        "prior_report":"bibimbap_v09_complex_original_developer_d0_20261113.json",
        "prior_report_sha256":"0037c30958437364434cd81696991d5268e2ca5c284eba3bf0329c6597cc01de",
        "original_score":2./3,
        "failed_metric":"right_location",
    },
    "topological_test_11":{
        "prior_report":"bibimbap_v09_complex_original_developer_d0_20261113.json",
        "prior_report_sha256":"0037c30958437364434cd81696991d5268e2ca5c284eba3bf0329c6597cc01de",
        "original_score":2./3,
        "failed_metric":"integrity_constraint",
    },
    "topological_test_17":{
        "prior_report":"bibimbap_v010_original_column_multi_developer_d0_20261113.json",
        "prior_report_sha256":"9341aa11206b2d9ae2e5c96e816287f66fb5e0bab0b02d506f65ba7e862fe938",
        "original_score":.5,
        "failed_metric":"integrity_constraint",
    },
}
NAMED_SLAB_V10="2IIWDJ6bzEPxU4iXeUX9Z5"
NAMED_SLAB_V09="0dxtXCDSn2mfP92h$AiPMM"
SLAB_V09="11kJIqz$n2Jf_DfJV1SCVP"
COLUMN_GUIDS_V09=("0n4qMSuxfEFA0BeEfapSQB","0n4qMSuxfEFA0BeEfapSHZ")


def _prior(root:Path,task:str)->tuple[dict,dict]:
    entry=PINNED[task]
    path=root/"reports"/entry["prior_report"]
    if file_hash(path)!=entry["prior_report_sha256"]:
        raise ValueError("Frozen D0 historical report changed: "+entry["prior_report"])
    old=json.loads(path.read_text(encoding="utf8"))
    if task=="geometry_test_04":
        record=next(c for c in old["tasks"] if c["original_public_task_id"]==task)
        grade=record["original_author_grade_after_freezing_d0"]
        expected={
            "source":record["source_m_normalized_sha256"],
            "native":record["candidate_original_m_units_sha256"],
            "mm":record["candidate_original_mm_units_sha256"],
            "original":record["original_public_ifc_sha256"],
            "question":record["public_question_sha256"],
        }
    elif task in ("geometry_test_14","topological_test_11"):
        record=next(c for c in old["cases"] if c["original_public_task"]==task)
        grade=record["original_author_grade_after_candidate_frozen"]
        expected={
            "source":record["native_normalized_source_sha256"],
            "native":record["independent_native_ifc_oracle"]["candidate_sha256"],
            "mm":record["native_output_original_units_sha256"],
            "original":record["original_source_ifc_sha256"],
            "question":record["original_public_question_sha256"],
        }
    else:
        if old["original_public_task_id"]!=task:
            raise ValueError("Original public task mismatch in v0.10 frozen D0")
        grade=old["original_author_D0_score_after_candidate_frozen"]
        expected={
            "source":old["normalized_original_ifc_sha256"],
            "native":old["native_candidate_sha256"],
            "mm":old["original_mm_candidate_sha256"],
            "original":old["original_public_ifc_sha256"],
            "question":old["original_public_question_sha256"],
        }
    if (grade["status"]!="AUTHOR_SCORED"
        or abs(grade["original_author_score"]-entry["original_score"])>1e-8
        or grade["original_author_full_mark"]
        or grade["original_author_metrics"][entry["failed_metric"]]!=0.
        and task!="geometry_test_04"):
        raise ValueError("Historical partial D0 author submetric no longer matches")
    if task=="geometry_test_04" and abs(
        grade["original_author_metrics"]["integrity_constraint"]-.6667
    )>1e-5:
        raise ValueError("Historical original Space integrity score changed")
    return expected,grade


def _frozen_candidate(task:str,raw:Path,folder:Path,expected:dict):
    native_src=folder/"source_metres.ifc"
    original=ifcopenshell.open(str(raw))
    if original.schema not in ("IFC2X3","IFC4X3"):
        raise ValueError("Unexpected original task native schema")
    if abs(ifcopenshell.util.unit.calculate_unit_scale(original)-.001)>1e-12:
        raise ValueError("Pinned original public IFC must still be millimetres")
    ifcopenshell.util.unit.convert_file_length_units(original,"METER").write(
        str(native_src))
    if file_hash(native_src)!=expected["source"]:
        raise ValueError("Frozen original-normalized-source bytes changed")
    if task=="geometry_test_04":
        view=project_legacy_v8(native_src)
        root=etree.fromstring(view.xml)
        v08_public_fixture(task,ifcopenshell.open(str(native_src)),root)
        candidate=folder/"candidate_metres.ifc"
        compile_declarative_xml_v8(native_src,etree.tostring(root),candidate)
        created=ifcopenshell.open(str(candidate)).by_type("IfcSpace")
        old_spaces={x.GlobalId for x in ifcopenshell.open(str(native_src)).by_type("IfcSpace")}
        made=[x.GlobalId for x in created if x.GlobalId not in old_spaces]
        if len(made)!=1:
            raise ValueError("Previously frozen native IfcSpace creation changed")
        proof=verify_ifc2x3_space(native_src,candidate,made[0])
    elif task in ("geometry_test_14","topological_test_11"):
        view=project_ifc_v9(native_src)
        root=etree.fromstring(view.xml)
        v09_public_fixture(task,root)
        candidate=folder/"candidate_metres.ifc"
        compile_declarative_xml_v9(native_src,etree.tostring(root),candidate)
        if task=="geometry_test_14":
            proof=verify_v09_rotated_slab_square(
                native_src,candidate,SLAB_V09)
        else:
            proof=verify_v09_shared_columns_touch_slab(
                native_src,candidate,COLUMN_GUIDS_V09,NAMED_SLAB_V09)
    else:
        view=project_ifc_v9(native_src)
        root=etree.fromstring(view.xml)
        plan=source_native_slab_contact_plan(
            ifcopenshell.open(str(native_src)),NAMED_SLAB_V10)
        for col in root.findall("./"+Q+"Elements/"+Q+"Column"):
            if col.get("ifcGuid") in plan["noncontact_delete_guids"]:
                root.find(Q+"Elements").remove(col)
        candidate=folder/"candidate_metres.ifc"
        compile_declarative_xml_v10(
            native_src,etree.tostring(root),candidate,
            reference_slab_guid=NAMED_SLAB_V10)
        proof=verify_v10_original_native_column_multi_delete(
            native_src,candidate,reference_slab_guid=NAMED_SLAB_V10)
    if file_hash(candidate)!=expected["native"]:
        raise ValueError(
            "Frozen previous native original candidate bytes changed; stop forensic scoring"
        )
    mm=folder/"candidate_native_mm.ifc"
    ifcopenshell.util.unit.convert_file_length_units(
        ifcopenshell.open(str(candidate)),"MILLIMETER").write(str(mm))
    if file_hash(mm)!=expected["mm"]:
        raise ValueError(
            "Frozen previous original-author candidate mm bytes changed; stop forensic scoring"
        )
    if file_hash(raw)!=expected["original"]:
        raise ValueError("Original public IFC source changed during frozen candidate compilation")
    return native_src,candidate,mm,proof


def _public_author_components(task:str,original:Path,edited_mm:Path,author:Path):
    if str(author) not in sys.path:
        sys.path.insert(0,str(author))
    # Pinned original evaluator public *components* are diagnostic only,
    # never compiled into source authoring/LLM instructions or target choice.
    from data.tests.integrity_utils import (
        check_integrity,non_target_elements_unchanged,
        _collect_geom_tree_clash_pairs,
    )
    from data.tests.delete_integrity import (
        wall_connections_deleted,spatial_containment_deleted,
        openings_deleted,aggregations_deleted,
    )
    from data.tests.utils.create_utils import (
        check_spatial_containment,check_elements_preserved,
    )
    from data.tests.utils.clash_utils import check_clash_integrity
    source=ifcopenshell.open(str(original))
    candidate=ifcopenshell.open(str(edited_mm))
    if task=="geometry_test_04":
        before_spaces={x.GlobalId for x in source.by_type("IfcSpace")}
        new=[x for x in candidate.by_type("IfcSpace")
             if x.GlobalId not in before_spaces]
        if len(new)!=1:
            raise ValueError("Expected precisely one newly created native IfcSpace")
        sp=new[0]
        source_aggregate=ifcopenshell.util.element.get_aggregate(sp)
        return {
            "evaluated_public_subchecks":{
                "original_author_check_spatial_containment":float(
                    check_spatial_containment(candidate,sp)),
                "original_author_check_clash_integrity":bool(
                    check_clash_integrity(source,candidate,
                                           list_of_targets=[sp.GlobalId],
                                           clash_mode="collision")),
                "original_author_check_all_prior_root_guids_preserved":float(
                    check_elements_preserved(source,candidate)),
            },
            "native_evidence":{
                "new_space_ifc_class":sp.is_a(),
                "original_source_storey_aggregate_relation_used":bool(
                    source_aggregate and source_aggregate.is_a("IfcBuildingStorey")),
                "source_aggregate_storey_globalid":(
                    source_aggregate.GlobalId if source_aggregate else None),
                "new_IfcSpace_direct_containment_relations":sum(
                    sp in rel.RelatedElements
                    for rel in candidate.by_type("IfcRelContainedInSpatialStructure")
                ),
            },
            "cause_class":"ORIGINAL_AUTHOR_REQUIRES_IFC_REL_CONTAINMENT_WHILE_NATIVE_SPACE_USES_REL_AGGREGATES",
            "interpretation":"The public 3-way author integrity average penalizes missing direct ContainedInSpatialStructure for a valid native space aggregated under original Storey; other two subchecks pass.",
        }
    if task=="geometry_test_14":
        from data.tests.geometry_test_14 import (
            _bbox_in_meters as author_bbox,_location_ok as author_location,
            CENTER_TOLERANCE as author_tolerance,
        )
        s=author_bbox(source.by_guid(SLAB_V09),1.)
        e=author_bbox(candidate.by_guid(SLAB_V09),1.)
        original_center=(s["x_center"],s["y_center"],s["z_center"])
        new_center=(e["x_center"],e["y_center"],e["z_center"])
        delta=tuple(float(x-y) for x,y in zip(new_center,original_center))
        integrity=check_integrity(source,candidate,list_of_targets=[SLAB_V09])
        if not integrity["integrity_constraint"]:
            raise ValueError("Frozen Slab original author integrity unexpectedly now fails")
        return {
            "evaluated_public_subchecks":{
                "original_author_slab_location_center_pass":bool(
                    author_location(source.by_guid(SLAB_V09),
                                    candidate.by_guid(SLAB_V09))),
                "original_author_center_coordinate_tolerance_original_units":
                    float(author_tolerance),
                "original_author_integrity":{
                    k:bool(v) for k,v in integrity.items()},
            },
            "native_evidence":{
                "original_native_slab_bbox_center_original_units":list(original_center),
                "frozen_candidate_slab_bbox_center_original_units":list(new_center),
                "frozen_candidate_center_shift_original_units":list(delta),
                "original_native_short_side_world_Y":float(s["y_len"]),
                "frozen_candidate_square_world_Y":float(e["y_len"]),
                "original_lower_world_Y_remains_fixed":bool(
                    abs(s["y_min"]-e["y_min"])<1e-5),
            },
            "cause_class":"SOURCE_ONLY_ANCHORED_EDGE_MOVE_CONFLICTS_WITH_ORIGINAL_AUTHOR_CENTER_PRESERVATION",
            "interpretation":"Original candidate pins the lower edge while enlarging the short dimension; original author location explicitly demands unchanged bbox center. This is a genuine D0 geometry placement mismatch, not a changed IFC Root.",
        }
    if task=="topological_test_11":
        targets=set(COLUMN_GUIDS_V09)
        integrity=check_integrity(source,candidate,list_of_targets=sorted(targets))
        options=dict(
            focus_guids=targets,clash_mode="collision",allow_touching=False,
            intersection_tolerance=.002,clearance=.05,
            check_all=True,include_classes=None,exclude_classes=None,
            geometry_settings=None,
        )
        before=_collect_geom_tree_clash_pairs(source,**options)
        after=_collect_geom_tree_clash_pairs(candidate,**options)
        introduced=after-before
        if integrity["no_new_clashes"] or len(introduced)!=3:
            raise ValueError("Original public shared-Column frozen clash result changed")
        return {
            "evaluated_public_subchecks":{
                "original_author_check_integrity":{
                    k:bool(v) for k,v in integrity.items()
                },
                "original_author_clash_pairs_before":len(before),
                "original_author_clash_pairs_after":len(after),
                "original_author_new_clash_pair_count":len(introduced),
                "original_author_new_clash_pairs":[
                    list(pair) for pair in sorted(introduced)
                ],
            },
            "native_evidence":{
                "source_named_upper_slab_globalid":NAMED_SLAB_V09,
                "original_column_guid_set":sorted(targets),
                "frozen_candidate_changed_only_the_shared_mapped_column_depth":
                    True,
            },
            "cause_class":"ORIGINAL_AUTHOR_ADDITIONAL_GEOMETRIC_CLASHES_AFTER_SOURCE_TYPED_COLUMN_EXTENSION",
            "interpretation":"Non-target properties/placement signatures pass, but source-to-candidate author geometric collision pairs increase by 3 (two upper slab contacts and another Wall/Column intersection). The original author integrity metric requires no new clashes.",
        }
    if task=="topological_test_17":
        # Source-only pre-registered contact selection, never original
        # grader target list/hidden solutions. The audit duplicates the
        # contact criterion independently via v0.10 oracle beforehand.
        removed={"2IIWDJ6bzEPxU4iXeUX9_B",
                 "2IIWDJ6bzEPxU4iXeUX9ow",
                 "2IIWDJ6bzEPxU4iXeUX9rK",
                 "2IIWDJ6bzEPxU4iXeUX9rM",
                 "2IIWDJ6bzEPxU4iXeUX9ti"}
        per_target={}
        for guid in sorted(removed):
            per_target[guid]={
                "wall_connections_deleted":bool(wall_connections_deleted(
                    source,candidate,guid)),
                "spatial_containment_deleted":bool(spatial_containment_deleted(
                    source,candidate,guid)),
                "openings_deleted":bool(openings_deleted(
                    source,candidate,guid)),
                "aggregations_deleted":bool(aggregations_deleted(
                    source,candidate,guid)),
            }
        preserved=bool(non_target_elements_unchanged(
            source,candidate,sorted(removed)))
        lost={
            x.GlobalId:x.is_a()
            for x in source.by_type("IfcRoot")
            if x.GlobalId not in {e.GlobalId for e in candidate.by_type("IfcRoot")}
            and x.GlobalId not in removed
        }
        counts=Counter(lost.values())
        if preserved or len(lost)!=35 or not all(all(r.values())
                                                  for r in per_target.values()):
            raise ValueError("Frozen original author source non-target delete cause changed")
        return {
            "evaluated_public_subchecks":{
                "original_author_all_target_delete_relation_checks_pass":
                    all(all(row.values()) for row in per_target.values()),
                "original_author_public_four_subchecks_by_source_column":
                    per_target,
                "original_author_non_target_elements_unchanged":preserved,
            },
            "native_evidence":{
                "removed_original_root_objects_excluding_removed_Column_GUIDs":
                    len(lost),
                "original_roots_considered_non_target_but_deleted_with_owned_Column":
                    dict(sorted(counts.items())),
                "original_source_deleted_root_examples_by_class":{
                    key:sorted(g for g,t in lost.items() if t==key)[:2]
                    for key in sorted(counts)
                },
            },
            "cause_class":"PUBLIC_DELETE_NON_TARGET_ROOT_GUARD_COUNTS_SOLE_OWNED_PSETS_AND_TYPE_RELATIONS_AS_MISSING",
            "interpretation":"Each Column has all four public deletion relation subchecks passing; the top-level public non-target Root guard excludes only Column GUIDs and therefore treats 35 owned Pset/Type relation root deletions as missing non-targets. The source-native dependency closure allows them, but the unmodified author grader does not.",
        }
    raise ValueError("Unsupported original v0.11 forensic case")


def run(root:Path,author:Path,dataset:Path,only=None):
    if _head(author)!=AUTHOR_SHA:
        raise ValueError("Pinned original author source SHA drift")
    if _head(dataset)!=DATA_SHA:
        raise ValueError("Pinned original public dataset SHA drift")
    selected=sorted(PINNED) if only is None else sorted(only)
    if not selected or not set(selected)<=set(PINNED):
        raise ValueError("Unknown frozen D0 case in forensics")
    public={x["test_id"]:x for x in public_45(author,dataset)}
    observations=[]
    for task in selected:
        expected,original_grade=_prior(root,task)
        public_entry=public[task]
        if (public_entry["original_ifc_sha256"]!=expected["original"]
            or public_entry["public_question_sha256"]!=expected["question"]):
            raise ValueError("Original public IFC/question SHA drift")
        raw=dataset/"ifc"/public_entry["original_source_ifc_relpath"]
        with tempfile.TemporaryDirectory(prefix="bibimbap136-v011-frozen-") as tmp:
            src,native,mm,proof=_frozen_candidate(
                task,raw,Path(tmp),expected)
            # Only after exact candidate/reproduced previous D0 SHA and
            # independent physical oracle pass may public evaluator
            # *subcomponents* be inspected; no hidden reference IFC.
            mechanics=_public_author_components(task,raw,mm,author)
            if proof.get("status") is None:
                raise ValueError("Independent native oracle returned no proof")
            observations.append({
                "original_public_task_id":task,
                "original_public_question_sha256":expected["question"],
                "original_public_ifc_sha256":expected["original"],
                "original_source_normalized_sha256":expected["source"],
                "recreated_native_candidate_sha256":file_hash(native),
                "recreated_original_units_candidate_sha256":file_hash(mm),
                "frozen_original_author_score":original_grade,
                "prior_D0_report_sha256":PINNED[task]["prior_report_sha256"],
                "candidate_exactly_byte_identical_to_prior_frozen_D0":True,
                "independent_native_ifc_oracle_status":proof["status"],
                "public_author_component_forensics":mechanics,
                "original_author_test_source_not_changed":True,
                "hidden_grader_reference_ifc_not_loaded":True,
                "developer_candidate_not_rewritten_to_improve_score":True,
            })
    return {
        "status":"ORIGINAL_AUTHOR_PUBLIC_METRIC_FORENSICS_V011_FROZEN_D0_ONLY",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/136",
        "original_author_revision":AUTHOR_SHA,
        "original_public_dataset_revision":DATA_SHA,
        "original_45_task_population":45,
        "analyzed_frozen_partial_D0_case_count":len(observations),
        "new_paid_model_calls":0,
        "added_api_cost_usd":"0",
        "historical_real_model_45_scores_untouched":True,
        "frozen_original_grader_edited":False,
        "no_hidden_reference_or_target_used_for_candidate":True,
        "native_all_45_task_parity_not_proven":True,
        "cases":observations,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-root",type=Path,default=Path.cwd())
    parser.add_argument("--author-repo",type=Path,required=True)
    parser.add_argument("--dataset",type=Path,required=True)
    parser.add_argument("--output-json",type=Path,required=True)
    parser.add_argument("--only",choices=sorted(PINNED))
    args=parser.parse_args()
    if args.output_json.exists() or args.output_json.is_symlink():
        parser.error("Refusing overwrite previous original forensic evidence")
    result=run(
        args.research_root.resolve(strict=True),
        args.author_repo.resolve(strict=True),
        args.dataset.resolve(strict=True),
        [args.only] if args.only else None,
    )
    # Validate all values before exclusive file creation to avoid a stray
    # zero-byte report after a failed JSON serialization.
    payload=(json.dumps(result,sort_keys=True,indent=2,
                        ensure_ascii=False)+"\n").encode("utf8")
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    with args.output_json.open("xb") as file:
        file.write(payload)
    print(json.dumps({
        "status":result["status"],
        "analyzed":len(result["cases"]),
        "frozen_original_author_scores":{
            c["original_public_task_id"]:
                c["frozen_original_author_score"]["original_author_score"]
            for c in result["cases"]
        },
        "failure_mechanics":{
            c["original_public_task_id"]:
                c["public_author_component_forensics"]["cause_class"]
            for c in result["cases"]
        },
        "report_sha256":file_hash(args.output_json),
        "new_model_calls":0,
    },sort_keys=True))


if __name__=="__main__":
    main()
