# BIBIMBAP v0.66 / Issue #247 — official Zenodo archive metadata, DOI correction and protected five-role source intake

**2026-11-19. Status: public metadata and synthetic evidence-flow checks only.** No new independent blind IFC source acquired, no source IFC/GT/evaluator read, no provider calls, no original IFC upload. BIXML/Xim production and original author files remain untouched.

## 1. Authoritative Zenodo DOI correction and archive accounting

Zenodo official read-only REST API: https://zenodo.org/api/records/19722012

- Record ID 19722012; version 1.0.0; publication date April 24, 2026; license id cc-by-4.0.
- **Correct version DOI: 10.5281/zenodo.19722012**.
- **Correct all-version concept DOI: 10.5281/zenodo.19722011**.

**Correction:** Previous v0.66 GitHub/README metadata interpretation inverted the roles of these two DOIs, mistaking a link used for download as the version identifier and the citation link as the concept DOI. The new Zenodo REST record explicitly exposes both roles. Old frozen reports and SHA checks remain immutable; this document and its new audit supersede only the DOI role interpretation.

### Seven officially listed files (no files downloaded)

| File | Exact size (bytes) | Publisher-reported checksum |
| --- | ---: | --- |
| 2025_BIMfundamentals.zip | 503,285,210 | md5:bab737c3cfb3ff0443f1cc43355b589c |
| 2026_BIMprojects.zip | 221,053,555 | md5:bc4bfb90313162c68a3ec4e24a0d33cf |
| class_distribution.png | 195,135 | md5:6e1bb235811413ad599e2e567bca56f7 |
| group6.png | 1,702,879 | md5:b90d5b9bd342ac32f55f68769c02a72b |
| LICENSE | 341 | md5:6389478e64b473658a64093199bef598 |
| other_online_BIM_model_resources.csv | 6,839 | md5:fcb578106523ca9b283ae43a042b789d |
| README.md | 4,288 | md5:56aa9ea145afcf63a805694eaebc3e1b |

**The two source archive ZIPs total 724,338,765 bytes** (724.3 MB in decimal SI). All seven files total **726,248,247 bytes**. The publisher claims 224 anonymized IFC models in two collections, 208 and 16. Their license metadata is CC BY 4.0 and they publicly assert authors' consent.

These checksums are ZIP-file MD5 metadata, NOT SHA256 of individual IFC models. They have not been validated against any downloaded bytes. MD5 is not collision-resistant evidence of authorship or file-level rights. Individual IFC SHA values, exact archive member contents and independent source suitability remain unknown. Download/extract/IFC inspection count is **0**. The large archive acquisition needs separate storage and data-owner authorization.

The public README warns that models may include third-party BIM product families. Public CC BY 4.0 rights/attribution are meaningful positive metadata, but they do NOT establish file-level creator signatures, every embedded library object's rights, a particular external provider's retention terms, absence from LLM pretraining, or an independently constructed task/GT.

## 2. Independent five-role source intake barrier

Offline tool: tools/bibimbap_v066_zenodo_source_handoff.py

It accepts public metadata-only claims from five *different* steward roles. All must refer to the **same NEW original IFC SHA** not in the old 31 source clusters.

| Independent role | Responsibility outside developer/model sandbox |
| --- | --- |
| source_steward | Obtain source under explicitly approved acquisition/storage, compute SHA256 and preserve chain of custody |
| task_evaluator_steward | Independently create sealed new C/U/D tasks and hidden evaluator/GT, with no developer/model answer exposure |
| independent_blind_reviewer | Review no-prior-development exposure, source/task boundaries, reviewer independence and sealed evaluator isolation |
| rights_reviewer | Authenticate original author consent, per-file CC BY obligations, embedded third-party products and provider-specific transfer/retention rights |
| research_owner | Sign a separate future preregistration, exact cohort/model/task/seed/cost limits and execution authorization |

Public receipts accept ONLY the five text fields role, steward_pseudonym, source_ifc_sha256, evidence_document_sha256 and scope_revision. Actual reviewer names, original IFC bytes or filesystem paths, GT, private targets, code, credentials and signatures are not stored in PR. The checker rejects extra fields, duplicate roles/pseudonyms, mismatched source hashes, old previously inspected original IFC hashes, invalid SHA and incorrect role scopes.

**CRITICAL:** Synthetic receipts and even five role-complete real-looking hashes return only **UNVERIFIED_EXTERNAL_ROLE_ATTESTATION_NOT_ADMITTED**. There are NO configured independently trusted signing public keys or legal identity verifications here. A document hash does not authenticate its rightsholder or reviewer. Real external trust anchors and signed documents need separate out-of-band audit. Neither true developer unfamiliarity nor true LLM pretraining non-exposure is automatically established for publicly published IFCs. The original unconditional no-provider gate is not modified. No trial launch method is implemented.

## 3. Crosswalk and outreach preconditions

The MIT License added to current upstream BIBIMBAP public code and unchanged previous Git object IDs demonstrate source-code continuity, but NOT the **exact EC3 published 100-task scored run** or its original runner/model/environment snapshots. The existing 45 edit tasks and 31 already inspected IFC clusters remain developer/exploratory only. Official published paper scorer SHA/tag is still unproven. There are no independent blind samples approved.

Two *proposed questions only* for separately authorized external outreach (none sent here):

**GNI dataset rights question:** Please identify whether the CC BY 4.0 license and student consent cover the specific IFC under consideration, including third-party embedded BIM libraries. Please confirm attribution obligations and whether sharing that source with a particular external AI model service under its stated retention/deletion contract is within the creator's and rightsholder's authorized scope.

**BIBIMBAP paper evaluator question:** Please identify the exact archived Git commit/tag and IfcOpenShell/model/decoding/scoring configuration used for the EC3 publication, and confirm whether the publicly pinned benchmark source/test-tree objects correspond to that execution. Can that version crosswalk be shared without exposing benchmark answer-bearing private reference assets?

No email, Slack, GitHub issues to third-party repositories, paid inference or data upload was initiated.

## 4. Reproducibility

Pure source metadata/receipt validator: tools/bibimbap_v066_zenodo_source_handoff.py

Offline frozen evidence generator: tools/audit_bibimbap_v066_zenodo_handoff.py

Negative/positive tests: tests/test_bibimbap_v066_zenodo_handoff.py

Canonical report: reports/bibimbap_v066_zenodo_archive_steward_handoff_20261119.json

SHA256: f089801dd7131338bc3b45821d319424cbd6ba4dc28287f07346aaf5cd9ed631

Commands from the existing research worktree:

    $py = 'D:\문서\D__1_Projects\202611\bim-markup-bench\.venv\Scripts\python.exe'
    & $py -m tools.audit_bibimbap_v066_zenodo_handoff --check
    & $py -m unittest -q tests.test_bibimbap_v066_zenodo_handoff

The check compares the cached official Zenodo observations and prior frozen rights reports; it does not make new HTTP requests or inspect ZIP/IFC files. It proves that malformed and fabricated metadata/role claims do not silently promote source rights or release a model trial.

**Remaining:** external independent source+task/evaluator authoring, authentication of five separate stewards, actual file rights and archive acquisition approval, paper scorer SHA, budget/model preregistration and separate owner launch consent. Issue #247 and Draft PR #248 must remain open and unmerged until these dependencies are satisfied.
