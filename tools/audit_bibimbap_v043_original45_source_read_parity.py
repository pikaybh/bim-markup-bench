"""v0.43 original 45-task native IFC versus ACTUAL model-facing XML source audit.

This is a forensic, read-only information audit. It never calls the original
benchmark grader, does not expose hidden GT, never invokes provider/Docker,
and never declares same-GUID visibility as complete IFC information parity.

Use genuine XmlSourceEditSession.read_building_xml in per-source scratch
directories and genuine ifcopenshell.open(original source IFC) on exactly the
original-public native IFC bytes. Explicit v0.38-v0.42 features are audited
separately from the unmodified default published runner.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
from typing import Any

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import (
    XmlSourceEditSession, UnsupportedArm, file_hash)
from src.runtime.experimental_v39_complex_overlay import PINS as COMPLEX_PINS
from src.runtime.experimental_v40_native_room_evidence import PINS as ROOM_PINS
from src.runtime.experimental_v41_p3_column_slab import PINS as P3_PINS
from src.runtime.experimental_v42_native_slab_readonly import PINS as SLAB_PINS

ROOT=Path(__file__).resolve().parents[1]
ISSUE="https://github.com/pikaybh/bim-markup-bench/issues/201"
PARENT_SHA="32925c0cccce17b5a14c7ba904e04b195dc40d16"
PARENT_REPORT=(
    "reports/bibimbap_v042_original_P3_source_native_slab_readonly_reproducible_20261117.json",
    "f883dfb095746ceebbaa9f718e5355c61dbb2a356387b7882b400036cdf1b20e"
)
# The entire original 45 CSV is pinned, not just known sampled question hashes.
# This prevents CSV question edits from passing just because its Git HEAD stayed the same.
QUESTION_CSV_SHA="21c07f08c923cdb748255d7960535bab05e2887e4d093d64f87f76ff6d6d100b"
ORIGINAL_IFC_FILE_HASH_COUNT=31
XML_GUID_RE=re.compile(r"^[0-9A-Za-z_$]{22}$")
SOURCE_XML_ELEMENTS={"Level","Wall","Slab","Column","Space","Door","Window",
                     "Opening","NativeSpace","NativeSlab","Product"}
PROPERTY_TAGS={"Property","PropertySet","IfcPropertySet","IfcPropertySingleValue",
               "PropertyDefinition","Pset","PsetProperty"}
MATERIAL_TAGS={"Material","IfcMaterial","MaterialLayer","MaterialProfile",
               "MaterialAssociation"}
SOURCE_RELS=("IfcRelContainedInSpatialStructure","IfcRelAggregates",
             "IfcRelVoidsElement","IfcRelFillsElement",
             "IfcRelDefinesByProperties","IfcRelAssociatesMaterial")


class ParityAuditError(ValueError):
    pass


def require(value:bool,message:str)->None:
    if not value: raise ParityAuditError(message)


def _git_clean(p:Path)->bool:
    proc=subprocess.run(
        ["git","-C",str(p),"status","--porcelain"],
        capture_output=True,text=True,check=True)
    return not proc.stdout.strip()


def original_population(author:Path,data:Path)->list[dict]:
    author,data=Path(author),Path(data)
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Original BIBIMBAP author/data immutable HEAD drift")
    require(_git_clean(author) and _git_clean(data),
            "Original author/data dirty; refuse source parity audit")
    csv=data/"prompts"/"all_questions.csv"
    require(csv.is_file() and not csv.is_symlink()
            and file_hash(csv)==QUESTION_CSV_SHA,
            "Original public question CSV SHA changed from preregistered source")
    require(file_hash(ROOT/PARENT_REPORT[0])==PARENT_REPORT[1],
            "v0.42 previous reproducible frozen report byte SHA changed")
    cohort=public_45(author,data)
    require(len(cohort)==45 and len({t["test_id"] for t in cohort})==45
            and Counter(t["crud"] for t in cohort)==
                {"create":15,"update":15,"delete":15}
            and Counter(t["category"] for t in cohort)==
                {"basic":15,"geometry":15,"topological":15}
            and len({t["original_ifc_sha256"] for t in cohort})==
                ORIGINAL_IFC_FILE_HASH_COUNT,
            "Original 45/15 ITT or original unique public IFC population changed")
    for t in cohort:
        path=Path(t["original_source_ifc_relpath"])
        allowed=(data/"ifc").resolve()
        require(not path.is_absolute()
                and (data/"ifc"/path).resolve().is_relative_to(allowed)
                and not (data/"ifc"/path).is_symlink()
                and file_hash(data/"ifc"/path)==t["original_ifc_sha256"],
                "Original public source IFC immutable path/file SHA drift")
    return sorted(cohort,key=lambda x:x["test_id"])


def _native(model)->dict:
    """Independent Python IfcOpenShell OPEN observable source; no author evaluator."""
    products={x.GlobalId:x for x in model.by_type("IfcProduct")}
    elements={x.GlobalId:x for x in model.by_type("IfcElement")}
    rels={x.GlobalId:x for x in model.by_type("IfcRelationship")}
    roots={x.GlobalId:x for x in model.by_type("IfcRoot")}
    require(len(products)==len(model.by_type("IfcProduct"))
            and len(rels)==len(model.by_type("IfcRelationship"))
            and len(roots)==len(model.by_type("IfcRoot")),
            "Original native IFC Root/product/relation GUID collision detected")
    pset=model.by_type("IfcPropertySet")
    mats=model.by_type("IfcMaterial")
    typ_rel=model.by_type("IfcRelDefinesByType")
    mrels=model.by_type("IfcRelAssociatesMaterial")
    prels=model.by_type("IfcRelDefinesByProperties")
    properties=model.by_type("IfcProperty")
    placements=model.by_type("IfcLocalPlacement")
    body=[x for x in products.values() if x.Representation is not None]
    return {
        "schema":model.schema,
        "unit_to_metres":ifcopenshell.util.unit.calculate_unit_scale(model),
        "root_guids":roots,
        "product_guids":products,
        "element_guids":elements,
        "relationship_guids":rels,
        "native_product_class_counts":dict(sorted(Counter(x.is_a() for x in products.values()).items())),
        "native_relationship_class_counts":dict(sorted(Counter(x.is_a() for x in rels.values()).items())),
        "native_ifc_products_count":len(products),
        "native_ifc_element_count":len(elements),
        "native_ifc_root_count":len(roots),
        "native_ifc_relationship_count":len(rels),
        "native_ifc_ifc_property_set_count":len(pset),
        "native_ifc_property_count":len(properties),
        "native_ifc_property_set_definition_relation_count":len(prels),
        "native_ifc_material_count":len(mats),
        "native_ifc_material_association_count":len(mrels),
        "native_ifc_type_definition_relation_count":len(typ_rel),
        "native_ifc_local_placement_count":len(placements),
        "native_ifc_products_with_object_placement_count":sum(
            x.ObjectPlacement is not None for x in products.values()),
        "native_ifc_products_with_geometric_representation_count":len(body),
        "native_ifc_source_properties_IfcRelDefinesByProperties":len(prels),
        "native_ifc_source_material_association_IfcRelAssociatesMaterial":len(mrels),
        "native_ifc_explicit_spatial_relationships":sum(
            1 for r in rels.values() if r.is_a() in SOURCE_RELS),
        "native_ifc_property_set_names":sorted({str(x.Name) for x in pset if x.Name}),
        "native_ifc_material_names":sorted({str(x.Name) for x in mats if x.Name}),
        "native_ifc_all_root_relation_guids":sorted(rels),
        "native_ifc_all_product_guids":sorted(products),
        "native_ifc_all_element_guids":sorted(elements),
        "native_ifc_ifc_slab_guids":sorted(x.GlobalId for x in model.by_type("IfcSlab")),
        "native_ifc_ifc_space_guids":sorted(x.GlobalId for x in model.by_type("IfcSpace")),
    }


def source_native_summary(file:Path,expected_sha:str)->tuple[dict,dict]:
    file=Path(file)
    require(file.is_file() and not file.is_symlink()
            and file_hash(file)==expected_sha,
            "Source original immutable IFC bytes changed")
    model=ifcopenshell.open(str(file))
    n=_native(model)
    require(model.schema in ("IFC2X3","IFC4","IFC4X3")
            and abs(n["unit_to_metres"]-.001)<1e-12,
            "Original IFC schema or native-mm units not accepted")
    # Store data only as bounded summary, no original task prompt or GT.
    printable={
        k:v for k,v in n.items()
        if k not in (
            "root_guids","product_guids","element_guids","relationship_guids",
            "native_ifc_all_root_relation_guids","native_ifc_all_product_guids",
            "native_ifc_all_element_guids","native_ifc_ifc_slab_guids",
            "native_ifc_ifc_space_guids","native_ifc_property_set_names",
            "native_ifc_material_names")}
    printable["native_original_distinct_property_set_names_count"]=len(
        n["native_ifc_property_set_names"])
    printable["native_original_distinct_material_names_count"]=len(
        n["native_ifc_material_names"])
    printable["native_IfcSlab_count"]=len(n["native_ifc_ifc_slab_guids"])
    printable["native_IfcSpace_count"]=len(n["native_ifc_ifc_space_guids"])
    printable["native_original_ifc_file_sha256"]=expected_sha
    require(file_hash(file)==expected_sha,
            "Original native IFC mutated during forensic inventory")
    return printable,n


def optin_for_source(tid:str,source_sha:str,crud:str)->dict:
    """Only preregistered ORIGINAL CREATE source-specific safe experimental reads."""
    if crud!="create":
        return {}
    if source_sha in SLAB_PINS and tid==SLAB_PINS[source_sha][0]:
        return {"experimental_original_native_slab_v042":True}
    if source_sha in ROOM_PINS and tid==ROOM_PINS[source_sha][0]:
        return {"experimental_original_room_v040":True}
    if source_sha in COMPLEX_PINS and tid==COMPLEX_PINS[source_sha][0]:
        return {"experimental_original_complex_v039":True}
    if source_sha in P3_PINS and tid==P3_PINS[source_sha][0]:
        return {"experimental_original_p3_v041":True}
    from tools.bibimbap_v038_legacy_live_gate import SOURCE_PROFILES as LEGACY_PINS
    if source_sha in LEGACY_PINS:
        return {"experimental_original_legacy_v08":True}
    return {}


def _loc(tag:str)->str:
    return etree.QName(tag).localname


def model_visible_summary(xml:bytes,n:dict,*,required_xml_read:bool)->dict:
    """Read *actual bytes returned to the model*, not an imagined IFC equivalent."""
    require(isinstance(xml,bytes) and 0<len(xml)<=300000,
            "Claimed XML source read is missing, oversized or not bytes")
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True)
    doc=etree.fromstring(xml,parser)
    require(_loc(doc.tag)=="Building","Actual read XML must be Building")
    source_products=set(n["product_guids"])
    source_elements=set(n["element_guids"])
    source_rel=set(n["relationship_guids"])
    native_roots=set(n["root_guids"])
    mentioned_source_roots=set()
    attrs_by_guid=defaultdict(set)
    element_nodes=defaultdict(list)
    tags=set()
    for x in doc.iter():
        if not isinstance(x.tag,str): continue
        tag=_loc(x.tag)
        tags.add(tag)
        for key,value in x.attrib.items():
            local_key=_loc(key)
            if (local_key in ("ifcGuid","sourceGuid","relationGuid")
                    and XML_GUID_RE.fullmatch(value)
                    and value not in native_roots):
                raise ParityAuditError(
                    "Actual source XML contains invented or unpinned original IFC GUID")
            if value in native_roots:
                mentioned_source_roots.add(value)
                attrs_by_guid[value].add(local_key)
        for key in ("ifcGuid","sourceGuid"):
            value=x.get(key)
            if value in source_products:
                element_nodes[value].append(tag)
    # IfcRel GUIDs can legitimately appear as `ifcGuid` in v0.39
    # and as `relationGuid` in v0.40/v0.42; count only SOURCE IFC GUIDs.
    visible_product=set(mentioned_source_roots)&source_products
    visible_element=set(mentioned_source_roots)&source_elements
    visible_rel=set(mentioned_source_roots)&source_rel
    property_names=[x for x in n["native_ifc_property_set_names"]
                    if x.encode("utf8") in xml]
    material_names=[x for x in n["native_ifc_material_names"]
                    if x.encode("utf8") in xml]
    missing_product=source_products-visible_product
    missing_element=source_elements-visible_element
    missing_rel=source_rel-visible_rel
    mismatches=[]
    for guid,nodes in element_nodes.items():
        native_type=n["product_guids"][guid].is_a()
        for tag in nodes:
            # Generic v0.39 Product is an opaque reference, NOT a claim
            # that an IFC entity is of concrete class `IfcProduct`.
            if tag=="Product":
                continue
            expected={
                "Level":"IfcBuildingStorey",
                "NativeSpace":"IfcSpace",
                "NativeSlab":"IfcSlab",
            }.get(tag,"Ifc"+tag)
            if tag in SOURCE_XML_ELEMENTS and expected!=native_type:
                mismatches.append({
                    "nativeIfcClass":native_type,"xmlTag":tag,
                    "native_source_guid":guid})
    # Semantically important: if there are original property-set/material
    # *links* not represented by source identity, all-IFC parity has failed.
    gap=bool(missing_product or missing_rel
        or (n["native_ifc_ifc_property_set_count"] and not property_names)
        or (n["native_ifc_material_count"] and not material_names)
        or mismatches)
    require(not any(r not in native_roots for r in mentioned_source_roots),
            "Unexpected model-visible source GUID not in original source")
    return {
        "status":"ACTUAL_MODEL_TOOL_XML_READ_OK",
        "xml_bytes_sha256":sha256(xml).hexdigest(),
        "xml_bytes_count":len(xml),
        "xml_visible_element_tag_counts":dict(sorted(Counter(
            _loc(e.tag) for e in doc.iter() if isinstance(e.tag,str)
            and _loc(e.tag) in SOURCE_XML_ELEMENTS).items())),
        "xml_has_dedicated_native_property_tags":bool(tags&PROPERTY_TAGS),
        "xml_has_dedicated_native_material_tags":bool(tags&MATERIAL_TAGS),
        "original_native_IFC_property_set_names_visible_by_exact_text_count":len(property_names),
        "original_native_IFC_material_names_visible_by_exact_text_count":len(material_names),
        "source_native_ifc_product_guid_seen_count":len(visible_product),
        "source_native_ifc_product_guid_unseen_count":len(missing_product),
        "source_native_ifc_element_guid_seen_count":len(visible_element),
        "source_native_ifc_element_guid_unseen_count":len(missing_element),
        "source_native_ifc_relationship_guid_seen_count":len(visible_rel),
        "source_native_ifc_relationship_guid_unseen_count":len(missing_rel),
        "source_native_ifc_product_guid_missing_examples":sorted(missing_product)[:8],
        "source_native_ifc_element_class_unseen_counts":dict(sorted(Counter(
            n["element_guids"][g].is_a() for g in missing_element).items())),
        "source_native_ifc_relation_type_unseen_counts":dict(sorted(Counter(
            n["relationship_guids"][g].is_a() for g in missing_rel).items())),
        "source_native_ifc_relation_guid_missing_examples":sorted(missing_rel)[:8],
        "source_product_xml_tag_vs_native_class_mismatch_examples":mismatches[:8],
        "source_identity_visibility_alone_is_full_IFC_information_parity":False,
        "demonstrated_missing_read_information":gap,
        "full_original_native_IFC_source_information_parity_confirmed":False,
        "source_ifc_local_placement_expressions_losslessly_equivalent_proven":False,
        "source_ifc_native_solid_geometry_representation_losslessly_equivalent_proven":False,
        "native_ifc_existing_objects_editable_via_XML_safely_parity_proven":False,
    }


def audit_model_read(original:Path,source_sha:str,n:dict,
                     folder:Path,*,flags:dict|None=None)->dict:
    flags=flags or {}
    try:
        session=XmlSourceEditSession(original,folder,**flags)
    except UnsupportedArm as exc:
        return {
            "status":"UNSUPPORTED_BACKEND_NOT_MODEL_FAILURE",
            "exception_class":type(exc).__name__,
            "reason":str(exc)[:128],
            "model_tool_xml_read_available":False,
            "full_original_native_IFC_source_information_parity_confirmed":False,
        }
    except Exception as exc:
        return {
            "status":"BACKEND_SETUP_ERROR_NOT_MODEL_FAILURE",
            "exception_class":type(exc).__name__,
            "reason":str(exc)[:128],
            "model_tool_xml_read_available":False,
            "full_original_native_IFC_source_information_parity_confirmed":False,
        }
    require({x["name"] for x in session.tools}==
            {"read_building_xml","submit_building_xml"},
            "Audited actual model-visible tool surface changed unexpectedly")
    result=session.call("read_building_xml",{})
    require(result["status"]=="ok"
            and result.get("xml")==session.original_xml.decode("utf8")
            and result.get("native_candidate_available") is False,
            "Reported original model-facing XML read is not from genuine actual tool")
    require(file_hash(original)==source_sha,
            "Native original source file changed during actual read")
    row=model_visible_summary(result["xml"].encode("utf8"),n,
                              required_xml_read=True)
    row["model_tool_xml_read_available"]=True
    row["explicit_research_optin_flag"]=next(iter(flags),"none")
    row["runtime_original_public_paid_runner_explicit_optin_enabled"]=False
    row["original_ifc_file_unchanged"]=True
    return row


def audit(author:Path,data:Path,*,progress:bool=False)->dict:
    author,data=Path(author),Path(data)
    cohort=original_population(author,data)
    by_source=defaultdict(list)
    for t in cohort:
        by_source[t["original_ifc_sha256"]].append(t)
    require(len(by_source)==31,"Original source unique file count changed")
    source_rows=[]
    task_rows=[]
    with TemporaryDirectory(prefix="bmb-v043-original45-all-native-read-diff-") as tmp:
        for i,(source_sha,associated_tasks) in enumerate(sorted(by_source.items())):
            task=sorted(associated_tasks,key=lambda x:x["test_id"])[0]
            original=data/"ifc"/task["original_source_ifc_relpath"]
            native_row,n=source_native_summary(original,source_sha)
            flags_by_key={"default":{}}
            for t in associated_tasks:
                ff=optin_for_source(
                    t["test_id"],source_sha,t["crud"])
                if ff:
                    flags_by_key[next(iter(ff))]=ff
            read_variants={}
            for name,flags in sorted(flags_by_key.items()):
                read_variants[name]=audit_model_read(
                    original,source_sha,n,
                    Path(tmp)/str(i)/name,
                    flags=flags)
            native_row["original_public_source_category_counts"]=dict(sorted(
                Counter(t["crud"] for t in associated_tasks).items()))
            native_row["actual_model_facing_source_variants"]=read_variants
            native_row["reused_in_original_public_task_ids"]=sorted(
                t["test_id"] for t in associated_tasks)
            source_rows.append(native_row)
            for t in associated_tasks:
                variant=optin_for_source(t["test_id"],source_sha,t["crud"])
                variant_name=next(iter(variant),"default")
                task_rows.append({
                    "original_public_task_id":t["test_id"],
                    "original_public_CRUD":t["crud"],
                    "original_public_category":t["category"],
                    "original_public_question_sha256":t["public_question_sha256"],
                    "original_public_ifc_source_relpath":t["original_source_ifc_relpath"],
                    "original_public_ifc_source_sha256":source_sha,
                    "native_ifc_schema":native_row["schema"],
                    "native_ifc_source_product_count":native_row["native_ifc_products_count"],
                    "native_ifc_source_relationship_count":native_row["native_ifc_relationship_count"],
                    "native_ifc_source_property_relation_count":native_row["native_ifc_property_set_definition_relation_count"],
                    "native_ifc_source_material_relation_count":native_row["native_ifc_material_association_count"],
                    "native_ifc_source_placement_count":native_row["native_ifc_local_placement_count"],
                    "baseline_default_model_read_status":read_variants["default"]["status"],
                    "best_research_feature_flag_tested":variant_name,
                    "best_research_model_read_status":read_variants[variant_name]["status"],
                    "full_native_IFC_read_information_parity_confirmed":False,
                    "full_native_IFC_write_authority_parity_confirmed":False,
                    "original_author_scored":False,
                    "real_paired_LLM_trial":False,
                })
            if progress:
                print(f"V043_SOURCE_PROGRESS {i+1}/31",
                      "tasks",len(associated_tasks),
                      "schema",native_row["schema"],
                      "prod",native_row["native_ifc_products_count"],
                      "rel",native_row["native_ifc_relationship_count"],
                      "default",read_variants["default"]["status"],
                      "research",{
                         k:v["status"] for k,v in read_variants.items()
                         if k!="default"},
                      flush=True)
    task_rows.sort(key=lambda r:r["original_public_task_id"])
    require(len(task_rows)==45
            and len({x["original_public_task_id"] for x in task_rows})==45
            and len(source_rows)==31
            and Counter(t["original_public_CRUD"] for t in task_rows)==
                {"create":15,"update":15,"delete":15},
            "Final original45/source31 audit rollup inconsistent")
    baseline=Counter(t["baseline_default_model_read_status"]
                     for t in task_rows)
    research=Counter(t["best_research_model_read_status"]
                     for t in task_rows)
    nprod=sum(x["native_ifc_products_count"] for x in source_rows)
    nrelations=sum(x["native_ifc_relationship_count"] for x in source_rows)
    nprop=sum(x["native_ifc_property_set_definition_relation_count"]
              for x in source_rows)
    nmats=sum(x["native_ifc_material_association_count"]
              for x in source_rows)
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA
            and _git_clean(author) and _git_clean(data)
            and file_hash(ROOT/PARENT_REPORT[0])==PARENT_REPORT[1],
            "Source or author/data changed after read-only independent audit")
    return {
        "status":"ORIGINAL45_NATIVE_IFC_VS_ACTUAL_XML_SOURCE_READ_PARITY_AUDIT_V043",
        "source_of_truth":"original_public_ifc_native_file_sha256_and_Python_IfcOpenShell_open",
        "actual_XML_tool_of_truth":"XmlSourceEditSession.read_building_xml",
        "pre_registered_issue_url":ISSUE,
        "stacked_parent_commit_sha":PARENT_SHA,
        "original_author_git_head":AUTHOR_SHA,
        "original_data_git_head":DATA_SHA,
        "frozen_original_public_question_csv_sha256":QUESTION_CSV_SHA,
        "frozen_prior_v042_final_report_sha256":PARENT_REPORT[1],
        "original_public_ITT_task_count":45,
        "original_public_CREATE_task_count":15,
        "original_public_UPDATE_task_count":15,
        "original_public_DELETE_task_count":15,
        "original_source_IFC_unique_sha256_count":31,
        "source_native_products_instances_across_31_unique_source_files":nprod,
        "source_native_ifc_relationship_instances_across_31_unique_source_files":nrelations,
        "source_native_property_association_instances_across_unique_files":nprop,
        "source_native_material_association_instances_across_unique_files":nmats,
        "original45_default_XML_model_read_status_counts":dict(sorted(baseline.items())),
        "original45_research_feature_flag_XML_read_status_counts":dict(sorted(research.items())),
        "original45_fully_proven_equal_IFC_source_read_information_tasks":0,
        "original45_fully_proven_equal_IFC_native_write_authority_tasks":0,
        "original_CREATE_task_specific_developer_D0_I0_pairs_previously":5,
        "original_CREATE_task_specific_developer_D0_I0_pairs_added_by_v043":0,
        "original_LLM_matched_XML_vs_Python_trials":0,
        "original_author_evaluator_invocations":0,
        "paid_provider_calls":0,
        "Docker_executions":0,
        "no_hidden_gt_or_original_task_answers_exposed":True,
        "original_native_source_and_grader_mutations":False,
        "default_model_run_one_pair_auto_enables_experimental_optin":False,
        "native_product_GUID_visibility_does_not_imply_all_metadata_geometry_parity":True,
        "explicitly_out_of_scope":"Full STEP byte parity, Docker or paid-model calls, any new source projection/edit feature, original benchmark grading",
        "next_priority":"Resolve demonstrable blocked READ/PROPERTY/MATERIAL/RELATION exposure in original source subsets and test equal native write authority before actual paired LLM execution",
        "original_45_task_rows":task_rows,
        "original_31_unique_native_source_rows":source_rows,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author",type=Path,required=True)
    parser.add_argument("--data",type=Path,required=True)
    parser.add_argument("--write",type=Path)
    parser.add_argument("--progress",action="store_true")
    a=parser.parse_args()
    report=audit(a.author,a.data,progress=a.progress)
    raw=(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf8")
    if a.write:
        a.write.parent.mkdir(parents=True,exist_ok=True)
        with a.write.open("xb") as out:out.write(raw)
        print("V043_FROZEN_REPORT",a.write,"sha256",sha256(raw).hexdigest(),flush=True)
    else:
        print(json.dumps({
            "status":report["status"],
            "baseline_default":report["original45_default_XML_model_read_status_counts"],
            "research_feature_flag":report["original45_research_feature_flag_XML_read_status_counts"],
        },sort_keys=True,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
