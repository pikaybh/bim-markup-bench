# G2 / Issue #21 — Independent IFC scorer replay attestation

Date: 2026-11-10. **This is NOT the official BIM-Edit evaluator.** No paper benchmark input/ground truth, LLM call, paid provider request or official scorer was executed. The existing frozen independent v0.1 scoring rules and public task lists are unmodified.

## Official evaluator source availability

Cross-checked arXiv 2606.20146, the official Hugging Face BIM-Edit-Tasks and BIM-Edit-runs releases, and GitHub repositories matching author/benchmark/evaluator terms. The paper describes MIT-licensed evaluator code in a submission bundle; it was not possible to identify a retrievable author-maintained **source repository, exact commit, dependency lock and executable scorer entrypoint**. The official published runs contain author **score reports**, but those files are not the evaluator itself. A separately distributed release might exist; do not assert absence universally. The fixed public reports in PR #81 are NOT used to tune the local metric.

Primary references:
- https://arxiv.org/abs/2606.20146
- https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks
- https://huggingface.co/datasets/BIM-Edit/BIM-Edit-runs/tree/9241abc9b3b4efa3906c0bdabcf3321f1558192f

## Own synthetic native IFC test

The existing score_ifc_result independently scored eight frozen OWN-generated IFC4X3 comparisons **twice each (16 local scorer calls)**, using separate native input, reference and result IFC files in a temporary grader-only directory:

| Case | Expected |
| --- | --- |
| update_identical_reference | Positive identical native target |
| update_wrong_height | Geometry failure from unmodified source |
| update_missing_space_boundary | Missing IFC topology edge |
| update_collateral_door_deletion | Non-target IFC mutation |
| invalid_candidate_bytes | Invalid candidate IFC; all three axes zero |
| create_equivalent_new_guid | Positive created wall with different GUID |
| delete_window_correct | Positive correct deletion |
| changed_ifc_length_units | Blocked reference/unit convention, all axes null |

**Three strict passes, five negative/blocked cases**. Both repeats of every case yielded identical complete scorer records with identical canonical JSON SHA-256. This is **only a deterministic OWN local scorer replay**, not proof of metric equivalence to the official code.

### Frozen assets and versions

| Asset | SHA-256 |
| --- | --- |
| OWN input IFC | 10d57d3eeb6e50fb51493b03d7cb508d57eadeb76719afaeb71fa6658c3ecf58 |
| OWN wall reference IFC | bb93df8babb11612f4c81f60145a7cf520ef7e19f3abfe49731bf45d92ccda6b |
| 17-case frozen expectations JSON | 678c469281e41de368be1ba4f3f27b8dd1fdaa393278a7b0b15e7952137b5806 |
| Frozen independent score result schema | 06aecf3712faeaf64681c5b5bd7ada41c95c89c9566aea6e18e1f2c62bcdac4d |

All four hashes are checked against separate **pinned constants** before any generated fixture is scored and again after replay. Every output is validated against the existing JSON schema, independently confirmed to have metric_origin = independent-reimplementation and official equivalence = false, and checked against its source/GT/result file hashes. Its status, three-axis mean, per-axis strict threshold 0.98, collateral audit and failure codes are consistent. A blocked reference cannot invent numeric scores. No exposed grader parameter accepts an agent arm, model source or provider name.

The standalone status CLI **intentionally returns 2** on an otherwise successful replay. Its report reports test-only IDs, OWN fixture hashes, output statuses, strict decisions and result SHA digests. It does NOT contain author-published per-task prompts, raw IFC data or hidden GT paths.

### Reproduction commands

1. Run: .venv/Scripts/python.exe -m unittest tests.test_independent_scorer_replay_attestation -v
2. Run: .venv/Scripts/python.exe -m tools.verify_independent_scorer_replay (intentional exit 2)
3. Run: .venv/Scripts/python.exe -m unittest discover -s tests -q

Files:
- src/evaluation/independent_replay_attestation.py
- tests/test_independent_scorer_replay_attestation.py
- tools/verify_independent_scorer_replay.py
- reports/g2_independent_ifc_replay_20261110.json

## Remaining obstacles and scientific limitations

The local geometry sampler uses 384 fixed-seed surface points per target versus paper-described up to 4096/entity. The independent created-target matcher uses GUID/nearest AABB center rather than the paper-described Hungarian OBB IoU; property relevance, topology node alignment and edge-case handling likewise differ or lack sufficient official specification. Do not retrospectively fit/tune these scoring rules against published results.

A true official equivalence check requires an actual author evaluator executable, pinned dependencies and at least three identical IFC source/reference/prediction triples independently scored in a GT-protected environment. Current Docker worker isolation also needs live retesting.

**G2/G3 official and paid-model gates remain BLOCKED. Official benchmark tasks scored: 0. Model calls: 0. No main branch update.**


## Actual validated Windows environment

- Python: 3.12.2
- Operating system / architecture: Windows / AMD64
- IfcOpenShell: 0.8.4.post1
- NumPy: 2.5.4
- jsonschema: 4.25.1

This native-kernel environment applies to the 8-case independent scorer replay. Results on macOS/arm64 or another IfcOpenShell kernel may have slight triangulation/numeric differences. Version declarations are for reproducibility, not official paper scorer-equivalence evidence.


## Frozen implementation source integrity (in addition to fixture SHA)

The qualification gate also freezes the exact source bytes of the independent scorer's four implementation modules. Changing one while preserving the version string is a **blocked metric revision** requiring a newly reviewed scorer version; it is not silently accepted into this proof.

| Source module | SHA-256 |
| --- | --- |
| src/evaluation/bim_edit_scorer.py | d6e4ccb238a7deaf9bcd6c9d6b0998cfaeb367c1d3036ebd332e503327c12288 |
| src/evaluation/geometry_metrics.py | 47b9bc8d6e6a32f62cb15b15397a57c814d750ad71c897cd929f20b65bb14e2c |
| src/evaluation/semantic_diff.py | c67afc9db5f3d647a3e20a17b2970565d0429e97d7761a40557ea4cb6f5f6f33 |
| src/evaluation/topology_metrics.py | 4cddaacc54ff0f0d88ec044212a4185721c57399771bc71928139d373f70ff90 |


## Additional direct arXiv submission-source archive inspection

The actual arXiv v3 source archive at https://arxiv.org/src/2606.20146v3
was retrieved **outside Git** into a temporary file and its tar member
filenames were inspected only (no extraction or execution). This
independently narrows the paper's vague claim about an accompanying
evaluation code folder:

- Download HTTP HEAD: 200, application/gzip, 15,836,931 bytes.
- Download content SHA-256:
  65f503d3cc501b4e4c89a7cff8471b74d9ad43f47b8b1f856c43620d94376243
- Archive members: **36**.
- Top-level entries: 00README.json, imgs, neurips_2026.bbl,
  neurips_2026.sty, neurips_2026.tex, references.bib.
- Executable evaluator/scorer Python, dependency lock, code directory
  or license file identifiable from archive member paths: **0**.

The temporary archive was deleted without extraction. This proves only
that **this exact arXiv v3 TeX submission** does not include a
recognizable evaluator code folder. It does NOT prove the authors'
claimed source does not exist elsewhere or forbid later release.
