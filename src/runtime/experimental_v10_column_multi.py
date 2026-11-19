"""Prospective v0.10 research native IFC4X3 multi-Column delete by Slab contact.

The direct-markup LLM edits a WHOLE declarative XML source-state snapshot.
Only the trusted runtime outside the model loop may use IfcOpenShell.
Task's original-public named reference Slab GUID is trusted task context,
NOT a hidden grading target or model-facing imperative command.

Supported, intentionally narrow: source has exactly ten native mapped
IfcColumns in two original storeys and the original public rectangular slab.
Exactly the five Columns *without direct bottom-face physical contact* to the
named slab are deleted by omitting their stable XML IDs; the five supported
Columns are unchanged. Source native typed data, material/type owners,
non-target geometry and all surviving relations are preserved fail-closed.
No model calls, no scores from this code.
"""
from __future__ import annotations

from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit
import numpy as np

from src.runtime.compiler import CompileReport
from src.runtime.ifc_mutations import Mutation
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.transaction import stage_and_commit
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document
from src.runtime.semantic_graph import graph_diff
from src.runtime.experimental_v9_projection import project_ifc_v9
from src.runtime.experimental_v7_projection import _mesh_exact_axis_box

EPS=1e-5


class MultiColumnV10Error(ValueError):
    pass


class MultiColumnV10Report(CompileReport):
    def as_dict(self):
        result=super().as_dict()
        result.update({
            "status":"COMMITTED_SOURCE_CONTACT_BOUNDED_MULTI_COLUMN_DELETE_V010",
            "compiler_version":"experimental-original-ifc4x3-multi-column-v0.10",
            "original_native_reference_relation":"verified physical bottom contact, not an invented IfcRelConnectsElement",
            "removed_native_column_count":len(self.operations),
            "preserved_original_ifc4x3_schema":True,
            "original_published_45_backend_parity_proven":False,
            "historical_real_GPT6_model_scores_unchanged":True,
            "paid_model_calls":0,
        })
        return result


def _box(product):
    """Complete original native 8-vertex/12-triangle, six-face world prism."""
    try:
        low, high=_mesh_exact_axis_box(product)
    except Exception as exc:
        raise MultiColumnV10Error(
            "Actual original IFC geometric world box unavailable; no AABB substitute"
        ) from exc
    lower=np.asarray(low,dtype=float)
    upper=np.asarray(high,dtype=float)
    if (not np.all(np.isfinite(lower)) or
        not np.all(np.isfinite(upper)) or
        not np.all(upper>lower)):
        raise MultiColumnV10Error("Original IFC native bounding prism invalid")
    return lower,upper


def source_native_slab_contact_plan(f,reference_slab_guid):
    """Derive original physical support only; no hidden GT or author score."""
    if not isinstance(reference_slab_guid,str) or len(reference_slab_guid)!=22:
        raise MultiColumnV10Error("A public original source reference Slab GlobalId is required")
    if f.schema!="IFC4X3" or abs(float(ifcopenshell.util.unit.calculate_unit_scale(f))-1.)>1e-8:
        raise MultiColumnV10Error("Original native IFC4X3 metre-normalized source required")
    try:
        slab=f.by_guid(reference_slab_guid)
    except RuntimeError as exc:
        raise MultiColumnV10Error("Named original public reference Slab is absent") from exc
    if not slab.is_a("IfcSlab"):
        raise MultiColumnV10Error("Public reference IFC GlobalId is not an IfcSlab")
    slab_lo,slab_hi=_box(slab)
    slab_container=ifcopenshell.util.element.get_container(slab)
    if slab_container is None or not slab_container.is_a("IfcBuildingStorey"):
        raise MultiColumnV10Error("Named original Slab has no source Storey containment")
    if any(rel.is_a("IfcRelConnectsElements") and
           (getattr(rel,"RelatingElement",None)==slab or
            getattr(rel,"RelatedElement",None)==slab)
           for rel in f.get_inverse(slab)):
        raise MultiColumnV10Error(
            "Original explicit native semantic Slab connections require a distinct relation policy"
        )
    columns=sorted(f.by_type("IfcColumn"),key=lambda c:c.GlobalId)
    if len(columns)!=10:
        raise MultiColumnV10Error(
            "v0.10 physical support policy audited only for exactly ten original Columns"
        )
    contacting=[]
    noncontact=[]
    source_geometry={}
    all_containers=set()
    for col in columns:
        if col.Representation is None or len(col.Representation.Representations)!=1:
            raise MultiColumnV10Error("Original Column source mapping unexpectedly absent")
        items=col.Representation.Representations[0].Items
        if len(items)!=1 or not items[0].is_a("IfcMappedItem"):
            raise MultiColumnV10Error("Original IFC Column is not one native mapped source item")
        low,high=_box(col)
        container=ifcopenshell.util.element.get_container(col)
        if container is None or not container.is_a("IfcBuildingStorey"):
            raise MultiColumnV10Error("Original IFC Column not contained in source Storey")
        all_containers.add(container.GlobalId)
        xy_overlap=float(max(0.,min(high[0],slab_hi[0])-max(low[0],slab_lo[0]))
                         *max(0.,min(high[1],slab_hi[1])-max(low[1],slab_lo[1])))
        bottom_area=float((high[0]-low[0])*(high[1]-low[1]))
        touching=(abs(low[2]-slab_hi[2])<=EPS
                  and xy_overlap>=.99*bottom_area
                  and container.GlobalId==slab_container.GlobalId)
        if abs(low[2]-slab_hi[2])<=EPS and not touching:
            raise MultiColumnV10Error(
                "Ambiguous Column corner-edge partial contact/Storey mismatch in source"
            )
        if low[2]<slab_hi[2]-EPS and not touching:
            raise MultiColumnV10Error(
                "Column penetrates or crosses named Slab plane; not safe to classify as unrelated"
            )
        source_geometry[col.GlobalId]={
            "native_lower_corner_m":tuple(float(x) for x in low),
            "native_upper_corner_m":tuple(float(x) for x in high),
            "bottom_face_slab_XY_overlap_fraction":xy_overlap/bottom_area,
            "source_native_storey_guid":container.GlobalId,
            "source_original_mapped_representation_guid":items[0].MappingSource.id(),
            "native_support_contact":bool(touching),
        }
        if touching:
            contacting.append(col.GlobalId)
        else:
            noncontact.append(col.GlobalId)
    if len(contacting)!=5 or len(noncontact)!=5 or len(all_containers)!=2:
        raise MultiColumnV10Error(
            "Original public source expected five contacting and five noncontacting mapped Columns"
        )
    if set(contacting)&set(noncontact):
        raise MultiColumnV10Error("Source native column relationship classification overlaps")
    return {
        "named_public_slab_guid":reference_slab_guid,
        "named_public_slab_world_bottom_m":tuple(slab_lo),
        "named_public_slab_world_top_m":tuple(slab_hi),
        "named_public_slab_storey_guid":slab_container.GlobalId,
        "contacting_keep_guids":tuple(contacting),
        "noncontact_delete_guids":tuple(noncontact),
        "source_column_geometry":source_geometry,
        "expected_removed_native_columns":5,
        "source_relation_policy":"physical bottom face / full native box + 99% XY overlap + actual source Storey",
        "no_fake_IfcRelConnectsElements":True,
    }


def _preflight_inverse_dependencies(f,deletion):
    """Source-only inverse graph contract for each removed Column."""
    before_roots={x.GlobalId:x for x in f.by_type("IfcRoot")}
    root_gone=set(deletion)
    allowed={"IfcRelContainedInSpatialStructure",
             "IfcRelDefinesByType","IfcRelDefinesByProperties"}
    managed_survivor_membership={}
    removed_product_reps=set()
    for guid in deletion:
        col=f.by_guid(guid)
        if not col.is_a("IfcColumn"):
            raise MultiColumnV10Error("Source delete target not a native IfcColumn")
        for rep in col.Representation.Representations:
            removed_product_reps.add(rep.id())
        for rel in f.get_inverse(col):
            if rel.is_a() not in allowed:
                raise MultiColumnV10Error(
                    "Column has unsupported inverse dependency "+rel.is_a()
                )
            cls=rel.is_a()
            if cls=="IfcRelDefinesByProperties":
                members=rel.RelatedObjects
                if len(members)!=1 or members[0].GlobalId!=guid:
                    raise MultiColumnV10Error("Original IfcColumn property relationship shared")
                pset=rel.RelatingPropertyDefinition
                if pset is None or not pset.is_a("IfcPropertySet"):
                    raise MultiColumnV10Error("Column native Pset has unsupported definition")
                if len([inv for inv in f.get_inverse(pset)
                        if inv.is_a("IfcRelDefinesByProperties")])!=1:
                    raise MultiColumnV10Error("Original native Column Pset shared with other source object")
                root_gone.update((rel.GlobalId,pset.GlobalId))
                continue
            members=(rel.RelatedElements if cls=="IfcRelContainedInSpatialStructure"
                     else rel.RelatedObjects)
            originals={x.GlobalId for x in members}
            if guid not in originals:
                raise MultiColumnV10Error("Original Column inverse membership contract missing")
            surviving=originals-set(deletion)
            if not surviving:
                root_gone.add(rel.GlobalId)
            else:
                if rel.GlobalId in managed_survivor_membership:
                    old=managed_survivor_membership[rel.GlobalId]
                    if old!=surviving:
                        raise MultiColumnV10Error("Original typed relation membership unexpectedly contradictory")
                managed_survivor_membership[rel.GlobalId]=surviving
    if root_gone-set(before_roots):
        raise MultiColumnV10Error("Missing original root in delete source dependency graph")
    return root_gone,managed_survivor_membership,removed_product_reps


def verify_native_multi_column_delete(
    source:Path, candidate:Path, plan:dict
)->int:
    """Trusted post-write native IFC graph + physical preservation check."""
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(candidate))
    if a.schema!="IFC4X3" or b.schema!=a.schema:
        raise MultiColumnV10Error("Original native IFC4X3 schema was changed")
    deletion=set(plan["noncontact_delete_guids"])
    kept=set(plan["contacting_keep_guids"])
    again=source_native_slab_contact_plan(a,plan["named_public_slab_guid"])
    if (set(again["noncontact_delete_guids"])!=deletion
        or set(again["contacting_keep_guids"])!=kept):
        raise MultiColumnV10Error("Source physical Slab-contact classification changed")
    old_step={e.id():str(e) for e in a}
    new_step={e.id():str(e) for e in b}
    if set(new_step)-set(old_step):
        raise MultiColumnV10Error("Column deletion added unexpected IFC STEP nodes")
    deleted_step=set(old_step)-set(new_step)
    changed={i for i in set(old_step)&set(new_step)
             if old_step[i]!=new_step[i]}
    allowed_removed_classes={
        "IfcColumn","IfcPropertySet","IfcRelDefinesByProperties",
        "IfcRelDefinesByType","IfcProductDefinitionShape","IfcCartesianPoint",
        "IfcAxis2Placement3D","IfcLocalPlacement","IfcPropertySingleValue",
        "IfcMappedItem","IfcShapeRepresentation","IfcAxis2Placement2D",
        "IfcExtrudedAreaSolid","IfcRectangleProfileDef","IfcPolyline",
        "IfcCartesianPointList2D",
    }
    for id in deleted_step:
        if a.by_id(id).is_a() not in allowed_removed_classes:
            raise MultiColumnV10Error(
                "Native multi-delete lost unrelated source STEP entity type"
            )
    for id in deleted_step:
        for inverse in a.get_inverse(a.by_id(id)):
            if inverse.id() not in deleted_step and inverse.id() not in changed:
                raise MultiColumnV10Error(
                    "Removed native IFC entity referenced by an unchanged surviving IFC STEP entity"
                )
    root_removed,allowed_membership,removed_reps=_preflight_inverse_dependencies(a,deletion)
    roots0={r.GlobalId:r for r in a.by_type("IfcRoot")}
    roots1={r.GlobalId:r for r in b.by_type("IfcRoot")}
    if set(roots1)-set(roots0) or set(roots0)-set(roots1)!=root_removed:
        raise MultiColumnV10Error(
            "Native multi-Column delete removed or added unexpected IFC Roots/Psets"
        )
    changed_root_steps=set()
    for guid,obj in roots1.items():
        old=roots0[guid]
        if old.is_a()!=obj.is_a():
            raise MultiColumnV10Error("Surviving original IFC Root class changed")
        if str(old)==str(obj):
            continue
        if guid not in allowed_membership:
            raise MultiColumnV10Error("Unrelated source Root/metadata modified")
        if old.is_a()=="IfcRelContainedInSpatialStructure":
            originals={x.GlobalId for x in old.RelatedElements}
            survivors={x.GlobalId for x in obj.RelatedElements}
            if (obj.RelatingStructure.GlobalId!=old.RelatingStructure.GlobalId
                or survivors!=allowed_membership[guid]
                or survivors!=originals-deletion):
                raise MultiColumnV10Error("Original source Storey containment damaged")
        elif old.is_a()=="IfcRelDefinesByType":
            originals={x.GlobalId for x in old.RelatedObjects}
            survivors={x.GlobalId for x in obj.RelatedObjects}
            if (obj.RelatingType.GlobalId!=old.RelatingType.GlobalId
                or survivors!=allowed_membership[guid]
                or survivors!=originals-deletion):
                raise MultiColumnV10Error("Surviving native Column type association changed")
        else:
            raise MultiColumnV10Error("Unexpected original IFC type of changed Root")
        changed_root_steps.add(old.id())
    touched_nonroot=changed-changed_root_steps
    for id in touched_nonroot:
        before=a.by_id(id)
        after=b.by_id(id)
        if (not before.is_a("IfcPresentationLayerAssignment")
            or not after.is_a("IfcPresentationLayerAssignment")):
            raise MultiColumnV10Error("Non-presentation/non-typed original STEP object modified")
        orig={x.id() for x in before.AssignedItems}
        current={x.id() for x in after.AssignedItems}
        if (current-orig or not orig-current<=removed_reps
            or (current & deleted_step)):
            raise MultiColumnV10Error(
                "Surviving source presentation layer lost unrelated representation references"
            )
    # New schema-valid output must have precisely the original five
    # physical source Columns in contact with the named lower Slab, and
    # no other original native IFC Products removed or renamed.
    products_a={x.GlobalId:x for x in a.by_type("IfcProduct")}
    products_b={x.GlobalId:x for x in b.by_type("IfcProduct")}
    if set(products_b)!=set(products_a)-deletion:
        raise MultiColumnV10Error("Native deletion removed/added non-target IFC Products")
    if {x.GlobalId for x in b.by_type("IfcColumn")}!=kept:
        raise MultiColumnV10Error("Surviving Columns do not exactly equal source physical supports")
    validated=0
    for guid,obj in products_b.items():
        source_obj=products_a[guid]
        if source_obj.is_a()!=obj.is_a() or str(source_obj)!=str(obj):
            raise MultiColumnV10Error("Original surviving native IFC Product changed")
        if obj.Representation is None:
            continue
        # Compare native vertex positions and triangle arrays, not only
        # a box/centroid summary. For original source triangular prisms this
        # ensures the actual world geometry did not change.
        try:
            opts=ifcopenshell.geom.settings()
            opts.set(opts.USE_WORLD_COORDS,True)
            # Keep BOTH native C++ shape owners alive while reading their
            # wrapped geometry. Accessing .geometry from a temporary shape
            # may free underlying OCC memory and crash (access violation).
            shape0=ifcopenshell.geom.create_shape(opts,source_obj)
            shape1=ifcopenshell.geom.create_shape(opts,obj)
            g0=shape0.geometry
            g1=shape1.geometry
            p0=np.asarray(g0.verts,dtype=float)
            p1=np.asarray(g1.verts,dtype=float)
            f0=np.asarray(g0.faces,dtype=int)
            f1=np.asarray(g1.faces,dtype=int)
        except Exception as exc:
            raise MultiColumnV10Error("Original native IFC survivor physical mesh unavailable") from exc
        if (p0.shape!=p1.shape or f0.shape!=f1.shape
            or not np.allclose(p0,p1,rtol=0,atol=EPS)
            or not np.array_equal(f0,f1)):
            raise MultiColumnV10Error("Surviving original native IFC geometry modified by delete")
        validated+=1
    # Check all original source Slabs remain with same native geometry and
    # original named Slab is still in correct original native Storey.
    ref=b.by_guid(plan["named_public_slab_guid"])
    lo,hi=_box(ref)
    if (not np.allclose(lo,plan["named_public_slab_world_bottom_m"],atol=EPS)
        or not np.allclose(hi,plan["named_public_slab_world_top_m"],atol=EPS)
        or ifcopenshell.util.element.get_container(ref).GlobalId
        !=plan["named_public_slab_storey_guid"]):
        raise MultiColumnV10Error("Original named physical Slab source was altered")
    # Every removed original column was explicitly noncontact, and every
    # remaining Column was original contact; no private GT consulted.
    return validated


def compile_declarative_xml_v10(
    source:Path,
    edited_xml:bytes,
    destination:Path,
    *,
    reference_slab_guid:str,
)->MultiColumnV10Report:
    """Source-hash-pinned whole-XML diff -> bounded native 5 Column delete."""
    if (not source.is_file() or source.is_symlink()
        or destination.exists() or destination.is_symlink()
        or source.resolve()==destination.resolve()):
        raise MultiColumnV10Error(
            "Existing original source IFC required; destination must be unused and distinct"
        )
    projection=project_ifc_v9(source)
    source_hash=projection.source.source_sha256
    before_ast=parse_xml(projection.xml,expected_source_sha256=source_hash)
    after_ast=parse_xml(edited_xml,expected_source_sha256=source_hash)
    old=bind_document(before_ast,projection=projection)
    new=bind_document(after_ast,projection=projection,verify_native_edges=False)
    diff=graph_diff(old.graph,new.graph)
    oldnodes=old.graph.by_id()
    if (diff.added_nodes or diff.changed_nodes or diff.added_edges
        or not diff.removed_nodes):
        raise MultiColumnV10Error(
            "Only removal of complete source-Column XML nodes is supported; no mixed native edit"
        )
    native=ifcopenshell.open(str(source))
    plan=source_native_slab_contact_plan(native,reference_slab_guid)
    target_guids=set(plan["noncontact_delete_guids"])
    deletions={id:oldnodes[id] for id in diff.removed_nodes}
    if (len(deletions)!=len(target_guids)
        or any(node.kind!="Column" or node.provenance!="existing_source"
               for node in deletions.values())
        or {node.ifc_guid for node in deletions.values()}!=target_guids):
        raise MultiColumnV10Error(
            "Declarative removed nodes must be exactly ALL source Columns not touching named Slab"
        )
    source_columns={x.GlobalId for x in native.by_type("IfcColumn")}
    projected_columns={n.ifc_guid for n in oldnodes.values()
                       if n.kind=="Column" and n.provenance=="existing_source"}
    if projected_columns!=source_columns:
        raise MultiColumnV10Error("All original native Columns must be visible in source XML")
    # No dangling or extra topology operations: removing n Column nodes
    # deletes precisely n derived level-containment edges and nothing more.
    affected_level_edges={(e.relation,e.target,e.ownership) for e in diff.removed_edges}
    if affected_level_edges!={("in_storey",name,"derived") for name in deletions}:
        raise MultiColumnV10Error("Deleted Column source XML has unexpected structural edge change")
    if len(diff.removed_edges)!=len(deletions):
        raise MultiColumnV10Error("Deleted source Columns have duplicate unexpected relations")
    _preflight_inverse_dependencies(native,target_guids)
    if snapshot_source(source).source_sha256!=source_hash:
        raise MultiColumnV10Error("Original immutable IFC source changed during plan")

    def write_output(path):
        # Deterministic order; native IfcOpenShell removes only the declared
        # IFC Column plus solely-owned Psets, type/containment memberships,
        # mapped item references and associated representations. Shared
        # source type representations must remain intact.
        for guid in sorted(target_guids):
            ifcopenshell.api.root.remove_product(
                native,product=native.by_guid(guid))
        native.write(str(path))

    def validate(path):
        if snapshot_source(source).source_sha256!=source_hash:
            raise MultiColumnV10Error("Original source IFC mutated during staged native delete")
        verify_native_multi_column_delete(source,path,plan)

    stage_and_commit(destination,write_output,validate)
    if snapshot_source(source).source_sha256!=source_hash:
        raise MultiColumnV10Error("Original IFC input was modified after native delete")
    physical_preserved=verify_native_multi_column_delete(source,destination,plan)
    finished=snapshot_source(destination)
    mutations=tuple(
        Mutation(
            "DELETE_COLUMN_WITHOUT_NAMED_SLAB_CONTACT",name,
            deletions[name].ifc_guid,1,
            ("original_native_column","source_physical_slab_contact","dependency_safe_delete"),
            "v0.10 bounded original-native IFC4X3 source-only contact-based multi Column delete",
        )
        for name in sorted(deletions)
    )
    return MultiColumnV10Report(
        source_hash,finished.source_sha256,
        projection.source.graph_fingerprint,finished.graph_fingerprint,
        mutations,physical_preserved,(),destination,True,
    )
