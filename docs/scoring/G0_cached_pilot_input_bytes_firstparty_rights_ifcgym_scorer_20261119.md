# BIM-Edit: verified existing pilot INPUT bytes, first-party dataset rights metadata, third-party scorer drift

**2026-11-19 / partial primary benchmark G0.** Research-only offline evidence. This does NOT change the 324 public tasks, 36-item candidate pilot, original GT IFC, original scorer, frozen reports, codebases outside bim-markup-bench, or provider authorization.

## 1. Exact input file content identity, not filename-only hints

Original published task SHA256: 9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83. Task revision: 2dc6462bfab145ddf81b43e9954322855b8443dc. Model revision: 0ae510bd21865def4e2c6145c1244f01a1e3bcb9. Original candidate sample is still NOT preregistered.

| Source-only, actual bytes verified locally | Count |
| --- | ---: |
| Fixed pilot task rows | 36 |
| Distinct public input IFC paths | 25 |
| Input files already present, publisher object + local SHA256 verified | **20** |
| Unique actual SHA256 among these files | **20** |
| Verified Git blob SHA-1 plus newly computed local SHA256 | 19 |
| Verified LFS SHA256 against the exact local bytes | 1 |
| Fixed pilot tasks with a present verified source | **30** |
| Fixed pilot tasks with absent or unverified source | **6** |
| Missing distinct IFC input assets | **5** |
| Local verified input bytes (sum of 20 distinct assets) | **40,744,368 bytes** |
| Remote reported bytes of 5 absent input assets | **736,810,930 bytes** |
| Task reference IFC opened via its GT role, author benchmark scorer or native geometry parsed | **0** |

**Cross-task reference alias finding (fixed published metadata, not private answer inspection):** Among the 25 source IFC input paths, **12 paths also serve as ground-truth/reference paths for some OTHER task in the full 324-task corpus**; 22 of the chosen pilot's 36 rows use those aliased inputs. **One path**, reused by **7 pilot tasks**, is also a reference path for a different task *within the 36 pilot*. All 36 tasks have different own source and own reference paths. **Nine of the 20 locally hashed source files** are cross-task reference aliases. The auditor accessed these files exclusively as the task-input role and read only opaque bytes for hashes; no task's private reference scoring metadata, geometry or GT-role file was accessed. However, it would be misleading to claim the bytes never appear anywhere in the public benchmark as a reference artifact. This overlap means the future agent runner must isolate task environments and prevent cross-task asset or answer leakage; cohort/source clustering and preregistration must treat aliasing explicitly. The audit report contains boolean overlap flags and counts, not GT filenames, target GUIDs or private rubrics.

This improves the previous filename/path-only review: 20 original public source files were actually opened **only as opaque bytes** and checked against the pinned publisher Git blob or LFS hash. Their SHA256 digests are all different. This DOES NOT prove that they originate from 20 different real-world buildings or are untouched prospective model holdouts. Nor does a hash prove per-file legal rights.

Reproducer: tools/audit_bim_edit_pilot_cached_input_bytes.py. The tool reads only the 25 pre-existing source paths in the frozen public task audit; missing 5 do not trigger downloads. Files are accepted only if size and actual local content match original published Git blob SHA-1 or LFS SHA-256. Path escapes, symlinks, modified/invalid cached files and unknown rights/provenance are rejected. An explicit cost gate skips present files above 50 MB and refuses aggregate checked inputs above 100 MB. The tool never resolves each task's ground_truth_ifc field into a file to read. Some public input assets are nevertheless shared with other tasks' ground-truth labels; the cross-task role alias is disclosed above. Hashes of source inputs do not become an agent/model-facing source of task answers.

New immutable report: reports/bim_edit_pilot_existing_cached_input_SHA256_20261119.json (SHA256 **99669d6ae1e006ad9d93039cc42c1ed5d7b460e73982399972285e37cf3dbd10**). New tests: tests/test_bim_edit_pilot_cached_input_bytes.py. The previous source-path audit and 25-path review queue are unchanged, and their SHA256 digests are checked before the new report is generated.

### Status by causal inference level

- **Verified:** 20 separate IFC *byte sequences* and their publisher object provenance, exact candidate task-to-input association.
- **Unverified:** the original physical-building families behind different byte sequences. Same building with multiple revisions can have different SHA256 values; sha-based resampling is still insufficient to claim project independence.
- **Blocked:** individually verified creator/embedded-component rights, named provider input transfer/deletion terms, independently sealed unseen sources/GT, paper-identical executable scorer, registered matched LLM experiment.
- **6 unavailable pilot tasks remain in the original 36-task denominator.** Do not reselect 30 easy tasks or silently omit missing cases.

## 2. First-party CC BY claim does NOT contain per-IFC rightsholder receipts

Read-only publisher metadata at immutable URL:

https://huggingface.co/datasets/BIM-Edit/BIM-Edit/resolve/0ae510bd21865def4e2c6145c1244f01a1e3bcb9/metadata.json

The publisher's 2,091-byte original Croissant JSON was fetched from the exact pinned revision over HTTPS with a 16 KiB cap; original raw publisher SHA256 **04107063e34e0939eb1992e1830a4c9dc5ddd897060ad84c831a96f27ffae861**. To avoid platform-specific Git whitespace errors, the deposited reports/bim_edit_publisher_croissant_metadata_20261119.json snapshot has only CRLF converted to LF (2,030 bytes), SHA256 **aebfbcd3592ba57825e23e59c30ca2edca9b49e971338f54bf32fd233ef724a7**. Converting its LF back to CRLF restores the exact pinned original raw hash; the JSON values are unchanged.

It declares the dataset-level license https://creativecommons.org/licenses/by/4.0/ and file sets simple/*.ifc and complex/*.ifc. But the sole metadata field declared for individual IFC model records is file_path. It supplies **no per-IFC creator, copyright holder, ownership chain, attribution record, embedded third-party BIM component license or model-provider-specific transfer/retention/deletion permission**. This means those facts are not established BY THIS METADATA; it is not proof that author permissions are absent elsewhere or that CC BY does not apply. The existing independent rights ledger still records 0/25 original pilot source assets authenticated for provider transfer.

The supplemental scholarly IfcGym authors list BIM-Edit as CC BY 4.0 in their NOTICE, but they are third parties and do not independently authenticate every component's rightsholder. Their own real IFC projects use heterogeneous licenses (project-specific). Their citation does not upgrade this first-party metadata into a per-original-IFC legal authorization.

## 3. New independent executable scorer provenance: alignment-default drift

Second independent scorer implementation identified in public GitHub:

- IfcGym/IfcEdit: https://github.com/wbw520/ifcgym
- Bounded Git HEAD observed November 19: ea9f5dabb3be22d9a264350cabbf0b9cf6b57625.
- Pinned scorer configuration: https://github.com/wbw520/ifcgym/blob/ea9f5dabb3be22d9a264350cabbf0b9cf6b57625/ifcedit/bimedit_scorer_config.json
- Exact Git blob SHA-1 observed from pinned GitHub file: 5a84a66a3908a3de6d1274240a4e93ac58558df2 (NOT a file SHA256).

The configuration explicitly says match=obb, require_class_match=true, min_iou=0.05, delete_semantics=present_is_one, and align=edit. The repository's own note explains that earlier frozen calibration used align=edit but a new default of gt_guid had silently changed results; it claims an approximately 16-point difference on released runs. **This 16-point effect is the other authors' code comment, not a result independently reproduced by bim-markup-bench.**

The pinned scorer config records an average calibration discrepancy score of 0.20825 and four published per-model final-score mean absolute errors (0..1 scale): Claude Sonnet 0.1842, Gemini Flash 0.2323, GPT-5.4 0.2033 and GPT-5.4 Mini 0.2005, each on n=324. Those are the INDEPENDENT evaluator's report numbers, not current BIM-Edit official scorer outputs and NOT scores produced by BIXML. The IfcGym repository's NOTICE explicitly labels the scorer a reimplementation of BIM-Edit from the paper. ONESTRUCTION independently says the original BIM-Edit executable evaluator is not publicly available and it also reimplemented a scorer: https://ai.onestruction.com/leaderboard/en/methodology/

As a result, three different scorers must remain separate: original author paper scorer (unverified executable provenance), third-party IfcGym calibrated reimplementation (pinned but not officially equal), and our independent-reimplementation (independent metric version). There is also existing third-party VeriBIM/ModIFC-Score with alternative topology and delete-semantic defaults. None can be silently substituted for another.

**Important design distinction:** An official-paper-equivalent scorer is needed to make **numerically direct claims against published BIM-Edit scores**. It is NOT logically required for a carefully controlled **within-study D versus I paired comparison**, if the same independent scorer, original tasks, fixed rules and blinded ground truth are frozen *before* real trials. That internally comparable experiment remains blocked for separate reasons: missing inputs, per-IFC external provider rights, capability/tooling asymmetries, independence of source/GT steward and owner model/cost approval. An official benchmark score is not an internally valid causal D/I effect by itself.

## 4. Reproducibility, integrity and safety

Run from the single existing Windows research checkout:

    .\.venv\Scripts\python.exe -m unittest -q tests.test_bim_edit_pilot_cached_input_bytes
    .\.venv\Scripts\python.exe -m tools.audit_bim_edit_pilot_cached_input_bytes --check

The --check command re-verifies native **source bytes only** against publisher identity and compares the new canonical JSON byte-for-byte. The --write command exclusively creates the new report and refuses replacing any existing report. No task reference IFC was accessed *in its GT role*, no private scorer/answers or native geometry was inspected, and no model provider, external upload or dataset download was involved in computing the 20 source-byte SHA256s. Original input files may double as other tasks' reference files, as explicitly documented. Original metadata/caches/pilot and prior hash-frozen reports remain unchanged.

**The next unresolved high-impact action requires an independent steward/rightsholder or the study owner** rather than more automated developer self-certification: check the 5 absent original inputs under authorized storage; ascertain original building lineage across all 25 paths and per-model AI-provider transfer rights; seal an independent evaluator and matched tool interface. No approval, official scorer parity or live LLM superiority is claimed in this checkpoint.
