# BIM-Edit pilot remaining six files: no-download readiness gate (2026-11-09)

**Issue:** #3, also informs #5/#6 rights review · **Status:** BLOCKED_MISSING_MODEL_BYTES_AND_INDIVIDUAL_RIGHTS.

## Frozen data and local availability

- Pilot task sample is fixed at 36 IDs. The source JSONL and IFC model revisions remain unchanged.
- Exactly 30 task pairs have locally hash-verified public input/GT bytes and basic native class/delta audit in `reports/pilot_asset_audit_partial.json`. This is **not 30 successful edits**.
- Six fixed task pairs are missing their source/GT assets; two pairs share the same remote source/reference files.
- **10 unique missing IFC files**, totaling **1,476,908,702 bytes** (decimal, ~1.477 GB). Reference/input file paths and target GUIDs are retained only inside the trusted audit process, not the exported report.
- Smallest missing complete source/GT pair is **94,044,329 bytes**, larger than the existing no-surprise downloader's maximum batch of **50,000,000 bytes**.
- At inspection time Windows D: reported **69,300,072,448 bytes free**. This is a snapshot, not a capacity reservation or a download authorization; the obstacle is the security/budget/rights gate, not an assertion that 1.48GB cannot fit.
- The published BIM-Edit corpus card identifies a dataset-level CC BY 4.0 tag: https://huggingface.co/datasets/BIM-Edit/BIM-Edit. Local `manifests/source_rights.json` explicitly **does not certify rights for each individual third-party model**. No per-IFC redistribution authorizations are present for these 52 candidate assets.
- No re-sampling, dataset rewriting, quota expansion, provider calls, or source/GT download occurred.

## Reproducible offline checks

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_remaining_pilot_gate -v
.\.venv\Scripts\python.exe -m tools.audit_remaining_pilot
```

The test group expects five passes. The CLI **must return exit 2**, status `BLOCKED_MISSING_MODEL_BYTES_AND_INDIVIDUAL_RIGHTS`, and report `download_performed:false`. The tool rereads the pinned task/tree metadata and checks cached file bytes. It rejects changed task IDs, missing metadata, corrupt local hashes and suspicious cache paths. It emits only sanitized task IDs, operations, class, byte counts and aggregate readiness. It never requests a URL or opens IFC geometry, thus has no accidental answer/model leakage.

## What unlocks future work

1. Obtain explicit authorization for planned storage/download budgets and any change to the 50MB safety cap, without modifying frozen sample membership.
2. Audit individual IFC model origins and rights (attribution, permitted use, redistribution status) before redistribution; keep original source and expected output as verified, ignored local data.
3. Download only independently justified pinned files with SHA checks, non-overwrite semantics, and separate trusted grader access. Re-run native delta audit after caching.
4. The *research-scoring gate* remains blocked until independent-vs-official metric parity is calibrated and common-supported D0/I0 tasks are proven. Do not infer LLM performance from cached input/GT integrity.

Related docs: `docs/scoring/independent_vs_paper_gap_20261109.md` may be pending separate PR #62 at the time this branch is reviewed.
