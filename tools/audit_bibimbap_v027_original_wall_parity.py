"""v0.27 real original PUBLIC test_19 source-only D0/I0 native IFC audit.

The independently pinned public original IFC and question identify one connected
Wall. D0 submits one complete declarative XML document (1 Wall + 2 Connects
removed), and trusted compiled IFC work is isolated in a crash-supervised
one-shot native child. Separately authored I0 uses its own native Python
IfcOpenShell program and never imports D0 XML/compiler/child. The untouched
original author scorer is only called *after* both independent IFC outputs
exist. No model, network, provider spending or hidden target use.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import re

import ifcopenshell
import ifcopenshell.util.unit

from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import XmlSourceEditSession,file_hash
from tools.audit_bibimbap_v026_connected_wall_safety import (
    proposed_complete_connected_wall_xml,
    exact_declarative_graph_proposal,
)
from tools.bibimbap_v027_independent_connected_wall_i0 import (
    independent_original_connected_wall_i0,
)
from src.runtime.connected_wall_delete import (
    PINNED_NORMALIZED_ORIGINAL_IFC_SHA,
    preflight_original_connected_wall,verify_original_connected_wall,
)

ROOT=Path(__file__).resolve().parents[1]
TASK_ID="test_19"
FROZEN_PRIOR_REPORTS={
    "reports/bibimbap_v024_original_test18_opening_window_D0_I0_20261115.json":
      "a31e74dacdece9924304de6c74c5d9e8769497a8ad68287779ddd4a37bac6a67",
    "reports/bibimbap_v025_original_test17_door_opening_D0_I0_20261115.json":
      "4ea264519d011288acf6d059fc15b3ca49aa7d4d21315ccb5cbebe5bb17f3f4a",
    "reports/bibimbap_v026_original_test19_connected_wall_fail_closed_20261116.json":
      "fe6137a71789bf0d6c55dcf6c62a43a70f86fa5614e5c87faee2894e855ac848",
    "reports/bibimbap_v026_non_docker_284_pass_and_docker_http500_20261116.json":
      "cff946ffde62bb2fe9ff453cd8318933a8edbbe4e10b7b3f5b93ecce7ff64fc1",
}


class OriginalConnectedWallParityBlocked(ValueError):
    pass


def require(value,reason):
    if not value:
        raise OriginalConnectedWallParityBlocked(reason)


def independent_original_public_native_oracle(
    source:Path,result:Path,wall_guid:str,
)->dict:
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(result))
    require(a.schema==b.schema=="IFC4X3"
            and abs(ifcopenshell.util.unit.calculate_unit_scale(a)-.001)<1e-12
            and abs(ifcopenshell.util.unit.calculate_unit_scale(b)-.001)<1e-12,
            "Real original IFC schema or millimetre unit drift")
    prior={x.GlobalId:x.is_a() for x in a.by_type("IfcProduct")}
    later={x.GlobalId:x.is_a() for x in b.by_type("IfcProduct")}
    require(prior.get(wall_guid)=="IfcWall"
            and later=={k:v for k,v in prior.items() if k!=wall_guid},
            "Original unrelated IFC Product GUID or class changed")
    baseline_orphans={
        cls:sum(a.get_total_inverses(x)==0 for x in a.by_type(cls))
        for cls in ("IfcShapeRepresentation","IfcProductDefinitionShape","IfcLocalPlacement")
    }
    result_orphans={
        cls:sum(b.get_total_inverses(x)==0 for x in b.by_type(cls))
        for cls in baseline_orphans
    }
    require(baseline_orphans==result_orphans,
            "Original IFC gained orphaned shape/placement")
    source_wall=a.by_guid(wall_guid)
    original_neighbor_guids={
        x.RelatingElement.GlobalId
        for x in a.get_inverse(source_wall)
        if x.is_a("IfcRelConnectsPathElements")
    }
    require(len(original_neighbor_guids)==2,"Original Wall path-neighbor count changed")
    for neighbor in original_neighbor_guids:
        obj=b.by_guid(neighbor)
        require(obj.is_a("IfcWall"),"Original surviving neighbor Wall class changed")
        require(not any(
            rel.RelatingElement.GlobalId==wall_guid or
            rel.RelatedElement.GlobalId==wall_guid
            for rel in b.get_inverse(obj)
            if rel.is_a("IfcRelConnectsPathElements")
        ),"Dangling deleted Wall connection remains")
    return {
        "status":"ORIGINAL_NATIVE_PRODUCT_CLASS_IDENTITY_AND_NEIGHBOR_PATHS_PASS",
        "original_IfcProducts":len(prior),
        "result_IfcProducts":len(later),
        "original_connected_wall_absent":True,
        "every_remaining_original_product_GUID_and_class_preserved":True,
        "original_neighbour_walls_preserved":len(original_neighbor_guids),
        "original_and_after_orphaned_geometries":baseline_orphans,
    }


def audit_original19_native_pair(root:Path,author:Path,data:Path)->dict:
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Pinned original benchmark author/data changed")
    for rel,hash_ in FROZEN_PRIOR_REPORTS.items():
        require(file_hash(root/rel)==hash_,"Frozen previous original source result changed")
    tasks={x["test_id"]:x for x in public_45(author,data)}
    require(len(tasks)==45 and TASK_ID in tasks,
            "Original public benchmark 45-task denominator drift")
    case=tasks[TASK_ID]
    require(case["crud"]=="delete" and case["category"]=="basic",
            "Public task19 operation classification drift")
    source=data/"ifc"/case["original_source_ifc_relpath"]
    sh=file_hash(source)
    require(sh==case["original_ifc_sha256"],"Original public IFC source SHA drift")
    original=ifcopenshell.open(str(source))
    public_guid=re.findall(
        r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",
        case["public_question"])
    require(len(public_guid)==1 and original.by_guid(public_guid[0]).is_a("IfcWall"),
            "Actual PUBLIC original Wall GUID absent/ambiguous")
    with TemporaryDirectory(prefix="bmb-v027-original19-paired-") as td:
        folder=Path(td)
        d=XmlSourceEditSession(source,folder/"D0")
        require(file_hash(d.normalized)==PINNED_NORMALIZED_ORIGINAL_IFC_SHA,
                "Original IFC normalized native source changed")
        wall_guid,changed=proposed_complete_connected_wall_xml(
            case["public_question"],d.original_xml)
        graph=exact_declarative_graph_proposal(d,changed)
        require(wall_guid==public_guid[0],"Original public wall target drift")
        plan=preflight_original_connected_wall(
            ifcopenshell.open(str(d.normalized)),wall_guid)
        receipt=d.call("submit_building_xml",{
            "xml_text":changed.decode("utf8"),
        })
        require(receipt.get("status")=="ok"
                and receipt.get("native_ifc_committed") is True
                and receipt.get("compile_status")=="COMMITTED_SCOPED_IFC4X3_WALL_EDIT"
                and d.output_ifc is not None and d.output_ifc.is_file(),
                "Supervised D0 full XML original Wall output not committed")
        new_model=ifcopenshell.open(str(d.normalized))
        metric_ifc=d.folder/"attempt_01"/"candidate_m.ifc"
        # XmlSourceEditSession owns a native metres commit on the way to
        # original millimetres output; compare its *complete* Root/STEP state.
        # The ephemeral session owns all generated files.
        require(metric_ifc.is_file(),"Native D0 staged metres result missing")
        native_check=verify_original_connected_wall(
            new_model,ifcopenshell.open(str(metric_ifc)),plan)
        i0path=folder/"I0_native_original_mm.ifc"
        independent=independent_original_connected_wall_i0(
            source,wall_guid,i0path)
        require(independent["status"]==
            "INDEPENDENT_DEVELOPER_ORIGINAL_CONNECTED_WALL_I0_NATIVE_OUTPUT"
            and independent["original_public_Wall_absent"]
            and independent["remaining_original_IfcProduct_count"]==42,
            "Native developer-only imperative I0 baseline failed")
        dsha=file_hash(d.output_ifc);isha=file_hash(i0path)
        require(dsha==isha and isha==independent["candidate_sha256"],
                "Paired complete original IFC output bytes differ")
        native_d=independent_original_public_native_oracle(
            source,d.output_ifc,wall_guid)
        native_i=independent_original_public_native_oracle(
            source,i0path,wall_guid)
        require(native_d==native_i,"Independent output oracles D0/I0 differ")
        grade_d=grade_author(author,source,d.output_ifc,TASK_ID)
        grade_i=grade_author(author,source,i0path,TASK_ID)
        require(grade_d==grade_i and grade_d["status"]=="AUTHOR_SCORED"
                and grade_d["original_author_score"]==0.5
                and grade_d["original_author_metrics"]==
                    {"object_not_exists":1.0,"integrity_constraint":0.0}
                and grade_d["original_author_full_mark"] is False,
                "Unmodified original author grade not reproducible")
        require(file_hash(source)==sh,"Original public source changed by paired run")
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Original author/data revisions drifted during native audit")
    return {
        "status":"ACTUAL_ORIGINAL_TEST19_CRASH_ISOLATED_D0_I0_FULL_NATIVE_BYTES_IDENTICAL",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/169",
        "original_task_id":TASK_ID,
        "original_public_intention_to_test_denominator":45,
        "original_author_pinned_git_sha":AUTHOR_SHA,
        "original_data_pinned_git_sha":DATA_SHA,
        "original_public_question_sha256":case["public_question_sha256"],
        "original_native_IFC_sha256":sh,
        "original_normalized_IFC_SHA256":PINNED_NORMALIZED_ORIGINAL_IFC_SHA,
        "frozen_v024_v025_v026_evidence_sha256":FROZEN_PRIOR_REPORTS,
        "declarative_full_XML_removed_original_wall_and_two_connections":graph,
        "D0_native_child_process_supervised_with_timeout_and_crash_fail_closed":True,
        "D0_native_child_parent_root_STEP_physical_and_full_XML_graph_validated":True,
        "D0_new_original_native_entire_IFC_SHA256":dsha,
        "I0_independent_original_native_entire_IFC_SHA256":isha,
        "D0_I0_entire_IFC_bytes_identical":True,
        "original_source_IfcProduct_native_oracle":native_d,
        "original_native_IFC_untouched_root_count":native_check,
        "unchanged_original_author_D0_score":grade_d,
        "unchanged_original_author_I0_score":grade_i,
        "unchanged_original_author_full_mark":False,
        "v026_inadmissible_native_wall_diagnostic_still_historical_not_paired":True,
        "previous_actual_developer_original_D0_I0_native_byte_equal":8,
        "new_cumulative_developer_original_D0_I0_native_byte_equal":9,
        "previous_original_author_callable_developer_pairs":6,
        "new_cumulative_original_author_callable_developer_pairs":7,
        "other_original_public_original45_cases_not_paired_under_same_protocol":36,
        "older_original_author_missing_Window_reference_cases_unmodified":2,
        "real_model_LLM_calls":0,
        "provider_paid_USD":0,
        "original_IFC2X3_or_IFC4_XML_write_supported_here":False,
        "full_original45_source_information_write_and_feedback_parity_proven":False,
        "actual_causal_XML_Python_LLM_performance_comparison":False,
        "original_source_scorer_or_frozen_reports_modified":False,
        "public_original_target_GUID_or_full_question_or_hidden_answers_in_report":False,
    }


def main()->None:
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--root",type=Path,default=ROOT)
    a.add_argument("--author",type=Path,required=True)
    a.add_argument("--data",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True)
    p=a.parse_args()
    if p.output.exists() or p.output.is_symlink():
        a.error("Refusing to overwrite frozen evidence")
    report=audit_original19_native_pair(p.root,p.author,p.data)
    p.output.parent.mkdir(parents=True,exist_ok=True)
    with p.output.open("x",encoding="utf8",newline="\n") as fp:
        json.dump(report,fp,ensure_ascii=False,sort_keys=True,indent=2)
        fp.write("\n")
    print("V027_ORIGINAL19",report["status"])
    print("V027_BOTH_FULL_NATIVE_SHA",report["D0_new_original_native_entire_IFC_SHA256"])
    print("V027_UNCHANGED_ORIGINAL_AUTHOR",report["unchanged_original_author_D0_score"]["original_author_score"])
    print("V027_ACTUAL_DEVELOPER_PAIRED_COUNT",report["new_cumulative_developer_original_D0_I0_native_byte_equal"])
    print("V027_REPORT_SHA256",sha256(p.output.read_bytes()).hexdigest())


if __name__=="__main__":main()
