"""v0.37: original-public 10 remaining CREATE live XML authoring preflight.

Runs the EXACT frozen prospective matched25 XML session, not hypothetical
schema/role assumptions. Every generated edit is an illustrative
*non-task-solution* generic class creation. No original grader/GT, provider,
Docker worker, paid model or user project is accessed. All original 45 stay
in ITT; no untested task is labeled a model failure or a success.

The five original CREATE developer D0/I0 witnesses are pinned separately:
test_01, test_02, test_03, test_04, test_05. This code does not replay scores.
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
from tools.audit_bibimbap_v030_reconcile import ROLES as V022_FROZEN_ROLES
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import (
    XmlSourceEditSession,UnsupportedArm,file_hash,
)
from tools.audit_bibimbap_v12_real45_capability_matrix import (
    REQUIREMENTS,SOURCE_GUID_PATTERN,
)

ROOT=Path(__file__).resolve().parents[1]
ISSUE="https://github.com/pikaybh/bim-markup-bench/issues/189"

# Frozen v0.31–v0.36 ancestors, not current mutable branch references.
PRIOR=(
 ("reports/bibimbap_v031_original45_eligibility_and_overlap_20261117.json",
  "d6680b3eadb5733be547c09ab8deed58dd48c7feaccbc3cb562b6e60b475c7dd"),
 ("reports/bibimbap_v032_original_test04_column_D0_I0_native_semantic_pair_20261117.json",
  "65cd592b83b06ac161ff420982cb2f3378e850613f4645419690e06764987b2b"),
 ("reports/bibimbap_v033_original_test02_slab_D0_I0_semantic_pair_20261117.json",
  "998064e23a0b3955b20a0ca1a7cabcb4424a612af1d633e42cd179f5e68ce660"),
 ("reports/bibimbap_v034_original_test05_wall_D0_I0_native_semantic_pair_20261117.json",
  "d4bc58a426fd30b6215fef0c2c8d0907c109df1127fa64d44f7d8ab911d4073d"),
 ("reports/bibimbap_v035_original_test01_hosted_door_D0_I0_20261117.json",
  "7ba3a9465996a90d4d324c8e31bc3ff18f3487cb890431e3c30989a516ac82c9"),
 ("reports/bibimbap_v036_original_test03_slab_opening_D0_I0_20261117.json",
  "04def65798913aab267b4894f234b2d8ba8f173baff001b3059eed55bdade138"),
)
COMPLETED_CREATE_IDS=frozenset(
    ("test_01","test_02","test_03","test_04","test_05"))
GENERIC_CREATE_KIND={
    "geometry_test_01":"Slab",
    "geometry_test_02":"Column",
    "geometry_test_03":"Door",
    "geometry_test_04":"Space",
    "geometry_test_05":"Wall",
    "topological_test_01":"Wall",
    "topological_test_02":"Column",
    "topological_test_03":"Wall",
    "topological_test_04":"Slab",
    "topological_test_05":"Door",
}
# Prospective v0.37 assertions from actual pre-report, pre-GT host inspections.
EXPECTED_NATIVE_ADMISSION={
    "geometry_test_01":"P1_LIVE_XML_GEOMETRY_PROJECTION_BLOCKED",
    "geometry_test_02":"P3_ACTUAL_HOST_NEW_CLASS_WRITER_BLOCKED",
    "geometry_test_03":"P0_LIVE_XML_SOURCE_SCHEMA_REJECTED",
    "geometry_test_04":"P0_LIVE_XML_SOURCE_SCHEMA_REJECTED",
    "geometry_test_05":"P0_LIVE_XML_SOURCE_SCHEMA_REJECTED",
    "topological_test_01":"P2_NAMED_ROOM_OR_SOURCE_SPACE_NOT_IN_XML",
    "topological_test_02":"P3_ACTUAL_HOST_NEW_CLASS_WRITER_BLOCKED",
    "topological_test_03":"P2_NAMED_ROOM_OR_SOURCE_SPACE_NOT_IN_XML",
    "topological_test_04":"P3_ACTUAL_HOST_NEW_CLASS_WRITER_BLOCKED",
    "topological_test_05":"P1_LIVE_XML_GEOMETRY_PROJECTION_BLOCKED",
}
EXPECTED_SCHEMAS={
    "geometry_test_01":"IFC4X3",
    "geometry_test_02":"IFC4X3",
    "geometry_test_03":"IFC2X3",
    "geometry_test_04":"IFC2X3",
    "geometry_test_05":"IFC4",
    "topological_test_01":"IFC4X3",
    "topological_test_02":"IFC4X3",
    "topological_test_03":"IFC4X3",
    "topological_test_04":"IFC4X3",
    "topological_test_05":"IFC4X3",
}
PRIORITY_TIERS=(
    "P0_LIVE_XML_SOURCE_SCHEMA_REJECTED",
    "P1_LIVE_XML_GEOMETRY_PROJECTION_BLOCKED",
    "P2_NAMED_ROOM_OR_SOURCE_SPACE_NOT_IN_XML",
    "P3_ACTUAL_HOST_NEW_CLASS_WRITER_BLOCKED",
)
XML_NS="{urn:bim-markup-bench:toy:v0}"
# Generic examples are deliberate non-solutions, with unrelated fixed geometry.
GENERIC_CREATE_BASE={
    "id":"v037_scope_only_not_a_task_solution",
    "x":"0","y":"0","z":"0",
}
class V037LiveGateBlocked(ValueError):
    pass


def require(ok:bool,message:str)->None:
    if not ok:
        raise V037LiveGateBlocked(message)


def locked_ancestors(root:Path)->tuple[dict,...]:
    values=[]
    for rel,pin in PRIOR:
        path=root/rel
        require(path.is_file() and not path.is_symlink() and
                file_hash(path)==pin,"Prior immutable evidence SHA drift: "+rel)
        values.append(json.loads(path.read_text(encoding="utf8")))
    old,*middle,latest=values
    require(old["original_intention_to_test_task_count"]==45
            and old["original45_developer_native_equal_witnesses"]==11
            and old["original45_create_task_developer_native_equal_witnesses"]==0
            and latest["original_public_task_id"]=="test_03"
            and latest["original_45_intention_to_test_denominator"]==45
            and latest["original_Create_semantic_only_developer_pairs"]==5
            and latest["original_Create_remaining_without_native_semantic_pair"]==10
            and latest["matched_real_LLM_D_I_trials"]==0,
            "Original benchmark frozen v0.31/v0.36 denominator/provenance drift")
    return tuple(values)


def original_population(author:Path,data:Path)->tuple[list[dict],dict]:
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Original author/data immutable Git revision changed")
    public=public_45(author,data)
    lookup={x["test_id"]:x for x in public}
    require(len(public)==45 and len(lookup)==45
            and Counter(x["crud"] for x in public)==
                {"create":15,"update":15,"delete":15},
            "Original published 45/15-per-CRUD population has changed")
    create={x["test_id"] for x in public if x["crud"]=="create"}
    remaining=create-COMPLETED_CREATE_IDS
    require(COMPLETED_CREATE_IDS<=create
            and remaining==set(GENERIC_CREATE_KIND)==set(EXPECTED_NATIVE_ADMISSION)
            and remaining==set(EXPECTED_SCHEMAS),
            "Original 15 CREATE or chosen remaining 10 evidence cohort drift")
    return public,lookup


def source_row(original_task:dict,ifc_dir:Path)->tuple[Path,ifcopenshell.file,dict]:
    rel=Path(original_task["original_source_ifc_relpath"])
    path=ifc_dir/rel
    require(not rel.is_absolute()
            and path.is_file() and not path.is_symlink()
            and path.resolve().is_relative_to(ifc_dir.resolve()),
            "Original public IFC must be an ordinary file inside immutable data/ifc")
    original_hash=original_task["original_ifc_sha256"]
    require(file_hash(path)==original_hash,
            "Actual original public input IFC SHA256 does not match published manifest")
    model=ifcopenshell.open(str(path))
    count=Counter(x.is_a() for x in model.by_type("IfcProduct"))
    guids={x.GlobalId:x for x in model.by_type("IfcProduct")}
    require(len(guids)==len(model.by_type("IfcProduct"))
            and model.schema==EXPECTED_SCHEMAS[original_task["test_id"]]
            and abs(ifcopenshell.util.unit.calculate_unit_scale(model)-.001)<1e-12,
            "Actual native original schema/units/products drifted")
    mentions=sorted(set(SOURCE_GUID_PATTERN.findall(original_task["public_question"])))
    require(all(g in guids for g in mentions),
            "Public instruction GUID absent in actual original IfcProduct source")
    return path,model,{
        "original_ifc_schema":model.schema,
        "native_millimetre_units":True,
        "native_source_IfcProduct_count":len(guids),
        "native_source_IfcProduct_class_counts":dict(sorted(count.items())),
        "native_root_GUID_count":len(model.by_type("IfcRoot")),
        "original_public_named_IfcProduct_references":[
            {"guid":guid,"ifc_class":guids[guid].is_a()} for guid in mentions
        ],
    }


def xml_visible_guid_map(xml_text:bytes)->dict[str,str]:
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True)
    tree=etree.fromstring(xml_text,parser=parser)
    require(tree.tag==XML_NS+"Building"
            and tree.find(XML_NS+"Levels") is not None
            and tree.find(XML_NS+"Elements") is not None,
            "Live current-model XML must be complete pinned declarative Building")
    nodes=[x for x in tree.iter()
           if x.get("ifcGuid") is not None]
    guids={x.get("ifcGuid"):x.tag.rsplit("}",1)[-1] for x in nodes}
    require(len(guids)==len(nodes),
            "Live current-model XML omitted or duplicated existing source GUID")
    return guids


def generic_edited_whole_xml(original_xml:bytes,klass:str)->bytes:
    """One generic CREATE class, never derived from actual task answer/GT."""
    require(klass in ("Wall","Column","Slab"),
            "No generic native mutation performed for other task classes")
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True)
    doc=etree.fromstring(original_xml,parser=parser)
    levels=doc.find(XML_NS+"Levels")
    elements=doc.find(XML_NS+"Elements")
    require(levels is not None and len(levels)>0 and elements is not None,
            "Cannot form generic complete XML without a source-pinned storey")
    attrs={**GENERIC_CREATE_BASE,"level":levels[0].get("id")}
    if klass=="Wall":
        attrs.update({"x1":"0","y1":"0","z1":"0","x2":"5","y2":"0",
                      "z2":"0","height":"3","thickness":"0.2"})
        for k in ("x","y","z"):attrs.pop(k)
    elif klass=="Column":
        attrs.update({"width":"0.3","depth":"0.3","height":"3"})
    else:
        attrs.update({"width":"0.3","depth":"0.3","thickness":"0.2"})
    require(not any(e.get("id")==attrs["id"] for e in elements),
            "Frozen generic source-diff ID already exists")
    etree.SubElement(elements,XML_NS+klass,attrib=attrs)
    new=etree.tostring(doc,encoding="utf8")
    require(new!=original_xml,
            "Real full XML source state was not modified by generic change")
    return new


def probe_live_host_for_one(task:dict,source:Path,model:ifcopenshell.file,
                            native:dict,folder:Path,older:dict)->dict:
    tid=task["test_id"]
    require(tid in GENERIC_CREATE_KIND and not folder.exists(),
            "Unique real host probe destination required")
    original_hash=file_hash(source)
    named=native["original_public_named_IfcProduct_references"]
    output={
        **native,
        "task_id":tid,
        "original_category":task["category"],
        "original_crud":task["crud"],
        "public_question_sha256":task["public_question_sha256"],
        "original_public_IFC_sha256":original_hash,
        "public_operation_family":older["public_edit_operation_family"],
        "required_public_source_roles_missing_in_prior_typed_XML":
            older["required_public_source_roles_missing_editable_XML"],
        "generic_authoring_class_probed":GENERIC_CREATE_KIND[tid],
        "generic_probe_is_original_task_solution":False,
        "original_author_evaluator_called":False,
        "visible_typed_XML_product_count":None,
        "unrepresented_original_native_IfcProduct_classes":None,
        "named_GUID_in_current_full_XML":None,
        "full_task_relevant_information_parity_proven":False,
        "full_task_relevant_native_write_parity_proven":False,
        "matched_LLM_execution":False,
        "scored_original_author_result":False,
    }
    try:
        session=XmlSourceEditSession(source,folder)
    except UnsupportedArm as exc:
        reason=str(exc)
        if model.schema!="IFC4X3":
            require(reason=="XML source compiler only accepts IFC4X3",
                    "Unexpected schema rejection status or diagnostic drift")
            output.update({
                "actual_XML_session_admission":"BLOCKED_NON_IFC4X3",
                "actual_XML_session_block_reason":"SCHEMA_GATE",
                "actual_generic_native_create_probe":"NOT_ATTEMPTED_SOURCE_REJECTED",
            })
        else:
            require(reason=="UnsupportedIFCGeometry",
                    "Unexpected real source geometry projection error")
            output.update({
                "actual_XML_session_admission":"BLOCKED_NATIVE_PROJECTION",
                "actual_XML_session_block_reason":"UNSUPPORTED_GEOMETRY",
                "actual_generic_native_create_probe":"NOT_ATTEMPTED_SOURCE_REJECTED",
            })
    else:
        xml=xml_visible_guid_map(session.current_xml)
        original={p.GlobalId:p for p in model.by_type("IfcProduct")}
        visible={guid:kind for guid,kind in xml.items() if guid in original}
        remaining={guid:entity.is_a() for guid,entity in original.items()
                   if guid not in xml}
        require(len(visible)<=len(original)
                and all(g in original for g in visible)
                and not session.output_ifc and session.submissions==0,
                "Actual live model-visible XML source malformed or side effect")
        output.update({
            "actual_XML_session_admission":"ADMITTED_SOURCE_ONLY",
            "actual_XML_session_block_reason":None,
            "live_model_visible_XML_sha256":sha256(session.current_xml).hexdigest(),
            "visible_typed_XML_product_count":len(visible),
            "live_XML_typed_node_class_counts":dict(sorted(Counter(
                xml.values()).items())),
            "unrepresented_original_native_IfcProduct_classes":dict(
                sorted(Counter(remaining.values()).items())),
            "named_GUID_in_current_full_XML":[
                {"guid":x["guid"],"visible":x["guid"] in xml,
                 "native_ifc_class":x["ifc_class"]}
                for x in named],
        })
        klass=GENERIC_CREATE_KIND[tid]
        require(klass in ("Wall","Column","Slab"),
                "Unexpected generic new-class admission test")
        candidate=generic_edited_whole_xml(session.current_xml,klass)
        output["illustrative_generic_whole_XML_sha256"]=sha256(candidate).hexdigest()
        result=session.call(
            "submit_building_xml",{"xml_text":candidate.decode("utf8")})
        require(session.submissions==1,
                "Exactly one isolated generic no-grader XML write probe expected")
        if klass=="Wall":
            require(result.get("status")=="ok"
                    and result.get("native_ifc_committed") is True
                    and session.output_ifc is not None
                    and session.output_ifc.is_file(),
                    "Current model-facing generic Wall native write no longer commits")
            candidate_native=ifcopenshell.open(str(session.output_ifc))
            original_guids={x.GlobalId for x in model.by_type("IfcRoot")}
            now_guids={x.GlobalId for x in candidate_native.by_type("IfcRoot")}
            new_walls={x.GlobalId for x in candidate_native.by_type("IfcWall")} - {
                x.GlobalId for x in model.by_type("IfcWall")}
            require(original_guids<=now_guids and len(new_walls)==1
                    and candidate_native.schema==model.schema
                    and abs(ifcopenshell.util.unit.calculate_unit_scale(
                        candidate_native)-.001)<1e-12,
                    "Illustrative generic Wall CREATE lacked real separate native IFC")
            output["actual_generic_native_create_probe"]="ILLUSTRATIVE_WALL_SAVED_NATIVE"
        else:
            require(result.get("status")=="error"
                    and result.get("native_ifc_committed") is not True
                    and "UnsupportedIFCMutation: Only creation of a new standalone Wall is supported"
                        in result.get("error","")
                    and session.output_ifc is None,
                    "Current matched host generic Column/Slab writer changed/failed open")
            output["actual_generic_native_create_probe"]="BLOCKED_UNSUPPORTED_NEW_CLASS"
        require(file_hash(source)==original_hash,
                "Source file changed across real matched XML whole-document edit attempt")
    require(file_hash(source)==original_hash,
            "Immutable original source SHA changed across live host constructor")
    output["source_native_sha256_unchanged_after_probe"]=True
    output["claimed_complete_current_D_I_causal_trial_eligibility"]=False
    return output


def classify_gates(row:dict)->dict:
    tid=row["task_id"]
    status=row["actual_XML_session_admission"]
    named=row.get("named_GUID_in_current_full_XML") or []
    original=row["native_source_IfcProduct_class_counts"]
    omitted=row.get("unrepresented_original_native_IfcProduct_classes") or {}
    # P0 and P1 are hard input barriers. P2 is the source-fact barrier
    # even when the superficial original XML admission succeeded.
    public_room_guid_ifc_wall=bool(
        tid=="topological_test_03"
        and len(row["original_public_named_IfcProduct_references"])==2
        and all(x["ifc_class"]=="IfcWall"
                for x in row["original_public_named_IfcProduct_references"]))
    room_source_omitted=bool(
        tid in ("topological_test_01","topological_test_03")
        and original.get("IfcSpace",0)>0
        and omitted.get("IfcSpace",0)==original["IfcSpace"])
    if status=="BLOCKED_NON_IFC4X3":
        tier=PRIORITY_TIERS[0]
    elif status=="BLOCKED_NATIVE_PROJECTION":
        tier=PRIORITY_TIERS[1]
    elif (any(not x["visible"] for x in named)
          or room_source_omitted or public_room_guid_ifc_wall):
        tier=PRIORITY_TIERS[2]
    else:
        require(status=="ADMITTED_SOURCE_ONLY"
                and row["actual_generic_native_create_probe"]==
                    "BLOCKED_UNSUPPORTED_NEW_CLASS",
                "Remaining cohort has unidentified generic writer/visibility gap")
        tier=PRIORITY_TIERS[3]
    row["public_room_named_GUIDs_refer_to_native_IfcWall_not_IfcSpace"] = (
        public_room_guid_ifc_wall
    )
    row["original_IfcSpace_required_for_room_reference_but_not_visible_in_XML"]=(
        room_source_omitted
    )
    row["next_engineering_priority_tier"]=tier
    require(tier==EXPECTED_NATIVE_ADMISSION[tid],
            "Pre-registered live actual 10-task authoring gate outcome drift")
    return row


def audit_remaining_create(
        root:Path,author:Path,data:Path)->dict:
    root,author,data=Path(root),Path(author),Path(data)
    history=locked_ancestors(root)
    _,public=original_population(author,data)
    v031={r["task_id"]:r for r in history[0]["rows"]}
    require(len(v031)==45 and set(v031)==set(public),
            "Frozen prior original45 public task set mismatch")
    # Original per-task PUBLIC question+native source SHA pins predate the
    # 0.31 row-only eligibility summary. This closes the potential ambiguity
    # of changed local question files while Git HEAD remains unchanged.
    role_path=root/"reports"/V022_FROZEN_ROLES[0]
    require(role_path.is_file() and not role_path.is_symlink()
            and file_hash(role_path)==V022_FROZEN_ROLES[1],
            "Frozen prior original45 question/source SHA manifest drift")
    role_report=json.loads(role_path.read_text(encoding="utf8"))
    old_public={x["task_id"]:x for x in
                role_report["all45_per_task_actual_source_role_and_admission_rows"]}
    require(len(old_public)==45 and set(old_public)==set(public),
            "Frozen original public task/question population drift")
    for tid,task in public.items():
        older=old_public[tid]
        require(older["original_public_question_sha256"]==task["public_question_sha256"]
                and older["original_native_IFC_sha256"]==task["original_ifc_sha256"]
                and older["original_crud"]==task["crud"]
                and older["original_category"]==task["category"],
                "Original public question/source SHA changed since frozen source audit: "+tid)
    ifc_dir=data/"ifc"
    require(ifc_dir.is_dir() and not ifc_dir.is_symlink(),
            "Pinned original author source IFC root unavailable")
    rows=[]
    with TemporaryDirectory(prefix="bmb-v037-pinned-original10-CREATE-") as temp:
        scratch=Path(temp)
        for i,tid in enumerate(sorted(GENERIC_CREATE_KIND)):
            task=public[tid]
            older=v031[tid]
            require(task["crud"]==older["original_crud"]=="create"
                    and task["category"]==older["original_category"]
                    and older["original_ifc_schema"]==EXPECTED_SCHEMAS[tid],
                    "Frozen task CRUD/category/IFC schema drift: "+tid)
            rel,model,native=source_row(task,ifc_dir)
            require(file_hash(rel)==task["original_ifc_sha256"],
                    "Source IFC bytes changed before real host session")
            row=probe_live_host_for_one(
                task,rel,model,native,scratch/f"task_{i:02d}",older)
            rows.append(classify_gates(row))
    require([x["task_id"] for x in rows]==sorted(GENERIC_CREATE_KIND)
            and len(rows)==10
            and all(x["source_native_sha256_unchanged_after_probe"] for x in rows)
            and _head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Original immutable public task input not preserved through probes")
    counts=Counter(x["next_engineering_priority_tier"] for x in rows)
    expected=[3,2,2,3]
    require([counts[k] for k in PRIORITY_TIERS]==expected,
            "Exact preregistered 10-case prioritization distribution drift")
    admitted=sum(x["actual_XML_session_admission"]=="ADMITTED_SOURCE_ONLY"
                 for x in rows)
    rejected=10-admitted
    writes=Counter(x["actual_generic_native_create_probe"] for x in rows)
    require(admitted==5 and rejected==5
            and writes["ILLUSTRATIVE_WALL_SAVED_NATIVE"]==2
            and writes["BLOCKED_UNSUPPORTED_NEW_CLASS"]==3
            and writes["NOT_ATTEMPTED_SOURCE_REJECTED"]==5,
            "Real host source/writer probe outcome unexpectedly changed")
    return {
        "status":"V037_ORIGINAL_PUBLIC_10_REMAINING_CREATE_LIVE_SOURCE_AND_WRITER_GATES",
        "issue":ISSUE,
        "stack_parent_v036_commit":"ca60e56a0a4fca331a093cbda2dc2074bc140ade",
        "original_author_git_sha":AUTHOR_SHA,
        "original_data_git_sha":DATA_SHA,
        "frozen_previous_reports_sha256":dict(PRIOR),
        "current_matched_host_file_sha256":
            file_hash(root/"tools/bibimbap_matched25_tools.py"),
        "current_matched_default_compiler_file_sha256":
            file_hash(root/"src/runtime/compiler.py"),
        "original_public_full_ITT_45":45,
        "original_public_all_CREATE_15":15,
        "previous_5_nonblinded_original_CREATE_semantic_pairs_still_5":5,
        "remaining_original_CREATE_not_yet_native_D0_I0_paired":10,
        "remaining_CREATE_live_source_XML_admitted_count":admitted,
        "remaining_CREATE_live_source_XML_rejected_count":rejected,
        "source_schema_hard_rejections":counts[PRIORITY_TIERS[0]],
        "native_geometry_projection_hard_rejections":counts[PRIORITY_TIERS[1]],
        "admitted_but_public_room_source_visibility_or_noun_mismatch":counts[PRIORITY_TIERS[2]],
        "admitted_but_generic_new_class_writer_rejections":counts[PRIORITY_TIERS[3]],
        "illustrative_GENERIC_Wall_natives_committed_not_task_success":2,
        "illustrative_GENERIC_Column_Slab_mutations_rejected":3,
        "live_source_rejection_means_benchmark_failure":False,
        "live_XML_admission_means_task_success":False,
        "generic_writer_commit_means_task_success":False,
        "current_v037_applies_no_changes_to_matched_host_or_original_IFC":True,
        "original_author_evaluator_invocations":0,
        "real_model_or_paid_inference_calls":0,
        "Docker_executions":0,
        "original45_full_task_relevant_read_information_parity_proven":0,
        "original45_full_native_write_capability_parity_proven":0,
        "real_matched_LLM_D_I_trials":0,
        "original45_developer_native_byte_equal_11_unchanged":11,
        "causal_XML_vs_Python_representation_effect_supported":False,
        "priority_tier_population":[
            {"tier":t,"task_ids":[x["task_id"] for x in rows
                                  if x["next_engineering_priority_tier"]==t]}
            for t in PRIORITY_TIERS
        ],
        "rows":rows,
    }


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--author",type=Path,required=True)
    parser.add_argument("--data",type=Path,required=True)
    parser.add_argument("--write",type=Path)
    args=parser.parse_args()
    result=audit_remaining_create(args.root,args.author,args.data)
    body=(json.dumps(result,sort_keys=True,indent=2)+"\n").encode("utf8")
    if args.write:
        args.write.parent.mkdir(parents=True,exist_ok=True)
        with args.write.open("xb") as writer:
            writer.write(body)
        print("WRITTEN",args.write,sha256(body).hexdigest())
    else:
        print(json.dumps({
            "status":result["status"],
            "source_admitted":result["remaining_CREATE_live_source_XML_admitted_count"],
            "schema_rejects":result["source_schema_hard_rejections"],
            "geometry_rejects":result["native_geometry_projection_hard_rejections"],
            "room_information_gap":result["admitted_but_public_room_source_visibility_or_noun_mismatch"],
            "generic_write_rejects":result["admitted_but_generic_new_class_writer_rejections"],
            "real_LLM_trials":result["real_matched_LLM_D_I_trials"],
        },sort_keys=True))


if __name__=="__main__":
    main()
