# v0.58 — Original 45-task D/I native capability census and source-cluster prospective holdout candidate

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/231

**Stacked base:** v0.57 [Draft PR #230](https://github.com/pikaybh/bim-markup-bench/pull/230), exact commit `661d733b77e801a491e56fee5b362ca59c44c9e7`.

**Research-only; NO trial launch.** This is an OFFLINE prospective *candidate* registry/selection frozen before any LLM-generated outcomes. It is NOT a completed experimental preregistration, funded/provider-authorized run, confirmatory model comparison or the published paper's official benchmark grade. Original input IFCs, original author source/test modules, old reports, research `main` and BIXML/Xim product remain untouched.

## 1. Direct original-source census, not a task catalog guessed from names

The pinned local original author repo `nbharathik/bibimbap` Git `667004e16bd38fd7d538bcee56191465429fd975`, original dataset commit and existing `public_45` original-question/IFC/source-hash preflight were independently reread. Every original source IFC is **actually SHA256-checked and opened via IfcOpenShell** in this checkpoint (one native schema per source hash). Every original author's `data/tests/<task>.py` source exists and is independently SHA256-pinned, **without importing or executing the grader or revealing code, target identifiers or question/answer text in the report**.

| Original public denominator | Direct evidence |
| --- | --- |
| Original editing tasks | **45** — 15 CREATE, 15 UPDATE, 15 DELETE |
| By category | **15 basic, 15 geometry, 15 topological** |
| **Distinct original IFC source SHA clusters** | **31** — 30 singleton clusters and **one shared basic input of 15 task IDs** |
| IFC4X3 source tasks / unique inputs | **42 / 28** |
| IFC2X3 source tasks / unique inputs | **2 / 2** |
| IFC4 source tasks / unique inputs | **1 / 1** |
| Historical earlier toy-XML *read-only input projection* | **36 PROJECTABLE, 9 BLOCKED** |
| **Current original-native D/I edit and source-preservation/oracle coverage** | **4 out of 45**, all **developer controls**, never an LLM-generated result |
| Remaining tasks with current native edit/oracle acceptance **unproven** | **41 out of 45** |

**Crucial:** historical XML *projection/readability* does **not** establish original-source edit/IFC compiler support. Indeed, four previously native-verified tasks include inputs marked BLOCKED by the older toy-geometry projection, because a more specialized actual IFC source/native writer was implemented later. It would be false to report 36/45 D-state editing coverage from that old input-read statistic.

It would also be false to count 15 basic tasks using the same `basic_tasks.ifc` as 15 independent IFC samples; the exact same original source and possible failure mechanisms would be reused. Source-cluster assignment and any prospective uncertainty estimate must respect this shared source.

### Frozen coverage judgment for four genuinely different arm identities

- **D_COMPLETE_XML:** whole source/managed XML final state, v0.55 native authoring + independent physical/schema gate; **four task-specific original native developer controls verified**, other 41 **NOT SUPPORTED by current four-task semantic diff/compiler**.
- **D_MANAGED_FINAL_STATE:** v0.57 compact **entire managed final state** with GUID-by-GUID present flag; four original source-native developer controls verified and **exact same real IFC** as full state, other 41 **NOT SUPPORTED by current four-task managed subset or native compiler**.
- **I_NATIVE:** genuinely arbitrary Python/IfcOpenShell executes in pinned nonroot/no-network Linux Docker, v0.55 independent source/task-specific scope+schema gate. Four original native developer controls verified. For other **41** tasks the **general Python execution capability exists, but task-specific native independent admission has NOT been established**. Do not label these as validated original editing successes or fair paired trials.
- **D_COMPLETE_XML_STREAMED:** v0.56 separate auxiliary transport arm, not silently merged into primary D. Four developer native controls, with different tool schema/call budget/feedback. Remains explicitly separate.

Additionally, the v0.55 source/candidate schema-delta admission is **IFC4X3-scoped**, and original `geometry_test_03`, `geometry_test_04` (IFC2X3) and `geometry_test_05` (IFC4) are structurally out of range regardless of whether generic IfcOpenShell can open their file. Those source formats must receive a newly verified native source/scope/schema policy before fair trials.

None of the current three primary arm interfaces are authorized to run arbitrary original 45-task LLM benchmarking simply because a public author scorer module exists.

## 2. Prospective source-cluster holdout candidate frozen before model results

**Seed:** `BIBIMBAP-v058-public-original-untouched-source-six-strata-holdout-20261118`

**Selection rule — deterministic, source-aware, no scores used:**
1. Identify the **four** source SHA clusters previously exposed to v0.45–v0.57 original-developer controls. Exclude all four from holdout. The four task IDs are `geometry_test_14`, `geometry_test_15`, `topological_test_11`, `topological_test_17`.
2. Partition previously **untouched, single-task** original source SHA clusters by six publicly known strata: geometry/topological × create/update/delete. The 15-task shared basic source cluster is kept **entirely in development**, avoiding leakage and unstable weight in a six-stratum holdout.
3. For each stratum, select the task with the minimum lexicographic `SHA256(seed|HOLDOUT|stratum|original_IFC_SHA256|task_id)`. Tie-break by task ID. Use no original author scores, private target IDs, generated developer answer controls, previous model results or source geometries to select.
4. Freeze future task order with `SHA256(seed|PROSPECTIVE_ORDER|task_id|original_IFC_SHA256)`. Freeze each D-versus-I arm order independently with `SHA256(seed|ARM_ORDER|task_id|D_arm_id|I_NATIVE)` parity.
5. The two **separate comparisons** are `PRIMARY_FULL_D_vs_I` and `ALTERNATIVE_MANAGED_D_vs_I`; a fresh I-native arm run and original source clone are required **for each comparison** (no shared/reused I result across D representations). A third D streamed arm is auxiliary and is not counted within this 24-slot candidate.
6. Exactly **25 model tool calls max per arm-task**, but that is **not** proof of token/cost/error-feedback equivalence.

### Locked six untouched-source original tasks

| Public stratum | Frozen original task | Native input schema |
| --- | --- | --- |
| Geometry · CREATE | `geometry_test_03` | **IFC2X3** |
| Geometry · UPDATE | `geometry_test_13` | IFC4X3 |
| Geometry · DELETE | `geometry_test_19` | IFC4X3 |
| Topological · CREATE | `topological_test_05` | IFC4X3 |
| Topological · UPDATE | `topological_test_12` | IFC4X3 |
| Topological · DELETE | `topological_test_18` | IFC4X3 |

The frozen randomized *candidate* trial order, not an executed run, is:
`topological_test_05` → `topological_test_12` → `topological_test_18` → `geometry_test_19` → `geometry_test_03` → `geometry_test_13`.

**Source/selection counts:** 31 unique IFC source clusters = **4 previously exposed developer-control** + **6 untouched holdout** + **21 other development**; 45 original tasks = 4 previous + 6 holdout + **35 current untested development**, including all 15 basic tasks sharing one source.

**IMPORTANT limitations:** the selected six source clusters were unseen by previous *developer native original-four controls* and selected blind to model outcomes; this is not a true representative holdout of all 45 original tasks (the 15 basic tasks are deliberately excluded), not a statistical validation cohort yet, and not an approved preregistration. Every selected holdout task **currently fails the source/task-specific edit admission coverage gate**, including one IFC2X3 source. **No v0.58 holdout model trial is runnable or authorized.** Freezing an attractive holdout list cannot turn unsupported native operations into success. Before trials, expand and independently test source-native editing/scope admission for each selected original task, and obtain explicit prospective protocol, rights, model, cost and token-budget approvals.

## 3. Outcome/denominator policy candidate

Do not cherry-pick only accepted model outputs or report native IFC schema validity as equivalent to the author's repository task grade.

The candidate ITT denominator is **six fixed holdout tasks per arm**, with two comparisons (12 independent task-pairs / 24 arm-task slots if actually funded and admitted). The full population ITT denominator is **45** if claiming original complete-set evaluation and only after coverage/approval. Model-rejected submissions, timeouts, tool failure and no submission must remain **in the original assigned denominator**, while any **structural backend ineligibility/unsupported task is reported separately from LLM failure**; if structural failure prevents a matched paired comparison, mark the causal estimand unavailable rather than simply reporting a model's bad accuracy.

For each future legitimate accepted candidate, distinguish:
- **Original author repository Boolean metrics and mean score**, executed only in an evaluator-only environment and with the actual author pinned source version. These are NOT known to match the *published paper's exact grader revision*.
- **Independent original public-source physical task predicate**, not an author hidden answer script.
- **Independent original native IFC source/non-target preservation** and **incremental schema error multiset**; source may contain inherited issues. IfcOpenShell `express_rules=False` is not full EXPRESS validation.
- **Failures**: task unsupported by source-specific native admission, model generation failure, tool-call failure/rejection, Docker attestation failure, task mismatch, output timeouts; each has a distinct future label.
- **Time and actual cost**: exact provider-billed input/output tokens, context truncation, max completion tokens, failed attempts/retries, per-arm wall time and US$ spend, not approximate bytes.

A physically valid original five-Column deletion can receive an **author-repository score of 0.50**, while a 25-new-schema-error low-level deletion can receive **1.00**. Preserve these known v0.54 observations and do **NOT** substitute native IFC “valid” for original-author score or silently reinterpret grades.

**No actual ITT or D/I causal effectiveness estimate is computed by this checkpoint**; the selection is a pre-model-outcome candidate, not the funded and approved run.

## 4. Rights, licensing, provider and budget launch gate

The original dataset card `clemenskujat/bibimbap-data`, observed read-only at SHA `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`, declares `license: cc-by-4.0`. This is a publisher metadata statement, NOT independent verification of the underlying IFC creator's rights, per-IFC attribution requirements or blanket permission to transmit original source XML to a third-party provider. The pinned author source checkout `nbharathik/bibimbap` at `667004e16bd38fd7d538bcee56191465429fd975` has no recognized LICENSE in the local checkout; do not transfer its source or evaluator/answer code into model inputs or infer code licensing from the data card.

The exact provider/model snapshot, endpoint/region, full original input rights/retention approval, max context/output limits and real provider token accounting, USD monetary cap, prompt/tool-feedback equivalence, temperature/seed/timeout/retry/ITT plan and explicit user authorization are **not** known or approved. The existing no-trial firewall remains unconditional, even with an all-TRUE synthetic approval request. This checkpoint makes **zero model requests, zero paid provider calls and zero original IFC/GT uploads**.

## 5. Reproducibility and immutability

New files:
- `tools/bibimbap_v058_original45_capability_registry.py` — original file/evaluator SHA and actual native IFC schema census, 45×arm honest coverage matrix, source-cluster stratification, randomization/blocked launch gate.
- `tools/audit_bibimbap_v058_original45_prospective_registry.py` — `--write` exclusive-create and `--check` exact reproducibility.
- `tests/test_bibimbap_v058_original45_capability_registry.py` — focused original-scope, cluster leakage, deterministic selection, scorer provenance and refusal tests.
- `reports/bibimbap_v058_original45_capability_prospective_holdout_20261118.json` — frozen 45-task public SHA and 31 source cluster evidence, selected 6-task holdout, 24 prospective arm slots, all provider fields null.
- This protocol.

**Frozen new report SHA-256:** `0d8e7ca07a08af0afa3a08c10de5a76427e179d41cd1ca9b9df508f40fcc96c8`

**Frozen parent v0.57 native report SHA:** `22b3f30166ba2164278cdc1b2b25e5e4c4d0d0cddb74c25f7b759287bd127e57`

**Frozen source rights v0.56 report SHA:** `6b8e983a80a88a06f8de9ebefaeee3c52a71231583bbfeb164c05e0c1b17137c`

Reproduce locally in the independent Windows worktree, using pinned original author/data source checkout and the research `.venv`:

    python -m tools.audit_bibimbap_v058_original45_prospective_registry --check
    python -m unittest -q tests.test_bibimbap_v058_original45_capability_registry

This actually recomputes the **45 public task/question SHA pins, 31 native IFC source SHA/schema pins and 45 author test-module SHA pins** before byte-comparing the frozen report. Only metadata/hashes (no original question text, IFC bytes, hidden grader code, GT or model results) are committed. `--write` refuses to overwrite an existing frozen report, and `--check` fails closed on any drift. No network/model/Docker or paid API execution is needed.
