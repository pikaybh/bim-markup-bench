# BIBIMBAP prospective Wall v0.5 — native planar pose/length & connection-aware removal

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/124
**Date:** 2026-11-13 Asia/Seoul
**Scope:** ONLY independent research `pikaybh/bim-markup-bench`. No modifications to Xim/BIXML product; no modifications to original BIBIMBAP author repository, original public input IFC corpus, experimental v0.1–v0.4 compiler, or historical #112 real GPT-6 Luna full-45 model outcomes. **New LLM/API calls 0; spend $0.**

**Research status:** New prospective v0.5 native IFC4X3 trusted compiler for a limited subset of Wall edits. Not general Revit interoperability, not full 45-task IFC feature parity with the paper's Python/IfcOpenShell baseline, not a new matched paid model run. The historic author full marks remain 3/45 from #112 (the previous LLM result); developer-authored D0 demonstration is categorically not a model success.

## Actual original IFC evidence and scope

Pinned original public BIBIMBAP dataset revision `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`, original author evaluator revision `667004e16bd38fd7d538bcee56191465429fd975`. Input original IFC units are millimetres; experiments normalize isolated source clones to metres, and convert the candidate back to original units before author scoring.

The public original `basic_tasks.ifc` includes 16 native IFC4X3 IfcWall objects; the requested `test_11` target `22hyxvAPr65PFt9WZfHSP3` has a unique source rectangular swept body and `IfcPolyline` axis and no native geometric path connections. The requested `test_19` wall `2UsXAbj6n0fwEWqdkVuHyn` has **two `IfcRelConnectsPathElements`**, plus original per-object property sets, shared type/material/classification and storey containment. Meanwhile the original `topological_test_12` includes one disconnected 2m-long wall `2c8iwp2JP1ox_Asrwk4CZr` outside the six public named walls, with a unique native body and explicit line axis. Walls in the other original geometry/rotational tasks can have native path connections; those are **explicitly rejected** by this limited version rather than silently updated.

## Experimental v0.5 declarative authoring and trusted operations

New separate `src.runtime.experimental_v5_wall.compile_declarative_xml_v5` reads v0.4 read-only IFC projection, checks the immutable original hash, binds complete before/after XML states to stable GlobalIds, and infers **exactly one** existing Wall mutation. No imperative Wall edit operations available to the direct XML model. Existing v0.1–v0.4 backends unchanged; v0.5 is **not wired into** the #114 25-call paid-model runner. It does not silently delegate or combine other feature versions.

| Stable-ID XML state change | Trusted native mutation | Native safety constraints |
|---|---|---|
| Both ends translated in XY, identical direction/length | `MOVE_WALL` | Original wall standalone from path/host constraints, source object placement unshared, native wall origin equals original explicit source axis start. Updates exactly one original CartesianPoint; original swept solid, axes, other IFC STEP records/physical meshes unchanged |
| Endpoint orientation changed with fixed total wall length | `ROTATE_WALL` | Same standalone/unique frame preflight. Native `IfcAxis2Placement3D.RefDirection` points to a **new** `IfcDirection` because original Revit direction is shared across multiple products. The existing original reference direction is not edited. If wall origin changes, its exclusive native placement CartesianPoint is also updated. Actual world IFC axis and generated shape mesh validated |
| One endpoint shortens/extends collinearly, first endpoint unchanged | `CHANGE_WALL_LENGTH` | Unique `IfcRectangleProfileDef`, unique original explicit `IfcPolyline` end point, local wall axis agrees with native wall object placement. Changes original rectangle XDim and only exclusive line-axis endpoint. Other walls, original STEP IDs and roots unchanged. No shape-dependent connection/host allowed |
| Existing Wall removed, including XML `Connects` edges incident to it | `DELETE_WALL_WITH_SAFE_RELATIONS` | Existing native `IfcRelConnectsPathElements` **only when no shape-dependent `ConnectionGeometry`**. Native root.remove_product cleans target-owned Psets and removes connected path relationships, while preserving all other original IFC products, all surviving original walls' actual meshes, other shared type/classification/material members and unrelated IFC Roots. Every removed native STEP inverse ownership closure and original presentation layer membership checked. **Hosted `IfcRelVoidsElement`, filled doors/windows, explicit space-boundaries and complex relation chains are NOT supported** |

For all operations, original IFC4X3+metre source, positive bounded wall length, positive existing height/thickness, original original class/GlobalId, exactly one changed Wall, consistent relationship edges, and unused destination are mandatory. Native changes are staged atomically and independently reopened; on validation failure, no candidate IFC output is published. Unchanged or unsupported edits are rejected. We do not reinterpret a wall center/pivot from hidden original author grader; a rotation XML describes both new endpoints and the trusted compiler follows that complete state.

### Independent native IFC oracle

`tools/oracle_bibimbap_wall_v05.py` imports neither the XML compiler/projection/binder nor original author grader. It independently reopens source and result IFCs and verifies:

- Native `IfcPolyline` axis endpoints transformed exactly as the declared XY motion, rotation about a **developer-declared pivot** (the public task-11 D0 fixes the first endpoint; an additional ungraded positive native fixture verifies a separate midpoint pivot) or one-metre same-direction shortening.
- Actual world-space IfcWall mesh vertices for rigid pose moves/rotation, rectangle-swept length for shortening, not just a metadata flag.
- Every other original IfcWall mesh unchanged and all original other IfcProduct GlobalId/STEP root semantics unchanged.
- Native IFC STEP entity set unchanged for length, controlled native reference-direction copy-on-write for rotations, and specific allowlisted geometry edits only.
- For connected deletion, only the target IFC Product is removed, target's original path connection relationships are absent, surviving shared material/classification/type/containment membership correct, and **all other native Wall meshes unchanged**.

This is a **task-specific limited independent oracle**, not proof of full building physics, all spatial/topological correctness, clash-free geometry, or official metric equivalence. Negative tests intentionally corrupt non-target IFC product data, wrong rotation sign, wrong length delta, try connected rotation, attempted hosted wall delete, dangling XML relations, bad source hashes, mixed edits and file overwrites.

## Original public BIBIMBAP developer fixed D0 results (NOT GPT-6 trials)

Fixed developer-authored input choices are in `tools/audit_bibimbap_wall_v05_d0.py`, derived only from the public question and original public input IFC. The original author grader runs AFTER the native result is compiled and independent oracle succeeds. No original expected output/reference IFC or hidden scorer data was used as the authoring input. Scores have NOT been used to post-hoc optimize the fixed D0 inputs or modify the original #112 model records.

| Public task | Developer input | Pinned author score | Interpretation |
|---|---|---:|---|
| `topological_test_12` | Shorten the single source-disconnected wall outside six named walls by **1m**, keeping first endpoint fixed and changing native profile+line axis | **1.0** (location, dimensions, integrity each 1.0) | Strict independent native oracle also validates original 8 IfcWall inventory, original other meshes and source STEP preservation |
| `test_11` | Rotate public-ID wall **+90° around first axis endpoint**. The public wording specifies angle/z-axis, not exact pivot; this is a declared *fixture choice* | **0.333333** (dimension 1.0; location 0.0; integrity 0.0) | Independent oracle validates the physical native mesh rotates around stated pivot, but **official authored task correctness is NOT established**. No claim author grader wrong; pivot semantics and other integrity rules remain unresolved |
| `test_19` | Remove public-ID Wall and its 2 source path relationships, leaving all other native products, wall meshes, shared type/material/relations intact | **0.5** (object absence 1.0; integrity 0.0) | Native limited relationship-preservation oracle passes, but **original author integrity criterion is not met**; remains partial. No post-hoc retuning |

Evidence `reports/bibimbap_wall_v05_developer_d0_20261113.json` stores all original public question/source checksums, candidate hashes, original-author submetrics and independent oracle results. It does not commit original IFC corpus, author-private grading source or raw model-provider responses.

**No scores listed above are newly observed GPT-6 Luna model successes.** No claim that passing a deterministic developer D0 proves a model can edit those XML states with 25 calls. Missing cases remain in 45-denominator task gap accounting and in original historical scores.

## Verification and reproduction

```powershell
$base='D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue124-wall-v05')
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$author=Join-Path $base 'bibimbap-author-upstream'
$data=Join-Path $base 'bibimbap-author-data'

& $py -m unittest tests.test_experimental_v5_wall -v

# Never overwrite prior evidence; use an unused path
& $py -m tools.audit_bibimbap_wall_v05_d0 --author-repo $author --dataset $data --output-json 'results/YOUR_UNUSED_WALL_V05_D0.json'
```

The new 15 tests cover actual original source IFCs, test_11/19/topological12, native translate, and a separate ungraded 90-degree midpoint-pivot native Wall rotation, plus fail-closed negatives (connected pose, hosted opening/door deletion, malformed or incomplete connection XML, mixed edits, invalid source hash, unacceptable length/direction, overwritten existing files, and post-run corruption of unrelated IFC Product). Existing v0.1–v0.4 regressions should be re-run and reported separately. No paid API calls.

## Remaining priorities (explicitly UNIMPLEMENTED)

1. Diagnose the discrepancy between the narrower independent physical oracle and the original author `test_11` location/integrity + `test_19` integrity scorer **against the public task definition, not private GT-guided tuning**. Expand pivot semantics and native connection semantics only with prospective versioned evidence.
2. **Hosted Wall+Opening+Door/Window lifecycle** with exact referential/void/fill property and spatial containment behavior and safe deletion of dependent entities. Existing v0.5 **rejects** a hosted Wall deletion; it must not be counted supported.
3. Nine non-projectable original sources (IFC2X3/IFC4/complex IFC4X3) with real native source geometry preserved. Complex boolean Walls, path connections, graph topological relation edits, and multi-object state transactions remain missing.
4. Independent full original 45-task D0/I0 validation and prospective honest full-set/support-subset metrics, then obtain explicit API budget to compare real GPT-6 Luna XML vs Python in the same model/tool/feedback conditions. This PR is not such a comparison.
