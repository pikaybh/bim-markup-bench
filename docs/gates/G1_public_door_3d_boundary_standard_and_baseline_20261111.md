# G1 #15 — IFC4.3 first-level boundary standard vs inherited 3D shell gap

**Date:** 2026-11-11 KST.
**Fixed source-only task:** DOR-DEL-DIR-A-001.
**Engineering verdict:** PRESERVED_SOURCE_3D_PRODUCT_SHAPE_AND_INHERITED_RELATION_GAP.
**Official BIM-Edit solve/score gate:** BLOCKED.

This is a narrowly versioned **post-hoc, non-LLM** research audit, not
an official evaluation, a complete IFC4.3 validator, an authorized benchmark
trial or a general BIM editing API. The fixed 36-case candidate population,
original IFC, benchmark GT files and previous v0.1/v0.2/v0.3 reports are
unchanged. The trusted G1 runtime introduced in PRs #91/#92 is also unchanged.

## 1. External source hierarchy and exact applicability

### buildingSMART normative semantics (IFC4.3, not BIM-Edit's scorer)

Authoritative entity description, IFC4.3.2.0:
https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcRelSpaceBoundary1stLevel.htm

This describes 1st-level space boundaries as a **closed shell around an
enclosed space** and allows overlapping inner boundaries for openings,
doors and windows. The boundaries may involve elements such as Walls and
Slabs (floor and ceiling). Its geometry guidance is at:
https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcRelSpaceBoundary.htm

The definitions distinguish a product's own IfcSpace geometry (a
separate representation) from geometric surfaces referenced by the
IfcRelSpaceBoundary relationship objects. The latter are NOT automatically
completed from the former merely because the product's mesh is closed.
Furthermore, source IFCs in different model views may have optional
logical-only relationships and nonuniform representations. Do not
treat this limited check as a global schema validator.

**Important source-type distinction:** The actual pinned IFC has 12
concrete **IfcRelSpaceBoundary** (base-class) objects whose Name is
"1stLevel". It has **zero** concrete
IfcRelSpaceBoundary1stLevel or IfcRelSpaceBoundary2ndLevel subclass objects.
Consequently the 1st-level conceptual closed-shell guidance is used to
explain *what would require further validation*, not to retroactively
assert the original author source violates an unverified schema/MVD.

### Public BIM-Edit benchmark definition (NOT a complete shell contract)

Official task card:
https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks

Research paper (HTML only, no PDF copied):
https://arxiv.org/html/2606.20146v3

For delete tasks the original paper defines evaluation from changed
elements/relationships against a reference model. The given frozen task
text names removal of a Door, its Opening, fill/void relationships and
requested Storey assignments. It does **not** explicitly command
generation of new floor/ceiling IfcRelSpaceBoundary objects or a
complete conversion of source relationships to an energy-analysis view.

The official evaluator's exact executable code/commit and policy for
this inherited 3D shell gap are **not verified**. On 2026-11-07 an
independent group reporting another BIM-Edit evaluation said they
reimplemented the scorer because the original implementation was not
public at the time:
https://huggingface.co/blog/ONESTRUCTION/construction-ai-leaderboard
(section "BIM-Edit"). This is corroborating dated third-party evidence,
not proof that official code can never be obtained. The original paper's
claim of an accompanying code release and this third-party report
should remain distinct pending an identifiable canonical source/CLI.
The G0 official scorer Issue #4 remains open.

**Policy decision for this audit:** never create missing horizontal
IfcRelSpaceBoundary objects just to satisfy an inferred official
evaluation or to mask an incomplete original IFC. Keep task outcomes
labeled source-relative and officially unscored.

## 2. Native IFC source and actual D0/I0 result comparison

Original frozen public IFC SHA-256:
170d9ed9c10a31d86c3ff2207a450fd552166af21472486f11004f6e2b14defb

Original public task instruction SHA-256:
8dc59cbf741dbbf626843eebd91972197fa9ff0b9cbea251d6b9a8d8cd0a752a

Original source consists of **two rectangular IfcSpace product solids**
and 12 separate first-level-named SpaceBoundary relations.

| Native check | 65 m2 IfcSpace | 83 m2 IfcSpace |
| --- | ---: | ---: |
| Product mesh vertices | 8 | 8 |
| Product mesh triangles | 12 | 12 |
| Distinct triangle mesh edges | 18 | 18 |
| Edge manifold and orientation | closed, oriented | closed, oriented |
| Floor product-mesh triangles | 2 | 2 |
| Ceiling product-mesh triangles | 2 | 2 |
| World height | 3.048 m | 3.048 m |
| Enclosed product mesh signed volume | 198.120 m3 | 252.984 m3 |
| Floor AND ceiling product cap areas | 65/65 m2 | 83/83 m2 |
| Original 1st-level relation surfaces, vertical/horizontal | 6/0 | 6/0 |
| D0/I0 output 1st-level relation surfaces | 5/0 | 6/0 |
| Wall XY perimeter | closed | closed |
| Product-mesh shape before/after | identical in both arms | identical in both arms |
| Missing horizontal boundary surface coverage | 130 m2 | 166 m2 |

These horizontal coverage values describe the two product-mesh cap
areas for which there are **no corresponding explicit horizontal
IfcRelSpaceBoundary surfaces**. This is a geometric comparison, NOT
a mandated number of new relations: different model views and boundary
partitioning policies can represent floor/ceiling in multiple ways.

**Conclusion:** The existing IfcSpace product geometry is a closed,
oriented mesh, but neither original nor output has a *closed shell
expressed through the first-level-named SpaceBoundary connection
surfaces*. The missing floor/ceiling relation coverage is a SOURCE
condition, unchanged in D0 and I0.

Deleting the Door-associated auxiliary boundary leaves 2→2 Room objects,
two unchanged XY wall loops, two unchanged product solids, 12→11 total
boundary relations, and no invented horizontal boundary. This does not
prove benchmark-author success or normative completeness.

## 3. Trusted source-only witness / regression

New evaluator-free, model-hidden witness:
tests/oracles/python/public_space_shell_gap.py

The checker:
1. Pins source SHA and parses IFC4X3 from a trusted local copy.
2. Extracts real IfcSpace world-coordinate triangulation with IfcOpenShell.
3. Requires single connected, oppositely oriented, edge-manifold
   triangular closed product mesh; nondegenerate faces; signed positive
   volume; and correctly sized floor/ceiling caps in this RECTANGULAR
   frozen source.
4. Checks the native SpaceBoundary connection surface geometry,
   distinguishing vertical extruded wall/door/window patches from
   absent horizontal relation surfaces.
5. Requires the original source's two rooms, geometric box volumes and
   all product vertices be preserved after deletion, with the previous
   independently checked 2D wall-ring result.
6. Emits only aggregate, redacted source-relative facts and explicit
   negatives; never uses task.target, grading metadata, hidden GT IFC
   or a scored model output.

tools/verify_public_door_3d_shell_gap.py runs the source-only witness
for BOTH temporary D0 and independently authored I0 native IFC files
via the existing **optional trusted observer**; the previous v0.2
default and v0.3 report behavior are not changed.
It validates per-Room observations across both arms.

tests/test_source_space_shell_gap.py includes the actual pinned source,
paired candidate proof, baseline vs output relation/shape distinction,
invalid original source hash, missing/invalid result IFC, altered
IfcSpace volume/representation, missing wall boundary, nonvertical
connection geometry, manufactured extra boundary, sanitation of
report and official-score hard blocking. All tests use non-billed
local source-only IFCs; no large asset fetch or inference.

This check is **not** inserted into a tested LLM tool list. It is also
NOT applied as a new G1 official pass criterion: a source model
already missing first-level floor/ceiling relations would otherwise
be marked a task failure for a baseline defect unrelated to the
published deletion instruction.

## 4. Reproduction

In the Windows research repository, on an already present pinned public
IFC source cache:

    $env:PYTHONUTF8='1'
    .\.venv\Scripts\python.exe -m unittest tests.test_source_space_shell_gap -v
    .\.venv\Scripts\python.exe -m tools.verify_public_door_3d_shell_gap --output-json reports/g1_public_door_inherited_3d_shell_gap_20261111.json
    .\.venv\Scripts\python.exe -m unittest discover -s tests -q

The CLI returns **exit 2 by design**. The output evidence is write-once.
For replay use a new report filename.

Evidence:
reports/g1_public_door_inherited_3d_shell_gap_20261111.json

Evidence SHA-256:
395167984d6abce4f87e0b125a056b37e43d304b2353acc18083e9f25f16c7ff

## 5. Remain blocked; what would change the decision

- Obtain a verifiable original BIM-Edit executable scorer source/commit,
  terms and exact scorer entrypoint; verify official topological behavior
  offline against author-provided examples in a strictly isolated grader,
  with no GT leaked to D0/I0.
- Identify an explicitly prospective, agreed *IFC4X3 view-definition*
  that actually requires closed full 3D first-level space-boundary
  relations for this task family, distinguishing product solid closure.
- Only then consider a **new separately versioned and justified**
  floor/ceiling boundary-generation capability, if such editing is
  actually required in the study. Never derive new relations/IDs or
  thresholds from hidden GT or silently alter the preregistered
  sample population.
- Continue independent D0/I0 geometry/semantics tests and G0 file-level
  rights, G2 matched sandbox/context and G3 budget gates.

**Scientific outcome:** inherited 3D relation-shell completeness is
not certified, but no new 3D spatial-shape damage or missing horizontal
relationship surfaces were introduced by this Door deletion. No official
tasks scored, no LLM calls, no causal superiority claim.


### Recorded actual test execution

- Targeted G1 shell-gap + current Door/SpaceBoundary regression:
  **47 tests, all pass** (15.307 seconds).
- Repository-wide Windows regression:
  **622 tests, 601 pass, 21 skips, zero failures** (307.736 seconds).
- Python syntax compilation and Git diff whitespace check: pass.
- Negative test fixtures detect malformed source/result, source SHA
  changes, altered Room solid volume/representation, missing retained
  wall boundary, nonvertical relation surface, and fabricated new
  boundary. No private GT or model code is used.
