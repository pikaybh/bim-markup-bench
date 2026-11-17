"""v0.46 actual full 27-source / 45-task paged native XML read audit.

Every original source PAGE is returned from the genuine model-facing tool and
independently compared with IfcOpenShell's ORIGINAL native source IFC data.
No hidden GT, original grader, Docker, provider, or native candidate edits.
"""
from __future__ import annotations

from collections import Counter,defaultdict
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse
import json

from lxml import etree

from tools.audit_bibimbap_v043_original45_source_read_parity import original_population
from tools.bibimbap_matched25_tools import XmlSourceEditSession,file_hash
from tools.bibimbap_v046_independent_native_catalog_oracle import (
    verify_native_catalog_046,original_27_sources)
from src.runtime.experimental_v46_original_native_catalog import (
    source_profiles,CATALOGS,PAGE_SIZE)

ROOT=Path(__file__).resolve().parents[1]
PARENT_HEAD="f385ad2ecb9a62a3663d408bc9a998cf5e016f25"
ISSUE="https://github.com/pikaybh/bim-markup-bench/issues/207"
PARENT_REPORT="reports/bibimbap_v045_original4_native_IFC_typed_writers_20261117.json"
PARENT_REPORT_SHA="7d7518f6c65242f7f00066beeb0229fbb6e42e44d5e841243666ac375105c4b3"
OLD_REPORT="reports/bibimbap_v043_original45_native_XML_source_read_parity_20261117.json"
OLD_SHA="eb05633d152b1ff15e4fdd888bb62924b31b126f6cddd05fb23e54fce3ef8dbf"


def require(ok,reason):
    if not ok: raise AssertionError(reason)


def audit_one_original_source(source:Path,sha:str,folder:Path)->dict:
    require(file_hash(source)==sha,"Original public source IFC exact SHA drift")
    session=XmlSourceEditSession(source,folder,
                   experimental_original_native_catalog_v046=True)
    require(session.normalized is None and session.output_ifc is None
            and not list(folder.rglob("*.ifc"))
            and {x["name"] for x in session.tools}==
            {"read_building_xml","read_native_ifc_page","submit_building_xml"},
            "Research model source catalog tool surface not source-only")
    response=session.call("read_building_xml",{})
    require(response["status"]=="ok"
            and response["native_candidate_available"] is False
            and response["xml"].encode("utf8")==session.original_xml,
            "Actual model source did not return its immutable XML")
    xml=response["xml"].encode("utf8")
    root=etree.fromstring(xml)
    counts={node.get("name"):
            (int(node.get("recordCount")),int(node.get("pageCount")))
            for node in root[0]}
    pages={}
    calls=0
    for name in CATALOGS:
        records,numpages=counts[name]
        require(records==len(session.native_catalog_v046.catalog[name])
                and numpages==(records+PAGE_SIZE-1)//PAGE_SIZE,
                "Native original source model page manifest inventory mismatch")
        pages[name]=[]
        for index in range(numpages):
            result=session.call("read_native_ifc_page",{
                "catalog":name,"page":index})
            require(result["status"]=="ok"
                    and result["native_candidate_available"] is False
                    and result["original_source_unchanged"] is True
                    and sha256(result["xml"].encode("utf8")).hexdigest()==
                         result["page_sha256"],
                    "Actual original native page tool source read failed")
            pages[name].append(result["xml"].encode("utf8"))
            calls+=1
    oracle=verify_native_catalog_046(source,sha,xml,pages)
    require(oracle["status"]==
        "V046_INDEPENDENT_ORIGINAL27_FULL_PAGED_NATIVE_SOURCE_ORACLE_PASS"
        and calls==oracle["full_native_source_catalog_page_count"],
        "Independent original native IFC/source page oracle mismatched")
    for payload in (
            response["xml"],
            response["xml"].replace("MILLIMETER","FAKE_METER")):
        failure=session.call("submit_building_xml",{"xml_text":payload})
        require(failure["status"]=="error"
                and failure["error_type"]=="UnsupportedArm"
                and failure["native_ifc_committed"] is False
                and failure["native_candidate_available"] is False
                and failure["last_valid_xml_preserved"] is True
                and failure["original_source_unchanged"] is True,
                "Read-only source catalog must fail every native IFC submit")
    require(session.submissions==2
            and session.output_ifc is None
            and session.current_xml==xml
            and not list(folder.rglob("*.ifc"))
            and not list(folder.glob("attempt_*"))
            and file_hash(source)==sha,
            "Original IFC source or session state changed after read-only test")
    return {
        "source_original_public_IFC_sha256":sha,
        "model_facing_original_native_manifest_sha256":sha256(xml).hexdigest(),
        "model_facing_original_native_manifest_bytes":len(xml),
        "actual_model_facing_page_calls":calls,
        "actual_model_facing_unsupported_native_submits":2,
        "all_8_original_source_catalogs_fully_validated_independently":True,
        "original_input_IFC_unchanged":True,
        "native_candidate_count":0,
        "independent_oracle":oracle,
    }


def audit(author:Path,data:Path,*,progress=False)->dict:
    author,data=Path(author),Path(data)
    require(file_hash(ROOT/PARENT_REPORT)==PARENT_REPORT_SHA
            and file_hash(ROOT/OLD_REPORT)==OLD_SHA,
            "Prior frozen source parity or v0.45 report changed")
    original=original_population(author,data)
    native_profiles=source_profiles()
    need_original=original_27_sources()
    prior=json.loads((ROOT/PARENT_REPORT).read_text(encoding="utf8"))
    original_four={
        row["original_public_source_sha256"] for row in prior["rows"]}
    all31={row["original_ifc_sha256"] for row in original}
    require(len(original_four)==4 and
            set(native_profiles)==set(need_original)==all31-original_four
            and len(all31)==31,
            "Source-pinned 27 must equal exact original31 except v0.44-45 source4")
    by_source=defaultdict(list)
    for task in original:
        by_source[task["original_ifc_sha256"]].append(task)
    source_rows=[]
    with TemporaryDirectory(prefix="bmb-v046-original27-native-catalog-all-pages-") as tmp:
        for index,sha in enumerate(sorted(native_profiles)):
            group=by_source[sha]
            first=group[0]
            source=data/"ifc"/first["original_source_ifc_relpath"]
            row=audit_one_original_source(source,sha,Path(tmp)/str(index))
            row["original_public_task_ids_reusing_source"]=sorted(
                t["test_id"] for t in group)
            row["original_public_task_reference_count"]=len(group)
            row["original_native_IFC_schema"]=native_profiles[sha]["schema"]
            source_rows.append(row)
            if progress:
                o=row["independent_oracle"]
                print("V046_SOURCE_ALL_8_CATALOGS_ALL_PAGES_INDEPENDENT_PASS",
                      index+1,"/27",first["test_id"],
                      "STEP",o["full_source_step_literal_original_line_count"],
                      "PAGES",o["full_native_source_catalog_page_count"],
                      "MAXBYTES",o["largest_model_facing_native_source_page_bytes"],
                      flush=True)
    rows=sorted(({
        "original_public_task_id":t["test_id"],
        "original_public_category":t["category"],
        "original_public_CRUD":t["crud"],
        "original_public_question_sha256":t["public_question_sha256"],
        "original_source_ifc_sha256":t["original_ifc_sha256"],
        "original_v046_native_paged_source_read_available":
            t["original_ifc_sha256"] in native_profiles,
        "original_v045_prior_four_source_not_this_mode":
            t["original_ifc_sha256"] in original_four,
        "original_full_IFC_Python_writer_authority_parity_proven":False,
        "real_XML_vs_Python_LLM_trial":False,
    } for t in original),key=lambda r:r["original_public_task_id"])
    require(len(rows)==45
            and len(source_rows)==27
            and sum(r["original_public_task_reference_count"]
                    for r in source_rows)==41
            and Counter(x["original_public_CRUD"] for x in rows)==
                {"create":15,"update":15,"delete":15}
            and len({x["original_source_ifc_sha256"] for x in rows})==31,
            "Final original public 45/27/31 source research denominators changed")
    total=Counter()
    max_page=0
    for row in source_rows:
        oracle=row["independent_oracle"]
        max_page=max(max_page,oracle["largest_model_facing_native_source_page_bytes"])
        for name in (
            "full_native_source_catalog_page_count",
            "full_source_step_literal_original_line_count",
            "original_native_root_GUIDs",
            "original_native_product_GUIDs",
            "original_native_relation_GUIDs_endpoint_lists",
            "original_native_property_sets_named_values",
            "original_native_materials_original_names",
            "original_native_local_placement_matrices",
            "original_native_product_geometry_digests_or_explicit_unavailable",
            "original_native_products_with_computed_physical_world_mesh",
            "original_native_products_with_explicit_unavailable_world_geometry",
            "original_native_products_without_original_representation",
        ):
            total[name]+=oracle[name]
    require(0<max_page<300000
            and total["full_source_step_literal_original_line_count"]>20000
            and total["original_native_relation_GUIDs_endpoint_lists"]>1500,
            "Original 27 all-source PAGE coverage or tool limit invalid")
    require(file_hash(ROOT/PARENT_REPORT)==PARENT_REPORT_SHA
            and file_hash(ROOT/OLD_REPORT)==OLD_SHA,
            "Prior v0.43/v0.45 frozen reports changed during original27 audit")
    return {
        "status":"V046_ORIGINAL27_FULL_SOURCE_IFC_PAGED_METADATA_AND_STEP_MODEL_READ_INDEPENDENT_PASS",
        "issue_url":ISSUE,
        "stacked_parent_v045_exact_SHA":PARENT_HEAD,
        "frozen_prior_v045_report_sha256":PARENT_REPORT_SHA,
        "frozen_prior_original45_v043_report_sha256":OLD_SHA,
        "original_public_ITT_tasks":45,
        "original_public_CREATE_tasks":15,
        "original_public_UPDATE_tasks":15,
        "original_public_DELETE_tasks":15,
        "original_unique_source_IFC_count":31,
        "original_unique_v046_source_categorized_IFC_count":27,
        "original45_task_rows_with_v046_source_read_available":41,
        "original45_task_rows_with_prior_v045_source_read_available":4,
        "source_original_8_catalog_page_kinds":list(CATALOGS),
        "original27_all_IFC_native_STEP_entity_source_text_available_on_demand":True,
        "original27_all_root_product_relationship_pset_material_placement_physical_digest_available_on_demand":True,
        "source_paged_model_tool_max_result_size_bytes":max_page,
        "total_actual_model_facing_original_IFC_page_reads":sum(
            row["actual_model_facing_page_calls"] for row in source_rows),
        "total_fail_closed_model_facing_native_edit_submissions":54,
        "total_original_native_IFC_candidate_files":0,
        "totals_across_27_unique_original_sources":dict(sorted(total.items())),
        "new_native_IFC_writer_authority_in_v046":False,
        "full_original45_equal_information_and_native_edit_authority_proven":False,
        "full_Python_IfcOpenShell_executable_model_interface_parity_proven":False,
        "same_model_initial_context_size_and_token_budget_proven":False,
        "default_paid_provider_runner_automatically_enables_v046":False,
        "previous_original_CREATE_task_specific_D0_I0_developer_pairs":5,
        "new_original_CREATE_task_specific_D0_I0_developer_pairs":0,
        "original_author_evaluator_calls":0,
        "paid_provider_calls":0,
        "Docker_executions":0,
        "real_original_XML_vs_Python_matched_LLM_trials":0,
        "original_public_task_IFCs_questions_and_author_grader_unchanged":True,
        "research_main_and_BIXML_Xim_unchanged":True,
        "next_priority":"Equalize original task-conditioned native edits and Python paged queries; prespecify a balanced subset or clearly labeled unequal tool-bundle benchmark; no scoring claims yet",
        "original_27_unique_source_results":source_rows,
        "original_45_per_task_provenance":rows,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--author",type=Path,required=True)
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--write",type=Path)
    p.add_argument("--progress",action="store_true")
    args=p.parse_args()
    report=audit(args.author,args.data,progress=args.progress)
    raw=(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf8")
    if args.write:
        args.write.parent.mkdir(parents=True,exist_ok=True)
        with args.write.open("xb") as f:f.write(raw)
        print("V046_FROZEN_ORIGINAL27_FULL_IFC_PAGED_SOURCE_REPORT",
              args.write,sha256(raw).hexdigest(),flush=True)
    else:
        print(json.dumps({"status":report["status"],
            "full27_source_valid":report["original_unique_v046_source_categorized_IFC_count"],
            "pages":report["total_actual_model_facing_original_IFC_page_reads"],
            "native_mutations":0,"matched_LLM_trials":0},sort_keys=True))


if __name__=="__main__":
    main()
