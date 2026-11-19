# v0.66 / Issue #247 — frozen BIM-Edit source-only task workspace staging

**2026-11-19 · offline implementation only · not preregistration, not an OS sandbox, not a model experiment.**

## Why

The actual original BIM-Edit 36-task pilot has 25 distinct input paths; SHA256 and publisher object identity were verified for 20 input files covering 30 tasks. Six task inputs are still unavailable. Critically, 12 of these 25 input paths are *also* ground-truth paths in other published tasks (22 of the 36 selected tasks use such inputs). Therefore a shared dataset mount, raw full task record, or workspace reused across tasks can expose another task's reference assets and contaminate the study.

The previous `src/security/agent_boundary.py` FileAccessPolicy restricts *tool operations*, **not** arbitrary OS filesystem access. Do not treat it as process isolation.

## Implemented in the existing single repository

`src/data/pilot_workspace.py` is a **frozen-pilot-aware offline input preparation adapter**, not an additional agent/harness. It:

- Checks byte-hash-pinned 324 task records, existing 36-task pilot, **25-source/30-available frozen identity report**, original publisher metadata and recorded per-source SHA256.
- Preserves **all 36 task rows** and reports six `BLOCKED_ORIGINAL_INPUT_ABSENT` statuses instead of dropping them or changing the sample. All 36 public task payloads pass the existing strict model-field sanitizer.
- Allows only `D_FULL`, `D_MANAGED`, `I_NATIVE` as *staging labels* (not a registered arm execution protocol). All three get the identical original input IFC bytes and identical sanitized instruction, with a separate fresh task–arm workspace.
- Copies only the chosen public **source input** into `input.ifc` and writes only `task.json` (fields `task_id`, `instruction`, `input_file`). It never copies neighboring source models, the original complete JSONL, private target metadata, any task's reference IFC by *reference role*, or a scorer.
- Rejects a different task, a changed original file, mismatched published Git/LFS hash, stale frozen SHA256, unsafe task instruction, symlink escape, repository-local or ancestor scratch directory, existing destination, unsupported arm, and source size above 50 MB. Source and destination SHA256 must agree.
- Never starts a model, executes generated Python, invokes an LLM API, downloads IFC files, touches the original ground-truth/scorer, or makes a claim that an OS/container isolation mechanism was established. On copy failure it removes its own partial files.
- Does not update the readiness gate's `rights_checked=false`, missing IFC status, official scorer parity, or preregistration conditions. Both staging preflight and staged record explicitly say **model launch disabled and OS sandbox unproven**.

There is a subtle but important truth: some *input* IFC files are also referenced as a *different task's* GT in the published metadata. This adapter does not examine GT roles or private results; it uses the original file solely as the selected task's legitimate input. Reusing a building across other tasks may still be a training/evaluation contamination risk. Separate task filesystems and building-lineage-aware sampling remain mandatory.

## Verified with actual pinned data, no provider

- Preflight: **36 original tasks, 30 original source inputs locally staged-capable, 6 explicitly blocked**.
- A real, already-cached original IFC input was staged separately for D_FULL, D_MANAGED and I_NATIVE. Each task–arm directory contained **exactly two files** (`input.ifc` and `task.json`); all three source SHA256 hashes and sanitized task payloads were identical. Temporary directories were deleted after the smoke test.
- A second positive case uses a selected input that is classified as another task's reference asset by *path metadata*, and verifies no other reference path, scorer or target appears in the agent payload.
- Synthetic negative cases verify modified source, publisher identity mismatch, stale frozen digest, bad URL-like instruction, bad input path, invalid arm, recycled workspace, scratch traversal and missing input denial.
- `tests/test_pilot_workspace.py`: new deterministic and actual-cached-source tests (run without paid APIs, answer access or geometry parsing).
- No source IFC or GT asset added to Git; only this data adapter, tests and research note.

## Replay

From the single original Windows `bim-markup-bench` checkout:

```powershell
.\.venv\Scripts\python.exe -m src.data.pilot_workspace --check
.\.venv\Scripts\python.exe -m src.data.pilot_workspace --smoke-stage
.\.venv\Scripts\python.exe -m unittest -q tests.test_pilot_workspace
```

These commands do **not** start a real LLM trial. `--smoke-stage` copies only one locally available selected public input to disposable task-arm temp folders and immediately removes the folders.

## Hard launch blocker (must remain)

**Staging a directory is NOT isolation of an untrusted Python process.** Before enabling I_NATIVE, the owner must ensure a separate externally approved container/VM with actual filesystem mount isolation, no source dataset/GT/host access outside the mounted task directory, no network or unauthorized process access, validated task outputs, and a reviewer-controlled scorer outside the agent sandbox. The D arms must receive a matched information budget and trusted compiler that is not callable as a BIM authoring tool by the LLM.

Equally mandatory: independent per-original-IFC rights and provider transfer/retention review, true unseen/source-family attestation, all five absent inputs or explicit six-task ITT failure accounting, official-score provenance if comparing to published scores, an approved frozen study budget/model/tool policy and prospective assessor separation. Do NOT change `main` or merge this Draft PR merely because staging tests pass.


## Windows preflight compatibility correction

The broader pilot regression uncovered a pre-existing Windows cp949 locale failure in `tools/pilot_preflight.py`: `protocol.read_text()` was decoding the existing UTF-8 draft YAML without an explicit encoding. The test's independent `DRAFT.read_text()` had the same flaw. Both are now read explicitly with `encoding="utf-8"`; no data, run policy, draft contents, model budget, frozen manifest or scoring rule was modified. Its CLI continues to exit 2 intentionally because the actual scientific release is blocked. The full existing preflight suite was rerun to distinguish successful *candidate integrity* from blocked live study approval.
