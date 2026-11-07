# G1 #12 — Typed IFC/Markup relationship contracts and dependency graph

**Status: first typed binder implemented; actual IFC transaction engine NOT implemented.** This is a read-only trusted backend. Existing Revit/Xim and production files are never accessed.

## ID and provenance contract

- XML `id`: stable human-readable, document-local name, not an IFC GlobalId.
- Existing IFC `ifcGuid`: must exactly match immutable original IFC and the original projection's frozen GUID↔XML local-ID map. A malicious edited XML cannot redirect an existing ID to another native object.
- New element with no IFC identity in the previous projection: assigned a deterministic 22-character IFC GlobalId using UUIDv5 with a frozen namespace, source IFC SHA-256, IFC class and XML local ID. The allocation checks against all original model IDs and previously allocated IDs.
- Newly declared objects cannot self-assign an arbitrary IFC GlobalId. Existing source IDs must retain class and GlobalId on edit.
- GUIDs for new elements are a **planning-only stable identity**; they are not inserted in an IFC model until G1 #13 compiler implementation.

The GraphNode captures original source vs deterministic-new provenance; GraphEdge captures a strict relationship type, direction and whether the source XML declared or derived it.

## Supported typed relations

| Relation | Source → target | Origin / checks |
| --- | --- | --- |
| in_storey | Level → Wall/Slab/Column | Derived from Level attr; IFC evidence from IfcRelContainedInSpatialStructure |
| aggregated_in_storey | Level → Space | Derived from Space's Level; IFC evidence from IfcRelAggregates |
| host_void | Wall → Opening | Derived from Opening.host; IFC evidence from IfcRelVoidsElement |
| opening_fill | Opening → Window/Door | Derived from filling.opening; IFC evidence from IfcRelFillsElement |
| space_boundary | Space → Wall | Declared SpaceBoundary; IFC evidence from IfcRelSpaceBoundary |
| connects | Wall → Wall | Declared Connects; IFC evidence from IfcRelConnectsElements |

In native evidence mode the binder opens the **immutable source IFC** itself, extracts the actual relation endpoints, and requires every declared graph relation for an existing element to match a real IFC relationship. Missing or wrong-class relations fail closed; GT or external evaluator files are NEVER read.

Type-level invalidation travels Wall → Opening → filling and Wall → adjacent Space or connected Wall. This is a conservative dependency invalidation set, **not** a compiled geometry recalculation or proof that a constraint has been satisfied.

## Semantic/physical invariants

- No duplicate local IDs or IFC GlobalIds; stable kind and identity enforced.
- Strict endpoint class: a void must be hosted by a Wall, a filling must target an Opening, a space boundary must connect Space↔Wall.
- An opening must fit within its host wall's length and height with 1-micron tolerance. Filling cannot exceed its opening.
- Wall axis must be horizontal and nondegenerate in v0.1; all geometric dimensions positive; no out-of-bound openings.
- Space boundary and wall connections cannot cross storeys; wall self-connection invalid.
- Ownership and host relation cycles are rejected, but Wall↔Wall connectivity cycles are legal.
- Two parses of unchanged/synonymously formatted XML produce identical stable IDs, typed nodes, edges and graph SHA-256.
- GraphDiff reports added/deleted/changed nodes and edges plus affected dependencies. An unrelated element's node identity and attributes remain unchanged.
- A new XML document with a different source IFC SHA or a tampered mapped source GUID cannot pass binding.

## Explicitly unsupported (NOT quietly implemented)

- IfcRelDefinesByType / material assignment: preserved in immutable IFC substrate and included in the IFC snapshot fingerprint but **not yet editable as typed XML edges**.
- Arbitrary hierarchical IFC containment, cross-storey hosted objects, complex furniture/MEP/railings/roofs/families, implicit material/void regeneration, structural analysis.
- IFC4/IFC2X3 cross-version models and general IFC4X3 topology, non-rectilinear walls/profiles.
- Most official BIM-Edit corpus objects; only a single small real IFC file has been inspected. IfcSpace without explicit source representation cannot be invented.
- A secure filesystem/process sandbox and blind independent scoring.
- Physically applying the graph delta to an IFC file with atomic rollback or ifc geometry inference. This belongs to #13–#16.
- Source-first hot reload GUI and production BIXML schemas.

## Reproduce

    uv sync --frozen --python 3.12
    .venv/bin/python -m unittest tests.test_semantic_graph -v
    .venv/bin/python -m unittest discover -s tests -v

Use `bind_document(parse_xml(xml_bytes))` for a synthetic document (new objects); use `bind_document(parse_xml(projection.xml), projection=projection)` for a **source-backed projection** that validates original IFC host relations. Always check report().all_ifc_relation_contracts_satisfied before using the graph as input to a future compiler.

All binder methods are offline and non-mutating. Creating a GraphDelta cannot be interpreted as having successfully edited BIM or passed any benchmark.
