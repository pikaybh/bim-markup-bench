# G2 #21 — independent native IFC evaluator (partial)

Status: **own synthetic tests pass; official BIM-Edit score NOT reproduced**.

## Data boundary

This read-only scorer takes three IFC4X3 files: immutable input, private
ground truth and predicted output. It also accepts grader-only operation,
target IFC class and existing target GlobalId metadata (update/delete).
No XML source, Python agent solution, BIM CommandBus, method label, model
provider, API key or external task prompt is consumed during scoring.

The official BIM-Edit task records and input/GT paths are public, but the
official evaluator implementation is not available publicly according to
ONESTRUCTION's independent benchmark methodology:
https://ai.onestruction.com/leaderboard/en/methodology/

This implementation must never be presented as an official score.

## Three independent components

Geometry: real IfcOpenShell IFC4X3 world-space triangulated mesh; 384
surface-area-weighted deterministic samples per target (seed 2607);
median bidirectional nearest-neighbor distance. Score is
exp(-5 * median_distance / union_AABB_diagonal). Exact mesh matches
within 1e-6m score 1. Deletion uses object absence. An absent reference
mesh blocks rather than generating an unsupported geometry score.

Semantics: 0.5 exact IFC class match plus 0.5 matching product properties,
including IFC typed values, primitive Psets and material identity;
5% relative tolerance for numeric properties. Unrelated product,
property, material and geometry alterations are flagged as collateral;
strict success requires zero collateral.

Topology: actual IFC relationship signatures for containment,
aggregation, voids, fills, space boundaries and element connections.
The reference delta from input to GT is compared to candidate delta
from input to result. Created node GUIDs can be aligned by geometry
independently, allowing equivalent output under a different new GUID.
Node-edit and edge-edit F1 are weighted 0.3 / 0.7. Unrequested graph
changes where GT topology has no changes receive topology 0.

Strict pass requires each component at least 0.98 AND zero unexpected
collateral. This is a **separately frozen independent rule**; we do not
claim identical matching, mesh sampling, tolerance, topology alignment or
property selection to the BIM-Edit paper or private evaluator.

Failures are explicit. Invalid prediction IFC receives 0,0,0 and
INVALID_OUTPUT_IFC; invalid reference / undefined target receives BLOCKED
and null component scores; geometry-less IfcSpace receives
BLOCKED_REFERENCE_GEOMETRY_UNAVAILABLE. Native IFC files are hashed
before and after read-only grading.

## Tested and not tested

Synthetic tests verify GT-vs-GT 1/1/1, native IFC parity, creation with
different generated GUID, deletion, wrong geometry, wrong IFC class,
wrong properties, missing wall opening relation, missing room boundary,
collateral deletion, mismatched target and invalid files. Removing the
wall-void relation changes BOTH graph topology and wall physical geometry,
which the scorer detects through native triangulation.

The scorer is not calibrated against the 324 official task GT files,
the official unseen implementation, a full six-class operation corpus
or real-world edge cases. Complex oriented box matching, multiple
simultaneous new entities, topology ambiguities and room meshes remain
unsupported or provisional. OS-level process isolation is not verified
(#19); parsing untrusted IFC requires additional security review.

## Offline reproduction

    uv sync --frozen --python 3.12
    .venv/bin/python -m unittest tests.test_bim_edit_scorer -v
    .venv/bin/python -m tools.score_independent_ifc
    .venv/bin/python -m tools.score_independent_ifc \
      --prediction tests/fixtures/synthetic/input.ifc

The first CLI score is an own synthetic GT-vs-GT 1/1/1 check.
The second demonstrates a wrong-height result with failed strict pass.
Neither invokes a paid model, writes IFC, or authorizes official scoring.

The primary bench score CLI and all G1/G2 live pilot gates remain BLOCKED.
No production Xim/BIXML changes.
