# BIBIMBAP research — experimental Slab v0.4 native IFC CRUD / physical shape validation

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/122
**Date:** 2026-11-13 Asia/Seoul
**Scope:** ONLY independent `pikaybh/bim-markup-bench` test harness. **BIXML/Xim product not inspected or modified**, original BIBIMBAP author code and external pinned public IFC dataset read-only. Original #112 real GPT-6 Luna 45-task score and prior v0.1/v0.2/v0.3 compiler implementations remain immutable.

**New paid API/LLM calls: 0, spend $0.** This is **native compiler D0** and independent validation, NOT a new LLM benchmark result, not the 45-task parity release, and not a claim of experimental causal fairness.

## Public original IFC structural evidence

Original frozen BIBIMBAP dataset revision `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`; author evaluator revision `667004e16bd38fd7d538bcee56191465429fd975`. The original public `basic_tasks.ifc` is IFC4X3 with millimetre length unit; existing experimental source conversion creates isolated IFC clones in metres. It contains **two Revit native IfcSlab objects** with `IfcExtrudedAreaSolid` rectangles, transformed/rotated local extrusion frames, inverse material-layer associations, original storey containment and shared type. Previous v0.1 could project **zero** of these two slabs. The new read-only v0.4 projection reconstructs their rectangular **world-space bounding envelopes** while preserving their source representations unchanged. The envelope is not self-contained BIM and is not permission to replace native geometry with a cuboid approximation.

V0.4 `project_ifc_v4` builds on v0.3 read-only Column overlay and accepts a slab only when its actual native tessellation and underlying unique direct rectangular extrusion form an **axis-aligned 8-corner box**, safely tied to an original native building storey. Polygons, voided slabs, booleans, slopes, nonrectangular meshes, unsupported schemas and mapped/indirect representations are kept opaque or fail closed rather than silently flattened.

## Prospective v0.4 operations and verified limits

The model authoring surface remains **a complete declarative XML state**. No `<Create/>`, `<Move/>`, `<Set/>` commands or callable IFC mutation tool. Only the trusted backend derives stable-ID before/after XML semantic diffs, validates native source hash, and applies a transaction to a **new IFC file**.

| XML state delta | Native backend action | Safety gates |
|---|---|---|
| One additional `<Slab .../>` | `CREATE_SLAB` | One new deterministic GlobalId, existing **zero-elevation** native storey, unique `Body/MODEL_VIEW` representation context, bounded x/y/z and positive width/depth/thickness. New native `IfcSlab` + `IfcRectangleProfileDef` + swept solid and containment, actual world mesh and all original STEP/root entities audited |
| Existing Slab x/y/z changed | `MOVE_SLAB` | One original Slab only; original `IfcLocalPlacement` and parent frame validated. Shared original `IfcCartesianPoint` **copy-on-write** instead of changing other Revit geometry; after native reopen exact world mesh translation, original non-target STEP/roots protected |
| Existing Slab width/depth changed | `RESHAPE_SLAB_RECTANGLE` | Unique direct native rectangle/profile/body; axis-aligned horizontal sweep frame; change only native `IfcRectangleProfileDef` dimensions and unique extrusion-position point to preserve original minimum footprint corner. Native mesh geometry/reopened STEP and untouched slabs independently checked |
| Existing Slab thickness changed | `UPDATE_SLAB_THICKNESS` | Only direct-extruded standalone unlayered Slab, vertical sweep with safe orientation; native extrusion depth/position changed while minimum Z stays fixed. **Original Revit Slab with material-layer thickness association explicitly rejected**, to avoid material/shape inconsistency |
| Existing Slab node removed | `DELETE_SLAB` | Single original Slab and inverse-dependency allowlist; target-only property-set/material usage/relation cleanup permitted. Shared type/containment/material layer owners and all surviving original IFC products must be preserved; non-target IFC properties/presentation preserved and independently checked |

All operations are isolated **one-object transactions**; combined edits and unknown relationships are rejected. Atomic staged output commit with destination overwrite refusal; no original IFC or original provider answer modification. Units, schema and source hashes are validated. Source IFC2X3/IFC4, non-axis-aligned or voided Slabs, mass IFC4X3 source conversion and unsupported native relationships remain out of scope.

### Actual original public 45-task developer-authored D0

Before running the author scorer, original public-question-only fixed geometry was declared in `tools/audit_bibimbap_slab_v04_d0.py`. Original author scorer used solely **after** XML compilation, never exposed to an LLM. Original LLM #112 scores were not recomputed.

| Original public task | Developer-input action | Pinned original-author score | Independent native oracle |
|---|---|---:|---|
| `test_02` Create Slab | x=-35 to -25m, y=-2.5 to 2.5m, thickness=0.2m, bottom z=0; footprint centre (-30,0) from public wording | **1.0**: existence/location/dimensions/integrity all 1.0 | New native `IfcSlab` physical mesh dimensions/containment; all original native Roots and original Slabs preserved |
| `test_14` Decrease Slab height 0.5m | Interpret height as **world-Z elevation**, translate original public-guid Slab -0.5m, **not** changing 0.3m material-layer thickness | **1.0**: location/dimensions/integrity all 1.0 | Physical mesh translates -0.5m; all other original STEP entities/roots preserved |
| `topological_test_15` Place upper Slab on lower | From original public IFC geometry only, upper Slab bottom z translated to meet lower Slab top; XY untouched | **1.0**: location/dimensions/integrity all 1.0 | Physical native bottom/top contact and original other Slab mesh/STEP unchanged |

Each D0 report records public question+source hashes, fixed developer geometry, native candidate SHA and original author scores, plus **a separate oracle independent from the XML compiler and original grader**. The native IFCs themselves remain ephemeral/local and are not committed. The original source dataset/checkouts are unchanged. Git-safe reproducible aggregate is `reports/bibimbap_v04_slab_developer_d0_20261113.json`.

**These scores are compiler capability checks, not GPT-6 Luna scores and not replacements for the original 3/45 historical full-score measurement.** No new model predictions were made. The broader paper methods/models differ and cannot be equated from these D0 examples.

### Additional native tests — NOT original paper task score

The original public `basic_tasks.ifc` also verifies native rectangular width and depth reshape (including the 90° swapped local profile axes) and a safe isolated Slab deletion. For deletion, the original Slab material-layer usage and exclusively owned Psets are cleaned while all other IFC products remain. Original 45-edit cohort has no equivalent generic Slab delete task to claim an author benchmark grade.

A generated independent experimental unlayered Slab validates actual native **thickness increase 0.2→0.4m**, including preserved base Z and unrelated native STEP data. This is intentionally **not** a solution to `test_14` material-layer mutation nor general Revit type-driven slab alteration. Linked-material source thickness changes fail closed.

`geometry_test_01` (source unprojectable), `geometry_test_14` (different initial source geometry unprojectable under base read-only requirements), and slab-hosted opening `test_03` remain **unsupported**. `topological_test_04` has not yet received a standalone original-author D0. **Do not silently add these to supported task denominator.**

## Independent oracle and failure-path coverage

`tools/oracle_bibimbap_slab_v04.py` imports native IfcOpenShell only — no XML compiler, planner, binder, schema projection or original author grading. It checks native source and output IFC4X3, full original STEP inventory and GlobalId preservation, actual world mesh extents, original slab count, exact allowed physical changes, native storey assignment, surviving IFC products and member-preserving type/material/containment relations.

Adversarial tests reject no-op, wrong bounds/translation, bad dimensions, multiple Slabs, Slab+other edit, invalid original hash, unsafe source material-layer thickness change, existing destination overwrite, and unrelated product mutation in independently checked outputs. All reported as **offline deterministic** tests, not model trials or new measured language-model pass rates. No full-building clash or all-45 independent semantic checker is claimed.

## Reproduction (zero paid calls)

```powershell
$base='D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue122-slab-v04')
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$author=Join-Path $base 'bibimbap-author-upstream'
$data=Join-Path $base 'bibimbap-author-data'

& $py -m unittest tests.test_experimental_v4_slab -v

# D0 reporter refuses to overwrite previously recorded reports
& $py -m tools.audit_bibimbap_slab_v04_d0 --author-repo $author --dataset $data --output-json 'results/YOUR_UNUSED_SLAB_D0_REPORT.json'
```

## Remaining implementation order

1. Freeze/review v0.4 scope as a distinct prospective backend release. Keep v0.1–v0.3, historic paid scores and original author code frozen. **This PR does not enable the v0.4 backend in the matched 25-tool paid runner.**
2. Wall pose/length rotation/hosted dependent deletion plus independent actual native oracle, and original-source IFC schema/geometry support for all nine source-blocked tasks.
3. Hosted Door/Opening/Slab void/Beam and explicit native relationship handling, without opaque data loss. Support Column mapped height by safe per-instance native type/material isolation rather than changing shared source geometry.
4. Independently prove **45/45 actual original D0 and I0** source IFC transformations and geometry/relationship preservation, separately count unsupported. Pre-freeze same-model 25-tool conditions and *only then* request a new explicit paid API budget to compare XML and Python. External published numbers remain noncausal context until matched-model parity is verified.
