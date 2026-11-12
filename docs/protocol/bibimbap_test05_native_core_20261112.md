# Public-task IFC core vs original BIBIMBAP scorer, test_05 (2026-11-12)

Tracking [Issue #108](https://github.com/pikaybh/bim-markup-bench/issues/108), stacked on heading-control [#104](https://github.com/pikaybh/bim-markup-bench/issues/104) and original evaluator work [#102](https://github.com/pikaybh/bim-markup-bench/issues/102).

## Evidentiary scope

The public task states *"Add a wall with a length of 15m beginning in (0, -10)."* Direction is free. Our **read-only native IFC task-core checker** in `tools/bibimbap_test05_native_core.py` is separate from the XML compiler and **does not import or invoke original author grader code**. Its criteria are specified from the public task:

- Original IFC4X3 and edited IFC4X3 in original millimetre units, parsed as native IFC;
- Exactly **one** new `IfcWall` identified via native IFC root GUID difference;
- All existing `IfcRoot` GUID/class identities retained (note: this is weaker than unchanged native geometry);
- Native IFC world-space XY mesh longest vertex-to-vertex span within 0.05 m of 15 m (slight thickness diagonal allowed);
- Native world-space geometry has a vertex within 0.5 m of the required start location (0,-10);
- IFC originals and predictions unchanged by the read-only evaluation, checked by SHA.

**Do not call this a full independent strict scorer or blind evaluation.** The broader research team previously inspected the original BIBIMBAP evaluator. This checker uses its own source-code path and the task's public properties only, but is not investigator-blind. Furthermore, it **does not independently validate clashes, unrelated original geometry invariance, wall material/type semantics, or broader BIM relationships**. Its field `full_independent_strict_task_success` is deliberately **null** for every case. A positive `public_task_core_success` is only a task-core geometry outcome.

## Actual native results, development controls only

Five developer-authored declarative XML variants were compiled by the existing runtime, restored to the original BIBIMBAP millimetre IFC and evaluated separately by this native checker and the **unchanged original author scorer**.

| Developer input | Native IFC max horizontal extent | Native public task core | Original author score |
|---|---:|---|---:|
| 0°, 15 m | ~15.0013 m | PASS | 1.000000 |
| 30°, 15 m | ~15.0013 m | PASS | 1.000000 |
| 45°, 15 m | ~15.0013 m | PASS | 0.916675 |
| 90°, 15 m | ~15.0013 m | PASS | 0.916675 |
| Wrong 10 m | ~10.0020 m | FAIL: length | 0.750000 |

The source-identical, merely unit-normalized IFC **also fails** the native core (no added wall). Thus both under-length and unchanged negative controls are correctly rejected despite the original author scorer's partial-credit behavior.

**Why some 15 m author scores differ:** The author metrics return correct location and dimension for all 15 m cases, while the original integrity subscore drops from 1.0 to 0.6667 at 45° and 90°. This is compatible with introducing a collision in those directions; the present native core checker does not resolve that issue. It would be **incorrect to say the original evaluator has a directional length defect**, or that a collided native IFC is necessarily a complete correct BIM result.

## Original/source preservation and rights

- Original author code pinned at `nbharathik/bibimbap@667004e16bd38fd7d538bcee56191465429fd975`, dataset at `clemenskujat/bibimbap-data@f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`; neither vendored into this Git repo. No license for the author code verified.
- New report `reports/bibimbap_test05_heading_native_core_20261112_v3.json` records native IFC result hashes, geometry properties, original author metric vectors, no-op controls and **zero LLM calls**. It does not include private answer files.
- Prior v1/v2 heading evidence from #104 and original P0/GPT-6 Luna reports remain unchanged. The full 45-task prospective launch gate #106 stays `NOT_READY` and no new paid inference is authorized.

## Offline reproduction

From independent Windows worktree `D:\문서\D__1_Projects\202611\bim-markup-bench-issue108-native-core`:

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$env:BIBIMBAP_AUTHOR_REPO = Join-Path $base 'bibimbap-author-upstream'
$env:BIBIMBAP_DATASET = Join-Path $base 'bibimbap-author-data'
Set-Location (Join-Path $base 'bim-markup-bench-issue108-native-core')
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
& $py -m unittest tests.test_bibimbap_native_core tests.test_bibimbap_test05_heading tests.test_bibimbap_author_integration -v
# For rerun, provide an UNUSED filename; current evidence is write-once.
& $py -m tools.audit_bibimbap_test05_heading --author-repo $env:BIBIMBAP_AUTHOR_REPO --dataset $env:BIBIMBAP_DATASET
```

**Next scientific gate:** independent collision/untouched-IFC geometry checks against source and edit results, plus strict success criteria for the remaining editing task families, before prospectively freezing any model experiment. No XML-vs-API causal claim follows from these non-LLM controls.
