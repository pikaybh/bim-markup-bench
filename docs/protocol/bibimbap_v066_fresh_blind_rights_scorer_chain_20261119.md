# BIBIMBAP v0.66 / Issue #247 — independent blind-source, per-IFC rights and paper-scorer identity gates

**Status: UNRESOLVED EXTERNAL GATES; offline metadata evidence verified, not a new model experiment or blind certification.** This document concerns only the independent bim-markup-bench research repository, not product BIXML/Xim. It does not amend any frozen historical IFC, author grader, target, source/question, earlier score, or publication. Owner/provider launch consent is NOT inferred.

## 1. What actually changed, and why

The earlier v0.65 cohort and v0.66 exposure reports establish 45 edit tasks in 31 original source SHA256 clusters. Previous v0.43 automation **opened/processed all 31 original IFCs** and counted actual native products and representations; v0.46 also paged native IFC data from 27, and 10 families have explicit task-specific developer evidence. The remaining 21 have *not* been independently cleared for task-specific human inspection. A prior 36-call XML-only LLM exercise does not constitute matched D vs I validation. No original source in the catalog is independently certified untouched.

**Hard consequence:** The 21 families with no documented human target-specific developer control CANNOT be called independently blind. Even an independent fresh reviewer cannot retroactively make already programmatically examined native sources pristine. The existing 31 historical SHA clusters remain useful for clearly labelled **developer engineering / historically exposed exploratory** work only, until a separately adjudicated permissible research role is decided. A truly fresh confirmatory source family must be acquired and independently audited with its own frozen SHA and separately access-controlled private evaluator, instead of reassignment of known source tasks.

The new gate module tools/bibimbap_v066_fresh_source_chain_gate.py uses only SHA identity and untrusted metadata references, refusing all known historical SHAs and incomplete intake dossiers. No IFC bytes, original author test/grader contents or private GT are opened. **Every** mock dossier remains blocked even if all fields contain plausible-looking document hashes or someone claims authorization: there is no independent verified trusted reviewer/rights-holder signature service available in this research environment. A SHA of a document proves only a referenced digest, not legal authority, signature authenticity or provenance. The module has no provider/execution activation method.

The auditor tools/audit_bibimbap_v066_fresh_source_scorer_provenance.py checks existing SHA-pinned historical research **JSON** reports and local author Git **commit/tree/blob metadata** only, applies 31 source metadata rules, tests forged approvals and a synthetic all-claimed dossier, and regenerates the canonical frozen result without external network access.

**Frozen report:** reports/bibimbap_v066_fresh_blind_rights_scorer_chain_20261119.json

**SHA256:** 93f8eacd2b0767c3bda5ae3f509f90a122973064f48ed9c70c3c807321798464

## 2. Reproducible findings

| Cohort/provenance fact | Actually verified | Scientific/rights interpretation |
|---|---:|---|
| Original source SHA clusters in fixed 45 edit-task subset | 31 | Task rows sharing IFC source are not independent observations |
| Original IFC source clusters already native-processed by old audit | 31/31 | All historically preprocessed, not a clean prospective new source |
| Source clusters with explicit task-specific developer source controls | 10 | Known task-specific developer exposure |
| Other source clusters not independently cleared for task-specific human inspection | 21 | Unverified; **not certified blind** |
| Independently certified untouched original sources | **0** | No prospective confirmatory source admission |
| Original IFCs with creator/individual asset license/attribution chain verified | **0/31** | Card-level cc-by-4.0 label does not establish asset title |
| Original IFCs with provider upload AND retention rights verified | **0/31** | External IFC transfer remains blocked |
| New independent external reviewer signatures verified | **0** | Cannot self-attest out of a ChatGPT/agent session |
| Original author grader/GT files read in this audit | **0** | Only previously recorded discrepancy metadata used |
| New provider calls, original IFC uploads | **0** | No actual model trials |

In the frozen matrix, each historical SHA has its native-inspected status and separate licensing, attribution, transfer/retention, task-specific exposure and provider-trial blocking flags. The source file *contents*, target IFCs, original grader source and evaluator answer are NOT in this report.

## 3. Future independent source intake — 15 hard evidence references, not approvals

A future external independent reviewer and original IFC rights holder would need these metadata/reference types before proposing anything to the owner:

1. Immutable original IFC SHA256 plus creator legal-identity reference and creation/chain-of-custody document hash.
2. Rights-holder authority hash, per-original-IFC specific license grant hash, attribution fulfilment document hash.
3. Explicit grant for transfer to the **named model provider**, including the original IFC in its actual data form, and a separate provider retention/deletion-scope terms hash.
4. Independent reviewer identity reference, independently signed original source-blind-history attestation hash, and an **out-of-band independent trust-channel reference**, with audit of all developer and provider prior exposures.
5. Source task definition hash and precise scorer contract revision hash; independent paper-vs-repository scorer SHA/tag crosswalk hash.
6. Explicit research owner trial-consent document hash, plus independently preregistered arm/model/cohort/budget details in a *new* protocol version.

The intake checks 15 named fields. The names and hashes are placeholders for a future **external validation process**, not signatures. File hashes alone are forgeable claims. The current research tool cannot cryptographically verify a rightsholder signature, a reviewer's independence or provider terms; therefore its strongest possible result is **COMPLETE_CLAIMS_UNVERIFIED_AWAIT_INDEPENDENT_EXTERNAL_REVIEW**, never provider approval. Changing any of these metadata booleans cannot bypass the separate unconditional old refusal function.

**Never place a new unseen source, creator personal IDs, signatures, task answers, private evaluator or IFC content directly into a PR, public Git issue, an LLM prompt or a shared cloud service.** An independent review process must keep the source and private answers partitioned with documented access controls. The source can later be identified to the research project by its hash only after permissions and acquisition are explicit.

## 4. Original author's scorer provenance: pinned Git object identity is not published scorer equivalence

The *local* original author checkout was read **only through Git object metadata**, not through the contents of original grader/tests/private answers:

| Git provenance item | SHA / evidence |
|---|---|
| Original author repository | https://github.com/nbharathik/bibimbap |
| Pinned commit | 667004e16bd38fd7d538bcee56191465429fd975 |
| Original data/tests directory tree Git OID | bcadba5d036dbe011d9794da994ac926f8febb44 |
| Original benchmark.py Git blob OID | 8d1e5740b02b8b81b74987ac7dbe37c2aed55aca |
| Tracked paths under original data/tests directory | 108 (filenames only, not number of 100 benchmark task records) |
| Recognized top-level LICENSE file in this checkout | None |
| Local tags pointing at pinned commit | None |
| Independently linked official EC³ paper scorer SHA or tag | **Not obtained** |

The [official EC³ 2026 BIBIMBAP publication page](https://ec-3.org/publication/ec32026_271/) gives DOI 10.35490/EC3.2026.271, 100 curated CRUD tasks and a best reported baseline 50.2%; **neither number is the 45-edit subset's score**. The paper landing page and this Git checkout do not provide a demonstrated canonical same-version release crosswalk. There are existing *historical* records of scorer-vs-public-task concerns: topological_test_05 (interior versus exterior hosted Door admitted by earlier author score), geometry_test_19 (original source lacking GUID assumed in pinned scorer), topological_test_17 (legal dependent cascade rejected by retained-property check), and geometry_test_03 (nearer versus farther +Y Door scored differently). These records are quoted from frozen local research metadata: **the original author test files were not reopened or re-executed here**. Any official-score statement must wait for a verified published scorer version and independent evaluator-only adjudication.

The original Git commit and tree/blob OIDs are immutable identifiers for **the pinned local checkout**, NOT proof that copyright has been granted or that the official publication used those exact evaluator bytes. The presence or absence of a top-level LICENSE file in one checkout is **not a legal conclusion**. The dataset metadata previously reported cc-by-4.0 at card level, which alone is insufficient evidence of the creators' underlying asset rights or individual provider-transfer terms.

## 5. Remaining sequential steps and what cannot be self-completed

1. **Independent new blind source:** Acquire a source *not belonging to the old 31 SHA clusters*, from an independently controlled creation/selection workflow. Have an independent external reviewer verify no prior developer/task answer exposure and preserve a separate hidden scoring source. No automated review of unseen source geometry or grader may occur during the quarantine certification phase.
2. **Rights owner + provider terms:** Obtain documentary proof and independently authenticate the source creator/rightsholder, per-file license, attribution, provider-specific transfers and retention/deletion approval. No email/Slack messages have been sent here.
3. **Official evaluator identity:** Obtain a publication-backed scorer release SHA/tag (or author confirmation with traceable evidence) and independent mapping to this pinned checkout. Do not call a repository checkout paper-official on the strength of a paper title or task count.
4. **Owner-approved preregistration:** After (1)–(3), freeze cohort SHA manifest, user/provider-approved model snapshots, decoding, tool affordances, seeds, timeouts, maximum exact billed tokens, cost cap, randomization, primary ITT outcome and cluster-level analysis, then authorize any trial separately. Keep genuine confirmatory sources and GT out of training/implementation tools.
5. **Do not merge/release by assumption:** Existing Issue #247 and Draft PR #248 remain research-only/open until these *external* gate conditions are independently fulfilled. Zero new model calls and zero rights changes.

## 6. Offline reproduction

    $py = 'D:\문서\D__1_Projects\202611\bim-markup-bench\.venv\Scripts\python.exe'
    & $py -m tools.audit_bibimbap_v066_fresh_source_scorer_provenance --check
    & $py -m unittest -q tests.test_bibimbap_v066_fresh_source_scorer_gate

The check revalidates the 31 historical SHA registry and external-transfer blocker from frozen reports, reads author Git identifiers only, tests a synthetic complete-but-untrusted dossier and ensures even forged owner/provider approvals do not launch a trial. No new IFC file, private scorer, model tokens, author task scores, network provider or original IFC upload is accessed.
