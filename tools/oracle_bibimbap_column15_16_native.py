"""Independent native-only IFC task15/task16 D0 validation, Issue #120.

Does NOT import an XML compiler, bind/schema, native mutation helpers, or
original author's grader. It reads two complete real IFC files and verifies
specific public task semantics plus all other original product identities,
native geometry/presentation, and surviving relationship memberships.
Strict only within the explicitly documented task-specific scope.
"""
from __future__ import annotations

import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
from tools.bibimbap_matched25_tools import file_hash


class NativeColumnOracleError(ValueError):
    pass


def model_pair(source:Path,output:Path):
    if not source.is_file() or not output.is_file() or source.resolve()==output.resolve():
        raise NativeColumnOracleError("Independent source and output IFC files required")
    old=ifcopenshell.open(str(source))
    new=ifcopenshell.open(str(output))
    if old.schema!=new.schema or old.schema!="IFC4X3":
        raise NativeColumnOracleError("IFC4X3 semantic schema mismatch")
    return old,new


def world_bounds(column):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        geo=ifcopenshell.geom.create_shape(settings,column)
    except Exception as exc:
        raise NativeColumnOracleError("Independent IFC geometry kernel failed") from exc
    vertices=geo.geometry.verts
    if len(vertices)<18 or len(vertices)%3:
        raise NativeColumnOracleError("Invalid IfcColumn native mesh")
    points=[vertices[i:i+3] for i in range(0,len(vertices),3)]
    return tuple(min(float(p[i]) for p in points) for i in range(3)),tuple(
        max(float(p[i]) for p in points) for i in range(3))


def _near(a,b,eps=1e-5):
    return math.isclose(float(a),float(b),rel_tol=0,abs_tol=eps)


def strict_move_column(source:Path,output:Path,guid:str,*,dy:float=-3.0)->dict:
    a,b=model_pair(source,output)
    source_roots={x.GlobalId:x for x in a.by_type("IfcRoot")}
    new_roots={x.GlobalId:x for x in b.by_type("IfcRoot")}
    if set(source_roots)!=set(new_roots) or guid not in source_roots:
        raise NativeColumnOracleError("Original IFC Root identities changed in Column move")
    target=a.by_guid(guid)
    if not target.is_a("IfcColumn"):
        raise NativeColumnOracleError("Target GlobalId is not a Column")
    # Strict entity-level edit: only the native placement CartesianPoint of
    # the public target is permitted to change, not its geometry or type.
    point=target.ObjectPlacement.RelativePlacement.Location
    if not point.is_a("IfcCartesianPoint"):
        raise NativeColumnOracleError("Target has unsupported placement coordinates")
    old_entities={ent.id():str(ent) for ent in a}
    new_entities={ent.id():str(ent) for ent in b}
    if set(old_entities)!=set(new_entities):
        raise NativeColumnOracleError("Native STEP entity count changed in Column move")
    changes={eid for eid in old_entities if old_entities[eid]!=new_entities[eid]}
    if changes!={point.id()}:
        raise NativeColumnOracleError("World column move changed unapproved STEP entity")

    orig=world_bounds(target)
    dest=world_bounds(b.by_guid(guid))
    for i in range(3):
        expected=dy if i==1 else 0
        if not all(_near(dest[k][i]-orig[k][i],expected) for k in range(2)):
            raise NativeColumnOracleError("IfcColumn mesh did not undergo requested y translation")
    old_cols={x.GlobalId:world_bounds(x) for x in a.by_type("IfcColumn")}
    new_cols={x.GlobalId:world_bounds(x) for x in b.by_type("IfcColumn")}
    if set(old_cols)!=set(new_cols):
        raise NativeColumnOracleError("Column count/identity changed in move")
    for key in old_cols:
        if key!=guid and old_cols[key]!=new_cols[key]:
            raise NativeColumnOracleError("Non-target column geometry moved")
    return {
        "status":"INDEPENDENT_REAL_IFC_TEST15_COLUMN_MOVE_VALIDATED",
        "metric_origin":"INDEPENDENT_IFC_NATIVE_STEP_WORLD_MESH_ORACLE",
        "original_public_task":"test_15",
        "verified_translation_y_m":dy,
        "changed_native_step_entity_count":len(changes),
        "changed_native_step_entity_kind":"IfcCartesianPoint",
        "non_target_original_native_roots_preserved":len(source_roots)-1,
        "unaffected_original_columns":len(old_cols)-1,
        "source_sha256":file_hash(source),
        "output_sha256":file_hash(output),
        "full_45_task_oracle_coverage":False,
    }


def strict_delete_column(source:Path,output:Path,guid:str)->dict:
    a,b=model_pair(source,output)
    old_roots={x.GlobalId:x for x in a.by_type("IfcRoot")}
    new_roots={x.GlobalId:x for x in b.by_type("IfcRoot")}
    target=old_roots.get(guid)
    if target is None or not target.is_a("IfcColumn") or guid in new_roots:
        raise NativeColumnOracleError("Specified original Column was not deleted")
    if set(new_roots)-set(old_roots):
        raise NativeColumnOracleError("Deletion introduced unexpected IFC Roots")
    old_col={x.GlobalId:x for x in a.by_type("IfcColumn")}
    new_col={x.GlobalId:x for x in b.by_type("IfcColumn")}
    if set(new_col)!=set(old_col)-{guid}:
        raise NativeColumnOracleError("Deleted unrelated IfcColumn")
    for name in new_col:
        if world_bounds(old_col[name])!=world_bounds(new_col[name]):
            raise NativeColumnOracleError("Surviving column native world geometry mutated")
    original_product={x.GlobalId:x for x in a.by_type("IfcProduct")}
    after_product={x.GlobalId:x for x in b.by_type("IfcProduct")}
    if set(after_product)!=set(original_product)-{guid}:
        raise NativeColumnOracleError("Deleted any unrelated original IfcProduct")
    if any(str(original_product[key])!=str(after_product[key]) for key in after_product):
        raise NativeColumnOracleError("Unrelated IFC product metadata or identity mutated")

    orig_relations={
        e.GlobalId:e for e in a.get_inverse(target)
        if e.is_a() in ("IfcRelContainedInSpatialStructure",
                        "IfcRelDefinesByType","IfcRelDefinesByProperties")
    }
    if any(e.is_a() not in (
        "IfcRelContainedInSpatialStructure",
        "IfcRelDefinesByType","IfcRelDefinesByProperties") for e in a.get_inverse(target)):
        raise NativeColumnOracleError("Target has unsupported inverse relationships")
    allowed_remove={guid}
    for rel in orig_relations.values():
        if rel.is_a("IfcRelDefinesByProperties"):
            if len(rel.RelatedObjects)!=1 or rel.RelatedObjects[0].GlobalId!=guid:
                raise NativeColumnOracleError("Shared properties incorrectly deleted")
            allowed_remove.add(rel.GlobalId)
            allowed_remove.add(rel.RelatingPropertyDefinition.GlobalId)
            continue
        old_members=(rel.RelatedElements if rel.is_a("IfcRelContainedInSpatialStructure")
                     else rel.RelatedObjects)
        old_ids={x.GlobalId for x in old_members}
        if guid not in old_ids:
            raise NativeColumnOracleError("Column missing from expected relation")
        next_rel=new_roots.get(rel.GlobalId)
        if len(old_ids)==1:
            allowed_remove.add(rel.GlobalId)
            if next_rel is not None:
                raise NativeColumnOracleError("Empty relation unexpectedly survived")
        elif next_rel is None:
            raise NativeColumnOracleError("Shared IFC relation unexpectedly removed")
        else:
            new_members=(next_rel.RelatedElements if rel.is_a("IfcRelContainedInSpatialStructure")
                         else next_rel.RelatedObjects)
            if {x.GlobalId for x in new_members}!=old_ids-{guid}:
                raise NativeColumnOracleError("Another IFC relation member was altered")
    if set(old_roots)-set(new_roots)!=allowed_remove:
        raise NativeColumnOracleError("Other IFC Root relationships/properties disappeared")
    for key in set(old_roots)&set(new_roots):
        prev=old_roots[key]
        now=new_roots[key]
        if prev.is_a()!=now.is_a():
            raise NativeColumnOracleError("Remaining IFC Root class changed")
        if key not in orig_relations and str(prev)!=str(now):
            raise NativeColumnOracleError("Unrelated IFC root changed after delete")
    return {
        "status":"INDEPENDENT_REAL_IFC_TEST16_COLUMN_DELETE_SEMANTICS_VALIDATED",
        "metric_origin":"INDEPENDENT_IFC_NATIVE_PRODUCTS_RELATIONSHIP_MESH_ORACLE",
        "original_public_task":"test_16",
        "deleted_native_globalid":guid,
        "preserved_original_other_columns":len(new_col),
        "preserved_original_other_ifc_products":len(after_product),
        "owned_property_and_relation_root_deletions":len(allowed_remove)-1,
        "source_sha256":file_hash(source),
        "output_sha256":file_hash(output),
        "original_author_integrity_metric_may_disagree":True,
        "full_45_task_oracle_coverage":False,
    }
