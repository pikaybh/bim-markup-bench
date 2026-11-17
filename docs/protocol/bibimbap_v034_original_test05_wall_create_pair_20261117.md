# v0.34 — original BIBIMBAP test_05 Wall Create, independently authored declarative D0 vs imperative I0

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/183
**Stack:** Draft PR #182 is the v0.33 parent; preserve its source tree and history
**Protocol class:** original-public **nonblinded developer-authored feasibility control**, NOT a matched model test, causal effect or production-readiness claim.

## Research need and public task

The frozen original BIBIMBAP dataset has **45 intention-to-test** tasks (15 CREATE, 15 UPDATE, 15 DELETE), but the prior success examples are selectively developer-implemented. In v0.31, **11/45 original cases** had byte-equal native IFC D0/I0 developer witnesses, none CREATE. v0.32 and v0.33 subsequently added one independent physical **Column** and **Slab** original public CREATE paired positive witness each. Neither native IFC pair had full-byte equivalence.

This v0.34 changes **no original 45 task**, **no scorer**, and **no earlier result**. It tests a third class: the original public basic CREATE **`test_05`**, wording: “Add a wall with a length of 15m beginning in (0, -10).” The source is original `basic_tasks.ifc`, native IFC4X3 millimetres, 358 original IfcRoots and 43 original IfcProducts.

Pre-grader independent input choices (the PUBLIC question does **not** specify these): choose wall world-space axis from **(0,−10,0) to (15,−10,0)** (**+X**, 15m long), level original **L1**, height **3.0m**, thickness **0.2m**, thickness centered around wall axis, bottom z=0. This is a developer-fixed engineering assumption, **not a claimed uniquely correct interpretation of the underdetermined question**. No geometry/default choice was tuned to original-author scorer feedback.

Source and provenance pins:

- Original upstream author Git: `667004e16bd38fd7d538bcee56191465429fd975`.
- Original upstream data Git: `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`.
- `basic_tasks.ifc` SHA256: `9ef1235e49d5b0359c1d44fd95a7afad7755149362109ca8b875d0427dc487ca`.
- Exact public test_05 question SHA256: `222cd92c3b4d9eae335aadda7511eadac9e65e5b1f22776ba8f7c1beb13cf4d0`.
- Frozen v0.31 / v0.32 / v0.33 reports verified by SHA256 before experiment.
- Full v0.34 actual original-task report `reports/bibimbap_v034_original_test05_wall_D0_I0_native_semantic_pair_20261117.json` has SHA256 **`d4bc58a426fd30b6215fef0c2c8d0907c109df1127fa64d44f7d8ab911d4073d`**.

## Why v0.6 was added rather than declaring v0.5 ready

Original `src/runtime/experimental_v5_wall.py` explicitly rejects graph additions and supports only **Wall UPDATE/DELETE** on already projected source walls. The original new Wall is not implemented by v0.5. The prior v0.33 full XML backend specifically handles Slab, not Wall.

v0.34 implements a **separate opt-in scoped** compiler in `src/runtime/experimental_v6_wall_create.py`, without modifying v0.5. It reads the complete original declarative XML state produced by `project_ifc_v4`, parses the edited full state with existing schema/typed XML parser, binds and assigns a deterministic new native GUID, computes a graph diff, and **permits only one new `Wall` node plus its existing-storey edge**. Mixed edits, a second wall, deletion, and changed original elements fail closed. It uses a staged transaction and native IfcOpenShell APIs to create an **IfcWall with Body extrusion and Axis line**, actual spatial containment, real world placement, and original IFC4X3-metre source-preservation checks. It is **not** an XML instruction tunneling through a hidden imperative `<Create>` tool.

The opt-in v0.6 backend is **not wired into the actual LLM matched25 model host**; v0.5 existing behavior remains intentionally unchanged. The successful developer run cannot be promoted to model host/full-45 parity.

## Executed order — grading isolation

1. Verify exact original author/data Git revisions, public task, 45-denominator and all prior report hashes; check original raw IFC remains unchanged.
2. Run newly written `tools/bibimbap_v034_original_wall_i0.py` **first**, from original IFC only. It imports neither D0 nor XML, original grader, hidden targets or previous candidate files. It creates physical `IfcWall` with native Body/Axis and original L1 containment using independent imperative Python/IfcOpenShell API. Persist a separate real native **mm IFC** scratch candidate.
3. **Before D0 is called**, reopen I0 native IFC with `tools/audit_bibimbap_v034_original_wall_pair.py` independent geometry/source oracle. Independently verify exact body and world axis, original root inventories, original product preservation and native world triangle mesh signatures.
4. Construct original whole XML and add one `Wall` element with predeclared endpoints, height, thickness and existing level. Call separate v0.6 trusted native compiler, persist mm IFC from its **separate** scratch working model, independently verify with exactly the same native read-only oracle. Neither candidate is derived from the other candidate.
5. Only after both native IFC candidates and read-only oracles pass, invoke **unchanged pinned original author scorer** separately for D0 and I0. Keep scores exactly as returned, including non-full scores if ever observed.
6. Check no original raw IFC, original author/data Git revision or frozen prior evidence changed. Publish no hidden GT, full original private IFC objects or model responses.

The original source is read-only and each candidate is created in a distinct scratch directory. The run's whole-file IFC SHA256 values may differ on rerun because each new run assigns fresh native entity IDs in I0; equality of whole bytes **within one execution** is measured without normalization, not assumed.

## Observed result

| Independent native predicate | XML D0 v0.6 | Python I0 |
| --- | --- | --- |
| Actual persisted IFC4X3 mm source-derived new `IfcWall` | PASS | PASS |
| Original zero-height L1 containment extended by exactly one wall | PASS | PASS |
| Native 3D axis from (0,-10,0) to (15,-10,0), metres | PASS | PASS |
| Body bbox (0,-10.1,0)–(15,-9.9,3), metres | PASS | PASS |
| Native actual extrusion height 3m | PASS | PASS |
| Preserve all original 358 IfcRoot IDs/classes/names/descriptions | PASS | PASS |
| Preserve all 43 original IfcProduct identities and original 39 shaped world meshes | PASS | PASS |
| Compare original **1,652 triangulated world-mesh faces** at 1µm canonical precision | PASS | PASS |
| Unchanged original-author score | **1.0** | **1.0** |
| Four original-author metric components | **all 1.0** | **all 1.0** |
| Actual full native IFC files byte-identical across arms | **NO** | **NO** |

Original native `IfcRoot` and original product/triangulated shape preservation **do not guarantee original full STEP entity preservation**: source millimetre-to-metre-to-millimetre conversion may rewrite native SI unit representations and original containment updates are expected. No full IFC metadata/properties/material equality, whole-building collision oracle, normative BIM quality, end-to-end model safety or full native authoring equivalence is claimed.

**Scientifically correct accounting:** preserve **11** earlier original tasks with byte-identical native developer outputs; add **one** more different-class original CREATE **task-specific semantic-only** paired developer example. Original CREATE positive paired examples now **3/15**: `test_04` Column, `test_02` Slab, `test_05` Wall; remaining **12/15** still lack such evidence (not proven infeasible). 11/45 byte-equal count does **not** rise to 14. Proven original45 complete information parity **0/45**; full native write parity **0/45**; real matched LLM D/I experiments **0**. No causal source representation performance inference.

## Tests, artifacts and execution

- `src/runtime/experimental_v6_wall_create.py` — separate opt-in single Wall CREATE compiler with state-diff-based native persistence; old v0.5 untouched.
- `tools/bibimbap_v034_original_wall_i0.py` — native original-source-only imperative I0 with fresh IFC output / source hash / original schema/units checks.
- `tools/audit_bibimbap_v034_original_wall_pair.py` — original provenance and frozen-report gates; standalone native read/oracle; strictly ordered paired source-only execution; unchanged author scoring after candidate freeze.
- `tests/test_bibimbap_v034_original_wall_pair.py` — positive real IFC and negative native provenance/geometry/multi-change/score-forgery controls; asserts v0.5 does not silently accept create.
- `reports/bibimbap_v034_original_test05_wall_D0_I0_native_semantic_pair_20261117.json` — frozen real trial summary.

Reproduce from v0.34 isolated worktree with a pre-existing suitable venv and pinned original author/data repositories:

```powershell
$base='D:\문서\D__1_Projects\202611'
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
& $py -m unittest -q tests.test_bibimbap_v034_original_wall_pair
& $py -m tools.audit_bibimbap_v034_original_wall_pair `
    --author (Join-Path $base 'bibimbap-author-upstream') `
    --data (Join-Path $base 'bibimbap-author-data')
```

`--write <new-path>` writes a report once with exclusive `xb`, never overwriting frozen existing evidence. No paid inference, Docker start/reset, API service modification, Xim source edit or research main merge was performed. Candidate real IFC files are transient and not committed.

## Next steps (blocked launch)

1. Original CREATE feasibility for other object kinds (Door, Opening, Space, room-bounding topology and relational wall) without success-based cherry picking; selected positives do not substitute for all 45 tasks.
2. Assess task-specific **read input parity**, including original non-projected IFC object roles, and **real writer capability parity** for every original task under the same model-visible interface and budget.
3. Prove isolated and nondestructively recovered Linux/Docker execution and model-host opt-in backend availability before any model-generated Python execution; do not disable sandbox as workaround.
4. Only after preceding gates, preregistered matched real LLM D/I trials with frozen per-arm tool feedback, model, context and budget; independent oracle and original author scoring afterward.

## Additional native source STEP accounting (read-only)

After both full original-native outputs had passed their independent product/triangle/axis checks, a separate read-only STEP-ID/class comparison of the untouched original **3,138 STEP entities** and each saved candidate found the **same changes in both D0 and I0**: **1 original `IfcSIUnit` entity no longer present**; **1 original `IfcUnitAssignment` entity changed**; **1 original `IfcRelContainedInSpatialStructure` changed**. Both candidates held **3,160 native STEP entities**, each with 22 more records net than the original. These observations are consistent with mm–m–mm normalization and appending the Wall to an existing storey but are **not exhaustive proof** of that causal mechanism. The input original source itself remains byte-unchanged. The v0.6 trusted compiler additionally checks original STEP-entity preservation when working on its separately normalized **metre** IFC source; this is **not** a claim that the native original mm source is byte/STEP identical after round-trip. Do not aggregate the semantic positive into the prior 11 native-byte-equal developer witnesses.
