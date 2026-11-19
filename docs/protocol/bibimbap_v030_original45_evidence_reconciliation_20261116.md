# BIBIMBAP v0.30 — original45 evidence reconciliation (prospective, offline)

**Issue:** [#175](https://github.com/pikaybh/bim-markup-bench/issues/175)
**Parent:** [Draft PR #174](https://github.com/pikaybh/bim-markup-bench/pull/174), commit `952d17d6c2596108e368d071eb6552c52e7c05bd`
**Nature:** Secondary read-only evidence synthesis, **not an LLM run, not new IFC mutation, not an amendment to the frozen benchmark protocol or results**.

## Research question retained

The independent variable remains the **LLM-editable source representation**: D-arm edits complete declarative XML state; I-arm writes Python/IfcOpenShell instructions. The outcome of interest is the *actual independently graded BIM edit produced by an LLM*. The historical D0/I0 controls are deterministic developer-authored ceiling tests; even byte-identical outputs do not establish LLM outcome parity or causation.

## Why this additional report is necessary

Frozen [v0.20 capability evidence](../../reports/bibimbap_v020_original45_capability_and_terminal_gate_20261115.json) correctly recorded **5/45** original-public-task native IFC byte-equal D0/I0 developer cases, of which **3/45** were callable with the original author grader and **2/45** exposed original-author reference/source mismatch. Later prospectively scoped independent reports v0.23, v0.24, v0.25, v0.27, v0.28 and v0.29 add six *distinct* original-public-task native D0/I0 byte-equal developer cases and six author-callable pairs, with **no intervening matched D/I LLM trials**.

The correct **current frozen-report reconciliation** is therefore:

| Evidence level | Original 45 cases | Meaning |
| --- | ---: | --- |
| Frozen v0.20 native D0/I0 byte-equal developer cases | 5 | Historical independently reported deterministic parity |
| Additional byte-equal developer cases, v0.23–v0.29 | 6 | Same fixed original 45-task population; newly evidenced slices |
| **Total native byte-equal developer cases** | **11** | **Not LLM performance** |
| Original author-callable developer pairs | **9** | **Not necessarily full scores** |
| Original author reference/source mismatch | 2 | Byte-equal developer cases with blocked original scorer |
| No same-protocol developer native pair yet proven | 34 | **Unknown**, not automatically failure or unsupported |
| Original 45 full IFC information parity proven | **0** | D may omit native products and relationships visible to Python |
| Original 45 full native write-capability parity proven | **0** | Shared packet/selected oracle cannot establish equal tool capabilities |
| Matched D/I real LLM trials in latest protocol | **0** | **No causal performance estimate permissible** |

The six newer author scores for both developer arms are: `test_20`, `test_18`, `test_17`, `test_19` **0.5**, and `test_11`, `test_14` **1.0**. This report does **not** average them into a headline model score. Historical original-author validation, even when callable, has separate metric and source-provenance caveats.

## Inputs and strict integrity barrier

The audit reads **only eight immutable JSON reports** in `reports/`; every byte stream is verified against an embedded SHA-256 before parsing. The original v0.20 capability matrix and v0.22 native-source-role census establish the exact 45-member denominator; six subsequent reports must advance developer and author-callable counts strictly **5→6→7→8→9→10→11** and **3→4→5→6→7→8→9** with no duplicate task, source/question hash mismatch, scoreability mismatch, or implicit eligibility inference.

The generated `reports/bibimbap_v030_original45_evidence_reconciliation_20261116.json` contains only task ID, CRUD/category, high-level evidence classification, score where available, source report filename and honesty gates. No original prompt text, target GlobalId, hidden answers, evaluator code, raw IFC, credentials, or model-generated responses are read or serialized. The script uses only Python's standard library.

This is a **pinned-report audit**, not an independent reproduction of every earlier native IFC edit. It cannot establish that a cited result is substantively correct if the underlying frozen report itself contains an undetected experimental error.

## Reproduce offline, without inference or downloads

From the repository root with Python 3.12+ available:

```powershell
python -m tools.audit_bibimbap_v030_reconcile
python -m tools.audit_bibimbap_v030_reconcile --check reports/bibimbap_v030_original45_evidence_reconciliation_20261116.json
python -m unittest -q tests.test_bibimbap_v030_reconciliation
```

Expected report SHA-256:

`4e14cce8dd0ee0c961d9b632345c559df7551c16fee073a89b7bc12df8a2b509`

The report is versioned and must not be overwritten by regenerating in place; compare with `--check`. `--write` explicitly refuses overwriting an existing output.

## Scientific launch decision and next blockers

**Causal comparison remains BLOCKED.** Before a future matched trial and inference-cost approval, independently certify task-specific D/I source visibility and editable native object/relation capability (or preregister a transparent unequal-capability study as a distinct experimental condition), verify isolated Python worker operation and model-safe feedback, and perform D0/I0 task-specific ceilings and scorer calibration. Keep the original 45-task intention-to-test denominator, unsupported classification, frozen prompts and evaluator identities intact.

The previously observed Windows Docker Desktop daemon HTTP 500 and missing offline IfcOpenShell wheel in a newly generated venv are **environment readiness failures**; neither warrants changing scientific outcomes nor resetting host Docker without authority. A previously installed research venv was used to rerun v0.29 and offline gating tests. No new paid API requests, original-data downloads, Docker reset, Xim/BIXML edits, main push or merge were part of v0.30.

## Validation scope and limitations

Current isolated v0.30 audit tests cover positive exact-row/count validation, deterministic report byte reproducibility, immutable source hash preservation, negative tampered inputs, missing reports, duplicate/reordered cases, partial scores, causal-gate honesty, and confidential input exclusion. Symlink substitution coverage is conditional on Windows symlink privileges and is reported as skipped if unavailable.

The v0.30 report is a **reconciliation of the latest committed frozen evidence**, not a claim that all historical regressions or the entire original repository test suite have been run at this HEAD. D0/I0 native IFC equality, original-author grading and actual model outcome must continue to be reported as distinct evidence tiers.
