"""Original-public BIBIMBAP test_19 connected Wall *safety blocker* audit.

IMPORTANT: This is a developer-only read/diagnostic workflow, not a supported
native IFC compiler and NOT a candidate output admissible to the original
D0/I0 representation experiment. The actual original wall has two connected
neighbor walls. A full safe native removal has not been established on the
pinned Windows IfcOpenShell runtime; this module explicitly refuses to mark
the minimally removed wall candidate as compiler-safe if original shape and
placement records become orphaned.

All outputs are isolated to TemporaryDirectory, never committed as source
IFC or model-visible XML. The original-author scorer is applied separately
only to a diagnostic I0 object-removal probe, never used as an oracle for
native source integrity. No LLM calls/paid provider activity.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import re

import ifcopenshell
import ifcopenshell.api.pset
import ifcopenshell.util.unit

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45, grade_author
from tools.bibimbap_matched25_tools import XmlSourceEditSession, file_hash
from src.runtime.ifc_projection import project_ifc
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document
from src.runtime.semantic_graph import graph_diff

ROOT=Path(__file__).resolve().parents[1]
TASK_ID="test_19"
NATIVE_ORIGINAL_NORMALIZED_SHA="16568e7c4b8b9d62567a7a199101269daa6e5b1b7535cec095b8e233ae2ef6ac"
FROZEN_PREVIOUS_REPORTS={
    "reports/bibimbap_v023_original_test20_space_delete_D0_I0_native_parity_20261115.json":
        "9abcc4ebd21c18891bf08307624a19f6012a981455eca7db89051ae70ce86102",
    "reports/bibimbap_v024_original_test18_opening_window_D0_I0_20261115.json":
        "a31e74dacdece9924304de6c74c5d9e8769497a8ad68287779ddd4a37bac6a67",
    "reports/bibimbap_v025_original_test17_door_opening_D0_I0_20261115.json":
        "4ea264519d011288acf6d059fc15b3ca49aa7d4d21315ccb5cbebe5bb17f3f4a",
}


class UnsafeOriginalConnectedWall(ValueError):
    pass


def require(cond:bool,reason:str)->None:
    if not cond:
        raise UnsafeOriginalConnectedWall(reason)


def proposed_complete_connected_wall_xml(
    original_public_question:str, complete_xml:bytes,
)->tuple[str,bytes]:
    """One source Wall + both declared connections removed, NO commands.

    The output is an *unsupported diagnostic source-state proposal* and must
    never be submitted as an approved native compilation operation.
    """
    from src.security.agent_boundary import check_xml_bytes
    targets=re.findall(r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",
                       original_public_question)
    require(len(targets)==1,"PUBLIC original wall target is ambiguous")
    guid=targets[0]
    orig=complete_xml.decode("utf8")
    walls=[line for line in orig.splitlines(keepends=True)
           if "<Wall " in line and 'ifcGuid="'+guid+'"' in line]
    require(len(walls)==1,"PUBLIC wall absent or ambiguous in source XML")
    wall=walls[0]
    target=re.search(r'\bid="([^"]+)"',wall)
    require(target is not None,"Original wall has no source ID")
    name=target.group(1)
    joins=[line for line in orig.splitlines(keepends=True)
           if "<Connects " in line
           and (('from="'+name+'"') in line or ('to="'+name+'"') in line)]
    require(len(joins)==2 and len(set(joins))==2,
            "Original wall does not have exactly two XML connection relations")
    new=orig.replace(wall,"",1)
    for line in joins:new=new.replace(line,"",1)
    check_xml_bytes(new.encode("utf8"))
    require(new!=orig and guid not in new,
            "Failed to form isolated complete declarative wall removal")
    return guid,new.encode("utf8")


def exact_declarative_graph_proposal(
    session:XmlSourceEditSession,updated_xml:bytes,
)->dict:
    projection=project_ifc(session.normalized)
    before=bind_document(
        parse_xml(session.original_xml,expected_source_sha256=projection.source.source_sha256),
        projection=projection)
    after=bind_document(
        parse_xml(updated_xml,expected_source_sha256=projection.source.source_sha256),
        projection=projection,verify_native_edges=False)
    delta=graph_diff(before.graph,after.graph)
    require(not delta.added_nodes and not delta.changed_nodes
            and not delta.added_edges and len(delta.removed_nodes)==1
            and before.graph.by_id()[delta.removed_nodes[0]].kind=="Wall",
            "Source-state delta is not exactly one removed Wall node")
    labels=sorted(edge.relation for edge in delta.removed_edges)
    require(labels==["connects","connects","in_storey"],
            "Source-state delta is missing exact two connections and storey membership")
    return {
        "status":"VALID_BUT_UNSUPPORTED_COMPLETE_DECLARATIVE_STATE_DIFF",
        "original_existing_wall_node_removed":1,
        "original_existing_connects_edges_removed":2,
        "original_existing_in_storey_edge_removed":1,
        "unrelated_graph_node_edits":0,
        "unrelated_graph_edge_edits":0,
    }


def _orphan_counts(f:ifcopenshell.file)->dict:
    return {
        "IfcShapeRepresentation":sum(f.get_total_inverses(x)==0
                                     for x in f.by_type("IfcShapeRepresentation")),
        "IfcProductDefinitionShape":sum(f.get_total_inverses(x)==0
                                       for x in f.by_type("IfcProductDefinitionShape")),
        "IfcLocalPlacement":sum(f.get_total_inverses(x)==0
                                for x in f.by_type("IfcLocalPlacement")),
    }


def developer_only_incomplete_native_probe(
    source:Path,normalized_source:Path,public_guid:str,
    temporary_root:Path,author:Path,
)->dict:
    """Deliberately diagnostic candidate, not a safe XML output or I0 pass.

    This uses the smallest tested non-crashing native operations: delete two
    path relationships, individually owned Psets via supported Pset API, and
    the single source Wall. This deliberately does NOT attempt the unstable
    deep representation/placement cleanup in the compiler process. We then
    independently reject the resulting orphaned native geometry/placement.
    """
    normsha=file_hash(normalized_source)
    require(normsha==NATIVE_ORIGINAL_NORMALIZED_SHA,
            "Original source IFC normalization SHA is not frozen")
    old=ifcopenshell.open(str(normalized_source))
    original_guids={p.GlobalId:p.is_a() for p in old.by_type("IfcProduct")}
    try:
        wall=old.by_guid(public_guid)
    except (RuntimeError,ValueError) as exc:
        raise UnsafeOriginalConnectedWall("Native original target GUID absent") from exc
    require(wall.is_a("IfcWall") and not wall.HasOpenings,
            "Original target must be an unhosted source Wall")
    relations=list(old.get_inverse(wall))
    joins=[x for x in relations if x.is_a("IfcRelConnectsPathElements")]
    prop_rels=[x for x in relations if x.is_a("IfcRelDefinesByProperties")]
    require(len(joins)==2 and len(prop_rels)==3 and len(relations)==9,
            "Original native Wall inverse inventory changed")
    for rel in joins:
        require(rel.RelatedElement==wall
                and rel.RelatingElement.is_a("IfcWall")
                and rel.RelatingElement.GlobalId!=public_guid,
                "Unexpected original path-connection role or neighbor")
    for rel in prop_rels:
        pset=rel.RelatingPropertyDefinition
        require(tuple(rel.RelatedObjects)==(wall,)
                and pset.is_a("IfcPropertySet")
                and tuple(old.get_inverse(pset))==(rel,),
                "Original Pset is not exclusively source-Wall-owned")
    baseline=_orphan_counts(old)
    wall_representations=tuple(wall.Representation.Representations)
    original_wall_shape_ids=tuple(x.id() for x in wall_representations)
    require(len(original_wall_shape_ids)==2,
            "Original Wall shape representation count changed")
    previous_roots={x.GlobalId:x.is_a() for x in old.by_type("IfcRoot")}
    # No other original file is loaded writable or changed.
    for rel in joins:
        old.remove(rel)
    for rel in prop_rels:
        ifcopenshell.api.pset.remove_pset(
            old, product=wall, pset=rel.RelatingPropertyDefinition)
    old.remove(wall)
    candidate=temporary_root/"diagnostic_unsafe_native_original_m.ifc"
    old.write(str(candidate))
    new=ifcopenshell.open(str(candidate))
    original_after={x.GlobalId:x.is_a() for x in new.by_type("IfcProduct")}
    require(original_after==
            {guid:cls for guid,cls in original_guids.items()
             if guid!=public_guid},"Low-level candidate changed unrelated native products")
    native_roots={x.GlobalId:x.is_a() for x in new.by_type("IfcRoot")}
    removed_roots=sorted(previous_roots[k]
                         for k in previous_roots.keys()-native_roots.keys())
    require(removed_roots==
            sorted(["IfcWall"]+["IfcRelConnectsPathElements"]*2+
                   ["IfcRelDefinesByProperties"]*3+["IfcPropertySet"]*3),
            "Diagnostic native Root cleanup differs from conservative inventory")
    current=_orphan_counts(new)
    delta={k:current[k]-baseline[k] for k in sorted(baseline)}
    retained_unowned_shapes=0
    for eid in original_wall_shape_ids:
        original_shape=new.by_id(eid)
        require(original_shape.is_a("IfcShapeRepresentation"),
                "Original removed Wall shape no longer present in native probe")
        represented_by_surviving_product=any(
            p.Representation is not None and original_shape in p.Representation.Representations
            for p in new.by_type("IfcProduct")
        )
        if not represented_by_surviving_product:
            retained_unowned_shapes+=1
    require(retained_unowned_shapes==2
            and delta["IfcProductDefinitionShape"]>=1
            and delta["IfcLocalPlacement"]>=1,
            "Original native orphan inventory differs; revise blocker diagnosis")
    # Author scoring is made on independent DIAGNOSTIC output, never
    # treated as a sufficient validation of IFC semantic safety.
    mm=ifcopenshell.util.unit.convert_file_length_units(
        ifcopenshell.open(str(candidate)),"MILLIMETER")
    mm_path=temporary_root/"diagnostic_unsafe_original_mm.ifc"
    mm.write(str(mm_path))
    grade=grade_author(author,source,mm_path,TASK_ID)
    return {
        "status":"DIAGNOSTIC_NATIVE_REMOVAL_INADMISSIBLE_ORPHANED_GEOMETRY",
        "source_original_IfcProduct_count":len(original_guids),
        "diagnostic_original_IfcProduct_count":len(original_after),
        "original_target_wall_absent_in_diagnostic":True,
        "remaining_native_product_classes_and_GUIDs_unchanged":True,
        "exact_original_native_roots_removed_class_inventory":removed_roots,
        "orphaned_native_step_entities_baseline":baseline,
        "orphaned_native_step_entities_diagnostic":current,
        "additional_original_orphaned_entities":delta,
        "retained_original_Wall_shapes_not_owned_by_surviving_products":retained_unowned_shapes,
        "result_is_not_an_admitted_D0_or_I0_original_public_edit":True,
        "original_author_diagnostic_score":grade,
        "native_candidate_sha256":file_hash(mm_path),
    }


def audit_original_connected_wall(
    root:Path,author:Path,data:Path,
)->dict:
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Original author or public dataset Git revision drift")
    for rel,h in FROZEN_PREVIOUS_REPORTS.items():
        require(file_hash(root/rel)==h,"Prior frozen original source report drift")
    tasks={x["test_id"]:x for x in public_45(author,data)}
    require(len(tasks)==45 and TASK_ID in tasks,"Original public45 cohort drift")
    case=tasks[TASK_ID]
    require(case["crud"]=="delete" and case["category"]=="basic",
            "Original test19 category or CRUD changed")
    source=data/"ifc"/case["original_source_ifc_relpath"]
    original_sha=file_hash(source)
    require(original_sha==case["original_ifc_sha256"],
            "Original native IFC source changed")
    with TemporaryDirectory(prefix="bmb-v026-public19-blocker-") as td:
        folder=Path(td)
        d=XmlSourceEditSession(source,folder/"D0_diagnostics")
        public_guid,updated=proposed_complete_connected_wall_xml(
            case["public_question"],d.original_xml)
        graph=exact_declarative_graph_proposal(d,updated)
        legacy=d.call("submit_building_xml",
                      {"xml_text":updated.decode("utf8")})
        require(legacy.get("status")=="error"
                and not legacy.get("native_ifc_committed")
                and d.output_ifc is None
                and d.current_xml==d.original_xml,
                "Existing safe XML compiler unexpectedly accepted blocked native operation")
        # Trusted diagnostic remains outside production compiler. The pinned
        # original author scorer path is explicit, not inferred from source.
        diag=developer_only_incomplete_native_probe(
            source,d.normalized,public_guid,folder,author)
        require(diag["original_author_diagnostic_score"]["original_author_score"]==.5
                and diag["original_author_diagnostic_score"]["original_author_metrics"]==
                   {"object_not_exists":1.0,"integrity_constraint":0.0},
                "Unmodified original-author diagnostic score unexpectedly changed")
        require(file_hash(source)==original_sha,
                "Original public IFC changed during diagnostic")
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Original benchmark repositories changed during diagnostic")
    return {
        "status":"V026_TEST19_BLOCKED_NATIVE_ORPHANED_GEOMETRY_NO_SAFE_D0_I0_PARITY",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/166",
        "original_benchmark_denominator":45,
        "original_case_id":TASK_ID,
        "original_author_git_sha":AUTHOR_SHA,
        "original_public_data_git_sha":DATA_SHA,
        "original_public_question_sha256":case["public_question_sha256"],
        "original_IFC_sha256":original_sha,
        "original_normalized_IFC_sha256":NATIVE_ORIGINAL_NORMALIZED_SHA,
        "prior_frozen_reports_sha256":FROZEN_PREVIOUS_REPORTS,
        "public_declarative_complete_XML_candidate_graph":graph,
        "current_D0_compiler_status":"FAIL_CLOSED_UNSUPPORTED_CONNECTED_WALL_DELETE",
        "diagnostic_low_level_native_only":diag,
        "new_native_original_developer_D0_I0_byte_equal_pairs":0,
        "prior_actual_developer_D0_I0_equal_original_pairs":8,
        "cumulative_actual_developer_D0_I0_equal_original_pairs":8,
        "prior_original_author_callable_developer_pairs":6,
        "cumulative_original_author_callable_developer_pairs":6,
        "other_original_tasks_unverified_same_protocol":37,
        "original_author_missing_Window_reference_cases":2,
        "full_original45_information_and_write_parity_proven":False,
        "real_LLM_calls":0,
        "paid_provider_usd":0,
        "original_author_scorer_source_or_original_IFC_modified":False,
        "untrusted_ifcopenshell_writer_enabled":False,
        "connected_wall_source_model_compiler_supported":False,
        "no_private_original_answer_or_public_target_GUID_in_report":True,
    }


def main()->None:
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--root",type=Path,default=ROOT)
    a.add_argument("--author",type=Path,required=True)
    a.add_argument("--data",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True)
    opt=a.parse_args()
    if opt.output.exists() or opt.output.is_symlink():
        a.error("Refuse to overwrite previous immutable benchmark report")
    result=audit_original_connected_wall(opt.root,opt.author,opt.data)
    opt.output.parent.mkdir(parents=True,exist_ok=True)
    with opt.output.open("x",encoding="utf8",newline="\n") as fh:
        json.dump(result,fh,ensure_ascii=False,sort_keys=True,indent=2)
        fh.write("\n")
    print("V026_RESULT",result["status"])
    print("V026_ORIGINAL_AUTHOR_DIAGNOSTIC",result["diagnostic_low_level_native_only"]["original_author_diagnostic_score"]["original_author_score"])
    print("V026_NEW_PAIRED_PARITY",result["new_native_original_developer_D0_I0_byte_equal_pairs"])
    print("V026_REPORT_SHA256",sha256(opt.output.read_bytes()).hexdigest())


if __name__=="__main__":
    main()
