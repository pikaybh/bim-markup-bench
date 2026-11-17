# BIBIMBAP v0.37 — Live original CREATE-10 eligibility, source-role and write-path gates

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/189
**Stack parent:** v0.36 Draft PR https://github.com/pikaybh/bim-markup-bench/pull/188, Git HEAD `ca60e56a0a4fca331a093cbda2dc2074bc140ade`
**Evidence type:** actual original-public IFC and current **matched25 XML session** offline authoring-path *diagnostics*. Neither original task solution, original benchmark score, independent I0, full source-equivalence proof, nor actual matched model comparison.

## Scientific boundary and actual execution

The original public BIBIMBAP denominator is unchanged: **45 tasks = 15 CREATE + 15 UPDATE + 15 DELETE**. Previously completed original CREATE task-specific developer-authored semantic D0/I0 cases are exactly `test_01` through `test_05` (5/15), including v0.36 Slab Opening with original author score 0.916675 in both independently written arms and a reported source-space collision. **The other 10 original CREATE cases were never thereby scored or proven unsupported.**

v0.37 runs all **10** previously unpaired source IFC files through the **actual, current `XmlSourceEditSession`** used by the future matched 25-tool protocol. Input hashes and the original author/data Git revisions are required to match the previous frozen public-input evidence. Input SHA, original IFC4X3/IFC2X3/IFC4 class/unit inventory and all referenced public GUID classes are independently inspected with IfcOpenShell *read-only*; no original author evaluator, hidden solution, private GT, model provider, Docker worker or billing invoked.

For each source admitted by the XML session, the audit independently parses the actual **model-visible complete XML** to cross-reference original native IFC product GUIDs (not a hypothetical comprehensive BIM view), then submits exactly one newly authored complete XML document with a **generic new Wall, Column or Slab at fixed harmless illustrative numeric parameters**. These numbers are **not** solutions to the original topology/spatial instructions. Every temporary output and copied input lives in a unique deleted scratch location; hashes of original IFC files are rechecked after the probe. The current native compiler and experimental versioned standalone compilers have different scopes; newer developer-only v0.2–v0.8 slices are **not** silently made available in the matched model host.

All previous v0.31–v0.36 report SHAs are pinned and read-only, alongside the earlier v0.22 actual 45 public-question/source SHA inventory. Any drift, duplicate, missing task, source schema change, replay mismatch or source mutation **fails closed**. This is a prospective technical diagnostic, **not a rerun or reinterpretation of original graded LLM trials**.

## Directly reproduced live results, including actual writer probe

| Original public CREATE task | Original native source | Current XML source admission | Current generic new-class native write | Actionable tier |
| --- | --- | --- | --- | --- |
| `geometry_test_01`: Slab atop four columns | IFC4X3, 4 IfcColumns | **Reject: unsupported IFC geometry** | Not attempted | P1 |
| `geometry_test_02`: Column at four-Wall centroid | IFC4X3, 4 IfcWalls all in XML | Admit | **Reject: generic Column unsupported in host** | P3 |
| `geometry_test_03`: relative north Wall Door | IFC2X3, IfcWallStandardCase | **Reject: non-IFC4X3** | Not attempted | P0 |
| `geometry_test_04`: Space left of named Column | IFC2X3, IfcColumn and IfcWallStandardCase | **Reject: non-IFC4X3** | Not attempted | P0 |
| `geometry_test_05`: absolute directional Wall | IFC4, hierarchy with 3 IfcProducts | **Reject: non-IFC4X3** | Not attempted | P0 |
| `topological_test_01`: enclose named room | IFC4X3, actual IfcSpace GUID referenced | Admit but **named IfcSpace absent from XML** | Generic standalone Wall IFC commits — **not** enclosure | P2 |
| `topological_test_02`: Column within four Walls | IFC4X3, 4 named IfcWalls all in XML | Admit | **Reject: generic Column unsupported in host** | P3 |
| `topological_test_03`: separate two named “rooms” | IFC4X3, 2 true IfcSpaces **not in XML** | Admit but room semantics incomplete | Generic standalone Wall IFC commits — **not** separation | P2 |
| `topological_test_04`: Slab closing four Walls | IFC4X3, 4 named IfcWalls all in XML | Admit | **Reject: generic Slab unsupported in host** | P3 |
| `topological_test_05`: Door connecting interior to outside | IFC4X3, 7 IfcWalls | **Reject: unsupported IFC geometry** | Not attempted | P1 |

**Exact totals:** 10/10 original public pending CREATE cases interrogated; **5** XML source-admitted, **3** schema-rejected, **2** actual projection-rejected; among the 5 admitted, **2 generic Wall commits** and **3 unsupported Column/Slab generic write rejections**. All ten original IFCs remain immutable. Neither generic Wall success is an original topology success.

### Critical independently established public-source inconsistency

The published original `topological_test_03` task explicitly asks for a wall “that separates the rooms with the ids …”, naming two specific GUIDs. **The named GUIDs actually identify two `IfcWall` products, not `IfcSpace`**, when opened from the pinned original IFC source. The IFC separately contains **two native IfcSpace products**, both omitted from the currently projected XML. Thus *the public wording and the literal IFC object classes disagree* and the current direct XML information needed to resolve actual rooms is absent. Record this as an **input-semantic interpretation and exposure risk**, not an inferred model failure or a license to alter the public task or the author evaluator.

In `topological_test_01`, the named GUID **is** a real `IfcSpace` but absent from XML, so even though a generic standalone Wall can be created, the model cannot directly inspect the task's referenced room in its current editable XML source. A separate read-only reference catalog existed earlier in v0.13, but it **does not make the current matched model host full XML source-equivalent**, nor does it supply a general native writer.

The original source file called `empty.ifc` for `geometry_test_05` is **not literally an entity-free IFC**: it is native **IFC4** with a Building, BuildingStorey and Site (3 IfcProducts). Avoid inferring a free-floating task or a schema normalization shortcut from its filename.

## Prioritized engineering queue (one mutually exclusive first blocker per task)

**P0 — Actual source schema rejection (3):** `geometry_test_03`, `geometry_test_04`, `geometry_test_05`. Version the XML authoring admission explicitly for actual IFC2X3/IFC4 original millimetre sources; preserve original root identities, native IFC schema, units, relationships, and author scorer input. A previous **read-only** legacy catalog does **not** prove a safe native CREATE compiler or a matched LLM writer. Do not silently upconvert or flatten IFC schema.

**P1 — Actual IFC geometry projection rejection (2):** `geometry_test_01`, `topological_test_05`. Diagnose original unsupported geometry non-destructively, provide source-backed opaque geometry and reference relations if needed, and verify exact visible public column/wall/host facts. Do not turn arbitrary complex geometry into fake editable rectangles to pass an XML projection.

**P2 — Required room facts missing / public object-class mismatch (2):** `topological_test_01`, `topological_test_03`. Establish faithful source-derived IfcSpace/room geometry and boundary visibility with independent native checks. For the two “room IDs” that actually name IfcWalls, flag benchmark ambiguity and use an **explicit prospective interpretation policy** before any LLM runs; never alter original public questions, GT or scorer post-score.

**P3 — Input admitted, but current native authoring host lacks generic CREATE class (3):** `geometry_test_02`, `topological_test_02`, `topological_test_04`. Implement explicit verified whole-state XML Column/Slab CREATE dispatch **in the current model-facing host** only after safe preflight/source-role checks; keep trusted IFC generation outside the XML model, preserve unrelated native IFC and add a matched imperative I baseline. Earlier developer-only experimental Column/Slab modules do not establish live host support. Column centroid and slab-closing geometry remain separately task-specific and underdetermined until independently verified.

The order is diagnostic severity (hard input barriers first), **not** an observed error rate, grade, economic estimate, feature completion forecast or preselected benchmark subset. Higher tiers have concrete blockers; lower tiers still have full task parity unproven.

## Frozen evidence and reproducibility

- Main auditor: `tools/audit_bibimbap_v037_remaining_create_live_gates.py`.
- Focused regression: `tests/test_bibimbap_v037_remaining_create_live_gates.py`; validates original 45/15/10 population, frozen SHA ancestry, exact old question hashes, complete original 10 source files, actual admitted/rejected host and native generic-write outcomes, original-IFC immutability, public room GUID mismatch, bounds and no privileged score/LLM calls. Includes live rerun and byte-identical report comparison plus negative mutation/tampering tests.
- Frozen JSON report: `reports/bibimbap_v037_original10_create_live_source_and_writer_gates_20261117.json`, SHA256 **`33d99e6fb624e6a5e89dc301791c269bd5ca7d2666d8618fc67379664938501f`**.
- The report records source SHA, public-question SHA and bounded named source GUID/class summaries; it does **not** commit native IFC data, generated IFC bytes, hidden GT, original grader code or model prompts.
- A first replay after adding the v0.22 per-question SHA gate reproduced the **exact frozen 33d99e… JSON byte sequence**; the report was **not** overwritten.
- New tests **31/31 PASS** in 3.967s (focused). **Selected 21-module non-Docker multi-version regression: 441 total tests, 437 passed, 4 skipped, 0 failed, 198.809s**, verified from `results/v037_selected_nondocker_regression_20261117.log` with process exit code 0. This includes prior v0.20–v0.36 control regressions and all 31 new v0.37 tests; it is not a complete repository or Docker-backed trial suite.

Run locally in the new isolated worktree with existing original author/data input repositories and the already-installed research Python environment:

    $base='D:\\문서\\D__1_Projects\\202611'
    $py=Join-Path $base 'bim-markup-bench\\.venv\\Scripts\\python.exe'
    & $py -m tools.audit_bibimbap_v037_remaining_create_live_gates --author (Join-Path $base 'bibimbap-author-upstream') --data (Join-Path $base 'bibimbap-author-data')
    & $py -m unittest -q tests.test_bibimbap_v037_remaining_create_live_gates

`--write NEW_OUTPUT_PATH` creates a uniquely named report with **exclusive `xb`**; never overwrite the committed original evidence.

## Explicit non-claims

**0 original45 complete task-relevant model-facing read-information equivalence proven; 0 original45 complete native write-capability parity proven; 0 matched real LLM XML-vs-Python trials; 0 new paid inference; 0 original-author grades in v0.37; 0 Docker executions.** The old 11 original developer native byte-equal witnesses and 5 original CREATE task-specific semantic pairs remain unchanged. These 10 cases are not model “failures,” and the 5 actual session admissions or 2 generic Wall writes are not task “successes.” No causal model performance conclusion is authorized.
