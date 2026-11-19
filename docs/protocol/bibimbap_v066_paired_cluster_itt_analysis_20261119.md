# v0.66 / Issue #247 — paired, source-clustered ITT analysis (OFFLINE)

**Status:** Implemented evaluator-side **analysis plumbing on synthetic/developer-exposed records only**. This is **not a new LLM experiment**, not independent blind confirmation, not a BIBIMBAP official paper score, and not authorization to use private task answers or call a model provider.

This intentionally closes a measurable implementation gap from the prospective source-family/cluster-ITT design in [v0.66 D/I fairness protocol](bibimbap_v066_prospective_D_I_fairness_20261119.md), while leaving genuine source rights, independent scoring and owner-approved preregistration **BLOCKED**. Research Issue [#247](https://github.com/pikaybh/bim-markup-bench/issues/247) remains open.

## What this actually implements

- New scorer-side, pure Python module: \`tools/bibimbap_v066_cluster_itt.py\`.
- 24 focused positive/negative tests: \`tests/test_bibimbap_v066_cluster_itt.py\`.
- A strict **preselected cohort ledger**: source IFC SHA256, public non-answer-bearing task ID, paired seed and operation; fixed arm order D_FULL, D_MANAGED, I_NATIVE; one-shot **or** iterative regime, never pooled.
- One explicit attempt-outcome row **per cohort × arm**, even for unsupported, invalid submission, timeout, abort, or not-attempted cases. Missing/duplicate/out-of-cohort rows abort the analysis rather than shrinking the ITT denominator.
- Source SHA256 **cluster** bootstrap, retaining all paired task/seed rows from each selected IFC together on each resample. The reported difference is **task/seed-pair-weighted** strict-pass ITT rate, not equally weighted across distinct IFCs.
- Paired discordant pass counts and operation-level descriptive rates. All three contrasts are reported, with no direction chosen post hoc. If fewer than five distinct original source clusters appear, CI is omitted as too fragile.
- Fails closed on unexpected keys, including target GUIDs, private scorer paths or extra purported rightsholder authorizations in public ledgers. This implementation is evaluator-side and imports **no** LLM runtime, author scorer, IFC source, Docker client or provider API.
- CLI reads two explicit input files, hashes their exact bytes, outputs deterministic JSON, and refuses to overwrite an existing output file.

**The code NEVER turns unverified source declarations into certified blind status.** The only currently admitted cohort label is \`developer_exposed_exploratory\`, because the separately required independent external reviewer/rights chain does not exist. This prevents these generated numbers from being passed off as confirmatory results by the code; it does not independently authenticate the input pass/fail labels themselves.

## Input contracts

\`manifest.json\` (create and SHA-freeze **before** any future trial; no hidden targets, reference IFC paths, private grading scripts or prompt answers):

\`\`\`json
{
  "protocol_id": "dev-pilot-001",
  "cohort_kind": "developer_exposed_exploratory",
  "regime": "one_shot",
  "arms": ["D_FULL", "D_MANAGED", "I_NATIVE"],
  "cohort": [
    {
      "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "task_id": "developer-only-1",
      "seed": 42,
      "operation": "create"
    }
  ]
}
\`\`\`

\`outcomes.json\` must list **exactly three** rows for the example cohort, each containing the same \`source_sha256\`, \`task_id\` and \`seed\`, plus \`arm\`, \`status\`, and boolean \`strict_pass\`. Status is one of \`completed\`, \`unsupported\`, \`invalid\`, \`engine_error\`, \`timeout\`, \`aborted\`, \`not_attempted\`; only a \`completed\` attempt may pass. \`strict_pass\` must be independently computed **after final candidate commit**, never from the model's claim or native admission alone.

An actual multi-source evaluation needs **distinct IFC SHA clusters**, independent source rights and protected hidden reference scoring before any confirmatory interpretation. One source will produce descriptive rates but **no bootstrap interval**.

## Reproduction

From the one existing \`bim-markup-bench\` checkout:

\`\`\`powershell
$py = '.\.venv\Scripts\python.exe'
& $py -m unittest -q tests.test_bibimbap_v066_cluster_itt

# Future evaluator-only use AFTER independent scoring (no provider invocation):
& $py -m tools.bibimbap_v066_cluster_itt --manifest .\manifest.json --outcomes .\outcomes.json --output .\paired_itt_report.json
\`\`\`

The output file is created exclusively. For automated validation, use the function \`analyse_paired_itt(manifest, outcomes, bootstrap_seed=..., bootstrap_resamples=...)\` with explicit protocol-fixed bootstrap seed before scoring. Defaults: 4,000 source-cluster resamples, seed 20261119, percentile 95% interval.

## Scientific and operational nonclaims

1. A task-weighted cluster bootstrap is a **descriptive uncertainty diagnostic**, not an a priori power analysis, a valid per-source unbiased treatment effect for every IFC or a randomization-based causal p-value.
2. The current system-level D vs I comparison differs in tool affordances, source native read ability and compiler capability. A D/I delta does **not** isolate the representational XML-vs-Python causal effect.
3. Strict-pass values are trusted **inputs from an independent evaluator**. The module does not calculate Geometry/Semantics/Topology, establish native IFC legality or authenticate the published paper's grader. Old scorer and synthetic reports remain untouched.
4. The module does not enforce real out-of-band preregistration; file SHA reported **after** input loading is necessary but **not sufficient** proof that a cohort was frozen before observing outcomes. A separate immutable preregistration record, steward and access controls are required.
5. Original BIBIMBAP 31 source families are historically inspected and 0 independently certified untouched; per-original-IFC provider transfer/retention rights 0/31 verified. No original/GNI IFC was downloaded, no private GT opened, no model inference performed in this change.
6. No external approvals were inferred; trial activation stays **blocked**. Do not merge this provisional evidence into an officially scored paper claim.

## Next priority (outside this implementation)

An independent external source steward must select and SHA-freeze a legally usable IFC **before developer inspection**, task/evaluator steward must seal private references, independent reviewer must attest source/task blindness, and rights reviewer must authenticate per-file license/attribution plus provider-specific transfer/retention terms. Publication-backed scorer SHA/version and user-approved model/tool/token/cost preregistration are separate preconditions. See [five-role source-intake handoff](bibimbap_v066_zenodo_source_steward_handoff_20261119.md) and [source provenance](bibimbap_v066_fresh_blind_rights_scorer_chain_20261119.md). The independent reviewer cannot be replaced by a Python \`approved: true\` flag or this agent's self-certification.
