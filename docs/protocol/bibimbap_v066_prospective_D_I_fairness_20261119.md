# v0.66 / Issue #247 — Prospective D/I interface, feedback and byte parity audit

**Status: PARTIAL PROSPECTIVE DESIGN, NOT preregistered or activated model comparison.** This is an additive offline audit on already developer-exposed sources; no production BIXML/Xim change, original IFC upload, private GT/author grader read, model/API execution or original report rewrite.

New reproducible evidence:
- Source-independent proposed tool contracts and budget ledger: tools/bibimbap_v066_prospective_fairness_contract.py
- Actual local source/control size audit: tools/audit_bibimbap_v066_prospective_fairness.py
- 45 negative/positive tests: tests/test_bibimbap_v066_prospective_fairness.py
- Frozen canonical report: reports/bibimbap_v066_prospective_D_I_fairness_20261119.json
- SHA-256: 39925fa8723b276f4cf44d115db4999f5691437c9e32922370c1d72ad2bd50ee

## Separate scientific questions that are not interchangeable

**System-level workflow comparison** (future, NOT authorized): compare D_FULL complete source XML plus trusted compiler, D_MANAGED complete managed XML plus trusted source rehydration/compiler, and I_NATIVE Python/IfcOpenShell executed against a cloned IFC in Linux Docker. This comparison includes real interface and tooling effects; it would not identify a representation-only mechanism.

**Representation-only causal claim** (BLOCKED): would require equivalent input data, editing capability, tooling affordances, environment and feedback. The current I runtime can inspect and modify the full original native IFC using general code. D only has a source projection with an opaque IFC pass-through and bounded operation support (hosted Door create IFC2X3/IFC4X3 and Window move/delete IFC4X3). Even if the source-only read payload is exactly equal, the information and operation affordances are not. Equal tool-call limits do not cure this confounding.

**Document size/component analysis** (currently supported): compare the size of developer-written source-anchored XML and code controls without inferring agent performance, actual token costs or vendor billing.

## Proposed three-arm read and action interface — not deployed

All three arms would receive the identical initial read response containing BOTH source-only FULL initial declarative XML and source-only MANAGED initial XML, original source SHA and native schema. The D_MANAGED edit mode must not receive privileged exclusive source information that is withheld from I or D_FULL.

| Arm | Proposed tools | Submitted artifact |
|---|---|---|
| D_FULL | read_source_state, submit_full_final_state | Complete FULL declarative XML replacing all explicitly managed final physical state, no operation/command nodes |
| D_MANAGED | read_source_state, submit_managed_final_state | Complete MANAGED declarative XML, linked to original FULL source SHA, no operation/command nodes |
| I_NATIVE | read_source_state, execute_ifc_python | General Python/IfcOpenShell code run against a fresh native original IFC clone inside pinned local Linux Docker, with commit() |

Proposed initial read information matches **only** the source-only tool response. I can still introspect native IFC through Python; D cannot. These are *static proposed JSON tool schemas*; no production/agent session is activated in this checkpoint.

| Regime | Source read | Candidate submissions | Max total calls | Model feedback before generation ends |
|---|---:|---:|---:|---|
| Primary one-shot | Exactly 1 | Exactly 1 | 2 | None from native runtime or author scorer |
| Secondary feedback | Exactly 1 | At most 24 | 25 | Common coarse native-engine class only |

Feedback classes: admitted_native_scope, invalid_submission, unsupported_source, native_execution_failure, native_scope_rejected, engine_timeout. No raw Python stdout, traceback, original author grader/task score, private target, coordinate hint or source-specific error text goes to the model under the proposal. A native-engine admission means an edit is structurally allowed, **NOT that it achieves a requested original benchmark goal**. Models would see no runtime result in the one-shot regime until finalized. Attempts count both admitted and rejected submissions. No read-after-edit or extra reads. Two regimes must not be pooled.

The offline ledger tests those budgets with **synthetic events only**; equal actual provider reasoning settings, timeouts, token allocations and feedback implementations are not tested and remain unapproved.

## Actual UTF-8 measurements on 4 developer-exposed source SHA clusters

Only these pre-inspected original IFC sources were opened read-only locally: geometry_test_03 (IFC2X3 hosted Door create); topological_test_05 (IFC4X3 hosted Door create); geometry_test_13 and geometry_test_19 (IFC4X3 Window move/delete). The two Window operations share one IFC per source, giving six source-operation rows but **only four independent IFC source clusters**.

| Source / operation | Same proposed initial read response (FULL+MANAGED+metadata) | D_FULL submitted | D_MANAGED submitted | I_NATIVE Python submitted |
|---|---:|---:|---:|---:|
| Hosted Door create, IFC2X3 | 2,913 B | 2,287 B | 1,054 B | 2,507 B |
| Hosted Door create, IFC4X3 | 4,716 B | 3,733 B | 1,261 B | 2,347 B |
| Window source A move | 8,984 B | 6,112 B | 2,166 B | 1,231 B |
| Window source A delete | 8,984 B | 6,117 B | 2,171 B | 847 B |
| Window source B move | 13,818 B | 10,020 B | 2,778 B | 1,231 B |
| Window source B delete | 13,818 B | 10,022 B | 2,780 B | 847 B |

Canonical proposed tool schema sizes: D_FULL 916 B, D_MANAGED 854 B, I_NATIVE 990 B. Tool argument JSON escaping/overhead is separately measured in the frozen report. This is exact UTF-8 data size, **not** actual LLM tokenizer output or provider costs.

Two transparent **non-tokenizer, non-billing proxies** appear solely for qualitative scale: ceiling(UTF8 bytes / 4) and ceiling(Unicode codepoints / 4). They cannot be used as vendor tokens, cached/reasoning token counts, equalized context budgets or dollar costs. Actual billed input/output/cached/reasoning tokens NULL, tokenizer model NULL, price snapshot NULL, approved USD limit NULL, model snapshot NULL, model calls ZERO, new API cost USD 0. Compact D_MANAGED document size alone does not establish overall system efficiency.

## Prospective paired/cluster ITT guardrails — still NOT pre-registered

1. **Sampling unit:** original source IFC SHA256; previous 45 original public BIBIMBAP edits belong to 31 original IFC clusters, with 15 public basic task rows sharing one source. Preserve source/task pairing, stratify by family/operation and avoid pretending repeated tasks are independent source samples.
2. **ITT:** explicitly report all selected tasks per arm, including unsupported and engine failures, under a later prospectively fixed sample list. Report common-supported subgroup separately and predeclare its membership before observing outcomes.
3. **Planned contrasts:** D_FULL vs I_NATIVE, D_MANAGED vs I_NATIVE, plus D_FULL vs D_MANAGED component ablation. Pair same original/source/task/model and compute cluster-level uncertainty; do not fit a causal representation-only model until capability confounding is removed.
4. **Separate regimes:** no pooling one-shot versus iterative trials. Full model snapshot, prompt, decoding params, source-visible tool configuration, timeouts, paid cap, output token ceiling, task sample IDs, randomization seed, cluster bootstrap details and repeated-sample counts remain NULL or not selected. Final registration must precede genuine model trial or score lookups.
5. **Independent blindness:** ZERO independently certified original unseen IFC source clusters; other previously catalogued but unverified ones must not be relabeled as blind. New independently verified source provenance needed.
6. **Per-file rights:** original author repository code license, individual source IFC rights, creator/attribution, provider transfer/retention and the pinned author-repository-vs-official-EC3-paper scorer revision are all unverified. Dataset-card cc-by-4.0 label alone is insufficient for underlying individual IFC rights. The unconditional no-provider gate remains BLOCKED.
7. **No unauthorized communications:** no owner-rights emails/Slack messages, paid model calls or external IFC transfers were performed.

## Read-only published benchmark and rights provenance check (2026-11-19)

The official EC³ conference publication landing page (https://ec-3.org/publication/ec32026_271/ ; DOI 10.35490/EC3.2026.271) describes **100 curated CRUD tasks** and states a **best baseline of 50.2%**. That is the published paper's overview, **not** a score or denominator for the 45 original public edit-task subset in this worktree. Its landing-page abstract is not evidence that the pinned original author-repository scorer checkout matches the paper's exact evaluation revision. It also does not establish creator/rights-holder provenance or provider-transfer permission for each individual original IFC. The historical local dataset-card metadata says cc-by-4.0; this checkpoint did not obtain independent per-file title/licensing confirmation, and the Hugging Face card could not be verified live by the browsing source. Therefore all 31/31 original IFC rights remain BLOCKED and author/paper scorer parity remains UNVERIFIED. No external messages, new dataset downloads, tests of previously unseen IFCs or original hidden-grader reads were made for this status check.

## Reproducibility

From the separate research worktree and existing venv:

    $py = 'D:\문서\D__1_Projects\202611\bim-markup-bench\.venv\Scripts\python.exe'
    & $py -m tools.audit_bibimbap_v066_prospective_fairness --check
    & $py -m unittest -q tests.test_bibimbap_v066_prospective_fairness

The --check audit reads 4 known-exposed original source IFCs, pins SHA and frozen prior reports, recomputes exact byte counts for source projections and developer controls (without running any scored trial), checks the pure proposed budget ledger, rejects forged provider approvals, and verifies canonical report bytes. Neither this audit nor the contract imports a provider SDK or exposes a paid-trial launcher. The report freezes **measured byte facts** and **proposed protocol design**, NOT an eligible confirmatory cohort, any actual model execution or completed preregistration.
