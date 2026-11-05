# Independent Experimental Architecture (proposal)

## Central invariant
**LLM modifies a declarative source file directly.** No `create_wall()`, authoring SDK, BIM CommandBus, Python/IfcOpenShell mutator or geometry operator is available to the **direct-markup LLM**. A trusted runtime outside the model turns source into a valid IFC result.

```text
immutable input.ifc + natural-language task
            |
      +-----+--------------------+
      |                          |
 DIRECT-MARKUP (D)         IMPERATIVE (I)
 LLM reads/building.xml    LLM writes code.py
 LLM edits XML             LLM uses IfcOpenShell APIs
      |                          |
 parse+validate XML             sandbox Python
 semantic bind / diff            IFC edits
      |                          |
    shared IfcOpenShell backend, identical kernel
      +-------------+------------+
                    |
             predicted.ifc
                    |
   isolated blind evaluator (ground truth hidden)
```

## Important scientific compromise
For phase one, the XML representation is an *experiment-only IFC-preserving authoring overlay*, **not an independently complete native-BIM serialization**. The unchanged input IFC is an immutable source asset, and XML specifies editable intent and references to IFC GlobalIds. The runtime clones the source and applies the exact delta, preserving unmodified IFC entities/relationships. This reduces the cost of a replacement IFC kernel while testing **the authoring representation**.

A self-contained `building.xml` (plus required binary assets) as an authoritative full BIM document is an optional later arm. Do not silently treat overlays as a complete BIXML implementation.

## Proposed XML dialect (illustrative only)
```xml
<BuildingOverlay sourceModelSha256="...">
  <Edit targetGuid="0123456789012345678901" expectedIfcType="IfcWall">
    <Set path="Pset_WallCommon.FireRating" value="REI60" />
  </Edit>
  <Create entityId="new-wall-1" ifcClass="IfcWall"
          storeyRef="known-IFC-GlobalId" start="0,0,0"
          end="6,0,0" thickness="0.2m" height="3m" />
</BuildingOverlay>
```

**Not a formal schema.** Canonical semantics for GUID assignment, property path type, unit system, coordinate frame, object identity, host/void/fill relationships, space boundary and deterministic ordering must be specified by dedicated issues. The example is *not proof* that these attributes are supported.

## Authoritative states
- Benchmark `input.ifc`: immutable, read-only and pinned by SHA-256, not modified in place.
- Direct arm `building.xml`: LLM-editable *delta source of truth* for one trial, with provenance to exact input hash. No hidden stateful IFC edits may be triggered by LLM except compiling committed XML.
- Runtime `SemanticGraph`: **derived** from source IFC + XML delta; may be cached but cannot overrule source. Compile errors must not partially mutate the IFC.
- `predicted.ifc`: generated output, not an editable source fed back to LLM without an explicitly budgeted feedback condition.
- `ground_truth.ifc`: hidden evaluator input, never mounted in authoring sandbox.

## Compiler requirements
1. Safe XML parser: disabled DTD/XXE/network schema fetch; byte/document/element nesting/attribute limits.
2. Deterministic normalized XML AST; stable identity/provenance; explicit units, transforms, coordinate frames and IFC schema version.
3. Semantic validator for existing references, no duplicate IDs, valid relation endpoints, type/host constraints.
4. Two-stage evaluation: **dry-run preflight** (assertions & dependency planning) then transactional apply to a disposable cloned IFC. Fail closed with structured diagnostics and no partial output.
5. Source maps: XML line/column/XPath -> affected IFC GlobalId(s) and IFC relationship changes for debugger and explainability.
6. Reversible diff: unchanged GlobalIds and unrelated Psets/relationships preserved. Record any allowed exceptions.
7. No `eval` / arbitrary scripts inside XML; no external fetch at compile time. Expressions, if later introduced, use restricted formal semantics.
8. Geometry correctness and topology must be verified on actual output IFC, never inferred from a parser pass.

## Fair control and execution
- Each task has an isolated workspace with a read-only input copy, condition-specific allowed tools, capped time/attempts/tokens and no reference target path.
- The imperative arm writes `code.py` and may call only the approved IfcOpenShell API surface; its stdout/stderr is captured and code cannot access grader/secrets/network.
- Both arms emit normalized `result.ifc`; the evaluator is a separate process with hidden GT and frozen scoring parameters.
- One run = one independent input clone. Never carry state between benchmark tasks or repeat seeds.

## Short-term vertical slice
- One synthetic IFC with a storey, two walls, an opening and a window, plus a slab or column.
- XML editing should change one property, one geometric parameter and one relationship, while preserving unrelated entities.
- A negative fixture must fail on missing host, invalid units, duplicate IDs or invalid XML without changing an IFC output.
- Deterministic XML authoring + deterministic Python oracle produce equivalent semantic IFC results within frozen tolerances.
- Only after this passes should an LLM be introduced.
