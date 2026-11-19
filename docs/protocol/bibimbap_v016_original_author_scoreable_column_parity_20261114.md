# BIBIMBAP v0.16 — Verified original-author-callable Column D0/I0 native parity (research-only)

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/146
**Parent:** v0.15 Issue #144 / Draft PR #145, commit `3960c5e1aee4d8ae8e6c1e7c139f9fd733c7e7b5`
**Status:** nonblinded prospective implementation of independent *developer* I0, paired against historical frozen public D0, **NOT** a real matched LLM comparison.

## 1. Exact original-public scientific scope

This version builds one of the first *original-author-scorer-callable* native source-only D0/I0 equivalence checks, distinct from earlier v0.15 Window cases whose original author test data produce a `RuntimeError`. Only two **public** original tasks are executed:

- `test_15`: `IfcColumn` with the publicly named original GlobalId, translated **-3m along world Y**, in actual `basic_tasks.ifc` IFC4X3.
- `test_16`: the publicly named original `IfcColumn` is deleted in actual `basic_tasks.ifc`, preserving original unrelated native IFC objects/relationships and native shapes.

**The selection of these two tasks is informed by prior developer D0 evidence, so results are nonblinded, non-held-out, not a random 45-case sample.** Historical frozen v0.3 developer D0 report `reports/bibimbap_v3_column_d0_test15_test16_20261113.json`, SHA-256 `f358d3f65fe89734078ff6712f2543d578fac043e915c9baad6280dbaa7906b7`, already recorded original-author D0 score 1.0 and 0.5. Those prior outcomes are used only **after** newly authored I0 candidates pass native source validation; neither I0 code nor target selection reads D0 output or author target metrics.

## 2. Author/data official correction provenance (read-only)

At 2026-11-14 Asia/Seoul, independently queried live *remote default branch HEAD* without fetching/replacing the source:

- GitHub `https://github.com/nbharathik/bibimbap.git`, `main` remote HEAD `667004e16bd38fd7d538bcee56191465429fd975`.
- HuggingFace `https://huggingface.co/datasets/clemenskujat/bibimbap-data`, `main` remote HEAD `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`.

Both are byte-exact versions used in prior experiments. Therefore there is **no verified correction in either remote default branch at the time of inspection** to the v0.15 original `geometry_test_18/19` missing-original-Window target reference. This does not rule out a pending issue, unmerged PR, nondefault branch or future fix. The frozen author/dataset code is never patched or retuned; any corrected version would require new data provenance and a separate prospectively frozen analysis.

## 3. Immutable source and independent implementation

`tools/bibimbap_v016_original_column_i0.py` is the complete independent imperative authoring implementation; it imports **no `src`, `tools`, D0 projection/compiler, grader, prior output, or hidden ground-truth code**. Its target and operation are parsed exclusively from the PUBLIC task question. It reads the **original IFC4X3 normalized to metres**, checks source native placement and ownership, and executes:

- Update: modify only original native IfcCartesianPoint coordinates along Y, preserving STEP identity and world native mesh.
- Delete: preflight source IFC native inverse relationship ownership and call `ifcopenshell.api.root.remove_product` on a fresh source clone. Do not fabricate a new source model.

Original source IFC is verified byte-identical and never overwritten; outputs use only unused paths in isolated temporary directories. Invalid prompt drift, schema/unit mismatch, shared placement, unsupported native dependency and destination collisions are rejected.

`tools/audit_bibimbap_v016_scoreable_column.py` enforces the following exact ordering:

1. Validate pinned 45 original public-task identities, 15 create / 15 update / 15 delete, and original source sha.
2. Build and independently validate **both I0 IFC candidates first**, using the already present independent task-specific native IFC-only Column oracles (`strict_move_column` and `strict_delete_column`); freeze their SHA.
3. Read previous v0.3 D0 evidence **only after I0 freeze**. Recreate original *whole declarative Column XML state* for both tasks using original public question IDs parsed independently, infer mutation by stable identity (not XML commands), and compile via historical unmodified v0.3 XML engine.
4. Independently native-oracle verify both D0 candidates and reject if the complete output native IFC SHA or public millimetre-unit IFC SHA differs from the historical frozen D0 report. For both tasks, I0 and D0 native candidate entire file SHA is **byte identical**.
5. **Only after all four IFC candidates and their hashes are frozen**, run the pinned original-author worker on D0/I0 separately, converting each native IFC back to the originally public millimetre unit. Recheck candidate original hashes after scoring. Preserve raw source unchanged.
6. Build a sanitized versioned 45-task denominator matrix based on frozen original v0.12 classification, without copying full public question text, target GUID literals or the hidden author scorer/solution into the report. Unscored 41 tasks are **unknown**, not automatically unsupported or scored zero.

The two arms share the real IfcOpenShell native backend, so matching complete output bytes prove **engineering native semantics parity for these two explicit tasks**, not causal impact of LLM representation on task performance. The XML direct-markup arm is still a bounded typed source view, not the full native IFC input exposed to Python. No model was invoked.

## 4. Actual frozen output and author-scorer outcome

| Original public task | Developer XML D0 author metric | Independent developer Python I0 author metric | Whole native IFC I0 == D0 | Independent native IFC oracle |
|---|---:|---:|---|---|
| `test_15` — Column move Y=-3m | **1.0** | **1.0** | SHA-256 byte identical | PASS |
| `test_16` — Column delete | **0.5** | **0.5** | SHA-256 byte identical | PASS |

**Important author metric disagreement:** `test_16` yields original author `object_not_exists = 1.0` but `integrity_constraint = 0.0` for **both exact same I0/D0 IFCs**, despite the earlier independent native original IFC relationship/product preservation oracle returning PASS. Therefore author score and independent IFC structural integrity quantify **different checks**; we do not change the author score or declare overall task success. `test_15` author submetrics (`integrity_constraint`, `right_dimensions`, `right_location`) are each 1.0 for both arms. These are nonblinded developer results, not scores from LLM inference.

Original **45-case intention-to-test denominator remains exactly 45** with original CRUD counts preserved:

| Classification demonstrated as of v0.16 | Count |
|---|---:|
| Confirmed both developer arms, callable pinned original author score (`test_15`, `test_16`) | 2 |
| Confirmed both developer arms, original author worker failed due already absent original source Window targets (prior `geometry_test_18/19`) | 2 |
| Not verified with the above exact paired original-task + scorer protocol | 41 |
| **Total** | **45** |

Other 41 have NOT been proved either compatible or incompatible. Do not treat the above 2/45 as a model task success or population-wide source coverage estimate. Historical read-only 45/45 catalogs did not establish 45 native write parity. All scores remain pinned to unmodified *author-source* metrics, distinct from independent full-task correctness.

## 5. Evidence and costs

- New immutable `reports/bibimbap_v016_original45_scoreability_and_column_parity_20261114.json`, **SHA-256 `162ff7408429062b4e80abb3fe48bb6bb1b0c0bff51260d04d0a616d7a104ae7`**. Independently reexecuted to a second unique ignored output, producing **byte-identical JSON SHA-256**. Report stores **only** public source/question hashes, hashed public target identity, native output SHA, author metric component results and original all-45 status; no full public IFC, hidden author target GUID list or model provider output.
- Other frozen reports / original datasets untouched. Original author code and data checkout remain on pinned HEAD with clean Git status.
- **New paid model/API requests: 0, USD: 0.** This audit runs original-author evaluator only for the two genuinely scoreable public Column tasks, not a 45-task benchmark sweep.
- **Scoped tests:** independent source-only authoring, original dataset SHA checks, duplicate output/invalid unit/prompt rejection, both original IFC native oracle checks, full 45 population count and no failure imputation, source-code import graph guard, deterministic audit replay. Historical v0.14 and v0.15 test modules should be run alongside the new module for integration scope; broad all-repository 832-test suite remains separately BLOCKED on previous worktree fixture/legacy gate issues. Do not call scoped suite a full regression.

**Actual scoped regression run:** `python -m unittest tests.test_experimental_v3_column_crud tests.test_experimental_v14_native_window_delete tests.test_bibimbap_v14_original_hosted_d0 tests.test_bibimbap_v015_i0_source_parity tests.test_bibimbap_v015_fixture_admission tests.test_bibimbap_v016_scoreable_column -q`, **73 tests / 73 PASS / 0 FAIL / 102.783 seconds / exit 0**. New v0.16 8 tests alone PASS in 11.020 seconds. This is a selected 6-module legacy+new code regression, not whole-repo discovery.

## 6. Offline exact reproduction

Requires only the existing pinned local publicly sourced Git checkouts and previously retained reports, no network downloads or new inference.

```powershell
$base='D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue146-scoreable-column-i0')
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'

& $py -m unittest tests.test_bibimbap_v016_scoreable_column -v

# Always choose a previously UNUSED output path; never overwrite historical evidence.
& $py -m tools.audit_bibimbap_v016_scoreable_column `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') `
  --frozen-v3-d0-report 'reports/bibimbap_v3_column_d0_test15_test16_20261113.json' `
  --frozen-v012-matrix 'reports/bibimbap_v012_actual_original45_native_read_and_D0I0_matrix_20261114.json' `
  --frozen-v015-report 'reports/bibimbap_v015_original_hosted_window_i0_d0_parity_20261114.json' `
  --output 'results/NEW_UNIQUE_issue146_column_audit.json'
```

## 7. Next research gates

1. **Scientific evaluator validity**: document/seek original author upstream correction or acknowledgement of `geometry_test_18/19` missing target GUIDs and `test_16` integrity disagreement; do NOT patch a new score into historical runs. Any new correction is a *new data/scorer version* with new preregistration and separate result.
2. **Common editable task set**: continue single original public tasks with native source geometry, independent D0 and I0, and both actual callable source scorers; include still-unsupported/unknown original tasks in 45 denominator.
3. **Full held-out LLM A/B causal design**: XML D and Python I arms currently differ in source information accessible; test matching ability, prompts/model, tool budget, independent scorer, original task difficulty and original source role coverage before any paid paired LLM claim. **New paid inference requires explicit budget authorization.**
