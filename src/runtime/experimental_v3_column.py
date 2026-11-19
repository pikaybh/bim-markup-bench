"""Research-only v0.3 Column UPDATE/DELETE (Issue #120).

The LLM authors one whole DECLARATIVE XML state; trusted backend infers
changes by stable IFC identity. Existing Revit IfcMappedItem shapes are never
unwrapped/rebuilt: translate unique object placement for MOVE, or remove a
single target with strict relationship preservation for DELETE. Only
unshared direct IfcExtrudedAreaSolid can undergo HEIGHT edit.
No v0.1/v0.2 baseline rewrites, no new LLM calls or benchmark claims.
"""
from __future__ import annotations

from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

from src.runtime.compiler import CompileReport
from src.runtime.ifc_mutations import Mutation
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.transaction import stage_and_commit
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document
from src.runtime.semantic_graph import graph_diff
from src.runtime.experimental_v2_column import _world_bbox,_column_params
from src.runtime.experimental_v3_projection import project_ifc_v3


EPS=1e-5
class ColumnV3Error(ValueError):
    pass


class ColumnV3CompileReport(CompileReport):
    def as_dict(self)->dict:
        out=super().as_dict()
        op=self.operations[0].operation
        out.update({
            "status":"COMMITTED_SCOPED_IFC4X3_"+op+"_V3",
            "scope":"one existing native IFC4X3 Column; strict fail-closed preservation",
            "compiler_version":"experimental-column-v0.3",
            "general_bim_edit_45_supported":False,
            "preserve_mapped_geometry":True,
        })
        return out


def _resolve(f,guid):
    try:
        obj=f.by_guid(guid)
    except RuntimeError as exc:
        raise ColumnV3Error("Native Column GlobalId missing") from exc
    if not obj.is_a("IfcColumn"):
        raise ColumnV3Error("Native entity is not IfcColumn")
    return obj


def _step_snapshots(original:Path,candidate:Path):
    before=ifcopenshell.open(str(original))
    after=ifcopenshell.open(str(candidate))
    if before.schema!="IFC4X3" or after.schema!=before.schema:
        raise ColumnV3Error("IFC4X3 schema changed")
    old_step={e.id():str(e) for e in before}
    new_step={e.id():str(e) for e in after}
    return before,after,old_step,new_step


def _placement_point(f:ifcopenshell.file,col):
    placement=col.ObjectPlacement
    if placement is None or not placement.is_a("IfcLocalPlacement"):
        raise ColumnV3Error("Column lacks local placement")
    relative=placement.RelativePlacement
    if not relative.is_a("IfcAxis2Placement3D"):
        raise ColumnV3Error("Column has unsupported relative placement")
    point=relative.Location
    if not point.is_a("IfcCartesianPoint"):
        raise ColumnV3Error("Column lacks point placement origin")
    # A column's coordinates must be an exclusive non-shared point and it
    # must not be a placement parent for another native product.
    if (len(f.get_inverse(point))!=1 or len(f.get_inverse(relative))!=1
        or any(x.id()!=col.id() for x in f.get_inverse(placement))):
        raise ColumnV3Error("Column placement geometry is shared")
    if placement.PlacementRelTo is not None:
        parent_matrix=np.asarray(ifcopenshell.util.placement.get_local_placement(placement.PlacementRelTo))
        if not np.allclose(parent_matrix[:3,:3],np.eye(3),rtol=0,atol=1e-8):
            raise ColumnV3Error("Rotated parent coordinate frame unsupported")
    return point


def _height_solid(f:ifcopenshell.file,col):
    if col.Representation is None:
        raise ColumnV3Error("Column has no unique shape")
    representations=col.Representation.Representations
    solids=[item for rep in representations for item in rep.Items
            if item.is_a("IfcExtrudedAreaSolid")]
    # IfcMappedItem cannot be mutated: its type geometry may be shared.
    if len(solids)!=1 or any(
        item.is_a("IfcMappedItem") for rep in representations for item in rep.Items):
        raise ColumnV3Error("Column height modification requires unshared direct extrusion")
    solid=solids[0]
    # Verify no shared representation reaches another product.
    for rep in f.get_inverse(solid):
        if rep.is_a("IfcShapeRepresentation"):
            pdefs=[x for x in f.get_inverse(rep) if x.is_a("IfcProductDefinitionShape")]
            if len(pdefs)!=1:
                raise ColumnV3Error("Column native solid has ambiguous product ownership")
            owners=[x for x in f.get_inverse(pdefs[0]) if x.is_a("IfcProduct")]
            if len(owners)!=1 or owners[0].GlobalId!=col.GlobalId:
                raise ColumnV3Error("Column extrusion geometry shared by another product")
    return solid


def _validate_delete_dependencies(f:ifcopenshell.file,col)->None:
    allowed={"IfcRelContainedInSpatialStructure","IfcRelDefinesByType",
             "IfcRelDefinesByProperties"}
    for relation in f.get_inverse(col):
        if relation.is_a() not in allowed:
            raise ColumnV3Error("Column has unhandled native inverse dependency "+relation.is_a())
        members=(list(relation.RelatedElements) if relation.is_a("IfcRelContainedInSpatialStructure")
                 else list(relation.RelatedObjects))
        if not any(x.GlobalId==col.GlobalId for x in members):
            raise ColumnV3Error("Column not in original expected IFC relationship")
        if relation.is_a("IfcRelDefinesByProperties"):
            if len(members)!=1:
                raise ColumnV3Error("Column property relationship is shared")
            pset=relation.RelatingPropertyDefinition
            if pset is None or not pset.is_a("IfcPropertySet"):
                raise ColumnV3Error("Unsupported property definition relation")
            if len([x for x in f.get_inverse(pset) if x.is_a("IfcRelDefinesByProperties")])!=1:
                raise ColumnV3Error("Column IfcPropertySet is shared with another relationship")


def _unchanged_after_update(source:Path,candidate:Path,guid:str,
                            expected_id:int)->int:
    a,b,old,new=_step_snapshots(source,candidate)
    if set(old)!=set(new):
        raise ColumnV3Error("Column update added/deleted native STEP entities")
    changes={k for k in old if old[k]!=new[k]}
    if changes!={expected_id}:
        raise ColumnV3Error("Column update changed non-target IFC STEP data: "+str(sorted(changes)))
    before_roots={x.GlobalId:x for x in a.by_type("IfcRoot")}
    after_roots={x.GlobalId:x for x in b.by_type("IfcRoot")}
    if set(before_roots)!=set(after_roots):
        raise ColumnV3Error("Column update changed native IFC root inventory")
    for key,entity in before_roots.items():
        if str(entity)!=str(after_roots[key]):
            raise ColumnV3Error("Column update rewrote native root object "+key)
    return len(before_roots)


def _delete_preservation(source:Path,candidate:Path,removed_guid:str)->int:
    a,b,old,new=_step_snapshots(source,candidate)
    before_roots={x.GlobalId:x for x in a.by_type("IfcRoot")}
    after_roots={x.GlobalId:x for x in b.by_type("IfcRoot")}
    if len(before_roots)!=len(a.by_type("IfcRoot")) or len(after_roots)!=len(b.by_type("IfcRoot")):
        raise ColumnV3Error("Duplicated native IFC GlobalId after deletion")
    target=before_roots[removed_guid]
    if not target.is_a("IfcColumn") or removed_guid in after_roots:
        raise ColumnV3Error("Expected Column not removed")
    if set(after_roots)-set(before_roots):
        raise ColumnV3Error("Unexpected new native root after Column delete")
    removed_ids=set(old)-set(new)
    changed={i for i in old.keys()&new.keys() if old[i]!=new[i]}
    added=set(new)-set(old)
    allowed_removed={
        "IfcColumn","IfcPropertySet","IfcRelDefinesByProperties","IfcRelDefinesByType",
        "IfcPropertySingleValue","IfcMappedItem","IfcShapeRepresentation",
        "IfcProductDefinitionShape","IfcAxis2Placement3D","IfcAxis2Placement2D",
        "IfcLocalPlacement","IfcCartesianPoint","IfcExtrudedAreaSolid",
        "IfcRectangleProfileDef","IfcPolyline","IfcCartesianPointList2D",
    }
    for n in removed_ids:
        if a.by_id(n).is_a() not in allowed_removed:
            raise ColumnV3Error("Deleted unrelated native STEP entity class")
    for n in added:
        if not b.by_id(n).is_a("IfcOwnerHistory"):
            raise ColumnV3Error("Unexpected new STEP entity after deletion")
    # For *every removed old STEP entity*, a remaining inverse reference is
    # forbidden unless the inverse is an explicitly audited changed relation.
    for entity_id in removed_ids:
        for inv in a.get_inverse(a.by_id(entity_id)):
            if inv.id() not in removed_ids and inv.id() not in changed:
                raise ColumnV3Error("Removed IFC geometry/property shared by surviving entity")

    old_relations={}
    for entity in a.get_inverse(target):
        if entity.is_a() in ("IfcRelContainedInSpatialStructure",
                            "IfcRelDefinesByType","IfcRelDefinesByProperties"):
            old_relations[entity.GlobalId]=entity
        else:
            raise ColumnV3Error("Target Column had unsupported dependency")
    expected_root_removed={removed_guid}
    for gid,entity in old_relations.items():
        if entity.is_a("IfcRelDefinesByProperties"):
            relmembers=tuple(entity.RelatedObjects)
            if len(relmembers)!=1 or relmembers[0].GlobalId!=removed_guid:
                raise ColumnV3Error("Shared properties were deleted")
            expected_root_removed.add(gid)
            expected_root_removed.add(entity.RelatingPropertyDefinition.GlobalId)
        else:
            members=entity.RelatedElements if entity.is_a("IfcRelContainedInSpatialStructure") else entity.RelatedObjects
            if len(members)==1:
                expected_root_removed.add(gid)
    removed_roots=set(before_roots)-set(after_roots)
    if removed_roots!=expected_root_removed:
        raise ColumnV3Error("Unexpected native IFC Root/PropertySet deletions: "+str(removed_roots^expected_root_removed))

    permitted_changed=set()
    unchanged=0
    for gid,obj in before_roots.items():
        if gid in expected_root_removed:
            continue
        current=after_roots[gid]
        if obj.is_a()!=current.is_a():
            raise ColumnV3Error("Surviving native Root changed IFC class")
        if str(obj)==str(current):
            unchanged+=1
            continue
        if gid not in old_relations:
            raise ColumnV3Error("Unrelated original IFC Root was mutated")
        if obj.is_a("IfcRelContainedInSpatialStructure"):
            old_ids={x.GlobalId for x in obj.RelatedElements}
            new_ids={x.GlobalId for x in current.RelatedElements}
            if new_ids !=old_ids-{removed_guid}:
                raise ColumnV3Error("Unrelated native containment membership changed")
        elif obj.is_a("IfcRelDefinesByType"):
            old_ids={x.GlobalId for x in obj.RelatedObjects}
            new_ids={x.GlobalId for x in current.RelatedObjects}
            if new_ids !=old_ids-{removed_guid} or current.RelatingType.GlobalId!=obj.RelatingType.GlobalId:
                raise ColumnV3Error("Unrelated native Type membership/identity changed")
        else:
            raise ColumnV3Error("Unsupported changed original Root relation")
        permitted_changed.add(obj.id())
    # A presentation layer is a native nonroot entity that references
    # shape representations. Removal may narrow its AssignedItems by the
    # target column's exact original representation IDs, and nothing else.
    allowed_reps={rep.id() for rep in target.Representation.Representations}
    for eid in changed-permitted_changed:
        older=a.by_id(eid)
        newer=b.by_id(eid)
        if not older.is_a("IfcPresentationLayerAssignment") or not newer.is_a("IfcPresentationLayerAssignment"):
            raise ColumnV3Error("Nonrelation nonpresentation STEP entity changed")
        before_refs={x.id() for x in older.AssignedItems}
        after_refs={x.id() for x in newer.AssignedItems}
        if not before_refs-after_refs<=allowed_reps or after_refs-before_refs:
            raise ColumnV3Error("Column deletion rewrote unrelated presentation assignment")
    # No surviving native product other than the allowed Root relationships
    # was modified at the IFC root level; all old STEP entity changes are
    # checked above and all removed nodes are ownership-closed.
    return unchanged


def compile_declarative_xml_v3(source:Path, edited_xml:bytes,
                               destination:Path)->ColumnV3CompileReport:
    if not source.is_file() or source.is_symlink() or destination.exists() or destination.is_symlink():
        raise ColumnV3Error("Source must exist; result must use a new unused IFC path")
    projected=project_ifc_v3(source)
    doc_before=parse_xml(projected.xml,expected_source_sha256=projected.source.source_sha256)
    doc_after=parse_xml(edited_xml,expected_source_sha256=projected.source.source_sha256)
    before=bind_document(doc_before,projection=projected)
    after=bind_document(doc_after,projection=projected,verify_native_edges=False)
    delta=graph_diff(before.graph,after.graph)
    old=before.graph.by_id()
    new=after.graph.by_id()
    if delta.added_nodes or delta.added_edges:
        raise ColumnV3Error("v0.3 supports no new objects; use frozen v0.2 for Column create")
    if (len(delta.changed_nodes)+len(delta.removed_nodes)!=1 or
        not (delta.changed_nodes or delta.removed_nodes)):
        raise ColumnV3Error("Only one existing Column update or delete in isolated XML state")
    name=(delta.changed_nodes or delta.removed_nodes)[0]
    prev=old[name]
    if prev.kind!="Column" or prev.provenance!="existing_source":
        raise ColumnV3Error("Only existing native Column has safe v0.3 authoring")
    native=ifcopenshell.open(str(source))
    if native.schema!="IFC4X3" or abs(ifcopenshell.util.unit.calculate_unit_scale(native)-1.0)>1e-8:
        raise ColumnV3Error("IFC4X3 metre-native source required")
    column=_resolve(native,prev.ifc_guid)
    old_low,old_high=_world_bbox(column)
    sourcehash=snapshot_source(source).source_sha256
    if sourcehash!=projected.source.source_sha256:
        raise ColumnV3Error("Original IFC source changed after projection")
    expected_id=None
    if delta.removed_nodes:
        if delta.changed_nodes or delta.added_edges:
            raise ColumnV3Error("Column delete must be isolated and not add relations")
        expected_relations={
            e for e in before.graph.edges if e.target==name and e.relation=="in_storey"
        }
        if set(delta.removed_edges)!=expected_relations or len(expected_relations)!=1:
            raise ColumnV3Error("Unexpected Column owned relationship removal")
        _validate_delete_dependencies(native,column)
        op="DELETE_COLUMN"
        target=None
        delta_pos=(0.0,0.0,0.0)
    else:
        if delta.removed_edges or delta.added_edges:
            raise ColumnV3Error("Column geometry update cannot change native relationships")
        if name not in new or new[name].ifc_guid!=prev.ifc_guid:
            raise ColumnV3Error("Original Column GlobalId changed")
        a=dict(prev.attributes)
        b=dict(new[name].attributes)
        fields=tuple(sorted(k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)))
        if fields==("height",):
            op="UPDATE_COLUMN_HEIGHT"
            solid=_height_solid(native,column)
            expected_id=solid.id()
            target=_column_params(b)
            delta_pos=(0.0,0.0,0.0)
        elif set(fields)<={"x","y","z"} and fields:
            op="MOVE_COLUMN"
            point=_placement_point(native,column)
            expected_id=point.id()
            target=_column_params(b)
            delta_pos=tuple(target[i]-old_low[i] for i in range(3))
            if any(not math.isfinite(v) or abs(v)>10000 for v in delta_pos):
                raise ColumnV3Error("Column target translation invalid")
        else:
            raise ColumnV3Error("v0.3 supports only Column world xyz translation OR direct solid height")
        if any(abs(float(b[k])-float(a[k]))>1e-8 for k in ("width","depth") ):
            raise ColumnV3Error("Column width/depth must remain unchanged")

    def writer(staged:Path):
        if op=="MOVE_COLUMN":
            point=_placement_point(native,column)
            coordinates=tuple(float(v) for v in point.Coordinates)
            if len(coordinates)!=3:
                raise ColumnV3Error("Column placement must have 3D point")
            point.Coordinates=tuple(coordinates[i]+delta_pos[i] for i in range(3))
        elif op=="UPDATE_COLUMN_HEIGHT":
            solid=_height_solid(native,column)
            solid.Depth=float(target[5])
        elif op=="DELETE_COLUMN":
            _validate_delete_dependencies(native,column)
            ifcopenshell.api.root.remove_product(native,product=column)
        else:
            raise ColumnV3Error("Unknown prospective native mutation")
        native.write(str(staged))

    def validator(staged:Path):
        if snapshot_source(source).source_sha256!=sourcehash:
            raise ColumnV3Error("Source changed during transaction")
        candidate=ifcopenshell.open(str(staged))
        if op=="DELETE_COLUMN":
            try:
                candidate.by_guid(prev.ifc_guid)
                raise ColumnV3Error("Deleted native Column still exists")
            except RuntimeError:
                pass
            _delete_preservation(source,staged,prev.ifc_guid)
        else:
            col=_resolve(candidate,prev.ifc_guid)
            now_low,now_high=_world_bbox(col)
            if op=="MOVE_COLUMN":
                want_low=tuple(old_low[i]+delta_pos[i] for i in range(3))
                want_high=tuple(old_high[i]+delta_pos[i] for i in range(3))
                if any(not math.isclose(g,w,rel_tol=0,abs_tol=EPS)
                       for g,w in zip((*now_low,*now_high),(*want_low,*want_high))):
                    raise ColumnV3Error("Actual native Column mesh did not translate rigidly")
            else:
                if any(abs(now_low[i]-old_low[i])>EPS for i in range(3)):
                    raise ColumnV3Error("Column height edit moved bottom footprint")
                if any(abs(now_high[i]-old_high[i])>EPS for i in (0,1)):
                    raise ColumnV3Error("Column height edit changed horizontal extents")
                if not math.isclose(now_high[2]-old_high[2],target[5]-float(dict(prev.attributes)["height"]),
                                    rel_tol=0,abs_tol=EPS):
                    raise ColumnV3Error("Column actual world Z height was not updated")
            _unchanged_after_update(source,staged,prev.ifc_guid,expected_id)

    stage_and_commit(destination,writer,validator)
    untouched=(_delete_preservation(source,destination,prev.ifc_guid)
               if op=="DELETE_COLUMN" else _unchanged_after_update(
                   source,destination,prev.ifc_guid,expected_id))
    if snapshot_source(source).source_sha256!=sourcehash:
        raise ColumnV3Error("Source changed following output commit")
    report=snapshot_source(destination)
    line=(doc_before if op=="DELETE_COLUMN" else doc_after).managed_by_id()[name].span.line
    change=Mutation(op,name,prev.ifc_guid,line,
                    (("entity",) if op=="DELETE_COLUMN" else
                     (("height",) if op=="UPDATE_COLUMN_HEIGHT" else ("x","y","z"))),
                    "experiment v0.3 strict existing native Column isolated state edit")
    return ColumnV3CompileReport(
        sourcehash,report.source_sha256,
        projected.source.graph_fingerprint,report.graph_fingerprint,
        (change,),untouched,(),destination,True)
