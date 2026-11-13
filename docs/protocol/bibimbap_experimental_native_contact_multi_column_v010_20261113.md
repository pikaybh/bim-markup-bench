# BIBIMBAP — prospective v0.10 native IFC4X3 multiple Column deletions by original named Slab contact

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/134

**Date:** 2026-11-13 Asia/Seoul

**Strict scope:** Independent research repo `pikaybh/bim-markup-bench` only, NOT BIXML/Xim/Revit production. Original BIBIMBAP public input IFC and scorer remain pinned and immutable; prior model-call evidence and original GPT-6 Luna full-45 results are unchanged. Original v0.1–v0.9 experimental compilers are untouched. **Zero new paid model calls ($0).** This is a frozen-source developer-authored D0 and independent native-IFC oracle, not a new LLM benchmark result.

## Original public problem and source-native relationship interpretation

Original public task: `topological_test_17`: **"Delete the columns that have no relationship with the slab with the id 2IIWDJ6bzEPxU4iXeUX9Z5."**

Pinned public dataset revision `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`, original scorer/author revision `667004e16bd38fd7d538bcee56191465429fd975`. Original source is `ifc/01/02/01_02_017.ifc`, native IFC4X3 in millimetres; a temporary isolated same-schema copy is normalized to metres for the trusted compiler.

**Important semantics:** The original file contains no direct native `IfcRelConnectsElements` edge joining these Columns with the named Slab. It would be false to claim that such IFC semantic links were found. The prospective v0.10 test interprets "relationship" using **measured native physical support** from the original full world-space meshes and source Storey membership, not a guessed IFC Relationship object:

- Original named source Slab is a complete actual original-native 8-corner/12-triangle rectangular solid, world XY footprint `[0,7.5] × [0,7.5] m`, bottom Z = **-0.3m**, top Z = **0m**, original Storey **L1**.
- Original 10 `IfcColumn` products are each a native `IfcMappedItem` and a complete source world-space rectangular prism. The source physical relationship is defined as Column **bottom-face Z equals named Slab top Z within 0.01mm**, native Column footprint over named Slab **at least 99%**, and the original source Storey is the same. Any partial/ambiguous native contact is rejected; the rule must not infer contact from bounding boxes of arbitrary clipped or rotated shapes.
- **Keep precisely 5 contacting original L1 Columns**: `2IIWDJ6bzEPxU4iXeUX9cP`, `2IIWDJ6bzEPxU4iXeUX9rk`, `2IIWDJ6bzEPxU4iXeUX9wF`, `2IIWDJ6bzEPxU4iXeUX9wJ`, `2IIWDJ6bzEPxU4iXeUX9zS`. All have world Z lower face at **0m**.
- **Delete precisely 5 non-contacting original L2 Columns**: `2IIWDJ6bzEPxU4iXeUX9_B`, `2IIWDJ6bzEPxU4iXeUX9ow`, `2IIWDJ6bzEPxU4iXeUX9rK`, `2IIWDJ6bzEPxU4iXeUX9rM`, `2IIWDJ6bzEPxU4iXeUX9ti`. All have world lower face at **3m**, not touching named L1 Slab. Some L2 Columns touch the *other* upper Slab — this is NOT the public named reference.
- **These are source-only derived sets** from original public input IFC and the public named Slab, not from hidden target IFC or any original-author scorer output. They are explicitly restricted to this frozen physical source family and do not establish general IFC semantic relationship equivalence.

## Direct declarative state vs trusted native deletion

`src/runtime/experimental_v10_column_multi.py::compile_declarative_xml_v10(source, edited_xml, destination, reference_slab_guid=...)` accepts a whole immutable-source-SHA-pinned XML document in existing research toy namespace `urn:bim-markup-bench:toy:v0`. The XML contains original ten source Columns, two original Slabs and original Storeys; the direct-markup arm edits the **model state** by removing the five non-contacting Column nodes, **not** by authoring `<Delete>` commands or a BIM authoring API.

The trusted runtime, running outside the LLM loop, uses the named source Slab GUID from the **original public natural-language task context**, not a hidden grader parameter. It calculates the original real source Slab/Column physical prism faces, validates original XML projection, semantic stable-ID deletion graph and original-source type/space relationships, and refuses:
- missing/extra/surviving-wrong Column edits (exact all five must be deleted),
- other source Product or Slab edit, new object, mixed create/update/delete, malformed XXE/DTD, unknown source hash and schema or raw millimetres incorrectly labelled metres,
- wrong original named Slab / only some of target Columns, original Column with unsupported placement, nonrectangular shape or shared/ambiguous inverse type/Pset dependencies,
- replacing an occupied destination, changing original IFC input or touching unrelated original source STEP objects,
- deleting any original source-rooted property set still used by another surviving object.

IfcOpenShell's trusted `ifcopenshell.api.root.remove_product` deletes the *five specific native IFC Column GlobalIds* in deterministic GUID order, and solely-owned property/type relations, geometry representation ownership, and Psets; the native source file itself remains read-only. **Original IFC schema remains IFC4X3.**

## Actual native IFC structural observations and independent proof

`tools/oracle_bibimbap_v10_native_multi.py` imports **no compiler, source projection, binder, XML graph, original author scorer or private reference**. It independently reopens source and candidate native IFC4X3, recalculates all 10 original Column meshes, checks six complete original source prism faces rather than trusting AABB extents, derives the named-Slab original physical support relation, and verifies native STEP/Root inventory and all original surviving physical meshes.

Measured original candidate transaction:

| Native metric | Source | Result |
|---|---:|---:|
| Original `IfcColumn` products | 10 | **5** (all original physically contacting L1) |
| Source native IFC STEP entities | 440 | **365** |
| Original IFC Roots | 158 | **118** |
| Native original STEP entities deleted | — | **75** |
| Surviving original STEP entities changed | — | **2**, exactly original L2 `IfcRelContainedInSpatialStructure` and `IfcPresentationLayerAssignment` |
| Source original rooted objects removed | — | **40** = 5 Columns + 15 exclusively owned `IfcPropertySet` + 15 `IfcRelDefinesByProperties` + 5 exclusively owned `IfcRelDefinesByType` |
| Original L1 five Columns / named Slab geometry and type maps | Original native physical meshes | **Identical world vertices and triangles**, same surviving native GlobalIds, mappings, type/material/Pset memberships |
| Original L2 Storey `IfcRelContainedInSpatialStructure` membership | 5 L2 Columns + upper Slab | Upper Slab only; no lost unrelated native Storey product |
| All other original Product/Root/STEP data | Original native geometry and source ownership | Verified unchanged, unless specifically accounted for in above deletion ownership closure |

Original native geometry, shared typed representations still used by survivors, non-target material association relationships and untouched physical Products are preserved. For each deleted STEP entity, every old inverse reference either disappears or belongs to exactly the audited changed relationship, preventing dangling references or accidental deletion of surviving shared mapped geometry. The independent oracle rejects changing a surviving Column name, original mapped representation extrusion or named source Slab solid.

**Native IFC structural and physical validator: PASS. This does not imply the original author grader's distinct integrity metric passed.** The original author is a separate metric authority and can disagree.

## Original pinned author D0 — disclose both metrics

Report `reports/bibimbap_v010_original_column_multi_developer_d0_20261113.json`, final SHA256 **`9341aa11206b2d9ae2e5c96e816287f66fb5e0bab0b02d506f65ba7e862fe938`**, generated by `tools/audit_bibimbap_v10_column_d0.py` with original public IFC/question hashes, source-derived 5+5 geometry evidence, exact deleted stable XML IDs, independent native oracle proof and pinned original-author submetric scores. The entire independent source→candidate→original-author scored D0 audit was reproduced after a clock interval with **byte-identical JSON and SHA256**.

**Original-author result after freezing candidate:**
- `object_not_exists = 1.0`: the original scorer recognizes the deleted Column targets are absent.
- `integrity_constraint = 0.0`: original author integrity criterion **NOT met**.
- **Original author D0 score = 0.5000, NOT a full mark.**

The reason the original author integrity metric differs from source-native preservation is **not established** here; do not assert that the original scorer is incorrect, that all physical/semantic integrity requirements are satisfied, or that the candidate meets full original paper correctness. The source-only developer D0 edit was **not retuned after observing these metrics**. No hidden reference IFC/ground truth is consulted to choose deletion targets or improve this score. This is a developer-authored backend ceiling example, **not a new LLM-run result**. Historic GPT-6 Luna full-45 model score remains unchanged, and v0.10 has not been wired into an equal-capability 25-tool model trial.

## Reproduction and quality gates

Run from the isolated Windows 11 original-research worktree:

```powershell
$base='D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue134-multi-column-v010')
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'

& $py -m unittest tests.test_experimental_v10_column_multi -v

# Choose a NEW unused path to avoid overwriting immutable D0 results.
& $py -m tools.audit_bibimbap_v10_column_d0 `
    --author-repo (Join-Path $base 'bibimbap-author-upstream') `
    --dataset (Join-Path $base 'bibimbap-author-data') `
    --output-json 'results/YOUR_NEW_UNUSED_V010_D0.json'
```

`tests/test_experimental_v10_column_multi.py` has **26 source-native positive and negative tests**: correct public Slab 5/5 partition, original 10 source XML Columns, native 5-Column delete and independent original IFC world mesh/STEP/Root/type proof, untouched original material/Pset/Storey memberships, repeat byte-identical IFC across a clock-second interval, bad named Slab, wrong/missing subset, deletion of original supported Column, malformed/command XML, mixed operations, changed original source SHA or GlobalId, raw millimetre schema confusion, output overwrite, and independent oracle detection of survivor/Slab corruption.

**No model inference or API cost**. **26/26 new native v0.10 source-positive/fail-closed tests pass**. The full v0.10+v0.9+v0.8+v0.7+v0.6+v0.5+v0.4+v0.3/v0.2 source regression, original full45 offline audit, 25-call paired harness, and initial native core/compiler regression returned **221 tests run, 219 PASS, 2 optional SKIP, 0 FAIL** (170.263 seconds). No paid provider calls.

## Remaining high-priority research

1. Explain the **original-author integrity failures** in an explicitly separate **prospective** diagnostic workstream for `topological_test_17` (this v0.10 D0 integrity=0), `topological_test_11` (v0.9 D0 integrity=0), `geometry_test_14` (v0.9 D0 location=0), and `geometry_test_04` (v0.8 D0 integrity=0.6667). Keep frozen D0 results and source native compiler unchanged; do not exploit the original grader/hidden GT to optimize developer targets.
2. Re-audit original **45 cases** to classify true direct XML native operations, original source schema coverage, independent D0/P0/I0 baseline, and explicit unsupported cases; no full common-capability benchmark equality yet.
3. Only after the capability / design / validity gates pass, request new explicit authorization for real paired 25-call or full original task model experiments and label all outcomes separately.
