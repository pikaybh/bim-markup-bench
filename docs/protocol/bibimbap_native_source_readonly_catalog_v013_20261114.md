# BIBIMBAP v0.13 — Original native IFC source-faithful read repair & opaque Product reference XML

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/140

**Date:** 2026-11-14, Asia/Seoul. Independently versioned research-only `pikaybh/bim-markup-bench` tree. Absolutely **no Xim/BIXML production code** changed. Neither original public BIBIMBAP IFC nor pinned author scorer/dataset nor previous v0.1–v0.12 projection/compiler/code, older developer D0 source/candidates/scores and historical real GPT-6 Luna 45-task scores were modified. **No new paid/model/API requests ($0).**

## Evidence standard and distinction

v0.13 is **NOT** a general IFC-editing implementation. It provides two separate, deliberately different source representations:

1. **Safe partial typed XML** in the pre-existing v0.9 IFC4X3 or v0.8 IFC2X3/IFC4 original-native-schema XML namespace. Only actual original source objects satisfying the **existing unchanged source hash + strict geometry / source IFC topology binder/XSD** are present as typed editable-grammar elements. Removing an original typed projection node **does not delete its IFC source product**; the real IFC is retained byte-identically. This view remains only a *partial* native model, not a native source lossless roundtrip.
2. A NEW **read-only original native IFC source XML catalog** in namespace `urn:bim-markup-bench:original-native-source:readonly:v0.13`. Contains every native original `IfcProduct` GlobalId, IFC class, true original STEP ID, original Storey containment and `IfcRelAggregates` parent when present, exact native world triangulation vertex/triangle count + SHA256 + bbox (or explicit unavailable), and explicit original `IfcRelVoidsElement`, `IfcRelFillsElement`, `IfcRelContainedInSpatialStructure`, `IfcRelAggregates`, `IfcRelSpaceBoundary` endpoints with original rooted IDs. The catalog is marked `READ_ONLY_NO_COMPILER_AUTHORITY`; every Product and relationship states `compilerEditPermission=NONE_FROM_THIS_CATALOG`. No compact model mesh or original IFC entity is fabricated as a fake editable axis-aligned box. The catalog does **not** record all arbitrary original IFC relationships, material-type dependencies, representations or STEP fields and is not a lossless IFC serialization. **It cannot be passed to the trusted native XML compiler to mutate IFC.** Original IFC remains authoritative.

These are separate outputs returned by `src/runtime/experimental_v13_opaque_source.py::project_original_native_v13`, not silently substituted into historical old source grammars. Actual original schema is preserved (IFC4X3, IFC2X3, IFC4). Original IFC2X3/IFC4 use v0.8's separate schema and XSD; no invalid IFC4X3 relabeling.

## Actual original-hosted Opening diagnosis and strict read-view repair

Pinned source original files:

| Original public task | Actual source Opening outside native host Wall axis | Original source IFC world `offset` | Original Opening world mesh width | Host actual world axis length | Excess | Source original fill |
|---|---|---:|---:|---:|---:|---|
| `geometry_test_18` | `07NAHYposfcUjqlUhBJbQM` | 6.3m | 0.75m | 6.8m | **0.25m** | `1xzI3PuNvF1RRUjZb8YIV$` |
| `geometry_test_19` | `0glQxPaBwI0t3x8bVYfCFb` | 6.4m | 0.9m | 6.9m | **0.40m** | `1mRYVM4YfFFBRkcbz1hH$v` |
| `geometry_test_19` | `20UNRRDp_InaW8_dq7ad4F` | 8.2m | 0.9m | 9.0m | **0.10m** | `1mRYVM4YfFFBRkcbz1hH_L` |
| `geometry_test_19` | `2uqjQk25XmTcRq6AABC8gG` | 3.4m | 0.9m | 4.0m | **0.30m** | `1mRYVM4YfFFBRkcbz1hHpZ` |

This source-only diagnosis was independently reproduced using actual original native `IfcWall` `Curve2D` line endpoints in native world coordinates, each original `IfcOpeningElement` object placement and physical world mesh projected on the native host axis — not estimated from a hidden reference or a prior authored XML candidate.

The previous v0.12 *real native binder* correctly failed closed on `Opening is outside the hosted wall's horizontal extent`. **Do not relax that binder**, clamp the source Opening offset, lengthen the source Wall or pretend these openings are safe to move/edit. v0.13's new **opt-in read-only projection wrapper** demotes only exactly these **four** original Opening elements and their exactly four native `IfcRelFillsElement` filled Windows to immutable-source-owned opaque references. It verifies original `IfcRelVoidsElement` host and `IfcRelFillsElement` fill identity before any demotion; all other typed original elements and their relationship XML remain byte-identical where no demotion is required. It then calls the **same existing IFC4X3 XML parser, semantic binder and native relationship validator** on the surviving safe subset. On an original source whose old v0.9 binding already passes, v0.13 returns the **exact same old XML bytes**.

This is a **source-faithful read repair** (all original products remain visible in protected catalog), **not a repair of the original native geometry** or new Window/Opening update support. The original task still cannot be represented completely in editable XML because the demoted original Windows are necessary to the requested deletion operation.

## Independent native-source oracle

`tools/oracle_bibimbap_v13_native_source.py` is genuinely separate and imports **no v0.13 read view/typed projection, compiler, binder, original author scorer, hidden target/GT, or model agent**. For each original metre-normalized IFC source, it independently opens the source and validates:

- Catalog contains exactly **all native original `IfcProduct` GUIDs**, classes and STEP IDs, no missing/duplicate/added product.
- Every protected noneditable source Product/relationship is marked read-only; native schema/source SHA and source ownership are unchanged.
- Actual original triangulation SHA256, original vertex/face counts and min/max world coordinates match the catalog or are honestly `NO_NATIVE_REPRESENTATION` / `NATIVE_MESH_NOT_AVAILABLE`. This is not inferring a native parametric solid from an arbitrary bounding box.
- Original source `IfcRelVoidsElement`, `IfcRelFillsElement`, exact spatial containment and aggregation, and source space-boundary relationship GUID edges match the source model with no invented link.
- The same four Opening world placements/physical mesh widths are independently shown to exceed original Wall line; all four and their actual original native Window fills are absent from the safe typed subset, but PRESENT as source-owned read-only products in the catalog. Any attempt to spoof typed editability, remove an original source GUID, alter a mesh digest, inject a fabricated link, reinsert a bad original Opening into typed XML, change the original schema or confuse raw millimetres with normalized metres is rejected.
- Re-check the exact immutable original source file SHA256 before/after all inspection.

The independent oracle can attest **source read / original native product & selected relation fidelity**, not complete native editing or all author task success.

## Full original 45-task audit — measured v0.13, no parity inference

New versioned tools `tools/audit_bibimbap_v13_source_worker.py` and `tools/audit_bibimbap_v13_original45_read_catalog.py` inspect all **31 unique exact public original IFC inputs** in separate child processes with bound original IFC public hashes, preserving original IFC4X3/IFC2X3/IFC4 schemas, and independently run the full native catalog oracle. Every original task-specific minimum original Product role and cited IFC GUID is evaluated **twice**: does the safe typed source XML expose it? Is it still visible (read-only) in the exact native source catalog?

| Actual v0.13 measure | Observed evidence |
|---|---:|
| Public original task population | **45/45**, no exclusions |
| Unique original native source IFCs tested | **31/31** |
| Current native source read-only catalog + independent IFC-only oracle passed | **45/45** tasks, **31/31** unique native sources |
| All original task-required source roles/references visible in READ-ONLY native catalog | **45/45** |
| All original task-required source roles/references in safe typed XML | **36/45** |
| Previously blocked v0.12 IFC4X3 source files now readable with opaque catalog | **2**, `geometry_test_18` and `geometry_test_19` |
| Physically out-of-extent original Openings excluded from *editable* XML | **4** |
| Original Windows filling those Openings excluded from editable XML | **4** |
| Historical v0.2–v0.10 developer D0 source-only edit candidate + original-author score evidence | **22/45** (11 full original-author grades, 11 partial, 23 not audited in those frozen D0 reports) |
| Actual new native task write implementation for demoted Windows/Openings | **0** |
| Exact original task-specific Python I0 matched controls actually run | **0/45** |
| New matched real-model XML-vs-Python trials / new paid model calls | **0 / 0** |

The **45/45 is READ-ONLY source fidelity**, **NOT 45/45 native edit support or equivalent full original task success**. The **36/45 safe typed XML source roles/references** is also only a *minimal source representation gate*, not proof those 36 can perform their requested operation. The original v0.12 write/evidence matrix and 9 historical D0 reports remain immutable, with original author scores unchanged. Full original tool and task-specific Python I0 access remains incomparable until native XML supports the same original operations and both arms are independently validated. Do not report this as an improved Luna or XML editing benchmark score.

## Reproducibility and tests

Tools and code:
- `src/runtime/experimental_v13_opaque_source.py` — opt-in safe original-schema source read + read-only catalog; no native write path.
- `tools/oracle_bibimbap_v13_native_source.py` — independent original IFC-only Product/relationship/mesh source witness.
- `tools/audit_bibimbap_v13_source_worker.py` — isolated per unique IFC process.
- `tools/audit_bibimbap_v13_original45_read_catalog.py` — all 45 task read vs editable provenance/capability matrix, source SHA-pinned v0.12 reference.
- `tests/test_experimental_v13_native_source.py` — real original IFC positive and fail-closed negative tests, deterministic XML across clock tick.
- `tests/test_bibimbap_v13_original45_catalog.py` — exact 45 original public input/read-only coverage, true missing editable roles, original v0.12 failures, original D0 score preservation, and no new Python I0/model false claims.
- `reports/bibimbap_v013_original45_safe_native_read_catalog_20261114.json` — new original native 31-source + 45-task report and independent oracle SHA evidence. **SHA256 `67b58b9b55d24d48ae644200e0ac9501b255ed4a346aa4add2036438cad3e9f5`**.
- `reports/bibimbap_v013_original45_safe_native_read_catalog_20261114.csv` — separate flat 45-task result for analysis. **SHA256 `1af1af7d235f80f6744486b97766ebb45d2318f391f1f06bb3cbe41946b766be`**.
- **Real original source repeat:** both the complete 31-IFC native source read-only/independent-oracle run and entire 45-task report assembly were rerun after a clock interval; BOTH JSON and CSV full SHA256 hashes reproduced **byte-identically**, with pinned author/dataset Git repos remaining clean. Interim/repeated reports stay in ignored `results/`, not in tracked historical evidence.
- **36/36 new tests PASS**: 21 original-source native positive/fail-closed tests plus 15 all-45 independent-catalog evidence tests.
- **Complete full regression**: v0.13 + v0.12 + v0.11 + all earlier native IFC experimental source/edit compiler slices, original public 45-case offline audits, 25-call matched harness and native core: **293 tests RUN / 291 PASS / 2 optional SKIP / 0 FAIL**, **221.424 seconds**, exit code **0**. Original author/D0 archives and original source repos unmodified.

```powershell
$base='D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue140-native-opaque-v013')
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$author=Join-Path $base 'bibimbap-author-upstream'
$data=Join-Path $base 'bibimbap-author-data'

& $py -m unittest tests.test_experimental_v13_native_source tests.test_bibimbap_v13_original45_catalog -v

# New path only: never overwrite frozen original v0.12 / v0.13 reports
& $py -m tools.audit_bibimbap_v13_original45_read_catalog `
  --author-repo $author --dataset $data `
  --output-json 'results/NEW_UNUSED_v013_original45_read_catalog.json' `
  --output-csv 'results/NEW_UNUSED_v013_original45_read_catalog.csv'
```

## Next scientific/engineering priority

**v0.14 native editable access**: Source-faithful typed representation of original arbitrary IFC4X3 host/window/void geometry and original IFC Space/Beam relational semantics requires new audited schema/command semantics; a catalog is not enough. Register a separate issue/feature branch, preserve original native placements, share/ownership graph and source-dependent openings, fail closed if operations cannot preserve real geometry. For `topological_test_14` original Beam trim, full native Beam physical and intersection semantics are necessary; *don't flatten unknown original geometry to a fake rectangular box*. For Space room deletion/creation, preserve original `IfcRelAggregates` and original storey/space topology.

**Benchmark validity**: Build truly matched **original-task-specific XML D0 and Python I0** with independently verified native IFC candidates for the preregistered common supported task set, retaining the original 45 denominator. Original-author integrity metrics remain authoritative even when they disagree with a narrower native oracle. Any optimization informed by prior test metric analysis must be labeled nonblinded developer work, not a held-out result. Only after actual capability parity can another **explicit paid-model budget approval** authorize a fresh real LLM paired trial.
