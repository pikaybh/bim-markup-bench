"""v0.39 reproducible original BIBIMBAP P1 actual-model-host complex-native tool audit.

Two pinned original 45 public Create IFCs; no grader, hidden GT, model,
Docker, external fees or product edits. Developer illustrative XML control is
NOT a matched model trial, nor original task success.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v39_complex_overlay import Q,PINS
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import (
    XmlSourceEditSession,UnsupportedArm,file_hash,
)
from tools.bibimbap_v039_complex_native_oracle import verify_complex_original_restored
from tools.audit_bibimbap_author import _head,AUTHOR_SHA,DATA_SHA

ROOT=Path(__file__).resolve().parents[1]
ISSUE="https://github.com/pikaybh/bim-markup-bench/issues/193"
V037=("reports/bibimbap_v037_original10_create_live_source_and_writer_gates_20261117.json",
      "33d99e6fb624e6a5e89dc301791c269bd5ca7d2666d8618fc67379664938501f")
V038=("reports/bibimbap_v038_original_p0_legacy_xml_live_optin_20261117.json",
      "c04448087528aa07b9cee64830defe61e5b3a7836fc4cae8f073dac4bfc7aad4")
TARGETS=("geometry_test_01","topological_test_05")

def ensure(cond,why):
    if not cond:raise ValueError(why)

def inputs(root:Path,author:Path,data:Path):
    ensure(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
           "Original published author/data Git source commit changed")
    old_reports={}
    for filename,expected in (V037,V038):
        path=root/filename
        ensure(path.is_file() and not path.is_symlink()
               and file_hash(path)==expected,
               "Prior frozen original report SHA has changed: "+filename)
        old_reports[filename]=json.loads(path.read_text(encoding="utf8"))
    v037=old_reports[V037[0]]
    v038=old_reports[V038[0]]
    ensure(v037["original_public_full_ITT_45"]==45
           and v037["original_public_all_CREATE_15"]==15
           and v037["remaining_original_CREATE_not_yet_native_D0_I0_paired"]==10
           and v038["original_45_ITT_denominator"]==45
           and v038["original_15_CREATE_denominator"]==15
           and v038["five_old_original_CREATE_developer_semantic_pairs"]==5
           and v038["actual_original_model_scored_LLM_trials"]==0,
           "Frozen original 45/15/10/5/v0.38 LLM evidence changed")
    rows={r["task_id"]:r for r in v037["rows"]}
    public=public_45(author,data)
    ensure(len(public)==45
           and len({x["test_id"] for x in public})==45
           and Counter(t["crud"] for t in public)==
                {"create":15,"update":15,"delete":15},
           "Original 45 public task denominator changed")
    tasks={t["test_id"]:t for t in public}
    for tid in TARGETS:
        row,task=rows[tid],tasks[tid]
        ensure(task["crud"]==row["original_crud"]=="create"
               and row["next_engineering_priority_tier"]==
                    "P1_LIVE_XML_GEOMETRY_PROJECTION_BLOCKED"
               and row["actual_XML_session_admission"]=="BLOCKED_NATIVE_PROJECTION"
               and row["actual_XML_session_block_reason"]=="UNSUPPORTED_GEOMETRY"
               and row["original_ifc_schema"]=="IFC4X3"
               and task["public_question_sha256"]==row["public_question_sha256"]
               and task["original_ifc_sha256"]==row["original_public_IFC_sha256"]
               and task["original_ifc_sha256"] in PINS
               and PINS[task["original_ifc_sha256"]][0]==tid,
               "P1 actual original source/question/SHA/schema prior gate has drifted")
    return tasks,rows


def illustrative_xml(xml:bytes,tid:str)->bytes:
    """Deliberate generic *not a successful original-author answer* control."""
    root=etree.fromstring(xml)
    assert root.tag==Q+"Building"
    elements=root.find(Q+"Elements")
    ensure(elements is not None and not list(elements),
           "Before P1 demo, new Elements must be empty")
    if tid=="geometry_test_01":
        # Small representative 1 x 1 m slab instead of the task's full
        # 3 x 3 m four-column exterior-edge support slab.
        etree.SubElement(elements,Q+"Slab",attrib={
            "id":"illustrative_slabscope",
            "levelGuid":"1ZGO8hrFCHqw0v0026FpFv",
            "x":"1","y":"1","z":"3","length":"1","depth":"1","thickness":".2"})
    elif tid=="topological_test_05":
        # Generic native clipped exterior Wall physical void; do NOT score.
        etree.SubElement(elements,Q+"Opening",attrib={
            "id":"illustrative_opscope",
            "hostGuid":"3Vyqk8cSj8TOuAk6zHUwAc",
            "centerX":"3","centerY":".1","sillZ":"0",
            "width":"1","height":"2"})
        etree.SubElement(elements,Q+"Door",attrib={
            "id":"illustrative_doorscope",
            "opening":"illustrative_opscope",
            "width":"1","height":"2"})
    else:
        raise ValueError("Unknown P1 original task")
    out=etree.tostring(root,encoding="utf8")
    ensure(out!=xml and b"<Create" not in out,
           "Only whole native-source declarative XML may be submitted")
    return out


def one_original_p1(task:dict,row:dict,source:Path,folder:Path)->dict:
    tid=task["test_id"]
    oldsha=file_hash(source)
    ensure(oldsha==task["original_ifc_sha256"]
           and source.is_file() and not source.is_symlink()
           and not folder.exists(),"Original P1 input IFC or folder unsafe")
    original=ifcopenshell.open(str(source))
    ensure(original.schema=="IFC4X3" and abs(
           ifcopenshell.util.unit.calculate_unit_scale(original)-.001)<1e-12,
           "Original P1 native file IFC schema/mm units changed")
    # Prove default old XML session still refuses complex originals.
    try:
        XmlSourceEditSession(source,folder/"default_no_optin")
    except UnsupportedArm as exc:
        ensure(str(exc)=="UnsupportedIFCGeometry",
               "Original P1 default typed projection failure changed unexpectedly")
    else:
        raise ValueError("Original P1 default unexpectedly admitted in old typed XML")
    session=XmlSourceEditSession(
        source,folder/"explicit_complex_v039",
        experimental_original_complex_v039=True)
    ensure(session.complex_original_task_id==tid
           and session.original_native_schema=="IFC4X3"
           and session.legacy_original_task_id is None
           and session.output_ifc is None and session.submissions==0
           and {x["name"] for x in session.tools}==
                {"read_building_xml","submit_building_xml"},
           "Actual model-facing v0.39 original XML tools/session invalid")
    read=session.call("read_building_xml",{})
    ensure(read["status"]=="ok"
           and not read["native_candidate_available"]
           and read["xml"]==session.current_xml.decode("utf8"),
           "Actual XML source read did not expose complete partial overlay state")
    originalxml=session.current_xml
    root=etree.fromstring(originalxml)
    native=root.find(Q+"OriginalNativeSource")
    products=native.find(Q+"Products").findall(Q+"Product")
    relations=native.find(Q+"Relations").findall(Q+"Relation")
    expected_prod={"geometry_test_01":8,"topological_test_05":13}[tid]
    ensure(len(products)==expected_prod
           and len(relations)>0
           and native.get("mode")=="READ_ONLY_NATIVE_IFC_AUTHORITY"
           and native.get("editableGeometryComplete")=="false"
           and root.get("sourceStateCompleteness")==
                "PARTIAL_NATIVE_REFERENCE_OVERLAY_NOT_LOSSLESS_IFC",
           "Original mapped/clipped IFC product representation incomplete or falsely editable")
    critical_type="MappedRepresentation" if tid=="geometry_test_01" else "Clipping"
    critical_class="IfcColumn" if tid=="geometry_test_01" else "IfcWall"
    expected_count=4 if tid=="geometry_test_01" else 7
    ensure(sum(x.get("nativeBodyRepresentationType")==critical_type
               for x in products if x.get("ifcClass")==critical_class)==expected_count,
           "Original mapped/clipped native IFC representation was fabricated/omitted")
    edits=illustrative_xml(originalxml,tid)
    output=session.call("submit_building_xml",{"xml_text":edits.decode("utf8")})
    ensure(output.get("status")=="ok" and output.get("native_ifc_committed") is True
           and output["compile_status"]==
                "COMMITTED_SOURCE_SCHEMA_PRESERVED_CREATE_ORIGINAL_IFC4X3_COMPLEX_V039"
           and session.output_ifc is not None
           and session.output_ifc.is_file()
           and session.current_xml==edits
           and session.submissions==1,
           "Actual model-facing P1 XML write failed physical IFC generation")
    oracle=verify_complex_original_restored(
        source,session.output_ifc,task_id=tid,submitted_xml=edits)
    reread=session.call("read_building_xml",{})
    ensure(reread["status"]=="ok"
           and reread["xml"]==edits.decode("utf8")
           and reread["native_candidate_available"],
           "Actual model-facing XML state not revised after native commit")
    ensure(file_hash(source)==oldsha,
           "Original public native P1 IFC modified after model-facing tool call")
    return {
        "task_id":tid,
        "public_original_ifc_sha256":oldsha,
        "public_question_sha256":task["public_question_sha256"],
        "v037_source_gate":row["actual_XML_session_admission"],
        "v037_source_reason":row["actual_XML_session_block_reason"],
        "default_typed_xml_session_admitted":False,
        "explicit_v039_p1_source_admitted":True,
        "original_source_native_ifc_schema":"IFC4X3",
        "original_source_native_length_unit_to_m":.001,
        "model_visible_complete_XML_partial_overlay_sha256":
            sha256(originalxml).hexdigest(),
        "model_visible_XML_byte_length":len(originalxml),
        "source_original_ifc_product_count_in_readonly_catalog":len(products),
        "source_original_ifc_explicit_relationship_entries_in_readonly_catalog":
            len(relations),
        "source_original_opaque_representation_type":critical_type,
        "source_original_opaque_product_class":critical_class,
        "source_original_opaque_product_count":expected_count,
        "original_opaque_geometry_is_readonly_not_simplified_typed_rectangle":True,
        "model_visible_tools":["read_building_xml","submit_building_xml"],
        "submitted_illustrative_full_xml_sha256":sha256(edits).hexdigest(),
        "submitted_illustrative_is_original_task_solution":False,
        "actual_native_schema_restored_write_committed":True,
        "actual_candidate_native_mm_sha256":file_hash(session.output_ifc),
        "native_compilation_status":output["compile_status"],
        "separate_independent_restored_native_physical_oracle":oracle,
        "original_source_bytes_unchanged":True,
        "original_author_grader_invoked":False,
        "real_model_inference_called":False,
        "causal_XML_vs_Python_impact_supported":False,
    }


def audit(root:Path,author:Path,data:Path)->dict:
    tasks,rows=inputs(root,author,data)
    results=[]
    with TemporaryDirectory(prefix="bmb-v039-actual-model-facing-p1-") as d:
        for ix,tid in enumerate(TARGETS):
            t=tasks[tid]
            rel=Path(t["original_source_ifc_relpath"])
            src=data/"ifc"/rel
            ensure(not rel.is_absolute()
                   and src.resolve().is_relative_to((data/"ifc").resolve()),
                   "Original P1 source file path is unsafe")
            results.append(one_original_p1(t,rows[tid],src,
                                           Path(d)/("case_"+str(ix))))
    ensure(len(results)==2
           and all(x["original_source_bytes_unchanged"] for x in results)
           and _head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
           "Original native public data provenance changed during P1 model host replay")
    return {
        "status":"V039_ORIGINAL_P1_TWO_COMPLEX_SOURCE_XML_HOST_OPTIN_NATIVE_CREATE_PROVEN",
        "issue":ISSUE,
        "stacked_parent_v038_head":
            "769b4013d1af1c0abce4f24d3305a231854fc685",
        "original_author_git_sha":AUTHOR_SHA,
        "original_data_git_sha":DATA_SHA,
        "v037_original10_frozen_report_sha256":V037[1],
        "v038_original_P0_frozen_report_sha256":V038[1],
        "original_45_public_ITT_denominator":45,
        "original_15_CREATE_denominator":15,
        "original_10_CREATE_without_new_task_specific_native_D0_I0_pair":10,
        "previous_task_specific_original_developer_D0_I0_pairs":5,
        "previous_P1_original_schema_valid_complex_geometry_rejections":2,
        "explicit_P1_optin_actual_model_facing_XML_reads":2,
        "explicit_P1_optin_actual_native_IFC_writes":2,
        "default_XML_source_P1_admissions":0,
        "prior_v038_P0_legacy_cases_still_optin_only":3,
        "original_task_specific_author_scores_run":0,
        "real_paired_LLM_XML_Python_model_trials":0,
        "new_paid_provider_requests":0,
        "Docker_code_execution_invoked":False,
        "complete_original_native_source_state_visible_in_XML_proven":False,
        "full_original_task_write_equivalence_between_D_and_I_proven":False,
        "original_native_geometry_of_mapped_or_clipped_source_simplified_or_replaced":False,
        "complete_IFC_STEP_bytes_preserved_proven":False,
        "causal_LLM_representation_performance_claim_supported":False,
        "next_priority":"P2 source IfcSpace visibility and public room GUID/native class ambiguity; P3 generic matched host Column/Slab capabilities",
        "rows":results,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--author",type=Path,required=True)
    parser.add_argument("--data",type=Path,required=True)
    parser.add_argument("--write",type=Path)
    args=parser.parse_args()
    report=audit(args.root,args.author,args.data)
    raw=(json.dumps(report,sort_keys=True,indent=2)+"\n").encode("utf8")
    if args.write:
        args.write.parent.mkdir(parents=True,exist_ok=True)
        with args.write.open("xb") as f:f.write(raw)
        print("WRITTEN",args.write,sha256(raw).hexdigest())
    else:
        print(json.dumps({
            "status":report["status"],
            "actual_P1_XML_read":
                report["explicit_P1_optin_actual_model_facing_XML_reads"],
            "actual_P1_native_write":
                report["explicit_P1_optin_actual_native_IFC_writes"],
            "matched_real_LLM_pairs":
                report["real_paired_LLM_XML_Python_model_trials"],
        },sort_keys=True))


if __name__=="__main__":
    main()
