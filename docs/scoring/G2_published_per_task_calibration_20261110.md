# G2 / Issue #21 — public author per-task score audit and independent metric limits

**2026-11-10. Audit status: AUTHOR_REPORTED_CSV_ARITHMETIC_VERIFIED_SCORER_STILL_BLOCKED.**

## Research purpose and boundaries

The independent BIM Markup Bench hypothesis concerns LLM editing *declarative XML directly* versus generating imperative Python/IfcOpenShell on matched source IFC tasks. This audit **does not** run either model or the BIM-Edit official evaluator. It analyzes the author's **already published** per-task score CSVs in a grader-private read-only process so we can distinguish:

1. **Author-published reported scores** (CSV values and their released aggregates).
2. **Paper-defined arithmetic** (per-axis mean and strict three-axis ≥0.98 threshold).
3. **An executable official scorer** that independently loads input, reference and result IFCs.
4. **Our local IFC-native scorer**, whose explicitly different version is `independent-reimplementation`.

Only (1) and the elementary arithmetic parts of (2) are verified here. Neither (3) nor cross-implementation equivalence of (4) has been established.

## Fixed source and exact measurement

Source: [BIM-Edit-runs Hugging Face release](https://huggingface.co/datasets/BIM-Edit/BIM-Edit-runs/tree/9241abc9b3b4efa3906c0bdabcf3321f1558192f), SHA:
`9241abc9b3b4efa3906c0bdabcf3321f1558192f`.

Per-model source files were retrieved **only in transient memory** from:
`/<model>/eval/per_task.csv` and `/<model>/eval/summary.json`.
No IFC data, model-generated Python source, cached answer text or hidden GT files
were downloaded or committed. The CSV has `prompt` and
`ground_truth_ifc` columns, but the audit does not inspect, print, return
or store their values. We checked fields `task_id`, `operation`,
`category`, `geometry`, `semantics`, `topology`, `final_score` only.

| Released model folder | Published rows | A / R from task IDs | Strict per-axis ≥0.98 in published CSV |
| --- | ---: | ---: | ---: |
| `claude-sonnet` | 324 | 162 / 162 | 6 |
| `deepseek-v3.2` | 324 | 162 / 162 | 7 |
| `gemini-flash-3.0` | 324 | 162 / 162 | 5 |
| `gemma4-31B` | 324 | 162 / 162 | 3 |
| `gpt-5.4-mini` | 324 | 162 / 162 | 2 |
| `gpt-5.4` | 324 | 162 / 162 | 4 |
| `qwen3.6-plus` | **323** | **162 / 161** | **11** |

These counts are **derived from released numerical CSVs**, not newly
computed IFC scores. In every model, published per-row `final_score`
matches the three-axis unweighted average within `0.0001`; the maximum
row rounding discrepancy observed was `0.0000666666...`. The mean of
each score field across CSV rows agrees with that model's own published
`summary.json` mean to within `0.000051` (four-decimal publication
precision). Checking equality without this rounding tolerance would
produce false failures.

The strict per-axis pass counts agree at one-decimal precision with
paper Table 2 (1.9%, 2.2%, 1.5%, 0.9%, 0.6%, 1.2%, 3.4% respectively).
For Qwen, the numerator is 11; the paper reports a 324-task benchmark,
yet the released table has 323 rows and its own released
`overall.n_tasks` and `overall.n_samples` are **323**.
We **do not impute an absent row or a zero score**, and we do not assert
that the authors' paper denominator was calculated using the same
absence policy. Qwen is precisely **one published CSV task ID short**
relative to the six full-model published task-ID sets.

### Scene summary mismatch

All seven `eval/summary.json` releases classify every row in
`by_scene_type` as `realistic` with no `artificial` bucket, even
though each `per_task.csv` contains 162 `-A-` scenes and 162
`-R-` scenes except Qwen's 162/161 split. This points to an
**aggregate scene-label grouping inconsistency**, not a proven IFC
scorer error. The script explicitly reports that warning and refuses
to silently relabel the author results.

## Actual local evaluator divergence (source-inspected, not tuned)

The project's independent scorer has **specific, important mathematical
and algorithmic differences** from the method described in the paper:

| Dimension | Current independent source | Paper's stated method | Verified equivalence |
| --- | --- | --- | --- |
| Geometry | `GeometrySettings.sample_count=384` surface samples per target, seeded `2607`; native IfcOpenShell point distance and a conservative near-identity/AABB rule | Up to 4096 per edited object and 16384 total; edit-set mesh sampling and median bidirectional Chamfer with decay | **No** |
| Creation target match | `_candidate_target` first matches new GUID, then nearest world bounding-box center | One-to-one Hungarian on oriented bounding-box IoU, 0.05 rejection threshold in semantics | **No** |
| Semantics | IFC class plus observed reference product properties (Name, ObjectType, PredefinedType, Psets, material), including independent missing-value/float conventions | IFC class plus specifically task-relevant properties after OBB matching | **No** |
| Topology | Six defined native relation types and GUID-based set-delta node/edge F1, with aliasing for a selected created target | Edit graph and greedy bipartite node alignment; relation comparison after matching | **No** |
| Empty/invalid/collateral | Local bounded fail statuses and collateral-change audit; source-typed validity checks | Paper description and evaluator internals for degenerate cases unavailable | **No** |

The local evaluator remains
`src/evaluation/bim_edit_scorer.py` with
`metric_origin="independent-reimplementation"` and the independently
frozen tolerance policy. **No scorer algorithm, tolerance, dataset/task
sampling, source IFC or reference IFC was changed in this PR.**
No score for our D0/I0 system was generated.

Published per-task score agreement with the paper's averages does **not**
establish that our local geometry, semantics or topology implementations
would produce those same scores for a fixed IFC triple.

## Reproducible verifier (grader side only)

`src/evaluation/published_per_task_audit.py` validates the pinned
seven-model report set with:

- Strict exactly seven known model directories and per-model bounded
  UTF-8 CSV inputs and required columns, task IDs, operation/category
  consistency, numeric ranges and unique rows.
- Published per-row final-mean arithmetic with a stated and tested
  four-decimal rounding allowance.
- Published aggregate row count (`n_tasks`, `n_samples`) and score
  means against `summary.json`, with no invention of missing scores.
- Cross-run task ID sets checked **in memory**: six full 324 sets must
  match, Qwen's partial set must be a subset with exactly one absent.
  Individual task IDs and reported task scores are never serialized.
- Explicit scene label warnings, source SHA of each raw CSV, model/row
  aggregates, zero official scorer calls, and an unconditional **blocked**
  official-equivalence/live-run gate.
- Negative fixtures for malformed/missing columns, duplicate IDs,
  wrong model/operation/category, injected data, invalid numeric values,
  rounding inconsistencies, denominator mismatch, wrong full and partial
  task sets, and forged scorer readiness.

The CLI `tools/audit_published_per_task_scores.py` fetches 14
whitelisted HTTPS text URLs at one frozen release revision
(7 CSV + 7 summary JSON, each bounded by 300 kB/45 kB respectively).
It permits only `huggingface.co` or the observed official HF HTTPS CDN
after redirect; never retrieves raw IFC, `eval_cache`, model prompt
caches, per-task edited IFC, source/GT model or a grader executable.
Evidence `reports/g2_published_per_task_audit_20261110.json`
contains row counts, digest strings, and aggregate arithmetic facts,
**not** CSV rows, task IDs, prompts or ground-truth paths.

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_published_per_task_audit -v
.\.venv\Scripts\python.exe -m tools.audit_published_per_task_scores # expected exit 2
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

CLI deliberately returns code **2** even after successfully auditing
public scores. It means the **official executable evaluator is still
unverified**, not that the published arithmetic failed.

## Further independent parity test requirements

1. Identify the source-controlled MIT official evaluator repository,
   immutable commit, dependency versions, exact CLI and reproducible
   scoring seed/mesh settings. No such executable has been verified here.
2. In an isolated grader with hidden GT protected from agents, compare
   independently computed **same-input/same-output** IFC triple scores
   per axis against at least three author-released
   `eval/per_task.csv` reference results, with tolerance decided
   *before* examining differences. This requires trusted source and
   target asset rights, provenance and the paper's method.
3. Investigate one Qwen published row absent from `per_task.csv`
   and the seven scene-label summary grouping discrepancies through
   official code or author clarification. Do not patch the frozen
   324/36-task manifest or reported benchmark totals post hoc.
4. Until parity is established, distinguish author-published score
   reaggregation from official IFC scoring and from independent
   authoring-arm results. **Paid model calls: 0; official tasks scored
   by this project: 0.**
