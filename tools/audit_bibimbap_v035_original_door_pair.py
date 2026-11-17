"""v0.35: original BIBIMBAP public test_01 independent hosted Door D0/I0.

Sequence: pin unchanged original -> independent original-native I0 writer ->
independent actual IFC oracle -> full-declarative-XML D0 trusted v0.7 compiler
-> SAME independent oracle -> unchanged original author scorer (AFTER freeze).

The task's width/height interpretation, location and leaf/void thickness
were registered in public Issue #185 before any original scorer invocation.
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
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.shape
import ifcopenshell.util.unit
from lxml import etree
import numpy as np

from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v035_original_door_i0 import (
    HOST_GUID,SOURCE_SHA,DOOR_WIDTH_M,DOOR_HEIGHT_M,
    DOOR_LEAF_THICKNESS_M,OPENING_THROUGH_WALL_DEPTH_M,
    OFFSET_FROM_HOST_AXIS_START_M,create_original_public_test01_door_i0,
)
from tools.audit_bibimbap_v033_original_slab_pair import _original_product_world_mesh_fingerprints

ROOT=Path(__file__).resolve().parents[1]
TASK="test_01"
QUESTION_SHA="6047b505112d7c9da219957e74a955d259c67148f019250b0722605db6610c31"
NS="{urn:bim-markup-bench:toy:v0}"
XML_OPENING_ID="test01_public_hosted_door_opening_v035"
XML_DOOR_ID="test01_public_hosted_door_filling_v035"
FROZEN=(
 ("reports/bibimbap_v031_original45_eligibility_and_overlap_20261117.json",
  "d6680b3eadb5733be547c09ab8deed58dd48c7feaccbc3cb562b6e60b475c7dd"),
 ("reports/bibimbap_v032_original_test04_column_D0_I0_native_semantic_pair_20261117.json",
  "65cd592b83b06ac161ff420982cb2f3378e850613f4645419690e06764987b2b"),
 ("reports/bibimbap_v033_original_test02_slab_D0_I0_semantic_pair_20261117.json",
  "998064e23a0b3955b20a0ca1a7cabcb4424a612af1d633e42cd179f5e68ce660"),
 ("reports/bibimbap_v034_original_test05_wall_D0_I0_native_semantic_pair_20261117.json",
  "d4bc58a426fd30b6215fef0c2c8d0907c109df1127fa64d44f7d8ab911d4073d"),
)


class OriginalHostedDoorV035Blocked(ValueError):
    pass


def require(condition:bool,message:str)->None:
    if not condition:
        raise OriginalHostedDoorV035Blocked(message)


def _native_shape(model,entity):
    s=ifcopenshell.geom.settings()
    s.set(s.USE_WORLD_COORDS,True)
    sh=ifcopenshell.geom.create_shape(s,entity)
    values=np.asarray(sh.geometry.verts,dtype=float)
    faces=np.asarray(sh.geometry.faces,dtype=int)
    require(values.size>=24 and values.size%3==0 and
            faces.size>=12 and faces.size%3==0 and np.isfinite(values).all(),
            "Physical native IFC shape/triangles missing")
    return sh,values.reshape(-1,3),len(faces)//3


def _bbox(world):
    return [float(v) for v in (*world.min(axis=0),*world.max(axis=0))]


def actual_original_native_hosted_door_oracle(
        original_mm:Path,candidate_mm:Path,
        claimed_door_guid:str|None=None,
        claimed_opening_guid:str|None=None)->dict:
    """Independent native 3D and host/filling check, no XML compiler/grader."""
    original_mm,candidate_mm=Path(original_mm),Path(candidate_mm)
    require(original_mm.is_file() and candidate_mm.is_file()
            and original_mm.resolve()!=candidate_mm.resolve(),
            "Original/native source and new candidate must be separate")
    source=ifcopenshell.open(str(original_mm))
    output=ifcopenshell.open(str(candidate_mm))
    require(source.schema==output.schema=="IFC4X3" and
            abs(ifcopenshell.util.unit.calculate_unit_scale(source)-.001)<1e-12
            and abs(ifcopenshell.util.unit.calculate_unit_scale(output)-.001)<1e-12,
            "Original native IFC4X3 mm schema/units drift")
    r0={x.GlobalId:x for x in source.by_type("IfcRoot")}
    r1={x.GlobalId:x for x in output.by_type("IfcRoot")}
    require(len(r0)==len(source.by_type("IfcRoot")) and
            len(r1)==len(output.by_type("IfcRoot")) and set(r0)<=set(r1),
            "Native IFC original Root GUIDs lost/duplicated")
    for g,item in r0.items():
        same=r1[g]
        require(item.is_a()==same.is_a() and item.Name==same.Name
                and item.Description==same.Description,
                "Original Root class/name/description mutated")
    p0={x.GlobalId:x for x in source.by_type("IfcProduct")}
    p1={x.GlobalId:x for x in output.by_type("IfcProduct")}
    require(set(p0)<=set(p1) and len(p1)==len(p0)+2,
            "Native result requires exactly two new products")
    added=set(p1)-set(p0)
    new_opening=[p1[g] for g in added if p1[g].is_a("IfcOpeningElement")]
    new_door=[p1[g] for g in added if p1[g].is_a("IfcDoor")]
    require(len(new_opening)==len(new_door)==1,"One new Opening and Door pair required")
    opening,door=new_opening[0],new_door[0]
    if claimed_opening_guid is not None:
        require(opening.GlobalId==claimed_opening_guid,"Writer claimed wrong Opening GUID")
    if claimed_door_guid is not None:
        require(door.GlobalId==claimed_door_guid,"Writer claimed wrong Door GUID")
    roots_delta=set(r1)-set(r0)-{opening.GlobalId,door.GlobalId}
    require(len(roots_delta)==2 and
            sorted(r1[g].is_a() for g in roots_delta)==
            ["IfcRelFillsElement","IfcRelVoidsElement"],
            "Exactly two new void/fill native relationships required")
    require(len(opening.VoidsElements)==1 and
            opening.VoidsElements[0].RelatingBuildingElement.GlobalId==HOST_GUID,
            "New opening does not void specified original public Wall")
    require(len(door.FillsVoids)==1 and
            door.FillsVoids[0].RelatingOpeningElement.GlobalId==opening.GlobalId,
            "New door does not fill newly-created real opening")
    wall=output.by_guid(HOST_GUID)
    require(wall.is_a("IfcWall"),"Original public host Wall class drift")
    level=ifcopenshell.util.element.get_container(wall)
    door_level=ifcopenshell.util.element.get_container(door)
    require(level is not None and door_level is not None
            and level.GlobalId==door_level.GlobalId
            and level.GlobalId in r0 and level.Name=="L1",
            "Door must be contained in original host L1 storey")
    source_containment={
        r.GlobalId:{x.GlobalId for x in r.RelatedElements}
        for r in source.by_type("IfcRelContainedInSpatialStructure")
    }
    changed=[]
    for guid,before in source_containment.items():
        after={x.GlobalId for x in output.by_guid(guid).RelatedElements}
        require(before<=after,"Original containment membership removed")
        if before!=after:
            require(after-before=={door.GlobalId},"Unexpected extra containment members")
            changed.append(guid)
    require(len(changed)==1,"Exactly one original containment relation must add Door")
    require(door.OverallHeight is not None and door.OverallWidth is not None
            and math.isclose(float(door.OverallHeight),2000.,abs_tol=1e-3)
            and math.isclose(float(door.OverallWidth),1000.,abs_tol=1e-3),
            "Door native dimensions are not 2m height × 1m width")
    before,_,before_tris=_native_shape(source,source.by_guid(HOST_GUID))
    after,_,after_tris=_native_shape(output,wall)
    source_host_volume=float(ifcopenshell.util.shape.get_volume(before.geometry))
    resulting_host_volume=float(ifcopenshell.util.shape.get_volume(after.geometry))
    removed_volume=source_host_volume-resulting_host_volume
    require(math.isclose(removed_volume,DOOR_HEIGHT_M*DOOR_WIDTH_M*.2,
                         abs_tol=1e-5,rel_tol=0),
            "Host Wall physical through-cut volume differs from requested opening")
    _,door_v,door_tris=_native_shape(output,door)
    _,opening_v,opening_tris=_native_shape(output,opening)
    require(np.allclose(_bbox(door_v),
                        [23.8,15.08,0.,24.8,15.12,2.],atol=1e-5,rtol=0),
            "Actual native Door world geometry outside fixed source wall center")
    require(np.allclose(_bbox(opening_v),
                        [23.8,14.9,0.,24.8,15.3,2.],atol=1e-5,rtol=0),
            "Actual native Opening does not fully traverse original wall thickness")
    orig_meshes=_original_product_world_mesh_fingerprints(source)
    output_meshes=_original_product_world_mesh_fingerprints(output)
    require(len(orig_meshes)==len(p0) and len(output_meshes)==len(p1),
            "Original native source product mesh inventory changed")
    for g,signature in orig_meshes.items():
        if g==HOST_GUID:
            require(output_meshes[g]!=signature,
                    "Native host wall did not actually change its world triangle mesh")
        else:
            require(output_meshes[g]==signature,
                    "Unrelated existing original native product world triangle mesh changed")
    require(sum(s[1] for s in orig_meshes.values())==39
            and sum(s[1] for g,s in orig_meshes.items() if g!=HOST_GUID)==38,
            "Original mesh-bearing source products drifted")
    return {
        "status":"V035_INDEPENDENT_REAL_NATIVE_HOSTED_DOOR_VOID_FILL_AND_SOURCE_PASS",
        "source_IfcRoot_identifiers_classes_names_preserved":True,
        "source_existing_IfcRoot_count":len(r0),
        "source_existing_IfcProduct_count":len(p0),
        "source_original_mesh_bearing_product_count":39,
        "original_unchanged_nonhost_mesh_bearing_product_count":38,
        "original_nonhost_triangle_face_count":sum(
            v[3] for g,v in orig_meshes.items() if g!=HOST_GUID),
        "original_host_wall_physically_cut":True,
        "host_wall_old_volume_m3":source_host_volume,
        "host_wall_new_volume_m3":resulting_host_volume,
        "host_wall_cut_volume_m3":removed_volume,
        "host_wall_triangle_count_before":before_tris,
        "host_wall_triangle_count_after":after_tris,
        "new_native_door_world_bbox_m":_bbox(door_v),
        "new_native_opening_world_bbox_m":_bbox(opening_v),
        "new_door_triangle_count":door_tris,
        "new_opening_triangle_count":opening_tris,
        "native_door_actual_width_height_m":[1.0,2.0],
        "original_wall_void_and_door_fills_relationships_present":True,
        "original_storey_containment_preserved_and_door_added":True,
        "full_original_native_STEP_lossless_preservation_claimed":False,
    }


def compile_full_declarative_test01_d0(source_mm:Path,out_mm:Path)->dict:
    from src.runtime.experimental_v4_projection import project_ifc_v4
    from src.runtime.experimental_v7_hosted_door_create import (
        compile_declarative_xml_v07_hosted_door_create,
    )
    with TemporaryDirectory(prefix="bmb-v035-xml-original-D0-") as t:
        folder=Path(t)
        metric_source=folder/"original_model_metres.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(source_mm)),"METER").write(str(metric_source))
        projection=project_ifc_v4(metric_source)
        mapping=dict(projection.projected_global_ids)
        require(HOST_GUID in mapping,
                "Original target public Wall not present in read-only XML projection")
        host_id=mapping[HOST_GUID]
        root=etree.fromstring(projection.xml)
        elements=root.find(NS+"Elements")
        require(elements is not None and
                not any(e.get("id") in (XML_OPENING_ID,XML_DOOR_ID) for e in elements),
                "Frozen full XML source already contains proposed IDs")
        etree.SubElement(elements,NS+"Opening",attrib={
            "id":XML_OPENING_ID,"host":host_id,
            "offset":str(OFFSET_FROM_HOST_AXIS_START_M),"sill":"0",
            "width":str(DOOR_WIDTH_M),"height":str(DOOR_HEIGHT_M),
        })
        etree.SubElement(elements,NS+"Door",attrib={
            "id":XML_DOOR_ID,"opening":XML_OPENING_ID,
            "width":str(DOOR_WIDTH_M),"height":str(DOOR_HEIGHT_M),
        })
        edited=etree.tostring(root,encoding="utf8")
        require(edited!=projection.xml,
                "Complete declarative source must differ from original XML")
        output_metric=folder/"compiled_trusted_D0_metric.ifc"
        compiled=compile_declarative_xml_v07_hosted_door_create(
            metric_source,edited,output_metric)
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(output_metric)),"MILLIMETER").write(str(out_mm))
        return {
            **compiled,
            "status":"V035_ORIGINAL_PUBLIC_DOOR_FULL_XML_D0_COMPILED",
            "native_original_mm_candidate_sha256":file_hash(out_mm),
            "new_complete_XML_sha256":sha256(edited).hexdigest(),
        }


def audit_original_test01_pair(root:Path,author:Path,data:Path)->dict:
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Pinned original benchmark author/data commits differ")
    past=[]
    for rel,digest in FROZEN:
        p=root/rel
        require(p.is_file() and not p.is_symlink() and file_hash(p)==digest,
                "Prior frozen report hash mismatch: "+rel)
        past.append(json.loads(p.read_text(encoding="utf8")))
    v031,v032,v033,v034=past
    require(v031["original_intention_to_test_task_count"]==45
            and v031["original45_developer_native_equal_witnesses"]==11
            and v032["original_public_task_id"]=="test_04"
            and v033["original_public_test_id"]=="test_02"
            and v034["original_test_id"]=="test_05"
            and not v034["full_IFC_D0_I0_bytes_equal"]
            and v034["matched_real_LLM_D_I_trials"]==0,
            "Original45/recent developer-only checkpoint evidence drift")
    tasks={x["test_id"]:x for x in public_45(author,data)}
    require(len(tasks)==45 and TASK in tasks,"Original 45 task population changed")
    task=tasks[TASK]
    require(task["crud"]=="create" and task["category"]=="basic"
            and task["original_source_ifc_relpath"]=="basic_tasks.ifc"
            and task["original_ifc_sha256"]==SOURCE_SHA
            and task["public_question_sha256"]==QUESTION_SHA
            and task["public_question"].startswith("Create a door with the size of 2 by 1")
            and HOST_GUID in task["public_question"],
            "Original public test01 instruction/source drift")
    orig=data/"ifc"/"basic_tasks.ifc"
    require(orig.is_file() and not orig.is_symlink()
            and file_hash(orig)==SOURCE_SHA,
            "Original public native IFC source hash changed")
    with TemporaryDirectory(prefix="bmb-v035-source-independent-") as t:
        scratch=Path(t)
        imperative_path=scratch/"independent_python_I0_mm.ifc"
        imperative=create_original_public_test01_door_i0(orig,imperative_path)
        oracle_i=actual_original_native_hosted_door_oracle(
            orig,imperative_path,
            claimed_door_guid=imperative["door_guid"],
            claimed_opening_guid=imperative["opening_guid"])
        native_i=file_hash(imperative_path)
        declarative_path=scratch/"whole_xml_trusted_D0_mm.ifc"
        declarative=compile_full_declarative_test01_d0(orig,declarative_path)
        oracle_d=actual_original_native_hosted_door_oracle(
            orig,declarative_path,
            claimed_door_guid=declarative["created_IfcDoor_guid"],
            claimed_opening_guid=declarative["created_IfcOpeningElement_guid"])
        native_d=file_hash(declarative_path)
        require(oracle_i==oracle_d
                and native_i==imperative["candidate_mm_ifc_sha256"]
                and native_d==declarative["native_original_mm_candidate_sha256"]
                and file_hash(orig)==SOURCE_SHA,
                "Physical native Door I0 and D0 results/oracles differ")
        # Original author scorer is called only AFTER independent two-arm
        # results pass and are frozen. Never imported into either writer.
        from tools.bibimbap_matched25_cli import grade_author
        grade_i=grade_author(author,orig,imperative_path,TASK)
        grade_d=grade_author(author,orig,declarative_path,TASK)
        require(grade_i["status"]=="AUTHOR_SCORED"
                and grade_d["status"]=="AUTHOR_SCORED",
                "Original frozen author grader unavailable")
        require(file_hash(orig)==SOURCE_SHA
                and _head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
                "Original source or frozen upstream revision changed after scoring")
    return {
        "status":"V035_ORIGINAL_PUBLIC_TEST01_HOSTED_DOOR_OPENING_D0_I0_NATIVE_PAIR",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/185",
        "original_45_intention_to_test_denominator":45,
        "original_public_test_id":TASK,
        "original_question_sha256":QUESTION_SHA,
        "original_source_IFC_sha256":SOURCE_SHA,
        "original_author_git_sha":AUTHOR_SHA,
        "original_data_git_sha":DATA_SHA,
        "frozen_previous_report_hashes":dict(FROZEN),
        "public_referenced_existing_host_class":"IfcWall",
        "public_fixed_2_by_1_interpreted_height_2m_width_1m":True,
        "unrequested_centered_wall_zero_sill_predeclared":True,
        "predeclared_opening_position_offset_m":OFFSET_FROM_HOST_AXIS_START_M,
        "predeclared_door_leaf_thickness_m":DOOR_LEAF_THICKNESS_M,
        "predeclared_opening_through_depth_m":OPENING_THROUGH_WALL_DEPTH_M,
        "independent_native_Python_I0_validated_before_XML_D0":True,
        "full_original_declarative_XML_D0_typed_two_node_diff":True,
        "native_actual_independent_oracle_both_arms":oracle_i,
        "native_independent_two_arm_semantic_equivalence":oracle_i==oracle_d,
        "native_whole_IFC_D0_sha256":native_d,
        "native_whole_IFC_I0_sha256":native_i,
        "native_whole_IFC_byte_equal":native_i==native_d,
        "original_author_I0":grade_i,
        "original_author_D0":grade_d,
        "original_author_score_equivalent":grade_i==grade_d,
        "original_author_I0_full_mark":grade_i["original_author_full_mark"],
        "original_author_D0_full_mark":grade_d["original_author_full_mark"],
        "prior_full_native_byte_equal_11_witnesses_unchanged":11,
        "new_distinct_original_Create_semantic_only_developer_pair":not(native_i==native_d),
        "original_Create_task_specific_semantic_paired_count":4,
        "original_Create_tasks_without_positive_native_semantic_pair":11,
        "original45_full_information_read_parity_proven":0,
        "original45_full_native_edit_write_parity_proven":0,
        "matched_real_LLM_D_I_trials":0,
        "new_paid_model_provider_calls":0,
        "model_host_scoped_v07_registered":False,
        "full_original_native_STEP_bytes_or_entities_preserved_claimed":False,
        "causal_representation_effect_permitted":False,
        "original_benchmark_data_GT_evaluator_changed":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--author",type=Path,required=True)
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--write",type=Path)
    a=p.parse_args()
    report=audit_original_test01_pair(a.root,a.author,a.data)
    blob=(json.dumps(report,sort_keys=True,indent=2)+"\n").encode("utf8")
    if a.write:
        a.write.parent.mkdir(parents=True,exist_ok=True)
        with a.write.open("xb") as f:
            f.write(blob)
        print("REPORT_WRITTEN",str(a.write),sha256(blob).hexdigest())
    else:
        print(json.dumps({
            "status":report["status"],
            "native_D0_I0_semantic_pair":report["native_independent_two_arm_semantic_equivalence"],
            "author_D0":report["original_author_D0"]["original_author_score"],
            "author_I0":report["original_author_I0"]["original_author_score"],
            "byte_equal":report["native_whole_IFC_byte_equal"],
            "model_trials":report["matched_real_LLM_D_I_trials"],
        },sort_keys=True))


if __name__=="__main__":
    main()
