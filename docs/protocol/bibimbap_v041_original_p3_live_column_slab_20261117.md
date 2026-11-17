# v0.41 P3 — original CREATE Column/Slab via actual whole-declarative XML model host

**Pre-registered issue:** https://github.com/pikaybh/bim-markup-bench/issues/197
**Exact parent:** v0.40 [Draft PR #196](https://github.com/pikaybh/bim-markup-bench/pull/196), head `95371fd3c7b1d1cbbcfd09a77569c4e815a1c0bd`
**Independent original-public P3 source SHA and question SHA:** pinned in issue, source-locked code and frozen audit.
**FROZEN machine report:** `reports/bibimbap_v041_original_p3_column_slab_live_source_and_native_writer_20261117.json` SHA256 **`370a70de43399f77fc57f22b4669ca15b5b63204005b6ddb7414c923bcde0b1e`** (exclusive `xb`, full byte-exact replay verified).

## Scope, real source inventories, and original-public semantics

Original benchmark remains **45 original public tasks, including 15 CREATE**, 15 UPDATE, 15 DELETE, no substitutions. Only five *earlier* original CREATE tasks have fully independent task-specific developer D0/I0 semantic native controls. **The present three developer-authored objects are *not* task-specific output-pair controls or original-task solutions**: no matched Python I0 arm was independently authored or graded for these three.

The public questions and native source SHA256 values were pinned and compared against the frozen v0.37 and v0.40 reports **before** new code was developed.

| Original public CREATE | Public question's required action | Source IFC4X3/mm SHA256 | Source native IFC counts | Actually typed model-visible original XML |
| --- | --- | --- | --- | --- |
| `geometry_test_02` | Create Column at centroid of original four walls | `58833e0bdf80e2207b8c221fc8195e5411f9f94e0d7f1cb39633b3c447eb4767` | 68 IfcRoots, 8 IfcProducts, **4 IfcWalls / 0 IfcSlabs** | 4 Walls, 2 Storeys |
| `topological_test_02` | Insert Column inside original four *specified* wall GUIDs | `8f1d9e885603f8680cb79f2a373fa36b4ecd52634ac920f2ec53c60ac465ad72` | 89 IfcRoots, 10 IfcProducts, **4 IfcWalls / 2 existing IfcSlabs** | 4 Walls, 2 Storeys; **existing Slabs absent** |
| `topological_test_04` | Create Slab closing original four specified wall GUIDs | `29cd44b72639ba9573aa1698a4efab4adcfbc5461c19dd85259e6a9505d303e5` | 108 IfcRoots, 12 IfcProducts, **7 IfcWalls / 1 existing IfcSlab** | 7 Walls, 2 Storeys; **existing Slab absent** |

All original IFC source native schema `IFC4X3`, native units **mm**, explicit source `IfcRelSpaceBoundary` count **0**. All original source Wall GUIDs in the three original questions are exposed as true typed Wall identifiers in XML. The original existing **3 IfcSlabs** across the two topological tasks are still **not represented in the XML read input**, even though the native Python arm can inspect them. This is **unresolved source-information-access parity**. We do not infer or fabricate room/adjacency/topology relations or claim full IFC STEP preservation.

## P3 feature: add one real physical Column or Slab through the existing model tool surface

The original XSD `spec/toy_markup_v0.xsd` has always described the declarative `Column` and `Slab` tags and their native-storey references. Prior to v0.41, the actual experiment model-facing `submit_building_xml` uses a trusted Wall-only native mutator (except special prior opt-in slices), **so nominally XSD-valid new Column/Slab additions failed**. v0.41 closes that exact native-authoring path without modifying the old XSD or default behavior.

The model tool surface is **unchanged**: `read_building_xml` returns the complete editable source XML, and `submit_building_xml` submits the **entire replacement XML text**, not a patch or command. Model-side Python snippets, helper actions, IFC APIs or direct mutators are never exposed. The new source-specific flag is:

```python
XmlSourceEditSession(
    exact_original_public_ifc_mm, isolated_new_session_dir,
    experimental_original_p3_v041=True,
)
```

The flag is **opt-in only**, mutually exclusive with v0.38 legacy, v0.39 complex, and v0.40 native Room experiments. It permits exactly the three original-public IFC SHA256 values and verified IFC4X3/mm source inventories; otherwise fail closed. No other source may inherit this experimental writer. The **model's read XML is literally byte-for-byte identical to the existing default model-visible source XML** for the same original input; no new hint/answer or privileged source metadata was injected.

The trusted external `src/runtime/experimental_v41_p3_column_slab.py` builds the exact original projected source XML, parses source and submitted full documents through the **unchanged pinned default v0.1 XSD and secure parser**, binds original source identities to IFC GUIDs, computes semantic graph diff, and permits **exactly one `deterministic_new` `Column`** for the first two source files or **one `Slab`** for the third. It forbids removed or altered original elements, arbitrary new GUIDs, extra relations, wrong class, extra new object, invalid or foreign Storey reference, physically degenerate/out-of-bounds dimensions and unrecognized attributes.

Actual native writer operates **only after source/schema/semantic preflight**, with the source cloned into a new unique metre-unit scratch candidate. It uses the existing genuine source Body `MODEL_VIEW` context, an `IfcRectangleProfileDef` swept solid, exact horizontal box geometry, an original native Storey via `IfcRelContainedInSpatialStructure`, and a deterministic IFC GlobalId assigned externally. After native candidate writing, the model-facing host reconverts a **separate candidate** to the source's original millimetres and independently verifies it **before accepting the updated XML/IFC as the last-valid state**. A rejected edit preserves the previous successful file and model state.

The writer can accept revisions to the same one new element in a later complete-XML submission. It does not accumulate prior successful native writes into its working original source, does not accept multiple new objects, and does not modify the original public source IFC.

## Actual model-facing execution, not pretend IFC representation

The developer submitted ONE deliberately **non-task-answer** object at x=8m,y=0,z=0 through actual `read_building_xml` → `submit_building_xml` sessions for EACH original-public input. The demonstration geometry intentionally lies outside the original four-walled source enclosure, so it must not be evaluated as correct for the benchmark's Column-centroid / inner-space / enclosing-Slab questions. Its purpose is **physical writer capability and original source preservation**.

| Real original P3 source | New actual native product and world bbox | Original native source preserved | Original physical triangle faces checked |
| --- | --- | --- | --- |
| `geometry_test_02` | `IfcColumn` physical bbox **(8,0,0)–(8.4,0.3,2.5)m**, 12 triangles | **68 original Root IDs**, 8 original products; 4 Walls | 4 shaped products, **48 triangles** |
| `topological_test_02` | `IfcColumn`, same independent physical bbox, 12 triangles | **89 original Root IDs**, 10 original products; **2 opaque old Slabs retained** | 6 shaped products, **72 triangles**, including all original Slabs |
| `topological_test_04` | `IfcSlab` physical bbox **(8,0,0)–(9.2,1.5,0.2)m**, 12 triangles | **108 original Root IDs**, 12 original products; **1 opaque old Slab retained** | 8 shaped products, **96 triangles**, including original Slab |

**Independent oracle** `tools/bibimbap_v041_p3_native_oracle.py` **does not import the v0.41 compiler or original published grader**. It reopens the **actual original IFC4X3/mm source and separately saved output IFC4X3/mm**; verifies original Root GUID/class/Name/Description, every original IfcProduct identity, every original physical world mesh's canonical vertex and planar faces (including the three source Slabs hidden from XML), existing original spatial and connection edges, no fake `IfcRelSpaceBoundary`, exactly one new native source-Storey containment relation, exactly one target native IfcColumn/IfcSlab with visible swept solid, and actual world-bbox dimensions matching the user-authored declarative XML values.

An independently tampered output with an **original opaque Slab deleted**, newly created Column physically translated, or new Slab representation removed correctly fails the oracle. This is stricter than checking `IfcColumn` / `IfcSlab` string presence in STEP files. It is **not** full STEP entity/metadata parity, test-author geometric task grading or a matched independent Python result.

## Scientific and security constraints

A separately frozen original-public baseline remains **45 ITT / 15 CREATE**; previous **5/15** task-specific developer D0/I0 semantic pairs are unchanged; **10/15** other CREATE cases still lack independent task-specific developer D0/I0 pairs. This P3 step adds *3 generic XML-host native writer reachability proofs*—**not three newly matched D0/I0 task solutions**. No task-specific original grader/evaluator called, no hidden GT read, no model providers, no Docker worker executions, no source data edits, no Xim product repository edits.

**0 original-task-relevant complete matched D/I model-visible source parity proofs**, **0 complete matched D/I native-write capability parity proofs**, and **0 actual matched LLM XML-versus-Python trials** as of this checkpoint. Since XML still omits opaque pre-existing native Slabs, do not claim fair equal-read exposure on topological source cases. The original questions, source IFCs and results are not edited to mask this limitation.

Tests include wrong source SHA, modified original source with valid schema, source unit drift, opt-in conflicts, original Wall mutation/removal/GUID spoof, arbitrary new GUID, duplicate and wrong-class new object, foreign or missing Storey reference, schema invalid attributes, zero/negative/oversized/nonfinite geometry, malicious XML DTD/XXE, failed edit after a successful commit preserving previous XML and native IFC, legitimate one-object revised second submit, altered output native original opaque Slab/new Column bbox/new Slab geometry, original-question SHA poisoning, duplicate original public task ID, exclusive frozen report writer and full byte-exact re-audit. Historical source-code-identity frozen tests remain scoped to their own original checkpoints rather than misreported against deliberately newer host source.

### Reproduce (Windows PowerShell, isolated Worktree)

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
& $py -m tools.audit_bibimbap_v041_p3_live_column_slab --author (Join-Path $base 'bibimbap-author-upstream') --data (Join-Path $base 'bibimbap-author-data')
& $py -m unittest -q tests.test_bibimbap_v041_p3_model_facing_column_slab
```

**Focused v0.41 verification: 48/48 PASS**, process exit 0, 8.041s, ignored local log `results/v041_p3_focused_original_three_native_20261117.log`. **Selected 25-module compatible multi-checkpoint non-Docker regression: 609 total / 605 PASS / 4 SKIP / 0 FAIL**, **238.985s**, verified process exit **0**, ignored local log `results/v041_selected_nondocker_multiversion_regression_20261117.log`. This includes previous v0.38–v0.40 host routes and the new v0.41 physical IFC roundtrip, but does **not** imply a whole-repository, Docker, paid-model or full original45 equal-parity test run.

**Next highest-value work** is source-relevant native existing Slab visibility for the two topological P3 cases (without inventing editable axis-aligned geometry for unsupported source Slabs), then rigorous **matched-model D0/I0 equal-information/read access and equal-native-write-authority** gates before allowing real original benchmark LLM D/I comparisons. Once those are genuinely equivalent, preregister matched model, prompting, seed, cost/time and original author scoring before claiming a causal XML-vs-Python finding.
