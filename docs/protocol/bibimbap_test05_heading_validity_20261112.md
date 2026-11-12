# BIBIMBAP `test_05`: heading sensitivity in original author grading (2026-11-12)

**Issue:** [#104](https://github.com/pikaybh/bim-markup-bench/issues/104), stacked on [#102](https://github.com/pikaybh/bim-markup-bench/issues/102).
**Evidence classification:** developer-authored non-LLM IFC controls graded by the original pinned author code; **zero LLM calls**, no model success statistic.

## Scientific question

The public author task reads: *"Add a wall with a length of 15m beginning in (0, -10)."*
The pinned author `test_05.py` explicitly allows **any direction**, height and thickness. Its rubric evaluates object creation, dimensions, location, and an `integrity_constraint` that averages spatial containment, clash integrity and preservation. An axis-specific XML edit example scored 1.0 in #102, but this does **not** establish that all physically different valid headings will score equally.

The original evaluator and data are used **without modification**. Only our XML heading changes; original IFC source, start point, nominal wall length, height, thickness, projection/compile units, source model and evaluator remain identical.

## Actual results

| Developer-authored direction | True XML wall length | Original author score | dimension | location | integrity |
|---|---:|---:|---:|---:|---:|
| X axis 0° | 15 m | **1.000000** | 1 | 1 | 1 |
| 30° | 15 m | **1.000000** | 1 | 1 | 1 |
| 45° | 15 m | **0.916675** | 1 | 1 | 0.6667 |
| Y axis 90° | 15 m | **0.916675** | 1 | 1 | 0.6667 |
| Wrong-length negative control, 0° | 10 m | **0.750000** | 0 | 1 | 1 |

**Important interpretation:** the 45° and 90° outcomes are *not* dimensional false negatives. The same author scorer marked their **dimensions and location correct**. The difference is an integrity subcriterion, consistent with an orientation-dependent collision risk. A 15 m wall at one heading need not have equal clash-free validity at another heading. Additional component-level collision evidence would be necessary before calling this a scorer defect.

The 10 m negative control got 0.75 even though the explicitly requested 15 m length was wrong: the original score is **partial credit, not strict task-edit success**. The two 15 m orientations scoring 0.916675 should not be counted as failed instruction-following merely because they scored below 1.0, without resolving the actual collision/semantic requirements. Per-task original scores remain unchanged and must be reported side-by-side with a separately preregistered strict correctness criterion.

## Reproducibility, evidence boundary, and correction

Pinned original author code: `nbharathik/bibimbap@667004e16bd38fd7d538bcee56191465429fd975`.
Pinned dataset: `clemenskujat/bibimbap-data@f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`.
Both live **outside** this research Git repository, and original IFC GUIDs are preserved. Refer to the machine-readable evidence for original task/source/scorer SHA-256 values.

- Initial `reports/bibimbap_test05_heading_validity_20261112_v1.json` is retained as a **failed first probe**: 90° calculated `x2 ≈ 9.18e−16`, which violates the XML `xs:decimal` attribute grammar. It correctly failed closed; do not count this as the author scorer's negative score.
- Corrected `v2` explicitly clamps floating-point near-zero endpoint components to decimal zero **before XML serialisation**, without changing the intended physical endpoint. All five cases were executed against the original grader. Report: `reports/bibimbap_test05_heading_validity_20261112_v2.json`.
- Reproduce with the existing pinned shared Python venv (no provider API):
  ```powershell
  $base = 'D:\문서\D__1_Projects\202611'
  $env:BIBIMBAP_AUTHOR_REPO = Join-Path $base 'bibimbap-author-upstream'
  $env:BIBIMBAP_DATASET = Join-Path $base 'bibimbap-author-data'
  Set-Location (Join-Path $base 'bim-markup-bench-issue104-angle-validity')
  $python = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
  & $python -m unittest tests.test_bibimbap_test05_heading -v
  # For a fresh audit use a NEW output path, not the frozen v1/v2 reports.
  & $python -m tools.audit_bibimbap_test05_heading --author-repo $env:BIBIMBAP_AUTHOR_REPO --dataset $env:BIBIMBAP_DATASET --output-json reports/bibimbap_test05_heading_repeat_NEW.json
  ```

## Consequences for future LLM editing experiments

1. Preserve the **original author score** for historical comparison; never change or reweight the author evaluator retrospectively.
2. Classify geometry correctness, requested-length satisfaction, semantic relationships, clash integrity, and partial-credit score **separately**. If the task permits multiple geometrically distinct answers, document the extra implicit integrity constraints.
3. Treat a score less than 1.0 as evidence for further analysis, not automatic proof of a wrong declarative representation. Similarly, no-op/underlength partial credit is not success.
4. Keep author evaluator/test code, developer-generated witness and task-specific answer parameters **outside the tested LLM's files/prompts**; expose only source IFC-derived XML and the public prompt. Code licensing remains unresolved for the upstream GitHub repo, so do not vendor it.
5. This report has **no causal implication** about D/XML versus I/Python. No paid calls, task selection revisions, published benchmark changes, new model outputs, or merges were made here.
