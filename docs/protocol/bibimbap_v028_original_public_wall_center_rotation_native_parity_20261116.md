# BIBIMBAP v0.28 — Original-public `test_11` Wall +90° midpoint rotation and IFC byte-parity

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/171

**Research-only stacked checkpoint.** Frozen previous v0.27 Draft PR #170, parent commit `cb4965d3d5e9f34cbc9a6eb97b9247a38b71d058`. No Xim/BIXML product/main edits; original author/data Git versions, scorer code, actual original IFC and all earlier frozen reports are preserved.

## 1. Why this original task comes next

The untested original PUBLIC `test_11` instructs rotating an existing native IFC4X3 `IfcWall` **+90° about Z, around its center**. The original source Wall is in the normal editable `<Wall>` XML projection. It has no doors/openings, other-Wall connection or Space boundary, making an exact, minimal source edit possible. Unlike original `test_14` (its target slab is opaque and absent from the typed XML source), no new projection format or model access is required.

The frozen original wall extends from (7.5, 13.9952) to (2.5, 13.9952) meters, with a 5 m physical native Axis Curve2D and +3.6 m height. Its original native local X axis is (-1,0), and its local placement start is (7.5,13.9952). A mathematically correct +90° midpoint rotation produces endpoints (5,16.4952) and (5,11.4952), preserving its midpoint (5,13.9952), 5 m axis length, thickness and height.

**Critical source-ownership trap:** The original native `IfcAxis2Placement3D.RefDirection` is `IfcDirection` STEP #6, initially referenced by **14 different IFC placements**. Directly changing that shared direction rotates/changes unrelated original Walls and makes the original author's `integrity_constraint=0.0`, even when location and dimension checks pass. The genuinely safe implementation **does not modify the shared direction**. It changes only the target Wall's exclusive `IfcCartesianPoint` placement location, adds **exactly one new private `IfcDirection`**, and updates only that Wall's exclusive `IfcAxis2Placement3D.RefDirection` link. Original shared-direction refs fall from 14 to 13 because the target is no longer one of those consumers; the shared entity itself is unchanged.

## 2. Trusted source-pinned declarative D0 compiler

`src/runtime/original_wall_rotation.py` is a separate narrowly trusted original-source IFC4X3 metric compiler backend. It enforces the original source-normalized IFC SHA `16568e7c4b8b9d62567a7a199101269daa6e5b1b7535cec095b8e233ae2ef6ac`, source 5m native curve, original target placement/axis and exact seven-class inverse inventory, no hosted openings/join/Space boundary, exclusive source placement and point ownership, and shared source RefDirection. Any modified input origin, unexpected native relationships, wrong schema/GUID, or non-target XML node change fails closed.

The **author submits the whole ordinary XML source** with exactly the `x1,y1,x2,y2` fields of one existing `<Wall>` changed to the +90° midpoint-rotated coordinates. The model does not obtain any `<Rotate>` action, native IFC writer, Python snippet or imperative tool. The compiler explicitly rejects changed height, thickness, level, source GUID, extra Wall edits, translation, wrong rotation direction or wrong angle.

`src/runtime/compiler.py` routes this only when trusted execution configuration sets `BMB_V028_ORIGINAL_WALL_CENTER_ROTATE=1` and the exact pinned original IFC source/checks are met. **Default is OFF**, retaining all older fail-closed behavior. This is an opt-in experimental source-specific compiler; not general orientation support.

The trusted writer stages a copy of the original IFC, creates precisely one new `IfcDirection`, and edits exactly the existing target exclusive placement point and placement reference, leaving all original `IfcRoot` GUIDs, IFC classes and serialized root attributes unchanged. Independently reopened complete native IFC verifier requires **all original Roots unchanged**, **zero original native STEP removal**, **one and only one newly added `IfcDirection`**, **exactly two original nonroot STEP records modified** (target point and target axis placement), shared source `IfcDirection` serialized bytes unchanged and other referenced placements unchanged. The target's physical placement matrix is independently verified, as is the whole native IFC-reprojected typed graph against the complete XML authoring state. Atomic native publish only after all validations; original source unchanged.

## 3. Genuine original-public matched D0/I0 evidence

`tools/audit_bibimbap_v028_original_wall_rotation.py` derives the target **only from the original PUBLIC task instruction**, builds one complete source-state XML edit, submits the D0 native compiler in a temporary session, then separately invokes `tools/bibimbap_v028_original_wall_rotation_i0.py` from the original PUBLIC mm source. The imperative I0 independently discovers the wall's original native Axis `IfcPolyline`, calculates midpoint and rotates its placement. I0 does **not import the D0 compiler, XML projection, original author grader or hidden task results**; it creates the same private native direction without modifying shared source state.

| Measured original PUBLIC `test_11` | Declarative D0 | Independent Python I0 |
|---|---:|---:|
| Exact original IFC4X3 millimetre source | PASS | PASS |
| +90° Z rotation about original wall midpoint | PASS | PASS |
| All 43 native `IfcProduct` GUID/classes preserved | PASS | PASS |
| All original native `IfcRoot` identities/classes preserved | PASS | PASS |
| Complete resultant original-mm IFC SHA-256 | **`5af3a2bd423c101e63cacad0a53342761b4496a0e9337ed0ce5b4b6d2a13f755`** | **byte-identical** |
| Unchanged original author right_location | **1.0** | **1.0** |
| Unchanged original author right_dimensions | **1.0** | **1.0** |
| Unchanged original author integrity_constraint | **1.0** | **1.0** |
| Unchanged original author final score | **1.0 — full mark** | **1.0 — full mark** |
| Actual LLM inference/provider spend | **0 / $0** | **0 / $0** |

The actual original-public report is `reports/bibimbap_v028_original_test11_wall_center_rotate_D0_I0_native_parity_20261116.json`, SHA-256 **`6818e6bfa2990f8dc9ee3730ba9a7197c72d6f3131af9bae9fbda8d22fefd8cb`**. A fresh execution must reproduce the whole original native output hash, all scorer results and sanitized report. No full original public prompt, target GUID, raw original IFC or hidden grader ground-truth target list is stored in reports.

**Important interpretation:** Original author full mark here is an actual correctness outcome for this developer-coded task, **not** evidence that an LLM can achieve it, nor evidence of causal advantages of declarative XML over Python. The model is never called, no paid API tokens used, and all45 cross-arm source/editability/feedback parity remains unproven.

## 4. Scientific counters

Previous original PUBLIC developer-written full output IFC byte-equal D0/I0 pairs: **9/45**. This new original task adds one **verified developer control pair**, cumulative **10/45**; original author-callable pairs **7/45 → 8/45**. The other **35** original PUBLIC tasks remain untested under the same full original IFC and scorer paired protocol. All old original Window-source missing-target cases and source-schema exclusions remain unchanged. No original benchmark files or scorer were patched.

## 5. Reproduction on the connected authorized Windows research workstation

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$repo = Join-Path $base 'bim-markup-bench-issue171-original-wall-rotation'
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
Set-Location $repo
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

& $py -m unittest tests.test_bibimbap_v028_original_wall_rotation -v

# Fresh ignored destination only; frozen reports cannot be overwritten.
& $py -m tools.audit_bibimbap_v028_original_wall_rotation `
  --root . `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') `
  --output 'results/UNIQUE_original_public11_rotation_report.json'
```

**Actual v0.28 regression results:** New original-public IFC & safety tests **35/35 PASS**, 30.791s unittest / 38.234s enclosing process (exit 0). Selected **18-module non-Docker cross-version regression 351/351 PASS**, 318.561s unittest / 328.578s enclosing process (exit 0); includes historical v0.26 default-native fail-closed and v0.27 explicit source-gated Wall delete. Immutable QA evidence is `reports/bibimbap_v028_selected_351_nondocker_regression_and_original11_native_QA_20261116.json`, SHA256 `8ad99438f24aa6e8cd34145439fdeb57aec24a59653fe4f007ab87cafd0170db`. The existing Docker Desktop Linux Engine still returns **HTTP 500 Internal Server Error** to read-only info/image/orphan queries, so the historical v0.19 Docker-sealed module is **excluded and unverified**. No Docker restart/reset/image reconstruction. The original pinned image's existence and old Docker orphan count are unknown, not proven absent or zero. **Do not claim Docker-included regression or complete 832-test historical repository discovery green.**

## 6. Next priority after v0.28

Research should next address the original PUBLIC update `test_14`: its slab target exists natively but is absent from current editable typed XML (opaque projection); moreover the original author's instruction uses height wording to mean **lower Z placement by 0.5m without changing geometry**, a subtle task-semantic mismatch. This needs first an independently verified typed-source representation extension before safe native writing; do not infer from other Slab experiments that the original `test_14` is supported. Other original public source geometry/complex topology gaps also remain.

No real paired LLM model trial is admissible yet without verified equal-information/editing affordances, explicit model/provider and budget, and preregistered results recording.
