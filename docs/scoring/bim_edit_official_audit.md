# BIM-Edit official evaluator availability audit (G0 Issue #4)

**2026-11-11 follow-up:** [Exact author-vs-independent scorer provenance audit](G0_original_scorer_source_reaudit_20261111.md). No original-author executable scorer source/commit/CLI has been verified. The public third-party [VeriBIM ModIFC-Score](https://github.com/NTUZZH/VeriBIM) is an *independent reimplementation*, not an official MIT release; its explicit topology and Delete-semantic interpretations have no established original-code parity. G0 Issue #4 remains OPEN.

**STATUS (updated 2026-11-10): AUTHOR-PUBLISHED SCORED RUN REPORTS VERIFIED IN PINNED HF RELEASE; EXECUTABLE OFFICIAL SCORER STILL NOT VERIFIED/INSTALLED. ISSUE REMAINS OPEN.**

**Critical updated audit:** [G0 official runs public release 2026-11-10](G0_official_public_runs_release_20261110.md). The exact HF `BIM-Edit-runs` revision `9241abc9b3b4efa3906c0bdabcf3321f1558192f` contains **7 model run folders with evaluation reports** (1,417 file entries), including per-task CSV and aggregate JSON for each model. The original paper's 2026 claim that evaluator **source code** is under MIT is **distinct** from verified executable access. No official source-code revision/entrypoint has been established. The older statement below about only model-output folders is historical and must not be used as the latest release inventory.

## Primary sources reviewed (no PDF downloaded or altered)

- arXiv v3 HTML, Section 3.2 and Appendices E, F, H, J: https://arxiv.org/html/2606.20146
- Task cards & task examples: https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks
- Published cached model runs: https://huggingface.co/datasets/BIM-Edit/BIM-Edit-runs
- Linked model corpus: https://huggingface.co/datasets/BIM-Edit/BIM-Edit

## Repository availability conclusion (current search, not an assertion of non-existence)

The paper explicitly says that inference harness and evaluator code are released under MIT, and Appendix F.5 describes a code folder included with the submission, with cached predictions and evaluations. However:
- Neither the arXiv HTML manuscript inspected nor the task/model dataset pages directly yielded a **verified source-code Git revision and executable scorer entrypoint**.
- GitHub public repository search for BIM-Edit returned unrelated BIM editors and this independent benchmark repo; no confidently identified author-owned source matching this exact evaluator.
- The HF BIM-Edit-runs dataset contains model output directories. The remote tree starts with numerous cached edited models, but this is **not enough evidence that it includes source code**.
- Therefore the scorer is **unverified**, NOT declared unpublished, inaccessible or unlicensed. The paper's MIT claim does NOT authorize inventing a local implementation and labeling it official.

**Action before closure:** find an identifiable code-release URI/commit, its LICENSE, build steps, exact pinned Python/backend dependencies and scorer CLI; otherwise request it from the original authors. No message was sent.

## Researcher-facing audit questions (draft only)

1. What is the canonical Git repository/release/commit of the BIM-Edit official evaluator and its MIT license?
2. Can it score arbitrary externally generated input IFC/result IFC/target task IDs, without rerunning LLM inference?
3. What random seed is used for 4096-per-object/16384-total surface point sampling, and which IFC shape kernel/meshing settings?
4. What are the special conventions for absent/degenerate geometry, no affected nodes, empty edge sets, matching ties, unsupported IFC4X3 and invalid IFC files?
5. Where are official scorer regression fixtures and the CSV/JSON records for example tasks, including their exact unrounded component scores?
6. Is a fixed version of the scorer paired with the current task JSONL SHA-256 and model revision?

## Scalar arithmetic extracted and implemented in isolation

src/evaluation/metric_contract.py implements only final mean, exponential normalized geometry score *after a Chamfer distance is already computed*, semantic mean *after matching*, topology F1 weighting *after aligning graphs*, deletion/no-topology special cases, and strict pass threshold. Its output marks metric_origin = paper-formula-only and full_ifc_evaluator_implemented = false.

This is an **arithmetic contract** with unit tests; it is **not** the independent full IFC evaluator, cannot score edited IFCs and must never be compared numerically to the paper's full evaluated runs.

## Release gate still required

- Official code/commit/license and direct runner execution verified OR an independent full implementation rigorously calibrated with explicit non-equivalence label.
- Real input/GT IFC assets verified (Issue #3).
- Shape extraction, point sampling, Chamfer computation, OBB matching, relevant semantic attribute selection, full topology graph diff+matching implemented with negative fixtures (Issue #21).
- Three paper example runs recomputed from actual raw benchmark outputs and independent shape/graph features (currently tests reproduce arithmetic only).
- Independent, isolated GT grader enforced (Issues #8, #19 and #22).

**This audit explicitly prevents claiming that our direct XML arm has a measured geometry, semantic or topology score until those items pass.**
