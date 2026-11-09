# G1 Issue #15 — source-only frozen BIM-Edit window move, rotated wall and native collision guards

2026-11-09 · **ONE PUBLIC INPUT MANUAL D0/I0 ORACLE PASS; NOT AN OFFICIAL TASK SCORE OR LLM RUN**.

## Frozen source and task

- Fixed predeclared task: `WIN-UPD-DIR-A-002` within the frozen 36-task candidate. Task text requires a Window and hosted Opening move by +1 metre in world +Y and preservation of relationships.
- The **same** locally cached and hash-verified public **input** IFC4X3 is given to D0 and I0. Source SHA-256: `c533767f850a7ba01b73caf4467fae7cc886807a72a900d65cd480e7b877bcc9`.
- The native host Wall has a 90° horizontal world azimuth. Host local +X is world +Y; the Opening has native Wall-relative placement with an associated Window filling. This task is expressible by changing one **declarative XML Opening offset** from its original value by +1 m; the agent-facing XML does not contain mutation opcodes.
- Correct physical width/height projection (Issue #11, PR #66) is a prerequisite. Previous projection interpreted 0.2m swept Depth as vertical height instead of thickness and blocked no-op binding.

## Source-only deterministic pair (trusted oracle)

- **D0:** manually modify the projected XML document state; the trusted compiler derives the semantic diff and emits a native IFC. No LLM calls BIM functions.
- **I0:** independently authored Python/IfcOpenShell reference recipe changes the *same native Opening local X position* by +1 m; the Python oracle imports no XML compiler/binder/mutator.
- **Verified**: native Window world displacement exactly `[0, +1, 0]` metres (within 1 µm); native IFC relation inventory unchanged; unexpected root changes zero; independent IFC observation parity true; the two result IFCs even have **identical full-file SHA-256**:
  `10c68b5a1320f51e1f75f0e12868e1b38f84bc316a92a3c123059d0358bdfe16`.
- Original IFC SHA-256 unchanged; each arm generates its result in a separate temporary directory; neither candidate IFC is committed; no GT IFC is opened and no benchmark scorer is called.
- The target's identity was resolved **inside the trusted oracle test process from frozen metadata**, not by an LLM. Thus this proves **a deterministic common execution ceiling for one fixed real-input task**, not model prompt comprehension, a fair-budget API trial or official BIM-Edit success.

## Geometry/security guard changes

1. `_plain_opening_local_frame` now allows horizontal azimuth of the host Wall if its 3×3 placement is proper/right-handed and world vertical remains +Z. It still rejects tilted/reflected frames, rotated Opening-local axes, non-Wall references and unsupported filling chains.
2. The output validator derives expected **world translation from host native local X**, rather than assuming world +X. It confirms host rotation and relation endpoints remain unchanged.
3. Collision checks compare actual world-coordinate native mesh *wall-axis intervals*. They no longer treat opening swept profile X as horizontal width, which was demonstrably incorrect on this public IFC (profile X instead encodes height). This remains a conservative 1D gate; it is NOT general purpose clash detection.
4. The original Opening location `IfcCartesianPoint` must have exactly one expected owner. Unexpected shared point references are rejected so the update cannot move another element through shared parameter aliasing.
5. The old/new native source-offset values must match the scoped wall-relative placement before mutating; differing projections fail closed.

## Reproduction — Windows, Python 3.12, no network, no paid calls

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_rotated_host_opening -v
.\.venv\Scripts\python.exe -m tools.verify_real_window_move_oracle
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

Sanitized structured evidence: `reports/manual_real_window_oracle_20261109.json`. No GUIDs, GT IFC paths, raw model files, prompt text or model secrets are included.

Positive regressions: OWN generated 90° rotated host plus hosted fill propagated world +Y; pinned public input matched an independent Python implementation exactly. Negative regressions: tilted host, actual public other-opening overlap, shared native location point, existing unrotated collision and dependency checks. Invalid candidates do not produce a new IFC.

## Remaining blockers

- Model/API never interpreted the natural-language prompt, so provider trial count and model success remain **zero**.
- No official evaluator source/commit or numerical grading against the published public GT has been verified. Official BIM-Edit score remains **unavailable**, not 1/36.
- The other 35 frozen pilot tasks have not been proven executable as matched real-input D0/I0 deterministic pairs. Previously recorded source conditional readiness ledger is historical and should not be read as post-fix; its test expectation is updated to the new pre-model capability result.
- Rotated Wall local-X-only moves do not enable arbitrary world-vector edits, resize, other IFC classes, tilted-host operations, complex relations or all three BIM-Edit categories. Per-model redistribution rights remain unresolved. No Xim/BIXML code, official task list, GT files, budgets or scoring math changed.

Related upstream Draft PRs: #64 (safe numeric XML serialization), #65 (frozen source readiness audit), #66 (physical void extent projection). This PR is stacked atop #66 and scoped to Issue #15 runtime topology, tests and trusted oracle evidence.
