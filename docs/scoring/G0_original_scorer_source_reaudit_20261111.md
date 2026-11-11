# G0 Issue #4 — BIM-Edit original executable evaluator provenance re-audit

**Date:** 2026-11-11 KST
**Research gate:** BLOCKED_OFFICIAL_AUTHOR_CODE_ENTRYPOINT_AND_SCORE_PARITY_UNVERIFIED

This is an evidence-based **source/provenance audit**, not a rerun of the
author's benchmark, a simulation of a scorer, or a new D0-vs-I0 comparison.
No benchmark GT IFC, predicted IFC, raw per-task result, model trace or
large third-party corpus was fetched. No external author contact was sent.

## 1. Precise status — what is public, and what is actually runnable

The **original authors' paper** says:
- Appendix F.1: original evaluator/inference pipeline uses Python >=3.13,
  IfcOpenShell 0.8.x, and pinned dependencies in an associated repository.
- Appendix F.5: a code folder accompanies the submission and original
  cached predictions/evaluation reports allow score verification without
  repeating inference; it advises readers to check the "code repository".
- Appendix J: original evaluator and inference harness source is released
  under MIT. **The exact URL, immutable original source commit, license
  file, lockfile, and executable scorer command are not directly given by
  these claims**, and have not been verified/installed in this project.

Primary source:
https://arxiv.org/html/2606.20146v3

The previous G0 public-release audit verified the author-controlled HF
BIM-Edit-runs repository at immutable SHA
9241abc9b3b4efa3906c0bdabcf3321f1558192f.
It contains **1,417 file entries including published per-task and aggregate
reports from seven models**, but **no Python, wheel, package or source archive
was found in that particular repository revision**. This says nothing
definitive about an unlocated submission ZIP or another source repository.

Original author run dataset:
https://huggingface.co/datasets/BIM-Edit/BIM-Edit-runs

Original public tasks:
https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks

A separately maintained, publicly readable construction-AI methodology
page currently says the original evaluator is not public and that it
independently reimplemented it. This corroborates the acquisition
difficulty, but it cannot establish permanent unavailability:
https://ai.onestruction.com/leaderboard/en/methodology/

Targeted GitHub repository searches on 2026-11-11 checked public project
names and code hits associated with author-related accounts or organizations
\`nbharathik\`, \`Tsesterh\`, \`Show2Instruct\`,
\`bartelt-lab\`, as well as the exact task and runs dataset IDs and
arXiv paper number. Public author-adjacent repositories such as
Show2Instruct/ifc-bonsai-mcp and Show2Instruct/bonsai-mcp were found;
**neither could be verified as the executable BIM-Edit scorer.**
Search results were **not exhaustive** across all hosts, repositories,
private submissions or future releases; no absence proof is claimed.

## 2. Newly discovered independent, runnable-source lead — NOT official

Public GitHub repository:
https://github.com/NTUZZH/VeriBIM

Inspected at commit:
\`cd3fe8cb18e8d33f76e73906253cf896cb5d4d3b\`

Source labels: **VeriBIM**, an independent study by Ziheng Zhang and Wei
Zhang (Singapore Institute of Technology), which names its local package
\`ModIFC-Score\`. Its own
[README](https://github.com/NTUZZH/VeriBIM/blob/cd3fe8cb18e8d33f76e73906253cf896cb5d4d3b/code/modifc_score/README.md)
explicitly calls it "a reimplementation of the BIM-Edit benchmark's
three-axis score" and documents the command
\`python -m modifc_score.cli\`.
The repository LICENSE is **Apache-2.0**, distinct from the original
BIM-Edit authors' stated MIT license for their own code. An independent
implementation is permitted to have a different license, but that is
not proof it reproduces the original evaluator or its defaults exactly.

Inspected small source file identities, Git blob SHA-1, at this fixed commit:

| File | Git blob SHA-1 | Provenance use |
| --- | --- | --- |
| \`README.md\` | \`59c8719521ca104449d8a4ba307bbc6ca7fa1836\` | third-party authorship |
| \`LICENSE\` | \`d645695673349e3947e8e5ae42332d0ac3164cd7\` | Apache-2.0 for VeriBIM |
| \`code/modifc_score/README.md\` | \`3baba7221bbf80a3fa2d8f64dbda93910759b0b8\` | independent scorer claims |
| \`code/modifc_score/config.py\` | \`6bb236cbc9542cd011344121062b4bd24481ec2b\` | explicit alternative metric readings |
| \`code/modifc_score/scorer.py\` | \`83b3f3176ba0b239e85193727434a602ae87a130\` | third-party scoring code |
| \`code/modifc_score/cli.py\` | \`68a915116a7323b8ee898dee9864e6638d410088\` | independent documented entry point |

These blob SHA-1s are Git metadata, **not SHA-256 file digests**. They
were read through the GitHub connector at the fixed revision. The
new offline audit itself does NOT fetch, import or execute those files,
install their dependencies or load any source/reference IFC.

### Important unresolved interpretation disagreement

The original paper, §3.2 and Appendix E, defines the topology score
as \`0.3 * node-F1 + 0.7 * edge-F1\` and defines Delete semantic
correctness by whether the intended target is removed.

The **third-party reimplementation's own source** says its default
topology aggregation is **\`mean_rules\`** (unweighted mean of seven
delta components) with \`paper\` as an alternative. For Delete
semantics its default is **\`matcher\`**, while \`removal\` matches the
paper text. The third party asserts that its defaults reproduce
published author run values. **This claim has NOT been independently
validated against original author scorer execution or per-task ground
truth**; the existence of alternative interpretations does not
establish what the missing official executable actually computes.

Exact third-party configuration:
https://github.com/NTUZZH/VeriBIM/blob/cd3fe8cb18e8d33f76e73906253cf896cb5d4d3b/code/modifc_score/config.py

This is a material source of potential non-equivalence. Until the
original scorer can be independently reproduced, do not calibrate
our own evaluation on these alternative defaults in secret or call
them official BIM-Edit results. An independent sensitivity analysis
may later compare both alternatives under an explicitly new protocol.

## 3. New fail-closed provenance gate

Implementation:
- \`src/evaluation/scorer_source_origin.py\`: pins prior G0 report
  SHA-256 and trusted published release inventory; records exact
  GitHub third-party source revision, file blob IDs and alternative
  metric interpretations; refuses any externally submitted
  \`official_evaluator=True\`, fabricated original author ownership
  or modified previously frozen report.
- \`tools/audit_scorer_source_origin.py\`: offline report generator,
  refuses overwrite or symlink destinations. Deliberate **exit code 2**.
- \`tests/test_scorer_source_origin.py\`: tests historical evidence
  integrity, spoofed official source ownership, forged MIT/commit/CLI,
  alternative metric provenance, publication blockers and JSON redaction.

Evidence:
\`reports/g0_official_scorer_origin_review_20261111.json\`

SHA-256:
\`5964631a47162528abbb059f1164cae600050cba2d5eccf69f3cd2fe6034d921\`

To reproduce from connected Windows research repo:

    $env:PYTHONUTF8='1'
    .\.venv\Scripts\python.exe -m unittest tests.test_scorer_source_origin -v
    .\.venv\Scripts\python.exe -m tools.audit_scorer_source_origin --output-json reports/replay-new-g0-provenance.json
    .\.venv\Scripts\python.exe -m unittest discover -s tests -q

The original source isn't downloaded by this audit. To re-check live
GitHub provenance, read six bounded files **at the pinned commit** via
the GitHub API/connector and compare each displayed Git blob SHA-1 with
the report's inventory; never use unpinned \`main\` as a source of
experimental provenance. No large archive, IFC, model output or private
reference should be downloaded merely to refresh this inventory.

## 4. Reproduction blockers and formal acceptance checklist

G0 Issue #4 remains open until the researchers establish each of:
1. A **verifiable original-author-controlled scorer source URL and
   immutable commit or deposited code archive**, not just its paper's
   statement or unrelated repository title.
2. The actual original code distribution's **MIT LICENSE** and
   environment lock with Python/IfcOpenShell versions.
3. A concrete scorer command for externally generated IFC predictions
   against the pinned tasks/IFC reference files, with clean isolation
   of private/reference GT from both model authoring arms.
4. Deterministic sampler seeds, missing/degenerate geometry policy,
   topology edge classes/weighting, Delete special-case semantics and
   exact strict 98% threshold; ambiguity must be resolved from code
   rather than inference from published rounded means.
5. Isolated original-code execution on at least three predeclared
   author example predictions and reference IFCs, with per-axis
   comparisons to the authors' published unrounded data. Only after
   per-file dataset rights are verified and allowed assets are present.
6. The original task population and all historical G1 fixed candidate
   classifications remain unchanged. No scored model calls or G3 trial
   without explicit budget approval and independent G2 environment.

The **latest verified result here is an acquisition blocker**,
not proof that the original scorer does not exist.

## 5. Prepared, UNSENT author inquiry (not an external action)

The original author's publicly listed contact in the paper and their
MCP4IFC project is Bharathi Kannan Nithyanantham at
\`bharathikannan.nithyanantham@uni-rostock.de\`.
The collaborator project's contact page also lists Tobias Sesterhenn
(\`tobias.sesterhenn@tu-clausthal.de\`):
https://show2instruct.github.io/mcp4ifc/

**Subject:** BIM-Edit benchmark — official evaluator source and reproducibility

Dear BIM-Edit authors,

I am conducting an independent research study on declarative XML editing
versus imperative Python/IfcOpenShell editing of IFC models using a
fixed set of public BIM-Edit tasks. I read the paper's Appendices F.5
and J, but have not been able to locate the canonical, executable
evaluator source code mentioned there.

Would you be willing to share its repository URL and pinned release,
MIT LICENSE, dependency lockfile and standalone evaluation command for
scoring externally generated IFC files? We are especially interested
in deterministic sample selection and the exact topology aggregation
and Delete-task semantic rules. We noticed that a third-party
reimplementation documents alternate readings of the published metric,
so we would prefer to rely directly on your original implementation.

For a Door+Opening deletion task in which the input IFC already lacks
explicit horizontal SpaceBoundary relations, can you clarify whether
the evaluator penalizes inherited incomplete Room-boundary shells or
only the changes introduced by the candidate edit?

We would preserve ground-truth isolation, attribution and your asset
rights, and would not claim equivalence until a calibration run passes.

Thank you for making the task definitions and run reports available.

Best regards,
Independent BIM Markup Bench research team

**Status:** DRAFT ONLY; NO EMAIL SENT. Do not invent a positive reply
or treat this request as author confirmation.

## 6. Conclusions

- **Original scorer source recovered and executed:** NO.
- **Independent third-party source with documented CLI found:** YES,
  but source origin and metric semantics differ.
- **Evidence of original official scoring of our IFCs:** NONE.
- **Official tasks scored / model provider calls / paid runs:** 0 / 0 / 0.
- **G0, G1, G2, G3 release:** BLOCKED.

No step above justifies unblocking paid experiments, changing the
fixed 36-task denominator or reclassifying the independent scorer as
the author's executable metric.


### Actual verification on connected Windows 11

- Targeted source-origin tests: **8 tests, all passed**.
- Whole research repository: **630 tests, 609 passed, 21 skipped,
  zero failures** (314.985 seconds).
- Python syntax compilation: passed for the new audit/test/CLI.
- Git staged diff whitespace checks and report privacy guard: passed.
- This audit intentionally preserves the G0 release block even though
  author-published results and separately licensed third-party source
  exist. The replay CLI's expected exit code is **2**.
