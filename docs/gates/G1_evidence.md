# G1-08 / Issue #16: deterministic XML vs Python oracle release gate

**Current verdict: SYNTHETIC ORACLE PASS / OFFICIAL BIM-EDIT RELEASE BLOCKED.**
No paid LLM calls. Not an official BIM-Edit pass, no valid official success
percentage or primary-study score can be inferred.

## What has actually passed

- Frozen input: self-authored IFC4X3 source tests/fixtures/synthetic/input.ifc,
  pinned SHA-256 10d57d3eeb6e50fb51493b03d7cb508d57eadeb76719afaeb71fa6658c3ecf58.
- D0 is a manually edited, declarative XML document compiled by the trusted
  bounded IFC writer. The LLM sees only XML; D0 has no IFC command/tool interface.
- I0 is an independently written Python/IfcOpenShell reference implementation
  with no imports from the XML compiler, binder, graph or mutation helpers.
  It uses the same original IFC and the same native IfcOpenShell kernel.
- Oracle scenarios (6): standalone IfcWall creation with storey containment;
  IfcWall height update; standalone IfcWall deletion; IfcOpeningElement
  translation with Window fill world translation; IfcWindow deletion with
  fill relation cleanup; explicit IfcRelConnectsElements creation.
- Direct / spatial / topological dimensions are represented by these
  deterministic manually authored cases only, not the full official natural
  language tasks or their ground-truth score.
- Independent checker reads both output IFC files only; compares original/
  output IFC schema, IfcRoot GUIDs/classes, native IfcRelContainedInSpatialStructure,
  IfcRelAggregates, IfcRelVoidsElement, IfcRelFillsElement,
  IfcRelSpaceBoundary, IfcRelConnectsElements endpoints, global placements,
  triangulated geometry bbox/volume with 1e-6 unit tolerance, Psets and
  native material records.
- A second source containing actual Pset_WallCommon and assigned IfcMaterial
  passes byte-identical no-op projection and direct-vs-imperative wall height
  output parity, with the Pset/material relationships preserved.
- Existing result IFC is never overwritten by invalid/malformed edits;
  unsupported host, invalid GlobalId and unsupported synthetic IfcSpace
  boundaries fail closed without publishing an output.

Verified commands:

    uv sync --frozen --python 3.12
    .venv/bin/python -m tools.verify_g1_oracles
    .venv/bin/python -m unittest tests.test_roundtrip_preservation -v
    .venv/bin/python -m unittest discover -s tests -v

The data files under tests/oracles/xml/ are frozen human-defined declarative
edits; independently authored imperative reference logic lives under
tests/oracles/python/. The generated PASS_SYNTHETIC_ONLY report is
reports/deterministic_ceiling.json. It is not the full official model ceiling.

## Official 324-task coverage / HARD BLOCK

From the official public BIM-Edit task JSONL fixed at SHA-256
9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83:

- All 324 task IDs are present and categorized by original create/update/
  delete (108 each), direct/spatial/topological (108 each), six IFC classes
  and 18 strata.
- A conservative preregisterable rule ledger marks **246** as statically
  unsupported by currently implemented G1 capabilities and **78** as
  source-dependent / not yet verified. These numbers classify *implementation
  readiness*, not LLM or benchmark success.
- **0/324** have been executed and independently graded against actual
  pinned source/GT IFC. The task-level ledger contains only task IDs and
  class/category/operation/scene/reason codes, NOT prompts, target GUIDs,
  source/GT paths or evaluation metadata.
- A model/API interaction never occurs during ledger generation or gate
  enforcement.
- The complete 4.31GB official IFC artifact set is not locally audited for
  content hashes; benchmark independent scorer still incomplete; declared
  engine support is only narrow G1 subset, not all six classes.
- Matching what the two LLMs can observe about source IFC and ensuring
  sandbox/permissions/budget limits are separate G2 blockers (#17–#22).

Offline commands:

    .venv/bin/python -m tools.audit_bim_edit --fetch-metadata-only
    .venv/bin/python -m tools.g1_release_gate
    .venv/bin/python -m tools.g1_release_gate --enforce

The last command **must exit nonzero** and report
BLOCKED_NO_OFFICIAL_EVALUATION until official asset-content, independent
evaluation, engine coverage and matched-arm safety gates are proven. Do not
override this by changing a report field or passing a budget flag.

## Explicit remaining issue #16 DoD gaps

- D0/I0 comparisons on real pinned official BIM-Edit inputs (only a tiny
  separate public 15KB BIM-Edit input was used for the bounded #13 wall-edit
  feasibility test, not a scored task).
- Full IFC4X3 six-class create/update/delete with hosted SpaceBoundary and
  complex geometry across every requested task/scene.
- Official input and GT source fingerprint/delta content audit (#3).
- Independent BIM-Edit Geometry/Semantics/Topology evaluator (#4/#21),
  tolerance calibration and frozen official score contract (#22).
- Matched LLM context/prompt availability and robust Python execution sandbox
  (#17–#20).
- Stable author-selected XML local ID persistence across multi-turn native IFC
  reprojection (#12/#13).

The native model and its source markup are protected by the trusted backend.
This experiment does not modify production Xim/BIXML, nor does an actual
LLM call/test occur at this stage.
