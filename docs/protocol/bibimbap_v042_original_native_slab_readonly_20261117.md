# v0.42: Original-public P3 native existing IfcSlab evidence, exact source-mm vertices/indices and trusted native Column/Slab writer

**Source-first Issue:** https://github.com/pikaybh/bim-markup-bench/issues/199
**Parent:** v0.41 [Draft PR #198](https://github.com/pikaybh/bim-markup-bench/pull/198), exact head `d48a31805e05b802b7fdf4f51852a4bb37d98b26`.
**Original author/data SHA pins:** unchanged original Git HEAD `667004e16bd38fd7d538bcee56191465429fd975` / `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`; original public question and IFC SHA256 independently pinned.
**Original full cohort:** 45/45 original published tasks, exactly 15 CREATE / 15 UPDATE / 15 DELETE. No redefined benchmark, copied hidden GT, test author scorer modification, Xim/BIXML product change, research-main merge, paid LLM trials or Docker evaluation.

## Original P3 source issue demonstrated on real IFC

The prior v0.41 source read host honestly exposed **Wall geometry, GUIDs and levels**, not all original source elements. `topological_test_02` original source IFC4X3/mm has two native `IfcSlab` products that were absent from the XML source read; `topological_test_04` has one. In the Python IFC arm, all these IfcSlab products are inspectable. The XML arm must not silently omit the geometric and identity context.

The two exact preregistered original IFC4X3 native-mm source hashes:

- `topological_test_02`: `8f1d9e885603f8680cb79f2a373fa36b4ecd52634ac920f2ec53c60ac465ad72`
- `topological_test_04`: `29cd44b72639ba9573aa1698a4efab4adcfbc5461c19dd85259e6a9505d303e5`

All native source Slabs are real `IfcSlab` / `PredefinedType=FLOOR` extruded physical solids, each original-mm IFC world mesh **8 vertices and 12 ordered indexed triangular faces**. The exact source is the **unaltered original mm IFC**, never the normalized metre-unit workbench as native face diagonals can be retessellated during unit conversion.

| Source Slab GUID | Source input(s) | Actual original-mm world bounding box, m | Actual native source Storey GUID | Original source `IfcRelContainedInSpatialStructure` GUID |
| --- | --- | --- | --- | --- |
| `3_DHXxtdb3wRKlXgyMiHD0` | `topological_test_02` | (0,0,-0.3) to (5.05,6.4,0) | `2JF4e6axWHqu3u0C1FZlmi` | `2JF4e6axWHqu3u0C5FZlmi` |
| `3_DHXxtdb3wRKlXgyMiHCa` | both tasks | (0,0,2.7) to (5.05,6.4,3) | `1ZGO8hrFCHqw0v0026FpFv` | `1ZGO8hrFCHqw0v0066FpFv` |

There are **3 source-Slab instances across 2 separate original public files** (2+1); the upper Slab appears with the same GlobalId in both input files. The new total of source instances is not three unique distinct Slab GUIDs. Original explicit `IfcRelSpaceBoundary` counts **0** in both source files and are not fabricated.

## Model-facing solution and immutable read-only evidence

The original source read tool `read_building_xml` now has a separate, explicitly gated v0.42 research variant:

```python
XmlSourceEditSession(
    original_public_ifc_native_mm,
    isolated_new_dir,
    experimental_original_native_slab_v042=True,
)
```

Only the two exact SHA-pinned source inputs are admitted. This variant is mutually exclusive with v0.38, v0.39, v0.40 and v0.41 experimental opt-ins. The ordinary default host's v0.1 source projection and writer remain unchanged. No additional model-facing IFC mutation, Python shell action or privileged tool is exposed.

Dedicated isolated `spec/toy_markup_original_native_slab_evidence_v042.xsd` preserves the **entire original v0.1 typed authoring grammar** and appends exactly one `OriginalNativeSlabEvidence` section **after Relations**. This section contains `NativeSlabs/NativeSlab` read-only native source records, each carrying:

- original `IfcSlab` GUID, native name/object type, `FLOOR` type, source true Storey GUID and **source native containment relationship GUID**;
- original-native-mm world mesh **every ordered world Vertex index and 6-decimal metre coordinate**, **every ordered source triangle index triple**, physical bbox and reference mesh SHA;
- explicit read-only marker `compilerEditPermission=NONE_READ_ONLY`, source original IFC SHA, normalized source-model SHA and schema; `OriginalExplicitSlabRelations` containing only real source `IfcRelContainedInSpatialStructure` relations, and a declaration of original `0` source SpaceBoundary relations.

These source products are **not** invented as editable axis-aligned `<Slab>` elements and cannot be directly mutated via this variant. The existing levels, Walls, typed geometry and prior Relations are unchanged, with no model-facing benchmark answer hints. Information access is improved specifically for these two inputs; this is **not complete original-IFC readable metadata parity**.

When the model submits a **complete replacement** `Building` via the unchanged `submit_building_xml` tool, host-side code validates secure XML and the dedicated pinned XSD, recreates immutable source-native-mm Slab catalog and requires **canonical semantic exact match**. Missing, duplicated, renamed, reordered, retargeted, different face index/vertex, forged source hash, altered GUID/relationship/Storey, or removed edit-permission flag fail closed. Only after checking does the trusted host strip the evidence section and invoke the existing v0.41 **genuine Column/Slab single-object native writer** on the original normalized source. It restores source mm units and independently reopens the final IFC before accepting last-valid XML/native candidate.

The independent verifier **does not import** the v0.42 projector/compiler or original author grader. It independently reads the source IFC4X3/mm, rechecks every ordered source world vertex to 1µm decimal, **exact integer triangle index ordering**, Slab GUID/class/name/true floor type, true contained storey/relationship GUID and all actual source Slabs. It separately invokes prior independently audited v0.41 physical output oracle, which verifies all original Root/Products/world physical meshes and real new Storey containment.

## Model-facing original-public experiment: source-only capabilities, not a task answer

Both original source inputs were read through the **actual current XML host tools** and then exercised with one **deliberately outside-target** generic box added to the complete XML:

- `topological_test_02`: read source 2 non-editable original Slabs, 16 ordered source vertices, 24 original source indexed faces, original 4 Walls and 2 Storeys; submit one new generic `IfcColumn` (8,0,0)–(8.4,0.3,2.5)m; reopened true IFC4X3/mm, original 89 Root identities, 10 Products and 2 hidden/physical Slab meshes all preserved.
- `topological_test_04`: read source 1 non-editable original Slab, 8 ordered vertices, 12 original source indexed faces, original 7 Walls and 2 Storeys; submit one new generic `IfcSlab` (8,0,0)–(9.2,1.5,0.2)m; reopened true IFC4X3/mm, original 108 Root identities, 12 Products and 1 existing physical Slab mesh preserved.

**Neither generic output solves the public original inner-space Column or closing Slab task.** There is no task-specific I0 pair for them, no original author score, and no actual matched XML/Python LLM runs. Original previously proven five task-specific developer D0/I0 CREATE pairs remain **5/15**, not seven.

## Forensic reproducibility: preserve the first report and correct an unexpected nondeterminism

The first frozen v0.42 report was prepared with the actual generated **whole candidate IFC file SHA** in the machine report. An independent subsequent replay verified all pinned source, original-mm indexed vertices/triangles, source relationships, target new IFC geometry and preservation fields, but the **new candidate full-file SHA differed** on the two tasks. In newly generated candidate IFC files, allocator-produced native relationship GUIDs/other serialized metadata can be nondeterministic despite a fixed single newly authored geometry.

**The original report is retained unchanged**:

`reports/bibimbap_v042_original_P3_source_native_slab_readonly_live_20261117.json`
SHA256: `044c78065e2e9c3c732a732a66658ba38d0a4fd41657c6818ddaa5d82f836489` — **preliminary forensic report, not the final reproducible replay contract**.

The corrected final audit **does not falsely freeze a newly generated whole-file SHA**. It explicitly marks that value nondeterministic, retains the independent original native-mm and new-target physical/semantic oracle evidence, and pins the preliminary report's unchanged SHA. Two consecutive full real source–native write–reopen audits produced byte-identical final result objects **before final freezing**. Final immutable and byte-for-byte replayable report:

`reports/bibimbap_v042_original_P3_source_native_slab_readonly_reproducible_20261117.json`
SHA256: **`f883dfb095746ceebbaa9f718e5355c61dbb2a356387b7882b400036cdf1b20e`**.

This correction **does not rewrite or delete** the first report. New result files can differ at the STEP byte level; we have **not proven complete STEP byte parity** and should never silently replace physical identity/geometry validation with whole-file SHA equality.

## Negative and regression validations

Focus test suite: `tests/test_bibimbap_v042_original_native_slab_readonly.py`. Cases cover original-45/15 ITT/question/input freeze; actual two-tool source/read/write; independent source mesh exactness; source Slab original GUID/class/name/true `FLOOR`, actual source storey and relation GUID; source SHA/class/units changes; no default host/XSD regression; input flag mutual exclusion; model attempts to alter original Walls/Slabs, editable Slab spoof, multiple new products, forged original GUIDs; mutated or removed source evidence, vertex and triangle order, relation target, metadata/digest/bbox; DTD/XXE; last-good native IFC preservation and valid revision; independently damaged original native output; preliminary and final immutable reports, exact byte replay and evidence of no paid/hidden scorer use.

Focused test runner (run from isolated v0.42 Worktree):

```powershell
$base='D:\문서\D__1_Projects\202611'
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
& $py -m unittest -q tests.test_bibimbap_v042_original_native_slab_readonly
& $py -m tools.audit_bibimbap_v042_original_native_slab_source --author (Join-Path $base 'bibimbap-author-upstream') --data (Join-Path $base 'bibimbap-author-data')
```

**Final actual process-exit test results:** 65/65 focused P3 source-Slab negative/positive tests **PASS**, 13.239s, exit 0 (ignored local log `results/v042_original_slab_final_focused_20261117.log`). Selected **26-module compatible multiversion non-Docker regression: 674 tests total / 670 PASS / 4 SKIP / 0 FAIL**, 273.648s, process exit 0 (ignored local log `results/v042_selected_nondocker_multiversion_regression_20261117.log`). Includes the existing v0.38, v0.39, v0.40 and v0.41 source/authoring slices and 65 new v0.42 source-index tests. This is **not** whole-repository validation or a matched Docker/paid-model study. Frozen v0.37 tests intentionally pin the v0.37 source-code snapshot and remain scoped to the v0.37 worktree.

**Next priority:** A rigorous **remaining original-source information parity audit** against complete native Python/IfcOpenShell read access: classes, properties, placements, source relations, materials and geometry semantics, including limitations not solved by v0.42. Do not grant task-specific answer hints or expand original public benchmark; first resolve feasible equal-read and equal-write matching, then preregister actual LLM D/I model/provider/seed/repeat, time/cost and original author score.
