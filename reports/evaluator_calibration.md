# G2 synthetic IFC evaluator calibration — November 7, 2026

**Calibration status: 17/17 own synthetic fixtures matched the prewritten
v0.1 check conditions. This is NOT BIM-Edit official scoring validation.**

Reference set: own IFC4X3 synthetic wall/window/room fixture, source
SHA256 10d57d3eeb6e50fb51493b03d7cb508d57eadeb76719afaeb71fa6658c3ecf58.
Scorer: independent-ifc-three-axis-v0.1, IfcOpenShell 0.8.4.post1,
surface sampling 384 points, seed 2607 and 1e-6 meter matching tolerance.

The expected conditions are recorded in
tests/evaluation/fixtures/calibration_expectations_v0.json. They were
written as a post-implementation synthetic regression specification;
they are **not** prospective preregistration for official BIM-Edit trials.
Calibration creates temporary IFC variants from the own source fixture and
never modifies input IFCs.

## Known synthetic positives

- Identical correct GT: Geometry 1.000, Semantics 1.000, Topology 1.000,
  strict pass.
- Create one physical new Wall with different valid predicted GlobalId:
  1.000 / 1.000 / 1.000, strict pass under derived geometry alignment.
- Delete the intended existing Window without unexpected native
  relationship loss: 1.000 / 1.000 / 1.000, strict pass.

## Seeded negative outcomes

- Wrong source wall height: Geometry 0.944, strict failure.
- Translated wall 1m: Geometry 0.885, strict failure.
- Rotated wall 45 degrees: Geometry 0.288, strict failure.
- Reassign target Wall to Slab: Semantics 0.500, Topology 0, strict failure.
- Omit reference Pset: Semantics 0.667, strict failure.
- Remove wall void relation: Geometry 0.903 and Topology 0; this
  physically changes the meshed wall as well as its graph.
- Remove source space-boundary relation: Topology 0.
- Delete unrelated Door: Semantics 0.500, Topology 0, collateral flagged.
- Edit unrelated Column instead of target Wall: Geometry 0.944,
  collateral flagged.
- Replace target GlobalId: Geometry and Semantics 0.
- Invalid IFC bytes: explicit INVALID_OUTPUT_IFC and all axes 0.
- Create with no new target: all axes 0.
- False deletion: all axes 0.
- Change project length unit unexpectedly: explicit
  BLOCKED_IFC_UNIT_MISMATCH with null axes, not a fabricated score.

These values apply only to this pinned small IFC and this independent
scorer. They MUST NOT be interpreted as official benchmark success rates.

## Tolerance and numeric sensitivity

A frozen translational scan at offsets 0, 1e-7, 1e-4, .01, .1, .5 and 1m
produced monotonically decreasing geometry scores from 1.0 to 0.885.
A rotational scan at 0, 15, 45 and 90 degrees decreased geometry scores
from 1.0 to approximately 0.212. The exact results are stored in
reports/evaluator_calibration.json and replayed in unit tests.

The independent geometry metric is normalized and therefore small but
nonzero offsets can still yield near-perfect numerical geometry values;
other axes and collateral checks can nevertheless prevent strict pass.
Changing project units is blocked rather than silently accepted; full
equivalent models expressed in other unit systems are not yet calibrated.
Alternative triangulations, complex rotated solids, full IfcSpace geometry,
multiple new targets, Hungarian OBB matching and the official scorer remain
limitations.

The paper's rounded illustrative component combinations are checked
only using the paper-formula scalar functions:
(1,1,.47) -> .823333 and (.38,.72,1) -> .7000. This does **not** validate
official geometry/semantic/topological reconstruction from actual paper IFCs.

## Related evidence and release status

- reports/arm_capability_matrix.csv: 108 combinations of target class,
  operation, category and scene. The 324 pinned public metadata tasks
  are partitioned as 246 statically unsupported and 78 source-dependent
  unverified. Official D0/I0 scored/verified tasks: **zero**.
- reports/G2_readiness.json: **BLOCKED_FOR_LIVE_MODEL_PILOT**.
  Official model inputs/GT IFC content, private scorer parity, actual OS
  isolation and real provider billing controls are not verified.
- No paid provider calls, arbitrary generated Python, official task
  scoring, server changes, Xim or production BIXML changes were performed.

To reproduce locally:

    .venv/bin/python -m tools.audit_bim_edit --fetch-metadata-only
    .venv/bin/python -m tools.calibrate_g2
    .venv/bin/python -m unittest tests.test_scorer_calibration -v
    .venv/bin/python -m tools.calibrate_g2 --enforce

The enforced gate MUST return exit code 2. Its report is deliberately
separate from a true official evaluation success metric.
