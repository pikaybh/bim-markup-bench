# G3 — Proposed three-arm 36-task contract and zero-inference replay (2026-11-20)

**Issue #247 · Draft PR #250 · existing single `bim-markup-bench` Windows checkout**

## Outcome

This checkpoint implements and tests a **non-authorizing, prospectively reviewable candidate** for the three labels `D_FULL`, `D_MANAGED`, `I_NATIVE` inside the existing `src/runner/manifest.py`, while keeping the legacy, research-historical `direct_xml`/`imperative_python` two-arm scheduler untouched. **This is not a finalized registered experiment and is not an executable three-arm model harness.**

- The original frozen BIM-Edit 36-task pilot remains unchanged. Deterministic, randomized counterbalanced scheduling yields **36 × 3 = 108 planned slots** with all three arms and the same original source hash within a task.
- Every arm appears 12 times in each ordinal position (first, second, third) over the original **full 36**, using each of six permutations exactly six times. It does **not** claim position balance within the **30 locally available** subsample.
- Original content verified for **30 tasks → 90 input-available but scientifically nonrunnable slots**. Five original input IFCs are still absent, blocking **6 tasks → 18 planned slots** without cohort shrinking or denominators being rewritten.
- **Runnable slots: zero.** The proposed `D_FULL` feature is not implemented as native-complete declarative authoring; the actual `D_FULL` versus `D_MANAGED` treatment contrast has not been established. `I_NATIVE` has independently tested security on owned fixtures and trusted original-input mount probing, **not** an approved model-generated real-BIM-Edit edit/evaluator workflow.
- Both existing G2 adapter defaults are checked against the candidate limits: **1 one-shot attempt; 180 seconds; 32,768 UTF-8 submission bytes**. The proposed model ceilings inherit **20,000 input and 6,000 output tokens** from the unregistered original two-arm draft. Feedback rounds are zero and the plan proposes one model-authored submission per arm. Separate model/tool feedback implementations still require proof.
- **Synthetic** pure-function tests reject any wrong arm authoring tool, second submission, additional response/feedback round, wrong type or 32,768+ payload. A separate synthetic token-envelope check refuses over-20,000 input and over-6,000 output counts. **These numbers are fixture counts, not actual provider or tokenizer counts; no provider receipts, model requests, paid tokens or price quotes exist.**
- The validator also pins actual model-visible text, not Windows CRLF host bytes: shared XML language documentation is **7,383 UTF-8 bytes** (SHA256 `05703e0ba035ccddfe942593dbe6e4c2355d989fd86ec97b6ad70985c53a284e`), and I-only API notes are **1,113 UTF-8 bytes** (SHA256 `cb6f952ee2b3e6e1f69836e99c3681dbdaf4071bcfb045843778c35f53a26901`). Altering either file fails the preflight, with negative tests.
- The I arm presently receives an extra **1,113-byte IfcOpenShell API reference** that D does not. Existing common projected XML equality for 30 tasks has been proven; full model-visible documentation, native source query semantics, actual tool/feedback parity, complete D full-geometry representation, registered variants or actual provider token parity have **not**.

## Exact artifacts

- Three-arm **candidate**, never a change to the historical two-arm `configs/pilot_36_plan_v0.json`: `configs/pilot_36_three_arm_candidate_v0.json`.
- Existing scheduler extended, not replaced: `src/runner/manifest.py` → `validate_three_arm_candidate`, `three_arm_candidate_schedule`, `validate_synthetic_one_shot_trace`, `validate_synthetic_token_ceiling`.
- Canonical, reproducible JSON of **all 108 nonrunnable planned slots**: `reports/g3_three_arm_108_slot_candidate_schedule_20261120.json`, SHA256 `c47e9222e3d533c7771ab49e3fc1a237a6344a9c7835c28e8ed8594090a58707`.
- Unit and negative security/ablation controls: `tests/test_three_arm_candidate_contract.py`. Modified contract fields are rejected, including unapproved provider/model/tokenizer/spend, enabling native D_FULL without implementation, dropping missing tasks, changing feedback/retry ceilings or mislabeling mock token counts as real.

## Replay without model calls

```powershell
.\.venv\Scripts\python.exe -m src.runner.manifest --check-three-arm-draft
.\.venv\Scripts\python.exe -m unittest -q tests.test_three_arm_candidate_contract
```

The first command **regenerates the plan in memory and checks the entire stored report byte-for-byte**, without rewriting it. The original evidence was created once with `--write-three-arm-draft`, which fails rather than overwriting an existing report.

## Research decision (still blocked)

The three-arm labels are not evidence for three validated experimental interventions. A defensible prospective scientific design must define in advance exactly what D_FULL and D_MANAGED can observe and edit, which task strata both support, the I arm's reference documentation exposure, matched feedback and tool invocations, independently validated task output metrics and scorer, actual provider tokenizer usage accounting, pricing/receipt captures, model snapshot/seed/temperature, and acceptable source-use/transfer policy. Outcomes should include original source-building clusters rather than treating 36 correlated task rows as independent buildings. If unsupported strata are excluded from a primary estimand, that exclusion must be prospectively justified and the original fixed 36-task ITT table must still show its nonexecuted rows.

Even an exact 108-slot schedule cannot authorize running any model. All original source rights, 5 missing IFC inputs (6 tasks), cross-task GT-role aliasing, original building lineage, original benchmark-score reproduction and actual provider cost approval remain unresolved. **Do not merge Draft PR #250 or mark Issue #247 completed on the strength of this offline plan.**
