# BIBIMBAP v0.14 — Actual original-source IFC4X3 hosted Window-only native deletion (nonblinded developer D0)

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/142
**Date:** 2026-11-14, Asia/Seoul. Independent research repo `pikaybh/bim-markup-bench`. Stacked after v0.13 Issue #140/Draft PR #141. NOT production Xim/BIXML. New opt-in v0.14 modules only; no old compiler/projector/scorer or prior v0.1–v0.13 evidence modifications, original IFC input file writes, or paid model/provider requests ($0).

## Scope: a narrow REAL native write, not an editable original IFC model

**Implemented:** true native IFC4X3 metre-normalized source-backed **IfcWindow delete-only** for exact original `IfcWindow` entities with unique original native `IfcRelFillsElement`, unique source `IfcOpeningElement`, original `IfcRelVoidsElement` and source host `IfcWall`. Supports **1 to 8 distinct Windows per atomic transaction** (source relationship survivorship and exclusive dependency checks), including previously v0.13 *opaque read-only* Windows. The source host original **Wall and source original Opening/Wall void are retained with identical native geometry**: removing a Window does **not** remove/patch its wall hole. This is *Window only*, not `DELETE_WINDOW_AND_OPENING`, and not a Window MOVE/CREATE, Opening UPDATE or Door/Space/Beam edit.

**Not implemented:** full original IFC4X3 BIM editing, remapping original IfcMappedItems, generalized `IfcSpace`/IFC4/IFC2X3 edit, IfcBeam physical trimming, unrelated IFC4X3 host/window geometry updates, 45/45 original full-task parity, or same-model matched Python I0 / LLM comparison.

### Why this is a direct-markup declarative edit, not a command wrapper

The editor sees a NEW strictly XSD-validated, source-SHA+catalog-SHA-pinned XML ***complete original Window substate*** (not all native IFC Products), namespace `urn:bim-markup-bench:source-window-delete:v0.14`, with root `NativeWindowState editScope="FULL_ORIGINAL_WINDOW_INVENTORY_DELETE_ONLY"` and one `Windows/Window` node for **every original source Window**. Each node has original source `ifcGuid`, its unique `originalOpeningGuid` and `originalHostWallGuid`, IFC class and immutable source ownership. The user/model can **only remove existing Window XML records**; the trusted compiler computes the set difference against every original Window. It rejects changed original GUIDs, host Opening/Wall, duplicate or invented Windows, new XML commands, modified attrs, undeclared/unsafe XML, changed source/catalog SHA, schema relabeling, no-ops, unknown dependencies, >8 removals, removal of all original shared-metadata members, and writes to an existing destination. The earlier **v0.13 read-only source catalog remains permanently noneditable**; it is not promoted into a general IFC mutation API.

XSD: `spec/experimental_original_hosted_window_v014.xsd`. Source-owned builder/compiler: `src/runtime/experimental_v14_native_window_delete.py`. Trust boundary uses the existing XML security check, parser without external entities/DTD/network, strict XSD and source inventory identity. The native source IFC remains byte-identical. Native mutation is performed on a fresh **source clone**, staged in a temporary directory and committed to an **unused destination only after native validation**. No generated output is permitted to overwrite original source or frozen benchmark artifacts.

### Native IFC ownership and integrity

Every original target Window has the following *actual source native inverse graph* in the two pinned public IFC4X3 samples: unique `IfcRelFillsElement`, `IfcRelContainedInSpatialStructure`, `IfcRelDefinesByType`, `IfcRelAssociatesClassification`, `IfcRelAssociatesMaterial`, and two independent sole-owned `IfcRelDefinesByProperties` relationships pointing to two sole-owned `IfcPropertySet` objects. The original Opening has exactly one `IfcRelVoidsElement` to the source Wall and one `IfcRelFillsElement`. Preflight verifies exact multiplicities, sole ownership and the affected shared relations' nonempty member sets after removing targets.

For each Window, delete *only* source-owned closure of **7 native IFC Roots**: the Window, its original Fill relationship, original exclusive material-association relationship, two original Pset-definition links, and two exclusively owned Psets. The source original Opening, host Wall, original `IfcRelVoidsElement` and all other source metadata remain. Three classes of **shared** native relations retain all other original members: `IfcRelContainedInSpatialStructure`, `IfcRelDefinesByType`, and `IfcRelAssociatesClassification`.

IfcOpenShell's `root.remove_product` has the side effect of reordering `IfcRelDefinesByType.RelatedObjects` and generating a current-time `IfcOwnerHistory`. Trusted v0.14 only for those exact source-shared relations **restores original sequence and original source OwnerHistory** (deletes orphan generated history), **not** an invented audit timestamp. The complete candidate is reloaded from disk, and native validation checks:
- Exactly expected source-owned rooted dependencies are removed, **no new original Root**.
- Every unrelated original rooted object is byte/string-identical at native STEP identity level; shared relationship changes are *only the exact deletion of named Window membership*, not material/type/classification metadata.
- Original host voids remain and `IfcRelVoids` source identity is unchanged; deleted Window Fill relations are absent, while other Windows and Fills remain.
- All surviving source `IfcProduct` physical world geometries match the original actual native world triangulation vertex multiset, face count and volume. No fake axis-aligned replacement.
- The output has the exact original IFC4X3 schema and metre units, introduces no new IFC STEP entity or timestamp, and the source/destination SHA remain stable.
- Commit uses an atomic file move only **after** full physical original IFC validation. Any failure leaves original native IFC and destination untouched.

## Fully independent original IFC-only oracle

`tools/oracle_bibimbap_v14_window_delete.py` imports only IfcOpenShell/NumPy and Python standard library; it imports **neither** v0.14 compiler, v0.13 source catalog/projection, XML binder, original author's scorer nor hidden GT solution data. It independently reconstructs original source Window–Opening–host and exclusively-owned inverse Root closure, computes affected three shared-root membership sets, checks full original-vs-result Root/STEP/IfcProduct inventory, independently regenerates **every retained physical native world mesh**, verifies all original host void and original Window-only deletion semantics. It rejects unexpected original void deletion, shifted original Wall geometry, added/deleted unrelated objects, relabeled source schema or incorrect Window-target declarations.

This oracle is strict native source consistency evidence, **not** the original BIBIMBAP author metric; the two are recorded independently and never substituted for each other.

## Real original public IFC tests: actual native write

| Frozen original source | Native Window deletion | Actual original Root closure removed | Retained original Root count | Actual world-space shapes unchanged | Native IFC oracle |
|---|---:|---:|---:|---:|---|
| `geometry_test_18`, IFC4X3, original 19 Windows | single (previously opaque v0.13) | 7 | 350 | 54 | PASS |
| `geometry_test_19`, IFC4X3, original 7 Windows | single (previously opaque v0.13) | 7 | 164 | 21 | PASS |
| `geometry_test_18`, same source | **6** original Windows (developer batching safety test) | **42** | **315** | **49** | PASS |
| `geometry_test_19`, same source | **6** original Windows (developer batching safety test) | **42** | **129** | **16** | PASS |

These six-Window batch tests verify true native deletion and physically preserved unrelated source scene; **they are not original natural-language solution selections or original author grades**. The one-Window experiment was repeated more than one clock second later with an **exact identical complete resulting IFC SHA256**. Original raw source IFC and metre clone were verified byte-identical before/after every compilation. All tests use fresh temporary paths.

## Fixed original-public developer D0: actual physical original prompt interpretation

`tools/audit_bibimbap_v14_original_hosted_d0.py` conducts separate **developer-fixed original public task source-only D0 candidate generation (not a preregistered study)**. It receives only the pinned original public task question and the original source IFC. **No original scorer/hidden target/GT is consulted until the complete declarative Window state/candidate and full independent native scene oracle are frozen.**

- `geometry_test_18`: public text explicitly says remove Windows in west Walls, `+X` east. Compute original source Wall `IfcPolyline` world axes, find minimum world-X north/south original Window host Wall, select exactly **2** original actual source Windows. The public direction and source geometry, not grader target GUIDs, determine selection.
- `geometry_test_19`: parse the **publicly named Wall's GlobalId** from the original question. Compute its exact native world axis and the original source host Wall lines. Select Windows on the unique parallel, separately positioned original opposite host Wall when the source Window's native Opening placement and original `IfcWindow.OverallWidth` span overlaps at least half the opening length on the named Wall's source projected horizontal interval. Select exactly **2** original source Windows. No hidden target is consulted; unexpected source geometry is rejected.
- For each original case the original IFC is normalized to metres with native IFC4X3 schema preserved; developer removes precisely those two Window nodes from the complete **v0.14 declarative original Window substate**; trusted v0.14 compiler produces native candidate. Entire output candidate and source SHA is frozen; **independent original IFC-only oracle passes before any author scorer call**. A separate candidate is converted back to original public **millimetres** before invoking the untouched pinned original BIBIMBAP author worker. This is fixed **developer D0**, NOT a real LLM model result or a blinded holdout.

### Critical original author scoring defect: these two public cases are presently UNSCORABLE

The unmodified pinned original author `geometry_test_18.py` and `geometry_test_19.py` invoke their `run_delete_integrity_check` with hard-coded original Window target GUIDs. **Some of those source test GUIDs do not exist in the pinned ORIGINAL raw IFC file before the edit**. This is independent of v0.14 candidate selection or native IFC correctness. The author worker calls `by_guid()` on those nonexisting original source GUIDs, raises a `RuntimeError` and returns **`AUTHOR_WORKER_FAILED`**, not a score. This was reproduced directly on independently hash-verified **byte-identical frozen native candidates**; source and scorer were never modified to generate a desired score.

| Original public task | Author scorer static target GUIDs declared | Actually present in pinned original public IFC | Absent **before** any edit | Original-author result AFTER candidate frozen |
|---|---:|---:|---:|---|
| `geometry_test_18` | 6 | 2 | **4** | `AUTHOR_WORKER_FAILED / RuntimeError` |
| `geometry_test_19` | 2 | 1 | **1** | `AUTHOR_WORKER_FAILED / RuntimeError` |

The postfreeze forensic function reads the public original scorer test's static `WINDOW_GUIDS` declaration only **after** the candidate and scorer have run, reports **counts only**, and never exposes those author-target GUID values to the XML author or native compiler. It does not patch author grader, rewrite source/dataset, fill in absent GUIDs, invent a replacement score or hide the two original cases from the **45-case denominator**. In any paper these two must be reported **unscoreable under pinned original author/data revision**, not zero, 0.5 or 1.0 model scores. This failure is not evidence that v0.14 failed native geometry semantics; conversely an independent native oracle PASS is not an original author full-task PASS.

Pinned original author revision: `667004e16bd38fd7d538bcee56191465429fd975`. Pinned original public data revision: `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`. Original scorer target GUID list is never stored in the new repo report.

**v0.14 original source/D0 evidence report:** `reports/bibimbap_v014_original_geometry18_19_native_hosted_window_developer_d0_20261114.json`, SHA256 **`4709b5ae0408cca79a46ce226c57754459a5690ef7c432d84bf4b3c090bcd02e`**. The initial prior unclassified failure report was moved to local ignored `results/` and was not committed; no v0.2–v0.13 historical D0 report was replaced.

## Remaining native Space and Beam requirements — original IFC source-grounded

The full native v0.13 read-only catalog still represents these original source types faithfully but **only as original immutable references**:
- `topological_test_14` original IFC4X3 source: **4 original IfcBeam products**, each with **two mapped `IfcMappedItem` representations** and `IfcRelDefinesByType` shared typology, three property relationships, `IfcRelContainedInSpatialStructure` to original Storey. Physically trimming beams requires source-mapped solid geometry and accurate hosted/physical intersections; merely editing a bounding box would be false equivalence.
- `topological_test_01` original IFC4X3 source: actual `IfcSpace` is **`IfcFacetedBrep`** with `IfcRelAggregates` under the original BuildingStorey (not a direct `IfcRelContainedInSpatialStructure`). `topological_test_03` has two such original Brep Spaces with analogous aggregate/type/Pset edges. Space delete/update must obey original native geometry, boundary, aggregation and ownership graph; a toy box or invented containment would be incorrect.

Neither Space nor Beam native authoring is implemented in v0.14; **next separately frozen v0.15** should tackle Space deletion/aggregation first, then mapped Beam physical trimming through actual world/native type geometry or explicitly unsupported safe rejection. Preserve source original semantics and audit against original author metrics only after fixing or formally identifying source/scorer mismatches.

## Verification and reproduction

New versioned files:
1. `spec/experimental_original_hosted_window_v014.xsd` — strict complete source Window inventory XML schema.
2. `src/runtime/experimental_v14_native_window_delete.py` — source-backed declarative Window state + trusted, atomic, clone-only Window delete compiler/Root/mesh validation.
3. `tools/oracle_bibimbap_v14_window_delete.py` — independent native IFC-only full scene oracle.
4. `tools/audit_bibimbap_v14_original_hosted_d0.py` — fixed source-only public task D0 + postfreeze original author runner and missing-source GUID count forensics.
5. `tests/test_experimental_v14_native_window_delete.py` — actual real original cases, single/batch operation, deterministic candidate SHA, 18 fail-closed/negative cases.
6. `tests/test_bibimbap_v14_original_hosted_d0.py` — original public 45 denominator preservation, developer source-only semantics, independent oracle, author scorer unscoreable proof, negative public prompt drift and audit determinism.
7. `reports/bibimbap_v014_original_geometry18_19_native_hosted_window_developer_d0_20261114.json` — source SHA-pinned original PUBLIC task D0 after unchanged original-author scorer, **UNSCORABLE** with exact source GUID counts, no hidden target values, no original IFC committed; SHA256 **`4709b5ae0408cca79a46ce226c57754459a5690ef7c432d84bf4b3c090bcd02e`**.
8. `tools/audit_bibimbap_v14_window_delete.py` — a SECOND offline, **no-scorer** source-only audit for exact one previously v0.13 opaque Window and a deterministic six-Window batch from each original source. Pins the original source IFC and public author/dataset revisions, independently validates native full-scene root/shape and never consults target GUIDs, hidden GT or a scorer. Output destination is exclusive-create. This is an **unscored native operation smoke experiment**, not a full original task D0.
9. `reports/bibimbap_v014_original_native_window_delete_20261114.json` — four independently verified physical native single/six Window candidates; **SHA256 `c57927e92e1955a231bd65da2d4804794fac6c9af1a023d49da6ae69b6865e36`**, generated twice from original source to byte-identical complete JSON. Zero model/scorer calls.
10. This protocol document.

**New tests:** **40/40 PASS** (29 native edit source and negative tests, 11 original public D0/scorer source consistency tests). **Full combined v0.14 + v0.13–v0.1 native original source/edit/original public45/matched25 offline framework regression: 333 tests run / 331 PASS / 2 optional SKIP / 0 FAIL, exit 0, 245.963 seconds.** Old v0.1–v0.13 code and prior D0 remain unchanged. No paid model or Python I0 control calls. Original author/D0 repo/data Git trees clean. Complete v0.14 original public D0 report was rerun after a clock interval with **byte-identical SHA256 `4709b5ae0408cca79a46ce226c57754459a5690ef7c432d84bf4b3c090bcd02e`**. The unscored one/six source-only operation audit was likewise reproduced byte-identically after a separate complete native IFC run, SHA256 `c57927e92e1955a231bd65da2d4804794fac6c9af1a023d49da6ae69b6865e36`.

```powershell
$base='D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue142-hosted-delete-v014')
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$author=Join-Path $base 'bibimbap-author-upstream'
$data=Join-Path $base 'bibimbap-author-data'

& $py -m unittest tests.test_experimental_v14_native_window_delete tests.test_bibimbap_v14_original_hosted_d0 -v

# Output must be NEW: immutable reports are exclusive-create only.
& $py -m tools.audit_bibimbap_v14_original_hosted_d0 `
  --author-repo $author --dataset $data `
  --output-json 'results/NEW_UNUSED_original14_D0_reproduction.json'
```

## Next priority and scientific limits

Proceed without changing past artifacts to **source-faithful original IfcSpace native deletion/creation relation validation** (original `IfcFacetedBrep`, original `IfcRelAggregates`, source boundary preservation), followed by **IfcBeam mapped source-world solid trim** (not generic bbox) in a separate prospective v0.15 contract. Also record formally that geometry18/19's original BIBIMBAP author/Data mismatch is an objective benchmark-data blocker requiring authors' correction/new labelled version; any later modified reference dataset needs a new held-out preregistered protocol and may not be retroactively substituted into historical comparison. Original developer D0 is not proof that a real LLM can select/manipulate the Windows; Python I0 equivalent candidate for these tasks remains unrun. Any new paid paired LLM run still requires explicit model budget approval.

## Independent coordinator broad-suite caveat (2026-11-14)

The 333-test regression statement above refers to the previously selected original BIBIMBAP/native compiler/LLM-harness suite, **not** the entire repository test inventory. A separate independent `python -m unittest discover -s tests -q` run on this isolated v0.14 Windows worktree collected **832 tests, 9 failures, 65 errors, 67 skips (exit 1)**. Many errors were unrelated pinned BIM-Edit/older gate prerequisites, including 39 missing `data/tasks.jsonl` accesses, a missing ignored historical BIBIMBAP preflight, and Windows `cp949` decode exceptions. The frozen `data/tasks.jsonl` (`9bdf9536...`) and historical preflight were subsequently copied byte-identically from existing local worktrees into gitignored test-only locations, without modifying original files. A selected older-gate rerun with UTF-8 still had **34 tests, 4 failures, 4 errors, 2 skips**: those are *not* claimed as fixed or unrelated to all possible code changes. Full repository-wide regression is therefore **NOT clean** and is not superseded by the scoped native pass.

As a separate independent current-version verification, both new v0.14 test modules passed **40/40 (70.370 seconds, 0 failures)**; the original D0 author worker remains unscoreable on the two referenced public cases and is not converted to an official benchmark score. No new paid model calls or hidden-GT access occurred. Do not cite the 333 selected-suite result as 832-test repo-wide evidence; future work should provide a reproducible explicitly listed suite manifest, fixture admission gate, and full-run stdout hash before upgrading the acceptance claim.