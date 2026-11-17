"""v0.45 original four pinned UPDATE/DELETE real native XML-tool writer audit.

All 4 input IFCs/questions are exact original public sources. All candidates
are DEVELOPER ILLUSTRATIONS intentionally not author-task answers. Independent
native oracle checks physical and original-identity preservation; NO grader,
LLM, hidden GT, paid API or Docker is used.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from collections import Counter

import ifcopenshell
import ifcopenshell.util.placement
from lxml import etree

from tools.bibimbap_matched25_tools import XmlSourceEditSession,file_hash,UnsupportedArm
from tools.bibimbap_matched25_cli import public_45
from tools.audit_bibimbap_v044_original4_native_step_read import original_45
from tools.bibimbap_v045_independent_native_mutation_oracle import (
    verify_original_native_mutation_v045)
from src.runtime.experimental_v44_original_native_step_readonly import PINS,Q
from src.runtime.experimental_v45_original_native_mutations import TASK_OPERATIONS

ROOT=Path(__file__).resolve().parents[1]
ISSUE="https://github.com/pikaybh/bim-markup-bench/issues/205"
PARENT_SHA="cd3d86b0ec30b1876e9072af32de451ee8892a12"
PREVIOUS_V044="dc58535db3dbec85ba610d3e8b9104c660c4bf0e3e019f9a20ee3a32a012281a"


def require(check,reason):
    if not check:raise AssertionError(reason)


def make_illustrative_plan(xml:bytes,tid:str,source:Path)->bytes:
    f=ifcopenshell.open(str(source))
    root=etree.fromstring(xml)
    plan=root[-1]
    require(plan.tag==Q+"NativeEditPlan" and len(plan)==0,
            "Source XML must have an empty independent original mutation plan")
    if tid=="geometry_test_14":
        slab=f.by_type("IfcSlab")[0]
        solid=slab.Representation.Representations[0].Items[0]
        x=round(solid.SweptArea.XDim/1000+.4,6)
        y=round(solid.SweptArea.YDim/1000,6)
        # Deliberately 8.9x10m, NOT original task square.
        require(abs(x-y)>.4,
                "Illustrative Slab candidate must not itself be a square/answer")
        etree.SubElement(plan,Q+"SetSlabRectangleDimensions",{
            "ifcGuid":slab.GlobalId,
            "newXDimM":f"{x:.6f}",
            "newYDimM":f"{y:.6f}",
        })
    elif tid=="geometry_test_15":
        col=sorted(f.by_type("IfcColumn"),key=lambda c:c.GlobalId)[0]
        frame=ifcopenshell.util.placement.get_local_placement(
            col.ObjectPlacement)
        etree.SubElement(plan,Q+"MoveColumnPlacement",{
            "ifcGuid":col.GlobalId,
            "newWorldOriginXM":f"{frame[0,3]/1000+.2:.6f}",
            "newWorldOriginYM":f"{frame[1,3]/1000:.6f}",
        })
    elif tid=="topological_test_11":
        etree.SubElement(plan,Q+"SetAllMappedColumnDepth",{
            "newDepthM":"2.000000",
        })
    elif tid=="topological_test_17":
        obj=sorted(f.by_type("IfcColumn"),key=lambda c:c.GlobalId)[0]
        d=etree.SubElement(plan,Q+"DeleteColumnsByGuid")
        etree.SubElement(d,Q+"DeleteColumn",{"ifcGuid":obj.GlobalId})
    else:
        raise ValueError("Unregistered original task")
    return etree.tostring(root,encoding="utf8",xml_declaration=True,
                          pretty_print=False)


def audit_one(source:Path,tid:str,original_sha:str,question_sha:str,
              trial_folder:Path)->dict:
    require(file_hash(source)==original_sha,"Original published source IFC SHA changed")
    s=XmlSourceEditSession(source,trial_folder,
        experimental_original_native_mutations_v045=True)
    require(s.native_mutation_original_task_id==tid and s.normalized is None
            and s.output_ifc is None
            and not list(s.folder.rglob("*.ifc")),
            "V045 exact original native authoring variant incorrectly initialized")
    names={x["name"]:x for x in s.tools}
    require(set(names)=={"read_building_xml","submit_building_xml"},
            "Actual XML model-facing tools changed")
    current=s.call("read_building_xml",{})
    require(current["status"]=="ok"
            and current["native_candidate_available"] is False
            and current["xml"].encode("utf8")==s.original_xml,
            "Original native full model XML not readable at v045 start")
    before=current["xml"].encode("utf8")
    candidate_xml=make_illustrative_plan(before,tid,source)
    applied=s.call("submit_building_xml",{
        "xml_text":candidate_xml.decode("utf8")})
    require(applied["status"]=="ok"
            and applied["native_ifc_committed"] is True
            and applied["independent_native_oracle_status"]==
                "V045_INDEPENDENT_ORIGINAL_IFC_NATIVE_MUTATION_ORACLE_PASS"
            and applied["original_author_benchmark_task_success_claimed"] is False,
            "Actual XML tool did not get independent original native IFC physical oracle")
    require(s.output_ifc is not None and s.output_ifc.is_file()
            and file_hash(source)==original_sha
            and s.current_xml==candidate_xml,
            "Original source changed or tool failed to commit native candidate")
    native=verify_original_native_mutation_v045(
        source,s.output_ifc,submitted_xml=candidate_xml,
        source_sha=original_sha,task_id=tid)
    require(native["status"]==applied["independent_native_oracle_status"],
            "Independent second source/native candidate oracle disagreed with host")
    prev_sha=file_hash(s.output_ifc)
    wrong_xml=candidate_xml.replace(b"NativeEditPlan",b"OriginalNativeEditSpoof",1)
    fail=s.call("submit_building_xml",{
        "xml_text":wrong_xml.decode("utf8")})
    require(fail["status"]=="error" and
            fail["native_ifc_committed"] is False and
            fail["last_valid_xml_preserved"] is True and
            s.output_ifc.is_file() and file_hash(s.output_ifc)==prev_sha and
            s.current_xml==candidate_xml and
            file_hash(source)==original_sha,
            "Failed second submission erroneously clobbered last verified native IFC")
    return {
        "original_public_task_id":tid,
        "original_public_question_sha256":question_sha,
        "original_public_source_sha256":original_sha,
        "original_native_ifc_schema":"IFC4X3",
        "original_native_length_unit":"millimetres",
        "original_model_visible_v045_read_sha256":sha256(before).hexdigest(),
        "original_model_visible_v045_read_bytes":len(before),
        "original_native_source_visible_complete":True,
        "candidate_xml_sha256":sha256(candidate_xml).hexdigest(),
        "candidate_original_native_mm_ifc_sha256":prev_sha,
        "candidate_native_ifc_bytes":s.output_ifc.stat().st_size,
        "actual_model_tools_verified":sorted(names),
        "illustrative_developer_candidate_is_original_task_answer":False,
        "illustrative_mutation_native_writer_and_independent_oracle_passed":True,
        "success_then_intentionally_corrupt_followup_rejected":True,
        "last_valid_native_IFC_and_XML_preserved_on_error":True,
        "original_source_IFC_byte_sha256_unchanged":True,
        "no_original_author_grader_invoked":True,
        "original_task_semantic_success_proven":False,
        "native_source_oracle":native,
    }


def audit(author:Path,data:Path,*,progress=False)->dict:
    author=Path(author);data=Path(data)
    original_tasks=original_45(author,data)
    require(file_hash(ROOT/"reports"/"bibimbap_v044_original4_native_STEP_readonly_20261117.json")==
            PREVIOUS_V044,"Original previous v044 frozen research report changed")
    rows=[]
    with TemporaryDirectory(prefix="bmb-v045-original4-native-mutation-") as td:
        for index,(_,pin) in enumerate(sorted(PINS.items())):
            tid,crud,qsha,_,_=pin
            t=original_tasks[tid]
            require(t["original_ifc_sha256"] in PINS and
                    t["public_question_sha256"]==qsha and
                    t["crud"]==crud,"Actual original question/source SHA changed")
            file=data/"ifc"/t["original_source_ifc_relpath"]
            row=audit_one(file,tid,t["original_ifc_sha256"],qsha,
                          Path(td)/str(index))
            rows.append(row)
            if progress:
                print("V045_ACTUAL_ORIGINAL_IFC_NATIVE_WRITER_INDEPENDENT_ORACLE_PASS",
                      tid,row["native_source_oracle"]["operation_kind"],
                      row["native_source_oracle"][
                          "exact_target_original_physical_products_actually_changed"],
                      "orig_task_scored",False,flush=True)
    require(len(rows)==4 and
            {r["original_public_task_id"] for r in rows}==
                {pin[0] for pin in PINS.values()},
            "All four original task input IFCs must be paired to typed native source mutations")
    return {
        "status":"V045_ORIGINAL_FOUR_TYPED_XML_NATIVE_MM_IFC_WRITERS_INDEPENDENT_PHYSICAL_ORACLE_PASS",
        "pre_registered_issue":ISSUE,
        "exact_frozen_v044_parent_head":PARENT_SHA,
        "exact_frozen_v044_report_sha256":PREVIOUS_V044,
        "original_public_ITT_task_count":45,
        "original_public_ITT_source_ifc_count":31,
        "original_public_CREATE_count":15,
        "original_public_UPDATE_count":15,
        "original_public_DELETE_count":15,
        "new_v045_exact_original_source_eligible_update_delete_tasks":4,
        "new_v045_source_eligible_true_native_IFC_mutation_and_independent_oracle_pass":4,
        "new_v045_native_original_IFC_result_commit_illustrative":4,
        "new_v045_all_original_native_sources_unchanged":True,
        "new_v045_native_original_task_semantic_answers_proven":0,
        "new_v045_author_grader_calls":0,
        "new_v045_paid_provider_calls":0,
        "new_v045_Docker_runs":0,
        "new_v045_matched_LLM_trials":0,
        "original_developer_D0_I0_task_pairs_CREATE":5,
        "original_full_45_equal_source_info_and_write_authority_proven":False,
        "new_v045_not_default_paid_runner_mode":True,
        "original_score_or_measured_experimental_result_claimed":False,
        "next_priority":"v0.46 full original source information/physical native writer parity on other 27 readable unique sources and robust task-conditioned semantic eligibility, then preregister balanced model trials",
        "rows":rows,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--author",type=Path,required=True)
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--write",type=Path)
    p.add_argument("--progress",action="store_true")
    args=p.parse_args()
    report=audit(args.author,args.data,progress=args.progress)
    raw=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
    if args.write:
        args.write.parent.mkdir(parents=True,exist_ok=True)
        with args.write.open("xb") as stream:
            stream.write(raw)
        print("V045_FROZEN_NATIVE_ORIGINAL4_REPORT",args.write,
              sha256(raw).hexdigest(),flush=True)
    else:
        print(json.dumps({
            "status":report["status"],
            "original_native_IFC_writers":report[
                "new_v045_source_eligible_true_native_IFC_mutation_and_independent_oracle_pass"],
            "original_task_scores":report["new_v045_native_original_task_semantic_answers_proven"],
            "paid_model_trials":report["new_v045_matched_LLM_trials"],
        },sort_keys=True))


if __name__=="__main__":
    main()
