# G1 #16 — Public Window task: independent native world-mesh postconditions

**2026-11-10 · Status: PASS_STRICT_PUBLIC_NATIVE_MESH_POSTCONDITIONS / FULL_OFFICIAL_ORACLE_BLOCKED**

This is a trusted non-LLM, source-only IFC-native validation for the
unchanged frozen candidate WIN-UPD-DIR-A-002. It does not change task IDs,
hidden GT, evaluator scoring, treatment representation, model prompts,
or preregistration.

## Why previous evidence was insufficient

Prior G1 reports establish D0 XML source-state editing versus independently
authored I0 IfcOpenShell output parity, the 1 m +Y translation of native
Window/Opening placements, root/relationship preservation and a single
IfcCartesianPoint mutation. Yet equality of D0 and I0 can be jointly wrong.
Physical regeneration of the host Wall void and preservation of all
other meshed products were not specified as strict independent
source-only postconditions.

A probe of the immutable real IFC demonstrated that moving the Opening
also changes the host Wall's evaluated mesh, though the Wall itself has
no direct STEP-row edit. Its void rim Y extent changes from 10.5..11.1 m
to 11.5..12.1 m, while the Wall exterior bbox and volume remain stable.

## New physical acceptance contract (NOT official scoring)

Source: tests/oracles/python/public_window_mesh_oracle.py. Independently written,
it does not import the D0 XML compiler, I0 authoring logic or benchmark
scorer. Inputs are only immutable original IFC, produced candidate IFC
and the original public natural-language instruction.

- Prompt grammar/one-metre world +Y direction, Window-Fills-Opening and
  Opening-Voids-Wall typed relationships, IFC4X3 metre units and original
  root/relationship inventory are checked from native IFC.
- All **28 represented IfcProducts** are triangulated in world coordinates.
  The Window and Opening entire vertex multisets shift by (0,+1,0) m;
  world triangle counts and enclosed mesh volumes remain unchanged.
- The host Wall loses exactly the old Opening perimeter vertices and gains
  the equivalent translated rim, preserving every other wall vertex.
  Outer bounds, triangles and volume are unchanged within 1e-6 tolerance.
- All other **25** represented products retain their world vertex
  multisets, triangle counts and volumes.
- Strict deterministic IFC reference additionally allows only one changed
  IfcCartesianPoint native STEP row; root and relationship inventories
  remain equal. Inputs/outputs are hashed before/after the read-only check.

The "one changed STEP row" condition is deliberately a reference ceiling
for this specific deterministic recipe, NOT a universal IFC equivalence
criterion. A semantically equivalent exporter could rewrite extra rows,
and would require a different prospectively specified independent metric.
No additional threshold or score is introduced into the benchmark.

The existing tool tools/verify_prompt_grounded_window_pair.py gains an
optional trusted read-only callback executed while its ephemeral D0/I0
outputs still exist. Its default behavior is unchanged. The new standalone
tools/verify_public_window_mesh_oracle.py evaluates both physical native
IFCs and fails closed if their independently observed postconditions differ.
The checker is never mounted in a tested LLM's workspace.

## Actual observed source-only evidence

| Check | Result |
| --- | --- |
| Native physical shapes checked per arm | 28 |
| Unrelated shapes preserved per arm | 25 |
| Window and Opening full world mesh moved +1m Y | PASS in D0 and I0 |
| Host void rim removed and replaced at translated location | PASS both |
| Host wall exterior bounds / mesh volume / triangle count | Preserved both |
| Existing native relations and non-target STEP entities | Preserved both |
| Original Window/Opening-host IFC source SHA-256 | c533767f850a7ba01b73caf4467fae7cc886807a72a900d65cd480e7b877bcc9 |
| Published task instruction SHA-256 | ff98d90daafa34a4979fc942d4d3477a0128526a2cf7c918c419473319078efe |
| Ground truth opened, official scored tasks, actual LLM calls | 0, 0, 0 |

The host Wall exterior bounds in this original input are
[29.2, -0.2, 0.0] to [29.4, 15.0, 3.6] metres; its native regenerated
mesh volume is approximately 10.584 cubic metres before and after.
This is a physical IFC observation, not a requirement copied from GT.

## Offline reproducibility

From the pinned Windows research repository:

    $env:PYTHONUTF8='1'
    .\.venv\Scripts\python.exe -m unittest tests.test_public_window_mesh_oracle -v
    .\.venv\Scripts\python.exe -m tools.verify_public_window_mesh_oracle --output-json reports/g1_window_world_mesh_20261110.json
    .\.venv\Scripts\python.exe -m unittest discover -s tests -q

The evidence CLI returns exit **2 by design** because the official/paid
G1/G2/G3 release gate remains blocked. The report is sanitized,
write-once and contains no raw prompts, private target GUIDs, original
model paths, IFC bytes or hidden reference solutions.

New tests include genuine source+I0 physical evidence, actual paired
D0/I0 ephemeral result verification, wrong displacement, missing void
relationship, collateral product mutation, fabricated failure of Wall
void regeneration, false unrelated mesh changes, invalid source and
prompt mutation, and evidence redaction.

## Research limitations / next gates

This validates ONE public Window task on native IFC output, not six-class
CRUD or all 36 task-specific paired oracles. It has NOT been compared
against the benchmark author's hidden target IFC or official executable
scorer. It is not an actual model-generated outcome and cannot be
used as an official success metric or to assert an XML benefit.

The distinct spatial Wall task still has unresolved complete room
semantics/partition interpretation; inventing new room metadata from
the hidden reference would violate source/answer separation. G2/G3
sandbox, tokenizer, matched feedback, cost and rights approvals remain
blocked. Do not leak this developer reference answer to either LLM arm.
