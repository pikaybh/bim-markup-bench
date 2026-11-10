# G1 #16 — Frozen public Door DELETE: native dependency + D0 fail-closed audit

**2026-11-11 KST** · Windows 11, pinned real public IFC source · no LLM / no GT / no paid calls.

**Verdict:** BLOCKED_D0_DELETE_COMPILER_AND_PUBLIC_SPACE_BOUNDARY_POLICY.

This is **one frozen task's deterministic readiness evidence**, NOT a
benchmark success, an official score, an approved Room/SpaceBoundary policy,
or experimental support for one arm over the other.

## 1. Selection without cherry-picking

Fixed candidate task: DOR-DEL-DIR-A-001. The original 36-case candidate set
has not been altered. Its public instruction explicitly names the Door,
Opening, host Wall and BuildingStorey. All four typed objects exist in the
immutable IFC source and are projected into the current D0 XML model-facing
view. This makes it a stronger **diagnostic candidate** than the spatial/
topological Window Delete tasks whose Windows are not projected at all.

This does NOT make the task a predeclared passing subset: the full 36-case
denominator and unsupported reason matrix stay unchanged. No task was
replaced after observing results.

Public original IFC SHA-256:
170d9ed9c10a31d86c3ff2207a450fd552166af21472486f11004f6e2b14defb

Public instruction SHA-256:
8dc59cbf741dbbf626843eebd91972197fa9ff0b9cbea251d6b9a8d8cd0a752a

Frozen task JSONL, fixed pilot manifest and public remote asset tree are
independently SHA-256 pinned before reading the source IFC. Only the
published prompt and original input IFC path are used from the task record.
The target GUID grading annotation, expected/reference model path and
evaluation field are NOT read to construct or verify the edit.

## 2. Input IFC contains an important source/prompt discrepancy

- The Door is related to the requested Opening by one IfcRelFillsElement.
- The Opening removes material from the named host Wall by one
  IfcRelVoidsElement. The Door belongs to the requested BuildingStorey via
  an existing IfcRelContainedInSpatialStructure containing other objects.
- **The Opening has NO direct IfcRelContainedInSpatialStructure assignment.**
  Yet the public instruction asks to delete assignments of both Door and
  Opening to that storey. Removing a nonexistent Opening/storey edge is a
  no-op, not evidence that an actual relationship was removed.
- The Door has one IfcRelSpaceBoundary to an existing Space. The public
  instruction does not explicitly mention this boundary or specify whether
  to delete it, reassign it or regenerate the Room's boundary surface.
- Door Type and Classification relations are shared with another Door;
  their membership must be reduced rather than deleting the shared roots.

The compiler must not silently treat unsupported relation cleanup as
success. The missing direct Opening/storey assignment and the unmentioned
Space boundary are separately recorded as **unresolved source semantics**,
not inferred using benchmark GT.

## 3. Actual D0/XML behavior (current runtime unchanged)

A source-only experiment stages the *same* published instruction and
source-projected XML that would be visible to D0. The manually authored
declarative edit removes the actual Door and Opening nodes from the document
state. It does not create an XML command list or call a tool on behalf
of the tested model.

- The XML editor accepts the resulting well-formed, typed, source-bound
  snapshot: ACCEPTED_VALID_XML.
- On trusted compilation of the accepted file, the current
  wall/topology planner rejects Door+Opening deletion because the
  verified native mutation surface currently supports only standalone
  Wall or hosted Window removal.
- This rejection is a **fail-closed CompilerError** and no partial native
  IFC result exists.
- The original pinned IFC is unchanged. D0's source instruction, XML,
  schema and other shared model context components are matched against
  the documented I0 source observations.
- A valid XML document does not constitute executable support for this
  complex Door deletion. The D0 gate remains BLOCKED.

Existing compiler, D0 agent-facing language and runtime production code
were **not modified** to bypass this limitation.

## 4. Independent I0 source-only physical probe

A separate manually authored Python/IfcOpenShell recipe loads a clone of
the same immutable public IFC, validates its public Door/Opening/Fill/Void
relations, and removes Door then Opening using the ordinary native product
deletion API. A separately authored native IFC postcondition checker
compares original and output IFCs without invoking the D0 compiler,
manual I0 authoring code or the benchmark scorer.

Observed outcome on this exact original source:

| Native difference | Verified outcome |
| --- | --- |
| Original IfcDoor and IfcOpeningElement removed | 1 each |
| Original filling and host void relations removed | 1 each |
| Related original IfcRelSpaceBoundary also removed | **1**, unmentioned in public instruction |
| Original IfcPropertySet removed | 2 |
| Original IfcRelDefinesByProperties removed | 2 |
| Original single-object IfcRelAssociatesMaterial removed | 1 |
| Total deleted IfcRoot records | **10**, with exact observed class inventory |
| Remaining shared Type, Classification, Storey membership records | 3 records safely reduced by Door membership |
| Shared IfcRelDefinesByType OwnerHistory | native API records a MODIFIED history |
| Other represented world meshes unchanged | **13** |
| Host Wall originally cut by Opening | no longer has this void |
| Native host wall volume gain | **0.374 m3**, equals old Opening volume |
| Existing IfcSpace count | 2, unchanged |
| Existing IfcRelSpaceBoundary count | 12 -> 11 |
| Explicit direct Opening/storey assignment in original | **none** |

These are source/output IFC facts for a **developer-authored, non-LLM I0
reference**. They do not establish that deletion of the Door's Space
boundary matches the unverified published evaluator, or that the result
would earn an official benchmark score.

The native checker rejects unexpected additional root deletions, other
product geometry changes, altered residual relationships, missing
host-void closure, wrong source GUID/class, forged public instruction or
invalid native IFC. Every output is ephemeral and under a trusted temp
directory. Original IFC and hidden reference files are never modified.

## 5. Reproducible commands

In the Windows bim-markup-bench repository with the existing gitignored
small public IFC cache and pinned Python environment:

    $env:PYTHONUTF8='1'
    .\.venv\Scripts\python.exe -m unittest tests.test_public_door_delete_gate -v
    .\.venv\Scripts\python.exe -m tools.verify_public_door_delete_gate --output-json reports/g1_public_door_delete_dependency_gate_20261111.json
    .\.venv\Scripts\python.exe -m unittest discover -s tests -q

The CLI intentionally returns **exit 2**, even if every diagnostic test
passes: it means a complete D0/I0 official task oracle is not ready.
The report is sanitized and write-once. For repeats, provide a *new*
output filename. It includes no raw GUIDs, full instruction, GT paths,
model-generated Python or private reference geometry.

Report SHA-256:
e52917418fb662739453ccc17eda6a24d76d6441a395db4a000ccf87cd66e946

### New tests

- actual public source, exact candidate selection, IFC checksum and
  published typed Door/Opening/Wall/Storey relationship resolution
- rejected D0 compiler with **no partial output**, plus source unchanged
- independent native I0 scoped removal, orphan avoidance, exact ten-root
  deletion, three edited shared memberships, one implicit space-boundary
  deletion and host-wall physical mesh regeneration
- malformed public prompts, forged task private metadata, mismatched
  frozen digests, missing/invalid IFC, duplicate wrong edits and collateral
  deletion/mutation of unrelated objects
- source-only report redaction and no raw answer paths

## 6. Next implementation gate

To implement D0 safely rather than bypassing it, a separate runtime/
topology owner review (G1 #15 / #16) is required for a **declarative stable-ID
Door+Opening state deletion** and an explicitly tested source-native
cascade policy covering IfcRelFillsElement, IfcRelVoidsElement, shared
Type/Classification/Storey memberships, owned Psets/materials, related
space boundaries and host physical void removal. Any policy that changes
IfcRelSpaceBoundary must be specified prospectively, not inferred from
hidden ground truth. Add positive and negative native IFC fixtures and
transactional rollback tests before proposing support.

Keep DOR-DEL-DIR-A-001 in the fixed selected set with its current
UNSUPPORTED status until both independently authored deterministic arms
prove the **same** declared result and an independent scorer boundary
is satisfied. Do not count I0 feasibility as D0 support or a measured
effect of markup over Python. The published official evaluator, model
rights, full 36 task oracle coverage and G2 model/tool fairness remain
blocked. No charged model run is authorized.
