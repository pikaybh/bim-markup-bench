# BIBIMBAP Original-Author Grader — Reproducible XML-Only Pivot (2026-11-12)

**Tracking:** [Issue #102](https://github.com/pikaybh/bim-markup-bench/issues/102). **Status: author-grader and one developer-authored XML/IFC witness verified; NO paid LLM experiment or official model comparison yet.**

## Upstream provenance (do not vendor without license verification)

- Authors' code: [nbharathik/bibimbap](https://github.com/nbharathik/bibimbap), pinned commit `667004e16bd38fd7d538bcee56191465429fd975`.
- Original task/IFC data: [clemenskujat/bibimbap-data](https://huggingface.co/datasets/clemenskujat/bibimbap-data), pinned commit `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`. Dataset card specifies CC BY 4.0.
- The authors' GitHub repository has **no root LICENSE file** at the pinned snapshot. Do not redistribute or copy its test code into this project until copyright/license status is clarified. This project stores only its own audit programs, task identifiers, metadata hashes and control scores.
- Source and dataset repos are cloned **outside** the BIM Markup Bench Git repository under sibling paths `bibimbap-author-upstream` and `bibimbap-author-data`. Clone SHA and clean Git status are validated before every audit.

## Actual original corpus and scorer behavior

- Dataset: 100 natural-language prompts, 55 retrieval and 45 edit tasks. Edit tasks: 15 Create, 15 Update, 15 Delete; 15 Basic, 15 Spatial/Geometry, 15 Topological.
- Exactly **45/45 original author `data/tests/<test_id>.py` files** expose an AST-verified `execute_test(original_ifc, edited_ifc, model_output)`.
- Each referenced original IFC exists physically and is checked as a STEP IFC, not an LFS pointer or fabricated substitute. 31 unique IFC inputs occur among the 45 edit tasks.
- The 45 tests were **actually executed** as independent subprocesses using two identical cloned IFC inputs. **45/45 returned `SCORED` without exceptions or timeouts**, no original file changed. Evidence: `reports/bibimbap_original_45_noop_20261112.json`.
- All 15 Create and all 15 Delete tasks scored **0.0** for no modification. All 15 Update tasks got **positive partial credit** despite no modification (mean approximately **0.62**) because preservation/location/dimension submetrics may hold on unchanged objects. This is an expected consequence of *graded subcriteria*, **not 15 successful edits**. The overall original no-op edit mean is therefore about 0.207, not necessarily strict edit pass rate.
- Positive developer-authored IFC controls, not XML: `test_15` column translation scored **1.0**; `test_16` column deletion scored **0.5** (object removal passes, integrity fails). Evidence: `reports/bibimbap_author_positive_witness_20261112.json`.
- **No paper baseline reproduction claim**: no published provider inference was rerun, and each author's published aggregate may reflect a different historical model configuration. This code verifies *original scorer execution* and specific control behavior, not numerical reproduction of the paper's overall 50.2%.

## Unit, schema and projection compatibility

All 45 edit task inputs use native IFC length unit **millimetre** (`calculate_unit_scale == 0.001`). The current BIM Markup Bench XML compiler requires **IFC4X3 and metre units**; direct IFC projection would reject every raw BIBIMBAP input. There are:

- 42 editing tasks with source schema IFC4X3;
- 2 editing tasks with source IFC2X3: `geometry_test_03`, `geometry_test_04`;
- 1 with IFC4: `geometry_test_05`.

A trusted adapter can normalize a **working copy** with `ifcopenshell.util.unit.convert_file_length_units(original, "METER")`, project to declarative XML, compile the edited XML on the normalized IFC, and restore the resulting IFC to `MILLIMETER` for **original author evaluation**.

This unit roundtrip was independently applied to **all 45 source cases** and re-evaluated with the original author scorer. **45/45 cases preserved the exact original no-op score and per-metric result, IFC root GlobalId/class inventory and original source bytes**, while preserving each original IFC schema. Evidence: `reports/bibimbap_45_unit_roundtrip_20261112_v2.json`. This establishes *rubric parity on unchanged input*, **not** full geometric equivalence of arbitrarily changed IFCs.

Actual source projection preflight after normalization:

| Disposition | Editing tasks |
| --- | ---: |
| XML source projection succeeded | **36** |
| Schema unsupported by compiler | **3** |
| No editable simple swept-solid geometry (complex mapping/Boolean) | **4** |
| Tilted swept-solid frame unsupported | **2** |
| Total | **45** |

Evidence: `reports/bibimbap_45_xml_projection_20261112.json`. **36 projected != 36 editable/scorable.** Projection can preserve non-editable IFC content as opaque. Task-specific CRUD support needs a separate proof.

## Real XML -> IFC -> original BIBIMBAP scorer witness (NO LLM)

The *first actual supported BIBIMBAP edit* is `test_05`: "Add a wall with a length of 15m beginning in (0,-10)".

Trusted offline demonstration (`tools/verify_bibimbap_xml_author.py`):

1. Open pinned `basic_tasks.ifc` in millimetres, independently clone/convert to metres.
2. Project the verified source into the existing read-only BIM XML using the benchmark's existing projection function.
3. Developer-authored **declarative XML** adds one `Wall` in a known storey with start `(0,-10,0)`, end `(15,-10,0)`, height `3m`, thickness `0.2m`. **No IFC `GlobalId` is invented by the XML author**; the trusted binder deterministically allocates one.
4. Existing `compile_declarative_xml` creates a scoped native IFC4X3 result. Convert only the output *back* to millimetres for the benchmark.
5. Original author `data.tests.test_05.execute_test` independently scores **1.0** across all four criteria: object existence, location, dimensions and integrity. Unit-only no-op scores **0.0**. Original Wall count 16 -> 17; no original GlobalIds removed.

Evidence: `reports/bibimbap_xml_author_witness_20261112.json`.
**Second original benchmark update witness:** \`geometry_test_11\` ("Decrease the height of all walls by 0.5 m on the 2nd storey"). Without using grader-private target GUIDs, the source-derived \`IfcBuildingStorey(Name="L2")\` identifies exactly six walls. Developer-authored XML reduces their height by 0.5m. The original author \`geometry_test_11.execute_test\` returns **1.0** (correct location, dimensions, integrity). No native root GUIDs were added or removed. Evidence: \`reports/bibimbap_xml_geometry11_witness_20261112.json\`. Thus **two distinct operation types (Create and Update)** are proven with developer-authored XML, 0 LLM attempts. **This is an engineering positive control, not GPT-6 Luna performance.** No external LLM calls, actual token usage, model success rate or paid spend.

## Endpoint policy before any real LLM benchmark

- **Primary author-native comparison:** original per-task metrics and exact paper scoring arithmetic; report 45-edit mean separately from all-100 paper mean. Compare each operation (15 cases) against the authors' operation breakdown; cite provider/version/turn differences.
- **Mandatory baselines:** original IFC unchanged (no-op) and developer-authored successful witness; report a second **strict task edit** metric requiring an actual requested mutation and applicable geometry/relationship satisfaction. Never represent author metric partial credit as strict binary task success.
- **Ablation:** no-op-adjusted score per task `score(xml) - score(identical_ifc)` and original raw score, both shown. Never replace the paper's original scoring rules.
- **Failure accounting:** 45 prospective tasks remain in denominator, including unsupported projection/edit, invalid XML, compiler failure, author evaluator exception and source schema mismatch. Do not cherry-pick favorable XML-supported tasks after seeing model outputs. Predeclare an optional supported-subset analysis separately.
- **Cross-paper caution:** BIBIMBAP 100-task all-CRUD score (including 55 retrieval tasks) cannot be subtracted from our 45-edit score; reported Create/Update/Delete submetrics are more relevant, but different model and turn budgets confound methodological superiority.
- **Rights/safety:** author test source not vendored; original data licensing respected. LLM receives only sanitized source-derived XML/task prompt; author grader / private test internals are excluded from model-facing context. Original test code executes in separate bounded subprocesses and IFCS are cloned. Network-/filesystem-level sandbox isolation of externally generated code remains a separate requirement if dynamic code is ever introduced.
- **Budget:** prior two-call P0 budget authorization is not approval for this new experiment. No paid API call occurs here.

## Exact offline reproduction on connected Windows PC

In `D:\문서\D__1_Projects\202611\bim-markup-bench-bibimbap-issue102`:

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$env:BIBIMBAP_AUTHOR_REPO = Join-Path $base 'bibimbap-author-upstream'
$env:BIBIMBAP_DATASET = Join-Path $base 'bibimbap-author-data'
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'

& $py -m unittest tests.test_bibimbap_author_integration -v

# Re-run only with a NEW --output-json name (write-once policy):
& $py -m tools.audit_bibimbap_author --author-repo $env:BIBIMBAP_AUTHOR_REPO --dataset $env:BIBIMBAP_DATASET --negative-controls
& $py -m tools.audit_bibimbap_unit_roundtrip --author-repo $env:BIBIMBAP_AUTHOR_REPO --dataset $env:BIBIMBAP_DATASET --baseline-json reports\bibimbap_original_45_noop_20261112.json
& $py -m tools.audit_bibimbap_projection_coverage --author-repo $env:BIBIMBAP_AUTHOR_REPO --dataset $env:BIBIMBAP_DATASET
& $py -m tools.verify_bibimbap_xml_author --author-repo $env:BIBIMBAP_AUTHOR_REPO --dataset $env:BIBIMBAP_DATASET
& $py -m tools.verify_bibimbap_xml_update_author --author-repo $env:BIBIMBAP_AUTHOR_REPO --dataset $env:BIBIMBAP_DATASET
```

None of the commands calls a paid model provider. Tests and runtime reports provide SHA provenance and strictly distinguish deterministic manual controls from LLM performance.

## Remaining engineering work before first *model-generated* official score

The XML author must generate the edit, not just a developer; supported task count must be demonstrated beyond `test_05`. Preserve the author-native scoring bridge, pre-register a budget and model snapshot, ensure model-facing context excludes grader answer code, and run immutable per-task outputs with source hash, edit diff, original author grade and fail reason. **At present: 2 developer positive XML witnesses / 45 tasks, 0 LLM-scored BIBIMBAP tasks.**
