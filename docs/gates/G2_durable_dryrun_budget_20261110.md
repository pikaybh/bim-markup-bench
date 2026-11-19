# G2 / Issue #20 — durable *offline* budget reservation and reconciliation proof

**2026-11-10. Research status: simulated ledger verified; real provider still strictly BLOCKED.**

## Motivation and scope

Issue #20 requires an auditable, persistent global spend ceiling, request token
envelopes, attempt caps, crash-safe persistence and no double spending between
D0 and I0. PR #76 established exact UTF-8 source-context measurements and
**no verified provider token counts**. The next engineering step is to test
the reservation/reconciliation mechanism separately, without accidentally
enabling any paid API or falsely claiming that a provider reports our synthetic
token counts.

This change adds `src/runner/durable_budget_dryrun.py` as a **separate,
OFFLINE-ONLY simulation module**, not as a provider transport or a live runtime.
The module does not import any vendor SDK, open an IFC model, call a network API,
load an LLM, inspect GT, or alter `src/runner/costs.py`,
`tools/cost_budget.py`, frozen manifests, prompt budgets or experiment models.

### Important accounting distinctions

- All `planned_input_tokens`, `planned_output_tokens` and settled
  `input_tokens`/`output_tokens` in this simulation are **explicitly
  artificial fixture integers**, **NOT** measured model tokens.
- The `hypothetical_input_usd_per_million` and
  `hypothetical_output_usd_per_million` are **synthetic test prices**,
  not a current price quote from any vendor.
- The model is restricted to `offline/mock-v0`; the price revision is locked
  to `OFFLINE_SYNTHETIC_QUOTE_NO_PROVIDER`. Substituting a real model or
  production price revision fails policy validation.
- Calculations use exact Python `Decimal`; reserved and settled costs are
  conservatively **rounded UP to integer micro-USD**. The cap is conservatively
  rounded DOWN. No floats or ambiguous `NaN`/`Infinity`/negative monetary
  values are accepted.
- The proof **does not** represent a validated payable system: there is no
  provider-side tokenization, wire-format preflight, price tier, cached/reasoning
  token billing, provider receipt, networking, credentials or durable live cost
  adapter. Actual provider token counts and USD charges are always `null`.
  The paid execution gate remains unchanged and blocked.

## Durable state machine

The SQLite database is created only under an existing local directory. A
single canonical policy and its budget, mock model, synthetic rate revision,
token ceilings and retry/concurrency ceilings are persisted and checked on
every open. SQLite `BEGIN IMMEDIATE` transactions serialize reserve, dispatch,
settlement, cancellation, and unknown-usage state transitions across database
handles and processes. SQLite WAL and `synchronous=FULL` are enabled for the
local stress test; this is a storage mechanism, not evidence of production
cross-host HA or security hardening.

- `RESERVED_UNSENT`: a unique attempt holds its **whole worst-case**
  hypothetical token-cost envelope. Duplicate attempt IDs, other task/arm
  retries beyond cap and reservations exceeding the global cap are refused.
- `DISPATCH_UNCONFIRMED`: the hypothetical request is marked dispatching;
  a crash/uncertainty does not silently refund reserved budget.
- `SETTLED_OFFLINE`: only explicitly supplied synthetic fixture token usage
  within both reserved input/output ceilings can settle, exactly once. The
  difference becomes available capacity, with a fully retained attempt record.
- `UNKNOWN_USAGE`: uncertain usage permanently retains the full reserved
  envelope pending a future, independently proven reconciliation mechanism.
  It cannot be canceled or settled by a replay of this mock API.
- `CANCELED_UNSENT`: a reservation never marked dispatched may be
  explicitly canceled. Its amount is freed but its attempt still consumes a
  retry slot, preventing silent reruns.

No operation connects to a provider. There is no mechanism in this module to
authorize paid execution; `provider_execution_authorized=false`,
`paid_run_authorized=false` and `real_provider_calls=0` are intentional.

## Verification

`tests/test_durable_budget_dryrun.py` verifies:

- Initial reservation, close/reopen and exact persisted micro-USD totals.
- A second and third request cannot oversubscribe a shared global cap.
- **10 competing threads** and **6 independently spawned Python processes**
  racing on the same ledger; each batch accepts exactly the number allowed by
  the fixed cap. No duplicate accepted attempts.
- Unique attempt IDs, per-task/arm retry caps and unchanged policy/price on
  reopen, including refusal of fake real model IDs or rate revisions.
- Repeated settlement and oversized usage refuse with original reservation
  intact; no partial commit leaks.
- Pre-dispatch cancellation versus unknown dispatch, with unknown reserved
  capacity never automatically refunded.
- Decimal rounding toward conservative reserve/cap accounting; unsafe path and
  invalid token field rejection. Optional Windows symlink privilege does not
  change core pass/fail.
- Model calls, real billing/usage, scored tasks and authorization remain zero
  even after a successful mock ledger flow.

`tools/verify_durable_budget_dryrun.py` produces a sanitized evidence summary:
`reports/g2_durable_budget_dryrun_20261110.json`. It intentionally returns
**exit code 2** for the still-unapproved live-model research gate, even when
its independent simulation assertions all succeed.

### Synthetic example (NOT current vendor prices)

A made-up **$0.000300** cap, input/output unit quote of **$1 per 1M tokens**,
and two example requests with 100+50 *hypothetical tokens* each:

- Two reservations consume 150 + 150 = **300 micro-USD**, exhausting the
  simulated cap.
- A third 150-micro-USD reservation is blocked.
- D0 *simulation* settles 75+25 tokens (100 micro-USD).
- I0 *simulation* enters `UNKNOWN_USAGE`, retaining 150 micro-USD.
- A third 50-micro-USD request is reserved and then proven unsent and canceled.
- On reopening the DB: **100 micro-USD settled**, **150 micro-USD reserved**,
  **50 micro-USD remaining** under the hypothetical 300-micro-USD ceiling;
  three unique attempt records remain.

These numbers have **no relation to actual model usage, prices or billing**.

## Reproduce on connected Windows PC

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_durable_budget_dryrun -v
.\.venv\Scripts\python.exe -m tools.verify_durable_budget_dryrun
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

The evidence CLI's exit **2** is expected because it intentionally refuses
to certify a live G3 trial. The test suite's return code **0** shows only
the offline accounting mechanism passed. All SQLite files exist only in
disposable temp directories, and the Git report contains aggregate counts and
outcome flags, not user data, IFC content, model outputs or secrets.

## Read-only inspection of the next blocker: Python OS isolation

The older `reports/docker_kernel_probe_evidence.json` records a successful
**trusted, non-generated** Linux kernel isolation probe. A new read-only
`docker version --format '{{.Server.Version}}'` on the connected Windows PC
during this work failed to connect to the
`//./pipe/dockerDesktopLinuxEngine` named pipe. Docker Linux Engine is
**not currently available to this session**, so no fresh container probe or
model-generated Python execution was attempted; no host service was started.
Historical positive evidence is not enough to claim the I-arm worker is
operational or safe for arbitrary agent-submitted Python today.

## Still required before anything billed or scored

1. Fix a legitimate target model/snapshot, **real** tokenization/provable
   provider per-arm usage and provider wire-envelope preflight.
2. Independently pin current pricing provenance, cached/reasoning/tool charges,
   retry/error billability and a supplier receipt-reconciliation policy.
3. Build/verify live durable budget enforcement against actual dispatch,
   process interruption and ambiguous provider-side requests; extend beyond
   this mock-only local DB and account for shared organizational API spend.
4. Confirm isolated generated-Python sandbox, exact D/I context and tool
   budgets, source IFC and GT licensing, independent official scorer and
   owner-approved paid experiment protocol.

Do not change the official 36/324 sample, interpret these figures as tokens,
or mark `G2_G3_live_pilot_gate` ready as a result of this PR.
