# BIBIMBAP v0.36 — Original-public Slab Opening CREATE: XML D0 and independent Python I0

**GitHub issue:** https://github.com/pikaybh/bim-markup-bench/issues/187
**Stack parent:** v0.35 Draft PR https://github.com/pikaybh/bim-markup-bench/pull/186; parent commit `3b426d8715aa87b9c466474231bc06414cbf4087`.
**Research classification:** **Developer-authored, nonblinded, original-public task-specific native IFC feasibility control. Not a matched actual LLM test or causal representation result.**

## Original source and prospective geometry

Original unchanged benchmark public `test_03`: “Add an opening of size 5 by 5 meters to the center of the slab with id 11kJIqz$n2Jf_DfJV1SCVP.” This exact public question has SHA256 `a887b002fe9606743cf68dcc2914cd6ef136c16f78083999184f901ccf57c289`. The original native IFC4X3 millimetre file `basic_tasks.ifc` has SHA256 `9ef1235e49d5b0359c1d44fd95a7afad7755149362109ca8b875d0427dc487ca`; original author Git `667004e16bd38fd7d538bcee56191465429fd975` and original data Git `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`.

Pre-grading native source inspection showed the published GUID is an actual **IfcSlab/FLOOR**, native world bbox **(-0.2,-0.175,3.8) to (10.2,10.2,4.1)m**, 10.4×10.375×0.3m, 32.37m³ with 12 triangular faces and no pre-existing opening.

Before accessing the original grader, [Issue #187](https://github.com/pikaybh/bim-markup-bench/issues/187) froze the following source-grounded interpretation:

- A **5×5m horizontal square void** centered on the slab's world XY AABB center **(5.0, 5.0125)m**, world XY min **(2.5,2.5125)m**, max **(7.5,7.5125)m**.
- Native void tool spans z=3.7–4.2m (0.5m vertical construction depth) to pass completely through original slab z=3.8–4.1m. The author-requested two 5m dimensions refer to **horizontal plan X/Y**, *not* vertical void tool depth. Expected removed original slab physical volume is **5×5×0.3=7.5m³**.
- In an **explicit opt-in v0.8-only version of existing declarative Opening markup**, the existing `Opening` attributes refer to a Slab: `host` = original source-projected Slab ID, `offset=2.7` = X displacement from slab-min X, `sill=2.6875` = Y displacement from slab-min Y, `width=5` = X span, and `height=5` = Y span. The `sill` and `height` names are **semantically overloaded and ambiguous** compared with Wall Opening vertical semantics; this is only a scoped trial encoding, not a general clean domain schema or full equal model authoring interface. Wall Opening semantics and default behavior remain unchanged.

No original hidden solution, source GT, or original scorer feedback was used to choose any of these construction values. They were **not tuned after** the observed non-full author grade.

## Required separate implementation boundaries

1. **Independent native imperative I0**: `tools/bibimbap_v036_original_slab_opening_i0.py` imports native IfcOpenShell APIs and **does not import XML, D0 compiler, typed binder, author grader, hidden GT, or any previously generated candidate IFC**. It begins with the pinned original public native-mm IFC and independently preflights real slab mesh/volume. Writes real physical `IfcOpeningElement` via native `IfcRelVoidsElement` through the published **IfcSlab** to separate scratch native-mm IFC.
2. **Independent native geometry/source oracle**: `tools/audit_bibimbap_v036_original_slab_opening_pair.py` reopens each *saved* candidate. It requires exactly one new `IfcOpeningElement`, correct typed source Slab `IfcRelVoidsElement`, no extra new Root object, original 358 IfcRoot GUIDs/classes/names preserved, original 43 products retained, original 38 non-host mesh-bearing products unchanged (1,640 original nonhost triangles), original native containment and aggregation unchanged, exact native new opening world bbox, and measured real source Slab physical volume 32.37→24.87m³. Only **validated** numeric oracle outputs are rounded to 1e-8 to make 3.7 and 3.6999999999999997 compare equivalent; physical acceptance retains 1e-5m/1e-5m³ tolerances.
3. **Default schema preservation and opt-in versioned XSD**: original `spec/toy_markup_v0.xsd` remains byte-unchanged and still enforces Wall-only host via keyrefs. New `spec/toy_markup_slab_opening_v08.xsd` introduces a typed Wall-or-Slab `knownOpeningHosts` key. `src/runtime/xml_parser.py` accepts only literal schema variants `default` (unchanged legacy) or `slab_opening_v08`; **never an untrusted schema path**. `src/runtime/binder.py` defaults `allow_slab_opening_hosts=False`, only accepts slab host on explicit True, checks host class, true Slab XY footprint, and retains old Wall Opening invariants.
4. **Trusted whole-XML D0 compiler**: new `src/runtime/experimental_v8_slab_opening_create.py` parses/binds both complete original and edited XML source states and computes a stable-ID semantic graph diff. Exactly **one** new Opening node + exactly one `host_void` edge to the *real published original IfcSlab*, with no other edits, is accepted. It stages and verifies native IFC4X3-metric physical geometry/void changes **outside the tested LLM boundary** then converts it back to original native-mm IFC. The XML is a **declarative source document**, not an imperative `<Create>` action list, BIM command bus or agent-facing mutator. New v0.8 is not wired into the frozen matched model host; old v0.5/0.6/0.7 compilers were untouched.
5. **Strict execution order**: verify original author/data Git SHAs, original public question/source SHA and 45-task denominator, all prior v0.31–v0.35 evidence SHA256s. Run and independently validate I0 **first**. Run and independently validate whole-XML D0 **second**. Compare actual native independent geometry and relation oracles. **Only after both pass** call unchanged original benchmark author scorer separately on both. Neither candidate is derived from the other.
6. **New artifact**: `reports/bibimbap_v036_original_test03_slab_opening_D0_I0_20261117.json`, frozen SHA256 **`04def65798913aab267b4894f234b2d8ba8f173baff001b3059eed55bdade138`**. The separate native IFC full-file SHA values in this report are one-execution proof only, not stable canonical IFC-byte identities across reruns. The original input IFC itself is byte-unchanged.

## Results — real native IFC semantics and original unchanged scorer

| Independent observed property | Full XML D0 | Python/IfcOpenShell I0 |
| --- | --- | --- |
| Real saved native IFC4X3 millimetres | PASS | PASS |
| Added exactly one real IfcOpeningElement hosted by original IfcSlab | PASS | PASS |
| Actual native IfcRelVoidsElement links opening to published slab GUID | PASS | PASS |
| Real slab body physically cut (12→32 triangle faces) | PASS | PASS |
| Actual slab volume before→after | **32.37→24.87m³** | **32.37→24.87m³** |
| Actual physically removed host slab volume | **7.50m³** | **7.50m³** |
| New opening tool bbox (metres) | (2.5,2.5125,3.7)–(7.5,7.5125,4.2) | same |
| Preserve 358 original Root GUIDs/classes/names and all 43 original products | PASS | PASS |
| Preserve all 38 unrelated world-mesh products, 1,640 unrelated triangles | PASS | PASS |
| Original scorer object exists, dimensions, location | **1.0,1.0,1.0** | **1.0,1.0,1.0** |
| Original scorer integrity constraint | **0.6667** | **0.6667** |
| **Unmodified original author total task score** | **0.916675** | **0.916675** |
| Entire saved native D0 and I0 IFC bytes identical | **NO** | **NO** |

**Do not substitute the independent 7.50m³ physical-through-cut acceptance result for the original author's integrity score.** The original scorer's actual `test_03.py` executable checks three integrity subcomponents: correct void relationship, **no new collision** via its own geometry tree, and preservation of all original Root GUIDs. Its accompanying docstring inaccurately describes one component as a type check. Void and GUID preservation pass both the independent oracle and the pinned original author's actual subchecks, while the observed average is **2/3**. **After the frozen report was written**, a read-only rerun of those exact author utility checks returned for BOTH I0 and D0: `check_voids_relationship=1.0`, `check_elements_preserved=1.0`, and `check_clash_integrity=False`. We additionally inspected the author's geometry-tree collision pairs: **exactly one new clash involving the new IfcOpeningElement and the pre-existing original IfcSpace with GlobalId `2UsXAbj6n0fwEWqdkVuHuP`**, in **both arms**. The source had zero pairs when focusing on the new Opening GUID; both candidate outputs had exactly one. This collision is **not the requested slab host**. No authored geometry, scorer, criterion or report was modified afterward. A physical slab through-cut is confirmed, but **the original author flags an additional space collision**; therefore the result is not overall clash-free BIM validity.

## Scientific scope and denominator

- Preserve original **45** original tasks, 15 CREATE, 15 UPDATE, 15 DELETE, no deletion/reselection or redefinition to boost results.
- The previous **11/45 developer witness native-IFC byte-equal** cases remain **11**, unchanged. No new whole IFC byte equality is established.
- Distinct original CREATE tasks with task-specific developer-written D0/I0 **meaningful native geometry/relationship paired evidence** now **5/15**: `test_04` Column, `test_02` Slab, `test_05` Wall, `test_01` hosted Door, and `test_03` hosted Slab Opening. **10/15 remain UNKNOWN under that same paired criterion**, not proven unsupported/failures.
- Original45 full task-relevant model-visible **information read parity proven 0/45**, full IFC **native edit/write parity proven 0/45**, real matched LLM D/I trials **0**, new paid LLM inference **0**. Developer-authored D0 vs I0 equivalence cannot estimate a causal XML vs Python LLM performance difference.
- Original source mm↔metre workbench conversions may alter native STEP unit assignment representation. Though original Root identity and all unaffected product world meshes are preserved, this experiment does **not** demonstrate whole-source IFC STEP-byte losslessness, material/property/type/quantity parity, complete building collision safety, generalized Slab operations or equal two-arm model tool access.

## Repeat independently

From v0.36 isolated worktree with original two Git-pinned upstream repositories and the preexisting IfcOpenShell/geometry venv, no API provider or Docker:

    $base='D:\\문서\\D__1_Projects\\202611'
    $py=Join-Path $base 'bim-markup-bench\\.venv\\Scripts\\python.exe'
    & $py -m unittest -q tests.test_bibimbap_v036_original_slab_opening_pair
    & $py -m tools.audit_bibimbap_v036_original_slab_opening_pair --author (Join-Path $base 'bibimbap-author-upstream') --data (Join-Path $base 'bibimbap-author-data')

The optional `--write NEW_REPORT_PATH` flag creates a new report **exclusively** with `xb`, never overwrites existing frozen evidence.

### Verification

New focused positive and negative tests: **32/32 PASS**, 29.390s. They include genuine original I0 and D0 native outputs, missing void relation, mislocated opening, wrong cut size, source IFC hash drift, default schema/binder rejection, explicitly authorized v0.8 acceptance, unknown schema-path rejection, extra object and mixed edit rejection, wrong host, and original scorer fraud rejection. **Selected 20-module non-Docker multi-version regression: 410 tests, 406 passed / 4 skipped / 0 failed**, 196.610s. This includes default XML parser and semantic graph, existing v0.5–v0.7 geometry/create/update/delete, frozen v0.20–v0.36 original evidence, and historical Wall/Door/Opening regression. This is **not a whole repository or Docker-worker suite**. The preexisting incompatible historical `test_hosted_door_delete_runtime` frozen pilot manifest case was excluded rather than mutating the older fixture.

### Next gates

Inspect the non-full author collision subcheck separately and disclose its actual evidence without adjusting the frozen original score or source-only writer choices. Continue original CREATE classes and original45 source/view-role/capability parity audits; restore nondestructive original isolated execution prerequisites separately before any matched LLM D/I trial. Old pilot-manifest-pinned hosted-door DELETE tests have a historical manifest incompatibility with current branch; do not rewrite the old manifest or misreport those older unrelated tests as passing.

### Additional source STEP accounting (read-only, after report freeze)

The original public native source contains **3,138 STEP entities**. Two newly created separate source-derived candidates each contain **3,156 STEP entities**. In **both D0 and I0**, read-only original STEP-ID comparison found **one original `IfcSIUnit` record no longer present** and **one `IfcUnitAssignment` record changed**, with **no other original STEP IDs missing/altered under this exact original-ID textual check**. The original source itself remains unchanged. These changes are consistent with millimetre→metre→millimetre normalization, but do not establish its exclusive cause or guarantee arbitrary STEP metadata preservation in other scenes. Both native output file byte streams remain different and there is **no claim of full lossless native IFC equivalence**.
