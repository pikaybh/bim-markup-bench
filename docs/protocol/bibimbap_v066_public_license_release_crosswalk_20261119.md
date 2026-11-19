# BIBIMBAP v0.66 / Issue #247 — public MIT license, publisher methodology and external IFC candidate

**Status:** Verifiable public-publisher metadata snapshot dated 2026-11-19, NOT proof of an officially pinned paper scorer release, automatic IFC permissions, new independent blind benchmark source or a model trial. Independent bim-markup-bench research only. BIXML/Xim and the original author checkout remain untouched.

## Implementation and immutable evidence

- Metadata normalization and fail-closed checks: tools/bibimbap_v066_public_publisher_crosswalk.py
- Offline author-pinned Git tree and prior-rights audit: tools/audit_bibimbap_v066_public_publisher_crosswalk.py
- 53 positive/negative unit tests: tests/test_bibimbap_v066_public_publisher_crosswalk.py
- Frozen canonical report: reports/bibimbap_v066_public_scorer_license_candidate_crosswalk_20261119.json
- SHA256: 381795b45366e20c27f200de90b7e611411fef95347a734e39e1784a3298eb6f

The source IDs below were read from public publisher or GitHub **metadata** without reading additional original IFC, original author grader/GT source contents, new dataset IFC files, private benchmarks, or model provider data.

## A. New finding: publicly posted upstream source now has MIT license

The pinned local original author checkout at commit 667004e16bd38fd7d538bcee56191465429fd975 (2026-04-07) has NO root LICENSE file. Current public upstream main was observed at commit 88ad844937de6e62eebff284ddaab479db8dc9d3 (2026-11-16): commit message "Add MIT License to the project". Its LICENSE Git blob object ID is a2e850d10ddfd0ceb4f6cad7fe1b7a7df4e0a7bb and its published text is MIT software-license terms.

Source links:
- Main immutable tree: https://api.github.com/repos/nbharathik/bibimbap/git/trees/88ad844937de6e62eebff284ddaab479db8dc9d3
- Published LICENSE at commit: https://github.com/nbharathik/bibimbap/blob/88ad844937de6e62eebff284ddaab479db8dc9d3/LICENSE
- License commit history: https://api.github.com/repos/nbharathik/bibimbap/commits?path=LICENSE
- Public releases: https://api.github.com/repos/nbharathik/bibimbap/releases — 0 results observed.

A separate read-only LOCAL Git ls-tree of the original author pinned April checkout shows **10** tracked root paths. The publisher current main root tree shows **11** paths, exactly the ten original Git object IDs plus **LICENSE alone**. Specifically, Git blob benchmark.py = 8d1e5740b02b8b81b74987ac7dbe37c2aed55aca, data subtree = ef5998c5f5817c961f2aa95634c547c5b4fea70b, original data/tests tree = bcadba5d036dbe011d9794da994ac926f8febb44. The author scripts, package requirements, docs, config and all other tracked directory/file OIDs also match byte-for-byte by Git object identity. No original scorer file contents were opened to make this verification.

**Resolved:** Current public upstream Git-tracked source now has a published MIT license. Every Git-tracked source object from the old pinned checkout is identical to the newly licensed public main snapshot. Preserve MIT notice and seek proper legal attribution if reusing publicly licensed software.

**Not resolved:** The old commit itself has no LICENSE; no publication-authorized exact EC³ scorer release tag was identified; a same-byte source tree cannot prove the exact archived runner configuration, external provider versions, task assignments, scorer settings or July 2026 paper score reproduction. MIT applies to the public software project, **not automatically** to original author IFC models, private task answers, student data, embedded third-party product families, retention/export of copies or model provider upload. Previously frozen individual IFC rights checks (31/31 unverified) remain unchanged and blocked.

## B. Official publisher paper task denominator and native-tool baseline

Publisher primary paper: https://ec-3.org/wp-content/uploads/2026/08/EC32026_271.pdf

DOI 10.35490/EC3.2026.271; arXiv identifier 2611.09933.

The paper methodology describes 100 curated tasks across five reasoning categories containing 20 each. The first three categories each contain five per CRUD operation, while the other two categories contain twenty Read tasks each. Consequently:

| Operation | Tasks computed from published structure |
| --- | ---: |
| Create | 15 |
| Read | 15 + 20 + 20 = 55 |
| Update | 15 |
| Delete | 15 |
| Total | 100 |
| All native IFC edits (Create/Update/Delete) | **45** |

Our historically pinned original edit subset is 45 tasks, so **category-level count correspondence is established**, not exact per-task file/grader version identity. The published 50.2% best model (Claude Opus 4.6) is an average **over all 100**, not the score for those 45 edits and not necessarily a strict all-metrics pass rate. The paper scores each task as the fraction of satisfied metrics; the task-specific metric denominators differ.

**Critical condition mismatch:** The paper's LLM baseline exposes one general Python/IfcOpenShell function tool (execute_ifc_code) and allows **up to 25 calls of that function**, including code-based reads/inspection. Our earlier prospective three-arm protocol uses **one shared read + up to 24 editing submissions = 25 total**, which is NOT equivalent to the paper baseline despite equal integers. Do NOT compare trial costs or tool budgets to the published baseline as if the sessions or task opportunities matched. Other mismatches remain: model snapshots, prompts, feedback, runtime, pricing and scorer snapshot. Paper says each task-specific IFC test was validated by another person; that is a **published author assertion**, not an independently authenticated signed grader archive seen here.

Paper reference points: pages 3 and 5 (zero-index PDF pages 2 and 4) for benchmark structure and max tool calls; page 6 (zero-index page 5) for 50.2% and model names.

## C. Public IFC candidate (separate from the old 31 source families): GNI BIM Dataset

Project: https://github.com/ZijianWang-ZW/GNI-BIM-Dataset

Observed main commit: e607ada78e8ae704aea7e381e7036c792ff8eba1

Original public evidence:
- README Git blob aa14b4805068d8e6ebcd607b9913c486ec603aca.
- Repo LICENSE Git blob 147670bb346bd87591f8e8663d70b7448fe74b4a.
- IFC-models subdirectory LICENSE Git blob e685f84a389b1e30e3740be2f034d813dea34909.
- README and IFC directory describe 224 anonymized TUM student IFC models, grouped 208 + 16, with declared original authors' consent under **CC BY 4.0**.
- Explicit README disclaimer says some original IFC content may incorporate **third-party product families**, with no warranty of those modeling contents.
- Dataset version download DOI: 10.5281/zenodo.19722011. Citation concept DOI: 10.5281/zenodo.19722012. These are different DOIs, neither is a SHA256 of a specific IFC in this research worktree.

The published source-specific license is a meaningful, concrete improvement over a generic benchmark-card licensing label. However, this is **metadata-only discovery**, not actual sampling: zero IFC files acquired or inspected; no specific model SHA, no third-party component audit, no out-of-band rightsholder signature verification, no named provider terms/retention permission, no independently sealed question/GT, and no confirmatory blind certification. It does not suffice to start a paid or free LLM trial. Candidate status: PUBLIC_METADATA_SOURCE_CANDIDATE_ONLY_NOT_A_TRIAL.

## D. Ordered next external steps

1. Have an independent, authorized source steward and legal reviewer select a GNI or equivalent source in a restricted external environment, review the CC BY author consent and embedded third-party components, and record source-specific attribution/license/transfer/retention evidence. Do not acquire IFC via this development agent by merely following a public archive link.
2. Have a separate independent task and scorer steward prepare new original C/U/D tasks and sealed private reference IFC/answer/evaluator, with a second qualified reviewer independently inspecting the rubric without exposing it to the model or editing developer.
3. Obtain the author-endorsed archived evaluation source SHA/tag AND paper-execution environment/metric configuration, then verify its equivalence to the pinned task-specific tests. A current public MIT code tree alone cannot certify paper score parity.
4. Obtain explicit owner permission to launch anything, including pinned model/provider/version, per-source transfer rights, retention scope, costs, accurate billed token caps, fixed cohort and paired analysis seeds. No outbound messages or new provider calls have been made.

## E. Reproducibility

    $py = 'D:\문서\D__1_Projects\202611\bim-markup-bench\.venv\Scripts\python.exe'
    & $py -m tools.audit_bibimbap_v066_public_publisher_crosswalk --check
    & $py -m unittest -q tests.test_bibimbap_v066_public_publisher_crosswalk

The offline audit confirms the local old pinned Git object tree and prior frozen source/license report SHA, and compares them with **cached immutably pinned** public metadata observations from November 19. It does not fetch external URLs at check time, certify a publisher signature, read private graders/IFCs or authorize LLM/provider usage. For future currency, re-check source URLs read-only before any separate externally authorized intake.
