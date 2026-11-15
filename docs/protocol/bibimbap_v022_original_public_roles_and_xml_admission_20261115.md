# BIBIMBAP v0.22 — Actual original 45-task IFC source roles, public GUID visibility and current XML writer admission

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/158
**Parent:** v0.21 Issue #156 / Draft PR #157, frozen commit `c791be8bbeac59fe9cd89418b3643175b3d5b3b4`.

**Research only.** Not BIXML/Xim product implementation, not new IFC feature support or LLM inference. Original author scorer, hidden references, public task questions, input IFC files and all older reports remain unchanged.

## 1. Scientific hypothesis and method

v0.17/v0.20 showed that all 45 original public IFCs contain some native `IfcProduct` instances not encoded in the **current editable typed XML**. This is a concrete *complete-source representation* gap but not proof that every omitted product is relevant to each particular task.

v0.22 asks a narrower, more actionable question: are the **original public instruction's explicitly named native GUIDs and required source object roles** visible in the current XML editing surface, and can the current `XmlSourceEditSession` even admit each original IFC schema/length unit? Are any earlier **actual D0/I0 native write result pairs** available to go beyond mere visibility?

The audit uses:
- **Original author repository** pinned Git SHA `667004e16bd38fd7d538bcee56191465429fd975`.
- **Original public dataset** pinned Git SHA `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`.
- The unmodified **45 original public BIBIMBAP instructions** (15 basic, 15 geometry, 15 topological; 15 create, 15 update, 15 delete), with exact public-question and IFC SHA checks, not hidden scorer targets.
- Frozen v0.12 publicly defined `REQUIREMENTS` mapping from task ID to necessary **source reference roles** and requested edit-family labels. These are labels based on public questions, **not a complete formal proof of semantic target relevance or executable compiler feature availability**.
- **Frozen v0.13 independent native source+editable typed catalog** SHA `67b58b9b55d24d48ae644200e0ac9501b255ed4a346aa4add2036438cad3e9f5`, containing all original native product GUIDs/classes and their independently verified editable-typed/opaque-read-only partition.
- Frozen v0.20 all45 capability evidence SHA `1aa218a0883186e6df1e7e7d895670fb9e012ef0229799b14881a87473f762be`.
- Frozen v0.21 actual scoped 162/162 regression evidence SHA `15a5af2cac9e2024c54fb9a79b2f46b51630ad9714e256487580090dbf0ccf11`.

The new worker `tools/bibimbap_v022_task_relevant_source_role_audit.py` opens **all 31 distinct actual original IFC files in IfcOpenShell, read-only**, validates source SHA before and after, independently reconstructs all actual source `IfcProduct` GUID/class maps and compares exact **480/480 objects** with frozen v0.13 native product catalogs. It verifies the older editable typed subset is an exact class-consistent partition of each actually read original source, binds each instruction's public GUIDs (not hidden grader GUIDs), recomputes each required source role's native/typed product counts, and checks current XML session's admission rule: **exact IFC4X3 schema plus original millimetre units**. No source normalization, IFC write, compiler mutation, original author scoring, Python solution, Docker execution or LLM tool use occurs in the v0.22 worker.

The actual original IFC is the fresh source of truth; v0.13 typed subset is independent **earlier evidence**, not a newly regenerated full editable XML source. Therefore this checkpoint validates the **current frozen typed partition against real original products**, not full source projection content, and it does not claim feature-write parity.

## 2. Verified all45 actionable gaps

| Question | Verified original tasks | Scope of conclusion |
|---|---:|---|
| Original denominator and source files | **45 tasks / 31 IFCs / 480 native IfcProducts** | Original public task membership and exact native product identities independently rechecked |
| Original explicit public GUID references absent from native source | **0/45** | All explicitly named original task GUIDs appear in the corresponding source IFC product inventory |
| Some native products omitted from current editable typed XML | **45/45** | Whole-source object completeness gap; task importance is not established for every omission |
| Required public source object role **fully covered** by the editable XML subset | **36/45** | Necessary coarse role-level source availability only, not sufficient for semantic task success |
| At least one *required source role* has original products omitted from editable XML | **9/45** | Role-class completeness gap, no invented failure score |
| Explicitly named PUBLIC source product GUIDs omitted from editable XML | **2/45** | The named source object exists natively; current edit-state encoding omits it |
| Actual **current XML editing session** rejects original IFC schema | **3/45** | Proven actual constructor rejection for IFC2X3/IFC4 under this particular IFC4X3-only implementation |
| Current XML session's schema/unit necessary admission check passes | **42/45** | Not proof projection/compile/write succeeds |
| Original full IFC source semantic equivalence proven | **0/45** | Missing required full information controls |
| Complete native write-capability parity proven | **0/45** | 5 historical task-specific developer results do not prove general writer equivalence |
| Previously native-byte-identical developer D0/I0 cases | **5/45** | Previously frozen proof on exact selected tasks, not new model trials |
| Previously original-author-scoreable developer D0/I0 cases | **3/45** | Other 2 known original author reference mismatches, remaining 40 not evaluated |
| New real LLM model trials or paid provider requests | **0 / $0** | No provider invoked |

**Nine cases with missing original objects in a public-required source role:**

`geometry_test_18`, `geometry_test_19`, `geometry_test_20`, `test_20`, `topological_test_01`, `topological_test_03`, `topological_test_14`, `topological_test_18`, `topological_test_20`.

The incomplete classes include original `IfcWindow`, `IfcWall`, `IfcSpace`, `IfcBeam`. Actual class counts are in each per-task JSON row. This is **stronger evidence than merely noting omitted site/building/storey objects**, because these classes are explicitly required by original public task semantics. It remains weaker than proof that the specific excluded native product is selected by the task, or that a complete XML read packet could not describe it.

**Two cases with public **named source GUIDs** absent from editable typed XML:** `topological_test_01` (one) and `topological_test_20` (two). These two are also among the above nine; **never add the counts**. The public GUIDs are all present in original source and in the older read-only native catalog; they are **not** author-private grading targets, and the omission from editable XML does not mean the common read-only v0.18 packet cannot report them.

**Three cases with actual current XML session input rejection:** `geometry_test_03` and `geometry_test_04` (`IFC2X3`), and `geometry_test_05` (`IFC4`). These are disjoint from the nine role-gap cases. Current `XmlSourceEditSession` requires `IFC4X3` and original millimetres. The v0.22 tests actually instantiate this class with each of the **three unchanged original IFCs** and verify it raises `UnsupportedArm("XML source compiler only accepts IFC4X3")` rather than editing any source or fabricating an IFC output. This is a **version-specific hard front-door limitation** of the *current arm*, not a statement that an XML representation could never handle these IFC editions.

**33 of 45 tasks** pass these *coarse necessary* checks (no incomplete frozen source-role class, no missing named source GUID, no schema/unit pre-admission rejection). They are **NOT** 33 executable, semantically supported, author-scoreable or scientifically comparable tasks. No such claim follows from these checks: construction, dimensioning, relationship edits, topological changes, IFC schema semantics, ground-truth grader consistency and native write capability still require independent task-specific positive/negative implementation evidence.

## 3. Exactly what was and was not implemented

Files:
- `tools/bibimbap_v022_task_relevant_source_role_audit.py` — actual pinned public input IFC `IfcProduct` scan with complete exact GUID/class set verification, older typed subset consistency, public instruction GUID and required-role crosschecks, original source SHA before/after, conservative all45 report.
- `tests/test_bibimbap_v022_original_source_roles.py` — **26 actual positive/negative tests** for 31 IFC source maps, source question/role/drift, prior report hash, duplicate/missing tasks, native/typed role fraud, named-public-source GUID disagreement, forged model/scorer results, actual non-IFC4X3 source admission rejection in the existing XML session, read-only provenance and source corruption detection.
- `reports/bibimbap_v022_original45_task_relevant_roles_and_xml_input_20261115.json` — **45 sanitized per-task rows**, class names and native/typed counts, source/instruction SHA, historical results, no raw IFC, original full question text, original native GUID inventory, hidden scorer target list or new IFC file committed. SHA-256: `f606994defa7517f898e22ee6e39d5e82da6dc40288c1b38cec25c98b7cd492e`.
- This protocol memo, written only after actual source inspection.

The v0.22 script never imports or calls the original scorer, XML compiler mutator or `ifcopenshell.api` edit tools. It does **not** move/rotate/create/delete any BIM entities, and therefore does not add a sixth native-byte-identical developer task, resolve original scorer source problems or add scored test coverage.

## 4. Verification and reproducibility

**Actually executed new v0.22 QA:** `python -m unittest tests.test_bibimbap_v022_original_source_roles -v` — **26/26 PASS**, 0 failures/errors/skips, **3.633s** test time / **10.094s** enclosing process, with actual independent reopening of all 31 source IFCs. The report generator's standalone real-source audit independently completed with **exit 0, 10.343s**, frozen report SHA as above. **Actual independently completed focused cross-version regression:** 13 selected modules covering v0.3/v0.4/v0.14–v0.22, including real original public IFC Docker execution and original author scorer validation: **188/188 PASS**, 0 failures/errors, **131.356s unittest / 138.047s enclosing process / exit 0** (2026-11-15 KST). This is **not** the historical full-repository 832-case test discovery. The additional sanitized QA ledger `reports/bibimbap_v022_scoped_regression_and_role_census_20261115.json` has SHA-256 `f85981907ce6cdafaead3a8fe6d438225d7c7377d81ba3b11b752dc260607d87`; original public author/data Git status clean and original Docker worker orphans 0, all verified after tests.

On Windows (prior pinned public checkouts, IfcOpenShell 0.8.4.post1 virtualenv, no Docker needed for this new read-only audit):

```powershell
$base = 'D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue158-original45-source-role-audit')
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

& $py -m unittest tests.test_bibimbap_v022_original_source_roles -v

# Output path MUST be new: never overwrite frozen evidence.
& $py -m tools.bibimbap_v022_task_relevant_source_role_audit `
  --root . `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') `
  --output 'results/NEW_UNIQUE_v022_role_source_audit.json'
```

No new provider/model API calls, no paid inference, no original Git author/data/scorer edits, no Xim/BIXML changes, no Git main merge, no dataset copies to the repository.

## 5. Next frozen research priority

**Full semantic authoring parity is still UNPROVEN for every one of the original 45 tasks.** With a verified 9-case role coverage gap and a 3-case schema admission gap, the next highest-value engineering checkpoints are (a) *declared common-support subset* with pre-registered task-specific semantics and native write probes, and (b) the minimal safe XML source-state/schema/opaque-preservation changes needed to handle representative genuine original IFC features. Any future XML schema extension must remain **direct declarative source editing**, never `<Move>` or imperative command wrappers. Also retain the two original author Window grader source-reference mismatches and the `test_16` scorer/native oracle disagreement.

If the paper instead compares the actual as-built systems without equal task source/write capabilities, preregister an explicit **unequal-information descriptive systems comparison** with the original 45 denominator, do not describe the difference as pure XML vs Python causal effect. Neither path is yet authorized for paid LLM experiments without a model, hard budget limit, security boundary and evaluator review.
