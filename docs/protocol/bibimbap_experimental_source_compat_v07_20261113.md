# BIBIMBAP experimental v0.7 — original IFC source compatibility, native bootstrap and 2 independent D0 edits

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/128

**Date:** 2026-11-13 Asia/Seoul

**Project scope:** Only standalone `pikaybh/bim-markup-bench` research; no BIXML/Xim or production app changes. All v0.1–v0.6 compilers, original provider traces, historic #112 GPT-6 Luna 45-task real outcomes, original BIBIMBAP author scorer and original IFC corpus remained unchanged. **New paid LLM calls: 0; additional API cost: $0.**

**Important distinction:** `native_source_admission_v7` ≠ `project_ifc_v7` ≠ `compile_declarative_xml_v7` ≠ full original author task correctness ≠ real LLM success. Treat each as a separate gate. The source file is always authoritative and is never regenerated from its partial XML.

## Original nine blocked files: real source-evidence audit

Pinned public original author revision `667004e16bd38fd7d538bcee56191465429fd975`; original dataset revision `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`. Original public IFC sources use native millimetre units; all experimental IFC4X3 editing occurs on isolated native metre-normalized clones. Reversion to original millimetre units before author scoring is required.

| Task ID | Source native schema | v0.7 result | What remains blocked |
|---|---|---|---|
| `geometry_test_01` | IFC4X3 | **Original 4 mapped native Columns safely projected**; new direct Slab CREATE compiled, independent native oracle and original author D0 **1.0** | LLM-driven 25-tool real result not measured |
| `geometry_test_03` | IFC2X3 | Full native STEP/root/schema/units read-only admission | IFC2X3-specific Door+Opening CREATE still unsupported |
| `geometry_test_04` | IFC2X3 | Full native read-only admission | IFC2X3-native Space creation still unsupported |
| `geometry_test_05` | IFC4 | Full native read-only admission; original Storey has **no explicit elevation** | Native IFC4 Wall CREATE missing; refuse to fabricate elevation or claim equivalent IFC4X3 |
| `geometry_test_14` | IFC4X3 | Native direct Slab **world-space exact prism** projected despite tilted underlying swept extrusion frame | Slab native reshape on tilted local frame not implemented |
| `geometry_test_15` | IFC4X3 | **4 original mapped Columns projected**; one mapped Column MOVE compiled, independent native oracle and original author D0 **1.0** | Other mapped Column operations not generally supported |
| `topological_test_05` | IFC4X3 | 2 direct Slabs projected; **7 Boolean Clipping Walls left opaque** | Hosted Door CREATE and Boolean Wall host authoring unsupported |
| `topological_test_11` | IFC4X3 | 2 mapped Columns + 2 direct Slabs projected; **7 Boolean Walls and 2 Spaces opaque** | Multi-Column height edits, shared mapped representations and native joins unsupported |
| `topological_test_17` | IFC4X3 | 10 mapped Columns + 2 Slabs projected; native mapped geometry retained | Multi-Column spatial dependency-aware deletion unsupported |

Totals on these exact **nine** original public files:
- **9/9 original native IFC files read and schema/units/source root+STEP fingerprint admitted**. This is native read-only inspection, *not* editing support.
- **6/6 former IFC4X3 no-managed-element inputs now have an independently validated partial XML projection**. These were historically v0.1 projection-blocked. Original native walls/spaces left opaque are NOT suddenly model-editable.
- **3/9 legacy-schema inputs remain uneditable by the old IFC4X3 XML grammar** (IFC2X3: two; IFC4: one); no misleading or unverified schema conversion.
- **2/9 have an isolated native IFC edit and developer-authored full original-author D0 1.0**: `geometry_test_01`, `geometry_test_15`. This does not establish an LLM score, and the other seven are NOT silently promoted to original task support.
- **0/45 newly observed model outcomes.** Historic real GPT-6 Luna 3/45 full-mark record remains untouched.

## Exact implementation boundary

### Read-only native source admission

`src/runtime/experimental_v7_projection.py::native_source_admission_v7` uses only original native IfcOpenShell read operations and source SHA + complete STEP fingerprint. It records original schema (`IFC2X3`, `IFC4`, `IFC4X3`), exact length-unit scale, Root and storey inventory (including missing original elevation). It does not create a fake IFC4X3 model, does not invent missing native `Elevation`, and does not authorize legacy editing.

### Previously blocked IFC4X3 partial XML bootstrap

`project_ifc_v7` reuses **the exact original v0.4 XML bytes unchanged** if the existing projector already succeeds. If, and only if, the previous projector errors because **zero editable geometry** could be projected, the isolated v0.7 fallback constructs a fresh valid v0.1-schema XML *partial* view using the immutable source hash, native storeys with explicit elevations, and:

- A **mapped IfcColumn** only when original mesh is an **8-vertex/12-triangle exact axis-aligned rectangular prism**, with eight bijective native corner matches, two triangles per face and full native area, original source typed containment and source GlobalId.
- A directly native-extruded `IfcSlab` of the same *actual world-space exact prism* verified by full vertex/face checks. An original **tilted local extrusion frame** is acceptable for *read-only world prism display*, but this does NOT authorize local IFC reshape or replacement of its actual native swept definition.
- Other source `IfcWall` Boolean-Clipping geometry, original `IfcSpace` boundary data, relationship graphs and unsupported source products remain **opaque original IFC source-owned data**. No fake rectangular Wall axis/Boolean flattening. The native mapped Column is never rebuilt merely because a bounding envelope appears in XML.

The source file must be an exact IFC4X3 **metre-normalized copy**, not raw millimetres mislabeled as metres. XSD/parser and source-hash checks remain strict. `project_ifc_v7` is read-only and cannot write IFC.

### Narrow, isolated native edits after bootstrap

`src/runtime/experimental_v7_compiler.py::compile_declarative_xml_v7` receives **a full declarative XML state** and trusted backend derives **exactly one** stable-ID graph change. It is NOT an imperative command list to the LLM.

1. `MOVE_ORIGINAL_MAPPED_COLUMN`: existing original mapped Column may change x/y/z (not height, width, type, GUID or relations). Requires unique exclusive `IfcCartesianPoint` placement, no unsupported rotated parent, bounds and native source hash. Changes exactly **one** source STEP CartesianPoint, preserving all original `IfcMappedItem`, type definitions, original IFC Roots, and other original product meshes.
2. `CREATE_SLAB_FROM_BOOTSTRAP`: exactly one new deterministic Slab node on original **zero-elevation** native `IfcBuildingStorey`, with positive bounded footprint/thickness, source-native `Body/MODEL_VIEW` and one containment relationship. Creates real IfcSlab + IfcExtrudedAreaSolid rectangle (not a fake XML-only box). Native world geometry and existing STEP/Roots/containment memberships are validated. A source-only, developer-fixed **3m×3m×0.2m** slab is placed above the upper outer edges of four native original mapped Columns at z=3m in original public geometry_test_01.
3. **Reproducible research IFC provenance:** the native IfcOpenShell API can reorder an original `IfcRelContainedInSpatialStructure.RelatedElements` IFC SET on insertion, and automatically stamps new `IfcOwnerHistory` with the current wall clock. Both would alter raw IFC SHA on identical inputs. In this isolated *research-only* CREATE path, v0.7 restores the exact source member ordering then appends the new Slab, and pins only **newly generated** OwnerHistory dates to the existing source-native CreationDate epoch; all original OwnerHistory/STEP/Root records remain unchanged. **This frozen timestamp is an experimental source-anchored reproducibility marker, NOT the real date of authoring or a production IFC provenance policy.** An extra negative/positive test spans at least one wall-clock second and verifies byte-identical outputs; the final entire audit JSON reproduced the same SHA across two later runs.
4. Absolutely **no multi-node transactions**, no inferred boolean clipping host reconstruction, no IFC2X3/IFC4 edit, no mapped Column direct height editing, no source ownership rewrite, no original input overwrite. Every candidate is written to a new file via atomic staged/native reopen validation and checks the original SHA again before/after commit.

### Independent native oracle and negative controls

`tools/oracle_bibimbap_v07_source.py` imports neither projection nor compiler nor XML binder nor original paper scorer. It independently verifies native typed IFC schema, root inventory, original source hash, exact native prism corner/face/area geometry, per-storey source containment, XML visible geometric values, opaque source preservation, original mapped Column world vertex translation, actual new direct IFC Slab mesh and original STEP/root/presentation integrity. A corrupted unrelated IFC Product or forged XML bounds fails. Original frozen public source remains unchanged.

`tests/test_experimental_v7_source.py` includes **20/20 passing** positive and negative tests on every original nine source, original v0.4 stable identical projection for previously working source, invalid input schemas/units, missing IFC4 Storey elevation, unsupported mapped Column height, multiple mixed operations, destination clobber/source-hash tampering, incorrect independent native geometry, and **byte-identical source→candidate repeated Slab CREATE across a system-clock-second boundary**. Combined v0.7+v0.6 Hosted+v0.5 Wall+v0.4 Slab+v0.3/v0.2 Column+#116 original45 native audit+#114 25-call offline runner+prior compiler regression: **145 tests run, 143 PASS, 2 optional SKIP, 0 FAIL** (final run 148.806 seconds, no model calls).

## Original pinned developer-authored D0 score (not real GPT-6 success)

`tools/audit_bibimbap_v07_source_d0.py` first records developer-selected geometry from public source/question only, compiles XML to original-native IFC and runs an IFC-only independent oracle. **Only then** does the original author pinned scorer inspect final IFC in original units. Neither grader nor GT supplies the developer's chosen input; no adaptation was made based on observed author scores.

- `geometry_test_01`: native original columns at four outer 3m×3m corners; developer creates a **3×3×0.2m** native slab at z=3m, covering their upper outer edges. **Original author 1.0**, all `object_exists`, `right_location`, `right_dimensions`, `integrity_constraint` = 1. Independent original native mapped Column and actual Slab box/containment proof PASS.
- `geometry_test_15`: four original mapped Columns; original right-upper Column's native bottom Y is 4.25m whereas other upper-left is 3.50m; move original public GUID `3lOEkLxYb9$uRd50gnIDqu` by **-0.75m world Y** to align rectangle. **Original author 1.0**, all location/dimensions/integrity = 1. Independently proves complete mapped-column world cloud shift and no other original IFC STEP changes.

**These are developer-authored deterministic D0 compiler capability demonstrations, not observed LLM output or model pass rates.** Both actual historical #112 real Luna score and same-model 25-call benchmark remain unchanged.

Git-safe evidence: `reports/bibimbap_v07_original_nine_source_and_d0_20261113.json`, final SHA256 `bdccd71a2fb0283221dec191d07adb06e8291a00aafc0c2e21d479a5368b7c55`. The exact same report byte SHA was independently regenerated twice, with at least two seconds separating runs. It includes original public task+IFC source hashes, original schemas, native source/partial XML gate results, rejected original legacy cases, exact developer fixture, native independent oracle and original author after-compile submetrics. No original IFC bytes, secret keys, private paper target IFC/hidden GT or model responses committed.

## Reproduction without API tokens

```powershell
$base='D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue128-compat-v07')
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$author=Join-Path $base 'bibimbap-author-upstream'
$data=Join-Path $base 'bibimbap-author-data'

& $py -m unittest tests.test_experimental_v7_source -v

# Refuses overwriting existing report. Use a fresh unused destination:
& $py -m tools.audit_bibimbap_v07_source_d0 --author-repo $author --dataset $data --output-json 'results/YOUR_NEW_UNUSED_COMPAT_V07_REPORT.json'
```

## Next priorities — explicitly missing

1. **True IFC2X3 + IFC4 native declarative projection and editing** without changing their original schema and without inventing the missing IFC4 storey elevation. The present v0.7 is *only native read-only admission* for 3 old schema files.
2. Native editable geometry on IFC4X3 Boolean/Clipping Walls with exact source meshes and original host relations (avoid bounding box fake Walls); direct local Slab rectangle reshape for tilted source with source-only displacement/axes; mapped type-driven Column height with safe per-instance isolation.
3. Hosted Door+Opening CREATE and Space CREATE, multiple dependent Column/Slab edits, source graph correctness and 45/45 task-by-task D0/I0 no-data-loss gates.
4. Only then, freeze real matched-model 25-call arm and obtain a new explicit budget before inference. The original experiment results are immutable, and unverified gaps are never counted as model failures/successes interchangeably.
