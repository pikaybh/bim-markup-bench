"""Independent original-native IFC4X3 multi-Column / named-Slab contact oracle.

No imports from compiler, projection/binder/XML, original author grader or
hidden GT. This oracle independently derives the public source geometry
relationship and independently re-opens the original/candidate native IFC.
The source has no explicit IfcRelConnectsElements(Column,Slab): this is
strict physical support evidence, not a fabricated IFC semantic relation.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from itertools import product as corner_product
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit
import numpy as np

EPS=1e-5
PUBLIC_REFERENCE_SLAB_GUID="2IIWDJ6bzEPxU4iXeUX9Z5"


class IndependentNativeMultiV10Error(ValueError):
    pass


def _sha(path:Path)->str:
    h=sha256()
    with path.open("rb") as file:
        for buf in iter(lambda:file.read(1024*1024),b""):
            h.update(buf)
    return h.hexdigest()


def _mesh_box(entity):
    opts=ifcopenshell.geom.settings()
    opts.set(opts.USE_WORLD_COORDS,True)
    try:
        # Preserve C++ OCC lifetime while reading wrapped native geometry.
        shape=ifcopenshell.geom.create_shape(opts,entity)
        points=np.asarray(shape.geometry.verts,dtype=float).reshape(-1,3)
        triangles=np.asarray(shape.geometry.faces,dtype=int).reshape(-1,3)
    except Exception as exc:
        raise IndependentNativeMultiV10Error(
            "Original source real native world mesh unavailable"
        ) from exc
    if (len(points)!=8 or len(triangles)!=12
        or not np.all(np.isfinite(points))):
        raise IndependentNativeMultiV10Error(
            "Source physical solid is not a complete 8-vertex/12-triangle box"
        )
    low=points.min(axis=0);high=points.max(axis=0)
    if np.any(high-low<=.01):
        raise IndependentNativeMultiV10Error("Source native prism has degenerate dimension")
    expected=np.array(list(corner_product(*[
        (low[i],high[i]) for i in range(3)
    ])),dtype=float)
    if not all(any(np.allclose(p,c,rtol=0,atol=EPS) for c in expected)
               for p in points):
        raise IndependentNativeMultiV10Error(
            "Native source nonorthogonal box cannot use envelope-only support"
        )
    areas={(i,s):[] for i in range(3) for s in (0,1)}
    for face in triangles:
        tri=points[face]
        area=float(np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))/2.)
        plane=[(i,side) for i in range(3)
               for side,limit in ((0,low[i]),(1,high[i]))
               if np.all(np.abs(tri[:,i]-limit)<EPS)]
        if len(plane)!=1 or area<=0:
            raise IndependentNativeMultiV10Error(
                "Native original solid has partial/clipped/nonplanar face"
            )
        areas[plane[0]].append(area)
    for (axis,side),face_areas in areas.items():
        other=[i for i in (0,1,2) if i!=axis]
        if (len(face_areas)!=2 or
            abs(sum(face_areas)-float(np.prod((high-low)[other])))>1e-4):
            raise IndependentNativeMultiV10Error(
                "Native original source has missing or overlapped box face"
            )
    return points,triangles,low,high


def _original_source_contact(f,guid):
    try:
        slab=f.by_guid(guid)
    except RuntimeError as exc:
        raise IndependentNativeMultiV10Error(
            "Named original public reference Slab not found"
        ) from exc
    if not slab.is_a("IfcSlab"):
        raise IndependentNativeMultiV10Error("Public named original GlobalId is not Slab")
    _,_,lower,upper=_mesh_box(slab)
    parent=ifcopenshell.util.element.get_container(slab)
    if parent is None or not parent.is_a("IfcBuildingStorey"):
        raise IndependentNativeMultiV10Error("Original reference Slab lacks Storey relation")
    cols=f.by_type("IfcColumn")
    if len(cols)!=10:
        raise IndependentNativeMultiV10Error("Original source not ten physical native Columns")
    keeping={}
    deleting={}
    for col in cols:
        _,_,lo,hi=_mesh_box(col)
        owner=ifcopenshell.util.element.get_container(col)
        if owner is None or not owner.is_a("IfcBuildingStorey"):
            raise IndependentNativeMultiV10Error(
                "Original source Column lacks native spatial containment"
            )
        overlap_x=max(0.,min(hi[0],upper[0])-max(lo[0],lower[0]))
        overlap_y=max(0.,min(hi[1],upper[1])-max(lo[1],lower[1]))
        coverage=float(overlap_x*overlap_y/((hi[0]-lo[0])*(hi[1]-lo[1])))
        touches=(abs(lo[2]-upper[2])<=EPS and coverage>=.99
                 and owner.GlobalId==parent.GlobalId)
        if abs(lo[2]-upper[2])<=EPS and not touches:
            raise IndependentNativeMultiV10Error("Ambiguous original partial Slab contact")
        if lo[2]<upper[2]-EPS and not touches:
            raise IndependentNativeMultiV10Error("Original Column intersects named Slab")
        data={
            "globalid":col.GlobalId,
            "world_min_m":list(map(float,lo)),
            "world_max_m":list(map(float,hi)),
            "source_native_storey":owner.GlobalId,
            "native_physical_contact":touches,
        }
        (keeping if touches else deleting)[col.GlobalId]=data
    if len(keeping)!=5 or len(deleting)!=5:
        raise IndependentNativeMultiV10Error(
            "Original public native contact partition differs from exactly 5 keep/5 delete"
        )
    return keeping,deleting,lower,upper,parent.GlobalId


def verify_v10_original_native_column_multi_delete(
    source:Path,candidate:Path,*,
    reference_slab_guid:str=PUBLIC_REFERENCE_SLAB_GUID,
)->dict:
    if (not source.is_file() or not candidate.is_file()
        or source.is_symlink() or candidate.is_symlink()
        or source.resolve()==candidate.resolve()):
        raise IndependentNativeMultiV10Error("Invalid source/native candidate IFC path")
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(candidate))
    if (a.schema!="IFC4X3" or b.schema!="IFC4X3"
        or abs(float(ifcopenshell.util.unit.calculate_unit_scale(a))-1.)>1e-8
        or abs(float(ifcopenshell.util.unit.calculate_unit_scale(b))-1.)>1e-8):
        raise IndependentNativeMultiV10Error(
            "Original native IFC4X3/metre schema is not preserved"
        )
    keep,delete,lower,upper,parent=_original_source_contact(
        a,reference_slab_guid)
    expected_keep=set(keep);expected_delete=set(delete)
    p0={x.GlobalId:x for x in a.by_type("IfcProduct")}
    p1={x.GlobalId:x for x in b.by_type("IfcProduct")}
    if (set(p1)!=set(p0)-expected_delete
        or {c.GlobalId for c in b.by_type("IfcColumn")}!=expected_keep):
        raise IndependentNativeMultiV10Error(
            "Native output removed wrong original IFC Products/Columns"
        )
    roots0={x.GlobalId:x for x in a.by_type("IfcRoot")}
    roots1={x.GlobalId:x for x in b.by_type("IfcRoot")}
    if set(roots1)-set(roots0):
        raise IndependentNativeMultiV10Error("Unexpected new IFC Root added by native delete")
    lost_roots=set(roots0)-set(roots1)
    lost_types=Counter(roots0[g].is_a() for g in lost_roots)
    expected_counts={
        "IfcColumn":5,
        "IfcPropertySet":15,
        "IfcRelDefinesByProperties":15,
        "IfcRelDefinesByType":5,
    }
    if dict(lost_types)!=expected_counts or not expected_delete<=lost_roots:
        raise IndependentNativeMultiV10Error(
            "Native Root/type/Pset ownership was not deleted as exactly observed in source"
        )
    for guid in lost_roots-expected_delete:
        root=roots0[guid]
        if root.is_a("IfcRelDefinesByProperties"):
            if (len(root.RelatedObjects)!=1
                or root.RelatedObjects[0].GlobalId not in expected_delete):
                raise IndependentNativeMultiV10Error(
                    "Original shared native property relation incorrectly removed"
                )
        elif root.is_a("IfcPropertySet"):
            original_refs=[x for x in a.get_inverse(root)
                           if x.is_a("IfcRelDefinesByProperties")]
            if (len(original_refs)!=1
                or original_refs[0].GlobalId not in lost_roots):
                raise IndependentNativeMultiV10Error(
                    "Original surviving IFC product still uses deleted PropertySet"
                )
        elif root.is_a("IfcRelDefinesByType"):
            if not set(x.GlobalId for x in root.RelatedObjects)<=expected_delete:
                raise IndependentNativeMultiV10Error(
                    "Native surviving Column's type association was deleted"
                )
        else:
            raise IndependentNativeMultiV10Error("Unexpected original source rooted dependency deleted")
    changed_root_ids=[]
    for guid,root in roots1.items():
        before=roots0[guid]
        if root.is_a()!=before.is_a():
            raise IndependentNativeMultiV10Error("Original surviving IFC Root class changed")
        if str(root)==str(before):
            continue
        if not before.is_a("IfcRelContainedInSpatialStructure"):
            raise IndependentNativeMultiV10Error(
                "Unrelated original IFC Root or native type/material graph changed"
            )
        old_members={p.GlobalId for p in before.RelatedElements}
        new_members={p.GlobalId for p in root.RelatedElements}
        if (root.RelatingStructure.GlobalId!=before.RelatingStructure.GlobalId
            or new_members!=old_members-expected_delete
            or old_members-new_members!=expected_delete):
            raise IndependentNativeMultiV10Error(
                "Original native Storey membership changed incorrectly"
            )
        changed_root_ids.append(guid)
    if len(changed_root_ids)!=1:
        raise IndependentNativeMultiV10Error("Only original L2 native containment may change")
    oldsteps={x.id():str(x) for x in a}
    newsteps={x.id():str(x) for x in b}
    if set(newsteps)-set(oldsteps):
        raise IndependentNativeMultiV10Error("Unexpected new native IFC STEP entity after delete")
    disappeared=set(oldsteps)-set(newsteps)
    changed={i for i in set(oldsteps)&set(newsteps) if oldsteps[i]!=newsteps[i]}
    if len(disappeared)!=75 or len(changed)!=2:
        raise IndependentNativeMultiV10Error(
            "Unapproved native IFC STEP deletion/mutation count"
        )
    if Counter(a.by_id(i).is_a() for i in changed)!={
        "IfcRelContainedInSpatialStructure":1,
        "IfcPresentationLayerAssignment":1,
    }:
        raise IndependentNativeMultiV10Error(
            "Unapproved source STEP class modified by deletion"
        )
    allowed_deleted={
        "IfcColumn","IfcPropertySet","IfcRelDefinesByProperties",
        "IfcRelDefinesByType","IfcProductDefinitionShape",
        "IfcCartesianPoint","IfcAxis2Placement3D","IfcLocalPlacement",
        "IfcPropertySingleValue","IfcMappedItem","IfcShapeRepresentation",
    }
    for i in disappeared:
        if a.by_id(i).is_a() not in allowed_deleted:
            raise IndependentNativeMultiV10Error("Unrelated original source STEP object deleted")
        for inv in a.get_inverse(a.by_id(i)):
            if inv.id() not in disappeared and inv.id() not in changed:
                raise IndependentNativeMultiV10Error(
                    "Removed STEP entity still referenced by original surviving native source"
                )
    removed_shape_representations={
        rep.id()
        for guid in expected_delete
        for rep in a.by_guid(guid).Representation.Representations
    }
    layers=[i for i in changed
            if a.by_id(i).is_a("IfcPresentationLayerAssignment")]
    original_items={x.id() for x in a.by_id(layers[0]).AssignedItems}
    remaining_items={x.id() for x in b.by_id(layers[0]).AssignedItems}
    if (remaining_items-original_items or
        not original_items-remaining_items<=removed_shape_representations):
        raise IndependentNativeMultiV10Error(
            "Unrelated source presentation layer was altered"
        )
    checked_geometry=0
    for guid,obj in p1.items():
        before=p0[guid]
        if obj.is_a()!=before.is_a() or str(obj)!=str(before):
            raise IndependentNativeMultiV10Error(
                "Surviving original source IFC Product metadata changed"
            )
        if obj.Representation is None:
            continue
        settings=ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS,True)
        # Retain native C++ shape owners; no temporary geometry lifetime bug.
        shape0=ifcopenshell.geom.create_shape(settings,before)
        shape1=ifcopenshell.geom.create_shape(settings,obj)
        vertices0=np.asarray(shape0.geometry.verts,dtype=float)
        vertices1=np.asarray(shape1.geometry.verts,dtype=float)
        faces0=np.asarray(shape0.geometry.faces,dtype=int)
        faces1=np.asarray(shape1.geometry.faces,dtype=int)
        if (vertices0.shape!=vertices1.shape or faces0.shape!=faces1.shape
            or not np.allclose(vertices0,vertices1,atol=EPS,rtol=0)
            or not np.array_equal(faces0,faces1)):
            raise IndependentNativeMultiV10Error(
                "Surviving original source IFC Product physical native mesh changed"
            )
        checked_geometry+=1
    result_slab=b.by_guid(reference_slab_guid)
    _,_,now_low,now_high=_mesh_box(result_slab)
    if (not np.allclose(now_low,lower,atol=EPS,rtol=0)
        or not np.allclose(now_high,upper,atol=EPS,rtol=0)
        or ifcopenshell.util.element.get_container(result_slab).GlobalId!=parent):
        raise IndependentNativeMultiV10Error("Named original public reference Slab was modified")
    for guid in expected_keep:
        orig_map=p0[guid].Representation.Representations[0].Items[0].MappingSource.id()
        new_map=p1[guid].Representation.Representations[0].Items[0].MappingSource.id()
        if orig_map!=new_map:
            raise IndependentNativeMultiV10Error(
                "Original native surviving mapped Column shape/type source changed"
            )
    return {
        "status":"INDEPENDENT_ORIGINAL_SOURCE_SLAB_CONTACT_MULTI_COLUMN_DELETE_PASS",
        "source_sha256":_sha(source),
        "candidate_sha256":_sha(candidate),
        "public_original_reference_slab_globalid":reference_slab_guid,
        "original_named_slab_top_world_z_m":float(upper[2]),
        "original_native_columns_count":len(keep)+len(delete),
        "original_native_contact_columns_preserved":tuple(sorted(keep)),
        "original_native_noncontact_columns_deleted":tuple(sorted(delete)),
        "relationship_evidence":"actual original world Slab upper face + each Column lower face with >=99 percent native XY footprint overlap and original Storey",
        "not_an_explicit_IfcRelConnectsElements":True,
        "removed_original_native_roots_by_class":dict(lost_types),
        "removed_original_native_step_entities":len(disappeared),
        "modified_original_native_step_entities":len(changed),
        "all_surviving_original_native_world_meshes_preserved":checked_geometry,
        "all_original_surviving_type_map_material_relations_preserved":True,
        "original_native_ifc4x3_schema_preserved":True,
        "new_LLM_model_run":False,
        "full_45_backend_parity_proven":False,
    }
