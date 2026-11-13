# BIBIMBAP v0.11 — forensic audit of four frozen partial D0 author scores and all 45 original public cases

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/136

**Date:** 2026-11-13 (Asia/Seoul). Independent experiment `pikaybh/bim-markup-bench`, NOT production Xim/BIXML. This is **post-hoc forensic analysis of historical developer D0** and source-only census, **not a new blinded research evaluation**, a score improvement, a new LLM run, or an original 45-case native capability/parity claim.

**Nonnegotiable controls:** Original public BIBIMBAP author source pinned to `667004e16bd38fd7d538bcee56191465429fd975`, source dataset pinned to `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`. Original scorer is not modified or replaced. Existing v0.1–v0.10 compilers, original IFC source files, all v0.8/v0.9/v0.10 historical D0 original-author reports/partial scores, and real GPT-6 Luna 45-task scores stay byte-identical. New paid/provider/model calls **0**, API cost **$0**. No model-facing or candidate authoring access to hidden target/ground-truth solution IFC. Any diagnostic source code imported from the public original author grader is **analysis-only after candidate SHA verification**, never compiler/model training code.

## Strong validity gate: forensic analysis starts ONLY on byte-identical frozen D0 artifacts

`tools/audit_bibimbap_v11_metric_forensics.py` reconstructs the same four previously fixed XML edits from their **existing v0.8/v0.9/v0.10 source-only fixture implementations**, not newly authored/retuned XML. For every case:

1. Verify the previous unmodified Git-stored D0 report's **entire SHA256** and expected original source IFC & public question SHA.
2. Re-read original immutable millimetre IFC and regenerate the same native-schema-preserving, metre-normalized source copy. Assert normalized source SHA equals the prior D0 report's SHA.
3. Generate the *exact same original frozen whole declarative XML state* using the prior corresponding script, compile with the **unchanged** v0.8/v0.9/v0.10 trusted compiler, verify candidate's native IFC **full-file SHA** equals the earlier frozen candidate.
4. Run the preexisting **independent IFC-only native oracle**, then convert a separate candidate copy to original millimetres and verify **full-file SHA** matches the original frozen candidate's exact millimetre IFC SHA.
5. **Only after these gates** inspect the *public* original-author **metric subcomponents** on the frozen native IFC pair. These operations only inspect IFC/score implementation; **do not change XML, native IFC, hidden GT, official metric or original D0 score**. No original-author rerun/feedback is used to create a candidate.
6. Save **sanitized, deterministic** JSON with source/question/candidate hashes, public scorer subcomponent booleans, exact native IFC oracle outcome and cause category. No original IFC binaries, original/private scorer source or hidden solution artifacts are copied into the repository.

This is a forensic decomposition of published original-author test behavior, not an independently blinded final correctness verdict. A native IFC structurally safe edit can still violate another valid semantic requirement, especially collision avoidance.

## Four frozen original-author discrepancies — now explicitly explained

| Public BIBIMBAP task | Original D0 score (unchanged) | Exact original evaluator component outcome and why | Interpretation |
|---|---:|---|---|
| `geometry_test_04`, IFC2X3 native `IfcSpace` | **0.916675** | Original author `check_spatial_containment = 0`, while `check_clash_integrity = True` and `check_elements_preserved = 1`, so the three-way integrity average is **2/3 ≈ 0.6667**. The true new native `IfcSpace` has an `IfcRelAggregates` parent under the original `IfcBuildingStorey`, but is NOT a direct member of an `IfcRelContainedInSpatialStructure`. | A **specific relationship convention mismatch** between native spatial decomposition and the original create grader's direct-containment expectation. This does not imply the author criterion should be ignored or that any IF2X3 Space aggregation is universally sufficient. |
| `geometry_test_14`, locally rotated IFC4X3 `IfcSlab` square | **0.666667** | Original author dimensions=1, integrity=1, **right_location=0**. Prior source-only developer XML change increased the world Y side from **8.5 to 10.0m** while keeping the original **lower Y edge fixed**; the native world bounding-box center consequently moved **+0.75m**. Original author's `_location_ok` requires **old/new x, y and z bbox centers to match** within original public `CENTER_TOLERANCE=0.05`. | A genuine **candidate geometry placement requirement mismatch**: anchoring an edge while expanding changes the center, even though the shape is a correct square and native STEP/Roots are preserved. Not a data corruption or original evaluator malfunction. |
| `topological_test_11`, two shared-mapped original IFC4X3 Columns meet upper Slab | **0.666667** | Original author dimensions=1, location=1, **integrity=0**. Public `check_integrity` reports `non_target_elements_unchanged=True` but `no_new_clashes=False`. Original geometric collision pairs count **1**; frozen candidate count **4**; **three new pairs**. Two pair the extended original Columns to publicly named upper Slab `0dxtXCDSn2mfP92h$AiPMM`, the third is another original Wall–Column pair. | A **real original-author collision rule failure** after native shared-type Column geometry extension. Independent source STEP/Root and other-product preservation does NOT satisfy the author no-new-clashes rule; full score is not appropriate. Some contacts have a small geometric overlap; new collisions must not be ignored. |
| `topological_test_17`, delete original non-contacting IFC4X3 Columns | **0.500000** | Original author `object_not_exists=1` but `integrity_constraint=0`. **ALL FOUR** public per-deleted-Column checks (`wall_connections_deleted`, `spatial_containment_deleted`, `openings_deleted`, `aggregations_deleted`) pass for **ALL 5** source-only deletion targets. However public `non_target_elements_unchanged` is **False**: deleting exactly five Columns via source-safe native ownership closure also deletes **35 rooted dependencies** that are not among the five Column GUIDs: **15 sole-owned IfcPropertySet, 15 IfcRelDefinesByProperties and 5 exclusive IfcRelDefinesByType**. The original author's generic root guard excludes only the five target Column GUIDs from its non-target inventory, so these 35 owned reference GUIDs are counted as missing. | An **explicit source-dependent root-retention scoring disagreement**. The independent native ownership-closure rule permits deletion of target-only Psets and type edges without dangling references, whereas the untouched original author check demands the non-target Root GUIDs remain. The *author score remains 0.5*, and this is NOT proof the scorer is wrong or that the implementation satisfies full original task integrity. |

**Original frozen D0 scores are not replaced.** The table diagnoses mechanics; it does not request rewriting IFC candidates to maximize already-observed test scores. Author score differences must be included transparently in any future paper.

Relevant original public source metric functions (read only): `data/tests/utils/create_utils.py::check_spatial_containment`, `data/tests/utils/create_utils.py::check_elements_preserved`, `data/tests/geometry_test_14.py::_location_ok`, `data/tests/integrity_utils.py::check_integrity`, `data/tests/integrity_utils.py::non_target_elements_unchanged`, `data/tests/delete_integrity.py::run_delete_integrity_check`. No original source files were modified.

## 45 original public edit tasks: comprehensive source/metadata census, NOT current operation support

`tools/audit_bibimbap_v11_full45_ledger.py` reads **every original public editing task in the pinned 45 cohort**, verifies individual source IFC bytes/question hashes, checks exact original native IFC schema and counts original rooted products (including IFC class names), and reports the previously frozen v0.1 read-only source projection gate **as historical**. The original public task denominator remains 45, including all unsupported, partial, untested, and previous model failures.

| Static frozen original cohort observation | Number |
|---|---:|
| Total original public editing tasks | **45** |
| Original native IFC4X3 | **42** |
| Original native IFC2X3 | **2** |
| Original native IFC4 | **1** |
| *Historical v0.1* XML source read-only projection previously PROJECTABLE | **36** |
| *Historical v0.1* XML source read-only projection previously BLOCKED | **9** |
| Exactly frozen **v0.8–v0.10 source-only developer D0** original-author full marks | **3** |
| Frozen **v0.8–v0.10 source-only developer D0** original-author partial grades | **4** |
| Remaining original tasks **not evaluated in v0.8–v0.10** (may have v0.1–v0.7 evidence) | **38** |

**Important distinctions:** Historical projectability = ability to **read** a source as then-designed XML, not to perform the requested native edit. Three fixed source-only developer D0 full marks are **not three new LLM passes**; older v0.1–v0.7 developer D0 results have their own evidence and are neither counted as a new v0.8–v0.10 result nor marked failed. The 38 unassessed cases are explicitly **NOT ASSESSED BY THESE LATER VERSIONS**, not "38 unsupported" or "38 failed." This metadata-only census does **not** call v0.8/v0.9 projections for all 45 and must not be described as successful updated source projection for 45. True 45/45 source+edit parity is **NOT PROVEN**, and the Python control arm's full original IFC access is still a capability advantage on unimplemented XML operations.

The latest static ledger is **not a native compiler coverage percentage**, not a normalized success rate and not a causal comparison with a published BIBIMBAP/Python score.

## Repro and automated regression

Fixed forensic audit report:
`reports/bibimbap_v011_frozen_D0_public_author_metric_forensics_20261113.json`
SHA256 **`774cbf90a7e082038f91c2aace7203734aa76dc2712a76f2751e68b0ec77f134`**.

Full original 45-case source/IFC static census report:
`reports/bibimbap_v011_full45_original_source_census_20261113.json`
SHA256 **`21eaef85e23c4fc34e455b1829d8f9614ac24538b6fff480be9dc16ac66cadce`**.

Scripts:
`tools/audit_bibimbap_v11_metric_forensics.py` and
`tools/audit_bibimbap_v11_full45_ledger.py`.

Tests:
`tests/test_bibimbap_v11_metric_forensics.py`,
`tests/test_bibimbap_v11_full45_ledger.py`.

```powershell
$base='D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue136-metric-diagnostics-v011')
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$author=Join-Path $base 'bibimbap-author-upstream'
$data=Join-Path $base 'bibimbap-author-data'

& $py -m unittest tests.test_bibimbap_v11_metric_forensics tests.test_bibimbap_v11_full45_ledger -v

# Output files must NOT already exist; prior evidence is immutable.
& $py -m tools.audit_bibimbap_v11_metric_forensics --author-repo $author --dataset $data --output-json 'results/NEW_UNUSED_v11_forensics.json'

& $py -m tools.audit_bibimbap_v11_full45_ledger --author-repo $author --dataset $data --output-json 'results/NEW_UNUSED_v11_full45_census.json'
```

The **18/18 new v0.11 tests** verify all four exact prior native candidate hashes and prior D0 score hashes, original scorer subcomponent decomposition, independent original native oracles, public 45-source original hashes, no duplicate 45 IDs, honest native schema counts, no hidden target usage, negative regression tests that reject corrupted prior frozen D0 evidence, and deterministic output under repeat invocation. **Full v0.11+v0.10+v0.9+v0.8+v0.7+v0.6+v0.5+v0.4+v0.3/v0.2 and original full45/paired25/native-core/initial compiler regression: 239 tests run / 237 PASS / 2 optional SKIP / 0 FAIL (169.718 seconds).** Both complete v0.11 JSON reports were regenerated after a clock-second delay and their complete SHA256 hashes are **byte-identical to the pinned files**. Original data, author scorer and prior reports are never edited.

## Next priority after v0.11

**First:** prospectively **freeze a true 45-case end-to-end source projection + semantic write capability matrix** rather than treating mere projected read-only files as edit support. For every original task retain source schema, original public IFC/question hash, required native operation family, projected read-view status, compiler-operation status, independently tested native D0, matching Python I0, original author scorer result, strict full-task pass, and explicit unsupported reasons. Do not give special capability credit to a task merely because one source object projects; fail-closed unsupported cases stay in the full denominator.

**Second:** Any future changes to IFC4X3 source-clash mitigation, IFC2X3 space containment, slab center-preserving reshape or deletion's Pset/type lifecycle must be registered as *new development variants informed by observed evaluation*, **NOT** an untouched blind holdout. Do not replace historical candidate/source/result or claim retroactive full marks; future tests require independent holdout or prospectively frozen tasks before scoring.

**Third:** Only after independently qualified common-supported D0/I0 backend coverage, secure **new explicit paid LLM experiment budget approval** before matched 25-call or full original 45 task model trials. Original published author/Python baselines under different model/runtime conditions are context, not equal-condition causal evidence.
