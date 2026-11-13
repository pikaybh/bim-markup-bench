"""Prospective experimental-only v0.4 IFC4X3 Slab native state compiler.

Only one isolated Slab CREATE/MOVE/RECTANGULAR_RESHAPE/THICKNESS/DELETE.
XML is a complete declarative state, NOT an operation/command list. Trusted
backend derives a one-node graph diff and modifies a clone of original IFC.
All revisions v0.1-v0.3 and historical model results remain untouched.
"""
from __future__ import annotations

from pathlib import Path
from decimal import Decimal
import math

import numpy as np
import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.api.geometry
import ifcopenshell.api.spatial
import ifcopenshell.util.placement
import ifcopenshell.util.element
import ifcopenshell.util.unit

from src.runtime.compiler import CompileReport
from src.runtime.ifc_mutations import Mutation
from src.runtime.transaction import stage_and_commit
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document
from src.runtime.semantic_graph import graph_diff
from src.runtime.experimental_v2_column import _body_context
from src.runtime.experimental_v4_projection import (
    project_ifc_v4,_slab_mesh_bbox,_source_slab_solid,
)


EPS=1e-5


class SlabV4Error(ValueError):
    pass


class SlabV4CompileReport(CompileReport):
    def as_dict(self):
        result=super().as_dict()
        result.update({
            "status":"COMMITTED_SCOPED_IFC4X3_"+self.operations[0].operation+"_V4",
            "compiler_version":"experimental-slab-v0.4",
            "general_ifc_authoring_parity_with_python":False,
            "original_45_case_native_backend_parity":False,
            "scope":"single native rectangular Slab, explicit fail-closed preservation",
        })
        return result


def _numeric(attrs,key):
    try:
        v=Decimal(attrs[key])
    except (KeyError,TypeError,ValueError,ArithmeticError) as exc:
        raise SlabV4Error("Invalid Slab "+key) from exc
    if not v.is_finite():
        raise SlabV4Error("Nonfinite Slab "+key)
    value=float(v)
    if not math.isfinite(value) or abs(value)>10000:
        raise SlabV4Error("Out-of-bounds Slab "+key)
    return value


def _params(attrs):
    v=tuple(_numeric(attrs,k) for k in ("x","y","z","width","depth","thickness"))
    if any(x<=0.02 or x>100 for x in v[3:]):
        raise SlabV4Error("Slab dimensions must be positive bounded numbers")
    return v


def _native_slab(f,guid):
    try:
        slab=f.by_guid(guid)
    except RuntimeError as exc:
        raise SlabV4Error("Original native Slab GlobalId missing") from exc
    if not slab.is_a("IfcSlab"):
        raise SlabV4Error("Target native GlobalId is not IfcSlab")
    return slab


def _unique_body(f,slab):
    solid=_source_slab_solid(f,slab)
    rep=slab.Representation.Representations[0]
    pds=slab.Representation
    owners=[x for x in f.get_inverse(rep) if x.is_a("IfcProductDefinitionShape")]
    products=[x for x in f.get_inverse(pds) if x.is_a("IfcProduct")]
    # Presentation layer and styled items are allowed additional read-only
    # inverse links; only *other product owners* would make an edit unsafe.
    if len(owners)!=1 or owners[0].id()!=pds.id() or len(products)!=1 or products[0].id()!=slab.id():
        raise SlabV4Error("Native slab shape representation is shared with another product")
    solid_owners=[x for x in f.get_inverse(solid) if x.is_a("IfcShapeRepresentation")]
    if len(solid_owners)!=1 or solid_owners[0].id()!=rep.id():
        raise SlabV4Error("Native Slab solid representation shared with another product")
    if len(f.get_inverse(solid.SweptArea))!=1 or len(f.get_inverse(solid.Position))!=1:
        raise SlabV4Error("Native slab rectangle or extrusion placement is shared")
    return solid


def _relative_point(f,slab):
    obj=slab.ObjectPlacement
    if obj is None or not obj.is_a("IfcLocalPlacement"):
        raise SlabV4Error("Only native local-placement Slab supported")
    relative=obj.RelativePlacement
    if not relative.is_a("IfcAxis2Placement3D"):
        raise SlabV4Error("Slab local placement is not 3D")
    if len(f.get_inverse(obj))!=1 or len(f.get_inverse(relative))!=1:
        raise SlabV4Error("Slab object or local placement shared with another object")
    p=relative.Location
    if p is None or not p.is_a("IfcCartesianPoint") or len(p.Coordinates)!=3:
        raise SlabV4Error("Slab object placement lacks 3D point")
    return relative,p


def _translate_local(f,parent,delta_world):
    if parent is None:
        r=np.eye(3)
    else:
        r=np.asarray(ifcopenshell.util.placement.get_local_placement(parent),dtype=float)[:3,:3]
    if not np.all(np.isfinite(r)) or not np.allclose(r.T@r,np.eye(3),atol=1e-7):
        raise SlabV4Error("Unsupported nonorthonormal parent placement")
    return r.T@np.asarray(delta_world,dtype=float)


def _edit_point(f,owner,point,local_delta):
    if len(point.Coordinates)!=3 or not np.all(np.isfinite(local_delta)):
        raise SlabV4Error("Invalid Slab location")
    nextcoords=tuple(float(point.Coordinates[i])+float(local_delta[i]) for i in range(3))
    if any(abs(v)>10000 or not math.isfinite(v) for v in nextcoords):
        raise SlabV4Error("Slab changed coordinates exceed bounded range")
    inv=list(f.get_inverse(point))
    if len(inv)==1 and inv[0].id()==owner.id():
        point.Coordinates=nextcoords
        return {point.id()},{}
    if not any(x.id()==owner.id() for x in inv):
        raise SlabV4Error("Placement owner does not reference its native point")
    # Copy on write when source's original CartesianPoint is reused across
    # other Revit geometry. Never translate the shared point in place.
    new_point=f.createIfcCartesianPoint(nextcoords)
    owner.Location=new_point
    return {owner.id()},{new_point.id(): "IfcCartesianPoint"}


def _expected_step_preservation(source,candidate,*,changed_ids,added_types):
    old=ifcopenshell.open(str(source))
    new=ifcopenshell.open(str(candidate))
    if old.schema!="IFC4X3" or new.schema!=old.schema:
        raise SlabV4Error("IFC4X3 source/output schema mismatch")
    a={e.id():str(e) for e in old}
    b={e.id():str(e) for e in new}
    if set(a)-set(b):
        raise SlabV4Error("Original IFC STEP entity disappeared during Slab edit")
    changed={i for i in a if a[i]!=b[i]}
    if changed!=changed_ids:
        raise SlabV4Error("Unrelated native STEP object changed during Slab edit")
    added=set(b)-set(a)
    if {i:new.by_id(i).is_a() for i in added}!=added_types:
        raise SlabV4Error("Slab edit added unapproved native STEP object")
    oldroots={x.GlobalId:x for x in old.by_type("IfcRoot")}
    newroots={x.GlobalId:x for x in new.by_type("IfcRoot")}
    if set(oldroots)!=set(newroots):
        raise SlabV4Error("Slab edit changed original native GlobalId inventory")
    for guid in oldroots:
        if str(oldroots[guid])!=str(newroots[guid]):
            raise SlabV4Error("Slab edit changed original non-target IFC Root")
    return len(oldroots)


def _verify_mesh(file,guid,expected):
    slab=_native_slab(file,guid)
    low,high=_slab_mesh_bbox(slab)
    intended=((*expected[:3],
               expected[0]+expected[3],expected[1]+expected[4],
               expected[2]+expected[5]))
    observed=(*low,*high)
    if not all(math.isclose(v,w,abs_tol=EPS,rel_tol=0) for v,w in zip(observed,intended)):
        raise SlabV4Error("Actual native Slab world mesh does not match edited XML")
    return low,high


def _native_add_preservation(source,result,new_guid):
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(result))
    old={e.id():str(e) for e in a}
    new={e.id():str(e) for e in b}
    if not set(old)<=set(new):
        raise SlabV4Error("Existing IFC STEP entity deleted during Slab creation")
    changed={id for id in old if old[id]!=new[id]}
    allowed={e.id() for e in a.by_type("IfcRelContainedInSpatialStructure")}
    if not changed<=allowed:
        raise SlabV4Error("Unrelated STEP entity changed during native Slab creation")
    # Existing storey containment is allowed to GROW by exactly the new
    # Slab's GlobalId; no old member may be dropped/replaced.
    containment_changed=0
    for relation in a.by_type("IfcRelContainedInSpatialStructure"):
        previous={x.GlobalId for x in relation.RelatedElements}
        after=b.by_guid(relation.GlobalId)
        following={x.GlobalId for x in after.RelatedElements}
        if following!=previous:
            if following!=previous|{new_guid}:
                raise SlabV4Error("Native Slab CREATE removed/replaced an original contained IFC element")
            containment_changed+=1
    if containment_changed!=1:
        raise SlabV4Error("Slab create must extend exactly one original storey containment relation")
    oldroots={x.GlobalId:x for x in a.by_type("IfcRoot")}
    newroots={x.GlobalId:x for x in b.by_type("IfcRoot")}
    if not set(oldroots)<=set(newroots) or new_guid not in newroots:
        raise SlabV4Error("Original IFC native Root missing after Slab creation")
    if not newroots[new_guid].is_a("IfcSlab"):
        raise SlabV4Error("Created GlobalId is not native IfcSlab")
    extras=set(newroots)-set(oldroots)-{new_guid}
    if any(not newroots[g].is_a("IfcRelContainedInSpatialStructure") for g in extras):
        raise SlabV4Error("Slab creation introduced unexpected native Root class")
    if len(b.by_type("IfcSlab"))!=len(a.by_type("IfcSlab"))+1:
        raise SlabV4Error("Created IfcSlab count inconsistent")
    if any(str(oldroots[g])!=str(newroots[g]) for g in oldroots
           if not oldroots[g].is_a("IfcRelContainedInSpatialStructure")):
        raise SlabV4Error("Unrelated native Root changed during creation")
    return len(oldroots)


def _validate_delete_dependencies(file,slab):
    allowed={
        "IfcRelContainedInSpatialStructure","IfcRelAssociatesMaterial",
        "IfcRelDefinesByType","IfcRelDefinesByProperties",
    }
    for relation in file.get_inverse(slab):
        if relation.is_a() not in allowed:
            raise SlabV4Error("Slab has an unsupported native inverse dependency")
        if relation.is_a("IfcRelContainedInSpatialStructure"):
            members=relation.RelatedElements
        else:
            members=relation.RelatedObjects
        if slab.GlobalId not in {x.GlobalId for x in members}:
            raise SlabV4Error("Slab native relation is inconsistent")
        if relation.is_a("IfcRelAssociatesMaterial"):
            if len(members)!=1:
                raise SlabV4Error("Slab material relationship is shared")
            use=relation.RelatingMaterial
            if use is None or not use.is_a("IfcMaterialLayerSetUsage"):
                raise SlabV4Error("Unknown Slab material association")
            if len(file.get_inverse(use))!=1:
                raise SlabV4Error("Slab material-layer usage is shared")
        if relation.is_a("IfcRelDefinesByProperties"):
            if len(members)!=1:
                raise SlabV4Error("Slab property relation is shared")
            pset=relation.RelatingPropertyDefinition
            if not pset.is_a("IfcPropertySet"):
                raise SlabV4Error("Unsupported Slab material/property definition")
            if len([r for r in file.get_inverse(pset)
                    if r.is_a("IfcRelDefinesByProperties")])!=1:
                raise SlabV4Error("Slab PropertySet shared with other native relation")


def _verify_native_delete(source,result,deleted_guid):
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(result))
    target=_native_slab(a,deleted_guid)
    _validate_delete_dependencies(a,target)
    origroots={x.GlobalId:x for x in a.by_type("IfcRoot")}
    newroots={x.GlobalId:x for x in b.by_type("IfcRoot")}
    if deleted_guid in newroots or set(newroots)-set(origroots):
        raise SlabV4Error("Target Slab survived or unrelated new IFC root was inserted")
    origproducts={x.GlobalId:x for x in a.by_type("IfcProduct")}
    newproducts={x.GlobalId:x for x in b.by_type("IfcProduct")}
    if set(newproducts)!=set(origproducts)-{deleted_guid}:
        raise SlabV4Error("Unrelated original IFC product removed by Slab deletion")
    if any(str(origproducts[g])!=str(newproducts[g]) for g in newproducts):
        raise SlabV4Error("Unrelated original IFC product was changed by delete")

    root_relations={
        x.GlobalId:x for x in a.get_inverse(target) if x.is_a() in {
            "IfcRelContainedInSpatialStructure","IfcRelAssociatesMaterial",
            "IfcRelDefinesByType","IfcRelDefinesByProperties",
        }
    }
    expected_removed={deleted_guid}
    allowed_changed=set()
    for guid,rel in root_relations.items():
        members=(rel.RelatedElements if rel.is_a("IfcRelContainedInSpatialStructure")
                 else rel.RelatedObjects)
        if rel.is_a("IfcRelDefinesByProperties"):
            expected_removed.add(guid)
            expected_removed.add(rel.RelatingPropertyDefinition.GlobalId)
        elif len(members)==1:
            expected_removed.add(guid)
        else:
            if guid not in newroots:
                raise SlabV4Error("Shared Slab native relationship deleted")
            later=newroots[guid]
            members_after=(later.RelatedElements if rel.is_a("IfcRelContainedInSpatialStructure")
                           else later.RelatedObjects)
            if {v.GlobalId for v in members_after}!={v.GlobalId for v in members}-{deleted_guid}:
                raise SlabV4Error("Unrelated native Slab relationship members changed")
            allowed_changed.add(guid)
    if set(origroots)-set(newroots)!=expected_removed:
        raise SlabV4Error("Unexpected native relationship/property root deletion")
    for guid in set(origroots)&set(newroots):
        original=origroots[guid]
        result_entity=newroots[guid]
        if original.is_a()!=result_entity.is_a():
            raise SlabV4Error("Native root IFC type changed unexpectedly")
        if str(original)!=str(result_entity) and guid not in allowed_changed:
            raise SlabV4Error("Unrelated native root changed during Slab deletion")

    old={e.id():str(e) for e in a}
    new={e.id():str(e) for e in b}
    disappeared=set(old)-set(new)
    appeared=set(new)-set(old)
    changed={i for i in old.keys()&new.keys() if old[i]!=new[i]}
    allowed_gone={
        "IfcSlab","IfcPropertySet","IfcRelDefinesByProperties",
        "IfcRelAssociatesMaterial","IfcRelContainedInSpatialStructure",
        "IfcRelDefinesByType","IfcAxis2Placement3D","IfcAxis2Placement2D",
        "IfcCartesianPoint","IfcLocalPlacement","IfcExtrudedAreaSolid",
        "IfcRectangleProfileDef","IfcProductDefinitionShape",
        "IfcShapeRepresentation","IfcMaterialLayerSetUsage",
        "IfcPropertySingleValue","IfcStyledItem",
    }
    if any(a.by_id(i).is_a() not in allowed_gone for i in disappeared):
        raise SlabV4Error("Slab delete removed unrelated STEP entity type")
    if any(not b.by_id(i).is_a("IfcOwnerHistory") for i in appeared):
        raise SlabV4Error("Slab delete added an unexpected STEP entity")
    for eid in disappeared:
        for inverse in a.get_inverse(a.by_id(eid)):
            if inverse.id() not in disappeared and inverse.id() not in changed:
                raise SlabV4Error("Removed source entity still owned by another IFC element")
    changed_allowed={origroots[g].id() for g in allowed_changed}
    original_repids={r.id() for r in target.Representation.Representations}
    for eid in changed-changed_allowed:
        older=a.by_id(eid)
        later=b.by_id(eid)
        if not older.is_a("IfcPresentationLayerAssignment") or not later.is_a("IfcPresentationLayerAssignment"):
            raise SlabV4Error("Unrelated original nonroot STEP entity changed during delete")
        before_set={x.id() for x in older.AssignedItems}
        after_set={x.id() for x in later.AssignedItems}
        if after_set-before_set or not before_set-after_set<=original_repids:
            raise SlabV4Error("Slab delete altered unrelated presentation layer items")
    return len(newproducts)


def compile_declarative_xml_v4(source:Path,edited_xml:bytes,destination:Path):
    if (not source.is_file() or source.is_symlink() or
        destination.exists() or destination.is_symlink()):
        raise SlabV4Error("Native IFC source required; output path must be unused")
    projection=project_ifc_v4(source)
    before=parse_xml(projection.xml,expected_source_sha256=projection.source.source_sha256)
    after=parse_xml(edited_xml,expected_source_sha256=projection.source.source_sha256)
    original=bind_document(before,projection=projection)
    edited=bind_document(after,projection=projection,verify_native_edges=False)
    delta=graph_diff(original.graph,edited.graph)
    source_nodes=original.graph.by_id()
    final_nodes=edited.graph.by_id()

    if len(delta.added_nodes)+len(delta.removed_nodes)+len(delta.changed_nodes)!=1:
        raise SlabV4Error("Only a single isolated declarative Slab object edit is supported")
    name=(delta.added_nodes or delta.removed_nodes or delta.changed_nodes)[0]
    node=(final_nodes if delta.added_nodes or delta.changed_nodes else source_nodes)[name]
    if node.kind!="Slab":
        raise SlabV4Error("Only native Slab modifications belong to v0.4")
    f=ifcopenshell.open(str(source))
    if f.schema!="IFC4X3" or abs(ifcopenshell.util.unit.calculate_unit_scale(f)-1.)>1e-8:
        raise SlabV4Error("IFC4X3 source with native metre units required")
    sourcehash=projection.source.source_sha256
    if snapshot_source(source).source_sha256!=sourcehash:
        raise SlabV4Error("Original native source modified during projection")

    params=None
    original_guid=None
    target_slab=None
    allowed_step=set()
    added_types={}
    if delta.added_nodes:
        if delta.changed_nodes or delta.removed_nodes or delta.removed_edges:
            raise SlabV4Error("Slab CREATE cannot alter or remove other native elements")
        added_rel=[e for e in delta.added_edges
                   if e.relation=="in_storey" and e.target==name]
        if len(added_rel)!=1 or len(delta.added_edges)!=1:
            raise SlabV4Error("Slab create requires exactly one existing storey reference")
        if node.provenance!="deterministic_new":
            raise SlabV4Error("New Slab identity not deterministic")
        params=_params(dict(node.attributes))
        level=final_nodes[dict(node.attributes)["level"]]
        if level.kind!="Level" or level.provenance!="existing_source":
            raise SlabV4Error("New Slab must use an existing native storey")
        storey=f.by_guid(level.ifc_guid)
        if not storey.is_a("IfcBuildingStorey") or storey.Elevation is None or abs(float(storey.Elevation))>1e-8:
            raise SlabV4Error("Slab create currently restricted to original ground storey")
        body=_body_context(f)
        if node.ifc_guid in {x.GlobalId for x in f.by_type("IfcRoot")}:
            raise SlabV4Error("Slab GlobalId collision")
        op="CREATE_SLAB"
    elif delta.removed_nodes:
        if delta.added_edges or delta.changed_nodes:
            raise SlabV4Error("Slab delete cannot add or change original relations")
        prev=source_nodes[name]
        if prev.provenance!="existing_source":
            raise SlabV4Error("Only original Slab may be deleted")
        native_edges={e for e in original.graph.edges
                      if e.relation=="in_storey" and e.target==name}
        if len(native_edges)!=1 or set(delta.removed_edges)!=native_edges:
            raise SlabV4Error("Slab delete unexpectedly changes original XML relationships")
        original_guid=prev.ifc_guid
        target_slab=_native_slab(f,original_guid)
        _validate_delete_dependencies(f,target_slab)
        op="DELETE_SLAB"
    else:
        if delta.added_edges or delta.removed_edges:
            raise SlabV4Error("Slab geometry edit may not change native relationships")
        prev=source_nodes[name]
        curr=final_nodes[name]
        if prev.provenance!="existing_source" or prev.ifc_guid!=curr.ifc_guid:
            raise SlabV4Error("Original Slab native identity changed")
        a=dict(prev.attributes)
        b=dict(curr.attributes)
        fields=tuple(sorted(k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)))
        params=_params(b)
        original_guid=prev.ifc_guid
        target_slab=_native_slab(f,original_guid)
        previous_bounds=_slab_mesh_bbox(target_slab)
        old_values=tuple(_numeric(a,k) for k in ("x","y","z","width","depth","thickness"))
        if set(fields)<={"x","y","z"} and fields:
            op="MOVE_SLAB"
            relative,point=_relative_point(f,target_slab)
            delta_world=tuple(params[i]-old_values[i] for i in range(3))
            local_delta=_translate_local(f,target_slab.ObjectPlacement.PlacementRelTo,delta_world)
            point_owner=relative
        elif set(fields)<={"width","depth"} and fields:
            op="RESHAPE_SLAB_RECTANGLE"
            solid=_unique_body(f,target_slab)
            profile=solid.SweptArea
            # Current shape must have a centered, axis-aligned swept profile.
            if profile.Position is not None:
                ref=profile.Position.RefDirection
                if ref is not None and not np.allclose(ref.DirectionRatios,(1.,0.),atol=1e-8):
                    raise SlabV4Error("Rotated native slab rectangle profile unsupported")
            R=np.asarray(ifcopenshell.util.placement.get_local_placement(target_slab.ObjectPlacement))[:3,:3]
            S=np.asarray(ifcopenshell.util.placement.get_axis2placement(solid.Position))[:3,:3]
            direction=R@S
            if not (
                (abs(direction[0,0])>.999999 and abs(direction[1,1])>.999999)
                or (abs(direction[1,0])>.999999 and abs(direction[0,1])>.999999)
            ):
                raise SlabV4Error("Native Slab not a horizontal axis-aligned rectangle")
            dimension_mapping=("xy" if abs(direction[0,0])>.999999 else "yx")
            displacement=np.array(((params[3]-old_values[3])/2,
                                   (params[4]-old_values[4])/2,0.0))
            local_delta=R.T@displacement
            point_owner=solid.Position
            point=solid.Position.Location
            owners=list(f.get_inverse(point))
            if len(owners)!=1 or owners[0].id()!=point_owner.id():
                raise SlabV4Error("Slab native rectangle center is shared")
        elif fields==("thickness",):
            op="UPDATE_SLAB_THICKNESS"
            if any(rel.is_a("IfcRelAssociatesMaterial") for rel in f.get_inverse(target_slab)):
                raise SlabV4Error("Cannot change Slab thickness with linked shared material layers")
            solid=_unique_body(f,target_slab)
            R=np.asarray(ifcopenshell.util.placement.get_local_placement(target_slab.ObjectPlacement))[:3,:3]
            S=np.asarray(ifcopenshell.util.placement.get_axis2placement(solid.Position))[:3,:3]
            e=np.asarray(solid.ExtrudedDirection.DirectionRatios,dtype=float)
            direction=R@S@e
            if not np.allclose(np.abs(direction),(0,0,1),atol=1e-8):
                raise SlabV4Error("Slab thickness extrusion axis is not vertical")
            delta_z=(params[5]-old_values[5]) if direction[2]<0 else 0.0
            point_owner=solid.Position
            point=point_owner.Location
            local_delta=R.T@np.array((0.,0.,delta_z))
        else:
            raise SlabV4Error("v0.4 only moves Slab xyz, reshapes rectangle width/depth, or edits unlayered thickness")
        if op=="MOVE_SLAB" and any(
            not math.isfinite(v) or abs(v)>10000 for v in delta_world):
            raise SlabV4Error("Invalid Slab translation")
        if op in ("RESHAPE_SLAB_RECTANGLE","UPDATE_SLAB_THICKNESS"):
            if not np.all(np.isfinite(local_delta)):
                raise SlabV4Error("Native rectangle frame invalid")
        if set(fields)&{"level","ifcGuid"}:
            raise SlabV4Error("Slab native storey and identity cannot be changed")

    def writer(output):
        nonlocal allowed_step,added_types
        if op=="CREATE_SLAB":
            slab=ifcopenshell.api.root.create_entity(
                f,ifc_class="IfcSlab",name="Research declarative Slab v0.4")
            slab.GlobalId=node.ifc_guid
            slab.PredefinedType="FLOOR"
            x,y,z,width,depth,thickness=params
            profile=f.createIfcRectangleProfileDef("AREA",None,None,width,depth)
            rep=ifcopenshell.api.geometry.add_profile_representation(
                f,context=body,profile=profile,depth=thickness)
            ifcopenshell.api.geometry.assign_representation(f,product=slab,representation=rep)
            matrix=np.eye(4,dtype="float64")
            matrix[:3,3]=(x+width/2,y+depth/2,z)
            ifcopenshell.api.geometry.edit_object_placement(f,product=slab,matrix=matrix)
            ifcopenshell.api.spatial.assign_container(f,products=[slab],relating_structure=storey)
        elif op=="DELETE_SLAB":
            _validate_delete_dependencies(f,target_slab)
            ifcopenshell.api.root.remove_product(f,product=target_slab)
        elif op=="MOVE_SLAB":
            changed,added=_edit_point(f,point_owner,point,local_delta)
            allowed_step.update(changed);added_types.update(added)
        elif op=="RESHAPE_SLAB_RECTANGLE":
            if dimension_mapping=="xy":
                solid.SweptArea.XDim=params[3]
                solid.SweptArea.YDim=params[4]
            else:
                solid.SweptArea.XDim=params[4]
                solid.SweptArea.YDim=params[3]
            allowed_step.add(solid.SweptArea.id())
            changed,added=_edit_point(f,point_owner,point,local_delta)
            allowed_step.update(changed);added_types.update(added)
        elif op=="UPDATE_SLAB_THICKNESS":
            solid.Depth=params[5]
            allowed_step.add(solid.id())
            if any(abs(x)>EPS for x in local_delta):
                changed,added=_edit_point(f,point_owner,point,local_delta)
                allowed_step.update(changed);added_types.update(added)
        else:
            raise SlabV4Error("Unrecognized prospective Slab edit")
        f.write(str(output))

    def verify(path):
        if snapshot_source(source).source_sha256!=sourcehash:
            raise SlabV4Error("Source IFC changed before committing candidate")
        if op=="DELETE_SLAB":
            _verify_native_delete(source,path,original_guid)
        elif op=="CREATE_SLAB":
            candidate=ifcopenshell.open(str(path))
            _verify_mesh(candidate,node.ifc_guid,params)
            slab=_native_slab(candidate,node.ifc_guid)
            container=ifcopenshell.util.element.get_container(slab)
            if container is None or container.GlobalId!=level.ifc_guid:
                raise SlabV4Error("Created native Slab missing intended storey containment")
            _native_add_preservation(source,path,node.ifc_guid)
        else:
            candidate=ifcopenshell.open(str(path))
            _verify_mesh(candidate,original_guid,params)
            original_slab=ifcopenshell.open(str(source)).by_guid(original_guid)
            current=_native_slab(candidate,original_guid)
            c0=ifcopenshell.util.element.get_container(original_slab)
            c1=ifcopenshell.util.element.get_container(current)
            if (c0 is None or c1 is None or c0.GlobalId!=c1.GlobalId):
                raise SlabV4Error("Slab update changed native storey containment")
            _expected_step_preservation(source,path,
                                        changed_ids=allowed_step,added_types=added_types)

    stage_and_commit(destination,writer,verify)
    if snapshot_source(source).source_sha256!=sourcehash:
        raise SlabV4Error("Original IFC source changed after transaction")
    result=snapshot_source(destination)
    if op=="DELETE_SLAB":
        preserved=_verify_native_delete(source,destination,original_guid)
    elif op=="CREATE_SLAB":
        preserved=_native_add_preservation(source,destination,node.ifc_guid)
    else:
        preserved=_expected_step_preservation(
            source,destination,changed_ids=allowed_step,added_types=added_types)
    line=(before if op=="DELETE_SLAB" else after).managed_by_id()[name].span.line
    change=Mutation(
        op,name,node.ifc_guid,line,
        ("entity",) if op=="DELETE_SLAB" else
        ("geometry","level") if op=="CREATE_SLAB" else
        ("x","y","z") if op=="MOVE_SLAB" else
        ("width","depth") if op=="RESHAPE_SLAB_RECTANGLE" else ("thickness",),
        "experimental v0.4 native Slab; real mesh and original STEP preservation",
    )
    return SlabV4CompileReport(
        sourcehash,result.source_sha256,
        projection.source.graph_fingerprint,result.graph_fingerprint,
        (change,),preserved,(),destination,True)
