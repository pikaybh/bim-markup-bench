# v0.45 — Original four BIBIMBAP UPDATE/DELETE IFC4X3:mm typed XML-to-native writers with independent physical oracle

Issue [#205](https://github.com/pikaybh/bim-markup-bench/issues/205). Stacked from v0.44 [Draft PR #204](https://github.com/pikaybh/bim-markup-bench/pull/204) on exact baseline commit `cd3d86b0ec30b1876e9072af32de451ee8892a12`.

## Research goal and integrity

Introduce **genuine native IFC file modifications** for the four original BIBIMBAP task inputs whose model-visible XML read-only source capability was demonstrated in v0.44. Keep the exact original public questions/IFC files/hidden ground truth/original grader unchanged. This is **experimental task-conditioned editing capability**, **not solving or scoring the original benchmark questions**.

The original full 45-task population (15 CREATE/15 UPDATE/15 DELETE), 31 distinct exact original IFC byte hashes, original author Git SHA `667004e16bd38fd7d538bcee56191465429fd975`, original source-data Git SHA `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`, original public question CSV SHA `21c07f08c923cdb748255d7960535bab05e2887e4d093d64f87f76ff6d6d100b`, and previous frozen v0.44 report SHA `dc58535db3dbec85ba610d3e8b9104c660c4bf0e3e019f9a20ee3a32a012281a` are pinned and independently rechecked. No original author benchmark file, original IFC, hidden GT, evaluator, default XML schema, prior frozen report, benchmark scoring or research main has been changed.

## Exactly four source-locked original public inputs

| Original task | Original public request (meaning only) | Native original source structure | New typed XML plan |
| --- | --- | --- | --- |
| `geometry_test_14` | Make slab footprint a square by increasing one side | Original `IfcSlab` → `IfcExtrudedAreaSolid` → `IfcRectangleProfileDef` | `SetSlabRectangleDimensions` (original Slab GUID, new X/Y dimensions in m; only one may increase) |
| `geometry_test_15` | Move a Column so the four Column pattern becomes rectangular | Four original `IfcColumn` products, `IfcMappedItem` geometry and **parent-relative `IfcLocalPlacement`** | `MoveColumnPlacement` (original Column GUID and absolute world X/Y in m, converted into actual parent frame) |
| `topological_test_11` | Increase heights of all Columns to meet a referenced original Slab | Two original `IfcColumn` products share the **same `IfcRepresentationMap` and one `IfcExtrudedAreaSolid`**, surrounded by untouched Slabs and seven clipped Walls | `SetAllMappedColumnDepth` (one shared extrusion depth in m; both Columns must change together) |
| `topological_test_17` | Remove Columns unrelated to a particular original Slab | Ten distinct original mapped Columns + original Slabs, storeys and native property/containment relations | `DeleteColumnsByGuid` (explicit 1–9 original Column GUIDs; no inferred deletion set) |

**No correct values, intended deleted identities, target square dimension, slab contact depth or rectangular Column location is hardcoded.** The model chooses the numbers and GUIDs using original native source facts. A valid original native edit does **not** imply a model chose the correct semantic result for the original question.

## Actual model-facing workflow

```python
session = XmlSourceEditSession(
    original_public_native_IFC4X3_mm,
    isolated_trial_folder,
    experimental_original_native_mutations_v045=True,
)
source = session.call("read_building_xml", {})
edited = create_updated_complete_xml_with_one_NativeEditPlan(source["xml"])
result = session.call("submit_building_xml", {"xml_text": edited})
```

This separate experimental flag works **only on the four exact original source IFC SHA256s** and is mutually exclusive with legacy/complex/room/P3/slab/read-only v0.38–v0.44 opt-ins. The original default paired provider runner does **not enable it**. Thus the original default model-facing source-read ability remains 36/45; best-available independent experimental source-read modes remain 45/45 but are not a unified balanced comparison.

The original v0.44 read-only source **retains all seven immutable XML sections** (all original IFC STEP DATA records, original Products, native direct relationship endpoints, PropertySets, Materials, LocalPlacements and independently verified source-world meshes) byte-equivalent under XML canonicalization. A dedicated `spec/original_native_typed_mutations_v045.xsd` extends the original v0.44 schema with **only one** optional `NativeEditPlan` child. Its generator `tools/generate_v045_schema.py` traces the exact v0.44 schema. Neither original v0.44 nor default `toy_markup_v0.xsd` is changed. The root has explicit limited native write authority; embedded original `OriginalNativeIFCSource` stays `NONE_READ_ONLY` and is checked by canonical XML and a second **independent original source read oracle** before allowing a plan.

Model-facing tools stay `read_building_xml` and `submit_building_xml`. The latter accepts **only** the four original-task-corresponding typed operations. It cannot execute Python or arbitrary IFC code, cannot edit immutable native STEP records, and rejects invented GUIDs, non-Column deletions, source SHA mismatches, invalid/duplicate/empty operations, malformed numeric bounds, non-finite values, no-op edits, unsafe shared shape targeting and arbitrary new XML attributes/sections. The source schema must be genuine IFC4X3 and native millimetres.

The native writer opens **the original native-mm IFC** and writes a new original-mm IFC candidate in the isolated attempt directory. It **does not rescale to metres or create a normalized source copy**, and it never writes to the original public source. All mutations operate on the original native IFC entities (Slab rectangle SweptArea X/Y dimensions, original Column `IfcLocalPlacement` XYZ point with parent-frame transform, shared mapped Column extrusion depth, or IfcOpenShell `root.remove_product` with precise GUIDs).

**Critical IFC geometry lessons verified with original files:**

- Slab `geometry_test_14`: changing `IfcRectangleProfileDef.XDim` or `.YDim` changes a real original source physical rectangle, with original height and footprint centre preserved.
- Column `geometry_test_15`: the source Column placements **can have a non-null `PlacementRelTo`**, so original world X/Y cannot be naively assigned to a parent-relative `IfcCartesianPoint`. Compute the original world `get_local_placement`, inverse the parent placement matrix, and write actual local XYZ. The independent oracle verifies the parent ID, absolute-world target position, basis, and physical world vertex shift (no shape resizing).
- Column `topological_test_11`: both columns share one original mapped representation/solid. Changing one source extrusion changes *both physical columns*, so the only safe supported operation sets the shared original depth and independently checks **both** physical world heights and all other original Slabs/Walls/Spaces.
- Delete `topological_test_17`: native `root.remove_product` deletes a specified original Column and its exclusively-owned property sets/relations, and removes it from shared original containments. The independent oracle permits only source relationships/psets whose complete original related product set is deleted, **preserving every unrelated remaining original product, relationship and physical geometry**.

For every submitted candidate the independent oracle reopens the original public IFC and newly written candidate, checks **IFC4X3/mm, original source SHA and exact unchanged model-visible original STEP content**, product class/name/Description/GUID conservation, relationship GUID/role/reference conservation except explicit safe deletions, and physical world meshes for **all** non-target products. It independently validates target physical edit deltas and preserved original source shape for others. An edit is committed to the model session **only after the independent oracle passes**; a failure returns explicit structured error and preserves the previous valid XML and IFC. The independent oracle does not import the v0.45 writer or original author grading code.

## Actual source-conditioned illustrative run

A developer-authored **non-solution illustrative source modification** was actually submitted via the two model-facing tools to each of the original four source files. The examples deliberately do not implement the original requested full semantic answer:

- Slab grows one original rectangle profile dimension by 0.4 m, **not to a square**.
- A single mapped Column shifts by +0.2 m in world X, **not a proven rectangular four-Column pattern**.
- Both shared mapped Columns extend to 2.0 m, **not to the original referenced upper Slab**.
- One arbitrary original Column GUID is removed, **without proving it is the correct disconnected Column set**.

All **four real XML submissions produced actual IFC4X3/mm candidate files** and passed the independent source/physical oracle. An additional intentionally corrupted XML resubmission to each live session failed without clobbering its previously verified native IFC or XML. All original source IFC byte hashes stayed identical. These candidates are **not** D0/I0 original benchmark scored solutions and are not paid LLM model trials.

The frozen per-source audit captures original question/source SHA and candidate XML/IFC SHA, names of the physical operations (not hidden GT), unchanged original source checks and independent oracle evidence. It is generated only with exclusive creation `xb`, refusing overwrite.

**Frozen machine report:** `reports/bibimbap_v045_original4_native_IFC_typed_writers_20261117.json`
**SHA256:** `7d7518f6c65242f7f00066beeb0229fbb6e42e44d5e841243666ac375105c4b3`.

## Focused tests and regression

The dedicated v0.45 suite contains **86 positive and negative tests** exercising original 45/31 pinned population, original 4 source/question SHAs, exact v0.44 source immutability, real four native IFC file writes and independent oracle, source schema/unit, valid original root and property/relationships, shared map conservation, source parent frame semantics, safe deletion, preservation of all original non-target objects and geometry, invalid GUID, duplicate deletion, non-column deletion, malformed numeric edits/NaN/negative/no-op, tampered source STEP/geometry metadata, forged native output/relationships/units/unrelated entity movement, preservation of last valid candidate after failed edit, frozen report byte-for-byte replay, old v0.44 and default schema unchanged, and no private grader/GT/LLM/Docker.

Reproduce on connected Windows system from isolated v0.45 Worktree:

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'

& $py -m tools.audit_bibimbap_v045_original4_native_mutations `
    --author (Join-Path $base 'bibimbap-author-upstream') `
    --data (Join-Path $base 'bibimbap-author-data') --progress

& $py -m unittest -q tests.test_bibimbap_v045_original4_native_mutations
```

## Research-validity cautions and remaining work

- **4/4 original native IFCS edited under the new four-source flags ≠ 4/4 original BIBIMBAP task success.** The original author benchmark evaluator has not scored any result, no correct original task-specific XML/Python paired answer D0/I0 is proven in this release, and no paid model has performed the original task.
- **Original Python IfcOpenShell remains more expressive** than these four limited XML operations. Native IFC authority is now established only for those four task-conditioned operations, not full equivalence of Python's read/query/write API surface or model exposure/token budgets.
- **45/45 best-research-mode original source reads ≠ 45/45 same-information reads**, since 27 previously readable unique original source IFCS are still missing native property/relationship/geometry information in their model-visible XML. v0.45 does not silently fix those or extend original benchmark denominators.
- Original author/GT/dataset untouched. The earlier five CREATE task-specific developer D0/I0 controls remain five; v0.45 creates zero original full-task answer pairs. Real original public LLM XML vs Python matched comparisons remain **0**.
- **Next v0.46 priority** is to eliminate task-relevant original source metadata/query information gaps across the remaining 27 unique readable IFCs and test equivalent edit capability and true semantic outcomes under original-author acceptance rules. Only then may an explicitly preregistered restricted equal-information/equal-write study or honestly labeled unequal-tool-bundle study proceed.

Neither research main, original author/data repos, original evaluator, BIXML/Xim, nor existing other research Worktrees are merged or modified by this checkpoint.
