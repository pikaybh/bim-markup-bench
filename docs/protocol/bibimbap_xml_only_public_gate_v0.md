# BIBIMBAP XML-only public input and launch admissibility, v0 candidate (2026-11-12)

**Issue [#106](https://github.com/pikaybh/bim-markup-bench/issues/106), based on [#102](https://github.com/pikaybh/bim-markup-bench/issues/102).** This is an **offline candidate protocol, not an approved preregistration**. Does not supersede the main D/I causal research protocol or retroactively change P0 GPT-6 Luna outcomes. The owner-approved XML-only pivot is a **noncausal comparison against external published baselines**, not a same-model XML-vs-Python experiment.

## What was actually verified

- Git-pinned original author code: `nbharathik/bibimbap@667004e16bd38fd7d538bcee56191465429fd975`.
- Git-pinned external dataset: `clemenskujat/bibimbap-data@f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`.
- Original public questions CSV SHA-256 `21c07f08c923cdb748255d7960535bab05e2887e4d093d64f87f76ff6d6d100b`.
- Full candidate denominator **45 Create/Update/Delete**, with **55 Read/Retrieve excluded** by task family before any model results.
- Source XML projection possible for 36/45; this is **not** proof that 36 tasks are executable or correctly scorable. The other 9 remain in the full cohort (3 unsupported schema, 4 mapped/Boolean, 2 tilted sweep). No post-hoc exclusions.
- Developer-authored XML positive witnesses for `test_05` and `geometry_test_11`; both previously scored 1.0 by original author test. These are **not model-generated successes**.
- Source-identical negative controls: original author scorer gives nonzero *partial credit* on all 15 Update cases. A raw >0 score cannot mean task completion. See #102 and #104 for details.
- The public-context entrypoint `tools.bibimbap_public_packet` successfully constructs a single in-memory model-facing `test_05` prompt from the original public question, IFC-to-metre normalized XML state projection and this repo's published toy v0 XML language documentation. Its CLI emits **hashes only**, not raw context or evaluator files.

## Firewall implementation / remaining threats

1. The model-facing builder **never takes an author-repo path** or imports its test/evaluator modules. It reads the exact pinned question CSV but extracts **only** `question`, `test` for selecting the task, `CRUD` and `ifc-file` for source verification. The `structured-output` column and unknown fields never enter the payload. The exact pinned original IFC hash and clean dataset commit are verified.
2. For the initial `test_05` pilot, only `PUBLIC TASK`, projected `building.xml`, public toy XML spec and XML-only output instructions appear. No Python execution, grader invocation, reference IFC, target GUIDs from the evaluator, scoring rules, trial answer, host absolute path or official test-code reference is included. The projection is a **partial IFC-backed overlay**; opaque entities remain in the trusted original.
3. This is **application-level payload separation**, not an audited OS/container/provider filesystem isolation of a live model agent. A live inference/feedback loop has **NOT** been exercised. Real provider and permissions setup remains a blocker.
4. The Git-safe report `reports/bibimbap_test05_public_packet_preflight_20261112.json` records hashes, byte-derived provenance and eligibility assertions only. It is NOT a scored provider result.
5. Separate `tools.audit_bibimbap_launch_gate` **may** access the isolated original author grader for an offline evidence audit, but **never generates a model packet**. Its output is a grader-only 45-row candidate ledger, never mounted to the LLM. Future agents must preserve this compartment boundary.

## Metrics and denominator rule (prospective proposal, not frozen)

For each of the original **45** editing tasks, retain distinct fields:

- **Author-native continuous score:** raw sum / count of numeric metrics exactly as the pinned author grader returns; label `original-author-executable` rather than the historical paper's model score.
- **Source-identical baseline:** same original IFC in both scorer inputs, kept as a negative control. Record `author_score - noop_score` as optional *analysis*, never replace original paper rubric.
- **Independent strict full task success:** **UNVERIFIED** until an independent, blinded IFC-state and task-specific predicate (actual requested mutation, correct geometry/relations and preservation) is prospectively implemented and tested on positive and negative controls. Do not use `raw_author_score == 1` as an unqualified substitute, nor `raw_author_score > 0`.
- **Intention-to-test:** all 45 original editing tasks belong in the primary denominator **even when projection fails, compiler edit is unsupported, the XML is invalid, the grader throws, or generation fails**. A separately declared common-supported analysis can be conducted only after technical eligibility is frozen without reference to actual LLM scores.
- **Paper comparison:** do not compare a 45-edit mean directly to an original all-100 CRUD mean (55 are retrieval); if historical operation-level numbers are used, label the source, metric arithmetic and unavoidable provider/version/turn differences. No causal inference.

A *model-generated* 45-task run remains fully blocked until the exact cohort, task-specific independent scorer, model/version/decoding, input/output token budget, number of trials, rights, approximate invoice policy and user-authorized USD cap have been frozen **before inference**.

## Verified offline outputs and exact commands

The two tools are deliberately different:

- `python -m tools.bibimbap_public_packet` prepares only one public prompt (no paid model) and returns a hash summary. **Success exit code 0 means packet preparation only.**
- `python -m tools.audit_bibimbap_launch_gate` audits all 45 candidates and returns **exit code 2 on NOT_READY** even if the ledger is written. This deliberate exit code is an admission block, not a broken test.

Run from the separate Windows worktree `D:\문서\D__1_Projects\202611\bim-markup-bench-issue106-public-gate`, using the already installed Python environment in sibling `bim-markup-bench\.venv`:

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$env:BIBIMBAP_AUTHOR_REPO = Join-Path $base 'bibimbap-author-upstream'
$env:BIBIMBAP_DATASET = Join-Path $base 'bibimbap-author-data'
Set-Location (Join-Path $base 'bim-markup-bench-issue106-public-gate')
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'

& $py -m unittest tests.test_bibimbap_public_gate tests.test_bibimbap_author_integration tests.test_xml_only_readiness -v
# No model calls. Avoid overwriting existing write-once reports; use NEW filenames.
& $py -m tools.bibimbap_public_packet --dataset $env:BIBIMBAP_DATASET
& $py -m tools.audit_bibimbap_launch_gate --author-repo $env:BIBIMBAP_AUTHOR_REPO --dataset $env:BIBIMBAP_DATASET
# Expected launch audit exit code is 2 for NOT_READY.
```

Machine-readable evidence: `reports/bibimbap_test05_public_packet_preflight_20261112.json` and `reports/bibimbap_xml_only_launch_gate_20261112.json`, including exact source and prompt hashes. These are not official BIBIMBAP model scores.

## Next scientific priority

Freeze the first **task-specific independent strict IFC outcome oracle** from the public `test_05` instruction and blind-source evidence, while preserving (not rewriting) original grader metrics. The #104 orientation controls require separating geometry correctness from newly introduced clashes. Then test the output bridge using **offline developer-authored controls** and source state changes. Only after its full adjudication, prompt/answer firewall, per-task cohort and cost contract are audited should a new real LLM call be considered. The previous P0 $1 cap cannot be reused.

**Current live admissibility: NOT_READY, seven blockers, zero BIBIMBAP LLM results, zero additional spending.**
