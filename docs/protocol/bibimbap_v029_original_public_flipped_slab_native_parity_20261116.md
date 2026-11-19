# BIBIMBAP v0.29 — Original PUBLIC `test_14` typed inverted Slab representation and −0.5m Z placement (D0/I0 native byte parity)

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/173

**Research-only stacked checkpoint.** Frozen parent v0.28 Draft PR #172 at commit `6505cc8ffd9907d8f4fc477e8424ea4bfcfd8788`. No Xim/BIXML product/main changes; original BIBIMBAP author and public data pinned at the same SHA; original scorer and IFC source files are never modified. No real LLM calls, no paid provider spend.

## 1. Actual native IFC source diagnosis — why the original Slab was opaque

Original PUBLIC `test_14` says: decrease the height of the slab by 0.5 metres. The unchanged original AUTHOR scorer's documented task semantics actually require moving the target Slab **downward by 0.5 m**, without reducing thickness, deforming the original body, or moving other Products. Never confuse this with an actual Slab thickness decrease.

This source is the pinned original `basic_tasks.ifc` (IFC4X3 millimetres, normalized to metres in the D0 session). The native original target `IfcSlab` is present as `FLOOR`, with an explicit physical swept-solid body `IfcExtrudedAreaSolid`, a rectangular `IfcRectangleProfileDef` (10.375m × 10.4m), original extrusion depth 0.3m, and an **inverted local Z axis (0,0,−1)**. The solid's local XY axes are swapped. The old restrictive XML projector rejected this source with **`Tilted swept extrusion frame unsupported`**, leaving both native original IfcSlab entities outside the typed editable XML despite their true world shape being precisely an axis-aligned cuboid.

This is *not* a free-form arbitrary polygon or approximation from a bounding box. In `src/runtime/original_slab_projection.py`, the trusted source reader calculates the exact eight corners of the original native rectangular extrusion, combining full original Product and solid frame transforms. It requires a single rectangular, unclipped `Body/SweptSolid`; a right-angle world-aligned frame; exact inverted −Z extrusion; all eight corners equal to the eight corners of the resulting cuboid; 0.3m physical Z thickness; unambiguous storey membership. Rotated/oblique/mapped/boolean native Slabs remain opaque and are never silently approximated. Source XML uses the **already frozen XSD `<Slab id ifcGuid level x y z width depth thickness />`** (no XSD extension, no imperative XML commands).

The original top target Slab is now faithfully represented with world footprint `x=−0.2`, `y=−0.175`, `z=3.8`, `width=10.4`, `depth=10.375`, `thickness=0.3`; its companion original bottom Slab appears as a second typed `<Slab>`, unchanged. The author submits the **complete original building XML**, with only the original target Slab `z="3.8"` changed to `z="3.3"`. All levels, other Products, source GUIDs, relationships and physical slab dimensions are preserved.

**Feature explicitly opt-in and default OFF:** `BMB_V029_ORIGINAL_SLAB_TRANSLATE=1` is set only in the trusted experiment configuration. The original normal projector and v0.28/earlier tests retain the former opaque representation, preserving the previous baseline and reports. For D0 original source, the flag additionally requires the frozen normalized original IFC source SHA **`16568e7c4b8b9d62567a7a199101269daa6e5b1b7535cec095b8e233ae2ef6ac`**. The compiler's validation explicitly reprojects its own freshly staged IFC with the same verified narrow physical cuboid reader.

## 2. Critical native shared-source placement aliasing

The target original Slab's exclusive `IfcLocalPlacement` contains a uniquely owned `IfcAxis2Placement3D`. However, its `Location` is the original `IfcCartesianPoint((0,0,0))`, referenced from **56 native IFC entities**. Naively changing those shared coordinates would move other products (and fail the original integrity metric).

The trusted `src/runtime/original_slab_translate.py` **never changes the original shared CartesianPoint**. Instead, it allocates exactly **one new private `IfcCartesianPoint((0,0,−0.5))`** and updates just the target's original unique `IfcAxis2Placement3D.Location` link. It does not modify the extrusion, the slab dimensions, any native `IfcRoot`, original shared representations, parent storey placements, or any unrelated native STEP entities.

An independently reopened full IFC verifier requires exactly **zero original native STEP entity deletions**, **one new private CartesianPoint**, and **one existing original STEP entity modified** (the unique target `IfcAxis2Placement3D`). The old shared zero point is byte-identical, with reference count falling from 56 to 55 only because the target was moved to its private point. All original `IfcRoot` GUIDs/classes/full serialized Root data remain identical, and original target world placement moves only Z by −0.5m, with X/Y unaffected. All original other physical geometry and typed XML are checked through complete IFC re-projection against the full submitted source document before atomic stage publication. Any mismatched source, extra XML edit or unexpected change fails closed without publishing a native IFC.

This is a narrow, source-pinned original Slab translation feature, **not** general native IFC Slab editing, arbitrary extrusion, or IFC4/IFC2X3 support.

## 3. Matched original-public developer D0/I0 evidence

`tools/audit_bibimbap_v029_original_slab.py` reads the PUBLIC target GUID only from the original PUBLIC question, creates a complete edited XML document with only the existing `z` state changed, and runs the trusted D0 compiler. Separately written imperative Python/IfcOpenShell I0 `tools/bibimbap_v029_original_slab_i0.py` edits the *same original PUBLIC IFC* from original millimetres, converts to metric internally, independently creates the private placement point, restores original IFC4X3 millimetres, and never imports the D0 XML compiler or the original scorer. It is a developer-written I0 control, **not an LLM-generated model result**.

| Actual original PUBLIC `test_14` | D0: complete XML → trusted IFC | I0: independent Python |
|---|---:|---:|
| Original IFC4X3 source, mm→m→mm | Same pinned source | Same pinned source |
| Slab world Z move −0.5m, X/Y unchanged | PASS | PASS |
| Preserve native Slab dimensions/profile/other native Products | PASS | PASS |
| Preserve all original Roots & shared 56-reference point | PASS | PASS |
| Complete resulting original-mm IFC SHA256 | **`1b0e811327765bf4f9f85545de64260da19e421f1707d005d8e9ac30e7914b18`** | **byte-identical** |
| Unchanged original author right_location | **1.0** | **1.0** |
| Unchanged original author right_dimensions | **1.0** | **1.0** |
| Unchanged original author integrity_constraint | **1.0** | **1.0** |
| Unchanged original author score | **1.0 FULL MARK** | **1.0 FULL MARK** |
| Actual real model/provider spend | 0 calls, $0 | 0 calls, $0 |

Actual frozen sanitized original-public report: `reports/bibimbap_v029_original_test14_flipped_slab_D0_I0_native_parity_20261116.json`, SHA256 **`338f763b691390b7186c51ecdaaa914ce18a9c8ab8586fa000542a7d63f8b748`**. Original full public question/target GUID, hidden grader GT, raw original IFC and credentials are **not** committed. The original 45-case denominator and all older source limitations remain independently auditable. No modification of the original scorer has been made.

## 4. Scientific accounting (do not overclaim)

| Metric | Frozen v0.28 | Actual v0.29 |
|---|---:|---:|
| Original PUBLIC benchmark tasks in cohort | 45 | 45 |
| Developer-only original complete IFC D0/I0 **byte-identical** paired cases | 10/45 | **11/45** |
| Original-author-callable developer D0/I0 paired cases | 8/45 | **9/45** |
| Original tasks still unpaired under identical native-output protocol | 35 | **34** |
| Real LLM matched D0/I0 model trials | 0 | **0** |
| Paid model/provider inference | $0 | **$0** |

This is an experiment-control implementation milestone, not a causal LLM model-performance result. The original full 45-task semantic read, writable capability and feedback/tool-call parity remain **unproven**.

## 5. Reproduce only on the authorized Windows research workstation

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$repo = Join-Path $base 'bim-markup-bench-issue173-original-slab-placement'
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
Set-Location $repo
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

& $py -m unittest tests.test_bibimbap_v029_original_slab -v

# Produce only a NEW ignored report path, not a frozen evidence file.
& $py -m tools.audit_bibimbap_v029_original_slab `
  --root . `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') `
  --output 'results/UNIQUE_test14_actual_native_D0_I0.json'
```

**Actually observed v0.29 regression:** New original-public and adversarial native tests **40/40 PASS** (29.995 seconds unittest / 37.937 seconds enclosing process, exit 0). Selected **19-module NON-DOCKER cross-version regression 391/391 PASS** (278.554 seconds unittest / 288.547 seconds process, exit 0), including all selected old v0.28 and earlier tests with their original default-off source projections, v0.27 source-specific native Wall and v0.28 Wall rotation safety. Frozen QA: `reports/bibimbap_v029_selected_391_nondocker_regression_and_original14_native_QA_20261116.json`, SHA-256 `ee74e52c47a71f261528f2269ed21bd045748eed258bb1ad9c0e2c45c5e19e7a`. Independent READ-ONLY Docker Desktop Linux Engine info, pinned-image inspect and old worker orphan list all returned **HTTP 500 Internal Server Error**. Therefore the old v0.19 sealed Docker test module was **excluded, not claimed green**; pinned image existence and worker orphan count remain unknown (neither confirmed missing nor zero). No Docker restart/reset, image reconstruction or prune. The historical entire ~832-case repository test discovery was not run and is not claimed green. Frozen original source and previous original reports remain SHA pinned and unchanged; private Window scorer GUIDs and credentials are scanned before scoped Git submission.

## 6. Next research priority

After v0.29, select next original PUBLIC update(s) such as `test_12` wall physical height adjustment or `test_13` window assembly relocation, **only after exact source topology/semantics/capability parity preflight**. Prioritize tasks with source-faithful read and write representation and stable original IFC writer. Do not run paid LLM trials without explicit provider/model/budget and registered fair original45 information/tooling/feedback parity.
