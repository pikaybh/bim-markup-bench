# v0.43 — All 45 original BIBIMBAP native IFC vs actual XML-model read-information parity audit

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/201
**Frozen base:** v0.42 [Draft PR #200](https://github.com/pikaybh/bim-markup-bench/pull/200), exact HEAD `32925c0cccce17b5a14c7ba904e04b195dc40d16`.
**Author/source:** Original author `667004e16bd38fd7d538bcee56191465429fd975`, original public IFC/question data `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca` (both clean and unmodified), exact public CSV SHA256 `21c07f08c923cdb748255d7960535bab05e2887e4d093d64f87f76ff6d6d100b`.
**Previously frozen v0.42 final report:** SHA256 `f883dfb095746ceebbaa9f718e5355c61dbb2a356387b7882b400036cdf1b20e`.
**v0.43 frozen audit:** `reports/bibimbap_v043_original45_native_XML_source_read_parity_20261117.json`, SHA256 **`eb05633d152b1ff15e4fdd888bb62924b31b126f6cddd05fb23e54fce3ef8dbf`**.

## Executive scientific finding

**The present original BIBIMBAP XML and Python source reads are not equal-information conditions.** Simply returning XML or exposing object GUIDs is not complete equality of source state, native relationships, materials, property names, placement structure, or edit authority. The measured gap is in the actual original-public inputs, not invented data or substituted tasks.

| Original public denominator or measured source | Independent finding |
| --- | ---: |
| Original public tasks | **45**: 15 CREATE + 15 UPDATE + 15 DELETE; 15 basic + 15 geometry + 15 topological |
| Distinct original-public immutable IFC byte hashes | **31 unique IFC files** (original basic tasks share one physical source across 15 tasks) |
| Source original IFC schema variants | **IFC2X3, IFC4, IFC4X3**; all original sources here use native mm, independently inspected |
| Actual default `XmlSourceEditSession.read_building_xml` model reads | **36/45 successful**, **9/45 unsupported backend**, not LLM failures |
| Research-only source-SHA opt-in read variants (v0.38–v0.42) | **41/45 successful**, **4/45 unsupported backend**, not activated by the default paid CLI |
| Distinct sources with successful best-available actual XML read | **27/31** |
| Original IFC `IfcProduct` instances across **31 distinct sources** | **480** |
| Original IFC `IfcRelationship` instances across **31 distinct sources** | **1,949** |
| Original IFC `IfcRelDefinesByProperties` instances across **31 distinct sources** | **1,227** |
| Original IFC `IfcRelAssociatesMaterial` instances across **31 distinct sources** | **153** |
| Original product GUIDs *not present as GUIDs anywhere* in best-available XML for **27 readable source files** | **121 / 433** |
| Original exact relationship GUIDs *not present as GUIDs anywhere* in best-available XML for **27 readable source files** | **1,743 / 1,757** |
| Readable sources with original material and property-set **name strings absent** | **27/27 each**; no dedicated native material/pset XML elements |
| Fully proven original45 equal-information XML/Python source reads | **0/45** |
| Fully proven original45 equal native write authority | **0/45** |
| Actual paid/model-matched LLM XML/Python comparisons | **0** |

The totals for 480 products, 1,949 relationships, 1,227 property links and 153 material links are **per-source instances over 31 unique source files**, not counts over 45 tasks. The 433 products and 1,757 relationships are restricted to **the 27 source files where the model-facing XML actually returned**. The discrepancy is not caused by double-counting the repeated original basic source.

**IMPORTANT semantic qualification:** 1,743 absent relationship **GUIDs** is *not* proof that every relationship's underlying semantic effect is absent. For example a declarative `Connects` relation or `level` reference may encode an approximate relation while omitting the source's original `IfcRelConnectsElements`/`IfcRelContainedInSpatialStructure` relationship identity and properties. The audit measures identity visibility directly and conservatively refuses to assume full semantic/STEP fidelity. Similarly an original material/property-set name missing from XML does not mean a model could not infer some geometric property; it proves the original native metadata values were not presented as explicit material or property-set names.

## How this was audited

1. Re-read **each of the exact 45 original public task entries** using the pinned original author public task loader. Verify the original question CSV file hash, all 45 per-task public question SHA256, each exact original native IFC source SHA256, all original task IDs, three CRUD/category groups, original Git HEADs and *clean working tree* state. Reject path escape and symlinked originals.
2. Deduplicate by **31 exact original IFC SHA256s**. Independently open every original IFC in local IfcOpenShell/Python: collect original IFC schema and unit, all IfcRoot/IfcProduct/IfcElement/IfcRelationship native GlobalIds and class counts, PropertySet and single property metadata, `IfcRelDefinesByProperties`, `IfcMaterial`, `IfcRelAssociatesMaterial`, `IfcLocalPlacement`, product ObjectPlacement and 3D Representation presence, original native Space/Slab identities and original relationship-class counts.
3. Actually instantiate the **current** `XmlSourceEditSession` in isolated throwaway directories, call the unchanged model-facing `read_building_xml` for every source under the **default exact runner**. For originally preregistered CREATE source hashes, additionally separately test the explicit opt-in research reader v0.38 legacy, v0.39 complex, v0.40 native Room, v0.41 P3 or v0.42 native Slab. Do **not** imply these are activated in the default `run_one_pair`; that runner currently calls `XmlSourceEditSession(original,folder)` without flags.
4. Compare returned XML bytes, original native source GUIDs and relationship GUIDs against actual `Building` XML node attribute values; inspect source native PropertySet/Material names for **literal** presence and dedicated XML material/pset markup; record missing native product/element classes and relation class counts, and whether source was actually unsupported, by task and by unique source SHA. No baseline Task XML is fabricated when the real tool rejects it. Real source IFC remains unmodified.
5. **No full native write authority or native binary STEP parity has been proven in this step.** Source `IfcLocalPlacement` and native representation presence are counted, but complete matrix/mesh equivalence is *not* inferred from an object's GUID, name or axis-aligned XML fields. The Python arm source inventory is a local read-only IfcOpenShell inspection, **not a Docker/paid-model Python execution**.

## Four original-public inputs still rejected on the best currently implemented XML reading path

These are all **UPDATE or DELETE**, not remaining CREATE:

- `geometry_test_14` — `UnsupportedIFCGeometry`
- `geometry_test_15` — `UnsupportedIFCGeometry`
- `topological_test_11` — `UnsupportedIFCGeometry`
- `topological_test_17` — `UnsupportedIFCGeometry`

This is **4/45 current backend failures after all existing source-locked research opt-ins**, not four model failures. The other 41 can return source XML only; their overall information parity is still not established. None of the source-locked experimental opt-ins is enabled automatically in the default provider benchmark.

## Threats to validity and boundaries

- **No tasks are substituted or regraded**: original 45 ITT, 15 CREATE, upstream original question/source/task/evaluator unchanged, 5/15 original CREATE developer D0/I0 task-specific semantic controls remain exactly five. v0.43 creates **zero** new original CREATE D0/I0 solution pairs.
- **Readability is not information equality**: even all 27 readable source files omit native metadata. A shared IfcProduct GUID is a reference to an object, not proof its full material, property, geometry, placement or native relationship context is present. Read-only source references from v0.40 and v0.42 are **not** edit permissions.
- **No fake causal claim**: a future LLM model may perform differently due to interface breadth, source fact availability, editing power, feedback or token allocation. An unmatched XML-vs-Python experiment would be a comparison of *entire tool bundles*, not a controlled direct-XML causal benefit. To claim a language/interface mechanism independently, preregister task-relevant matched source information, matching write authority, repetition, model/provider, seed, time/token/cost and identical original-native-oracle gating first.
- **No confidential grading leak**: the audit imports neither the original author grader nor hidden GT, makes zero model/provider calls, does not write native candidate IFC or generate task answers, and commits only bounded diagnostics/IDs without full public question text.
- **No retroactive reports**: v0.42 and all earlier frozen source reports remain byte-identical. The v0.43 report is created exclusively once with `xb` and independently rerun byte-for-byte. Every source SHA is immutable, including shared basic-model data.

## Reproduction, controls and next priority

From the isolated Windows research Worktree:

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'

& $py -m tools.audit_bibimbap_v043_original45_source_read_parity `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') --progress

& $py -m unittest -q tests.test_bibimbap_v043_original45_source_read_parity
```

**Completed verification results (actual exit codes, not inferred):** original-45 focused read-parity and negative test suite **53/53 PASS**, 10.178s, exit 0 (ignored local log `results/v043_original45_focused_final_20261117.log`). Selected **27-module compatible nondocker multiversion regression: 727 tests total / 723 PASS / 4 SKIP / 0 FAIL**, 285.758s, exit 0 (ignored local log `results/v043_selected_multiversion_nondocker_regression_20261117.log`). The latter includes preceding v0.38–v0.42 model-facing read/write/oracle tests; no claim of whole repository, Docker, paid-model or original author benchmark scoring coverage. Source manifest, previous v0.42 frozen report and new v0.43 report verified exact SHA and independent byte-exact live replay.

**Next priority**: choose one of two *explicitly preregistered* methodological routes instead of concealing the current confound. (A) Add sufficiently source-faithful, immutable read-only original native property/material/relation/placement evidence to actual XML model read while preserving native authority limits and safely completing those four source-geometry failures; then verify the exact task-relevant equal-read/equal-write capability gates. (B) Define a narrower **task-conditioned intersection** of source/operations available to *both* arms, retaining original public question and IFC unchanged but explicitly treating the comparison as interface bundles if the Python native arm stays unrestricted. In either case, original LLM scoring must not start on the unsupported/unmatched conditions, and claims must be calibrated to the actual experimental contrast.
