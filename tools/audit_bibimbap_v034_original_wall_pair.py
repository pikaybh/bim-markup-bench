"""Actual original BIBIMBAP test_05 Wall Create native D0/I0 evidence.

Order is source-first: pinned public task -> independent imperative native I0
-> independent native oracle -> complete XML D0 via opt-in scoped v0.6
-> identical native oracle -> original author grader AFTER both candidates.
Do not reinterpret weak author scores as LLM failures or tune assumptions.
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
import ifcopenshell.util.unit
from lxml import etree
import numpy as np

from tools.audit_bibimbap_author import AUTHOR_SHA,DATA_SHA,_head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v034_original_wall_i0 import (
    SPEC,SOURCE_SHA,EXPECTED_BODY_BBOX_M,AXIS_START_M,AXIS_END_M,
    create_original_test05_wall_i0,
)
from tools.audit_bibimbap_v033_original_slab_pair import (
    _original_product_world_mesh_fingerprints,
)

ROOT=Path(__file__).resolve().parents[1]
TASK="test_05"
QUESTION_SHA="222cd92c3b4d9eae335aadda7511eadac9e65e5b1f22776ba8f7c1beb13cf4d0"
SOURCE_FILE="basic_tasks.ifc"
XML_ID="v034_wall_predeclared_test05"
NS="{urn:bim-markup-bench:toy:v0}"
PREVIOUS_REPORTS=(
    ("reports/bibimbap_v031_original45_eligibility_and_overlap_20261117.json",
     "d6680b3eadb5733be547c09ab8deed58dd48c7feaccbc3cb562b6e60b475c7dd"),
    ("reports/bibimbap_v032_original_test04_column_D0_I0_native_semantic_pair_20261117.json",
     "65cd592b83b06ac161ff420982cb2f3378e850613f4645419690e06764987b2b"),
    ("reports/bibimbap_v033_original_test02_slab_D0_I0_semantic_pair_20261117.json",
     "998064e23a0b3955b20a0ca1a7cabcb4424a612af1d633e42cd179f5e68ce660"),
)


class OriginalWallV034Blocked(ValueError):
    pass


def require(condition:bool,why:str)->None:
    if not condition:
        raise OriginalWallV034Blocked(why)


def pinned_json(root:Path,pair:tuple[str,str])->dict:
    path=root/pair[0]
    require(path.is_file() and not path.is_symlink() and file_hash(path)==pair[1],
            "Frozen prior checkpoint evidence SHA drift: "+pair[0])
    return json.loads(path.read_text(encoding="utf8"))


def _native_wall_axis(world_wall,scale:float):
    """World-space native Axis endpoints in metres, no D0 writer imports."""
    reps=world_wall.Representation.Representations if world_wall.Representation else ()
    if len(reps)!=2:
        raise OriginalWallV034Blocked("Physical wall should contain Body and Axis representations")
    axes=[r for r in reps if r.RepresentationIdentifier=="Axis"]
    bodies=[r for r in reps if r.RepresentationIdentifier=="Body"]
    require(len(axes)==1 and len(bodies)==1, "Expected one Wall Axis and Body")
    require(len(axes[0].Items)==1,"Expected unique native wall axis")
    line=axes[0].Items[0]
    if line.is_a("IfcIndexedPolyCurve") and line.Segments is None:
        coords=line.Points.CoordList
    elif line.is_a("IfcPolyline"):
        coords=[x.Coordinates for x in line.Points]
    else:
        raise OriginalWallV034Blocked("Unsupported new native axis curve")
    require(len(coords)==2 and len(coords[0])==len(coords[1])==2,
            "Native wall axis must consist of two 2D endpoints")
    transform=ifcopenshell.util.placement.get_local_placement(world_wall.ObjectPlacement)
    actual=[]
    for coord in coords:
        point=transform@np.array([coord[0],coord[1],0.,1.],dtype=float)
        actual.append(tuple(float(v)*scale for v in point[:3]))
    return actual,bodies[0]


def verify_new_native_original_wall(source_mm:Path,candidate_mm:Path,
                                    expected_new_guid:str|None=None)->dict:
    """Independent actual saved IFC scene check; no declarative compiler or grader."""
    require(source_mm.is_file() and candidate_mm.is_file()
            and source_mm.resolve()!=candidate_mm.resolve(),
            "Original source and independent native result must be separate")
    original=ifcopenshell.open(str(source_mm))
    candidate=ifcopenshell.open(str(candidate_mm))
    scale=ifcopenshell.util.unit.calculate_unit_scale(original)
    require(original.schema==candidate.schema=="IFC4X3" and abs(scale-.001)<1e-12
            and abs(ifcopenshell.util.unit.calculate_unit_scale(candidate)-scale)<1e-12,
            "Pinned original IFC4X3 millimetre context changed")
    a_roots={x.GlobalId:x for x in original.by_type("IfcRoot")}
    b_roots={x.GlobalId:x for x in candidate.by_type("IfcRoot")}
    require(len(a_roots)==len(original.by_type("IfcRoot"))
            and len(b_roots)==len(candidate.by_type("IfcRoot"))
            and set(a_roots)<=set(b_roots),
            "Preexisting native Root identity lost/duplicate")
    for guid,old in a_roots.items():
        new=b_roots[guid]
        require(old.is_a()==new.is_a() and old.Name==new.Name
                and old.Description==new.Description,
                "Existing native IFC Root class/name/description changed")
    a_products={x.GlobalId:x for x in original.by_type("IfcProduct")}
    b_products={x.GlobalId:x for x in candidate.by_type("IfcProduct")}
    require(set(a_products)<set(b_products)
            and len(b_products)==len(a_products)+1,
            "Exactly one new original-native IFC Product must be created")
    fresh=set(b_products)-set(a_products)
    require(len(fresh)==1,"Exactly one physical Wall product required")
    guid=next(iter(fresh))
    if expected_new_guid is not None:
        require(guid==expected_new_guid, "Created Wall identity differs from declared writer")
    wall=b_products[guid]
    require(wall.is_a("IfcWall"),"New native product is not IfcWall")
    new_roots=set(b_roots)-set(a_roots)
    require(new_roots>={guid} and all(
        g==guid or b_roots[g].is_a("IfcRelContainedInSpatialStructure")
        for g in new_roots), "Unexpected new root entities during Wall creation")
    level=ifcopenshell.util.element.get_container(wall)
    require(level is not None and level.GlobalId in a_roots
            and level.is_a("IfcBuildingStorey") and level.Name=="L1"
            and level.Elevation is not None and abs(float(level.Elevation))<1e-8,
            "New native Wall not in original ground storey")
    mutated_rel=[]
    for rel in original.by_type("IfcRelContainedInSpatialStructure"):
        before={x.GlobalId for x in rel.RelatedElements}
        after={x.GlobalId for x in candidate.by_guid(rel.GlobalId).RelatedElements}
        require(before<=after,"Existing native containment member lost")
        if before!=after:
            require(after-before=={guid},"Unrelated IFC native member added")
            mutated_rel.append(rel.GlobalId)
    require(len(mutated_rel)==1,"Original ground containment must grow by exactly one")
    axis,body=_native_wall_axis(wall,scale)
    for actual,expected in zip(axis,(AXIS_START_M,AXIS_END_M)):
        require(np.allclose(actual,expected,atol=1e-5,rtol=0),
                "New native Wall world axis position or length differs from public fixture")
    solids=[x for x in body.Items if x.is_a("IfcExtrudedAreaSolid")]
    require(len(solids)==1 and math.isclose(float(solids[0].Depth)*scale,3.,
                                           abs_tol=1e-5,rel_tol=0),
            "New Wall actual native extrusion height differs")
    settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
    shape=ifcopenshell.geom.create_shape(settings,wall)
    vertices=np.asarray(shape.geometry.verts,dtype=float)
    require(vertices.size>=18 and vertices.size%3==0 and np.isfinite(vertices).all(),
            "New native wall physical mesh missing")
    corners=vertices.reshape(-1,3)
    bbox=tuple(float(x) for x in (*corners.min(axis=0),*corners.max(axis=0)))
    require(np.allclose(bbox,EXPECTED_BODY_BBOX_M,atol=1e-5,rtol=0),
            "Native Wall world physical body differs from source-only public fixture")
    old_meshes=_original_product_world_mesh_fingerprints(original)
    new_meshes=_original_product_world_mesh_fingerprints(candidate)
    for existing,mesh in old_meshes.items():
        require(new_meshes.get(existing)==mesh,
                "Existing original native world triangle mesh changed")
    require(len(old_meshes)==len(a_products),"Original product scene inventory changed")
    return {
        "status":"V034_INDEPENDENT_NATIVE_ORIGINAL_PUBLIC_WALL_AND_SOURCE_PRESERVATION_PASS",
        "new_wall_native_original_L1":True,
        "new_wall_exact_axis_start_end_m":[list(p) for p in axis],
        "new_wall_world_body_bbox_m":list(bbox),
        "new_wall_extrusion_height_m":float(solids[0].Depth)*scale,
        "existing_native_IfcRoot_identity_class_name_preserved":True,
        "existing_original_native_IfcRoot_count":len(a_roots),
        "existing_original_native_IfcProduct_count":len(a_products),
        "existing_native_world_mesh_object_count":sum(x[1] for x in old_meshes.values()),
        "existing_world_mesh_original_triangle_face_count":sum(x[3] for x in old_meshes.values()),
        "all_preexisting_original_IfcProduct_world_meshes_unchanged":True,
        "existing_original_containment_relations_preserved":True,
        "whole_original_IFC_STEP_entity_preservation_proven":False,
    }


def create_full_declarative_D0(source_mm:Path,out_mm:Path)->dict:
    """Scoped complete XML state + previously separate opt-in v0.6 compiler."""
    from src.runtime.experimental_v4_projection import project_ifc_v4
    from src.runtime.experimental_v6_wall_create import compile_declarative_xml_v6_wall_create
    with TemporaryDirectory(prefix="bmb-v034-xml-D0-") as td:
        folder=Path(td)
        source_m=folder/"original_m.ifc"
        original=ifcopenshell.open(str(source_mm))
        ifcopenshell.util.unit.convert_file_length_units(
            original,"METER").write(str(source_m))
        projected=project_ifc_v4(source_m)
        xml=etree.fromstring(projected.xml)
        els=xml.find(NS+"Elements")
        levels=xml.find(NS+"Levels")
        require(els is not None and levels is not None
                and all(x.get("id")!=XML_ID for x in els),
                "Original full XML structure or new stable ID corrupted")
        ground=[x for x in levels if x.get("elevation") is not None
                and abs(float(x.get("elevation")))<1e-8]
        require(len(ground)==1,"Original level cannot be uniquely identified")
        x1,y1,z1,x2,y2,z2,h,t=SPEC
        attrs={
            "id":XML_ID,"level":ground[0].get("id"),
            "x1":str(x1),"y1":str(y1),"z1":str(z1),
            "x2":str(x2),"y2":str(y2),"z2":str(z2),
            "height":str(h),"thickness":str(t),
        }
        etree.SubElement(els,NS+"Wall",attrib=attrs)
        edited=etree.tostring(xml,encoding="utf8")
        require(edited!=projected.xml,"No new complete declarative Wall state")
        native_metric=folder/"compiled_original_wall_m.ifc"
        report=compile_declarative_xml_v6_wall_create(source_m,edited,native_metric)
        require([item.operation for item in report.operations]==["CREATE_WALL"],
                "D0 XML must derive exactly one native Wall create")
        native_mm=ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(native_metric)),"MILLIMETER")
        native_mm.write(str(out_mm))
        return {
            "status":report.as_dict()["status"],
            "new_native_wall_guid":report.operations[0].ifc_guid,
            "complete_declarative_XML_one_added_Wall":True,
            "XML_does_not_contain_imperative_Create_opcode":True,
            "compiled_XML_sha256":sha256(edited).hexdigest(),
            "candidate_native_original_mm_sha256":file_hash(out_mm),
            "compiler":"experimental-wall-create-v0.6",
        }


def audit_original_test05_wall_pair(root:Path,author:Path,data:Path)->dict:
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Pinned original author/data Git revision drift")
    past=[pinned_json(root,pair) for pair in PREVIOUS_REPORTS]
    v031,v032,v033=past
    require(v031["original_intention_to_test_task_count"]==45
            and v031["original45_developer_native_equal_witnesses"]==11
            and v032["original_public_task_id"]=="test_04"
            and v032["native_full_D0_I0_bytes_equal"] is False
            and v033["original_public_test_id"]=="test_02"
            and v033["native_entire_D0_I0_IFC_byte_equal"] is False
            and v033["original_CREATE_semantic_only_developer_pairs_after_v033"]==2,
            "Frozen earlier ITT/native witness accounting changed")
    public={x["test_id"]:x for x in public_45(author,data)}
    require(len(public)==45 and TASK in public,
            "Original benchmark 45 public task population altered")
    task=public[TASK]
    require(task["crud"]=="create" and task["category"]=="basic"
            and task["original_source_ifc_relpath"]==SOURCE_FILE
            and task["original_ifc_sha256"]==SOURCE_SHA
            and task["public_question_sha256"]==QUESTION_SHA,
            "Original public wall task provenance drift")
    question=task["public_question"].lower()
    require("wall" in question and "15m" in question and "(0, -10)" in question,
            "Frozen original public Wall instruction differs")
    orig=data/"ifc"/SOURCE_FILE
    require(orig.is_file() and not orig.is_symlink()
            and file_hash(orig)==SOURCE_SHA,"Original native IFC source changed")
    with TemporaryDirectory(prefix="bmb-v034-original-public-wall-") as folder:
        td=Path(folder)
        i0_path=td/"separate_independent_I0_native_mm.ifc"
        i0=create_original_test05_wall_i0(orig,i0_path)
        i_check=verify_new_native_original_wall(orig,i0_path,i0["new_native_IfcWall_GUID"])
        i_sha=file_hash(i0_path)
        d0_path=td/"separate_complete_XML_D0_native_mm.ifc"
        d0=create_full_declarative_D0(orig,d0_path)
        d_check=verify_new_native_original_wall(orig,d0_path,d0["new_native_wall_guid"])
        d_sha=file_hash(d0_path)
        require(i_check==d_check and file_hash(orig)==SOURCE_SHA
                and i_sha==i0["new_candidate_native_mm_ifc_SHA256"]
                and d_sha==d0["candidate_native_original_mm_sha256"],
                "Independently written Wall D0/I0 geometry/source audits disagree")
        # Unmodified original-author grader accessed ONLY after the pair is frozen.
        from tools.bibimbap_matched25_cli import grade_author
        author_i=grade_author(author,orig,i0_path,TASK)
        author_d=grade_author(author,orig,d0_path,TASK)
        require(author_i["status"]=="AUTHOR_SCORED" and
                author_d["status"]=="AUTHOR_SCORED",
                "Original author Wall scorer did not produce transparent scores")
        require(file_hash(orig)==SOURCE_SHA and
                _head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
                "Original author/data/source drift after grade")
    return {
        "status":"V034_ORIGINAL_PUBLIC_TEST05_WALL_CREATE_ACTUAL_D0_I0_NATIVE_PAIRED_DEVELOPER_CONTROL",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/183",
        "original_45_intention_to_test_unchanged":45,
        "original_test_id":TASK,
        "original_public_task_question_SHA256":QUESTION_SHA,
        "original_IFC_native_input_SHA256":SOURCE_SHA,
        "original_author_git_sha":AUTHOR_SHA,
        "original_dataset_git_sha":DATA_SHA,
        "frozen_prior_reports_SHA256":{r:h for r,h in PREVIOUS_REPORTS},
        "original_IFC4X3_native_length_units":"MILLIMETRE",
        "original_public_spec_fixes_axis_only_start_and_length":True,
        "developer_assumed_positive_X_direction_height_3m_thickness_0_2m":True,
        "predeclared_world_axis_start_m":list(AXIS_START_M),
        "predeclared_world_axis_end_m":list(AXIS_END_M),
        "predeclared_h_height_m":3.,
        "predeclared_t_thickness_m":.2,
        "I0_independent_Python_native_IFC_executed_before_XML_D0":True,
        "D0_uses_full_declarative_XML_state_and_sandboxed_scoped_v06_compiler":True,
        "old_v05_update_delete_wall_compiler_unchanged":True,
        "native_independent_original_IFC_semantic_oracle_both":i_check,
        "native_geometry_axis_source_products_equivalent":i_check==d_check,
        "actual_original_IFC_D0_SHA256":d_sha,
        "actual_original_IFC_I0_SHA256":i_sha,
        "full_IFC_D0_I0_bytes_equal":i_sha==d_sha,
        "original_author_D0":author_d,
        "original_author_I0":author_i,
        "original_author_scores_equal":author_i==author_d,
        "original_author_D0_full_score":author_d["original_author_score"]==1.,
        "original_author_I0_full_score":author_i["original_author_score"]==1.,
        "previous_full_native_byte_equal_developer_11_unchanged":11,
        "cumulative_full_native_byte_equal_developer_witnesses":11+int(i_sha==d_sha),
        "previous_two_original_CREATE_semantic_only_cases_unchanged":True,
        "new_Create_semantic_only_developer_case":not (i_sha==d_sha),
        "original_Create_cases_without_semantically_validated_developer_pair":12,
        "original45_full_information_read_parity_proven":0,
        "original45_full_native_edit_write_parity_proven":0,
        "matched_real_LLM_D_I_trials":0,
        "paid_provider_requests":0,
        "this_is_not_a_causal_LLM_benchmark_result":True,
        "model_host_new_v06_Wall_compiler_available":False,
        "full_building_collision_oracle_proven":False,
        "original_author_hidden_targets_not_used_for_writers":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--author",type=Path,required=True)
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--write",type=Path)
    args=p.parse_args()
    result=audit_original_test05_wall_pair(args.root,args.author,args.data)
    payload=(json.dumps(result,sort_keys=True,indent=2)+"\n").encode("utf8")
    if args.write:
        args.write.parent.mkdir(parents=True,exist_ok=True)
        with args.write.open("xb") as out:
            out.write(payload)
        print("WROTE",args.write,sha256(payload).hexdigest())
    else:
        print(json.dumps({
            "status":result["status"],
            "actual_native_equivalence":result["native_geometry_axis_source_products_equivalent"],
            "D0_author_score":result["original_author_D0"]["original_author_score"],
            "I0_author_score":result["original_author_I0"]["original_author_score"],
            "full_native_bytes_equal":result["full_IFC_D0_I0_bytes_equal"],
            "paid_LLM_calls":result["paid_provider_requests"],
        },sort_keys=True))


if __name__=="__main__":
    main()
