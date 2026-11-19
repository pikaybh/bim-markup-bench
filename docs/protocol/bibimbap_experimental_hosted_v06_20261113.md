# BIBIMBAP — prospective native IFC4X3 hosted v0.6: Opening + Door/Window dependent lifecycle

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/126

**Date:** 2026-11-13 Asia/Seoul

**Strict scope:** Independent `pikaybh/bim-markup-bench` research only, no BIXML/Xim production, no modifications to original BIBIMBAP author/dataset, no change to v0.1–v0.5 prospective backends, no modifications to previously paid GPT-6 Luna 45-task scores. **New model calls: 0, additional API cost $0.** Neither v0.6 nor prior v0.x feature slices are yet connected to the #114 matched-25 paid model arm.

The original public BIBIMBAP IFC dataset was pinned at `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`, original author benchmark evaluator at `667004e16bd38fd7d538bcee56191465429fd975`. Original millimetre IFC inputs are cloned and normalized to metres for v0.6; author grading occurs on independently reconverted millimetre output IFCs only **after** the developer-owned XML state was compiled.

## Why a new hosted implementation was needed

Earlier `src/runtime.hosted_door_delete.preflight_door_opening_deletion` expected exactly one native `IfcRelSpaceBoundary` on the deleted Door. The public **`test_17`** Door in `basic_tasks.ifc` has **no** such boundary, although its actual dependency graph includes:

- One original native `IfcRelFillsElement` linking the Door and `IfcOpeningElement`.
- One `IfcRelVoidsElement` linking that Opening and original host `IfcWall`.
- Original Door containment, shared or exclusively owned classification, material, type and two property sets.
- Original IFC product/world mesh and the host Wall's actual physical void.

The former strict special-case rejection was not a true lack of IFC capability. However, simply deleting the IFC Door leaves a dangling Window/Door opening. A bounded **declarative XML pair removal** is a safer input contract than imperative commands to the LLM.

The original IfcOpenShell `root.remove_product` API also leaves a *singleton* `IfcRelAssociatesClassification` with an empty `RelatedObjects` tuple when the last related filling is deleted. This invalid native membership must not be silently preserved. v0.6 explicitly removes only this original single-member now-empty classification relation, while **never deleting a shared classification**. Every other relation is derived from the source IFC before mutation.

## Prospective v0.6 — exact supported state differences

The LLM authoring surface is a **complete original XML model state**. The trusted compiler `src/runtime/experimental_v6_hosted.py::compile_declarative_xml_v6` parses/binds original+edited documents, validates immutable source hash, and derives stable-ID semantic graph differences.

| XML state delta | Backend native result | Source-pinned constraints |
|---|---|---|
| Change exactly **one existing filled Opening's** `offset` value | `MOVE_FILLED_OPENING` | Exactly one original IfcDoor/IfcWindow filling, uniquely original Wall-hosted void, native Opening placement relative to Wall with exclusive CartesianPoint, filling placement relative to Opening; no overlaps, no wall overflow, no unsupported SpaceBoundary or unknown references |
| Remove exactly **one original Door + its original Opening** | `DELETE_HOSTED_FILLING_AND_OPENING` | Remove original `IfcRelFillsElement`, `IfcRelVoidsElement`, uniquely owned Psets and solitary native classifications; retain host Wall, original surviving IFC Products, all other original world meshes and correctly updated shared relation members |
| Remove exactly **one original Window + its original Opening** | same operation | Same exact pair ownership and inverse relationship whitelist. **This is a developer cascade policy** if the public instruction only says to delete the opening; the resulting original author grade may penalize unexpected removal |

No operation-list XML, `Create`, `Move`, `Delete`, `Set` command or direct IfcOpenShell tool is exposed to the declarative model. The trusted compiler always clones the source IFC, refuses an occupied destination, validates results on an isolated staged candidate, then commits atomically. Unknown inverse relations or source assumptions fail closed without an output IFC.

**Not supported:** create a new Door or hosted Opening, create Slab opening, delete only an empty original Opening, delete only a filled Window retaining its Opening, move/rotate underlying host Wall with filling, deleting a host Wall with nested fills/voids, nonrectilinear hosted void transformation, unsupported source schemas including IFC2X3/IFC4, multiple edits per state transaction, rebuilding space-boundary topology. v0.6 is not a complete BIM authoring language, not a paper-equivalent 45-task backend, and not a claim that model-generated XML can solve these tasks.

## Independent actual IFC geometry oracle

`tools/oracle_bibimbap_hosted_v06.py` does **not** import runtime compiler, binder, XML graph planner, original author scorer, or the existing hosted-door helper. It separately reopens IFC4X3 source and candidate and checks:

- The original `IfcRelVoidsElement`, `IfcRelFillsElement`, filling and host's typed GlobalIds and original inverse dependency closure.
- On **move**, exactly one native `IfcCartesianPoint` changes; all original IfcRoots and other STEP IDs retain identical source representations; native Opening and original filling **entire vertex clouds** and triangle counts translate by exactly the original host's local X converted to world coordinates; host Wall void actually changes position yet maintains its original volume; every unrelated original IFC Product remains.
- On **pair delete**, original Filling/Opening and exactly their owned relation/Pset roots disappear, shared material/type/classification/containment relations have the correct surviving members, and **no native classification relation becomes empty**. The host Wall remains and its original opening closes physically, increasing host solid volume by the deleted opening's original volume. Original other IFC product meshes, native surviving Roots, presentation-layer membership and STEP ownership closure remain untouched. New native IFC OwnerHistory is permitted only for a changed shared native Type relationship.
- Adversarial mutations to a surviving original Window name or Door name are rejected by the independent oracle. A wrong declared move direction/distance also fails.

The original Revit-mapped Door tessellation contains overlapping/non-watertight triangles. The geometry kernel's naive signed-volume estimate may change slightly when this *identical* mesh is translated rigidly, even though all vertices translate exactly. The independent move oracle therefore checks **all world vertex coordinates and native triangle counts**, not strict signed-volume equality for the moved filling. It still checks host solid volume and opening geometry/transform. This is a measured numerical caveat, not an exemption for missing or mismatched geometry.

## Original public author D0 (developer-authored fixed XML, **NOT a new LLM run**)

Only the public original question and original public IFC were used to select/author input states in `tools/audit_bibimbap_hosted_v06_d0.py`. Candidate scoring used the pinned original author evaluator **after** compiled IFC output, never exposed to a model or reused as a prompt. This was fixed D0, not GPT-6 Luna inference, not a matched 25-tool parity evaluation.

| Original public test | Fixed source-only selection and XML change | Original author grade | Interpretation |
|---|---|---:|---|
| `test_17` | Delete named native Door `11kJIqz$n2Jf_DfJV1SDY7` plus its uniquely filled Opening, leaving its host Wall | **0.5**: object absence 1, integrity 0 | Independent typed native host/void/relationship cleanup PASS; original-author stricter integrity not satisfied |
| `test_18` | Delete named Opening `0APGbZXNKfgPNB$VQQZ0pi` **and the Window filling it**; exact developer-declared cascade, not a hidden reference expectation | **0.5**: object absence 1, integrity 0 | Original author may require different semantics; record partial only |
| `geometry_test_13` | Select the only original Window wider than 1.50m (native reported 1.6m) and move its hosted Opening **+3m global X** with filling following | **0.666667**: dimensions 1, integrity 1, location 0 | Independent full physical native vertex translation PASS; author's location semantics remain unresolved |
| `geometry_test_16` | Find unique original center Door between two public named original Door GUIDs by original public IFC world X centers, then remove its Door+Opening | **0.5**: object absence 1, integrity 0 | Independent native relationship and host closure PASS; stricter author integrity still fails |

Original fixed D0 report: `reports/bibimbap_hosted_v06_developer_d0_20261113.json`, final SHA256 `a4252265919e1d7456a53fae1d6afbf7e8cda22bed47a31148c2af762313082f`, with original public task/question and source checksums, developer's explicit planned edits, candidate IFC SHA, both independent native and original-author metric results. Original IFC files are **not committed**, only hashes. Existing historical #112 real paid LLM full-mark score (3/45) remains unchanged.

There is no D0 full-mark claim on these tasks. `topological_test_13` has a **positive native hosted Window shift** isolated test but no claim of satisfying the original full target-contact geometry or original-author D0. Original `test_01` and `topological_test_05` Door CREATE remain missing; they should not enter the supported denominator.

## New offline tests and reproduction

Final combined v0.6+v0.5 Wall+v0.4 Slab+v0.3/v0.2 Column+original 45-case native-audit+25-tool offline runner+legacy compiler regression: **125 tests run, 123 pass, 2 optional skipped, 0 failed**. No provider calls made during either individual or combined tests.

`tests/test_experimental_v6_hosted.py` contains **17 positive/negative** original-IFC-native deterministic tests. They include actual original `basic_tasks.ifc`, original geometry-test 13/16, original topological-test 13, window/door move, pair deletion, removal of source-only singleton classification relation, and negative cases for wrong source hash, existing output, no-op, removing only one member of the pair, empty/unfilled Opening, multiple edits, unrelated Wall change, colliding or overflowing hosted void, and corrupted other IFC Products.

```powershell
$base='D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue126-hosted-v06')
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$author=Join-Path $base 'bibimbap-author-upstream'
$data=Join-Path $base 'bibimbap-author-data'

& $py -m unittest tests.test_experimental_v6_hosted -v

# D0 script refuses overwrite. Supply a NEW unused report path.
& $py -m tools.audit_bibimbap_hosted_v06_d0 --author-repo $author --dataset $data --output-json 'results/YOUR_UNUSED_HOSTED_V06_D0_REPORT.json'
```

## Next actual parity blockers

1. **Original-author integrity discrepancies:** investigate public scorer and physical relation invariants without optimizing fixed D0 results after observing grades. Separate strict author equality from independent IFC correctness. In particular deleting the filled Opening may not be equivalent to deleting only the Door; the current policy is explicitly prospective and restricted.
2. **Host-native Door/Opening creation** including void clipping, unique IFC geometry and filling, spatial placement and material/type consistency, plus Slab cutout. No pseudo-command XML.
3. **Nine source projection blockers** (schema IFC2X3/IFC4, complex/sloped/voided/mapped geometries) with exact original source coverage and no false flattening. Track D0/I0 gates per public original task.
4. Only after true independent original 45/45 source+operation D0/I0 eligibility, freeze matched real-model experiment and obtain fresh explicit paid API authorization. External paper numbers are not direct causal equal-condition benchmarks.
