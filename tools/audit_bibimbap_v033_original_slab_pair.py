"""Original BIBIMBAP public test_02 native Slab CREATE D0/I0 control (v0.33).

Order: original public source -> standalone imperative I0 -> independent actual
native IFC oracle -> complete declarative XML D0 -> identical external oracle
-> both separately unchanged original author scores. Not a matched LLM result.
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
import ifcopenshell.util.unit
from lxml import etree
import numpy as np

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v033_original_slab_i0 import (
    SOURCE_SHA, SPEC_METRES, EXPECTED_BBOX_METRES,
    create_independent_original_test02_i0,
)

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/pikaybh/bim-markup-bench/issues/181"
TASK = "test_02"
QUESTION_SHA = "b11d1746b2a59a6b346bbcf643aa5ae738f6719d31babe9468ca8d90209592d3"
REPORT_V032 = (
    "reports/bibimbap_v032_original_test04_column_D0_I0_native_semantic_pair_20261117.json",
    "65cd592b83b06ac161ff420982cb2f3378e850613f4645419690e06764987b2b",
)
REPORT_HISTORICAL_D0 = (
    "reports/bibimbap_v04_slab_developer_d0_20261113.json",
    "98166dc3a6c606996a5f9bd43e3b0b26fb2852fb61e1c64ea1154aaefc630fec",
)
REPORT_V031 = (
    "reports/bibimbap_v031_original45_eligibility_and_overlap_20261117.json",
    "d6680b3eadb5733be547c09ab8deed58dd48c7feaccbc3cb562b6e60b475c7dd",
)
XML_SLAB_ID = "d0_predeclared_public_rectangle"
XML_NS = "{urn:bim-markup-bench:toy:v0}"


class OriginalSlabV033Blocked(ValueError):
    pass


def require(test: bool, message: str) -> None:
    if not test:
        raise OriginalSlabV033Blocked(message)


def _pinned_json(root: Path, name_hash: tuple[str, str]) -> dict:
    relative, digest = name_hash
    path=root / relative
    require(path.is_file() and not path.is_symlink()
            and file_hash(path)==digest, f"Pinned historical evidence SHA drift: {relative}")
    return json.loads(path.read_text(encoding="utf8"))


def _original_product_world_mesh_fingerprints(model: ifcopenshell.file) -> dict:
    """Independent actual 3D triangle-mesh fingerprints, not just bounding boxes.

    Ignore vertex/face order but preserve every world-space triangle and
    multiplicity, quantized to 1 micron. No target answer or grading is read.
    """
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    result={}
    for product in model.by_type("IfcProduct"):
        guid=product.GlobalId
        require(guid not in result,"Duplicated original native product GUID")
        if product.Representation is None:
            result[guid]=(product.is_a(),False,None,0)
            continue
        try:
            shape=ifcopenshell.geom.create_shape(settings,product)
            verts=np.asarray(shape.geometry.verts,dtype=float)
            faces=np.asarray(shape.geometry.faces,dtype=int)
        except Exception as exc:
            raise OriginalSlabV033Blocked(
                "Native original product world triangle mesh not computable") from exc
        require(verts.size>=9 and verts.size%3==0 and faces.size>=3
                and faces.size%3==0 and np.isfinite(verts).all(),
                "Original source native product is missing valid world triangles")
        xyz=verts.reshape(-1,3)
        triangles=faces.reshape(-1,3)
        require(np.min(triangles)>=0 and np.max(triangles)<len(xyz),
                "Native triangular face references out of vertex range")
        coords=tuple(tuple(int(round(value*1_000_000)) for value in row)
                     for row in xyz)
        canonical=tuple(sorted(tuple(sorted(coords[int(i)] for i in face))
                               for face in triangles))
        fingerprint=sha256(repr(canonical).encode("ascii")).hexdigest()
        result[guid]=(product.is_a(),True,fingerprint,len(canonical))
    return result


def verify_original_native_slab_create(
    original: Path, candidate: Path, expected_new_guid: str | None = None,
) -> dict:
    """Read-only actual IFC verifier, independent of D0 and I0 writers."""
    from tools.audit_bibimbap_v032_original_column_pair import (
        native_original_product_geometry,
    )
    require(original.is_file() and candidate.is_file()
            and original.resolve()!=candidate.resolve(),
            "Two separate actual native IFC files are required")
    a=ifcopenshell.open(str(original))
    b=ifcopenshell.open(str(candidate))
    require(a.schema==b.schema=="IFC4X3"
            and abs(ifcopenshell.util.unit.calculate_unit_scale(a)-0.001)<1e-12
            and abs(ifcopenshell.util.unit.calculate_unit_scale(b)-0.001)<1e-12,
            "Original IFC4X3 native millimetre schema/units changed")
    original_roots={x.GlobalId:x for x in a.by_type("IfcRoot")}
    result_roots={x.GlobalId:x for x in b.by_type("IfcRoot")}
    require(len(original_roots)==len(a.by_type("IfcRoot"))
            and len(result_roots)==len(b.by_type("IfcRoot"))
            and set(original_roots)<=set(result_roots),
            "Original IFC Root GUIDs deleted or duplicated")
    for g, old in original_roots.items():
        new=result_roots[g]
        require(old.is_a()==new.is_a()
                and old.Name==new.Name and old.Description==new.Description,
                "Original IFC Root identity/class/name/description changed")
    source_products={x.GlobalId:x for x in a.by_type("IfcProduct")}
    output_products={x.GlobalId:x for x in b.by_type("IfcProduct")}
    require(set(source_products)<set(output_products)
            and len(output_products)==len(source_products)+1,
            "Exactly one new native IFC product required, originals preserved")
    extra=set(output_products)-set(source_products)
    require(len(extra)==1, "Expected exactly one created native product")
    new_guid=next(iter(extra))
    if expected_new_guid is not None:
        require(new_guid==expected_new_guid, "New created native Slab GUID disagrees with writer claim")
    slab=output_products[new_guid]
    require(slab.is_a("IfcSlab") and slab.PredefinedType=="FLOOR",
            "Expected one new physical native FLOOR IfcSlab")
    extra_roots=set(result_roots)-set(original_roots)
    require(extra_roots>={new_guid}
            and all(g==new_guid or
                    result_roots[g].is_a("IfcRelContainedInSpatialStructure")
                    for g in extra_roots),
            "Unexpected other root classes created")
    level=ifcopenshell.util.element.get_container(slab)
    require(level is not None and level.GlobalId in original_roots
            and level.is_a("IfcBuildingStorey") and level.Name=="L1"
            and level.Elevation is not None and abs(float(level.Elevation))<1e-8,
            "Slab not contained in original zero-elevation L1")
    contained=[]
    for rel in a.by_type("IfcRelContainedInSpatialStructure"):
        old={x.GlobalId for x in rel.RelatedElements}
        newrel=b.by_guid(rel.GlobalId)
        follow={x.GlobalId for x in newrel.RelatedElements}
        require(old<=follow, "Preexisting native containment member removed")
        if old!=follow:
            require(follow-old=={new_guid}, "Unexpected native containment member changed")
            contained.append(rel.GlobalId)
    require(len(contained)==1, "Created Slab must extend one original native containment relation")
    require(slab.Representation is not None, "Created slab has no native shape")
    solids=[x for rep in slab.Representation.Representations for x in rep.Items
            if x.is_a("IfcExtrudedAreaSolid")]
    require(len(solids)==1 and math.isclose(float(solids[0].Depth),200.,
                                           rel_tol=0,abs_tol=1e-4),
            "Created slab native 200 mm extrusion thickness missing")
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    mesh=ifcopenshell.geom.create_shape(settings,slab)
    vertices=np.array(mesh.geometry.verts, dtype=float)
    require(vertices.size>=24 and vertices.size%3==0 and np.isfinite(vertices).all(),
            "Created slab physical native 3D mesh missing")
    xyz=vertices.reshape(-1,3)
    bbox=tuple(float(v) for v in (*xyz.min(axis=0), *xyz.max(axis=0)))
    require(all(math.isclose(v,w,rel_tol=0,abs_tol=1e-5)
                for v,w in zip(bbox,EXPECTED_BBOX_METRES)),
            "Physical slab geometry differs from fixed public instruction")
    old_geom=native_original_product_geometry(a)
    new_geom=native_original_product_geometry(b)
    for guid, older in old_geom.items():
        fresh=new_geom[guid]
        require(older[:2]==fresh[:2], "Original product type/geometry availability changed")
        if older[2] is not None:
            require(all(math.isclose(x,y,rel_tol=0,abs_tol=1e-5)
                        for x,y in zip(older[2], fresh[2])),
                    "Original native product world geometry was changed")
    original_meshes=_original_product_world_mesh_fingerprints(a)
    candidate_meshes=_original_product_world_mesh_fingerprints(b)
    for original_guid, original_mesh in original_meshes.items():
        require(candidate_meshes.get(original_guid)==original_mesh,
                "Existing original native world-space triangle mesh changed")
    require(len(original_meshes)==len(source_products),
            "Native original mesh inventory incomplete")
    return {
        "status":"INDEPENDENT_ORIGINAL_PUBLIC_NATIVE_SLAB_CREATE_GEOMETRY_AND_SOURCE_PASS",
        "original_IfcRoot_identity_class_name_description_preserved":True,
        "original_native_root_count":len(original_roots),
        "original_native_product_count":len(source_products),
        "original_native_product_world_shapes_verified":sum(x[1] for x in old_geom.values()),
        "original_native_products_without_shape":sum(not x[1] for x in old_geom.values()),
        "one_and_only_one_new_physical_native_IfcSlab":True,
        "new_native_slab_PredefinedType":"FLOOR",
        "original_storey_L1_containment_preserved_extended_by_one":True,
        "native_new_slab_bbox_m":list(bbox),
        "native_new_slab_extrusion_thickness_mm":float(solids[0].Depth),
        "all_original_product_native_world_shapes_preserved":True,
        "all_original_product_native_world_triangle_meshes_preserved":True,
        "original_product_triangle_faces_independently_compared":sum(
            signature[3] for signature in original_meshes.values()),
    }


def compile_one_full_declarative_slab_D0(original_mm: Path, output_mm: Path) -> dict:
    """Full XML-state Slab addition with old scoped v0.4 trusted native backend."""
    from src.runtime.experimental_v4_projection import project_ifc_v4
    from src.runtime.experimental_v4_slab import compile_declarative_xml_v4

    original=ifcopenshell.open(str(original_mm))
    with TemporaryDirectory(prefix="bmb-v033-full-xml-D0-") as td:
        folder=Path(td)
        source_m=folder/"original_metric_m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(original,"METER").write(
            str(source_m))
        projected=project_ifc_v4(source_m)
        root=etree.fromstring(projected.xml)
        els=root.find(XML_NS+"Elements")
        storeys=root.find(XML_NS+"Levels")
        require(els is not None and storeys is not None
                and not any(x.get("id")==XML_SLAB_ID for x in els),
                "Original full XML source structure/ID invalid")
        ground=[s for s in storeys if s.get("elevation") is not None
                and float(s.get("elevation"))==0.]
        require(len(ground)==1, "Ground source storey ambiguous in declarative XML")
        x,y,z,width,depth,thickness=SPEC_METRES
        attrs={
            "id":XML_SLAB_ID,"level":ground[0].get("id"),
            "x":str(x),"y":str(y),"z":str(z),
            "width":str(width),"depth":str(depth),"thickness":str(thickness),
        }
        etree.SubElement(els,XML_NS+"Slab",attrib=attrs)
        edited=etree.tostring(root,encoding="utf8")
        require(edited!=projected.xml, "No whole-XML source change submitted")
        metric_out=folder/"native_candidate_m.ifc"
        result=compile_declarative_xml_v4(source_m,edited,metric_out)
        require([change.operation for change in result.operations]==["CREATE_SLAB"],
                "Whole declarative XML did not compile one Slab Create")
        native=ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(metric_out)),"MILLIMETER")
        native.write(str(output_mm))
        return {
            "status":result.as_dict()["status"],
            "existing_experimental_D0_compiler_version":"experimental-slab-v0.4",
            "full_declarative_XML_with_exactly_one_new_Slab":True,
            "no_imperative_operations_inside_XML":True,
            "new_native_slab_guid":result.operations[0].ifc_guid,
            "full_updated_XML_sha256":sha256(edited).hexdigest(),
            "result_original_mm_native_IFC_sha256":file_hash(output_mm),
        }


def audit_original_public_test02(root: Path, author: Path, data: Path) -> dict:
    root=Path(root)
    require(_head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
            "Frozen original BIBIMBAP author/data Git revisions changed")
    v031=_pinned_json(root,REPORT_V031)
    v032=_pinned_json(root,REPORT_V032)
    prior=_pinned_json(root,REPORT_HISTORICAL_D0)
    require(v031["original_intention_to_test_task_count"]==45
            and v031["original45_developer_native_equal_witnesses"]==11
            and v031["matched_D_I_LLM_trials_executed"]==0,
            "v0.31 original 45 denominator/developer evidence drift")
    prior_case=[x for x in prior["tasks"] if x["original_public_task_id"]==TASK]
    require(len(prior_case)==1
            and prior_case[0]["original_source_ifc_sha256"]==SOURCE_SHA
            and prior_case[0]["public_question_sha256"]==QUESTION_SHA
            and prior_case[0]["original_author_grade_after_compilation"]["original_author_score"]==1.0
            and prior_case[0]["developer_fixed_input_not_model"] is True,
            "Previously frozen original-public Slab D0 developer witness changed")
    require(v032["original_public_task_id"]=="test_04"
            and v032["new_separate_semantic_only_original_public_create_pair_count"]==1
            and v032["native_full_D0_I0_bytes_equal"] is False
            and v032["matched_real_D_I_LLM_trials"]==0,
            "v0.32 original Create semantic-only witness drift")
    all45={x["test_id"]:x for x in public_45(author,data)}
    require(len(all45)==45 and TASK in all45,
            "Original45 population missing or changed")
    task=all45[TASK]
    require(task["crud"]=="create" and task["category"]=="basic"
            and task["original_source_ifc_relpath"]=="basic_tasks.ifc"
            and task["original_ifc_sha256"]==SOURCE_SHA
            and task["public_question_sha256"]==QUESTION_SHA,
            "Public original Slab task provenance drift")
    prompt=task["public_question"].lower()
    require("slab" in prompt and "10 by 5" in prompt
            and "20 centimeters" in prompt and "(-30, 0)" in prompt,
            "Original public Slab task wording changed")
    source=data/"ifc"/task["original_source_ifc_relpath"]
    require(source.is_file() and not source.is_symlink()
            and file_hash(source)==SOURCE_SHA,
            "Pinned original native source IFC changed")

    with TemporaryDirectory(prefix="bmb-v033-public-original-test02-") as td:
        scratch=Path(td)
        i_file=scratch/"separate_I0_native_original_mm.ifc"
        # Imperative writer imported before any XML v0.4 authoring or grader.
        i_summary=create_independent_original_test02_i0(source,i_file)
        i_audit=verify_original_native_slab_create(
            source,i_file,expected_new_guid=i_summary["new_native_slab_guid"])
        i_sha=file_hash(i_file)
        d_file=scratch/"separate_D0_native_original_mm.ifc"
        d_summary=compile_one_full_declarative_slab_D0(source,d_file)
        d_audit=verify_original_native_slab_create(
            source,d_file,expected_new_guid=d_summary["new_native_slab_guid"])
        d_sha=file_hash(d_file)
        require(i_audit==d_audit
                and i_sha==i_summary["candidate_original_mm_ifc_sha256"]
                and d_sha==d_summary["result_original_mm_native_IFC_sha256"]
                and file_hash(source)==SOURCE_SHA,
                "Two separately authored Slab native results/oracles disagree")
        # Hidden original grader remains outside both authoring scripts.
        from tools.bibimbap_matched25_cli import grade_author
        grade_i=grade_author(author,source,i_file,TASK)
        grade_d=grade_author(author,source,d_file,TASK)
        require(grade_i==grade_d
                and grade_i["status"]=="AUTHOR_SCORED"
                and grade_i["original_author_score"]==1.0
                and grade_i["original_author_full_mark"] is True
                and grade_i["original_author_metrics"] == {
                    "integrity_constraint":1.0,"object_exists":1.0,
                    "right_dimensions":1.0,"right_location":1.0,
                }, "Original unchanged author Slab scores unequal or not full")
        require(file_hash(source)==SOURCE_SHA
                and _head(author)==AUTHOR_SHA and _head(data)==DATA_SHA,
                "Original benchmark source/data/author changes detected after graders")
    return {
        "status":"V033_ORIGINAL_PUBLIC_TEST02_PHYSICAL_SLAB_CREATE_INDEPENDENT_D0_I0_SEMANTIC_PAIR",
        "issue":ISSUE,
        "original_public45_denominator_unchanged":45,
        "original_public_test_id":TASK,
        "original_public_question_sha256":QUESTION_SHA,
        "original_public_source_ifc_sha256":SOURCE_SHA,
        "original_author_pinned_git_sha":AUTHOR_SHA,
        "original_dataset_pinned_git_sha":DATA_SHA,
        "frozen_prior_v031_sha256":REPORT_V031[1],
        "frozen_prior_v032_sha256":REPORT_V032[1],
        "frozen_historical_D0_v04_sha256":REPORT_HISTORICAL_D0[1],
        "predeclared_public_slab_xyz_dimensions_thickness_m":list(SPEC_METRES),
        "original_public_IFC_schema_units":"IFC4X3_NATIVE_MILLIMETRES",
        "independent_Python_I0_wrote_actual_IFC_before_D0_XML_compilation":True,
        "trusted_D0_source_is_full_declarative_XML_state":True,
        "native_IfcProduct_and_IfcRoot_source_preservation_both_arms":True,
        "independent_task_specific_native_geometric_semantic_pair_equivalent":True,
        "native_independent_slab_verification_both_arms":i_audit,
        "native_original_full_IFC_D0_SHA256":d_sha,
        "native_original_full_IFC_I0_SHA256":i_sha,
        "native_entire_D0_I0_IFC_byte_equal":d_sha==i_sha,
        "original_author_D0_score":grade_d,
        "original_author_I0_score":grade_i,
        "original_author_full_score_equal_both_arms":True,
        "prior_11_original_native_full_IFC_byte_equal_developer_cases_unchanged":11,
        "new_original_native_full_IFC_byte_equal_developer_cases":11+int(d_sha==i_sha),
        "original_CREATE_semantic_only_developer_pairs_after_v033": (
            2-int(d_sha==i_sha)),
        "original_CREATE_cases_without_test_specific_semantic_pair":13,
        "original45_full_source_information_equivalence_proven":0,
        "original45_full_native_write_capability_equivalence_proven":0,
        "matched_real_D_I_LLM_trials":0,
        "paid_model_requests":0,
        "causal_source_representation_effect_claim_permitted":False,
        "full_original45_original_author_scorer_parity_established":False,
        "no_original_IFC_author_data_or_past_result_modified":True,
        "full_building_collision_oracle_complete":False,
        "underlying_model_host_enables_this_v04_D0_backend":False,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--author",type=Path,required=True)
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--write",type=Path,help="Create report once, no overwrite")
    args=p.parse_args()
    report=audit_original_public_test02(args.root,args.author,args.data)
    encoded=(json.dumps(report,sort_keys=True,indent=2)+"\n").encode("utf8")
    if args.write:
        args.write.parent.mkdir(parents=True,exist_ok=True)
        with args.write.open("xb") as output:
            output.write(encoded)
        print("REPORT_WRITTEN",str(args.write),sha256(encoded).hexdigest())
    else:
        print(json.dumps({
            "status":report["status"],
            "author_D0":report["original_author_D0_score"]["original_author_score"],
            "author_I0":report["original_author_I0_score"]["original_author_score"],
            "native_task_parity":report["independent_task_specific_native_geometric_semantic_pair_equivalent"],
            "full_native_bytes_identical":report["native_entire_D0_I0_IFC_byte_equal"],
            "matched_LLM_trials":report["matched_real_D_I_LLM_trials"],
        },sort_keys=True))


if __name__=="__main__":
    main()
