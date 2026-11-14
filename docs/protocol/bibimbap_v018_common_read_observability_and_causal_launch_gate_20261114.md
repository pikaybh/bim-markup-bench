# BIBIMBAP v0.18 — Original 45-task common read-only IFC source evidence

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/150
**Parent:** v0.17 Issue #148 / Draft PR #149 at `1fccbaf6b85b0a81913d348e43de33b4471fdbcd`
**Research identity:** independent `bim-markup-bench` scientific experiment, **NOT** BIXML or Xim implementation.

## 1. Hypothesis and hard boundary

Research question: is the difference between direct declarative XML source authoring (D) and imperative Python/IfcOpenShell native authoring (I) measurable on the original public BIBIMBAP data under sufficiently comparable **source information**, tool observations, model and native editing capabilities?

Prior v0.17 source audit demonstrated that **45/45 original tasks** include original native `IfcProduct` objects absent from the bounded safe editable XML typed view. The current imperative Python arm could introspect the full original IFC directly. Matching only the public question, model, 25 tool calls and rubric is **not** a full original-source information-controlled comparison.

**This checkpoint implements a common READ-ONLY source fact channel, not a fully secured LLM A/B execution environment.** The original declarative arm remains a full XML state editor with native conversion outside the model; this source packet contains no BIM modification tool and no XML `Create`/`Update` operation wrapper. The I arm still requires an externally isolated one-shot Python writer to eliminate direct native filesystem read/feedback bypass. No real LLM trials are conducted in v0.18.

## 2. Actual source data and encoded facts

Pinned unchanged original public inputs:

- BIBIMBAP author code commit `667004e16bd38fd7d538bcee56191465429fd975`.
- BIBIMBAP public data commit `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`.
- All **45 original** public tasks retained, **15 create + 15 update + 15 delete**, over **31 distinct original IFC sources**.
- Actual IFC schema distribution over 31 sources: **28 IFC4X3, 2 IFC2X3, 1 IFC4**.
- Total native `IfcProduct` identities over the distinct 31 IFCs: **480 of 480 included** in the exported source inventory (all 22-character public-native GUIDs), no invented product and no source files committed.
- Native source IFC geometry: **355 products with computed physical world metre bbox** and **125 with no original shape representation**; the latter are explicitly marked `NO_SHAPE_REPRESENTATION`, not assumed to have no physical consequence.
- Native world placements: **480 available**, original source unit-to-metres scale recorded per IFC.
- Native `IfcRelationship` records: original link GUID/type with direct `IfcProduct`-reference roles, spatial containment, names/description, representation identifier/type/count. This is NOT an exhaustive export of every IFC attribute, material, property set, mesh, geometric topology or indirect relationship.

Module `tools/bibimbap_v018_common_read.py` performs one **outside-model** original-source IFC read, validates source SHA-256 and schema, and produces deterministic canonical UTF-8 JSON bytes (sorted keys, stable float metre rounding, no timestamps, no local filesystem paths). Original IFC is **never copied into the Git repository**. A source snapshot can be bound to a different **public question SHA** while all native IFC-derived facts remain byte-for-byte unchanged, allowing multiple original tasks to share an original source IFC without repeated geometry extraction.

The server-side builder is **NOT** part of a model's tool surface. Only the `CommonReadSession.request()` operations are intended as a future host-level model-observation API. A production external host must restrict model access to that interface; importing the source builder or Python runtime into a model tool is **not** sandboxing.

## 3. Equal read response and replay receipts

For each original task, two **separate** arm sessions are instantiated from the **same immutable source fact packet SHA-256**. The expected packet SHA is mandatory for both sessions; noncanonical/truncated/mismatched bytes fail closed. Each arm has the same enforced hard limit of at most **25 read calls per task**.

Read operations only (exact names, no writes): `source_summary`, `list_all_products`, `list_by_class`, `get_product` (original public source GUID), and `related_relations` (original product reference links). All responses are deterministic canonical bytes; both sessions expose the same source facts, do not return source file paths or native IfcOpenShell objects, and record SHA-256 of each exact canonical request/response. Receipts contain arm, packet hash, call count/cap and per-query hash; only digests and counts are committed to evidence reports, not all original public objects or datasets.

`tools/audit_bibimbap_v018_common_read_45.py` executes original-source only replay for **every one of the 45 original tasks**, checking prior frozen v0.17 original source census and public question and original IFC digests. It queries original source summary, every product identity, at least one actual native source product class, and actual PUBLIC-named source target and native relationship references where the public instruction names them; otherwise it exercises a deterministic non-target source product. **45/45 cases returned byte-identical D/I observations with identical tool-call counts and hash transcripts.** That is an *interface observation invariance result* under scripted queries, not an LLM acting through the interface.

The prior true native developer edit controls `test_15`, `test_16` and `topological_test_15` were also checked through identical D/I common read sessions. Prior v0.17 output still stands separately: **5/45 independently developer-edited IFC byte-identical D0/I0** and **3/45 with actual original-author-scorable D0/I0**. Earlier original author scorer failures for `geometry_test_18/19` stay as distinct nonzero-error statuses; other **40 tasks are untested under the original source edit+author grader protocol**. The v0.18 read audit does **not** add 45 scoreable edits or 45 actual LLM trials.

## 4. Fail-closed real LLM launch gate (NOT SANDBOXED YET)

`strict_llm_trial_launch_gate()` explicitly checks these blockers:

- Python can mount/open the original native IFC outside the common-read facility.
- Python has unrestrained filesystem/exec observability outside a verified OS-level sandbox.
- No independent external sandbox attestation or no matched native write capabilities.
- No exact common source read response parity or no **explicit approved paid LLM model/budget**.

**Current real causal LLM launch status: `BLOCKED`.** Even with caller-provided flags set to pretend all constraints are satisfied, this module never authorizes a launch: `causal_real_LLM_launch_permitted_by_this_module = false`. A boolean is NOT a security proof; a real externally verified OS/confinement boundary and independently testable one-shot native writer are missing. LLM-generated imperative code must not be executed in the LLM tool process with an original-source IFC path or hidden grader/answer access. Its future native execution needs isolation and **no iterative native-source stdout/stderr/exception side-channel feedback** during solution authoring. This package does not and cannot enforce filesystem or network security by parsing Python source alone.

**A shared packet does not establish all information parity:** D additionally sees its typed XML editing state, I might see all IFC-native properties during execution; common packets omit full IFC attributes, topology and properties. A future causal claim requires an independently certified **complete observation and native write capability scope**, not simply SHA equality of these packets. If the study instead deliberately compares *the as-implemented systems*, that is an **unequal-information systems comparison**, not pure-representation effect, and must be preregistered as such.

## 5. Scientific provenance and rights

- Original public files, evaluation code, prior versioned D0/I0 reports and source SHA are read-only, never patched to boost original author scores or fix upstream inconsistency.
- `reports/bibimbap_v018_original45_common_read_observation_audit_20261114.json` stores **sanitized per-task hashes/status/counts**, no original IFC file bytes, product GUID inventory, full public question text, local filesystem paths, hidden target lists, original author scorer code or model/provider tokens.
- The source packet contains original IFC public source-derived data and is generated locally **outside Git** on demand, avoiding dataset/license redistribution as a derived full structured IFC export.
- **Verified new 20 unit tests:** 20/20 PASS in **3.669 seconds**, exit 0; direct original 45-task report reexecuted independently to a unique ignored output and **identical SHA-256 `89a53c28a9c5e679fcdfb962bebe6b9bd8075e4ac0437e07ea1a0b72ea7b1b2a`** confirmed. Original v0.17 info report SHA `c2683de1705b92ebe0ce8472c6a870b98c54c668e387ddf80c9377cdb2e88078` unchanged.
- **Actually run combined scoped regression:** `python -m unittest tests.test_experimental_v4_slab tests.test_experimental_v3_column_crud tests.test_experimental_v14_native_window_delete tests.test_bibimbap_v14_original_hosted_d0 tests.test_bibimbap_v015_i0_source_parity tests.test_bibimbap_v015_fixture_admission tests.test_bibimbap_v016_scoreable_column tests.test_bibimbap_v017_topological_slab_and_information_gate tests.test_bibimbap_v018_original_common_read -q` — **119/119 PASS / 0 FAIL / 107.588 seconds / exit 0**. This is a 9-module focused regression, not full repository discovery.
- New paid API calls: **0**. New real LLM D/I trials: **0**. No external data downloads or source revisions. Historical full repository test discovery (832 previously observed in older worktree) is NOT green; scoped new regression results must not be presented as full-suite pass.

## 6. Reproduction

Requires original public author and dataset Git checkouts at above pinned HEADs, an existing IfcOpenShell-capable local Python venv, and no external network, API token or GPU.

```powershell
$base = 'D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue150-common-source-facts')
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

& $py -m unittest tests.test_bibimbap_v018_original_common_read -v

# Output path MUST NOT exist; never overwrite previous evidence.
& $py -m tools.audit_bibimbap_v018_common_read_45 `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') `
  --prior-v017-information 'reports/bibimbap_v017_original45_information_parity_gate_20261114.json' `
  --prior-v017-slab 'reports/bibimbap_v017_original_topological_slab_I0_D0_author_parity_20261114.json' `
  --output 'results/NEW_UNIQUE_v018_original_45_common_read.json'
```

Future actual causally controlled study needs separately approved model/cost, a preregistered 45-case question/IFC/operation matrix, a protected host with identical source observation and feedback, and a sealed one-shot Python editor that cannot reveal extra source facts during authoring.

## 7. Future research priority

1. Implement and test an **OS-backed isolated offline sealed single-execution Python authoring worker**, controlled by the host and outside model; equal knowledge of the original IFC is not guaranteed by this fact packet alone. Verify wall-mounted source access, import/file/network restrictions and stdout/exception no-feedback on adversarial dummy scripts before treating it as sandboxed. Never execute untrusted Python on the connected research Windows PC without robust isolation.
2. For both arms, establish task-by-task **native write-capability equivalence** or mark unsupported tasks explicitly in the original 45 denominator; do not require an opaque IFC reading to be editable XML.
3. Seek corrected version/provenance from original benchmark maintainers for `geometry_test_18/19` absent source references and `test_16` integrity predicate and `test_14` slab height ambiguity, maintaining previous metrics unchanged.
4. Only then run paid matched-LLM pilots, after an explicit model/budget cap authorization, with same model, question, source, time/calls and independent grader. Never infer a source information equality or model XML advantage from current developer-led proof of concept.
