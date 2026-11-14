# Original BIBIMBAP 45-case actual source read capability and frozen D0/I0 matrix — v0.12

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/138

**Date:** 2026-11-14 Asia/Seoul

**Research only:** `pikaybh/bim-markup-bench`; no production BIXML/Xim edits, original BIBIMBAP source/dataset/score changes, old D0 candidate changes, or new paid model calls.

## Experimental validity and strict distinctions

This is a **read-only real IFC source projection + historical *developer-authored* source-only D0 evidence ledger**. It is **not** an actual matched XML-vs-Python LLM experiment, not a model benchmark score, not Python I0, and **not** proof of full original-task or 45-case edit parity.

The complete 45-task denominator remains, even if a task cannot be projected, cannot reference important native source objects, has only a partial original-author D0 score, or has not been implemented. No task is excluded from denominators to make XML appear better. No hidden target/solution IFC is consulted for any authoring or scoring. All previously frozen developer-authored D0 scores in the **nine** pre-existing v0.2–v0.10 evidence reports are linked by their exact SHA256; prior v0.11 forensic findings and original real GPT-6 Luna model outcomes remain untouched. No original author grader is invoked for new candidate scoring. All Python I0 statuses are **NOT_RUN**, never silently scored zero.

### Current measured results (45 exact original public tasks)

| Audited property | Actual evidence | Required interpretation |
|---|---:|---|
| Original public editing population | **45** | Preserved denominator, no omission |
| Distinct original IFC source files | **31** | Each unique source measured separately once in isolated native process |
| Original IFC4X3 / IFC2X3 / IFC4 | **42 / 2 / 1** tasks | Original file schema and units preserved |
| **Current actual** source read-only XML projection successful | **43 / 45** | Partial XML model and source identity validated; **NOT** editable task coverage |
| Current actual read projection blocked | **2 / 45** | `geometry_test_18`, `geometry_test_19`; current v0.9 XML binder fails closed |
| Named public GUID refs + all required original Product source roles projected | **36 / 45** | Read-time minimum; does not prove semantic edit write capability |
| Nine pinned v0.2–v0.10 research reports: distinct task-specific developer D0 **candidate + original-author grade** | **22 / 45** | A single frozen exact task slice per original task; NOT LLM success |
| Of those developer D0, original-author full marks | **11** | Not independently attested full original task success rate |
| Of those developer D0, original-author partial scores | **11** | Partial results retained without retuning |
| No v0.2–v0.10 developer D0 record | **23** | NOT EVALUATED BY THESE FROZEN D0 SLICES; does not mean impossible/failed |
| Python original-task matched I0 runs | **0 / 45** | Generic Python IFC tool availability is not an I0 result |
| Equal-condition paired real LLM trials | **0** | Requires capability gates and separately approved paid model budget |

**Historical initial v0.1 source-only projection 36 PROJECTABLE / 9 BLOCKED is NOT the current result**. Current projection uses v0.9 for original IFC4X3 and v0.8 original-native legacy XML for IFC2X3/IFC4, in every case against a temporary original-native-schema metre-normalized original clone. The native geometry/typed elements, original sources, original GUID cases, and original dimensions are never relabelled or faked to admit an input.

### Actual two source read blocks

- `geometry_test_18` — original IFC4X3 requested west-wall windows deletion, source product count includes **17 Walls and 19 Windows**. v0.9 XML projection generates a partial model, but the **frozen source semantic binder** rejects it with `BindingError: Opening is outside the hosted wall's horizontal extent`.
- `geometry_test_19` — original IFC4X3 requested selected windows opposite a named Wall, with original source **8 Walls and 7 Windows**. Same independently observed **current XML binder opening/host horizontal extent invariant** fails.
- These are **model compatibility/binding limitations**. They do **not** prove the original IFC files are invalid or that arbitrary manual XML edits can fix them. The worker records stable, sanitized failure code `HOSTED_OPENING_OUTSIDE_SOURCE_WALL_XML_BINDER_EXTENT` and separately the original `BindingError` class. Neither the old source projection, native IFC nor XML binder were patched to inflate current counts. Failure cases remain in the 45 denominator.

### Seven more successfully read cases missing required source roles

Seven of the 43 read-view successes do not fully project the *minimum* original native object classes/roots explicitly referenced by the public task:

| Original task | Missing projected native source role |
|---|---|
| `geometry_test_20` | 3 of original 6 Walls not in Elements read view |
| `test_20` | 1 of original 3 Spaces not in Elements read view |
| `topological_test_01` | Original named Space is not projected |
| `topological_test_03` | Both original Spaces not projected |
| `topological_test_14` | Original 4 Beams not projected at all |
| `topological_test_18` | 1 of original 3 Spaces not projected |
| `topological_test_20` | Original 2 Spaces not projected |

The other 36 original task read views project all original required *source object roles* and named GUID references; **this is a minimum read-time coverage gate, not proof of geometry/topology or write expressivity**. The source model can still contain unprojected other products, unsupported relationship graphs, original host openings or arbitrary geometric operations.

For example, original shared `basic_tasks.ifc` has 43 `IfcProduct` objects and 35 original Product GUIDs represented as XML `Elements` nodes; the other 8 are not represented in `Elements` (some spatial hierarchy products may be represented in `Levels`). The source IFC, material/type/unknown STEP entities remain source-owned; it would be incorrect to treat the XML as a complete lossless IFC serialization.

### Genuine historical D0 write evidence

The v0.12 capability ledger statically imports exactly **22 distinct source-only developer D0** reports from the nine immutable version-specific JSON evidence files (v0.2–v0.10). Every original task name and any safely defined original public IFC/question hash are checked against the pinned cohort. Original author scores and the presence/absence of the historical independent oracle are carried through without modifying, normalizing, rerunning or post-hoc optimizing any candidate.

Noteworthy transparency requirements:
- The original author returned **11 full grades and 11 partial grades** on 22 developer-authored D0 inputs. These are not new real GPT-6 Luna attempts; historical real Luna 45-task results are unchanged.
- `test_04` original-author D0 full grade **1.0** is accurately recorded, **but the earlier v0.2 JSON explicitly has `independent_full_scene_clash_oracle_pass=null`**. The v0.12 row therefore labels the full-scene independent oracle **NOT RECORDED**, rather than silently marking it PASS.
- A later compilation may project a source used by a task without implementing that task's original requested edit. Neither read projection nor a narrowly successful developer D0 edit transfers general functionality to different source geometry, host relations, transformations or multi-object workflows.
- The matrix deliberately sets **`native_full_original_task_success_independently_verified=false` for all 45**, because the original full problem requirements (including independent collision/contact/scene integrity and exact original scorer) have not been uniformly verified by one full-task-independent oracle; this is **not** a claim that all 45 tasks fail. It is an evidence standard.
- The Python arm's generic `execute_ifc_code` tool is already implemented in the research harness, but **no task-specific prospective original-author Python I0 candidate/oracle** is recorded here. `Python_control_matching_task_specific_I0_run=NOT_RUN_NO_EVIDENCE` on **all 45**.
- Therefore **equal-capability XML-vs-Python native semantics cannot yet be claimed**; do not divide 11 successful developer examples by 45 to report LLM XML accuracy.

## How the original source is measured, without state changes

`tools/audit_bibimbap_v12_real45_capability_matrix.py` freezes each original public task with task-ID → required native semantic *operation family* and source Product roles based solely on original public questions (not private grader/GT); requires all exact 45 IDs; verifies each public question and source IFC SHA against immutable pinned `public_45`; caches original source only by exact SHA256, but computes **task-specific public named GUID/required class read coverage separately**.

`tools/audit_bibimbap_v12_projection_worker.py` runs inside a **separate subprocess for each unique original IFC** with a per-source timeout, so a failing native OCC kernel or XML binding cannot contaminate other task probes. A temporary metre-normalized clone preserves original IFC2X3/IFC4/IFC4X3 schema. It loads real current v0.9 IFC4X3 partial XML or v0.8 original-native-schema partial XML, validates source model SHA, XML namespace, every projected original Product/Level GUID, duplicate GlobalId absence and original native product class inventory. On IFC4X3 it also runs the actual frozen source semantic graph binder. Legacy v0.8 is explicitly marked **`SCHEMA_NATIVE_LEGACY_READONLY_XML_NOT_IFC4X3_BINDER`** and must not be mistaken for IFC4X3 full native binder parity.

Each worker returns only structured source/product/GUID evidence, original class inventory, read-model count and safe error codes. The parent creates the 45 original per-task rows, required operation labels, actual reference coverage, prior D0 evidence, and **explicit unrun Python I0 & LLM statuses**, all as read-only data. Source hash is reverified after subprocess execution. No candidate is authored in v0.12, no original author scorer invoked, no physical IFC library payload committed.

## Reproducible research outputs

- Full deterministic source+task matrix: `reports/bibimbap_v012_actual_original45_native_read_and_D0I0_matrix_20261114.json`; **SHA256 `8fcaed91fc0578051ea99151925daaa9e6a742d46c218b6db39ec83531ef6758`**
- Flat all-45 task inspectable CSV: `reports/bibimbap_v012_actual_original45_native_read_and_D0I0_matrix_20261114.csv`; **SHA256 `f6d218adf9f09eb72777790e39e304cfff0330ea3c4f8296e2934105f6fcd452`**
- Audit scripts: `tools/audit_bibimbap_v12_real45_capability_matrix.py`, `tools/audit_bibimbap_v12_projection_worker.py`
- Offline positive/negative audit tests: `tests/test_bibimbap_v12_real45_matrix.py`
- **Actual full reproduction evidence:** both complete reports were regenerated from the original native source files and all 9 pinned D0 inputs after a clock interval; both SHA256 sums **matched byte for byte**. Earlier provisional reason-unclassified files are preserved only under ignored `results/`, not committed as scientific evidence.
- **18/18 new v0.12 tests PASS**. **Combined v0.12 + v0.11 + v0.10 + all prior native/45-case/matched25 offline regressions: 257 tests run / 255 PASS / 2 optional SKIP / 0 FAIL** (178.838 seconds). No external paid calls.

```powershell
$base='D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue138-original45-matrix-v012')
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$author=Join-Path $base 'bibimbap-author-upstream'
$data=Join-Path $base 'bibimbap-author-data'

& $py -m unittest tests.test_bibimbap_v12_real45_matrix -v

# Use fresh unused output paths; never replace immutable Git research evidence.
& $py -m tools.audit_bibimbap_v12_real45_capability_matrix `
   --author-repo $author --dataset $data `
   --output-json 'results/NEW_UNUSED_v12_actual_matrix.json' `
   --output-csv 'results/NEW_UNUSED_v12_actual_matrix.csv'
```

The new test suite checks every original 45 source/question, each schema's real read path, both exact native opening/host binder failures, the 7 additional missing required source-role cases, the original 31 unique source objects, 9 prior frozen D0 report SHA256, all 22 developer D0 author outcomes, honest missing v0.2 full-scene oracle, true case-sensitive 22-character IFC GlobalIds, legacy IFC2X3/IFC4 no schema relabelling, all 45 Python I0 not run, null model benchmark and a malicious/mismatched input source hash being rejected.

## Next prospective work

1. Fix and independently verify the **two actual original native source opening/wall binder read blockers** and the **seven partial source-role/reference blockers**, without assuming every novel original IFC relationship or mesh can be faithfully represented as the existing toy XML. This requires new opt-in v0.13 compiler/projection rather than rewriting frozen earlier v0.8/v0.9 source code, reports or scores.
2. Establish rigorous **task-by-task original native write D0 and separately authored original-source Python I0 candidates** (with independent full-scene/contact and root integrity oracles), preserving all 45 task IDs. A Python control arm can read the complete original IFC, so unsupported XML operations must remain explicit and cannot be removed from the matched denominator.
3. Only after pre-registered equal-capability gates are demonstrably met, obtain **new explicit owner-approved paid model call budget** before any new matched-25-call or full original 45-task LLM trial. Published author baselines under different models/tool budgets are only contextual, not causal equality evidence.
