# Prospective BIBIMBAP Column v0.3 — real IFC mapped geometry, move/delete/height

**Issue:** [#120](https://github.com/pikaybh/bim-markup-bench/issues/120)
**Date:** 2026-11-13 Asia/Seoul
**Repository scope:** Only independent experimental `pikaybh/bim-markup-bench`; original BIXML/Xim product not inspected, modified, or deployed. **No new LLM calls or API charges.** Historical #112 full 45-task real GPT-6 Luna results and #116 frozen gap matrix are **unchanged**, not silently rescored.

**Science status:** Experimental v0.3 is a *new, separately versioned trusted backend capability slice*. Not the 45-task paper-comparable benchmark, not fully-feature-equivalent to Python/IfcOpenShell, and **not wired into #114's 25-tool paid model loop**. Any later use must prospectively freeze a model/tool/schema/backend version and obtain new explicit owner paid-budget approval.

## Original source gap

The original author public `basic_tasks.ifc` is IFC4X3 in millimetres; the v0.1 experiment normalizes to metres for XML compilation. It contains **10 native `IfcColumn` objects** exported with `IfcMappedItem` and Revit-style type/properties/presentation, all **opaque/not visible in the prior v0.1 XML projection**.

The new read-only `project_ifc_v3` augments only the experimental projection with **native world-space bounding-envelope XML `Column` nodes** for eligible mapped columns. It preserves every original GlobalId, maps to an existing IfcBuildingStorey, and labels the source's bounds as proxy coordinates. This is **not a lossless reconstruction** of the mapped/native representation. New XML attributes remain the original declarative `BoxElementType`; original mapped geometry and shared type geometry stay in IFC backing source, never recreated by moving the bounding proxy.

The previous no-op/error baseline and full 45 original prompt input versions are untouched.

## Operations actually implemented

| Declarative semantic diff | Trusted isolated IFC mutation | Conditions and validation |
|---|---|---|
| `Column` existing stable node x/y/z changed | `MOVE_COLUMN` | Only one source Column changed; unique nonshared `IfcCartesianPoint` original local object placement with unrotated parent frame; original native solid shape remains opaque. One **and only one** original STEP entity may change. After real native IFC reopen, target's world mesh bbox shifts by exact requested XYZ vector and every original root remains byte/STEP-equivalent |
| Existing direct-extrusion Column height changed | `UPDATE_COLUMN_HEIGHT` | Only directly owned `IfcExtrudedAreaSolid` and no `IfcMappedItem`; native height/mesh top changes, world bbox base unchanged, exactly one original STEP solid entity changes. **Mapped Revit type geometry is explicitly rejected**, because modifying it could affect other columns |
| Existing `Column` node removed from XML | `DELETE_COLUMN` | Single, isolated original Column only; native IfcOpenShell `remove_product` removes its privately owned shape/Psets/type & containment memberships. All other original IFC Products, Columns, Psets, surviving type/containment members and world meshes preserved. Enumerated STEP ownership/presentation assignments are audited. Extra dependencies and shared property ownership fail closed |

Original v0.1 compiler and v0.2 create compiler are not altered. v0.3 **does not** support combined changes, more than one Column per transaction, changing a mapped Column height, mapped profile size/rotation, unsupported parent transforms, IFC4/IFC2X3 sources, or global building clash certification. No imperative BIM command surface is exposed to XML authoring.

## Actual original BIBIMBAP public cases (developer fixed offline D0, NOT an LLM score)

All original public source IFCs remain byte-identical. The two target IFC GlobalIds below are literally present in original public task questions, **not held-out/private ground truth**. Entire original IFC normalized to metres, transformed by trusted v0.3 compiler in isolated scratch and converted back to millimetres before scoring.

| Original public test | Developer XML state change | Independently verified native effect | Frozen original author grade |
|---|---|---|---|
| `test_15` (Update) | Move the public-target Column **-3m along global Y** | Real native `IfcCartesianPoint` and world mesh translate exactly -3m; nine other native Columns unmoved, all 357 other IFC Roots preserved | **1.0** (`integrity_constraint=1`, `right_dimensions=1`, `right_location=1`) |
| `test_16` (Delete) | Remove public-target Column and owned native resources | Native target absent, nine original other Columns retain world geometry, **42 other IFC Products** preserved; target-only property sets/type/containment relation members cleaned | **0.5** (`object_not_exists=1`, `integrity_constraint=0`) |

**A central unresolved discrepancy is deliberately retained**: the pinned original author integrity scorer returns **zero integrity credit on test_16** even though a separate independent semantic IFC oracle validates that the target is removed and other native product identities, nine other column meshes, type associations and property relation memberships are preserved under this narrowly defined native criterion. This does **not** prove the author's grader wrong or the deletion fully correct under its criterion. The stronger author integrity condition is not yet met, and no post-hoc reference/GT-based retuning was performed. It remains an explicit blocker before 45-task equivalence.

The **original author scores here are for developer authored fixed D0 compiler tests**, NOT a new GPT-6 Luna trial and **NOT replacements for original #112 attempts** (where the full benchmark originally scored 3/45 full marks). New GPT usage is **0**, estimated API cost **$0**.

Git-safe (no original IFC bytes or author-private test code): `reports/bibimbap_v3_column_d0_test15_test16_20261113.json` includes task IDs, frozen original input/question hashes, developer input distinction, native candidate hashes, exact original score + metric breakdown and independent native task-specific oracle evidence.

### Independent oracle separation

`tools/oracle_bibimbap_column15_16_native.py` does **not** import the XML compiler, graph binder, validation planner, or original author grader:

- `strict_move_column` checks original/mutated entire IFC STEP inventories, permits only one native placement `IfcCartesianPoint` delta, verifies actual target world mesh -3m and all non-target Columns / IFC roots unchanged.
- `strict_delete_column` checks every original IFC product survives except the intended target, other Column meshes remain identical, required native containment/type memberships are unchanged aside from the target, and only singly owned property roots/relationships may disappear.
- These are **task-specific partial-independent IFC correctness oracles**. They do not prove zero clashes across the entire building, do not override original-author metrics and do not imply remaining 43 tasks are supported.
- Negative tests deliberately corrupt non-target Column metadata, wrong translation sign, wrong deletion target, unsupported dependency, invalid source hash, multiple columns at once, nonpositive height, mapped-type height and profile dimensions. The tests **must reject** these inputs.

Synthetic fixture `tests/fixtures/synthetic/input.ifc` additionally demonstrates a strictly unshared direct native Column solid can change its **height by 0.5m** without changing any other STEP entity. This is **not** the original public `topological_test_11` (its input has unsupported mapped geometry), which remains blocked.

## Reproduce offline

```powershell
$base='D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue120-column-crud')
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$author=Join-Path $base 'bibimbap-author-upstream'
$data=Join-Path $base 'bibimbap-author-data'

# Real original public IFC, native geometries, adversarial invariants
& $py -m unittest tests.test_experimental_v3_column_crud -v

# Separate fixed D0, no model calls; refuses reused output path
& $py -m tools.audit_bibimbap_v3_column_d0 --author-repo $author --dataset $data --output-json 'results/YOUR_UNUSED_D0_RUN.json'
```

**Next priorities:** explain/independently resolve deletion integrity discrepancy through published/independent specification without tuning on hidden GT; support safe mapped height by per-instance geometry isolation instead of changing shared type; expand to slab creation/placement/deletion, wall pose and deletion, source schema/shape compatibility; verify 45 individual D0/I0 oracle cases, then get a new paid model budget and run the prospectively frozen matched benchmark. No original paper-equivalent performance assertion yet.
