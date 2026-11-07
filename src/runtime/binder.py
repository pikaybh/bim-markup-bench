"""Typed BIM state binder and stable IFC identity mapping (no IFC mutation)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import hashlib
import uuid

import ifcopenshell

from src.runtime.ast import BuildingDocument, ElementNode
from src.runtime.semantic_graph import (
    BindingError, GraphEdge, GraphNode, SemanticGraph, canonical_value, make_graph,
)
from src.runtime.ifc_snapshot import IFCSnapshot, _sha256
from src.runtime.ifc_projection import Projection

NAMESPACE=uuid.UUID("9218e3de-9b55-4960-b9b0-e4dddf796ebd")
XML_TO_IFC={
    "Level":"IfcBuildingStorey","Wall":"IfcWall","Slab":"IfcSlab",
    "Column":"IfcColumn","Space":"IfcSpace","Opening":"IfcOpeningElement",
    "Window":"IfcWindow","Door":"IfcDoor",
}
EDITABLE_KINDS={"Wall","Slab","Column","Space","Opening","Window","Door"}

@dataclass(frozen=True)
class BindingEvidence:
    """No permission to compile IFC. Existing source edges must be checked against IFC."""
    graph: SemanticGraph
    existing_globalids: tuple[str,...]
    new_generated_globalids: tuple[str,...]
    source_relation_edges_checked: tuple[tuple[str,str,str], ...]
    missing_source_relation_edges: tuple[tuple[str,str,str], ...]

    def report(self) -> dict:
        return {
            "graph_fingerprint":self.graph.fingerprint,
            "object_count":len(self.graph.nodes),
            "edge_count":len(self.graph.edges),
            "existing_source_globalids":len(self.existing_globalids),
            "deterministically_allocated_new_globalids":len(self.new_generated_globalids),
            "source_relation_checks":len(self.source_relation_edges_checked),
            "missing_source_relation_edges":len(self.missing_source_relation_edges),
            "ifc_mutated":False,
            "all_ifc_relation_contracts_satisfied":not self.missing_source_relation_edges,
        }


def allocate_new_ifc_guid(source_sha256: str,kind: str,local_id: str,
                          existing: set[str]) -> str:
    if kind not in XML_TO_IFC or not local_id:
        raise BindingError("Invalid type or local ID for new IFC GlobalId")
    name=f"bim-markup-v0.1:{source_sha256}:{XML_TO_IFC[kind]}:{local_id}"
    new=ifcopenshell.guid.compress(uuid.uuid5(NAMESPACE,name).hex)
    if new in existing:
        raise BindingError("Stable IFC GlobalId allocation collided with an existing element")
    return new


def _as_decimal(attr: dict, key: str) -> Decimal:
    val=attr.get(key)
    if not isinstance(val,Decimal) or not val.is_finite():
        raise BindingError("Missing or invalid numeric attribute: "+key)
    return val


def _check_endpoint(elements: dict[str, ElementNode], target: str,kind: str) -> ElementNode:
    node=elements.get(target)
    if node is None or node.kind!=kind:
        raise BindingError(f"Wrong or missing {kind} relationship endpoint")
    return node


def _geometry_preconditions(elements: dict[str,ElementNode], source_sha: str) -> None:
    for element in elements.values():
        attrs=element.attrs()
        if element.kind=="Wall":
            xyz=[_as_decimal(attrs,k) for k in ("x1","y1","z1","x2","y2","z2")]
            if xyz[2]!=xyz[5]:
                raise BindingError("Sloping walls are unsupported by initial geometry contract")
            dx=xyz[3]-xyz[0];dy=xyz[4]-xyz[1]
            length=(dx*dx+dy*dy).sqrt()
            if length <= Decimal("0.01"):
                raise BindingError("Wall has degenerate axis")
            for dim in ("height","thickness"):
                if _as_decimal(attrs,dim)<=0:
                    raise BindingError("Wall has nonpositive dimension")
        elif element.kind=="Opening":
            host=_check_endpoint(elements,attrs.get("host"),"Wall")
            host_attrs=host.attrs()
            length=((_as_decimal(host_attrs,"x2")-_as_decimal(host_attrs,"x1"))**2+
                    (_as_decimal(host_attrs,"y2")-_as_decimal(host_attrs,"y1"))**2).sqrt()
            offset=_as_decimal(attrs,"offset")
            width=_as_decimal(attrs,"width")
            sill=_as_decimal(attrs,"sill")
            height=_as_decimal(attrs,"height")
            if offset<0 or offset+width>length+Decimal("0.000001"):
                raise BindingError("Opening is outside the hosted wall's horizontal extent")
            if sill<0 or sill+height>_as_decimal(host_attrs,"height")+Decimal("0.000001"):
                raise BindingError("Opening exceeds the hosted wall's vertical extent")
        elif element.kind in ("Window","Door"):
            opening=_check_endpoint(elements,attrs.get("opening"),"Opening")
            opening_attrs=opening.attrs()
            if _as_decimal(attrs,"width") > _as_decimal(opening_attrs,"width")+Decimal("0.000001"):
                raise BindingError("Filling exceeds opening width")
            if _as_decimal(attrs,"height") > _as_decimal(opening_attrs,"height")+Decimal("0.000001"):
                raise BindingError("Filling exceeds opening height")
        elif element.kind in ("Column","Space","Slab"):
            keys=("width","depth","thickness" if element.kind=="Slab" else "height")
            if any(_as_decimal(attrs,k)<=0 for k in keys):
                raise BindingError("Nonpositive BIM box dimension")


def _source_relation_evidence(graph: SemanticGraph, model_path) -> tuple[tuple,tuple]:
    """Compare existing projected graph relation pairs against actual IFC relationships."""
    f=ifcopenshell.open(str(model_path))
    ids={n.id:n.ifc_guid for n in graph.nodes if n.provenance=="existing_source"}
    rels=set()
    for relation in f.by_type("IfcRelVoidsElement"):
        rels.add(("host_void",relation.RelatingBuildingElement.GlobalId,
                  relation.RelatedOpeningElement.GlobalId))
    for relation in f.by_type("IfcRelFillsElement"):
        rels.add(("opening_fill",relation.RelatingOpeningElement.GlobalId,
                  relation.RelatedBuildingElement.GlobalId))
    for relation in f.by_type("IfcRelSpaceBoundary"):
        if relation.RelatingSpace and relation.RelatedBuildingElement:
            rels.add(("space_boundary",relation.RelatingSpace.GlobalId,
                      relation.RelatedBuildingElement.GlobalId))
    for relation in f.by_type("IfcRelConnectsElements"):
        if relation.RelatingElement and relation.RelatedElement:
            rels.add(("connects",relation.RelatingElement.GlobalId,
                      relation.RelatedElement.GlobalId))
    for relation in f.by_type("IfcRelContainedInSpatialStructure"):
        for product in relation.RelatedElements:
            rels.add(("in_storey",relation.RelatingStructure.GlobalId,product.GlobalId))
    for relation in f.by_type("IfcRelAggregates"):
        for product in relation.RelatedObjects:
            rels.add(("aggregated_in_storey",relation.RelatingObject.GlobalId,product.GlobalId))
    checked=[];missing=[]
    for edge in graph.edges:
        if edge.source not in ids or edge.target not in ids:
            continue
        # Declared graph-level relation classes are checked against their
        # exact corresponding native IFC relation (never inferred from XML).
        key=(edge.relation,ids[edge.source],ids[edge.target])
        if edge.relation in ("in_storey","aggregated_in_storey",
                             "host_void","opening_fill","space_boundary","connects"):
            if key in rels:
                checked.append(key)
            else:
                missing.append(key)
    return tuple(sorted(checked)),tuple(sorted(missing))


def bind_document(document: BuildingDocument, *, source: IFCSnapshot|None=None,
                  projection: Projection|None=None, verify_native_edges: bool=True) -> BindingEvidence:
    if projection is not None:
        if source is None:
            source=projection.source
        elif source.source_sha256!=projection.source.source_sha256:
            raise BindingError("Projected IFC backing asset differs from binder source")
    if source is not None and document.source_model_sha256!=source.source_sha256:
        raise BindingError("Immutable source hash mismatch at binder")
    if source is not None and _sha256(source.source_file)!=source.source_sha256:
        raise BindingError("Immutable IFC bytes changed before semantic binding")
    elements=document.managed_by_id()
    if len(elements)!=len(document.levels)+len(document.elements):
        raise BindingError("Duplicate local object IDs")
    if not document.levels:
        raise BindingError("Building requires at least one storey")
    projected_ids={}
    if projection is not None:
        projected_ids={local:guid for guid,local in projection.projected_global_ids}
    existing_guids=set(dict(source.global_ids)) if source else set()
    assigned_guids=set()
    existing=[]
    generated=[]
    nodes=[]
    for element in (*document.levels,*document.elements):
        if element.kind not in XML_TO_IFC:
            raise BindingError("Unsupported XML element kind")
        if not element.id:
            raise BindingError("Missing stable local ID")
        raw_guid=element.ifc_guid
        if element.id in projected_ids:
            guid=projected_ids[element.id]
            if raw_guid!=guid:
                raise BindingError("Existing IFC identity mismatch with frozen projection")
            cls=dict(source.global_ids).get(guid) if source else None
            if cls is not None and cls!=XML_TO_IFC[element.kind]:
                raise BindingError("Existing IFC class mismatch")
            provenance="existing_source"
            existing.append(guid)
        else:
            if raw_guid is not None:
                raise BindingError("New XML object cannot self-assign an existing or arbitrary IFC GlobalId")
            guid=allocate_new_ifc_guid(document.source_model_sha256,element.kind,element.id,
                                       existing_guids|assigned_guids)
            provenance="deterministic_new"
            generated.append(guid)
        if guid in assigned_guids:
            raise BindingError("Duplicate IFC GlobalId after binding")
        assigned_guids.add(guid)
        attrs=tuple(sorted((str(k),canonical_value(v)) for k,v in element.attrs().items()))
        nodes.append(GraphNode(element.id,element.kind,guid,provenance,attrs))
    _geometry_preconditions(elements,document.source_model_sha256)
    edges=[]
    deps=[]
    levels={x.id for x in document.levels}
    for element in document.elements:
        a=element.attrs()
        if element.kind in ("Wall","Slab","Column","Space"):
            level=a.get("level")
            if level not in levels:
                raise BindingError("Dangling or wrong-class IfcBuildingStorey reference")
            kind="aggregated_in_storey" if element.kind=="Space" else "in_storey"
            edges.append(GraphEdge(kind,str(level),element.id,"derived"))
        elif element.kind=="Opening":
            host=str(a.get("host"))
            _check_endpoint(elements,host,"Wall")
            edges.append(GraphEdge("host_void",host,element.id,"derived"))
            deps.append((host,element.id))
        elif element.kind in ("Window","Door"):
            opening=str(a.get("opening"))
            _check_endpoint(elements,opening,"Opening")
            edges.append(GraphEdge("opening_fill",opening,element.id,"derived"))
            deps.append((opening,element.id))
    for relation in document.relations:
        a=relation.attrs()
        if relation.kind=="SpaceBoundary":
            space=_check_endpoint(elements,str(a.get("space")),"Space")
            wall=_check_endpoint(elements,str(a.get("element")),"Wall")
            if space.attrs()["level"]!=wall.attrs()["level"]:
                raise BindingError("Space boundary crosses storeys")
            edges.append(GraphEdge("space_boundary",space.id,wall.id,"declared"))
            deps.append((wall.id,space.id))
        elif relation.kind=="Connects":
            src=_check_endpoint(elements,str(a.get("from")),"Wall")
            dst=_check_endpoint(elements,str(a.get("to")),"Wall")
            if src.id==dst.id:
                raise BindingError("Wall cannot be connected to itself")
            if src.attrs()["level"]!=dst.attrs()["level"]:
                raise BindingError("Wall connection crosses storeys")
            edges.append(GraphEdge("connects",src.id,dst.id,"declared"))
            deps.extend(((src.id,dst.id),(dst.id,src.id)))
        else:
            raise BindingError("Unsupported declarative relationship class")
    # A repeated declarative relation must not silently collapse to an
    # identical graph/no-op. Duplicate topology is a model semantic error.
    if len(edges)!=len(set(edges)):
        raise BindingError("Duplicate declared or derived IFC relationship")
    graph=make_graph(document.source_model_sha256,nodes,edges,deps)
    checked=();missing=()
    if source is not None and projection is not None and verify_native_edges:
        checked,missing=_source_relation_evidence(graph,source.source_file)
        if _sha256(source.source_file)!=source.source_sha256:
            raise BindingError("Immutable IFC bytes changed during native relation validation")
        if missing:
            raise BindingError("Projected relationship does not exist in immutable original IFC model")
    return BindingEvidence(graph,tuple(sorted(existing)),tuple(sorted(generated)),
                           checked,missing)
