# G0 #3 — Frozen BIM-Edit pilot IFC data/provenance/rights checkpoint

**Date:** 2026-11-10, connected Windows 11. No paid API or bulk data download.

**Decision: BLOCKED_PER_MODEL_RIGHTS_AND_MISSING_IFC_CONTENT.**

This is an offline read-only provenance triage, NOT an official BIM-Edit
score, license grant, author endorsement, full 324 benchmark audit, or proof
that the public dataset license applies to each underlying building model.

## Observed evidence (unchanged fixed tasks)

The original 36 task IDs and exact public task revision remain intact.
The previous G0 source/reference audit is pinned by SHA-256. This new audit
independently rechecks its 30 previously verified task input/reference pairs
against the exact remote Git blob/LFS bytes and reads only the bounded STEP
HEADER of each distinct local IFC.

| Evidence | Actual status |
| --- | --- |
| Frozen task IDs | 36 (unchanged) |
| Source/reference task pairs reverified | 30 |
| Missing pairs still blocked | 6 |
| Unique locally verified IFC assets | 42 files / 87,353,128 bytes |
| Unique missing IFC assets | 10 files / 1,476,908,702 bytes |
| IFC STEP HEADER syntactically recognizable | 42/42 |
| Literal license/copyright marker in IFC HEADER | 0/42 |
| Independently verified per-model legal permission | 0 |
| Official scored benchmark tasks and LLM model calls | 0 and 0 |

The six missing tasks remain in the original sample. Ten missing files do
not imply twelve distinct assets because multiple tasks can reference the
same files.

The bounded HEADER scan looked for literal forms of license, licence,
copyright, Creative Commons and CC-BY. Finding no strings does NOT establish
absence of licensing rights; permission may be held in separate project
contracts, repository documents or contributor agreements. Conversely, a
literal license label in a HEADER would not establish the copyright holder's
permission. The pre-existing rights ledger therefore remains unresolved,
with rights_checked false and redistribution_permitted false. These flags
mean NOT VERIFIED, not an assertion of copyright violation.

## Public source cross-check

- Official model corpus (dataset-level CC-BY 4.0 tag, 4.31 GB catalog):
  https://huggingface.co/datasets/BIM-Edit/BIM-Edit
  Pinned model revision:
  0ae510bd21865def4e2c6145c1244f01a1e3bcb9
- Official task dataset (324 records, operations and scene strata):
  https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks
  Pinned task revision:
  2dc6462bfab145ddf81b43e9954322855b8443dc
- Independent ONESTRUCTION methodology:
  https://ai.onestruction.com/leaderboard/en/methodology/
  That third party states that it independently reimplemented the evaluator
  because the original executable scorer was not public. This is NOT proof
  that code cannot be made available privately or in a subsequent release.
- Prior local author-runs provenance record:
  reports/g0_official_bim_edit_public_release_20261110.json

No task inclusion, scoring formula, benchmark source revision, or protocol
setting was changed as a result of these public observations.

## Implementation and confidentiality

- src/data/pilot_ifc_rights.py checks five existing trusted file digests:
  original task JSONL, fixed candidate manifest, remote IFC metadata tree,
  prior asset-content audit and rights ledger. These must all match the
  original reviewed bytes. Then each local IFC is verified against its pinned
  remote Git object or LFS digest before bounded HEADER inspection.
- Original and reference IFC bytes are accessed only in this trusted G0
  audit; they are never mounted in a tested LLM's workspace. No task
  target/GUID/evaluation field or source path is exposed to an authoring arm.
- The saved report includes public task IDs, category-level statuses,
  aggregate files/bytes, HEADER hint counts and explicit blocked flags.
  It contains no IFC HEADER author/organization text, raw IFC bytes, source
  or GT paths, native GUIDs, prompts, evaluator internals or solutions.
- Malformed, truncated or linked IFCs; content/hash mismatches; forged rights
  promotion; stale prior audit snapshots; missing remote file metadata and
  an altered frozen task population fail closed.
- Existing dataset, GT, manifests, license ledger, scorer, Xim and product
  repositories are not modified.

## Reproduction on the connected Windows PC

Run within the bim-markup-bench repository:

    $env:PYTHONUTF8 = "1"
    .\.venv\Scripts\python.exe -m unittest tests.test_pilot_ifc_rights -v
    .\.venv\Scripts\python.exe -m tools.audit_pilot_ifc_rights --output-json reports/g0_pilot_ifc_rights_20261110.json

Six new tests include genuine pinned source/reference checks, positive and
negative HEADER fixtures, outdated prior report/rights SHA rejection and
a forged license-string check. The CLI returns exit 2 **intentionally**:
G0 remains blocked, even if all 30 prior content records are reproduced.
The CLI refuses to overwrite existing evidence; rerun with a fresh output
path. No network, paid inference or new download occurs.

## Independent decisions needed before G0 release

1. Obtain model/file-level provenance and permission from BIM-Edit's
   maintainers for source and derived GT IFCs: named rights holder,
   license grant scope, research/derivative storage and redistribution,
   and an auditable model-to-notice mapping. Store this in a new reviewed
   ledger revision, not by silently changing the frozen source-rights file.
2. Obtain a storage/download budget and rights approval for the remaining
   ten distinct large IFC assets (~1.48 GB) before attempting full fixed
   pilot audit; keep all 36 preselected task IDs unchanged.
3. Obtain the authors' official evaluator commit, entrypoint and license,
   or explicitly preregister a differently named independent scorer
   without pretending numerical comparability to published scores.
4. Keep the paid G3 pilot and final research conclusions blocked pending
   matched D/I execution security, full task oracles, scorer validity and
   per-model rights review.

This document is an engineering evidence record, not legal advice.
