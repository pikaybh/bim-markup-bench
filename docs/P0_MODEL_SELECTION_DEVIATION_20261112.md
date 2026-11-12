# P0 configured model deviation — 2026-11-12

**Incident:** The actual first paid P0 paired LLM experiment used
`gpt-5.4-mini-2026-03-17`, but the operator-owned, Git-ignored
`.env` explicitly specified `OPENAI_MODEL=gpt-6-luna`.

### Verified cause

- The runner in `tools/p0_first_pair.py` selected its API model from
  the separately prepared `results/p0_approval_20261112_private.json`.
- The operator's `.env` contained `OPENAI_MODEL=gpt-6-luna` and
  `OPENAI_API_KEY` (key existence checked without exposing its value).
- The assistant had manually put the cheaper 5.4 mini model into the
  paid-run approval file instead of respecting the model specified
  by the user. The code did not cross-check it.
- A non-generating OpenAI model metadata request verified that
  `gpt-6-luna` is accessible to the configured API key. This is
  **not** a completed generation or a paid LLM trial.

### Scientific interpretation and correction

The prior P0 real paired trial is reproducible as a **5.4 mini**
exploratory result: one owned synthetic task with D/XML native success
and I/Python preflight failure; two calls, estimated total token
cost USD 0.0072990. That result is **NOT the user-configured GPT-6
Luna experiment** and must not be represented as such. Correct
GPT-6 Luna LLM edit attempts and native results remain **zero**.

No existing result file, IFC model, output hash, old charge or model
text is changed. No additional generative model calls are made in
this correction.

The paid live entrypoint now:
1. Loads the Git-ignored repository `.env` when invoked directly,
   without overriding an existing environment setting.
2. Requires `OPENAI_MODEL` to be present.
3. Refuses any live paid call if `OPENAI_MODEL` does not exactly
   match the explicitly approved run manifest's `model` field.
4. Preserves the independent explicit USD budget/cost approval
   and exact model-version review. A model-name match is not
   itself permission to spend.

A regression test constructs exactly this mismatch
(`OPENAI_MODEL=gpt-6-luna`, approved manifest =
`gpt-5.4-mini-2026-03-17`) and verifies that a ValueError occurs
**before any provider client is instantiated** and no output
directory is created.

The previous $1 approval was for the two already-executed
requests, **not an authorization for another paid pair**.
Future Luna requests require a fresh price review and approved
cost ceiling; never silently substitute a cheaper model.
