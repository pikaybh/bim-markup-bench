# BIBIMBAP v0.15 — Original IFC4X3 hosted Window D0/I0 source-only parity and scorer provenance

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/144
**Stacked base:** `feat/142-native-hosted-source-delete-v014`, commit `b1e20f18a72b3c62755f8929b3b9adc4d4308575`
**Status:** Research-only, nonblinded developer D0/I0; **NOT** an evaluated LLM paired experiment or a full native BIM source. No Xim/BIXML changes; no main merge.

## Research question preserved

A controlled LLM study must isolate *source representation* as its independent variable. This v0.15 check is deliberately narrower: for two original-public BIBIMBAP hosted-Window deletion instructions, can an **independently authored Python/IfcOpenShell imperative I0** acting on the same pinned original IFC produce the same native IFC end state as the **previously frozen XML-state declarative D0**? The authoring agent/program gets only the original PUBLIC instruction and original source IFC, not the original author scorer target list or the frozen D0 output.

D0 and I0 use IfcOpenShell backend technology; matching outputs are a limited **backend/native feasibility parity** check, not causal evidence about LLM success, model tool-use performance, accuracy, token cost, wall-clock time, or applicability to 45 original tasks. Their *presented representations still differ*: XML is a bounded source-native Window substate; Python receives the original IFC object graph. This parity slice does not eliminate input-information confounding in a future actual LLM experiment.

## Strict sequence and independent trust boundaries

1. Pin original BIBIMBAP author/data revisions via existing immutable Git SHA checks and preserve the original **45-case** denominator. Read only public task instructions and raw original IFCs. Normalize clone to metres (same IFC4X3 engine and units as frozen v0.14); preserve raw millimetre IFC unchanged.
2. `tools/bibimbap_v015_imperative_i0.py` has **no imports from project `tools`, `src`, D0 XML compiler, evaluator, scorer, target metadata or previous reports**. It computes original Wall axis and original Windows by traversing native IfcOpenShell objects and the public wording. On each original native Window, imperative `ifcopenshell.api.root.remove_product` acts on a fresh file clone with preflight dependency constraints. Only surviving shared original relation member ordering/OwnerHistory are restored to source identity. It emits an immutable I0 native IFC candidate and SHA without ever consulting D0.
3. Independent existing `tools/oracle_bibimbap_v14_window_delete.py` reopens the I0 IFC and original native IFC, verifies original Root/STEP inventory and every surviving world native product mesh, unchanged Wall/Openings/voids, selected removal closure and source immutability. This oracle is **outside** both writers, not an original-author score.
4. **Only after** I0 candidate and oracle are fixed, `tools/audit_bibimbap_v015_original_i0_d0.py` loads the frozen v0.14 D0 evidence, reproduces D0 with the original source/public instruction, verifies D0 XML hash and IFC hash are exactly equal to frozen v0.14, and applies the independent IFC oracle again. Source-only I0 and D0 must select exactly the same original Window set and preserve the same unrelated source Roots, relations and native meshes. A mismatch is an error, not a silently dropped comparison case.
5. **Only after both candidates are frozen**, the untouched pinned original author worker runs on the independent I0 result normalized back to public source units. The separate forensic routine parses original author's static Window target declarations, reports only *counts* of source-present and source-absent roots, never emits the original author target GUID values, and runs a clearly labeled **counterfactual scratch candidate** to distinguish two mutually conflicting source evaluator requirements. That scratch is **never** used to score D0/I0 and does not modify their candidates.

## Verified results on the original PUBLIC cases

| Public task | Independently selected Window count | Native I0 source-only oracle | D0 vs I0 native IFC complete SHA | Author score |
|---|---:|---|---|---|
| `geometry_test_18` | 2 | PASS | Byte-identical | **UNSCORABLE** |
| `geometry_test_19` | 2 | PASS | Byte-identical | **UNSCORABLE** |

For both tasks: D0 original native candidate SHA from v0.14 was reproduced exactly; I0 source native IFC output SHA matched D0; all original non-target surviving physical world meshes and originally retained Wall/Openings were independently validated. Hash equality is stronger than necessary for native semantic parity but does **not** make the experiments fully causal or representative.

**Pinned original-author/public-IFC mismatch:** original author `geometry_test_18.py` hard-codes six Window target GUIDs, but four are already absent in its pinned *original public IFC before any editing*. For `geometry_test_19.py`, one of two is absent before editing. Consequently the original author worker returns `AUTHOR_WORKER_FAILED/RuntimeError` for both cases. This is not an LLM failure, a zero score, or an XML success. Original author/data are never modified; no synthetic grade is substituted.

**Second, independent evaluation caveat:** pinned `delete_integrity.py` requires `openings_deleted`, which fails if original host Opening remains. Yet original `non_target_elements_unchanged` accepts only Window target GUIDs and fails if that original Opening (an untargeted `IfcRoot`) is removed. A source-derived Window retained-Opening result and a separate intentionally invalid scratch removal were used to demonstrate each side. This is a local, source-code-grounded discrepancy diagnosis, **not** proof that every conceivable author test is impossible nor a replacement scorer. Diagnosing these conditions took place after authoring both candidates.

**Evidence records:**
- Frozen v0.14 D0 source-only report, unchanged: `reports/bibimbap_v014_original_geometry18_19_native_hosted_window_developer_d0_20261114.json`, SHA-256 `4709b5ae0408cca79a46ce226c57754459a5690ef7c432d84bf4b3c090bcd02e`.
- New `reports/bibimbap_v015_original_hosted_window_i0_d0_parity_20261114.json`, SHA-256 `62888d0ed5b5af80a3ab744ef5fce5d6591b5baa38fbbebea142cc91eaa646c3`.
- New separate read-only `reports/bibimbap_v015_fixture_admission_20261114.json` classifies two known older-worktree fixtures absent from this branch without copying them into Git.
- No hidden GT, original author target GUID values, original IFC bytes, secrets or paid model outputs are committed.

## Tests and scope caveats

**Actual final combined focused rerun:** v0.14 two modules (40 tests) + new v0.15 I0/fixture two modules (13 tests) = **53/53 PASS, 61.524 seconds, zero failures, exit 0**. The independently rerun v0.15 JSON returned byte-identical SHA-256 62888d0ed5b5af80a3ab744ef5fce5d6591b5baa38fbbebea142cc91eaa646c3. These scoped outcomes do not upgrade the unrelated historical repository-wide suite.

Tests cover actual original IFC4X3 native positive outcomes; exact source SHA and original D0 result SHA; no imports from XML/evaluator in the imperative authoring module; wrong/changed public wording, unsupported task, wrong source units, destination overwrite and malformed local fixture fail-closed; independent native oracle for both IFC outputs; postfreeze author score/error/target-absence classification; deterministic audit re-execution.

A **previous** independently run broad `python -m unittest discover -s tests -q` on a v0.14 isolated worktree produced **832 tests, 9 failures, 65 errors, 67 skips (exit 1)**. Among causes were missing ignored `data/tasks.jsonl`, an ignored original-45 historical preflight, several Windows CP949 errors, and older pilot gate behavior. Two known worktree fixtures are available from separate original local worktrees but are not mounted in this clean new branch. **This v0.15 change does NOT repair or rerun the full 832-test historical suite**. The new `inspect_v015_fixture_admission.py` reports only known two-item fixture readiness, safely blocks missing/tampered fixtures, and cannot be treated as evidence of full test suite success. No frozen tests/scorer/fixtures were rewritten to force a green result.

## Offline reproduction

With the pinned original author/data Git checkouts already available locally at `D:\문서\D__1_Projects\202611`, and a Python 3.12 environment using IfcOpenShell 0.8.4.post1, run from the v0.15 worktree:

```powershell
$base='D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue144-independent-i0')
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'

& $py -m unittest tests.test_bibimbap_v015_i0_source_parity tests.test_bibimbap_v015_fixture_admission -v

# Output must be a NEW, gitignored path. Never overwrite frozen evidence.
& $py -m tools.audit_bibimbap_v015_original_i0_d0 `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') `
  --frozen-d0-report 'reports/bibimbap_v014_original_geometry18_19_native_hosted_window_developer_d0_20261114.json' `
  --output 'results/NEW_UNIQUE_v015_i0_d0_audit.json'

& $py -m tools.inspect_v015_fixture_admission `
  --worktree (Get-Location).Path `
  --primary-repo (Join-Path $base 'bim-markup-bench') `
  --issue112-repo (Join-Path $base 'bim-markup-bench-issue112-full45') `
  --output 'results/NEW_UNIQUE_v015_fixture_admission.json'
```

## Required next phase, without scoring contamination

- Do **not** backfill original geometry18/19 with invented target GUIDs or silently fix the historical author data. Request an upstream author/data correction with clear new revision/license and preregister a **separate held-out version** before any corrected formal scorer run.
- Freeze a task-level common D/I information/access schedule and official/independent evaluator distinction. Extend original task semantic parity only where BOTH arms can perform the operation on the true native original IFC. Preserve unsupported cases in all-45 denominator, not subset success rate.
- Establish isolated-worktree fixture admission and separate older pilot-gate error provenance before claiming repo-wide green. Do not expose original author private target labels to model prompts or local task authoring.
- No new paid API calls or mass benchmark runs without new explicit scope and budget approval.
