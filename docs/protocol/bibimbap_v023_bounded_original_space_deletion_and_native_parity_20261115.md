# BIBIMBAP v0.23 — Original-public Room deletion: real declarative XML → IFC, independent I0 and frozen original-author scorer

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/160
**Stacked parent:** v0.22 Draft PR #159, exact frozen parent commit `bc05b2dfb8981174ba9a0dafaa0f872a290e4f43`.

**Research-only implementation.** Not Xim/BIXML production, not an LLM performance trial, not a new version of the original author benchmark or scorer.

## 1. Why this source operation matters

The prior v0.22 per-task audit independently opened all **31 original public IFC sources**, confirmed all **480 native original `IfcProduct` identities**, and identified 9 original tasks with incomplete object-role coverage in the safe editable XML, plus 3 original IFC2X3/IFC4 tasks which the current IFC4X3-only XML session refuses. These are **coarse necessary source coverage conditions**, not a proof all missing native entities are the required target for each task.

A particularly informative untouched original-public task is **`test_20`**, whose PUBLIC question requests deletion of one named `IfcSpace`. Its exact original IFC4X3 millimetre source has **three rooms**, with **two existing `<Space>` nodes in editable XML and one native room omitted from that editable subset**. Crucially, the specifically named PUBLIC target **is** present in the editable XML. The partial class-coverage gap should therefore not be promoted to "the original task is impossible."

Before v0.23 the real `XmlSourceEditSession` rejected removing the one `<Space>` element, with `UnsupportedIFCMutation: Only safe removal of a standalone Wall or existing hosted Window is supported`. A developer-authored independent imperative IfcOpenShell edit could delete the original room, but the unmodified original author scorer returned **0.5** (object absence 1.0; integrity constraint 0.0), so neither a perfect author score nor pure D-vs-I model parity was demonstrated.

## 2. Actually implemented compiler support

- `src/runtime/space_delete.py` is a **separate restricted trusted native compiler backend** reached only when the before/after semantic graphs show exactly **one deleted existing `Space` node** and exactly one derived `aggregated_in_storey` relationship removal. The authoring arm still submits **complete ordinary declarative XML**, removing its existing `<Space ... />` element; the input is never an imperative `<Delete>` or hidden Python command. This preserves the declarative-vs-imperative scientific distinction.
- The existing `src/runtime/compiler.py` routes only that narrow graph delta to the new backend. All pre-existing Wall, hosted Opening/Window/Door, topology and Space partition operations remain on their existing routes.
- The new original native eligibility gate requires an original source-bound **`IfcSpace`**, one parent **`IfcBuildingStorey` aggregation** with surviving sibling rooms, no child object placements, and only conservatively recognized individually owned `IfcRelDefinesByType`/`IfcRelDefinesByProperties` metadata. Existing Space boundaries, shared relationship memberships, unrecognized associations and unrelated graph changes cause **fail-closed rejection**.
- Mutation uses the trusted host **IfcOpenShell `root.remove_product`** on a separate loaded/cloned IFC file. An exclusive `stage_and_commit` transaction publishes the candidate only after independent re-open and validation. The original public IFC cannot be overwritten, and the source file SHA is rechecked before/after.
- The validator compares the **full original native `IfcRoot` GUID/class and unchanged root entity strings**, permits only deletion of the target Space and its own owned type/metadata links, and permits one original storey aggregation to drop exactly that Space while preserving sibling rooms. It also checks **every surviving original STEP entity** for unexpected changes. In the real original source the Space's shape is listed in a shared `IfcPresentationLayerAssignment`: removing ONLY its one representation is separately preflighted and verified; all other original layer members and metadata must survive. This prevented a naïve "all other STEP rows must be byte unchanged" rule from incorrectly rejecting valid native deletion, without broadly allowing unrelated geometry edits.
- The candidate's **entire typed semantic graph is re-projected and compared** to the complete submitted XML state after IFC mutation, not only the target GUID. All other existing native `IfcProduct` identities/classes, including the omitted room, remain intact.

This feature is strictly for the **tested bounded class of existing source `IfcSpace` deletion**. It is **not** a promise of arbitrary room removal with boundaries/complex relationships, general IFC entity editing, or IFC2X3/IFC4 support.

## 3. Real matched developer experiment

`tools/bibimbap_v023_original_space_i0.py` independently performs the original PUBLIC target deletion using native IfcOpenShell, with no XML parser, XML compiler, private author-target lookup or model calls. Both I0 and D0 undergo the same original millimetres → metres → original millimetres file/unit envelope, enabling a strict apples-to-apples **full native IFC byte comparison**. The actual source edit for D0 changes one complete XML state document, not a geometry command.

`tools/audit_bibimbap_v023_original_space_delete.py` runs both arms **on the actual pinned original PUBLIC IFC**, and calls the unchanged original author scorer **only after both outputs exist**. It also independently checks the original 43 `IfcProduct` objects against the 42 candidate products: exactly one target Space removed, every other original product GUID/class unchanged, and both other original Rooms retained.

| Real original `test_20` measurement | D0 declarative XML | I0 native Python |
|---|---:|---:|
| Native candidate IFC4X3 | **PASS** | **PASS** |
| Target original `IfcSpace` removed | **PASS** | **PASS** |
| All 42 unrelated original `IfcProduct` identities/classes preserved | **PASS** | **PASS** |
| Exact serialized full native IFC SHA-256 | `2a3fb1e29e7b6d929b2dd87de898d414d75c944cf8c2fa7d95fa0d7b619162d3` | **identical** |
| Original author score, unchanged grader | **0.5** | **0.5** |
| Original author `object_not_exists` metric | **1.0** | **1.0** |
| Original author `integrity_constraint` metric | **0.0** | **0.0** |
| Actual LLM calls | **0** | **0** |

**Independent source/scorer discrepancy diagnosed (do not silently patch):** The original `data/tests/test_20.py` invokes `run_delete_integrity_check`, which includes the original `data/tests/delete_integrity.py::spatial_containment_deleted` predicate. That predicate obtains `ifcopenshell.util.element.get_container(original_space)` and requires a native container before performing the check. **The ACTUAL original source Space has a native storey *aggregation* but `get_container(original_space) is None`.** Thus this integrity subtest is unsatisfied even though our independent root/STEP oracle and D0/I0 byte parity confirm exactly the same native IFC output. Record the original grade as **0.5**; the original scorer and source are never modified, and the score discrepancy cannot be counted as a D/I representation effect. This finding is distinct from the previously documented two Window tasks with originally missing source-reference targets and the `test_16` native/original-score disagreement.

## 4. New reproducible evidence, rigorous limits

- Sanitized new report `reports/bibimbap_v023_original_test20_space_delete_D0_I0_native_parity_20261115.json`; SHA-256: `9abcc4ebd21c18891bf08307624a19f6012a981455eca7db89051ae70ce86102`. Contains no raw IFC, full original public question, target GUID, hidden original scorer answer list or user credentials.
- Live independent **second audit** from the same exact source reproduces the full JSON SHA, including both original author scores and the byte-identical IFC outputs. Tests re-open the original native file, check complete `IfcProduct` class/identity preservation, confirm no source mutation and ensure the I0 implementation imports **no declarative XML compiler**.
- **New 27/27 tests PASS**, 12.902s unittest / 18.422s enclosing process, exit 0. Negative probes reject missing GUID, wrong class, shared property relationships, an added IfcSpaceBoundary, missing storey aggregation, another room/wall removed in the same declaration, forged/unrelated surviving root changes, removed native product, unexpected shared presentation layer changes, invalid XML instruction and original IFC2X3/IFC4 schema. Both prior source and previously frozen v0.22 report remain untouched.
- Historical frozen counts **remain intact** as v0.22 evidence: prior developer D0/I0 byte-identical original tasks **5/45**, prior both original-author-scoreable developer pairs **3/45**, two original Window reference mismatches, 40 previously untested. **This one new independent source-native developer pair now gives cumulative 6/45 actual D0/I0 byte-identical developer tasks and 4/45 callable author scorer pairs; 39 other original tasks remain untested under the same protocol.** It does **not** give 6 original LLM results, 4 perfect author scores, or complete native write-capability parity.
- No real LLM/model inference, no provider cost, no original author scorer edits, no raw original native IFC file committed, no main/Xim/BIXML changes. The imperative I0 is developer-owned local trusted Python, **not** the earlier v0.19 Docker one-shot model-code sandbox and **not** a production-safe arbitrary-code executor.
- The prior v0.22 reported 9 source-role gaps and 3 schema-admission failures remain recorded. The successful original `test_20` shows **one of the nine class-coverage gaps does not preclude deleting a specific *present, eligible* XML room**. It does **not** eliminate that case's native source-view incompleteness, or imply support for all nine role-gap cases.

## 5. Reproduction

```powershell
$base = 'D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue160-safe-space-deletion')
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

& $py -m unittest tests.test_bibimbap_v023_original_space_delete -v

# NEVER overwrite prior evidence; choose an unused ignored output path.
& $py -m tools.audit_bibimbap_v023_original_space_delete `
  --root . `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') `
  --output 'results/NEW_UNIQUE_v023_original_test20_D0_I0.json'
```

**Actually completed v0.23 selected cross-version regression:** v0.3/v0.4/v0.14–v0.23 (14 modules, including original IFC Docker and author scorer), **215/215 PASS**, 0 errors/failures, 148.949 seconds unittest / 151.235 seconds enclosing process, exit 0. New sanitized report `reports/bibimbap_v023_scoped_215_regression_and_scorer_precondition_20261115.json`, SHA-256 `fb1b318b6a3c66d8badf0d405fafe73ec7d75d97cecc2b73a2f013795322651b`. That report independently confirms native original Space **aggregated** in its storey but **not contained**, exactly matching the unchanged original scorer's unmet containment precondition. No orphaned v0.19 worker Docker containers or modifications to original author/data repositories. This does **not** claim the historical whole-repository 832-test discovery is green.

## 6. Next research priority

Keep full **original public 45 intention-to-test** denominator. Next, fix **other *task-relevant* role and source-schema gaps** conservatively and perform actual developer D0/I0 native edits with independent oracles and unmodified scorer for each selected task, not silently infer success from read-only catalogs. Pre-register the causal vs unequal-system estimand before using a model. The model security broker remains offline-only; **any real matched LLM run requires separately agreed provider/model and hard budget cap plus audited information/write/feedback parity.** No such run is authorized here.
