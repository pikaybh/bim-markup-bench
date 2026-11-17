"""v0.40 original P2 actual model-facing IfcSpace source facts + native Wall smoke.

Source-first offline audit, not original task answer or an LLM comparison.
Exactly two source-SHA-pinned original topological CREATE tasks. No hidden GT,
original author scorer, Docker, model provider or Xim source.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v40_native_room_evidence import Q,PINS
from tools.audit_bibimbap_author import _head,AUTHOR_SHA,DATA_SHA
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import XmlSourceEditSession,file_hash
from tools.bibimbap_v040_native_room_oracle import verify_p2_native_wall_create

ROOT=Path(__file__).resolve().parents[1]
ISSUE="https://github.com/pikaybh/bim-markup-bench/issues/195"
V037=("reports/bibimbap_v037_original10_create_live_source_and_writer_gates_20261117.json",
      "33d99e6fb624e6a5e89dc301791c269bd5ca7d2666d8618fc67379664938501f")
V039=("reports/bibimbap_v039_original_p1_complex_native_xml_live_20261117.json",
      "3d7a5e642b22b024c938d5c1f712c0eaab8e11ffb6fbe274b0c90ddef074b09a")
TARGETS=("topological_test_01","topological_test_03")


def check(test,description):
    if not test: raise ValueError(description)


def inputs(root:Path,author:Path,data:Path)->tuple[dict,dict]:
    check(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
          "Original author/data Git source HEAD changed")
    records={}
    for rel,pin in (V037,V039):
        file=root/rel
        check(file.is_file() and not file.is_symlink()
              and file_hash(file)==pin,
              "Prior frozen original public report SHA drift: "+rel)
        records[rel]=json.loads(file.read_text(encoding="utf8"))
    v37=records[V037[0]]
    v39=records[V039[0]]
    check(v37["original_public_full_ITT_45"]==45
          and v37["original_public_all_CREATE_15"]==15
          and v37["remaining_original_CREATE_not_yet_native_D0_I0_paired"]==10
          and v39["original_45_public_ITT_denominator"]==45
          and v39["original_15_CREATE_denominator"]==15
          and v39["previous_task_specific_original_developer_D0_I0_pairs"]==5
          and v39["real_paired_LLM_XML_Python_model_trials"]==0,
          "Frozen original45 denominator or research classification changed")
    original=public_45(author,data)
    check(len(original)==45
          and len({x["test_id"] for x in original})==45
          and Counter(x["crud"] for x in original)==
                {"create":15,"update":15,"delete":15},
          "Original 45 public tasks or 15 CREATE denominator changed")
    original={x["test_id"]:x for x in original}
    prior={x["task_id"]:x for x in v37["rows"]}
    check(set(TARGETS)==set(x[0] for x in PINS.values()),
          "P2 hard source SHA cohort drift")
    for tid in TARGETS:
        source,old=original[tid],prior[tid]
        check(source["crud"]==old["original_crud"]=="create"
              and source["category"]==old["original_category"]=="topological"
              and source["public_question_sha256"]==old["public_question_sha256"]
              and source["original_ifc_sha256"]==old["original_public_IFC_sha256"]
              and PINS[source["original_ifc_sha256"]][0]==tid
              and old["next_engineering_priority_tier"]==
                "P2_NAMED_ROOM_OR_SOURCE_SPACE_NOT_IN_XML"
              and old["actual_XML_session_admission"]=="ADMITTED_SOURCE_ONLY",
              "Original P2 public SHA/IFC/role/class pre-registered evidence changed")
    return original,prior


def illustrative_wall(source_xml:bytes)->bytes:
    root=etree.fromstring(source_xml)
    check(root.tag==Q+"Building" and
          len(root.findall("./"+Q+"OriginalNativeRoomEvidence"))==1,
          "No complete P2 immutable original Room source state")
    zero=next((l for l in root.findall("./"+Q+"Levels/"+Q+"Level")
               if abs(float(l.get("elevation")))<1e-10),None)
    check(zero is not None and zero.get("ifcGuid"),
          "P2 source original zero-elevation native Storey missing")
    elements=root.find(Q+"Elements")
    check(elements is not None and len(elements)>0,
          "P2 typed original Walls not in source")
    check(not any(x.get("id")=="v040_generic_wall_not_task_solution"
                  for x in elements),"Duplicate deterministic Wall source ID")
    # Deliberately far from any original room; NOT a topological task answer.
    etree.SubElement(elements,Q+"Wall",{
        "id":"v040_generic_wall_not_task_solution",
        "level":zero.get("id"),
        "x1":"8","y1":"0","z1":"0",
        "x2":"9","y2":"0","z2":"0",
        "height":"2.5","thickness":"0.2"})
    return etree.tostring(root,encoding="utf8")


def actual_source_and_writer_probe(task:dict,old:dict,source:Path,scratch:Path)->dict:
    tid=task["test_id"]
    original_sha=file_hash(source)
    check(source.is_file() and not source.is_symlink()
          and original_sha==task["original_ifc_sha256"]
          and not scratch.exists(),
          "Original P2 input IFC or unique temporary session directory invalid")
    native=ifcopenshell.open(str(source))
    check(native.schema=="IFC4X3" and abs(
          ifcopenshell.util.unit.calculate_unit_scale(native)-.001)<1e-12,
          "Original P2 native IFC4X3/millimetre source drift")
    native_spaces=native.by_type("IfcSpace")
    named=PINS[original_sha][1]
    source_names={g:native.by_guid(g).is_a() for g in named}
    check(len(native_spaces)==PINS[original_sha][2]
          and len(native.by_type("IfcRelSpaceBoundary"))==0,
          "P2 original room count or absent source boundary drift")

    # Actual future D0 host default stays unchanged and hides native Rooms.
    default=XmlSourceEditSession(source,scratch/"original_default_XML")
    check(default.room_original_task_id is None
          and default.submissions==0 and default.output_ifc is None,
          "Unmodified default XML session unexpectedly changed behavior")
    base=etree.fromstring(default.current_xml)
    baseids={n.get("ifcGuid") for n in base.find(Q+"Elements")}
    check(all(x.GlobalId not in baseids for x in native_spaces)
          and all(g in baseids for g in named if source_names[g]=="IfcWall"),
          "Old default XML original source-room information gap changed")

    session=XmlSourceEditSession(
        source,scratch/"explicit_v040_native_room",
        experimental_original_room_v040=True)
    check(session.room_original_task_id==tid
          and session.legacy_original_task_id is None
          and session.complex_original_task_id is None
          and session.output_ifc is None and session.submissions==0
          and set(x["name"] for x in session.tools)==
              {"read_building_xml","submit_building_xml"},
          "v0.40 actual model-facing source view and tool names changed")
    read=session.call("read_building_xml",{})
    check(read.get("status")=="ok"
          and read["xml"]==session.current_xml.decode("utf8")
          and read["native_candidate_available"] is False,
          "v0.40 complete model-facing XML read returned wrong state")
    baseline=session.current_xml
    root=etree.fromstring(baseline)
    evidence=root.find(Q+"OriginalNativeRoomEvidence")
    spaces=evidence.find(Q+"NativeSpaces").findall(Q+"NativeSpace")
    relationships=evidence.find(Q+"OriginalExplicitSpaceRelations").findall(Q+"Relation")
    references=evidence.find(Q+"PublicRoomIdentifiers").findall(Q+"PublicRoomReference")
    check(len(spaces)==len(native_spaces)==len(relationships)
          and len(references)==len(named)
          and int(evidence.get("originalExplicitSpaceBoundaryCount"))==0
          and evidence.get("compilerEditPermission")=="NONE_READ_ONLY",
          "P2 genuine original Spaces or relationships not fully exposed")
    catalog={x.get("ifcGuid"):x for x in spaces}
    check(set(catalog)=={x.GlobalId for x in native_spaces},
          "P2 source true original IfcSpace GUID omitted in new XML")
    # Independent original native-mm input vs exact *model-visible* indexed
    # triangle oracle. IfcOpenShell's mm->metre file conversion can retessellate
    # two source IfcSpaces with a different surface diagonal, even where
    # vertices/physical surfaces agree. True source authority must be read
    # from native original IFC, not the normalized clone.
    source_mesh_settings=ifcopenshell.geom.settings()
    source_mesh_settings.set(source_mesh_settings.USE_WORLD_COORDS,True)
    details=[]
    for space in sorted(native_spaces,key=lambda e:e.GlobalId):
        node=catalog[space.GlobalId]
        agg=ifcopenshell.util.element.get_aggregate(space)
        triangles=node.findall("./"+Q+"WorldTriangles/"+Q+"Triangle")
        vertices=node.findall("./"+Q+"WorldVertices/"+Q+"Vertex")
        want=12 if tid=="topological_test_01" else 20
        native_owner=ifcopenshell.geom.create_shape(source_mesh_settings,space)
        native_shape=native_owner.geometry
        original_vertex_numbers=list(native_shape.verts)
        original_face_indices=list(native_shape.faces)
        indexed_native_vertices=[tuple(original_vertex_numbers[i+j]
            for j in range(3))
            for i in range(0,len(original_vertex_numbers),3)]
        indexed_visible_vertices=[tuple(float(x.get(axis)) for axis in ("x","y","z"))
            for x in vertices]
        indexed_native_triangles=[tuple(original_face_indices[i+j]
            for j in range(3))
            for i in range(0,len(original_face_indices),3)]
        indexed_visible_triangles=[tuple(int(x.get(axis)) for axis in ("a","b","c"))
            for x in triangles]
        check(len(indexed_native_vertices)==len(indexed_visible_vertices)
              and len(indexed_native_triangles)==len(indexed_visible_triangles)
              and all(all(abs(x-y)<=.000000500001
                          for x,y in zip(physical,visible))
                      for physical,visible in zip(indexed_native_vertices,indexed_visible_vertices))
              and indexed_native_triangles==indexed_visible_triangles,
              "Read-only P2 XML source room indexed geometry not IDENTICAL to actual original-mm IFC")
        check(agg and agg.is_a("IfcBuildingStorey")
              and node.get("sourceAggregateStoreyGuid")==agg.GlobalId
              and len(triangles)==want
              and len(vertices)==(8 if want==12 else 12)
              and node.get("nativeIfcClass")=="IfcSpace"
              and node.get("compilerEditPermission")=="NONE_READ_ONLY",
              "P2 real room mesh or original Storey aggregate was misrepresented")
        details.append({
            "ifc_guid":space.GlobalId,
            "native_ifc_class":"IfcSpace",
            "native_room_source_name":str(space.Name),
            "native_room_source_long_name":str(space.LongName),
            "original_aggregate_storey_guid":agg.GlobalId,
            "read_only_world_vertex_count":len(vertices),
            "read_only_original_physical_triangle_count":len(triangles),
            "world_bounds_m":[float(node.get(k)) for k in (
                "worldMinX","worldMinY","worldMinZ",
                "worldMaxX","worldMaxY","worldMaxZ")],
            "world_mesh_source_digest":node.get("worldMeshSha256"),
            "read_only_XML_indexed_mesh_matches_original_native_mm_IFC_exactly":True,
            "explicit_original_IfcRelSpaceBoundary_count":0,
            "editable_as_fake_rectangular_XML_Space":False,
        })
    actual_named={}
    for ref in references:
        guid=ref.get("publicGuid")
        check(guid in named
              and ref.get("actualNativeIfcClass")==source_names[guid]
              and ref.get("remappingOrInferredRoomGuidAllowed")=="false",
              "Public named Room GUID class was silently remapped")
        actual_named[guid]=ref.get("actualNativeIfcClass")
    check(actual_named==source_names,
          "Original public question room-noun/native class mismatch hidden")
    edits=illustrative_wall(baseline)
    written=session.call("submit_building_xml",{
        "xml_text":edits.decode("utf8")})
    check(written.get("status")=="ok"
          and written.get("native_ifc_committed") is True
          and written.get("compile_status")==
                "COMMITTED_ORIGINAL_IFC4X3_ROOM_NATIVE_REFERENCE_READONLY_V040"
          and session.output_ifc is not None and session.output_ifc.is_file()
          and session.submissions==1 and session.current_xml==edits,
          "P2 actual XML model-host native IFC Wall writer failed")
    oracle=verify_p2_native_wall_create(
        source,session.output_ifc,task_id=tid,submitted_xml=edits)
    after=session.call("read_building_xml",{})
    check(after["xml"]==edits.decode("utf8")
          and after["native_candidate_available"] is True
          and file_hash(source)==original_sha,
          "P2 original source mutated or actual model read not updated")
    return {
        "task_id":tid,
        "original_public_native_IFC_sha256":original_sha,
        "original_public_question_sha256":task["public_question_sha256"],
        "original_native_schema":"IFC4X3",
        "original_native_length_unit_to_m":.001,
        "default_source_XML_admitted_but_missing_native_IfcSpaces":True,
        "v040_explicit_optin_source_XML_admitted":True,
        "model_visible_XML_full_state_sha256":sha256(baseline).hexdigest(),
        "model_visible_original_IfcSpace_readonly_count":len(spaces),
        "model_visible_real_original_IfcSpace_meshes":details,
        "model_visible_original_IfcSpace_explicit_aggregate_relations":len(relationships),
        "original_IfcRelSpaceBoundary_count":0,
        "public_guid_actual_IFC_class":dict(sorted(actual_named.items())),
        "original_public_room_noun_mismatch_explicit":any(
            kind!="IfcSpace" for kind in actual_named.values()),
        "original_public_guid_remapped_to_different_IfcSpace":False,
        "original_room_adjacency_inferred_from_proximity":False,
        "source_IfcSpace_typed_XML_authorable":False,
        "model_facing_XML_tool_names":["read_building_xml","submit_building_xml"],
        "illustrative_wall_XML_digest":sha256(edits).hexdigest(),
        "illustrative_wall_is_original_topological_task_answer":False,
        "actual_model_facing_native_Wall_written":True,
        "independent_reopened_native_IFC_oracle":oracle,
        "original_IFC_source_unchanged":True,
        "original_author_evaluator_called":False,
        "matched_LLM_D_I_trial":False,
    }


def audit(root:Path,author:Path,data:Path)->dict:
    root,author,data=Path(root),Path(author),Path(data)
    tasks,prior=inputs(root,author,data)
    rows=[]
    with TemporaryDirectory(prefix="bmb-v040-original-room-native-source-") as temp:
        for i,tid in enumerate(TARGETS):
            t=tasks[tid]
            rel=Path(t["original_source_ifc_relpath"])
            source=data/"ifc"/rel
            check(not rel.is_absolute()
                  and source.resolve().is_relative_to((data/"ifc").resolve()),
                  "Unsafe original P2 native source relative path")
            rows.append(actual_source_and_writer_probe(
                t,prior[tid],source,Path(temp)/("case_"+str(i))))
    check(len(rows)==2 and
          [row["task_id"] for row in rows]==list(TARGETS)
          and all(row["original_IFC_source_unchanged"] for row in rows)
          and _head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
          "Original P2 native sources or Git heads changed")
    return {
        "status":"V040_ORIGINAL_P2_IFCSPACE_ROOM_READONLY_SOURCE_AND_NATIVE_WALL_WRITER_VERIFIED",
        "issue":ISSUE,
        "stacked_parent_v039_commit":"071c97b380b5a25821aff5b41e071cb33a1daf93",
        "original_author_git_sha":AUTHOR_SHA,
        "original_data_git_sha":DATA_SHA,
        "original_frozen_v037_report_sha256":V037[1],
        "original_frozen_v039_report_sha256":V039[1],
        "original45_public_ITT_denominator":45,
        "original15_CREATE_denominator":15,
        "original_5_previous_task_specific_developer_D0_I0_semantic_pairs":5,
        "original_10_CREATE_without_task_specific_native_D0_I0_pairs":10,
        "prior_v037_P2_room_information_blocker_cases":2,
        "v040_original_P2_source_room_evidence_XML_admitted":2,
        "v040_original_P2_illustrative_native_Wall_writes":2,
        "v040_original_native_IfcSpace_entities_readonly_exposed":3,
        "v040_all_original_IfcSpace_ordered_vertices_and_indexed_triangles_verbatim_from_native_mm":True,
        "v040_original_public_wrong_room_GUID_class_instances_disclosed":2,
        "v040_new_IfcRelSpaceBoundary_records_invented":0,
        "default_typed_XML_host_modified_or_enabled_v040_automatically":False,
        "actual_original_task_specific_grader_scores_in_v040":0,
        "actual_real_matched_LLM_XML_Python_trials":0,
        "new_paid_provider_requests":0,
        "Docker_worker_executions":0,
        "complete_original45_model_visible_source_facts_equal_across_D_I_proven":0,
        "complete_original45_native_edit_rights_equal_across_D_I_proven":0,
        "public_room_identifier_semantic_conflict_repaired_by_editing_original_dataset":False,
        "full_original_IFC_STEP_entity_byte_equivalence_proven":False,
        "causal_original_45_XML_vs_imperative_LLM_performance_effect_proven":False,
        "next_priority":"P3 actual model-facing Column/Slab CREATE support, followed by fair matched LLM input/write parity",
        "rows":rows,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--author",type=Path,required=True)
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--write",type=Path)
    args=p.parse_args()
    report=audit(args.root,args.author,args.data)
    raw=(json.dumps(report,sort_keys=True,indent=2)+"\n").encode("utf8")
    if args.write:
        args.write.parent.mkdir(parents=True,exist_ok=True)
        with args.write.open("xb") as f:f.write(raw)
        print("WRITTEN",args.write,sha256(raw).hexdigest())
    else:
        print(json.dumps({
            "status":report["status"],
            "native_rooms_readonly_exposed":report[
                "v040_original_native_IfcSpace_entities_readonly_exposed"],
            "public_room_GUID_conflicts":report[
                "v040_original_public_wrong_room_GUID_class_instances_disclosed"],
            "actual_native_Wall_writes":report[
                "v040_original_P2_illustrative_native_Wall_writes"],
            "matched_LLM_trials":report["actual_real_matched_LLM_XML_Python_trials"],
        },sort_keys=True))


if __name__=="__main__":
    main()
