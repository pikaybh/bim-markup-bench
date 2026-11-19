# G1 Issue #11 — correct physical Opening width/height for rotated/reoriented swept voids

2026-11-09 · Scope: **read-only IFC4X3 → XML projection**. This is not a compiled task result or an official benchmark score.

## Before
For the frozen public-input IFC belonging to `WIN-UPD-DIR-A-002` (metadata-pinned; private target metadata never shown to an agent), the native `IfcExtrudedAreaSolid.Depth=0.2 m` describes a **wall-thickness** dimension, not the opening's height. The source opening mesh has wall-parallel span **0.6 m** and vertical span **1.5 m**. Earlier XML falsely declared width **1.5 m** and height **0.2 m**. The native Window's declared dimensions were width 0.6 m and height 1.5 m, causing a real-source no-op compile to fail `BindingError: Filling exceeds opening height`. The previous float precision fix (#64) only made the XML syntax parseable.

## Change
The trusted read-only projection now computes Opening width from the **world-coordinate IFC mesh** projected onto the horizontal native host-wall axis, and Opening height from the **world Z** span; it also requires a strictly positive nondegenerate wall-normal thickness. The pre-existing native swept-solid/profile preflight remains fail-closed for unsupported geometry. Native IFC input remains the authoritative backend data, while XML remains a partial and potentially lossy view. We do **not** change the model-facing XML semantics, source IFC, task IDs, target reference IFC, hidden GT, task prompts or scoring logic.

## Evidence / reproduction
PowerShell in project root:
```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_projection_numeric_precision tests.test_ifc_projection -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```
Tests include pinned public-input hash validation, mesh width/height vs native Window dimensions, native binder source relation contracts, exact byte-identical no-op compilation, unchanged first-party synthetic source, and negative nonfinite/degenerated projection guards. All IFC output is confined to temporary run directories and checked for immutable input preservation.

## Boundary
This solves read-only source projection and no-op binding only. The official task's **+1m world-Y Window+Opening relocation** is still pending a source-specific native-frame preflight, guarded collision analysis, and independent I0 parity against exactly the same source IFC. Do not mark task success before that, and never expose frozen grader target fields to a model-facing prompt. No official evaluator run, provider calls or paid inference.
