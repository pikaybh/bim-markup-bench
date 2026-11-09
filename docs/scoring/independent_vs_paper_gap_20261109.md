# BIM-Edit official vs independent scorer — verified gap gate (2026-11-09)

**Issue:** #4 (also informs #21) · **Status:** BLOCKED_OFFICIAL_SCORER_UNVERIFIED

This is a **provenance and implementation-gap audit**, not numerical official-vs-independent score parity. The latter requires the *same* predicted IFC to be evaluated by both executable scorers. The official executable scorer entrypoint, source commit and version-compatible dependencies have not been verified locally. The paper's claim of a code release is not proof that the published numbers have been reproduced.

## Evidence and differences

| Dimension | Paper-derived metric notes | Current independent implementation | Gap classification |
| --- | --- | --- | --- |
| Geometry point sampling | Up to 4,096 per edited object; area-proportional with 16,384 total cap | 384 points per **single target** by default, fixed seed 2607, area-weighted | Same general shape intent, **sampling schedule/seed uncalibrated** |
| Geometry distance-to-score | Exponential of normalized median Chamfer, alpha=5 | Same exponential mapping on independently sampled mesh points | Scalar expression agrees; values **not numerically equivalent by evidence** |
| Semantic matching | One-to-one OBB IoU matching/Hungarian threshold at 0.05 | Preserve update/delete GUID; create GUID or nearest new geometry center | **Matching policy not equivalent** |
| Semantic attributes | Task-relevant class and property matching with 5% numeric relative tolerance | Local Name/ObjectType/PredefinedType/Psets/materials with abs+rel tolerance | **Property scope/zero handling uncalibrated** |
| Topology | Graph delta, greedy node alignment, 0.3/0.7 F1 node/edge | Raw GUID-set delta with optional aliases; same 0.3/0.7 F1 | **Alignment policy not equivalent** |
| Strict success | All three components >=0.98 | Same per-axis threshold plus *collateral-clean* gate and no failure flags | **Additional strict veto** |
| Reference/examples | Four paper examples provide rounded component numbers | Scalar contract recomputes only averages; no raw prediction IFC replay | **Not a per-task fidelity comparison** |

Sources: paper https://arxiv.org/abs/2606.20146; publicly linked tasks https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks; run artifacts https://huggingface.co/datasets/BIM-Edit/BIM-Edit-runs. Paper and dataset licenses must be inspected independently of the claimed software MIT license.

Code reviewed: `src/evaluation/bim_edit_scorer.py`, `geometry_metrics.py`, `semantic_diff.py`, `topology_metrics.py`, `metric_contract.py`. The new `src/evaluation/metric_gap_audit.py` generates fail-closed evidence and hashes its three inspected source functions. A later code edit must trigger a re-audit rather than silently inherit today's comparison.

## Reproduction (offline; Windows PowerShell)

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_metric_gap_audit -v
.\.venv\Scripts\python.exe -m tools.audit_metric_gap
```

The second command **must exit 2**. Its JSON reports zero official tasks scored and zero model calls. Do not change its status to PASS until an identified, pinned, legally usable official evaluator is run and compared against identical frozen prediction IFCs.

## Next research gate

1. Obtain author-owned official scorer repository/commit/LICENSE/entrypoint, or document no executable is available after a pinned source inventory audit.
2. Choose a predeclared test set including perfect, unchanged, invalid, semantic mismatch, translated geometry, lost relation and deletion collateral cases.
3. Regrade **the same IFC outputs** under both scorers; compare numeric components, task matching, error policy, RNG, tolerances and execution times.
4. Freeze model/IFC/scorer revisions and exact behavior changes before scored LLM work.

No dataset paths, hidden target GUIDs, raw GT, paid model outputs or secrets are included here.
