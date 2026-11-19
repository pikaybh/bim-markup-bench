# BIBIMBAP full 45-task XML/native-IFC capability gap — evidence-based audit

**Issue:** [#116](https://github.com/pikaybh/bim-markup-bench/issues/116)
**Date:** 2026-11-13 (Asia/Seoul)
**Scope:** Independent *experimental* `pikaybh/bim-markup-bench` repository only. The real BIXML/Xim product was not read, touched, forked or deployed. New LLM inference **0 requests**, API **$0**. Old #112 score and source/raw provider records preserved byte-for-byte.

**This is a structural/runtime eligibility audit, NOT a claim of 45 task oracle success, complete Xim, or a new language-model benchmark.**

## Authoritative source and scope

- Original BIBIMBAP public [dataset](https://huggingface.co/datasets/clemenskujat/bibimbap-data) commit `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`; pinned original [author repository](https://github.com/nbharathik/bibimbap) commit `667004e16bd38fd7d538bcee56191465429fd975`.
- The **45/45** public editing instructions (15 Create / 15 Update / 15 Delete and 15 basic / 15 geometry / 15 topological), each public source IFC, original schema and source GlobalId inventory were read independently. The taxonomy is derived **only from public question text**, without using private original author grader Python/expected geometry/GT to construct an input the model could see. Public question SHA256, source IFC SHA256 and native source file inventory are recorded per task, not redistributed IFC bytes.
- BIBIMBAP #112 actual one-shot result JSON is frozen at commit `8b29349f365780e86c6294c90fc5b94e4c42ef91`. Existing 45-case original-author outcome remains **3/45 full marks**, zero-filled mean `0.1962966667`, estimated usage cost `$0.0527285`. **None of these historical measurements were rerun, repaired, rescored or overwritten.**
- Compiler source/hash and XSD schema/hash are pinned in this audit; the matrix is reproducible from public source and production-independent test-only compiler code.

## Measured static task eligibility (exact 45-denominator)

| Mutually exclusive present-day gate | Count | Meaning |
|---|---:|---|
| Existing operation implemented in narrow compiler slice, strict task oracle not guaranteed | **2** | `test_05` wall create, `geometry_test_11` wall height |
| Native operation exists but source/relations/geometry require specific eligibility and task oracle | **12** | e.g. Wall delete with dependencies, Window removal, hosted offset, room enclosure |
| Native mutation operation **not implemented** | **20** | e.g. create Column/Slab/Door, wall rotate/shorten, column/delete/pose, space deletion |
| v0.1 XML declarative vocabulary **cannot express** required state | **2** | `test_03` slab-hosted opening, `topological_test_14` Beam trim |
| Original IFC source cannot be projected by experiment's IFC4X3-only restricted geometry reader | **9** | 2 IFC2X3, 1 IFC4, 6 IFC4X3 with tilted/mapped/boolean unsupported geometry |
| **All original editing tasks** | **45** | No task silently removed |

The nine source-blocked task IDs: `geometry_test_01`, `geometry_test_03`, `geometry_test_04`, `geometry_test_05`, `geometry_test_14`, `geometry_test_15`, `topological_test_05`, `topological_test_11`, `topological_test_17`.

Two operation-family examples show why treating all IFC4X3 input as automatically comparable is incorrect:

- Source-projectable IfcDoor+Opening and IfcColumn definitions can exist in XML, but the trusted compiler has **no general creation code for either**. The language may express the requested entity without the backend being able to materialize it.
- The XML contains a `Wall` endpoint geometry but the existing update code only edits swept-wall **height or thickness**, not planar translation/rotation/length. Twenty-five tool calls cannot overcome that missing backend operation.
- Only a safe *isolated* native Door+Opening deletion is implemented; a request to delete one Door may require wider relationship cleanup. Runtime conditional support does not mean original task-level correctness.

### Breakdown by operation

| CRUD | Fully identified restricted operation slice | Conditional | Native missing | XML schema gap | Source blocked |
|---|---:|---:|---:|---:|---:|
| Create | 1 | 2 | 6 | 1 | 5 |
| Update | 1 | 2 | 8 | 1 | 3 |
| Delete | 0 | 8 | 6 | 0 | 1 |

## Offline forensic replay of all 21 historical model-edit failures

This is not new paid inference: existing exact provider texts and source IFC clones were read from **Gitignored** worktree `bim-markup-bench-issue112-full45/results/bibimbap_original_45_luna_20261112_issue112/`. Every actual model response hash and exact source hash were checked against its prior evidence. The trusted compiler was invoked on disposable temporary files; no altered XML was submitted or repaired, and original response/score/dataset files remained immutable.

| Replayed native rejection | Count |
|---|---:|
| Target class creation handler missing | 6 |
| Existing geometry modification not implemented | 4 |
| Relationship addition/deletion unsupported | 2 |
| Native deletion scope unsupported | 2 |
| Dependent Wall deletion rejected | 3 |
| Strict Door+Opening paired-deletion precondition not satisfied | 1 |
| Invalid hosted Opening offset (model-authored state) | 2 |
| Invalid XML reference to deleted/absent Wall | 1 |
| **Total** | **21** |

Important: **invalid XML and out-of-range Opening placement are genuine candidate/source-state failures**, not automatically evidence that implementing a new compiler operation would make a given model output correct. Other categories represent unsupported trusted backend preconditions or operations. This taxonomy therefore distinguishes *model-produced semantic invalidity* from *compiler capability* and does not attribute every failure to the LLM.

## New independent native IFC oracle — `geometry_test_11`

Original public task: decrease **all walls in the second storey** by **0.5 m**.

Implementation: `tools/oracle_bibimbap_geometry11_height.py`. This oracle reads actual IFC in **metres**, never calls the model, never uses the XML compiler/source parser or the original author grader, and checks **all serialized STEP entities plus actual world-space wall meshes**.

Verified against the **previously stored exact model-generated native IFC**, NOT a newly optimized or model-repaired result:

- Second storey is resolved by actual `IfcBuildingStorey.Elevation` and `IfcRelContainedInSpatialStructure` container identity.
- **6 of 6** second-storey walls reduced in extrusion depth by exactly **0.5 m**.
- All **6 other storey walls unchanged**.
- The native IFC `IfcExtrudedAreaSolid` depth and **world-space mesh top height** each decrease by 0.5 m while bottom remains fixed.
- **All 429 STEP entity IDs preserved**; **exactly 6 entities changed**, and they are the target six extruded solids; no other object, property, relation or identity serialized as STEP changed.
- The previous original author graded this case **1.0**. Our independent result is a task-specific **strict native height edit + preservation** verification, **not** a blanket assertion about all other tasks, collision-free model completeness, or equal backend capability.

Independent negative controls use fresh clones of the real public IFC (never prior user outputs): no-op, wrong height on one wall, wrong-storey wall edit, unrelated wall rename, and added unrelated IFC entity all correctly FAIL. Fixed developer-authored 6-height-change candidate PASSES. This is **offline deterministic engineering evidence** and must not be labeled a new LLM trial.

Git-safe result files:
- `reports/bibimbap45_capability_audit_20261113.json` — full 45-row evidence matrix and 21 replay categories
- `reports/bibimbap_geometry_test11_independent_native_oracle_20261113.json` — real previous model-result native evidence, per-wall IFC shape world-Z extents, full STEP preservation audit
- This protocol; repeatable read-only checks and negative-control tests

## Required next priorities, in order

1. **Freeze and review this 45-row gap matrix** and the next experimental-only compiler/evaluator changes as a NEW prospective version (historical #112 outcomes must not be relabeled). **Done in #116**.
2. **Implement deterministically verified native IFC operations by impact, never by selecting known model outputs:** column create/delete/height/placement affect at least **10** of 45 public tasks; slab create/move/reshape at least **6**; wall plan transforms and dependent deletion at least **7**; hosted door/window and opening/topology require separate relationship/geometry tests. Each must carry independent D0 positive/negative IFC fixtures, immutable source preservation, and no accidental spatial/pset damage.
3. **Add source-format compatibility** for the 2 IFC2X3, 1 IFC4, and six geometrically complex IFC4X3 sources without faking geometry or dropping opaque dependencies. Check every original IFC GUID, native geometry/relationships and robust forward/backward schema semantics; this is not a generic version-string replacement. `geometry_test_05` original source is IFC4 (with a storey), not IFC4X3.
4. **Add an independent, task-specific native semantic and geometry oracle for each remaining case.** Original author score 1.0 or positive Update no-op credit cannot substitute for this; route held-out scorer to a separate trusted process.
5. **Run offline, per-task D0 XML vs I0 Python known-positive fixtures, for all 45 tasks**, before any more paid model calls. Only after each arm's task oracle is verified should a new prospective paired GPT-6 Luna budget be requested; record entire 45 ITT as well as predeclared common-supported subset separately.
6. Keep model/turn parity settings of #114 but **do not call #114 'paper equivalent'** while backend coverage and strict task oracles are incomplete. All known mismatches remain in the study report.

### Reproduce (no API calls)

```powershell
$base='D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue116-45-capability')
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$author=Join-Path $base 'bibimbap-author-upstream'
$data=Join-Path $base 'bibimbap-author-data'
$replay=Join-Path $base 'bim-markup-bench-issue112-full45\results\bibimbap_original_45_luna_20261112_issue112\geometry_test_11'

& $py -m unittest tests.test_bibimbap45_capability_oracles -v
& $py -m tools.oracle_bibimbap_geometry11_height --source (Join-Path $replay 'source_normalized_m.ifc') --candidate (Join-Path $replay 'model_compiled_m.ifc')
```

Full 45-row matrix generation (including all 21 historical forensic replays) is available through `tools.audit_bibimbap45_capability` with `--author-repo`, `--dataset`, `--replay-dir` and **a new non-existing `--output-json` path**; it deliberately refuses to overwrite historical or published reports. Reports contain hashes/provenance and category evidence, not model-generated raw IFC/large original input files or private grading code.

**Status: gap diagnosis and one independent task-specific native oracle delivered; full XML/IFC functionality parity remains unimplemented.**
