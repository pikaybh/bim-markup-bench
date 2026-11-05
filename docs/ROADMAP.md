# Research workstream roadmap

**Planning document; GitHub Issues are the executable assignments.** Completion requires reproducible evidence, not an assertion.

## G0: reproducible foundation and data
- Repository/project governance, security, access and licensing
- Benchmark inventory, version pins, task/IFC pairing and data leakage controls
- Source fixtures, synthetic examples, deterministic round-trip baselines
- Evaluation metric reconstruction or official evaluator acquisition

## G1: source authoring and runtime equivalence
- Safe XML grammar, direct file writer, stable identity and semantic references
- IFC-preserving clone/import/bind/patch/export
- Real geometry updates and topology/host/space boundary validation
- Deterministic D0/P0 oracles and unchanged-entity checks
- Atomic failure handling, source diagnostics and file-level state isolation

## G2: matched agent loop
- Direct XML file editing arm with no BIM API exposure
- Python/IfcOpenShell baseline with approved API capability profile
- Same backend, model, budgets, feedback, input visibility and environment
- Trial isolation, logging, costs and token measurements
- Independent blinded scorer with test fixtures

## G3: pilot
- Frozen predeclared stratified task IDs and feasibility coverage
- First matched paired LLM pilot; no passing-task selection
- Triage systemic IFC/geometry/semantic errors and fix without retuning metrics on pilot outputs
- Report negative/failed/unsupported cases and paired bootstrap

## G4: full primary benchmark
- 324 BIM-Edit if G3 gates pass; report ITT and common-supported subset
- Family-specific performance, untouched semantic integrity, scripts/prompts/checksums
- Replication bundle for independent reviewers

## G5: secondary and paper
- BIBIMBAP 100 only if legal artifacts and evaluator are available
- IFC-Bench v2 1,027 question corpus: READ-only and distinct outcome
- Ablations: markup syntax / source view / schema context / feedback budget, representation effects
- Scientific writeup with threat-to-validity and limitations

## Release gates and conservative definitions
- **G0 complete** only if data and scoring provenance is frozen and reproducible.
- **G1 complete** only when both non-LLM oracles can solve a shared fixture, including topological relationship changes.
- **G2 complete** only when LLM cannot access GT and each arm runs end-to-end under matched resource constraints.
- **G3 complete** only when a fixed pilot reports every attempt and failure.
- **G4 complete** only when all 324 primary tasks are *attempted or explicitly marked unsupported*, without cherry-picking.
- **G5 complete** only after independent task-family validation and rights audit.

Prefer completing evidence-driven gates over implementing more IFC object types without passing any test.
