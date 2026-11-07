"""Immutable semantic graph of v0.1 XML-visible objects and IFC provenance.

This is intentionally NOT an IFC writer: the graph is derived from parsed XML,
and must be compared with real IFC relationship evidence before any edit commit.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json

class BindingError(ValueError):
    pass

@dataclass(frozen=True)
class GraphNode:
    id: str
    kind: str
    ifc_guid: str
    provenance: str  # existing_source or deterministic_new
    attributes: tuple[tuple[str,str], ...]

    def canonical(self) -> tuple:
        return self.id,self.kind,self.ifc_guid,self.provenance,self.attributes

@dataclass(frozen=True,order=True)
class GraphEdge:
    relation: str
    source: str
    target: str
    ownership: str  # derived or declared
    def canonical(self) -> tuple:
        return self.relation,self.source,self.target,self.ownership

@dataclass(frozen=True)
class SemanticGraph:
    source_model_sha256: str
    nodes: tuple[GraphNode,...]
    edges: tuple[GraphEdge,...]
    fingerprint: str
    dependency_graph: tuple[tuple[str,str],...]

    def by_id(self) -> dict[str,GraphNode]:
        return {n.id:n for n in self.nodes}

    def affected_by(self, changed_ids: set[str]) -> tuple[str,...]:
        """Conservative deterministic transitive invalidation of host dependents."""
        known=set(self.by_id())
        if not changed_ids <= known:
            raise BindingError("Unknown changed object ID")
        downstream={}
        for src,dst in self.dependency_graph:
            downstream.setdefault(src,set()).add(dst)
        visited=set(changed_ids)
        stack=list(changed_ids)
        while stack:
            for other in downstream.get(stack.pop(),()):
                if other not in visited:
                    visited.add(other)
                    stack.append(other)
        return tuple(sorted(visited))

@dataclass(frozen=True)
class GraphDelta:
    added_nodes: tuple[str,...]
    removed_nodes: tuple[str,...]
    changed_nodes: tuple[str,...]
    added_edges: tuple[GraphEdge,...]
    removed_edges: tuple[GraphEdge,...]
    invalidates: tuple[str,...]
    before_fingerprint: str
    after_fingerprint: str

    @property
    def is_noop(self)->bool:
        return not any((self.added_nodes,self.removed_nodes,self.changed_nodes,
                        self.added_edges,self.removed_edges))

    def as_dict(self)->dict:
        return {
            "added_nodes":list(self.added_nodes),
            "removed_nodes":list(self.removed_nodes),
            "changed_nodes":list(self.changed_nodes),
            "added_edges":[e.canonical() for e in self.added_edges],
            "removed_edges":[e.canonical() for e in self.removed_edges],
            "invalidates":list(self.invalidates),
            "before_fingerprint":self.before_fingerprint,
            "after_fingerprint":self.after_fingerprint,
            "is_noop":self.is_noop,
            "ifc_written":False,
        }


def canonical_value(val: str|Decimal) -> str:
    if isinstance(val,Decimal):
        if not val.is_finite():
            raise BindingError("Nonfinite BIM geometry attribute")
        return "0" if val==0 else format(val.normalize(),"f")
    return str(val)


def make_graph(source_sha: str, nodes: list[GraphNode], edges: list[GraphEdge],
               dependency_graph: list[tuple[str,str]]) -> SemanticGraph:
    ids=[x.id for x in nodes]
    if len(ids)!=len(set(ids)):
        raise BindingError("Duplicate local object ID")
    guids=[x.ifc_guid for x in nodes]
    if len(guids)!=len(set(guids)):
        raise BindingError("Duplicate IFC GlobalId")
    known=set(ids)
    if any(e.source not in known or e.target not in known for e in edges):
        raise BindingError("Dangling typed relationship endpoint")
    validate_containment_acyclic(nodes,edges)
    data={
        "source_model_sha256":source_sha,
        "nodes":[n.canonical() for n in sorted(nodes,key=lambda n:n.id)],
        "edges":[e.canonical() for e in sorted(set(edges))],
    }
    digest=hashlib.sha256(json.dumps(data,separators=(",",":"),sort_keys=True).encode()).hexdigest()
    return SemanticGraph(source_sha,
                         tuple(sorted(nodes,key=lambda n:n.id)),
                         tuple(sorted(set(edges))),
                         digest,
                         tuple(sorted(set(dependency_graph))))


CONTAINMENT_TYPES={"in_storey","aggregated_in_storey","host_void","opening_fill"}


def validate_containment_acyclic(nodes: list[GraphNode],edges: list[GraphEdge]) -> None:
    """No cycle in ownership/host graph. Wall-to-wall connections may cycle."""
    known={n.id for n in nodes}
    parents={}
    for edge in edges:
        if edge.relation not in CONTAINMENT_TYPES:
            continue
        if edge.source==edge.target:
            raise BindingError("Self containment/host relationship forbidden")
        if edge.source not in known or edge.target not in known:
            raise BindingError("Dangling containment endpoint")
        if edge.target in parents:
            raise BindingError("Object has multiple conflicting ownership parents")
        parents[edge.target]=edge.source
    # Ownership direction: parent->child in all relationship edges
    for node in known:
        cur=node
        seen=set()
        while cur in parents:
            if cur in seen:
                raise BindingError("Cyclic containment or host hierarchy")
            seen.add(cur)
            cur=parents[cur]


def graph_diff(previous: SemanticGraph,edited: SemanticGraph) -> GraphDelta:
    if previous.source_model_sha256!=edited.source_model_sha256:
        raise BindingError("Source IFC changed between graph snapshots")
    a=previous.by_id();b=edited.by_id()
    common=set(a)&set(b)
    for name in common:
        if a[name].kind!=b[name].kind:
            raise BindingError("Existing class changed at stable object ID")
        if a[name].ifc_guid!=b[name].ifc_guid:
            raise BindingError("Existing IFC GlobalId changed at stable object ID")
    new=set(b)-set(a)
    gone=set(a)-set(b)
    modified={name for name in common if a[name].attributes!=b[name].attributes}
    e1=set(previous.edges);e2=set(edited.edges)
    added=tuple(sorted(e2-e1));removed=tuple(sorted(e1-e2))
    invalidates=set(modified)|new|gone
    for e in (*added,*removed):
        invalidates.update((e.source,e.target))
    # Inspect dependencies from both snapshots so delete/disconnect cases are
    # not silently omitted from the invalidation set.
    for g in (previous,edited):
        for changed in invalidates & set(g.by_id()):
            invalidates.update(g.affected_by({changed}))
    return GraphDelta(
        added_nodes=tuple(sorted(new)),removed_nodes=tuple(sorted(gone)),
        changed_nodes=tuple(sorted(modified)),added_edges=added,removed_edges=removed,
        invalidates=tuple(sorted(invalidates)),
        before_fingerprint=previous.fingerprint,after_fingerprint=edited.fingerprint,
    )
