# v0.48 — Original four native IFC source semantic acceptance research

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/211
**Stacked base:** v0.47 Draft PR #210, frozen exact commit a9a0a5c4ba4387995ca38543884fdbcb4705e7f6.
**Published original population:** 45 tasks (15 CREATE / 15 UPDATE / 15 DELETE), 31 distinct exact source IFC SHA-256s. v0.48 includes exactly four original tasks, not the other 41.
**Frozen prior v0.47 report SHA:** cf1d37bf84fe744921989affc8b524e296c4d3b38731601513fd1b9fa95a44aa.
**Frozen prior v0.46 report SHA:** beab50998c1f2f984342cf784fe910adc384752a16b8f0eed40623421c38509f.

## Purpose, independence, validity boundary

The v0.47 pilot demonstrated original IFC4X3/mm source information and edit authority parity for four restricted XML/Python typed operations, including byte-identical native IFC candidate writes. However its illustration edits were intentionally not answers to the exact original public questions.

v0.48 adds a **separately implemented native geometry semantic predicate** for four unchanged original published public tasks and original source IFCs. This is an explicit *research-defined physical semantic eligibility gate*, NOT the original BIBIMBAP author grader, private hidden ground truth, a benchmark task score, a paid model trial or a claim of unrestricted original Python/IfcOpenShell authority. The new semantic checker does NOT import the v0.45 original native writer/compiler, independent v0.45 source-conservation oracle, private original grader or its developer positive control generator. Both independent conditions must pass externally before calling a candidate research-eligible: (A) unchanged prior independent v0.45 true native source and physical edit scope oracle, and (B) new independent v0.48 original question physical semantic oracle.

The original author code/data/hidden GT, all original public task question/source SHA pins, other 41 tasks, v0.45-v0.47 freeze files, existing default runner, research main, Stash and BIXML/Xim product remain untouched.

## Critical source units and geometry admissibility

The original IFC native length units are **millimetres** with native source unit scale 0.001. But IfcOpenShell geom.create_shape(settings with USE_WORLD_COORDS=True) returns **world physical mesh vertices ALREADY IN METRES**. Dividing these generated vertices again by 1000 yields false results. The original representation's placement coordinates, when read separately with IFC API, can remain in millimetres; only those values require the original unit conversion.

The predicate is deliberately narrow. Each relevant IfcSlab and IfcColumn must be a real **axis-aligned, closed rectangular prism**, with exactly 8 physical world vertices and 12 nondegenerate triangular faces, all eight distinct 3D bounds corners, precisely 18 undirected triangle edges each shared twice, two triangles on each of six planes and independently verified exact physical area coverage. Non-box, rotated, clipped, non-manifold, unrenderable or missing physical geometry is rejected. No generic rule is inferred merely from a loose AABB. Disclosed geometric tolerance is **0.0001 metre = 0.1 mm**, positive XY overlap above 0.1 mm in both horizontal axes. Neither this threshold nor the original4-specific rectangular-prism restriction is claimed as equivalent to the author private scorer.

## Exact original four native semantic predicates

| Original public task | Source-derived physical research acceptance |
| --- | --- |
| geometry_test_14 (UPDATE) | One original IfcSlab GUID preserved. Exactly one real horizontal world prism dimension increases; the other dimension and native thickness/level remain unchanged. Actual physical XY dimensions must form a square to within 0.1 mm. Original slab not already square. |
| geometry_test_15 (UPDATE) | All four original IfcColumn GUIDs and physical sizes/Z retained. Exactly one true Column centre moves in world XY. Its output four world XY centres have exactly two distinct X and two Y coordinates, occupying each of four genuinely nondegenerate rectangle corners once. |
| topological_test_11 (UPDATE) | Both source native Columns increase actual world height; their TOP faces must exactly touch the **SPECIFICALLY PUBLIC QUESTION NAMED** upper original IfcSlab UNDERSIDE with positive XY contact area. No column base/XY move or slab geometry change. Source named upper slab underside is 2.6952m; both columns initially stop at 1.5m. An overly tall Column intruding into slab does NOT count as exactly touching its underside. |
| topological_test_17 (DELETE) | Original 10 Columns: identify true original physical bottom-contact with SPECIFICALLY NAMED lower original IfcSlab TOP face and positive overlap area. Keep all and only the five source touching lower Columns, unchanged; delete all and only five upper non-touching Columns; preserve both Slabs. Separately check original spatial Storey containment agrees EXACTLY with original physical contact grouping. |

**Original topology caveat:** the actual source for topological_test_17 has **no Column–Slab IfcRelConnectsElements relationship**. Inferring that all ten Columns are unrelated because such an explicit relation does not exist would be invalid. Five lower Columns are in physical contact with the named ground Slab top; five upper Columns are not; their original IfcRelContainedInSpatialStructure matches precisely. This is a defensible original-public-source interpretation, not proof that the paper's hidden author scorer uses the same interpretation.

**Non-uniqueness caveat:** geometry_test_15's original source has MORE THAN ONE physically valid one-Column move that forms a rectangle. The original English question does not name a specific target Column GUID. A correct research geometric predicate accepts any of these single-Column rectangular arrangements, not one hidden presumed GUID; the developer control generator deterministically picks one.

## Real two-arm physical IFC candidates, positive and negative controls

The separate developer control generator reads only **original public source IFC geometry, exact public question text and source IfcRelContainedInSpatialStructure**, never the author's hidden scorer. It produces one research-semantic-POSITIVE physical edit per task. Each positive is submitted via BOTH actual model-facing v0.47 restricted XML and restricted Python typed native-edit sessions (two distinct native candidate IFC files), verified by existing independent v0.45 source-preservation native physical oracle, then separately checked by new v0.48 research semantic checker. The native outputs are **byte-identical for each original task**. No positive control is injected into a model prompt as ground truth.

The NEGATIVE control is the previous deliberately illustrative non-solution native edit from v0.45/v0.47 for each task: it is accepted by the trusted writer and independent source-preservation physical oracle but rightly rejected by the new semantic predicate. The paired XML/Python native outputs are still byte-identical. This explicitly distinguishes *valid native IFC edit* from *actual requested original physical relationship*.

| Measure | Actual verification |
| --- | ---: |
| Positive (research physical semantic pass) controls | 4/4 |
| Negative (research physical semantic fail) controls | 4/4 |
| Actual paired restricted XML/Python native IFC source experiments | 8 |
| Newly emitted real original IFC4X3/mm candidates | 16 |
| Existing independent native source-conservation physical oracle passes | 16/16 |
| Byte-identical native IFC candidate pairs | 8/8 |
| Original question and source exact SHA-pins validated | 4/4 |
| Total model-facing source read tool calls | 8 XML / 8 Python |
| Total model-facing native edit tool calls | 8 XML / 8 Python |
| Original author evaluator invocations | 0 |
| Paid LLM / Docker executions | 0 / 0 |

**Frozen machine report:** reports/bibimbap_v048_original4_semantic_positive_negative_native_controls_20261117.json
**SHA-256:** ca5f365198bff4f92b14031690b30338d3000adfd70b39c2be4471c9a32d7e08

This report is exclusive-create, byte-identically reproducible from exact original author/data inputs, contains all eight actual native paired candidate IFC hashes, exact original source/question provenance and separate physical semantic observations, and cannot be overwritten. Previous v0.45, v0.46, v0.47 report SHA remain frozen.

## Stress checks, limitations and next checkpoint

Focused v0.48 tests exercise original 45/31 source/question integrity, independent source and candidate IFC reopen, native-mm world-metre conversion, real closed prism manifold proof, changed source/question and named target slab rejection, invalid/rotated/corrupt or missing native candidate fail-closed behavior, positive four tasks and negative four tasks, byte-reproducible report, and physical near-miss counterexamples: 2mm/0.2mm slab still not square, 1mm column centre discrepancy, 1mm gap to upper slab and 1mm penetration into it, overly tall columns, deleting four rather than all five unrelated columns, deleting a wrong related column, deleting six columns including a related one, order-invariant correct deletion set and previously preserved non-target physical IFC state under independent v0.45 source scope oracle.

**Not proven:** original private evaluator/hidden GT equivalence; real paid model original-question success rates or accuracy; unrestricted Python/IfcOpenShell tool equivalence; one unified full 45-task native write authority; identical input token cost/tool interface ergonomics. Do not report these research-defined developer controls as genuine original published benchmark scores.

**Next v0.49:** prospectively preregister frozen original 4-question model instructions, fixed 25-tool-call budget and token/cost accounting; keep independent source-native semantic checker BLIND from model tools; assess whether author original evaluator can be separately invoked without leaking private GT; explicitly label restricted XML-vs-restricted Python pilot separately from original unrestricted Python/IfcOpenShell tool-bundle comparison. Only then run paid paired LLM trial or report original author benchmark scores.

### Reproduce in isolated Windows research Worktree

    $base = 'D:\문서\D__1_Projects\202611'
    $py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
    & $py -m tools.audit_bibimbap_v048_original4_semantic_controls --author (Join-Path $base 'bibimbap-author-upstream') --data (Join-Path $base 'bibimbap-author-data') --progress
    & $py -m unittest -q tests.test_bibimbap_v048_original4_semantic_native_oracle

The scripts create temporary physical native IFC candidates in independently isolated trial directories only; never modify the original public IFCs, author evaluator, research main or prior reports. Remain Draft, stacked on v0.47; do NOT merge main without independent review.
