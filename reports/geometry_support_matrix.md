# G1 #14 — IFC4X3 parametric geometry coverage matrix (PARTIAL)

## Verified (one first-party synthetic standalone wall)

The trusted compiler now supports editing the **physical** thickness of a *standalone* straight IfcWall in original metric IFC4X3:
- Original XML thickness = 0.20 m; direct-edit XML after = 0.35 m.
- Output IfcArbitraryClosedProfileDef / IfcIndexedPolyCurve profile measured 0.35 m, and IfcOpenShell triangulated wall mesh Y extent increased exactly 0.15 m.
- Only the approved IfcCartesianPointList2D STEP entity changed in the existing source, all unrelated entities and IFC root objects were preserved. Original IFC source SHA unchanged; output is separately staged/committed.
- Half-written, zero/negative/out-of-range or semantically invalid edits fail closed; blocked path never emits result IFC. Numeric 0.2 vs 0.200 is a byte-identical no-op.
- A pre-existing IfcWall with IfcRelVoidsElement / IfcRelSpaceBoundary / connections or type/material ownership is deliberately NOT eligible. Void and hosted filling regeneration are not implemented, and pretending otherwise would corrupt topology.

## Source correctness and status

| IFC class / geometry edit | Current state |
| --- | --- |
| Straight standalone IfcWall height | Implemented and triangulation tested (#13) |
| Straight standalone IfcWall thickness (polygon profile) | Implemented and triangulation tested (#14) |
| Simple IfcWall create / remove | Implemented only standalone and safe (#13) |
| Existing IfcWall with attached Opening/SpaceBoundary | Unsupported edits except specifically safe height; thickness rejected |
| Wall endpoint length/rotation/placement | Not implemented |
| IfcSlab boundary, inclination, depth | Not implemented |
| IfcColumn profile, rotation, height | Not implemented |
| IfcDoor/IfcWindow size / offset with hosted void | Not implemented |
| IfcSpace exact shape / boundary | Not implemented, missing geometry in synthetic fixture |
| IFC4 or IFC2X3 editing | Unsupported; current XML grammar fixed to IFC4X3 |
| Official BIM-Edit 324 tasks | No valid official scores, only one tiny real input wall *height* edit tested |
| Matched Python baseline and independent scored geometry | Not implemented |

This is a real 3D/parametric edit, not an XML-only mock. It does **not** imply a general parametric BIM engine. The next necessary fixes for #14 are wall length/rotation with correct host geometry, slab/column/space shape, opening propagation and independent geometric tolerances. Issue #15 owns typed topology regeneration.

The direct-edit LLM sees XML source only. The IfcOpenShell mutation is performed behind the trusted runtime boundary; do not expose helper methods to the direct-edit model.
