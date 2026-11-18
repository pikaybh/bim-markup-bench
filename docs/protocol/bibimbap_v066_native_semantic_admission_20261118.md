# v0.66 / Issue #247 — STEP-independent native IFC preservation admission (bounded family)

**Status:** Research-only **offline engineering validity** under [Issue #247](https://github.com/pikaybh/bim-markup-bench/issues/247), additive to stacked Draft [PR #248](https://github.com/pikaybh/bim-markup-bench/pull/248), on v0.65 Draft PR #246. This is **NOT** a published author grader, not a blinded controlled LLM D/I result, not a claim of superiority, and not permission to transmit or run original IFCs through a provider. The BIXML/Xim product remains entirely separate and untouched.

## Problem and falsifiable invariant

The frozen v0.65 source-neutral Door/Opening gate requires **identical numeric IFC STEP entity identifiers** on every original entity. v0.66 first reproduced two false rejections under bijective STEP relabeling, even though the entire other STEP Physical File was byte-identical under exact inverse remapping. Numeric STEP labels identify entities **within one serialization**, not their semantic identity across a legitimately recreated IFC file. The old gate remains untouched as historical evidence.

The next candidate validator tests the narrower falsifiable property: **under the declared managed one-hosted-Door+Opening CREATE family**, the original source model's typed entity attribute/reference graph, rooted identity, schema, unrelated geometry and physical host-wall aperture must be preserved regardless of numeric STEP label assignment.

The result is a separate, *prospective candidate admission* function `tools/bibimbap_v066_native_semantic_admission.py::post_native_semantic_gate`, NOT a score used for an actual controlled study. It intentionally fails closed outside its bounded scope.

## Native source-preservation algorithm

1. Open the immutable SHA-pinned original IFC and a distinct candidate IFC. Verify same precise schema identifier and native length unit. Only original IFC2X3 or IFC4X3 with the represented planar Wall supported by v0.65 is in scope.
2. For every source and candidate native entity, compute **typed explicit forward-attribute fingerprints that do not include STEP numeric IDs**. Each reference contributes a label from the previous refinement round. Check multiset inclusion of *all* original entity fingerprints at depths **0, 1, 2, 4, 8, 16**. This spans anonymous property, representation, material, placement and relationship nodes, not only `IfcRoot`. An unchanged source graph must remain present; new entities can be added by the bounded operation.
3. Source numeric real attributes are rounded to **10 decimal places in their native units** before fingerprinting. This is a declared precision/tolerance compromise for real IFC2X3 and IFC4X3 writer/parser floating-point serialization noise. It is not exact real-number byte identity, and changes below this resolution may be indistinguishable. Negative fixtures change spatial geometry by at least 0.25 source length units and a reported width by 15%.
4. Independently require every original `IfcRoot.GlobalId` and class, unique Root GUIDs, no extra unpermitted rooted classes and exactly the five additions for a single Door/Opening, fill, void and storey containment. IFC2X3 new Roots must have valid OwnerHistory.
5. Starting from all `IfcRoot` instances, traverse forward references and refuse *additional root-unreachable anonymous entity counts by IFC class*. This catches extra orphan geometry, while allowing a different legal order or numeric STEP assignment. It does **not** establish arbitrary native graph isomorphism or legal alternative shape modeling.
6. Check physical IFC Door/Opening meshes, door inside opening, through-thickness Wall CSG volume reduction against source, new native door width/height in project metres, original other-product mesh bounding boxes/volumes, and the real host, `IfcRelVoidsElement`, `IfcRelFillsElement`, `IfcRelContainedInSpatialStructure` chain. Compare IFC validator findings against the source: no additional findings.
7. Compare **physical edit semantic digest** (source SHA + schema + original host GUID + Door/Opening absolute boxes + actual CSG cut) across the D original, reencoded D and independently executed Linux Docker I. This digest is *not* a task correctness or broad IFC semantic-equivalence claim.

The graph fingerprints represent a bounded, conservative source preservation check, not a formal proof of complete IFC graph equivalence. The physical geometry helpers and schema counter reuse trusted existing local IfcOpenShell libraries; this validation should **not** be described as an independent implementation of the full official/paper task scorer.

## Actual evidence (already developer-exposed inputs only)

All results are for only two previously inspected, source-SHA-frozen original IFCs:

| Original test ID | Schema | New D FULL | D FULL with all STEP IDs bijectively relabeled | Genuine pinned Linux Docker independent Python I | Native negative artifacts rejected |
| --- | --- | --- | --- | --- | ---: |
| `geometry_test_03` | IFC2X3 | PASS | PASS | PASS | 8/8 |
| `topological_test_05` | IFC4X3 | PASS | PASS | PASS | 8/8 |
| **Total** | **2 schemas** | **2/2** | **2/2** | **2/2** | **16/16** |

The genuine I source is an independently authored Python/IfcOpenShell script, *not* the direct XML compiler, executed against its own IFC clone in a **SHA-pinned local Linux Docker OS sandbox**. The same new native gate accepts the native physical result; cross-arm physical edit digest is equal for each source. No model generated the scripts or XML for this test. No new original author grader/GT was inspected.

Negative IFC mutations (each schema) include: change original Wall Name; mutate shared old OwnerHistory; modify old native anonymous geometric Cartesian point; alter an existing original IFC relation's metadata; add an orphan anonymous point; add an unauthorized new Root; change Door physical numeric width without matching geometry; and redirect an Opening void to a wrong original host Wall. Failures distinguish source graph mismatch, new orphan, new forbidden Root, numeric dimension mismatch and hosted geometry mismatch. No synthetically constructed positive uses an unsupported unseen task. All original IFC SHA values were unchanged.

**Frozen report:** `reports/bibimbap_v066_native_semantic_scope_20261118.json` SHA-256 **`f908cc10086f0fb00efee0d8651385d378ef50221b7d6eab00ad42df7441d49b`**.

## Reproduction (local only)

```powershell
$py = 'D:\문서\D__1_Projects\202611\bim-markup-bench\.venv\Scripts\python.exe'
& $py -m tools.audit_bibimbap_v066_native_semantic_admission --check
& $py -m unittest -q tests.test_bibimbap_v066_native_semantic_admission
```

The `--check` audit actually compiles two D native IFCs, reopens each under the new gate, bijectively relabels and rechecks each, executes two independent Python/IfcOpenShell Docker native candidates, verifies native physical semantic digests, constructs sixteen real negative IFCs and recomputes the entire JSON byte-for-byte. This run does not invoke a provider and never reads new unknown source geometries.

## What is still scientifically unproved

- Full legal IFC graph-isomorphism or alternate lawful geometry authoring strategies; legitimate *original source representation* modifications may still be rejected.
- General IFC4 (not IFC4X3), complex/curved walls, existing product moves, hosted Window assembly updates, deletes and arbitrary native representation types.
- An official unchanged original BIBIMBAP scorer/paper revision match, truly unseen test sources or independent audit of all source exposures.
- Per-original-IFC external transfer rights, matched LLM provider/model snapshots, actual billed D/I token and cost parity, or causal representation effects.

**Required next action:** broaden **source-neutral** declarative physical final states to at least one bounded real move and delete family, matching genuine independent Docker Python I on already developer-exposed sources, and audit whether the proposed source-preservation criterion itself needs an operation-scoped exception list. Do not weaken this gate globally or adapt it to each author's hidden target answer. No paid trial without independent rights / fairness / source-blind authorization.
