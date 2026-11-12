# Original BIBIMBAP 45 edit tasks — actual GPT-6 Luna XML-only attempt, $1 max

- **Experiment Issue:** [#112](https://github.com/pikaybh/bim-markup-bench/issues/112).
- **Prior one-shot:** [#110](https://github.com/pikaybh/bim-markup-bench/issues/110), actual `test_05` response reused, never called again.
- **Date:** 2026-11-12 (Asia/Seoul), provider model **`gpt-6-luna`**.
- **Scope:** independent `bim-markup-bench` *experimental* adapters and test code **ONLY**. The BIXML/Xim implementation is a separate product and **no product code was read, modified or deployed**.
- **Research design:** single model, direct declarative XML editing of a partial IFC-backed projection, *not* the original paper's API/tool interface. This is a noncausal comparison to published external paper results; not a controlled A/B comparison against Python/IfcOpenShell.
- **Population:** **45 original BIBIMBAP editing tasks** (15 Create / 15 Update / 15 Delete; 15 basic / 15 geometry / 15 topological). The other **55 original retrieval tasks were excluded from the editing-only experiment**, NOT silently excluded from the original benchmark's published 100-task denominator.

## Actual completed outcomes

| Status | Original ITT task count | Interpretation |
|---|---:|---|
| Original author's grader returned all components at 1.0 | **3** | Exact real model XML→native IFC result, **not** independently verified full strict task success |
| Original author's grader returned a partial or zero score | **12** | IFC compiled and scored, but rubric not full pass |
| Real model returned, but trusted XML→IFC compilation/author scoring failed | **21** | Zero in 45-case ITT score; do not silently drop |
| Original public IFC input is unsupported by frozen experimental projection | **9** | Fail/unsupported in original 45 denominator, **no model call** |
| **Total** | **45** | **36 actual provider requests = 1 previous + 35 new, one per projectable case, no retries** |

**Original author full-score rate: 3/45 = 6.67%.** This is a measured *end-to-end experimental pipeline* pass rate, **not a pure LLM task correctness rate**. Independent full strict-task success rate remains **unverified**, as the native core has not verified absence of all unintended downstream clashes and geometry changes for 45 tasks.

The **three** author-graded 1.0 tasks were:

| Original task ID | Public task (summarized) | Observed exact model XML semantic changes |
|---|---|---|
| `test_05` | Create a 15m wall from (0,-10) | 1 new Wall, 25 existing XML IDs unchanged; prior one-shot, independent native wall geometry core PASS |
| `geometry_test_11` | Decrease the height of all second-storey walls by 0.5m | **6 existing XML node attributes changed**; no new/deleted IDs |
| `topological_test_13` | Move specified window to touch exterior of specified wall | **1 existing XML node's attributes changed**; no new/deleted IDs |

All 3 passed their **original author tests** and produced native IFC4X3 in millimetres. The independent post-hoc semantic-diff tool verified all 3 raw model outputs actually changed XML state (so they are not just grader no-op partial credit). This does *not* prove complete non-target native geometry and clash preservation.

Four original question/score fields for `test_05` existed only in prior issue #110. The prior exact SHA, input/output usage and score were **reused rather than regenerating the task, making the full 45 dataset neither repeated nor upsampled**.

### Breakdown

| Original CRUD | ITT denominator | Original author 1.0 tasks | Mean author score, unsuccessful/unsupported = 0 |
|---|---:|---:|---:|
| Create | 15 | 1 (6.67%) | 0.188890 |
| Update | 15 | 2 (13.33%) | 0.400000 |
| Delete | 15 | 0 (0%) | 0.000000 |
| **Total** | **45** | **3 (6.67%)** | **0.1962967** |

By original category: basic 1/15, geometry 1/15, topological 1/15 attained original author score 1.0.

Original author score distribution among the **15** cases actually scored, including `test_05`, is **0.58889 mean**, but that is selected-case-only and **not** the 45-task result. The 45-case zero-filled mean original author score is **0.1962967**.

**No-op score caveat:** original author graders give positive baseline credit to some Update tasks even when the IFC was unchanged (e.g., `test_12` 0.6667, same as its original no-op score). The separate 45-case original author's source-identical negative-control **mean was 0.2074074**. The zero-filled experimental score 0.1963 is actually below this number, but no causal inference should be made from this unadjusted comparison because unsupported attempts are counted zero. **Never convert positive fractional scores into binary successes.**

## Costs — actual provider usage and conservative upper cap

Owner permission: run the entire 45 editing task experiment **only if combined paid API cost is less than $1 USD**.

Official [GPT-6 Luna standard OpenAI API tariff](https://developers.openai.com/api/docs/pricing): USD **$0.10 per million input tokens** and **$0.50 per million output tokens**, short-context standard processing. Fixed max **16,000 output tokens per call**, `reasoning.effort=medium`, `service_tier=default`, `store=false`, `tools=[]`, `max_retries=0`; no re-prompts, automatic retries, or user-facing tool execution.

Before *any* of the 35 new calls, the complete corpus's public packets and input-normalized IFC files were hashed and frozen, and an upper reservation calculated from **each input's byte count + 2048 input-margin tokens + full 16,000 maximum output tokens**, then **multiplied by 2** as a further tariff margin.

| Cost / accounting | Value |
|---|---:|
| Prior test05 actual request reused | 1 |
| New real single-attempt calls | 35 |
| Original inputs known unprojectable | 9 (no API call) |
| Total actual provider input tokens | **126,320** |
| Total actual provider output tokens | **80,193** |
| **Usage-based estimated total spend (including prior test05)** | **$0.0527285** |
| **All 35 new call reservations plus prior request, conservatively ×2** | **$0.6575428** |
| Owner limit | **$1.00** |
| Provider final invoice reconciled | **NO** |

Each fixed input/request was below the model short-context threshold, no other billable provider tools or hosted compute were used, and configured/provider-returned model was `gpt-6-luna` for all 36 paid calls. Final provider invoice discounts/uplifts may differ from this *usage-based estimate*.

## Major confound: this was predominantly a compiler capability test, not a language-model test

The experimental XML language is **`toy_markup_v0`**; it is explicitly *not* the real BIXML/Xim markup or production compiler.

- **9 original inputs blocked even before the model**: three original IFCs are not IFC4X3; the others have mapped/boolean or tilted geometry unprojectable by this experimental IFC-backed XML projection.
- **21 additional model outputs did not reach the original grader** because the *trusted runtime* rejected an unsupported mutation or XML/geometry compilation path. Diagnostic examples include `Only creation of a new standalone Wall is supported`, `Only verified Wall geometry and hosted Opening.offset updates are supported`, and `Unsupported IFC relationship deletion`. These are **not evidence that GPT-6 Luna could not conceptually author a correct BIM edit**, nor grounds to invent a score or substitute native IFC API calls.
- 15 native IFC outputs *were* graded by the pinned original author, showing both 1.0 full and 0.0/partial results. One task such as `topological_test_01` scored **0.916675**, losing original `integrity_constraint` credit; this is not a full success despite meeting dimensions/location/existence.

Therefore, the present **6.67%** reflects an honest, frozen, limited-capability experimental protocol, **not the benchmark potential of a complete BIXML or a tool-equipped agent**.

## Frozen evidence, privacy, and offline reproduction

- `reports/bibimbap_original45_luna_20261112.json`: one original-author-score/status/usage/result-digest entry for **each of the 45 original edit tasks**, with zero-filled ITT mean and per-category/CRUD aggregation. Original author test source and privately structured targets are not in provider input.
- `reports/bibimbap_original45_luna_semantic_audit_20261112.json`: reproducible source-XML semantic differences of raw exactly preserved LLM outputs, no provider/author grader call.
- **Local only**, ignored by Git, original responses and IFC candidates, frozen prompts, existing normalized IFCs, per-task score records under `results/bibimbap_original_45_luna_20261112_issue112/`. Includes `preflight.json` with precommitted per-case fixed prompt hashes and budget reservations. No secrets, unlicensed original IFC source or original author grader Python published to Git.
- Prior `test_05` unchanged real response and IFC remains local in the issue #110 worktree's `results/bibimbap_test05_luna_one_shot_20261112_110/`. The Git-safe hash/score reports are carried as a dependency, not regenerated.
- No production files, servers or BIXML/Xim repository were modified. The regular `bim-markup-bench` main checkout was not modified; changes are confined to a new experimental Git worktree/branch and an unmerged Draft PR.

Read-only verification on connected Windows 11 environment, assuming the original data directory and shared test venv exist:

```powershell
$base = 'D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue112-full45')
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$env:BIBIMBAP_AUTHOR_REPO = Join-Path $base 'bibimbap-author-upstream'
$env:BIBIMBAP_DATASET = Join-Path $base 'bibimbap-author-data'

& $py -m unittest tests.test_bibimbap_full45_real tests.test_bibimbap_real_luna_evidence tests.test_bibimbap_public_gate tests.test_bibimbap_native_core -v
& $py -m tools.audit_bibimbap_full45_semantics
```

**DO NOT rerun `--live-approved`**: all 35 new one-shot API requests are already consumed and the runner refuses a second attempt. Changing the experimental compiler or source grammar after seeing the results and resubmitting would create an entirely different prospective study, not revise this frozen 45-case outcome.

## Recommended scientific follow-up (not authorized within this run)

1. Independently validate non-target geometry/relationship/clash preservation for the 3 original-author full-score results, particularly the two Updates. This can run **offline**, with original IFC and saved candidate; does not touch BIXML.
2. Register *before* new calls an improved **experimental-only** compiler grammar + complete 45-case capability support and own strict binary task oracles. Evaluate `test_05` as already observed but do not retroactively relabel historical outcomes.
3. Design a matched-model same-public-input XML editing vs Python/IfcOpenShell tool arm under equivalent attempts and cost caps; use original published results only for contextual noncausal external comparison.
4. Obtain a new specific owner budget approval for any additional paid tests. No general permission to use BIXML/Xim product source or to merge to main.

**Conclusion:** The requested 45-case original-edit cohort was fully enumerated and accounted for; the first successful task did not generalize to this deliberately limited experimental compiler. The experiment remained **under $1** and kept the actual errors rather than tuning the grader, hiding difficult cases or rewriting model outputs.
