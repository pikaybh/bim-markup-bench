# XML-only BIM-Edit pilot: prospective protocol v0 (DRAFT, not registered)

Date: 2026-11-12. Tracking: [#100](https://github.com/pikaybh/bim-markup-bench/issues/100).

## Decision and research claim

Owner selected **Direct XML Editing only** as the primary experiment. Do **not**
implement Revit MCP, Xim APIs, or rerun Python baselines to claim a causal
representation comparison. Treat the existing Luna P0 paired work as a
separately labeled engineering pilot and preserve frozen records unchanged.

**Question:** What task success, IFC geometry/semantic/topology validity,
collateral mutation, latency and cost does a direct-declarative XML BIM editor
achieve on tasks from the public BIM-Edit corpus?

**Historical context:** compare task categories and published model baselines
from [BIM-Edit](https://arxiv.org/abs/2606.20146), and only qualitatively
discuss Revit/Tool Calling and BIBIMBAP papers. Report **cross-study** results
as *descriptive*, NOT head-to-head paired superiority. Published BIM-Edit
model results use Python/IfcOpenShell and different provider models/budgets.
Never write that our independent scorer output is the official author score
until numerical calibration against an executable original author scorer
succeeds.

## Fixed population and candidates; no cherry-picking

- The public task snapshot is 324 tasks (all six IFC element classes and 18
  operation x instruction-category x scene strata), pinned in
  `manifests/bim_edit_revision.json` and verified by SHA-256 on
  `data/tasks.jsonl`. The full 324 denominator must be reported for any
  full-population analysis, with unsupported tasks as failures/unscorable per
  prospectively fixed rule, not silently dropped.
- Reuse exactly the existing **36** deterministic sample IDs from
  `manifests/pilot_36_candidate_v0.json` for the pilot. This is an
  **unregistered candidate**, not a scored sample or approved study.
- Preserve all 36 IDs in a future ITT denominator even when the engine cannot
  perform the edit; publish separate "supported", "unsupported", "invalid",
  "source unavailable", and "metric unavailable" counts. A supported-only
  analysis is exploratory unless independently frozen *before* LLM results.
- Existing 324-row static engine audit has **246 unsupported** and **78
  conditional/unverified** statuses. Among the fixed 36 candidates, the
  earlier readiness audit found **23 static unsupported**, **9 blocked by
  source dependencies/oracles**, **2 uncached**, and **2 manual source-only
  demonstrations with gates**. These are past engineering classifications,
  *not* predictions of LLM task performance or final eligibility.
- Three developer-authored D0/I0 source-relative demonstration pairs passed
  native checks. They are **not** independently verified full task solutions
  or official benchmark scores.

## Single arm: what LLM can and cannot do

- The agent sees the permitted public instruction, a sanitized source-only
  IFC-derived declarative `building.xml`, the schema and error feedback
  subject to a frozen call/feedback policy.
- It edits an XML **state document**, not command opcodes. Only trusted
  compiler code outside the LLM converts a before/after state diff into a
  cloned IFC output.
- No authoring API, IfcOpenShell mutation methods, direct code editing or
  operation-list XML is permitted in model-facing authoring.
- All ground-truth IFC, evaluators, private grader target GUIDs and reference
  answers live outside the model context and run sandbox. Preserve exact
  source identity, untouched relationships and output hashes.

## Scoring and provenance

Primary prospective endpoints (once frozen and implemented):
1. Strict IFC per-task satisfaction, including no unintended mutations.
2. Geometry, semantic and topology components.
3. Explicit failure/unsupported/blocked fractions over the *full* declared
   task denominator.
Secondary: latency, measured token usage, actual price, invalid XML/IFC,
context tokens, compiler failures.

For the original paper's official metrics, the **original runnable author
scorer has not been verified in this repository** (see
`reports/g0_official_scorer_origin_review_20261111.json`). The existing
local scorer is an *independent reimplementation*; it has not established
numerical parity with the authors' scorer. Published raw evaluation summaries
and per-task CSV arithmetic were audited for seven models; one reported
model's task table lacked a row. Re-aggregating published tables is not
re-scoring predicted IFCs. Historical literature scores may be quoted with
their reported origin, **not** subtracted from local independent scores to
claim an exact performance delta.

Frozen official scorer replacement, if necessary, must be explicitly named
"independent approximation", with its own method and error calibration.
A failure in the XML→IFC compiler must not be misattributed to LLM reasoning.

## Go/no-go before any paid BIM-Edit task inference

1. G0: pinned original input/GT IFC bytes, per-model licensing/usage review,
   source and GT separated from the LLM. Current prior audit: 30 fixed
   pilot pairs cached, 6 missing, individual model licensing unresolved.
2. G1: direct XML compiler can produce a task-specific valid IFC (D0) with
   full independent task postconditions. Existing source-relative demos do
   not establish this for the full 36.
3. G2: blind independent grader on final IFC, clear scorer provenance and
   calibration, no leaked reference data. If original author scorer remains
   unavailable, official numerical parity claims remain prohibited.
4. G3: exact model (configured model ID), per-call ceilings and cumulative
   paid cap explicitly authorized; validated cost admission gate; frozen
   seed/temperature/tool feedback budget, candidate list, run and failure
   protocol. The earlier USD 1 authorization was only for the old two-call
   Luna P0 replay, **not** for a new 36-task BIM-Edit experiment.

Do not silently relax any gate to spend budget. If the full 36 does not pass,
publish the factual blocked coverage and perform only non-scored engineering
proofs until prospective re-registration.

## Offline audit reproduction

On Windows with the original cached, pinned 324-row **public task metadata**
(not GT IFC):

```powershell
$env:BIM_EDIT_PINNED_TASK_JSONL = 'D:\문서\D__1_Projects\202611\bim-markup-bench\data\tasks.jsonl'
& 'D:\문서\D__1_Projects\202611\bim-markup-bench\.venv\Scripts\python.exe' -m unittest tests.test_xml_only_readiness -v
& 'D:\문서\D__1_Projects\202611\bim-markup-bench\.venv\Scripts\python.exe' -m tools.audit_xml_only_readiness --task-jsonl $env:BIM_EDIT_PINNED_TASK_JSONL
```

The CLI deliberately exits **2** when launch is blocked, even with a valid,
read-only report. `--output-json` writes once to a new file and refuses to
overwrite prior evidence. It never executes paid inference, fetches data or
loads ground-truth IFC files.

## Next allowed engineering step

First resolve the most economical *single supported original BIM-Edit
task*'s full instruction oracle and rights in a clean independent reviewer
process, with source-only XML preview and an isolated GT evaluator. Verify
one end-to-end no-LLM candidate against that external reference; then
prospectively lock a feasible pilot denominator and budget. Avoid
rebuilding a BIM engine or MCP until this path is demonstrably blocked.
