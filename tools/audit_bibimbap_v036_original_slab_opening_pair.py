"""Independent original-native slab Opening oracle, plus ordered D0/I0 v0.36 audit.

Developer-authored benchmark feasibility controls ONLY. The unchanged
original author scorer is called after both actual IFC native candidates
pass the same independently authored source-preservation and volume checks.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.shape
import ifcopenshell.util.unit
import numpy as np
from lxml import etree

from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v036_original_slab_opening_i0 import (
    PUBLIC_HOST_GUID,SOURCE_SHA,OPENING_WORLD_BBOX_M,
    OPENING_CENTER_M,SLAB_NATIVE_WORLD_BBOX_M,
    EXPECTED_REMOVED_SLAB_VOLUME_M3,create_original_test03_slab_opening_i0,
)
from tools.audit_bibimbap_v033_original_slab_pair import (
    _original_product_world_mesh_fingerprints,
)

ROOT=Path(__file__).resolve().parents[1]
TASK="test_03"
QUESTION_SHA="a887b002fe9606743cf68dcc2914cd6ef136c16f78083999184f901ccf57c289"
NS="{urn:bim-markup-bench:toy:v0}"
XML_OPENING_ID="v036_original_test03_slab_opening"
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
)


class OriginalSlabOpeningV036Blocked(ValueError):
    pass


def require(ok:bool,reason:str)->None:
    if not ok:
        raise OriginalSlabOpeningV036Blocked(reason)


def actual_original_native_slab_opening_oracle(
        source_path:Path,new_path:Path,claimed_opening_guid:str|None=None)->dict:
    """Independent persisted original-mm IFC scene check, no D0/GT/grader imports."""
    source_path,new_path=Path(source_path),Path(new_path)
    require(source_path.is_file() and new_path.is_file()
            and source_path.resolve()!=new_path.resolve(),
            "Original and candidate native IFC inputs must differ")
    require(file_hash(source_path)==SOURCE_SHA,
            "Original immutable public IFC source hash drift")
    a=ifcopenshell.open(str(source_path))
    b=ifcopenshell.open(str(new_path))
    require(a.schema==b.schema=="IFC4X3" and
            abs(ifcopenshell.util.unit.calculate_unit_scale(a)-.001)<1e-12 and
            abs(ifcopenshell.util.unit.calculate_unit_scale(b)-.001)<1e-12,
            "Actual saved candidate IFC4X3 native-mm contract drift")
    ar={x.GlobalId:x for x in a.by_type("IfcRoot")}
    br={x.GlobalId:x for x in b.by_type("IfcRoot")}
    require(len(ar)==len(a.by_type("IfcRoot"))
            and len(br)==len(b.by_type("IfcRoot"))
            and set(ar)<=set(br),
            "Original native IfcRoot identity lost/duplicated")
    for guid,old in ar.items():
        new=br[guid]
        require(old.is_a()==new.is_a() and old.Name==new.Name
                and old.Description==new.Description,
                "Existing original IFC Root class/name/description changed")
    ap={x.GlobalId:x for x in a.by_type("IfcProduct")}
    bp={x.GlobalId:x for x in b.by_type("IfcProduct")}
    require(set(ap)<=set(bp) and len(bp)==len(ap)+1,
            "Exactly one new IFC product is required")
    added=set(bp)-set(ap)
    new_guid=next(iter(added))
    opening=bp[new_guid]
    require(opening.is_a("IfcOpeningElement"),
            "New physical product not IfcOpeningElement")
    if claimed_opening_guid is not None:
        require(new_guid==claimed_opening_guid,
                "Claimed newly authored opening GUID did not match native object")
    new_roots=set(br)-set(ar)
    require(new_roots=={new_guid}|
            {r.GlobalId for r in b.by_type("IfcRelVoidsElement")
             if r.RelatedOpeningElement.GlobalId==new_guid}
            and len(new_roots)==2,
            "Unexpected native new IFC Root or missing void relationship")
    require(len(opening.VoidsElements)==1
            and opening.VoidsElements[0].RelatingBuildingElement.GlobalId==PUBLIC_HOST_GUID
            and not opening.HasFillings,
            "New opening does not void exact original public IfcSlab")
    slab=b.by_guid(PUBLIC_HOST_GUID)
    require(slab.is_a("IfcSlab") and slab.PredefinedType=="FLOOR"
            and len(slab.HasOpenings)==1
            and slab.HasOpenings[0].RelatedOpeningElement.GlobalId==new_guid,
            "Original published slab not physically hosted/opened")
    for cls in ("IfcRelContainedInSpatialStructure","IfcRelAggregates"):
        originals={r.GlobalId:str(r) for r in a.by_type(cls)}
        candidate={r.GlobalId:str(r) for r in b.by_type(cls)}
        require(all(candidate.get(g)==raw for g,raw in originals.items()),
                "Pre-existing native containment/aggregate relation changed")
    scene0=_original_product_world_mesh_fingerprints(a)
    scene1=_original_product_world_mesh_fingerprints(b)
    require(len(ap)==43 and len(scene0)==43 and len(bp)==44 and len(scene1)==44,
            "Expected original IFC complete product/shape inventory changed")
    for guid,before in scene0.items():
        if guid==PUBLIC_HOST_GUID:
            require(scene1[guid]!=before,
                    "Target slab geometry unchanged despite requested physical cut")
        else:
            require(scene1[guid]==before,
                    "Unrelated original native IFC product mesh changed")
    require(sum(v[1] for v in scene0.values())==39,
            "Expected 39 original shaped products drifted")
    setting=ifcopenshell.geom.settings()
    setting.set(setting.USE_WORLD_COORDS,True)
    def shape_info(model,obj):
        sh=ifcopenshell.geom.create_shape(setting,obj)
        pts=np.asarray(sh.geometry.verts,dtype=float).reshape(-1,3)
        require(len(pts)>=8 and np.isfinite(pts).all(),
                "Native 3D shape missing/nonfinite")
        return (sh,pts,tuple(float(x) for x in (*pts.min(axis=0),*pts.max(axis=0))),
                len(sh.geometry.faces)//3,
                float(ifcopenshell.util.shape.get_volume(sh.geometry)))
    orig_shape,_,orig_bbox,orig_tris,old_volume=shape_info(a,a.by_guid(PUBLIC_HOST_GUID))
    new_shape,_,new_bbox,new_tris,new_volume=shape_info(b,slab)
    _,_,opening_bbox,opening_tris,opening_volume=shape_info(b,opening)
    require(np.allclose(orig_bbox,SLAB_NATIVE_WORLD_BBOX_M,atol=1e-5,rtol=0)
            and np.allclose(new_bbox,orig_bbox,atol=1e-5,rtol=0)
            and np.allclose(opening_bbox,OPENING_WORLD_BBOX_M,atol=1e-5,rtol=0),
            "Original Slab/opening actual world geometry bbox drift")
    require(math.isclose(old_volume,32.37,abs_tol=1e-5,rel_tol=0)
            and math.isclose(new_volume,24.87,abs_tol=1e-5,rel_tol=0)
            and math.isclose(old_volume-new_volume,EXPECTED_REMOVED_SLAB_VOLUME_M3,
                             abs_tol=1e-5,rel_tol=0),
            "Physical slab not cut by exact 5×5×0.3m source volume")
    require(math.isclose(opening_volume,12.5,abs_tol=1e-5,rel_tol=0)
            and opening_tris==12
            and orig_tris==12 and new_tris==32,
            "Native through-cut tool/target body topology differs")
    # Geometry is first validated independently at 1e-5m / 1e-5m3;
    # normalize only independently verified floating evidence to 1e-8
    # to avoid meaningless 3.7 vs 3.6999999999999997 comparisons.
    metric=lambda value:round(float(value),8)
    return {
        "status":"V036_INDEPENDENT_ACTUAL_NATIVE_SLAB_OPENING_5x5_THROUGH_VOID_ORACLE_PASS",
        "original_IfcRoot_GUID_class_name_preserved":True,
        "original_IfcRoot_count":len(ar),
        "original_IfcProduct_count":len(ap),
        "original_mesh_bearing_products":39,
        "original_nonhost_mesh_bearing_products_unchanged":38,
        "original_nonhost_triangle_face_count":sum(
            v[3] for g,v in scene0.items() if g!=PUBLIC_HOST_GUID),
        "original_slab_host_is_real_IfcSlab":True,
        "new_void_hosted_by_original_IfcSlab_not_wall":True,
        "native_IfcRelVoidsElement_exists":True,
        "existing_containment_and_aggregate_relations_unchanged":True,
        "original_slab_world_bbox_m":[metric(x) for x in orig_bbox],
        "new_slab_world_bbox_m":[metric(x) for x in new_bbox],
        "native_opening_world_bbox_m":[metric(x) for x in opening_bbox],
        "original_slab_volume_m3":metric(old_volume),
        "new_slab_volume_m3":metric(new_volume),
        "physically_removed_slab_volume_m3":metric(old_volume-new_volume),
        "native_void_tool_volume_m3":metric(opening_volume),
        "original_slab_triangles_before":orig_tris,
        "original_slab_triangles_after":new_tris,
        "new_opening_triangles":opening_tris,
        "original_source_full_STEP_entity_preservation_claimed":False,
        "matched_model_host_supported":False,
    }


def compile_full_xml_slab_D0(source_mm:Path,out_mm:Path)->dict:
    """Whole XML, explicitly versioned opt-in schema and binder; no LLM API."""
    from src.runtime.experimental_v4_projection import project_ifc_v4
    from src.runtime.experimental_v8_slab_opening_create import (
        compile_declarative_xml_v08_slab_opening_create,
    )
    with TemporaryDirectory(prefix="bmb-v036-full-XML-original-D0-") as t:
        scratch=Path(t)
        source_m=scratch/"original_source_metric.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(source_mm)),"METER").write(str(source_m))
        projected=project_ifc_v4(source_m)
        mapping=dict(projected.projected_global_ids)
        require(PUBLIC_HOST_GUID in mapping,
                "Original actual slab omitted from trusted XML source projection")
        root=etree.fromstring(projected.xml)
        elements=root.find(NS+"Elements")
        require(elements is not None
                and not any(x.get("id")==XML_OPENING_ID for x in elements),
                "XML source state missing or proposed new stable ID duplicate")
        slab_id=mapping[PUBLIC_HOST_GUID]
        require(any(x.get("id")==slab_id and x.tag==NS+"Slab" for x in elements),
                "Original user-visible XML host is not a genuine Slab node")
        etree.SubElement(elements,NS+"Opening",attrib={
            "id":XML_OPENING_ID,"host":slab_id,
            "offset":"2.7","sill":"2.6875","width":"5","height":"5",
        })
        edited_xml=etree.tostring(root,encoding="utf8")
        require(edited_xml!=projected.xml,
                "Full declarative XML state has no new Opening")
        metric_out=scratch/"v08_D0_compiled_metric.ifc"
        compiled=compile_declarative_xml_v08_slab_opening_create(
            source_m,edited_xml,metric_out)
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(metric_out)),"MILLIMETER").write(str(out_mm))
        return {
            **compiled,
            "full_edited_XML_sha256":sha256(edited_xml).hexdigest(),
            "D0_original_native_mm_IFC_sha256":file_hash(out_mm),
        }


def audit_original_test03_pair(root:Path,author:Path,data:Path)->dict:
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Original immutable author/data Git revision drift")
    older=[]
    for rel,digest in PRIOR:
        p=root/rel
        require(p.is_file() and not p.is_symlink() and file_hash(p)==digest,
                "Frozen older original45 report source SHA256 mismatch: "+rel)
        older.append(json.loads(p.read_text(encoding="utf8")))
    v031,v032,v033,v034,v035=older
    require(v031["original_intention_to_test_task_count"]==45
            and v031["original45_developer_native_equal_witnesses"]==11
            and v032["original_public_task_id"]=="test_04"
            and v033["original_public_test_id"]=="test_02"
            and v034["original_test_id"]=="test_05"
            and v035["original_public_test_id"]=="test_01"
            and v035["original_Create_task_specific_semantic_paired_count"]==4,
            "Historic benchmark full 45 ITT or prior Create witnesses changed")
    tasks={x["test_id"]:x for x in public_45(author,data)}
    require(len(tasks)==45 and TASK in tasks,
            "Original BIBIMBAP 45 public task population changed")
    task=tasks[TASK]
    require(task["crud"]=="create" and task["category"]=="basic"
            and task["original_source_ifc_relpath"]=="basic_tasks.ifc"
            and task["original_ifc_sha256"]==SOURCE_SHA
            and task["public_question_sha256"]==QUESTION_SHA
            and PUBLIC_HOST_GUID in task["public_question"]
            and "5 by 5 meters" in task["public_question"]
            and "slab" in task["public_question"].lower(),
            "Original public test03 task question/source mismatch")
    original=data/"ifc"/"basic_tasks.ifc"
    require(original.is_file() and not original.is_symlink()
            and file_hash(original)==SOURCE_SHA,
            "Frozen native source raw IFC changed")
    with TemporaryDirectory(prefix="bmb-v036-original-native-pair-") as d:
        scratch=Path(d)
        i0_file=scratch/"first_independent_Python_original_I0_mm.ifc"
        i0=create_original_test03_slab_opening_i0(original,i0_file)
        oracle_i=actual_original_native_slab_opening_oracle(
            original,i0_file,i0["new_native_opening_guid"])
        i0_sha=file_hash(i0_file)
        require(i0_sha==i0["candidate_original_mm_IFC_sha256"],
                "I0 candidate changed before full-XML D0")
        d0_file=scratch/"second_complete_declarative_XML_original_D0_mm.ifc"
        d0=compile_full_xml_slab_D0(original,d0_file)
        oracle_d=actual_original_native_slab_opening_oracle(
            original,d0_file,d0["created_IfcOpeningElement_GUID"])
        d0_sha=file_hash(d0_file)
        require(oracle_i==oracle_d
                and d0_sha==d0["D0_original_native_mm_IFC_sha256"]
                and file_hash(original)==SOURCE_SHA,
                "Independent actual saved D0/I0 Slab Opening native oracles differ")
        # Original scoring starts only after independent native and provenance
        # verification of *both* candidates; author answers not used as input.
        from tools.bibimbap_matched25_cli import grade_author
        score_i=grade_author(author,original,i0_file,TASK)
        score_d=grade_author(author,original,d0_file,TASK)
        require(score_i["status"]=="AUTHOR_SCORED"
                and score_d["status"]=="AUTHOR_SCORED",
                "Original author benchmark grader produced no valid result")
        require(file_hash(original)==SOURCE_SHA
                and _head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
                "Original frozen author/data/source changed after scoring")
    return {
        "status":"V036_ORIGINAL_PUBLIC_TEST03_SLAB_OPENING_NATIVE_SEMANTIC_D0_I0_PAIR",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/187",
        "original_public_task_id":TASK,
        "original_45_intention_to_test_denominator":45,
        "original_question_sha256":QUESTION_SHA,
        "original_native_IFC_source_sha256":SOURCE_SHA,
        "original_author_git_sha":AUTHOR_SHA,
        "original_data_git_sha":DATA_SHA,
        "prior_reports_sha256":dict(PRIOR),
        "original_host_kind_real_native_IfcSlab":True,
        "original_benchmark_task_under_determined_choices_preregistered":True,
        "preregistered_opening_square_horizontal_5_by_5_m":True,
        "preregistered_5x5_world_center_xy_m":[5.,5.0125],
        "preregistered_opening_world_bbox_m":list(OPENING_WORLD_BBOX_M),
        "original_slab_world_bbox_m":list(SLAB_NATIVE_WORLD_BBOX_M),
        "predeclared_0_5m_vertical_void_tool_through_0_3m_slab":True,
        "opt_in_XML_v08_slab_opening_host_typed_only":True,
        "default_XML_schema_wall_only_unchanged":True,
        "default_typed_binder_wall_only_unchanged":True,
        "XML_slab_offset_and_sill_mean_X_and_Y_footprint_coordinates":True,
        "independent_native_I0_saved_and_checked_before_XML_D0":True,
        "both_actual_native_oracles":oracle_i,
        "D0_I0_actual_native_semantic_equivalence":oracle_i==oracle_d,
        "D0_original_native_IFC_sha256":d0_sha,
        "I0_original_native_IFC_sha256":i0_sha,
        "D0_I0_entire_IFC_byte_identical":d0_sha==i0_sha,
        "original_author_D0":score_d,
        "original_author_I0":score_i,
        "original_author_scores_identical":score_d==score_i,
        "original_author_D0_full_mark":score_d["original_author_full_mark"],
        "original_author_I0_full_mark":score_i["original_author_full_mark"],
        "historical_developer_native_byte_equal_11_unchanged":11,
        "original_Create_semantic_only_developer_pairs":5,
        "original_Create_remaining_without_native_semantic_pair":10,
        "original45_full_task_relevant_read_parity_proven":0,
        "original45_full_native_write_parity_proven":0,
        "matched_real_LLM_D_I_trials":0,
        "paid_LLM_provider_calls":0,
        "new_slab_opening_compiler_registered_in_trial_host":False,
        "causal_LLM_representation_comparison_permitted":False,
        "whole_native_IFC_STEP_byte_equal_or_lossless_proven":False,
        "original_author_dataset_GT_evaluator_mutated":False,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--author",type=Path,required=True)
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--write",type=Path)
    args=p.parse_args()
    report=audit_original_test03_pair(args.root,args.author,args.data)
    data=(json.dumps(report,sort_keys=True,indent=2)+"\n").encode("utf8")
    if args.write:
        args.write.parent.mkdir(parents=True,exist_ok=True)
        with args.write.open("xb") as output:
            output.write(data)
        print("WRITTEN",args.write,sha256(data).hexdigest())
    else:
        print(json.dumps({
            "status":report["status"],
            "native_D0_I0_equivalent":report["D0_I0_actual_native_semantic_equivalence"],
            "original_author_D0_score":report["original_author_D0"]["original_author_score"],
            "original_author_I0_score":report["original_author_I0"]["original_author_score"],
            "whole_IFC_byte_equal":report["D0_I0_entire_IFC_byte_identical"],
            "real_LLM_trials":report["matched_real_LLM_D_I_trials"],
        },sort_keys=True))


if __name__=="__main__":
    main()
