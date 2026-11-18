# v0.65 — Original IFC source-family leakage, source-neutral Door feasibility and unconditional offline admission

**Research checkpoint:** [Issue #245](https://github.com/pikaybh/bim-markup-bench/issues/245). Exact stacked base v0.64 [Draft PR #244](https://github.com/pikaybh/bim-markup-bench/pull/244), commit a20bcc5fa6bf3ad4de0f18c9b6d79acb8b3d498d. Work on independent research repository pikaybh/bim-markup-bench, not BIXML/Xim production.

**NO MODEL TRIAL, NO PAID MODEL CALL, NO EXTERNAL IFC TRANSFER, NO CLAIM OF LLM SUPERIORITY.** All new results use only developer-exposed original IFC files and actual local isolated Linux Docker, not any unseen candidate source or grader.

## 1. Original 45 tasks represent only 31 source IFC families

The exact public original 45 edit tasks (15 create/15 update/15 delete) resolve to only **31 unique original IFC SHA256 clusters**. **Fifteen basic tasks share the same one original IFC file**. The original v0.58 source registry confirms 2 IFC2X3 clusters, 1 IFC4 cluster and 28 IFC4X3 clusters. A task-level random split would leak source-model structure between development and test. The independence unit must be **source-family SHA**, with all task rows in a family assigned together. Rare IFC2X3 and IFC4 strata, CRUD and geometry/topology categories need explicit prospective grouping.

The v0.58 six-source cohort was chosen before any actual model trial. Since then all six models, original native geometry, original author metrics and target-side success logic were inspected by developers. The previous label PROSPECTIVE_UNTOUCHED_SOURCE_HOLDOUT is therefore **outdated**, not a valid present-day blind evaluation claim. Four earlier original source tasks were also inspected. The frozen v0.65 ledger records **10 known developer-exposed distinct IFC source families**: geometry_test_03/13/14/15/19, topological_test_05/11/12/17/18. The remaining **21 families are not certified unseen**; earlier catalog/metadata inspection exists and independent detailed exposure assessment is absent. **Certified truly unseen source families = 0.**

The v0.65 ledger contains **31 per-source entries** with original file SHA, relative path, schema, group task IDs and question hashes, category/CRUD, former v0.58 assignment, developer-exposure status and per-source rights statuses. A deterministic seed selects a **metadata-only quarantined candidate shortlist** across schema/CRUD/category buckets without opening any additional IFC geometry or author grader. These are provisional candidates, NOT a registered/approved experiment or genuine blind test until independent exposure and rights certification. The original 31-source metadata/registry is not altered.

## 2. Source-neutral physical IFC2X3/IFC4X3 Door+Opening prototype

The new module tools/bibimbap_v065_source_neutral_door.py has **no source-specific task ID, hardcoded original IFC SHA, hardcoded correct target GUID, author grader or private answers**. Its caller supplies a SHA-pinned original native IFC. It computes the original products, every original Wall GUID, original world geometry, schema and project length unit dynamically. The model-facing final-state data can include a new Door and a fully hosted Opening but **does not identify the correct Wall for any natural-language task**. Native IFC legality and task correctness are separate.

- **D whole final XML:** submits the ENTIRE unchanged original BuildingState source/geometry subtree, all original source Wall present rows (count computed dynamically), and precisely one newly declared Door and Opening with unique IFC GUIDs, source original host Wall reference, Door filling Opening reference, and absolute world-metre final 3D bounding boxes. No typed operation list, patch, AST or model-code-in-XML.
- **D managed final XML:** includes complete original Wall roster plus both new products and the SHA of the original IFC and entire full source XML. Trusted source-only compiler restores and rechecks the complete original BuildingState.
- **Independent I native Python:** independently generated general Python/IfcOpenShell on a cloned original IFC inside the SHA-pinned OS-isolated local Linux Docker, explicit commit. The I script does not call the D compiler or original author grader.

**The SAME source-neutral original-native post-edit gate** checks IFC2X3 or IFC4X3 project length units, all original STEP IDs/native attributes/Root GUIDs retained, exactly five new legal Root classes (IfcDoor, IfcOpeningElement, IfcRelFillsElement, IfcRelVoidsElement, IfcRelContainedInSpatialStructure), no orphan new IFC STEP geometry, actual Door/Opening world meshes, correct host and storey relations, original Wall full-thickness native CSG subtraction measured from separately reopened unmodified source and output IFC, unchanged other original product meshes/volumes, native OverallWidth/Height unit consistency and **zero new schema findings**. The IFC2X3 form must attach existing valid source OwnerHistory to new missing mandatory relation fields without touching original STEP objects.

**Genuine local source-neutral two-schema demonstration, only already exposed originals:**

| Source already inspected by developers | Schema | D full, D managed, general Docker I original-native IFC results | Actual hosted-wall CSG cut |
| --- | --- | --- | --- |
| geometry_test_03 | IFC2X3 | 3/3 PASS | 0.418 m³ |
| topological_test_05 | IFC4X3 | 3/3 PASS | 0.418 m³ |

All **six actual native original IFC candidates**, including **two genuinely executed pinned local Linux Docker general Python runs**, passed the same native source integrity/geometry/schema gate and have matching normalized native semantic digests for equivalent cases. Source authors' official metrics were NOT rerun here. This does **not** prove truly unseen-source generalization.

**Source-neutral does not mean universal.** This adapter currently supports only **one Door plus fully hosted Opening** in an axis-aligned represented planar Wall with a pre-existing storey, IFC2X3 or IFC4X3 and compatible native length units. No IFC4 (non-X3), curved/complex Wall, moves, deletes, arbitrary multi-element edits, or different lawful IFC representation transformations. It enforces strict source STEP-ID and exact five-new-Root preservation, so semantically valid I-native alternatives may be rejected; D and I do not have equivalent tool affordances. A source-backed code SHA/grammar inventory for v0.50/v0.55/v0.57/v0.59–v0.65 is in the frozen report, including source-specific limits, unique representation assumptions, live Python endpoint, tool schema disparity and strict source shape policies. **Equal native outcome on developer fixtures is not proof of equal difficulty, equal tokens, or causal superiority.**

## 3. Original author evaluation validity and provenance

The pinned original author source checkout is https://github.com/nbharathik/bibimbap, git HEAD **667004e16bd38fd7d538bcee56191465429fd975**. The README refers to LICENSE, but **the pinned checkout has no recognized LICENSE or COPYING file**. Author repository scoring version is not independently verified as exactly the published paper's official scorer version. The EC³ 2026 BIBIMBAP paper (DOI **10.35490/EC3.2026.271**, [official publication](https://ec-3.org/publication/ec32026_271/)) discusses **100 benchmark tasks** and a reported best baseline 50.2%, **not a result measured by the present restricted 45 original edit tasks, nor a source-native D/I LLM comparison**.

Prior original-repository metrics, based on real source/edited IFC and stored frozen evidence, remain separate from physical public-question correctness:
1. topological_test_05: true exterior Door author score 1.00 **and** incorrect internal-wall Door author score 1.00. The repo evaluator checks filling/hosting but does not require actual exterior. The original IFC has no IfcSpace, so even an outer-envelope research proxy does not prove semantic room circulation.
2. geometry_test_19: pinned author repo scorer references an original-target GUID absent from exact original IFC; no fictional official score is substituted.
3. topological_test_17: correct removal of five Columns cascades dependent property/type relationships; repository non-target Root survival check rejects lawful cleanup, author score 0.50.
4. geometry_test_03: original repo distinguished correct nearest positive-Y Wall (1.00) from farther-north Wall (less than 1.00), although both create structurally sound IFC.

Unchanged repository Boolean and floating-point submetrics must be retained, and independent native physical task predicates reported alongside, never silently replacing author metrics with a patched scorer.

## 4. Per-original-IFC rights are unverified: 31/31 blocked for provider transfer

The previously pinned public dataset card clemenskujat/bibimbap-data (card SHA f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca) advertises **cc-by-4.0 metadata**. A metadata label is not documented **per IFC source** provenance/creator permission, attribution or permission to upload raw IFC content to a commercial model provider or allow its retention. No individual source chain-of-title or attribution ledger was verified for any of the 31 original source SHA families; all remain UNVERIFIED/BLOCKED for external provider upload and retention. This does not mean a legal prohibition was established; it means an affirmative permission was **not verified**. Author repository code redistribution is also not assumed licensed from a README alone. **No original IFC file or private author GT was uploaded or included in this PR.**

## 5. UNREGISTERED, OFFLINE D/I experiment manifest — hard no-launch

tools/bibimbap_v065_offline_trial_admission.py records a **candidate-only protocol** with no trial launcher. It specifies source-SHA cluster as independence/randomization unit; schema/CRUD/category stratification; D_FULL, D_MANAGED and general Python I as **three different interventions**; identical initial source XML (byte-exact), 25 total calls maximum, native IFC/source schema/physical quality checks, source-cluster ITT denominator including failures/invalid edits/errors/timeouts, and prospective provider-billed input/output/tool-token/cost logging.

All unapproved fields remain explicit **null/false**: independent blind-auditor signoff, rights/retention permission, official author scorer parity, exact model/provider snapshot, temperature/seed, context/output budgets, sample cost cap, actual token pricing, retry/timeouts and intervention equivalence. Both D and I need source-specific feedback and tool-power auditing. The module **always raises TrialBlocked065, even if a caller forges every approval and unlimited budget to true**. No payment, network, provider or model runner is present.

A future separate explicitly authorized checkpoint must independently confirm data rights, genuinely blind source families (or acquire unseen models), exact published scorer provenance and matched model/tool/token/feedback conditions *before* implementing a paid model runner. Merely changing a config flag must never authorize transmission.

## 6. Reproducibility and frozen evidence

Frozen report: reports/bibimbap_v065_source_neutral_cross_schema_leakage_no_launch_20261118.json

**SHA256 cc55f6623fc65d3936cf6ee9bbacf1c46d3893aa94122317632d9f90d009382d**.

Auditor: python -m tools.audit_bibimbap_v065_offline_generalization --check

Tests: python -m unittest -q tests.test_bibimbap_v065_offline_generalization

The --check audit really reopens the same two already developer-exposed IFC models, creates **four source-neutral full/managed original IFCs + two independently authored genuine OS-isolated pinned local Linux Docker Python IFCs**, applies the exact same source-neutral scope validator, checks all 31 source-family metadata/rights, verifies v0.58/v0.63/v0.64 frozen SHA, checks unconditional no-model-launch and byte-compares every JSON field against the newly frozen report. --write creates the report exclusively and will not overwrite an existing file. It does not inspect unknown source geometry or any new task-specific author graders. All original files, research main, Xim production, previous frozen reports and Git Stash unchanged.

**Actual LLM attempts 0, paid provider calls 0, original IFC provider uploads 0, independently certified unseen source-family count 0.**
