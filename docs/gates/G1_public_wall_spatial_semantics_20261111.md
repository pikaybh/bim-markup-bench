# G1 #16 — Frozen public spatial Wall: physical T-joins are not a proven Room split

**Date:** 2026-11-11 KST · Windows offline IFC source-only evidence.

**Verdict:** PASS_BOTH_NATIVE_WALL_JOINS_ROOM_PARTITION_NOT_PROVEN.

**Release gate:** BLOCKED_FULL_ROOM_ORACLE_AND_OFFICIAL_SCORER.

This report is an independent, developer-authored, non-LLM IFC-native
postcondition check for the unchanged fixed candidate WAL-CRE-SPA-A-003.
It is NOT an author-provided BIM-Edit grader result, an official task
success, a new experiment selection, or permission to run paid inference.

## 1. Exact scientific boundary

The frozen public instruction requests a new Wall orthogonally between two
specified existing Walls. Its location references a door viewed from the
specified Room, at a 1.3025 m offset, thickness 0.175 m, height 2.800 m.
It does not explicitly prescribe a second IfcSpace ID, name, type,
property-set, quantity, altered Space boundary or exact Room splitting rule.

A physical new Wall may geometrically divide an enclosed volume while the
IFC semantic IfcSpace object remains unchanged. Therefore D0/I0 IFC
physical parity does not establish parity with a potentially richer hidden
GT Space topology. Conversely it does not prove that creating a separate
IfcSpace is mandatory under the public instruction. No hidden GT target
metadata is read to settle that ambiguity.

## 2. Source-only native observations

- Public original IFC SHA-256:
  e90e635629a85cf1942163db0f647a49edc6d24631ba72ec79a0381c9145a0de
- Published instruction SHA-256:
  31a00588498f68ef6791a133b033cc3da442749d5a237e76f0f5817cf095d14d
- Original named Room world bbox: [0.175, 2.900, 0.000] to
  [4.625, 6.025, 2.800] metres.
- New Wall world bbox: [0.175, 5.23275, 0] to
  [4.625, 5.40775, 2.800] metres.
- World-coordinate door offset: published 1.3025 m from the door bounding
  edge as interpreted in this specific pinned source; not a general Revit
  inside/outside policy for arbitrary doors.
- New Wall native solid volume (also overlap with original Room volume):
  2.1805 m3.
- The new Wall meets the two named boundary Walls and creates two native
  IfcRelConnectsPathElements with the expected ATPATH/ATSTART and
  ATPATH/ATEND bindings. Its storey containment matches the original room.
- All **10 originally represented IFC product meshes** retain their world
  vertices, mesh triangle counts and native volume in both D0 and I0.
- Original IFC Space count is **2 before and 2 after** in both arms.
- Original IfcRelSpaceBoundary count is **13 before and 13 after**.
- The original Room's native geometry and original boundary relations
  remain unchanged. There is NO new native IfcSpace.
- Both D0 and I0 satisfy the independent checks. Their IFC serialized
  output bytes may differ, so raw equality is not asserted.
- No official evaluator, benchmark GT, model-generated text, provider
  inference or billable calls were used; official tasks scored = zero.

The current source Room still geometrically overlaps the new Wall. This
establishes that the two presented candidates have not updated the
IfcSpace representation to a Room partition. It does NOT by itself
establish the hidden official success criteria or assert the candidates
are globally invalid IFC.

## 3. Implementation and safety

- tests/oracles/python/public_wall_space_semantics.py:
  independent frozen public instruction parser and IFC world-mesh,
  root, relation, Wall contact and Space-semantic checker. It imports
  neither D0 XML authoring, I0 imperative authoring, nor either scorer.
  It discovers the new Wall from the native root inventory difference;
  the new Wall GUID is not provided by hidden task metadata.
- tools/verify_prompt_grounded_spatial_wall.py:
  only an optional trusted read-only observer hook is added, invoked
  after compilation while temporary D0 and I0 outputs are available.
  Default historical verifier behavior remains unchanged.
- tools/verify_public_wall_spatial_postconditions.py:
  invokes the independent checker on both temporary IFC outputs, enforces
  parity of the task-specific postconditions and writes sanitized,
  write-once aggregate evidence. This checker is not mounted into any
  experimental model's workspace.
- tests/test_public_wall_space_semantics.py:
  positive original-source witness plus failures for altered prompt/source,
  wrong Wall geometry, broken T join, missing storey containment,
  changed unrelated Wall, invented IfcSpace, missing Space boundary,
  changed original Room geometry, malformed IFC and evidence leakage.

All original IfcRoot classes and descriptive fields are preserved.
The verifier prevents changes to existing native relationships other
than the narrowly allowed Wall containment extension. Unrelated
existing world-meshed IFC products must remain unchanged. The strict
fixture checks are NOT the official BIM-Edit evaluation formula.

## 4. Reproduction

From the connected Windows repository:

    $env:PYTHONUTF8='1'
    .\.venv\Scripts\python.exe -m unittest tests.test_public_wall_space_semantics tests.test_prompt_grounded_spatial_wall -q
    .\.venv\Scripts\python.exe -m tools.verify_public_wall_spatial_postconditions --output-json reports/g1_public_wall_space_semantics_20261111.json
    .\.venv\Scripts\python.exe -m unittest discover -s tests -q

The observer CLI deliberately returns exit code **2** despite positive
physical evidence: complete official task/oracle, matched G2/G3 model
execution, data rights and an official executable scoring standard remain
blocked. It refuses to overwrite existing files; use a fresh destination
name on replay.

Recorded evidence SHA-256:
590bd0c99b9fe8dbc4e4ee84d46951fb429db889fe4f10a24752fbc7a3be8352

## 5. Next logical gate

Formal G1 completion still requires complete D0/I0 official-task semantics
for all selected cases, or explicit preregistered unsupported categories.
Any decision about authoring new Spaces, their property sets, boundaries,
quantities and naming must use **public instruction and source-only**
evidence or a prospectively agreed evaluation rule, never hidden reference
metadata leaked into a model. The actual official BIM-Edit scorer still
has not been verified in this repository. No G3 run is authorized.

This one-case improvement is a stronger *source-only* physical and spatial
audit, not an official success result, efficacy claim, or experimental
comparison of direct XML versus Python editing.
