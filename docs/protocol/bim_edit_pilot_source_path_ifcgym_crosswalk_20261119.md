# BIM-Edit primary pilot — pinned input reuse and IfcGym scorer crosswalk

**2026-11-19 | offline scientific-validity evidence | NOT a model experiment**

This report uses the existing pinned BIM-Edit public task JSONL and remote *file metadata*. It neither reads/changes original or reference IFC bytes, reveals private reference answers, modifies a frozen sample, runs a model, nor certifies licensing or official scorer equivalence.

## A. Real original BIM-Edit pilot source-path dependence

Fixed task dataset revision: 2dc6462bfab145ddf81b43e9954322855b8443dc. Original task JSONL SHA256: 9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83. Model repository revision: 0ae510bd21865def4e2c6145c1244f01a1e3bcb9. The original 36-task pilot in manifests/pilot_36_candidate_v0.json remains CANDIDATE_NOT_PREREGISTERED.

| Metadata-only finding | Measured |
| --- | ---: |
| Original 324 task rows | 324 |
| Distinct exact input IFC paths in the original 324 | 88 |
| Frozen pilot tasks | 36 |
| Distinct exact input IFC paths in the 36 pilot | **25** |
| Repeated task rows beyond first use of a path | 11 |
| Largest number of pilot tasks sharing one path | **7** |
| Remote-reported total size of 25 distinct pilot inputs | **777,555,298 bytes** |
| IFC or reference IFC files opened/downloaded by this audit | **0** |

Equal paths demonstrate input reuse. **Different paths may still be variants of the same original building**, so 25 is an upper bound on independent source families, NOT a verified cluster count. Similarly, the 88 paths in the full dataset are not necessarily 88 buildings. A path hash, remote Git object ID, or unverified LFS pointer is NOT a independently verified input-IFC SHA256. Such values must not be placed into a cluster-ITT input under the misleading field name source_sha256.

Existing G0 evidence independently had 30/36 original input/GT pairs content-verified, and 6 blocked; this new audit verifies only **public task-to-input-path and publisher tree metadata**, not original IFC content, prompt validity, source rights, or GT. The previously frozen missing-data result is unchanged. Future analyses must report ITT for all prespecified tasks including unsupported/blocked attempts, use verified source IFC hashes, and ideally externally adjudicate common source-building lineage across input revisions before outcomes are seen. The existing cluster ITT analysis refuses nonexistent or forged source SHA fields.

Technical files:
- tools/audit_bim_edit_pilot_input_clusters.py
- tests/test_bim_edit_pilot_input_clusters.py
- reports/bim_edit_pilot_source_path_independence_20261119.json

Only public task IDs, input repo paths, and publisher size metadata appear in the new report. No task prompt, target GUID, reference path, geometry, private scorer, or model answers appear.

## B. New relevant paper: IfcGym / IfcEdit (November 17, 2026)

Jiaxin Zhang, Yao Luo, Yuze Dan, Yunqin Li, Bowen Wang, *Learning to Edit IFC Building Models: Verifiable Checkers as the Training Signal for Dependency-Aware Editing Agents*, arXiv 2611.22307v1. Primary source: https://arxiv.org/html/2611.22307v1 ; abstract https://arxiv.org/abs/2611.22307

This paper is a directly relevant CodeAct / Python+IfcOpenShell editing and evaluator baseline. **Reported by its authors, not independently reproduced here**:

- The IfcGym agent uses four checks: validity, intent, dependency, preservation. Its trained IfcEdit student improves by SFT then GRPO; the 9B student reports 86.78% strict success on its own 1,990-task / 13 held-out real-project IfcEditBench, versus 79.15% after SFT only; the 27B model reports 91.76% strict success.
- The 9B student reports BIM-Edit score 55.19 and BIBIMBAP score 54.50. These scores use different datasets and are not the IfcEditBench strict-success percentage.
- Code/reproduction link declared in the paper: https://github.com/wbw520/ifcgym ; test dataset https://huggingface.co/datasets/wbw520wbw520/ifceditbench . We did not clone, download, inspect the IFC content, or independently confirm data rights.
- Published source/data licensing is heterogeneous (Apache code, per-project CC BY/MIT/GPL/KIT among the real projects, and separate CC BY-NC synthetic training corpus). A dataset metadata label is not a blanket provider transfer/rightsholder grant.

**Critical scorer evidence from Appendix G:** The authors report that BIM-Edit's official executable scorer was not public. They attempted 1,024 reconstruction configurations using original paper details plus public released task scores. Their chosen scorer had ~20.8-point (0–100) mean absolute calibration error. Appendix Table 18 reports per-task final-score MAE: Claude Sonnet 4.6 calibration **18.4**, Gemini 3.0 Flash calibration **23.2**, GPT-5.4 Pro held-out **20.3**, GPT-5.4 Mini held-out **20.1**. Only 20–46% of predictions fell within five points, depending on run. Table 19 reports update-task MAE near **39 points** with low correlation (at most 0.24). Authors explicitly characterize original-vs-reimplemented scorer comparisons as approximate.

**Implications for our study:** Never call our independent scorer or theirs official or numerically interchangeable. Publish its provenance, inspect sensitivity to evaluator conventions, and distinguish (i) a whole-workflow D_FULL/D_MANAGED-vs-I_NATIVE comparison from (ii) the currently unsupported representation-only causal claim. Current D/I editing capabilities, native-IFC accessibility, and compiler affordances are asymmetric. The IfcGym paper is a stronger code-based baseline for context, not evidence that the XML editing hypothesis is true or false.

## C. Remaining hard gates and no-launch constraints

1. Acquire/verify the selected original IFC source content and creator/individual asset licensing under separately authorized storage/rightsholder conditions. Seal building-lineage groups and an independent task/reference evaluator before developer inspection; do NOT relabel reused/reviewed sources blind.
2. Obtain a publication-backed official BIM-Edit scorer executable SHA/tag, or explicitly mark all independent scoring not directly comparable. Do not optimize any evaluator by peeking at pilot or trial outcomes.
3. Freeze accepted model/provider snapshot, equal task instructions and read/feedback budgets, token and cost accounting, timeout/retry behavior, immutable preregistration, rights approval and owner-funded cap before initiating model trials.
4. Preserve the original fixed 36 task sample and preserve all failures and unsupported cases in ITT denominator, not only the readily available 30 tasks.

This checkpoint does not solve independently blind sourcing, individual IFC rights, unreleased original scorer, model execution or statistical power.

## Offline replay

Run from the existing single bim-markup-bench repository:

    .\.venv\Scripts\python.exe -m tools.audit_bim_edit_pilot_input_clusters --check
    .\.venv\Scripts\python.exe -m unittest -q tests.test_bim_edit_pilot_input_clusters

The --check script compares canonical frozen report bytes and refuses to overwrite an existing report. Mutation tests reject changed task SHA, revisions, sample, strata, paths, duplicate cohort IDs, missing tree assets, malformed JSON and false preregistration claims.
