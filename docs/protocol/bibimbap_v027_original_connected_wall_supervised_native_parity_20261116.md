# BIBIMBAP v0.27 — Crash-isolated original public connected Wall deletion; real native IFC D0/I0 byte parity

**Research Issue:** https://github.com/pikaybh/bim-markup-bench/issues/169
**Frozen parent:** v0.26 Draft PR #167, exact commit `8e3564ca19606d82b0880a279e0fd4c5dbed137d`.

**Research-only, not BIXML/Xim production.** The original author test code, private answers, public source IFC files, previous evidence reports, 45-task protocol, and `main` remain unmodified. Real model LLM calls and paid inference: **zero**.

## 1. The original public task and why v0.26 could not pass

The original benchmark PUBLIC `test_19` requests deletion of a named original `IfcWall` in public `basic_tasks.ifc`, IFC4X3 millimetres. Native source has 43 original `IfcProduct`s. The target is involved in **exactly two** directed original `IfcRelConnectsPathElements` joining it to two other existing Walls. It has three exclusively owned original propertyset relationships and shared storey/type/material/classification memberships, with two original shape representations and a source-owned local placement.

The **only admissible direct XML source edit** is a complete normal `<Building>` document missing exactly its one original `<Wall>` and the two corresponding existing `<Connects>` elements. Removing only the Wall violates the existing XML keyrefs. The authoring agent does not call `IfcOpenShell`, an imperative tool, `<Delete>`, `<Move>`, or typed BIM command APIs.

v0.26 found that directly calling IfcOpenShell `root.remove_product` on this original connected Wall can terminate the Windows native process. Its surviving minimal low-level alternative removed the Wall/Psets/paths but **left two Wall shape representations no longer owned by surviving products**, plus an orphan `IfcProductDefinitionShape` and `IfcLocalPlacement`. The original author still scored that unsafe diagnostic 0.5, proving the original author grade was not a sufficient native-integrity oracle. Accordingly v0.26 deliberately kept the D0 source compiler blocked, and previous scientifically valid developer D0/I0 native output count remained **8/45**.

## 2. Actual new v0.27 implementation and safety boundary

- `src/runtime/connected_wall_delete.py`: a new **source SHA-pinned IFC4X3 original-public connected Wall compiler**, selected by `src/runtime/compiler.py` only when there is one original existing Wall source-state removal, the exact normalized original IFC SHA matches `16568e7c4b8b9d62567a7a199101269daa6e5b1b7535cec095b8e233ae2ef6ac`, and the complete graph loses exactly **2 `connects` edges + 1 derived `in_storey` edge**. Other Wall editing routes retain their existing behavior. The public original file is never overwritten.
- The native preflight rejects wrong/forged GUIDs or classes, ambiguous path direction/neighbors, unknown `IfcRelSpaceBoundary` or other inverse dependency, shared target propertysets, shared target product shapes/placements, missing owner and unrecognized presentation-layer memberships. **Exactly 9 original deletable `IfcRoot`s** are identified before execution: one Wall, two path connections, three propertyset relations, three owned propertysets. **Exactly 4 shared original `IfcRoot` relations** may lose the Wall from membership: storey containment, type, material, and classification.
- `tools/bibimbap_v027_wall_native_worker.py` is a fixed, internal, **one-shot child-process-only trusted native writer**. It removes exactly the two native paths, uses the supported Pset API for each exclusively owned source propertyset, drops the Wall's two representations from its one shared presentation layer while preserving every other member, detaches the Wall's product definition shape, recursively purges only unshared geometry, detaches and purges the source-owned local placement, then removes the Wall root. This sequence avoids the previously crashing `root.remove_product` path. Its source is pinned; the child cannot write the user's original IFC path and cannot publish an output independently.
- The runtime parent invokes the child via `subprocess.run` with an explicit **25-second deadline**, checks nonzero/native-crash exit code, timeout, duplicate/invalid receipt and missing/tampered child output, then moves the candidate only to a **private staged transaction file**. Synthetic native access-violation exits, timeout and forged `success` are unit-tested fail-closed. The only final publication is `stage_and_commit` after independent full native verification.
- The parent independently reopens *both* original and staged native IFC, checking **all original surviving `IfcRoot` GUIDs/classes/attribute strings**, the exact nine deleted roots and four required shared-membership changes, exactly one original presentation-layer STEP membership change, **all surviving original STEP records unchanged except those five approved edits**, no unexpected added STEP records, every deleted STEP record reachable from approved original owned-root descendants, original source shapes/product shape/placement actually gone, every other original `IfcProduct` identity/class preserved, both neighbor Walls and all their non-target relationships preserved, and no new shape/placement orphan counts. Final native IFC is reprojected to the entire declarative XML typed graph and must equal the submitted complete state before atomic publication.
- The above safety claims apply only to the **pinned original native source and tightly bounded operation**, not generic connected-wall deletion, other input IFC sources, IFC2X3/IFC4 XML admission, or an arbitrary Python code sandbox. Process isolation stops a native crash from terminating the parent, but is **not** a general security sandbox against hostile untrusted code.

## 3. Actual matched developer-coded D0 and independently written native I0

`tools/bibimbap_v027_independent_connected_wall_i0.py` is separately developed native Python/IfcOpenShell. It imports **no D0 XML compiler, no markup parser and no D0 native worker**. It independently reads the same original public IFC and the public original Wall GUID, discovers its two native paths and three propertysets, and applies the native geometry/placement cleanup in the independent imperative environment. Both arms have the same source millimetres → normalized metres → source millimetres output envelope.

`tools/audit_bibimbap_v027_original_wall_parity.py` actually executes both arms, verifies the exact original source IFC SHA and public question SHA, checks original 45 cohort, pinned author/data Git HEADs and every previous v0.24–v0.26 research report SHA, independently reopens resulting IFC native objects and relationships, and calls the **unchanged original author scorer only after** both native IFC outputs exist.

| Actual original PUBLIC `test_19` | Declarative XML D0 | Independent Python I0 |
|---|---:|---:|
| Real original IFC4X3 mm input | Pinned | Same pinned |
| Target native Wall and 2 connections removed | PASS | PASS |
| Other 42 original IFC Products GUID/class identity preserved | PASS | PASS |
| Owned target shape/product shape/local placement removed; no new orphan | PASS | PASS |
| Entire native output IFC SHA-256 | `5a3bf2626f32219cc770b5b8d68277f6e959aa7822a5ad92974931eb47b9941d` | **exact same bytes** |
| Unmodified original author `object_not_exists` | 1.0 | 1.0 |
| Unmodified original author `integrity_constraint` | 0.0 | 0.0 |
| Unmodified original author overall | **0.5** | **0.5** |
| Actual LLM model calls/provider spend | **0 / $0** | **0 / $0** |

The original author score of **0.5 is not full marks**; native safety is established separately by root/STEP/orphan/graph validators. The original evaluation formula was not changed and cannot be counted as a causal XML/Python representation difference because the **complete output files are identical**.

The new immutable sanitized actual original native report is `reports/bibimbap_v027_original_test19_complete_native_D0_I0_parity_20261116.json`, SHA-256 **`5f1d3601910048e514678869f86868bca90cf2073e23883463bd7a89233c0f04`**. A second actual full benchmark replay reproduces identical report bytes and both IFC hashes. No raw original IFC, full public task question, original public target GUID, hidden grader target list, or credential is committed.

## 4. Tests and bounded scientific claims

**New v0.27: 32/32 original IFC and positive/negative tests PASS**, 30.083 seconds unittest / 37.156 seconds enclosing process, exit 0. These include source pinning, D0 actual native commit, independent Python I0 source/byte parity, original grader, 9 original Root/remaining original STEP preservation, zero new shape/placement orphans, wrong target type/GUID, shared property/geometry violation, extra space boundary, reversed connection role, model-facing XML dangling-connection rejection, extra unrelated edit rejection, forged child receipt, synthetic native crash exit and worker timeout (both fail-closed/no published IFC), legacy unsupported original IFC2X3/IFC4 source and reproducible immutable source/report checks.

The v0.26 `test_bibimbap_v026_connected_wall_safety` module is a **historical frozen source-verification module that asserts the old D0 compiler rejects `test_19`**. That exact expectation is intentionally superseded by this new source-pinned feature, so the v0.27 active regression selection excludes this *obsolete fail-closed expectation* without changing the archived v0.26 report/tests. Previous native functionality v0.3–v0.25 is regression-tested normally. The historical full repository ~832-test discovery is not claimed green.

**Actually completed selected v0.27 regression:** 16 selected non-Docker modules covering v0.3/v0.4/v0.14–v0.25 and new v0.27: **298/298 PASS**, no errors/failures, 280.895 s unittest / 289.844 s enclosing process, exit 0. The historical v0.26 module with its now-superseded "D0 must reject original test_19" assertion was deliberately *not* changed or counted in the new active regression. The separate historical v0.19 sealed-Docker module was excluded because fresh read-only Docker Desktop Linux Engine `info` and pinned-image `inspect` queries again returned **HTTP 500**. No Docker reset/restart/pull/prune; image existence and orphan worker count are **not verified**. The frozen new QA report `reports/bibimbap_v027_original19_non_docker_298_regression_and_docker_http500_20261116.json` has SHA256 **`f58f8df1f9e98121283df844b652838c82b89cac5d1382f310b89fd4f768c636`**. This is **not** a claim that the v0.19 Docker module or historical whole repository ~832-test discovery passed.

## 5. Research accounting (original 45 unchanged)

| Actual, distinct original-public matched developer outputs | Before v0.27 | After v0.27 |
|---|---:|---:|
| Full native IFC D0/I0 **byte-identical** original task cases | **8/45** | **9/45** |
| Developer pairs callable by unchanged original-author scorer | **6/45** | **7/45** |
| Original tasks not yet paired under the same approved native output protocol | **37** | **36** |
| Original PUBLIC test_19 safely native-authorable by these two developer implementations | No | **Yes, restricted to pinned source** |
| Real matched LLM trials | **0** | **0** |
| Paid inference/provider USD | **$0** | **$0** |

The frozen prior v0.26 low-level orphaned diagnostic output is NOT retroactively recast as safe. This checkpoint's valid new pair is established by a separate source-pinned guarded implementation and a separate independent Python I0, both with the verified complete original native IFC output.

No causal XML-vs-Python model-performance conclusion is supported until the **same task-specific original native source information, independent write capabilities, feedback budgets, retry and model inference conditions** are rigorously controlled and actual model trials are authorized.

## 6. Reproduce on the authorized Windows research workstation

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$repo = Join-Path $base 'bim-markup-bench-issue169-v027-supervised-wall-delete'
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
Set-Location $repo
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

& $py -m unittest tests.test_bibimbap_v027_original_wall_parity -v

# Choose a NEW, ignored destination. Never overwrite prior evidence.
& $py -m tools.audit_bibimbap_v027_original_wall_parity `
  --root . `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') `
  --output 'results/NEW_UNIQUE_v027_original19_native_parity.json'
```

## 7. Next priority

Validate the new native source-pinned Wall operation against additional independent original-public source files and physical geometry representations before attempting to generalize beyond the exact original-public `test_19` source. Then address the remaining original45 role and IFC schema asymmetries task-by-task. Continue to disclose original author grader integrity failures without modifying their private target data/scoring. Actual LLM trials require separate owner-approved model/provider and hard cost budget plus a pre-registered fair XML-vs-Python source/write/tool parity protocol.
