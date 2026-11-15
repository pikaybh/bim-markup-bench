# BIBIMBAP v0.25 — Original public Door/Opening declarative XML source edit and native IFC result parity

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/164
**Frozen parent:** v0.24 Draft PR #163, commit `9384a9e92615467abc0bcabea91537d5a43c91fc`. Research-only; original author scorer, original public task files, prior reports, main, and production Xim/BIXML code are never modified.

## 1. Original-public task, scientific scope

The original public `test_17` instructs removal of one public-named `IfcDoor` in the genuine `basic_tasks.ifc` native IFC4X3 millimetre source, which also contains the Door's original `IfcOpeningElement` and host `IfcWall`. The actual source's Door has an individually defined IFC property/type/material set, a single filling/void relationship, an exclusive classifier, a shared building-storey containment relationship, and one shared presentation layer. Its native dependency structure **differs materially** from the previously working experimental hosted-Door fixture: the fixture preflight also expects a space boundary and shared type/classifier memberships. Simply relaxing that fixture's expected counts would make other real IFC sources unsafe.

This research checkpoint implements a separate, narrower source-pinned compiler operation. A declarative D0 author edits the **full ordinary XML building state**, removing exactly one existing `<Door>` and its exact `<Opening>` referenced by that Door, not using special `<Delete>` commands, raw IFC edits, function calls, or the imperative Python encoder. The paired independent imperative I0 is a separately coded developer-owned IfcOpenShell native manipulation of the same original public Door and its one original Opening. **No LLM is called.**

## 2. Verified native IFC compiler and safety boundary

- `src/runtime/door_opening_delete.py`: deliberately dedicated trusted source-state native writer copied from the previously validated bounded Window/Opening structure, with native `IfcDoor` type, source-relevant exclusive inverses, source-specific `IfcDoor` presentation geometry and own separate operation ID.
- `src/runtime/compiler.py`: dispatch to this new backend **only if an ordinary full-XML semantic diff removes a Door plus Opening** on an exact normalized original-public IFC4X3 source SHA `16568e7c4b8b9d62567a7a199101269daa6e5b1b7535cec095b8e233ae2ef6ac`. All other existing source Door cases still follow their historical fixture-specific compiler branch. This intentionally does **not** silently extend general IFC4X3 Door editing.
- Strict preflight: exact source-bounded Door, Opening, one host Wall, fill and void relations; Window-specific functionality is NOT used. The Door must have the inspected exclusive property/type/material metadata, one approved classifier and a shared storey containment and presentation layer. Extra inverse dependencies (e.g. an added space boundary), shared property/type/material membership, invalid original source GUID/classes, added openings/fillings or dependent placements cause fail-closed refusal.
- The trusted writer calls native IfcOpenShell `root.remove_product` for original Door then original Opening on a **separate native loaded file**. Atomic exclusive staging publishes only after independent validation. The original input native IFC SHA must be unchanged before and after.
- The verifier compares **every original/result `IfcRoot` GUID/class**, requires exactly **10 original Root deletions** and exactly **two bounded shared IFC relation member changes**; also checks one `IfcPresentationLayerAssignment` drops *only* the removed Door shape. No added native STEP IDs; every surviving original STEP entity is unchanged except the three approved membership changes. Non-root entities removed by IfcOpenShell must originate in the owned original deleted-root subgraph and have no unauthorized surviving inverse references. Every other original IFC product GUID and class must survive unchanged.
- Complete resulting native IFC is independently reprojected to typed declarative XML and compared against the **entire submitted graph**, not just the public target. Scope is bounded to this source and operation; no guarantee for all Doors, opening hosts, schemas, IFC2X3 or IFC4.

## 3. Actual matched original-public D0/I0 results

`tools/audit_bibimbap_v025_original_door.py` executes the real original public benchmark input, checks frozen public question/source SHA and dataset/author Git revisions and all earlier v0.22/v0.23/v0.24 report checksums, builds D0 with exactly two ordinary removed XML state nodes, independently executes I0 from `tools/bibimbap_v025_original_door_i0.py` (which has no XML compiler imports), and calls the unchanged original author scorer on each output **only after** native IFC creation.

| Original `test_17` measurement | Declarative XML D0 | Independent native Python I0 |
|---|---:|---:|
| Original IFC4X3 millimetre source | exact pinned public | same |
| One original Door and hosted Opening removed | PASS | PASS |
| Other original 41 `IfcProduct` GUID/classes survive | PASS | PASS |
| **Entire output native IFC SHA-256** | `7807db482647c4cae88678eef38beb5003d365ea1c08e1b589b68e3a8d86196f` | **identical bytes** |
| Original author `object_not_exists` | 1.0 | 1.0 |
| Original author `integrity_constraint` | 0.0 | 0.0 |
| Original author final grade | **0.5** | **0.5** |
| Actual LLM API/provider calls and spend | **0 / $0** | **0 / $0** |

New sanitized frozen report `reports/bibimbap_v025_original_test17_door_opening_D0_I0_20261115.json` SHA-256 `4ea264519d011288acf6d059fc15b3ca49aa7d4d21315ccb5cbebe5bb17f3f4a`. Its exact bytes and the paired native output SHA reproduce on a second actual run. The report contains no raw IFC, full public question, public target GUID, private scorer targets or credentials.

### Original author grading limitation: not the same as test_20 or test_18

The independently inspected **unchanged original** author implementation `data/tests/test_17.py` checks public Door absence and invokes `run_delete_integrity_check` only with **the Door's GUID**. In a separate posthoc run of the original `data/tests/delete_integrity.py` on the real independently generated I0 output:

- `wall_connections_deleted`: TRUE
- `spatial_containment_deleted`: TRUE (the actual original Door has an `IfcBuildingStorey` container)
- `openings_deleted`: TRUE
- `aggregations_deleted`: TRUE
- `filling_deleted`: **throws `AttributeError`**, because the original implementation treats the Door's **tuple** of `FillsVoids` relations as if it were one `IfcRelFillsElement` with a `RelatedBuildingElement` property
- `non_target_elements_unchanged` with only the public Door GUID: FALSE (the actual native deletion necessarily removes the linked Opening and owned metadata as well)

Therefore the observed original author grade 0.5 is explained by the original author integrity check's incompatible native Door relationship assumption and non-target preservation semantics. This was **not patched or adjusted** to optimize our score. For comparison, v0.23 original Space deletion failed the original author's nonexistent containment precondition; v0.24 Opening deletion failed non-target preservation despite all five explicit deletion predicates TRUE. These are distinct source/evaluation mismatches; identical D0/I0 output cannot establish a performance difference between authoring representations.

## 4. Honest cumulative research accounting

The frozen original public 45 task intention-to-test population remains unchanged. Previous developer-owned native D0/I0 output byte-equal tasks **7/45**; the new independent original `test_17` adds exactly one, cumulative **8/45**. Previously both original-author-scoreable developer pairs **5/45**, now **6/45**, including this original half-score pair. **37 other original tasks remain untested** under the same full output and grader protocol. Two previously diagnosed original missing-Window-reference original author cases remain unscoreable unchanged.

A fully fair causal study of XML vs Python representation **has NOT yet been run**: all eight pairs are developer-authored controls, **0 real LLM trials, $0 provider spend**, and original45 full input information, write capabilities, feedback budget and native source semantic parity are not proven. Current direct XML source admission remains IFC4X3-only for this editing slice; three known original IFC2X3/IFC4 schema exclusions and other task-relevant role gaps are still present.

## 5. Reproduction on authorized connected Windows research workstation

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$repo = Join-Path $base 'bim-markup-bench-issue164-original-door-opening-delete'
$python = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
Set-Location $repo
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

& $python -m unittest tests.test_bibimbap_v025_original_door -v

# Always supply a NEW destination: frozen reports are exclusive and never overwritten.
& $python -m tools.audit_bibimbap_v025_original_door `
  --root . `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') `
  --output 'results/UNIQUE_v025_original_public17_native_audit.json'
```

**Actual v0.25 test evidence:** New original-public positive/negative tests **32/32 PASS** (13.585 s unittest / 14.875 s enclosing process). Selected cross-version original IFC, Docker and original-author regression **277/277 PASS across 16 modules** (208.970 s unittest / 214.172 s enclosing process, exit 0, no skips reported). The separately frozen forensic QA report is `reports/bibimbap_v025_scoped_277_regression_and_scorer_forensics_20261115.json`, SHA-256 `f9f7e0c16c6fa306a4bd2fc6bdb8c605ac96d4106c6f7a2685c8f641fcbe7663`. Posthoc unmodified scorer criteria independently rechecked: four true deletion predicates, `filling_deleted` AttributeError (Door's FillsVoids tuple), non-target preservation false; original author/source Git clean and zero orphaned prior Docker containers. **Do not claim full historical 832-test repository discovery is green**; it was not executed in this checkpoint.

## 6. Next original task

The next explicitly prioritized remaining public task is `test_19`, connected `IfcWall` deletion. The real original Wall has two native `IfcRelConnectsPathElements` plus shared material/type/classification and individually owned Psets. The safe XML deletion must also express the two relationship removals, enforce full native connectivity cleanup and reject surprise changes; the same independent I0 and original author grading conditions apply. Neither this protocol nor its code silently supports this task yet.
