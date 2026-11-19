# G1 #16 / G2 #19–20 — First matched model experiment: actual readiness after deterministic IFC rubrics

**Date:** 2026-11-11 KST.
**Technical result:** 6 native D0/I0 source-relative checks PASS on 3 fixed original source IFCs.
**Real LLM release:** BLOCKED. **0** model calls, **0** official or independent full-task scores, **0** paid inference.

## Research target and what is *not* a result

The scientific question is whether an LLM editing the **actual declarative
XML source state** can outperform the same LLM producing Python/IfcOpenShell
edits, under controlled input, tools, evaluator and budget. We must not
confuse successful post-hoc, **developer-authored** native IFC candidates
with any LLM task success or with the original BIM-Edit benchmark score.

The original 36-case candidate list is unchanged and not preregistered;
30/36 were historically hash-verified original/reference IFC pairs but
individual model-level reuse rights remain unresolved, and six pairs
are missing. In previous source-only checks, only 11 conditional
source documents generated matched common D0/I0 input texts. This
does **not** prove actual model token/feedback parity.

For the technical proof here, fixed three task IDs, one per operation:
WIN-UPD-DIR-A-002 (update), WAL-CRE-SPA-A-003 (create) and
DOR-DEL-DIR-A-001 (delete). The third case became supported only
after engineers inspected its particular public source; the selection
is **post-hoc and not a statistically legitimate primary analysis subset**.
The other 33 original cases stay in the study denominator, including
all historical unsupported and unavailable statuses.

## Independently executed IFC-native postconditions (source-only surrogate)

New trusted grader:
src/evaluation/three_case_source_rubric.py

This **independent source-relative rubric** never imports the D0
compiler, XML source-rewrite policy, the I0 *authoring* recipe, an LLM
runtime or a model-generated solution. It uses only original pinned
public IFC, authored candidate IFC and the published natural-language
task instruction. It relies on the pre-existing independent native
IFC inspection and Door dependency checker under tests/oracles/python;
it is neither the author's official grader nor a generic IFC scorer.
It has SHA-locked input and instruction for each of the three
demonstrations. The exact checks were written after source inspection
and are explicitly *post-hoc*.

| Frozen task | What MUST pass (native source-relative, not GT) | What remains scientifically unknown |
| --- | --- | --- |
| WIN-UPD-DIR-A-002 | Window and Opening retain identities, move **+1.0 m world Y** in placement AND world geometry; all other product shapes, root identities, relationships, material/Psets unchanged | Full benchmark reference interpretation, true model inference and feedback/token parity |
| WAL-CRE-SPA-A-003 | Exactly **one** new Wall and **two** new native path joins; no deleted original roots; unchanged original product shapes, property sets and materials; new Wall 0.175m thickness, 2.8m height, correct door-relative +1.3025m world-Y and room floor elevation | Whether a further Space split/Room type/Pset is expected or necessary |
| DOR-DEL-DIR-A-001 | Door and Opening cascade: exactly **10** specified IfcRoot removals; **13** unrelated product world meshes unchanged; host Wall void closed; shared memberships adjusted only as permitted | The original Door SpaceBoundary cascade policy and nonexistent direct Opening→Storey relation; normative/benchmark space boundary completion |

These are *Boolean* source-relative native diagnostic checks and
not the paper's geometry/semantic/topology axis scores, and not
a full instruction-specific oracle. Each candidate's native IFC is
re-opened, source/output hashes are checked against mutation, wrong
classes/geometry/relations are rejected and the grader returns
only sanitized, arm-neutral, explicit source-relative evidence.

This audit re-executed exactly **six ephemeral candidate IFC files**
(three D0 and three I0). Both arms pass their own native source-only
predicates, but no benchmark pass ratio is computed.

Positive/negative security and correctness tests:
- actual three D0/I0 ephemeral pair outputs, independent of XML parser and Python authoring implementation;
- unchanged source (no-op) fails for all three cases;
- Window wrong displacement and unrelated new product fail;
- Wall removed path connection, wrong thickness fail;
- Door no-op or unrelated new root fails;
- modified published task prompt, substituted source IFC, invalid STEP IFC fail;
- report status cannot be promoted to full-task success, official scorer equivalence, rights clearance or model-generated performance.

A native checker "PASS" is valid only under these explicit predicates.
The user must not interpret this as **3/3 tasks solved**.

## Readiness against actual host, data rights and budget

Read-only local Docker/Linux worker admission check rerun on this
connected Windows 11 host. It found:

- **BLOCKED_LOCAL_DOCKER_ENGINE_UNAVAILABLE**: Windows Docker Desktop
  Linux daemon not reachable; independent Linux kernel/isolation for
  model-generated Python unavailable.
- The earlier OWN-only synthetic Docker demonstration and image SHA
  are *historical*, not a current general task-worker admission.
- No WSL, Docker service, container, Python model-generated script,
  external network or LLM subprocess was started.

New report:
reports/g2_local_worker_live_preflight_20261111.json

SHA-256:
a27fd255f8d499cec63b08056cfaa5802a781488b17aa67544841a0ca8e0f592

G0 IFC legal evidence:
reports/g0_pilot_ifc_rights_20261110.json

- 30 historically pinned source/reference IFC pairs, six incomplete.
- **0** individual external model license documents cleared.
- The dataset card's generic CC BY 4.0 is not proof of every source
  architectural model's reuse/redistribution terms.
- Native IFCs and their paths remain outside Git and model contexts
  unless model source rights and privacy conditions are approved.

G2 budget evidence:
reports/g2_durable_budget_dryrun_20261110.json

- Existing durable budget tests use **OFFLINE_SYNTHETIC_VALUES_ONLY**.
- No verified actual provider model ID / API envelope / tokenizer usage,
  current price revision, cost cap approval or real usage accounting.
- The example budget config is **PROPOSED_NOT_AUTHORIZED**; its rates,
  model label and US-dollar cap are not proof of currently valid prices,
  access rights or an authorization to submit paid requests.
- Context evidence is only *common text byte equality* for 11
  source inputs, not model wire-format or billed tokens.

## Prepared fail-closed first pilot gate

New implementation:
src/evaluation/first_pilot_release_preflight.py

New read-only, write-once command:
tools/audit_first_matched_pilot_preflight.py

It verifies exact SHA-256 of original 36-candidate source-readiness,
model-rights, Docker, synthetic-budget and G2-context reports. It
recreates three ephemeral D0 and I0 IFC outputs using independent
developer-authored recipes, then checks **all six** through the
new source-relative native rubric. It rejects forged scores, changed
rights/budget snapshots, wrong case IDs, missing paired runs, source
mutation, non-passing native postconditions, or a claim that a
model/official scorer/paid trial was executed.

The CLI intentionally returns **exit code 2**. This means:
native technical checks passed, **real trial NOT authorized**.

New evidence:
reports/g2_first_matched_llm_preflight_20261111.json

SHA-256:
557abffe46de5db48481aa1ee6e0bd838800a20e89938f436d1bf7647db5e0b8

## Reproduction on connected Windows (NO provider or Docker execution)

In D:\문서\D__1_Projects\202611\bim-markup-bench:

    $env:PYTHONUTF8='1'
    .\.venv\Scripts\python.exe -m unittest tests.test_first_pilot_source_relative_rubric -v
    .\.venv\Scripts\python.exe -m unittest tests.test_first_pilot_release_preflight -v
    .\.venv\Scripts\python.exe -m tools.audit_first_matched_pilot_preflight --output-json reports/new-replay-preflight.json
    .\.venv\Scripts\python.exe -m tools.audit_local_worker_admission --output-json reports/new-replay-worker.json
    .\.venv\Scripts\python.exe -m unittest discover -s tests -q

Use fresh report names. Both preflight CLI tools deliberately return 2
with outstanding gates, and refuse to overwrite earlier evidence.

## Prospective next-run contract (NOT preregistered and NOT authorized)

A **small engineering smoke** may use only the fixed three case IDs
and two arms for 6 potential cell attempts under a separately approved
low-cost model setting, but must NEVER be represented as a randomized
or preregistered comparison of the original 36-task pilot. The original
36/72-arm-slot design remains untouched.

No real inference can begin until ALL of:
1. Verify rights/consent for each of the three original public IFC
   source models (or conduct an independently labeled pilot on our
   own wholly synthetic/openly licensed IFCs instead).
2. Define and prospectively review each full instruction-specific
   **independent** graded-task contract and negative controls, including
   exactly which Wall Space and Door SpaceBoundary side effects count.
   Label results **independent**, never "official BIM-Edit" without code
   parity. Sequester GT from both model authoring workspaces.
3. Verify a local Linux worker and immutable image/lock provenance
   with actual malicious-code isolation/mount/secret tests. I-arm
   arbitrary Python must never execute on unrestricted Windows host.
4. Select a specific provider/model/version, fixed generation settings,
   token/attempt/time limits, common D/I source observations, allowed
   feedback cycles, and provider-reported usage transport.
5. Independently verify current model rates and obtain an **explicit**
   US-dollar spend cap; enforce a durable pre-charge reservation and
   account for retries/unknown billing, with safe failure.
6. Version, independently review and preregister experimental
   eligibility, denominator, metric tolerances, seeds, artifact
   retention and cluster-correct inference **before seeing LLM outputs**.

Missing original author scorer is not itself a mandatory blocker if
the independent evaluator is separately defined and appropriately
validated. The listed model rights, isolation, experimental fairness
and actual budget approval ARE blockers.

**Current decision:** no live LLM or paid experiment. Do not equate
six post-hoc surrogate diagnostics with six benchmark successes.


## Actual regression execution results

- Source-relative scorer + first-pilot gate targeted unit suite:
  **25 tests, all pass** before the minor clarification that the
  evaluator does not itself authenticate who authored a candidate.
- Full repository regression on connected Windows 11:
  **668 tests, 647 pass, 21 skipped, zero failures** (427.657 seconds).
- Source-relative scorer and preflight are research-only trusted code,
  not exposed to a future D0 or I0 LLM worker. The grader's verdict
  never asserts that it independently verified whether a caller's
  IFC was LLM-generated; the runner records that provenance.
- Parser/IFC errors and wrong relationships were rejected by negative
  fixtures, with no original IFC mutation or artifact publication.
- Syntax compilation, staged Git whitespace check and redacted report
  field audit pass.
