# v0.53 — Author-repository test calibration, original-four D/I primary arm and offline candidate preregistration

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/221
**Stacked parent:** v0.52 Draft PR #220, exact base SHA a0ef25fad9e86c32661344a45cee0c15a47b675a.

**Status:** OFFLINE and BLOCKED for model trials. This is a prospective *candidate*, NOT a formally registered or completed LLM experiment, an original published-paper score or a finding that one representation is better. No Xim/BIXML product, research main, original source IFC, published author code or prior frozen report was changed.

## 1. Primary causal contrast (and what it is not)

D_STATE: LLM reads full original native IFC XML evidence and directly edits a declarative final-state snapshot under stable IFC GlobalIds. A trusted compiler outside the model computes before/after diff and writes a real native IFC. The model gets no XML edit-operation list, command bus or Python authoring API.

I_NATIVE: LLM reads the *same* source XML evidence and submits real general Python/IfcOpenShell code to a true OS-isolated pinned Linux Docker sandbox, with independent source-native IFC physical and relationship preservation checking. The v0.52 developer-only real Docker controls proved native execution; they are NOT LLM successes.

Previous T_XML_TYPED (XML NativeEditPlan) and T_PYTHON_RESTRICTED_AST (one AST-whitelisted Python-like call, not executing Python) are auxiliary, not primary D or I evidence.

Both primary sessions returned byte-identical initial XML source evidence for each of the four original IFC4X3/mm inputs. The common system and public-question user messages are identical and frozen by SHA. Both use two model-facing tools and 25 total calls. **Their tool action schemas, feedback, authoring length and output capacity are unequal. Byte-equal initial source is NOT equal provider token use, model prior familiarity, error information or expressive authority.** Freeze and measure these separately before claiming causal equivalence.

## 2. Fixed exploratory original BIBIMBAP population

Original editing population: **45 tasks**, 15 CREATE + 15 UPDATE + 15 DELETE, derived from **31 unique original public IFC file hashes**. Current original-source native-capability subset:

- geometry_test_14 — original Slab rectangle dimensions
- geometry_test_15 — moving one of four original Column XY locations
- topological_test_11 — original mapped two-Column shared depth, contacting named upper Slab
- topological_test_17 — removing original Columns not related to named lower Slab

These four were selected after engineering investigation, not by prospectively blinded random sampling. They are **exploratory**; the other 41 original edit task rows have NOT been attempted and cannot be silently excluded or promoted to a 45-case conclusion. Future paired ITT denominator is four source/task pairs; eight arm/task slots for one repetition, with independent fresh original IFC per arm. Trial order is deterministically assigned by first-byte parity of SHA256(frozen public seed + task ID). Planned estimand is descriptive mean of four paired binary-success differences. Only four unique source clusters; do not present confirmatory p-values or generalization to the original 45.

## 3. Original BIBIMBAP author test code exists, executes and has a distinct grading interpretation

Pinned author checkout commit: **667004e16bd38fd7d538bcee56191465429fd975**.

The author Git repository contains an actual test module for each selected original task, with a public-author execute_test(original_ifc, edited_ifc, model_output) signature. The original benchmark.py calls it and computes the arithmetic mean of Boolean metrics. Exact original test source, original benchmark, cache evaluation and shared integrity utility SHA-256 hashes are recorded in the evaluator-only report; no original author test code was copied into this repository. **Author-repository executable test results are distinct from verified equivalence to the published paper's original official scorer version, environment and paper tables. That last equivalence remains UNVERIFIED/NULL.**

In a strictly **separate evaluator-only process**, we generated 8 real D-state and 8 independently authored I-native native IFC candidates from original IFC/source-derived developer controls, with no model code or paid provider. We ran 16 author-repository tests. D and I match in all eight matched developer-control conditions:

| Original task | D-state developer positive / negative | I-native developer positive / negative |
| --- | --- | --- |
| geometry_test_14 | 1.000 / 0.667 | 1.000 / 0.667 |
| geometry_test_15 | 1.000 / 0.667 | 1.000 / 0.667 |
| topological_test_11 | 1.000 / 0.667 | 1.000 / 0.667 |
| topological_test_17 | **0.500 / 0.000** | **0.500 / 0.000** |

These are developer-controlled **source/native IFC** evidence, not 16 trials, 16 actual LLM completions or author-published benchmark results. The separate v0.48 public-source research physical predicate accepted positive edits for all four and rejected negative edits for all four.

### Why the positive Column delete receives an author score of 0.5

- All five originally specified target Columns are absent in the positive native IFC (author object_not_exists=True).
- Original author subchecks for wall connections, spatial containment, openings and aggregation EACH returned True for all five targets (20/20).
- Real IfcOpenShell API native product deletion also cascaded cleanup of original 15 IfcPropertySet Roots, 15 IfcRelDefinesByProperties Roots and 5 IfcRelDefinesByType Roots that were dependent on deleted Columns.
- The author's non_target_elements_unchanged helper compares the survival of every non-target IfcRoot GlobalId. It therefore treats those **35 valid dependent-root cleanups** as non-target losses and assigns integrity_constraint=False. The same failure is observed for D and I.
- Do not alter or mask the author metric. A physically successful native delete can receive 0.5 on the original author's repository test because of the helper's non-target preservation interpretation. This mismatch is a scoring-policy issue, not proof that any one primary representation fails. Published author-run version parity and the correctness of alternate deletion representations remain unverified.

All developer-only target sets, selected edit coordinates, test code and original target GUIDs remain OUTSIDE the model-facing prompt, tools and sandbox. Report only scores/Boolean metrics, native file digests, class counts and immutable public input hashes.

## 4. Rights and evaluation provenance

The README in the pinned original-author checkout references a LICENSE file, but that local pinned checkout contains **no LICENSE file**. This does NOT establish any redistribution rights for original author source, IFC models or published paper scores. No original source code, target IFCs, private answers or original data files are committed here. License/data-use approval is still explicitly required before uploading source IFC evidence to a model provider, distributing results that embed source, or making a public artifact.

This checkpoint proved the author-repository task functions can be executed on engineering candidates. It does NOT independently verify the published paper's final scorer code version or reproduce an official paper table. Report provenance labels must remain distinct: independent-native source safety, independent original public task physical surrogate, original author-repository test metrics, and published-paper equivalence unverified.

## 5. Candidate future D/I study and mandatory no-launch gates

Candidate manifest freezes: exact four public question/source SHA pins, model-facing system/user prompt SHA, initial XML byte count/SHA parity, separate tool schema hash and UTF-8 sizes, original 45/31 denominator, the four task-pair orders, maximum **25** tool calls per arm/task, selected original four source clusters and intended four-task ITT rule.

**Still missing and not defaulted:**
- Actual provider/model endpoint, exact resolved model snapshot, chosen sampling parameters (seed/temperature/top_p), real context truncation and tool feedback policies.
- Same provider *billed* input/output token constraints and receipts for both arms; tool schema and action lengths differ. Equal source bytes do not establish equality.
- Approved endpoint data retention/privacy and source rights, an exact approved total USD cap with hard enforcement, task timeout and retry policy.
- Independent scorer/paper-code provenance verification and a precommitted way to disclose the original delete-integrity mismatch.
- Explicit owner approval and a formally frozen/reviewed experiment registration before observing model outputs.

Every one of these missing entries is kept null or false. The offline admission method refuses even an all-true synthetic approval payload. This module has **NO provider call, payment, LLM execution or official original published paper score path**. Future experiments need a separately approved checkpoint/commit and runtime safeguards; do not silently enable paid calls.

## 6. Immutable evidence and reproduction

**Author-repository forensic executable:** tools/audit_bibimbap_v053_original_author_provenance.py

**Source-native D/I + original author test report:** reports/bibimbap_v053_author_origin_four_original_score_20261118.json

SHA-256: **40742725e59f7b0909f2d1ff061a7d68bcfcf1f35da829c3d15d0624928366e4**

**Offline candidate prompt/arm/source and no-launch gate:** tools/audit_bibimbap_v053_paired_prereg_gate.py

**Candidate manifest:** reports/bibimbap_v053_primary_DI_exploratory_prereg_candidate_20261118.json

SHA-256: **600a951bfb0733a79f09e9db43376526ceaa9e1a66cc3e800e2ca00601862524**

Previous v0.52 frozen live Linux Docker evidence remains unchanged, SHA-256 83aaebf382ddad136ee55ff4e3b54559e6630b64587c4665f447bb12baffcc31.

Offline Windows reproduction with the existing research Python environment and original author checkout:

    python -m tools.audit_bibimbap_v053_original_author_provenance --check
    python -m tools.audit_bibimbap_v053_paired_prereg_gate --check
    python -m unittest -q tests.test_bibimbap_v053_author_scorer_prereg

Author-source --check recreates 16 true source-native IFC developer candidates and reruns original author test metrics before exact bytewise report comparison. Frozen report writes are create-only and never overwrite prior evidence. No paid provider, Docker invocation or model trial is made by these audit commands.
