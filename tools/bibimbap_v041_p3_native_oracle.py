"""v0.41 independent reopened actual original-mm P3 native IFC geometry oracle.

Does NOT import the v0.41 compiler, original evaluator, hidden GT or author
task code. Checks all source original Root identities and physical product
surfaces, including opaque existing IfcSlabs, and exact one new real physical
IfcColumn / IfcSlab with original Storey containment.
"""
from __future__ import annotations

from collections import Counter
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.unit
import ifcopenshell.util.element
from lxml import etree

from tools.bibimbap_v038_legacy_live_gate import _world_mesh
from tools.bibimbap_matched25_tools import file_hash

PINS={
 "geometry_test_02":("58833e0bdf80e2207b8c221fc8195e5411f9f94e0d7f1cb39633b3c447eb4767","IfcColumn",4,0),
 "topological_test_02":("8f1d9e885603f8680cb79f2a373fa36b4ecd52634ac920f2ec53c60ac465ad72","IfcColumn",4,2),
 "topological_test_04":("29cd44b72639ba9573aa1698a4efab4adcfbc5461c19dd85259e6a9505d303e5","IfcSlab",7,1),
}
Q="{urn:bim-markup-bench:toy:v0}"


class P3IndependentNativeError(ValueError):
    pass


def require(value:bool,message:str)->None:
    if not value:raise P3IndependentNativeError(message)


def _spatial_edges(f):
    edges=set()
    for relation in f.by_type("IfcRelAggregates"):
        for child in relation.RelatedObjects:
            edges.add(("IfcRelAggregates",relation.RelatingObject.GlobalId,child.GlobalId))
    for relation in f.by_type("IfcRelContainedInSpatialStructure"):
        for child in relation.RelatedElements:
            edges.add(("IfcRelContainedInSpatialStructure",
                       relation.RelatingStructure.GlobalId,child.GlobalId))
    for relation in f.by_type("IfcRelSpaceBoundary"):
        if relation.RelatingSpace and relation.RelatedBuildingElement:
            edges.add((relation.is_a(),relation.RelatingSpace.GlobalId,
                       relation.RelatedBuildingElement.GlobalId))
    for relation in f.by_type("IfcRelConnectsElements"):
        edges.add((relation.is_a(),relation.RelatingElement.GlobalId,
                   relation.RelatedElement.GlobalId))
    for relation in f.by_type("IfcRelVoidsElement"):
        edges.add((relation.is_a(),relation.RelatingBuildingElement.GlobalId,
                   relation.RelatedOpeningElement.GlobalId))
    for relation in f.by_type("IfcRelFillsElement"):
        edges.add((relation.is_a(),relation.RelatingOpeningElement.GlobalId,
                   relation.RelatedBuildingElement.GlobalId))
    return edges


def verify_p3_original_native_add(
        source_mm:Path,output_mm:Path,*,task_id:str,
        submitted_xml:bytes)->dict:
    source_mm,output_mm=Path(source_mm),Path(output_mm)
    require(task_id in PINS,"Unknown independent P3 public original task")
    sha,klass,expected_walls,expected_old_slabs=PINS[task_id]
    require(source_mm.is_file() and not source_mm.is_symlink()
            and output_mm.is_file() and not output_mm.is_symlink()
            and source_mm.resolve()!=output_mm.resolve()
            and file_hash(source_mm)==sha,
            "Original P3 native-mm source SHA is not exactly preregistered")
    old=ifcopenshell.open(str(source_mm))
    after=ifcopenshell.open(str(output_mm))
    for model in (old,after):
        require(model.schema=="IFC4X3" and abs(
                ifcopenshell.util.unit.calculate_unit_scale(model)-.001)<1e-12,
                "P3 actual original native IFC4X3/millimetres schema or units drift")
    old_roots={x.GlobalId:x for x in old.by_type("IfcRoot")}
    out_roots={x.GlobalId:x for x in after.by_type("IfcRoot")}
    require(len(old_roots)==len(old.by_type("IfcRoot"))
            and len(out_roots)==len(after.by_type("IfcRoot"))
            and set(old_roots)<=set(out_roots),
            "Existing P3 source Root GUID missing or duplicated")
    for gid,object0 in old_roots.items():
        changed=out_roots[gid]
        require(changed.is_a()==object0.is_a()
                and changed.Name==object0.Name
                and changed.Description==object0.Description,
                "P3 changed an existing source Root identity, IFC class or metadata")
    old_products={p.GlobalId:p for p in old.by_type("IfcProduct")}
    new_products={p.GlobalId:p for p in after.by_type("IfcProduct")}
    require(set(old_products)<=set(new_products),
            "Original P3 source IFCProduct removed")
    added={g:p for g,p in new_products.items() if g not in old_products}
    require(Counter(x.is_a() for x in added.values())==Counter({klass:1}),
            "P3 must have exactly one newly created native IfcColumn/IfcSlab")
    new_guid,product=next(iter(added.items()))
    extra_roots={g:entity for g,entity in out_roots.items()
                 if g not in old_roots}
    require(all(x.is_a() in (klass,"IfcRelContainedInSpatialStructure")
                for x in extra_roots.values()),
            "P3 native output created an unauthorized native IFC Root/relation")
    require(len(old.by_type("IfcWall"))==len(after.by_type("IfcWall"))==expected_walls,
            "Source original native Wall count modified")
    require(len(old.by_type("IfcSlab"))==expected_old_slabs
            and len(after.by_type("IfcSlab"))==expected_old_slabs+
                (1 if klass=="IfcSlab" else 0),
            "P3 original opaque native IfcSlab count was modified")
    require(len(old.by_type("IfcRelSpaceBoundary"))==0
            and len(after.by_type("IfcRelSpaceBoundary"))==0,
            "P3 created a fake original IFC spatial boundary")
    before_edges=_spatial_edges(old)
    after_edges=_spatial_edges(after)
    require(before_edges<=after_edges,
            "P3 deleted or changed an existing source native relation")
    added_edges=after_edges-before_edges
    require(len(added_edges)==1
            and next(iter(added_edges))[0]=="IfcRelContainedInSpatialStructure"
            and next(iter(added_edges))[2]==new_guid,
            "P3 native added relationship is not exactly a new Storey containment")
    preserved_shapes=0
    preserved_tris=0
    old_shape_by_class=Counter()
    for guid,source_product in old_products.items():
        current=new_products[guid]
        require(current.is_a()==source_product.is_a(),
                "P3 existing original native product class altered")
        if source_product.Representation is None:
            require(current.Representation is None,
                    "P3 invented physical geometry for original non-shape IFC Product")
            continue
        orig_mesh=_world_mesh(source_product)
        final_mesh=_world_mesh(current)
        require(orig_mesh[2]==final_mesh[2]
                and orig_mesh[4]==final_mesh[4]
                and orig_mesh[5]==final_mesh[5],
                "P3 original source physical product world surface/vertices changed")
        preserved_shapes+=1
        preserved_tris+=orig_mesh[2]
        old_shape_by_class[source_product.is_a()]+=1
    require(old_shape_by_class["IfcSlab"]==expected_old_slabs,
            "P3 failed to compare every originally opaque existing native Slab mesh")
    require(product.Representation is not None,
            "P3 new native Column/Slab has no physical representation")
    low,high,tris,*_=_world_mesh(product)
    require(tris>=12,"P3 new native Column/Slab geometric mesh is incomplete")
    try:
        document=etree.fromstring(submitted_xml)
    except (etree.XMLSyntaxError,TypeError) as exc:
        raise P3IndependentNativeError("P3 submitted XML not actually parseable") from exc
    require(document.tag==Q+"Building" and
            document.get("ifcSchema")=="IFC4X3" and
            document.get("units")=="m",
            "P3 submitted original model-facing XML root/schema/units incorrect")
    elements=document.find(Q+"Elements")
    found=[x for x in elements
           if x.tag==Q+klass.removeprefix("Ifc") and not x.get("ifcGuid")]
    require(len(found)==1 and len([x for x in elements
            if x.tag in (Q+"Column",Q+"Slab") and not x.get("ifcGuid")])==1,
            "P3 model-facing declarative source must include one new Column/Slab")
    node=found[0]
    numeric=[float(node.get(k)) for k in ("x","y","z","width","depth",
              "height" if klass=="IfcColumn" else "thickness")]
    x,y,z,w,d,h=numeric
    require(all(math.isfinite(v) for v in numeric)
            and all(abs(a-b)<=.00001 for a,b in zip(
                low,(x,y,z)))
            and all(abs(a-b)<=.00001 for a,b in zip(
                high,(x+w,y+d,z+h))),
            "P3 new native IFC world bbox did not reproduce complete declarative XML dimensions")
    levels={l.get("id"):l.get("ifcGuid")
            for l in document.findall("./"+Q+"Levels/"+Q+"Level")}
    storey_guid=levels.get(node.get("level"))
    require(storey_guid is not None and old.by_guid(storey_guid)
            and old.by_guid(storey_guid).is_a("IfcBuildingStorey"),
            "P3 native new object must reference real original public IFC Storey")
    container=ifcopenshell.util.element.get_container(product)
    require(container is not None and container.GlobalId==storey_guid
            and ("IfcRelContainedInSpatialStructure",storey_guid,new_guid)
                in added_edges,
            "P3 native new object not really contained in original XML-selected Storey")
    require(file_hash(source_mm)==sha,
            "P3 original source IFC changed during independent restored native audit")
    return {
        "status":"INDEPENDENT_ORIGINAL_P3_NATIVE_COLUMN_SLAB_AND_SOURCE_PRESERVATION_PASS",
        "task_id":task_id,
        "native_schema":"IFC4X3",
        "native_length_unit":"mm",
        "all_original_root_Guids_classes_names_descriptions_preserved":len(old_roots),
        "all_original_IfcProducts_preserved":len(old_products),
        "all_original_native_wall_count_preserved":expected_walls,
        "original_native_opaque_Slab_count_preserved":expected_old_slabs,
        "all_original_opaque_native_Slab_physical_shapes_preserved":old_shape_by_class["IfcSlab"],
        "old_physical_IfcProduct_shapes_preserved":preserved_shapes,
        "old_physical_IfcProduct_triangles_preserved":preserved_tris,
        "old_explicit_IFC_topology_edges_preserved":len(before_edges),
        "new_spatial_relationship_only_existing_Storey":True,
        "original_IfcRelSpaceBoundary_count":0,
        "output_IfcRelSpaceBoundary_count":0,
        "new_original_native_IFC_class":klass,
        "new_original_native_IFC_GUID":new_guid,
        "new_native_physical_mesh_triangles":tris,
        "new_native_world_bbox_m":{
            "min":[round(float(v),6) for v in low],
            "max":[round(float(v),6) for v in high],
        },
        "new_native_box_matches_full_declarative_XML":True,
        "original_public_task_solution_proven":False,
        "complete_original_IFC_STEP_byte_identity_proven":False,
        "original_source_IFC_bytes_unchanged":True,
    }
