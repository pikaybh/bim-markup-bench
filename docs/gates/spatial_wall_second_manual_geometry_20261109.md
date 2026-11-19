# G1 #14 — frozen spatial wall: manual real-input geometry parity, full-task topology blocked (2026-11-09)

**Status: `BLOCKED_FULL_TASK_TOPOLOGY_ORACLE_PENDING_AFTER_MANUAL_GEOMETRY_PARITY_PASS`**. This is a trusted deterministic geometry execution test, **not** a model benchmark run, an official grading result, a claim of task-level success or full information equivalence.

## Fixed task / source-only constraints

- The original, preregistration-candidate 36-task list is unchanged. Test identifier: `WAL-CRE-SPA-A-003` (spatial Wall create in a public input IFC4X3).
- Public **INPUT** SHA-256 is `e90e635629a85cf1942163db0f647a49edc6d24631ba72ec79a0381c9145a0de` (verify before processing). The code never opens the reference/ground-truth IFC, reads grader target annotations or makes provider calls.
- The natural-language task describes a 0.175m-thick, 2.8m-high wall between two parallel walls at +Y 1.3025m from the room-side Door jamb. Native public IFC source inspection indicates a room rectangle, a hosted Door and both enclosing walls.
- The new #11 parent PR #68 ensures the room formerly opaque due to an internal rotated swept-solid frame is visible as a **typed declarative Space**. It is an exact world-cuboid representation, not a fabricated bounding box. This removes one necessary input-information asymmetry but does **not** prove all semantic/source information parity.

## Trusted geometry reasoning and manual pair

The trusted G1 tool `tools/verify_spatial_wall_manual_oracle.py` resolves public prompt references against the native **INPUT** (not GT) and checks room–wall–door alignment, floor containment and all requested dimensions. It then sets one additional declarative `<Wall .../>` **document state** (NOT a create command) and the independent I0 recipe authors an IfcOpenShell Wall with the same source-only coordinates.

- Expected new Wall world bbox: min **(0.175, 5.23275, 0)** m; max **(4.625, 5.40775, 2.8)** m.
- D0 declarative IFC and I0 independently generated Python IFC both create the wall; independent IFC structural observation parity passes. Their complete-file SHA-256 values can **differ across arms and runs** due to generated native IFC relation identifiers; do not claim byte-identical IFC results here.
- A single building-storey containment relationship for the new wall is verified. All pre-existing typed IFC relationships are preserved: no old space boundaries, openings, walls, fills or connectivity are dropped or unexpectedly rewired.
- The new wall has **zero native IFC connects relationships and zero new space-boundary relationships**. This is an objective limit of the current *standalone wall* geometry backend, not proof that the full task's implicit physical connectivity/topology semantics hold. The official evaluator could require more.
- Candidate result IFC files exist only in isolated temporary folders during execution. The initial source is checked for hash preservation. The report contains **no private target GlobalIds, GT file paths, raw IFC bytes, model-generated solutions, or source paths**.

## Explicit fail-closed readiness classification

The audit command returns **exit 2 intentionally** even when manual D0/I0 geometry parity passes, because:
- native IFC join/space-boundary creation for the task is not implemented/validated;
- full parity of what an LLM can infer from XML vs full IFC has not been independently established;
- no model has attempted the natural-language task;
- official BIM-Edit evaluator provenance/metric parity remain unverified and actual full 36-task sample is not runnable.

`all_input_information_equivalence_proven=false`, `space_boundary_reconstruction_verified=false`, `this_is_an_approved_full_task_oracle=false`, `official_scores=0`, `LLM_provider_calls=0` are **hard assertions** in the evidence output.

## Reproduction / tests

Windows PowerShell, working directory `D:\문서\D__1_Projects\202611\bim-markup-bench`:

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_spatial_wall_manual_oracle tests.test_oracle_parity -v
.\.venv\Scripts\python.exe -m tools.verify_spatial_wall_manual_oracle
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

Expected: dedicated regression tests pass; the evidence CLI **returns 2 (blocked)** and prints a sanitized positive *geometry* comparison only. Tests cover nonpositive dimensions, nonexistent public IFC references, immutable source, no GT keys in evidence, independent D0/I0 output and forced unrelated native relationship changes that must be denied. The I0 reference module imports no XML compiler, binder or runtime mutator.

## Next eligible milestones

1. Separate reviewed native topology implementation of physical Wall–Wall joins and required `IfcRelConnectsPathElements` / `IfcRelSpaceBoundary` only when the task's true authored intended relationships can be independently justified. Avoid inventing missing BIM semantics.
2. Prove complete true task-level D0/I0 oracle including boundaries, retained native relations and physical shape vs a predeclared source-only test; keep official GT isolated until blind scoring.
3. Check equal information/available tool budgets in actual agents; only then obtain official scorer/author provenance or disclose independent scores, and authorize matched paid LLM pilot separately.

Related Draft PRs: #64→#65→#66→#67→#68 (parent projection). This #14 branch is stacked on #68. **No normative BIXML/Xim source has been edited.**
