# BIBIMBAP experimental v0.8 — original-native IFC2X3 and IFC4 declarative editing

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/130

**Date:** 2026-11-13 Asia/Seoul.

**Independent experimental repo ONLY.** This is not Xim/BIXML code, not a product schema, and not full original-paper-equivalent 45-task IFC support. Original frozen IFC4X3 toy grammar and v0.1–v0.7 runtime remain unchanged; original BIBIMBAP scorer, original public inputs, prior real GPT-6 Luna #112 45-task outcomes (3/45 historical full marks), and paid model experiment records remain unchanged. **New provider calls 0; additional API charge $0.**

## Why a separate IFC2X3/IFC4 declarative dialect is necessary

The original previous toy XML namespace `urn:bim-markup-bench:toy:v0` has a strict literal `ifcSchema="IFC4X3"` and an XSD that requires every `Level.elevation` to be present. It would be methodologically false to feed native IFC2X3 or IFC4 inputs through this schema by quietly stamping IFC4X3, inventing an IFC4 missing `IfcBuildingStorey.Elevation`, or ignoring original native IFC2X3 `IfcWallStandardCase` and spatial IfcRelAggregates semantics.

The separate research dialect `urn:bim-markup-bench:legacy:v0.8`, pinned at `spec/experimental_native_legacy_v08.xsd`, explicitly records source IFC schema (`IFC2X3` or `IFC4`), immutable source SHA-256, units (metres on a temporary original-schema-preserving normalized clone), full original named Storey nodes, and exactly source-verifiable original Wall/Column partial geometry. A missing native Storey Elevation is **`elevationState="MISSING"` and no `elevation` attribute**, while `placementZ` is independently measured from the *actual original IfcLocalPlacement* (not an invented Elevation). The `IfcBuildingStorey.Elevation` in final native IFC remains null.

The editable document is a **declarative model state**, never a list of procedural `Create`/`Move`/`Set` commands. The trusted backend `src/runtime/experimental_v8_legacy_compiler.py` diffs original/proposed state by stable IDs against source-original native IFC and infers one narrow allowed creation transaction. Unknown source objects remain opaque native IFC passed through, never silently deleted. The model itself is never given Python/IfcOpenShell editing calls in the direct-markup arm.

## Original public source files and fixed developer D0

Original dataset revision: `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`. Original author scorer revision: `667004e16bd38fd7d538bcee56191465429fd975`.

| Public original task | Original native IFC schema | Public question summary and source-only developer decision | Native IFC implementation | Original pinned author D0 grade |
|---|---|---|---|---|
| `geometry_test_03` | **IFC2X3** | Add a Door in a Wall north of named south Wall GUID `3YQ$1CPXD2Mh2vQ18vV$hw`. Source-only choose nearest original north Wall GUID `3YQ$1CPXD2Mh2vQ18vV$ig`; 1m × 2.1m Door at world x=0, y=1.6m; native Opening 1m×0.4m×2.1m, door 1m×0.08m×2.1m | New native `IfcOpeningElement` + native `IfcRelVoidsElement` linking original host Wall; native `IfcDoor` + `IfcRelFillsElement`, original Storey containment; **original host wall physical mesh transforms from 8 vertices/12 triangles to 16 vertices/28 triangles**, native solid wall volume decreases ~0.42m³. All unrelated original solids untouched | **1.0000**: existence/location/dimensions/integrity all 1.0 |
| `geometry_test_04` | **IFC2X3** | Create `IfcSpace` strictly left of original Column GUID `3A5GfH23DBvBYpavCfWh4z`; developer chooses x=0.2–6.3m, y=0.2–6.7m, z=0–2.8m. Column original x minimum=6.35m, leaving a physical 0.05m gap | Native IFC2X3 `IfcSpace` with original geometry context, true rectangular `IfcExtrudedAreaSolid`, physical 8-vertex native mesh, original Storey **`IfcRelAggregates`** membership (not incorrect wall containment). Original Columns/Walls/STEP preserved | **0.916675**: existence=1, location=1, dimensions=1, original-author integrity=0.6667. **Unresolved stricter author-integrity requirement**; independent native oracle passes. NOT full mark |
| `geometry_test_05` | **IFC4** | Create a 5m Wall from world plan coordinate (10,5), direction (+1,0); developer chooses 3m height and 0.2m thickness, world mesh [10,5,0] to [15,5.2,3] | New native IFC4 `IfcWall` with actual `IfcExtrudedAreaSolid` and native `IfcRelContainedInSpatialStructure`, using original Storey ObjectPlacement. Original `IfcBuildingStorey.Elevation` stays **None**; original IFC4 STEP/Root objects untouched | **1.0000**: existence/location/dimensions/integrity all 1.0 |

These are **three developer-authored, hand-fixed D0 source-state edits** based exclusively on original public input IFC and public natural-language question, with native compiler+independent IFC oracle; original author scoring was executed *only after compiling and closing candidate IFC*, never shared with a tested model or used to retune any grade. **This is not a new LLM run and cannot be added to GPT-6 Luna's earlier 45-trial numerator.** Two original full marks + one original fractional pass are backend capability evidence only.

## Scope and native safety conditions

`src/runtime/experimental_v8_legacy_projection.py::project_legacy_v8`:
- Accepts **native-schema-preserving metre-normalized copies** of original IFC2X3 and IFC4 (original raw IFC input is millimetres), never re-labels schemas. Rejects raw mm as metres and any unexpected schema.
- Projects explicit original native `IfcBuildingStorey` with independent native world placement and optional `Elevation`. Projects original direct IF2X3 `IfcWallStandardCase` line axes/true rectangular profiles and physical meshes only if world geometry is exactly orthogonal rectangular prism. Original 90° world-rotated axes are supported for read-only wall projection. Projects original source `IfcColumn` only if complete actual world mesh independently corresponds to an eight-corner/twelve-triangle native rectangular solid, **not just the AABB**.
- Keeps all unrepresented IFC Product/Root/STEP entity graphs source-owned opaque, including nonrectangular walls, IFC4 unknown features, materials/property sets and original spatial relations.
- Validates the new local XSD under network/DTD/XXE-disabled parsing, root hash/schema/units, unique stable IDs, original source GUIDs, native level/host/opening referential integrity and explicit-vs-missing elevation distinction.
- Never modifies or writes to the source IFC.

`src/runtime/experimental_v8_legacy_compiler.py::compile_declarative_xml_v8` permits only these exact original-schema-preserving declarative differences:
- IFC4: exactly **one added Wall node** on an original missing-elevation Storey whose native placement is available; bounded horizontal axis, real original native representation context, native wall and storey containment. Does not set `IfcBuildingStorey.Elevation`.
- IFC2X3: exactly **one added Space node** on an original explicit-elevation Storey with bounded world rectangular prism, true native `IfcSpace` (CompositionType native to IFC2X3) and an `IfcRelAggregates` relationship into the original spatial tree.
- IFC2X3: exactly **one added Opening node plus its unique filled Door node** under one **original** projected positive-world-X `IfcWallStandardCase`; bounded opening offset/sill, physical cut wholly inside original host dimensions, new native `IfcRelVoidsElement`, `IfcRelFillsElement`, door containment in original Storey, and IFC2X3-required **non-null IfcRectangleProfileDef.Position**. Invalid references, dangling Door/Opening, wrong dimensions, out-of-host placements, wall-update/other-source-node edits and multi-create transactions fail closed.

All new IFC Product GlobalIds and new IFC Relationship GlobalIds are source-hash+node-ID deterministic, source STEP/Roots and original containment member order are preserved (only one new Door may extend existing containment). The original IFC2X3 `IfcOwnerHistory` records are unchanged; **only new** generated owner-history dates are pinned to original source CreationDate for byte-reproducible research artifact creation. **This synthetic timestamp is a source-anchored reproducibility marker, not an actual creation time and not a production policy.** Atomic stage/verify/commit preserves original IFC file and refuses existing destination. The IFC source and output use identical native schemas; conversion to original millimetre units happens only on a separate copy for author scorer.

**Not supported or claimed:** IFC4/IFC2X3 arbitrary IFC mutation, IFC2X3 existing wall edit/rotation, multiple new doors or multiple source element modifications, semantic Space boundaries or complete building-space topology, general IFC4 missing-elevation level editing, source IFC with existing hosted opening, arbitrary rotated/complex Boolean walls, automatic room inference from tessellated building envelopes, opening sill/door style types, or parity with original author Python/IfcOpenShell access for all 45 tasks.

## Independent native oracle, adversarial negatives and D0 reproducibility

`tools/oracle_bibimbap_v08_native.py` imports **no** projection/compiler/XML binder/mutation helpers or original grader; it independently reopens original-schema IfcOpenShell source+candidate and verifies every original source Root and original STEP entity remains, except precisely allowed new Door containment relation membership. It confirms all original IFC Product metadata, shape vertices/triangles (excluding declared host Wall whose void is physically cut), actual new schema-typed IfcWall/Space/Opening/Door, original spatial containment/aggregation, missing original IFC4 Elevation, Door void/filling native inverse consistency, actual host Wall volume removal, and source-only location/dimension criteria. It independently rejects a wrong original host Wall (even if physically valid new Door was made there), unrelated original Storey metadata tampering and schema/geometry mismatches.

`tests/test_experimental_v8_legacy.py` includes at least twenty positive and negative cases on all three original public sources. Important negative fixtures: original source schema mismatch, spoofed missing elevation, source Storey placement tampering, changed original IFC2X3 Wall/Column, DTD/XXE and pseudo-command XML, wrong original digest, existing output overwrite, orphan opening, dangling/mismatched door, wrong northern host, out-of-bounds opening, multiple additions and corrupted original IFC product metadata. It also verifies byte-identical native results from repeat CREATE runs across more than one actual wall-clock second.

Original author D0 report: `reports/bibimbap_v08_legacy_ifc2x3_ifc4_d0_20261113.json`, **SHA256 `1264e33403a8b7e554913a34fc79b031890fd0aee832bc6b8f2010f912a5b4e0`**, generated via `tools/audit_bibimbap_v08_legacy_d0.py` with public-task/source/question SHA-256, declared developer fixture choices, independent oracle evidence and untouched original author submetrics. The entire audit was generated again independently after a wall-clock delay with **identical output bytes and report SHA256**. The separate v0.8 test suite is **23/23 PASS** and the combined v0.8+v0.7+v0.6+v0.5+v0.4+v0.3/v0.2 plus original 45-audit, original offline paired 25-tool harness and legacy compiler suites is **168 tests / 166 PASS / 2 optional SKIP / 0 FAIL**, last complete run **137.932 seconds** (no LLM/provider calls). **No original IFC corpus bytes, private GT solutions, model outputs, secrets, or author grader sources committed.**

### Reproduce without LLM/API

```powershell
$base='D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue130-legacy-v08')
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$author=Join-Path $base 'bibimbap-author-upstream'
$data=Join-Path $base 'bibimbap-author-data'

& $py -m unittest tests.test_experimental_v8_legacy -v

# Output path MUST be unused; prior evidence is immutable.
& $py -m tools.audit_bibimbap_v08_legacy_d0 --author-repo $author --dataset $data --output-json 'results/YOUR_NEW_UNUSED_V08_D0.json'
```

## Next actual work after v0.8

1. Resolve original-author `geometry_test_04` Space integrity discrepancy against **public expectations** without post-hoc grading optimization or claiming full mark from independent native integrity.
2. Grow safe original IFC4X3 editable Boolean/Clipping Wall and direct Slab rotated-local-frame geometry, and mapped-column type geometry height edit safely with instance isolation; add multi-element dependencies required by original BIBIMBAP topological tasks.
3. Freeze all-45 true D0/P0 independent native capability coverage and honest negative cases, then secure a new explicit paid LLM budget only if the paired 25-call identical-capability experiment gates pass. Published external benchmark numbers are not an equal-condition causal comparator by themselves.
