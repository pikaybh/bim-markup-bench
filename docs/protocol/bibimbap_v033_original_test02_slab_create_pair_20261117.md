# BIBIMBAP v0.33 — Original public `test_02` IfcSlab CREATE, independent I0/D0 control

**Issue:** [#181](https://github.com/pikaybh/bim-markup-bench/issues/181)
**Parent:** [Draft PR #180](https://github.com/pikaybh/bim-markup-bench/pull/180) at `b29ef537514754287c87609e888b9ad6e318901d`
**Status:** Verified **developer-authored native geometry/author-score parity**, not an actual matched model run, not native byte equality, and not full D/I source/capability parity.

## Protocol and provenance

The original BIBIMBAP public `test_02` requests a slab **10 by 5m, 20cm thick, with its bottom/plan center at (-30,0)**. We adopt the **previously frozen developer D0** interpretation rather than tuning after scores: world-space bottom bbox (-35,-2.5,0), top bbox (-25,2.5,0.2), existing original ground `L1` storey, native `IfcSlab.PredefinedType=FLOOR`. These are direct public-instruction-derived world coordinates. This one case is part of the unmodified original 45 (15 create, 15 update, 15 delete); the question set, original IFC file, benchmark author and grading code were **not modified**.

- Original author Git SHA: `667004e16bd38fd7d538bcee56191465429fd975`
- Original dataset Git SHA: `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`
- Actual original source: `basic_tasks.ifc`, IFC4X3 in native **millimetres**; SHA256 `9ef1235e49d5b0359c1d44fd95a7afad7755149362109ca8b875d0427dc487ca`
- Original question SHA256 `b11d1746b2a59a6b346bbcf643aa5ae738f6719d31babe9468ca8d90209592d3`
- Previous scoped whole-XML D0-only report `reports/bibimbap_v04_slab_developer_d0_20261113.json`, frozen SHA `98166dc3a6c606996a5f9bd43e3b0b26fb2852fb61e1c64ea1154aaefc630fec`
- v0.31 full-45 eligibility report SHA `d6680b3eadb5733be547c09ab8deed58dd48c7feaccbc3cb562b6e60b475c7dd`
- v0.32 independent original Create Column control SHA `65cd592b83b06ac161ff420982cb2f3378e850613f4645419690e06764987b2b`

## Actual execution sequence and isolation

1. Verify pinned 45 public tasks, question/source SHA, unchanged source Git revisions and SHA-pinned prior reports.
2. Use a **new independently authored imperative Python/IfcOpenShell I0 script** `tools/bibimbap_v033_original_slab_i0.py`, which imports **no declarative XML system, native D0 compiler, grader, hidden source, or answer key**. Open the untouched original mm IFC, normalize a *separate in-memory copy* to metres, create a true `IfcSlab` with rectangle profile and extruded depth, place it at the public footprint, contain it in original `L1`, then convert a separate scratch result back to original millimetres.
3. **Before any D0 compiler runs**, re-open the I0 actual IFC and validate it with a separate native-only read oracle. Assert precisely one new physical `IfcSlab FLOOR`, world bbox, native 200mm extrusion depth, existing spatial containment extended by one member only, and original scene preservation.
4. Create **whole declarative XML** from the same original native IFC under previously committed `src.runtime.experimental_v4_projection`; add a single `Slab` element (not a command or `<Create>` opcode). Call existing **trusted native** `compile_declarative_xml_v4` and save D0 as separate mm IFC. Re-run **the exact same independent native oracle**.
5. Only after two native candidates are verified and frozen, separately invoke the unchanged pinned original-author scorer on D0 and I0. Compare metrics, independently retain actual full file hashes, check original source/data/author unchanged.

The read-only independent native oracle verifies original **358 IfcRoot** identities/classes/names/descriptions and original **43 IfcProduct** identity/classes, plus unchanged world-space mesh bounding boxes **and full triangle-mesh fingerprints (1,652 source triangles)** for **39** physically represented pre-existing products; four products have no native mesh and remain classified that way. It checks the original containment relation's prior members are retained. The source file itself is never overwritten and candidate IFCs live in unique scratch directories; no hidden target IDs are given to either authoring path.

## Frozen actual-original source results

| Predicate | Whole XML D0 | Independent imperative I0 |
| --- | --- | --- |
| Native physical `IfcSlab FLOOR` created, IFC4X3 mm IFC persisted | **PASS** | **PASS** |
| World bbox min/max (metres) | (-35,-2.5,0) / (-25,2.5,0.2) | same |
| Native extrusion depth | 200mm | 200mm |
| Original IFC Root/Product identities & 39 original native shapes preserved | **PASS** | **PASS** |
| Existing L1 containment preserved, one Slab added | **PASS** | **PASS** |
| Original author score after frozen outputs | **1.0** | **1.0** |
| Author metric components | integrity, exists, location, dimensions **1.0 each** | same |
| **Full native IFC bytes identical to other arm** | **NO** | **NO** |

The D0 and I0 files have distinct newly generated entity identifiers/metadata, and their full IFC byte streams are **not** the same. This is **narrow native geometry and pre-existing building preservation agreement with identical original author scores**, not exhaustive IFC semantic identity. No full-scene clash analysis or construction-quality judgement was conducted; the original scorer's 1.0 means the pinned author grading predicates passed for these developer candidates, not an official LLM benchmark score.

The v0.31 **11 original tasks with developer full native IFC byte equality remain 11**. v0.32 added distinct `test_04` *semantic-only* Create and v0.33 adds `test_02` *semantic-only* Create; the **2 semantic-only Create controls must not be counted as byte-equal**. Thus **13/15 original Create tasks still lack equivalent task-specific paired positive developer evidence**. The original 45-case model ITT sample remains untouched.

No new paid inference; **0 matched actual LLM D/I trials**. Evidence for complete IFC source parity, native-write parity, or model-causal representation effect remains **0/45 proven**. The isolated XML D0 v0.4 backend is **not** seamlessly enabled in the matched25 production evaluation session. It would be scientifically incorrect to declare this case model-trial eligible, or to use 2 successful developer Create examples as a selected model-test cohort.

## Artifacts, tests and reproducibility

- `tools/bibimbap_v033_original_slab_i0.py` — independent original-public Python I0; source-only, fail-closed source/version/original units checks, never overwrite.
- `tools/audit_bibimbap_v033_original_slab_pair.py` — strictly ordered source-only I0→native validation→declarative D0→native validation→original author scorer.
- `tests/test_bibimbap_v033_original_slab_pair.py` — real original IFC positive/negative controls, fake score rejection, original SHA drift/overwrite rejection, missing/misplaced/thin physical slab negative cases, no answer leakage or LLM-score inflation.
- `reports/bibimbap_v033_original_test02_slab_D0_I0_semantic_pair_20261117.json` — frozen actual trial summary SHA-256 `998064e23a0b3955b20a0ca1a7cabcb4424a612af1d633e42cd179f5e68ce660`.

With a preinstalled Python/IfcOpenShell environment and the two pinned original benchmark repositories available:

```powershell
$base='D:\문서\D__1_Projects\202611'
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
& $py -m unittest -q tests.test_bibimbap_v033_original_slab_pair
& $py -m tools.audit_bibimbap_v033_original_slab_pair `
    --author (Join-Path $base 'bibimbap-author-upstream') `
    --data (Join-Path $base 'bibimbap-author-data')
```

The optional `--write` creates a new report only via exclusive write, refusing overwrite. Fresh native IFC GUIDs make whole-file candidate SHA256 **run-specific**; rerun checks compare physical geometry, preexisting entities/shape preservation and author score instead. The versioned committed JSON output and original upstream reports remain SHA-pinned.

## Next priorities and blocked launch

1. Prospectively examine remaining 13 original Create tasks, especially a new element class beyond Column/Slab; any new developer candidate must be independently paired and source-only, not scorer-target-derived.
2. Audit task-relevant **complete source facts, geometry/relations, and native edit capability** for actual model D/I before any randomized/preregistered trial. The current original native IFC↔typed XML projection omits IFC entities, so one physical Create example cannot prove full information parity.
3. Revalidate isolated Linux Docker model-Python worker without resetting/starting a host service against authorization. Test model host feature flags and fair read/feedback budget before proposing any paid inference.
4. Keep unchanged paper grader, frozen original tasks, source IFCs, model outputs/previous benchmark reports, research `main`, stashes and Xim product code.

## Extra post-frozen native STEP accounting — important limitation

A further independent read-only comparison of the original **3,138 STEP entities** against each separate actual IFC candidate found the **same differences in both arms**: one original `IfcSIUnit` STEP entity no longer present, and exactly two pre-existing STEP entities rewritten: one `IfcUnitAssignment` and one `IfcRelContainedInSpatialStructure`. This is consistent with the original millimetre-to-metre-to-millimetre round trip and the extra contained Slab, but an exhaustive independent cause analysis was not conducted. The original source IFC file remains byte-unchanged. Do **not** claim lossless round-tripping or full original native STEP preservation: preserving all original IfcRoot identities, 43 products and the 1,652 native world triangles is narrower than lossless preservation of all original STEP entities. Both developer arms showed the same observed change classes.

The strengthened oracle now verifies original-product full world-coordinate triangle meshes, not only bounding boxes. It hashes canonical triangles and multiplicity with coordinates quantized to 1 micrometre, and a negative test forces a fingerprint mismatch despite unchanged bounding box. Actual original mesh vertices, GUIDs, grader targets and IFC source bytes are not serialized in the published report.
