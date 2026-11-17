"""v0.42 full original-public P3 existing native-Slab read-only XML audit.

Preregistered exact original 45/15 and 2 source/question SHAs; independent
source-native-mm ordered vertices + indexed faces / relationship oracle;
real model-facing 2-tool Column/Slab native IFC writes, no model provider,
Docker, hidden GT or original author grading. Original files immutable.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from tools.audit_bibimbap_author import _head,AUTHOR_SHA,DATA_SHA
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import XmlSourceEditSession,file_hash
from tools.bibimbap_v042_native_slab_source_oracle import (
    verify_original_native_slab_evidence,verify_v042_output_original_native)
from tools.audit_bibimbap_v041_p3_live_column_slab import (
    illustrative_non_answer_xml,V037,V040)

ROOT=Path(__file__).resolve().parents[1]
ISSUE="https://github.com/pikaybh/bim-markup-bench/issues/199"
V041=("reports/bibimbap_v041_original_p3_column_slab_live_source_and_native_writer_20261117.json",
      "370a70de43399f77fc57f22b4669ca15b5b63204005b6ddb7414c923bcde0b1e")
# Keep the first source/native experiment report as an immutable forensic record.
# The full native IFC file SHA is NOT repeatable because native IFC allocator
# serializes generated new relationship GUIDs; source/physical IFC invariants
# are independently repeatable and must be the authoritative final evidence.
V042_PRELIM=(
    "reports/bibimbap_v042_original_P3_source_native_slab_readonly_live_20261117.json",
    "044c78065e2e9c3c732a732a66658ba38d0a4fd41657c6818ddaa5d82f836489")
Q="{urn:bim-markup-bench:toy:v0}"
PINS={
 "topological_test_02":{
  "source_sha":"8f1d9e885603f8680cb79f2a373fa36b4ecd52634ac920f2ec53c60ac465ad72",
  "question_sha":"8d9053bf43826d2354f8053fb9e23b147c13e496c3cdb79b063443e237f297ff",
  "kind":"Column","existing_walls":4,"native_slabs":2,"source_roots":89},
 "topological_test_04":{
  "source_sha":"29cd44b72639ba9573aa1698a4efab4adcfbc5461c19dd85259e6a9505d303e5",
  "question_sha":"c587dae1444490eb2be2e92ea2359039e5099b87690828dfd4cbe81c7cf46fba",
  "kind":"Slab","existing_walls":7,"native_slabs":1,"source_roots":108},
}
TARGETS=tuple(PINS)


def require(ok,why):
    if not ok:raise ValueError(why)


def input_cohort(root:Path,author:Path,data:Path)->dict:
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Original author/data HEAD changed from frozen upstream original public")
    for file,hash_value in (V037,V040,V041,V042_PRELIM):
        require(file_hash(root/file)==hash_value,
                "Previously frozen baseline author/Report source SHA changed: "+file)
    population=public_45(author,data)
    require(len(population)==45
            and len({x["test_id"] for x in population})==45
            and Counter(x["crud"] for x in population)==
                {"create":15,"update":15,"delete":15},
            "Original full benchmark 45 ITT / 15 original CREATE count changed")
    indexed={x["test_id"]:x for x in population}
    for tid,pin in PINS.items():
        task=indexed.get(tid)
        require(task is not None and task["crud"]=="create"
                and task["original_ifc_sha256"]==pin["source_sha"]
                and task["public_question_sha256"]==pin["question_sha"],
                "v0.42 source original public task question/input sha mismatch")
    return indexed


def inspect_one(task:dict,pin:dict,source:Path,folder:Path)->dict:
    original_sha=file_hash(source)
    require(original_sha==pin["source_sha"] and not source.is_symlink(),
            "v0.42 original source IFC SHA invalid")
    native=ifcopenshell.open(str(source))
    require(native.schema=="IFC4X3" and abs(
            ifcopenshell.util.unit.calculate_unit_scale(native)-.001)<1e-12
            and len(native.by_type("IfcWall"))==pin["existing_walls"]
            and len(native.by_type("IfcSlab"))==pin["native_slabs"]
            and len(native.by_type("IfcRoot"))==pin["source_roots"]
            and len(native.by_type("IfcRelSpaceBoundary"))==0,
            "Original native source IFC/geometry population mismatch")
    previous=XmlSourceEditSession(
        source,folder/"old_v041",experimental_original_p3_v041=True)
    base=etree.fromstring(previous.current_xml)
    require(len(base)==3 and len(base.find(Q+"Elements"))==pin["existing_walls"]
            and not any(e.tag==Q+"Slab" for e in base.find(Q+"Elements")),
            "Prior P3 matched XML source-opaque Slab count not as preregistered")
    live=XmlSourceEditSession(
        source,folder/"new_v042",experimental_original_native_slab_v042=True)
    require(live.slab_original_task_id==task["test_id"]
            and live.p3_original_task_id is None
            and live.room_original_task_id is None
            and live.complex_original_task_id is None
            and {t["name"] for t in live.tools}==
                {"read_building_xml","submit_building_xml"},
            "v0.42 model-facing 2-tool surface changed or optins combined")
    read=live.call("read_building_xml",{})
    require(read["status"]=="ok" and read["xml"]==live.current_xml.decode("utf8")
            and read["native_candidate_available"] is False,
            "v0.42 actual model-facing read not exposed full source XML")
    root=etree.fromstring(live.current_xml)
    require(len(root)==4
            and etree.tostring(root.find(Q+"Levels"),method="c14n")==
                etree.tostring(base.find(Q+"Levels"),method="c14n")
            and etree.tostring(root.find(Q+"Elements"),method="c14n")==
                etree.tostring(base.find(Q+"Elements"),method="c14n")
            and etree.tostring(root.find(Q+"Relations"),method="c14n")==
                etree.tostring(base.find(Q+"Relations"),method="c14n"),
            "v0.42 read-only slab evidence changed any existing mutable typed XML state")
    read_evidence=verify_original_native_slab_evidence(
        source,live.current_xml,task_id=task["test_id"])
    require(read_evidence["actual_model_facing_existing_native_slab_count"]==
                pin["native_slabs"],
            "v0.42 actual model source Slab objects not completely exposed")
    full_text=illustrative_non_answer_xml(
        live.current_xml,kind=pin["kind"])
    submitted=live.call("submit_building_xml",{
        "xml_text":full_text.decode("utf8")})
    require(submitted["status"]=="ok"
            and submitted.get("native_ifc_committed") is True
            and submitted.get("compile_status")==
                "COMMITTED_V042_ORIGINAL_NATIVE_SLAB_READONLY_XML_AND_REAL_P3_NATIVE_WRITER"
            and live.output_ifc and live.output_ifc.is_file()
            and live.current_xml==full_text,
            "v0.42 actual P3 model-facing native IFC writer failed")
    independent=verify_v042_output_original_native(
        source,live.output_ifc,task_id=task["test_id"],
        submitted_xml=full_text)
    require(independent["original_native_mm_output_physical_oracle"][
                "all_original_opaque_native_Slab_physical_shapes_preserved"]==
            pin["native_slabs"],
            "v0.42 native output did not preserve all pre-existing Slabs")
    after=live.call("read_building_xml",{})
    require(after["status"]=="ok"
            and after["xml"]==full_text.decode("utf8")
            and after["native_candidate_available"] is True
            and file_hash(source)==original_sha,
            "v0.42 last-valid XML/native and original source invariants failed")
    return {
        "task_id":task["test_id"],
        "original_public_question":task["public_question"],
        "original_public_question_sha256":task["public_question_sha256"],
        "original_native_source_ifc_relpath":task["original_source_ifc_relpath"],
        "original_native_source_ifc_sha256":original_sha,
        "original_native_ifc_schema":"IFC4X3",
        "original_native_length_unit":"mm",
        "original_original_native_roots_count":pin["source_roots"],
        "original_native_source_wall_count":pin["existing_walls"],
        "original_native_source_slab_count":pin["native_slabs"],
        "prior_v041_XML_visible_original_source_Slabs":0,
        "v042_XML_native_readonly_reference_Slabs":pin["native_slabs"],
        "v042_XML_editable_existing_original_Slabs":0,
        "new_generic_native_target_kind":pin["kind"],
        "v042_model_visible_XML_source_sha256":sha256(live.original_xml).hexdigest(),
        "v042_model_visible_XML_unchanged_existing_typed_state":True,
        "v042_model_facing_native_writer_status":submitted["compile_status"],
        # Do not freeze a non-repeatable native candidate whole-file SHA here.
        # It is verified by the independent physical IFC oracle, not byte parity.
        "v042_generated_native_candidate_whole_file_sha_repeatable":False,
        "v042_native_candidate_physical_geometry_and_source_verified":True,
        "v042_model_facing_tools":["read_building_xml","submit_building_xml"],
        "v042_read_source_mesh_original_native_mm_independent_oracle":read_evidence,
        "v042_reopened_original_native_IFC_independent_oracle":
            independent["original_native_mm_output_physical_oracle"],
        "v042_original_IFC_source_bytes_unchanged":True,
        "v042_readonly_Slab_mesh_compile_permission":"NONE_READ_ONLY",
        "original_task_specific_I0_D0_matched_pair":False,
        "original_author_task_answer_proven":False,
        "original_author_evaluator_invoked":False,
    }


def audit(root:Path,author:Path,data:Path)->dict:
    cohort=input_cohort(root,author,data)
    rows=[]
    with TemporaryDirectory(prefix="bmb-v042-native-slab-readonly-exact-") as td:
        for index,tid in enumerate(TARGETS):
            t=cohort[tid]
            rel=Path(t["original_source_ifc_relpath"])
            require(not rel.is_absolute()
                    and (data/"ifc"/rel).resolve().is_relative_to((data/"ifc").resolve()),
                    "Original source path escaped public source data IFC directory")
            rows.append(inspect_one(
                t,PINS[tid],data/"ifc"/rel,Path(td)/str(index)))
    require(len(rows)==2
            and sum(x["v042_XML_native_readonly_reference_Slabs"] for x in rows)==3
            and all(x["v042_original_IFC_source_bytes_unchanged"] for x in rows)
            and _head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Original source invariant or combined 3 Slab source count failed")
    return {
        "status":"V042_ORIGINAL_P3_TWO_REAL_XML_MODEL_SLAB_NATIVE_READONLY_EVIDENCE_AND_NATIVE_WRITERS_PASS",
        "pre_registered_issue":ISSUE,
        "stacked_parent_v041_exact_commit":"d48a31805e05b802b7fdf4f51852a4bb37d98b26",
        "original_author_git_head":AUTHOR_SHA,
        "original_data_git_head":DATA_SHA,
        "previous_original_v037_report_sha256":V037[1],
        "previous_original_v040_report_sha256":V040[1],
        "previous_original_v041_report_sha256":V041[1],
        "preserved_preliminary_v042_forensic_report_sha256":V042_PRELIM[1],
        "preliminary_v042_report_contains_generated_candidate_nonrepeatable_SHA":True,
        "authoritative_final_report_excludes_generated_candidate_whole_file_SHA":True,
        "original_public_ITT_tasks_total":45,
        "original_PUBLIC_create_tasks_total":15,
        "original_previous_task_specific_developer_D0_I0_create_pairs":5,
        "original_create_tasks_still_without_task_specific_D0_I0_pairs":10,
        "actual_original_native_Slabs_newly_visible_as_read_only_in_XML_instances":3,
        "actual_original_public_P3_task_sources_newly_read_exposed":2,
        "source_native_original_Slab_mesh_verts_total":24,
        "source_native_original_Slab_mesh_triangle_indices_total":36,
        "new_actual_model_facing_P3_native_create_writers_verified":2,
        "v041_previous_opaque_Slabs_read_only_reference_no_longer_missing":True,
        "new_native_Slab_evidence_is_editable":False,
        "full_other_original_IFC_metadata_information_parity_proven":False,
        "complete_matched_XML_Python_information_parity_45_tasks":0,
        "complete_matched_XML_Python_native_mutation_parity_45_tasks":0,
        "original_public_task_specific_D0_I0_solution_proven_by_v042":0,
        "original_author_evaluator_invocations":0,
        "real_matched_LLM_XML_vs_Python_trials":0,
        "Docker_calls":0,
        "paid_provider_calls":0,
        "original_public_source_files_modified":False,
        "original_author_code_or_evaluator_modified":False,
        "original_default_XSD_modified":False,
        "research_main_or_Xim_modified":False,
        "complete_original_IFC_STEP_parity_proven":False,
        "next_priority":"Complete remaining original source read parity beyond native Slab; enumerate model-visible original IFC metadata/relation differential against Python; only after full read/write parity preregister matched LLM D vs I",
        "rows":rows,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--author",type=Path,required=True)
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--write",type=Path)
    a=p.parse_args()
    result=audit(a.root,a.author,a.data)
    raw=(json.dumps(result,sort_keys=True,indent=2)+"\n").encode("utf8")
    if a.write:
        a.write.parent.mkdir(parents=True,exist_ok=True)
        with a.write.open("xb") as f:f.write(raw)
        print("V042_FINAL_FROZEN_REPORT",a.write,"sha256",sha256(raw).hexdigest())
    else:
        print(json.dumps({
            "status":result["status"],
            "new_readonly_source_native_slabs":
                result["actual_original_native_Slabs_newly_visible_as_read_only_in_XML_instances"],
            "actual_native_P3_creators":
                result["new_actual_model_facing_P3_native_create_writers_verified"],
            "original_matched_LLM_trials":result["real_matched_LLM_XML_vs_Python_trials"],
        },sort_keys=True))


if __name__=="__main__":
    main()
