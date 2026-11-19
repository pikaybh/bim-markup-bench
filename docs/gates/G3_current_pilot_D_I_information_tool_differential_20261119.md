# G3 — Actual frozen BIM-Edit pilot D/I information and tool differential (2026-11-19)

## Decision and scope

This report audits the **EXISTING** G2 source-text D and I adapters, across the unchanged **36-task BIM-Edit candidate pilot**. It extends `src/runner/frozen_context_parity.py` rather than creating a second harness. All 36 task identities are retained, 30 have locally cached verified original input IFCs, and six remain `BLOCKED_ORIGINAL_INPUT_MISSING_OR_INVALID`. **No original reference/GT IFC file is opened; no paid model/provider/tokenizer, IFC editing operation, benchmark scoring, or raw prompt/IFC bytes are included in the recorded report.**

This is an **information differential audit**, not proof of full scientific comparability or a frozen preregistration.

## Actual measurements

For each of the 30 available task rows, the direct XML side and the imperative Python side independently rendered the actual same *read-only source* with their current adapters. Five pre-existing shared source fields are compared verbatim: public task ID, public instruction, v0.1 projected XML, v0.1 language specification, original IFC source SHA256.

- **30/30 cached task rows have matching common XML, schema and instruction source bytes** (against 20 distinct original IFC paths); zero cached tasks were silently dropped.
- **Six/36 tasks have missing pinned original source IFCs** and remain in the denominator. Their full sample task IDs are retained, but no model prompt or private GT paths are exposed.
- The resulting XML representations span **624 to 30,043 UTF-8 bytes** across tested rows, but these are **partial IFC projections**, not lossless IFC files. A small projection is not proof that the model has enough original semantic/topological information.
- Both existing G2 adapters expose the same v0.1 XML language specification (**7,383 UTF-8 bytes**) as part of their common initial observation.
- **Only the imperative adapter additionally supplies 1,113 UTF-8 bytes of IfcOpenShell API reference notes.** The extra documentation is *not* common prompt content.
- For the current two G2 adapters, the **initial configured** budgets match: `one_shot`, **1 attempt**, **180 seconds**, **32,768 output-submission UTF-8 bytes**. This does **not** prove equivalent error feedback, query power, tool call opportunity, native IFC access, end-to-end time fairness, or observed provider tokens.
- The legacy unfrozen two-arm pilot plan declares `["direct_xml","imperative_python"]`, input **20,000 model tokens** and output **6,000 model tokens** maximum per attempt, while the recent input-only stager has **three labels** `["D_FULL","D_MANAGED","I_NATIVE"]`. These are **not currently a prospectively registered identical three-arm representation protocol**; relabeling is not evidence that D_FULL and D_MANAGED have separately implemented, scientifically fair native execution semantics.
- The Python arm's model-visible G2 context still reports `OS_sandbox_available=false` and `allowed_execution_operations=[]`. A *separate trusted G2 Docker safety probe* has successfully run, but that does not mean the actual model can execute Python or that its feedback tool-call budget is fixed.

### Research conclusion

The limited condition **"same original source input hash and same common projected XML/initial instruction"** is independently verified for 30 source-available candidate task rows. **Full D/I treatment fairness is NOT established**, because the existing Python arm has additional API documentation and different authoring/execution affordances, while the XML projection does not necessarily preserve all information an imperative program could query from the native IFC. One-shot byte ceilings are not observed token counts.

**Do not achieve apparent parity by padding a prompt with irrelevant filler, deleting required control-arm API documentation after seeing results, or silently upgrading one arm's tool privileges.** Before scoring: preregister what baseline comparison means and explicitly separate (a) identical common source facts, (b) arm-specific authoring language/library documentation, and (c) native source querying, compilation, execution and feedback availability. Define accepted common-supported source-entity/task strata before looking at model outputs; report unsupported/unknown cases separately without dropping them from the original 36-task ITT denominator.

A defensible prospective study might choose a **pre-registered arm-specific documentation condition** with transparently measured differing input tokens and a matched total ceiling, plus a separate **shared-docs ablation** as a robustness check. These are proposals, **not** implemented or scored trial arms. Protocol status remains DRAFT until model/provider, tokenizer and prices, exact matched prompts, feedback cycles, full-original-file rights, independent source lineage, frozen blinded evaluator and owner cost authorization are confirmed.

## Existing tools and reproducibility

- Audit implementation: `src/runner/frozen_context_parity.py`, `audit_current_pilot_information_and_tool_parity`.
- Evidence: `reports/g3_bim_edit_36_task_information_and_tool_parity_20261119.json` (created once, byte-for-byte compare on replay), **SHA256 `c78650e8e30f50029237e927ae6006e18a92e9872416e9e75c03290db22abad8`**, created from the full 36 task row audit and pinned by the regression test.
- Tests: `tests/test_pilot_current_information_tool_parity.py` (actual pinned cohort, positive/negative common-context checks, tool budgets, document asymmetry, dataset-denominator and frozen status safety).
- Original `manifests/pilot_36_candidate_v0.json`, tasks, the six missing originals, IFCs, fixed source rights ledger, earlier G2/G1 reports and frozen model-side protocols are unchanged.

Run from the single existing Windows checkout, using the existing Python venv, with no provider and no Docker process:

```powershell
.\.venv\Scripts\python.exe -m src.runner.frozen_context_parity --check-current
.\.venv\Scripts\python.exe -m unittest -q tests.test_pilot_current_information_tool_parity
```

`--check-current` reprojects already-cached original IFC inputs twice per available task through independent D/I adapters and compares the canonical stored JSON; it can require substantial CPU time. It does **not** run native editing or a real model. If any original input is missing or altered, the affected task is recorded blocked (with the original 36 denominator retained), and the frozen report comparison fails.

**Live release stays disabled:** `BLOCKED_INFORMATION_AND_TOOL_PARITY_NOT_ESTABLISHED`, `actual_model_prompt_transport_verified=false`, `same_exact_provider_tokens_measured=false`, `model_launch_allowed=false`, and zero official scores.
