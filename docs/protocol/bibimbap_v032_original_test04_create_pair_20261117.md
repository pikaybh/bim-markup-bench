# BIBIMBAP v0.32 — Original public `test_04` physical Column CREATE paired developer controls

**Issue:** [#179](https://github.com/pikaybh/bim-markup-bench/issues/179)
**Parent:** [v0.31 Draft PR #178](https://github.com/pikaybh/bim-markup-bench/pull/178), source commit `669b245414cacdda89b4fe5deeffcb58f78788c2`
**Classification:** *New real original IFC native developer control, not matched LLM performance, not full native byte identity, not global D/I source/operation equivalence.*

## Why this checkpoint

v0.31 showed the historical **11 original-public-task D0/I0 native byte-equal developer witnesses are exclusively 7 DELETE and 4 UPDATE**; **0/15 original CREATE tasks** had paired native developer controls. This undermines any temptation to select developer-success cases as the model comparison population. The first CREATE feasibility question therefore targets the frozen original-public task `test_04`, which has a prior *D0-only* positive real IFC result (`reports/bibimbap_test04_column_v2_developer_d0_20261113.json`), but no independently paired original-native Python I0.

The unmodified original public question asks to create a Column **at (12, 8), 3m high**. It does not specify a footprint. Retain the historical predeclared developer-only width/depth **0.3m × 0.3m** with base z=0 and original existing L1 zero-elevation storey. These are public-fixture engineering defaults, not hidden grader facts or evidence about how an LLM would choose unspecified dimensions.

Original author repository SHA `667004e16bd38fd7d538bcee56191465429fd975`; public dataset SHA `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`. Input original IFC `basic_tasks.ifc` is IFC4X3, **millimetre** native units, SHA-256 `9ef1235e49d5b0359c1d44fd95a7afad7755149362109ca8b875d0427dc487ca`; question SHA-256 `bdc610efa790a67c601a0c3d9056c47c702a7af9bcb05d3b8e3acb3d9771ce57`. The original author test's private targets and scorer implementation **are not made available to either writer**.

## Actually executed native pipeline

1. Check pinned Git revisions, original-public 45-task count and public task/source hashes; SHA-pin frozen v0.31 report and historical v0.2 D0 report. Fail closed on mismatch.
2. Independently implement imperative **Python/IfcOpenShell I0** in `tools/bibimbap_v032_original_column_i0.py`, directly from the original public source IFC, independently normalizing units to metre. No imports of XML projector/compiler/binder, original author grader, hidden targets or prior D0 output. Generate an IfcColumn with rectangular profile/extruded depth 3m, translated world placement, and existing L1 storey containment. Persist an independent mm IFC result in isolated temporary space.
3. **Before D0 execution**, run an independently implemented actual native-IFC oracle on I0. Reopen actual result IFC, require exactly one added physical IfcColumn, preserved original 358 IfcRoot identity/class/name/description, preserved original 43 native IfcProducts, original world geometry for all **39 source products with shape**, and explicit no-shape classification for the other 4. Confirm new Column's actual native 3D mesh world bbox `(12,8,0)`–`(12.3,8.3,3)` metres, real 3000mm IfcExtrudedAreaSolid depth, original zero-level storey containment.
4. Independently compile **full declarative XML state** with only one added Column element, using previously committed `experimental-column-v0.2` trusted compiler. This is **direct declarative source editing**, not a `<Create>` command API disguised as XML. Convert native result back to original millimetres, then apply the **same separate** actual native IFC verifier.
5. Verify both independently computed native-oracle summaries agree, neither source/author/data revision changed, and both candidates remain separated. **Only after both candidates are frozen and independently audited**, run the **unchanged pinned original author scorer separately on D0 and I0**, with no scorer feedback returned to either writer.

No candidate IFC, raw source IFC, hidden target GUID, private grader source, full original question or model conversation is committed. File hashes refer to the transient saved actual IFCs of this **specific frozen trial**, not stable recomputation hashes across calls with fresh native random GUIDs.

## Measured original-public result

| Verification | D0: whole declarative XML | I0: independent Python/IfcOpenShell |
| --- | --- | --- |
| Native original IFC4X3 mm result independently reopened | PASS | PASS |
| One new physical native IfcColumn in original L1 storey | PASS | PASS |
| World bbox min / max (metres) | (12,8,0)/(12.3,8.3,3) | (12,8,0)/(12.3,8.3,3) |
| Native extrusion depth (mm) | 3000 | 3000 |
| Original 358 Root identities/classes/names preserved | PASS | PASS |
| Original 43 native Products including 39 physically shaped geometries preserved | PASS | PASS |
| Unchanged original-author score | **1.0** | **1.0** |
| Original-author metric components | object_exists, location, dimensions, integrity: **1.0 each** | same |
| Actual candidate files byte-identical to the *other* arm | **NO** | **NO** |

In the actual frozen run, D0 whole-IFC SHA-256 and I0 whole-IFC SHA-256 **differ**. This is a **task-specific native shape, original product geometry, containment and original-author-evaluation semantic agreement**, NOT full native byte equality or proof of exhaustive IFC semantic equivalence. The writer outputs have separately authored entity metadata/new native GUIDs; those bytes are not normalized away, modified or described as equal.

**Result accounting:** keep prior v0.31 **11/45 byte-equal native paired developer cases unchanged**, add exactly **1 distinct original CREATE task with task-specific semantic/native-author-scorer paired developer evidence**. Do not sum these categories into an ambiguous 12/45 “byte-equal” count. **14/15 original CREATE tasks remain without newly evidenced paired original-task semantic feasibility.** Other original tasks' unknown statuses remain unknown; do not infer inability.

The original45 full IFC information and native write-capability parity remain **0/45 proven**; no actual matched LLM trial or new provider cost; no source representation causal performance claim. This v0.32 D0 compile path uses the **v0.2 experimental compiler**, which is **not transparently enabled in the original 25-tool-call model host**. A future fair model study must preregister a uniformly available trial backend and match reading and feedback; selected developer examples alone do not establish model host readiness.

## Source artifacts and test procedure

- `tools/bibimbap_v032_original_column_i0.py`: independently authored source-only Python I0; requires fixed original native source SHA, refuses overwritten output, verifies original units and object-creation output.
- `tools/audit_bibimbap_v032_original_column_pair.py`: strictly ordered real source-only I0→native oracle→complete-XML D0→native oracle→original author scorer pair.
- `tests/test_bibimbap_v032_original_column_pair.py`: positive real source control and negative tests covering score fabrication, source/hash drift, extra/absent Column, false claimed GUID, wrong world position, already-used output, original source identity, unchanged original inputs and research-honesty gate.
- `reports/bibimbap_v032_original_test04_column_D0_I0_native_semantic_pair_20261117.json`: frozen real original-task summary, SHA-256 `65cd592b83b06ac161ff420982cb2f3378e850613f4645419690e06764987b2b`. Run-specific candidate IFC hashes provide evidence provenance, not a claim of deterministic IFC bytes across independent runs.

From the isolated research worktree, with an **already provisioned** Python/IfcOpenShell venv and local pinned original data, execute:

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
& $py -m unittest -q tests.test_bibimbap_v032_original_column_pair

# Reproduce independently in transient directories without writing an output report:
& $py -m tools.audit_bibimbap_v032_original_column_pair `
    --author (Join-Path $base 'bibimbap-author-upstream') `
    --data (Join-Path $base 'bibimbap-author-data')
```

The optional `--write` creates a report with exclusive `xb` open only, never overwrites prior frozen evidence. Re-executions should reproduce **native geometry/score/oracle invariants**, not the D0 or I0 full-file SHA produced by newly generated IFC GlobalIds. The output versioned report itself is immutable and its actual SHA checked.

## Remaining blockers and next priorities

1. **Other original CREATE tasks (14)**: prospectively select by public operation family and support gaps, NOT according to historical model success or hidden scorer results; add a second representative physical element type/geometry with genuinely independent I0 and XML D0 if feasible. Underlying v0.31 45-task denominator stays fixed.
2. **Task-relevant full source and write parity:** the XML view is incomplete for every original native IFC as a whole. One proven Column creation shows narrow feasible editing only; original IFC metadata, materials, properties and relationships still require task-specific checking for every future model candidate.
3. **Secured model execution:** Windows Docker Desktop engine was unavailable in v0.31, and the specific experimental D0 v0.2 compiler is not the matched25 production runner. Do not perform an unsafe unisolated model-Python candidate execution on Windows to work around this. No Docker reset or daemon startup was part of v0.32.
4. Independent original author scorer disagreements on other tasks remain unresolved and are not altered here.

Original 45 inputs, original author evaluator, earlier reports and Git stashes, existing PRs, research `main` and Xim/BIXML product code remain unchanged.
