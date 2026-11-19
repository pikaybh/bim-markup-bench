# BIBIMBAP v0.20 — Frozen original 45-task capability gate and offline terminal one-shot broker

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/154
**Parent:** v0.19 Issue #152, Draft PR #153, frozen `21ece56590c982824d4dfa36aabf64b21b59e2ee`
**Research identity:** an independent declarative-XML-vs-imperative-Python BIBIMBAP study. **Not** BIXML/Xim product implementation or a new live LLM score report.

## 1. Research question and frozen source evidence

When comparing direct declarative XML editing (D) against imperative Python/IfcOpenShell native IFC editing (I) on the **original 45 public BIBIMBAP edit tasks**, what can be inferred from *actually reproduced* evidence without mistaking shared reading, a developer-authored successful edit, or an original scorer failure for a causal LLM performance result?

This v0.20 checkpoint makes **no changes** to original IFC datasets, original evaluator or previous results, and makes **zero model/provider calls**.

Five prior reports are **SHA-256 pinned**, independently read and cross-joined by all 45 original task IDs. Both original benchmark Git commits remain frozen: author `667004e16bd38fd7d538bcee56191465429fd975`, data `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`.

| Evidence source | Frozen SHA256 | Scope |
|---|---|---|
| v0.16 native source-only Column parity | `162ff7408429062b4e80abb3fe48bb6bb1b0c0bff51260d04d0a616d7a104ae7` | Public Column and Window original-source pairs, original author scorer provenance |
| v0.17 full native source info audit | `c2683de1705b92ebe0ce8472c6a870b98c54c668e387ddf80c9377cdb2e88078` | 45 original native source IFC/typed XML omission census |
| v0.17 topological slab source-only parity | `c6b02877a3f031c8f5435222b65db4a0fef04568119eaa750586f106d53231e8` | Original `topological_test_15` native and author scoreability, full 45 control statuses |
| v0.18 identical common-read transcript | `89a53c28a9c5e679fcdfb962bebe6b9bd8075e4ac0437e07ea1a0b72ea7b1b2a` | 45/45 independent D/I source-fact **read-only** response byte parity |
| v0.19 one-shot native Docker test | `5a49f85e74398269ad5a094db9ec362fe9ed4658a89028a68b3c08452059075e` | One repeated **developer-authored** original `test_15` in real Linux Docker, 14/14 denial probes, 1.0 pinned author score |

Source task ID, public question SHA, original IFC SHA, original schema, task category/CRUD, original IfcProduct count, missing typed XML object count, paired native equality and author-score status are checked across the frozen reports. Any duplicate/missing task, changed hash, inconsistent category, unsupported previous status, fabricated paid model result, made-up scorer pass, or changed denominator fails closed.

## 2. Real all45 scope — preserve unknown rather than manufacturing results

| Distinct question | Observed original public task evidence |
|---|---|
| Original task denominator | **45/45** (15 create + 15 update + 15 delete; 15 basic + 15 geometry + 15 topological) |
| Original IFC schema by task | 42 IFC4X3, 2 IFC2X3, 1 IFC4 |
| One common read-only source fact interface, exact D/I scripted response bytes | **45/45** |
| Original IFC `IfcProduct` identities not fully represented in the safe writable typed XML | **45/45** |
| Original *complete native* source information equivalence proved | **0/45** |
| Original *complete native write capability* equivalence proved | **0/45** |
| Both **developer-authored** D0/I0 output IFCs byte-identical on original source | **5/45** |
| Both sides callable by **original author scorer** | **3/45** |
| Native-paired but original author grader cannot score due original missing-source references | **2/45** |
| Other original same-protocol native edit/scorer pairs | **40/45 NOT EVALUATED** |
| Existing original source **developer-only** sealed Docker native/author scorer witness | **1 repeated original task**, `test_15` |
| Actual matched LLM calls / new approved paid runs | **0 / $0** |

Exactly five historical developer native pairs:

- `geometry_test_18`, `geometry_test_19`: native D0/I0 byte-identical Windows deletion, but original grader target references absent from actual public source IFC, so **no valid original author numerical score**. Do **not** count as LLM failure or patch the grader.
- `test_15`: original Column −3m Y, native D0/I0 identical, original author both **1.0**. The v0.19 single sealed Docker test repeats this **same** case; does not increase five matched tasks to six.
- `test_16`: original Column delete, native D0/I0 identical, original author both **0.5** despite an independent stricter native oracle passing. Preserve the scorer/native oracle disagreement.
- `topological_test_15`: original Slab-on-Slab move, native D0/I0 identical and original author callable (frozen v0.17). It was deliberately selected from previously observed developer results, **not** a blinded held-out trial.

The 40 other tasks have **unknown paired edit feasibility and unknown author-scoreability under this exact original-source protocol**; this is neither proof they are impossible nor an evaluated success/failure. Original D-only prior scores or read-only native projection do not upgrade a row to paired native capability.

The original v0.17 observation that native source contains more products than the partial writable XML applies to **all 45 tasks**. It does **not by itself** show those omitted products matter to each specific edit, so every row explicitly records task-relevance of omissions as **NOT ESTABLISHED**. Conversely, no one may claim full source-information equality just because a common limited fact packet is byte-identical.

## 3. Implementation

`tools/bibimbap_v020_original45_capability_gate.py`:
- Reads five **exact frozen SHA-256 reports** and compares every one of the 45 public task rows across four historical all45 matrices.
- Checks 15/15/15 CRUD, 15/15/15 category, 42/2/1 task IFC schema, original task source/question hashes and native IFC product census.
- Conservatively reports separate fields for original typed/native source info, common source read receipts, true paired original native output, callable original author scorer, complete backend native write capability, and real LLM score.
- Requires source-only original author-status exact 3/2/40 and native D0/I0 equivalence exact 5/40; any accidental status promotion or data drift fails closed.
- Produces deterministic `reports/bibimbap_v020_original45_capability_and_terminal_gate_20261115.json`, one row per original public task. **No original IFC bytes, hidden scorer target GUID inventory, model code or new dataset are committed**.

`tools/bibimbap_v020_terminal_submission_broker.py`:
- A **purely offline state machine/test double**, not an executing provider client, Docker service, model plugin, network endpoint or production security boundary.
- An untrusted hypothetical model submission is accepted **once**, for a bounded UTF-8 byte string of at most 64 KiB, with invalid/NUL input rejected. **The script is NEVER executed** by this broker, and no IFC parser is imported.
- After a valid submit, the only model-visible response is the exact constant:

```json
{"execution_feedback_available":false,"status":"SEALED_ONE_SHOT_SUBMISSION_RECORDED","tool_continuation_allowed":false}
```

- No other post-submission model action: retries, result polling, follow-up reads or observed tool execution/status are all forbidden. A separately instantiated, trusted **offline host** can store private result metadata, but **that private object MUST NOT be serialized into the same model's context**.
- An offline noninterference audit submits different dummy strings, records **different host-private** scorer/exception outcomes and proves the exact model-visible response bytes remain equal. This is a useful contract test, **not** a proof a real cloud model provider host enforces that behavior. A real model-host terminal broker remains an explicit v0.20 blocker.

## 4. Scientific estimand and launch decision

Two plausible studies must be labeled differently:

**Descriptive system comparison.** Hold model, question, public source, time, sampling and calls constant while comparing the actual *systems*, including XML's partial edit view versus Python's native source code. This is meaningful but is **not a pure representation causal effect**; document unmatched information and operations explicitly and count all 45 original tasks.

**Causal representation comparison.** Requires the two arms to receive equivalent **task-relevant original source information**, equivalent **native IFC write capabilities**, fair iterative vs one-shot feedback policies, independently verified model-host sequestration, same graded outputs and auditability. The currently shared read-only packet and small original IFC Docker demonstration do **not** satisfy these conditions.

**Current decision: all actual LLM trials BLOCKED.** Code and report expose a false `any_paid_or_unpaid_real_LLM_launch_permitted` flag, false `causal_XML_vs_Python_pure_representation_performance_claim_permitted` flag and an enumerated original evidence blocker list. No provider/token/model/budget approved and no real model transport included.

Next ordered work:
1. Implement **real host-side terminal broker isolation and test its actual model-execution lifecycle**, not merely this offline state machine. Do not let a model import host-private scorer/native IFC or run arbitrary Python on Windows. Independently review the Linux Docker sandbox image/source-to-image proof and unknown-code isolation.
2. Audit original 45 cases for **task-relevant native IFC facts and actual write features**. Separate true unsupported operations from untested cases, with a prior and non-score-optimizing frozen rule.
3. Retain original author scorer abnormalities and missing source references; seek original author clarification or published correction without editing the original scoring software in place.
4. Only after scientific preregistration, explicit requested provider/model and USD cap approval, run real matched LLM calls. Preserve full 45 intention-to-test count and per-task provenance, never cherry-pick already successful developer examples into blind performance claims.

## 5. Reproduction and safeguards

No Docker, network, model calls, original dataset checkout, provider credentials or IfcOpenShell installation are necessary for this v0.20 **read-only frozen-report** audit.

```powershell
$base = 'D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue154-original45-capability-gate')
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

& $py -m unittest tests.test_bibimbap_v020_capability_and_terminal -v

# Never overwrite previously frozen reports; choose a new filename.
& $py -m tools.bibimbap_v020_original45_capability_gate `
  --root . `
  --output 'results/NEW_UNIQUE_v020_45task_capability_gate.json'
```

**New v0.20 verification**: 20/20 isolated unit/negative tests PASS, 0 failures, 0 errors, 0 skips in 0.121 s, Windows host Python 3; includes SHA-tamper, scorer fabrication, missing/duplicate task IDs, source/question mismatch, category/native count drift, forbidden model retries/result polls and no code execution. New report SHA-256: `1aa218a0883186e6df1e7e7d895670fb9e012ef0229799b14881a87473f762be`.

**Live v0.19 replay limitation on the current Windows research host (November 15, 2026 KST):** the isolated two-module 31-test run (`tests.test_bibimbap_v019_sealed_original_docker` + `tests.test_bibimbap_v020_capability_and_terminal`) finished with **one error**, specifically the unchanged v0.19 Docker image-inspection subprocess timing out after 12 seconds against `npipe:////./pipe/dockerDesktopLinuxEngine`. This is a **current Docker Desktop runtime/daemon availability blocker**, NOT a successful v0.19 replay; its previous live v0.19 frozen report remains historical evidence only. No Docker service was restarted or changed, no original source mutated and the standalone v0.20 20/20 offline tests remain passing. The long 11-module regression was also not green because it included the same unavailable runtime; diagnose/revalidate the engine separately before any actual Docker-dependent model research.

Full legacy repository discovery had historical errors; this checkpoint claims only its *actually run* selected tests and any separately observed multi-version regression, not full-suite pass. Previous frozen sources and reports stay immutable; submit new v0.20 files on their own stacked Draft PR, not main.
