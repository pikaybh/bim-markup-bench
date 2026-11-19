# BIBIMBAP v0.35 — Original-public test_01 physical hosted Door CREATE: XML D0 versus Python I0

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/185
**Parent:** v0.34 Draft PR #184; exact base commit 4db0d9e34f385f1fd2f82d8828377147925bcd6f
**Research class:** original-public, developer-authored, source-only **physical IFC feasibility control**. **Not a matched LLM benchmark or causal result.**

## Research contribution and limits

After source-only native positive D0/I0 pairs for Column, Slab and Wall, this study handles an actual relationship-dependent **Door** task. Unlike an unhosted solid, a valid original-public test_01 requires the new IfcDoor to fill an IfcOpeningElement which physically cuts the *specified original IfcWall*. The experimental direct XML arm edits **complete declarative source state**, and its trusted compiler creates the real IFC objects and graph outside the tested LLM boundary. The imperative I0 arm uses a separately authored Python/IfcOpenShell script on the original IFC. This is *not* an LLM test: both controls are authored by a developer.

The immutable original-public instruction requests a door size 2 by 1 metres in an explicitly named source wall. Pre-evaluation assumptions were specified in GitHub Issue #185 **before the original author scorer was invoked**: **height 2m, width 1m**, zero sill, center of the source Wall's actual 10.2m horizontal axis (offset 5.1m), original L1 storey, 0.4m-deep through-cut in the 0.2m Wall, and a centered 0.04m physical door leaf. Height/width order and exact placement were not fully specified by the natural-language question; this is only **one openly fixed feasible interpretation**, not a claim of uniqueness. No hidden answer, reference IFC, scorer conditions or previous D0 output was consulted while writing I0 or D0.

## Frozen original evidence

- Original author repository Git HEAD: 667004e16bd38fd7d538bcee56191465429fd975.
- Original data repository Git HEAD: f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca.
- Original public source basic_tasks.ifc: IFC4X3 **millimetres**, SHA-256 9ef1235e49d5b0359c1d44fd95a7afad7755149362109ca8b875d0427dc487ca.
- Original public task test_01 question SHA-256: 6047b505112d7c9da219957e74a955d259c67148f019250b0722605db6610c31.
- Before execution, the v0.31–v0.34 original45/evidence reports are checked against exact frozen SHA256 values inside the audit script.
- Frozen v0.35 actual two-arm report: reports/bibimbap_v035_original_test01_hosted_door_D0_I0_20261117.json, SHA256 **7ba3a9465996a90d4d324c8e31bc3ff18f3487cb890431e3c30989a516ac82c9**.

## Actual ordered experiment

1. Verify original author/data Git revisions, original public task and source IFC hashes, original 45-task denominator and all prior frozen reports.
2. Create **independent I0 first** using tools/bibimbap_v035_original_door_i0.py, which imports no XML, compiler, binder, original evaluator or hidden target. Start from untouched original IFC and save a separate actual mm-native IfcDoor, IfcOpeningElement, IfcRelVoidsElement, IfcRelFillsElement and original-storey contained door.
3. **Before executing D0**, reopen real saved I0 IFC. A separate native geometry+graph oracle verifies the exact original Wall, actual physical wall-volume subtraction, new door/opening bboxes, proper native host/fill IFC relations, new product inventory, original IFC Root identities and **all 38 unrelated mesh-bearing original products**.
4. Read original XML projection and add **exactly two declarative elements**: one Opening (existing Wall host, offset, sill, width, height) and one Door (new Opening reference, width, height). This is **complete XML document state**, with no imperatively encoded Create operation.
5. A new **opt-in v0.7 trusted native compiler** in src/runtime/experimental_v7_hosted_door_create.py checks parsed typed old/new states, stable source and allocated GUIDs, and requires exactly **2 new nodes + host_void and opening_fill relations**. It refuses all other new/deleted/mixed edits, new arbitrary GUIDs and unrelated host Wall. It uses a staged transaction to write the separate real D0 IFC using trusted IFC APIs. The pre-existing v0.5 and v0.6 Wall behavior remains untouched.
6. Reopen D0 IFC and run **exactly the same independent native geometry and source-preservation oracle**, then compare D0/I0 evidence. Only *after both outputs pass*, run unchanged original author scorer separately for each. Never choose only the higher scorer or assume scorer=independent oracle.

No candidate IFC, original IFC model bytes, grader source, private target GUID, model prompt/response, or hidden GT is checked into this branch. The two native candidate IFC SHA-256 values in the frozen report are single-run provenance only; fresh native random GUIDs can make rerun IFC bytes differ without changing geometry.

## Executed findings

| Independent check | XML D0 | Python/IfcOpenShell I0 |
| --- | --- | --- |
| Persist original-derived IFC4X3 mm file with physical Door + Opening | PASS | PASS |
| New Opening really voids specified original Wall | PASS | PASS |
| New Door really fills that Opening and is in original L1 | PASS | PASS |
| New Door physical bbox (metres) | (23.8,15.08,0)–(24.8,15.12,2) | same |
| Opening physical bbox (metres) | (23.8,14.9,0)–(24.8,15.3,2) | same |
| Actual original host Wall triangles before → after | 12 → 28 | 12 → 28 |
| Original host Wall actual solid volume before → after | 7.344 → 6.944 m³ | same |
| **Precisely 1m × 2m × .2m wall void physically removed** | **.400m³** | **.400m³** |
| Preserve original 358 IfcRoot GUIDs/classes/names | PASS | PASS |
| Preserve original 43 products, incl. **38 non-host world mesh objects** | PASS | PASS |
| Original nonhost native triangles independently compared (1µm precision) | **1,640** | **1,640** |
| Original author task score | **1.0** | **1.0** |
| Author components: exists, position, dimensions, integrity | all 1.0 | all 1.0 |
| **Entire D0 vs I0 native IFC file bytes equal** | **NO** | **NO** |

The original Wall has intentionally *changed* geometry. Thus this checkpoint does **not** claim all 39 original shaped products remain geometrically unchanged; only the **38 non-target products** are unchanged, and the host is explicitly validated as having a properly sized hole. Original IFC Root identity/class/name and original products persist.

The read/write normalization from original native millimetres through a metre working model can alter output native STEP SI units/unit assignments, while original spatial containment changes as the Door is added. The **original input file remains byte-unchanged**, but exhaustive preservation of all original STEP entities/metadata/materials/quantity values and lossless native roundtrip are **NOT proven**. Entire-building intersection/collision correctness and actual performance of an LLM are likewise not proven.

## Denominator discipline

The original **45 task intention-to-test denominator remains unchanged**. Previous 11 developer-generated original cases with entire native IFC **byte equality stay 11**. v0.32–v0.35 add **four separate, semantic-only positive developer D0/I0 CREATE controls** for Column test_04, Slab test_02, Wall test_05 and hosted Door test_01. **11 of 15 original CREATE tasks remain unverified** under the same semantic paired controls. This is not a 15-case byte-equal sample or a 4/15 LLM pass rate.

Original45 full task-relevant read parity proven: **0/45**. Full native write parity proven: **0/45**. Matched *actual LLM* D/I trials: **0**. New paid model calls: **0**. No claim of causal representation advantage.

The Door D0 v0.7 backend is **separately opt-in**, not integrated with the frozen matched25 model host. A matched model test requires independently pinned equal model-visible source information, tool budget, feedback, and safe isolated Python execution. Windows Docker Desktop Linux engine was unavailable in the last environment audit and was not modified here.

## Reproducibility

Files: src/runtime/experimental_v7_hosted_door_create.py; tools/bibimbap_v035_original_door_i0.py; tools/audit_bibimbap_v035_original_door_pair.py; tests/test_bibimbap_v035_original_door_pair.py; frozen JSON report above.

From the isolated worktree, with preexisting Python/IfcOpenShell venv and locally pinned external original author/data repos:

    $base = 'D:\\문서\\D__1_Projects\\202611'
    $py = Join-Path $base 'bim-markup-bench\\.venv\\Scripts\\python.exe'
    & $py -m unittest -q tests.test_bibimbap_v035_original_door_pair
    & $py -m tools.audit_bibimbap_v035_original_door_pair --author (Join-Path $base 'bibimbap-author-upstream') --data (Join-Path $base 'bibimbap-author-data')

Optional audit flag --write creates a **new** frozen evidence file via exclusive binary create and rejects overwrite. All native candidates are written in temporary isolated folders, not committed.

## Next scientific priorities

Original test_03 calls for an **opening in a slab**, but the existing declarative Opening.host contract accepts **Wall only**, so a Slab-opening must **not** be represented as a fake Wall host. Next inspect/reconcile this source-schema and native-authoring gap through a separately frozen scoped change; preserve all old Wall-hosted semantics. Also prospectively audit the geometry/topological Create cases by original-45 membership, not post-hoc selection. A completed developer proof is not a verified ready-to-run fair D/I LLM trial.

No original benchmark/evaluator/GT changes, Xim changes, paid inference or Docker service changes were made in this checkpoint.

## Post-frozen native STEP inventory (read-only)

After both actual native IFC candidates had been created and scored, a separate read-only STEP-ID/class comparison counted **3,138** entities in the untouched original IFC and **3,174** in each independent D0 and I0 candidate. In both results the same original-native deviations were observed: exactly **one original IfcSIUnit entity is absent**, while **one original IfcUnitAssignment** and **one original IfcRelContainedInSpatialStructure** record differ. The original source IFC file itself remains SHA256-unchanged. These output-level differences are consistent with unit conversion and expected Door containment, but do not prove exhaustive cause or byte-/STEP-level losslessness. They must not be recast as complete original IFC information/read/write equivalence; original IFC Root identities and 38 untouched product world meshes are a narrower property.

## Final v0.35 test accounting and older fixture compatibility

- **New focused tests:** 25 of 25 PASS (including real native original IFC, wrong host/wall, absent or spoofed void/filling relation, wrong Door world position, source hash drift, mixed/two-node-plus XML edits, unchanged v0.5/v0.6 refusal and forged author score).
- **Selected non-Docker multi-version regression:** 270 tests total, **269 PASS / 1 SKIP / 0 FAIL**, 162.971s. The single skip is a pre-existing Windows symlink-privilege case. This is not a full repository test run or Docker worker revalidation.
- **Additional historically compatible Door/Opening tests:** modules test_bibimbap_v024_original_opening, test_bibimbap_v025_original_door and test_rotated_host_opening: **67 tests, 65 PASS / 2 SKIP / 0 FAIL**, 26.736s. These may overlap in part with wider existing checks; do not sum counts into one independent population.
- **Separate older module cannot be run against current tracked manifest:** test_hosted_door_delete_runtime internally pins an *older* pilot manifest SHA256 **75b4847814dbefad95340556c0b62f9cda72cac319cd82ecb23ea4933c9ab694**, while this v0.35 branch's tracked manifests/pilot_36_candidate_v0.json is **356dbf9ec1b696fff96b4c7c66145393bc73085f8fe1767e3adc4740d186b0d8**. Initial attempt with missing untracked inputs produced one setup error; we then copied the three published source-only, SHA-pinned public files from the original research worktree **only to the isolated v0.35 worktree** (180459 + 25930 + 136436 bytes; all ignored/untracked); the legacy manifest mismatch remains. We explicitly **did not overwrite/revert the tracked pilot manifest, alter any frozen pin, or mark the old module passing**. The compatible modules above were rerun and passed. This is a **historical-fixture/version gate**, not a v0.35 Door Create runtime error. A future separately versioned migration may reconcile that old test, if required.

Versioned report SHA-256 remains **7ba3a9465996a90d4d324c8e31bc3ff18f3487cb890431e3c30989a516ac82c9**. Original upstream author/data and source IFCS remain unchanged. No paid model or full-45 experiment was run.
