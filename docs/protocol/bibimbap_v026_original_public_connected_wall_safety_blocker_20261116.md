# BIBIMBAP v0.26 — Original public `test_19` connected Wall: reproducible native safety blocker

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/166

**Research-only stacked checkpoint.** Frozen previous v0.25 Draft PR #165 at commit `11b32352661e1e3f684071a4a99e811ccaf86598`. Neither Xim/BIXML product, `main`, original author benchmark and data Git repos, original author scoring code, raw original IFC files, nor previous v0.23–v0.25 frozen results are edited.

## 1. Objective and actual source evidence

The previously successful developer-only original IFC D0/I0 exact output parity total is **8/45** source cases. The next original PUBLIC benchmark task, `test_19`, asks to remove one identified `IfcWall` in the original IFC4X3 millimetre `basic_tasks.ifc` file. The native source has **43 `IfcProduct` objects**. The public target Wall is a single existing source object in the XML projected state.

Native original inverse dependencies of that Wall include exactly **two** `IfcRelConnectsPathElements` to **two other original neighbor Walls**, three individually assigned `IfcRelDefinesByProperties` with three separately related `IfcPropertySet` roots, three multi-member type/material/classification relationships, and a multi-member building-storey containment relation. It has no hosted original opening. Its geometry is an original physical swept solid and a 2D curve representation, both assigned in a shared `IfcPresentationLayerAssignment`.

An XML-only removal of the `<Wall>` element is **invalid**, since two existing `<Connects>` elements would reference a missing wall ID and violate the frozen XML keyref. The correct complete declarative *proposal* removes **exactly three ordinary XML state elements**: one original `<Wall>` and its two original `<Connects>` declarations. The resulting graph is valid and removes precisely one Wall node, two directed declared connects edges and one derived storey ownership edge, with no added/modified unrelated state. **This is a valid declarative request, not evidence that the trusted native writer can safely execute it.**

## 2. Important Windows native IfcOpenShell blocker

Unlike the original public Door and Window cases, the pinned Windows IfcOpenShell 0.8.4.post1 native `ifcopenshell.api.root.remove_product` call on this actual original connected Wall terminated its Python process with **Windows native access-violation status 0xC0000005**, even when the two connected-path relations were explicitly removed first. Other exploratory owned geometry/property deep-cleanup sequences also terminated with native access violations or process-stack failure statuses. These exceptions **cannot be caught** by a Python `try/except` because the operating-system process exits.

The diagnostic therefore **does not enable a new compiler operation** or give the model an unsafe native tool. All native experiments used temporary local model copies. They did not overwrite the original source.

A conservative noncrashing, developer-only diagnostic sequence was established:
1. Load a new copy of the pinned normalized original IFC4X3.
2. Validate exactly the two native directed path connections to other original Walls and exactly three exclusive source-wall property definitions.
3. Remove the two native `IfcRelConnectsPathElements` via the low-level IfcOpenShell file API.
4. Remove three owned property relationships/sets via the tested `ifcopenshell.api.pset.remove_pset` function.
5. Remove the source Wall identity using low-level `file.remove`, **without** the unsafe deep-geometry cleanup.
6. Serialize to an ephemeral diagnostic IFC in an exclusive `TemporaryDirectory`, reopen and independently check every original `IfcProduct` class/GUID, native root deletion inventory, and nonproduct representation/placement orphan states.
7. Restore original millimetres only for a separately labeled **diagnostic author-scoring probe**. Discard all ephemeral files.

This minimally edited native candidate has **42 original IFC products**, only the named Wall identity removed, and exactly **9 expected original `IfcRoot` removals**: one Wall, two connections, three own property sets and three owned property-definition relations. However, it **leaves the deleted Wall's two original shape representations reachable only from the shared presentation layer rather than owned by a surviving Product**. The deleted Wall's product definition shape and placement additionally become orphan native STEP entities (one each). Direct `IfcShapeRepresentation` zero-inverse counting alone is insufficient because the shared layer retains references; the audit explicitly checks all surviving products for shape ownership.

That native output must **NOT** pass our safe D0/I0 original benchmark admission gate. The original author's unchanged score is **0.5** (object missing=1.0, integrity=0.0), but original grading does not guarantee native physical geometry or relationship integrity. This 0.5 is not evidence of a successful, comparable XML authoring arm, and cannot be counted as new D0/I0 parity.

## 3. Implemented reproducible safety audit

`tools/audit_bibimbap_v026_connected_wall_safety.py` is a new bounded, read-only-to-original developer diagnostic and strict native admission checker. It pins exact original public IFC SHA, normalized public source SHA, original author/data Git HEAD, prior original-task v0.23/24/25 report hashes, the 45-case public denominator, and only reads the public question to select an existing target GUID. All original named target GUIDs and full original question text are excluded from the committed JSON evidence.

A proposed XML document passes the complete XML parser/typed graph analysis. The existing D0 compiler **fails closed** for this operation, returns a rejected tool receipt, preserves last valid source XML, and publishes **no** native IFC. Independently, the developer-only minimal native probe is explicitly classified `DIAGNOSTIC_NATIVE_REMOVAL_INADMISSIBLE_ORPHANED_GEOMETRY`; a half-scored author result does not bypass this classification.

The frozen report is `reports/bibimbap_v026_original_test19_connected_wall_fail_closed_20261116.json` (SHA256 `fe6137a71789bf0d6c55dcf6c62a43a70f86fa5614e5c87faee2894e855ac848`). It records source/product counts, exact native root class changes, orphan summaries, original-author metric, current compiler refusal, and honest no-new-parity status. No original IFC is stored in the repository.

The dedicated `tests/test_bibimbap_v026_connected_wall_safety.py` includes **18/18 passing tests** across true source pinning, native two-connected-wall topology, genuine complete declarative graph edit, dangling-keyref rejection, supported XML compiler fail-closed, diagnostic native identity changes, orphan detection, original grader 0.5 without full score, forged/ambiguous public question, tampered source, previous reports immutable, second actual real-source report reproducibility, and no LLM/performance overclaim. New-test unittest time **9.948s**, enclosing process **17.422s**, exit code 0.

**Observed selected cross-version integration:** The 17-module run attempted **295 tests** and completed **294 without error**, but **one v0.19 sealed-Docker original IFC test errored** with `DockerIsolationError: Pinned worker image is unavailable` (170.464 s unittest / 176.906 s process). Independent read-only checks of the Docker Desktop Linux Engine showed **HTTP 500 Internal Server Error** on both cold and warm pinned-image inspect; this is an engine failure, **not evidence that the image was deleted**. No Docker restart/reset or image recreation was performed. A separate selected **16-module run excluding only the v0.19 sealed-Docker module passed 284/284 tests** (209.648 s unittest / 217.0 s process, exit 0). The new v0.26 tests remain 18/18 PASS. Frozen separately sourced QA report: `reports/bibimbap_v026_non_docker_284_pass_and_docker_http500_20261116.json`, SHA-256 `cff946ffde62bb2fe9ff453cd8318933a8edbbe4e10b7b3f5b93ecce7ff64fc1`. Because the engine returns HTTP 500, current orphan-container count is **unverified**, not zero. **Do not claim all selected 295, the old Docker module, or the entire historical 832-test suite green.**

## 4. Frozen scientific accounting

| Measure | Before v0.26 | After v0.26 |
|---|---:|---:|
| Original PUBLIC intention-to-test cases | 45 | 45 |
| Actual developer D0/I0 complete IFC byte-identical pairs | **8/45** | **8/45** |
| Developer pairs callable by unchanged original author scorer | **6/45** | **6/45** |
| Other original PUBLIC tasks not evaluated under the same approved paired output protocol | **37** | **37** |
| Native `test_19` safe D0 compiler supported | No | **No — explicitly blocked** |
| Real matched LLM/model calls | 0 | **0** |
| Paid model/provider spend | $0 | **$0** |

The two older original Window source-reference scorer cases remain classified as before. An original half-grade obtained from this **unsafe diagnostic native candidate** is not added to either count.

## 5. Reproduce on authorized research Windows workstation

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$repo = Join-Path $base 'bim-markup-bench-issue166-original-connected-wall-delete'
$python = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
Set-Location $repo
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

& $python -m unittest tests.test_bibimbap_v026_connected_wall_safety -v

# Use a NEW, ignored report destination. Existing frozen reports cannot be overwritten.
& $python -m tools.audit_bibimbap_v026_connected_wall_safety `
  --root . `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') `
  --output 'results/UNIQUE_original_test19_wall_safety_audit.json'
```

## 6. Next highest-priority engineering work

The next step is **not** to add a broad Wall-delete mutator. Instead, isolate native cleanup in a separately supervised child worker so that native process crashes cannot terminate the model-facing compiler, then find a stable and fully verified geometry/placement cleanup path (potentially with version-pinned IfcOpenShell fixes or different safe primitives). Require these before admitting original `test_19`:

- Correct complete ordinary XML diff: target Wall plus both original connections, no other source changes.
- Exact original IFC Root identities and neighbor connection constraints, owned metadata removal, preserving shared type/material/classification/storey relations and all surviving original native products.
- Original target shape representations and local placements genuinely removed where exclusively owned, shared layer retains every surviving other representation. No new orphan IFC STEP entities or undocumented modified native roots.
- Whole native physical output re-projection equals the complete XML state.
- Atomic stage validation and fail-closed on any child crash, time-out, source hash drift or IFC structural deviation.
- **Only after safe native output** perform a separate independent developer I0 implementation and exact complete IFC byte comparison, then use the unchanged original-author grader. Keep every result honestly counted and refuse real paid-model trials without provider/model/budget and equal access verification.

**Conclusion:** v0.26 materially resolves the original XML edit dependency and diagnoses the unsafe native cleanup blocker with replayable evidence, but is **a fail-closed research/safety checkpoint**, not a newly supported 9th original task or a causal XML/Python benchmark.
