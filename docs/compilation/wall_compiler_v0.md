# G1 Issue #13 — Declarative XML to actual IFC edit (vertical slice)

**Status: real IFC write is now demonstrated, but Issue #13 remains OPEN.** This implements only a deliberately small *trusted* compiler behind the source-editing boundary. It is not a general XML/BIXML engine, six-class CRUD or official BIM-Edit benchmark runner.

## Ground rules

The model sees and edits **building.xml** only. It cannot invoke an IFC authoring SDK, python/eval mutation commands or any proprietary BIM application. The separate trusted compiler may use a pinned IfcOpenShell 0.8.4.post1 backend to convert a checked, typed declarative state delta into an IFC4X3 result.

The original source IFC is opened read-only and SHA-256 pinned. It is never overwritten.

## Implemented operations (fail-closed scope)

| XML before/after | Native IFC effect | Conditions |
| --- | --- | --- |
| Only harmless formatting/decimal representation change | Byte-identical IFC copy | Source hash unchanged, semantic diff NO_OP |
| Existing supported Wall height changes | Change IfcExtrudedAreaSolid.Depth | Pure swept solid, unique geometry ownership, no geometry-carrying space/element connection |
| New unhosted standalone Wall appears | Create IfcWall, Body representation, ObjectPlacement and spatial containment | Existing storey, straight horizontal centerline, positive height/thickness, unique Body context and allocated stable new GUID |
| Existing standalone Wall disappears from XML | Remove IfcWall and its containment/geometry | No hosted opening, space boundary, material/Pset type relation, connection or any non-container inverse relation |
| Mixed supported wall height + independent wall create | Apply both in staged copy | All preconditions must pass before mutation |

Any other change to Wall attributes, or changes to Slab/Space/Column/Window/Door/Opening or relationships, **fail without writing a result**. That is an intentionally honest capability gap, not an implementation omission to be hidden.

### Safety and proof before commit

1. Rebuild exact source projection from immutable IFC; verify SHA, typed original native relationships and stable local ID/GUID map.
2. Safely parse edited XML with XSD; bind typed graph; build semantic delta and whitelist operations/graph edges.
3. Enforce source/projection identity, wall-height/host geometric bounds, no duplicate GUID, existing/created storey and unique shape constraints.
4. Open a private IfcOpenShell clone in memory and apply operations there, never on original file.
5. Write IFC to hidden temporary file, reopen it, verify IFC4X3 syntax, expected Wall GlobalIds, actual swept solid depth, uniqueness and unaffected root entities; for height-only edits, diff **every original STEP entity** and permit changes only to the exact approved IfcExtrudedAreaSolid.
6. Check original IFC SHA again before publication, then exclusively link the already validated staged file as a *new* result file. Existing destination is never overwritten. Failed parse/geometry/validator leaves no output and removes staged temporary data.

The output ledger records operation, XML node ID and source line, unchanged root count, input/result SHA, full STEP graph fingerprints and zero unexpected root modifications. The public report explicitly says general BIM-Edit-324 support is false.

## Reproduce without OpenAI

Run from an isolated Python 3.12 + uv pinned environment:

    uv sync --frozen --python 3.12
    .venv/bin/python -m tools.project_ifc \
      tests/fixtures/synthetic/input.ifc --xml-out data/projections/example.xml
    # Edit ONLY data/projections/example.xml, e.g., change the north wall height from 3 to 3.3.
    .venv/bin/python -m tools.compile_markup \
      --source-ifc tests/fixtures/synthetic/input.ifc \
      --edited-xml data/projections/example.xml \
      --result-ifc data/projections/edited.ifc
    .venv/bin/python -m unittest tests.test_compiler -v

The input IFC is a self-generated fixture under 7 KB, and data/projections is Git-ignored. No API key, external GT IFC or model invocation is required.

## Observed evidence / known limitations

- The self-generated North Wall changed actual extrusion depth from 3.0 to 3.3 m. Comparing IFC entity-by-entity, **only the intended IfcExtrudedAreaSolid STEP entity changed**; all original other entity statements were identical.
- A second wall created by a declarative XML node became an actual meshed IfcWall with containment and assigned GlobalId. Removing its declaration on the next backed input generated a valid IFC with that wall removed and all unrelated hosted voids intact.
- No-op output equals original IFC byte-for-byte, including attributes and material/Pset content.
- Invalid schema, unexpected XML attribute changes, missing host bounds, unsafe deletion, existing output and stage validation failures were rejected.
- The schema exposes only supported source classes, while missing IfcSpace geometry and uneditable relationships remain opaque in the original IFC. This creates a hard capability gate for the full benchmark.
- **Important stable-ID limitation:** after writing a newly created wall, reprojecting the resulting IFC without a retained local-ID mapping may assign a new hash-derived *XML local ID*, even though IFC GlobalId remains stable. This must be corrected in Issue #12/#13 before multi-turn LLM feedback and an honest native DOM continuity claim.
- The compiler does not currently preserve an independent XML source edit history alongside IFC results, and may not detect every non-root attribute change in compound create/delete operations. Material/type/property and full geometric topology checks are not yet proven.
- Nothing here is an official BIM-Edit geometry/semantic/topology score. The full 36-task pilot requires Issues #14–#22 and actual scorer/data audits.

Future work: broader shape and semantic constraints, complete relation ownership, unbiased scorer, persistent source identity and proper graph-aware propagation of voids/space boundaries.

## Actual public BIM-Edit IFC input edit (single additional sample)

The pinned official dataset input simple/17_input.ifc (model repository
0ae510bd21865def4e2c6145c1244f01a1e3bcb9; source SHA-256
c1e0a58fc0f3a99c71250009858f114463fbb8be8519152c2fe524c4c12d0cff)
was loaded into the same trusted compiler.

Its Revit-style Wall profile has an IfcPresentationLayerAssignment pointing
at the same IfcShapeRepresentation. This is **not a second product owner**.
The ownership check now allows the presentation-layer metadata reference
while still blocking multiple IfcProductDefinitionShape owners.

Editing the first wall's declarative XML height from approximately 2.8m
to 3.1m created a valid new IFC4X3 result with native
IfcExtrudedAreaSolid.Depth = 3.1. All 76 unrelated source IFC root entities
were unchanged and the original source was never modified. The full
height-only STEP diff check ensures that only the approved wall extrusion
entity changed. This is a **single geometry-edit feasibility test**, NOT a
complete BIM-Edit task score or official evaluation.
