# BIBIMBAP v0.24 — Original-public hosted Opening deletion and IFC4X3 Window dependency

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/162
**Parent (frozen):** v0.23 Draft PR #161, commit `2390662cd2266907aabaf8fc81dfc0e1a60db286`. **Research-only**: the original author Git HEAD, public dataset, original 45-task denominator, evaluator, previous reports, Xim/BIXML product and `main` are never modified.

## 1. Exact original public task selected

The original public `test_18` asks to delete a named `IfcOpeningElement` in the original public `basic_tasks.ifc` (IFC4X3, millimetres). The source file's opening has a **single native `IfcRelVoidsElement` to a Wall and a single `IfcRelFillsElement` to an existing `IfcWindow`**. Both source objects are represented in the current safe declarative XML state, unlike some other benchmark objects that are opaque. Deleting only `<Opening>` violates the existing XML keyref because `<Window>` refers to it. Deleting exactly the two existing XML nodes was previously rejected by a door-specific planner.

To avoid an artificial *direct XML* advantage or an impossible dangling Window, v0.24 defines the XML intent as the **complete edited `<Building>` state**, with exactly one original `<Opening>` and its one filling `<Window>` removed. The representation is declarative state, **not** a new imperative `<Delete>` tag, native IfcOpenShell tool, patch, script, or privileged model command.

## 2. Implemented trusted compiler feature

The new `src/runtime/opening_window_delete.py` runs only for one precise two-node graph delta (an existing original Opening and its existing original Window); `src/runtime/compiler.py` dispatches it without changing the existing Door/Opening, Space, Wall, or other topology command behavior.

Native preflight is **fail-closed** and source-proven: IFC4X3, source-bound original GUIDs/types; one host Wall, one native fill and void relation, exact seven-class inverse inventory for the Window, two individually-owned `IfcPropertySet` links, one exclusive type link, one exclusive material link, one uniquely classified Window, a surviving multi-element building-storey containment relation, no unknown boundary, shared type, source-dependent placement, property set-sharing or unrecognized association. The Window's physical `IfcShapeRepresentation` must have a single matching shared `IfcPresentationLayerAssignment` and must not be owned by another original product.

The trusted backend deletes **only** the original Window and Opening with `ifcopenshell.api.root.remove_product` in a separate native in-memory file, using exclusive `stage_and_commit`, retaining the original read-only IFC source hash. The native verifier compares every original and result **`IfcRoot` GUID/class**, requires exactly **10 bounded native root deletions** (two target products, void/fill relations, owned metadata/type/material), two surviving membership relationship updates (storey containment and source Window classification), and validates exactly one original presentation layer membership removal. Every **surviving native STEP record** is checked unchanged except those three verified relation/layer edits; no new native STEP IDs and no other `IfcProduct` deletion/class reassignment. Removed native nonroot geometry/property items must be descendants of approved removed roots and have no surviving unapproved inverse references. Finally, the **whole reprojected native XML typed graph** must equal the submitted XML state; unrelated original projected elements cannot disappear. Failed preflight/validation does not publish output and does not advance the original XML session.

This feature does **not** support arbitrary Opening/Window deletion, IFC2X3 or IFC4, Door deletion from this public source, an unknown host, source schema conversion, or all 45 original operations. It is one original-public, independently verified native writing slice.

## 3. Actual developer paired native result and separate unchanged author grader

`tools/bibimbap_v024_original_opening_i0.py` is separately coded **developer-owned** native Python/IfcOpenShell. It reads only the original source and public named Opening, independently finds its single native Window, removes Window first and Opening second and restores original millimetre units; it imports **no XML compiler** or author scorer. The audited D0 experiment uses `XmlSourceEditSession` on the exact original public IFC and submits a complete updated XML source document. The immutable original author test is called **after output** on both separate candidates.

| Original public `test_18` measure | D0 declarative XML → trusted native IFC | I0 independent native Python |
|---|---:|---:|
| Original IFC4X3 millimetre input | exact pinned original | same original |
| Requested Opening and filling Window removed | **PASS** | **PASS** |
| Other 41 original `IfcProduct` GUID/classes preserved | **PASS** | **PASS** |
| **Entire native output IFC SHA-256** | `41dc92e4d667e82f14a0355ac55471429213ae95cad859713c5917e275c354ea` | **exact same bytes** |
| Unmodified original author grade | **0.5** | **0.5** |
| Original author `object_not_exists` | 1.0 | 1.0 |
| Original author `integrity_constraint` | 0.0 | 0.0 |
| Real model inference calls/provider spend | **0 / $0** | **0 / $0** |

One deterministic sanitized immutable report: `reports/bibimbap_v024_original_test18_opening_window_D0_I0_20261115.json`, SHA-256 `a31e74dacdece9924304de6c74c5d9e8769497a8ad68287779ddd4a37bac6a67`. A separate real source audit on the identical pinned public source re-generates **exactly identical full JSON bytes**, including original scores. **Do not include public target GUIDs, hidden grader references, raw IFC, original question full text or user credentials in Git.**

### Why the original author grade is 0.5 (independently diagnosed)

The unchanged original `data/tests/delete_integrity.py::run_delete_integrity_check` requires **all** of its predicates, including `data/tests/integrity_utils.py::non_target_elements_unchanged(original,edited,[public_opening_guid])`, which checks surviving `IfcRoot` entities against that **single Opening** target. In the actually executed original Python result:

- `wall_connections_deleted`: **True**
- `spatial_containment_deleted`: **True** (unlike original public `test_20`, the Opening DOES resolve a native `IfcBuildingStorey` container)
- `openings_deleted`: **True**
- `filling_deleted`: **True**
- `aggregations_deleted`: **True**
- `non_target_elements_unchanged`: **False**

At least the Window is removed as a necessary native dependency, while the original grader's target list includes only the Opening, so its non-target preservation check rejects the output. The original source's `get_container(opening)` is **not None**. This is *not* the same scorer precondition as the earlier `test_20` Room test. **Never silently reinterpret 0.5 as 1.0 or alter the original author implementation; disclose source/task scope and author-grade mismatch when analyzing LLM performance.** This is a scientifically material, preexisting evaluation constraint, not a demonstrated D0-vs-I0 representation difference; both produce byte-identical native outputs and identical scores.

## 4. Strict study accounting and limits

- Prior v0.23 proven developer-only original native IFC D0/I0 byte-equal: **6/45**. This genuinely adds one distinct original public task, yielding cumulative developer output byte parity **7/45** and both original-author-scoreable developer pairs **5/45**. **38 original tasks remain untested** under that paired writing protocol.
- The **original 45 intended tasks** (15 each basic/geometry/topology; 15 create/update/delete) remain intact. The original two unscoreable Window reference mismatch cases remain classified and unchanged. Native output equality **does not** establish LLM authoring success, equal source representation completeness, equal tool affordance, causal XML advantage, or acceptable all45 coverage.
- Original schema exclusions IFC2X3/IFC4 for current XML session remain, as do other task-relevant source-role/relationship gaps. Real paired LLM trials **0**, budget **$0**, no model-generated untrusted Python enabled.
- Native preflight/root/STEP guards are intentionally conservative; unrelated source sets (including original opaque objects), original artifact SHA and original grader remain read-only. The local Windows experiment uses separate personal research worktrees, not Xim/BIXML production.

## 5. Reproduction on the authorized research workstation

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$repo = Join-Path $base 'bim-markup-bench-issue162-opening-window-delete'
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
Set-Location $repo
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

& $py -m unittest tests.test_bibimbap_v024_original_opening -v

# Give an unused output path. The auditor refuses overwrites.
& $py -m tools.audit_bibimbap_v024_original_opening `
  --root . `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') `
  --output 'results/UNIQUE_new_v024_test18_audit.json'
```

**Actually completed selected cross-version regression:** 15 modules covering selected v0.3/v0.4/v0.14–v0.24, including actual original IFC Docker worker and original author scorer: **245/245 PASS**, 0 errors/failures, 171.775s unittest / 176.25s enclosing process, exit 0. New v0.24-specific positive/negative tests **30/30 PASS** (23.955s unittest / 30.109s enclosing process). Frozen independent QA and original-author posthoc subcriterion report: `reports/bibimbap_v024_scoped_245_regression_and_original_scorer_diagnostics_20261115.json`, SHA256 `04a739c07b362a0fcf70ac4eaf57e60b1ab75a2e7d7c433e99c5f263a04b3eba`. Actual unmodified original scoring subcriterion diagnostic confirms all five deletion predicates True but `non_target_elements_unchanged` False, the Window dependency being excluded from the single original Opening target list. Pinned original author and data Git worktrees clean, old Docker-worker orphan containers 0. **Do not claim a full historical 832-test repository discovery green or a full original45 matched model experiment.**

## 6. Next technical priority

Continue selected original `test_17` hosted Door deletion, where the original public Door has a **different real inverse/root metadata shape** from the earlier safe Door fixture, or `test_19` connected Wall deletion, where real original source path/connection/property memberships require independently verified narrow native cleanup. Reproduce each original task with source-bound XML and independent I0, preserve immutable original scorer, and pre-register paired tool-budget/source information parity before any actual LLM inference.
