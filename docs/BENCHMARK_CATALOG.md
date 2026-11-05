# External benchmark catalog and acquisition ledger

**Verified high-level sources. Exact dataset revisions/checksums, redistribution rights and runnable evaluator status have NOT yet been frozen.** Do not download or mirror multi-GB datasets without authorization. Use local content-addressed caches and licenses.

## BIM-Edit — primary edit benchmark

- Paper: https://arxiv.org/abs/2606.20146
- Task definitions: https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks
- Input and GT IFC: https://huggingface.co/datasets/BIM-Edit/BIM-Edit
- Associated runs: https://huggingface.co/datasets/BIM-Edit/BIM-Edit-runs
- Current published task definitions: **324 rows**, 108 per create/update/delete and 108 per direct/spatial/topological; 162 artificial vs 162 realistic. Classes: IfcWall (72), IfcSlab (72), IfcSpace (72), IfcDoor (36), IfcWindow (36), IfcColumn (36). Exact counts and mappings must be revalidated against a pinned revision.
- `tasks.jsonl` has `task_id, operation, category, input_ifc, ground_truth_ifc, prompt, target, evaluation, tags`. **The target and GT paths are grader-only.**
- Known dataset corrections: a recent merged discussion fixed target GUID mismatches and prompt typos; earlier reports found a doubled `.ifc` filename in one model. Verify every path, 22-char IFC GUID and source/reference delta after pinning. Do not silently patch tasks.
- **Official evaluator code availability not yet established.** The presence of paper metric definitions does not prove publication of executable scorer. Track origin and obtain official authors' artifacts or label local reproduction independently.
- Scene and edit type metrics may be differentially constrained by geometry/relations; preserve model-level paired samples.

## BIBIMBAP — secondary CRUD, artifact gate

- Publication and DOI: https://ec-3.org/publication/ec32026_271/
- Paper describes 100 curated CRUD tasks with spatial, geometric, topological, numeric, conceptual categories; includes natural-language prompt, IFC, expected structured outputs, and test scripts.
- **Unverified:** public machine-readable task package, runnable evaluator, test scripts, license and author permissions. Require an acquisition/legal/evaluation audit before implementation; if unavailable, mark blocked rather than fabricate equivalent official benchmark data.
- Requires distinct treatment for `Read` tasks and perhaps text/structured answers rather than IFC mutations.

## IFC-Bench v2 — secondary read/QA

- Canonical dataset page: https://huggingface.co/datasets/sylvainHellin/ifc-bench
- Published paper: https://www.sciencedirect.com/science/article/pii/S0926580526005017
- Dataset describes **1,027 QA pairs**, complexity categories (direct / aggregation / spatial geometry / missing information); fixed test partition described in paper includes **514** test questions, but available dataset revisions may differ and the split file needs pinning.
- Repository revisions can change the count of projects/models (the published paper says 21 projects/37 models; later dataset documentation shows 22/51) and may remove a duplicated training question. **Never silently mix snapshot counts**. Verify pinned commit and exact ID manifest.
- Read-only QA scores must be separate from BIM editing. The direct arm can use a typed read-only projection of IFC as XML; baseline can query via Python/IfcOpenShell under equal information budgets.
- Question/license documentation may be CC BY 4.0 but **individual IFC models have their own licenses**; some are GPL. Check `license.txt` for each input before storage/republication.

## Acquisition ledger (to create)

```json
{
  "benchmark": "bim-edit",
  "dataset_revision": "UNPINNED",
  "files": [],
  "license_reviewed": false,
  "ground_truth_isolated": false,
  "official_evaluator_available": "unknown",
  "task_mapping_verified": false
}
```

Freeze: dataset commit IDs, SHA-256 of task records + every IFC, license matrix, source URLs, known exceptions and official evaluator status. The corpus must NOT be committed to this repository.

## If a benchmark fails the gate
Record `BLOCKED_DATA`, `BLOCKED_LICENSE`, `BLOCKED_EVALUATOR` or `BLOCKED_MISMATCH` with evidence, avoid ghost completion, and proceed on a predeclared supported subset while marking coverage.
