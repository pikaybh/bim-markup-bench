# G1 #16 — Frozen 36 candidate source/oracle/readiness reconciliation

**2026-11-10 · Status: BLOCKED_FROZEN_36_NO_COMPLETE_TASK_ORACLES_OR_LIVE_SCORER.**

This research artifact reconciles previously isolated evidence without changing
one task ID, stratified sample, author-visible context, scoring formula or
source IFC. It is **not a paid pilot**, **not experimental model performance**,
and **not a fresh run of the author's BIM-Edit evaluator**.

## Question answered

**How many of the original predeclared 36 task candidates are currently
substantiated as ready for matched D0/XML versus I0/Python LLM execution?**

**Zero complete instruction-specific paired task oracles.** The trustworthy
source of this answer is not module presence or historical "PASS" labels
but an independently checked crosswalk between the original pilot candidate,
the existing complete 324 metadata-only G1 support matrix, today's native
source-only preflight, the pinned partial source/reference asset audit,
two distinct real-source manual demonstrations, the official scorer
provenance gate, offline mock-token budget, and the actual Docker daemon
status.

**Revalidated now:** 11 source IFC preflights, immutable candidate and
prior report bytes/hash values, two manual demonstration source hashes and
capability tags, local Docker admission via read-only CLI.
**Not revalidated now:** ground-truth IFC/model target bytes
recorded in the historical asset audit, official IFC edit scores or
full D0/I0 natural-language task success.

## Exact coverage dimensions

| Reconciliation dimension | Count | Interpretation |
| --- | ---: | --- |
| Public BIM-Edit tasks in pinned task metadata | 324 | Metadata-only original source revision, not 324 IFC runs |
| Stratified candidate task IDs | 36 | Six classes; 18 strata x 2 task IDs, no reselection |
| Original candidate D0+I0 run slots per repetition | 72 | No model has used any of them |
| G1 static metadata engine-unimplemented classes/operations (324) | 246 | Neither official unsupported rate nor tested LLM failures |
| G1 conditional metadata cases (324) | 78 | Require native source and paired oracle proofs |
| Frozen 36 static engine unsupported | **23** | Source IFC probing not required for this existing static classification |
| Frozen 36 conditional with locally missing input cache | **2** | Cannot verify source-dependent changes now |
| Frozen 36 native input IFCs checked in current audit | **11** | Hash-pinned source-only model; no GT read |
| Conditional source tasks with constraints/oracles pending | **9** | Source dependencies, native relations, unsupported edit semantics |
| Conditional tasks with a *distinct* manual source-only pair demonstration | **2** | Do not count multiple reports for one task as extra tasks |
| Full instruction-specific paired D0/I0 task-oracle approvals | **0** | No LLM/scorer experiment can be justified from these reports |
| *Historical* verified original input+reference bytes and class deltas | **30/36** | Reused SHA-pinned 2026-11-09 asset audit; **not reverified now** |
| *Historical* unavailable original/ref bytes | **6/36** | Asset report separate from today's 2 missing source files |
| Author-official IFC benchmark scores calculated by this project | **0** | Author published CSV reaggregation does not count |
| Real paid model API calls | **0** | Mock USD/microtoken accounting remains synthetic only |

Disposition of **all 36**, mutually exclusive:
23 static unsupported + 2 missing cached original inputs +
9 native source blockers/full task-oracle gaps +
2 partial manually selected D0/I0 source demonstrations.
Full task IDs and reason codes are in
`reports/g1_frozen_pilot_readiness_20261110.json` as public task
identifiers only. Each row retains class, operation, category, scene,
legacy static/native reason, historical source-and-GT verification *flag*
and gated manual evidence code. It contains **no task prompt, target GUID,
source IFC path, original/reference IFC bytes or independent full solution**.

### What changed since the old 2026-11-09 source audit

The currently pinned 2026-11-10 source-only report changed **one**
conditional status for `WIN-UPD-DIR-A-002`:

- Before: `OPENING_MOVE_NATIVE_FRAME_OR_DEPENDENCY_BLOCKED`.
- Now: `WINDOW_MOVE_VECTOR_AND_PAIRED_ORACLE_NOT_PROVEN`.

The rotated/opening frame preflight obstacle is no longer the first reported
blocker, but the **full instruction-specific world vector and fair D0/I0
task oracle are still NOT proven**. This is a real improvement in
engineering feasibility, not a benchmark success.

### Manual demonstrations: two distinct partial cases, not two solved tasks

- `WIN-UPD-DIR-A-002`: the 2026-11-09 real source-native
  manual translation (one trusted chosen displacement) generated two
  independently observed IFC variants with matching non-target
  state and identical full source hashes. The model did **not**
  interpret the complete instruction, official GT/evaluator was
  not loaded, and the actual task-specific model-facing information
  parity is unverified.
- `WAL-CRE-SPA-A-003`: D0/I0 source-backed native wall/space
  topology/room subdivision can agree at IFC schema, geometry and
  relations with an **experimentally separate v0.2 markup extension**.
  Yet the native room metadata was synthesized with manual
  source-only assumptions; the actual benchmark prompt does not
  prove that new room type/Psets, function and material are correctly
  inferred. The v0.2 authoring layer is not approved for the live
  D0 model; neither full model-facing input parity nor official scoring
  has been established.

The wall task has multiple dated reports, but **only one** frozen
pilot task ID. Its earlier v0.1 and later v0.2 evidence is never
double counted, and the `PASS` in an experimental context
cannot become `full_instruction_specific_paired_D0_I0_task_oracles_proven=1`
without a new prospective, task-specific protocol and independent GT-only check.

## Actual host and official gates

- The Windows 11 Docker Desktop **Linux Engine** local pipe
  `//./pipe/dockerDesktopLinuxEngine` remains unavailable;
  `com.docker.service` is Stopped (Manual).
- Admission `BLOCKED_LOCAL_DOCKER_ENGINE_UNAVAILABLE`.
  The process only issued existing **read-only** Docker info checks.
  It did **not** start/restart Docker Desktop, WSL, services, or containers.
- Published author score tables are available but the **exact
  executable official IFC scorer source/commit is not verified**.
  Project evaluator remains
  `metric_origin=independent-reimplementation`.
- Real model/provider rate/token envelope and cost cap are
  **not** approved; prior durable budget exercise is an
  `offline/mock-v0` **synthetic micro-USD test**.
- Candidate pilot is **not preregistered**; frozen labels are intact
  and no new "common supported" experimental subset was selected
  post hoc.

**Therefore G1/G2/G3 live release is BLOCKED.**

## Evidence architecture / fail-closed conditions

Implementation:
- `src/evaluation/frozen_pilot_readiness.py`
- `tools/audit_frozen_pilot_readiness.py`
- `tests/test_frozen_pilot_readiness.py`
- `reports/g1_frozen_pilot_readiness_20261110.json`

The audit first SHA-256 verifies the **exact byte content of nine**
approved candidate/source/asset/manual/scorer/budget reports and refuses
symlinks. Then it invokes the **existing conservative source-only native
IFC preflight** for the 36 selected entries and requires it to be
byte-for-byte equivalent in structured JSON form to the reviewed
2026-11-10 snapshot. Any drift requires an explicitly reviewed update,
not silent "new supported case" promotion.

The pure reconciliation validates cross-report agreement on all 36
public task IDs, operations, categories, classes, scene strata,
reason code counts, 324 static engine classifications, 30/6 previous
input/reference audit records, 11 current source probes and
2 distinct manual proof source identifiers with no official/model runs.
It prevents forged or unexpected full-oracle, Docker worker, official
scorer and model budget authorization. The output contains **only
public task IDs, safe reason labels, boolean support evidence and
source file SHA-256 summaries**.

### Reproduce on Windows PC (no network, no GT, no model)

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_frozen_pilot_readiness -v
.\.venv\Scripts\python.exe -m tools.audit_frozen_pilot_readiness
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

The CLI intentionally exits **2** for
`BLOCKED_FROZEN_36_NO_COMPLETE_TASK_ORACLES_OR_LIVE_SCORER`.
The tests should exit **0** when internal evidence invariants
are maintained. No snapshots, manifest or unsupported case has been
altered to improve apparent readiness.

## Prioritized independent next engineering gates

1. **Source/asset rights:** distinguish six missing historical
   input/reference pairs from two currently missing conditional source
   inputs. Source/reference full byte provenance and individual IFC
   license clearance are prerequisites before legitimate large-scale
   official-model comparisons; no large dataset downloads authorized
   by this PR.
2. **Task-specific D0/I0 oracles:** begin with the two already
   demonstrated **manual** source-pair candidates. Freeze an exact
   externally observable edit target from allowed public instruction
   only and independently test all task-required geometry, topology,
   room metadata, world transforms, untouched state and equal model
   information *without relying on the GT in model prompts*.
3. **Engine domains:** implement missing six-class CRUD operations
   under a reviewed versioned schema/ABI, maintain exact relation
   semantics, and rerun the **entire** frozen 36; never choose easy
   tasks as the primary denominator.
4. **Worker/evaluator:** restore and read-only attest a local
   Docker Linux Engine for actual OWN-only kernel isolation;
   obtain author's official scorer or preregister the explicitly
   different independent metric. Verify provider token usage/pricing,
   a legitimate model budget, isolated code/GT processes before G3.
5. **Statistical design:** confirm frozen 36 paired 72 run slots;
   exclude unsupported from common-supported analyses only through
   an **independently preregistered** eligibility rule, and still report
   full-set ITT (unsupported as fail).

These are preparation tasks, not evidence that the research hypothesis
favors XML or Python. Official benchmark tasks scored **0**;
real LLM model provider calls **0**.


## Actual regression on connected Windows 11

- Focused tests: `python -m unittest tests.test_frozen_pilot_readiness -v`
  → **17 passed, 0 failed**.
- Full suite: `python -m unittest discover -s tests -q`
  → **508 total; 487 passed, 21 pre-existing conditional skips,
  0 failures** (`202.672s`).
- Code compilation check: passed.
- Git staged whitespace/error check: passed.
- Read-only live source audit: matches the pinned 2026-11-10
  36-task source report with no drift; expected CLI exit **2**.

Any assertion that the numerical 36-task LLM performance was measured
from these engineering checks is unsupported and must be rejected.
