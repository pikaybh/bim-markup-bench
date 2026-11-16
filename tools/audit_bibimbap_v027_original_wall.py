"""v0.27 actual original PUBLIC test_19: matched developer D0/I0 native parity.

Separate declarative source-state D0 (with explicitly trusted experimental
source-gated compiler), independent pure-IfcOpenShell Python I0 in a separate
subprocess, native IFC identity/geometry oracle, and ORIGINAL unmodified
author scorer run only after actual outputs are built. No model calls.
All original IFC, author scorer, data, previous reports remain read-only.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

import ifcopenshell
import ifcopenshell.util.unit

from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import XmlSourceEditSession,file_hash
from tools.audit_bibimbap_v026_connected_wall_safety import (
    proposed_complete_connected_wall_xml,exact_declarative_graph_proposal,
)
from src.runtime.connected_wall_delete import (
    PINNED_NORMALIZED_SOURCE_SHA,preflight_original_connected_wall,
    verify_original_connected_wall,
)

ROOT=Path(__file__).resolve().parents[1]
TASK_ID="test_19"
PARENT_V026_REPORTS={
    "reports/bibimbap_v026_original_test19_connected_wall_fail_closed_20261116.json":
        "fe6137a71789bf0d6c55dcf6c62a43a70f86fa5614e5c87faee2894e855ac848",
    "reports/bibimbap_v026_non_docker_284_pass_and_docker_http500_20261116.json":
        "cff946ffde62bb2fe9ff453cd8318933a8edbbe4e10b7b3f5b93ecce7ff64fc1",
}
PARENT_FROZEN_COMMIT="8e3564ca19606d82b0880a279e0fd4c5dbed137d"


class OriginalPublicWallPairAuditBlocked(ValueError):
    pass


def _require(condition:bool, reason:str):
    if not condition:raise OriginalPublicWallPairAuditBlocked(reason)


def original_product_identity_check(
    original:Path,output:Path,target_guid:str,
)->dict:
    """Completely independent original IF C product identity/class oracle."""
    a=ifcopenshell.open(str(original))
    b=ifcopenshell.open(str(output))
    _require(a.schema==b.schema=="IFC4X3", "Original native schema changed")
    _require(abs(ifcopenshell.util.unit.calculate_unit_scale(a)-.001)<1e-12
             and abs(ifcopenshell.util.unit.calculate_unit_scale(b)-.001)<1e-12,
             "Output does not preserve source millimetres")
    original_products={p.GlobalId:p.is_a() for p in a.by_type("IfcProduct")}
    after_products={p.GlobalId:p.is_a() for p in b.by_type("IfcProduct")}
    _require(original_products[target_guid]=="IfcWall",
             "PUBLIC deletion target is not a source Wall")
    _require(after_products=={k:v for k,v in original_products.items()
                             if k!=target_guid},
             "Native candidate changed unrelated original product identities/classes")
    return {
        "status":"INDEPENDENT_ORIGINAL_IFC_PRODUCT_CLASS_AND_GUID_ORACLE_PASS",
        "original_product_count":len(original_products),
        "candidate_product_count":len(after_products),
        "removed_original_native_Product_count":1,
        "all_other_original_native_products_preserved":True,
        "original_schema_and_length_unit_preserved":True,
    }


def _run_independent_i0(
    public_guid:str,original:Path,output:Path,root:Path,
)->dict:
    args=[
        sys.executable,"-m","tools.bibimbap_v027_independent_wall_i0",
        "--source",str(original),"--output",str(output),
    ]
    allow=("SYSTEMROOT","SystemRoot","WINDIR","PATH","TEMP","TMP","VIRTUAL_ENV")
    env={k:os.environ[k] for k in allow if k in os.environ}
    env.update(PYTHONUTF8="1",PYTHONIOENCODING="utf-8")
    try:
        process=subprocess.run(args,input=public_guid+"\n",capture_output=True,
            text=True,encoding="utf8",errors="replace",timeout=35,
            shell=False,cwd=str(root),env=env)
    except subprocess.TimeoutExpired as exc:
        raise OriginalPublicWallPairAuditBlocked("Native independent I0 subprocess timed out") from exc
    _require(process.returncode==0,"Native independent I0 process failed")
    _require(output.is_file(),"Independent I0 did not generate original native IFC")
    try:
        obj=json.loads(process.stdout.strip())
    except (ValueError,TypeError) as exc:
        raise OriginalPublicWallPairAuditBlocked("Independent I0 returned malformed receipt") from exc
    _require(obj.get("status")=="INDEPENDENT_ORIGINAL_NATIVE_CONNECTED_WALL_DELETE"
             and obj.get("original_public_wall_absent")
             and obj.get("native_output_sha256")==file_hash(output),
             "Independent native I0 output receipt is invalid")
    return obj


def audit_real_original_test19(
    root:Path,author:Path,data:Path,
)->dict:
    _require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
             "Original benchmark author/data Git SHA changed")
    for rel,h in PARENT_V026_REPORTS.items():
        _require(file_hash(root/rel)==h,"Frozen v0.26 report drift")
    cases={c["test_id"]:c for c in public_45(author,data)}
    _require(len(cases)==45 and TASK_ID in cases,
             "Original public45 cohort differs")
    case=cases[TASK_ID]
    _require(case["crud"]=="delete" and case["category"]=="basic",
             "Original PUBLIC test19 operation changed")
    src=data/"ifc"/case["original_source_ifc_relpath"]
    sha=file_hash(src)
    _require(sha==case["original_ifc_sha256"],"Actual original input SHA changed")
    public_guids=re.findall(r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",
                            case["public_question"])
    _require(len(public_guids)==1,
             "Original public Wall question no longer contains one GUID")
    _require(ifcopenshell.open(str(src)).by_guid(public_guids[0]).is_a("IfcWall"),
             "Original PUBLIC source target no longer an existing Wall")
    with TemporaryDirectory(prefix="bmb-v027-public19-real-matched-pair-") as td:
        folder=Path(td)
        d=XmlSourceEditSession(src,folder/"D0")
        _require(file_hash(d.normalized)==PINNED_NORMALIZED_SOURCE_SHA,
                 "Native normalized original PUBLIC source SHA changed")
        public_guid,edited=proposed_complete_connected_wall_xml(
            case["public_question"],d.original_xml)
        proposal=exact_declarative_graph_proposal(d,edited)
        plan=preflight_original_connected_wall(d.normalized,public_guid)
        with patch.dict(os.environ,{"BMB_V027_ORIGINAL_CONNECTED_WALL_NATIVE":"1"}):
            receipt=d.call("submit_building_xml",{"xml_text":edited.decode("utf8")})
        _require(receipt.get("status")=="ok"
                 and receipt.get("native_ifc_committed") is True
                 and receipt.get("compile_status")==
                     "COMMITTED_SCOPED_IFC4X3_TOPOLOGY_EDIT"
                 and d.output_ifc is not None and d.output_ifc.is_file(),
                 "Original PUBLIC D0 actual native IFC did not commit")
        # The source-native (metre) IFC produced by the worker gets reopened
        # and FULL original native STEP/root/shape orphan-checked independently
        # by the caller; the child stdout's result is never sufficient proof.
        candidate_m=d.folder/"attempt_01"/"candidate_m.ifc"
        _require(candidate_m.is_file(),
                 "Actual D0 native normalized IFC stage missing")
        survivor_count=verify_original_connected_wall(
            d.normalized,candidate_m,plan)
        iout=folder/"I0_independently_native_original_mm.ifc"
        i0=_run_independent_i0(public_guid,src,iout,root)
        dsha=file_hash(d.output_ifc)
        isha=file_hash(iout)
        _require(dsha==isha==i0["native_output_sha256"],
                 "Original public full serialized D0/I0 IFC bytes not identical")
        independent_D=original_product_identity_check(
            src,d.output_ifc,public_guid)
        independent_I=original_product_identity_check(
            src,iout,public_guid)
        _require(independent_D==independent_I,
                 "Independent original native product identity oracle disagrees")
        score_d=grade_author(author,src,d.output_ifc,TASK_ID)
        score_i=grade_author(author,src,iout,TASK_ID)
        _require(score_d==score_i and score_d["status"]=="AUTHOR_SCORED"
                 and score_d["original_author_score"]==0.5
                 and score_d["original_author_metrics"]==
                     {"integrity_constraint":0.0,"object_not_exists":1.0}
                 and score_d["original_author_full_mark"] is False,
                 "Original author scorer output unexpected")
        _require(file_hash(src)==sha,
                 "Original native source changed by matched candidate generation")
    _require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
             "Original author or data Git revision changed")
    return {
        "status":"V027_ORIGINAL_TEST19_MATCHED_D0_I0_FULL_NATIVE_BYTES_IDENTICAL_SAFE",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/168",
        "original_public_task_id":TASK_ID,
        "frozen_original_public45_denominator":45,
        "original_author_git_sha":AUTHOR_SHA,
        "original_public_data_git_sha":DATA_SHA,
        "frozen_parent_v026_git_commit":PARENT_FROZEN_COMMIT,
        "frozen_v026_previous_reports_sha256":PARENT_V026_REPORTS,
        "original_public_question_sha256":case["public_question_sha256"],
        "original_IFC4X3_mm_source_sha256":sha,
        "normalized_original_public_IFC_sha256":PINNED_NORMALIZED_SOURCE_SHA,
        "original_declarative_XML_proposal":proposal,
        "trusted_model_invisible_v027_native_compiler_opt_in":True,
        "native_child_worker_crash_timeout_isolation":True,
        "original_native_surviving_roots_fully_verified":survivor_count,
        "original_full_STEP_survivor_changes_restricted_to_four_relations_and_one_layer":True,
        "original_target_two_shape_reps_and_placement_deep_cleaned":True,
        "no_new_native_orphan_shape_or_local_placement":True,
        "D0_complete_native_original_mm_IFC_sha256":dsha,
        "I0_complete_native_original_mm_IFC_sha256":isha,
        "original_D0_I0_full_IFC_bytes_equal":True,
        "independent_developer_Python_I0_no_declarative_XML_compiler":True,
        "independent_original_native_IfcProduct_oracle":independent_D,
        "unchanged_original_author_D0":score_d,
        "unchanged_original_author_I0":score_i,
        "original_author_full_mark_achieved":False,
        "prior_frozen_developer_original_native_D0_I0_byte_equal":8,
        "new_cumulative_developer_original_native_D0_I0_byte_equal":9,
        "prior_frozen_original_author_callable_developer_pairs":6,
        "new_cumulative_original_author_callable_developer_pairs":7,
        "other_original_same_protocol_tasks_not_verified":36,
        "historical_original_missing_Window_reference_scorer_cases_unchanged":2,
        "real_model_calls":0,
        "paid_provider_USD":0,
        "real_matching_LLM_XML_vs_Python_causal_performance_proven":False,
        "all45_semantic_source_and_write_access_parity_proven":False,
        "original_author_scorer_or_source_IFC_modified":False,
        "untrusted_native_Wall_mutator_exposed_to_model":False,
        "raw_original_public_target_GUID_or_full_public_question_in_report":False,
    }


def main()->None:
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=ROOT)
    ap.add_argument("--author",type=Path,required=True)
    ap.add_argument("--data",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    opt=ap.parse_args()
    if opt.output.exists() or opt.output.is_symlink():
        ap.error("Refuse overwriting previous original research evidence")
    report=audit_real_original_test19(opt.root,opt.author,opt.data)
    opt.output.parent.mkdir(parents=True,exist_ok=True)
    with opt.output.open("x",encoding="utf8",newline="\n") as fh:
        json.dump(report,fh,ensure_ascii=False,sort_keys=True,indent=2)
        fh.write("\n")
    print("V027_REAL_ORIGINAL19",report["status"])
    print("V027_NATIVE_FULL_IFC_SHA256",report["D0_complete_native_original_mm_IFC_sha256"])
    print("V027_ORIGINAL_AUTHOR_BOTH",report["unchanged_original_author_D0"]["original_author_score"])
    print("V027_DEVELOPER_NATIVE_PARITY_CUMULATIVE",
          report["new_cumulative_developer_original_native_D0_I0_byte_equal"])
    print("V027_MODEL_CALLS",report["real_model_calls"])
    print("V027_REPORT_SHA256",sha256(opt.output.read_bytes()).hexdigest())


if __name__=="__main__":
    main()
