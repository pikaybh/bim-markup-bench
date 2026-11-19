# G0 Issue #4 — BIM-Edit author-published runs vs official executable scorer

**2026-11-10 | Verified pinned public release, NO official executable scorer installed**

This is the *source-provenance* gate for the independent BIM Markup Bench
project, NOT an evaluation of our D0/XML or I0/Python hypotheses. No
third-party IFC model, GT IFC, model predictions or per-task solution
payload was downloaded by this audit; no paid API or scorer ran.

## Primary sources and fixed artifacts

| Scope | Authoritative URL / revision | Verified observation |
| --- | --- | --- |
| Paper/metric and licensing statements | https://arxiv.org/html/2606.20146v3 , §3.2, Appendices E, F.5, J | Paper says evaluator & inference harness are MIT licensed and a code folder accompanies the submission, but **no direct canonical code repository/commit/CLI was verified** |
| Public task card | https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks | 324 tasks; metadata describes 162 artificial and 162 realistic |
| Author-run release | https://huggingface.co/datasets/BIM-Edit/BIM-Edit-runs/tree/9241abc9b3b4efa3906c0bdabcf3321f1558192f | **1,417 published file entries**, **seven model directories**, all seven have author evaluation reports |
| HF API metadata | https://huggingface.co/api/datasets/BIM-Edit/BIM-Edit-runs | Current reported HEAD = `9241abc9b3b4efa3906c0bdabcf3321f1558192f` when checked |
| Claude released aggregate | https://huggingface.co/datasets/BIM-Edit/BIM-Edit-runs/resolve/9241abc9b3b4efa3906c0bdabcf3321f1558192f/claude-sonnet/eval/summary.json | 324 tasks, geometry **0.5590**, semantics **0.3385**, topology **0.4619**, overall **0.4531** |

The seven published author-run folders are `claude-sonnet`,
`deepseek-v3.2`, `gemini-flash-3.0`, `gemma4-31B`,
`gpt-5.4-mini`, `gpt-5.4` and `qwen3.6-plus`. **Every**
folder has at least:
- `eval/per_task.csv`
- `eval/report.csv`
- `eval/resolved_defaults.json`
- `eval/summary.json`

The pinned tree also lists other evaluation files such as
`summary_by_tag.csv` and `eval_cache.json`; these are **released
results or caches**, not an evaluator implementation. No `.py`,
`.ipynb`, `.whl`, `.zip`, `.tar.gz` or `.toml` executable-code
candidate appears among these **1,417 entries in this particular
HF runs revision**. This does NOT establish that the paper authors
never released code in a separate repository or original submission
archive. A code artifact would still require file/revision/license
and isolated runtime verification before claiming official scores.

### Correction to earlier audit

Earlier private project notes about the HF runs release were incomplete
and in some cases observed a historical snapshot containing only two
models without public evaluation reports. The **2026-11-10 fixed
revision does contain reports for all seven models**. Do not reproduce
the old “public score reports unavailable” claim.

### Published aggregate cross-check, NOT rerunning evaluation

The released Claude `eval/summary.json` fields match the paper's
Table 1 rounded percentages: 55.90 / 33.85 / 46.19 / 45.31. Taking the
unweighted mean of the three published component averages gives
0.453133…, agreeing with 0.4531 to the released precision.

**This is a validation of published aggregate numbers against the
paper, not a validation of per-task scorer code, point-cloud sampling,
Hungarian OBB matching, source/GT deltas, semantic property filters,
topology graph alignment, or the local IFC evaluator.**

The public Claude `by_scene_type` summary assigns all **324** records
to `realistic`, with no `artificial` bucket. The task card defines
162 of each. This is **a potential inconsistency in summary-group
labels**, not proof of inaccurate individual IFC metrics. It requires
a source-of-truth check of the public per-task `scene` labels versus
the summary generator once the official scripts are available. It must
not be silently corrected or used as a criterion to tune a local
evaluator toward the observed results.

## Executable evaluator provenance: still BLOCKED

- **Paper claim:** Evaluator source and inference harness under MIT,
  a code folder mentioned in Appendix F.5.
- **Verified:** seven folders with cached evaluation reports, pinned
  dataset revision, published aggregate that agrees with Table 1.
- **Not verified:** canonical author-controlled source repository URI,
  exact source commit, MIT license file in that code repo, dependency
  lock, scorer entrypoint, reproducible author per-task scores from
  raw IFC with source/GT separation and documented seed/tolerances.
- **Local code:** `src/evaluation/bim_edit_scorer.py` remains strictly
  `metric_origin=independent-reimplementation`, **not** the paper's
  binary-equivalent or method-equivalent implementation.
- **Separate scalar formulas:** `src/evaluation/metric_contract.py`
  implements only arithmetic after mesh/graph features are known.
  It is labeled `paper-formula-only`. Neither local module may
  claim an official BIM-Edit solved task.
- Neither paper textual source nor published aggregate alone permits
  changing independent metric provenance to `official`.
  **Official benchmark tasks scored by this project: 0.**

## Automated evidence contract

`src/evaluation/official_release_provenance.py` independently checks
the full 1,417-path release inventory against the pinned SHA and all
seven expected report sets. It validates exact values, table arithmetic,
task count, source revision/path tampering and the anomalous scene
summary label. It **hard-blocks official evaluator readiness even when
an input release JSON includes forged “verified” keys**, because
evaluator code and source/GT-calibrated execution have not occurred.

`tools/audit_official_bim_edit_release.py` makes **only two**
allowlisted bounded public HTTPS JSON requests: HF runs repository
metadata and Claude aggregate `summary.json` at the pinned SHA.
The latter may redirect to the official Hugging Face HTTPS CDN
`us.aws.cdn.hf.co`; any other redirect is denied. Request bodies
are not persisted; the committed result contains SHA-256 fingerprints,
counts, score checks, model folder names and statuses only.
The full raw model predictions, IFC corpora and GT are never fetched.

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_official_bim_edit_public_release -v
.\.venv\Scripts\python.exe -m tools.audit_official_bim_edit_release
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

The audit CLI **intentionally exits 2** despite passing the published
artifact checks: `BLOCKED_OFFICIAL_EXECUTABLE_EVALUATOR_NOT_VERIFIED`.
Evidence: `reports/g0_official_bim_edit_public_release_20261110.json`.

## Remaining gates (do not merge experiments under the official label)

1. Obtain/identify the **actual author's source code repository and
   pinned revision**, an unambiguous MIT license file, supported
   Python/IfcOpenShell versions and complete environment lock.
   If not publicly identifiable, request the official evaluator
   URL/command and calibration fixtures directly from the authors.
2. Run official scorer **offline in the isolated grader** on
   at least 3 named paper example IFC outputs, with exact per-axis
   and strict-pass comparison against their released per-task records.
   Preserve source/input/output/GT hashes. Treat reported rounded
   results as lossy evidence; avoid output-driven tuning.
3. Audit the per-task scene type summary discrepancy and the task
   target GUID corrections without modifying the frozen candidate
   task list, evaluating only known metadata integrity.
4. Until an executable official run is independently proved, present
   our local evaluation as an **independently defined metric**. Do
   not apply the paper's original-model score distributions as a
   direct numerical baseline to independent D/I IFC results.

No actual model calls, official scores, or GT access took place.
