# G1 #15 — Bounded native IFC Door + Opening deletion (v0.2)

**2026-11-11 KST.** Source-only deterministic D0/I0 native postconditions:
**PASS**. Official BIM-Edit task oracle and G1/G2/G3 release: **BLOCKED**.

This implementation was developed **after inspecting one of the existing
36 candidate tasks**. It is a versioned engineering feasibility result,
NOT an unbiased/preregistered model experiment. The historical 36-task
eligibility matrix remains unchanged. A future provider experiment must
be separately frozen and disclose this post-hoc capability development.

## Fixed original public case and evidence

- Case: DOR-DEL-DIR-A-001. Source IFC SHA-256:
  170d9ed9c10a31d86c3ff2207a450fd552166af21472486f11004f6e2b14defb
- Published instruction SHA-256:
  8dc59cbf741dbbf626843eebd91972197fa9ff0b9cbea251d6b9a8d8cd0a752a
- Its Door fills one Opening and that Opening voids one host Wall.
  The Door has an explicit shared storey assignment, two exclusively
  owned Psets, one sole material relation, shared Type and Classification.
- The source Opening has NO direct storey assignment, despite the public
  text asking for its removal. This is a no-op on a nonexistent edge,
  never silently counted as deleting an actual source relationship.
- One IfcRelSpaceBoundary references the Door itself but is not named in
  the public deletion task. The policy below is source-only; it does not
  derive target semantics from hidden benchmark GT.

## Prospective, narrow IFC-dependent deletion policy

A tested D0 agent would edit a **declarative state XML document**, removing
two existing Door and Opening nodes. There is no command-opcode XML and no
direct IFC API/tool access to that tested agent. Only the **trusted backend**
derives their stable-ID graph diff and applies IFC mutations.

This new backend accepts ONLY one isolated removal of an existing Door
and the exact Opening it fills, with precisely the expected opening_fill
and host_void graph edges removed, and no unrelated state/geometry change.

Native preflight insists on a unique Door, Opening, host Wall and storey;
one Fill and one Void relation; one Door-related SpaceBoundary; exactly
two Door-only Pset assignments and Psets; one Door-only material relation;
and uniquely scoped three shared Type/Classification/Storey memberships.
It refuses arbitrary extra inverse relations, shared Psets/materials,
direct Opening/storey containment, a second filling, wrong IFC classes or
an unknown native relationship.

Trusted native deletion removes the two products and exactly **eight
dependent native IFC roots**, totaling **ten removed IfcRoots**:
- IfcDoor, IfcOpeningElement;
- IfcRelFillsElement, IfcRelVoidsElement;
- one IfcRelSpaceBoundary that would otherwise point to the deleted Door;
- one Door-only IfcRelAssociatesMaterial;
- two IfcRelDefinesByProperties and their two IfcPropertySets.

The Storey, Type and Classification shared relations are preserved with
only the deleted Door removed from their member lists. The native
IfcRelDefinesByType OwnerHistory receives a standard MODIFIED update.
No new Room or Space boundaries are generated. The remaining Room
boundary surface's completeness after deleting a Door boundary is **not
established**; official author-specified Space semantics remain unknown.

The native staged result is reopened and checked for precise old/new
IfcRoot inventory, shared relation membership and unchanged unrelated
root data. All **13 surviving unrelated represented product meshes**
must retain their world vertex multisets, triangle counts and volumes.
The original host Wall's opening must close, increasing volume by exactly
0.374 m3 (the original Opening volume). A failed validation prevents
publication of the staged file, and tests demonstrate rollback.

This is an intentionally strict deterministic fixture validator and
not a general IFC equivalence metric for all possible Door deletions.

## Verified offline results

| Evidence | Observed |
| --- | --- |
| D0 valid XML state with both objects removed | accepted |
| D0 trusted native result | committed, new IFC output |
| Independent authored I0 native deletion | committed in isolated test clone |
| D0 and I0 removed native roots | 10 each |
| Preserved shared Type / Classification / Storey relations | 3 each |
| Preserved unrelated represented world meshes | 13 each |
| Host Wall void closed / volume gain | yes / 0.374 m3 each |
| Existing IfcSpace | 2 unchanged |
| Existing IfcRelSpaceBoundary | 12 before, 11 after |
| Original Opening direct storey assignment | 0 |
| Official evaluator, hidden GT or scored tasks used | none |
| Actual LLM calls or billable inference | none |

The independent test authored under tests/oracles/python evaluates both
native IFC outputs; equal source-only physical evidence is NOT equivalent
to a benchmark-author verified complete task success.

## Files, evidence and reproduction

Native runtime:
- src/runtime/hosted_door_delete.py
- src/runtime/ifc_mutations.py
- src/runtime/topology_ops.py
- src/runtime/compiler.py

Developer-only tests, harness and report:
- tests/test_hosted_door_delete_runtime.py
- tests/test_public_door_delete_gate.py
- tools/verify_public_door_delete_gate.py
- reports/g1_public_door_delete_compiler_v02_20261111.json

New report SHA-256:
adf18246cda9f16044977e7882f6a3ab53a7d3ff0b9d7d7f39151c35a443cdd5

Prior historical v0.1 evidence is deliberately retained unchanged at
reports/g1_public_door_delete_dependency_gate_20261111.json, which
accurately documents the OLD compiler's inability to delete this pair.

Offline Windows reproduction:

    $env:PYTHONUTF8='1'
    .\.venv\Scripts\python.exe -m unittest tests.test_hosted_door_delete_runtime tests.test_public_door_delete_gate -q
    .\.venv\Scripts\python.exe -m tools.verify_public_door_delete_gate --output-json reports/my-fresh-replay.json
    .\.venv\Scripts\python.exe -m unittest discover -s tests -q

The report CLI intentionally returns **exit 2** despite passing native
checks: G1/G2/G3 release remains blocked and the output is write-once.

## Research limitations and next gates

- The source-only policy deletes the orphaned Door-related boundary
  instead of fabricating Room repairs. Whether official BIM-Edit expects
  another boundary/Room shape cannot be determined without the genuine
  grader or explicit prospective policy; do not infer it from GT.
- This capability was developed after inspecting a frozen task. Report it
  as post-hoc engineering coverage, not a pre-registered treatment win.
- No arbitrary Door deletion, shared material/Pset cascades, multi-host
  Openings, general spatial recomputation or complete BIM-Edit 324
  support is claimed.
- Actual official scorer, original/reference IFC file-level rights,
  blinded fixed-case grading, G2 tool/resource parity and secure
  provider sandbox remain blocked.
- No Xim/BIXML product code, production server, frozen sample, or
  benchmark evaluator was changed.

**Verdict:** stronger source-only native D0/I0 feasibility in one fixed
Door Delete scenario. Not evidence of LLM-generated task success nor
causal superiority of declarative markup over imperative Python.
