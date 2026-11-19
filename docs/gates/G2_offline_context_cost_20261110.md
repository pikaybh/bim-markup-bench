# G2 / Issue #20 — offline model-context byte accounting and G3 fail-closed gate

**2026-11-10. No LLM call, no source GT inspection, no official scored result.**

## Why this audit exists

The frozen 36-task candidate tests the hypothesis that an LLM which directly edits declarative XML can outperform LLM-generated imperative Python/IfcOpenShell under controlled, paired tasks and budgets. Draft PR #75 established an *offline developer-authored* v0.2 typed IfcSpace/Pset/QTO proof but **did not** promote that grammar into a model-facing experiment. A new context is an intervention/ablation and cannot silently replace the frozen v0.1 condition.

Issue #20 requires measurement of prompt tokens, provider charges and control parity **before** any paid model call. This audit is a **source-only preflight** that measures actual text objects returned by the existing G2 D/I **offline** runners; it **does not** pretend those objects are provider wire-format messages. There is still **no selected model/tokenizer, no verified provider transport, no billing budget enforcement and no real Python execution sandbox**. Those blockers are release requirements, not obstacles to work around.

## Exact source-only observations (one frozen public input)

For `WAL-CRE-SPA-A-003`, input IFC checksum:

`e90e635629a85cf1942163db0f647a49edc6d24631ba72ec79a0381c9145a0de`

The trusted local audit independently built the real G2 D0 `AgentVisibleSource` and I0 `MatchedObservations` from the **same public task instruction and verified input IFC**. Both had identical task IDs, prompt strings, v0.1 source XML, language specification and original IFC SHA.

| Exact observed text component | UTF-8 bytes | Visibility |
|---|---:|---|
| Public task instruction | 313 | Common D0/I0 |
| v0.1 XML source | 2,684 | Common D0/I0 |
| v0.1 language specification | 7,383 | Common D0/I0 |
| I0 reference API notes | 1,113 | I0 only (intentional treatment difference) |
| v0.2 source semantics overlay candidate | 2,211 | **Proposed**, reproducible source-only on both, NOT model-facing |

**These are byte counts, not tokens.** The standard experiment host has no installed `tiktoken`, `tokenizers`, `sentencepiece`, or `transformers`, and no **approved target-model tokenizer** is selected. The exact provider request envelope, provider-side message formatting/serialization, model IDs, prices, cached-token accounting and live usage records are also absent. Consequently:

- `provider_input_tokens=null`
- `billable_provider_tokens=null`
- `real_provider_token_count=null`
- `actual_usd_cost=null`
- `v02_candidate_added_provider_tokens=null`

**Do not divide bytes/characters by an arbitrary constant to invent tokenizer counts or a cost estimate.** The one-shot draft specifies ceilings of 20,000 input and 6,000 output **tokens per attempt**, not measured usage or an approval. Current proposed spend price values in `configs/budget.example.json` are examples, not current verified billable rates or an entitlement to run.

Source-only v0.2 metadata is rebuilt twice and checked against the immutable IFC. No developer-authored *new room 135* solution from PR #75 is given to either model. That would leak a manually chosen candidate answer into the inference context and compromise the experiment.

## Fresh frozen 36-case source eligibility refresh

Read-only and GT-free `tools.audit_pilot_source_eligibility` was rerun on 2026-11-10. The report `reports/g1_frozen_source_eligibility_20261110.json` has a reproducible SHA-pinned candidate manifest and **36** unmodified task IDs.

- **23** are `STATIC_ENGINE_UNSUPPORTED` under the legacy conservative v0.1 classifier.
- **13** are conditional; **11** had source IFC bytes verified and source conditions probed; **2** missing from local pinned source cache.
- The conservative v0.1 capability classifier is **not updated for the later geometry and metadata research prototypes**. It therefore cannot certify that all of the 23 are still unsupported, nor that any formerly blocked task is officially solved. It is a diagnostic coverage inventory, not a new score.
- Actual official completed D0/I0 task oracles **0**, official benchmark tasks scored **0**, paid model calls **0**.
- This audit did **not** load any benchmark ground-truth IFC.

The dataset's source/model rights ledger remains unreviewed for the individual BIM-Edit IFC source licenses. We do not redistribute IFC data or reference solutions.

## Exact security/experimental gates

`src/runner/offline_context_cost_gate.py` builds and fingerprints every common source text field and separately fingerprints the I0-only API notes. A context mismatch in task ID, public instruction, XML, language spec or source hash **raises a typed error**. A stale, forged, unequal or developer-answer-contaminated v0.2 semantic overlay fails source verification.

The release gate requires ALL of the following: common source identity; same verified source-only proposed overlay; approved model transport; exact model tokenizer (or provider-reported tokens with verified accounting); matched provider usage/costs; prospectively reviewed/preregistered v0.2 ablation; OS sandbox for untrusted I0 code; official/independently cross-calibrated scorer; source/GT and license coverage; verified price snapshot and explicit spend approval; durable budget runtime.

It remains `BLOCKED_NO_ACTUAL_MODEL_TOKEN_COUNTS_OR_FAIR_G3_RUN`, even if a caller fabricates positive values for currently known subconditions. **No user- or agent-controlled field can bypass the unimplemented live conditions in this audit.**

Notably, the independent blind IFC grader has five passing smoke/test conditions, but its provenance is `independent-reimplementation`; it has **not** been demonstrated equivalent to the BIM-Edit official evaluator. Latest local and public-search checks did not establish a verified official executable scorer. This does NOT assert the official author code is definitively unavailable.

The current mock I-arm exposes Python source submission, **not execution**: its `OS_sandbox_available` and `allowed_execution_operations` report false/empty. The direct arm exposes only XML text-editing operations and no authoring BIM API. Real asymmetric execution costs/feedback cannot yet be claimed equal.

## Reproduction and boundaries

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_offline_context_cost_gate -v
.\.venv\Scripts\python.exe -m tools.audit_pilot_source_eligibility
.\.venv\Scripts\python.exe -m tools.audit_g2_model_context_cost
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

Both trusted evidence CLIs **intentionally exit 2**: their source-only observations pass while the research release gate is still blocked. They produce only checksums, lengths, redacted status and reason codes. The report JSON is `reports/g2_offline_context_cost_20261110.json`. No synthetic user reply or benchmark solution is serialized, no API key/secret is read, and no billed API service or GT path is accessed.

New tests include positive paired context observations; one-byte/one-field mismatches; fake/stale v0.2 metadata; UTF-8 byte-versus-codepoint accounting; unsupported budgets; fraudulent approval flags; source-input SHA and candidate-manifest integrity; absence of official scored tasks.

## Further work for scientific readiness

1. Acquire/verify the target provider's exact **versioned tokenizer** or wire-format and actual per-arm provider token usage, with a pinned model/snapshot and price, without conflating UTF-8 lengths with billable tokens.
2. Design a **preregistered**, model-visible v0.2 **ablation** with fixed input output budgets and equal source semantics. Both arms' differing authoring tool affordances and API-note lengths must be recorded, and a genuine isolated Python runner must be verified before any inference.
3. Independently verify official scorer code/provenance/tolerances or explicitly declare a separate independently defined metric (not official BIM-Edit parity), then review dataset source/GT model rights and the frozen support matrix.
4. Implement durable live budgets, explicit owner authorization and immutable cost/trace records. Until these gates are met, model calls and official scored tasks remain zero.
