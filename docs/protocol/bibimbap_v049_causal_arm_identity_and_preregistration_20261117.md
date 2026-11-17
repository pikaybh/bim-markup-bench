# v0.49 — Causal arm-identity firewall and prospective matched-study admission

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/213
**Stacked base:** v0.48 Draft PR #212, exact source commit 0da87ff4275582f98b5c4b8381cdb38a03178a40.
**Status:** OFFLINE, BLOCKED for causal inference and paid LLM launch. This is a **prospective protocol candidate, NOT a completed/preregistered experiment**. No task prompt, cohort, scoring criterion or hidden original-ground-truth file was changed.

## Why this gate is necessary

The independent variable in the primary research question is **BIM source representation**. The established repository contract is not merely "the input is serialized as XML"; it is that an LLM directly edits a *declarative document snapshot*. Creation, update and deletion are then inferred from the *before/after state* by a trusted compiler outside the LLM.

Reviewing the exact v0.45 / v0.47 documented model-facing sessions exposes a critical contrast distinction:

| Label | Model-facing edit interface | Correct causal interpretation | Evidence status |
| --- | --- | --- | --- |
| **D-state** (PRIMARY) | Direct edits to declarative XML element/relationship **state**, stable ID + semantic diff, no explicit edit opcodes | Representation-effect arm | Not demonstrated for these exact four original source-native IFCs |
| **I-native** (PRIMARY) | Executed Python/IfcOpenShell IFC-authoring code in independently isolated sandbox | Imperative baseline arm | Not demonstrated in matched original four pilot |
| **T-XML** (AUXILIARY) | Full native source XML plus bounded **NativeEditPlan** with typed operations | Restricted typed interface study; **not D-state** | v0.45/v0.47 native writer + controls |
| **T-Python** (AUXILIARY) | Python AST accepted only as a single whitelisted typed function call; **no Python execution** | Restricted typed interface study; **not I-native** | v0.47 source/authority matched + controls |

**Non-negotiable:** Comparing T-XML with T-Python under fully matched tool authorization may be useful as a bounded syntax/usability *auxiliary study*. Such a result cannot establish whether LLMs perform better at editing declarative BIM source than at writing unrestricted imperative Python/IfcOpenShell programs. The XML NativeEditPlan is effectively a typed command even when wrapped by immutable source XML; embedding it inside source XML does not transform it into a declarative state diff. Conversely, one AST-validated typed Python call is not a normal Python/IfcOpenShell control arm.

The v0.48 independent original task physical-semantic predicate is separate from the original author benchmark grader and hidden GT. A source-derived research physical success is **not** an original benchmark grade, even if it is geometrically plausible and both original IFC result files are byte-identical.

## Frozen empirical denominator and prospective claims

Original public BIBIMBAP edit population remains **45 distinct task rows**, consisting of 15 CREATE / 15 UPDATE / 15 DELETE across **31 unique original input IFC SHA-256 files**. Four original public tasks were selected during engineering development, not by prospective blinded random sampling:

- geometry_test_14 — source-preserving original Slab rectangle update to physical square;
- geometry_test_15 — one Column centre changed to complete four-corner rectangle, multiple legitimate source interpretations;
- topological_test_11 — both original Columns reach and contact the *named* upper original Slab underside;
- topological_test_17 — remove Columns that do not physically contact the *named* lower Slab; native physical/storey witnesses, no explicit Column–Slab IfcRelConnectsElements.

The exact original public question SHA and original source IFC SHA pins are not copied here as unverified literals: they are independently bound in the immutable **v0.47** report and re-emitted by the v0.49 report for each of the four rows. The other 41 tasks are NOT attempts and must not be counted as successes or failures of a four-case pilot. Do not claim the four selected tasks provide a 45-task or a prospectively confirmatory denominator. Historical deterministic developer examples and their source-inferred correct controls are engineering fixtures, **not independent LLM solutions**. No "4/4" from those fixtures is an observed LLM success rate.

The existing study protocol's eventual complete-benchmark ITT denominator remains 45 for this original BIBIMBAP adaptation (or separately frozen 324 for BIM-Edit). Independent attrition and unsupported work must be counted in predeclared full-set analyses. For a real paired analysis, multiple tasks sharing the same IFC should be clustered at original source model level; exact significance/CI calculation, random seeds and multiplicity policy need prospective freeze. Four post-selected cases are exploratory and not a basis for confirmatory p-values.

## Prospective pre-registration checklist BEFORE contacting any model

1. **Declare the estimand and arm identity.** Primary D-state vs I-native is not implemented on this exact four-case matched native path. Auxiliary T-XML vs T-Python restricted is already implemented as developer control, but no LLM outcome exists. Separate experiment IDs, tables and conclusions. Never pool these as one two-arm study.
2. **Freeze eligible tasks/inputs up front.** Keep the original 45/31 immutable hash index and full ITT coverage; for an exploratory four-case trial freeze the four exact source/English-question SHA pins. Exclude or count nothing after viewing model outcomes. Do not inject any v0.48 control value, target, source-derived selected edit GUID/coordinates, private grader signal or scored candidate text into model prompts.
3. **Freeze model conditions.** Record exact provider/API, deployed model snapshot, model alias resolution, temperature/seed/top_p, output cap, tool return formatting, permitted retry strategy, model request/response usage and tokenization method, and context truncation rules. Do not estimate exact tokens from text bytes; request billed counts from the actual provider and preserve raw *sanitized* tool/user roles for accounting.
4. **Ensure balanced source information and tool authority.** The four T surfaces currently have source facts equivalent by a byte-exact XML round trip, but one display is Python-escaped XML and has different bytes/tokens. Even in the auxiliary pilot, compare actual per-task prompt and tool descriptions using the chosen tokenizer or provider input usage; clearly disclose any unavoidable asymmetry. Restrict tool and source-read feedback equivalently or make it a separate controlled ablation. For the primary D/I trial, prove source-relevant native geometry, Psets, relationships, identity and editable authority are available under both surface rules (not necessarily identical encoding).
5. **Freeze action and observation budgets.** Existing auxiliary source matched pilot allows **25 model tool calls/arm/task** and exactly two bounded tools. Define whether compiling/submitting counts, how error feedback is returned, what happens on timeout/out-of-budget, how zero-shot vs feedback cycles are stratified. This 25-call budget alone does not demonstrate equivalent prompt tokens, editing expressiveness or wall time. For genuine I-native restrict OS/filesystem/network and audit no GT or grader mount; do not "upgrade" the v0.47 AST-only call into full Python merely by renaming it.
6. **Prove native outputs and scorer.** Independently reopen actual output IFC and validate type, geometry, native units, relations and non-target preservation. When official author grader is available, validate access rights, exact version, whether its own helper uses hidden answers and the separateness of the grading sandbox; report author grader and independent surrogate scores in different fields. Until provenance is proven, original author score stays NULL. A physically sensible oracle is not automatically identical to the paper's metric.
7. **Preapprove cost/rights.** Require explicit provider/model, billing cap, approved API pricing snapshot, data rights and storage policy. No default inferencing or background scheduling from this protocol.
8. **Immutable trial capture.** For each task, record an opaque trial ID; arm ID; source/question SHA; source mode/version; exact code and model snapshot hashes; sanitized prompt/tool spec hashes; original public inputs; provider return usage/cost; attempt count; tool feedback transcript with GT stripped; output IFC SHA; compiler/runtime/evaluator versions; failure category; candidate grader version; and provenance of any score. Results cannot silently overwrite previous trials.

**Leakage barrier:** Public original prompt and immutable source IFC may be available to model-facing sessions. Prior source-derived *positive* developer edits, expected target geometries inferred by v0.48, target GUIDs selected by controls, evaluator scripts, private GT, source answer snippets and author score traces may be accessed only from a segregated offline evaluator/developer namespace. File path names, stack traces, tool listing and environment variables must not reveal them. Verify this in an actual isolated launch attempt *before* issuing a provider request. This prospective checklist does not claim such isolation has been measured for the next model run.

## Deterministic offline admission: exact evidence

**New executable:** tools/audit_bibimbap_v049_causal_readiness.py

It loads the four prior *frozen* JSON evidence files, validates exact **raw-file SHA-256**, checks 45/31/15+15+15 and the four source/question pins, the restricted Python AST-only semantics, 25-call budget, source-byte parity, independent native oracle and the explicit absence of paid model/author scores. It enforces AGENTS.md and ARCHITECTURE.md declarations. Its output is independent of provider/LLM access and does **not** edit IFCs.

| Frozen checkpoint | Exact SHA-256 |
| --- | --- |
| v0.45 | 7d7518f6c65242f7f00066beeb0229fbb6e42e44d5e841243666ac375105c4b3 |
| v0.46 | beab50998c1f2f984342cf784fe910adc384752a16b8f0eed40623421c38509f |
| v0.47 | cf1d37bf84fe744921989affc8b524e296c4d3b38731601513fd1b9fa95a44aa |
| v0.48 | ca5f365198bff4f92b14031690b30338d3000adfd70b39c2be4471c9a32d7e08 |

**New frozen report:** reports/bibimbap_v049_causal_arm_admission_20261117.json
**Exact SHA-256:** 14a3dd1bd2a00c4fbd7efdafca88c89d00b7c4d247152782d53055b494d54478

Machine-declared result **BLOCKED_CAUSAL_PRIMARY_AND_PAID_TRIAL**. Unknown model tokens, cost and author benchmark scores are JSON null, not zero-valued observations. The engineering parity evidence (8/8 paired restricted developer control native output matches) remains recorded but cannot be relabeled as causal D/I or as real model outcome. Even supplying every boolean approval flag cannot trigger an LLM call through this module: the hard non-executing final gate will refuse.

The report is created exclusively once with --write; --check recreates it in memory and verifies bytes exactly. Rerunning --write on an existing frozen report fails; no old report is overwritten. Positive and negative tests cover false source evidence, tampered report bytes, phantom scorer claims, leaked developer control as model solution, full 45-task authority promotion, arm label forgery, model launch and immutability.

### Reproduce on Windows

Use the existing research virtual environment (no provider, Docker, model download or evaluator needed):

    Set-Location 'D:\문서\D__1_Projects\202611\bim-markup-bench-issue213-causal-firewall'
    $py = 'D:\문서\D__1_Projects\202611\bim-markup-bench\.venv\Scripts\python.exe'
    & $py -m tools.audit_bibimbap_v049_causal_readiness --check
    & $py -m unittest -q tests.test_bibimbap_v049_causal_readiness

This checkpoint improves inference validity and enforces a **no-launch gate**, not original model-score coverage. The next genuinely scientific implementation step is to support **state-diff declarative editing** and **isolated real Python/IfcOpenShell execution** for a prospectively frozen common-supported subset, without reusing the T-arm labels.
