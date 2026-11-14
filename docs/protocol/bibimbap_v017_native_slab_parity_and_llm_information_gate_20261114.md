# BIBIMBAP v0.17 — Native original Slab-on-Slab parity, strict information-equivalence gate, and prospective matched-LLM plan

Issue: https://github.com/pikaybh/bim-markup-bench/issues/148

This is a **separate research benchmark repository**; not Xim/BIXML application development. The purpose is to establish what would constitute a *defensible* original-paper-compatible comparison between direct whole-state declarative XML BIM authoring (D) and imperative Python/IfcOpenShell BIM authoring (I), avoiding previously identified source/scorer contamination. Every prior report and the original author/data/scorer remain **untouched**.

## 1. Exact original task and independent native edit

**Original publicly published task:** `topological_test_15`. It instructs moving one existing `IfcSlab` so that it rests on another existing `IfcSlab`, identifying **both** source GlobalIds in the public question. Source is the actual original IFC4X3 file `01/02/01_02_015.ifc`, not a newly synthesized reproduction, normalized from public millimetres to metres **only in an isolated, temporary cloned source**.

The original native IFC world-space mesh yields:
- Original upper Slab world Z minimum = **3.05 m**; original lower Slab world Z maximum = **3.00 m**.
- Native source-derived move = **−0.05 m along world Z**, with original horizontal overlap approximately **1.00 m²**. Upper Slab remains at the same XY position.
- Original IFC point-of-origin `IfcCartesianPoint` is shared by many native references. Mutating that point would damage unrelated original IFC placements. New `tools/bibimbap_v017_independent_slab_on_slab_i0.py` instead performs **copy-on-write** on the target object's unique local placement reference; no unrelated IFC Root, original STEP or remaining Slab shape is changed.

**I0 writer isolation:** This independent *developer-authored* imperative I0 module only imports standard Python, NumPy and native IfcOpenShell APIs. It does not import any project XML runtime, historical D0 report, original author scorer, original author hidden target answers or project tools. Source target IDs come from parsing the PUBLIC question, not the evaluator. Source metre-unit, schema, geometry, finite transforms, rigid native placement and shared ownership are explicitly validated; wrong or unsupported tasks fail closed.

External `tools/oracle_bibimbap_slab_v04.py` independently proves that this I0 edits the *real* source `IfcSlab` by the original question's world delta while preserving the others, and the clone's original source SHA is unchanged.

**Order-preserving external audit:** `tools/audit_bibimbap_v017_topological_slab.py` first completes and freezes I0 candidate IFC + independent native oracle. It then opens previous **frozen** v0.4 D0 evidence (SHA `98166dc3a6c606996a5f9bd43e3b0b26fb2852fb61e1c64ea1154aaefc630fec`) and reproduces the D0 result from original complete declarative XML Slab state with the unmodified XML compiler. Original public question IDs are **independently parsed** again; the prior D0 report cannot target the new I0. The original native XML candidate and original public millimetre IFC output are required to match the historical frozen v0.4 D0 hashes. **Only after both I0 and D0 candidates are frozen** is the original author scorer executed on each. Candidate SHA and original input SHA are verified again afterwards.

| Actual nonblinded developer result | XML D0 | Independent Python I0 |
|---|---|---|
| Original public Slab-on-Slab task | `topological_test_15` | `topological_test_15` |
| Native IFC4X3 result | **Identical SHA** `6fbbea5ddccd22b85c407de17bdb08681ac602574a3402869cb32ae00127c798` | **Identical SHA** |
| Independent native source-only Slab oracle | PASS | PASS |
| Original author score (unchanged scorer) | **1.0** | **1.0** |
| Genuine new model/API inference | **0** | **0** |

The original full **45 public editing tasks** are preserved: exactly **15 create + 15 update + 15 delete**. Previously verified and current developer controls across v0.15–v0.17 now count **5 source-native D0/I0 identical IFC results**; only **3** of these have *confirmed callable original-author scorer results* (`test_15`, `test_16`, `topological_test_15`). Prior `geometry_test_18` / `geometry_test_19` scorer worker failures remain **two separate reference integrity cases**, not 0 scores. The other **40** tasks remain untested under this exact paired native-and-author protocol. Neither developer score nor exact IFC equivalence is a real model comparative outcome.

**Semantic guardrail for another candidate:** Original `test_14` uses the phrase *decrease the height of the slab by 0.5m*. Historical v0.4 D0 interprets this as **lowering Slab elevation**, but it could be interpreted as changing **thickness**. Even though historical original author scorer awarded its D0 1.0, this version does **not** call it an independently unambiguous full-task-success benchmark or include it in the new +1 paired verified count. A source-grounded ambiguity rubric, external expert/author clarification, or explicit prospective sensitivity arms is necessary first.

## 2. Critical source information asymmetry: independently audited original 45/45

`tools/audit_bibimbap_v017_information_parity_gate.py` processes the previously frozen v0.13 original **31 distinct public IFC source** inventory and cross-validates the new 45-case source-and-scorer matrix. It compares **the original native IFC `IfcProduct` count** with the current **safe, editable typed XML state** entity count for each public task, using frozen *source observations*, not the author's evaluation targets or model-generated answers.

**Result:** **45/45** original editing tasks have **strictly more original native IFC products than are represented as editable typed XML objects**. Thus all 45 **fail the strong full-native-original-IFC source information equivalence gate**. Original named *required* source roles may be visible to the typed D view, but that is not evidence that the whole original native IFC, inverse relations, hosted dependencies, geometry or query affordances are equivalent. Equally, absence of a product from the typed view **does not establish it is relevant to that individual task**; this is a conservative *strict full-source* scientific gate, not a statement that all tasks are impossible or that XML is inferior. An expanded read-only source catalog is **not** automatically writable XML and cannot fix backend differences by itself.

The two current proposed research estimands MUST be distinguished:

1. **As-implemented system comparison (descriptive, unequal source information/capability):** D receives task-specific bounded XML projection with trusted source-edit compiler, while I receives an original native IFC object and Python/IfcOpenShell access. Even with the same task/model/tool-call budget, this compares **complete systems** with **different information/operation affordances**. Report it as such; do **not** claim a controlled causal XML-vs-Python representation effect or compare aggregate scores to original paper as if protocols were identical.
2. **Strict information-controlled representation comparison (NOT IMPLEMENTED):** Both LLM arms must be able to observe the *same task-relevant original IFC facts*, and the experiment must prove a task-by-task equivalence certificate including original source products/identities, required links, world-space geometry, unit systems, inverse dependencies, allowed tool queries, and feedback outputs. Both arms must be able to perform the target operation natively (or be explicitly fail-closed). Python cannot have a private extra IFC-inspection feedback channel and D cannot be denied relevant native facts. A *common read facility* or a restricted audited information-access sandbox is needed; mere equality of prompt tokens or 25 tool calls is **not** information equivalence.

Even if both arms receive an identical source fact packet, Python's ability to introspect native IFC **inside the code tool** must be bounded/audited and its observations/feedback accounted for. Restricting it safely must not silently alter the original-paper imperative tool into a different capability. Any controlled arm should be labeled a **new experimental variant**, not misrepresented as reproducing the BIBIMBAP published baseline.

## 3. Matched-LLM study preregistration: protocol decision gates

Before any new paid experiment, freeze and publicly timestamp a protocol specifying:

- **Population:** original 45 public edit tasks (15 per CRUD). Preserve unsupported and scorer-broken cases in the original intention-to-test denominator, and separately show verified-scoreable subset. Do not drop the two corrupted Window reference cases or treat author worker failure as 0 score.
- **Input identity:** exact original task question SHA + original IFC SHA and schema. If benchmark author issues a new dataset/scorer revision, treat corrected cases as a **separate versioned analysis**; do not backfill the historical score table.
- **Read channel:** same underlying source IFC snapshot for each task; declare whether D/I observe full native products or explicitly scoped task-relevant facts. Audit per-tool input/output facts, object identities, inverse relations, world-space geometry, and fallback/unsupported paths. Record whether the source-only XML covers the requested operation.
- **Write channel:** D's entire declarative document is the output, not operation-shaped XML commands. I submits Python/IfcOpenShell code to an isolated native source writer. Both produce real original IFC candidates and freeze their SHA before inspecting scorer. Python execution stdout/stderr/side-effect read channels must be declared as part of observable information.
- **LLM configuration:** same pinned model **snapshot**, temperature, reasoning effort, max provider output tokens, prompt-level instructions, tool call cap (candidate 25 per arm/task aligned with paper), timeout, retries, observation formatting, task-order randomization, sample count and model seed where supported. Avoid comparing to different paper model or context as equivalent.
- **Execution budget:** explicitly approved model/provider, maximum requests/tokens/USD, with durable accounting, enforced stop at cap, no secret/credential ingestion into Git, no paid calls by this preflight. Real LLM experiments are NOT authorized by implementing this gate.
- **Evaluation:** original pinned author continuous metrics and independent IFC structural/geometry oracle are different measurements. Track both per task. Do not alter author scorer to make native-valid IFC obtain a higher mark. `test_16` has author `integrity_constraint=0` despite independent native product/relationship preservation PASS; do not silently call that equivalent success.
- **Outcomes/analysis:** per-task D and I predeclared success and continuous author metrics, scorer failure rate, unsupported rate, edit completeness, API cost/tokens, time and tool attempts, stable source integrity. Paired task-level confidence intervals and category breakdown only after sufficient **real** trials. Developer D0/I0 equivalence and historical GPT-6 Luna single-arm attempts must never become matched LLM scores.

**Release gate is BLOCKED on full native source information parity**; task-specific operation proof of feasibility is not a causal readiness certificate. It is reasonable to run a separately labeled **unequal-information system comparison** later if that is the preregistered question; the present gate explicitly prevents falsely describing it as an information-controlled pure-representation experiment.

## 4. Pinned source and reproducibility

- Original paper code Git commit: `667004e16bd38fd7d538bcee56191465429fd975`.
- Original public data Git commit: `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`.
- These are the same live remote **default branch** HEADs verified read-only on 2026-11-14. This is not a search of unmerged remote PRs or all branches.
- Historical v0.4 D0/author score, historical v0.13 source inventory, v0.16 column parity and original author/IFC files all **unchanged**. New results:
  - `reports/bibimbap_v017_original_topological_slab_I0_D0_author_parity_20261114.json`: SHA-256 `c6b02877a3f031c8f5435222b65db4a0fef04568119eaa750586f106d53231e8`
  - `reports/bibimbap_v017_original45_information_parity_gate_20261114.json`: SHA-256 `c2683de1705b92ebe0ce8472c6a870b98c54c668e387ddf80c9377cdb2e88078`
- **Actual scoped regression:** `python -m unittest tests.test_experimental_v4_slab tests.test_experimental_v3_column_crud tests.test_experimental_v14_native_window_delete tests.test_bibimbap_v14_original_hosted_d0 tests.test_bibimbap_v015_i0_source_parity tests.test_bibimbap_v015_fixture_admission tests.test_bibimbap_v016_scoreable_column tests.test_bibimbap_v017_topological_slab_and_information_gate -q` — **99 tests, 99 PASS, 0 FAIL, 129.341 seconds, exit 0**. New v0.17 12 tests separately **12 PASS, 5.128 seconds, exit 0**. The historical **whole repo 832-test discovery suite was not green** in prior worktree because of missing ignored fixtures, legacy script environment and code page behavior; this does not change by passing newly selected regression tests.

Reproduction on the connected Windows research machine:

```powershell
$base = 'D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue148-topological-slab-i0')
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

& $py -m unittest tests.test_bibimbap_v017_topological_slab_and_information_gate -v

# Choose two NEW unused output paths; neither script overwrites frozen evidence.
& $py -m tools.audit_bibimbap_v017_topological_slab `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') `
  --prior-v04-d0-report 'reports/bibimbap_v04_slab_developer_d0_20261113.json' `
  --prior-v016-report 'reports/bibimbap_v016_original45_scoreability_and_column_parity_20261114.json' `
  --output 'results/NEW_UNIQUE_v017_original_slab_parity.json'

& $py -m tools.audit_bibimbap_v017_information_parity_gate `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') `
  --frozen-v013 'reports/bibimbap_v013_original45_safe_native_read_catalog_20261114.json' `
  --v017 'reports/bibimbap_v017_original_topological_slab_I0_D0_author_parity_20261114.json' `
  --output 'results/NEW_UNIQUE_v017_full_source_parity_gate.json'
```

## 5. Next work priorities

1. **Design equality of observations** without secretly granting one LLM access to more task-relevant IFC facts. Either implement the common audited read/feedback layer, or preregister an explicitly non-causal unequal-information system comparison.
2. Triage and seek author clarification/errata for original `geometry_test_18/19` missing source target references, original `test_16` integrity predicate conflict, and `test_14` height/elevation ambiguity; do not edit hidden GT, author scorer or older metrics.
3. Add further source-only original task-specific D0/I0 **independent candidate + native oracle + author scorer** controls from the untested 40 while preserving all-45 denominator. Even if developer proofs succeed, do not label them LLM trials.
4. Once a defensible study protocol and payer-approved budget exist, run a small true matched pilot with exhaustive per-task source/observation/model provenance and meaningful independent-vs-author scoring, then progress to the original public 45-case cohort. Do not make unverified percentage claims.
