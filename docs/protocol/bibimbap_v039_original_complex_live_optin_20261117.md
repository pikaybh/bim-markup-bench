# BIBIMBAP v0.39 — P1 original IFC4X3 mapped columns and clipped walls

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/193
**Stacked parent:** v0.38 Issue #191 / Draft PR #192, commit `769b4013d1af1c0abce4f24d3305a231854fc685`
**Frozen machine evidence:** `reports/bibimbap_v039_original_p1_complex_native_xml_live_20261117.json`, SHA256 `3d7a5e642b22b024c938d5c1f712c0eaab8e11ffb6fbe274b0c90ddef074b09a`.

## Scope, question, and scientific design

The original BIBIMBAP population remains **45 original published tasks: CREATE 15, UPDATE 15, DELETE 15**. Exactly **5 original CREATE tasks** had prior *task-specific developer-authored* D0/I0 semantic witness pairs. **10 original CREATE tasks still do not**. This v0.39 implementation is a **separate original input/physical writer-gate**: two previously failing native source inputs can now be read and a small, illustrative added object can be committed through the same model-facing whole-XML session tool interface with explicit opt-in. It does **not** claim two additional task-specific D0/I0 answers, does not change the original question or its grader, and does not count any actual scored LLM sample.

v0.37 frozen evidence identified two **P1** original native **IFC4X3 / millimetre** sources that fail the default `XmlSourceEditSession` at original geometry projection with `UnsupportedIFCGeometry`. No hidden ground truth or original author evaluator was needed to inspect that failure. The actual public source IFC bytes were independently inspected before implementation:

| Original public task | Original question, abbreviated | Actual source geometry | Original IFC SHA256 |
| --- | --- | --- | --- |
| `geometry_test_01` | Create a 0.2m-thick slab at the upper outer edges of four columns | **4 original IfcColumn** using actual IFC **MappedRepresentation / IfcMappedItem**, at four 3m exterior corner bounds | `d7a0c0bda9572787b5b8e7a57b48f8157d898a9f444ac28978e9f9b9a8ff9702` |
| `topological_test_05` | Create a Door connecting an interior to outdoor through a pre-existing Wall | **7 original IfcWall** with `IfcBooleanClippingResult`, 2 original IfcSlabs, original external and internal Walls | `c0e0019d7224185d5872b80bdd3652da2bc960b819c1d8c0dd03b213b14847ca` |

The original four mapped columns have physical bounds (x and y each near 0 or 3m), z 0–3m; the native column definition names reference Revit types but **the actual IFC mesh, not its display name**, is authoritative. In `topological_test_05`, the 7 original clipped Walls, including the outside host Wall, are physically represented as IFC Boolean clipping solids, not plain editable extrusion rectangles.

## Implementation — the source remains authoritative, never simplified

A **new opt-in** `XmlSourceEditSession(..., experimental_original_complex_v039=True)` applies to **only** those two exact original file SHA256s, both actual IFC4X3 with original millimetres. This remains **mutually exclusive** with v0.38 experimental legacy IFC2X3/IFC4 admission. Without this keyword, the standard host continues to use the same previously frozen IFC4X3 projection and **still refuses** these two complex original sources. The future matched-25 paid-run CLI remains unchanged and does **not** automatically enable the new opt-in. No model provider, Docker or arbitrary Python executed in this v0.39 experiment.

The new XSD namespace `urn:bim-markup-bench:complex-native:v0.39` describes a complete declarative `Building` document, containing:

- **Immutable `OriginalNativeSource`:** original IFC product GUID, IFC class, exact source-owned Name, original **MappedRepresentation** / **Clipping** type, source-native World mesh triangle SHA, canonical world vertex SHA, world bounding envelope in SI metres and original GUID-to-GUID explicit spatial/void/fill relationships. This remains a bounded reference view; the entire IFC is **not** serialized losslessly into XML. Every original source Product and catalog relation is immutable and a mutation makes the compiler fail closed.
- **`Elements`:** only a single bounded new `IfcSlab`, or exactly one new `IfcOpeningElement` plus `IfcDoor` referencing one original source Wall GUID and each other by declarative ID. No IFC mutator methods, programmatic API calls, commands, free-form executable code or rewriting source geometry are exposed to the agent.

The trusted compiler rechecks the exact source SHA, schema, 1m normalized source units and immutable canonical original catalog. It creates the new object in a separate IFC4X3 clone, assigns its deterministic original-source-derived GUID and trusted native shape/relations, restores the result **metres → original millimetres**, and then invokes a **separate restored-native-mm physical oracle before a model-facing success is committed**. New spatial relation GUIDs and OwnerHistory timestamps are anchored to the public original normalized IFC to make repeated fixed-input output IFC **byte-stable** across runs. Old spatial membership order is retained even if IfcOpenShell API set operations reorder it.

## Actual illustrative model-facing tool calls

Two original public source IFCs were separately opened in new temporary sessions. `read_building_xml` returned the complete partial XML source overlay, then the developer independently authored a **non-benchmark-answer** complete XML replacement and invoked `submit_building_xml`. Both actual tool calls returned committed status. These are **developer source controls, not LLM completions or scored original benchmark answers**.

**`geometry_test_01`:** declaratively added a small representative slab: x=1,y=1,z=3, length=1, depth=1, thickness=0.2m, under original L2 Storey. Its physical new native IfcSlab bounds are **(1,1,3) to (2,2,3.2) metres**. It is **not** the task's requested four-column full exterior slab. The independent oracle verified all **63 original IfcRoot identities**, **8 original Products**, all source relationship edges, and original **4 mapped column world meshes / 48 original physical triangles**. The new IFC4X3 native-mm candidate SHA256 is `068723a7ab0752f4009dd8a3a83ac4ef1f6379405797110dbd650b35d869fb72`.

**`topological_test_05`:** declared an illustrative 1m x 2m Door plus new Opening on the original south clipped Wall `3Vyqk8cSj8TOuAk6zHUwAc`, at world centre (3,.1), sill=0m. The source was verified as a true, initially unvoided clipped Wall with adequate physical extent. The new opening's actual native world bounds are **(2.5,-0.1,0) to (3.5,0.3,2)** metres and the Door has **(2.5,0.06,0) to (3.5,0.14,2)** metres. A real Boolean void in the original clipped Wall increases its physical triangulation **12→28 triangles** without changing its external bounding envelope; exact native `IfcRelVoidsElement` and `IfcRelFillsElement` link the original source Wall, new opening and Door. The independent restored-native oracle verified all **116 old original IfcRoot identities**, **13 original Products**, original relations and unchanged **8 source physical solids / 96 triangles** excluding the declared host Wall, as well as native Door dimensions and original Storey containment. This example alone does **not** prove the benchmark's semantic condition that indoor and outdoor spaces are genuinely connected under a task-independent topological oracle. Its candidate native-mm SHA256 is `59344c62e813ce08929871ac29eb18f20ed4bc1e883911579261b9d23c9f8d19`.

Repeated compilation from the same frozen public input and same XML produced **byte-identical new native output IFCs on both examples**, verified by paired local SHA checks. This does not mean the candidates are byte-identical to their *original source* IFC; they intentionally add new native objects.

## Safety properties, independently tested rejection cases

The independent physical oracle `tools/bibimbap_v039_complex_native_oracle.py` knows only the original source, externally declared complete XML and restored native candidate; it does **not** import or execute the new trusted writer code. It compares original Root GUID/class/Name/Description, product inventory and native relationship edges; non-host original mesh world vertices and physical planar faces; the single declared original clipped Wall's real Boolean cut and unchanged exterior envelope; all new native physical product geometry, native unit/schema, Door opening/fill and Storey edges. A missing new physical representation, moved mapped column, changed original metadata, missing void, or altered native schema cannot silently pass. This is bounded original-product semantic preservation, **not** proof of full native STEP entity-by-entity metadata equivalence or complete IFC model parity.

The experimental edit binder/host refuses new original-source object edits or omission, changed root source hashes or catalog hashes, source schema/units spoofing, malformed XML/DTD/XXE, executable command nodes/processing instructions, duplicate or extra elements, missing or forged Storey or original Wall GUID, Door/Opening size mismatch, Door outside the physical host Wall, outside true original Wall thickness/axis, or opening above real clipped Wall height. The tool state remains unchanged after rejected edits; a previous valid IFC remains available for a later correction.

## Reproducibility and limitations

Frozen population report: `reports/bibimbap_v037_original10_create_live_source_and_writer_gates_20261117.json`, SHA256 `33d99e6fb624e6a5e89dc301791c269bd5ca7d2666d8618fc67379664938501f`; prior v0.38 P0 report SHA `c04448087528aa07b9cee64830defe61e5b3a7836fc4cae8f073dac4bfc7aad4`. New audit checks both hashes, original author Git SHA, original data Git SHA and all unchanged original question + IFC SHAs.

Run from `D:\문서\D__1_Projects\202611\bim-markup-bench-issue193-original-complex-live-xml` with the private research Python environment:

```powershell
$base='D:\문서\D__1_Projects\202611'
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
& $py -m tools.audit_bibimbap_v039_original_complex_host --author (Join-Path $base 'bibimbap-author-upstream') --data (Join-Path $base 'bibimbap-author-data')
& $py -m unittest -q tests.test_bibimbap_v039_original_complex_host
```

Machine evidence `--write NEW_UNUSED_FILE.json` uses exclusive file creation, never overwrites the frozen report. Focused v0.39 actual host test run: **47/47 PASS**, 9.000s, process exit 0; ignored Windows worktree log `results/v039_focused_final_20261117.log`. The v0.39 **selected 23-module multi-version non-Docker regression passed 516 total tests: 512 PASS / 4 SKIP / 0 FAIL**, 276.956s, process exit 0, with Windows research Worktree log `results/v039_selected_nondocker_regression_20261117.log`. It included the v0.39 47 cases, v0.38 previous 36, v0.8 legacy native tests, and selected earlier tests; it is **not** the whole repository suite, Docker Python sandbox or a scored model experiment. The v0.38 historical selected regression separately passed 469 (465 PASS, 4 SKIP) on its own version. The old v0.37 file-hash-locked host tests belong to their original frozen worktree and are not legitimate same-file-identity assertions against modified v0.39 code.

**Scientific inference boundary:** Original public denominator 45 with 15 CREATE, 10 still lacking task-specific developer D0/I0 parity. P1 original schema/complex geometry projection admission 2/2 in explicitly opted-in sessions; actual physical native writes 2/2; default source admissions 0/2. **0/45 full model-visible original source information parity proved. 0/45 full task-relevant native writer parity proved. 0 matched real LLM D/I trials. 0 new task-specific author scores. 0 new paid provider requests.** No causally valid XML vs Python model-performance conclusion from illustrative controls.

**Next highest original priorities:** P2 original `IfcSpace` visibility and room-named GUID vs actual IfcWall class ambiguity. Then P3 generic matched25 host Column/Slab write capabilities and comprehensive equal-facts/equal-write parity. None are silently counted as addressed by this P1 patch.
