# v0.66 / Issue #247 — Historical source-family exposure reconciliation (offline, partial)

**Status:** Evidence-only initial scope under [Issue #247](https://github.com/pikaybh/bim-markup-bench/issues/247), stacked on v0.65 Draft [PR #246](https://github.com/pikaybh/bim-markup-bench/pull/246) exact parent `03c21572dfb09929eaf69c87e9e1bf2841833ac8`. This is NOT independent blind certification, paper-scoring parity, model performance comparison, or provider launch approval. This research repository is separate from BIXML/Xim products.

## Research validity correction

The source-representation intervention is not identified by developer-written D0/I0 oracle agreement. The v0.65 *new* actual provider/model calls count of zero refers only to the **new proposed matched D/I generalization trial**. Earlier, a separately approved and frozen 2026-11-12 **XML-only** GPT-6 Luna cohort made **36 paid API calls** over a 45-task intention-to-test denominator. It yielded **15 author-scored IFC outputs**, **3/45 author full marks**, and **independently verified strict full success UNKNOWN**. It was not a paired Python/IfcOpenShell model-control study. Its original input source-family SHA and task ID are reconciled here without reopening prompts, outputs, or grader code.

Across the same 45 original editing tasks, there are **31 distinct original source IFC SHA families**, including 15 basic tasks on one shared source. The prior v0.43 original-source physical metadata/representation inventory already **programmatically examined all 31 source IFC families**; v0.46 programmatically read 27 families in native paged IFC form. Those prior programs saw original source structures and selected native features. This is evidence of **automated research-pipeline inspection**; it is NOT, by itself, proof that human developers opened a task-specific grader or target answer. Conversely it prevents making a blanket claim that these source models were wholly unexamined.

Of 31 sources, the existing v0.65 registry explicitly documents 10 families as task-specific developer controls and leaves 21 families without an independently completed *human/task-specific inspection* audit. The 21 are **POSSIBLE / NOT CERTIFIED**, not genuine blind holdout, because absence of a case-specific control in v0.65 is not positive evidence of untouched source. The historical one-arm XML-only model cohort exposed XML source projections from **22 unique families** (36 task requests); actual author scoring occurred in **10 families** (15 tasks). Overlap of those sets and the 10 v0.65 developer controls cannot be treated as independent cohorts. The level of historical *model-facing information* also differs: XML projection from 2026-11-12 is not equivalent to raw full IFC.

**Independent truly untouched original-source families certified: 0.** Also, **per-original-IFC external provider transfer and retention rights verified: 0/31**. No claim that all 31 are legally prohibited, only that permissions have not been established. No new original IFC or task-specific grader was opened during this audit.

## Evidence hierarchy (do not collapse these)

1. **Direct frozen observations:** v0.43 31-source native metadata/geometry-census report, v0.46 27-source paged native inspection report, original 2026-11-12 45-task one-arm LLM report (36 requests), v0.65 31-source rights/developer-control ledger.
2. **Independent deterministic reconciliation:** exact four input report SHA-256 values, full 45-task-to-31-source join, original 36 provider requests and 15 scored outputs, all 31 prior automated native-source reads, 27 paged reads, 10 explicitly task-specific developer-controlled, 21 not independently inspected for human/answer exposure.
3. **Not established:** all earlier developer interactive viewing/external provider trace histories, true untouched-source certification, original scorer = published official version, externally transferable rights, matched model/tool/feedback/token constraints, source-neutral move/delete, legal IFC alternative-encoding equivalence, any causal D-vs-I model-performance effect.

The four frozen JSON inputs are checked by SHA-256 before aggregation. Their contents are not rewritten. The new report is machine metadata only: source SHA, public task IDs, schema, Boolean source-processing evidence, and historical request/scorer counts. It excludes original native IFC geometry/GUID/attributes, original task questions, reference IFCs, grading source, output candidates, and provider payloads.

## Reproduce without opening original IFC or scoring source

From the Issue #247 worktree, with Python 3.12:

```powershell
$py = 'D:\문서\D__1_Projects\202611\bim-markup-bench\.venv\Scripts\python.exe'
& $py -m tools.audit_bibimbap_v066_historical_exposure --check
& $py -m unittest -q tests.test_bibimbap_v066_historical_exposure
```

Report: `reports/bibimbap_v066_historical_exposure_reconciliation_20261118.json`

Frozen report SHA-256: `ad4474b04b601986bcad7c2710b2461ff77ac231f3d76278d779b21431d68427`.

The audit code opens exactly four already-committed, SHA-verified reports. It has no provider/network/IFC parser/author-grader dependency, no launch function, no rights unlock. The existing v0.65 unconditional no-launch firewall remains unchanged.

## Residual Issue #247 / prioritized research work

1. Obtain independent human review of historical developer artifacts and genuinely unseen source acquisition/certification criteria. **Automated source inspection alone does not certify/deny manual grader leakage**; source-family classification remains deliberately conservative.
2. Investigate legal IFC2X3/IFC4X3 alternative native edits against exact STEP-ID/five-Root strict acceptance, with negative controls proving no illegal topology/schema damage and semantic-preservation policy that does not privilege D.
3. Extend source-neutral final-state native D + actual isolated Docker I to one bounded move family and one bounded delete family on already developer-exposed sources, without introducing command-opcode XML, per-task target GUIDs or private answer hints.
4. Freeze a prospective *three-intervention* D_FULL, D_MANAGED, I_NATIVE tool/feedback/token plan; preserve arm-input information equivalence and distinguish raw bytes vs actual provider-billed token counts.
5. Verify original IFC per-file provenance and published scorer revision before any model-provider/paid comparison, and obtain explicit owner authorization. **Do not launch or transmit existing original IFCs while blocked.**

This additive evidence-only initial PR deliberately does **not** claim Issue #247 is fully implemented or ready to close.
