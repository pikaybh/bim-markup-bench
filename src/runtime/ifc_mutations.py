"""Strict IFC4X3 wall-only transactional mutation building blocks.

This is a first real vertical slice: one safe wall creation, standalone wall
deletion and swept-solid height change. Unsupported operations FAIL CLOSED.
The LLM cannot call these methods directly in the declarative experiment.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
import math
from typing import Any

import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.geom
import ifcopenshell.util.element
import numpy as np

from src.runtime.ast import BuildingDocument
from src.runtime.binder import BindingEvidence
from src.runtime.ifc_projection import _body_extrusion
from src.runtime.semantic_graph import BindingError, graph_diff

class UnsupportedIFCMutation(ValueError):
    pass

def by_guid_or_none(model:ifcopenshell.file,guid:str):
    """IfcOpenShell raises RuntimeError when a GUID does not exist."""
    try:
        return model.by_guid(guid)
    except RuntimeError:
        return None


@dataclass(frozen=True)
class Mutation:
    operation: str
    xml_id: str
    ifc_guid: str
    source_line: int
    changed_fields: tuple[str,...]
    reason: str

    def as_dict(self) -> dict:
        return {
            "operation":self.operation,"xml_id":self.xml_id,
            "ifc_guid":self.ifc_guid,"source_line":self.source_line,
            "changed_fields":list(self.changed_fields),"reason":self.reason,
        }


def plan_wall_mutations(
        before_doc: BuildingDocument, after_doc: BuildingDocument,
        before: BindingEvidence, after: BindingEvidence) -> tuple[Mutation,...]:
    """Validate all edits before any IFC object is mutated."""
    graph_delta=graph_diff(before.graph,after.graph)
    if graph_delta.is_noop:
        return ()
    old_by_id=before.graph.by_id()
    new_by_id=after.graph.by_id()
    xml_edited=after_doc.managed_by_id()
    old_xml=before_doc.managed_by_id()
    changes=[]
    for name in graph_delta.changed_nodes:
        old=old_by_id[name];new=new_by_id[name]
        old_attrs=dict(old.attributes);new_attrs=dict(new.attributes)
        fields=tuple(sorted(k for k in old_attrs.keys()|new_attrs.keys()
                     if old_attrs.get(k)!=new_attrs.get(k)))
        if old.kind!="Wall" or new.kind!="Wall" or fields not in (("height",),("thickness",)):
            raise UnsupportedIFCMutation(
                "Only in-place Wall.height and independent Wall.thickness updates are supported")
        if old.provenance!="existing_source" or new.provenance!="existing_source":
            raise UnsupportedIFCMutation("Updating a new uncommitted wall requires a separate source")
        if fields==("height",):
            changes.append(Mutation("UPDATE_WALL_HEIGHT",name,old.ifc_guid,
                          xml_edited[name].span.line,fields,"single swept-solid wall height"))
        else:
            changes.append(Mutation("UPDATE_WALL_THICKNESS",name,old.ifc_guid,
                          xml_edited[name].span.line,fields,"unhosted rectangular wall profile thickness"))
    for name in graph_delta.added_nodes:
        node=new_by_id[name]
        if node.kind!="Wall" or node.provenance!="deterministic_new":
            raise UnsupportedIFCMutation("Only creation of a new standalone Wall is supported")
        changes.append(Mutation("CREATE_WALL",name,node.ifc_guid,
                  xml_edited[name].span.line,("geometry","level"),"straight standalone wall"))
    for name in graph_delta.removed_nodes:
        node=old_by_id[name]
        if node.kind!="Wall" or node.provenance!="existing_source":
            raise UnsupportedIFCMutation("Only deletion of an existing standalone Wall is supported")
        changes.append(Mutation("DELETE_WALL",name,node.ifc_guid,
                  old_xml[name].span.line,("entity","level"),"standalone existing wall"))
    allowed_added=set()
    allowed_removed=set()
    for change in changes:
        if change.operation=="CREATE_WALL":
            allowed_added.add(("in_storey",change.xml_id))
        elif change.operation=="DELETE_WALL":
            allowed_removed.add(("in_storey",change.xml_id))
    for edge in graph_delta.added_edges:
        if (edge.relation,edge.target) not in allowed_added:
            raise UnsupportedIFCMutation("Unsupported IFC relationship addition")
    for edge in graph_delta.removed_edges:
        if (edge.relation,edge.target) not in allowed_removed:
            raise UnsupportedIFCMutation("Unsupported IFC relationship deletion")
    return tuple(sorted(changes,key=lambda x:(x.operation,x.xml_id)))


def _unique_wall_representation(f:ifcopenshell.file,wall) -> Any:
    item=_body_extrusion(wall)
    # Reject shared shape representations: an edit must never alter an
    # unrelated family's geometry via a shared IfcExtrudedAreaSolid.
    for rep in f.get_inverse(item):
        if rep.is_a("IfcShapeRepresentation"):
            # Revit-authored walls may also reference the shape from a
            # presentation layer; that is metadata, not shape ownership.
            # Count ONLY actual product-definition shape owners.
            owners=[owner for owner in f.get_inverse(rep)
                    if owner.is_a("IfcProductDefinitionShape")]
            if len(owners)!=1:
                raise UnsupportedIFCMutation("Wall shape representation is shared/ambiguous")
            product_owners=[x for x in f.get_inverse(owners[0]) if x.is_a("IfcProduct")]
            if len(product_owners)!=1 or product_owners[0].GlobalId!=wall.GlobalId:
                raise UnsupportedIFCMutation("Wall ProductDefinitionShape has multiple/mismatched owners")
    return item


def validate_source_mutation_eligibility(f:ifcopenshell.file,
                                         changes:tuple[Mutation,...]) -> None:
    for c in changes:
        if c.operation not in ("UPDATE_WALL_HEIGHT","UPDATE_WALL_THICKNESS","DELETE_WALL"):
            continue
        wall=by_guid_or_none(f,c.ifc_guid)
        if wall is None or not wall.is_a("IfcWall"):
            raise UnsupportedIFCMutation("Source IFC wall GUID/class not found")
        if c.operation=="UPDATE_WALL_HEIGHT":
            item=_unique_wall_representation(f,wall)
            if not isinstance(item.Depth,(int,float)):
                raise UnsupportedIFCMutation("Wall extrusion has unrecognized depth")
            for inv in f.get_inverse(wall):
                if inv.is_a("IfcRelConnectsElements") and inv.ConnectionGeometry is not None:
                    raise UnsupportedIFCMutation("Wall has geometry-dependent connection")
                if inv.is_a("IfcRelSpaceBoundary") and inv.ConnectionGeometry is not None:
                    raise UnsupportedIFCMutation("Wall has geometry-dependent space boundary")
        if c.operation=="UPDATE_WALL_THICKNESS":
            # Late import avoids a circular dependency in geometry_ops.
            from src.runtime.geometry_ops import wall_thickness_eligibility
            wall_thickness_eligibility(f,wall)
        if c.operation=="DELETE_WALL":
            inverses=f.get_inverse(wall)
            if any(not rel.is_a("IfcRelContainedInSpatialStructure") for rel in inverses):
                raise UnsupportedIFCMutation("Cannot delete Wall with host/boundary/constraint/connection/attribute dependencies")


def _geometry_nonempty(f,wall) -> None:
    try:
        s=ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(),wall)
    except Exception as exc:
        raise UnsupportedIFCMutation("IfcOpenShell cannot create updated wall mesh") from exc
    if len(s.geometry.verts)<9 or len(s.geometry.faces)<3:
        raise UnsupportedIFCMutation("Updated wall has empty/invalid triangulation")


def mutate_wall_height(f,wall,requested_height:Decimal):
    depth=float(requested_height)
    if not (0<depth<10000) or not math.isfinite(depth):
        raise UnsupportedIFCMutation("Invalid wall height")
    item=_unique_wall_representation(f,wall)
    item.Depth=depth
    _geometry_nonempty(f,wall)


def create_standalone_wall(f,params:dict,global_id:str,storey_guid:str):
    try:
        storey=f.by_guid(storey_guid)
    except RuntimeError as exc:
        raise UnsupportedIFCMutation("IFC BuildingStorey missing for create") from exc
    if storey is None or not storey.is_a("IfcBuildingStorey"):
        raise UnsupportedIFCMutation("Invalid target storey for new Wall")
    coords=[float(params[k]) for k in ("x1","y1","z1","x2","y2","z2")]
    x1,y1,z1,x2,y2,z2=coords
    if abs(z1-z2)>1e-6:
        raise UnsupportedIFCMutation("Tilted Wall creation unsupported")
    dx=x2-x1;dy=y2-y1
    length=math.hypot(dx,dy)
    if length<=0.01:
        raise UnsupportedIFCMutation("Degenerate new wall length")
    try:
        contexts=[x for x in f.by_type("IfcGeometricRepresentationSubContext")
                  if x.ContextIdentifier=="Body" and x.TargetView=="MODEL_VIEW"]
        if len(contexts)!=1:
            raise UnsupportedIFCMutation("No unique native Body subcontext in IFC input")
        body=contexts[0]
        wall=ifcopenshell.api.root.create_entity(f,ifc_class="IfcWall",name="Created by declarative XML")
        wall.GlobalId=global_id
        rep=ifcopenshell.api.geometry.add_wall_representation(f,context=body,
            length=length,height=float(params["height"]),thickness=float(params["thickness"]))
        ifcopenshell.api.geometry.assign_representation(f,product=wall,representation=rep)
        transform=np.eye(4,dtype="float64")
        transform[:3,0]=[dx/length,dy/length,0.]
        transform[:3,1]=[-dy/length,dx/length,0.]
        transform[:3,3]=[x1,y1,z1]
        ifcopenshell.api.geometry.edit_object_placement(f,product=wall,matrix=transform)
        ifcopenshell.api.spatial.assign_container(f,products=[wall],relating_structure=storey)
        _geometry_nonempty(f,wall)
    except UnsupportedIFCMutation:
        raise
    except Exception as exc:
        raise UnsupportedIFCMutation("IfcOpenShell new standalone Wall geometry failed") from exc


def delete_standalone_wall(f,global_id:str):
    wall=by_guid_or_none(f,global_id)
    if wall is None or not wall.is_a("IfcWall"):
        raise UnsupportedIFCMutation("Cannot delete unknown Wall")
    if any(not rel.is_a("IfcRelContainedInSpatialStructure") for rel in f.get_inverse(wall)):
        raise UnsupportedIFCMutation("Wall has non-container dependencies; deleting it is unsafe")
    ifcopenshell.api.root.remove_product(f,product=wall)
    if by_guid_or_none(f,global_id) is not None:
        raise UnsupportedIFCMutation("IfcOpenShell failed to remove Wall")
