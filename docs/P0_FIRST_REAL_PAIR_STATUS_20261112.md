# Issue #97 / P0 — First actual model-generated XML vs Python IFC edit

## Status (2026-11-12 KST)

**P0 not yet complete. Actual provider calls: 0. Real LLM solutions: 0.
Paid spend: $0. Actual head-to-head results: 0.**

We have deliberately stopped adding new BIM features or full benchmark
evaluation infrastructure. All work below is immediately needed for the
single first LLM A/B task and not a result of the comparison.

### Exact test case frozen for this exploratory first smoke

- OWN self-generated source: tests/fixtures/synthetic/input.ifc
- Source SHA256:
  10d57d3eeb6e50fb51493b03d7cb508d57eadeb76719afaeb71fa6658c3ecf58
- IFC schema: IFC4X3.
- One public instruction:
  Change only North Wall height from 3.0 m to 3.3 m. Do not modify any
  other IFC object, identity, relationship or geometry.
- A/D: receive source XML partial projection and same XML language
  specification; LLM must return full edited XML text; trusted compiler
  applies XML document-state difference to original IFC clone.
- B/I: receive **same** original XML partial projection, spec,
  instruction; only this arm additionally gets minimal IfcOpenShell API
  notes. LLM must produce executable Python; the immutable OWN IFC input
  is mounted read-only in the Linux container.
- Both outputs are graded using the **same exact OWN source native IFC
  wall-height check**: wall extrusion depth 3.3, source 3.0, all IFC
  original roots/classes unchanged, only exactly one IfcExtrudedAreaSolid
  STEP entity differs. This first synthetic smoke is **not** an official
  BIM-Edit task or a primary paper statistic.
- Single generation per arm, no retry or tool feedback; same provider
  model, fixed 3500 max output tokens each (including reasoning).
- The D/I *shared context fields* are identical; actual provider
  tokenization/total cost equality is not assumed. Python API notes
  are a transparently recorded arm-specific affordance.

### Actually verified now

1. Launched Docker Desktop as the existing Windows-user application.
   Docker server answered **28.3.2, Linux x86_64**. The pinned local
   OWN worker image already exists, no build/pull needed:
   sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee
2. Reexecuted the OWN synthetic dynamic Linux worker positive and
   embedded adversarial denial proof. Both cases pass in isolated
   candidate/grader containers; source unchanged, no GT, host secrets
   or Docker socket mounted to candidate. Existing dynamic worker
   supports **only this OWN synthetic IFC**, not arbitrary BIM-Edit.
3. Added real Responses API one-shot text generation wiring behind
   explicit owner-approved model/pricing/cap config. It **never calls
   the provider** in its default prepare mode. No automatic retry;
   max two calls only when expressly enabled.
4. Generated D and I **actual model-facing prompt packets**, from
   runtime XML projection and same original IFC, not manually
   written model answers. Raw synthetic packet for reproduction:
   reports/p0_first_real_pair_prompt_packet_20261112.json
5. Connected generated D output -> source-only trusted XML controller
   -> IFC output; generated I output -> AST preflight -> pinned OWN
   dynamic Linux container -> separate native/grader container.
   Added opt-in export of *independently graded OWN IFC only* to the
   research run folder, with exclusive-write and SHA checks.
6. A FakeClient transport inserted developer-written test oracle text
   *only as test fixtures* to prove the whole wiring works (and that a
   wrong Python result is not silently counted as success).
   **This is NOT an LLM run or a performance comparison.**

### Files

- tools/p0_first_pair.py — minimal actual P0 provider-to-IFC runner,
  with default no-billing prompt preparation
- src/runner/generated_candidate.py — optional verified OWN-only IFC
  export after isolated independent grader pass, default behavior intact
- configs/p0_approval.example.json — intentionally NOT APPROVED; rates
  zero so it cannot accidentally authorize a paid call
- tests/test_p0_first_pair.py — fake transport and hard gates
- reports/p0_first_real_pair_prompt_packet_20261112.json — OWN prompts
- reports/p0_own_dynamic_sandbox_recheck_20261112.json — actual sandbox test

### Reproduce safely, ZERO provider calls

From D:\문서\D__1_Projects\202611\bim-markup-bench:

    $env:PYTHONUTF8='1'
    .\.venv\Scripts\python.exe -m tools.p0_first_pair --prepare
    .\.venv\Scripts\python.exe -m unittest tests.test_p0_first_pair -v

Both commands **must execute without any model key**. The configured
model, key and API spend are NOT inferred from a ChatGPT subscription.
An environment variable is a transport credential, not cost consent.

### How the first real LLM pair will actually run — NOT YET AUTHORIZED

Requires the user to select and approve an exact API model and USD cap,
and verify current per-million-token input/output rates. Configure a
private copy of configs/p0_approval.example.json outside Git. Do NOT
commit that approval file, API key or credentials. Set:

- approved = true only after actual user approval
- model = the exact provider API model ID, not a made-up alias
- input_rate_per_million_usd / output_rate_per_million_usd = verified
  current decimal-string values from the official API pricing page
- cap_usd = approved positive decimal <= 10
- price_checked_utc = actual current verification timestamp
- max_output_tokens = 3500 fixed
- OPENAI_API_KEY in the process environment, never in the JSON

Then, and only then, use a new output directory:

    .\.venv\Scripts\python.exe -m tools.p0_first_pair --run-approved --approval-file C:\private\p0_approval.json --out C:\private\p0_runs\attempt_001

The runner makes at most two ONE-SHOT provider calls (D then I);
retains exact generated source text, actual response token counts
when provided, output IFCs if they pass, and negative/failure records.
Usage-derived costs are estimates, not provider invoice reconciliation.
A provider API exception may still incur charges; it cannot be
automatically retried. The total worst-case token envelope is bounded
by approved cap before sending either request. No benchmark GT is sent
to the model or mounted in the Python candidate.

**Remaining blocking input: selected provider model / explicit cost cap,
valid verified prices and user-provisioned OPENAI_API_KEY.**

Do not present the mock transport result, prepared packets or existing
D0/I0 oracle parity as a successful real-model comparison.


## This turn's test evidence

- Actual Linux OWN dynamic worker and hostile-code denial: 2 independent
  sandbox cases PASS; evidence is the pinned read-only/isolated run report.
- With Docker image explicitly pinned: P0 and existing dynamic worker
  regression 15 tests PASS, zero skipped.
- P0 focused integration/negative tests after latest changes:
  6 PASS in 14.077 seconds, zero failures. The successful two-arm
  FakeClient demonstration used preauthored code and is *not* a model test.
- The unapproved example config was passed to the live entrypoint as
  a deliberate negative check: request was refused before client/network
  creation, no output directory created. OPENAI_API_KEY absent on host.
- Syntax compilation and staged Git whitespace checks PASS.
- Full legacy suite was not rerun in this P0 change; previous baseline
  668 tests PASS including 21 skipped belonged to the prior branch.
