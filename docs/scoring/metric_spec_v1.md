# BIM-Edit paper-defined metric contract — working notes, NOT an official scorer

Source: https://arxiv.org/html/2606.20146, Sections 3.2, Appendix E. This document contains **definitions for an independent implementation to follow**, not a validated executable benchmark scorer.

## Task and edit graph

Three models per trial:
- M0: immutable input IFC.
- M*: hidden reference/ground truth IFC.
- M': predicted IFC written by either authoring arm.

Compute G*_delta = diff(M0,M*), G'_delta = diff(M0,M') on affected nodes and relations. Create: new entities; update: final edited target state including delete+recreate under changed GUID; delete: removed entity and dependent relations. **Never score the entire unchanged model** instead of delta. Target GUIDs and reference model are grader-only and NOT passed to the model.

## Component metrics (all in [0,1])

### Geometry, Eq. 5

- Extract actual IFC edit geometry; uniformly sample mesh/surface points across affected entities.
- Up to 4,096 points per edited entity, 16,384 per edit overall, with at least 256 points per object where feasible; allocate proportionally to surface area.
- Let CD_med be the median bidirectional nearest-neighbor Chamfer distance between aggregate reference/predicted clouds; let D be the diagonal of their union axis-aligned bounding box.
- S_geo = exp(-5 × CD_med / D).
- Additional non-headline diagnostics: OBB and AABB IoU, voxel IoU 0.05m at 128³, point F-score at 1% D, Jensen–Shannon divergence of voxel occupancy, Hausdorff distance.
- **Unknown:** behavior for both-empty edit clouds, D=0, mesh errors, deterministic seed and nearest-neighbor implementation. Current scalar helper refuses invalid/degenerate D; it does not invent an official fallback.

### Semantics, Eq. 3

- Hungarian one-to-one matching of edited entities by oriented bounding-box IoU; discard pairs below IoU 0.05.
- For each matched reference entity: average class exact-match (0 or 1) and fraction of task-relevant matching properties (0 to 1).
- Relevant numeric properties: relative tolerance 5%, excluding Tag, Description and LongName. Exact property-key inclusion rules are not fully specified in the paper and require official code.
- Unmatched references score 0; task semantic score = sum pair scores / reference edited entity count.
- For delete, semantic score is 1 if intended entity removed, else 0.
- **Unknown:** tie-breaking, alternate valid properties/material values, tolerance at zero and missing attributes.

### Topology, Eq. 4

- Graph nodes = structurally relevant IFC entities; relation edges cover spatial containment, aggregation, space boundaries, voids, fills and element connection.
- Reference edit = symmetric difference of node/relation sets between input and GT. Predicted edit = symmetric difference between input and result.
- Align nodes using greedy bipartite matching based on IFC class and local-placement proximity. Relation IDs are then compared only after alignment.
- S_topo = 0.3 × F1(edited nodes) + 0.7 × F1(edited relations).
- Exception: reference has NO topology edit: S_topo = 1 if prediction also has none, 0 otherwise.
- **Unknown:** exact alignment score/threshold and F1 conventions for empty sets.

### Final + strict pass

- Final mean S = (S_geo + S_sem + S_topo) / 3.
- Strictly solved if EACH component is **at least 0.98**. High final mean alone is NOT a pass.
- Origin tags mandatory: paper-formula-only / independent-reimplementation / official.
- For invalid IFC, leaked GT, unsupported engine geometry and missing scorer features: status must explicitly record failure/blocked under frozen protocol; never fabricate scores as official.

## Three illustrated arithmetic checks (paper-reported rounded components)

These are arithmetic checks from Appendix H, NOT recomputations from reference IFC:

| Example | Geometry | Semantics | Topology | Mean | Strict pass |
| --- | ---: | ---: | ---: | ---: | --- |
| H.1 door-opening translation (perfect) | 1.00 | 1.00 | 1.00 | 1.0000 | yes |
| H.2 wall-length resize (partial topology) | 1.00 | 1.00 | 0.47 | 0.8233 | no |
| H.3 wall-thickness resize (partial geom+semantic) | 0.38 | 0.72 | 1.00 | 0.7000 | no |
| H.4 window translation failure | 0.00 | 0.00 | 0.00 | 0.0000 | no |

Round values shown in the paper limit exact numeric reproduction. Actual geometry/graph tests are required before claiming evaluator equivalence.

## Planned scorer implementation order (Issue #21)

1. Pin actual IFC data, verify input/GT hashes and measure IFCSchema (sample real model is IFC4X3).
2. IFC edit graph diff and unchanged-object integrity, target matching.
3. Mesh sampling and median CD with fixed RNG, geometry numerical and tolerance tests.
4. OBB IoU matching / semantic property comparison, delete special case.
5. Typed topology relation graph, greedy node alignment, F1 node/edge and empty relation semantics.
6. Evaluate paper cached predictions and verify exact model/task component scores, or formally label independent.
7. Blind arm identity / reference output firewall; only then permit scored live model runs.
