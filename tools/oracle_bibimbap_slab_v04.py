"""Independent native-only IFC Slab task-specific validation, experimental v0.4.

No import from declarative XML projection/binder/compiler/mutation planner or
original author scorer. Reads actual source and edited native IFC files,
all original STEP IDs, original IFC Root/Product identities, and real world
mesh bounds. This validates a restricted Slab feature slice, NOT building-
wide clash clearance or paper-equivalent full 45-task benchmark success.
"""
from __future__ import annotations

import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit

from tools.bibimbap_matched25_tools import file_hash


class IndependentSlabOracleError(ValueError):
    pass


def _models(source:Path,output:Path):
    if (not source.is_file() or not output.is_file()
        or source.resolve()==output.resolve()):
        raise IndependentSlabOracleError("Two separate native IFC files required")
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(output))
    if a.schema!="IFC4X3" or b.schema!=a.schema:
        raise IndependentSlabOracleError("IFC4X3 source/result schema differs")
    if not math.isclose(ifcopenshell.util.unit.calculate_unit_scale(a),1.,abs_tol=1e-8):
        raise IndependentSlabOracleError("Source metre-unit IFC required")
    if not math.isclose(ifcopenshell.util.unit.calculate_unit_scale(b),1.,abs_tol=1e-8):
        raise IndependentSlabOracleError("Output metre-unit IFC required")
    return a,b


def _bbox(slab):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        shape=ifcopenshell.geom.create_shape(settings,slab)
    except Exception as exc:
        raise IndependentSlabOracleError("Native slab mesh unavailable") from exc
    v=shape.geometry.verts
    if len(v)<24 or len(v)%3:
        raise IndependentSlabOracleError("Slab native shape missing")
    arr=[tuple(float(x) for x in v[i:i+3]) for i in range(0,len(v),3)]
    return (
        tuple(min(x[i] for x in arr) for i in range(3)),
        tuple(max(x[i] for x in arr) for i in range(3)),
    )


def _same(a,b,tolerance=1e-5):
    return math.isclose(float(a),float(b),abs_tol=tolerance,rel_tol=0)


def _slab_boxes(f):
    return {s.GlobalId:_bbox(s) for s in f.by_type("IfcSlab")}


def _native_roots(f):
    return {r.GlobalId:r for r in f.by_type("IfcRoot")}


def _ensure_unaffected_slabs(a,b,excluded):
    aa=_slab_boxes(a)
    bb=_slab_boxes(b)
    if set(aa)-{excluded}!=set(bb)-{excluded}:
        raise IndependentSlabOracleError("Unrelated IFC slab inventory changed")
    for guid in set(aa)&set(bb)-{excluded}:
        orig=aa[guid]
        new=bb[guid]
        if any(not _same(orig[i][j],new[i][j]) for i in (0,1) for j in range(3)):
            raise IndependentSlabOracleError("Another slab native mesh was changed")
    return len(aa)-int(excluded in aa)


def _original_root_integrity(a,b,*,allow_containment:bool=False):
    aa=_native_roots(a)
    bb=_native_roots(b)
    for guid in aa:
        if guid not in bb:
            raise IndependentSlabOracleError("Original IFC Root disappeared")
        if aa[guid].is_a()!=bb[guid].is_a():
            raise IndependentSlabOracleError("Existing IFC Root class changed")
        if str(aa[guid])!=str(bb[guid]):
            if not allow_containment or not aa[guid].is_a("IfcRelContainedInSpatialStructure"):
                raise IndependentSlabOracleError("Unrelated original IFC Root changed")
    return len(aa)


def verify_create(source:Path,output:Path,guid:str,*,bounds_min,bounds_max)->dict:
    a,b=_models(source,output)
    original=_native_roots(a)
    result=_native_roots(b)
    if guid in original or guid not in result or not result[guid].is_a("IfcSlab"):
        raise IndependentSlabOracleError("New native Slab must be exactly one new GlobalId")
    if len(b.by_type("IfcSlab"))!=len(a.by_type("IfcSlab"))+1:
        raise IndependentSlabOracleError("Expected only one native Slab creation")
    n=_original_root_integrity(a,b,allow_containment=True)
    _ensure_unaffected_slabs(a,b,guid)
    allowed_extra={g for g in result if g not in original and g!=guid}
    if any(not result[g].is_a("IfcRelContainedInSpatialStructure") for g in allowed_extra):
        raise IndependentSlabOracleError("Created unexpected native IFC Root")
    old={e.id():str(e) for e in a}
    new={e.id():str(e) for e in b}
    if not set(old)<=set(new):
        raise IndependentSlabOracleError("Native IFC entity deleted during creation")
    changed={i for i in old if old[i]!=new[i]}
    allowed={r.id() for r in a.by_type("IfcRelContainedInSpatialStructure")}
    if not changed<=allowed:
        raise IndependentSlabOracleError("Unrelated IFC STEP source mutated during creation")
    original_containment_changed=0
    for relation in a.by_type("IfcRelContainedInSpatialStructure"):
        before_set={x.GlobalId for x in relation.RelatedElements}
        after_set={x.GlobalId for x in b.by_guid(relation.GlobalId).RelatedElements}
        if before_set!=after_set:
            if after_set!=before_set|{guid}:
                raise IndependentSlabOracleError("Slab creation damaged original storey containment")
            original_containment_changed+=1
    if original_containment_changed!=1:
        raise IndependentSlabOracleError("Slab creation did not add exactly one storey member")
    col=result[guid]
    contain=ifcopenshell.util.element.get_container(col)
    if contain is None or not contain.is_a("IfcBuildingStorey"):
        raise IndependentSlabOracleError("New Slab missing original native storey containment")
    low,high=_bbox(col)
    if any(not _same(actual,expected)
           for actual,expected in zip((*low,*high),(*bounds_min,*bounds_max))):
        raise IndependentSlabOracleError("New physical native slab mesh outside planned bounds")
    return {
        "status":"INDEPENDENT_NATIVE_SLAB_CREATE_PHYSICAL_IFC_VALIDATED",
        "original_root_preserved_count":n,
        "new_slab_guid":guid,
        "world_native_bbox_min_m":low,
        "world_native_bbox_max_m":high,
        "source_sha256":file_hash(source),
        "output_sha256":file_hash(output),
        "full_building_collision_oracle":None,
    }


def verify_update(source:Path,output:Path,guid:str,*,kind:str,
                  new_bounds_min=None,new_bounds_max=None,delta=None)->dict:
    a,b=_models(source,output)
    aa=_native_roots(a)
    bb=_native_roots(b)
    if set(aa)!=set(bb):
        raise IndependentSlabOracleError("Updated native IFC GlobalId inventory changed")
    n=_original_root_integrity(a,b)
    _ensure_unaffected_slabs(a,b,guid)
    oldslab=a.by_guid(guid)
    newslab=b.by_guid(guid)
    if not oldslab.is_a("IfcSlab") or not newslab.is_a("IfcSlab"):
        raise IndependentSlabOracleError("Target is not native IfcSlab")
    before=_bbox(oldslab)
    after=_bbox(newslab)
    if kind=="move":
        if delta is None or len(delta)!=3:
            raise IndependentSlabOracleError("Move requires exact world XYZ delta")
        for i in range(3):
            if not all(_same(after[k][i]-before[k][i],delta[i]) for k in (0,1)):
                raise IndependentSlabOracleError("Native Slab world mesh failed exact translation")
    elif kind in ("resize","thickness"):
        if new_bounds_min is None or new_bounds_max is None:
            raise IndependentSlabOracleError("Resize needs predeclared native geometry bbox")
        if any(not _same(actual,expected) for actual,expected in
               zip((*after[0],*after[1]),(*new_bounds_min,*new_bounds_max))):
            raise IndependentSlabOracleError("Native Slab mesh wrong after rectangular editing")
    else:
        raise IndependentSlabOracleError("Unknown independent Slab modification kind")
    original_step={e.id():str(e) for e in a}
    result_step={e.id():str(e) for e in b}
    if set(original_step)-set(result_step):
        raise IndependentSlabOracleError("Native IFC STEP entity lost during update")
    changed={i for i in original_step if original_step[i]!=result_step[i]}
    valid_types={"IfcCartesianPoint","IfcAxis2Placement3D","IfcRectangleProfileDef","IfcExtrudedAreaSolid"}
    if not changed or any(a.by_id(i).is_a() not in valid_types for i in changed):
        raise IndependentSlabOracleError("Slab edit mutated an unrelated native STEP entity")
    added=set(result_step)-set(original_step)
    if any(not b.by_id(i).is_a("IfcCartesianPoint") for i in added):
        raise IndependentSlabOracleError("Unexpected native STEP entity created in update")
    if kind=="move":
        if len(changed)!=1 or a.by_id(next(iter(changed))).is_a() not in (
            "IfcCartesianPoint","IfcAxis2Placement3D"):
            raise IndependentSlabOracleError("Slab move must modify one placement STEP entity")
    else:
        allowed={"IfcRectangleProfileDef","IfcCartesianPoint","IfcAxis2Placement3D"}
        if kind=="thickness":
            allowed={"IfcExtrudedAreaSolid","IfcCartesianPoint","IfcAxis2Placement3D"}
        if any(a.by_id(i).is_a() not in allowed for i in changed):
            raise IndependentSlabOracleError("Slab profile edit changed unrelated native geometry")
    return {
        "status":"INDEPENDENT_NATIVE_SLAB_"+kind.upper()+"_PHYSICAL_IFC_VALIDATED",
        "original_root_preserved_count":n,
        "native_original_step_changed_count":len(changed),
        "native_original_step_changed_types":sorted(a.by_id(i).is_a() for i in changed),
        "native_new_copy_on_write_points":len(added),
        "verified_non_target_slab_count":len(a.by_type("IfcSlab"))-1,
        "actual_world_native_bbox_min_m":after[0],
        "actual_world_native_bbox_max_m":after[1],
        "source_sha256":file_hash(source),
        "output_sha256":file_hash(output),
        "full_building_collision_oracle":None,
    }


def verify_delete(source:Path,output:Path,guid:str)->dict:
    a,b=_models(source,output)
    if guid not in _native_roots(a) or guid in _native_roots(b):
        raise IndependentSlabOracleError("Slab deletion target identity invalid")
    original_products={x.GlobalId:x for x in a.by_type("IfcProduct")}
    final_products={x.GlobalId:x for x in b.by_type("IfcProduct")}
    if set(original_products)-{guid}!=set(final_products):
        raise IndependentSlabOracleError("Unrelated IFC Products disappeared in deletion")
    if any(str(original_products[k])!=str(final_products[k]) for k in final_products):
        raise IndependentSlabOracleError("Unrelated original IFC Product changed in deletion")
    unchanged=_ensure_unaffected_slabs(a,b,guid)
    original_roots=_native_roots(a)
    final_roots=_native_roots(b)
    target=original_roots[guid]
    allowed_relations={
        x.GlobalId:x for x in a.get_inverse(target)
        if x.is_a() in ("IfcRelContainedInSpatialStructure",
                        "IfcRelDefinesByType","IfcRelDefinesByProperties",
                        "IfcRelAssociatesMaterial")
    }
    if len(allowed_relations)!=len(a.get_inverse(target)):
        raise IndependentSlabOracleError("Slab has unrelated inverse IFC dependence")
    expected_removed={guid}
    changed_relations=set()
    for key,rel in allowed_relations.items():
        members=rel.RelatedElements if rel.is_a("IfcRelContainedInSpatialStructure") else rel.RelatedObjects
        src={x.GlobalId for x in members}
        if guid not in src:
            raise IndependentSlabOracleError("Target Slab missing from original relation")
        if rel.is_a("IfcRelDefinesByProperties"):
            if len(src)!=1:
                raise IndependentSlabOracleError("Shared native PropertySet incorrectly deleted")
            expected_removed.add(key)
            expected_removed.add(rel.RelatingPropertyDefinition.GlobalId)
        elif len(src)==1:
            expected_removed.add(key)
        else:
            new=final_roots.get(key)
            if new is None:
                raise IndependentSlabOracleError("Shared native relation unexpectedly deleted")
            tail=(new.RelatedElements if new.is_a("IfcRelContainedInSpatialStructure")
                  else new.RelatedObjects)
            if {x.GlobalId for x in tail}!=src-{guid}:
                raise IndependentSlabOracleError("Unrelated type/material/containment members changed")
            changed_relations.add(key)
    if set(original_roots)-set(final_roots)!=expected_removed or set(final_roots)-set(original_roots):
        raise IndependentSlabOracleError("Unrelated native IFC Root removed/added")
    for gid in set(original_roots)&set(final_roots):
        if original_roots[gid].is_a()!=final_roots[gid].is_a():
            raise IndependentSlabOracleError("Surviving IFC Root type changed")
        if str(original_roots[gid])!=str(final_roots[gid]) and gid not in changed_relations:
            raise IndependentSlabOracleError("Unrelated IFC Root modified")
    return {
        "status":"INDEPENDENT_NATIVE_SLAB_DELETE_OWNED_RELATIONS_VALIDATED",
        "preserved_surviving_original_products":len(final_products),
        "preserved_unrelated_slab_meshes":unchanged,
        "owned_removed_root_count":len(expected_removed),
        "author_integrity_metric_equivalence":None,
        "source_sha256":file_hash(source),
        "output_sha256":file_hash(output),
        "full_building_collision_oracle":None,
    }
