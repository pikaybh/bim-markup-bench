# G0 — Compute and API Budget Policy

**No live API calls are implemented or authorized by this issue.** A future G2 orchestration layer must implement durable cost accounting.

## Model and estimated cost

Planned GPT-6 Luna, model gpt-6-luna, Standard short-context rates as of November 2026:
- $0.10 per million input tokens, $0.01 cached input, $0.50 output.
- Source: https://developers.openai.com/api/docs/pricing
- Long context, tool, cache write, regional and service tier rates can differ. Recheck immediately before any paid run.

36 tasks x two authoring arms x one repetition = 72 arm-trials, NOT 72 guaranteed HTTP calls.

Assume total 20,000 input tokens and 5,000 output tokens per arm-trial:
- Input: 72 x 20,000 / 1,000,000 x $0.10 = $0.144
- Output: 72 x 5,000 / 1,000,000 x $0.50 = $0.180
- **Estimate: $0.324**, excluding retries, cache, tool calls, taxes, output/reasoning variation.

Proposed $5.00 maximum is NOT approved. configs/budget.example.json sets allow_paid_api_calls and explicit_budget_approval both false.

## Offline commands

- .venv/bin/python tools/cost_budget.py — estimate only.
- .venv/bin/python tools/cost_budget.py --authorize — intentionally BLOCKS (exit 2) even if flags are later flipped, because a durable billing ledger does not exist yet.

## Live runner release requirements (future G2)

- Explicitly approve maximum USD, model ID, service tier, pricing snapshot, output token cap and retries.
- A durable, concurrency-safe reservation ledger; maximum-cost admission before each API request and reconciliation of actual provider usage (including reasoning tokens).
- Stop further requests if usage is unknown, estimated remaining cap is insufficient, timeout/retry limits are exceeded, or provider prices change.
- Keep API keys in a trusted orchestrator only, never in untrusted model-generated Python execution or prompt/sandbox.
- Provider-side project spend alerts and credential revocation independently from local enforcement.
- Never expose ground-truth IFC, scorer internals, private evaluation data or API tokens to the tested model.

Negative tests in tests/test_budget.py cover unapproved spend, invalid rates/model/limits, malformed config and missing paid-run approval. No G0 command can make a paid request.
